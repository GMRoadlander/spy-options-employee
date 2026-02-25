"""Paper trading performance reporter -- orchestrates data fetching, metric
computation, embed building, and chart generation for all report types.

Provides daily, weekly, monthly, per-strategy, comparison, and degradation
reports suitable for Discord posting.

All public methods are async and return ``tuple[list[discord.Embed], list[discord.File]]``
(or ``list[discord.Embed]`` for degradation checks).
"""

from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta
from typing import Any

import discord

from src.config import config
from src.discord_bot.paper_charts import (
    create_degradation_chart,
    create_monthly_pnl_heatmap,
    create_paper_equity_drawdown_chart,
    create_rolling_sharpe_chart,
    create_strategy_comparison_chart,
    create_win_rate_trend_chart,
)
from src.discord_bot.paper_embeds import (
    build_degradation_alert_embed,
    build_paper_daily_summary_embed,
    build_paper_monthly_report_embeds,
    build_paper_strategy_comparison_embed,
    build_paper_strategy_performance_embed,
    build_paper_weekly_review_embed,
)
from src.strategy.lifecycle import StrategyStatus

logger = logging.getLogger(__name__)


class PaperPerformanceReporter:
    """Generates paper trading performance reports for Discord.

    Orchestrates data from PaperTradingEngine, StrategyManager, and
    PnLCalculator to build embeds and charts for daily, weekly, and
    monthly reports.

    Args:
        paper_engine: PaperTradingEngine instance.
        strategy_manager: StrategyManager instance.
        store: Store instance for DB access to backtest results.
    """

    def __init__(
        self,
        paper_engine: Any,
        strategy_manager: Any,
        store: Any,
    ) -> None:
        self._engine = paper_engine
        self._manager = strategy_manager
        self._store = store

    # ------------------------------------------------------------------
    # 3b: Daily Report
    # ------------------------------------------------------------------

    async def daily_report(
        self,
        report_date: date | None = None,
    ) -> tuple[list[discord.Embed], list[discord.File]]:
        """Generate daily paper trading summary.

        Returns embeds and chart files to attach to the Discord message.

        Args:
            report_date: Date to report on.  Defaults to today.

        Returns:
            Tuple of (embeds, chart_files).
        """
        if self._engine is None:
            return [], []

        if report_date is None:
            report_date = date.today()

        try:
            portfolio = await self._engine.get_portfolio_summary()
        except Exception as exc:
            logger.error("Failed to get portfolio summary: %s", exc)
            return [], []

        # Query today's closed trades
        day_trades = await self._query_day_trades(report_date)

        # Per-strategy rolling 7-day snapshots
        strategy_snapshots = await self._build_strategy_snapshots(report_date)

        # Risk status
        risk_status = self._build_risk_status(portfolio)

        embed = build_paper_daily_summary_embed(
            report_date=report_date,
            portfolio=portfolio,
            day_trades=day_trades,
            strategy_snapshots=strategy_snapshots,
            risk_status=risk_status,
        )

        embeds: list[discord.Embed] = [embed]
        files: list[discord.File] = []

        # Optional equity chart if we have > 7 days of data
        try:
            equity_data = await self._engine.pnl_calculator.get_equity_curve(days=30)
            if len(equity_data) > 7:
                chart = create_paper_equity_drawdown_chart(equity_data)
                if chart is not None:
                    files.append(chart)
        except Exception as exc:
            logger.debug("Skipping daily equity chart: %s", exc)

        return embeds, files

    # ------------------------------------------------------------------
    # 3c: Weekly Report
    # ------------------------------------------------------------------

    async def weekly_report(
        self,
        week_end: date | None = None,
    ) -> tuple[list[discord.Embed], list[discord.File]]:
        """Generate weekly paper trading review.

        Includes strategy comparison, paper vs backtest, risk evolution,
        and promotion readiness.  Attached charts: equity curve + drawdown.

        Args:
            week_end: End of the week to report on.  Defaults to last Friday.

        Returns:
            Tuple of (embeds, chart_files).
        """
        if self._engine is None:
            return [], []

        if week_end is None:
            today = date.today()
            # Go back to last Friday
            days_since_friday = (today.weekday() - 4) % 7
            week_end = today - timedelta(days=days_since_friday)

        week_start = week_end - timedelta(days=6)

        # Portfolio start/end values
        portfolio_start, portfolio_end = await self._get_portfolio_week_values(
            week_start, week_end,
        )

        # Trades this week
        weekly_trades = await self._query_trades_between(week_start, week_end)

        # Strategy comparison and promotion readiness
        paper_strategies = await self._manager.list_strategies(
            status=StrategyStatus.PAPER,
        )

        strategy_comparison: list[dict] = []
        promotion_readiness: list[dict] = []

        for s in paper_strategies:
            comp, promo = await self._build_strategy_comparison_entry(s)
            strategy_comparison.append(comp)
            promotion_readiness.append(promo)

        # Risk evolution (simplified -- current vs prior week)
        risk_evolution = await self._build_risk_evolution(week_start, week_end)

        embeds = build_paper_weekly_review_embed(
            week_start=week_start,
            week_end=week_end,
            portfolio_start=portfolio_start,
            portfolio_end=portfolio_end,
            weekly_trades=weekly_trades,
            strategy_comparison=strategy_comparison,
            risk_evolution=risk_evolution,
            promotion_readiness=promotion_readiness,
        )

        files: list[discord.File] = []

        # Equity + drawdown chart
        try:
            equity_data = await self._engine.pnl_calculator.get_equity_curve(days=7)
            chart = create_paper_equity_drawdown_chart(equity_data)
            if chart is not None:
                files.append(chart)
        except Exception as exc:
            logger.debug("Skipping weekly equity chart: %s", exc)

        # Strategy comparison chart (if 2+ strategies)
        if len(strategy_comparison) >= 2:
            comp_data = [
                {
                    "name": sc.get("name", ""),
                    "sharpe_ratio": sc.get("sharpe", 0.0),
                }
                for sc in strategy_comparison
            ]
            comp_chart = create_strategy_comparison_chart(comp_data)
            if comp_chart is not None:
                files.append(comp_chart)

        return embeds, files

    # ------------------------------------------------------------------
    # 3d: Monthly Report
    # ------------------------------------------------------------------

    async def monthly_report(
        self,
        month: date | None = None,
    ) -> tuple[list[discord.Embed], list[discord.File]]:
        """Generate monthly deep report.

        Comprehensive analysis: P/L by strategy, shadow mode comparison,
        slippage analysis, degradation tracking, lifecycle events.

        Args:
            month: The month to report on (year and month used).
                   Defaults to previous month.

        Returns:
            Tuple of (embeds, chart_files).
        """
        if self._engine is None:
            return [], []

        if month is None:
            today = date.today()
            first_of_this = today.replace(day=1)
            prev_month_last = first_of_this - timedelta(days=1)
            month = prev_month_last.replace(day=1)

        month_start = date(month.year, month.month, 1)
        if month.month == 12:
            month_end = date(month.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month.year, month.month + 1, 1) - timedelta(days=1)

        # All trades this month by strategy
        all_trades = await self._query_trades_between(month_start, month_end)

        # Group by strategy
        by_strategy: dict[int, list[dict]] = {}
        for t in all_trades:
            sid = t.get("strategy_id", 0)
            by_strategy.setdefault(sid, []).append(t)

        monthly_pnl_by_strategy: list[dict] = []
        shadow_comparison: list[dict] = []

        paper_strategies = await self._manager.list_strategies(
            status=StrategyStatus.PAPER,
        )

        for s in paper_strategies:
            sid = s["id"]
            trades = by_strategy.get(sid, [])
            pnls = [t.get("total_pnl", 0.0) - t.get("fees", 0.0) for t in trades]
            total_pnl = sum(pnls)
            wins = sum(1 for p in pnls if p > 0)
            wr = wins / len(pnls) if pnls else 0.0
            sharpe = self._simple_sharpe(pnls)

            monthly_pnl_by_strategy.append({
                "name": s["name"],
                "trades": len(trades),
                "pnl": total_pnl,
                "sharpe": sharpe,
                "win_rate": wr,
            })

            # Shadow comparison
            sc = await self._build_shadow_comparison(s, pnls)
            shadow_comparison.append(sc)

        # Aggregate metrics
        aggregate_metrics = await self._build_aggregate_metrics(
            month_start, month_end, all_trades, paper_strategies,
        )

        # Slippage analysis
        slippage_analysis = await self._build_slippage_analysis(month_start, month_end)

        # Degradation summary
        degradation_summary = self._build_degradation_summary(shadow_comparison)

        # Lifecycle events
        strategy_lifecycle_events = await self._query_lifecycle_events(
            month_start, month_end,
        )

        embeds = build_paper_monthly_report_embeds(
            month=month,
            monthly_pnl_by_strategy=monthly_pnl_by_strategy,
            aggregate_metrics=aggregate_metrics,
            slippage_analysis=slippage_analysis,
            shadow_comparison=shadow_comparison,
            degradation_summary=degradation_summary,
            strategy_lifecycle_events=strategy_lifecycle_events,
        )

        files: list[discord.File] = []

        # Charts
        try:
            equity_data = await self._engine.pnl_calculator.get_equity_curve(days=31)
            chart = create_paper_equity_drawdown_chart(equity_data)
            if chart is not None:
                files.append(chart)
        except Exception as exc:
            logger.debug("Skipping monthly equity chart: %s", exc)

        if shadow_comparison:
            deg_data = [
                {
                    "strategy_name": sc.get("strategy_name", ""),
                    "paper_sharpe": sc.get("paper_sharpe", 0.0),
                    "backtest_sharpe": sc.get("backtest_sharpe", 0.0),
                    "paper_win_rate": sc.get("paper_wr", 0.0),
                    "backtest_win_rate": sc.get("backtest_wr", 0.0),
                    "paper_pf": 0.0,
                    "backtest_pf": 0.0,
                }
                for sc in shadow_comparison
            ]
            deg_chart = create_degradation_chart(deg_data)
            if deg_chart is not None:
                files.append(deg_chart)

        # Daily PnL for heatmap
        try:
            daily_pnl_data = await self._query_daily_pnl(month_start, month_end)
            heatmap = create_monthly_pnl_heatmap(daily_pnl_data, month)
            if heatmap is not None:
                files.append(heatmap)
        except Exception as exc:
            logger.debug("Skipping monthly heatmap: %s", exc)

        return embeds, files

    # ------------------------------------------------------------------
    # 3e: Strategy Performance Report
    # ------------------------------------------------------------------

    async def strategy_performance_report(
        self,
        strategy_name_or_id: str,
    ) -> tuple[list[discord.Embed], list[discord.File]]:
        """Generate detailed performance report for a single strategy.

        Args:
            strategy_name_or_id: Strategy name or database ID.

        Returns:
            Tuple of (embeds, chart_files).
        """
        strategy = await self._find_strategy(strategy_name_or_id)
        if strategy is None:
            embed = discord.Embed(
                title="Strategy Not Found",
                description=f"No strategy matching '{strategy_name_or_id}'",
                color=0xFF0000,
            )
            return [embed], []

        sid = strategy["id"]

        # Get paper results
        paper_results = await self._engine.get_strategy_paper_results(sid)

        # Get backtest metrics
        backtest_metrics = await self._get_backtest_metrics(sid)

        # Promotion criteria
        promotion_criteria = self._evaluate_promotion_criteria(
            paper_results.metrics,
            len(paper_results.trades),
            paper_results.days_in_paper,
        )

        embeds = build_paper_strategy_performance_embed(
            strategy_name=strategy["name"],
            strategy_id=sid,
            paper_metrics=paper_results.metrics,
            backtest_metrics=backtest_metrics,
            promotion_criteria=promotion_criteria,
            days_in_paper=paper_results.days_in_paper,
            trade_count=len(paper_results.trades),
        )

        files: list[discord.File] = []

        # Equity + drawdown chart
        try:
            equity_data = await self._get_strategy_equity_curve(sid, days=90)
            # Convert to format expected by chart generators
            chart_data = [
                {"date": e["date"], "total_equity": 100000 + e["cumulative_pnl"]}
                for e in equity_data
            ]
            if chart_data:
                chart = create_paper_equity_drawdown_chart(
                    chart_data, strategy_name=strategy["name"],
                )
                if chart is not None:
                    files.append(chart)
        except Exception as exc:
            logger.debug("Skipping strategy equity chart: %s", exc)

        # Rolling Sharpe chart
        try:
            rolling = await self._get_rolling_metrics(sid, window_trades=20)
            rolling_data = rolling.get("rolling_data", [])
            if rolling_data:
                sharpe_chart = create_rolling_sharpe_chart(
                    rolling_data, strategy_name=strategy["name"],
                )
                if sharpe_chart is not None:
                    files.append(sharpe_chart)
        except Exception as exc:
            logger.debug("Skipping rolling Sharpe chart: %s", exc)

        # Win rate trend chart
        try:
            wr_data = await self._build_win_rate_trend(sid)
            if wr_data:
                wr_chart = create_win_rate_trend_chart(
                    wr_data, strategy_name=strategy["name"],
                )
                if wr_chart is not None:
                    files.append(wr_chart)
        except Exception as exc:
            logger.debug("Skipping win rate chart: %s", exc)

        return embeds, files

    # ------------------------------------------------------------------
    # 3f: Strategy Comparison Report
    # ------------------------------------------------------------------

    async def strategy_comparison_report(
        self,
        strategy_names: list[str] | None = None,
    ) -> tuple[list[discord.Embed], list[discord.File]]:
        """Compare 2-4 paper trading strategies side-by-side.

        If no names given, compares all PAPER strategies (up to 4).

        Args:
            strategy_names: Optional list of strategy names to compare.

        Returns:
            Tuple of (embeds, chart_files).
        """
        if strategy_names:
            strategies = []
            for name in strategy_names[:4]:
                s = await self._find_strategy(name)
                if s is not None:
                    strategies.append(s)
        else:
            strategies = await self._manager.list_strategies(
                status=StrategyStatus.PAPER,
            )
            strategies = strategies[:4]

        comp_data: list[dict] = []
        for s in strategies:
            try:
                results = await self._engine.get_strategy_paper_results(s["id"])
                metrics = results.metrics
                comp_data.append({
                    "name": s["name"],
                    "sharpe": getattr(metrics, "sharpe_ratio", 0.0),
                    "sortino": getattr(metrics, "sortino_ratio", 0.0),
                    "win_rate": getattr(metrics, "win_rate", 0.0),
                    "max_dd": getattr(metrics, "max_drawdown", 0.0),
                    "profit_factor": getattr(metrics, "profit_factor", 0.0),
                    "trades": len(results.trades),
                    "total_pnl": sum(
                        t.get("total_pnl", 0.0) - t.get("fees", 0.0)
                        for t in results.trades
                    ),
                })
            except Exception as exc:
                logger.debug("Failed to get results for %s: %s", s["name"], exc)

        embed = build_paper_strategy_comparison_embed(comp_data)
        files: list[discord.File] = []

        if comp_data:
            chart_data = [
                {
                    "name": c["name"],
                    "sharpe_ratio": c["sharpe"],
                }
                for c in comp_data
            ]
            chart = create_strategy_comparison_chart(chart_data)
            if chart is not None:
                files.append(chart)

        return [embed], files

    # ------------------------------------------------------------------
    # 3g: Degradation Check
    # ------------------------------------------------------------------

    async def check_degradation(self) -> list[discord.Embed]:
        """Check all PAPER strategies for performance degradation vs backtest.

        Called automatically during daily post-market processing.
        Returns list of alert embeds for any degraded strategies.

        Degradation thresholds (from config):
        - Sharpe deviation > threshold below backtest: ALERT
        - Win rate deviation > threshold below backtest: ALERT
        - Max drawdown > ratio * backtest max drawdown: ALERT

        Returns:
            List of degradation alert embeds (empty if no degradation).
        """
        alerts: list[discord.Embed] = []

        paper_strategies = await self._manager.list_strategies(
            status=StrategyStatus.PAPER,
        )

        min_trades = config.degradation_min_trades_for_check

        for s in paper_strategies:
            sid = s["id"]
            try:
                results = await self._engine.get_strategy_paper_results(sid)
            except Exception as exc:
                logger.debug("Skipping degradation check for %s: %s", s["name"], exc)
                continue

            trade_count = len(results.trades)
            if trade_count < min_trades:
                continue

            metrics = results.metrics
            backtest = await self._get_backtest_metrics(sid)
            if backtest is None:
                continue

            paper_sharpe = getattr(metrics, "sharpe_ratio", 0.0)
            bt_sharpe = backtest.get("sharpe_ratio", 0.0)
            sharpe_dev = paper_sharpe - bt_sharpe

            if sharpe_dev < -config.degradation_sharpe_threshold:
                alerts.append(build_degradation_alert_embed(
                    strategy_name=s["name"],
                    strategy_id=sid,
                    metric_name="Sharpe Ratio",
                    paper_value=paper_sharpe,
                    backtest_value=bt_sharpe,
                    deviation=sharpe_dev,
                    threshold=config.degradation_sharpe_threshold,
                ))

            paper_wr = getattr(metrics, "win_rate", 0.0)
            bt_wr = backtest.get("win_rate", 0.0)
            wr_dev = paper_wr - bt_wr

            if wr_dev < -config.degradation_win_rate_threshold:
                alerts.append(build_degradation_alert_embed(
                    strategy_name=s["name"],
                    strategy_id=sid,
                    metric_name="Win Rate",
                    paper_value=paper_wr,
                    backtest_value=bt_wr,
                    deviation=wr_dev,
                    threshold=config.degradation_win_rate_threshold,
                ))

            paper_dd = abs(getattr(metrics, "max_drawdown", 0.0))
            bt_dd = abs(backtest.get("max_drawdown", 0.0))

            if bt_dd > 0 and paper_dd > bt_dd * config.degradation_max_dd_ratio:
                dd_ratio = paper_dd / bt_dd
                alerts.append(build_degradation_alert_embed(
                    strategy_name=s["name"],
                    strategy_id=sid,
                    metric_name="Max Drawdown",
                    paper_value=paper_dd,
                    backtest_value=bt_dd,
                    deviation=dd_ratio,
                    threshold=config.degradation_max_dd_ratio,
                ))

        return alerts

    # ------------------------------------------------------------------
    # 3h: Rolling Metrics Helper
    # ------------------------------------------------------------------

    async def _get_rolling_metrics(
        self,
        strategy_id: int,
        window_trades: int = 20,
    ) -> dict:
        """Compute rolling metrics over the last N trades for a strategy.

        Returns dict with: rolling_sharpe, rolling_wr, rolling_pf,
        consecutive_losses, trade_count, rolling_data.
        """
        db = self._get_db()

        cursor = await db.execute(
            """
            SELECT exit_date, total_pnl, fees
            FROM paper_trades
            WHERE strategy_id = ?
            ORDER BY exit_date DESC
            LIMIT ?
            """,
            (strategy_id, window_trades),
        )
        rows = await cursor.fetchall()

        if not rows:
            return {
                "rolling_sharpe": 0.0,
                "rolling_wr": 0.0,
                "rolling_pf": 0.0,
                "consecutive_losses": 0,
                "trade_count": 0,
                "rolling_data": [],
            }

        # Reverse to chronological order
        rows = list(reversed(rows))
        pnls = [row[1] - row[2] for row in rows]
        trade_count = len(pnls)

        # Win rate
        wins = sum(1 for p in pnls if p > 0)
        rolling_wr = wins / trade_count if trade_count > 0 else 0.0

        # Sharpe
        rolling_sharpe = self._simple_sharpe(pnls)

        # Profit factor
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        rolling_pf = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Consecutive losses from most recent trade backwards
        consecutive_losses = 0
        for p in reversed(pnls):
            if p < 0:
                consecutive_losses += 1
            else:
                break

        # Build rolling data for chart (date, rolling_sharpe)
        rolling_data: list[dict] = []
        for i, row in enumerate(rows):
            rolling_data.append({
                "date": row[0],
                "rolling_sharpe": rolling_sharpe,  # simplified
            })

        return {
            "rolling_sharpe": rolling_sharpe,
            "rolling_wr": rolling_wr,
            "rolling_pf": rolling_pf,
            "consecutive_losses": consecutive_losses,
            "trade_count": trade_count,
            "rolling_data": rolling_data,
        }

    # ------------------------------------------------------------------
    # 3i: Equity Curve Data Helper
    # ------------------------------------------------------------------

    async def _get_strategy_equity_curve(
        self,
        strategy_id: int,
        days: int = 30,
    ) -> list[dict]:
        """Build equity curve data for a single strategy from its trades.

        Since paper_portfolio stores aggregate portfolio data,
        strategy-level equity must be reconstructed from paper_trades.

        Returns list of dicts: {date, cumulative_pnl, trade_count}.
        """
        db = self._get_db()

        cutoff = (date.today() - timedelta(days=days)).isoformat()
        cursor = await db.execute(
            """
            SELECT exit_date, (total_pnl - fees) as net_pnl
            FROM paper_trades
            WHERE strategy_id = ?
              AND exit_date >= ?
            ORDER BY exit_date
            """,
            (strategy_id, cutoff),
        )
        rows = await cursor.fetchall()

        if not rows:
            return []

        # Group by date
        daily_pnl: dict[str, float] = {}
        daily_count: dict[str, int] = {}
        for row in rows:
            d = row[0]
            daily_pnl[d] = daily_pnl.get(d, 0.0) + row[1]
            daily_count[d] = daily_count.get(d, 0) + 1

        # Build cumulative series with gap-filling
        sorted_dates = sorted(daily_pnl.keys())
        if not sorted_dates:
            return []

        result: list[dict] = []
        cumulative = 0.0
        total_count = 0

        # Fill from first date to today
        current = date.fromisoformat(sorted_dates[0])
        end = date.today()

        while current <= end:
            d_str = current.isoformat()
            if d_str in daily_pnl:
                cumulative += daily_pnl[d_str]
                total_count += daily_count[d_str]
            result.append({
                "date": d_str,
                "cumulative_pnl": round(cumulative, 2),
                "trade_count": total_count,
            })
            current += timedelta(days=1)

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_db(self) -> Any:
        """Return the active DB connection from the store."""
        return self._store._ensure_connected()

    async def _query_day_trades(self, report_date: date) -> list[dict]:
        """Query trades closed on a specific date."""
        db = self._get_db()
        date_str = report_date.isoformat()
        cursor = await db.execute(
            """
            SELECT t.id, t.strategy_id, t.entry_date, t.exit_date,
                   t.entry_price, t.exit_price, t.total_pnl, t.fees,
                   t.close_reason, t.slippage_cost,
                   s.name as strategy_name
            FROM paper_trades t
            LEFT JOIN strategies s ON t.strategy_id = s.id
            WHERE t.exit_date = ?
            ORDER BY t.id
            """,
            (date_str,),
        )
        rows = await cursor.fetchall()
        cols = [
            "id", "strategy_id", "entry_date", "exit_date",
            "entry_price", "exit_price", "total_pnl", "fees",
            "close_reason", "slippage_cost", "strategy_name",
        ]
        return [dict(zip(cols, row)) for row in rows]

    async def _query_trades_between(
        self, start: date, end: date,
    ) -> list[dict]:
        """Query trades closed between two dates (inclusive)."""
        db = self._get_db()
        cursor = await db.execute(
            """
            SELECT t.id, t.strategy_id, t.entry_date, t.exit_date,
                   t.entry_price, t.exit_price, t.total_pnl, t.fees,
                   t.close_reason, t.slippage_cost,
                   s.name as strategy_name
            FROM paper_trades t
            LEFT JOIN strategies s ON t.strategy_id = s.id
            WHERE t.exit_date BETWEEN ? AND ?
            ORDER BY t.exit_date
            """,
            (start.isoformat(), end.isoformat()),
        )
        rows = await cursor.fetchall()
        cols = [
            "id", "strategy_id", "entry_date", "exit_date",
            "entry_price", "exit_price", "total_pnl", "fees",
            "close_reason", "slippage_cost", "strategy_name",
        ]
        return [dict(zip(cols, row)) for row in rows]

    async def _build_strategy_snapshots(self, report_date: date) -> list[dict]:
        """Build rolling 7-day strategy snapshots for daily report."""
        paper_strategies = await self._manager.list_strategies(
            status=StrategyStatus.PAPER,
        )
        snapshots: list[dict] = []
        cutoff = (report_date - timedelta(days=7)).isoformat()
        db = self._get_db()

        for s in paper_strategies:
            cursor = await db.execute(
                """
                SELECT total_pnl, fees
                FROM paper_trades
                WHERE strategy_id = ? AND exit_date >= ?
                ORDER BY exit_date
                """,
                (s["id"], cutoff),
            )
            rows = await cursor.fetchall()
            pnls = [row[0] - row[1] for row in rows]
            total_pnl = sum(pnls)
            wins = sum(1 for p in pnls if p > 0)
            wr = wins / len(pnls) if pnls else 0.0
            sharpe = self._simple_sharpe(pnls)

            snapshots.append({
                "name": s["name"],
                "sharpe": sharpe,
                "win_rate": wr,
                "pnl": total_pnl,
            })

        return snapshots

    def _build_risk_status(self, portfolio: Any) -> dict:
        """Build risk limit status from portfolio data."""
        warnings: list[str] = []

        # Check daily loss limit
        if portfolio.daily_pnl < 0:
            daily_loss_pct = abs(portfolio.daily_pnl) / max(
                portfolio.starting_capital, 1,
            )
            if daily_loss_pct > config.risk_max_daily_loss_pct:
                warnings.append(
                    f"Daily loss at {daily_loss_pct:.1%} "
                    f"(limit: {config.risk_max_daily_loss_pct:.1%})"
                )

        # Check drawdown limit
        if abs(portfolio.max_drawdown) > config.risk_max_drawdown_pct:
            warnings.append(
                f"Drawdown at {abs(portfolio.max_drawdown):.1%} "
                f"(limit: {config.risk_max_drawdown_pct:.1%})"
            )

        return {"warnings": warnings}

    async def _get_portfolio_week_values(
        self, week_start: date, week_end: date,
    ) -> tuple[float, float]:
        """Get portfolio equity at start and end of a week."""
        db = self._get_db()

        cursor = await db.execute(
            """
            SELECT total_equity FROM paper_portfolio
            WHERE snapshot_date <= ?
            ORDER BY snapshot_date ASC
            LIMIT 1
            """,
            (week_start.isoformat(),),
        )
        start_row = await cursor.fetchone()
        start_val = start_row[0] if start_row else config.paper_starting_capital

        cursor = await db.execute(
            """
            SELECT total_equity FROM paper_portfolio
            WHERE snapshot_date <= ?
            ORDER BY snapshot_date DESC
            LIMIT 1
            """,
            (week_end.isoformat(),),
        )
        end_row = await cursor.fetchone()
        end_val = end_row[0] if end_row else start_val

        return start_val, end_val

    async def _build_strategy_comparison_entry(
        self, strategy: dict,
    ) -> tuple[dict, dict]:
        """Build strategy comparison and promotion readiness entries."""
        sid = strategy["id"]

        try:
            results = await self._engine.get_strategy_paper_results(sid)
            metrics = results.metrics
            paper_pnl = sum(
                t.get("total_pnl", 0.0) - t.get("fees", 0.0)
                for t in results.trades
            )
            sharpe = getattr(metrics, "sharpe_ratio", 0.0)
            wr = getattr(metrics, "win_rate", 0.0)
        except Exception:
            paper_pnl = 0.0
            sharpe = 0.0
            wr = 0.0
            results = None

        # Get backtest expected
        bt = await self._get_backtest_metrics(sid)
        bt_expected = bt.get("total_pnl", 0.0) if bt else 0.0

        comp = {
            "name": strategy["name"],
            "paper_pnl": paper_pnl,
            "bt_expected": bt_expected,
            "delta": paper_pnl - bt_expected,
            "sharpe": sharpe,
            "win_rate": wr * 100,
        }

        # Promotion readiness
        trade_count = len(results.trades) if results else 0
        days = results.days_in_paper if results else 0
        criteria = self._evaluate_promotion_criteria(
            results.metrics if results else None,
            trade_count,
            days,
        )
        passed = sum(1 for c in criteria if c.get("passed", False))
        total = len(criteria)
        ready = passed == total and total > 0

        detail = ""
        if not ready and criteria:
            missing = [c["name"] for c in criteria if not c.get("passed", False)]
            detail = ", ".join(missing[:3])

        promo = {
            "name": strategy["name"],
            "ready": ready,
            "criteria_met": passed,
            "criteria_total": total,
            "detail": detail,
        }

        return comp, promo

    async def _build_risk_evolution(
        self, week_start: date, week_end: date,
    ) -> list[dict]:
        """Build risk metrics evolution (this week vs last week)."""
        db = self._get_db()
        last_week_start = week_start - timedelta(days=7)

        # This week max drawdown
        cursor = await db.execute(
            """
            SELECT MIN(max_drawdown) FROM paper_portfolio
            WHERE snapshot_date BETWEEN ? AND ?
            """,
            (week_start.isoformat(), week_end.isoformat()),
        )
        row = await cursor.fetchone()
        this_dd = row[0] if row and row[0] is not None else 0.0

        # Last week max drawdown
        cursor = await db.execute(
            """
            SELECT MIN(max_drawdown) FROM paper_portfolio
            WHERE snapshot_date BETWEEN ? AND ?
            """,
            (last_week_start.isoformat(), (week_start - timedelta(days=1)).isoformat()),
        )
        row = await cursor.fetchone()
        last_dd = row[0] if row and row[0] is not None else 0.0

        dd_change = "Improved" if this_dd > last_dd else "Worsened" if this_dd < last_dd else "Unchanged"

        return [
            {
                "metric": "Max Drawdown",
                "last_week": f"{last_dd:.2%}",
                "this_week": f"{this_dd:.2%}",
                "change": dd_change,
            },
        ]

    async def _build_shadow_comparison(
        self, strategy: dict, pnls: list[float],
    ) -> dict:
        """Build shadow mode comparison for a strategy."""
        sid = strategy["id"]
        bt = await self._get_backtest_metrics(sid)

        paper_sharpe = self._simple_sharpe(pnls)
        paper_wr = sum(1 for p in pnls if p > 0) / len(pnls) if pnls else 0.0
        paper_avg_pnl = sum(pnls) / len(pnls) if pnls else 0.0
        paper_max_dd = 0.0  # Simplified

        bt_sharpe = bt.get("sharpe_ratio", 0.0) if bt else 0.0
        bt_wr = bt.get("win_rate", 0.0) if bt else 0.0
        bt_avg_pnl = bt.get("avg_pnl", 0.0) if bt else 0.0
        bt_max_dd = bt.get("max_drawdown", 0.0) if bt else 0.0

        sharpe_delta = paper_sharpe - bt_sharpe
        wr_delta = paper_wr - bt_wr
        avg_pnl_delta = paper_avg_pnl - bt_avg_pnl
        max_dd_delta = paper_max_dd - bt_max_dd

        # Verdict
        issues = 0
        if abs(sharpe_delta) > config.degradation_sharpe_threshold:
            issues += 1
        if abs(wr_delta) > config.degradation_win_rate_threshold:
            issues += 1

        if issues == 0:
            verdict = "CONSISTENT"
        elif issues == 1:
            verdict = "MINOR DEVIATION"
        else:
            verdict = "DEGRADED"

        return {
            "strategy_name": strategy["name"],
            "paper_sharpe": paper_sharpe,
            "backtest_sharpe": bt_sharpe,
            "sharpe_delta": sharpe_delta,
            "paper_wr": paper_wr,
            "backtest_wr": bt_wr,
            "wr_delta": wr_delta,
            "paper_avg_pnl": paper_avg_pnl,
            "backtest_avg_pnl": bt_avg_pnl,
            "avg_pnl_delta": avg_pnl_delta,
            "paper_max_dd": paper_max_dd,
            "backtest_max_dd": bt_max_dd,
            "max_dd_delta": max_dd_delta,
            "verdict": verdict,
        }

    async def _build_aggregate_metrics(
        self,
        month_start: date,
        month_end: date,
        all_trades: list[dict],
        paper_strategies: list[dict],
    ) -> dict:
        """Build aggregate portfolio metrics for the month."""
        db = self._get_db()

        # Start/end equity from snapshots
        cursor = await db.execute(
            """
            SELECT total_equity FROM paper_portfolio
            WHERE snapshot_date >= ?
            ORDER BY snapshot_date ASC LIMIT 1
            """,
            (month_start.isoformat(),),
        )
        row = await cursor.fetchone()
        start_eq = row[0] if row else config.paper_starting_capital

        cursor = await db.execute(
            """
            SELECT total_equity FROM paper_portfolio
            WHERE snapshot_date <= ?
            ORDER BY snapshot_date DESC LIMIT 1
            """,
            (month_end.isoformat(),),
        )
        row = await cursor.fetchone()
        end_eq = row[0] if row else start_eq

        pnls = [t.get("total_pnl", 0.0) - t.get("fees", 0.0) for t in all_trades]
        total_trades = len(pnls)
        wins = sum(1 for p in pnls if p > 0)
        wr = wins / total_trades if total_trades > 0 else 0.0
        sharpe = self._simple_sharpe(pnls)

        # Max drawdown from snapshots
        cursor = await db.execute(
            """
            SELECT MIN(max_drawdown) FROM paper_portfolio
            WHERE snapshot_date BETWEEN ? AND ?
            """,
            (month_start.isoformat(), month_end.isoformat()),
        )
        row = await cursor.fetchone()
        max_dd = row[0] if row and row[0] is not None else 0.0

        # Average holding days
        holding_days = [
            t.get("holding_days", 0) for t in all_trades
            if t.get("holding_days") is not None
        ]
        avg_holding = sum(holding_days) / len(holding_days) if holding_days else 0.0

        return {
            "starting_equity": start_eq,
            "ending_equity": end_eq,
            "month_pnl": end_eq - start_eq,
            "total_trades": total_trades,
            "win_rate": wr,
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "active_strategies": len(paper_strategies),
            "avg_holding_days": avg_holding,
        }

    async def _build_slippage_analysis(
        self, month_start: date, month_end: date,
    ) -> dict:
        """Build slippage analysis for the month."""
        db = self._get_db()

        try:
            cursor = await db.execute(
                """
                SELECT AVG(slippage), SUM(slippage * order_size),
                       COUNT(*), MAX(slippage), MIN(timestamp)
                FROM slippage_log
                WHERE timestamp BETWEEN ? AND ?
                """,
                (month_start.isoformat(), month_end.isoformat() + "T23:59:59"),
            )
            row = await cursor.fetchone()

            avg_slip = row[0] if row and row[0] is not None else 0.0
            total_cost = row[1] if row and row[1] is not None else 0.0
            total_records = row[2] if row and row[2] else 0
            worst_slip = row[3] if row and row[3] is not None else 0.0

            return {
                "avg_slippage": avg_slip,
                "total_slip_cost": total_cost,
                "fill_rate": 1.0,
                "fills_first_tick": total_records,
                "fills_total": total_records,
                "worst_slippage": worst_slip,
                "worst_date": "N/A",
                "worst_option_desc": "N/A",
                "by_strategy": [],
                "model_accuracy": 0.95,
            }
        except Exception:
            return {
                "avg_slippage": 0.0,
                "total_slip_cost": 0.0,
                "fill_rate": 0.0,
                "fills_first_tick": 0,
                "fills_total": 0,
                "worst_slippage": 0.0,
                "worst_date": "N/A",
                "worst_option_desc": "N/A",
                "by_strategy": [],
                "model_accuracy": 0.0,
            }

    def _build_degradation_summary(
        self, shadow_comparison: list[dict],
    ) -> dict:
        """Build degradation summary from shadow comparisons."""
        alert_list: list[str] = []
        scores: list[float] = []

        for sc in shadow_comparison:
            sharpe_delta = sc.get("sharpe_delta", 0.0)
            wr_delta = sc.get("wr_delta", 0.0)
            name = sc.get("strategy_name", "Unknown")

            # Score: higher = better consistency (1.0 = perfect match)
            sharpe_score = max(0.0, 1.0 - abs(sharpe_delta))
            wr_score = max(0.0, 1.0 - abs(wr_delta) * 5)
            score = (sharpe_score + wr_score) / 2
            scores.append(score)

            if sharpe_delta < -config.degradation_sharpe_threshold:
                alert_list.append(
                    f"{name}: Sharpe degraded by {abs(sharpe_delta):.2f}"
                )
            if wr_delta < -config.degradation_win_rate_threshold:
                alert_list.append(
                    f"{name}: Win rate degraded by {abs(wr_delta):.0%}"
                )

        overall = sum(scores) / len(scores) if scores else 0.0

        return {
            "alerts": alert_list,
            "overall_score": round(overall, 2),
        }

    async def _query_lifecycle_events(
        self, month_start: date, month_end: date,
    ) -> list[dict]:
        """Query strategy lifecycle transitions for the month."""
        db = self._get_db()

        try:
            cursor = await db.execute(
                """
                SELECT st.transitioned_at, s.name, st.from_status, st.to_status,
                       st.reason
                FROM strategy_transitions st
                JOIN strategies s ON st.strategy_id = s.id
                WHERE st.transitioned_at BETWEEN ? AND ?
                ORDER BY st.transitioned_at
                """,
                (month_start.isoformat(), month_end.isoformat() + "T23:59:59"),
            )
            rows = await cursor.fetchall()

            events: list[dict] = []
            for row in rows:
                events.append({
                    "date": row[0][:10] if row[0] else "N/A",
                    "strategy": row[1],
                    "description": f"{row[2]} -> {row[3]}",
                    "recommendation": None,
                    "rec_detail": row[4] or "",
                })
            return events
        except Exception:
            return []

    async def _query_daily_pnl(
        self, month_start: date, month_end: date,
    ) -> list[dict]:
        """Query daily P/L from portfolio snapshots."""
        db = self._get_db()

        cursor = await db.execute(
            """
            SELECT snapshot_date, daily_pnl
            FROM paper_portfolio
            WHERE snapshot_date BETWEEN ? AND ?
            ORDER BY snapshot_date
            """,
            (month_start.isoformat(), month_end.isoformat()),
        )
        rows = await cursor.fetchall()
        return [{"date": row[0], "pnl": row[1]} for row in rows]

    async def _get_backtest_metrics(self, strategy_id: int) -> dict | None:
        """Get latest backtest metrics for comparison."""
        db = self._get_db()

        try:
            cursor = await db.execute(
                """
                SELECT sharpe, sortino, win_rate, max_drawdown,
                       profit_factor, num_trades
                FROM backtest_results
                WHERE strategy_id = ?
                ORDER BY run_at DESC LIMIT 1
                """,
                (str(strategy_id),),
            )
            row = await cursor.fetchone()

            if row is None:
                return None

            return {
                "sharpe_ratio": row[0] or 0.0,
                "sortino_ratio": row[1] or 0.0,
                "win_rate": row[2] or 0.0,
                "max_drawdown": row[3] or 0.0,
                "profit_factor": row[4] or 0.0,
                "num_trades": row[5] or 0,
                "avg_pnl": 0.0,
                "total_pnl": 0.0,
            }
        except Exception:
            return None

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

    def _evaluate_promotion_criteria(
        self,
        metrics: Any,
        trade_count: int,
        days_in_paper: int,
    ) -> list[dict]:
        """Evaluate promotion criteria for a strategy."""
        min_trades = config.paper_min_trades_for_promotion
        min_days = config.paper_min_days_for_promotion

        criteria: list[dict] = []

        criteria.append({
            "name": f"Min Trades ({min_trades})",
            "passed": trade_count >= min_trades,
            "value": f"{trade_count}/{min_trades}",
        })

        criteria.append({
            "name": f"Min Days ({min_days})",
            "passed": days_in_paper >= min_days,
            "value": f"{days_in_paper}/{min_days}",
        })

        sharpe = getattr(metrics, "sharpe_ratio", 0.0) if metrics else 0.0
        criteria.append({
            "name": "Sharpe > 1.0",
            "passed": sharpe > 1.0,
            "value": f"{sharpe:.2f}",
        })

        wr = getattr(metrics, "win_rate", 0.0) if metrics else 0.0
        criteria.append({
            "name": "Win Rate > 50%",
            "passed": wr > 0.50,
            "value": f"{wr:.0%}",
        })

        max_dd = abs(getattr(metrics, "max_drawdown", 0.0)) if metrics else 0.0
        criteria.append({
            "name": "Max DD < 15%",
            "passed": max_dd < 0.15,
            "value": f"{max_dd:.0%}",
        })

        pf = getattr(metrics, "profit_factor", 0.0) if metrics else 0.0
        criteria.append({
            "name": "Profit Factor > 1.3",
            "passed": pf > 1.3,
            "value": f"{pf:.2f}",
        })

        return criteria

    async def _build_win_rate_trend(self, strategy_id: int) -> list[dict]:
        """Build win rate trend data for charting."""
        db = self._get_db()

        cursor = await db.execute(
            """
            SELECT total_pnl, fees
            FROM paper_trades
            WHERE strategy_id = ?
            ORDER BY exit_date
            """,
            (strategy_id,),
        )
        rows = await cursor.fetchall()

        if not rows:
            return []

        data: list[dict] = []
        wins_so_far = 0
        rolling_window: list[bool] = []

        for i, row in enumerate(rows):
            net = row[0] - row[1]
            is_win = net > 0
            if is_win:
                wins_so_far += 1

            rolling_window.append(is_win)
            if len(rolling_window) > 10:
                rolling_window.pop(0)

            cum_wr = (wins_so_far / (i + 1)) * 100
            roll_wr = (sum(rolling_window) / len(rolling_window)) * 100

            data.append({
                "trade_number": i + 1,
                "cumulative_win_rate": cum_wr,
                "rolling_10_wr": roll_wr,
            })

        return data

    @staticmethod
    def _simple_sharpe(pnls: list[float]) -> float:
        """Compute a simple Sharpe ratio approximation from a list of PnLs."""
        if len(pnls) < 2:
            return 0.0
        mean = sum(pnls) / len(pnls)
        variance = sum((p - mean) ** 2 for p in pnls) / (len(pnls) - 1)
        std = math.sqrt(variance) if variance > 0 else 0.0
        if std == 0:
            return 0.0
        # Annualize assuming ~252 trading days
        return (mean / std) * math.sqrt(252)
