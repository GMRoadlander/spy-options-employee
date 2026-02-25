"""Tests for paper trading chart functions."""

import unittest
from datetime import datetime, timedelta

import discord

from src.discord_bot.charts import (
    create_daily_pnl_bar_chart,
    create_drawdown_chart,
    create_pnl_curve_chart,
)


# -- Fixtures ----------------------------------------------------------------


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
        })
    return data


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


if __name__ == "__main__":
    unittest.main()
