"""Tests for ML feature computation functions.

Covers all 6 pure computation functions: IV rank, IV percentile,
25-delta skew, term structure slope, RV/IV spread, and Hurst exponent.
Tests include normal cases, edge cases, and mathematical correctness.
"""

import math
from datetime import date, datetime, timedelta

import numpy as np
import pytest

from src.data import OptionContract, OptionsChain
from src.ml.features import (
    compute_hurst_exponent,
    compute_iv_percentile,
    compute_iv_rank,
    compute_rv_iv_spread,
    compute_skew_25d,
    compute_term_structure_slope,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_contract(
    strike: float,
    option_type: str,
    iv: float,
    delta: float = 0.0,
    expiry: date | None = None,
    days_out: int = 30,
) -> OptionContract:
    """Create a minimal OptionContract for testing."""
    if expiry is None:
        expiry = date.today() + timedelta(days=days_out)
    return OptionContract(
        ticker="SPX",
        expiry=expiry,
        strike=strike,
        option_type=option_type,
        bid=1.0,
        ask=1.5,
        last=1.25,
        volume=100,
        open_interest=1000,
        iv=iv,
        delta=delta,
    )


def _make_chain(contracts: list[OptionContract], spot: float = 5000.0) -> OptionsChain:
    """Wrap contracts in an OptionsChain."""
    return OptionsChain(
        ticker="SPX",
        spot_price=spot,
        timestamp=datetime.now(),
        contracts=contracts,
    )


# ===================================================================
# IV Rank
# ===================================================================


class TestComputeIVRank:
    """Tests for compute_iv_rank (high/low range method)."""

    def test_known_history(self):
        """IV rank of 35 in [10,20,30,40,50]: (35-10)/(50-10)*100 = 62.5."""
        rank = compute_iv_rank(35, [10, 20, 30, 40, 50])
        assert rank == pytest.approx(62.5)

    def test_at_high(self):
        """Current at max of history -> rank = 100."""
        rank = compute_iv_rank(50, [10, 20, 30, 40, 50])
        assert rank == pytest.approx(100.0)

    def test_at_low(self):
        """Current at min of history -> rank = 0."""
        rank = compute_iv_rank(10, [10, 20, 30, 40, 50])
        assert rank == pytest.approx(0.0)

    def test_above_high(self):
        """Current above max of history -> clamped to 100."""
        rank = compute_iv_rank(100, [10, 20, 30, 40, 50])
        assert rank == pytest.approx(100.0)

    def test_below_low(self):
        """Current below min of history -> clamped to 0."""
        rank = compute_iv_rank(1, [10, 20, 30, 40, 50])
        assert rank == pytest.approx(0.0)

    def test_empty_history(self):
        """Empty history returns default 50."""
        assert compute_iv_rank(30, []) == pytest.approx(50.0)

    def test_single_value_history(self):
        """Single-value history returns default 50."""
        assert compute_iv_rank(30, [30]) == pytest.approx(50.0)

    def test_constant_history(self):
        """All identical values (hi == lo) returns default 50."""
        assert compute_iv_rank(20, [20, 20, 20]) == pytest.approx(50.0)

    def test_numpy_array_input(self):
        """Accepts numpy arrays as input."""
        rank = compute_iv_rank(35, np.array([10, 20, 30, 40, 50]))
        assert rank == pytest.approx(62.5)

    def test_nan_in_history(self):
        """NaN values in history are ignored."""
        rank = compute_iv_rank(35, [10, float("nan"), 30, float("nan"), 50])
        # Valid history is [10, 30, 50], rank = (35-10)/(50-10)*100 = 62.5
        assert rank == pytest.approx(62.5)


# ===================================================================
# IV Percentile
# ===================================================================


class TestComputeIVPercentile:
    """Tests for compute_iv_percentile (count below method)."""

    def test_known_history(self):
        """35 in [10,20,30,40,50]: 3 of 5 below 35 -> 60%."""
        pct = compute_iv_percentile(35, [10, 20, 30, 40, 50])
        assert pct == pytest.approx(60.0)

    def test_at_minimum(self):
        """Current at min -> 0%."""
        pct = compute_iv_percentile(10, [10, 20, 30, 40, 50])
        assert pct == pytest.approx(0.0)

    def test_above_all(self):
        """Current above all -> 100%."""
        pct = compute_iv_percentile(100, [10, 20, 30, 40, 50])
        assert pct == pytest.approx(100.0)

    def test_empty_history(self):
        """Empty history returns default 50."""
        assert compute_iv_percentile(30, []) == pytest.approx(50.0)

    def test_single_value_history(self):
        """Single-value history returns default 50."""
        assert compute_iv_percentile(30, [30]) == pytest.approx(50.0)

    def test_numpy_array_input(self):
        """Accepts numpy arrays as input."""
        pct = compute_iv_percentile(35, np.array([10, 20, 30, 40, 50]))
        assert pct == pytest.approx(60.0)

    def test_differs_from_iv_rank(self):
        """IV percentile and IV rank give different results for same input."""
        history = [10, 20, 30, 40, 50]
        rank = compute_iv_rank(35, history)
        pct = compute_iv_percentile(35, history)
        assert rank != pct  # 62.5 vs 60.0


# ===================================================================
# 25-Delta Skew
# ===================================================================


class TestComputeSkew25d:
    """Tests for compute_skew_25d (risk reversal)."""

    def test_synthetic_positive_skew(self):
        """Puts more expensive than calls -> positive skew."""
        expiry = date.today() + timedelta(days=30)
        contracts = [
            # Puts with deltas -0.20 and -0.30 (bracket -0.25)
            _make_contract(4900, "put", iv=0.22, delta=-0.30, expiry=expiry),
            _make_contract(4800, "put", iv=0.25, delta=-0.20, expiry=expiry),
            # Calls with deltas 0.20 and 0.30 (bracket 0.25)
            _make_contract(5100, "call", iv=0.17, delta=0.20, expiry=expiry),
            _make_contract(5200, "call", iv=0.15, delta=0.30, expiry=expiry),
        ]
        chain = _make_chain(contracts)
        skew = compute_skew_25d(chain)
        # 25D put IV ~ 0.235 (interp between 0.22@-0.30 and 0.25@-0.20)
        # 25D call IV ~ 0.16 (interp between 0.17@0.20 and 0.15@0.30)
        assert skew > 0  # puts more expensive

    def test_synthetic_negative_skew(self):
        """Calls more expensive than puts -> negative skew."""
        expiry = date.today() + timedelta(days=30)
        contracts = [
            _make_contract(4900, "put", iv=0.12, delta=-0.30, expiry=expiry),
            _make_contract(4800, "put", iv=0.13, delta=-0.20, expiry=expiry),
            _make_contract(5100, "call", iv=0.25, delta=0.20, expiry=expiry),
            _make_contract(5200, "call", iv=0.22, delta=0.30, expiry=expiry),
        ]
        chain = _make_chain(contracts)
        skew = compute_skew_25d(chain)
        assert skew < 0  # calls more expensive

    def test_empty_chain(self):
        """Empty chain returns 0.0."""
        chain = _make_chain([])
        assert compute_skew_25d(chain) == 0.0

    def test_insufficient_contracts(self):
        """Only one put and one call is insufficient for interpolation."""
        expiry = date.today() + timedelta(days=30)
        contracts = [
            _make_contract(4900, "put", iv=0.20, delta=-0.25, expiry=expiry),
            _make_contract(5100, "call", iv=0.18, delta=0.25, expiry=expiry),
        ]
        chain = _make_chain(contracts)
        assert compute_skew_25d(chain) == 0.0

    def test_zero_iv_contracts_filtered(self):
        """Contracts with iv=0 are excluded from interpolation."""
        expiry = date.today() + timedelta(days=30)
        contracts = [
            _make_contract(4900, "put", iv=0.0, delta=-0.30, expiry=expiry),
            _make_contract(4800, "put", iv=0.0, delta=-0.20, expiry=expiry),
            _make_contract(5100, "call", iv=0.17, delta=0.20, expiry=expiry),
            _make_contract(5200, "call", iv=0.15, delta=0.30, expiry=expiry),
        ]
        chain = _make_chain(contracts)
        assert compute_skew_25d(chain) == 0.0


# ===================================================================
# Term Structure Slope
# ===================================================================


class TestComputeTermStructureSlope:
    """Tests for compute_term_structure_slope."""

    def test_contango_positive_slope(self):
        """Far expiry IV > near expiry IV -> positive slope (contango)."""
        exp_near = date.today() + timedelta(days=7)
        exp_far = date.today() + timedelta(days=37)
        contracts = [
            _make_contract(5000, "call", iv=0.15, expiry=exp_near),
            _make_contract(5000, "call", iv=0.20, expiry=exp_far),
        ]
        chain = _make_chain(contracts, spot=5000.0)
        slope = compute_term_structure_slope(chain)
        assert slope > 0  # contango

    def test_backwardation_negative_slope(self):
        """Far expiry IV < near expiry IV -> negative slope (backwardation)."""
        exp_near = date.today() + timedelta(days=7)
        exp_far = date.today() + timedelta(days=37)
        contracts = [
            _make_contract(5000, "call", iv=0.25, expiry=exp_near),
            _make_contract(5000, "call", iv=0.15, expiry=exp_far),
        ]
        chain = _make_chain(contracts, spot=5000.0)
        slope = compute_term_structure_slope(chain)
        assert slope < 0  # backwardation

    def test_slope_normalised_by_dte(self):
        """Slope is divided by DTE difference."""
        exp_near = date.today() + timedelta(days=10)
        exp_far = date.today() + timedelta(days=40)
        contracts = [
            _make_contract(5000, "call", iv=0.15, expiry=exp_near),
            _make_contract(5000, "call", iv=0.18, expiry=exp_far),
        ]
        chain = _make_chain(contracts, spot=5000.0)
        slope = compute_term_structure_slope(chain)
        # (0.18 - 0.15) / 30 = 0.001
        assert slope == pytest.approx(0.001, rel=1e-6)

    def test_single_expiry_returns_zero(self):
        """Chain with only one expiry returns 0.0."""
        exp = date.today() + timedelta(days=30)
        contracts = [_make_contract(5000, "call", iv=0.15, expiry=exp)]
        chain = _make_chain(contracts, spot=5000.0)
        assert compute_term_structure_slope(chain) == 0.0

    def test_empty_chain_returns_zero(self):
        """Empty chain returns 0.0."""
        chain = _make_chain([])
        assert compute_term_structure_slope(chain) == 0.0


# ===================================================================
# RV/IV Spread
# ===================================================================


class TestComputeRvIvSpread:
    """Tests for compute_rv_iv_spread."""

    def test_known_returns(self):
        """Verify annualisation with a known constant-return series."""
        # 20 daily returns all equal to 0.01 (1%)
        returns = [0.01] * 25
        iv = 0.20

        # std(constant) = 0 with ddof=1 is nan... use varied returns
        # Use a series with known std
        np.random.seed(123)
        returns = list(np.random.normal(0, 0.01, 25))
        daily_std = np.std(returns[-20:], ddof=1)
        expected_rv = daily_std * math.sqrt(252)
        expected_spread = expected_rv - iv

        spread = compute_rv_iv_spread(returns, iv, window=20)
        assert spread == pytest.approx(expected_spread, rel=1e-6)

    def test_negative_spread_vol_overpriced(self):
        """When RV < IV, spread is negative (vol overpriced)."""
        # Low-volatility returns vs high IV
        returns = [0.001] * 5 + [-0.001] * 5 + [0.001] * 5 + [-0.001] * 5 + [0.001] * 5
        spread = compute_rv_iv_spread(returns, 0.30, window=20)
        assert spread < 0  # IV > RV

    def test_positive_spread_vol_underpriced(self):
        """When RV > IV, spread is positive."""
        # High-volatility returns vs low IV
        np.random.seed(42)
        returns = list(np.random.normal(0, 0.05, 30))
        spread = compute_rv_iv_spread(returns, 0.05, window=20)
        assert spread > 0  # RV > IV

    def test_insufficient_data(self):
        """Fewer returns than window returns 0.0."""
        assert compute_rv_iv_spread([0.01, 0.02], 0.20, window=20) == 0.0

    def test_empty_returns(self):
        """Empty returns list returns 0.0."""
        assert compute_rv_iv_spread([], 0.20) == 0.0

    def test_uses_trailing_window(self):
        """Only the last `window` returns are used."""
        # 30 returns, but window=5: only last 5 matter
        returns = [0.0] * 25 + [0.01, -0.01, 0.02, -0.02, 0.01]
        daily_std = np.std(returns[-5:], ddof=1)
        expected_rv = daily_std * math.sqrt(252)
        spread = compute_rv_iv_spread(returns, 0.20, window=5)
        assert spread == pytest.approx(expected_rv - 0.20, rel=1e-6)

    def test_numpy_array_input(self):
        """Accepts numpy arrays as input."""
        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 25)
        spread = compute_rv_iv_spread(returns, 0.20, window=20)
        assert isinstance(spread, float)


# ===================================================================
# Hurst Exponent
# ===================================================================


class TestComputeHurstExponent:
    """Tests for compute_hurst_exponent (R/S analysis)."""

    def test_pure_trend_high_hurst(self):
        """Strongly trending prices should have H > 0.5."""
        prices = np.linspace(100, 200, 500)
        h = compute_hurst_exponent(prices, max_lag=20)
        assert h > 0.7  # should be close to 1.0

    def test_random_walk_mid_hurst(self):
        """Random walk should have H approximately 0.5.

        Note: R/S analysis has a known small-sample upward bias, so we
        use max_lag=100 with a large sample for a tighter estimate.
        """
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(5000))
        # Keep prices positive
        prices = prices - np.min(prices) + 10
        h = compute_hurst_exponent(prices, max_lag=100)
        assert 0.4 < h < 0.8  # approximately 0.5, allowing for R/S bias

    def test_mean_reverting_low_hurst(self):
        """Mean-reverting process should have H < 0.5.

        Uses strong mean-reversion and max_lag=100 to overcome
        R/S small-sample bias.
        """
        np.random.seed(99)
        n = 10000
        theta = 0.8  # strong mean-reversion speed
        mu = 100     # long-term mean
        sigma = 0.5
        prices = np.zeros(n)
        prices[0] = mu
        for i in range(1, n):
            prices[i] = prices[i - 1] + theta * (mu - prices[i - 1]) + sigma * np.random.randn()
        h = compute_hurst_exponent(prices, max_lag=100)
        assert h < 0.5

    def test_insufficient_data(self):
        """Fewer than max_lag+1 prices returns default 0.5."""
        assert compute_hurst_exponent([100, 101, 102], max_lag=20) == 0.5

    def test_empty_prices(self):
        """Empty prices returns default 0.5."""
        assert compute_hurst_exponent([], max_lag=20) == 0.5

    def test_single_price(self):
        """Single price returns default 0.5."""
        assert compute_hurst_exponent([100], max_lag=20) == 0.5

    def test_result_bounded(self):
        """Hurst should always be in [0, 1]."""
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(200))
        prices = prices - np.min(prices) + 10
        h = compute_hurst_exponent(prices, max_lag=20)
        assert 0.0 <= h <= 1.0

    def test_numpy_array_input(self):
        """Accepts numpy arrays as input."""
        prices = np.linspace(100, 200, 100)
        h = compute_hurst_exponent(prices, max_lag=10)
        assert isinstance(h, float)

    def test_nan_in_prices(self):
        """NaN values are filtered out."""
        prices = list(np.linspace(100, 200, 50))
        prices[10] = float("nan")
        prices[20] = float("nan")
        h = compute_hurst_exponent(prices, max_lag=10)
        assert 0.0 <= h <= 1.0
