"""Tests for the signal reconciliation engine.

Covers level reconciliation (GEX vs SpotGamma), HIRO reconciliation,
edge cases with None inputs, threshold behavior, confidence formula,
and summary string formatting.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from src.analysis.reconciliation import (
    LevelComparison,
    ReconciliationResult,
    reconcile_hiro,
    reconcile_levels,
)


# ---------------------------------------------------------------------------
# Lightweight stand-ins so tests don't depend on full model imports
# ---------------------------------------------------------------------------


@dataclass
class _FakeSGLevels:
    call_wall: float
    put_wall: float
    vol_trigger: float
    hedge_wall: float = 0.0
    abs_gamma: float = 0.0


@dataclass
class _FakeGEXResult:
    gamma_flip: float | None
    gamma_ceiling: float | None
    gamma_floor: float | None
    net_gex: float = 0.0
    squeeze_probability: float = 0.0


@dataclass
class _FakeSGHIRO:
    hedging_impact: float
    cumulative_impact: float = 0.0


@dataclass
class _FakeDIYHIRO:
    hedging_impact: float
    cumulative_impact: float = 0.0
    call_pressure: float = 0.0
    put_pressure: float = 0.0
    trade_count: int = 0
    timestamp: datetime = datetime(2026, 4, 6, tzinfo=timezone.utc)


# ===================================================================
# reconcile_levels
# ===================================================================


class TestReconcileLevelsFullAgreement:
    """All three levels within the default 15-pt threshold."""

    def test_all_agree(self):
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(gamma_flip=5705.0, gamma_ceiling=5810.0, gamma_floor=5590.0)

        result = reconcile_levels(sg, gex)

        assert result.agreement_count == 3
        assert result.conflict_count == 0
        assert result.agreement_ratio == pytest.approx(1.0)
        assert result.confidence_adjustment == pytest.approx(1.0)
        assert "3/3" in result.summary
        assert "CONFLICT" not in result.summary

    def test_exact_match(self):
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(gamma_flip=5700.0, gamma_ceiling=5800.0, gamma_floor=5600.0)

        result = reconcile_levels(sg, gex)

        assert result.agreement_count == 3
        for comp in result.level_comparisons:
            assert comp.difference == pytest.approx(0.0)
            assert comp.agrees is True


class TestReconcileLevelsFullConflict:
    """All three levels outside the threshold."""

    def test_all_conflict(self):
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(gamma_flip=5750.0, gamma_ceiling=5850.0, gamma_floor=5550.0)

        result = reconcile_levels(sg, gex, threshold=15.0)

        assert result.agreement_count == 0
        assert result.conflict_count == 3
        assert result.agreement_ratio == pytest.approx(0.0)
        assert result.confidence_adjustment == pytest.approx(0.5)
        assert "CONFLICT" in result.summary

    def test_summary_shows_worst_conflict(self):
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(gamma_flip=5750.0, gamma_ceiling=5820.0, gamma_floor=5560.0)

        result = reconcile_levels(sg, gex, threshold=15.0)

        # Gamma flip diff=50 is the worst
        assert "Gamma Flip" in result.summary
        assert "50 pts" in result.summary


class TestReconcileLevelsMixed:
    """Some levels agree, some don't."""

    def test_two_agree_one_conflict(self):
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(
            gamma_flip=5705.0,     # agree (5 pts diff)
            gamma_ceiling=5810.0,  # agree (10 pts diff)
            gamma_floor=5550.0,    # conflict (50 pts diff)
        )

        result = reconcile_levels(sg, gex)

        assert result.agreement_count == 2
        assert result.conflict_count == 1
        assert result.agreement_ratio == pytest.approx(2.0 / 3.0)
        # confidence = 1.0 - 0.5 * (1/3) = ~0.833
        assert result.confidence_adjustment == pytest.approx(1.0 - 0.5 / 3.0)

    def test_one_agree_two_conflict(self):
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(
            gamma_flip=5705.0,     # agree
            gamma_ceiling=5850.0,  # conflict
            gamma_floor=5550.0,    # conflict
        )

        result = reconcile_levels(sg, gex)

        assert result.agreement_count == 1
        assert result.conflict_count == 2
        # confidence = 1.0 - 0.5 * (2/3) = ~0.667
        assert result.confidence_adjustment == pytest.approx(1.0 - 1.0 / 3.0)


class TestReconcileLevelsNoneInputs:
    """Graceful handling of None sources."""

    def test_both_none(self):
        result = reconcile_levels(None, None)

        assert result.agreement_count == 0
        assert result.conflict_count == 0
        assert result.confidence_adjustment == 0.0
        assert "unavailable" in result.summary.lower()

    def test_sg_none(self):
        gex = _FakeGEXResult(gamma_flip=5700.0, gamma_ceiling=5800.0, gamma_floor=5600.0)

        result = reconcile_levels(None, gex)

        assert result.agreement_count == 0
        assert result.conflict_count == 3
        # All comparisons have difference=None (missing SG side)
        for comp in result.level_comparisons:
            assert comp.sg_value is None
            assert comp.difference is None
            assert comp.agrees is False
        assert "unavailable" in result.summary.lower()

    def test_gex_none(self):
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)

        result = reconcile_levels(sg, None)

        assert result.agreement_count == 0
        assert result.conflict_count == 3
        for comp in result.level_comparisons:
            assert comp.our_value is None
            assert comp.difference is None

    def test_gex_with_none_fields(self):
        """GEX result exists but gamma_flip is None (no zero crossing)."""
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(gamma_flip=None, gamma_ceiling=5810.0, gamma_floor=5590.0)

        result = reconcile_levels(sg, gex)

        # gamma_flip comparison disagrees (our side None)
        assert result.agreement_count == 2
        assert result.conflict_count == 1
        flip_comp = result.level_comparisons[0]
        assert flip_comp.our_value is None
        assert flip_comp.agrees is False


class TestReconcileLevelsThreshold:
    """Threshold parameter controls agreement sensitivity."""

    def test_tight_threshold(self):
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(gamma_flip=5705.0, gamma_ceiling=5808.0, gamma_floor=5594.0)

        # Default threshold=15 -> all agree
        result_default = reconcile_levels(sg, gex, threshold=15.0)
        assert result_default.agreement_count == 3

        # Tight threshold=3 -> none agree (diffs are 5, 8, 6)
        result_tight = reconcile_levels(sg, gex, threshold=3.0)
        assert result_tight.agreement_count == 0

    def test_threshold_boundary(self):
        """Exactly at threshold counts as agreement."""
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(gamma_flip=5715.0, gamma_ceiling=5800.0, gamma_floor=5600.0)

        result = reconcile_levels(sg, gex, threshold=15.0)

        flip_comp = result.level_comparisons[0]
        assert flip_comp.difference == pytest.approx(15.0)
        assert flip_comp.agrees is True


class TestConfidenceAdjustment:
    """Validate confidence_adjustment formula across edge cases."""

    def test_formula_zero_conflicts(self):
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(gamma_flip=5700.0, gamma_ceiling=5800.0, gamma_floor=5600.0)

        result = reconcile_levels(sg, gex)
        # 1.0 - 0.5 * (0/3) = 1.0
        assert result.confidence_adjustment == pytest.approx(1.0)

    def test_formula_all_conflicts(self):
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(gamma_flip=5900.0, gamma_ceiling=5900.0, gamma_floor=5400.0)

        result = reconcile_levels(sg, gex)
        # 1.0 - 0.5 * (3/3) = 0.5
        assert result.confidence_adjustment == pytest.approx(0.5)

    def test_confidence_never_below_half(self):
        """Even with missing data on both sides, floor is 0.5."""
        sg = _FakeSGLevels(call_wall=5800.0, put_wall=5600.0, vol_trigger=5700.0)
        gex = _FakeGEXResult(gamma_flip=None, gamma_ceiling=None, gamma_floor=None)

        result = reconcile_levels(sg, gex)
        # 3/3 conflicts (all None on our side)
        assert result.confidence_adjustment >= 0.5


# ===================================================================
# reconcile_hiro
# ===================================================================


class TestReconcileHIRODirectionAgreement:
    """Both HIRO sources point the same way."""

    def test_both_bullish(self):
        sg = _FakeSGHIRO(hedging_impact=0.4)
        diy = _FakeDIYHIRO(hedging_impact=0.5)

        result = reconcile_hiro(sg, diy)

        direction = result.level_comparisons[0]
        assert direction.name == "HIRO Direction"
        assert direction.agrees is True

    def test_both_bearish(self):
        sg = _FakeSGHIRO(hedging_impact=-0.3)
        diy = _FakeDIYHIRO(hedging_impact=-0.6)

        result = reconcile_hiro(sg, diy)

        direction = result.level_comparisons[0]
        assert direction.agrees is True

    def test_both_zero(self):
        sg = _FakeSGHIRO(hedging_impact=0.0)
        diy = _FakeDIYHIRO(hedging_impact=0.0)

        result = reconcile_hiro(sg, diy)

        direction = result.level_comparisons[0]
        assert direction.agrees is True


class TestReconcileHIRODirectionConflict:
    """HIRO sources disagree on direction."""

    def test_opposite_direction(self):
        sg = _FakeSGHIRO(hedging_impact=0.5)
        diy = _FakeDIYHIRO(hedging_impact=-0.3)

        result = reconcile_hiro(sg, diy)

        direction = result.level_comparisons[0]
        assert direction.name == "HIRO Direction"
        assert direction.agrees is False
        assert "CONFLICT" in result.summary or result.conflict_count >= 1


class TestReconcileHIROMagnitude:
    """HIRO magnitude comparison (threshold = 0.3)."""

    def test_similar_magnitude(self):
        sg = _FakeSGHIRO(hedging_impact=0.4)
        diy = _FakeDIYHIRO(hedging_impact=0.5)

        result = reconcile_hiro(sg, diy)

        magnitude = result.level_comparisons[1]
        assert magnitude.name == "HIRO Magnitude"
        assert magnitude.agrees is True  # diff = 0.1, within 0.3

    def test_large_magnitude_difference(self):
        sg = _FakeSGHIRO(hedging_impact=0.8)
        diy = _FakeDIYHIRO(hedging_impact=0.1)

        result = reconcile_hiro(sg, diy)

        magnitude = result.level_comparisons[1]
        assert magnitude.agrees is False  # diff = 0.7, exceeds 0.3


class TestReconcileHIRONoneInputs:
    """HIRO reconciliation with None sources."""

    def test_both_none(self):
        result = reconcile_hiro(None, None)

        assert result.agreement_count == 0
        assert result.conflict_count == 0
        assert result.confidence_adjustment == 0.0
        assert "unavailable" in result.summary.lower()

    def test_sg_hiro_none(self):
        diy = _FakeDIYHIRO(hedging_impact=0.5)

        result = reconcile_hiro(None, diy)

        assert result.conflict_count == 2
        for comp in result.level_comparisons:
            assert comp.sg_value is None
            assert comp.agrees is False

    def test_diy_hiro_none(self):
        sg = _FakeSGHIRO(hedging_impact=-0.3)

        result = reconcile_hiro(sg, None)

        assert result.conflict_count == 2
        for comp in result.level_comparisons:
            assert comp.our_value is None
            assert comp.agrees is False
