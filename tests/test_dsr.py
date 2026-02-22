"""Tests for the Deflated Sharpe Ratio module (Bailey & Lopez de Prado 2014)."""
from __future__ import annotations

import pytest
import numpy as np
from scipy import stats

from src.backtest.dsr import (
    EULER_MASCHERONI,
    DSRResult,
    deflated_sharpe_ratio,
    evaluate_dsr,
    expected_max_sharpe,
)


# ---------------------------------------------------------------------------
# 1. n_trials=1 -> expected max sharpe equals mean, DSR easier to pass
# ---------------------------------------------------------------------------
class TestExpectedMaxSharpe:
    def test_single_trial_returns_mean(self):
        """With only one trial there is no selection bias; SR_0 = mean."""
        assert expected_max_sharpe(1, mean_sr=0.0) == 0.0
        assert expected_max_sharpe(1, mean_sr=1.5) == 1.5

    def test_more_trials_raises_threshold(self):
        """More trials -> higher expected max -> harder to beat."""
        sr_10 = expected_max_sharpe(10)
        sr_100 = expected_max_sharpe(100)
        sr_1000 = expected_max_sharpe(1000)
        assert sr_10 < sr_100 < sr_1000


# ---------------------------------------------------------------------------
# 2. High Sharpe with few trials -> should pass
# ---------------------------------------------------------------------------
class TestHighSharpePassesFewTrials:
    def test_strong_sharpe_few_trials_passes(self):
        """A genuinely strong strategy with few variants tested should pass."""
        sr0 = expected_max_sharpe(n_trials=5)
        dsr_val = deflated_sharpe_ratio(
            estimated_sharpe=2.5,
            expected_max_sr=sr0,
            backtest_horizon=252,
        )
        assert dsr_val > 0.95, f"DSR {dsr_val:.4f} should exceed 0.95"


# ---------------------------------------------------------------------------
# 3. Low Sharpe with many trials -> should fail (selection bias)
# ---------------------------------------------------------------------------
class TestLowSharpeManyTrialsFails:
    def test_mediocre_sharpe_many_trials_fails(self):
        """A mediocre SR picked from many variants is likely overfitting."""
        sr0 = expected_max_sharpe(n_trials=1000)
        dsr_val = deflated_sharpe_ratio(
            estimated_sharpe=1.0,
            expected_max_sr=sr0,
            backtest_horizon=252,
        )
        assert dsr_val < 0.95, f"DSR {dsr_val:.4f} should be below 0.95"


# ---------------------------------------------------------------------------
# 4. High kurtosis reduces DSR (options-like fat-tailed returns)
# ---------------------------------------------------------------------------
class TestKurtosisEffect:
    def test_high_kurtosis_reduces_dsr(self):
        """Fat tails (high kurtosis) inflate the SR variance, reducing DSR.

        We need estimated_sharpe > expected_max_sr (positive numerator) so that
        a larger denominator from excess kurtosis actually *reduces* the test
        statistic and therefore the CDF.  A shorter horizon (T=30) keeps both
        DSR values away from the 0/1 boundaries for a clear comparison.
        """
        sr0 = expected_max_sharpe(n_trials=10)
        dsr_normal = deflated_sharpe_ratio(
            estimated_sharpe=1.8,
            expected_max_sr=sr0,
            backtest_horizon=30,
            kurtosis=3.0,   # normal
        )
        dsr_fat = deflated_sharpe_ratio(
            estimated_sharpe=1.8,
            expected_max_sr=sr0,
            backtest_horizon=30,
            kurtosis=9.0,   # fat tails (options-like)
        )
        assert dsr_fat < dsr_normal, (
            f"Fat-tail DSR {dsr_fat:.4f} should be less than normal DSR {dsr_normal:.4f}"
        )


# ---------------------------------------------------------------------------
# 5. Negative skew reduces DSR (short premium strategies)
# ---------------------------------------------------------------------------
class TestSkewEffect:
    def test_negative_skew_reduces_dsr(self):
        """Negative skew (short premium) should reduce DSR vs zero skew.

        With positive numerator (SR > SR_0), negative skew increases the
        denominator (-skew * SR is positive), shrinking the test statistic
        and yielding a lower DSR.
        """
        sr0 = expected_max_sharpe(n_trials=10)
        dsr_zero_skew = deflated_sharpe_ratio(
            estimated_sharpe=1.8,
            expected_max_sr=sr0,
            backtest_horizon=30,
            skew=0.0,
        )
        dsr_neg_skew = deflated_sharpe_ratio(
            estimated_sharpe=1.8,
            expected_max_sr=sr0,
            backtest_horizon=30,
            skew=-1.5,
        )
        assert dsr_neg_skew < dsr_zero_skew, (
            f"Neg-skew DSR {dsr_neg_skew:.4f} should be less than "
            f"zero-skew DSR {dsr_zero_skew:.4f}"
        )


# ---------------------------------------------------------------------------
# 6. Boundary test: DSR at exactly 0.95 threshold
# ---------------------------------------------------------------------------
class TestBoundaryThreshold:
    def test_near_threshold_boundary(self):
        """DSR near 0.95 boundary: just above passes, just below fails."""
        # Reverse-engineer the SR needed for DSR = 0.95 with n_trials=10
        sr0 = expected_max_sharpe(n_trials=10)
        T = 252
        # For normal returns (skew=0, kurtosis=3), denominator = 1
        # DSR = Phi[(SR - sr0) * sqrt(T-1)]
        # 0.95 = Phi[z] => z = 1.6449
        z_crit = stats.norm.ppf(0.95)
        sr_boundary = sr0 + z_crit / np.sqrt(T - 1)

        dsr_just_above = deflated_sharpe_ratio(
            estimated_sharpe=sr_boundary + 0.01,
            expected_max_sr=sr0,
            backtest_horizon=T,
        )
        dsr_just_below = deflated_sharpe_ratio(
            estimated_sharpe=sr_boundary - 0.01,
            expected_max_sr=sr0,
            backtest_horizon=T,
        )
        assert dsr_just_above > 0.95, f"Above-boundary DSR {dsr_just_above:.4f}"
        assert dsr_just_below < 0.95, f"Below-boundary DSR {dsr_just_below:.4f}"


# ---------------------------------------------------------------------------
# 7. Single trial with strong sharpe passes
# ---------------------------------------------------------------------------
class TestSingleTrialStrongSharpe:
    def test_single_trial_strong_sharpe_passes(self):
        """One strategy variant with a solid SR should easily pass."""
        sr0 = expected_max_sharpe(n_trials=1)  # = 0.0
        dsr_val = deflated_sharpe_ratio(
            estimated_sharpe=1.5,
            expected_max_sr=sr0,
            backtest_horizon=252,
        )
        assert dsr_val > 0.99, f"Single-trial strong SR should trivially pass, got {dsr_val:.4f}"


# ---------------------------------------------------------------------------
# 8. evaluate_dsr convenience function works end-to-end
# ---------------------------------------------------------------------------
class TestEvaluateDSR:
    def test_convenience_function_returns_result(self):
        """evaluate_dsr should return a populated DSRResult dataclass."""
        all_sharpes = [0.3, 0.5, 0.7, 1.0, 1.2, 0.8, 0.6, 0.4, 0.9, 1.1]
        result = evaluate_dsr(
            strategy_sharpe=2.5,
            all_sharpes=all_sharpes,
            backtest_horizon=252,
            skew=-0.5,
            kurtosis=5.0,
            strategy_name="iron_condor_v3",
        )
        assert isinstance(result, DSRResult)
        assert result.strategy_name == "iron_condor_v3"
        assert result.n_trials == 10
        assert result.backtest_horizon == 252
        assert result.skewness == -0.5
        assert result.kurtosis == 5.0
        assert 0.0 <= result.dsr <= 1.0
        assert result.estimated_sharpe == 2.5
        assert result.expected_max_sharpe > 0.0
        # A 2.5 SR among 10 trials should pass even with skew/kurtosis penalty
        assert result.passed is True, f"DSR {result.dsr:.4f} expected to pass"

    def test_empty_sharpes_list_treated_as_single_trial(self):
        """An empty comparison list should default to single-trial behavior."""
        result = evaluate_dsr(
            strategy_sharpe=1.0,
            all_sharpes=[],
            backtest_horizon=252,
            strategy_name="solo",
        )
        assert result.n_trials == 1
        assert result.expected_max_sharpe == 0.0
        assert result.passed is True
