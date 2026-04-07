"""Signal reconciliation engine for cross-source level comparison.

When our DIY GEX levels disagree with SpotGamma's published levels, this
module detects the conflict, quantifies the divergence, and produces a
human-readable summary for Discord.

Pure computation -- no I/O, no database, no Discord dependency.

Phase 4 / Step 11 of the SpotGamma integration plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LevelComparison:
    """Single level-vs-level comparison between two sources.

    Attributes:
        name: Human-readable label, e.g. "Gamma Flip / Vol Trigger".
        our_value: Value from our DIY GEX engine (None if unavailable).
        sg_value: Value from SpotGamma (None if unavailable).
        difference: Absolute difference in points (None if either side
            is unavailable).
        agrees: True when both values are present and within the
            threshold.  False when they diverge or one side is missing.
    """

    name: str
    our_value: float | None
    sg_value: float | None
    difference: float | None
    agrees: bool


@dataclass
class ReconciliationResult:
    """Aggregate outcome of reconciling two signal sources.

    Attributes:
        level_comparisons: Individual level-by-level comparisons.
        agreement_count: Number of comparisons that agree.
        conflict_count: Number of comparisons that disagree.
        agreement_ratio: ``agreement_count / total`` (0.0 when no
            comparisons exist).
        confidence_adjustment: Multiplier in [0.5, 1.0].
            1.0 = full agreement, scales down with conflicts.
        summary: Human-readable string for Discord display.
    """

    level_comparisons: list[LevelComparison] = field(default_factory=list)
    agreement_count: int = 0
    conflict_count: int = 0
    agreement_ratio: float = 0.0
    confidence_adjustment: float = 0.0
    summary: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compare_level(
    name: str,
    our_value: float | None,
    sg_value: float | None,
    threshold: float,
) -> LevelComparison:
    """Build a single :class:`LevelComparison`."""
    if our_value is None or sg_value is None:
        return LevelComparison(
            name=name,
            our_value=our_value,
            sg_value=sg_value,
            difference=None,
            agrees=False,
        )
    diff = abs(our_value - sg_value)
    return LevelComparison(
        name=name,
        our_value=our_value,
        sg_value=sg_value,
        difference=diff,
        agrees=diff <= threshold,
    )


def _build_result(comparisons: list[LevelComparison]) -> ReconciliationResult:
    """Aggregate a list of comparisons into a :class:`ReconciliationResult`."""
    if not comparisons:
        return ReconciliationResult(
            level_comparisons=[],
            agreement_count=0,
            conflict_count=0,
            agreement_ratio=0.0,
            confidence_adjustment=0.0,
            summary="No comparisons available",
        )

    total = len(comparisons)
    agree = sum(1 for c in comparisons if c.agrees)
    conflict = total - agree

    ratio = agree / total
    # 1.0 - (0.5 * conflict_count / total), clamped to [0.5, 1.0]
    raw_adj = 1.0 - (0.5 * conflict / total)
    confidence = max(0.5, min(1.0, raw_adj))

    # Build summary string
    if conflict == 0:
        summary = f"{agree}/{total} levels agree"
    else:
        # Highlight the largest conflict
        conflicts = [c for c in comparisons if not c.agrees and c.difference is not None]
        if conflicts:
            worst = max(conflicts, key=lambda c: c.difference)  # type: ignore[arg-type]
            summary = (
                f"CONFLICT: {agree}/{total} levels agree -- "
                f"{worst.name} differs by {worst.difference:.0f} pts"
            )
        else:
            # Conflicts exist but are due to missing data, not divergence
            missing = [c for c in comparisons if not c.agrees and c.difference is None]
            names = ", ".join(c.name for c in missing)
            summary = f"{agree}/{total} levels agree ({names} unavailable)"

    return ReconciliationResult(
        level_comparisons=comparisons,
        agreement_count=agree,
        conflict_count=conflict,
        agreement_ratio=ratio,
        confidence_adjustment=confidence,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def reconcile_levels(
    sg_levels: object | None,
    gex_result: object | None,
    threshold: float = 15.0,
) -> ReconciliationResult:
    """Compare SpotGamma levels against our GEX analysis.

    Comparisons performed:
        - ``sg.vol_trigger`` vs ``gex.gamma_flip``
          (both represent the gamma flip / vol-trigger zone)
        - ``sg.call_wall`` vs ``gex.gamma_ceiling``
          (both represent the max call-gamma strike)
        - ``sg.put_wall`` vs ``gex.gamma_floor``
          (both represent the max put-gamma strike)

    Args:
        sg_levels: A :class:`~src.data.spotgamma_models.SpotGammaLevels`
            instance, or ``None`` if SpotGamma data is unavailable.
        gex_result: A :class:`~src.analysis.gex.GEXResult` instance, or
            ``None`` if our GEX engine produced no result.
        threshold: Maximum point difference to consider "agreement".
            Default is 15 SPX points.

    Returns:
        :class:`ReconciliationResult` with per-level comparisons, counts,
        confidence adjustment, and human-readable summary.
    """
    if sg_levels is None and gex_result is None:
        return ReconciliationResult(
            level_comparisons=[],
            agreement_count=0,
            conflict_count=0,
            agreement_ratio=0.0,
            confidence_adjustment=0.0,
            summary="Both sources unavailable",
        )

    # Extract values, tolerating None on either side
    sg_vol_trigger = getattr(sg_levels, "vol_trigger", None) if sg_levels else None
    sg_call_wall = getattr(sg_levels, "call_wall", None) if sg_levels else None
    sg_put_wall = getattr(sg_levels, "put_wall", None) if sg_levels else None

    gex_flip = getattr(gex_result, "gamma_flip", None) if gex_result else None
    gex_ceiling = getattr(gex_result, "gamma_ceiling", None) if gex_result else None
    gex_floor = getattr(gex_result, "gamma_floor", None) if gex_result else None

    comparisons = [
        _compare_level("Gamma Flip / Vol Trigger", gex_flip, sg_vol_trigger, threshold),
        _compare_level("Call Wall / Gamma Ceiling", gex_ceiling, sg_call_wall, threshold),
        _compare_level("Put Wall / Gamma Floor", gex_floor, sg_put_wall, threshold),
    ]

    return _build_result(comparisons)


def reconcile_hiro(
    sg_hiro: object | None,
    diy_hiro: object | None,
) -> ReconciliationResult:
    """Compare SpotGamma HIRO against our DIY HIRO.

    Comparisons performed:
        - **Direction agreement**: Both bullish (positive hedging_impact),
          both bearish (negative), or conflicting.
        - **Magnitude similarity**: Absolute difference of the normalized
          hedging impact values.

    Args:
        sg_hiro: A :class:`~src.data.spotgamma_models.SpotGammaHIRO`
            instance, or ``None``.
        diy_hiro: A :class:`~src.analysis.hiro.DIYHIROResult` instance,
            or ``None``.

    Returns:
        :class:`ReconciliationResult` with direction and magnitude
        comparisons.
    """
    if sg_hiro is None and diy_hiro is None:
        return ReconciliationResult(
            level_comparisons=[],
            agreement_count=0,
            conflict_count=0,
            agreement_ratio=0.0,
            confidence_adjustment=0.0,
            summary="Both HIRO sources unavailable",
        )

    sg_impact = getattr(sg_hiro, "hedging_impact", None) if sg_hiro else None
    diy_impact = getattr(diy_hiro, "hedging_impact", None) if diy_hiro else None

    comparisons: list[LevelComparison] = []

    # Direction comparison
    if sg_impact is not None and diy_impact is not None:
        # Agree if same sign, or both zero
        same_direction = (
            (sg_impact >= 0 and diy_impact >= 0)
            or (sg_impact < 0 and diy_impact < 0)
        )
        comparisons.append(
            LevelComparison(
                name="HIRO Direction",
                our_value=diy_impact,
                sg_value=sg_impact,
                difference=abs(diy_impact - sg_impact),
                agrees=same_direction,
            )
        )

        # Magnitude comparison -- treat as "agree" if within 0.3 of each other
        # (both values are normalized to [-1, 1])
        mag_diff = abs(diy_impact - sg_impact)
        comparisons.append(
            LevelComparison(
                name="HIRO Magnitude",
                our_value=diy_impact,
                sg_value=sg_impact,
                difference=mag_diff,
                agrees=mag_diff <= 0.3,
            )
        )
    else:
        # One or both sides missing
        comparisons.append(
            LevelComparison(
                name="HIRO Direction",
                our_value=diy_impact,
                sg_value=sg_impact,
                difference=None,
                agrees=False,
            )
        )
        comparisons.append(
            LevelComparison(
                name="HIRO Magnitude",
                our_value=diy_impact,
                sg_value=sg_impact,
                difference=None,
                agrees=False,
            )
        )

    return _build_result(comparisons)


__all__ = [
    "LevelComparison",
    "ReconciliationResult",
    "reconcile_hiro",
    "reconcile_levels",
]
