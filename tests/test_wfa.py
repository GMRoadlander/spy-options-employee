"""Tests for Walk-Forward Analysis module."""
from __future__ import annotations

from datetime import date

import pytest

from src.backtest.wfa import WalkForwardAnalyzer, WFAResult, _add_months


# -- Helpers ---------------------------------------------------------------


@pytest.fixture
def default_analyzer() -> WalkForwardAnalyzer:
    """12-month IS, 3-month OOS, step 3 months."""
    return WalkForwardAnalyzer(is_months=12, oos_months=3, step_months=3)


# -- _add_months utility ---------------------------------------------------


class TestAddMonths:
    def test_basic(self):
        assert _add_months(date(2020, 1, 1), 3) == date(2020, 4, 1)

    def test_year_rollover(self):
        assert _add_months(date(2020, 11, 1), 3) == date(2021, 2, 1)

    def test_day_clamp(self):
        # Jan 31 + 1 month -> Feb 29 in a leap year
        assert _add_months(date(2020, 1, 31), 1) == date(2020, 2, 29)


# -- Window generation -----------------------------------------------------


class TestGenerateWindows:
    def test_correct_is_oos_pairs(self, default_analyzer: WalkForwardAnalyzer):
        """First window: IS 2018-01-01..2019-01-01, OOS 2019-01-01..2019-04-01."""
        windows = default_analyzer.generate_windows(date(2018, 1, 1), date(2023, 1, 1))
        first = windows[0]
        assert first == (
            date(2018, 1, 1),
            date(2019, 1, 1),
            date(2019, 1, 1),
            date(2019, 4, 1),
        )

    def test_window_count_five_years(self, default_analyzer: WalkForwardAnalyzer):
        """5 years of data (2018-01 to 2023-01): IS=12m, OOS=3m, step=3m.

        First OOS ends 2019-04-01 (window 1), each step adds 3m.
        Last window where OOS end <= 2023-01-01:
        cursor starts at 2018-01-01; cursor = 2018-01 + k*3m.
        OOS_end = cursor + 15m.
        cursor + 15m <= 2023-01 => cursor <= 2021-10-01.
        k=0 -> 2018-01, k=1 -> 2018-04, ... k=15 -> 2021-10.
        That is 16 windows.
        """
        windows = default_analyzer.generate_windows(date(2018, 1, 1), date(2023, 1, 1))
        assert len(windows) == 16

    def test_windows_non_overlapping_oos(self, default_analyzer: WalkForwardAnalyzer):
        """With step == OOS length, OOS windows should tile without overlap."""
        windows = default_analyzer.generate_windows(date(2018, 1, 1), date(2023, 1, 1))
        for i in range(len(windows) - 1):
            _, _, oos_start_curr, oos_end_curr = windows[i]
            _, _, oos_start_next, _ = windows[i + 1]
            # Current OOS end should be <= next OOS start (non-overlapping)
            assert oos_end_curr <= oos_start_next

    def test_insufficient_data(self):
        """Date range too short for even one window."""
        analyzer = WalkForwardAnalyzer(is_months=12, oos_months=3, step_months=3)
        windows = analyzer.generate_windows(date(2020, 1, 1), date(2020, 6, 1))
        assert len(windows) == 0

    def test_step_size_variation(self):
        """Step of 6 months produces fewer windows than step of 3."""
        a3 = WalkForwardAnalyzer(is_months=12, oos_months=3, step_months=3)
        a6 = WalkForwardAnalyzer(is_months=12, oos_months=3, step_months=6)
        w3 = a3.generate_windows(date(2018, 1, 1), date(2023, 1, 1))
        w6 = a6.generate_windows(date(2018, 1, 1), date(2023, 1, 1))
        assert len(w3) > len(w6)


# -- Evaluation -------------------------------------------------------------


class TestEvaluate:
    def test_degradation_calculation(self, default_analyzer: WalkForwardAnalyzer):
        """degradation = mean_oos / mean_is."""
        result = default_analyzer.evaluate(
            is_sharpes=[2.0, 2.0],
            oos_sharpes=[1.5, 1.5],
            strategy_name="test",
        )
        assert result.degradation == pytest.approx(0.75)

    def test_pass_good_oos(self, default_analyzer: WalkForwardAnalyzer):
        """OOS Sharpe > 0 and degradation >= 0.5 => pass."""
        result = default_analyzer.evaluate(
            is_sharpes=[1.0, 1.2],
            oos_sharpes=[0.8, 0.9],
            strategy_name="good",
        )
        assert result.passed is True
        assert result.oos_sharpe_mean > 0
        assert result.degradation >= 0.5

    def test_fail_negative_oos(self, default_analyzer: WalkForwardAnalyzer):
        """Negative OOS Sharpe => fail."""
        result = default_analyzer.evaluate(
            is_sharpes=[1.0, 1.0],
            oos_sharpes=[-0.3, -0.1],
            strategy_name="bad_oos",
        )
        assert result.passed is False

    def test_fail_high_degradation(self, default_analyzer: WalkForwardAnalyzer):
        """OOS > 0 but degradation < 0.5 (more than 50 % drop) => fail."""
        result = default_analyzer.evaluate(
            is_sharpes=[2.0, 2.0],
            oos_sharpes=[0.5, 0.5],
            strategy_name="overfit",
        )
        # degradation = 0.25 < 0.5
        assert result.degradation == pytest.approx(0.25)
        assert result.passed is False

    def test_empty_sharpe_lists(self, default_analyzer: WalkForwardAnalyzer):
        """Empty inputs => fail with 0 windows."""
        result = default_analyzer.evaluate(
            is_sharpes=[],
            oos_sharpes=[],
            strategy_name="empty",
        )
        assert result.passed is False
        assert result.num_windows == 0

    def test_oos_sharpe_std(self, default_analyzer: WalkForwardAnalyzer):
        """Standard deviation is computed correctly (sample std)."""
        result = default_analyzer.evaluate(
            is_sharpes=[1.0, 1.0, 1.0],
            oos_sharpes=[0.8, 1.0, 1.2],
            strategy_name="std_test",
        )
        # sample std of [0.8, 1.0, 1.2] = 0.2
        assert result.oos_sharpe_std == pytest.approx(0.2)


# -- Constructor validation -------------------------------------------------


class TestConstructor:
    def test_invalid_months_raises(self):
        with pytest.raises(ValueError):
            WalkForwardAnalyzer(is_months=0, oos_months=3, step_months=3)
