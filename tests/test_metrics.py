"""Tests for strategy evaluation metrics."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import BacktestResult
from src.backtest.metrics import (
    StrategyMetrics,
    calculate_metrics,
    format_metrics_report,
)


def _make_result(
    daily_returns: list[float] | None = None,
    trade_pnls: list[float] | None = None,
    entry_dates: list[date] | None = None,
    exit_dates: list[date] | None = None,
    num_trades: int | None = None,
) -> BacktestResult:
    """Build a BacktestResult from raw P&L data."""
    if daily_returns is None:
        daily_returns = [1.0, -0.5, 0.8, -0.3, 0.6]

    idx = pd.bdate_range(start="2024-01-02", periods=len(daily_returns))
    daily_series = pd.Series(daily_returns, index=idx, dtype=float)

    if trade_pnls is None:
        trade_pnls = [1.0, -0.5, 0.8, -0.3, 0.6]

    n = len(trade_pnls)
    if entry_dates is None:
        entry_dates = [date(2024, 1, 2 + i) for i in range(n)]
    if exit_dates is None:
        exit_dates = [date(2024, 1, 12 + i) for i in range(n)]

    trade_log = pd.DataFrame({
        "entry_date": entry_dates[:n],
        "exit_date": exit_dates[:n],
        "pnl": trade_pnls,
        "entry_credit": trade_pnls,
    })

    return BacktestResult(
        strategy_name="Test",
        strategy_id="test-1",
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 31),
        num_trades=num_trades if num_trades is not None else n,
        total_return=sum(trade_pnls),
        daily_returns=daily_series,
        trade_log=trade_log,
        raw_data=pd.DataFrame(),
    )


class TestSharpeRatio:
    """Test Sharpe ratio calculation."""

    def test_positive_sharpe(self):
        # Consistently positive returns
        result = _make_result(daily_returns=[1.0] * 100, trade_pnls=[1.0] * 10)
        metrics = calculate_metrics(result)
        assert metrics.sharpe_ratio > 0

    def test_constant_returns_high_sharpe(self):
        # Constant positive returns → very high Sharpe (low std)
        result = _make_result(daily_returns=[0.01] * 252, trade_pnls=[0.01] * 10)
        metrics = calculate_metrics(result)
        assert metrics.sharpe_ratio > 10  # effectively infinite

    def test_negative_returns_negative_sharpe(self):
        # Varying negative returns (constant would have std=0)
        rets = [-1.0 + 0.1 * (i % 5) for i in range(100)]
        result = _make_result(daily_returns=rets, trade_pnls=[-1.0] * 10)
        metrics = calculate_metrics(result)
        assert metrics.sharpe_ratio < 0

    def test_zero_returns(self):
        result = _make_result(daily_returns=[0.0] * 50, trade_pnls=[0.0] * 5)
        metrics = calculate_metrics(result)
        # Zero std → 0 or special case
        assert metrics.sharpe_ratio <= 0


class TestSortinoRatio:
    """Test Sortino ratio calculation."""

    def test_all_positive_returns_infinite_sortino(self):
        result = _make_result(daily_returns=[1.0] * 100, trade_pnls=[1.0] * 10)
        metrics = calculate_metrics(result)
        assert metrics.sortino_ratio == float("inf")

    def test_mixed_returns_finite_sortino(self):
        result = _make_result(daily_returns=[1.0, -0.5, 0.8, -0.3] * 25)
        metrics = calculate_metrics(result)
        assert np.isfinite(metrics.sortino_ratio)


class TestDrawdown:
    """Test drawdown calculations."""

    def test_known_max_drawdown(self):
        # Sequence: +10, -15, +5 → cumulative: 10, -5, 0
        # running_max: 10, 10, 10 → drawdown: 0, -15, -10
        result = _make_result(daily_returns=[10.0, -15.0, 5.0])
        metrics = calculate_metrics(result)
        assert metrics.max_drawdown == pytest.approx(-15.0)

    def test_no_drawdown_all_positive(self):
        result = _make_result(daily_returns=[1.0, 2.0, 3.0])
        metrics = calculate_metrics(result)
        assert metrics.max_drawdown == 0.0

    def test_drawdown_duration(self):
        # Create a sequence with a clear drawdown period
        returns = [1.0] * 10 + [-0.5] * 5 + [1.0] * 10
        result = _make_result(daily_returns=returns)
        metrics = calculate_metrics(result)
        assert metrics.max_drawdown_duration > 0


class TestTradeStats:
    """Test trade-level statistics."""

    def test_win_rate(self):
        result = _make_result(trade_pnls=[1.0, 1.0, -0.5, 1.0, -0.3])
        metrics = calculate_metrics(result)
        assert metrics.win_rate == pytest.approx(3 / 5)

    def test_all_winners(self):
        result = _make_result(trade_pnls=[1.0, 2.0, 3.0])
        metrics = calculate_metrics(result)
        assert metrics.win_rate == 1.0
        assert metrics.avg_loss == 0.0

    def test_all_losers(self):
        result = _make_result(trade_pnls=[-1.0, -2.0, -3.0])
        metrics = calculate_metrics(result)
        assert metrics.win_rate == 0.0
        assert metrics.avg_win == 0.0

    def test_avg_win_avg_loss(self):
        result = _make_result(trade_pnls=[4.0, 2.0, -1.0, -3.0])
        metrics = calculate_metrics(result)
        assert metrics.avg_win == pytest.approx(3.0)  # (4+2)/2
        assert metrics.avg_loss == pytest.approx(-2.0)  # (-1+-3)/2

    def test_expectancy(self):
        # win_rate=0.5, avg_win=2.0, avg_loss=-1.0
        result = _make_result(trade_pnls=[2.0, -1.0, 2.0, -1.0])
        metrics = calculate_metrics(result)
        expected = (0.5 * 2.0) + (0.5 * -1.0)  # 0.5
        assert metrics.expectancy == pytest.approx(expected)

    def test_profit_factor(self):
        result = _make_result(trade_pnls=[3.0, 1.0, -2.0])
        metrics = calculate_metrics(result)
        # gross profit = 4, gross loss = 2
        assert metrics.profit_factor == pytest.approx(2.0)

    def test_profit_factor_no_losses(self):
        result = _make_result(trade_pnls=[1.0, 2.0])
        metrics = calculate_metrics(result)
        assert metrics.profit_factor == float("inf")

    def test_single_trade(self):
        result = _make_result(trade_pnls=[5.0], num_trades=1)
        metrics = calculate_metrics(result)
        assert metrics.num_trades == 1
        assert metrics.win_rate == 1.0

    def test_holding_days(self):
        result = _make_result(
            trade_pnls=[1.0, 2.0],
            entry_dates=[date(2024, 1, 2), date(2024, 1, 5)],
            exit_dates=[date(2024, 1, 12), date(2024, 1, 15)],
        )
        metrics = calculate_metrics(result)
        assert metrics.avg_holding_days == 10.0  # (10+10)/2


class TestNoTrades:
    """Test metrics with no trades."""

    def test_zero_trades(self):
        result = BacktestResult(
            strategy_name="Empty",
            strategy_id="empty",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            num_trades=0,
            total_return=0.0,
            daily_returns=pd.Series(dtype=float),
            trade_log=pd.DataFrame(),
            raw_data=pd.DataFrame(),
        )
        metrics = calculate_metrics(result)
        assert metrics.num_trades == 0
        assert metrics.sharpe_ratio == 0.0
        assert metrics.win_rate == 0.0


class TestDistribution:
    """Test return distribution metrics."""

    def test_skewness_negative_for_short_premium(self):
        # Short premium: many small wins, few large losses
        np.random.seed(42)
        wins = [0.5] * 80
        losses = [-3.0] * 20
        rets = wins + losses
        np.random.shuffle(rets)
        result = _make_result(daily_returns=rets)
        metrics = calculate_metrics(result)
        assert metrics.skewness < 0  # negatively skewed

    def test_kurtosis_high_for_fat_tails(self):
        np.random.seed(42)
        # Normal + fat tail events
        rets = list(np.random.normal(0, 1, 100)) + [10.0, -10.0]
        result = _make_result(daily_returns=rets)
        metrics = calculate_metrics(result)
        assert metrics.kurtosis > 0  # excess kurtosis (leptokurtic)


class TestCalmarRatio:
    """Test Calmar ratio calculation."""

    def test_calmar_positive(self):
        returns = [1.0] * 50 + [-2.0] + [1.0] * 50
        result = _make_result(daily_returns=returns)
        metrics = calculate_metrics(result)
        if metrics.max_drawdown < 0:
            assert metrics.calmar_ratio > 0


class TestFormatReport:
    """Test report formatting."""

    def test_format_returns_string(self):
        metrics = StrategyMetrics(
            num_trades=10,
            total_return=1500.0,
            sharpe_ratio=1.5,
            win_rate=0.65,
        )
        report = format_metrics_report(metrics)
        assert "Trades: 10" in report
        assert "Sharpe: 1.500" in report
        assert "65.0%" in report
