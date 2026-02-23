"""Statistical anomaly detection for unusual options activity.

Provides z-score based detectors for volume spikes, IV anomalies,
volume/OI ratio anomalies, and strike clustering.  All pure-stat
functions are stateless and synchronous (no I/O).

A convenience ``scan_chain_anomalies`` function runs all detectors on
an :class:`OptionsChain` in one call.

The module also provides:

- :class:`FlowAnomalyDetector` — scikit-learn IsolationForest wrapper
  for multi-feature anomaly detection on options flow data.
- :class:`AnomalyManager` — async pipeline that combines z-score
  detectors with isolation forest scoring and persists results to the
  feature store.

Phase 3-05 of the ML intelligence layer.
"""

from __future__ import annotations

import logging
import os
import pickle
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.data import OptionsChain
    from src.ml.feature_store import FeatureStore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AnomalyReport dataclass
# ---------------------------------------------------------------------------


@dataclass
class AnomalyReport:
    """Aggregated anomaly results for a given snapshot.

    Attributes:
        volume_anomalies: Results from volume z-score detection.
        iv_anomalies: Results from IV anomaly detection.
        voi_anomalies: Results from volume/OI ratio detection.
        strike_clusters: Top strikes by volume concentration.
        overall_score: Composite anomaly score in [0, 1].
        timestamp: ISO-format timestamp of the report.
    """

    volume_anomalies: list[dict] = field(default_factory=list)
    iv_anomalies: list[dict] = field(default_factory=list)
    voi_anomalies: list[dict] = field(default_factory=list)
    strike_clusters: list[dict] = field(default_factory=list)
    overall_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------------
# Z-score detectors
# ---------------------------------------------------------------------------


def detect_volume_anomaly(
    current_volume: int,
    historical_volumes: list[int],
    threshold_sigma: float = 2.0,
) -> dict:
    """Z-score of current volume vs rolling history.

    Args:
        current_volume: Current observed volume.
        historical_volumes: List of historical volume values.
        threshold_sigma: Number of standard deviations for anomaly flag.

    Returns:
        Dict with keys: is_anomaly, z_score, threshold, volume, mean, std.
    """
    arr = np.asarray(historical_volumes, dtype=float)
    arr = arr[np.isfinite(arr)]

    if len(arr) < 2:
        return {
            "is_anomaly": False,
            "z_score": 0.0,
            "threshold": threshold_sigma,
            "volume": current_volume,
            "mean": 0.0,
            "std": 0.0,
        }

    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))

    if std < 1e-10:
        return {
            "is_anomaly": False,
            "z_score": 0.0,
            "threshold": threshold_sigma,
            "volume": current_volume,
            "mean": mean,
            "std": 0.0,
        }

    z_score = (current_volume - mean) / std

    return {
        "is_anomaly": z_score > threshold_sigma,
        "z_score": float(z_score),
        "threshold": threshold_sigma,
        "volume": current_volume,
        "mean": mean,
        "std": std,
    }


def detect_iv_anomaly(
    current_iv: float,
    historical_ivs: list[float],
    underlying_change_pct: float,
    threshold_sigma: float = 2.0,
) -> dict:
    """Flag when IV moves significantly without a corresponding underlying move.

    An anomaly is flagged when the absolute IV z-score exceeds
    *threshold_sigma* AND the absolute underlying change is less than 1%.

    Args:
        current_iv: Current implied volatility.
        historical_ivs: Historical IV values.
        underlying_change_pct: Percentage change in the underlying (e.g. 0.5 for 0.5%).
        threshold_sigma: Number of standard deviations for anomaly flag.

    Returns:
        Dict with keys: is_anomaly, iv_z_score, underlying_change, type.
    """
    arr = np.asarray(historical_ivs, dtype=float)
    arr = arr[np.isfinite(arr)]

    if len(arr) < 2:
        return {
            "is_anomaly": False,
            "iv_z_score": 0.0,
            "underlying_change": underlying_change_pct,
            "type": "normal",
        }

    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))

    if std < 1e-10:
        return {
            "is_anomaly": False,
            "iv_z_score": 0.0,
            "underlying_change": underlying_change_pct,
            "type": "normal",
        }

    iv_z_score = (current_iv - mean) / std

    # Determine expansion or contraction
    if iv_z_score > threshold_sigma:
        iv_type = "expansion"
    elif iv_z_score < -threshold_sigma:
        iv_type = "contraction"
    else:
        iv_type = "normal"

    is_anomaly = abs(iv_z_score) > threshold_sigma and abs(underlying_change_pct) < 1.0

    return {
        "is_anomaly": is_anomaly,
        "iv_z_score": float(iv_z_score),
        "underlying_change": underlying_change_pct,
        "type": iv_type,
    }


def detect_volume_oi_anomaly(
    volume: int,
    open_interest: int,
    historical_ratios: list[float],
    threshold_sigma: float = 2.0,
) -> dict:
    """Flag when V/OI ratio is unusually high (new positioning).

    Args:
        volume: Current volume.
        open_interest: Current open interest.
        historical_ratios: Historical V/OI ratio values.
        threshold_sigma: Number of standard deviations for anomaly flag.

    Returns:
        Dict with keys: is_anomaly, ratio, z_score, interpretation.
    """
    if open_interest == 0:
        ratio = 0.0
    else:
        ratio = volume / open_interest

    # Determine interpretation based on ratio
    if ratio > 3.0:
        interpretation = "aggressive new positioning"
    elif ratio > 1.0:
        interpretation = "active trading"
    elif ratio < 0.3:
        interpretation = "quiet"
    else:
        interpretation = "normal"

    arr = np.asarray(historical_ratios, dtype=float)
    arr = arr[np.isfinite(arr)]

    if len(arr) < 2:
        return {
            "is_anomaly": False,
            "ratio": float(ratio),
            "z_score": 0.0,
            "interpretation": interpretation,
        }

    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))

    if std < 1e-10:
        return {
            "is_anomaly": False,
            "ratio": float(ratio),
            "z_score": 0.0,
            "interpretation": interpretation,
        }

    z_score = (ratio - mean) / std

    return {
        "is_anomaly": z_score > threshold_sigma,
        "ratio": float(ratio),
        "z_score": float(z_score),
        "interpretation": interpretation,
    }


def detect_strike_clustering(
    chain_volumes: dict[float, int],
    spot_price: float,
    top_n: int = 5,
) -> list[dict]:
    """Identify strikes attracting disproportionate volume.

    Args:
        chain_volumes: Mapping of strike price to volume.
            Keys are strikes, values are total volumes at that strike.
        spot_price: Current underlying price.
        top_n: Number of top strikes to return.

    Returns:
        List of dicts sorted by concentration descending. Each entry has:
        strike, volume, concentration, distance_from_spot_pct, type.
    """
    if not chain_volumes:
        return []

    total_volume = sum(chain_volumes.values())
    if total_volume == 0:
        return []

    results: list[dict] = []
    for strike, vol in chain_volumes.items():
        concentration = vol / total_volume
        distance_pct = ((strike - spot_price) / spot_price) * 100.0 if spot_price != 0 else 0.0

        # Classify based on relationship to spot
        if strike > spot_price:
            strike_type = "call"
        elif strike < spot_price:
            strike_type = "put"
        else:
            strike_type = "both"

        results.append({
            "strike": float(strike),
            "volume": vol,
            "concentration": float(concentration),
            "distance_from_spot_pct": float(distance_pct),
            "type": strike_type,
        })

    # Sort by concentration descending
    results.sort(key=lambda x: x["concentration"], reverse=True)

    return results[:top_n]


# ---------------------------------------------------------------------------
# Convenience chain scanner
# ---------------------------------------------------------------------------


def _compute_overall_score(
    volume_anomalies: list[dict],
    iv_anomalies: list[dict],
    voi_anomalies: list[dict],
) -> float:
    """Compute an overall anomaly score in [0, 1] from z-score detectors.

    Counts the fraction of detections that are flagged as anomalies.
    """
    all_results = volume_anomalies + iv_anomalies + voi_anomalies
    if not all_results:
        return 0.0

    anomaly_count = sum(1 for r in all_results if r.get("is_anomaly", False))
    return min(anomaly_count / max(len(all_results), 1), 1.0)


def scan_chain_anomalies(
    chain: OptionsChain,
    historical_data: dict | None = None,
) -> AnomalyReport:
    """Run all anomaly detectors on an OptionsChain.

    Args:
        chain: An :class:`OptionsChain` to scan.
        historical_data: Optional dict with keys:
            - ``volume_history``: ``{strike: [volumes]}``
            - ``iv_history``: ``{strike: [ivs]}``
            - ``voi_history``: ``[ratios]``
            If None, returns a report with all is_anomaly=False.

    Returns:
        :class:`AnomalyReport` with all detector results.
    """
    if historical_data is None:
        return AnomalyReport(
            volume_anomalies=[],
            iv_anomalies=[],
            voi_anomalies=[],
            strike_clusters=[],
            overall_score=0.0,
        )

    volume_history = historical_data.get("volume_history", {})
    iv_history = historical_data.get("iv_history", {})
    voi_history = historical_data.get("voi_history", [])

    volume_anomalies: list[dict] = []
    iv_anomalies: list[dict] = []
    voi_anomalies: list[dict] = []

    # Build strike volumes for clustering
    chain_volumes: dict[float, int] = {}

    for contract in chain.contracts:
        strike = contract.strike

        # Accumulate strike volumes
        chain_volumes[strike] = chain_volumes.get(strike, 0) + contract.volume

        # Volume anomaly per strike
        hist_vol = volume_history.get(strike, [])
        vol_result = detect_volume_anomaly(contract.volume, hist_vol)
        vol_result["strike"] = strike
        vol_result["option_type"] = contract.option_type
        volume_anomalies.append(vol_result)

        # IV anomaly per strike
        hist_iv = iv_history.get(strike, [])
        iv_result = detect_iv_anomaly(contract.iv, hist_iv, 0.0)
        iv_result["strike"] = strike
        iv_result["option_type"] = contract.option_type
        iv_anomalies.append(iv_result)

        # V/OI anomaly per contract
        voi_result = detect_volume_oi_anomaly(
            contract.volume, contract.open_interest, voi_history
        )
        voi_result["strike"] = strike
        voi_result["option_type"] = contract.option_type
        voi_anomalies.append(voi_result)

    # Strike clustering
    strike_clusters = detect_strike_clustering(chain_volumes, chain.spot_price)

    # Compute overall score from z-score detectors
    overall_score = _compute_overall_score(volume_anomalies, iv_anomalies, voi_anomalies)

    return AnomalyReport(
        volume_anomalies=volume_anomalies,
        iv_anomalies=iv_anomalies,
        voi_anomalies=voi_anomalies,
        strike_clusters=strike_clusters,
        overall_score=overall_score,
    )


# ---------------------------------------------------------------------------
# FlowAnomalyDetector — IsolationForest wrapper
# ---------------------------------------------------------------------------


class FlowAnomalyDetector:
    """Isolation forest for multi-feature anomaly detection on options flow.

    Wraps scikit-learn's :class:`~sklearn.ensemble.IsolationForest`.
    Feature columns expected: ``[volume, oi, v_oi_ratio, iv, iv_change,
    premium, delta, gamma, moneyness]``.

    Args:
        contamination: Expected fraction of outliers in training data.
        n_estimators: Number of trees in the isolation forest.
        random_state: Random seed for reproducibility.
    """

    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        random_state: int = 42,
    ) -> None:
        from sklearn.ensemble import IsolationForest

        self._model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
        )
        self._fitted = False

    def fit(self, feature_matrix: np.ndarray) -> None:
        """Fit the isolation forest on historical flow data.

        Args:
            feature_matrix: 2-D array of shape ``(n_samples, n_features)``.
        """
        self._model.fit(feature_matrix)
        self._fitted = True

    def predict(self, features: np.ndarray) -> list[dict]:
        """Score each row for anomalousness.

        Args:
            features: 2-D array of shape ``(n_samples, n_features)``.

        Returns:
            List of dicts, one per row: ``{"is_anomaly": bool,
            "anomaly_score": float}``.  The anomaly score comes from
            ``decision_function()`` (lower = more anomalous).

        Raises:
            RuntimeError: If the model has not been fitted.
        """
        if not self._fitted:
            raise RuntimeError("FlowAnomalyDetector has not been fitted")

        labels = self._model.predict(features)
        scores = self._model.decision_function(features)

        results: list[dict] = []
        for label, score in zip(labels, scores):
            results.append({
                "is_anomaly": int(label) == -1,
                "anomaly_score": float(score),
            })
        return results

    def save(self, path: str) -> None:
        """Persist the fitted model to disk via pickle.

        Args:
            path: File path to write (parent directory must exist).

        Raises:
            RuntimeError: If the model has not been fitted.
        """
        if not self._fitted:
            raise RuntimeError("Cannot save: FlowAnomalyDetector has not been fitted")

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self._model, f)
        logger.info("Saved FlowAnomalyDetector to %s", path)

    def load(self, path: str) -> None:
        """Load a previously fitted model from disk.

        Args:
            path: File path to read.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")

        with open(path, "rb") as f:
            self._model = pickle.load(f)  # noqa: S301
        self._fitted = True
        logger.info("Loaded FlowAnomalyDetector from %s", path)


# ---------------------------------------------------------------------------
# AnomalyManager — async pipeline
# ---------------------------------------------------------------------------


def _classify_score(score: float) -> str:
    """Map overall anomaly score to severity level."""
    if score > 0.7:
        return "alert"
    if score > 0.4:
        return "elevated"
    return "normal"


class AnomalyManager:
    """Async pipeline combining z-score detectors with isolation forest.

    Persists the composite ``anomaly_score`` to the feature store after
    each update cycle.

    Args:
        feature_store: An initialised :class:`FeatureStore` instance.
        model_dir: Directory for isolation forest model artifacts.
    """

    _Z_SCORE_WEIGHT = 0.6
    _FOREST_WEIGHT = 0.4

    def __init__(self, feature_store: FeatureStore, model_dir: str) -> None:
        self._feature_store = feature_store
        self._model_dir = model_dir
        self._forest: FlowAnomalyDetector | None = None
        self._latest_report: dict[str, AnomalyReport] = {}  # keyed by ticker

    @property
    def model_path(self) -> str:
        """Path to the persisted isolation forest model."""
        return os.path.join(self._model_dir, "anomaly_forest.pkl")

    async def update(
        self,
        chain: OptionsChain,
        historical_data: dict | None,
        ticker: str = "SPX",
    ) -> AnomalyReport:
        """Run z-score detectors + isolation forest and persist results.

        Args:
            chain: Current options chain snapshot.
            historical_data: Historical data for z-score baselines.
            ticker: Ticker symbol for feature store persistence.

        Returns:
            :class:`AnomalyReport` with composite ``overall_score``.
        """
        # 1. Z-score scan
        report = scan_chain_anomalies(chain, historical_data)

        z_score_raw = report.overall_score  # already 0-1

        # 2. Isolation forest score (if fitted)
        forest_raw = 0.0
        if self._forest is not None and self._forest._fitted:
            features = self._extract_features(chain)
            if features is not None and len(features) > 0:
                predictions = self._forest.predict(features)
                # Fraction of contracts flagged anomalous
                anomaly_count = sum(1 for p in predictions if p["is_anomaly"])
                forest_raw = anomaly_count / len(predictions) if predictions else 0.0

        # 3. Compute weighted overall score
        if self._forest is not None and self._forest._fitted:
            overall = (
                self._Z_SCORE_WEIGHT * z_score_raw
                + self._FOREST_WEIGHT * forest_raw
            )
        else:
            # No isolation forest — use z-score only
            overall = z_score_raw

        overall = min(max(overall, 0.0), 1.0)
        report.overall_score = overall

        # 4. Cache report
        self._latest_report[ticker] = report

        # 5. Persist to feature store
        today = date.today().isoformat()
        await self._feature_store.save_features(
            ticker, today, {"anomaly_score": overall}
        )

        logger.info(
            "Anomaly update for %s: score=%.3f (%s)",
            ticker,
            overall,
            _classify_score(overall),
        )

        return report

    async def train_forest(
        self,
        historical_chains: list[dict],
    ) -> dict:
        """Fit isolation forest on historical flow data.

        Each entry in *historical_chains* should be a dict with keys
        matching the feature columns: ``volume``, ``oi``, ``v_oi_ratio``,
        ``iv``, ``iv_change``, ``premium``, ``delta``, ``gamma``,
        ``moneyness``.

        Args:
            historical_chains: List of dicts, one per observation.

        Returns:
            Training statistics dict.
        """
        if not historical_chains:
            return {"status": "error", "reason": "no training data"}

        feature_cols = [
            "volume", "oi", "v_oi_ratio", "iv", "iv_change",
            "premium", "delta", "gamma", "moneyness",
        ]

        rows: list[list[float]] = []
        for entry in historical_chains:
            row = [float(entry.get(col, 0.0)) for col in feature_cols]
            rows.append(row)

        matrix = np.array(rows, dtype=float)

        self._forest = FlowAnomalyDetector()
        self._forest.fit(matrix)

        # Save to disk
        os.makedirs(self._model_dir, exist_ok=True)
        self._forest.save(self.model_path)

        return {
            "status": "ok",
            "n_samples": len(rows),
            "n_features": len(feature_cols),
            "model_path": self.model_path,
        }

    async def get_current_anomalies(
        self,
        ticker: str = "SPX",
    ) -> AnomalyReport | None:
        """Return the most recently cached anomaly report.

        Args:
            ticker: Ticker symbol.

        Returns:
            The cached :class:`AnomalyReport`, or ``None`` if no update
            has been run yet for this ticker.
        """
        return self._latest_report.get(ticker)

    def _extract_features(self, chain: OptionsChain) -> np.ndarray | None:
        """Build a feature matrix from an OptionsChain for isolation forest.

        Returns:
            2-D numpy array of shape ``(n_contracts, 9)`` or ``None``
            if the chain is empty.
        """
        if not chain.contracts:
            return None

        rows: list[list[float]] = []
        spot = chain.spot_price if chain.spot_price != 0 else 1.0

        for c in chain.contracts:
            oi = c.open_interest if c.open_interest > 0 else 1
            v_oi = c.volume / oi
            premium = c.mid * 100.0  # approximate notional
            moneyness = c.strike / spot

            rows.append([
                float(c.volume),
                float(c.open_interest),
                float(v_oi),
                float(c.iv),
                0.0,  # iv_change — not available in a single snapshot
                float(premium),
                float(c.delta),
                float(c.gamma),
                float(moneyness),
            ])

        return np.array(rows, dtype=float)
