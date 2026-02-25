"""Strategy performance reporting -- monthly deep reports and comparisons.

Provides:
    - Monthly deep report: strategy scoreboard, per-strategy breakdown,
      signal accuracy trends, hypothesis tracking, recommendations
    - Strategy comparison: side-by-side metrics for 2-4 strategies
    - Signal accuracy report: hit rates by source over a date range
"""

import logging
import math
from datetime import date, datetime, timedelta, timezone
from typing import Any

import discord

from src.discord_bot.embeds import (
    COLOR_BEARISH,
    COLOR_BULLISH,
    COLOR_INFO,
    COLOR_NEUTRAL,
)

logger = logging.getLogger(__name__)


class StrategyReporter:
    """Generates strategy performance reports for Discord.

    Args:
        store: Store instance for database access.
        strategy_manager: StrategyManager for strategy data.
    """

    def __init__(self, store: Any, strategy_manager: Any) -> None:
        self._store = store
        self._manager = strategy_manager

    async def monthly_report(self, month: date) -> list[discord.Embed]:
        """Generate monthly deep report as multi-embed Discord message.

        Contents:
        - Strategy scoreboard: all strategies ranked by Sharpe
        - Per-strategy breakdown: trades, metrics, gate results
        - Signal accuracy trends
        - Hypothesis tracking
        - Recommendations: which strategies to promote/retire

        Args:
            month: The month to report on (uses year and month).

        Returns:
            List of Discord Embeds.
        """
        embeds: list[discord.Embed] = []

        # Header
        month_str = month.strftime("%B %Y")
        header = discord.Embed(
            title=f"Monthly Report -- {month_str}",
            description="Strategy performance deep analysis",
            color=COLOR_INFO,
            timestamp=datetime.now(timezone.utc),
        )
        header.set_footer(text="SPY Options Employee | Monthly Report")
        embeds.append(header)

        # Strategy scoreboard
        scoreboard = await self._build_scoreboard(month)
        embeds.append(scoreboard)

        # Signal accuracy
        accuracy = await self._build_signal_accuracy(month)
        embeds.append(accuracy)

        # Recommendations
        recommendations = await self._build_recommendations(month)
        embeds.append(recommendations)

        # Paper trading summary (Phase 4+, graceful when table absent)
        paper_summary = await self._build_paper_summary(month)
        if paper_summary is not None:
            embeds.append(paper_summary)

        return embeds

    async def strategy_comparison(
        self,
        strategy_names: list[str],
    ) -> discord.Embed:
        """Side-by-side comparison of 2-4 strategies.

        Compares: Sharpe, Sortino, win rate, max DD, expectancy.

        Args:
            strategy_names: List of strategy names or IDs to compare.

        Returns:
            Discord Embed with comparison table.
        """
        embed = discord.Embed(
            title="Strategy Comparison",
            description=f"Comparing {len(strategy_names)} strategies",
            color=COLOR_INFO,
            timestamp=datetime.now(timezone.utc),
        )

        db = self._get_db()

        for name in strategy_names[:4]:
            # Find strategy
            strategy = await self._find_strategy(name)
            if strategy is None:
                embed.add_field(
                    name=name,
                    value="Strategy not found",
                    inline=True,
                )
                continue

            # Get latest backtest result
            cursor = await db.execute(
                """SELECT sharpe, sortino, win_rate, max_drawdown, profit_factor,
                          num_trades, recommendation
                   FROM backtest_results
                   WHERE strategy_id = ?
                   ORDER BY run_at DESC LIMIT 1""",
                (str(strategy["id"]),),
            )
            row = await cursor.fetchone()

            if row is None:
                embed.add_field(
                    name=strategy["name"],
                    value="No backtest results",
                    inline=True,
                )
                continue

            sharpe, sortino, win_rate, max_dd, pf, trades, rec = row
            embed.add_field(
                name=f"{strategy['name']} ({rec})",
                value=(
                    f"**Sharpe:** {sharpe:.3f}\n"
                    f"**Sortino:** {sortino:.3f}\n"
                    f"**Win Rate:** {(win_rate or 0) * 100:.1f}%\n"
                    f"**Max DD:** ${max_dd:,.2f}\n"
                    f"**Profit Factor:** {pf:.2f}\n"
                    f"**Trades:** {trades}"
                ),
                inline=True,
            )

        embed.set_footer(text="SPY Options Employee | Comparison")
        return embed

    async def signal_accuracy_report(
        self,
        start: date,
        end: date,
    ) -> discord.Embed:
        """Signal accuracy analysis over date range.

        Breaks down by source and shows hit rate, total signals.

        Args:
            start: Start date.
            end: End date.

        Returns:
            Discord Embed with signal accuracy data.
        """
        embed = discord.Embed(
            title=f"Signal Accuracy -- {start} to {end}",
            description="Signal performance analysis by source",
            color=COLOR_INFO,
            timestamp=datetime.now(timezone.utc),
        )

        db = self._get_db()

        # Get signals by source with outcomes
        cursor = await db.execute(
            """
            SELECT source, COUNT(*) as total,
                   SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins
            FROM signal_log
            WHERE timestamp >= ? AND timestamp <= ?
                  AND outcome IS NOT NULL
            GROUP BY source
            ORDER BY total DESC
            """,
            (
                datetime(start.year, start.month, start.day).isoformat(),
                datetime(end.year, end.month, end.day, 23, 59, 59).isoformat(),
            ),
        )
        rows = await cursor.fetchall()

        if not rows:
            embed.add_field(
                name="No Data",
                value="No signals with outcomes in this period",
                inline=False,
            )
        else:
            for source, total, wins in rows:
                hit_rate = wins / total if total > 0 else 0
                source_name = source or "Unknown"
                embed.add_field(
                    name=source_name,
                    value=(
                        f"Total: {total}\n"
                        f"Wins: {wins}\n"
                        f"Hit Rate: {hit_rate:.1%}"
                    ),
                    inline=True,
                )

        # Overall stats
        cursor = await db.execute(
            """
            SELECT COUNT(*), SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END)
            FROM signal_log
            WHERE timestamp >= ? AND timestamp <= ?
                  AND outcome IS NOT NULL
            """,
            (
                datetime(start.year, start.month, start.day).isoformat(),
                datetime(end.year, end.month, end.day, 23, 59, 59).isoformat(),
            ),
        )
        overall = await cursor.fetchone()
        if overall and overall[0] > 0:
            total_signals = overall[0]
            total_wins = overall[1] or 0
            embed.add_field(
                name="Overall",
                value=(
                    f"**Total:** {total_signals}\n"
                    f"**Wins:** {total_wins}\n"
                    f"**Hit Rate:** {total_wins / total_signals:.1%}"
                ),
                inline=False,
            )

        embed.set_footer(text="SPY Options Employee | Signal Accuracy")
        return embed

    # -- Internal helpers --------------------------------------------------

    def _get_db(self) -> "aiosqlite.Connection":
        """Return the active DB connection from the store, or raise RuntimeError."""
        try:
            return self._store._ensure_connected()
        except RuntimeError:
            logger.error("Store not connected when building report")
            raise

    async def _build_scoreboard(self, month: date) -> discord.Embed:
        """Build strategy scoreboard embed ranked by Sharpe."""
        embed = discord.Embed(
            title="Strategy Scoreboard",
            description="All strategies ranked by Sharpe ratio",
            color=COLOR_INFO,
        )

        db = self._get_db()

        # Get all strategies with their latest backtest results
        strategies = await self._manager.list_strategies()

        # Check if paper_trades table exists for paper metric enrichment
        paper_table_exists = False
        try:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='paper_trades'"
            )
            paper_table_exists = (await cursor.fetchone()) is not None
        except Exception:
            pass

        ranked = []
        for s in strategies:
            cursor = await db.execute(
                """SELECT sharpe, sortino, win_rate, recommendation, num_trades
                   FROM backtest_results
                   WHERE strategy_id = ?
                   ORDER BY run_at DESC LIMIT 1""",
                (str(s["id"]),),
            )
            row = await cursor.fetchone()
            if row:
                entry = {
                    "name": s["name"],
                    "status": s["status"],
                    "sharpe": row[0],
                    "sortino": row[1],
                    "win_rate": row[2],
                    "recommendation": row[3],
                    "trades": row[4],
                    "paper_trades": 0,
                    "paper_sharpe": None,
                }

                # Enrich with paper trading data if strategy is in PAPER status
                if s["status"] == "paper" and paper_table_exists:
                    try:
                        cursor = await db.execute(
                            "SELECT COUNT(*) FROM paper_trades WHERE strategy_id = ?",
                            (str(s["id"]),),
                        )
                        entry["paper_trades"] = (await cursor.fetchone())[0]

                        if entry["paper_trades"] >= 5:
                            cursor = await db.execute(
                                """SELECT (total_pnl - fees) FROM paper_trades
                                   WHERE strategy_id = ?
                                   ORDER BY exit_date""",
                                (str(s["id"]),),
                            )
                            pnl_rows = await cursor.fetchall()
                            pnls = [r[0] for r in pnl_rows if r[0] is not None]
                            if len(pnls) >= 2:
                                mean_pnl = sum(pnls) / len(pnls)
                                variance = sum((p - mean_pnl) ** 2 for p in pnls) / (len(pnls) - 1)
                                std_pnl = math.sqrt(variance) if variance > 0 else 0
                                if std_pnl > 0:
                                    entry["paper_sharpe"] = (mean_pnl / std_pnl) * math.sqrt(252)
                    except Exception:
                        pass  # Graceful fallback if paper_trades query fails

                ranked.append(entry)

        # Sort by Sharpe descending
        ranked.sort(key=lambda x: x["sharpe"] or 0, reverse=True)

        if not ranked:
            embed.add_field(
                name="No Data", value="No strategies with backtest results",
                inline=False,
            )
        else:
            for i, r in enumerate(ranked[:10], 1):
                value = (
                    f"Sharpe: {r['sharpe']:.3f} | "
                    f"Sortino: {r['sortino']:.3f} | "
                    f"Win: {(r['win_rate'] or 0) * 100:.0f}% | "
                    f"Trades: {r['trades']}"
                )
                if r.get("paper_trades", 0) > 0:
                    value += f" | Paper: {r['paper_trades']} trades"
                    if r.get("paper_sharpe") is not None:
                        value += f", Sharpe {r['paper_sharpe']:.2f}"
                embed.add_field(
                    name=f"#{i} {r['name']} ({r['recommendation']})",
                    value=value,
                    inline=False,
                )

        embed.set_footer(text="SPY Options Employee | Scoreboard")
        return embed

    async def _build_paper_summary(self, month: date) -> discord.Embed | None:
        """Build paper trading summary embed for the monthly report.

        Shows aggregate paper trading stats for the month:
        total trades, P/L, strategies active, slippage.
        Returns None if no paper trading data exists or the table
        has not been created yet (pre-Phase 4).
        """
        db = self._get_db()

        # Check if paper_trades table exists (may not exist pre-Phase 4)
        try:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='paper_trades'"
            )
            if not (await cursor.fetchone()):
                return None
        except Exception:
            return None

        # Month boundaries
        start = date(month.year, month.month, 1)
        if month.month == 12:
            end = date(month.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(month.year, month.month + 1, 1) - timedelta(days=1)

        # Aggregate stats
        cursor = await db.execute(
            """
            SELECT COUNT(*),
                   COALESCE(SUM(total_pnl - fees), 0),
                   COALESCE(SUM(CASE WHEN (total_pnl - fees) > 0 THEN 1 ELSE 0 END), 0),
                   COUNT(DISTINCT strategy_id)
            FROM paper_trades
            WHERE exit_date BETWEEN ? AND ?
            """,
            (start.isoformat(), end.isoformat()),
        )
        row = await cursor.fetchone()
        total_trades, total_pnl, wins, strategy_count = row

        if total_trades == 0:
            return None

        win_rate = wins / total_trades if total_trades > 0 else 0

        embed = discord.Embed(
            title="Paper Trading Summary",
            description=f"Paper trading activity for {month.strftime('%B %Y')}",
            color=COLOR_BULLISH if total_pnl > 0 else COLOR_BEARISH if total_pnl < 0 else COLOR_NEUTRAL,
            timestamp=datetime.now(timezone.utc),
        )

        embed.add_field(name="Total Trades", value=str(total_trades), inline=True)
        embed.add_field(name="Net P/L", value=f"${total_pnl:,.2f}", inline=True)
        embed.add_field(name="Win Rate", value=f"{win_rate:.1%}", inline=True)
        embed.add_field(name="Strategies Active", value=str(strategy_count), inline=True)

        # Slippage stats for the month
        cursor = await db.execute(
            """
            SELECT COALESCE(AVG(slippage), 0), COALESCE(SUM(slippage_cost), 0)
            FROM paper_trades
            WHERE exit_date BETWEEN ? AND ?
            """,
            (start.isoformat(), end.isoformat()),
        )
        slip_row = await cursor.fetchone()
        embed.add_field(name="Avg Slippage", value=f"${slip_row[0]:.4f}/contract", inline=True)
        embed.add_field(name="Total Slip Cost", value=f"${slip_row[1]:,.2f}", inline=True)

        embed.set_footer(text="SPY Options Employee | Paper Trading Summary")
        return embed

    async def _build_signal_accuracy(self, month: date) -> discord.Embed:
        """Build signal accuracy embed for the month."""
        start = date(month.year, month.month, 1)
        # End of month: first day of next month minus 1 day (C6: off-by-one fix)
        if month.month == 12:
            end = date(month.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(month.year, month.month + 1, 1) - timedelta(days=1)

        return await self.signal_accuracy_report(start, end)

    async def _build_recommendations(self, month: date) -> discord.Embed:
        """Build recommendations embed based on latest results."""
        embed = discord.Embed(
            title="Recommendations",
            description="Based on latest evaluation pipeline results",
            color=COLOR_INFO,
        )

        strategies = await self._manager.list_strategies()
        db = self._get_db()

        promote = []
        refine = []
        reject = []

        for s in strategies:
            if s["status"] == "retired":
                continue

            cursor = await db.execute(
                """SELECT recommendation FROM backtest_results
                   WHERE strategy_id = ?
                   ORDER BY run_at DESC LIMIT 1""",
                (str(s["id"]),),
            )
            row = await cursor.fetchone()
            if row:
                rec = row[0]
                if rec == "PROMOTE":
                    promote.append(s["name"])
                elif rec == "REFINE":
                    refine.append(s["name"])
                elif rec == "REJECT":
                    reject.append(s["name"])

        if promote:
            embed.add_field(
                name="[PROMOTE] Ready for Paper Trading",
                value="\n".join(f"  {n}" for n in promote),
                inline=False,
            )
        if refine:
            embed.add_field(
                name="[REFINE] Needs Adjustment",
                value="\n".join(f"  {n}" for n in refine),
                inline=False,
            )
        if reject:
            embed.add_field(
                name="[REJECT] Consider Retiring",
                value="\n".join(f"  {n}" for n in reject),
                inline=False,
            )

        if not promote and not refine and not reject:
            embed.add_field(
                name="No Recommendations",
                value="No strategies have been evaluated yet",
                inline=False,
            )

        embed.set_footer(text="SPY Options Employee | Recommendations")
        return embed

    async def _find_strategy(self, name_or_id: str) -> dict | None:
        """Find a strategy by name or ID."""
        try:
            sid = int(name_or_id)
            return await self._manager.get(sid)
        except (ValueError, TypeError):
            pass

        strategies = await self._manager.list_strategies()
        for s in strategies:
            if s["name"].lower() == name_or_id.lower():
                return s
        return None
