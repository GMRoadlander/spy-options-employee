"""LSTM volatility forecasting for SPX options trading.

Predicts 1-day and 5-day realised volatility using an LSTM model with
macro features (VIX level, VIX term structure slope, HMM regime state,
Hurst exponent).  Better vol forecasts improve entry timing for
premium-selling strategies.

Classes:
    VolDataset   -- PyTorch Dataset for sliding-window vol sequences.
    VolLSTM      -- LSTM + FC head producing 2-output vol forecasts.
    VolForecaster -- High-level API: predict, save, load.
    VolManager   -- Daily update pipeline with feature store integration.

Usage::

    forecaster = VolForecaster(lookback=60)
    dataset, stats = prepare_training_data(returns, vix)
    forecaster.train(dataset)
    pred = forecaster.predict(recent_features)
    print(pred)  # {"vol_1d": 0.15, "vol_5d": 0.17}
"""

from __future__ import annotations

import logging
import math
import os
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

if TYPE_CHECKING:
    from src.ml.feature_store import FeatureStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default number of past days used as input to the LSTM.
DEFAULT_LOOKBACK = 60

# Number of input features: [realized_vol, vix, vix_slope, regime_state, hurst]
DEFAULT_N_FEATURES = 5

# Minimum rows required after feature construction (lookback + forward targets).
MIN_TRAINING_ROWS = 100


# ---------------------------------------------------------------------------
# Data preprocessing
# ---------------------------------------------------------------------------


class VolDataset(Dataset):
    """Sliding-window dataset for LSTM volatility forecasting.

    Each sample is a ``(lookback, n_features)`` input tensor paired with
    a ``(2,)`` target tensor ``[rv_1d, rv_5d]``.  Features are normalised
    using caller-provided mean/std (StandardScaler-style, manual for
    portability).

    Args:
        features: ``(T, n_features)`` numpy array of daily features.
        targets: ``(T, 2)`` numpy array of forward-looking targets
            ``[rv_1d, rv_5d]``.
        lookback: Number of past days per input sequence.
        feature_mean: Per-feature mean for normalisation.
        feature_std: Per-feature std for normalisation.
        target_mean: Per-target mean for normalisation.
        target_std: Per-target std for normalisation.
    """

    def __init__(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        lookback: int,
        feature_mean: np.ndarray,
        feature_std: np.ndarray,
        target_mean: np.ndarray,
        target_std: np.ndarray,
    ) -> None:
        if len(features) != len(targets):
            raise ValueError(
                f"features and targets must have the same length, "
                f"got {len(features)} and {len(targets)}"
            )
        if len(features) < lookback:
            raise ValueError(
                f"Need at least {lookback} rows for lookback, got {len(features)}"
            )

        self.lookback = lookback

        # Normalise features.
        safe_std = feature_std.copy()
        safe_std[safe_std == 0] = 1.0
        self._features = (features - feature_mean) / safe_std

        # Normalise targets.
        safe_target_std = target_std.copy()
        safe_target_std[safe_target_std == 0] = 1.0
        self._targets = (targets - target_mean) / safe_target_std

    def __len__(self) -> int:
        return len(self._features) - self.lookback

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = self._features[idx : idx + self.lookback]
        y = self._targets[idx + self.lookback - 1]
        return (
            torch.tensor(x, dtype=torch.float32),
            torch.tensor(y, dtype=torch.float32),
        )


def prepare_training_data(
    returns: pd.Series,
    vix: pd.Series,
    vix_slope: pd.Series | None = None,
    regime: pd.Series | None = None,
    hurst: pd.Series | None = None,
    lookback: int = DEFAULT_LOOKBACK,
) -> tuple[VolDataset, dict]:
    """Build a :class:`VolDataset` from raw market series.

    Computes realised vol (20-day rolling std * sqrt(252)) as primary
    feature, constructs forward-looking targets (1-day and 5-day
    realised vol), drops NaN rows, computes normalisation stats, and
    returns the dataset plus stats dict.

    Args:
        returns: Daily returns series.
        vix: Daily VIX levels.
        vix_slope: VIX term structure slope (optional, zeros if None).
        regime: Regime state from HMM (optional, zeros if None).
        hurst: Hurst exponent (optional, zeros if None).
        lookback: Sliding window length.

    Returns:
        Tuple of ``(VolDataset, stats_dict)`` where *stats_dict*
        contains ``feature_mean``, ``feature_std``, ``target_mean``,
        ``target_std``, ``lookback``, ``n_features``.

    Raises:
        ValueError: If fewer than ``MIN_TRAINING_ROWS`` valid rows remain.
    """
    returns = pd.Series(returns, dtype=float).reset_index(drop=True)
    vix = pd.Series(vix, dtype=float).reset_index(drop=True)

    n = len(returns)

    # Realised vol: 20-day rolling std * sqrt(252).
    rv = returns.rolling(20).std() * math.sqrt(252)

    # Forward-looking targets.
    # 1-day forward RV: absolute return * sqrt(252) as a proxy.
    rv_1d = returns.shift(-1).abs() * math.sqrt(252)
    # 5-day forward RV: rolling(5) std shifted forward * sqrt(252).
    rv_5d = returns.rolling(5).std().shift(-5) * math.sqrt(252)

    # Optional features — fill with zeros if not provided.
    if vix_slope is None:
        vix_slope = pd.Series(np.zeros(n), dtype=float)
    else:
        vix_slope = pd.Series(vix_slope, dtype=float).reset_index(drop=True)

    if regime is None:
        regime = pd.Series(np.zeros(n), dtype=float)
    else:
        regime = pd.Series(regime, dtype=float).reset_index(drop=True)

    if hurst is None:
        hurst = pd.Series(np.zeros(n), dtype=float)
    else:
        hurst = pd.Series(hurst, dtype=float).reset_index(drop=True)

    # Build feature matrix: [rv, vix, vix_slope, regime, hurst]
    feature_df = pd.DataFrame(
        {
            "realized_vol": rv,
            "vix": vix,
            "vix_slope": vix_slope,
            "regime_state": regime,
            "hurst": hurst,
        }
    )
    target_df = pd.DataFrame({"rv_1d": rv_1d, "rv_5d": rv_5d})

    # Combine and drop NaN rows.
    combined = pd.concat([feature_df, target_df], axis=1).dropna()

    if len(combined) < lookback + 1:
        raise ValueError(
            f"Need at least {lookback + 1} valid rows after NaN removal, "
            f"got {len(combined)}"
        )

    features = combined[["realized_vol", "vix", "vix_slope", "regime_state", "hurst"]].values
    targets = combined[["rv_1d", "rv_5d"]].values

    # Compute normalisation stats.
    feature_mean = features.mean(axis=0)
    feature_std = features.std(axis=0)
    target_mean = targets.mean(axis=0)
    target_std = targets.std(axis=0)

    dataset = VolDataset(
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
        "n_features": features.shape[1],
    }

    logger.info(
        "Prepared training data: %d samples (lookback=%d, features=%d)",
        len(dataset),
        lookback,
        features.shape[1],
    )
    return dataset, stats


# ---------------------------------------------------------------------------
# LSTM Model
# ---------------------------------------------------------------------------


class VolLSTM(nn.Module):
    """Simple LSTM for volatility forecasting.

    Architecture:
        - LSTM: 2 layers, configurable hidden size, dropout 0.2
        - FC head: hidden -> 32 -> 2 (1d and 5d forecast)

    No attention, no bells and whistles -- LSTM baseline first.

    Args:
        n_features: Number of input features per timestep.
        hidden_size: LSTM hidden state dimension.
    """

    def __init__(
        self,
        n_features: int = DEFAULT_N_FEATURES,
        hidden_size: int = 64,
    ) -> None:
        super().__init__()
        self.hidden_size = hidden_size
        self.n_features = n_features

        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_size,
            num_layers=2,
            dropout=0.2,
            batch_first=True,
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor of shape ``(batch, lookback, n_features)``.

        Returns:
            Output tensor of shape ``(batch, 2)`` with ``[vol_1d, vol_5d]``.
        """
        # LSTM output: (batch, seq_len, hidden_size)
        lstm_out, _ = self.lstm(x)
        # Take last hidden state.
        last_hidden = lstm_out[:, -1, :]
        return self.fc(last_hidden)


# ---------------------------------------------------------------------------
# VolForecaster -- high-level API
# ---------------------------------------------------------------------------


class VolForecaster:
    """High-level volatility forecaster wrapping :class:`VolLSTM`.

    Provides predict, save, load functionality with CPU-only inference.

    Args:
        lookback: Number of past days per input sequence.
        hidden_size: LSTM hidden state dimension.
        n_features: Number of input features.
    """

    def __init__(
        self,
        lookback: int = DEFAULT_LOOKBACK,
        hidden_size: int = 64,
        n_features: int = DEFAULT_N_FEATURES,
    ) -> None:
        self.lookback = lookback
        self.hidden_size = hidden_size
        self.n_features = n_features
        self.device = torch.device("cpu")

        self.model = VolLSTM(
            n_features=n_features,
            hidden_size=hidden_size,
        ).to(self.device)

        # Normalisation stats -- set after training or loading.
        self._stats: dict[str, Any] | None = None

    @property
    def is_trained(self) -> bool:
        """Return True if normalisation stats have been set (model is usable)."""
        return self._stats is not None

    def predict(self, recent_features: np.ndarray) -> dict[str, float]:
        """Run inference on recent feature data.

        Args:
            recent_features: Array of shape ``(lookback, n_features)``
                with raw (unnormalised) feature values.

        Returns:
            Dict with ``vol_1d`` and ``vol_5d`` (denormalised) floats.

        Raises:
            ValueError: If input shape does not match expected dimensions.
            RuntimeError: If model has not been trained or loaded.
        """
        if self._stats is None:
            raise RuntimeError(
                "Model has no normalisation stats. Train or load a model first."
            )

        recent_features = np.asarray(recent_features, dtype=np.float32)

        if recent_features.ndim != 2:
            raise ValueError(
                f"Expected 2-D array (lookback, n_features), got shape {recent_features.shape}"
            )
        if recent_features.shape[0] < self.lookback:
            raise ValueError(
                f"Need at least {self.lookback} rows, got {recent_features.shape[0]}"
            )
        if recent_features.shape[1] != self.n_features:
            raise ValueError(
                f"Expected {self.n_features} features, got {recent_features.shape[1]}"
            )

        # Use last `lookback` rows.
        window = recent_features[-self.lookback :]

        # Normalise.
        feat_mean = self._stats["feature_mean"]
        feat_std = self._stats["feature_std"].copy()
        feat_std[feat_std == 0] = 1.0
        normalised = (window - feat_mean) / feat_std

        # Forward pass.
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(normalised, dtype=torch.float32).unsqueeze(0).to(self.device)
            output = self.model(x).squeeze(0).cpu().numpy()

        # Denormalise targets.
        target_mean = self._stats["target_mean"]
        target_std = self._stats["target_std"].copy()
        target_std[target_std == 0] = 1.0
        denorm = output * target_std + target_mean

        return {
            "vol_1d": float(denorm[0]),
            "vol_5d": float(denorm[1]),
        }

    def save(self, path: str) -> None:
        """Save model state dict, hyperparams, and normalisation stats.

        Args:
            path: Filesystem path for the checkpoint file.

        Raises:
            RuntimeError: If model has not been trained.
        """
        if self._stats is None:
            raise RuntimeError("Cannot save: model has no normalisation stats.")

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        payload = {
            "model_state_dict": self.model.state_dict(),
            "lookback": self.lookback,
            "hidden_size": self.hidden_size,
            "n_features": self.n_features,
            "stats": {
                "feature_mean": self._stats["feature_mean"],
                "feature_std": self._stats["feature_std"],
                "target_mean": self._stats["target_mean"],
                "target_std": self._stats["target_std"],
            },
        }
        torch.save(payload, path)
        logger.info("Saved VolForecaster to %s", path)

    def load(self, path: str) -> None:
        """Load model from a checkpoint file.

        Args:
            path: Filesystem path of the checkpoint.

        Raises:
            FileNotFoundError: If *path* does not exist.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")

        payload = torch.load(path, map_location=self.device, weights_only=False)

        # Restore hyperparams.
        self.lookback = payload["lookback"]
        self.hidden_size = payload["hidden_size"]
        self.n_features = payload["n_features"]

        # Rebuild model with correct architecture.
        self.model = VolLSTM(
            n_features=self.n_features,
            hidden_size=self.hidden_size,
        ).to(self.device)
        self.model.load_state_dict(payload["model_state_dict"])

        # Restore normalisation stats.
        self._stats = payload["stats"]

        logger.info("Loaded VolForecaster from %s", path)

    def train(
        self,
        dataset: VolDataset,
        epochs: int = 100,
        lr: float = 0.001,
        patience: int = 10,
        val_split: float = 0.2,
        batch_size: int = 32,
        stats: dict[str, Any] | None = None,
    ) -> dict[str, float | int]:
        """Train the LSTM on a :class:`VolDataset`.

        Uses a temporal split (last ``val_split`` fraction for
        validation -- NOT random split, preserves time ordering).
        Early stopping based on validation loss.

        Args:
            dataset: Training dataset.
            epochs: Maximum training epochs.
            lr: Learning rate for Adam optimiser.
            patience: Early stopping patience (epochs without improvement).
            val_split: Fraction of data for validation (temporal split).
            batch_size: Mini-batch size.
            stats: Normalisation stats dict (``feature_mean``,
                ``feature_std``, ``target_mean``, ``target_std``).
                If provided, sets ``_stats`` so the model is usable
                for prediction after training.

        Returns:
            Dict with ``train_loss``, ``val_loss``, ``epochs_trained``,
            ``best_epoch``.
        """
        if stats is not None:
            self._stats = stats
        n = len(dataset)
        val_size = max(1, int(n * val_split))
        train_size = n - val_size

        # Temporal split: first train_size for training, last val_size for validation.
        train_dataset = torch.utils.data.Subset(dataset, list(range(train_size)))
        val_dataset = torch.utils.data.Subset(dataset, list(range(train_size, n)))

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        self.model.train()
        optimiser = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        best_val_loss = float("inf")
        best_epoch = 0
        best_state = None
        epochs_without_improvement = 0

        for epoch in range(1, epochs + 1):
            # Training.
            self.model.train()
            train_losses: list[float] = []
            for x_batch, y_batch in train_loader:
                x_batch = x_batch.to(self.device)
                y_batch = y_batch.to(self.device)
                optimiser.zero_grad()
                pred = self.model(x_batch)
                loss = criterion(pred, y_batch)
                loss.backward()
                optimiser.step()
                train_losses.append(loss.item())

            avg_train_loss = sum(train_losses) / len(train_losses) if train_losses else 0.0

            # Validation.
            self.model.eval()
            val_losses: list[float] = []
            with torch.no_grad():
                for x_batch, y_batch in val_loader:
                    x_batch = x_batch.to(self.device)
                    y_batch = y_batch.to(self.device)
                    pred = self.model(x_batch)
                    loss = criterion(pred, y_batch)
                    val_losses.append(loss.item())

            avg_val_loss = sum(val_losses) / len(val_losses) if val_losses else 0.0

            if epoch % 10 == 0 or epoch == 1:
                logger.info(
                    "Epoch %d/%d — train_loss: %.6f, val_loss: %.6f",
                    epoch,
                    epochs,
                    avg_train_loss,
                    avg_val_loss,
                )

            # Early stopping.
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                best_epoch = epoch
                best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1

            if epochs_without_improvement >= patience:
                logger.info(
                    "Early stopping at epoch %d (best epoch: %d)", epoch, best_epoch
                )
                break

        # Restore best model.
        if best_state is not None:
            self.model.load_state_dict(best_state)

        return {
            "train_loss": avg_train_loss,
            "val_loss": best_val_loss,
            "epochs_trained": epoch,
            "best_epoch": best_epoch,
        }

    def evaluate(self, test_dataset: VolDataset) -> dict[str, float]:
        """Evaluate the model on a test dataset.

        Args:
            test_dataset: A :class:`VolDataset` for evaluation.

        Returns:
            Dict with ``mae``, ``rmse``, ``directional_accuracy``
            (fraction of times the forecast correctly predicted whether
            vol increased or decreased).
        """
        loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

        all_preds: list[np.ndarray] = []
        all_targets: list[np.ndarray] = []

        self.model.eval()
        with torch.no_grad():
            for x_batch, y_batch in loader:
                x_batch = x_batch.to(self.device)
                pred = self.model(x_batch)
                all_preds.append(pred.cpu().numpy())
                all_targets.append(y_batch.numpy())

        preds = np.concatenate(all_preds, axis=0)
        targets = np.concatenate(all_targets, axis=0)

        # MAE and RMSE (on normalised values).
        errors = preds - targets
        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors**2)))

        # Directional accuracy: did the forecast predict up/down correctly?
        # Compare sign of predicted change vs actual change (using first target: rv_1d).
        if len(preds) > 1:
            pred_diff = np.diff(preds[:, 0])
            actual_diff = np.diff(targets[:, 0])
            correct = np.sum(np.sign(pred_diff) == np.sign(actual_diff))
            directional_accuracy = float(correct / len(pred_diff))
        else:
            directional_accuracy = 0.0

        return {
            "mae": mae,
            "rmse": rmse,
            "directional_accuracy": directional_accuracy,
        }


# ---------------------------------------------------------------------------
# VolManager -- daily update pipeline (mirrors RegimeManager)
# ---------------------------------------------------------------------------

# Rolling window size kept in memory.
_ROLLING_WINDOW = 1000


class VolManager:
    """Orchestrates daily vol forecasting and feature store persistence.

    Mirrors the :class:`RegimeManager` pattern: keeps a rolling window
    of recent features in memory, runs inference via :class:`VolForecaster`,
    and persists predictions to the feature store.

    Args:
        feature_store: An initialised :class:`FeatureStore`.
        model_dir: Directory where model checkpoint files are stored.
        lookback: Lookback window for the LSTM.
    """

    def __init__(
        self,
        feature_store: FeatureStore,
        model_dir: str,
        lookback: int = DEFAULT_LOOKBACK,
    ) -> None:
        self._feature_store = feature_store
        self._model_dir = model_dir
        self._lookback = lookback
        self._forecaster: VolForecaster | None = None

        # Rolling history of features kept in memory: list of (n_features,) arrays.
        self._feature_buffer: list[np.ndarray] = []

    @property
    def forecaster(self) -> VolForecaster | None:
        """The underlying :class:`VolForecaster`, or None if uninitialised."""
        return self._forecaster

    @property
    def model_path(self) -> str:
        """Path to the persisted model checkpoint file."""
        return os.path.join(self._model_dir, "vol_model.pt")

    async def initialize(
        self,
        returns: pd.Series,
        vix: pd.Series,
        vix_slope: pd.Series | None = None,
        regime: pd.Series | None = None,
        hurst: pd.Series | None = None,
        epochs: int = 100,
        lr: float = 0.001,
        patience: int = 10,
    ) -> dict:
        """Prepare data, train model, save checkpoint.

        Args:
            returns: Daily returns series.
            vix: Daily VIX levels.
            vix_slope: Optional VIX term structure slope.
            regime: Optional regime state from HMM.
            hurst: Optional Hurst exponent.
            epochs: Max training epochs.
            lr: Learning rate.
            patience: Early stopping patience.

        Returns:
            Training stats dict from :meth:`VolForecaster.train`.
        """
        dataset, stats = prepare_training_data(
            returns=returns,
            vix=vix,
            vix_slope=vix_slope,
            regime=regime,
            hurst=hurst,
            lookback=self._lookback,
        )

        forecaster = VolForecaster(
            lookback=self._lookback,
            n_features=stats["n_features"],
        )

        training_result = forecaster.train(
            dataset, epochs=epochs, lr=lr, patience=patience, stats=stats
        )

        # Save checkpoint.
        os.makedirs(self._model_dir, exist_ok=True)
        forecaster.save(self.model_path)

        self._forecaster = forecaster
        self._feature_buffer = []

        logger.info(
            "VolManager initialized: train_loss=%.6f, val_loss=%.6f, epochs=%d",
            training_result["train_loss"],
            training_result["val_loss"],
            training_result["epochs_trained"],
        )
        return training_result

    async def update(
        self,
        latest_features: dict[str, float],
        ticker: str = "SPX",
    ) -> dict[str, float]:
        """Run inference with latest features and persist to feature store.

        Args:
            latest_features: Dict with keys ``realized_vol``, ``vix``,
                ``vix_slope``, ``regime_state``, ``hurst``.
            ticker: Ticker symbol for feature store persistence.

        Returns:
            Dict with ``vol_1d`` and ``vol_5d`` predictions.

        Raises:
            RuntimeError: If manager has not been initialised and no saved
                model exists.
        """
        if self._forecaster is None:
            # Try loading from disk.
            if os.path.exists(self.model_path):
                self._forecaster = VolForecaster(lookback=self._lookback)
                self._forecaster.load(self.model_path)
                logger.info("Loaded saved model from %s", self.model_path)
            else:
                raise RuntimeError(
                    "VolManager has no model. Call initialize() or ensure a "
                    "saved model exists at: " + self.model_path
                )

        # Build feature vector: [realized_vol, vix, vix_slope, regime_state, hurst]
        feature_row = np.array(
            [
                latest_features.get("realized_vol", 0.0),
                latest_features.get("vix", 0.0),
                latest_features.get("vix_slope", 0.0),
                latest_features.get("regime_state", 0.0),
                latest_features.get("hurst", 0.0),
            ],
            dtype=np.float32,
        )

        self._feature_buffer.append(feature_row)

        # Trim to rolling window.
        if len(self._feature_buffer) > _ROLLING_WINDOW:
            self._feature_buffer = self._feature_buffer[-_ROLLING_WINDOW:]

        # Need at least `lookback` observations to predict.
        if len(self._feature_buffer) < self._forecaster.lookback:
            logger.warning(
                "Not enough data for prediction: %d/%d rows",
                len(self._feature_buffer),
                self._forecaster.lookback,
            )
            return {"vol_1d": 0.0, "vol_5d": 0.0}

        # Build input array.
        recent = np.stack(self._feature_buffer[-self._forecaster.lookback :])
        prediction = self._forecaster.predict(recent)

        # Persist to feature store.
        from datetime import date

        today = date.today().isoformat()
        await self._feature_store.save_features(
            ticker,
            today,
            {
                "vol_forecast_1d": prediction["vol_1d"],
                "vol_forecast_5d": prediction["vol_5d"],
            },
        )

        logger.info(
            "Vol forecast for %s: 1d=%.4f, 5d=%.4f",
            ticker,
            prediction["vol_1d"],
            prediction["vol_5d"],
        )
        return prediction

    async def get_current_forecast(self, ticker: str = "SPX") -> dict | None:
        """Read the latest vol forecast from the feature store.

        Args:
            ticker: Ticker symbol.

        Returns:
            Dict with ``vol_forecast_1d`` and ``vol_forecast_5d``, or
            None if no forecast has been stored.
        """
        latest = await self._feature_store.get_latest_features(ticker)
        if latest is None:
            return None

        vol_1d = latest.get("vol_forecast_1d")
        vol_5d = latest.get("vol_forecast_5d")

        if vol_1d is None and vol_5d is None:
            return None

        return {
            "vol_forecast_1d": float(vol_1d) if vol_1d is not None else None,
            "vol_forecast_5d": float(vol_5d) if vol_5d is not None else None,
        }
