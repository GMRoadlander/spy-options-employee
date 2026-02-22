"""Strategy performance reporting -- monthly deep reports and comparisons.

Provides:
    - Monthly deep report: strategy scoreboard, per-strategy breakdown,
      signal accuracy trends, hypothesis tracking, recommendations
    - Strategy comparison: side-by-side metrics for 2-4 strategies
    - Signal accuracy report: hit rates by source over a date range
"""

import json
import logging
from datetime import date, datetime
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
            timestamp=datetime.utcnow(),
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
            timestamp=datetime.utcnow(),
        )

        db = self._store._ensure_connected()

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
            timestamp=datetime.utcnow(),
        )

        db = self._store._ensure_connected()

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

    async def _build_scoreboard(self, month: date) -> discord.Embed:
        """Build strategy scoreboard embed ranked by Sharpe."""
        embed = discord.Embed(
            title="Strategy Scoreboard",
            description="All strategies ranked by Sharpe ratio",
            color=COLOR_INFO,
        )

        db = self._store._ensure_connected()

        # Get all strategies with their latest backtest results
        strategies = await self._manager.list_strategies()

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
                ranked.append({
                    "name": s["name"],
                    "status": s["status"],
                    "sharpe": row[0],
                    "sortino": row[1],
                    "win_rate": row[2],
                    "recommendation": row[3],
                    "trades": row[4],
                })

        # Sort by Sharpe descending
        ranked.sort(key=lambda x: x["sharpe"] or 0, reverse=True)

        if not ranked:
            embed.add_field(
                name="No Data", value="No strategies with backtest results",
                inline=False,
            )
        else:
            for i, r in enumerate(ranked[:10], 1):
                embed.add_field(
                    name=f"#{i} {r['name']} ({r['recommendation']})",
                    value=(
                        f"Sharpe: {r['sharpe']:.3f} | "
                        f"Sortino: {r['sortino']:.3f} | "
                        f"Win: {(r['win_rate'] or 0) * 100:.0f}% | "
                        f"Trades: {r['trades']}"
                    ),
                    inline=False,
                )

        embed.set_footer(text="SPY Options Employee | Scoreboard")
        return embed

    async def _build_signal_accuracy(self, month: date) -> discord.Embed:
        """Build signal accuracy embed for the month."""
        start = date(month.year, month.month, 1)
        # End of month
        if month.month == 12:
            end = date(month.year + 1, 1, 1)
        else:
            end = date(month.year, month.month + 1, 1)

        return await self.signal_accuracy_report(start, end)

    async def _build_recommendations(self, month: date) -> discord.Embed:
        """Build recommendations embed based on latest results."""
        embed = discord.Embed(
            title="Recommendations",
            description="Based on latest evaluation pipeline results",
            color=COLOR_INFO,
        )

        strategies = await self._manager.list_strategies()
        db = self._store._ensure_connected()

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
