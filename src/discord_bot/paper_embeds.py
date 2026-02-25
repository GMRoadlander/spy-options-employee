"""Discord embed builders for paper trading performance reports.

Builds rich embeds for daily summaries, weekly reviews, monthly deep reports,
strategy performance dashboards, degradation alerts, and strategy comparisons.

All functions return ``discord.Embed`` or ``list[discord.Embed]``.

Conventions (matching ``embeds.py``):
    - Color constants: COLOR_BULLISH, COLOR_BEARISH, COLOR_NEUTRAL, COLOR_INFO
    - Footer: "SPY Options Employee | {context}" with UTC timestamp
    - Text indicators: [PASS]/[FAIL], [OK]/[WARN] -- no emoji
    - Inline fields for compact metrics (3 per row)
    - Field values capped at 1024 chars
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

import discord

from src.discord_bot.embeds import (
    COLOR_BEARISH,
    COLOR_BULLISH,
    COLOR_INFO,
    COLOR_NEUTRAL,
    _fmt_number,
    _fmt_pct,
    _fmt_price,
)

logger = logging.getLogger(__name__)


def _truncate(text: str, limit: int = 1024) -> str:
    """Truncate text to fit within Discord field value limit."""
    if len(text) <= limit:
        return text
    return text[: limit - 20] + "\n... (truncated)"


# ---------------------------------------------------------------------------
# 1a: Daily Summary Embed
# ---------------------------------------------------------------------------


def build_paper_daily_summary_embed(
    report_date: date,
    portfolio: Any,  # PortfolioSummary
    day_trades: list[dict],
    strategy_snapshots: list[dict],
    risk_status: dict,
) -> discord.Embed:
    """Build a paper trading daily summary embed.

    Args:
        report_date: The date of the report.
        portfolio: PortfolioSummary dataclass from src.paper.models.
        day_trades: List of trade dicts closed today.
        strategy_snapshots: List of per-strategy rolling 7d metric dicts.
        risk_status: Dict with risk limit status information.

    Returns:
        Discord Embed with daily paper trading summary.
    """
    daily_pnl = portfolio.daily_pnl

    if daily_pnl > 0:
        color = COLOR_BULLISH
    elif daily_pnl < 0:
        color = COLOR_BEARISH
    else:
        color = COLOR_NEUTRAL

    embed = discord.Embed(
        title=f"Paper Trading Daily Summary -- {report_date}",
        description=(
            f"Portfolio: {_fmt_price(portfolio.total_equity)} | "
            f"Day P/L: {_fmt_price(daily_pnl)}"
        ),
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    # Day's Trades (inline=False)
    if day_trades:
        trade_lines: list[str] = []
        display_trades = day_trades[:8]
        for t in display_trades:
            time_str = str(t.get("exit_time", t.get("exit_date", "")))[:5]
            strategy = t.get("strategy_name", "Unknown")
            action = t.get("close_reason", "closed")
            option_desc = t.get("option_desc", "SPX")
            price = t.get("exit_price", 0.0)
            net_pnl = t.get("total_pnl", 0.0) - t.get("fees", 0.0)
            trade_lines.append(
                f"{time_str} {strategy} {action} {option_desc} "
                f"@ {_fmt_price(price)} P/L: ${net_pnl:+,.2f}"
            )
        if len(day_trades) > 8:
            trade_lines.append(f"...and {len(day_trades) - 8} more")
        embed.add_field(
            name="Day's Trades",
            value=_truncate("\n".join(trade_lines)),
            inline=False,
        )
    else:
        embed.add_field(
            name="Day's Trades",
            value="No trades closed today",
            inline=False,
        )

    # Open Positions (inline)
    embed.add_field(
        name="Open Positions",
        value=str(portfolio.open_positions),
        inline=True,
    )

    # Day P/L (inline)
    realized = sum(
        t.get("total_pnl", 0.0) - t.get("fees", 0.0) for t in day_trades
    )
    unrealized = portfolio.unrealized_pnl
    embed.add_field(
        name="Day P/L",
        value=f"${realized:+,.2f} realized + ${unrealized:+,.2f} unrealized",
        inline=True,
    )

    # Cumulative P/L (inline)
    cumulative = portfolio.total_equity - portfolio.starting_capital
    embed.add_field(
        name="Cumulative P/L",
        value=f"${cumulative:+,.2f}",
        inline=True,
    )

    # Strategy Snapshot (inline=False)
    if strategy_snapshots:
        snap_lines: list[str] = []
        for snap in strategy_snapshots:
            name = snap.get("name", "Unknown")
            sharpe = snap.get("sharpe", 0.0)
            win_rate = snap.get("win_rate", 0.0)
            pnl = snap.get("pnl", 0.0)
            snap_lines.append(
                f"{name}: Sharpe {sharpe:.2f} | WR {win_rate:.0%} | PnL ${pnl:+,.2f}"
            )
        embed.add_field(
            name="Strategy Snapshot",
            value=_truncate("\n".join(snap_lines)),
            inline=False,
        )

    # Risk Limits (inline)
    warnings = risk_status.get("warnings", [])
    if warnings:
        warn_text = "\n".join(f"[WARN] {w}" for w in warnings[:5])
        embed.add_field(name="Risk Limits", value=warn_text, inline=True)
    else:
        embed.add_field(name="Risk Limits", value="All [OK]", inline=True)

    embed.set_footer(text="SPY Options Employee | Paper Daily")
    return embed


# ---------------------------------------------------------------------------
# 1b: Weekly Review Embed
# ---------------------------------------------------------------------------


def build_paper_weekly_review_embed(
    week_start: date,
    week_end: date,
    portfolio_start: float,
    portfolio_end: float,
    weekly_trades: list[dict],
    strategy_comparison: list[dict],
    risk_evolution: list[dict],
    promotion_readiness: list[dict],
) -> list[discord.Embed]:
    """Build paper trading weekly review embeds.

    Returns 2 embeds to stay within character limits.

    Args:
        week_start: Start of the review week.
        week_end: End of the review week.
        portfolio_start: Portfolio value at week start.
        portfolio_end: Portfolio value at week end.
        weekly_trades: List of trade dicts for the week.
        strategy_comparison: List of per-strategy comparison dicts.
        risk_evolution: List of risk metric evolution dicts.
        promotion_readiness: List of promotion readiness dicts.

    Returns:
        List of 2 Discord Embeds.
    """
    embeds: list[discord.Embed] = []

    # -- Embed 1: Portfolio Performance --
    week_pnl = portfolio_end - portfolio_start
    week_pct = (week_pnl / portfolio_start * 100) if portfolio_start else 0.0

    total_trades = len(weekly_trades)
    wins = sum(
        1 for t in weekly_trades
        if (t.get("total_pnl", 0.0) - t.get("fees", 0.0)) > 0
    )
    losses = total_trades - wins
    win_rate = (wins / total_trades * 100) if total_trades else 0.0

    embed1 = discord.Embed(
        title=f"Paper Portfolio Weekly Review -- Week of {week_start}",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    summary_text = (
        f"Starting Value: {_fmt_price(portfolio_start)}\n"
        f"Ending Value:   {_fmt_price(portfolio_end)}\n"
        f"Week P/L:       ${week_pnl:+,.2f} ({week_pct:+.1f}%)\n"
        f"Trades:         {total_trades} ({wins} wins, {losses} losses)\n"
        f"Win Rate:       {win_rate:.1f}%"
    )
    embed1.add_field(name="Portfolio Summary", value=summary_text, inline=False)

    # Best / Worst / Avg trade
    if weekly_trades:
        net_pnls = [
            (t, t.get("total_pnl", 0.0) - t.get("fees", 0.0))
            for t in weekly_trades
        ]
        best_trade, best_pnl = max(net_pnls, key=lambda x: x[1])
        worst_trade, worst_pnl = min(net_pnls, key=lambda x: x[1])
        avg_pnl = sum(p for _, p in net_pnls) / len(net_pnls)

        embed1.add_field(
            name="Best Trade",
            value=(
                f"{best_trade.get('strategy_name', 'N/A')}\n"
                f"P/L: ${best_pnl:+,.2f}\n"
                f"Date: {best_trade.get('exit_date', 'N/A')}"
            ),
            inline=True,
        )
        embed1.add_field(
            name="Worst Trade",
            value=(
                f"{worst_trade.get('strategy_name', 'N/A')}\n"
                f"P/L: ${worst_pnl:+,.2f}\n"
                f"Date: {worst_trade.get('exit_date', 'N/A')}"
            ),
            inline=True,
        )
        embed1.add_field(
            name="Avg Trade P/L",
            value=f"${avg_pnl:+,.2f}",
            inline=True,
        )
    else:
        embed1.add_field(name="Best Trade", value="No trades", inline=True)
        embed1.add_field(name="Worst Trade", value="No trades", inline=True)
        embed1.add_field(name="Avg Trade P/L", value="$0.00", inline=True)

    embed1.set_footer(text="SPY Options Employee | Paper Weekly")
    embeds.append(embed1)

    # -- Embed 2: Strategy Comparison & Readiness --
    embed2 = discord.Embed(
        title="Strategy Comparison & Promotion Readiness",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    # Strategy Comparison Table
    if strategy_comparison:
        header = f"{'Strategy':<18} {'Paper PnL':>10} {'BT Expected':>12} {'Delta':>8} {'Sharpe':>7} {'WR':>5}"
        rows = [header]
        for sc in strategy_comparison:
            name = sc.get("name", "Unknown")[:18]
            paper_pnl = sc.get("paper_pnl", 0.0)
            bt_expected = sc.get("bt_expected", 0.0)
            delta = sc.get("delta", 0.0)
            sharpe = sc.get("sharpe", 0.0)
            wr = sc.get("win_rate", 0.0)
            rows.append(
                f"{name:<18} ${paper_pnl:>+8,.0f} ${bt_expected:>+10,.0f} "
                f"${delta:>+6,.0f} {sharpe:>6.2f} {wr:>4.0f}%"
            )
        embed2.add_field(
            name="Strategy Comparison Table",
            value=_truncate("```\n" + "\n".join(rows) + "\n```"),
            inline=False,
        )
    else:
        embed2.add_field(
            name="Strategy Comparison Table",
            value="No strategy data available",
            inline=False,
        )

    # Risk Metrics Evolution
    if risk_evolution:
        risk_header = f"{'Metric':<20} {'Last Week':>10} {'This Week':>10} {'Change':>10}"
        risk_rows = [risk_header]
        for rm in risk_evolution:
            metric = rm.get("metric", "Unknown")[:20]
            last_week = rm.get("last_week", "N/A")
            this_week = rm.get("this_week", "N/A")
            change = rm.get("change", "N/A")
            risk_rows.append(
                f"{metric:<20} {str(last_week):>10} {str(this_week):>10} {str(change):>10}"
            )
        embed2.add_field(
            name="Risk Metrics Evolution",
            value=_truncate("```\n" + "\n".join(risk_rows) + "\n```"),
            inline=False,
        )

    # Promotion Readiness
    if promotion_readiness:
        readiness_lines: list[str] = []
        for pr in promotion_readiness:
            name = pr.get("name", "Unknown")
            ready = pr.get("ready", False)
            criteria_met = pr.get("criteria_met", 0)
            criteria_total = pr.get("criteria_total", 6)
            detail = pr.get("detail", "")
            tag = "[READY]" if ready else "[NOT READY]"
            line = f"{tag} {name} -- {criteria_met}/{criteria_total} criteria met"
            if detail and not ready:
                line += f" ({detail})"
            readiness_lines.append(line)
        embed2.add_field(
            name="Promotion Readiness",
            value=_truncate("\n".join(readiness_lines)),
            inline=False,
        )

    embed2.set_footer(text="SPY Options Employee | Paper Weekly")
    embeds.append(embed2)

    return embeds


# ---------------------------------------------------------------------------
# 1c: Monthly Deep Report Embeds
# ---------------------------------------------------------------------------


def build_paper_monthly_report_embeds(
    month: date,
    monthly_pnl_by_strategy: list[dict],
    aggregate_metrics: dict,
    slippage_analysis: dict,
    shadow_comparison: list[dict],
    degradation_summary: dict,
    strategy_lifecycle_events: list[dict],
) -> list[discord.Embed]:
    """Build paper trading monthly deep report embeds.

    Returns 3-4 embeds depending on whether lifecycle events exist.

    Args:
        month: The month being reported on.
        monthly_pnl_by_strategy: Per-strategy PnL breakdown.
        aggregate_metrics: Aggregate portfolio metrics for the month.
        slippage_analysis: Slippage/execution quality metrics.
        shadow_comparison: Paper vs backtest comparison per strategy.
        degradation_summary: Overall degradation summary.
        strategy_lifecycle_events: Lifecycle events (promotions, resets, etc.).

    Returns:
        List of 3-4 Discord Embeds.
    """
    embeds: list[discord.Embed] = []
    month_name = month.strftime("%B %Y")

    # -- Embed 1: Monthly Overview --
    embed1 = discord.Embed(
        title=f"Paper Trading Monthly Report -- {month_name}",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    start_eq = aggregate_metrics.get("starting_equity", 0.0)
    end_eq = aggregate_metrics.get("ending_equity", 0.0)
    month_pnl = aggregate_metrics.get("month_pnl", end_eq - start_eq)
    month_pct = (month_pnl / start_eq * 100) if start_eq else 0.0
    total_trades = aggregate_metrics.get("total_trades", 0)
    wr = aggregate_metrics.get("win_rate", 0.0)
    sharpe = aggregate_metrics.get("sharpe", 0.0)
    max_dd = aggregate_metrics.get("max_drawdown", 0.0)

    perf_text = (
        f"Starting Equity:  {_fmt_price(start_eq)}\n"
        f"Ending Equity:    {_fmt_price(end_eq)}\n"
        f"Month P/L:        ${month_pnl:+,.2f} ({month_pct:+.1f}%)\n"
        f"Total Trades:     {total_trades}\n"
        f"Win Rate:         {wr:.1%}\n"
        f"Sharpe (monthly): {sharpe:.2f}\n"
        f"Max Drawdown:     {max_dd:.1%}"
    )
    embed1.add_field(name="Portfolio Performance", value=perf_text, inline=False)

    # P/L by Strategy
    if monthly_pnl_by_strategy:
        strat_header = f"{'Strategy':<18} {'Trades':>7} {'PnL':>10} {'Sharpe':>7} {'WR':>5}"
        strat_rows = [strat_header]
        for sp in monthly_pnl_by_strategy:
            sname = sp.get("name", "Unknown")[:18]
            strades = sp.get("trades", 0)
            spnl = sp.get("pnl", 0.0)
            ssharpe = sp.get("sharpe", 0.0)
            swr = sp.get("win_rate", 0.0)
            strat_rows.append(
                f"{sname:<18} {strades:>7} ${spnl:>+8,.0f} {ssharpe:>6.2f} {swr:>4.0%}"
            )
        embed1.add_field(
            name="P/L by Strategy",
            value=_truncate("```\n" + "\n".join(strat_rows) + "\n```"),
            inline=False,
        )

    embed1.add_field(
        name="Month Total",
        value=f"${month_pnl:+,.2f}",
        inline=True,
    )
    embed1.add_field(
        name="Active Strategies",
        value=str(aggregate_metrics.get("active_strategies", 0)),
        inline=True,
    )
    embed1.add_field(
        name="Avg Trade Duration",
        value=f"{aggregate_metrics.get('avg_holding_days', 0.0):.1f} days",
        inline=True,
    )

    embed1.set_footer(text="SPY Options Employee | Paper Monthly")
    embeds.append(embed1)

    # -- Embed 2: Shadow Mode & Degradation --
    embed2 = discord.Embed(
        title="Paper vs Backtest Comparison",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    for sc in shadow_comparison:
        sname = sc.get("strategy_name", "Unknown")
        metrics_table = (
            f"{'Metric':<14} {'Paper':>8} {'Backtest':>10} {'Delta':>8} {'Status':>8}\n"
            f"{'Sharpe':<14} {sc.get('paper_sharpe', 0.0):>8.2f} "
            f"{sc.get('backtest_sharpe', 0.0):>10.2f} "
            f"{sc.get('sharpe_delta', 0.0):>+8.2f} "
            f"{'[OK]' if abs(sc.get('sharpe_delta', 0.0)) < 0.5 else '[WARN]':>8}\n"
            f"{'Win Rate':<14} {sc.get('paper_wr', 0.0):>7.0%} "
            f"{sc.get('backtest_wr', 0.0):>9.0%} "
            f"{sc.get('wr_delta', 0.0):>+7.0%} "
            f"{'[OK]' if abs(sc.get('wr_delta', 0.0)) < 0.10 else '[WARN]':>8}\n"
            f"{'Avg PnL':<14} ${sc.get('paper_avg_pnl', 0.0):>7,.0f} "
            f"${sc.get('backtest_avg_pnl', 0.0):>9,.0f} "
            f"${sc.get('avg_pnl_delta', 0.0):>+7,.0f} "
            f"{'[OK]':>8}\n"
            f"{'Max DD':<14} {sc.get('paper_max_dd', 0.0):>7.0%} "
            f"{sc.get('backtest_max_dd', 0.0):>9.0%} "
            f"{sc.get('max_dd_delta', 0.0):>+7.0%} "
            f"{'[OK]' if sc.get('max_dd_delta', 0.0) < 0.05 else '[WARN]':>8}\n"
            f"Verdict: {sc.get('verdict', 'UNKNOWN')}"
        )
        embed2.add_field(
            name=sname,
            value=_truncate(f"```\n{metrics_table}\n```"),
            inline=False,
        )

    # Degradation Alerts
    alerts = degradation_summary.get("alerts", [])
    if alerts:
        alert_text = "\n".join(f"[WARN] {a}" for a in alerts[:5])
        embed2.add_field(
            name="Degradation Alerts",
            value=_truncate(alert_text),
            inline=False,
        )
    else:
        embed2.add_field(
            name="Degradation Alerts",
            value="No degradation detected",
            inline=False,
        )

    # Overall Shadow Score
    shadow_score = degradation_summary.get("overall_score", 0.0)
    embed2.add_field(
        name="Overall Shadow Score",
        value=f"{shadow_score:.2f}",
        inline=True,
    )

    embed2.set_footer(text="SPY Options Employee | Paper Monthly")
    embeds.append(embed2)

    # -- Embed 3: Slippage & Execution Quality --
    embed3 = discord.Embed(
        title="Execution Quality Analysis",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    avg_slip = slippage_analysis.get("avg_slippage", 0.0)
    total_slip_cost = slippage_analysis.get("total_slip_cost", 0.0)
    fill_rate = slippage_analysis.get("fill_rate", 0.0)
    fill_num = slippage_analysis.get("fills_first_tick", 0)
    fill_total = slippage_analysis.get("fills_total", 0)
    worst_slip = slippage_analysis.get("worst_slippage", 0.0)
    worst_date = slippage_analysis.get("worst_date", "N/A")
    worst_desc = slippage_analysis.get("worst_option_desc", "N/A")

    slip_text = (
        f"Avg Slippage:     ${avg_slip:.4f}/contract\n"
        f"Total Slip Cost:  ${total_slip_cost:,.2f}\n"
        f"Fill Rate:        {fill_rate:.0%} ({fill_num}/{fill_total} orders filled on first tick)\n"
        f"Worst Slippage:   ${worst_slip:.4f} on {worst_date} ({worst_desc})"
    )
    embed3.add_field(name="Slippage Summary", value=slip_text, inline=False)

    # Slippage by Strategy
    slip_by_strat = slippage_analysis.get("by_strategy", [])
    if slip_by_strat:
        strat_slip_lines: list[str] = []
        for ss in slip_by_strat:
            strat_slip_lines.append(
                f"{ss.get('name', 'Unknown')}: ${ss.get('avg_slippage', 0.0):.4f}/contract"
            )
        embed3.add_field(
            name="Slippage by Strategy",
            value=_truncate("\n".join(strat_slip_lines)),
            inline=False,
        )

    # Model Accuracy
    model_accuracy = slippage_analysis.get("model_accuracy", 0.0)
    embed3.add_field(
        name="Model Accuracy",
        value=f"{model_accuracy:.1%}",
        inline=True,
    )

    embed3.set_footer(text="SPY Options Employee | Paper Monthly")
    embeds.append(embed3)

    # -- Embed 4: Lifecycle & Recommendations (conditional) --
    if strategy_lifecycle_events:
        embed4 = discord.Embed(
            title="Strategy Lifecycle Events",
            color=COLOR_INFO,
            timestamp=datetime.now(timezone.utc),
        )

        event_lines: list[str] = []
        for event in strategy_lifecycle_events:
            evt_date = event.get("date", "N/A")
            evt_strategy = event.get("strategy", "Unknown")
            evt_desc = event.get("description", "")
            event_lines.append(f"{evt_date} {evt_strategy} {evt_desc}")
        embed4.add_field(
            name="Events This Month",
            value=_truncate("\n".join(event_lines)),
            inline=False,
        )

        recommendations = [
            e for e in strategy_lifecycle_events if e.get("recommendation")
        ]
        if recommendations:
            rec_lines: list[str] = []
            for r in recommendations:
                rec_tag = r.get("recommendation", "CONTINUE")
                rec_name = r.get("strategy", "Unknown")
                rec_detail = r.get("rec_detail", "")
                rec_lines.append(f"[{rec_tag}] {rec_name} -- {rec_detail}")
            embed4.add_field(
                name="Recommendations",
                value=_truncate("\n".join(rec_lines)),
                inline=False,
            )

        embed4.set_footer(text="SPY Options Employee | Paper Monthly")
        embeds.append(embed4)

    return embeds


# ---------------------------------------------------------------------------
# 1d: Strategy Performance Embed
# ---------------------------------------------------------------------------


def build_paper_strategy_performance_embed(
    strategy_name: str,
    strategy_id: int,
    paper_metrics: Any,  # StrategyMetrics or dict
    backtest_metrics: dict | None,
    promotion_criteria: list[dict],
    days_in_paper: int,
    trade_count: int,
) -> list[discord.Embed]:
    """Build strategy performance dashboard embeds.

    Returns 2 embeds: metrics dashboard and backtest comparison/promotion.

    Args:
        strategy_name: Name of the strategy.
        strategy_id: Database ID of the strategy.
        paper_metrics: Strategy metrics (dataclass or dict).
        backtest_metrics: Backtest metrics dict for comparison, or None.
        promotion_criteria: List of promotion criteria check dicts.
        days_in_paper: Number of days in PAPER status.
        trade_count: Total number of paper trades.

    Returns:
        List of 2 Discord Embeds.
    """
    embeds: list[discord.Embed] = []

    # Helper to get metric values from dataclass or dict
    def _get(obj: Any, key: str, default: float = 0.0) -> float:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # -- Embed 1: Metrics Dashboard --
    embed1 = discord.Embed(
        title=f"Paper Performance -- {strategy_name} (#{strategy_id})",
        description=f"Status: PAPER | {trade_count} trades | {days_in_paper} days",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    # Risk-Adjusted Returns (inline x3)
    embed1.add_field(
        name="Sharpe",
        value=f"{_get(paper_metrics, 'sharpe_ratio'):.3f}",
        inline=True,
    )
    embed1.add_field(
        name="Sortino",
        value=f"{_get(paper_metrics, 'sortino_ratio'):.3f}",
        inline=True,
    )
    embed1.add_field(
        name="Calmar",
        value=f"{_get(paper_metrics, 'calmar_ratio'):.3f}",
        inline=True,
    )

    # Trade Statistics (inline x3)
    embed1.add_field(
        name="Win Rate",
        value=f"{_get(paper_metrics, 'win_rate'):.1%}",
        inline=True,
    )
    embed1.add_field(
        name="Profit Factor",
        value=f"{_get(paper_metrics, 'profit_factor'):.2f}",
        inline=True,
    )
    embed1.add_field(
        name="Expectancy",
        value=f"${_get(paper_metrics, 'expectancy'):+,.2f}",
        inline=True,
    )

    # Drawdown (inline x3)
    embed1.add_field(
        name="Max DD",
        value=f"{_get(paper_metrics, 'max_drawdown'):.1%}",
        inline=True,
    )
    embed1.add_field(
        name="Max DD Duration",
        value=f"{_get(paper_metrics, 'max_drawdown_duration'):.0f} days",
        inline=True,
    )
    embed1.add_field(
        name="Avg DD",
        value=f"{_get(paper_metrics, 'avg_drawdown'):.1%}",
        inline=True,
    )

    # Trade Details (inline x3)
    embed1.add_field(
        name="Avg Win",
        value=f"${_get(paper_metrics, 'avg_win'):+,.2f}",
        inline=True,
    )
    embed1.add_field(
        name="Avg Loss",
        value=f"${_get(paper_metrics, 'avg_loss'):+,.2f}",
        inline=True,
    )
    embed1.add_field(
        name="Avg Holding Days",
        value=f"{_get(paper_metrics, 'avg_holding_days'):.1f}",
        inline=True,
    )

    # Distribution (inline x2)
    embed1.add_field(
        name="Skewness",
        value=f"{_get(paper_metrics, 'skewness'):.3f}",
        inline=True,
    )
    embed1.add_field(
        name="Kurtosis",
        value=f"{_get(paper_metrics, 'kurtosis'):.3f}",
        inline=True,
    )

    embed1.set_footer(text="SPY Options Employee | Paper Strategy")
    embeds.append(embed1)

    # -- Embed 2: Backtest Comparison & Promotion --

    # Determine color based on promotion criteria
    passed_count = sum(1 for pc in promotion_criteria if pc.get("passed", False))
    total_criteria = len(promotion_criteria) if promotion_criteria else 6
    if passed_count == total_criteria:
        color2 = COLOR_BULLISH
    elif passed_count >= 4:
        color2 = COLOR_NEUTRAL
    else:
        color2 = COLOR_BEARISH

    embed2 = discord.Embed(
        title=f"Backtest Comparison & Promotion -- {strategy_name}",
        color=color2,
        timestamp=datetime.now(timezone.utc),
    )

    # Shadow Comparison
    if backtest_metrics is not None:
        compare_header = f"{'Metric':<16} {'Paper':>8} {'Backtest':>10} {'Delta':>8}"
        compare_rows = [compare_header]

        paper_sharpe = _get(paper_metrics, "sharpe_ratio")
        bt_sharpe = backtest_metrics.get("sharpe_ratio", 0.0)
        compare_rows.append(
            f"{'Sharpe':<16} {paper_sharpe:>8.2f} {bt_sharpe:>10.2f} {paper_sharpe - bt_sharpe:>+8.2f}"
        )

        paper_wr = _get(paper_metrics, "win_rate")
        bt_wr = backtest_metrics.get("win_rate", 0.0)
        compare_rows.append(
            f"{'Win Rate':<16} {paper_wr:>7.0%} {bt_wr:>9.0%} {paper_wr - bt_wr:>+7.0%}"
        )

        paper_avg = _get(paper_metrics, "expectancy")
        bt_avg = backtest_metrics.get("avg_pnl", 0.0)
        compare_rows.append(
            f"{'Avg PnL':<16} ${paper_avg:>7,.0f} ${bt_avg:>9,.0f} ${paper_avg - bt_avg:>+7,.0f}"
        )

        paper_dd = _get(paper_metrics, "max_drawdown")
        bt_dd = backtest_metrics.get("max_drawdown", 0.0)
        compare_rows.append(
            f"{'Max DD':<16} {paper_dd:>7.0%} {bt_dd:>9.0%} {paper_dd - bt_dd:>+7.0%}"
        )

        paper_pf = _get(paper_metrics, "profit_factor")
        bt_pf = backtest_metrics.get("profit_factor", 0.0)
        compare_rows.append(
            f"{'Profit Factor':<16} {paper_pf:>8.1f} {bt_pf:>10.1f} {paper_pf - bt_pf:>+8.1f}"
        )

        embed2.add_field(
            name="Shadow Comparison",
            value=_truncate("```\n" + "\n".join(compare_rows) + "\n```"),
            inline=False,
        )
    else:
        embed2.add_field(
            name="Shadow Comparison",
            value="No backtest data available for comparison",
            inline=False,
        )

    # Promotion Criteria
    if promotion_criteria:
        criteria_lines: list[str] = []
        for pc in promotion_criteria:
            tag = "[PASS]" if pc.get("passed", False) else "[FAIL]"
            name = pc.get("name", "Unknown")
            value_str = pc.get("value", "N/A")
            criteria_lines.append(f"{tag} {name}: {value_str}")

        overall = "ELIGIBLE FOR PROMOTION" if passed_count == total_criteria else f"{passed_count}/{total_criteria} criteria met"
        criteria_lines.append(f"Overall: {overall}")

        embed2.add_field(
            name="Promotion Criteria",
            value=_truncate("\n".join(criteria_lines)),
            inline=False,
        )

    embed2.set_footer(text="SPY Options Employee | Paper Strategy")
    embeds.append(embed2)

    return embeds


# ---------------------------------------------------------------------------
# 1e: Degradation Alert Embed
# ---------------------------------------------------------------------------


def build_degradation_alert_embed(
    strategy_name: str,
    strategy_id: int,
    metric_name: str,
    paper_value: float,
    backtest_value: float,
    deviation: float,
    threshold: float,
) -> discord.Embed:
    """Build a performance degradation alert embed.

    Args:
        strategy_name: Name of the degraded strategy.
        strategy_id: Database ID of the strategy.
        metric_name: Name of the degraded metric.
        paper_value: Current paper trading value.
        backtest_value: Expected backtest value.
        deviation: Actual deviation from backtest.
        threshold: Threshold that was breached.

    Returns:
        Discord Embed with degradation alert.
    """
    embed = discord.Embed(
        title=f"ALERT: Performance Degradation -- {strategy_name}",
        color=COLOR_BEARISH,
        timestamp=datetime.now(timezone.utc),
    )

    degraded_text = (
        f"Metric: {metric_name}\n"
        f"Paper Value: {paper_value:.4f}\n"
        f"Backtest Expected: {backtest_value:.4f}\n"
        f"Deviation: {deviation:.4f} (threshold: {threshold:.4f})"
    )
    embed.add_field(name="Degraded Metric", value=degraded_text, inline=False)

    embed.add_field(
        name="Recommendation",
        value=(
            f"Review strategy #{strategy_id} ({strategy_name}). "
            f"Consider adjusting parameters or extending the paper trading "
            f"period to confirm whether degradation is persistent or transient."
        ),
        inline=False,
    )

    embed.set_footer(text=f"SPY Options Employee | Degradation Alert | #{strategy_id}")
    return embed


# ---------------------------------------------------------------------------
# 1f: Strategy Comparison Embed
# ---------------------------------------------------------------------------


def build_paper_strategy_comparison_embed(
    strategies: list[dict],
) -> discord.Embed:
    """Build a paper strategy comparison embed.

    Compares up to 4 strategies side-by-side with key metrics.

    Args:
        strategies: List of strategy metric dicts (max 4 displayed).

    Returns:
        Discord Embed with strategy comparison fields.
    """
    embed = discord.Embed(
        title="Paper Strategy Comparison",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    if not strategies:
        embed.add_field(
            name="No Strategies",
            value="No paper trading strategies to compare.",
            inline=False,
        )
        embed.set_footer(text="SPY Options Employee | Paper Comparison")
        return embed

    # Cap at 4 strategies (Discord field limits)
    display_strategies = strategies[:4]

    for strat in display_strategies:
        name = strat.get("name", "Unknown")
        sharpe = strat.get("sharpe", 0.0)
        sortino = strat.get("sortino", 0.0)
        wr = strat.get("win_rate", 0.0)
        max_dd = strat.get("max_dd", 0.0)
        pf = strat.get("profit_factor", 0.0)
        count = strat.get("trades", 0)
        total_pnl = strat.get("total_pnl", 0.0)

        value = (
            f"Sharpe: {sharpe:.2f}\n"
            f"Sortino: {sortino:.2f}\n"
            f"Win Rate: {wr:.0%}\n"
            f"Max DD: {max_dd:.1%}\n"
            f"Profit Factor: {pf:.2f}\n"
            f"Trades: {count}\n"
            f"PnL: ${total_pnl:+,.2f}"
        )
        embed.add_field(name=name, value=value, inline=True)

    embed.set_footer(text="SPY Options Employee | Paper Comparison")
    return embed
