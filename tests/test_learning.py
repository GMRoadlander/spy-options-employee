"""Tests for Continuous Learning + Bayesian Calibration pipeline.

Covers OUTCOME_MAP, resolve_outcome, SignalTracker, BayesianCalibrator,
and LearningManager. Uses in-memory SQLite for fast, isolated tests.
"""

import math

import pytest
import pytest_asyncio
import aiosqlite

from src.db.signal_log import SignalLogger
from src.ml.learning import (
    OUTCOME_MAP,
    BayesianCalibrator,
    LearningManager,
    SignalTracker,
    resolve_outcome,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_test_db():
    """Create an in-memory DB with required tables."""
    db = await aiosqlite.connect(":memory:")
    await db.execute("""
        CREATE TABLE signal_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            ticker TEXT NOT NULL,
            direction TEXT NOT NULL DEFAULT 'neutral',
            strength REAL NOT NULL DEFAULT 0.5,
            source TEXT,
            metadata TEXT DEFAULT '{}',
            outcome TEXT,
            outcome_pnl REAL,
            outcome_updated_at TEXT
        )
    """)
    await db.execute("""
        CREATE TABLE model_calibration (
            signal_type TEXT PRIMARY KEY,
            alpha REAL NOT NULL DEFAULT 5.0 CHECK(alpha > 0),
            beta REAL NOT NULL DEFAULT 5.0 CHECK(beta > 0),
            last_signal_id INTEGER NOT NULL DEFAULT 0,
            last_updated TEXT NOT NULL
        )
    """)
    await db.commit()
    return db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db():
    """Create an in-memory SQLite database with required tables."""
    conn = await _setup_test_db()
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def signal_logger(db):
    """Create a SignalLogger backed by the in-memory DB."""
    return SignalLogger(db)


@pytest_asyncio.fixture
async def tracker(signal_logger):
    """Create a SignalTracker wrapping the in-memory SignalLogger."""
    return SignalTracker(signal_logger)


# ---------------------------------------------------------------------------
# Tests: OUTCOME_MAP
# ---------------------------------------------------------------------------


class TestOutcomeMap:
    """Tests for OUTCOME_MAP constant."""

    def test_outcome_map_values(self):
        """OUTCOME_MAP has the correct keys and values."""
        assert OUTCOME_MAP["win"] is True
        assert OUTCOME_MAP["loss"] is False
        assert OUTCOME_MAP["scratch"] is None
        assert OUTCOME_MAP["expired"] is None
        assert len(OUTCOME_MAP) == 4


# ---------------------------------------------------------------------------
# Tests: resolve_outcome
# ---------------------------------------------------------------------------


class TestResolveOutcome:
    """Tests for the resolve_outcome helper function."""

    def test_resolve_outcome_win(self):
        """'win' resolves to True."""
        assert resolve_outcome("win") is True

    def test_resolve_outcome_loss(self):
        """'loss' resolves to False."""
        assert resolve_outcome("loss") is False

    def test_resolve_outcome_scratch_none(self):
        """'scratch' without PnL resolves to None."""
        assert resolve_outcome("scratch") is None

    def test_resolve_outcome_scratch_with_positive_pnl(self):
        """'scratch' with positive PnL resolves to True."""
        assert resolve_outcome("scratch", pnl=50.0) is True

    def test_resolve_outcome_scratch_with_negative_pnl(self):
        """'scratch' with negative PnL resolves to False."""
        assert resolve_outcome("scratch", pnl=-20.0) is False

    def test_resolve_outcome_scratch_with_zero_pnl(self):
        """'scratch' with zero PnL resolves to None (not positive or negative)."""
        assert resolve_outcome("scratch", pnl=0.0) is None

    def test_resolve_outcome_expired(self):
        """'expired' resolves to None."""
        assert resolve_outcome("expired") is None


# ---------------------------------------------------------------------------
# Tests: SignalTracker
# ---------------------------------------------------------------------------


class TestSignalTracker:
    """Tests for the SignalTracker class."""

    @pytest.mark.asyncio
    async def test_record_and_outcome_roundtrip(self, tracker):
        """Record a signal, update outcome, and verify via accuracy."""
        sid = await tracker.record_signal(
            signal_type="gamma_flip",
            ticker="SPY",
            direction="bearish",
            strength=0.8,
            source="test",
        )
        assert sid > 0

        await tracker.record_outcome(sid, "win", pnl=100.0)
        acc = await tracker.get_accuracy(signal_type="gamma_flip", days=30)
        assert acc["total"] == 1
        assert acc["accuracy"] == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_invalid_outcome_raises(self, tracker):
        """Recording an invalid outcome raises ValueError."""
        sid = await tracker.record_signal(
            signal_type="test", ticker="SPY"
        )
        with pytest.raises(ValueError, match="Invalid outcome"):
            await tracker.record_outcome(sid, "bogus")

    @pytest.mark.asyncio
    async def test_get_accuracy_mixed(self, tracker):
        """Accuracy with a mix of wins and losses."""
        for outcome in ["win", "win", "loss", "loss", "loss"]:
            sid = await tracker.record_signal(signal_type="squeeze", ticker="SPY")
            await tracker.record_outcome(sid, outcome)

        acc = await tracker.get_accuracy(days=30)
        assert acc["total"] == 5
        assert acc["accuracy"] == pytest.approx(0.4)

    @pytest.mark.asyncio
    async def test_get_accuracy_by_type(self, tracker):
        """Accuracy breakdown by signal type."""
        # 2 gamma_flip wins
        for _ in range(2):
            sid = await tracker.record_signal(signal_type="gamma_flip", ticker="SPY")
            await tracker.record_outcome(sid, "win")
        # 1 squeeze loss
        sid = await tracker.record_signal(signal_type="squeeze", ticker="SPY")
        await tracker.record_outcome(sid, "loss")

        acc = await tracker.get_accuracy(days=30)
        assert acc["by_type"]["gamma_flip"]["total"] == 2
        assert acc["by_type"]["gamma_flip"]["accuracy"] == pytest.approx(1.0)
        assert acc["by_type"]["squeeze"]["total"] == 1
        assert acc["by_type"]["squeeze"]["accuracy"] == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_get_accuracy_respects_days(self, tracker):
        """Time windowing: old signals outside the window are excluded."""
        from datetime import datetime

        # Record a signal with an old timestamp via the underlying logger
        from src.db.signal_log import SignalEvent
        old_event = SignalEvent(
            signal_type="test",
            ticker="SPY",
            timestamp=datetime(2020, 1, 1),
        )
        old_id = await tracker._logger.log_signal(old_event)
        await tracker._logger.update_outcome(old_id, "win")

        # Record a recent signal
        sid = await tracker.record_signal(signal_type="test", ticker="SPY")
        await tracker.record_outcome(sid, "loss")

        # Only the recent signal should be counted with days=30
        acc = await tracker.get_accuracy(days=30)
        assert acc["total"] == 1
        assert acc["accuracy"] == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_get_new_outcomes(self, tracker):
        """get_new_outcomes returns only outcomes since the given signal ID."""
        ids = []
        for outcome in ["win", "loss", "win"]:
            sid = await tracker.record_signal(signal_type="test", ticker="SPY")
            await tracker.record_outcome(sid, outcome)
            ids.append(sid)

        # Get outcomes since the first signal
        new = await tracker.get_new_outcomes(signal_type="test", since_signal_id=ids[0])
        assert len(new) == 2
        # Should be (id, bool) tuples
        result_ids = [r[0] for r in new]
        assert ids[1] in result_ids
        assert ids[2] in result_ids

    @pytest.mark.asyncio
    async def test_from_connection(self, db):
        """from_connection classmethod creates a working SignalTracker."""
        st = SignalTracker.from_connection(db)
        sid = await st.record_signal(signal_type="test", ticker="SPY")
        assert sid > 0


# ---------------------------------------------------------------------------
# Tests: BayesianCalibrator
# ---------------------------------------------------------------------------


class TestBayesianCalibrator:
    """Tests for the BayesianCalibrator class."""

    def test_uninformative_prior(self):
        """Default prior gives 0.5 confidence."""
        cal = BayesianCalibrator()
        assert cal.get_confidence() == pytest.approx(0.5)

    def test_all_successes(self):
        """All True outcomes push confidence above 0.5."""
        cal = BayesianCalibrator()
        for _ in range(20):
            cal.update_single(True)
        assert cal.get_confidence() > 0.6

    def test_all_failures(self):
        """All False outcomes push confidence below 0.5."""
        cal = BayesianCalibrator()
        for _ in range(20):
            cal.update_single(False)
        assert cal.get_confidence() < 0.4

    def test_known_posterior(self):
        """Verify math: Beta(5+3, 5+2) = Beta(8, 7), mean = 8/15."""
        cal = BayesianCalibrator(prior_accuracy=0.5, prior_strength=10)
        # Prior: alpha=5, beta=5
        outcomes = [True, True, True, False, False]
        cal.update(outcomes)
        # Expected: alpha=5+3=8, beta=5+2=7, mean=8/15
        expected = 8.0 / 15.0
        assert cal.get_confidence() == pytest.approx(expected, abs=1e-10)
        assert cal.alpha == pytest.approx(8.0)
        assert cal.beta == pytest.approx(7.0)

    def test_credible_interval_narrows(self):
        """More data leads to a narrower credible interval."""
        cal_small = BayesianCalibrator()
        cal_small.update([True] * 5 + [False] * 5)
        interval_small = cal_small.get_credible_interval()

        cal_large = BayesianCalibrator()
        cal_large.update([True] * 50 + [False] * 50)
        interval_large = cal_large.get_credible_interval()

        width_small = interval_small[1] - interval_small[0]
        width_large = interval_large[1] - interval_large[0]
        assert width_large < width_small

    def test_save_load_roundtrip(self):
        """save/load preserves state."""
        cal = BayesianCalibrator(prior_accuracy=0.7, prior_strength=20)
        cal.update([True, True, False])
        state = cal.save()

        cal2 = BayesianCalibrator()
        cal2.load(state)
        assert cal2.alpha == pytest.approx(cal.alpha)
        assert cal2.beta == pytest.approx(cal.beta)
        assert cal2.get_confidence() == pytest.approx(cal.get_confidence())

    def test_empty_update(self):
        """Empty list returns current posterior without change."""
        cal = BayesianCalibrator()
        initial = cal.get_confidence()
        result = cal.update([])
        assert result == pytest.approx(initial)

    def test_extreme_alpha_beta(self):
        """No overflow at boundaries -- values are clamped."""
        cal = BayesianCalibrator()
        # Push alpha very high
        cal.alpha = 20000.0
        cal._clamp()
        assert cal.alpha == 10000.0  # _MAX_ALPHA_BETA

        # Push beta very low
        cal.beta = 0.001
        cal._clamp()
        assert cal.beta == pytest.approx(0.01)  # _MIN_ALPHA_BETA

    def test_load_rejects_invalid(self):
        """NaN, inf, and negative values are rejected by load()."""
        cal = BayesianCalibrator()

        with pytest.raises(ValueError, match="NaN"):
            cal.load({"alpha": float("nan"), "beta": 5.0})

        with pytest.raises(ValueError, match="infinity"):
            cal.load({"alpha": float("inf"), "beta": 5.0})

        with pytest.raises(ValueError, match="must be positive"):
            cal.load({"alpha": -1.0, "beta": 5.0})

        with pytest.raises(ValueError, match="must be numeric"):
            cal.load({"alpha": "bad", "beta": 5.0})


# ---------------------------------------------------------------------------
# Tests: LearningManager
# ---------------------------------------------------------------------------


class TestLearningManager:
    """Tests for the LearningManager class."""

    @pytest.mark.asyncio
    async def test_update_calibration(self, tracker, db):
        """End-to-end calibration update with DB."""
        # Record signals with outcomes
        for outcome in ["win", "win", "loss"]:
            sid = await tracker.record_signal(signal_type="gex", ticker="SPY")
            await tracker.record_outcome(sid, outcome)

        mgr = LearningManager(tracker, db)
        results = await mgr.update_calibration(signal_type="gex")

        assert "gex" in results
        assert results["gex"]["new_outcomes"] == 3
        assert results["gex"]["confidence"] > 0.5  # 2 wins, 1 loss + prior

    @pytest.mark.asyncio
    async def test_no_double_counting(self, tracker, db):
        """last_signal_id prevents double-counting outcomes."""
        # Record initial signals
        for outcome in ["win", "loss"]:
            sid = await tracker.record_signal(signal_type="pcr", ticker="SPY")
            await tracker.record_outcome(sid, outcome)

        mgr = LearningManager(tracker, db)

        # First update processes 2 outcomes
        r1 = await mgr.update_calibration(signal_type="pcr")
        assert r1["pcr"]["new_outcomes"] == 2

        # Second update with no new outcomes
        r2 = await mgr.update_calibration(signal_type="pcr")
        assert r2["pcr"]["new_outcomes"] == 0

        # Add a new outcome
        sid = await tracker.record_signal(signal_type="pcr", ticker="SPY")
        await tracker.record_outcome(sid, "win")

        # Third update picks up only the new one
        r3 = await mgr.update_calibration(signal_type="pcr")
        assert r3["pcr"]["new_outcomes"] == 1

    @pytest.mark.asyncio
    async def test_multiple_signal_types(self, tracker, db):
        """Separate calibrators for different signal types."""
        # Record gex signals
        for outcome in ["win", "win"]:
            sid = await tracker.record_signal(signal_type="gex", ticker="SPY")
            await tracker.record_outcome(sid, outcome)

        # Record pcr signals
        for outcome in ["loss", "loss"]:
            sid = await tracker.record_signal(signal_type="pcr", ticker="SPY")
            await tracker.record_outcome(sid, outcome)

        mgr = LearningManager(tracker, db)
        results = await mgr.update_calibration(signal_type="all")

        assert "gex" in results
        assert "pcr" in results
        # gex should have higher confidence than pcr
        assert results["gex"]["confidence"] > results["pcr"]["confidence"]

    @pytest.mark.asyncio
    async def test_insufficient_data_trend(self, tracker, db):
        """Returns 'insufficient_data' when < MIN_SAMPLE signals."""
        # Record only 3 signals (below _MIN_SAMPLE=10)
        for outcome in ["win", "loss", "win"]:
            sid = await tracker.record_signal(signal_type="test", ticker="SPY")
            await tracker.record_outcome(sid, outcome)

        mgr = LearningManager(tracker, db)
        health = await mgr.get_model_health()
        assert health["trend"] == "insufficient_data"

    @pytest.mark.asyncio
    async def test_calibration_survives_restart(self, tracker, db):
        """Calibrator state persists to DB and can be loaded by a new manager."""
        # Record signals and calibrate
        for outcome in ["win", "win", "loss"]:
            sid = await tracker.record_signal(signal_type="gex", ticker="SPY")
            await tracker.record_outcome(sid, outcome)

        mgr1 = LearningManager(tracker, db)
        r1 = await mgr1.update_calibration(signal_type="gex")
        confidence1 = r1["gex"]["confidence"]

        # Create a new manager (simulating restart) with same DB
        mgr2 = LearningManager(tracker, db)
        await mgr2._load_calibrators()

        # The new manager should have the same calibrator state
        assert "gex" in mgr2._calibrators
        assert mgr2._calibrators["gex"].get_confidence() == pytest.approx(confidence1)


# ---------------------------------------------------------------------------
# Tests: Store integration
# ---------------------------------------------------------------------------


class TestStoreIntegration:
    """Tests for Store.init() creating the model_calibration table."""

    @pytest.mark.asyncio
    async def test_store_init_creates_model_calibration_table(self):
        """Store.init() creates the model_calibration table."""
        from src.db.store import Store

        store = Store(db_path=":memory:")
        await store.init()

        db = store._ensure_connected()
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='model_calibration'"
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == "model_calibration"

        await store.close()
