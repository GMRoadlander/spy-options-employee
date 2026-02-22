"""Strategy performance metric calculations.

Computes risk-adjusted returns, drawdown analysis, and trade statistics
from BacktestResult objects. All formulas use standard financial conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestResult


@dataclass
class StrategyMetrics:
    """Complete set of strategy evaluation metrics."""

    # Return metrics
    total_return: float = 0.0
    annual_return: float = 0.0
    monthly_returns: list[float] = field(default_factory=list)

    # Risk-adjusted
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Drawdown
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    avg_drawdown: float = 0.0

    # Trade stats
    num_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    expectancy: float = 0.0
    profit_factor: float = 0.0
    avg_holding_days: float = 0.0

    # Distribution
    skewness: float = 0.0
    kurtosis: float = 0.0

    # Regime-conditional
    sharpe_by_regime: dict[str, float] | None = None


def calculate_metrics(
    result: BacktestResult,
    risk_free_rate: float = 0.05,
) -> StrategyMetrics:
    """Calculate all metrics from a BacktestResult.

    Args:
        result: Backtest output with daily_returns and trade_log.
        risk_free_rate: Annual risk-free rate (default 5%).

    Returns:
        StrategyMetrics with all fields populated.
    """
    metrics = StrategyMetrics()
    metrics.num_trades = result.num_trades

    if result.num_trades == 0:
        return metrics

    # --- Return metrics ---
    daily_returns = result.daily_returns
    metrics.total_return = result.total_return

    if len(daily_returns) > 0:
        trading_days = len(daily_returns)
        years = trading_days / 252.0

        if years > 0:
            metrics.annual_return = metrics.total_return / years

        # Monthly returns
        if hasattr(daily_returns.index, 'to_period'):
            monthly = daily_returns.resample("ME").sum()
            metrics.monthly_returns = monthly.tolist()

    # --- Risk-adjusted metrics ---
    if len(daily_returns) > 1:
        daily_rf = risk_free_rate / 252.0
        excess = daily_returns - daily_rf
        std = daily_returns.std()

        # Sharpe ratio (annualized)
        if std > 0:
            metrics.sharpe_ratio = (excess.mean() / std) * np.sqrt(252)
        else:
            metrics.sharpe_ratio = float("inf") if excess.mean() > 0 else 0.0

        # Sortino ratio (annualized)
        downside = daily_returns[daily_returns < 0]
        if len(downside) > 0:
            downside_std = downside.std()
            if downside_std > 0:
                metrics.sortino_ratio = (excess.mean() / downside_std) * np.sqrt(252)
        elif excess.mean() > 0:
            metrics.sortino_ratio = float("inf")

        # Distribution
        metrics.skewness = float(daily_returns.skew()) if len(daily_returns) > 2 else 0.0
        metrics.kurtosis = float(daily_returns.kurtosis()) if len(daily_returns) > 3 else 0.0

    # --- Drawdown analysis ---
    if len(daily_returns) > 0:
        cumulative = daily_returns.cumsum()
        running_max = cumulative.cummax()
        drawdown = cumulative - running_max

        metrics.max_drawdown = float(drawdown.min()) if len(drawdown) > 0 else 0.0

        # Drawdown duration (business days in worst drawdown)
        if metrics.max_drawdown < 0:
            in_dd = drawdown < 0
            dd_groups = (~in_dd).cumsum()
            if in_dd.any():
                dd_lengths = in_dd.groupby(dd_groups).sum()
                dd_lengths = dd_lengths[dd_lengths > 0]
                metrics.max_drawdown_duration = int(dd_lengths.max()) if len(dd_lengths) > 0 else 0

            dd_values = drawdown[drawdown < 0]
            metrics.avg_drawdown = float(dd_values.mean()) if len(dd_values) > 0 else 0.0

        # Calmar ratio
        if metrics.max_drawdown < 0:
            metrics.calmar_ratio = metrics.annual_return / abs(metrics.max_drawdown)

    # --- Trade statistics ---
    if not result.trade_log.empty and "pnl" in result.trade_log.columns:
        pnls = result.trade_log["pnl"]

        winners = pnls[pnls > 0]
        losers = pnls[pnls < 0]

        metrics.win_rate = len(winners) / len(pnls) if len(pnls) > 0 else 0.0
        metrics.avg_win = float(winners.mean()) if len(winners) > 0 else 0.0
        metrics.avg_loss = float(losers.mean()) if len(losers) > 0 else 0.0

        # Expectancy: (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        metrics.expectancy = (metrics.win_rate * metrics.avg_win) + \
                             ((1 - metrics.win_rate) * metrics.avg_loss)

        # Profit factor: gross profits / |gross losses|
        gross_profit = float(winners.sum()) if len(winners) > 0 else 0.0
        gross_loss = float(losers.sum()) if len(losers) > 0 else 0.0
        if gross_loss < 0:
            metrics.profit_factor = gross_profit / abs(gross_loss)
        elif gross_profit > 0:
            metrics.profit_factor = float("inf")

        # Average holding days
        if "entry_date" in result.trade_log.columns and "exit_date" in result.trade_log.columns:
            holding = (
                pd.to_datetime(result.trade_log["exit_date"]) -
                pd.to_datetime(result.trade_log["entry_date"])
            ).dt.days
            metrics.avg_holding_days = float(holding.mean())

    return metrics


def format_metrics_report(metrics: StrategyMetrics) -> str:
    """Format metrics as a human-readable text report for Discord.

    Args:
        metrics: Calculated strategy metrics.

    Returns:
        Formatted multi-line string.
    """
    lines = [
        "**Strategy Performance Report**",
        "",
        f"Trades: {metrics.num_trades}",
        f"Total Return: ${metrics.total_return:,.2f}",
        f"Annual Return: ${metrics.annual_return:,.2f}",
        "",
        "**Risk-Adjusted**",
        f"Sharpe: {metrics.sharpe_ratio:.3f}",
        f"Sortino: {metrics.sortino_ratio:.3f}",
        f"Calmar: {metrics.calmar_ratio:.3f}",
        "",
        "**Drawdown**",
        f"Max DD: ${metrics.max_drawdown:,.2f}",
        f"Max DD Duration: {metrics.max_drawdown_duration} days",
        "",
        "**Trade Stats**",
        f"Win Rate: {metrics.win_rate:.1%}",
        f"Avg Win: ${metrics.avg_win:,.2f}",
        f"Avg Loss: ${metrics.avg_loss:,.2f}",
        f"Expectancy: ${metrics.expectancy:,.2f}",
        f"Profit Factor: {metrics.profit_factor:.2f}",
        f"Avg Holding: {metrics.avg_holding_days:.1f} days",
    ]
    return "\n".join(lines)
