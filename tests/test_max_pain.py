"""Tests for Max Pain calculations.

Validates the max pain algorithm by hand-calculating total option payouts
at each candidate settlement price and verifying the code matches.
"""

import pytest
from datetime import date, datetime, timedelta

from src.data import OptionContract, OptionsChain
from src.analysis.max_pain import (
    MaxPainResult,
    _compute_pain_at_settlement,
    calculate_max_pain,
    calculate_max_pain_all_expiries,
)


# ---------------------------------------------------------------------------
# Helper: build test contracts and chains
# ---------------------------------------------------------------------------

def _expiry() -> date:
    """Compute a future expiry per-call to avoid midnight flakiness."""
    return date.today() + timedelta(days=30)


def make_contract(
    strike: float,
    option_type: str,
    open_interest: int,
    volume: int = 500,
) -> OptionContract:
    """Create a single OptionContract for max pain testing."""
    return OptionContract(
        ticker="SPY",
        expiry=_expiry(),
        strike=strike,
        option_type=option_type,
        bid=1.0,
        ask=1.5,
        last=1.25,
        volume=volume,
        open_interest=open_interest,
        iv=0.15,
    )


def make_chain(
    spot: float,
    strikes: list[float],
    oi_calls: list[int],
    oi_puts: list[int],
) -> OptionsChain:
    """Build an OptionsChain with calls and puts at each strike."""
    contracts = []
    for i, k in enumerate(strikes):
        contracts.append(make_contract(k, "call", oi_calls[i]))
        contracts.append(make_contract(k, "put", oi_puts[i]))

    return OptionsChain(
        ticker="SPY",
        spot_price=spot,
        timestamp=datetime.now(),
        contracts=contracts,
    )


# ===================================================================
# _compute_pain_at_settlement tests
# ===================================================================

class TestComputePainAtSettlement:

    def test_settlement_at_high_strike_calls_have_value(self):
        """If stock settles at 610, the 590-call (OI=1000) pays (610-590)*1000*100."""
        calls = [make_contract(590, "call", open_interest=1000)]
        puts = []
        pain = _compute_pain_at_settlement(610.0, calls, puts)
        expected = (610 - 590) * 1000 * 100.0
        assert pain == pytest.approx(expected)

    def test_settlement_at_low_strike_puts_have_value(self):
        """If stock settles at 590, the 610-put (OI=1000) pays (610-590)*1000*100."""
        calls = []
        puts = [make_contract(610, "put", open_interest=1000)]
        pain = _compute_pain_at_settlement(590.0, calls, puts)
        expected = (610 - 590) * 1000 * 100.0
        assert pain == pytest.approx(expected)

    def test_settlement_at_strike_no_intrinsic(self):
        """Settlement exactly at a call's strike gives zero call value."""
        calls = [make_contract(600, "call", open_interest=1000)]
        puts = [make_contract(600, "put", open_interest=1000)]
        pain = _compute_pain_at_settlement(600.0, calls, puts)
        assert pain == pytest.approx(0.0)

    def test_zero_oi_contracts_ignored(self):
        """Contracts with zero OI should not contribute to pain."""
        calls = [make_contract(590, "call", open_interest=0)]
        pain = _compute_pain_at_settlement(610.0, calls, [])
        assert pain == pytest.approx(0.0)


# ===================================================================
# Hand-calculated max pain test
# ===================================================================

class TestMaxPainHandCalculated:
    """Verify max pain with a fully hand-calculated example.

    Strikes: 590, 595, 600, 605, 610
    Call OI:  500, 800, 2000, 800, 500
    Put OI:   500, 800, 2000, 800, 500

    For each candidate settlement price, compute total payout:

    Settlement at 590:
      Calls: none ITM (all strikes >= 590, settlement = 590)
      Puts:  595-put pays (595-590)*800*100 = 400,000
             600-put pays (600-590)*2000*100 = 2,000,000
             605-put pays (605-590)*800*100  = 1,200,000
             610-put pays (610-590)*500*100  = 1,000,000
      Total = 4,600,000

    Settlement at 595:
      Calls: 590-call pays (595-590)*500*100 = 250,000
      Puts:  600-put pays (600-595)*2000*100 = 1,000,000
             605-put pays (605-595)*800*100  = 800,000
             610-put pays (610-595)*500*100  = 750,000
      Total = 2,800,000

    Settlement at 600:
      Calls: 590-call pays (600-590)*500*100 = 500,000
             595-call pays (600-595)*800*100 = 400,000
      Puts:  605-put pays (605-600)*800*100  = 400,000
             610-put pays (610-600)*500*100  = 500,000
      Total = 1,800,000

    Settlement at 605:
      Calls: 590-call pays (605-590)*500*100  = 750,000
             595-call pays (605-595)*800*100  = 800,000
             600-call pays (605-600)*2000*100 = 1,000,000
      Puts:  610-put pays (610-605)*500*100   = 250,000
      Total = 2,800,000

    Settlement at 610:
      Calls: 590-call pays (610-590)*500*100  = 1,000,000
             595-call pays (610-595)*800*100  = 1,200,000
             600-call pays (610-600)*2000*100 = 2,000,000
             605-call pays (610-605)*800*100  = 400,000
      Puts:  none ITM
      Total = 4,600,000

    Max pain = 600 (minimum total payout = 1,800,000)
    """

    def setup_method(self):
        """Create the test chain used across this test class."""
        self.strikes = [590.0, 595.0, 600.0, 605.0, 610.0]
        self.oi_calls = [500, 800, 2000, 800, 500]
        self.oi_puts = [500, 800, 2000, 800, 500]
        self.chain = make_chain(
            spot=602.0,
            strikes=self.strikes,
            oi_calls=self.oi_calls,
            oi_puts=self.oi_puts,
        )

    def test_max_pain_strike_is_600(self):
        """Max pain should be at 600 where total payout is minimized."""
        result = calculate_max_pain(self.chain, expiry=_expiry())
        assert result.max_pain_price == pytest.approx(600.0)

    def test_total_pain_at_max_matches_hand_calculation(self):
        """Total pain at the max pain strike should be 1,800,000."""
        result = calculate_max_pain(self.chain, expiry=_expiry())
        assert result.total_pain_at_max == pytest.approx(1_800_000.0)

    def test_pain_at_590_matches(self):
        """Pain at settlement=590 should be 4,600,000."""
        result = calculate_max_pain(self.chain, expiry=_expiry())
        assert result.pain_by_strike[590.0] == pytest.approx(4_600_000.0)

    def test_pain_at_595_matches(self):
        """Pain at settlement=595 should be 2,800,000."""
        result = calculate_max_pain(self.chain, expiry=_expiry())
        assert result.pain_by_strike[595.0] == pytest.approx(2_800_000.0)

    def test_pain_at_600_matches(self):
        """Pain at settlement=600 should be 1,800,000."""
        result = calculate_max_pain(self.chain, expiry=_expiry())
        assert result.pain_by_strike[600.0] == pytest.approx(1_800_000.0)

    def test_pain_at_605_matches(self):
        """Pain at settlement=605 should be 2,800,000."""
        result = calculate_max_pain(self.chain, expiry=_expiry())
        assert result.pain_by_strike[605.0] == pytest.approx(2_800_000.0)

    def test_pain_at_610_matches(self):
        """Pain at settlement=610 should be 4,600,000."""
        result = calculate_max_pain(self.chain, expiry=_expiry())
        assert result.pain_by_strike[610.0] == pytest.approx(4_600_000.0)

    def test_pain_is_symmetric_around_max_pain(self):
        """With symmetric OI, pain at equidistant strikes should be equal."""
        result = calculate_max_pain(self.chain, expiry=_expiry())
        # 590 and 610 are equidistant from 600
        assert result.pain_by_strike[590.0] == pytest.approx(
            result.pain_by_strike[610.0]
        )
        # 595 and 605 are equidistant from 600
        assert result.pain_by_strike[595.0] == pytest.approx(
            result.pain_by_strike[605.0]
        )


# ===================================================================
# Distance percent calculation
# ===================================================================

class TestDistancePercent:

    def test_distance_pct_positive_when_spot_above(self):
        """When spot is above max pain, distance_pct should be positive."""
        # spot=610, max pain should be 600
        chain = make_chain(
            spot=610.0,
            strikes=[590.0, 595.0, 600.0, 605.0, 610.0],
            oi_calls=[500, 800, 2000, 800, 500],
            oi_puts=[500, 800, 2000, 800, 500],
        )
        result = calculate_max_pain(chain, expiry=_expiry())
        assert result.distance_pct > 0

    def test_distance_pct_negative_when_spot_below(self):
        """When spot is below max pain, distance_pct should be negative."""
        # spot=590, max pain should be 600
        chain = make_chain(
            spot=590.0,
            strikes=[590.0, 595.0, 600.0, 605.0, 610.0],
            oi_calls=[500, 800, 2000, 800, 500],
            oi_puts=[500, 800, 2000, 800, 500],
        )
        result = calculate_max_pain(chain, expiry=_expiry())
        assert result.distance_pct < 0

    def test_distance_pct_formula(self):
        """distance_pct = (spot - max_pain) / spot * 100."""
        chain = make_chain(
            spot=610.0,
            strikes=[590.0, 595.0, 600.0, 605.0, 610.0],
            oi_calls=[500, 800, 2000, 800, 500],
            oi_puts=[500, 800, 2000, 800, 500],
        )
        result = calculate_max_pain(chain, expiry=_expiry())
        expected_pct = (610.0 - result.max_pain_price) / 610.0 * 100.0
        assert result.distance_pct == pytest.approx(expected_pct)

    def test_distance_pct_zero_when_at_max_pain(self):
        """When spot equals max pain, distance_pct should be 0."""
        chain = make_chain(
            spot=600.0,
            strikes=[590.0, 595.0, 600.0, 605.0, 610.0],
            oi_calls=[500, 800, 2000, 800, 500],
            oi_puts=[500, 800, 2000, 800, 500],
        )
        result = calculate_max_pain(chain, expiry=_expiry())
        assert result.distance_pct == pytest.approx(0.0, abs=0.01)


# ===================================================================
# Edge cases
# ===================================================================

class TestMaxPainEdgeCases:

    def test_single_strike(self):
        """With only one strike, max pain should be that strike."""
        chain = make_chain(
            spot=600.0,
            strikes=[600.0],
            oi_calls=[1000],
            oi_puts=[1000],
        )
        result = calculate_max_pain(chain, expiry=_expiry())
        assert result.max_pain_price == 600.0
        assert result.total_pain_at_max == 0.0

    def test_two_strikes(self):
        """With two strikes, verify max pain selects the lower-payout one."""
        # At settlement=595: call at 595 pays 0, put at 605 pays (605-595)*1000*100 = 1,000,000
        # At settlement=605: call at 595 pays (605-595)*1000*100 = 1,000,000, put at 605 pays 0
        # Both equal -> should pick first (595) or either is acceptable
        chain = make_chain(
            spot=600.0,
            strikes=[595.0, 605.0],
            oi_calls=[1000, 1000],
            oi_puts=[1000, 1000],
        )
        result = calculate_max_pain(chain, expiry=_expiry())
        assert result.max_pain_price in [595.0, 605.0]
        assert result.total_pain_at_max == pytest.approx(1_000_000.0)

    def test_empty_chain(self):
        """Empty chain should return spot as max pain with zero pain."""
        chain = OptionsChain(
            ticker="SPY",
            spot_price=600.0,
            timestamp=datetime.now(),
            contracts=[],
        )
        result = calculate_max_pain(chain)
        assert result.max_pain_price == 600.0
        assert result.total_pain_at_max == 0.0
        assert result.distance_pct == 0.0

    def test_result_structure(self):
        """MaxPainResult should have all expected fields."""
        chain = make_chain(
            spot=600.0,
            strikes=[590.0, 600.0, 610.0],
            oi_calls=[1000, 2000, 1000],
            oi_puts=[1000, 2000, 1000],
        )
        result = calculate_max_pain(chain, expiry=_expiry())

        assert isinstance(result, MaxPainResult)
        assert isinstance(result.max_pain_price, float)
        assert isinstance(result.total_pain_at_max, float)
        assert isinstance(result.current_price, float)
        assert isinstance(result.distance_pct, float)
        assert isinstance(result.pain_by_strike, dict)
        assert result.current_price == 600.0
        assert result.expiry == _expiry()

    def test_max_pain_is_minimum_pain(self):
        """max_pain_price should have the minimum total_pain across all strikes."""
        chain = make_chain(
            spot=600.0,
            strikes=[590.0, 595.0, 600.0, 605.0, 610.0],
            oi_calls=[500, 800, 2000, 800, 500],
            oi_puts=[500, 800, 2000, 800, 500],
        )
        result = calculate_max_pain(chain, expiry=_expiry())
        min_pain_value = min(result.pain_by_strike.values())
        assert result.total_pain_at_max == pytest.approx(min_pain_value)
        assert result.pain_by_strike[result.max_pain_price] == pytest.approx(
            min_pain_value
        )

    def test_asymmetric_oi_shifts_max_pain(self):
        """Heavy call OI at high strikes should pull max pain upward."""
        # Heavy call OI at 610 means settling higher costs writers more,
        # so max pain should be at or above the middle
        chain_symmetric = make_chain(
            spot=600.0,
            strikes=[590.0, 600.0, 610.0],
            oi_calls=[1000, 1000, 1000],
            oi_puts=[1000, 1000, 1000],
        )
        chain_heavy_high_calls = make_chain(
            spot=600.0,
            strikes=[590.0, 600.0, 610.0],
            oi_calls=[1000, 1000, 10000],
            oi_puts=[1000, 1000, 1000],
        )
        result_sym = calculate_max_pain(chain_symmetric, expiry=_expiry())
        result_heavy = calculate_max_pain(chain_heavy_high_calls, expiry=_expiry())

        # With heavy call OI at 610, max pain should shift up (or stay)
        # because settling above 610 costs more, pulling the minimum higher
        assert result_heavy.max_pain_price >= result_sym.max_pain_price


# ===================================================================
# All expiries test
# ===================================================================

class TestMaxPainAllExpiries:

    def test_returns_result_per_expiry(self):
        """calculate_max_pain_all_expiries should return one result per expiration."""
        expiry1 = date.today() + timedelta(days=7)
        expiry2 = date.today() + timedelta(days=30)

        contracts = [
            OptionContract(
                ticker="SPY", expiry=expiry1, strike=600.0, option_type="call",
                bid=1.0, ask=1.5, last=1.25, volume=500, open_interest=1000, iv=0.15,
            ),
            OptionContract(
                ticker="SPY", expiry=expiry1, strike=600.0, option_type="put",
                bid=1.0, ask=1.5, last=1.25, volume=500, open_interest=1000, iv=0.15,
            ),
            OptionContract(
                ticker="SPY", expiry=expiry2, strike=600.0, option_type="call",
                bid=2.0, ask=2.5, last=2.25, volume=500, open_interest=2000, iv=0.15,
            ),
            OptionContract(
                ticker="SPY", expiry=expiry2, strike=600.0, option_type="put",
                bid=2.0, ask=2.5, last=2.25, volume=500, open_interest=2000, iv=0.15,
            ),
        ]
        chain = OptionsChain(
            ticker="SPY", spot_price=600.0, timestamp=datetime.now(),
            contracts=contracts,
        )

        results = calculate_max_pain_all_expiries(chain)
        assert len(results) == 2
        expiries_returned = {r.expiry for r in results}
        assert expiry1 in expiries_returned
        assert expiry2 in expiries_returned
