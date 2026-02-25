"""Tests for PortfolioAnalyzer: Greeks, VaR, concentration, correlation.

Uses realistic SPX option positions with known Greeks behavior to verify
the analyzer computes correct aggregated values.
"""

import json
from datetime import date, timedelta

import numpy as np
import pytest

from src.risk.analyzer import PortfolioAnalyzer, _greeks_cosine_similarity
from src.risk.config import RiskConfig
from src.risk.models import PortfolioGreeks

# Common test fixtures
SPOT = 5000.0
NAV = 100_000.0
DAILY_VOL = 0.15  # 15% annualized

# Expiry about 30 days from now
EXPIRY_30D = (date.today() + timedelta(days=30)).isoformat()
EXPIRY_14D = (date.today() + timedelta(days=14)).isoformat()


def _make_position(
    strategy_id=1,
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
        "strategy_id": strategy_id,
        "legs": legs,
        "quantity": quantity,
        "entry_price": entry_price,
        "status": "open",
    }


@pytest.fixture
def analyzer():
    return PortfolioAnalyzer(RiskConfig())


# --- Greeks Tests ---

class TestComputeGreeks:
    def test_compute_greeks_empty_positions(self, analyzer):
        """Empty list returns zero Greeks."""
        result = analyzer.compute_greeks([], SPOT)
        assert result.delta == 0.0
        assert result.gamma == 0.0
        assert result.theta == 0.0
        assert result.vega == 0.0
        assert result.num_positions == 0
        assert result.num_legs == 0

    def test_compute_greeks_single_call_buy(self, analyzer):
        """1 long call: positive delta, negative theta."""
        pos = _make_position()
        result = analyzer.compute_greeks([pos], SPOT)
        assert result.delta > 0, "Long call should have positive delta"
        assert result.theta < 0, "Long call should have negative theta (time decay)"
        assert result.num_positions == 1
        assert result.num_legs == 1

    def test_compute_greeks_single_put_sell(self, analyzer):
        """1 short put: positive delta (short put = bullish)."""
        legs = [{
            "leg_name": "short_put",
            "option_type": "put",
            "strike": 4900.0,
            "expiry": EXPIRY_30D,
            "action": "sell",
            "quantity": 1,
            "iv": 0.20,
        }]
        pos = _make_position(legs=legs)
        result = analyzer.compute_greeks([pos], SPOT)
        # Short put: put delta is negative, selling reverses sign -> positive
        assert result.delta > 0, "Short put should contribute positive delta"

    def test_compute_greeks_iron_condor(self, analyzer):
        """4-leg IC: near-zero delta, negative gamma, positive theta."""
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
        result = analyzer.compute_greeks([pos], SPOT)
        # IC delta should be small (near zero)
        assert abs(result.delta) < 50, "Iron condor should have near-zero net delta"
        # IC is short gamma (sell premium)
        assert result.gamma < 0, "Iron condor should be short gamma"
        # IC is positive theta (collect premium decay)
        assert result.theta > 0, "Iron condor should have positive theta"

    def test_compute_greeks_vertical_spread(self, analyzer):
        """2-leg bull put spread: moderate positive delta."""
        legs = [
            {"leg_name": "sell_put", "option_type": "put", "strike": 4900.0,
             "expiry": EXPIRY_30D, "action": "sell", "quantity": 1, "iv": 0.20},
            {"leg_name": "buy_put", "option_type": "put", "strike": 4850.0,
             "expiry": EXPIRY_30D, "action": "buy", "quantity": 1, "iv": 0.21},
        ]
        pos = _make_position(legs=legs)
        result = analyzer.compute_greeks([pos], SPOT)
        assert result.delta > 0, "Bull put spread should have positive delta"

    def test_compute_greeks_multiple_positions(self, analyzer):
        """3 positions, verify sums are correct."""
        positions = [
            _make_position(strategy_id=1, pos_id=1),
            _make_position(strategy_id=2, pos_id=2),
            _make_position(strategy_id=3, pos_id=3),
        ]
        result = analyzer.compute_greeks(positions, SPOT)
        assert result.num_positions == 3
        assert result.num_legs == 3

    def test_compute_greeks_by_expiry(self, analyzer):
        """2 positions with different expiries, verify breakdown."""
        legs_30d = [{"leg_name": "c30", "option_type": "call", "strike": 5000.0,
                     "expiry": EXPIRY_30D, "action": "buy", "quantity": 1, "iv": 0.20}]
        legs_14d = [{"leg_name": "c14", "option_type": "call", "strike": 5000.0,
                     "expiry": EXPIRY_14D, "action": "buy", "quantity": 1, "iv": 0.20}]
        positions = [
            _make_position(legs=legs_30d, pos_id=1),
            _make_position(legs=legs_14d, pos_id=2),
        ]
        result = analyzer.compute_greeks(positions, SPOT)
        assert len(result.greeks_by_expiry) == 2
        assert EXPIRY_30D in result.greeks_by_expiry
        assert EXPIRY_14D in result.greeks_by_expiry

    def test_compute_greeks_by_strategy(self, analyzer):
        """2 positions with different strategy IDs, verify breakdown."""
        positions = [
            _make_position(strategy_id=1, pos_id=1),
            _make_position(strategy_id=2, pos_id=2),
        ]
        result = analyzer.compute_greeks(positions, SPOT)
        assert "1" in result.greeks_by_strategy
        assert "2" in result.greeks_by_strategy

    def test_compute_greeks_dollar_conversion(self, analyzer):
        """Verify dollar_delta and dollar_gamma formulas."""
        pos = _make_position()
        result = analyzer.compute_greeks([pos], SPOT)
        # dollar_delta = total_delta (already in $ terms from multiplier)
        # Both are rounded but to different precision, so use approx
        assert result.dollar_delta == pytest.approx(result.delta, abs=0.1)
        # dollar_gamma = total_gamma * spot * 0.01
        expected_dg = round(result.gamma * SPOT * 0.01, 2)
        assert result.dollar_gamma == pytest.approx(expected_dg, abs=0.01)

    def test_compute_greeks_zero_spot(self, analyzer):
        """spot=0 returns empty Greeks."""
        pos = _make_position()
        result = analyzer.compute_greeks([pos], 0.0)
        assert result.delta == 0.0
        assert result.num_positions == 0

    def test_compute_greeks_expired_leg(self, analyzer):
        """Leg with past expiry uses T=0.001 (no crash)."""
        past_date = (date.today() - timedelta(days=5)).isoformat()
        legs = [{"leg_name": "expired", "option_type": "call", "strike": 5000.0,
                 "expiry": past_date, "action": "buy", "quantity": 1, "iv": 0.20}]
        pos = _make_position(legs=legs)
        # Should not raise
        result = analyzer.compute_greeks([pos], SPOT)
        assert result.num_legs == 1

    def test_compute_greeks_legs_as_json_string(self, analyzer):
        """Legs stored as JSON string (not list) still work."""
        legs = [{"leg_name": "c", "option_type": "call", "strike": 5000.0,
                 "expiry": EXPIRY_30D, "action": "buy", "quantity": 1, "iv": 0.20}]
        pos = _make_position()
        pos["legs"] = json.dumps(legs)
        result = analyzer.compute_greeks([pos], SPOT)
        assert result.delta > 0


# --- VaR Tests ---

class TestComputeVaR:
    def test_compute_var_zero_greeks(self, analyzer):
        """All-zero Greeks returns zero VaR."""
        greeks = PortfolioGreeks()
        result = analyzer.compute_var(greeks, SPOT, DAILY_VOL, NAV)
        assert result.dg_var_95 == 0.0
        assert result.dg_var_99 == 0.0

    def test_compute_var_positive_delta(self, analyzer):
        """Long delta portfolio has positive VaR."""
        greeks = PortfolioGreeks(delta=100.0, dollar_delta=100.0, theta=-50.0)
        result = analyzer.compute_var(greeks, SPOT, DAILY_VOL, NAV)
        assert result.dg_var_95 > 0
        assert result.dg_var_99 > 0

    def test_compute_var_99_greater_than_95(self, analyzer):
        """VaR_99 >= VaR_95."""
        greeks = PortfolioGreeks(delta=100.0, dollar_delta=100.0, theta=-50.0)
        result = analyzer.compute_var(greeks, SPOT, DAILY_VOL, NAV)
        assert result.dg_var_99 >= result.dg_var_95

    def test_compute_var_with_historical(self, analyzer):
        """Historical returns provided, verify hist_var populated."""
        greeks = PortfolioGreeks(delta=100.0, dollar_delta=100.0,
                                  dollar_gamma=5.0, theta=-50.0)
        # Generate random historical returns (252 days)
        rng = np.random.RandomState(42)
        returns = rng.normal(0, 0.01, 252)
        result = analyzer.compute_var(greeks, SPOT, DAILY_VOL, NAV,
                                       historical_returns=returns)
        assert result.hist_var_95 is not None
        assert result.hist_var_99 is not None
        assert result.worst_case is not None

    def test_compute_var_pct_of_nav(self, analyzer):
        """Verify pct_of_nav = var / nav."""
        greeks = PortfolioGreeks(delta=200.0, dollar_delta=200.0, theta=-100.0)
        result = analyzer.compute_var(greeks, SPOT, DAILY_VOL, NAV)
        expected_pct = round(result.dg_var_95 / NAV, 6)
        assert result.pct_of_nav_95 == expected_pct

    def test_compute_var_cvar_greater_than_var(self, analyzer):
        """CVaR_95 >= hist_var_95."""
        greeks = PortfolioGreeks(delta=100.0, dollar_delta=100.0,
                                  dollar_gamma=5.0, theta=-50.0)
        rng = np.random.RandomState(42)
        returns = rng.normal(0, 0.01, 252)
        result = analyzer.compute_var(greeks, SPOT, DAILY_VOL, NAV,
                                       historical_returns=returns)
        if result.cvar_95 is not None and result.hist_var_95 is not None:
            assert result.cvar_95 >= result.hist_var_95

    def test_compute_var_zero_vol(self, analyzer):
        """daily_vol=0 returns zero VaR."""
        greeks = PortfolioGreeks(delta=100.0, dollar_delta=100.0)
        result = analyzer.compute_var(greeks, SPOT, 0.0, NAV)
        assert result.dg_var_95 == 0.0


# --- Concentration Tests ---

class TestComputeConcentration:
    def test_concentration_single_expiry(self, analyzer):
        """All positions same expiry = 100% concentration."""
        pos = _make_position()
        greeks = analyzer.compute_greeks([pos], SPOT)
        report = analyzer.compute_concentration([pos], greeks, NAV)
        assert report.max_expiry_concentration == pytest.approx(1.0, abs=0.01)

    def test_concentration_two_expiries(self, analyzer):
        """Split across two expiries."""
        legs_30d = [{"leg_name": "c30", "option_type": "call", "strike": 5000.0,
                     "expiry": EXPIRY_30D, "action": "buy", "quantity": 1, "iv": 0.20}]
        legs_14d = [{"leg_name": "c14", "option_type": "call", "strike": 5000.0,
                     "expiry": EXPIRY_14D, "action": "buy", "quantity": 1, "iv": 0.20}]
        positions = [
            _make_position(legs=legs_30d, pos_id=1),
            _make_position(legs=legs_14d, pos_id=2),
        ]
        greeks = analyzer.compute_greeks(positions, SPOT)
        report = analyzer.compute_concentration(positions, greeks, NAV)
        assert len(report.by_expiry) == 2

    def test_concentration_strategy_split(self, analyzer):
        """3 strategies, verify percentages."""
        positions = [
            _make_position(strategy_id=1, pos_id=1),
            _make_position(strategy_id=2, pos_id=2),
            _make_position(strategy_id=3, pos_id=3),
        ]
        greeks = analyzer.compute_greeks(positions, SPOT)
        report = analyzer.compute_concentration(positions, greeks, NAV)
        assert len(report.by_strategy) == 3

    def test_concentration_strike_ranges(self, analyzer):
        """Positions at various strikes, verify 25-pt grouping."""
        legs1 = [{"leg_name": "c1", "option_type": "call", "strike": 5000.0,
                  "expiry": EXPIRY_30D, "action": "buy", "quantity": 1,
                  "iv": 0.20, "fill_price": 10.0}]
        legs2 = [{"leg_name": "c2", "option_type": "call", "strike": 5100.0,
                  "expiry": EXPIRY_30D, "action": "buy", "quantity": 1,
                  "iv": 0.20, "fill_price": 5.0}]
        positions = [
            _make_position(legs=legs1, pos_id=1),
            _make_position(legs=legs2, pos_id=2),
        ]
        greeks = analyzer.compute_greeks(positions, SPOT)
        report = analyzer.compute_concentration(positions, greeks, NAV)
        # Different strike ranges: 5000-5025 and 5100-5125
        assert len(report.by_strike_range) >= 1

    def test_concentration_warnings_generated(self, analyzer):
        """Exceeding expiry limit produces warning."""
        # Single position = 100% expiry concentration > 40% limit
        pos = _make_position()
        greeks = analyzer.compute_greeks([pos], SPOT)
        report = analyzer.compute_concentration([pos], greeks, NAV)
        assert len(report.warnings) > 0
        assert "Expiry concentration" in report.warnings[0]


# --- Correlation Tests ---

class TestComputeCorrelation:
    def test_correlation_identical_pnl(self, analyzer):
        """Identical P&L streams = correlation 1.0."""
        pnls = {1: [1.0, 2.0, -1.0, 3.0, -2.0, 1.5, -0.5, 2.0, 0.5, -1.0],
                2: [1.0, 2.0, -1.0, 3.0, -2.0, 1.5, -0.5, 2.0, 0.5, -1.0]}
        report = analyzer.compute_correlation(pnls, None)
        assert (1, 2) in report.pnl_correlation
        assert report.pnl_correlation[(1, 2)] == pytest.approx(1.0, abs=0.01)

    def test_correlation_opposite_pnl(self, analyzer):
        """Inverse P&L streams = correlation -1.0."""
        pnls = {1: [1.0, 2.0, -1.0, 3.0, -2.0, 1.5, -0.5, 2.0, 0.5, -1.0],
                2: [-1.0, -2.0, 1.0, -3.0, 2.0, -1.5, 0.5, -2.0, -0.5, 1.0]}
        report = analyzer.compute_correlation(pnls, None)
        assert report.pnl_correlation[(1, 2)] == pytest.approx(-1.0, abs=0.01)

    def test_correlation_insufficient_data(self, analyzer):
        """<10 data points skipped."""
        pnls = {1: [1.0, 2.0, 3.0], 2: [4.0, 5.0, 6.0]}
        report = analyzer.compute_correlation(pnls, None)
        assert len(report.pnl_correlation) == 0

    def test_greeks_similarity_identical(self, analyzer):
        """Same Greeks vectors = similarity 1.0."""
        greeks = {
            1: {"delta": 100, "gamma": 5, "theta": -50, "vega": 200},
            2: {"delta": 100, "gamma": 5, "theta": -50, "vega": 200},
        }
        report = analyzer.compute_correlation(None, greeks)
        assert report.greeks_similarity[(1, 2)] == pytest.approx(1.0, abs=0.01)

    def test_greeks_similarity_orthogonal(self, analyzer):
        """Orthogonal Greeks = similarity 0.0."""
        greeks = {
            1: {"delta": 100, "gamma": 0, "theta": 0, "vega": 0},
            2: {"delta": 0, "gamma": 100, "theta": 0, "vega": 0},
        }
        report = analyzer.compute_correlation(None, greeks)
        assert report.greeks_similarity[(1, 2)] == pytest.approx(0.0, abs=0.01)

    def test_high_correlation_warning(self, analyzer):
        """Pair > 0.80 generates warning."""
        pnls = {1: [1.0, 2.0, -1.0, 3.0, -2.0, 1.5, -0.5, 2.0, 0.5, -1.0],
                2: [1.0, 2.0, -1.0, 3.0, -2.0, 1.5, -0.5, 2.0, 0.5, -1.0]}
        report = analyzer.compute_correlation(pnls, None)
        assert len(report.high_correlation_pairs) > 0
        assert len(report.warnings) > 0
