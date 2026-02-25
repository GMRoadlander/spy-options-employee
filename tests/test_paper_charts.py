"""Tests for paper trading chart functions.

Phase 4-6 tests (from src.discord_bot.charts):
    - create_pnl_curve_chart (5 tests)
    - create_drawdown_chart (4 tests)
    - create_daily_pnl_bar_chart (4 tests)

Phase 4-7 tests (from src.discord_bot.paper_charts):
    - create_paper_equity_chart (4 tests)
    - create_paper_drawdown_chart (2 tests)
    - create_paper_equity_drawdown_chart (1 test)
    - create_strategy_comparison_chart (2 tests)
    - create_degradation_chart (2 tests)
    - create_rolling_sharpe_chart (2 tests)
    - create_win_rate_trend_chart (1 test)
    - create_monthly_pnl_heatmap (1 test)
    - Cross-cutting: figure cleanup (1 test)
    - Cross-cutting: png filenames (1 test)
"""

import unittest
from datetime import date, datetime, timedelta

import discord
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.discord_bot.charts import (
    create_daily_pnl_bar_chart,
    create_drawdown_chart,
    create_pnl_curve_chart,
)
from src.discord_bot.paper_charts import (
    create_degradation_chart,
    create_monthly_pnl_heatmap,
    create_paper_drawdown_chart,
    create_paper_equity_chart,
    create_paper_equity_drawdown_chart,
    create_rolling_sharpe_chart,
    create_strategy_comparison_chart,
    create_win_rate_trend_chart,
)


# ===========================================================================
# Shared Fixtures
# ===========================================================================


def _make_equity_data(days=20, starting_capital=100_000, daily_change=50.0):
    """Create sample equity data for chart testing."""
    data = []
    equity = starting_capital
    base_date = datetime(2026, 2, 1)
    for i in range(days):
        # Alternate positive/negative with trend
        change = daily_change if i % 3 != 0 else -daily_change * 0.8
        equity += change
        date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        data.append({
            "date": date_str,
            "total_equity": equity,
            "daily_pnl": change,
            "max_drawdown": 0.0,
        })
    return data


def _make_flat_equity_data(days=10, starting_capital=100_000):
    """Create equity data with no drawdown (all positive daily PnL)."""
    data = []
    equity = starting_capital
    base_date = datetime(2026, 2, 1)
    for i in range(days):
        equity += 25.0  # Always positive
        date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        data.append({
            "date": date_str,
            "total_equity": equity,
            "daily_pnl": 25.0,
            "max_drawdown": 0.0,
        })
    return data


# ===========================================================================
# Phase 4-7 Specific Fixtures
# ===========================================================================


def _make_rolling_sharpe_data(n: int = 30) -> list[dict]:
    """Rolling sharpe data with dates."""
    base = datetime(2026, 1, 1)
    data: list[dict] = []
    for i in range(n):
        data.append({
            "date": (base + timedelta(days=i)).strftime("%Y-%m-%d"),
            "rolling_sharpe": 0.5 + (i % 10) * 0.15 - 0.3,
        })
    return data


def _make_win_rate_data(n: int = 40) -> list[dict]:
    """Cumulative win rate data."""
    data: list[dict] = []
    wins = 0
    for i in range(1, n + 1):
        if i % 3 != 0:
            wins += 1
        cum_wr = (wins / i) * 100
        rolling = cum_wr + ((-1) ** i) * 5
        data.append({
            "trade_number": i,
            "cumulative_win_rate": cum_wr,
            "rolling_10_wr": rolling,
        })
    return data


def _make_strategy_list(n: int = 3) -> list[dict]:
    """Strategy dicts for comparison chart."""
    strats = []
    for i in range(n):
        strats.append({
            "name": f"Strategy {i + 1}",
            "sharpe_ratio": 1.0 + i * 0.3 - 0.2,
            "win_rate": 55 + i * 3,
            "profit_factor": 1.5 + i * 0.2,
            "total_pnl": 500 + i * 200,
            "max_drawdown": -5 - i,
        })
    return strats


def _make_comparison_data(n: int = 3) -> list[dict]:
    """Degradation comparison data."""
    return [
        {
            "strategy_name": f"Strategy {i + 1}",
            "paper_sharpe": 1.0 + i * 0.2,
            "backtest_sharpe": 1.2 + i * 0.1,
            "paper_win_rate": 60 + i,
            "backtest_win_rate": 65 + i,
            "paper_pf": 1.5 + i * 0.1,
            "backtest_pf": 1.8 + i * 0.1,
        }
        for i in range(n)
    ]


def _make_daily_pnl_data(month: date) -> list[dict]:
    """Daily PnL data for heatmap."""
    import calendar as cal_mod

    _, days_in = cal_mod.monthrange(month.year, month.month)
    data: list[dict] = []
    for d in range(1, days_in + 1):
        # Skip weekends (approximate)
        dt = date(month.year, month.month, d)
        if dt.weekday() >= 5:
            continue
        pnl = 100 - d * 5 if d % 2 == 0 else d * 8 - 50
        data.append({
            "date": dt.strftime("%Y-%m-%d"),
            "pnl": pnl,
        })
    return data


# ###########################################################################
#
#  PHASE 4-6 TESTS (from src.discord_bot.charts)
#
# ###########################################################################


# -- create_pnl_curve_chart tests -------------------------------------------


class TestCreatePnlCurveChart(unittest.TestCase):
    """Tests for create_pnl_curve_chart."""

    def test_success(self):
        """Returns discord.File with correct filename prefix."""
        data = _make_equity_data(20)
        result = create_pnl_curve_chart(data)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)
        self.assertTrue(result.filename.startswith("pnl_curve_"))

    def test_empty_data(self):
        """Empty data returns None."""
        result = create_pnl_curve_chart([])
        self.assertIsNone(result)

    def test_single_day(self):
        """Single day of data returns None (need at least 2 points)."""
        result = create_pnl_curve_chart([{
            "date": "2026-02-01",
            "total_equity": 100_000,
            "daily_pnl": 0,
        }])
        self.assertIsNone(result)

    def test_with_strategy_name(self):
        """Chart with strategy name renders successfully."""
        data = _make_equity_data(5)
        result = create_pnl_curve_chart(data, strategy_name="Iron Condor Weekly")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)

    def test_two_days_minimum(self):
        """Two days of data is the minimum for a chart."""
        data = _make_equity_data(2)
        result = create_pnl_curve_chart(data)
        self.assertIsNotNone(result)


# -- create_drawdown_chart tests --------------------------------------------


class TestCreateDrawdownChart(unittest.TestCase):
    """Tests for create_drawdown_chart."""

    def test_success(self):
        """Returns discord.File with correct filename prefix."""
        data = _make_equity_data(20)
        result = create_drawdown_chart(data)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)
        self.assertTrue(result.filename.startswith("drawdown_"))

    def test_no_drawdown(self):
        """Data with all positive PnL still returns a valid chart (flat at 0)."""
        data = _make_flat_equity_data(10)
        result = create_drawdown_chart(data)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)

    def test_empty_data(self):
        """Empty data returns None."""
        result = create_drawdown_chart([])
        self.assertIsNone(result)

    def test_single_day(self):
        """Single day returns None."""
        result = create_drawdown_chart([{
            "date": "2026-02-01",
            "total_equity": 100_000,
        }])
        self.assertIsNone(result)


# -- create_daily_pnl_bar_chart tests ----------------------------------------


class TestCreateDailyPnlBarChart(unittest.TestCase):
    """Tests for create_daily_pnl_bar_chart."""

    def test_success(self):
        """Returns discord.File with correct filename prefix."""
        data = _make_equity_data(15)
        result = create_daily_pnl_bar_chart(data, days=15)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)
        self.assertTrue(result.filename.startswith("daily_pnl_"))

    def test_empty_data(self):
        """Empty data returns None."""
        result = create_daily_pnl_bar_chart([])
        self.assertIsNone(result)

    def test_mixed_pnl(self):
        """Mixed positive/negative days render correctly."""
        data = [
            {"date": "2026-02-01", "daily_pnl": 100.0},
            {"date": "2026-02-02", "daily_pnl": -50.0},
            {"date": "2026-02-03", "daily_pnl": 75.0},
            {"date": "2026-02-04", "daily_pnl": -25.0},
            {"date": "2026-02-05", "daily_pnl": 200.0},
        ]
        result = create_daily_pnl_bar_chart(data, days=5)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)

    def test_days_limit(self):
        """Only last N days shown when days < total data."""
        data = _make_equity_data(30)
        result = create_daily_pnl_bar_chart(data, days=10)
        self.assertIsNotNone(result)


# ###########################################################################
#
#  PHASE 4-7 TESTS (from src.discord_bot.paper_charts)
#
# ###########################################################################


# ---------------------------------------------------------------------------
# 2a: Equity chart tests
# ---------------------------------------------------------------------------


class TestEquityChart(unittest.TestCase):

    def test_equity_chart_returns_discord_file(self):
        """Normal data produces a discord.File."""
        result = create_paper_equity_chart(_make_equity_data(20))
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)

    def test_equity_chart_empty_data_returns_none(self):
        """Empty list returns None."""
        result = create_paper_equity_chart([])
        self.assertIsNone(result)

    def test_equity_chart_single_datapoint(self):
        """Single data point still returns a file (chart is valid)."""
        data = _make_equity_data(1)
        result = create_paper_equity_chart(data)
        # A single point is valid -- it renders a dot + reference line.
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)

    def test_equity_chart_subsamples_large_data(self):
        """More than 80 data points get sub-sampled without error."""
        data = _make_equity_data(200)
        result = create_paper_equity_chart(data)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)


# ---------------------------------------------------------------------------
# 2b: Drawdown chart tests
# ---------------------------------------------------------------------------


class TestPaperDrawdownChart(unittest.TestCase):

    def test_drawdown_chart_returns_discord_file(self):
        """Normal data produces a discord.File."""
        result = create_paper_drawdown_chart(_make_equity_data(20))
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)

    def test_drawdown_chart_no_drawdown(self):
        """All-positive equity still produces a file (flat at 0)."""
        data = _make_flat_equity_data(10)
        result = create_paper_drawdown_chart(data)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)


# ---------------------------------------------------------------------------
# 2c: Combined chart test
# ---------------------------------------------------------------------------


class TestCombinedChart(unittest.TestCase):

    def test_combined_chart_dual_panels(self):
        """Combined chart returns discord.File."""
        data = _make_equity_data(20)
        result = create_paper_equity_drawdown_chart(data)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)


# ---------------------------------------------------------------------------
# 2d: Strategy comparison chart tests
# ---------------------------------------------------------------------------


class TestStrategyComparisonChart(unittest.TestCase):

    def test_strategy_comparison_chart_multiple_strategies(self):
        """Multiple strategies produce a valid chart."""
        strats = _make_strategy_list(3)
        result = create_strategy_comparison_chart(strats, metric="sharpe_ratio")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)

    def test_strategy_comparison_chart_single_strategy(self):
        """Single strategy still renders a chart."""
        strats = _make_strategy_list(1)
        result = create_strategy_comparison_chart(strats)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)


# ---------------------------------------------------------------------------
# 2e: Degradation chart tests
# ---------------------------------------------------------------------------


class TestDegradationChart(unittest.TestCase):

    def test_degradation_chart_with_data(self):
        """Comparison data produces a valid chart."""
        comps = _make_comparison_data(2)
        result = create_degradation_chart(comps)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)

    def test_degradation_chart_empty_returns_none(self):
        """Empty comparisons list returns None."""
        result = create_degradation_chart([])
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# 2f: Rolling Sharpe chart tests
# ---------------------------------------------------------------------------


class TestRollingSharpeChart(unittest.TestCase):

    def test_rolling_sharpe_chart_with_data(self):
        """Normal rolling data produces a valid chart."""
        data = _make_rolling_sharpe_data(30)
        result = create_rolling_sharpe_chart(data, "TestStrategy")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)

    def test_rolling_sharpe_chart_threshold_lines(self):
        """Verify threshold lines are present on the chart axes.

        We patch _save_to_discord_file to intercept the figure and inspect
        horizontal lines before it is closed.
        """
        from unittest.mock import patch, MagicMock

        captured_fig = {}

        def _capture_fig(fig, filename):
            # Record axes info before close
            ax = fig.axes[0]
            captured_fig["hlines"] = [
                line.get_ydata()[0]
                for line in ax.get_lines()
                if hasattr(line.get_ydata(), "__len__")
                and len(set(line.get_ydata())) == 1
                and len(line.get_ydata()) > 1
            ]
            # Still need to close
            plt.close(fig)
            return discord.File(fp=__import__("io").BytesIO(b"fake"), filename=filename)

        data = _make_rolling_sharpe_data(30)
        with patch(
            "src.discord_bot.paper_charts._save_to_discord_file",
            side_effect=_capture_fig,
        ):
            result = create_rolling_sharpe_chart(data, "TestStrategy")

        self.assertIsNotNone(result)
        # The chart should have axhlines at 1.0, 0.5, and 0.0
        hlines = captured_fig.get("hlines", [])
        for expected in (1.0, 0.5, 0.0):
            self.assertIn(expected, hlines, f"Missing threshold line at {expected}")


# ---------------------------------------------------------------------------
# 2g: Win rate trend chart test
# ---------------------------------------------------------------------------


class TestWinRateTrendChart(unittest.TestCase):

    def test_win_rate_trend_chart(self):
        """Win rate data produces a valid chart."""
        data = _make_win_rate_data(40)
        result = create_win_rate_trend_chart(data, "TestStrategy")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)


# ---------------------------------------------------------------------------
# 2h: Monthly PnL heatmap test
# ---------------------------------------------------------------------------


class TestMonthlyPnlHeatmap(unittest.TestCase):

    def test_monthly_pnl_heatmap(self):
        """Heatmap data for a month produces a valid chart."""
        month = date(2026, 2, 1)
        data = _make_daily_pnl_data(month)
        result = create_monthly_pnl_heatmap(data, month)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, discord.File)


# ---------------------------------------------------------------------------
# Cross-cutting tests
# ---------------------------------------------------------------------------


class TestAllChartsCloseFigure(unittest.TestCase):
    """Ensure every chart function closes its figure (no leak)."""

    def test_all_charts_close_figure(self):
        """After calling every chart function, no unclosed figures remain."""
        plt.close("all")

        # Call each chart function
        eq_data = _make_equity_data(20)
        create_paper_equity_chart(eq_data)
        create_paper_drawdown_chart(eq_data)
        create_paper_equity_drawdown_chart(eq_data)
        create_strategy_comparison_chart(_make_strategy_list(2))
        create_degradation_chart(_make_comparison_data(2))
        create_rolling_sharpe_chart(_make_rolling_sharpe_data(), "Test")
        create_win_rate_trend_chart(_make_win_rate_data(), "Test")
        create_monthly_pnl_heatmap(
            _make_daily_pnl_data(date(2026, 2, 1)), date(2026, 2, 1),
        )

        # All figures should have been closed by _save_to_discord_file
        open_figs = plt.get_fignums()
        self.assertEqual(len(open_figs), 0, f"Leaked figures: {open_figs}")


class TestAllChartsReturnPngFilename(unittest.TestCase):
    """Verify every returned discord.File has a .png filename."""

    def test_all_charts_return_png_filename(self):
        eq_data = _make_equity_data(20)
        results = [
            create_paper_equity_chart(eq_data),
            create_paper_drawdown_chart(eq_data),
            create_paper_equity_drawdown_chart(eq_data),
            create_strategy_comparison_chart(_make_strategy_list(2)),
            create_degradation_chart(_make_comparison_data(2)),
            create_rolling_sharpe_chart(_make_rolling_sharpe_data(), "Test"),
            create_win_rate_trend_chart(_make_win_rate_data(), "Test"),
            create_monthly_pnl_heatmap(
                _make_daily_pnl_data(date(2026, 2, 1)), date(2026, 2, 1),
            ),
        ]

        for i, result in enumerate(results):
            self.assertIsNotNone(result, f"Chart function {i} returned None")
            self.assertTrue(
                result.filename.endswith(".png"),
                f"Chart {i} filename {result.filename!r} does not end with .png",
            )


if __name__ == "__main__":
    unittest.main()
