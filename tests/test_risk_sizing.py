"""Tests for position sizing: Kelly fraction, vol adjustment, anomaly scaling.

Verifies the complete position sizing pipeline with various inputs
including edge cases.
"""

from dataclasses import dataclass

import pytest

from src.risk.config import RiskConfig
from src.risk.sizing import (
    anomaly_multiplier,
    compute_position_size,
    kelly_fraction,
    vol_adjusted_multiplier,
)

NAV = 100_000.0


@dataclass
class MockMetrics:
    """Mock strategy metrics for testing."""
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0


class TestKellyFraction:
    def test_kelly_fraction_basic(self):
        """60% WR, 2:1 ratio = known Kelly value."""
        # b = 200 / 100 = 2, f* = (0.6 * 2 - 0.4) / 2 = 0.4
        result = kelly_fraction(0.6, 200.0, -100.0)
        assert result == pytest.approx(0.4, abs=0.01)

    def test_kelly_fraction_zero_win_rate(self):
        """0% WR = 0.0."""
        result = kelly_fraction(0.0, 200.0, -100.0)
        assert result == 0.0

    def test_kelly_fraction_negative_avg_win(self):
        """avg_win <= 0 = 0.0."""
        result = kelly_fraction(0.6, -50.0, -100.0)
        assert result == 0.0

    def test_kelly_fraction_positive_avg_loss(self):
        """avg_loss >= 0 = 0.0."""
        result = kelly_fraction(0.6, 200.0, 50.0)
        assert result == 0.0

    def test_kelly_fraction_clamped_to_zero(self):
        """Low WR/ratio -> negative Kelly clamped to 0."""
        # WR=20%, 1:1 ratio -> f* = (0.2*1 - 0.8)/1 = -0.6 -> clamped to 0
        result = kelly_fraction(0.2, 100.0, -100.0)
        assert result == 0.0


class TestVolAdjustedMultiplier:
    def test_vol_adjusted_low_vol(self):
        """Vol at average -> multiplier = 1.0."""
        result = vol_adjusted_multiplier(0.15, 0.15)
        assert result == 1.0

    def test_vol_adjusted_below_average(self):
        """Vol below average -> multiplier = 1.0 (no increase)."""
        result = vol_adjusted_multiplier(0.10, 0.15)
        assert result == 1.0

    def test_vol_adjusted_high_vol(self):
        """Vol 2x average -> multiplier = 0.5."""
        result = vol_adjusted_multiplier(0.30, 0.15)
        assert result == pytest.approx(0.5, abs=0.01)

    def test_vol_adjusted_very_high_vol(self):
        """Vol 3x average -> multiplier ~0.33."""
        result = vol_adjusted_multiplier(0.45, 0.15)
        assert result == pytest.approx(1.0 / 3.0, abs=0.01)

    def test_vol_adjusted_zero_vol(self):
        """Zero vol -> multiplier = 1.0."""
        result = vol_adjusted_multiplier(0.0, 0.15)
        assert result == 1.0


class TestAnomalyMultiplier:
    def test_anomaly_multiplier_low(self):
        """Score < 0.3 -> 1.0."""
        assert anomaly_multiplier(0.1) == 1.0
        assert anomaly_multiplier(0.0) == 1.0
        assert anomaly_multiplier(0.29) == 1.0

    def test_anomaly_multiplier_medium(self):
        """Score 0.5-0.7 -> 0.5."""
        assert anomaly_multiplier(0.55) == 0.5
        assert anomaly_multiplier(0.65) == 0.5

    def test_anomaly_multiplier_medium_low(self):
        """Score 0.3-0.5 -> still 1.0 (warning only)."""
        assert anomaly_multiplier(0.35) == 1.0
        assert anomaly_multiplier(0.49) == 1.0

    def test_anomaly_multiplier_high(self):
        """Score > 0.7 -> 0.0."""
        assert anomaly_multiplier(0.75) == 0.0
        assert anomaly_multiplier(0.85) == 0.0
        assert anomaly_multiplier(1.0) == 0.0


class TestComputePositionSize:
    def test_compute_position_size_green_regime(self):
        """Full sizing in risk-on."""
        metrics = MockMetrics(win_rate=0.6, avg_win=200, avg_loss=-100)
        result = compute_position_size(
            nav=NAV,
            strategy_metrics=metrics,
            regime_state=0,
            predicted_vol_1d=0.15,
            anomaly_score_val=0.0,
            config=RiskConfig(),
        )
        assert result.max_premium > 0
        assert result.regime_multiplier == 1.0
        assert result.vol_multiplier == 1.0
        assert result.anomaly_multiplier == 1.0

    def test_compute_position_size_red_regime(self):
        """Zero sizing in crisis."""
        metrics = MockMetrics(win_rate=0.6, avg_win=200, avg_loss=-100)
        result = compute_position_size(
            nav=NAV,
            strategy_metrics=metrics,
            regime_state=2,  # crisis
            predicted_vol_1d=0.15,
            anomaly_score_val=0.0,
            config=RiskConfig(),
        )
        assert result.max_premium == 0.0
        assert result.regime_multiplier == 0.0

    def test_compute_position_size_hard_cap(self):
        """Kelly allocation above cap -> capped at 2% NAV."""
        # Very high Kelly = large allocation, but cap at 2% of NAV = $2,000
        metrics = MockMetrics(win_rate=0.9, avg_win=500, avg_loss=-50)
        config = RiskConfig(max_position_premium_pct=0.02)
        result = compute_position_size(
            nav=NAV,
            strategy_metrics=metrics,
            regime_state=0,
            predicted_vol_1d=0.15,
            anomaly_score_val=0.0,
            config=config,
        )
        assert result.max_premium <= NAV * 0.02

    def test_compute_position_size_rationale(self):
        """Verify rationale string contains all factors."""
        metrics = MockMetrics(win_rate=0.6, avg_win=200, avg_loss=-100)
        result = compute_position_size(
            nav=NAV,
            strategy_metrics=metrics,
            regime_state=0,
            predicted_vol_1d=0.20,
            anomaly_score_val=0.3,
            config=RiskConfig(),
        )
        assert "Kelly raw=" in result.rationale
        assert "Regime=" in result.rationale
        assert "Vol=" in result.rationale
        assert "Anomaly=" in result.rationale
        assert "Final=" in result.rationale

    def test_compute_position_size_no_metrics(self):
        """Missing metrics -> uses hard cap."""
        metrics = MockMetrics()  # All zeros
        result = compute_position_size(
            nav=NAV,
            strategy_metrics=metrics,
            regime_state=0,
            predicted_vol_1d=0.15,
            anomaly_score_val=0.0,
            config=RiskConfig(),
        )
        # With zero Kelly, falls back to hard cap
        assert result.max_premium > 0
        assert result.kelly_raw == 0.0

    def test_compute_position_size_max_contracts(self):
        """Verify max_contracts is estimated."""
        metrics = MockMetrics(win_rate=0.6, avg_win=200, avg_loss=-100)
        result = compute_position_size(
            nav=NAV,
            strategy_metrics=metrics,
            regime_state=0,
            predicted_vol_1d=0.15,
            anomaly_score_val=0.0,
            config=RiskConfig(),
        )
        assert isinstance(result.max_contracts, int)
        assert result.max_contracts >= 0

    def test_compute_position_size_yellow_regime(self):
        """Risk-off regime reduces sizing by 50%."""
        metrics = MockMetrics(win_rate=0.6, avg_win=200, avg_loss=-100)
        green = compute_position_size(
            nav=NAV, strategy_metrics=metrics, regime_state=0,
            predicted_vol_1d=0.15, anomaly_score_val=0.0, config=RiskConfig(),
        )
        yellow = compute_position_size(
            nav=NAV, strategy_metrics=metrics, regime_state=1,
            predicted_vol_1d=0.15, anomaly_score_val=0.0, config=RiskConfig(),
        )
        assert yellow.max_premium < green.max_premium
        assert yellow.regime_multiplier == 0.5
