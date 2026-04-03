"""Tests for HMM regime detection (src/ml/regime.py).

Covers RegimeDetector fit, predict, state sorting, save/load, BIC
model selection, edge cases, and RegimeManager pipeline.
"""

from __future__ import annotations

import pytest

pytest.importorskip("hmmlearn", reason="hmmlearn not installed")

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np

from src.ml.regime import MIN_OBSERVATIONS, RegimeDetector, RegimeManager


# ---------------------------------------------------------------------------
# Helpers — synthetic regime data
# ---------------------------------------------------------------------------


def _make_two_regime_data(
    n_low: int = 300,
    n_high: int = 200,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic returns + VIX with two clear regimes.

    Block 1 (low vol): small returns, low VIX.
    Block 2 (high vol): large returns, high VIX.
    """
    rng = np.random.RandomState(seed)

    # Low-vol block.
    ret_low = rng.normal(0.0005, 0.005, n_low)
    vix_low = rng.normal(14.0, 1.0, n_low)

    # High-vol block.
    ret_high = rng.normal(-0.001, 0.025, n_high)
    vix_high = rng.normal(30.0, 3.0, n_high)

    returns = np.concatenate([ret_low, ret_high])
    vix = np.concatenate([vix_low, vix_high])
    return returns, vix


# ---------------------------------------------------------------------------
# RegimeDetector tests
# ---------------------------------------------------------------------------


class TestRegimeDetectorInit:
    """Constructor and validation."""

    def test_valid_2_state(self) -> None:
        det = RegimeDetector(n_states=2)
        assert det.n_states == 2

    def test_valid_3_state(self) -> None:
        det = RegimeDetector(n_states=3)
        assert det.n_states == 3

    def test_invalid_n_states(self) -> None:
        with pytest.raises(ValueError, match="n_states must be 2 or 3"):
            RegimeDetector(n_states=4)

    def test_invalid_n_states_one(self) -> None:
        with pytest.raises(ValueError, match="n_states must be 2 or 3"):
            RegimeDetector(n_states=1)


class TestRegimeDetectorFit:
    """Fitting the HMM."""

    def test_fit_basic(self) -> None:
        returns, vix = _make_two_regime_data()
        det = RegimeDetector(n_states=2)
        det.fit(returns, vix)
        assert det._fitted is True
        assert det.model is not None

    def test_fit_stores_scaler(self) -> None:
        returns, vix = _make_two_regime_data()
        det = RegimeDetector(n_states=2)
        det.fit(returns, vix)
        assert det._feature_mean is not None
        assert det._feature_std is not None
        assert det._feature_mean.shape == (2,)

    def test_fit_insufficient_data(self) -> None:
        rng = np.random.RandomState(0)
        short_ret = rng.normal(0, 0.01, 100)
        short_vix = rng.normal(15, 1, 100)
        det = RegimeDetector(n_states=2)
        with pytest.raises(ValueError, match="at least"):
            det.fit(short_ret, short_vix)

    def test_fit_mismatched_lengths(self) -> None:
        returns = np.zeros(300)
        vix = np.zeros(200)
        det = RegimeDetector(n_states=2)
        with pytest.raises(ValueError, match="same length"):
            det.fit(returns, vix)

    def test_state_sorting_by_volatility(self) -> None:
        """State 0 should have lower return variance than state 1."""
        returns, vix = _make_two_regime_data()
        det = RegimeDetector(n_states=2)
        det.fit(returns, vix)

        # Get the sorted covariance of returns (feature 0) for each state.
        assert det.model is not None and det._state_perm is not None
        covars = det.model.covars_
        var_state0 = covars[det._state_perm[0]][0, 0]
        var_state1 = covars[det._state_perm[1]][0, 0]
        assert var_state0 < var_state1, "State 0 should have lower variance"

    def test_fit_3_state(self) -> None:
        returns, vix = _make_two_regime_data(n_low=400, n_high=200)
        det = RegimeDetector(n_states=3)
        det.fit(returns, vix)
        assert det._fitted is True
        assert det.n_states == 3

    def test_n_train_obs_stored(self) -> None:
        returns, vix = _make_two_regime_data()
        det = RegimeDetector(n_states=2)
        det.fit(returns, vix)
        assert det._n_train_obs == len(returns)


class TestRegimeDetectorPredict:
    """Prediction from a fitted model."""

    @pytest.fixture()
    def fitted_detector(self) -> RegimeDetector:
        returns, vix = _make_two_regime_data()
        det = RegimeDetector(n_states=2)
        det.fit(returns, vix)
        return det

    def test_predict_returns_dict(self, fitted_detector: RegimeDetector) -> None:
        returns, vix = _make_two_regime_data()
        result = fitted_detector.predict(returns, vix)
        assert isinstance(result, dict)
        assert "state" in result
        assert "state_name" in result
        assert "probabilities" in result
        assert "transition_matrix" in result
        assert "expected_duration" in result

    def test_predict_state_is_int(self, fitted_detector: RegimeDetector) -> None:
        returns, vix = _make_two_regime_data()
        result = fitted_detector.predict(returns, vix)
        assert isinstance(result["state"], int)
        assert result["state"] in (0, 1)

    def test_predict_state_name(self, fitted_detector: RegimeDetector) -> None:
        returns, vix = _make_two_regime_data()
        result = fitted_detector.predict(returns, vix)
        assert result["state_name"] in ("risk-on", "risk-off")

    def test_probabilities_sum_to_one(self, fitted_detector: RegimeDetector) -> None:
        returns, vix = _make_two_regime_data()
        result = fitted_detector.predict(returns, vix)
        total = sum(result["probabilities"])
        assert abs(total - 1.0) < 1e-4, f"Probabilities sum to {total}, expected 1.0"

    def test_transition_matrix_rows_sum_to_one(self, fitted_detector: RegimeDetector) -> None:
        returns, vix = _make_two_regime_data()
        result = fitted_detector.predict(returns, vix)
        for row in result["transition_matrix"]:
            row_sum = sum(row)
            assert abs(row_sum - 1.0) < 1e-4, f"Row sums to {row_sum}"

    def test_expected_duration_positive(self, fitted_detector: RegimeDetector) -> None:
        returns, vix = _make_two_regime_data()
        result = fitted_detector.predict(returns, vix)
        for name, dur in result["expected_duration"].items():
            assert dur > 0, f"Expected duration for {name} should be positive"

    def test_predict_unfitted_raises(self) -> None:
        det = RegimeDetector(n_states=2)
        rng = np.random.RandomState(0)
        with pytest.raises(RuntimeError, match="not been fitted"):
            det.predict(rng.normal(0, 1, 300), rng.normal(15, 1, 300))

    def test_predict_mismatched_lengths(self, fitted_detector: RegimeDetector) -> None:
        with pytest.raises(ValueError, match="same length"):
            fitted_detector.predict(np.zeros(100), np.zeros(50))

    def test_predict_low_vol_data_returns_risk_on(self) -> None:
        """When predicting on purely low-vol data, state should be risk-on."""
        returns, vix = _make_two_regime_data()
        det = RegimeDetector(n_states=2)
        det.fit(returns, vix)

        # Predict on only low-vol data.
        rng = np.random.RandomState(99)
        low_ret = rng.normal(0.0005, 0.005, 300)
        low_vix = rng.normal(14.0, 1.0, 300)
        result = det.predict(low_ret, low_vix)
        assert result["state"] == 0
        assert result["state_name"] == "risk-on"

    def test_predict_high_vol_data_returns_risk_off(self) -> None:
        """When predicting on purely high-vol data, state should be risk-off."""
        returns, vix = _make_two_regime_data()
        det = RegimeDetector(n_states=2)
        det.fit(returns, vix)

        rng = np.random.RandomState(99)
        high_ret = rng.normal(-0.001, 0.025, 300)
        high_vix = rng.normal(30.0, 3.0, 300)
        result = det.predict(high_ret, high_vix)
        assert result["state"] == 1
        assert result["state_name"] == "risk-off"


class TestRegimeDetectorSelectNStates:
    """BIC-based model selection."""

    def test_returns_valid_candidate(self) -> None:
        returns, vix = _make_two_regime_data()
        det = RegimeDetector(n_states=2)
        best = det.select_n_states(returns, vix, candidates=[2, 3])
        assert best in (2, 3)

    def test_default_candidates(self) -> None:
        returns, vix = _make_two_regime_data()
        det = RegimeDetector(n_states=2)
        best = det.select_n_states(returns, vix)
        assert best in (2, 3)


class TestRegimeDetectorPersistence:
    """Save / load roundtrip."""

    def test_save_load_roundtrip(self) -> None:
        returns, vix = _make_two_regime_data()
        det = RegimeDetector(n_states=2)
        det.fit(returns, vix)

        pred_before = det.predict(returns, vix)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "model.pkl")
            det.save(path)
            assert os.path.exists(path)

            det2 = RegimeDetector()
            det2.load(path)
            pred_after = det2.predict(returns, vix)

        assert pred_before["state"] == pred_after["state"]
        assert pred_before["state_name"] == pred_after["state_name"]
        # Probabilities should be very close.
        for a, b in zip(pred_before["probabilities"], pred_after["probabilities"]):
            assert abs(a - b) < 1e-4

    def test_save_unfitted_raises(self) -> None:
        det = RegimeDetector(n_states=2)
        with pytest.raises(RuntimeError, match="not been fitted"):
            det.save("/tmp/should_not_exist.pkl")

    def test_load_nonexistent_raises(self) -> None:
        det = RegimeDetector(n_states=2)
        with pytest.raises(FileNotFoundError):
            det.load("/tmp/nonexistent_model_abc123.pkl")


# ---------------------------------------------------------------------------
# RegimeManager tests
# ---------------------------------------------------------------------------


def _make_mock_feature_store() -> MagicMock:
    """Create a mock FeatureStore with async methods."""
    store = MagicMock()
    store.save_features = AsyncMock()
    store.get_latest_features = AsyncMock(return_value=None)
    return store


class TestRegimeManagerInitialize:
    """RegimeManager.initialize() stores model artifacts."""

    @pytest.mark.asyncio
    async def test_initialize_creates_model_file(self) -> None:
        returns, vix = _make_two_regime_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = RegimeManager(store, tmpdir)
            await mgr.initialize(returns.tolist(), vix.tolist())

            assert mgr.detector is not None
            assert mgr.detector._fitted is True
            assert os.path.exists(mgr.model_path)

    @pytest.mark.asyncio
    async def test_initialize_sets_trained_at(self) -> None:
        returns, vix = _make_two_regime_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = RegimeManager(store, tmpdir)
            await mgr.initialize(returns.tolist(), vix.tolist())
            assert mgr._trained_at is not None

    @pytest.mark.asyncio
    async def test_initialize_populates_rolling_window(self) -> None:
        returns, vix = _make_two_regime_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = RegimeManager(store, tmpdir)
            await mgr.initialize(returns.tolist(), vix.tolist())
            assert len(mgr._returns) == len(returns)
            assert len(mgr._vix) == len(vix)


class TestRegimeManagerUpdate:
    """RegimeManager.update() persists to feature store."""

    @pytest.mark.asyncio
    async def test_update_persists_to_feature_store(self) -> None:
        returns, vix = _make_two_regime_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = RegimeManager(store, tmpdir)
            await mgr.initialize(returns.tolist(), vix.tolist())

            result = await mgr.update(0.001, 15.0, ticker="SPX")

            assert isinstance(result, dict)
            assert "state" in result
            assert "state_name" in result
            store.save_features.assert_called()
            call_args = store.save_features.call_args
            assert call_args[0][0] == "SPX"
            features = call_args[0][2]
            assert "regime_state" in features
            assert "regime_probability" in features

    @pytest.mark.asyncio
    async def test_update_appends_to_rolling_window(self) -> None:
        returns, vix = _make_two_regime_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = RegimeManager(store, tmpdir)
            await mgr.initialize(returns.tolist(), vix.tolist())

            initial_len = len(mgr._returns)
            await mgr.update(0.002, 16.0)
            assert len(mgr._returns) == initial_len + 1

    @pytest.mark.asyncio
    async def test_update_without_initialize_raises(self) -> None:
        store = _make_mock_feature_store()
        mgr = RegimeManager(store, "/tmp/nonexistent")
        with pytest.raises(RuntimeError, match="not initialized"):
            await mgr.update(0.001, 15.0)


class TestRegimeManagerGetCurrentRegime:
    """RegimeManager.get_current_regime() reads from feature store."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_data(self) -> None:
        store = _make_mock_feature_store()
        store.get_latest_features.return_value = None
        mgr = RegimeManager(store, "/tmp")
        result = await mgr.get_current_regime("SPX")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_regime_from_store(self) -> None:
        store = _make_mock_feature_store()
        store.get_latest_features.return_value = {
            "regime_state": 0,
            "regime_probability": 0.92,
        }
        mgr = RegimeManager(store, "/tmp")
        result = await mgr.get_current_regime("SPX")
        assert result is not None
        assert result["regime_state"] == 0
        assert result["regime_probability"] == 0.92
        assert result["state_name"] == "risk-on"

    @pytest.mark.asyncio
    async def test_returns_none_when_regime_state_missing(self) -> None:
        store = _make_mock_feature_store()
        store.get_latest_features.return_value = {
            "regime_state": None,
            "regime_probability": None,
        }
        mgr = RegimeManager(store, "/tmp")
        result = await mgr.get_current_regime("SPX")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_regime_includes_duration_after_update(self) -> None:
        """After update(), get_current_regime includes expected_duration and transition_matrix."""
        returns, vix = _make_two_regime_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            # Return regime data from the feature store so get_current_regime
            # doesn't return None.
            store.get_latest_features.return_value = {
                "regime_state": 0,
                "regime_probability": 0.90,
            }
            mgr = RegimeManager(store, tmpdir)
            await mgr.initialize(returns.tolist(), vix.tolist())
            await mgr.update(0.001, 15.0, ticker="SPX")

            result = await mgr.get_current_regime("SPX")
            assert result is not None
            assert "expected_duration" in result
            assert "transition_matrix" in result
            assert isinstance(result["expected_duration"], dict)
            assert isinstance(result["transition_matrix"], list)

    @pytest.mark.asyncio
    async def test_get_current_regime_no_cached_prediction(self) -> None:
        """Without a prior update(), result has no expected_duration or transition_matrix."""
        store = _make_mock_feature_store()
        store.get_latest_features.return_value = {
            "regime_state": 0,
            "regime_probability": 0.85,
        }
        mgr = RegimeManager(store, "/tmp")
        result = await mgr.get_current_regime("SPX")
        assert result is not None
        assert "expected_duration" not in result
        assert "transition_matrix" not in result


class TestRegimeManagerShouldRetrain:
    """Retrain heuristic tests."""

    @pytest.mark.asyncio
    async def test_retrain_when_never_trained(self) -> None:
        store = _make_mock_feature_store()
        mgr = RegimeManager(store, "/tmp")
        assert await mgr.should_retrain() is True

    @pytest.mark.asyncio
    async def test_no_retrain_when_recently_trained(self) -> None:
        returns, vix = _make_two_regime_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = RegimeManager(store, tmpdir)
            await mgr.initialize(returns.tolist(), vix.tolist())

            # Just trained, should not need retrain.
            assert await mgr.should_retrain() is False

    @pytest.mark.asyncio
    async def test_retrain_when_old_model(self) -> None:
        returns, vix = _make_two_regime_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = RegimeManager(store, tmpdir)
            await mgr.initialize(returns.tolist(), vix.tolist())

            # Fake an old training date (timezone-aware to match now_et).
            from src.utils import now_et
            mgr._trained_at = now_et() - timedelta(days=31)
            assert await mgr.should_retrain() is True

    @pytest.mark.asyncio
    async def test_retrain_on_frequent_transitions(self) -> None:
        returns, vix = _make_two_regime_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = RegimeManager(store, tmpdir)
            await mgr.initialize(returns.tolist(), vix.tolist())

            # Simulate frequent regime transitions (>3 in 5 observations).
            mgr._recent_states = [0, 1, 0, 1, 0]
            assert await mgr.should_retrain() is True

    @pytest.mark.asyncio
    async def test_no_retrain_stable_transitions(self) -> None:
        returns, vix = _make_two_regime_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = RegimeManager(store, tmpdir)
            await mgr.initialize(returns.tolist(), vix.tolist())

            # Stable: all same state, 0 transitions.
            mgr._recent_states = [0, 0, 0, 0, 0]
            assert await mgr.should_retrain() is False
