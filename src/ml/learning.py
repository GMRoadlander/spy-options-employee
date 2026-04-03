"""Continuous learning pipeline with Bayesian confidence calibration.

Tracks signal outcomes and uses Beta-Binomial conjugate updating to
calibrate model confidence over time. Designed to prevent double-counting
via last_signal_id tracking and to handle scratch trades via P&L-aware
outcome mapping.

Classes:
    SignalTracker -- Wraps SignalLogger for signal recording and outcome tracking.
    BayesianCalibrator -- Beta-Binomial conjugate model for confidence calibration.
    LearningManager -- Async pipeline for calibration updates and model health.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from src.utils import now_et

if TYPE_CHECKING:
    import aiosqlite
    from src.db.signal_log import SignalLogger

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Outcome mapping
# ---------------------------------------------------------------------------

OUTCOME_MAP: dict[str, bool | None] = {
    "win": True,
    "loss": False,
    "scratch": None,   # Excluded from calibration; use P&L sign when available
    "expired": None,   # Excluded
}


def resolve_outcome(outcome: str, pnl: float | None = None) -> bool | None:
    """Map outcome string to bool for calibration, with P&L awareness for scratches.

    Returns True (success), False (failure), or None (exclude from calibration).
    """
    base = OUTCOME_MAP.get(outcome)
    if base is not None:
        return base
    # For scratch/expired with P&L data
    if outcome == "scratch" and pnl is not None:
        if pnl > 0:
            return True
        elif pnl < 0:
            return False
    return None


# ---------------------------------------------------------------------------
# SignalTracker
# ---------------------------------------------------------------------------


class SignalTracker:
    """Wraps SignalLogger for signal recording, outcome tracking, and accuracy queries."""

    def __init__(self, signal_logger: SignalLogger) -> None:
        self._logger = signal_logger

    @classmethod
    def from_connection(cls, db: aiosqlite.Connection) -> SignalTracker:
        """Create a SignalTracker from a raw DB connection."""
        from src.db.signal_log import SignalLogger
        return cls(SignalLogger(db))

    async def record_signal(
        self,
        signal_type: str,
        ticker: str,
        direction: str = "neutral",
        strength: float = 0.5,
        source: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Record a new signal event. Returns the signal ID."""
        from src.db.signal_log import SignalEvent
        event = SignalEvent(
            signal_type=signal_type,
            ticker=ticker,
            direction=direction,
            strength=strength,
            source=source,
            metadata=metadata or {},
        )
        return await self._logger.log_signal(event)

    async def record_outcome(
        self,
        signal_id: int,
        outcome: str,
        pnl: float | None = None,
    ) -> None:
        """Record the outcome for a previously logged signal.

        Raises ValueError if outcome not in OUTCOME_MAP.
        """
        if outcome not in OUTCOME_MAP:
            raise ValueError(
                f"Invalid outcome '{outcome}'. Must be one of: {list(OUTCOME_MAP.keys())}"
            )
        await self._logger.update_outcome(signal_id, outcome, pnl)

    async def get_accuracy(
        self,
        signal_type: str | None = None,
        ticker: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """Compute accuracy stats for signals with outcomes."""
        since = now_et() - timedelta(days=days)
        signals = await self._logger.get_signals(
            ticker=ticker,
            signal_type=signal_type,
            since=since,
            limit=10000,
        )

        # Filter to signals with outcomes
        with_outcomes = [s for s in signals if s.get("outcome") is not None]

        if not with_outcomes:
            return {"total": 0, "accuracy": 0.0, "avg_pnl": 0.0, "by_type": {}}

        total = len(with_outcomes)
        wins = sum(1 for s in with_outcomes if s["outcome"] == "win")

        pnls = [s["outcome_pnl"] for s in with_outcomes if s.get("outcome_pnl") is not None]
        avg_pnl = sum(pnls) / len(pnls) if pnls else 0.0

        # By type breakdown
        by_type: dict[str, dict] = {}
        for s in with_outcomes:
            st = s["signal_type"]
            if st not in by_type:
                by_type[st] = {"total": 0, "wins": 0}
            by_type[st]["total"] += 1
            if s["outcome"] == "win":
                by_type[st]["wins"] += 1

        for st_data in by_type.values():
            st_data["accuracy"] = st_data["wins"] / st_data["total"] if st_data["total"] > 0 else 0.0

        return {
            "total": total,
            "accuracy": wins / total if total > 0 else 0.0,
            "avg_pnl": avg_pnl,
            "by_type": by_type,
        }

    async def get_new_outcomes(
        self,
        signal_type: str | None = None,
        since_signal_id: int = 0,
    ) -> list[tuple[int, bool]]:
        """Get new outcomes since last_signal_id for calibration.

        Returns list of (signal_id, success_bool) tuples. Skips outcomes
        that resolve to None (scratch/expired without P&L).
        """
        # Query signals with outcomes that have ID > since_signal_id
        signals = await self._logger.get_signals(
            signal_type=signal_type,
            limit=10000,
        )

        results = []
        for s in signals:
            if s["id"] <= since_signal_id:
                continue
            if s.get("outcome") is None:
                continue
            resolved = resolve_outcome(s["outcome"], s.get("outcome_pnl"))
            if resolved is not None:
                results.append((s["id"], resolved))

        return results


# ---------------------------------------------------------------------------
# BayesianCalibrator
# ---------------------------------------------------------------------------

_MIN_ALPHA_BETA = 0.01
_MAX_ALPHA_BETA = 10000.0


class BayesianCalibrator:
    """Beta-Binomial conjugate model for confidence calibration.

    Prior: Beta(alpha, beta) where alpha = prior_accuracy * prior_strength.
    Update: alpha += 1 for success, beta += 1 for failure.
    Posterior mean: alpha / (alpha + beta).
    """

    def __init__(self, prior_accuracy: float = 0.5, prior_strength: int = 10) -> None:
        self._prior_alpha = prior_accuracy * prior_strength
        self._prior_beta = (1 - prior_accuracy) * prior_strength
        self.alpha = self._prior_alpha
        self.beta = self._prior_beta

    def _clamp(self) -> None:
        """Clamp alpha/beta to safe bounds."""
        self.alpha = max(_MIN_ALPHA_BETA, min(_MAX_ALPHA_BETA, self.alpha))
        self.beta = max(_MIN_ALPHA_BETA, min(_MAX_ALPHA_BETA, self.beta))

    def update_single(self, outcome: bool) -> float:
        """Update with a single outcome. Returns new posterior mean."""
        if outcome:
            self.alpha += 1.0
        else:
            self.beta += 1.0
        self._clamp()
        return self.get_confidence()

    def update(self, outcomes: list[bool]) -> float:
        """Batch update with multiple outcomes. Returns new posterior mean."""
        if not outcomes:
            return self.get_confidence()
        successes = sum(1 for o in outcomes if o)
        failures = len(outcomes) - successes
        self.alpha += successes
        self.beta += failures
        self._clamp()
        return self.get_confidence()

    def get_confidence(self) -> float:
        """Posterior mean: alpha / (alpha + beta)."""
        total = self.alpha + self.beta
        if total == 0:
            return 0.5
        return self.alpha / total

    def get_credible_interval(self, level: float = 0.95) -> tuple[float, float]:
        """Credible interval using scipy.stats.beta.ppf."""
        from scipy.stats import beta as beta_dist
        tail = (1 - level) / 2
        lower = float(beta_dist.ppf(tail, self.alpha, self.beta))
        upper = float(beta_dist.ppf(1 - tail, self.alpha, self.beta))
        return (lower, upper)

    def save(self) -> dict:
        """Serialize state to dict."""
        return {"alpha": self.alpha, "beta": self.beta}

    def load(self, state: dict) -> None:
        """Load state from dict. Validates values."""
        alpha = state.get("alpha", self._prior_alpha)
        beta_val = state.get("beta", self._prior_beta)

        # Validate
        for name, val in [("alpha", alpha), ("beta", beta_val)]:
            if not isinstance(val, (int, float)):
                raise ValueError(f"Invalid {name}: must be numeric, got {type(val)}")
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Invalid {name}: NaN or infinity")
            if val <= 0:
                raise ValueError(f"Invalid {name}: must be positive, got {val}")

        self.alpha = float(alpha)
        self.beta = float(beta_val)
        self._clamp()


# ---------------------------------------------------------------------------
# LearningManager
# ---------------------------------------------------------------------------

_MIN_SAMPLE = 10


class LearningManager:
    """Async pipeline for calibration updates and model health monitoring."""

    def __init__(self, tracker: SignalTracker, db: aiosqlite.Connection) -> None:
        self._tracker = tracker
        self._db = db
        self._calibrators: dict[str, BayesianCalibrator] = {}
        self._last_signal_ids: dict[str, int] = {}
        self._loaded = False

    async def _load_calibrators(self) -> None:
        """Load calibrator state from model_calibration table."""
        try:
            cursor = await self._db.execute(
                "SELECT signal_type, alpha, beta, last_signal_id FROM model_calibration"
            )
            rows = await cursor.fetchall()

            for signal_type, alpha, beta_val, last_signal_id in rows:
                cal = BayesianCalibrator()
                cal.load({"alpha": alpha, "beta": beta_val})
                self._calibrators[signal_type] = cal
                self._last_signal_ids[signal_type] = last_signal_id

            self._loaded = True
            logger.info("Loaded %d calibrators from database", len(self._calibrators))
        except Exception as exc:
            logger.error("Failed to load calibrators: %s", exc)
            self._loaded = True  # Mark as loaded even on error to prevent retry loops

    async def _save_calibrator(
        self, signal_type: str, cal: BayesianCalibrator, last_signal_id: int
    ) -> None:
        """Persist calibrator state to database."""
        now = now_et().isoformat()
        state = cal.save()
        try:
            await self._db.execute(
                """INSERT OR REPLACE INTO model_calibration
                   (signal_type, alpha, beta, last_signal_id, last_updated)
                   VALUES (?, ?, ?, ?, ?)""",
                (signal_type, state["alpha"], state["beta"], last_signal_id, now),
            )
            await self._db.commit()
        except Exception as exc:
            logger.error("Failed to save calibrator for %s: %s", signal_type, exc)

    async def update_calibration(self, signal_type: str = "all") -> dict:
        """Update calibration using only new outcomes since last_signal_id."""
        if not self._loaded:
            await self._load_calibrators()

        types_to_update = []
        if signal_type == "all":
            # Get all signal types that have outcomes
            signals = await self._tracker._logger.get_signals(limit=10000)
            seen_types = set()
            for s in signals:
                if s.get("outcome") is not None:
                    seen_types.add(s["signal_type"])
            types_to_update = list(seen_types)
            # Also include any types already in calibrators
            for t in self._calibrators:
                if t not in types_to_update:
                    types_to_update.append(t)
        else:
            types_to_update = [signal_type]

        results = {}
        for st in types_to_update:
            last_id = self._last_signal_ids.get(st, 0)
            new_outcomes = await self._tracker.get_new_outcomes(
                signal_type=st,
                since_signal_id=last_id,
            )

            if not new_outcomes:
                if st in self._calibrators:
                    results[st] = {
                        "confidence": self._calibrators[st].get_confidence(),
                        "new_outcomes": 0,
                    }
                continue

            # Create calibrator if needed
            if st not in self._calibrators:
                self._calibrators[st] = BayesianCalibrator()

            cal = self._calibrators[st]
            outcomes = [outcome for _, outcome in new_outcomes]
            max_id = max(sid for sid, _ in new_outcomes)

            cal.update(outcomes)
            self._last_signal_ids[st] = max_id

            # Persist
            await self._save_calibrator(st, cal, max_id)

            results[st] = {
                "confidence": cal.get_confidence(),
                "new_outcomes": len(new_outcomes),
                "alpha": cal.alpha,
                "beta": cal.beta,
            }

        return results

    async def get_model_health(self) -> dict:
        """Compare 7d vs 30d accuracy with MIN_SAMPLE enforcement."""
        if not self._loaded:
            await self._load_calibrators()

        acc_7d = await self._tracker.get_accuracy(days=7)
        acc_30d = await self._tracker.get_accuracy(days=30)

        # Enforce minimum sample size
        trend = "insufficient_data"
        if acc_7d["total"] >= _MIN_SAMPLE and acc_30d["total"] >= _MIN_SAMPLE:
            diff = acc_7d["accuracy"] - acc_30d["accuracy"]
            if diff > 0.05:
                trend = "improving"
            elif diff < -0.05:
                trend = "degrading"
            else:
                trend = "stable"

        health = {
            "accuracy_7d": acc_7d,
            "accuracy_30d": acc_30d,
            "trend": trend,
            "calibrators": {},
        }

        for st, cal in self._calibrators.items():
            interval = cal.get_credible_interval()
            health["calibrators"][st] = {
                "confidence": cal.get_confidence(),
                "credible_interval": interval,
                "alpha": cal.alpha,
                "beta": cal.beta,
            }

        return health
