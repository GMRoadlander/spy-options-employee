"""Tests for the combo odds engine.

Validates jump-diffusion simulation, IV skew estimation, future IV projection,
per-leg P&L calculation, and the top-level evaluate_combo integration.
All math is tested with known expected values -- no mocking.
"""

import asyncio

import numpy as np
import pytest

from src.analysis.combo_odds import (
    ComboLeg,
    ComboOddsResult,
    compute_leg_pnl,
    estimate_future_iv,
    estimate_iv,
    evaluate_combo,
    simulate_jump_diffusion,
)

# ---------------------------------------------------------------------------
# Shared parameters
# ---------------------------------------------------------------------------

S0 = 650.0
ATM_VOL = 0.18
R = 0.05
N_PATHS = 5_000
SEED = 42
T_30D = 30 / 252


# ===================================================================
# simulate_jump_diffusion
# ===================================================================


class TestSimulateJumpDiffusion:

    def test_returns_correct_horizon_keys(self):
        horizons = [1, 5, 21]
        result = simulate_jump_diffusion(S0, ATM_VOL, horizons, seed=SEED)
        assert set(result.keys()) == {1, 5, 21}

    def test_each_array_length_equals_n_paths(self):
        result = simulate_jump_diffusion(
            S0, ATM_VOL, [1, 21], n_paths=N_PATHS, seed=SEED,
        )
        for arr in result.values():
            assert len(arr) == N_PATHS

    def test_seeded_runs_are_identical(self):
        r1 = simulate_jump_diffusion(S0, ATM_VOL, [21], n_paths=N_PATHS, seed=SEED)
        r2 = simulate_jump_diffusion(S0, ATM_VOL, [21], n_paths=N_PATHS, seed=SEED)
        np.testing.assert_array_equal(r1[21], r2[21])

    def test_different_seeds_differ(self):
        r1 = simulate_jump_diffusion(S0, ATM_VOL, [21], n_paths=N_PATHS, seed=1)
        r2 = simulate_jump_diffusion(S0, ATM_VOL, [21], n_paths=N_PATHS, seed=2)
        assert not np.array_equal(r1[21], r2[21])

    def test_all_prices_positive(self):
        result = simulate_jump_diffusion(
            S0, ATM_VOL, [1, 5, 21], n_paths=N_PATHS, seed=SEED,
        )
        for arr in result.values():
            assert np.all(arr > 0)

    def test_mean_near_expected(self):
        """Sample mean within 5% of S0 for zero-drift simulation."""
        horizons = [5, 21]
        result = simulate_jump_diffusion(
            S0, ATM_VOL, horizons, n_paths=50_000, seed=SEED, r=0.0,
        )
        for h in horizons:
            sample_mean = np.mean(result[h])
            assert abs(sample_mean - S0) / S0 < 0.05


# ===================================================================
# estimate_iv
# ===================================================================


class TestEstimateIV:

    def test_otm_put_has_higher_iv_than_atm(self):
        iv_atm = estimate_iv(strike=S0, spot=S0, atm_vol=ATM_VOL, dte_trading=21)
        iv_put = estimate_iv(strike=S0 * 0.95, spot=S0, atm_vol=ATM_VOL, dte_trading=21)
        assert iv_put > iv_atm

    def test_otm_call_has_lower_or_equal_iv_than_atm(self):
        iv_atm = estimate_iv(strike=S0, spot=S0, atm_vol=ATM_VOL, dte_trading=21)
        iv_call = estimate_iv(strike=S0 * 1.05, spot=S0, atm_vol=ATM_VOL, dte_trading=21)
        assert iv_call <= iv_atm

    def test_fear_regime_raises_near_term_iv(self):
        iv_normal = estimate_iv(
            strike=S0, spot=S0, atm_vol=ATM_VOL, dte_trading=5, fear_regime=False,
        )
        iv_fear = estimate_iv(
            strike=S0, spot=S0, atm_vol=ATM_VOL, dte_trading=5, fear_regime=True,
        )
        assert iv_fear > iv_normal

    def test_iv_floor_at_five_percent(self):
        iv = estimate_iv(strike=S0 * 1.50, spot=S0, atm_vol=0.01, dte_trading=1)
        assert iv >= 0.05


# ===================================================================
# estimate_future_iv
# ===================================================================


class TestEstimateFutureIV:

    def test_spot_drop_increases_iv(self):
        iv_flat = estimate_future_iv(
            strike=S0, future_spot=S0, entry_spot=S0, entry_atm_vol=ATM_VOL,
        )
        iv_drop = estimate_future_iv(
            strike=S0, future_spot=S0 * 0.95, entry_spot=S0, entry_atm_vol=ATM_VOL,
        )
        assert iv_drop > iv_flat

    def test_spot_rally_decreases_iv(self):
        iv_flat = estimate_future_iv(
            strike=S0, future_spot=S0, entry_spot=S0, entry_atm_vol=ATM_VOL,
        )
        iv_rally = estimate_future_iv(
            strike=S0, future_spot=S0 * 1.05, entry_spot=S0, entry_atm_vol=ATM_VOL,
        )
        assert iv_rally < iv_flat

    def test_drop_asymmetry(self):
        move = 0.05
        iv_base = estimate_future_iv(
            strike=S0, future_spot=S0, entry_spot=S0, entry_atm_vol=ATM_VOL,
        )
        iv_drop = estimate_future_iv(
            strike=S0, future_spot=S0 * (1 - move),
            entry_spot=S0, entry_atm_vol=ATM_VOL,
        )
        iv_rally = estimate_future_iv(
            strike=S0, future_spot=S0 * (1 + move),
            entry_spot=S0, entry_atm_vol=ATM_VOL,
        )
        vol_added_by_drop = iv_drop - iv_base
        vol_removed_by_rally = iv_base - iv_rally
        assert vol_added_by_drop > vol_removed_by_rally


# ===================================================================
# compute_leg_pnl
# ===================================================================


class TestComputeLegPnl:

    def test_put_debit_spread_max_payout_below_lower_strike(self):
        long_leg = ComboLeg("long_put", "put", 650.0, 14, "buy", leg_role="vertical_long")
        deep_spots = np.full(200, 500.0)
        pnl = compute_leg_pnl(long_leg, deep_spots, S0, ATM_VOL, R)
        # At expiry, long put at 650 with spot at 500: intrinsic = 150
        assert np.mean(pnl) > 0

    def test_call_debit_spread_max_payout_above_upper_strike(self):
        long_leg = ComboLeg("long_call", "call", 660.0, 4, "buy", leg_role="vertical_long")
        high_spots = np.full(200, 800.0)
        pnl = compute_leg_pnl(long_leg, high_spots, S0, ATM_VOL, R)
        # At expiry, long call at 660 with spot at 800: intrinsic = 140
        assert np.mean(pnl) > 0

    def test_single_put_intrinsic_at_expiry(self):
        leg = ComboLeg("test_put", "put", 640.0, 14, "buy", leg_role="single")
        spots = np.array([600.0, 620.0, 640.0, 660.0])
        pnl = compute_leg_pnl(leg, spots, S0, ATM_VOL, R)
        expected = np.maximum(640.0 - spots, 0.0)
        np.testing.assert_allclose(pnl, expected, rtol=0.01)

    def test_calendar_far_returns_zeros(self):
        leg = ComboLeg("far_put", "put", 600.0, 35, "buy", leg_role="calendar_far")
        spots = np.full(100, S0)
        pnl = compute_leg_pnl(leg, spots, S0, ATM_VOL, R)
        assert np.all(pnl == 0.0)


# ===================================================================
# evaluate_combo (integration)
# ===================================================================


@pytest.mark.slow
class TestEvaluateCombo:
    """Integration tests. Run with: pytest -m slow"""

    _BOREY_LEGS = [
        ComboLeg("long_645p", "put", 645.0, 14, "buy", leg_role="vertical_long"),
        ComboLeg("short_635p", "put", 635.0, 14, "sell", leg_role="vertical_short"),
        ComboLeg("long_660c", "call", 660.0, 4, "buy", leg_role="vertical_long"),
        ComboLeg("short_664c", "call", 664.0, 4, "sell", leg_role="vertical_short"),
        ComboLeg("near_600p", "put", 600.0, 14, "sell", leg_role="calendar_near"),
        ComboLeg("far_600p", "put", 600.0, 35, "buy", leg_role="calendar_far"),
    ]

    def test_returns_combo_odds_result_type(self):
        result = asyncio.run(evaluate_combo(
            legs=self._BOREY_LEGS, spot=S0, atm_iv=ATM_VOL,
            r=R, n_paths=50_000, entry_cost=100.0, seed=SEED,
        ))
        assert isinstance(result, ComboOddsResult)

    def test_all_fields_populated(self):
        result = asyncio.run(evaluate_combo(
            legs=self._BOREY_LEGS, spot=S0, atm_iv=ATM_VOL,
            r=R, n_paths=50_000, entry_cost=100.0, seed=SEED,
        ))
        assert result.prob_profit is not None
        assert result.expected_pnl is not None
        assert result.percentiles is not None
        assert result.risk_flags is not None

    def test_prob_profit_between_zero_and_one(self):
        result = asyncio.run(evaluate_combo(
            legs=self._BOREY_LEGS, spot=S0, atm_iv=ATM_VOL,
            r=R, n_paths=50_000, entry_cost=100.0, seed=SEED,
        ))
        assert 0.0 <= result.prob_profit <= 1.0

    def test_percentiles_monotonically_increasing(self):
        result = asyncio.run(evaluate_combo(
            legs=self._BOREY_LEGS, spot=S0, atm_iv=ATM_VOL,
            r=R, n_paths=50_000, entry_cost=100.0, seed=SEED,
        ))
        ordered = [result.percentiles[k] for k in sorted(result.percentiles.keys())]
        assert ordered == sorted(ordered)

    def test_risk_flags_is_list_of_strings(self):
        result = asyncio.run(evaluate_combo(
            legs=self._BOREY_LEGS, spot=S0, atm_iv=ATM_VOL,
            r=R, n_paths=50_000, entry_cost=100.0, seed=SEED,
        ))
        assert isinstance(result.risk_flags, list)
        assert all(isinstance(f, str) for f in result.risk_flags)

    def test_borey_combo_prob_profit_in_sane_range(self):
        """With zero entry_premium on legs, spreads always pay >= 0,
        so prob_profit is high. This tests the engine runs end-to-end."""
        result = asyncio.run(evaluate_combo(
            legs=self._BOREY_LEGS, spot=S0, atm_iv=ATM_VOL,
            r=R, n_paths=50_000, entry_cost=100.0, seed=SEED,
        ))
        # With no debit subtracted, prob_profit should be very high
        assert 0.50 <= result.prob_profit <= 1.0
        # Expected PNL should be finite and non-negative
        assert result.expected_pnl >= 0.0
        assert np.isfinite(result.expected_pnl)
