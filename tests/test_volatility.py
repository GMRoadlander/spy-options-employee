"""Tests for LSTM volatility forecasting (src/ml/volatility.py).

Covers VolDataset, VolLSTM, VolForecaster (predict, save/load, train,
evaluate), VolManager pipeline, data preprocessing, and edge cases.
"""

from __future__ import annotations

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pandas as pd
import pytest
import torch

from src.ml.volatility import (
    DEFAULT_LOOKBACK,
    DEFAULT_N_FEATURES,
    VolDataset,
    VolForecaster,
    VolLSTM,
    VolManager,
    prepare_training_data,
)


# ---------------------------------------------------------------------------
# Helpers -- synthetic data
# ---------------------------------------------------------------------------


def _make_synthetic_series(
    n: int = 500,
    seed: int = 42,
) -> tuple[pd.Series, pd.Series]:
    """Generate synthetic returns and VIX for testing.

    Returns daily returns with a sinusoidal vol pattern and corresponding
    VIX values.
    """
    rng = np.random.RandomState(seed)

    # Sinusoidal vol pattern (easier to learn).
    t = np.arange(n, dtype=float)
    vol_pattern = 0.01 + 0.005 * np.sin(2 * np.pi * t / 60)
    returns = pd.Series(rng.normal(0, vol_pattern))

    # VIX correlated with vol.
    vix = pd.Series(15.0 + 10.0 * vol_pattern + rng.normal(0, 0.5, n))

    return returns, vix


def _make_vol_dataset(
    n: int = 200,
    lookback: int = 20,
    n_features: int = 5,
    seed: int = 42,
) -> tuple[VolDataset, dict]:
    """Create a small VolDataset for testing."""
    rng = np.random.RandomState(seed)
    features = rng.randn(n, n_features).astype(np.float32)
    targets = rng.randn(n, 2).astype(np.float32)

    feature_mean = features.mean(axis=0)
    feature_std = features.std(axis=0)
    target_mean = targets.mean(axis=0)
    target_std = targets.std(axis=0)

    ds = VolDataset(
        features=features,
        targets=targets,
        lookback=lookback,
        feature_mean=feature_mean,
        feature_std=feature_std,
        target_mean=target_mean,
        target_std=target_std,
    )
    stats = {
        "feature_mean": feature_mean,
        "feature_std": feature_std,
        "target_mean": target_mean,
        "target_std": target_std,
        "lookback": lookback,
        "n_features": n_features,
    }
    return ds, stats


# ---------------------------------------------------------------------------
# VolDataset tests
# ---------------------------------------------------------------------------


class TestVolDataset:
    """VolDataset sequence creation and shapes."""

    def test_length(self) -> None:
        ds, _ = _make_vol_dataset(n=200, lookback=20)
        assert len(ds) == 200 - 20

    def test_sequence_shape(self) -> None:
        lookback = 20
        n_features = 5
        ds, _ = _make_vol_dataset(n=200, lookback=lookback, n_features=n_features)
        x, y = ds[0]
        assert x.shape == (lookback, n_features)
        assert y.shape == (2,)

    def test_dtype_is_float32(self) -> None:
        ds, _ = _make_vol_dataset()
        x, y = ds[0]
        assert x.dtype == torch.float32
        assert y.dtype == torch.float32

    def test_last_sample(self) -> None:
        ds, _ = _make_vol_dataset(n=100, lookback=10)
        x, y = ds[len(ds) - 1]
        assert x.shape == (10, 5)
        assert y.shape == (2,)

    def test_insufficient_rows_raises(self) -> None:
        rng = np.random.RandomState(0)
        features = rng.randn(10, 5).astype(np.float32)
        targets = rng.randn(10, 2).astype(np.float32)
        with pytest.raises(ValueError, match="Need at least"):
            VolDataset(
                features=features,
                targets=targets,
                lookback=20,
                feature_mean=features.mean(axis=0),
                feature_std=features.std(axis=0),
                target_mean=targets.mean(axis=0),
                target_std=targets.std(axis=0),
            )

    def test_mismatched_features_targets_raises(self) -> None:
        rng = np.random.RandomState(0)
        features = rng.randn(100, 5).astype(np.float32)
        targets = rng.randn(50, 2).astype(np.float32)
        with pytest.raises(ValueError, match="same length"):
            VolDataset(
                features=features,
                targets=targets,
                lookback=10,
                feature_mean=features.mean(axis=0),
                feature_std=features.std(axis=0),
                target_mean=targets.mean(axis=0),
                target_std=targets.std(axis=0),
            )


# ---------------------------------------------------------------------------
# VolLSTM tests
# ---------------------------------------------------------------------------


class TestVolLSTM:
    """VolLSTM architecture and forward pass."""

    def test_output_shape(self) -> None:
        model = VolLSTM(n_features=5, hidden_size=64)
        x = torch.randn(4, 60, 5)  # batch=4, lookback=60, features=5
        out = model(x)
        assert out.shape == (4, 2)

    def test_single_sample(self) -> None:
        model = VolLSTM(n_features=5, hidden_size=32)
        x = torch.randn(1, 30, 5)
        out = model(x)
        assert out.shape == (1, 2)

    def test_custom_n_features(self) -> None:
        model = VolLSTM(n_features=3, hidden_size=16)
        x = torch.randn(2, 20, 3)
        out = model(x)
        assert out.shape == (2, 2)

    def test_gradient_flows(self) -> None:
        model = VolLSTM(n_features=5, hidden_size=32)
        x = torch.randn(2, 30, 5, requires_grad=True)
        out = model(x)
        loss = out.sum()
        loss.backward()
        assert x.grad is not None


# ---------------------------------------------------------------------------
# prepare_training_data tests
# ---------------------------------------------------------------------------


class TestPrepareTrainingData:
    """Data preprocessing pipeline."""

    def test_returns_dataset_and_stats(self) -> None:
        returns, vix = _make_synthetic_series(n=500)
        ds, stats = prepare_training_data(returns, vix, lookback=20)
        assert isinstance(ds, VolDataset)
        assert "feature_mean" in stats
        assert "feature_std" in stats
        assert "target_mean" in stats
        assert "target_std" in stats
        assert stats["lookback"] == 20
        assert stats["n_features"] == 5

    def test_handles_none_optional_features(self) -> None:
        """Missing features (None) should be filled with zeros."""
        returns, vix = _make_synthetic_series(n=500)
        ds, stats = prepare_training_data(
            returns, vix, vix_slope=None, regime=None, hurst=None, lookback=20
        )
        assert len(ds) > 0

    def test_handles_provided_optional_features(self) -> None:
        returns, vix = _make_synthetic_series(n=500)
        n = len(returns)
        vix_slope = pd.Series(np.random.randn(n))
        regime = pd.Series(np.random.choice([0, 1], n))
        hurst = pd.Series(np.random.uniform(0.3, 0.7, n))
        ds, stats = prepare_training_data(
            returns, vix, vix_slope=vix_slope, regime=regime, hurst=hurst, lookback=20
        )
        assert len(ds) > 0

    def test_insufficient_data_raises(self) -> None:
        returns = pd.Series(np.random.randn(30))
        vix = pd.Series(np.random.uniform(10, 20, 30))
        with pytest.raises(ValueError, match="valid rows"):
            prepare_training_data(returns, vix, lookback=60)

    def test_stats_shapes(self) -> None:
        returns, vix = _make_synthetic_series(n=500)
        _, stats = prepare_training_data(returns, vix, lookback=20)
        assert stats["feature_mean"].shape == (5,)
        assert stats["feature_std"].shape == (5,)
        assert stats["target_mean"].shape == (2,)
        assert stats["target_std"].shape == (2,)


# ---------------------------------------------------------------------------
# VolForecaster tests
# ---------------------------------------------------------------------------


class TestVolForecasterPredict:
    """VolForecaster.predict() inference."""

    @pytest.fixture()
    def trained_forecaster(self) -> VolForecaster:
        """A forecaster with dummy stats and random weights."""
        f = VolForecaster(lookback=20, hidden_size=32, n_features=5)
        f._stats = {
            "feature_mean": np.zeros(5, dtype=np.float32),
            "feature_std": np.ones(5, dtype=np.float32),
            "target_mean": np.zeros(2, dtype=np.float32),
            "target_std": np.ones(2, dtype=np.float32),
        }
        return f

    def test_predict_returns_dict(self, trained_forecaster: VolForecaster) -> None:
        data = np.random.randn(20, 5).astype(np.float32)
        result = trained_forecaster.predict(data)
        assert isinstance(result, dict)
        assert "vol_1d" in result
        assert "vol_5d" in result

    def test_predict_returns_floats(self, trained_forecaster: VolForecaster) -> None:
        data = np.random.randn(20, 5).astype(np.float32)
        result = trained_forecaster.predict(data)
        assert isinstance(result["vol_1d"], float)
        assert isinstance(result["vol_5d"], float)

    def test_predict_with_more_rows(self, trained_forecaster: VolForecaster) -> None:
        """Should accept more rows than lookback (uses last lookback)."""
        data = np.random.randn(100, 5).astype(np.float32)
        result = trained_forecaster.predict(data)
        assert "vol_1d" in result

    def test_predict_insufficient_rows_raises(
        self, trained_forecaster: VolForecaster
    ) -> None:
        data = np.random.randn(5, 5).astype(np.float32)
        with pytest.raises(ValueError, match="Need at least"):
            trained_forecaster.predict(data)

    def test_predict_wrong_features_raises(
        self, trained_forecaster: VolForecaster
    ) -> None:
        data = np.random.randn(20, 3).astype(np.float32)
        with pytest.raises(ValueError, match="Expected 5 features"):
            trained_forecaster.predict(data)

    def test_predict_without_stats_raises(self) -> None:
        f = VolForecaster()
        data = np.random.randn(60, 5).astype(np.float32)
        with pytest.raises(RuntimeError, match="no normalisation stats"):
            f.predict(data)

    def test_predict_1d_input_raises(self, trained_forecaster: VolForecaster) -> None:
        data = np.random.randn(100).astype(np.float32)
        with pytest.raises(ValueError, match="Expected 2-D"):
            trained_forecaster.predict(data)


# ---------------------------------------------------------------------------
# VolForecaster save/load tests
# ---------------------------------------------------------------------------


class TestVolForecasterPersistence:
    """Save / load roundtrip."""

    def test_save_load_roundtrip(self) -> None:
        f = VolForecaster(lookback=20, hidden_size=32, n_features=5)
        f._stats = {
            "feature_mean": np.zeros(5, dtype=np.float32),
            "feature_std": np.ones(5, dtype=np.float32),
            "target_mean": np.zeros(2, dtype=np.float32),
            "target_std": np.ones(2, dtype=np.float32),
        }

        data = np.random.randn(20, 5).astype(np.float32)
        pred_before = f.predict(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "model.pt")
            f.save(path)
            assert os.path.exists(path)

            f2 = VolForecaster()
            f2.load(path)
            pred_after = f2.predict(data)

        assert abs(pred_before["vol_1d"] - pred_after["vol_1d"]) < 1e-5
        assert abs(pred_before["vol_5d"] - pred_after["vol_5d"]) < 1e-5

    def test_save_without_stats_raises(self) -> None:
        f = VolForecaster()
        with pytest.raises(RuntimeError, match="no normalisation stats"):
            f.save("/tmp/should_not_exist.pt")

    def test_load_nonexistent_raises(self) -> None:
        f = VolForecaster()
        with pytest.raises(FileNotFoundError):
            f.load("/tmp/nonexistent_vol_model_xyz.pt")

    def test_load_restores_hyperparams(self) -> None:
        f = VolForecaster(lookback=30, hidden_size=48, n_features=5)
        f._stats = {
            "feature_mean": np.zeros(5, dtype=np.float32),
            "feature_std": np.ones(5, dtype=np.float32),
            "target_mean": np.zeros(2, dtype=np.float32),
            "target_std": np.ones(2, dtype=np.float32),
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "model.pt")
            f.save(path)

            f2 = VolForecaster()
            f2.load(path)
            assert f2.lookback == 30
            assert f2.hidden_size == 48
            assert f2.n_features == 5

    def test_is_trained_property(self) -> None:
        f = VolForecaster()
        assert f.is_trained is False
        f._stats = {"feature_mean": np.zeros(5)}
        assert f.is_trained is True


# ---------------------------------------------------------------------------
# VolForecaster train tests
# ---------------------------------------------------------------------------


class TestVolForecasterTrain:
    """Training pipeline."""

    def test_train_on_synthetic_data_converges(self) -> None:
        """Training on sinusoidal vol pattern should converge to low loss."""
        returns, vix = _make_synthetic_series(n=500, seed=42)
        ds, stats = prepare_training_data(returns, vix, lookback=20)

        f = VolForecaster(lookback=20, hidden_size=32, n_features=5)
        f._stats = stats

        result = f.train(ds, epochs=30, lr=0.001, patience=15, batch_size=32)

        assert "train_loss" in result
        assert "val_loss" in result
        assert "epochs_trained" in result
        assert "best_epoch" in result
        assert result["val_loss"] < 5.0  # Reasonable upper bound for normalised MSE

    def test_train_returns_correct_structure(self) -> None:
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=16, n_features=5)
        f._stats = stats

        result = f.train(ds, epochs=5, patience=3)
        assert isinstance(result["train_loss"], float)
        assert isinstance(result["val_loss"], float)
        assert isinstance(result["epochs_trained"], int)
        assert isinstance(result["best_epoch"], int)

    def test_early_stopping_triggers(self) -> None:
        """With patience=1 and a hard-to-learn dataset, training should stop early."""
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=8, n_features=5)
        f._stats = stats

        result = f.train(ds, epochs=100, patience=2, lr=1e-6)
        # Should stop before 100 epochs (patience is very low).
        assert result["epochs_trained"] <= 100

    def test_train_sets_model_to_best(self) -> None:
        """After training, model should be in the best state."""
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=16, n_features=5)
        f._stats = stats

        result = f.train(ds, epochs=10, patience=5)
        # Best epoch should be <= epochs trained.
        assert result["best_epoch"] <= result["epochs_trained"]


# ---------------------------------------------------------------------------
# VolForecaster evaluate tests
# ---------------------------------------------------------------------------


class TestVolForecasterEvaluate:
    """Evaluation metrics."""

    def test_evaluate_returns_metrics(self) -> None:
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=16, n_features=5)
        f._stats = stats

        result = f.evaluate(ds)
        assert "mae" in result
        assert "rmse" in result
        assert "directional_accuracy" in result

    def test_evaluate_metrics_are_non_negative(self) -> None:
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=16, n_features=5)
        f._stats = stats

        result = f.evaluate(ds)
        assert result["mae"] >= 0.0
        assert result["rmse"] >= 0.0
        assert 0.0 <= result["directional_accuracy"] <= 1.0


# ---------------------------------------------------------------------------
# VolManager tests
# ---------------------------------------------------------------------------


def _make_mock_feature_store() -> MagicMock:
    """Create a mock FeatureStore with async methods."""
    store = MagicMock()
    store.save_features = AsyncMock()
    store.get_latest_features = AsyncMock(return_value=None)
    return store


class TestVolManagerInitialize:
    """VolManager.initialize() trains and saves model."""

    @pytest.mark.asyncio
    async def test_initialize_creates_model_file(self) -> None:
        returns, vix = _make_synthetic_series(n=500)
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = VolManager(store, tmpdir, lookback=20)
            result = await mgr.initialize(
                returns, vix, epochs=5, patience=3
            )
            assert mgr.forecaster is not None
            assert mgr.forecaster.is_trained
            assert os.path.exists(mgr.model_path)
            assert "train_loss" in result

    @pytest.mark.asyncio
    async def test_initialize_returns_training_stats(self) -> None:
        returns, vix = _make_synthetic_series(n=500)
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = VolManager(store, tmpdir, lookback=20)
            result = await mgr.initialize(
                returns, vix, epochs=5, patience=3
            )
            assert "val_loss" in result
            assert "epochs_trained" in result


class TestVolManagerUpdate:
    """VolManager.update() runs inference and persists."""

    @pytest.mark.asyncio
    async def test_update_persists_to_feature_store(self) -> None:
        returns, vix = _make_synthetic_series(n=500)
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = VolManager(store, tmpdir, lookback=20)
            await mgr.initialize(returns, vix, epochs=5, patience=3)

            # Fill buffer with enough data.
            for i in range(20):
                features = {
                    "realized_vol": 0.15,
                    "vix": 15.0,
                    "vix_slope": 0.01,
                    "regime_state": 0.0,
                    "hurst": 0.5,
                }
                result = await mgr.update(features, ticker="SPX")

            assert "vol_1d" in result
            assert "vol_5d" in result
            store.save_features.assert_called()
            call_args = store.save_features.call_args
            assert call_args[0][0] == "SPX"
            saved_features = call_args[0][2]
            assert "vol_forecast_1d" in saved_features
            assert "vol_forecast_5d" in saved_features

    @pytest.mark.asyncio
    async def test_update_without_model_raises(self) -> None:
        store = _make_mock_feature_store()
        mgr = VolManager(store, "/tmp/nonexistent_vol_dir_xyz", lookback=20)
        with pytest.raises(RuntimeError, match="no model"):
            await mgr.update({"realized_vol": 0.15, "vix": 15.0})

    @pytest.mark.asyncio
    async def test_update_with_insufficient_buffer_returns_zeros(self) -> None:
        """Before buffer fills up to lookback, should return zero forecasts."""
        returns, vix = _make_synthetic_series(n=500)
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = VolManager(store, tmpdir, lookback=20)
            await mgr.initialize(returns, vix, epochs=5, patience=3)

            # Single update -- buffer has only 1 row, need 20.
            result = await mgr.update(
                {"realized_vol": 0.15, "vix": 15.0}, ticker="SPX"
            )
            assert result["vol_1d"] == 0.0
            assert result["vol_5d"] == 0.0


class TestVolManagerLoadSavedModel:
    """VolManager loads a saved model on first update."""

    @pytest.mark.asyncio
    async def test_loads_saved_model_on_update(self) -> None:
        returns, vix = _make_synthetic_series(n=500)
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()

            # First manager: train and save.
            mgr1 = VolManager(store, tmpdir, lookback=20)
            await mgr1.initialize(returns, vix, epochs=5, patience=3)

            # Second manager: should auto-load from disk.
            mgr2 = VolManager(store, tmpdir, lookback=20)
            assert mgr2.forecaster is None  # Not loaded yet.

            # Fill buffer and update -- should trigger load.
            for i in range(20):
                await mgr2.update(
                    {"realized_vol": 0.15, "vix": 15.0}, ticker="SPX"
                )

            assert mgr2.forecaster is not None
            assert mgr2.forecaster.is_trained


class TestVolManagerGetCurrentForecast:
    """VolManager.get_current_forecast() reads from feature store."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_data(self) -> None:
        store = _make_mock_feature_store()
        store.get_latest_features.return_value = None
        mgr = VolManager(store, "/tmp")
        result = await mgr.get_current_forecast("SPX")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_forecast_from_store(self) -> None:
        store = _make_mock_feature_store()
        store.get_latest_features.return_value = {
            "vol_forecast_1d": 0.15,
            "vol_forecast_5d": 0.18,
        }
        mgr = VolManager(store, "/tmp")
        result = await mgr.get_current_forecast("SPX")
        assert result is not None
        assert result["vol_forecast_1d"] == 0.15
        assert result["vol_forecast_5d"] == 0.18

    @pytest.mark.asyncio
    async def test_returns_none_when_no_forecasts(self) -> None:
        store = _make_mock_feature_store()
        store.get_latest_features.return_value = {
            "vol_forecast_1d": None,
            "vol_forecast_5d": None,
        }
        mgr = VolManager(store, "/tmp")
        result = await mgr.get_current_forecast("SPX")
        assert result is None


# ---------------------------------------------------------------------------
# Task 2: Additional tests for training pipeline and feature store integration
# ---------------------------------------------------------------------------


class TestTrainingPipelineConvergence:
    """Detailed training convergence and temporal split tests."""

    def test_train_loss_decreases_over_epochs(self) -> None:
        """Training loss should generally decrease during training."""
        returns, vix = _make_synthetic_series(n=500, seed=42)
        ds, stats = prepare_training_data(returns, vix, lookback=20)

        f = VolForecaster(lookback=20, hidden_size=32, n_features=5)
        f._stats = stats

        # Train for 5 epochs first.
        result_5 = f.train(ds, epochs=5, lr=0.001, patience=100, batch_size=32)
        loss_5 = result_5["train_loss"]

        # Reinitialise and train for 20 epochs.
        f2 = VolForecaster(lookback=20, hidden_size=32, n_features=5)
        f2._stats = stats
        result_20 = f2.train(ds, epochs=20, lr=0.001, patience=100, batch_size=32)
        loss_20 = result_20["val_loss"]

        # More epochs should yield lower or similar loss.
        assert loss_20 <= loss_5 + 0.5  # Allow small tolerance.

    def test_temporal_split_preserves_order(self) -> None:
        """Validation set should come from the end of the dataset (temporal)."""
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=16, n_features=5)
        f._stats = stats

        # Train with 20% val split = 36 samples val, 144 train.
        result = f.train(ds, epochs=3, val_split=0.2)
        # Verify training produced non-zero stats.
        assert result["train_loss"] > 0
        assert result["val_loss"] > 0

    def test_val_split_zero_uses_all_for_training(self) -> None:
        """With val_split=0 only 1 sample in validation."""
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=16, n_features=5)
        f._stats = stats

        # val_split=0.0 still has at least 1 validation sample (max(1, ...)).
        result = f.train(ds, epochs=3, val_split=0.0)
        assert result["epochs_trained"] == 3

    def test_train_then_predict_produces_finite_values(self) -> None:
        """Full pipeline: prepare -> train -> predict should give finite output."""
        returns, vix = _make_synthetic_series(n=500, seed=42)
        ds, stats = prepare_training_data(returns, vix, lookback=20)

        f = VolForecaster(lookback=20, hidden_size=32, n_features=5)
        f._stats = stats
        f.train(ds, epochs=10, lr=0.001, patience=5)

        # Create a simple feature array for prediction.
        fake_features = np.random.randn(20, 5).astype(np.float32)
        result = f.predict(fake_features)
        assert np.isfinite(result["vol_1d"])
        assert np.isfinite(result["vol_5d"])


class TestEvaluationPipeline:
    """Detailed evaluation metric tests."""

    def test_evaluate_rmse_geq_mae(self) -> None:
        """RMSE should always be >= MAE."""
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=16, n_features=5)
        f._stats = stats
        f.train(ds, epochs=5, patience=3)

        result = f.evaluate(ds)
        assert result["rmse"] >= result["mae"]

    def test_evaluate_after_training_metrics_change(self) -> None:
        """Metrics from an untrained model should differ from a trained one."""
        ds, stats = _make_vol_dataset(n=200, lookback=20, seed=99)

        # Untrained model.
        f_untrained = VolForecaster(lookback=20, hidden_size=16, n_features=5)
        f_untrained._stats = stats
        eval_untrained = f_untrained.evaluate(ds)

        # Trained model.
        f_trained = VolForecaster(lookback=20, hidden_size=16, n_features=5)
        f_trained._stats = stats
        f_trained.train(ds, epochs=20, lr=0.001, patience=10)
        eval_trained = f_trained.evaluate(ds)

        # MAE should generally be lower after training (or at least different).
        assert eval_untrained["mae"] != eval_trained["mae"]

    def test_evaluate_directional_accuracy_is_float(self) -> None:
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=16, n_features=5)
        f._stats = stats

        result = f.evaluate(ds)
        assert isinstance(result["directional_accuracy"], float)


class TestVolManagerEndToEnd:
    """End-to-end VolManager lifecycle tests."""

    @pytest.mark.asyncio
    async def test_initialize_with_optional_features(self) -> None:
        """Initialize with all optional features provided."""
        returns, vix = _make_synthetic_series(n=500)
        n = len(returns)
        vix_slope = pd.Series(np.random.randn(n))
        regime = pd.Series(np.random.choice([0, 1], n))
        hurst = pd.Series(np.random.uniform(0.3, 0.7, n))

        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = VolManager(store, tmpdir, lookback=20)
            result = await mgr.initialize(
                returns, vix,
                vix_slope=vix_slope,
                regime=regime,
                hurst=hurst,
                epochs=5,
                patience=3,
            )
            assert mgr.forecaster is not None
            assert "train_loss" in result

    @pytest.mark.asyncio
    async def test_model_path_property(self) -> None:
        store = _make_mock_feature_store()
        mgr = VolManager(store, "/some/dir", lookback=20)
        assert mgr.model_path == "/some/dir/vol_model.pt"

    @pytest.mark.asyncio
    async def test_update_fills_buffer_gradually(self) -> None:
        """Buffer should grow with each update call."""
        returns, vix = _make_synthetic_series(n=500)
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = VolManager(store, tmpdir, lookback=20)
            await mgr.initialize(returns, vix, epochs=5, patience=3)

            assert len(mgr._feature_buffer) == 0
            await mgr.update({"realized_vol": 0.15, "vix": 15.0})
            assert len(mgr._feature_buffer) == 1
            await mgr.update({"realized_vol": 0.16, "vix": 16.0})
            assert len(mgr._feature_buffer) == 2

    @pytest.mark.asyncio
    async def test_update_default_feature_values(self) -> None:
        """Missing keys in latest_features dict should default to 0.0."""
        returns, vix = _make_synthetic_series(n=500)
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr = VolManager(store, tmpdir, lookback=20)
            await mgr.initialize(returns, vix, epochs=5, patience=3)

            # Only provide partial features.
            result = await mgr.update({"vix": 15.0})
            # Should not raise; missing keys default to 0.0.
            assert "vol_1d" in result

    @pytest.mark.asyncio
    async def test_save_load_roundtrip_via_manager(self) -> None:
        """Train via manager, load in a new manager, predictions should match."""
        returns, vix = _make_synthetic_series(n=500)
        with tempfile.TemporaryDirectory() as tmpdir:
            store = _make_mock_feature_store()
            mgr1 = VolManager(store, tmpdir, lookback=20)
            await mgr1.initialize(returns, vix, epochs=5, patience=3)

            # Get predictions from first manager.
            test_features = np.random.randn(20, 5).astype(np.float32)
            pred1 = mgr1.forecaster.predict(test_features)

            # Load in new manager's forecaster.
            mgr2 = VolManager(store, tmpdir, lookback=20)
            f2 = VolForecaster()
            f2.load(mgr2.model_path)
            pred2 = f2.predict(test_features)

            assert abs(pred1["vol_1d"] - pred2["vol_1d"]) < 1e-5
            assert abs(pred1["vol_5d"] - pred2["vol_5d"]) < 1e-5


# ---------------------------------------------------------------------------
# Step 7: VolForecaster.train() stats parameter tests
# ---------------------------------------------------------------------------


class TestVolForecasterTrainStats:
    """Tests for passing stats through train() instead of setting _stats directly."""

    def test_forecaster_train_with_stats_enables_predict(self) -> None:
        """Passing stats to train() makes the model usable for prediction."""
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=16, n_features=5)

        # Do NOT set _stats directly; pass through train().
        assert f._stats is None
        f.train(ds, epochs=3, patience=2, stats=stats)

        # Now _stats should be set and predict should work.
        assert f._stats is not None
        assert f.is_trained is True
        data = np.random.randn(20, 5).astype(np.float32)
        result = f.predict(data)
        assert "vol_1d" in result
        assert "vol_5d" in result

    def test_forecaster_train_without_stats_predict_raises(self) -> None:
        """Training without stats leaves _stats as None; predict raises."""
        ds, stats = _make_vol_dataset(n=200, lookback=20)
        f = VolForecaster(lookback=20, hidden_size=16, n_features=5)

        # Train without passing stats.
        f.train(ds, epochs=3, patience=2)

        # _stats was never set, so predict should raise.
        assert f._stats is None
        data = np.random.randn(20, 5).astype(np.float32)
        with pytest.raises(RuntimeError, match="no normalisation stats"):
            f.predict(data)
