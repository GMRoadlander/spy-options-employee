"""Tests for Gamma Exposure (GEX) calculations.

Validates GEX computation, sign conventions, gamma flip detection,
and edge cases using synthetic option chains with known parameters.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from src.data import OptionContract, OptionsChain
from src.analysis.gex import (
    GEXResult,
    _compute_contract_gex,
    _find_gamma_flip,
    calculate_gex,
)


# ---------------------------------------------------------------------------
# Helper: build synthetic option chains
# ---------------------------------------------------------------------------

def make_contract(
    strike: float,
    option_type: str,
    open_interest: int = 1000,
    volume: int = 500,
    iv: float = 0.15,
    days_to_expiry: int = 30,
    ticker: str = "SPY",
) -> OptionContract:
    """Create a single OptionContract with sensible defaults."""
    expiry = date.today() + timedelta(days=days_to_expiry)
    return OptionContract(
        ticker=ticker,
        expiry=expiry,
        strike=strike,
        option_type=option_type,
        bid=1.0,
        ask=1.50,
        last=1.25,
        volume=volume,
        open_interest=open_interest,
        iv=iv,
    )


def make_test_chain(
    spot: float = 600.0,
    strikes: list[float] | None = None,
    oi_calls: list[int] | None = None,
    oi_puts: list[int] | None = None,
    iv: float = 0.15,
    days_to_expiry: int = 30,
) -> OptionsChain:
    """Build an OptionsChain with call+put at each strike.

    Args:
        spot: Underlying spot price.
        strikes: List of strike prices. Defaults to [590, 595, 600, 605, 610].
        oi_calls: Open interest for each call. Must match len(strikes).
        oi_puts: Open interest for each put. Must match len(strikes).
        iv: Implied volatility for all contracts.
        days_to_expiry: Days until expiry for all contracts.

    Returns:
        OptionsChain with the specified contracts.
    """
    if strikes is None:
        strikes = [590.0, 595.0, 600.0, 605.0, 610.0]
    if oi_calls is None:
        oi_calls = [1000] * len(strikes)
    if oi_puts is None:
        oi_puts = [1000] * len(strikes)

    assert len(strikes) == len(oi_calls) == len(oi_puts)

    contracts = []
    for i, k in enumerate(strikes):
        contracts.append(
            make_contract(k, "call", open_interest=oi_calls[i], iv=iv, days_to_expiry=days_to_expiry)
        )
        contracts.append(
            make_contract(k, "put", open_interest=oi_puts[i], iv=iv, days_to_expiry=days_to_expiry)
        )

    return OptionsChain(
        ticker="SPY",
        spot_price=spot,
        timestamp=datetime.now(),
        contracts=contracts,
    )


# ===================================================================
# Contract-level GEX tests
# ===================================================================

class TestComputeContractGEX:

    def test_call_gex_is_positive(self):
        """Call contracts should produce positive GEX (dealer short calls)."""
        contract = make_contract(600, "call", open_interest=1000)
        gex = _compute_contract_gex(contract, spot=600.0, risk_free_rate=0.05)
        assert gex > 0

    def test_put_gex_is_negative(self):
        """Put contracts should produce negative GEX (dealer short puts)."""
        contract = make_contract(600, "put", open_interest=1000)
        gex = _compute_contract_gex(contract, spot=600.0, risk_free_rate=0.05)
        assert gex < 0

    def test_zero_open_interest_returns_zero(self):
        """Contracts with zero OI should contribute no GEX."""
        contract = make_contract(600, "call", open_interest=0)
        gex = _compute_contract_gex(contract, spot=600.0, risk_free_rate=0.05)
        assert gex == 0.0

    def test_expired_contract_returns_zero(self):
        """Expired contracts (days_to_expiry=0) should contribute no GEX."""
        contract = make_contract(600, "call", open_interest=1000, days_to_expiry=0)
        gex = _compute_contract_gex(contract, spot=600.0, risk_free_rate=0.05)
        assert gex == 0.0

    def test_gex_scales_with_open_interest(self):
        """Doubling OI should double the GEX magnitude."""
        c1 = make_contract(600, "call", open_interest=1000)
        c2 = make_contract(600, "call", open_interest=2000)
        gex1 = _compute_contract_gex(c1, spot=600.0, risk_free_rate=0.05)
        gex2 = _compute_contract_gex(c2, spot=600.0, risk_free_rate=0.05)
        assert gex2 == pytest.approx(2.0 * gex1, rel=1e-6)

    def test_call_and_put_gex_have_opposite_signs(self):
        """Call and put at same strike with same OI should have opposite-signed GEX."""
        call = make_contract(600, "call", open_interest=1000)
        put = make_contract(600, "put", open_interest=1000)
        gex_call = _compute_contract_gex(call, spot=600.0, risk_free_rate=0.05)
        gex_put = _compute_contract_gex(put, spot=600.0, risk_free_rate=0.05)
        assert gex_call > 0
        assert gex_put < 0
        # At ATM, gamma is the same so magnitudes should be equal
        assert abs(gex_call) == pytest.approx(abs(gex_put), rel=1e-6)


# ===================================================================
# Gamma flip detection tests
# ===================================================================

class TestFindGammaFlip:

    def test_no_crossing_all_positive(self):
        """When all net GEX is positive, gamma flip should be None."""
        strikes = [590.0, 595.0, 600.0, 605.0, 610.0]
        net_gex = [100.0, 200.0, 300.0, 200.0, 100.0]
        assert _find_gamma_flip(strikes, net_gex) is None

    def test_no_crossing_all_negative(self):
        """When all net GEX is negative, gamma flip should be None."""
        strikes = [590.0, 595.0, 600.0, 605.0, 610.0]
        net_gex = [-100.0, -200.0, -300.0, -200.0, -100.0]
        assert _find_gamma_flip(strikes, net_gex) is None

    def test_clear_crossing_finds_flip(self):
        """When GEX clearly crosses zero, the flip point should be found."""
        strikes = [590.0, 595.0, 600.0, 605.0, 610.0]
        # Negative at lower strikes, positive at higher strikes
        net_gex = [-200.0, -100.0, 50.0, 200.0, 300.0]
        flip = _find_gamma_flip(strikes, net_gex)
        assert flip is not None
        # Should be between 595 and 600 (where sign changes from -100 to +50)
        assert 595.0 < flip < 600.0

    def test_flip_linear_interpolation(self):
        """Verify linear interpolation gives the correct crossing point."""
        strikes = [100.0, 200.0]
        net_gex = [-50.0, 50.0]
        # Crossing at midpoint: 100 + 50 * (200-100) / (50 - (-50)) = 150
        flip = _find_gamma_flip(strikes, net_gex)
        assert flip == pytest.approx(150.0, abs=1e-10)

    def test_flip_asymmetric_interpolation(self):
        """Verify interpolation with asymmetric values."""
        strikes = [100.0, 200.0]
        # -25 to 75 -> crossing at 100 + 25 * 100 / 100 = 125
        net_gex = [-25.0, 75.0]
        flip = _find_gamma_flip(strikes, net_gex)
        assert flip == pytest.approx(125.0, abs=1e-10)

    def test_single_strike_returns_none(self):
        """A single strike cannot have a crossing."""
        assert _find_gamma_flip([600.0], [100.0]) is None

    def test_empty_strikes_returns_none(self):
        """Empty input should return None."""
        assert _find_gamma_flip([], []) is None

    def test_finds_first_crossing(self):
        """If multiple crossings exist, return the first one."""
        strikes = [100.0, 200.0, 300.0, 400.0]
        # Crosses at 150, then crosses back at 350
        net_gex = [-100.0, 100.0, 100.0, -100.0]
        flip = _find_gamma_flip(strikes, net_gex)
        # Should find the first crossing between 100 and 200
        assert flip is not None
        assert 100.0 < flip < 200.0


# ===================================================================
# Full GEX calculation tests
# ===================================================================

class TestCalculateGEX:

    @patch("src.analysis.gex.config")
    def test_net_gex_with_equal_call_put_oi(self, mock_config):
        """With equal call and put OI at ATM, net GEX should be near zero.

        Calls contribute positive GEX, puts contribute negative GEX.
        At the same strike/OI, the magnitudes cancel out.
        """
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_test_chain(
            spot=600.0,
            strikes=[600.0],
            oi_calls=[1000],
            oi_puts=[1000],
        )
        result = calculate_gex(chain)
        # Net should be approximately zero (call GEX + put GEX cancel)
        assert result.net_gex == pytest.approx(0.0, abs=1e-6)

    @patch("src.analysis.gex.config")
    def test_call_dominated_chain_positive_gex(self, mock_config):
        """Chain with heavy call OI should have positive net GEX."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_test_chain(
            spot=600.0,
            strikes=[600.0],
            oi_calls=[5000],
            oi_puts=[500],
        )
        result = calculate_gex(chain)
        assert result.net_gex > 0

    @patch("src.analysis.gex.config")
    def test_put_dominated_chain_negative_gex(self, mock_config):
        """Chain with heavy put OI should have negative net GEX."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_test_chain(
            spot=600.0,
            strikes=[600.0],
            oi_calls=[500],
            oi_puts=[5000],
        )
        result = calculate_gex(chain)
        assert result.net_gex < 0

    @patch("src.analysis.gex.config")
    def test_gex_result_has_correct_structure(self, mock_config):
        """GEXResult should have all expected fields populated."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_test_chain(spot=600.0)
        result = calculate_gex(chain)

        assert isinstance(result, GEXResult)
        assert isinstance(result.net_gex, float)
        assert result.gamma_ceiling is None or isinstance(result.gamma_ceiling, float)
        assert result.gamma_floor is None or isinstance(result.gamma_floor, float)
        assert isinstance(result.squeeze_probability, float)
        assert len(result.strikes) == 5
        assert len(result.call_gex) == 5
        assert len(result.put_gex) == 5
        assert len(result.net_gex_by_strike) == 5

    @patch("src.analysis.gex.config")
    def test_call_gex_list_all_positive(self, mock_config):
        """All individual call GEX values should be positive."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_test_chain(spot=600.0)
        result = calculate_gex(chain)
        for gex_val in result.call_gex:
            assert gex_val >= 0

    @patch("src.analysis.gex.config")
    def test_put_gex_list_all_negative(self, mock_config):
        """All individual put GEX values should be negative."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_test_chain(spot=600.0)
        result = calculate_gex(chain)
        for gex_val in result.put_gex:
            assert gex_val <= 0

    @patch("src.analysis.gex.config")
    def test_net_gex_is_sum_of_per_strike(self, mock_config):
        """net_gex should equal the sum of net_gex_by_strike."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_test_chain(spot=600.0)
        result = calculate_gex(chain)
        assert result.net_gex == pytest.approx(sum(result.net_gex_by_strike), rel=1e-10)

    @patch("src.analysis.gex.config")
    def test_net_gex_by_strike_equals_call_plus_put(self, mock_config):
        """Each net_gex_by_strike entry should equal call_gex + put_gex at that strike."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_test_chain(spot=600.0)
        result = calculate_gex(chain)
        for i in range(len(result.strikes)):
            expected = result.call_gex[i] + result.put_gex[i]
            assert result.net_gex_by_strike[i] == pytest.approx(expected, rel=1e-10)

    @patch("src.analysis.gex.config")
    def test_empty_chain_returns_zero_gex(self, mock_config):
        """An empty chain should return a zero GEXResult."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = OptionsChain(
            ticker="SPY",
            spot_price=600.0,
            timestamp=datetime.now(),
            contracts=[],
        )
        result = calculate_gex(chain)
        assert result.net_gex == 0.0
        assert result.gamma_flip is None
        assert result.gamma_ceiling is None
        assert result.gamma_floor is None
        assert result.squeeze_probability == 0.0
        assert result.strikes == []

    @patch("src.analysis.gex.config")
    def test_strike_filtering_excludes_far_strikes(self, mock_config):
        """Contracts outside the lookback range should be excluded."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 10  # Only +/- 10 from spot

        chain = make_test_chain(
            spot=600.0,
            strikes=[580.0, 590.0, 600.0, 610.0, 620.0],
            oi_calls=[1000, 1000, 1000, 1000, 1000],
            oi_puts=[1000, 1000, 1000, 1000, 1000],
        )
        result = calculate_gex(chain)
        # Only strikes within [590, 610] should remain
        for s in result.strikes:
            assert 590.0 <= s <= 610.0
        # Strikes 580 and 620 should be excluded
        assert 580.0 not in result.strikes
        assert 620.0 not in result.strikes

    @patch("src.analysis.gex.config")
    def test_gamma_flip_detected_in_asymmetric_chain(self, mock_config):
        """A chain with heavy puts below spot and heavy calls above should have a gamma flip."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        # Heavy puts at low strikes (negative GEX dominates below)
        # Heavy calls at high strikes (positive GEX dominates above)
        # Avoid equal call/put OI at ATM (600) since that yields exactly zero,
        # which _find_gamma_flip does not count as a sign change.
        chain = make_test_chain(
            spot=600.0,
            strikes=[590.0, 595.0, 600.0, 605.0, 610.0],
            oi_calls=[100, 100, 800, 5000, 5000],
            oi_puts=[5000, 5000, 1200, 100, 100],
        )
        result = calculate_gex(chain)
        # Net GEX at low strikes is dominated by puts (negative),
        # at high strikes by calls (positive), with 600 still slightly negative.
        # There should be a gamma flip between 600 and 605.
        assert result.gamma_flip is not None
        assert 590.0 <= result.gamma_flip <= 610.0

    @patch("src.analysis.gex.config")
    def test_squeeze_probability_bounded(self, mock_config):
        """Squeeze probability should always be between 0 and 1."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_test_chain(spot=600.0)
        result = calculate_gex(chain)
        assert 0.0 <= result.squeeze_probability <= 1.0

    @patch("src.analysis.gex.config")
    def test_zero_oi_chain_returns_none_ceiling_floor(self, mock_config):
        """Chain with all OI=0 should return None for ceiling and floor."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_test_chain(
            spot=600.0,
            strikes=[590.0, 595.0, 600.0, 605.0, 610.0],
            oi_calls=[0, 0, 0, 0, 0],
            oi_puts=[0, 0, 0, 0, 0],
        )
        result = calculate_gex(chain)
        assert result.gamma_ceiling is None
        assert result.gamma_floor is None
        assert result.net_gex == 0.0

    @patch("src.analysis.gex.config")
    def test_expiry_filter(self, mock_config):
        """Passing an expiry should filter to only that date's contracts."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        # Create chain with two different expiries
        expiry_near = date.today() + timedelta(days=7)
        expiry_far = date.today() + timedelta(days=30)

        contracts = [
            OptionContract(
                ticker="SPY", expiry=expiry_near, strike=600.0,
                option_type="call", bid=1.0, ask=1.5, last=1.25,
                volume=500, open_interest=2000, iv=0.15,
            ),
            OptionContract(
                ticker="SPY", expiry=expiry_far, strike=600.0,
                option_type="call", bid=2.0, ask=2.5, last=2.25,
                volume=500, open_interest=3000, iv=0.15,
            ),
        ]
        chain = OptionsChain(
            ticker="SPY", spot_price=600.0, timestamp=datetime.now(),
            contracts=contracts,
        )

        result_near = calculate_gex(chain, expiry=expiry_near)
        result_far = calculate_gex(chain, expiry=expiry_far)

        # Different OI should produce different GEX values
        assert result_near.net_gex != result_far.net_gex


# ===================================================================
# Multi-expiry GEX aggregation tests
# ===================================================================

def make_multi_expiry_chain(
    spot: float = 600.0,
    strikes: list[float] | None = None,
    expiry_days: list[int] | None = None,
    oi_per_expiry: dict[int, tuple[list[int], list[int]]] | None = None,
    iv: float = 0.15,
) -> OptionsChain:
    """Build an OptionsChain with contracts across multiple expirations.

    Args:
        spot: Underlying spot price.
        strikes: Strike prices. Defaults to [595, 600, 605].
        expiry_days: Days-to-expiry for each expiration. Defaults to [7, 14, 30].
        oi_per_expiry: Dict mapping days_to_expiry -> (call_oi_list, put_oi_list).
                       If None, uses 1000 OI for all.
        iv: Implied volatility for all contracts.

    Returns:
        OptionsChain with contracts across all specified expirations.
    """
    if strikes is None:
        strikes = [595.0, 600.0, 605.0]
    if expiry_days is None:
        expiry_days = [7, 14, 30]

    contracts = []
    for dte in expiry_days:
        if oi_per_expiry and dte in oi_per_expiry:
            oi_calls, oi_puts = oi_per_expiry[dte]
        else:
            oi_calls = [1000] * len(strikes)
            oi_puts = [1000] * len(strikes)

        for i, k in enumerate(strikes):
            contracts.append(
                make_contract(k, "call", open_interest=oi_calls[i],
                              iv=iv, days_to_expiry=dte)
            )
            contracts.append(
                make_contract(k, "put", open_interest=oi_puts[i],
                              iv=iv, days_to_expiry=dte)
            )

    return OptionsChain(
        ticker="SPY",
        spot_price=spot,
        timestamp=datetime.now(),
        contracts=contracts,
    )


class TestMultiExpiryGEX:

    @patch("src.analysis.gex.config")
    def test_multi_expiry_returns_gex_by_expiry(self, mock_config):
        """When expiry=None, gex_by_expiry should be a dict, not None."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_multi_expiry_chain()
        result = calculate_gex(chain)

        assert result.gex_by_expiry is not None
        assert isinstance(result.gex_by_expiry, dict)

    @patch("src.analysis.gex.config")
    def test_single_expiry_returns_none_gex_by_expiry(self, mock_config):
        """When expiry is specified, gex_by_expiry should be None."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_multi_expiry_chain()
        target_expiry = date.today() + timedelta(days=7)
        result = calculate_gex(chain, expiry=target_expiry)

        assert result.gex_by_expiry is None

    @patch("src.analysis.gex.config")
    def test_gex_by_expiry_has_all_expirations(self, mock_config):
        """gex_by_expiry should contain an entry for each expiration in the chain."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        expiry_days = [7, 14, 30]
        chain = make_multi_expiry_chain(expiry_days=expiry_days)
        result = calculate_gex(chain)

        assert result.gex_by_expiry is not None
        expected_keys = {
            (date.today() + timedelta(days=d)).isoformat() for d in expiry_days
        }
        assert set(result.gex_by_expiry.keys()) == expected_keys

    @patch("src.analysis.gex.config")
    def test_gex_by_expiry_sums_to_net_gex(self, mock_config):
        """Sum of all per-expiry GEX values should equal the aggregate net_gex."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_multi_expiry_chain(
            oi_per_expiry={
                7: ([3000, 2000, 1000], [500, 1000, 2000]),
                14: ([2000, 1500, 1000], [1000, 1500, 2000]),
                30: ([1000, 1000, 1000], [1000, 1000, 1000]),
            }
        )
        result = calculate_gex(chain)

        assert result.gex_by_expiry is not None
        expiry_sum = sum(result.gex_by_expiry.values())
        assert expiry_sum == pytest.approx(result.net_gex, rel=1e-10)

    @patch("src.analysis.gex.config")
    def test_multi_expiry_aggregates_all_contracts(self, mock_config):
        """With expiry=None, net_gex should include contributions from all expirations."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        expiry_days = [7, 30]
        chain = make_multi_expiry_chain(expiry_days=expiry_days)

        # Calculate individual expiry results
        result_7 = calculate_gex(chain, expiry=date.today() + timedelta(days=7))
        result_30 = calculate_gex(chain, expiry=date.today() + timedelta(days=30))
        result_all = calculate_gex(chain)

        # Aggregate should equal sum of individual expiry results
        assert result_all.net_gex == pytest.approx(
            result_7.net_gex + result_30.net_gex, rel=1e-10
        )

    @patch("src.analysis.gex.config")
    def test_gex_by_expiry_matches_individual_runs(self, mock_config):
        """Each per-expiry value should match calculate_gex run with that expiry."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        expiry_days = [7, 14, 30]
        chain = make_multi_expiry_chain(
            expiry_days=expiry_days,
            oi_per_expiry={
                7: ([5000, 3000, 1000], [500, 1000, 3000]),
                14: ([2000, 2000, 2000], [2000, 2000, 2000]),
                30: ([1000, 1000, 5000], [3000, 1000, 500]),
            },
        )
        result_all = calculate_gex(chain)

        for dte in expiry_days:
            exp_date = date.today() + timedelta(days=dte)
            result_single = calculate_gex(chain, expiry=exp_date)
            assert result_all.gex_by_expiry is not None
            assert result_all.gex_by_expiry[exp_date.isoformat()] == pytest.approx(
                result_single.net_gex, rel=1e-10
            )

    @patch("src.analysis.gex.config")
    def test_single_expiry_in_chain_produces_one_entry(self, mock_config):
        """A chain with only one expiration should have exactly one gex_by_expiry entry."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = make_multi_expiry_chain(expiry_days=[14])
        result = calculate_gex(chain)

        assert result.gex_by_expiry is not None
        assert len(result.gex_by_expiry) == 1
        exp_key = (date.today() + timedelta(days=14)).isoformat()
        assert exp_key in result.gex_by_expiry

    @patch("src.analysis.gex.config")
    def test_empty_chain_gex_by_expiry_not_set(self, mock_config):
        """An empty chain should return None for gex_by_expiry (early return path)."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        chain = OptionsChain(
            ticker="SPY",
            spot_price=600.0,
            timestamp=datetime.now(),
            contracts=[],
        )
        result = calculate_gex(chain)

        assert result.gex_by_expiry is None
        assert result.net_gex == 0.0

    @patch("src.analysis.gex.config")
    def test_backward_compat_default_gex_by_expiry(self, mock_config):
        """GEXResult created without gex_by_expiry should default to None."""
        result = GEXResult(
            net_gex=100.0,
            gamma_flip=600.0,
            gamma_ceiling=610.0,
            gamma_floor=590.0,
            squeeze_probability=0.3,
        )
        assert result.gex_by_expiry is None

    @patch("src.analysis.gex.config")
    def test_multi_expiry_preserves_strike_aggregation(self, mock_config):
        """With multiple expiries sharing strikes, per-strike GEX should aggregate correctly."""
        mock_config.risk_free_rate = 0.05
        mock_config.gex_lookback_strikes = 50

        # Both expiries use the same strikes — per-strike lists should combine them
        chain = make_multi_expiry_chain(
            strikes=[600.0],
            expiry_days=[7, 30],
            oi_per_expiry={
                7: ([2000], [1000]),
                30: ([1000], [2000]),
            },
        )
        result = calculate_gex(chain)

        # Should have one unique strike
        assert len(result.strikes) == 1
        assert result.strikes[0] == 600.0
        # net_gex_by_strike should aggregate across both expiries
        assert result.net_gex_by_strike[0] == pytest.approx(result.net_gex, rel=1e-10)
