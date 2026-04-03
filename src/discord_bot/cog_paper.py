"""Paper trading cog -- Discord interface for the paper trading engine.

Implements slash commands:
    /paper_status              -- Portfolio overview with positions and fills
    /paper_history [strategy] [days]  -- Trade history with pagination
    /paper_position <id>       -- Detailed view of a specific position
    /paper_close <id> [reason] -- Manually close a paper position
    /paper_orders              -- View pending/recent orders
    /paper_pnl [days]          -- P/L chart and daily breakdown

Background tasks:
    - Auto-post daily P/L summary at 16:15 ET to #paper-trading
    - Post fill alerts in real-time to #paper-trading
"""

import logging
from datetime import datetime, time, timedelta, timezone
from typing import Any, TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands, tasks

from src.config import config
from src.discord_bot.embeds import build_paper_history_embed

if TYPE_CHECKING:
    from src.paper.engine import PaperTradingEngine

logger = logging.getLogger(__name__)

from src.utils import ET, now_et as _now_et


# -- Autocomplete helpers ----------------------------------------------------


async def strategy_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete from strategies in PAPER status."""
    manager = getattr(interaction.client, "strategy_manager", None)
    if manager is None:
        return []
    try:
        from src.strategy.lifecycle import StrategyStatus
        strategies = await manager.list_strategies(status=StrategyStatus.PAPER)
        return [
            app_commands.Choice(name=s["name"], value=s["name"])
            for s in strategies
            if current.lower() in s["name"].lower()
        ][:25]  # Discord max 25 choices
    except Exception:
        return []


# -- Views -------------------------------------------------------------------


class PaginatedHistoryView(discord.ui.View):
    """Pagination buttons for trade history.

    Stores current page state and rebuilds embed on button press.
    Timeout after 300 seconds (buttons become inactive).
    """

    def __init__(
        self,
        trades: list[dict],
        strategy_filter: str | None,
        days: int,
        page: int = 1,
        page_size: int = 15,
        timeout: float = 300.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.trades = trades
        self.strategy_filter = strategy_filter
        self.days = days
        self.page = page
        self.page_size = page_size
        self.total_pages = max(1, (len(trades) + page_size - 1) // page_size)
        self._update_buttons()

    def _update_buttons(self) -> None:
        """Enable/disable buttons based on current page."""
        self.prev_button.disabled = self.page <= 1
        self.next_button.disabled = self.page >= self.total_pages

    @discord.ui.button(label="< Prev", style=discord.ButtonStyle.secondary)
    async def prev_button(
        self, interaction: discord.Interaction, button: discord.ui.Button,
    ) -> None:
        self.page = max(1, self.page - 1)
        self._update_buttons()
        embed = build_paper_history_embed(
            self.trades, self.strategy_filter, self.days,
            page=self.page, page_size=self.page_size,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next >", style=discord.ButtonStyle.secondary)
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button,
    ) -> None:
        self.page = min(self.total_pages, self.page + 1)
        self._update_buttons()
        embed = build_paper_history_embed(
            self.trades, self.strategy_filter, self.days,
            page=self.page, page_size=self.page_size,
        )
        await interaction.response.edit_message(embed=embed, view=self)


class CloseConfirmView(discord.ui.View):
    """Confirmation buttons for manual position close.

    Prevents accidental closes. Timeout 60 seconds.
    """

    def __init__(
        self,
        position_id: int,
        reason: str,
        timeout: float = 60.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.position_id = position_id
        self.reason = reason
        self.confirmed: bool | None = None

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.red)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button,
    ) -> None:
        self.confirmed = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button,
    ) -> None:
        self.confirmed = False
        self.stop()


# -- Cog class ---------------------------------------------------------------


class PaperTradingCog(commands.Cog, name="PaperTrading"):
    """Discord commands for paper trading status, history, and management."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._daily_posted_date: str = ""  # prevent double daily post
        logger.info("PaperTradingCog loaded")

    # -- Lifecycle hooks ------------------------------------------------------

    async def cog_load(self) -> None:
        """Start background tasks when the cog is loaded."""
        self.auto_paper_daily.start()
        logger.info("PaperTrading background tasks started")

    async def cog_unload(self) -> None:
        """Stop background tasks when the cog is unloaded."""
        self.auto_paper_daily.cancel()
        logger.info("PaperTrading background tasks stopped")

    # -- Channel and engine helpers -------------------------------------------

    def _get_paper_channel(self) -> discord.TextChannel | None:
        """Get the paper trading channel from config."""
        channel_id = getattr(config, "paper_trading_channel_id", 0)
        if channel_id == 0:
            channel_id = getattr(config, "paper_channel_id", 0)
        if channel_id == 0:
            # Fall back to analysis channel
            channel_id = config.analysis_channel_id
        if channel_id == 0:
            logger.warning("No paper trading channel configured")
            return None

        channel = self.bot.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.TextChannel):
            logger.warning(
                "Paper trading channel %d not found or not text channel",
                channel_id,
            )
            return None
        return channel

    def _get_engine(self) -> "PaperTradingEngine | None":
        """Get paper engine from bot, with None guard."""
        return getattr(self.bot, "paper_engine", None)

    # -- Shared helper methods ------------------------------------------------

    async def _enrich_positions(self, positions: list[dict]) -> list[dict]:
        """Add strategy_name to each position dict."""
        manager = getattr(self.bot, "strategy_manager", None)
        if manager is None:
            return positions

        for pos in positions:
            try:
                strategy = await manager.get(pos["strategy_id"])
                pos["strategy_name"] = strategy["name"] if strategy else f"Strategy #{pos['strategy_id']}"
            except Exception:
                pos["strategy_name"] = f"Strategy #{pos['strategy_id']}"
        return positions

    async def _get_todays_fills(self, engine: "PaperTradingEngine") -> list[dict]:
        """Get fills from today's orders."""
        today = _now_et().date().isoformat()
        try:
            cursor = await engine._db.execute(
                """
                SELECT o.id, o.strategy_id, o.direction, o.fill_price,
                       o.slippage, o.filled_at
                FROM paper_orders o
                WHERE o.status = 'filled'
                  AND o.filled_at >= ?
                ORDER BY o.filled_at DESC
                """,
                (today,),
            )
            rows = await cursor.fetchall()
            cols = ["id", "strategy_id", "direction", "fill_price",
                    "slippage", "filled_at"]
            fills = []
            for row in rows:
                fill = dict(zip(cols, row))
                # Get leg fills for this order
                leg_fills = await engine.order_manager.get_fills_for_order(fill["id"])
                fill["legs"] = leg_fills
                fills.append(fill)
            return fills[:20]  # Cap at 20 most recent
        except Exception as exc:
            logger.error("Failed to get today's fills: %s", exc)
            return []

    async def _enrich_trades(self, trades: list[dict]) -> list[dict]:
        """Add strategy_name to each trade dict."""
        manager = getattr(self.bot, "strategy_manager", None)
        if manager is None:
            return trades

        # Cache strategy names to avoid repeated lookups
        name_cache: dict[int, str] = {}
        for trade in trades:
            sid = trade["strategy_id"]
            if sid not in name_cache:
                try:
                    strategy = await manager.get(sid)
                    name_cache[sid] = strategy["name"] if strategy else f"#{sid}"
                except Exception:
                    name_cache[sid] = f"#{sid}"
            trade["strategy_name"] = name_cache[sid]
        return trades

    async def _get_trade_history(
        self,
        engine: "PaperTradingEngine",
        strategy_filter: str,
        days: int,
    ) -> list[dict]:
        """Fetch trade history with optional strategy filter."""
        cutoff = (_now_et() - timedelta(days=days)).date().isoformat()

        # Build query
        if strategy_filter:
            # Resolve strategy name to ID
            manager = getattr(self.bot, "strategy_manager", None)
            strategy_id = None
            if manager:
                try:
                    strategies = await manager.list_strategies()
                    for s in strategies:
                        if s["name"].lower() == strategy_filter.lower():
                            strategy_id = s["id"]
                            break
                except Exception:
                    pass

            if strategy_id is not None:
                cursor = await engine._db.execute(
                    """
                    SELECT id, strategy_id, entry_date, exit_date,
                           holding_days, entry_price, exit_price,
                           total_pnl, fees, slippage_cost, close_reason
                    FROM paper_trades
                    WHERE strategy_id = ? AND exit_date >= ?
                    ORDER BY exit_date DESC
                    """,
                    (strategy_id, cutoff),
                )
            else:
                cursor = await engine._db.execute(
                    """
                    SELECT id, strategy_id, entry_date, exit_date,
                           holding_days, entry_price, exit_price,
                           total_pnl, fees, slippage_cost, close_reason
                    FROM paper_trades
                    WHERE exit_date >= ?
                    ORDER BY exit_date DESC
                    """,
                    (cutoff,),
                )
        else:
            cursor = await engine._db.execute(
                """
                SELECT id, strategy_id, entry_date, exit_date,
                       holding_days, entry_price, exit_price,
                       total_pnl, fees, slippage_cost, close_reason
                FROM paper_trades
                WHERE exit_date >= ?
                ORDER BY exit_date DESC
                """,
                (cutoff,),
            )

        rows = await cursor.fetchall()
        cols = ["id", "strategy_id", "entry_date", "exit_date",
                "holding_days", "entry_price", "exit_price",
                "total_pnl", "fees", "slippage_cost", "close_reason"]
        trades = [dict(zip(cols, row)) for row in rows]

        # Enrich with strategy names
        trades = await self._enrich_trades(trades)
        return trades

    async def _get_recent_orders(
        self,
        engine: "PaperTradingEngine",
        status_filter: str,
    ) -> list[dict]:
        """Get recent paper orders, optionally filtered by status."""
        if status_filter == "pending":
            return await engine.order_manager.get_pending_orders()

        cutoff = (_now_et() - timedelta(days=7)).isoformat()

        if status_filter == "all":
            cursor = await engine._db.execute(
                """
                SELECT id, strategy_id, order_type, direction, quantity,
                       limit_price, status, submitted_at, filled_at,
                       fill_price, slippage
                FROM paper_orders
                WHERE submitted_at >= ?
                ORDER BY submitted_at DESC
                LIMIT 30
                """,
                (cutoff,),
            )
        else:
            cursor = await engine._db.execute(
                """
                SELECT id, strategy_id, order_type, direction, quantity,
                       limit_price, status, submitted_at, filled_at,
                       fill_price, slippage
                FROM paper_orders
                WHERE status = ? AND submitted_at >= ?
                ORDER BY submitted_at DESC
                LIMIT 30
                """,
                (status_filter, cutoff),
            )

        rows = await cursor.fetchall()
        cols = ["id", "strategy_id", "order_type", "direction", "quantity",
                "limit_price", "status", "submitted_at", "filled_at",
                "fill_price", "slippage"]
        return [dict(zip(cols, row)) for row in rows]

    async def _get_todays_closed_trades(
        self,
        engine: "PaperTradingEngine",
    ) -> list[dict]:
        """Get trades closed today."""
        today = _now_et().date().isoformat()
        try:
            cursor = await engine._db.execute(
                """
                SELECT id, strategy_id, entry_date, exit_date, total_pnl,
                       fees, close_reason
                FROM paper_trades
                WHERE exit_date = ?
                ORDER BY id
                """,
                (today,),
            )
            rows = await cursor.fetchall()
            cols = ["id", "strategy_id", "entry_date", "exit_date",
                    "total_pnl", "fees", "close_reason"]
            trades = [dict(zip(cols, row)) for row in rows]
            return await self._enrich_trades(trades)
        except Exception as exc:
            logger.error("Failed to get today's trades: %s", exc)
            return []

    # -- Slash commands -------------------------------------------------------

    @app_commands.command(
        name="paper_status",
        description="Paper trading portfolio overview -- positions, P/L, today's activity",
    )
    async def paper_status(self, interaction: discord.Interaction) -> None:
        """Show current paper trading status with positions and fills."""
        await interaction.response.defer()

        engine = self._get_engine()
        if engine is None:
            await interaction.followup.send(
                "Paper trading engine not available.", ephemeral=True,
            )
            return

        try:
            # Get portfolio summary
            portfolio = await engine.get_portfolio_summary()

            # Get open positions with strategy names
            positions = await engine.position_tracker.get_open_positions()
            positions = await self._enrich_positions(positions)

            # Get today's fills
            todays_fills = await self._get_todays_fills(engine)

            # Build embed
            from src.discord_bot.embeds import build_paper_status_embed
            embed = build_paper_status_embed(portfolio, positions, todays_fills)

            await interaction.followup.send(embed=embed)

        except Exception as exc:
            logger.error("paper_status failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to fetch paper trading status.", ephemeral=True,
            )

    @app_commands.command(
        name="paper_history",
        description="Paper trade history -- completed trades with P/L breakdown",
    )
    @app_commands.describe(
        strategy="Filter by strategy name (optional)",
        days="Lookback period in days (1-90, default 7)",
    )
    @app_commands.autocomplete(strategy=strategy_autocomplete)
    async def paper_history(
        self,
        interaction: discord.Interaction,
        strategy: str = "",
        days: int = 7,
    ) -> None:
        """Show paper trade history with pagination."""
        await interaction.response.defer()

        engine = self._get_engine()
        if engine is None:
            await interaction.followup.send(
                "Paper trading engine not available.", ephemeral=True,
            )
            return

        # Validate days parameter
        days = max(1, min(90, days))

        try:
            trades = await self._get_trade_history(engine, strategy, days)

            embed = build_paper_history_embed(
                trades,
                strategy_filter=strategy or None,
                days=days,
                page=1,
                page_size=15,
            )

            # Add pagination if needed
            if len(trades) > 15:
                view = PaginatedHistoryView(
                    trades=trades,
                    strategy_filter=strategy or None,
                    days=days,
                )
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as exc:
            logger.error("paper_history failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to fetch paper trade history.", ephemeral=True,
            )

    @app_commands.command(
        name="paper_position",
        description="Detailed view of a specific paper position",
    )
    @app_commands.describe(
        position_id="Position ID number (shown in /paper_status)",
    )
    async def paper_position(
        self,
        interaction: discord.Interaction,
        position_id: int,
    ) -> None:
        """Show detailed position info including legs, fills, and P/L."""
        await interaction.response.defer()

        engine = self._get_engine()
        if engine is None:
            await interaction.followup.send(
                "Paper trading engine not available.", ephemeral=True,
            )
            return

        try:
            position = await engine.position_tracker._get_position(position_id)
            if position is None:
                await interaction.followup.send(
                    f"Position #{position_id} not found.", ephemeral=True,
                )
                return

            # Get strategy name
            manager = getattr(self.bot, "strategy_manager", None)
            strategy_name = f"Strategy #{position['strategy_id']}"
            if manager:
                try:
                    s = await manager.get(position["strategy_id"])
                    if s:
                        strategy_name = s["name"]
                except Exception:
                    pass

            # Get opening fills
            fills = await engine.order_manager.get_fills_for_order(
                position["open_order_id"],
            )

            from src.discord_bot.embeds import build_paper_position_detail_embed
            embed = build_paper_position_detail_embed(
                position=position,
                strategy_name=strategy_name,
                fills=fills,
            )
            await interaction.followup.send(embed=embed)

        except Exception as exc:
            logger.error("paper_position failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to fetch position details.", ephemeral=True,
            )

    @app_commands.command(
        name="paper_close",
        description="Manually close a paper position",
    )
    @app_commands.describe(
        position_id="Position ID to close",
        reason="Reason for manual close (optional, default: 'manual')",
    )
    async def paper_close(
        self,
        interaction: discord.Interaction,
        position_id: int,
        reason: str = "manual",
    ) -> None:
        """Close a paper position manually with confirmation."""
        await interaction.response.defer()

        engine = self._get_engine()
        if engine is None:
            await interaction.followup.send(
                "Paper trading engine not available.", ephemeral=True,
            )
            return

        # Verify position exists and is open
        position = await engine.position_tracker._get_position(position_id)
        if position is None:
            await interaction.followup.send(
                f"Position #{position_id} not found.", ephemeral=True,
            )
            return

        if position["status"] != "open":
            await interaction.followup.send(
                f"Position #{position_id} is already {position['status']}.",
                ephemeral=True,
            )
            return

        # Show position details and ask for confirmation
        from src.discord_bot.embeds import build_paper_position_detail_embed

        manager = getattr(self.bot, "strategy_manager", None)
        strategy_name = f"Strategy #{position['strategy_id']}"
        if manager:
            try:
                s = await manager.get(position["strategy_id"])
                if s:
                    strategy_name = s["name"]
            except Exception:
                pass

        fills = await engine.order_manager.get_fills_for_order(
            position["open_order_id"],
        )
        embed = build_paper_position_detail_embed(
            position=position,
            strategy_name=strategy_name,
            fills=fills,
        )
        embed.title = f"Close Position #{position_id}? -- {strategy_name}"
        embed.description = f"Reason: {reason}\nConfirm to close this position."

        view = CloseConfirmView(position_id=position_id, reason=reason)
        msg = await interaction.followup.send(embed=embed, view=view)

        # Wait for user confirmation
        timed_out = await view.wait()

        if timed_out or not view.confirmed:
            embed.title = f"Close Cancelled -- Position #{position_id}"
            embed.color = 0x808080  # Gray
            embed.description = "Position close was cancelled or timed out."
            await msg.edit(embed=embed, view=None)
            return

        # Execute the close
        try:
            trade_id = await engine.force_close_position(
                position_id=position_id,
                reason=reason,
            )

            if trade_id is not None:
                close_embed = discord.Embed(
                    title=f"Position #{position_id} Closed",
                    description=(
                        f"Strategy: {strategy_name}\n"
                        f"Reason: {reason}\n"
                        f"Trade ID: #{trade_id}"
                    ),
                    color=0x0099FF,
                    timestamp=datetime.now(timezone.utc),
                )
                close_embed.set_footer(
                    text="SPY Options Employee | Paper Trading",
                )
                await msg.edit(embed=close_embed, view=None)
            else:
                await msg.edit(
                    embed=discord.Embed(
                        title="Close Failed",
                        description=(
                            f"Could not close position #{position_id}. "
                            "It may require live chain data for fill simulation."
                        ),
                        color=0xFF0000,
                    ),
                    view=None,
                )

        except Exception as exc:
            logger.error(
                "paper_close failed for position #%d: %s",
                position_id, exc, exc_info=True,
            )
            await msg.edit(
                embed=discord.Embed(
                    title="Close Error",
                    description=f"Error closing position #{position_id}.",
                    color=0xFF0000,
                ),
                view=None,
            )

    @app_commands.command(
        name="paper_orders",
        description="View pending and recent paper orders",
    )
    @app_commands.describe(
        status="Order status filter (default: all recent)",
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Pending", value="pending"),
        app_commands.Choice(name="Filled", value="filled"),
        app_commands.Choice(name="Cancelled", value="cancelled"),
        app_commands.Choice(name="All Recent", value="all"),
    ])
    async def paper_orders(
        self,
        interaction: discord.Interaction,
        status: str = "all",
    ) -> None:
        """Show paper orders with optional status filter."""
        await interaction.response.defer()

        engine = self._get_engine()
        if engine is None:
            await interaction.followup.send(
                "Paper trading engine not available.", ephemeral=True,
            )
            return

        try:
            orders = await self._get_recent_orders(engine, status)

            embed = discord.Embed(
                title=f"Paper Orders ({status.title()})",
                description=f"{len(orders)} orders found",
                color=0x0099FF,
                timestamp=datetime.now(timezone.utc),
            )

            if not orders:
                embed.add_field(
                    name="No Orders",
                    value="No matching orders found.",
                    inline=False,
                )
            else:
                order_lines = []
                for o in orders[:20]:
                    status_icon = {
                        "pending": "[PEND]",
                        "filled": "[FILL]",
                        "cancelled": "[CANC]",
                        "expired": "[EXP]",
                    }.get(o["status"], o["status"])

                    line = (
                        f"#{o['id']} {status_icon} {o['direction'].upper()} "
                        f"| Qty: {o['quantity']} | {o['order_type']}"
                    )
                    if o["fill_price"] is not None:
                        line += f" | Fill: ${o['fill_price']:.4f}"
                    if o["submitted_at"]:
                        line += f" | {o['submitted_at'][:16]}"
                    order_lines.append(line)

                embed.add_field(
                    name="Orders",
                    value="\n".join(order_lines),
                    inline=False,
                )

            embed.set_footer(text="SPY Options Employee | Paper Orders")
            await interaction.followup.send(embed=embed)

        except Exception as exc:
            logger.error("paper_orders failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to fetch paper orders.", ephemeral=True,
            )

    @app_commands.command(
        name="paper_pnl",
        description="Paper trading P/L chart and daily breakdown",
    )
    @app_commands.describe(
        days="Number of days of history (default: 30, max: 365)",
    )
    async def paper_pnl(
        self,
        interaction: discord.Interaction,
        days: int = 30,
    ) -> None:
        """Show P/L chart with equity curve and daily bar chart."""
        await interaction.response.defer()

        engine = self._get_engine()
        if engine is None:
            await interaction.followup.send(
                "Paper trading engine not available.", ephemeral=True,
            )
            return

        days = max(1, min(365, days))

        try:
            equity_data = await engine.pnl_calculator.get_equity_curve(days=days)

            if not equity_data:
                await interaction.followup.send(
                    "No portfolio data available yet. Paper trading needs at least one daily snapshot.",
                    ephemeral=True,
                )
                return

            # Build summary embed
            latest = equity_data[-1] if equity_data else {}
            total_pnl = latest.get("total_equity", 0) - engine._config.starting_capital
            color = 0x00FF00 if total_pnl > 0 else 0xFF0000 if total_pnl < 0 else 0xFFFF00

            embed = discord.Embed(
                title=f"Paper Trading P/L -- {days} Days",
                description=f"Total P/L: ${total_pnl:+,.2f}",
                color=color,
                timestamp=datetime.now(timezone.utc),
            )

            # Daily stats
            daily_pnls = [d.get("daily_pnl", 0) for d in equity_data]
            win_days = sum(1 for p in daily_pnls if p > 0)
            loss_days = sum(1 for p in daily_pnls if p < 0)
            best_day = max(daily_pnls) if daily_pnls else 0
            worst_day = min(daily_pnls) if daily_pnls else 0
            avg_day = sum(daily_pnls) / len(daily_pnls) if daily_pnls else 0

            embed.add_field(
                name="Win/Loss Days", value=f"{win_days}W / {loss_days}L",
                inline=True,
            )
            embed.add_field(
                name="Best Day", value=f"${best_day:+,.2f}",
                inline=True,
            )
            embed.add_field(
                name="Worst Day", value=f"${worst_day:+,.2f}",
                inline=True,
            )
            embed.add_field(
                name="Avg Day", value=f"${avg_day:+,.2f}",
                inline=True,
            )
            embed.add_field(
                name="Max Drawdown",
                value=f"{latest.get('max_drawdown', 0):.2%}",
                inline=True,
            )
            embed.add_field(
                name="Current Equity",
                value=f"${latest.get('total_equity', 0):,.2f}",
                inline=True,
            )

            embed.set_footer(text="SPY Options Employee | Paper P/L")

            # Generate charts
            from src.discord_bot.charts import create_pnl_curve_chart

            files: list[discord.File] = []
            pnl_chart = create_pnl_curve_chart(equity_data)
            if pnl_chart is not None:
                embed.set_image(url=f"attachment://{pnl_chart.filename}")
                files.append(pnl_chart)

            if files:
                await interaction.followup.send(embed=embed, files=files)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as exc:
            logger.error("paper_pnl failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to generate P/L chart.", ephemeral=True,
            )

    # -- Background task: daily P/L auto-post ---------------------------------

    @tasks.loop(time=time(16, 15, tzinfo=ET))
    async def auto_paper_daily(self) -> None:
        """Auto-post paper trading daily summary at 16:15 ET.

        Posts to #paper-trading channel. Only fires on weekdays.
        Skips if already posted today (guard against task restart).
        """
        now = _now_et()
        # Skip weekends
        if now.weekday() >= 5:
            return

        # Skip if already posted today
        today_str = now.date().isoformat()
        if today_str == self._daily_posted_date:
            return

        engine = self._get_engine()
        if engine is None:
            return

        channel = self._get_paper_channel()
        if channel is None:
            return

        try:
            portfolio = await engine.get_portfolio_summary()

            # Skip if no activity (no trades and no open positions)
            if portfolio.total_trades == 0 and portfolio.open_positions == 0:
                return

            todays_trades = await self._get_todays_closed_trades(engine)

            from src.discord_bot.embeds import build_paper_daily_pnl_embed
            embed = build_paper_daily_pnl_embed(
                portfolio=portfolio,
                todays_trades=todays_trades,
                date_str=now.strftime("%b %d, %Y"),
            )

            # Attach P/L chart if we have enough data
            files: list[discord.File] = []
            try:
                equity_data = await engine.pnl_calculator.get_equity_curve(days=30)
                if len(equity_data) >= 2:
                    from src.discord_bot.charts import create_pnl_curve_chart
                    chart = create_pnl_curve_chart(equity_data)
                    if chart is not None:
                        embed.set_image(url=f"attachment://{chart.filename}")
                        files.append(chart)
            except Exception:
                pass  # Chart is optional -- send without it

            if files:
                await channel.send(embed=embed, files=files)
            else:
                await channel.send(embed=embed)

            self._daily_posted_date = today_str
            logger.info("Paper trading daily summary posted")

        except discord.HTTPException as exc:
            logger.error("Failed to post paper daily summary: %s", exc)
        except Exception as exc:
            logger.error("Paper daily summary error: %s", exc, exc_info=True)

    @auto_paper_daily.error
    async def on_paper_daily_error(self, error: Exception) -> None:
        """Log errors from the daily summary background task."""
        logger.error("Paper daily task error: %s", error, exc_info=error)

    @auto_paper_daily.before_loop
    async def before_paper_daily(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()

    # -- Alert methods (called by scheduler) ------------------------------------

    async def post_daily_pnl_alert(self, summary: Any) -> None:
        """Post an alert when daily PnL exceeds 2% of starting capital.

        Called by the scheduler during post-market processing.

        Args:
            summary: PortfolioSummary with daily_pnl and other fields.
        """
        channel = self._get_paper_channel()
        if channel is None:
            return

        try:
            pnl = summary.daily_pnl
            direction = "gain" if pnl > 0 else "loss"
            color = 0x00FF00 if pnl > 0 else 0xFF0000

            embed = discord.Embed(
                title=f"Paper Trading Alert: Significant Daily {direction.title()}",
                description=(
                    f"**Daily P/L: ${pnl:+,.2f}**\n"
                    f"Total Equity: ${summary.total_equity:,.2f}\n"
                    f"Open Positions: {summary.open_positions}\n"
                    f"Win Rate: {summary.win_rate:.1%}"
                ),
                color=color,
                timestamp=datetime.now(timezone.utc),
            )
            embed.set_footer(text="SPY Options Employee | Paper Trading Alert")
            await channel.send(embed=embed)
            logger.info("Paper PnL alert posted: $%.2f %s", pnl, direction)
        except discord.HTTPException as exc:
            logger.error("Failed to post paper PnL alert: %s", exc)
        except Exception as exc:
            logger.error("Paper PnL alert error: %s", exc, exc_info=True)

    # -- Fill notification (called by engine/scheduler) -----------------------

    async def post_fill_notification(
        self,
        order: dict,
        fills: list[dict],
        strategy_name: str,
    ) -> None:
        """Post a fill notification to the paper trading channel.

        Called by the scheduler cog or engine after a fill occurs.
        Not a slash command -- this is an internal notification method.

        Args:
            order: The filled order dict.
            fills: List of fill dicts for the order.
            strategy_name: Name of the strategy.
        """
        channel = self._get_paper_channel()
        if channel is None:
            return

        try:
            from src.discord_bot.embeds import build_paper_fill_alert_embed
            embed = build_paper_fill_alert_embed(
                order=order,
                fills=fills,
                strategy_name=strategy_name,
            )
            await channel.send(embed=embed)
        except discord.HTTPException as exc:
            logger.error("Failed to post fill notification: %s", exc)
        except Exception as exc:
            logger.error("Fill notification error: %s", exc, exc_info=True)


# -- Module setup function ---------------------------------------------------


async def setup(bot: commands.Bot) -> None:
    """Register the PaperTradingCog with the bot."""
    await bot.add_cog(PaperTradingCog(bot))
    logger.info("PaperTradingCog registered")
