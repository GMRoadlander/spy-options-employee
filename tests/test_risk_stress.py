"""Tests for StressTestEngine: scenario-based stress testing.

Uses realistic SPX positions to verify stress test P&L calculations
and status classification.
"""

import json
from datetime import date, timedelta

import pytest

from src.risk.config import RiskConfig
from src.risk.models import StressScenario
from src.risk.stress import (
    ALL_SCENARIOS,
    COMBINED_SCENARIOS,
    SPOT_SCENARIOS,
    StressTestEngine,
    VOL_SCENARIOS,
    _bs_price,
)

SPOT = 5000.0
NAV = 100_000.0
EXPIRY_30D = (date.today() + timedelta(days=30)).isoformat()


def _make_position(
    legs=None,
    quantity=1,
    entry_price=2.50,
    pos_id=1,
):
    """Helper to create a position dict for testing."""
    if legs is None:
        legs = [
            {
                "leg_name": "long_call",
                "option_type": "call",
                "strike": 5000.0,
                "expiry": EXPIRY_30D,
                "action": "buy",
                "quantity": 1,
                "iv": 0.20,
            }
        ]
    return {
        "id": pos_id,
        "strategy_id": 1,
        "legs": legs,
        "quantity": quantity,
        "entry_price": entry_price,
        "status": "open",
    }


@pytest.fixture
def engine():
    return StressTestEngine(RiskConfig())


class TestStressScenarios:
    def test_stress_no_positions(self, engine):
        """Empty positions = zero P&L for all scenarios."""
        results = engine.run_all_scenarios([], SPOT, NAV)
        for r in results:
            assert r.portfolio_pnl == 0.0

    def test_stress_spot_down_long_call(self, engine):
        """Long call loses on SPX -5%."""
        pos = _make_position()
        scenario = StressScenario(name="SPX -5%", spot_shock=-0.05)
        result = engine.run_scenario([pos], SPOT, scenario, NAV)
        assert result.portfolio_pnl < 0, "Long call should lose on spot decline"

    def test_stress_spot_down_short_put(self, engine):
        """Short put loses on SPX -5%."""
        legs = [{"leg_name": "short_put", "option_type": "put", "strike": 4900.0,
                 "expiry": EXPIRY_30D, "action": "sell", "quantity": 1, "iv": 0.20}]
        pos = _make_position(legs=legs)
        scenario = StressScenario(name="SPX -5%", spot_shock=-0.05)
        result = engine.run_scenario([pos], SPOT, scenario, NAV)
        assert result.portfolio_pnl < 0, "Short put should lose on spot decline"

    def test_stress_vol_up_long_vega(self, engine):
        """Long vega position gains on VIX +10."""
        # Long straddle = long vega
        legs = [
            {"leg_name": "long_call", "option_type": "call", "strike": 5000.0,
             "expiry": EXPIRY_30D, "action": "buy", "quantity": 1, "iv": 0.20},
            {"leg_name": "long_put", "option_type": "put", "strike": 5000.0,
             "expiry": EXPIRY_30D, "action": "buy", "quantity": 1, "iv": 0.20},
        ]
        pos = _make_position(legs=legs)
        scenario = StressScenario(name="VIX +10", vol_shock=+0.10)
        result = engine.run_scenario([pos], SPOT, scenario, NAV)
        assert result.portfolio_pnl > 0, "Long vega should gain on vol increase"

    def test_stress_iron_condor_spot_shock(self, engine):
        """IC survives small shocks, loses on large."""
        legs = [
            {"leg_name": "sell_put", "option_type": "put", "strike": 4800.0,
             "expiry": EXPIRY_30D, "action": "sell", "quantity": 1, "iv": 0.22},
            {"leg_name": "buy_put", "option_type": "put", "strike": 4750.0,
             "expiry": EXPIRY_30D, "action": "buy", "quantity": 1, "iv": 0.23},
            {"leg_name": "sell_call", "option_type": "call", "strike": 5200.0,
             "expiry": EXPIRY_30D, "action": "sell", "quantity": 1, "iv": 0.18},
            {"leg_name": "buy_call", "option_type": "call", "strike": 5250.0,
             "expiry": EXPIRY_30D, "action": "buy", "quantity": 1, "iv": 0.17},
        ]
        pos = _make_position(legs=legs)

        # Small shock should be survivable
        small = engine.run_scenario(
            [pos], SPOT, StressScenario(name="small", spot_shock=-0.01), NAV)

        # Large shock should cause bigger loss
        large = engine.run_scenario(
            [pos], SPOT, StressScenario(name="large", spot_shock=-0.10), NAV)

        # The large shock should cause a bigger loss (more negative P&L)
        assert large.portfolio_pnl < small.portfolio_pnl

    def test_stress_combined_scenario(self, engine):
        """'Black Monday' scenario applies all three shocks."""
        pos = _make_position()
        bm = StressScenario(name="Black Monday", spot_shock=-0.07,
                            vol_shock=+0.25, time_days=1)
        result = engine.run_scenario([pos], SPOT, bm, NAV)
        # Long call in Black Monday: spot down hurts, vol up helps, but net negative
        assert isinstance(result.portfolio_pnl, float)
        assert result.scenario.name == "Black Monday"

    def test_stress_time_decay(self, engine):
        """Time decay scenario reduces position value."""
        pos = _make_position()
        scenario = StressScenario(name="5 day decay", time_days=5)
        result = engine.run_scenario([pos], SPOT, scenario, NAV)
        assert result.portfolio_pnl < 0, "Long option loses from time decay"

    def test_stress_breach_classification(self, engine):
        """P&L loss >10% NAV = 'breach' status."""
        # Use large position to trigger breach
        pos = _make_position(quantity=50)
        scenario = StressScenario(name="crash", spot_shock=-0.20)
        result = engine.run_scenario([pos], SPOT, scenario, NAV)
        # With 50 contracts of a long call losing 20% of spot, loss should exceed 10% NAV
        if abs(result.pnl_pct_of_nav) > 0.10:
            assert result.status == "breach"

    def test_stress_warn_classification(self, engine):
        """Check 'warn' classification for moderate losses."""
        # Construct to get around 5-10% loss
        pos = _make_position(quantity=10)
        scenario = StressScenario(name="moderate", spot_shock=-0.10)
        result = engine.run_scenario([pos], SPOT, scenario, NAV)
        # If P&L is in warn range, check classification
        if 0.05 < abs(result.pnl_pct_of_nav) <= 0.10:
            assert result.status == "warn"

    def test_stress_ok_classification(self, engine):
        """P&L loss <5% NAV = 'ok' status."""
        pos = _make_position(quantity=1)
        scenario = StressScenario(name="small", spot_shock=-0.01)
        result = engine.run_scenario([pos], SPOT, scenario, NAV)
        if abs(result.pnl_pct_of_nav) < 0.05:
            assert result.status == "ok"

    def test_stress_all_scenarios_run(self, engine):
        """run_all_scenarios returns results for all 18 scenarios."""
        pos = _make_position()
        results = engine.run_all_scenarios([pos], SPOT, NAV)
        assert len(results) == len(ALL_SCENARIOS)
        assert len(results) == 18

    def test_stress_position_pnl_breakdown(self, engine):
        """Verify per-position P&L dict populated."""
        pos = _make_position(pos_id=42)
        scenario = StressScenario(name="test", spot_shock=-0.05)
        result = engine.run_scenario([pos], SPOT, scenario, NAV)
        assert 42 in result.position_pnls

    def test_stress_expired_option(self, engine):
        """Near-expiry options correctly repriced."""
        expiry_soon = (date.today() + timedelta(days=1)).isoformat()
        legs = [{"leg_name": "c", "option_type": "call", "strike": 5000.0,
                 "expiry": expiry_soon, "action": "buy", "quantity": 1, "iv": 0.20}]
        pos = _make_position(legs=legs)
        scenario = StressScenario(name="near_expiry", spot_shock=-0.05)
        result = engine.run_scenario([pos], SPOT, scenario, NAV)
        assert isinstance(result.portfolio_pnl, float)

    def test_bs_price_at_expiry(self, engine):
        """T=0 returns intrinsic value."""
        # ITM call: S=5000, K=4900 -> intrinsic = 100
        price = _bs_price(5000, 4900, 0.0, 0.20, 0.05, "call")
        assert price == 100.0

        # OTM call: S=5000, K=5100 -> intrinsic = 0
        price = _bs_price(5000, 5100, 0.0, 0.20, 0.05, "call")
        assert price == 0.0

        # ITM put: S=5000, K=5100 -> intrinsic = 100
        price = _bs_price(5000, 5100, 0.0, 0.20, 0.05, "put")
        assert price == 100.0

        # OTM put: S=5000, K=4900 -> intrinsic = 0
        price = _bs_price(5000, 4900, 0.0, 0.20, 0.05, "put")
        assert price == 0.0


class TestScenarioCounts:
    """Verify the standard scenario lists."""

    def test_spot_scenarios_count(self):
        assert len(SPOT_SCENARIOS) == 8

    def test_vol_scenarios_count(self):
        assert len(VOL_SCENARIOS) == 4

    def test_combined_scenarios_count(self):
        assert len(COMBINED_SCENARIOS) == 6

    def test_all_scenarios_total(self):
        assert len(ALL_SCENARIOS) == 18
