"""Tests for risk configuration and related constants.

Verifies default values, environment variable overrides,
regime multipliers, and Kelly fractions.
"""

import os
from unittest.mock import patch

import pytest

from src.risk.config import (
    KELLY_FRACTIONS,
    REGIME_MULTIPLIERS,
    RiskConfig,
)


class TestRiskConfigDefaults:
    """Verify all defaults match research doc values."""

    def test_risk_config_defaults(self):
        cfg = RiskConfig()

        # Position-level
        assert cfg.max_position_premium_pct == 0.02
        assert cfg.max_loss_multiplier == 1.5
        assert cfg.max_position_delta == 200.0
        assert cfg.max_position_notional_pct == 0.10
        assert cfg.min_dte == 7
        assert cfg.max_dte == 60

        # Strategy-level
        assert cfg.max_strategy_allocation_pct == 0.20
        assert cfg.max_concurrent_per_strategy == 3
        assert cfg.max_strategy_delta == 300.0
        assert cfg.max_strategy_vega == 5000.0
        assert cfg.max_strategy_daily_loss_pct == 0.03
        assert cfg.max_strategy_weekly_loss_pct == 0.05

        # Portfolio-level
        assert cfg.max_portfolio_delta == 500.0
        assert cfg.max_portfolio_gamma == 100.0
        assert cfg.max_portfolio_vega == 15000.0
        assert cfg.max_daily_theta == -2000.0
        assert cfg.max_daily_loss_pct == 0.05
        assert cfg.max_drawdown_pct == 0.10
        assert cfg.max_expiry_concentration_pct == 0.40
        assert cfg.max_strike_concentration_pct == 0.30
        assert cfg.max_correlated_strategies == 3
        assert cfg.min_cash_reserve_pct == 0.30

        # VaR
        assert cfg.max_var_95_pct == 0.03
        assert cfg.max_var_99_pct == 0.05

        # Circuit breakers
        assert cfg.vix_halt_threshold == 35.0
        assert cfg.vix_resume_threshold == 30.0
        assert cfg.spx_crash_threshold == -0.03
        assert cfg.anomaly_halt_threshold == 0.8
        assert cfg.anomaly_resume_threshold == 0.5
        assert cfg.max_consecutive_order_failures == 3

        # Correlation
        assert cfg.high_correlation_threshold == 0.80
        assert cfg.moderate_correlation_threshold == 0.60

        # Risk-free rate
        assert cfg.risk_free_rate == 0.05

    def test_risk_config_from_env(self):
        """Set env vars, verify override."""
        env_vars = {
            "RISK_MAX_PORTFOLIO_DELTA": "300",
            "RISK_MAX_DRAWDOWN_PCT": "0.15",
            "RISK_MIN_DTE": "14",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            cfg = RiskConfig.from_env()
            assert cfg.max_portfolio_delta == 300.0
            assert cfg.max_drawdown_pct == 0.15
            assert cfg.min_dte == 14

    def test_risk_config_from_env_no_overrides(self):
        """Without env vars, from_env returns defaults."""
        # Clean any RISK_ env vars
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("RISK_")}
        with patch.dict(os.environ, clean_env, clear=True):
            cfg = RiskConfig.from_env()
            assert cfg.max_portfolio_delta == 500.0
            assert cfg.min_dte == 7


class TestRegimeMultipliers:
    """Verify regime multipliers structure."""

    def test_regime_multipliers_all_states(self):
        """Keys 0, 1, 2 must exist with required categories."""
        required_categories = {
            "position_size", "portfolio_delta", "portfolio_gamma",
            "portfolio_vega", "max_concurrent", "daily_loss_pct",
        }
        for state in [0, 1, 2]:
            assert state in REGIME_MULTIPLIERS
            mults = REGIME_MULTIPLIERS[state]
            for cat in required_categories:
                assert cat in mults, f"Missing {cat} in state {state}"
                assert isinstance(mults[cat], float)

    def test_regime_0_is_full_limits(self):
        """Risk-on state should have all 1.0 multipliers."""
        for val in REGIME_MULTIPLIERS[0].values():
            assert val == 1.0

    def test_regime_2_position_size_zero(self):
        """Crisis mode should block new positions."""
        assert REGIME_MULTIPLIERS[2]["position_size"] == 0.0

    def test_regime_1_reduced_limits(self):
        """Risk-off should have reduced (< 1.0) multipliers."""
        for val in REGIME_MULTIPLIERS[1].values():
            assert val <= 1.0


class TestKellyFractions:
    """Verify Kelly fraction constants."""

    def test_kelly_fractions_all_levels(self):
        assert "paper_new" in KELLY_FRACTIONS
        assert "paper_proven" in KELLY_FRACTIONS
        assert KELLY_FRACTIONS["paper_new"] == 0.25
        assert KELLY_FRACTIONS["paper_proven"] == 0.33

    def test_kelly_fractions_ordering(self):
        """Proven strategies should have a higher Kelly fraction."""
        assert KELLY_FRACTIONS["paper_proven"] > KELLY_FRACTIONS["paper_new"]
