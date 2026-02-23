"""Tests for statistical anomaly detection (src/ml/anomaly.py).

Covers z-score detectors for volume, IV, V/OI, and strike clustering,
the AnomalyReport dataclass, scan_chain_anomalies convenience function,
FlowAnomalyDetector (IsolationForest), and AnomalyManager pipeline.
"""

from __future__ import annotations

import os
import tempfile
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from src.data import OptionContract, OptionsChain
from src.ml.anomaly import (
    AnomalyManager,
    AnomalyReport,
    FlowAnalyzer,
    FlowAnomalyDetector,
    _classify_score,
    detect_iv_anomaly,
    detect_strike_clustering,
    detect_volume_anomaly,
    detect_volume_oi_anomaly,
    scan_chain_anomalies,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_contract(
    strike: float,
    option_type: str,
    volume: int = 100,
    open_interest: int = 1000,
    iv: float = 0.20,
    expiry: date | None = None,
    days_out: int = 30,
) -> OptionContract:
    """Create a minimal OptionContract for testing."""
    if expiry is None:
        expiry = date.today() + timedelta(days=days_out)
    return OptionContract(
        ticker="SPX",
        expiry=expiry,
        strike=strike,
        option_type=option_type,
        bid=1.0,
        ask=1.5,
        last=1.25,
        volume=volume,
        open_interest=open_interest,
        iv=iv,
    )


def _make_chain(
    contracts: list[OptionContract],
    spot: float = 5000.0,
) -> OptionsChain:
    """Wrap contracts in an OptionsChain."""
    return OptionsChain(
        ticker="SPX",
        spot_price=spot,
        timestamp=datetime.now(),
        contracts=contracts,
    )


# ===================================================================
# detect_volume_anomaly
# ===================================================================


class TestDetectVolumeAnomaly:
    """Tests for volume z-score detection."""

    def test_normal_volume_not_anomaly(self):
        """Volume within 1 sigma should not be flagged."""
        result = detect_volume_anomaly(105, [100, 100, 100, 100, 100, 110, 90, 100, 95, 105])
        assert result["is_anomaly"] is False
        assert abs(result["z_score"]) < 2.0

    def test_3_sigma_spike_is_anomaly(self):
        """Volume 3+ sigma above mean should be flagged."""
        history = [100] * 20
        # std of constant list is 0, so use slight variation
        history = [100, 102, 98, 101, 99, 100, 103, 97, 100, 101,
                   100, 102, 98, 101, 99, 100, 103, 97, 100, 101]
        mean = np.mean(history)
        std = np.std(history, ddof=1)
        spike = int(mean + 3.5 * std)  # well above 3 sigma

        result = detect_volume_anomaly(spike, history)
        assert result["is_anomaly"] is True
        assert result["z_score"] > 2.0

    def test_empty_history_not_anomaly(self):
        """Empty history should return not anomaly."""
        result = detect_volume_anomaly(500, [])
        assert result["is_anomaly"] is False
        assert result["z_score"] == 0.0
        assert result["mean"] == 0.0
        assert result["std"] == 0.0

    def test_single_data_point_not_anomaly(self):
        """Single data point history should return not anomaly."""
        result = detect_volume_anomaly(500, [100])
        assert result["is_anomaly"] is False

    def test_zero_std_not_anomaly(self):
        """All identical history values (zero std) should not flag."""
        result = detect_volume_anomaly(200, [100, 100, 100, 100, 100])
        assert result["is_anomaly"] is False
        assert result["std"] == 0.0

    def test_returns_correct_fields(self):
        """Result should have all expected keys."""
        result = detect_volume_anomaly(100, [90, 100, 110, 95, 105])
        expected_keys = {"is_anomaly", "z_score", "threshold", "volume", "mean", "std"}
        assert set(result.keys()) == expected_keys

    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        history = [100, 102, 98, 101, 99, 100, 103, 97, 100, 101]
        mean = np.mean(history)
        std = np.std(history, ddof=1)

        # Just above 1 sigma
        volume = int(mean + 1.5 * std)
        result_strict = detect_volume_anomaly(volume, history, threshold_sigma=2.0)
        result_loose = detect_volume_anomaly(volume, history, threshold_sigma=1.0)

        assert result_strict["is_anomaly"] is False
        assert result_loose["is_anomaly"] is True


# ===================================================================
# detect_iv_anomaly
# ===================================================================


class TestDetectIVAnomaly:
    """Tests for IV anomaly detection."""

    def test_iv_spike_no_underlying_move_is_anomaly(self):
        """IV spike with no underlying change -> anomaly."""
        history = [0.20, 0.21, 0.19, 0.20, 0.22, 0.18, 0.20, 0.21, 0.19, 0.20]
        mean = np.mean(history)
        std = np.std(history, ddof=1)
        spike_iv = mean + 3.0 * std

        result = detect_iv_anomaly(spike_iv, history, underlying_change_pct=0.1)
        assert result["is_anomaly"] is True
        assert result["type"] == "expansion"

    def test_iv_spike_with_underlying_move_not_anomaly(self):
        """IV spike with corresponding underlying move -> not anomaly."""
        history = [0.20, 0.21, 0.19, 0.20, 0.22, 0.18, 0.20, 0.21, 0.19, 0.20]
        mean = np.mean(history)
        std = np.std(history, ddof=1)
        spike_iv = mean + 3.0 * std

        result = detect_iv_anomaly(spike_iv, history, underlying_change_pct=2.5)
        assert result["is_anomaly"] is False  # underlying moved enough

    def test_iv_contraction(self):
        """Large IV drop without underlying move -> contraction anomaly."""
        history = [0.25, 0.26, 0.24, 0.25, 0.27, 0.23, 0.25, 0.26, 0.24, 0.25]
        mean = np.mean(history)
        std = np.std(history, ddof=1)
        low_iv = mean - 3.0 * std

        result = detect_iv_anomaly(low_iv, history, underlying_change_pct=0.2)
        assert result["is_anomaly"] is True
        assert result["type"] == "contraction"

    def test_normal_iv_not_anomaly(self):
        """IV within normal range -> not anomaly."""
        history = [0.20, 0.21, 0.19, 0.20, 0.22, 0.18, 0.20, 0.21, 0.19, 0.20]
        result = detect_iv_anomaly(0.20, history, underlying_change_pct=0.0)
        assert result["is_anomaly"] is False
        assert result["type"] == "normal"

    def test_empty_history(self):
        """Empty history should return not anomaly."""
        result = detect_iv_anomaly(0.30, [], underlying_change_pct=0.0)
        assert result["is_anomaly"] is False
        assert result["type"] == "normal"

    def test_zero_std(self):
        """Constant history should return not anomaly."""
        result = detect_iv_anomaly(0.30, [0.20, 0.20, 0.20], underlying_change_pct=0.0)
        assert result["is_anomaly"] is False


# ===================================================================
# detect_volume_oi_anomaly
# ===================================================================


class TestDetectVolumeOIAnomaly:
    """Tests for volume/OI ratio detection."""

    def test_high_ratio_is_anomaly(self):
        """V/OI >> historical ratios -> anomaly."""
        historical = [0.5, 0.6, 0.4, 0.55, 0.45, 0.5, 0.6, 0.4, 0.5, 0.55]
        result = detect_volume_oi_anomaly(5000, 1000, historical)
        # ratio = 5.0, way above historical mean ~0.5
        assert result["is_anomaly"] is True
        assert result["ratio"] == pytest.approx(5.0)
        assert result["interpretation"] == "aggressive new positioning"

    def test_normal_ratio_not_anomaly(self):
        """V/OI within historical range -> not anomaly."""
        historical = [0.5, 0.6, 0.4, 0.55, 0.45, 0.5, 0.6, 0.4, 0.5, 0.55]
        result = detect_volume_oi_anomaly(500, 1000, historical)
        # ratio = 0.5, right at mean
        assert result["is_anomaly"] is False
        assert result["ratio"] == pytest.approx(0.5)

    def test_quiet_interpretation(self):
        """Low V/OI ratio -> quiet interpretation."""
        historical = [0.5, 0.6, 0.4, 0.55, 0.45]
        result = detect_volume_oi_anomaly(10, 1000, historical)
        assert result["interpretation"] == "quiet"
        assert result["ratio"] == pytest.approx(0.01)

    def test_active_trading_interpretation(self):
        """Moderate V/OI ratio -> active trading."""
        historical = [0.5, 0.6, 0.4, 0.55, 0.45]
        result = detect_volume_oi_anomaly(1500, 1000, historical)
        assert result["interpretation"] == "active trading"

    def test_zero_open_interest(self):
        """Zero OI should not crash, ratio = 0."""
        result = detect_volume_oi_anomaly(100, 0, [0.5, 0.6])
        assert result["ratio"] == 0.0

    def test_empty_history(self):
        """Empty history -> not anomaly."""
        result = detect_volume_oi_anomaly(500, 1000, [])
        assert result["is_anomaly"] is False


# ===================================================================
# detect_strike_clustering
# ===================================================================


class TestDetectStrikeClustering:
    """Tests for strike clustering detection."""

    def test_known_distribution(self):
        """Known volume distribution returns correct top strikes."""
        chain_volumes = {
            5000.0: 10000,
            5050.0: 500,
            4950.0: 500,
            5100.0: 200,
            4900.0: 100,
        }
        results = detect_strike_clustering(chain_volumes, spot_price=5000.0, top_n=3)
        assert len(results) == 3
        assert results[0]["strike"] == 5000.0
        assert results[0]["concentration"] > 0.8  # dominates
        assert results[0]["type"] == "both"  # at spot

    def test_top_n_respected(self):
        """Only top_n results are returned."""
        chain_volumes = {float(i): 100 for i in range(4990, 5010)}
        results = detect_strike_clustering(chain_volumes, spot_price=5000.0, top_n=5)
        assert len(results) == 5

    def test_empty_volumes(self):
        """Empty chain_volumes returns empty list."""
        results = detect_strike_clustering({}, spot_price=5000.0)
        assert results == []

    def test_zero_total_volume(self):
        """All zero volumes returns empty list."""
        chain_volumes = {5000.0: 0, 5050.0: 0}
        results = detect_strike_clustering(chain_volumes, spot_price=5000.0)
        assert results == []

    def test_distance_from_spot(self):
        """Distance from spot is correctly computed."""
        chain_volumes = {5100.0: 1000}
        results = detect_strike_clustering(chain_volumes, spot_price=5000.0)
        assert len(results) == 1
        assert results[0]["distance_from_spot_pct"] == pytest.approx(2.0)
        assert results[0]["type"] == "call"  # above spot

    def test_put_type_below_spot(self):
        """Strikes below spot are classified as put."""
        chain_volumes = {4900.0: 1000}
        results = detect_strike_clustering(chain_volumes, spot_price=5000.0)
        assert results[0]["type"] == "put"

    def test_sorted_by_concentration(self):
        """Results are sorted by concentration descending."""
        chain_volumes = {
            5000.0: 100,
            5050.0: 500,
            4950.0: 300,
        }
        results = detect_strike_clustering(chain_volumes, spot_price=5000.0, top_n=10)
        concentrations = [r["concentration"] for r in results]
        assert concentrations == sorted(concentrations, reverse=True)


# ===================================================================
# AnomalyReport
# ===================================================================


class TestAnomalyReport:
    """Tests for the AnomalyReport dataclass."""

    def test_default_values(self):
        """Default report has empty lists and zero score."""
        report = AnomalyReport()
        assert report.volume_anomalies == []
        assert report.iv_anomalies == []
        assert report.voi_anomalies == []
        assert report.strike_clusters == []
        assert report.overall_score == 0.0
        assert report.timestamp  # should be set

    def test_custom_values(self):
        """Can set custom values."""
        report = AnomalyReport(
            volume_anomalies=[{"is_anomaly": True}],
            overall_score=0.85,
        )
        assert len(report.volume_anomalies) == 1
        assert report.overall_score == 0.85


# ===================================================================
# scan_chain_anomalies
# ===================================================================


class TestScanChainAnomalies:
    """Tests for the scan_chain_anomalies convenience function."""

    def test_no_historical_data_returns_empty_report(self):
        """Without historical data, report has no anomalies."""
        chain = _make_chain([
            _make_contract(5000, "call"),
            _make_contract(5000, "put"),
        ])
        report = scan_chain_anomalies(chain, historical_data=None)
        assert isinstance(report, AnomalyReport)
        assert report.overall_score == 0.0
        assert report.volume_anomalies == []
        assert report.iv_anomalies == []
        assert report.voi_anomalies == []

    def test_with_historical_data(self):
        """With historical data, all detectors run."""
        contracts = [
            _make_contract(5000, "call", volume=100, open_interest=1000, iv=0.20),
            _make_contract(5000, "put", volume=200, open_interest=500, iv=0.22),
            _make_contract(5050, "call", volume=50, open_interest=800, iv=0.18),
        ]
        chain = _make_chain(contracts)

        historical_data = {
            "volume_history": {
                5000.0: [90, 100, 110, 95, 105, 100, 98, 102, 97, 103],
                5050.0: [45, 50, 55, 48, 52, 50, 47, 53, 49, 51],
            },
            "iv_history": {
                5000.0: [0.19, 0.20, 0.21, 0.19, 0.20, 0.21, 0.19, 0.20, 0.21, 0.20],
                5050.0: [0.17, 0.18, 0.19, 0.17, 0.18, 0.19, 0.17, 0.18, 0.19, 0.18],
            },
            "voi_history": [0.1, 0.12, 0.09, 0.11, 0.10, 0.08, 0.12, 0.09, 0.11, 0.10],
        }

        report = scan_chain_anomalies(chain, historical_data)

        assert isinstance(report, AnomalyReport)
        assert len(report.volume_anomalies) == 3  # one per contract
        assert len(report.iv_anomalies) == 3
        assert len(report.voi_anomalies) == 3
        assert len(report.strike_clusters) > 0
        assert 0.0 <= report.overall_score <= 1.0

    def test_anomalous_chain_has_positive_score(self):
        """Chain with spikes should produce a positive overall score."""
        contracts = [
            _make_contract(5000, "call", volume=99999, open_interest=100, iv=0.80),
        ]
        chain = _make_chain(contracts)

        historical_data = {
            "volume_history": {
                5000.0: [100, 102, 98, 101, 99, 100, 103, 97, 100, 101],
            },
            "iv_history": {
                5000.0: [0.19, 0.20, 0.21, 0.19, 0.20, 0.21, 0.19, 0.20, 0.21, 0.20],
            },
            "voi_history": [0.1, 0.12, 0.09, 0.11, 0.10],
        }

        report = scan_chain_anomalies(chain, historical_data)
        assert report.overall_score > 0.0

    def test_empty_chain_with_historical_data(self):
        """Empty chain with historical data produces empty report."""
        chain = _make_chain([])
        historical_data = {
            "volume_history": {},
            "iv_history": {},
            "voi_history": [],
        }
        report = scan_chain_anomalies(chain, historical_data)
        assert report.overall_score == 0.0
        assert report.volume_anomalies == []


# ===================================================================
# FlowAnomalyDetector
# ===================================================================


def _make_synthetic_data(n_normal: int = 200, n_outliers: int = 10, seed: int = 42):
    """Generate synthetic flow data with known outliers."""
    rng = np.random.RandomState(seed)
    # Normal data: centred around moderate values
    normal = rng.normal(
        loc=[500, 1000, 0.5, 0.20, 0.0, 5000, 0.50, 0.01, 1.0],
        scale=[100, 200, 0.1, 0.02, 0.005, 1000, 0.10, 0.005, 0.05],
        size=(n_normal, 9),
    )
    # Outliers: extreme values
    outliers = rng.normal(
        loc=[50000, 100, 50.0, 0.80, 0.3, 500000, 0.99, 0.10, 2.0],
        scale=[5000, 10, 5.0, 0.05, 0.05, 50000, 0.01, 0.01, 0.1],
        size=(n_outliers, 9),
    )
    data = np.vstack([normal, outliers])
    labels = np.array([1] * n_normal + [-1] * n_outliers)
    return data, labels


class TestFlowAnomalyDetector:
    """Tests for IsolationForest-based anomaly detection."""

    def test_fit_predict_basic(self):
        """Detector can fit and predict on synthetic data."""
        data, _labels = _make_synthetic_data()
        det = FlowAnomalyDetector(contamination=0.05)
        det.fit(data)
        results = det.predict(data)

        assert len(results) == len(data)
        assert all("is_anomaly" in r for r in results)
        assert all("anomaly_score" in r for r in results)

    def test_detects_known_outliers(self):
        """Most known outliers should be flagged as anomalous."""
        data, labels = _make_synthetic_data(n_normal=200, n_outliers=20)
        det = FlowAnomalyDetector(contamination=0.10)
        det.fit(data)
        results = det.predict(data)

        # Check the last 20 (outlier) rows
        outlier_results = results[-20:]
        flagged = sum(1 for r in outlier_results if r["is_anomaly"])
        # At least half the outliers should be detected
        assert flagged >= 10, f"Only {flagged}/20 outliers detected"

    def test_normal_data_mostly_not_anomalous(self):
        """Normal data should rarely be flagged."""
        data, _labels = _make_synthetic_data()
        det = FlowAnomalyDetector(contamination=0.05)
        det.fit(data)
        results = det.predict(data[:200])  # only normal data

        flagged = sum(1 for r in results if r["is_anomaly"])
        # Expect <15% false positives on normal data
        assert flagged < 30, f"{flagged}/200 normal points flagged"

    def test_predict_unfitted_raises(self):
        """Predict on unfitted detector raises RuntimeError."""
        det = FlowAnomalyDetector()
        data, _ = _make_synthetic_data()
        with pytest.raises(RuntimeError, match="not been fitted"):
            det.predict(data)

    def test_save_load_roundtrip(self):
        """Save/load preserves model predictions."""
        data, _ = _make_synthetic_data()
        det = FlowAnomalyDetector()
        det.fit(data)
        pred_before = det.predict(data[:5])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "model.pkl")
            det.save(path)
            assert os.path.exists(path)

            det2 = FlowAnomalyDetector()
            det2.load(path)
            pred_after = det2.predict(data[:5])

        for a, b in zip(pred_before, pred_after):
            assert a["is_anomaly"] == b["is_anomaly"]
            assert a["anomaly_score"] == pytest.approx(b["anomaly_score"])

    def test_save_unfitted_raises(self):
        """Saving unfitted detector raises RuntimeError."""
        det = FlowAnomalyDetector()
        with pytest.raises(RuntimeError, match="not been fitted"):
            det.save("/tmp/should_not_exist.pkl")

    def test_load_nonexistent_raises(self):
        """Loading from nonexistent path raises FileNotFoundError."""
        det = FlowAnomalyDetector()
        with pytest.raises(FileNotFoundError):
            det.load("/tmp/nonexistent_anomaly_model_xyz.pkl")


# ===================================================================
# _classify_score helper
# ===================================================================


class TestClassifyScore:
    """Tests for score classification."""

    def test_alert(self):
        assert _classify_score(0.8) == "alert"
        assert _classify_score(0.71) == "alert"

    def test_elevated(self):
        assert _classify_score(0.5) == "elevated"
        assert _classify_score(0.41) == "elevated"
        assert _classify_score(0.7) == "elevated"

    def test_normal(self):
        assert _classify_score(0.3) == "normal"
        assert _classify_score(0.0) == "normal"
        assert _classify_score(0.4) == "normal"


# ===================================================================
# AnomalyManager
# ===================================================================


def _make_mock_feature_store() -> MagicMock:
    """Create a mock FeatureStore with async methods."""
    store = MagicMock()
    store.save_features = AsyncMock()
    store.get_latest_features = AsyncMock(return_value=None)
    return store


class TestAnomalyManagerUpdate:
    """Tests for AnomalyManager.update()."""

    @pytest.mark.asyncio
    async def test_update_without_forest(self):
        """Manager works without a fitted isolation forest (z-scores only)."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            contracts = [
                _make_contract(5000, "call", volume=100, open_interest=1000, iv=0.20),
            ]
            chain = _make_chain(contracts)
            historical_data = {
                "volume_history": {5000.0: [90, 100, 110, 95, 105]},
                "iv_history": {5000.0: [0.19, 0.20, 0.21, 0.19, 0.20]},
                "voi_history": [0.1, 0.12, 0.09, 0.11, 0.10],
            }

            report = await mgr.update(chain, historical_data, ticker="SPX")

            assert isinstance(report, AnomalyReport)
            assert 0.0 <= report.overall_score <= 1.0
            store.save_features.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_persists_anomaly_score(self):
        """Update persists anomaly_score to feature store."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            contracts = [
                _make_contract(5000, "call", volume=100, open_interest=1000, iv=0.20),
            ]
            chain = _make_chain(contracts)

            await mgr.update(chain, None, ticker="SPX")

            call_args = store.save_features.call_args
            assert call_args[0][0] == "SPX"  # ticker
            features = call_args[0][2]
            assert "anomaly_score" in features

    @pytest.mark.asyncio
    async def test_update_with_forest(self):
        """Manager combines z-score and forest scores when forest is fitted."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            # Train forest on synthetic data
            training_data = []
            rng = np.random.RandomState(42)
            for _ in range(100):
                training_data.append({
                    "volume": float(rng.normal(500, 100)),
                    "oi": float(rng.normal(1000, 200)),
                    "v_oi_ratio": float(rng.normal(0.5, 0.1)),
                    "iv": float(rng.normal(0.20, 0.02)),
                    "iv_change": float(rng.normal(0, 0.005)),
                    "premium": float(rng.normal(5000, 1000)),
                    "delta": float(rng.normal(0.50, 0.10)),
                    "gamma": float(rng.normal(0.01, 0.005)),
                    "moneyness": float(rng.normal(1.0, 0.05)),
                })
            await mgr.train_forest(training_data)

            # Now update with a chain
            contracts = [
                _make_contract(5000, "call", volume=100, open_interest=1000, iv=0.20),
            ]
            chain = _make_chain(contracts)
            historical_data = {
                "volume_history": {5000.0: [90, 100, 110, 95, 105]},
                "iv_history": {5000.0: [0.19, 0.20, 0.21, 0.19, 0.20]},
                "voi_history": [0.1, 0.12, 0.09, 0.11, 0.10],
            }

            report = await mgr.update(chain, historical_data)
            assert isinstance(report, AnomalyReport)
            assert 0.0 <= report.overall_score <= 1.0

    @pytest.mark.asyncio
    async def test_update_caches_report(self):
        """Update caches the latest report."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            contracts = [_make_contract(5000, "call")]
            chain = _make_chain(contracts)

            await mgr.update(chain, None, ticker="SPX")

            cached = await mgr.get_current_anomalies(ticker="SPX")
            assert cached is not None
            assert isinstance(cached, AnomalyReport)


class TestAnomalyManagerTrainForest:
    """Tests for AnomalyManager.train_forest()."""

    @pytest.mark.asyncio
    async def test_train_forest_basic(self):
        """Training returns success stats."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            training_data = []
            for i in range(50):
                training_data.append({
                    "volume": 500.0 + i,
                    "oi": 1000.0,
                    "v_oi_ratio": 0.5,
                    "iv": 0.20,
                    "iv_change": 0.0,
                    "premium": 5000.0,
                    "delta": 0.50,
                    "gamma": 0.01,
                    "moneyness": 1.0,
                })

            result = await mgr.train_forest(training_data)

            assert result["status"] == "ok"
            assert result["n_samples"] == 50
            assert result["n_features"] == 9
            assert os.path.exists(result["model_path"])

    @pytest.mark.asyncio
    async def test_train_forest_empty_data(self):
        """Training with empty data returns error."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)
            result = await mgr.train_forest([])
            assert result["status"] == "error"


class TestAnomalyManagerGetCurrentAnomalies:
    """Tests for AnomalyManager.get_current_anomalies()."""

    @pytest.mark.asyncio
    async def test_returns_none_before_update(self):
        """Returns None when no update has been run."""
        store = _make_mock_feature_store()
        mgr = AnomalyManager(store, "/tmp")
        result = await mgr.get_current_anomalies("SPX")
        assert result is None


class TestOverallScoreComputation:
    """Tests for overall score computation with weights."""

    @pytest.mark.asyncio
    async def test_score_without_forest_equals_zscore(self):
        """Without forest, overall score equals z-score scan score."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            # Create a chain with known anomalous activity
            contracts = [
                _make_contract(5000, "call", volume=99999, open_interest=100, iv=0.80),
            ]
            chain = _make_chain(contracts)
            historical_data = {
                "volume_history": {5000.0: [100, 102, 98, 101, 99]},
                "iv_history": {5000.0: [0.19, 0.20, 0.21, 0.19, 0.20]},
                "voi_history": [0.1, 0.12, 0.09, 0.11, 0.10],
            }

            report = await mgr.update(chain, historical_data)

            # Without forest, overall_score = z_score_raw
            z_report = scan_chain_anomalies(chain, historical_data)
            assert report.overall_score == pytest.approx(z_report.overall_score)

    @pytest.mark.asyncio
    async def test_score_bounded_0_1(self):
        """Overall score is always in [0, 1]."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            contracts = [_make_contract(5000, "call")]
            chain = _make_chain(contracts)

            report = await mgr.update(chain, None)
            assert 0.0 <= report.overall_score <= 1.0


# ===================================================================
# FlowAnalyzer
# ===================================================================


def _make_mock_uw_client(flow_summary: dict | None = None) -> MagicMock:
    """Create a mock UnusualWhalesClient with async methods."""
    client = MagicMock()
    if flow_summary is None:
        flow_summary = {
            "total_premium": 500000.0,
            "call_premium": 300000.0,
            "put_premium": 200000.0,
            "sweep_count": 15,
            "block_count": 5,
            "golden_sweep_count": 2,
            "net_sentiment": 0.3,
            "dark_pool_volume": 50000,
        }
    client.get_flow_summary = AsyncMock(return_value=flow_summary)
    return client


class TestFlowAnalyzer:
    """Tests for FlowAnalyzer class."""

    @pytest.mark.asyncio
    async def test_with_uw_client_returns_summary(self):
        """FlowAnalyzer with mocked UW client returns correct summary."""
        uw_client = _make_mock_uw_client()
        analyzer = FlowAnalyzer(uw_client=uw_client)

        result = await analyzer.get_enriched_flow("SPX")

        assert result["flow_source"] == "unusual_whales"
        assert result["total_premium"] == 500000.0
        assert result["call_premium"] == 300000.0
        assert result["put_premium"] == 200000.0
        assert result["sweep_count"] == 15
        assert result["block_count"] == 5
        assert result["net_sentiment"] == 0.3
        assert result["dark_pool_ratio"] > 0

    @pytest.mark.asyncio
    async def test_without_data_source_returns_empty(self):
        """FlowAnalyzer without any data source returns empty summary."""
        analyzer = FlowAnalyzer(uw_client=None, polygon_stream=None)

        result = await analyzer.get_enriched_flow("SPX")

        assert result["flow_source"] == "none"
        assert result["total_premium"] == 0.0
        assert result["sweep_count"] == 0
        assert result["anomaly_flags"] == []

    @pytest.mark.asyncio
    async def test_with_uw_and_polygon_source_label(self):
        """FlowAnalyzer with both sources labels correctly."""
        uw_client = _make_mock_uw_client()
        polygon_stream = MagicMock()  # just needs to exist

        analyzer = FlowAnalyzer(uw_client=uw_client, polygon_stream=polygon_stream)
        result = await analyzer.get_enriched_flow("SPX")

        assert result["flow_source"] == "unusual_whales+polygon"

    @pytest.mark.asyncio
    async def test_anomaly_flags_detect_sweep_surge(self):
        """Flow anomaly flags correctly detect sweep surges."""
        uw_client = _make_mock_uw_client({
            "total_premium": 500000.0,
            "call_premium": 300000.0,
            "put_premium": 200000.0,
            "sweep_count": 100,  # Very high
            "block_count": 5,
            "golden_sweep_count": 2,
            "net_sentiment": 0.3,
            "dark_pool_volume": 50000,
        })
        analyzer = FlowAnalyzer(uw_client=uw_client)

        baselines = {
            "sweep_counts": [10, 12, 8, 11, 9, 10, 13, 7, 10, 11,
                            10, 12, 8, 11, 9, 10, 13, 7, 10, 11],
            "premium_values": [400000, 450000, 380000, 420000, 460000,
                             400000, 450000, 380000, 420000, 460000,
                             400000, 450000, 380000, 420000, 460000,
                             400000, 450000, 380000, 420000, 460000],
            "dark_pool_ratios": [0.2, 0.22, 0.18, 0.21, 0.19,
                               0.2, 0.22, 0.18, 0.21, 0.19,
                               0.2, 0.22, 0.18, 0.21, 0.19,
                               0.2, 0.22, 0.18, 0.21, 0.19],
        }

        result = await analyzer.get_enriched_flow("SPX", historical_baselines=baselines)

        assert len(result["anomaly_flags"]) == 3  # sweep, premium, dark pool
        sweep_flag = next(f for f in result["anomaly_flags"] if f["type"] == "sweep_surge")
        assert sweep_flag["is_anomaly"] is True
        assert sweep_flag["z_score"] > 2.0

    @pytest.mark.asyncio
    async def test_uw_client_error_returns_empty(self):
        """FlowAnalyzer handles UW client error gracefully."""
        uw_client = MagicMock()
        uw_client.get_flow_summary = AsyncMock(side_effect=Exception("Connection error"))
        analyzer = FlowAnalyzer(uw_client=uw_client)

        result = await analyzer.get_enriched_flow("SPX")

        assert result["flow_source"] == "none"
        assert result["total_premium"] == 0.0

    @pytest.mark.asyncio
    async def test_no_baselines_no_flags(self):
        """Without historical baselines, no anomaly flags are produced."""
        uw_client = _make_mock_uw_client()
        analyzer = FlowAnalyzer(uw_client=uw_client)

        result = await analyzer.get_enriched_flow("SPX", historical_baselines=None)

        assert result["anomaly_flags"] == []


# ===================================================================
# AnomalyManager with flow data
# ===================================================================


class TestAnomalyManagerWithFlowData:
    """Tests for AnomalyManager.update() with flow_data parameter."""

    @pytest.mark.asyncio
    async def test_update_with_flow_data_adjusts_weighting(self):
        """AnomalyManager with flow data uses three-way weighting."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            contracts = [
                _make_contract(5000, "call", volume=99999, open_interest=100, iv=0.80),
            ]
            chain = _make_chain(contracts)
            historical_data = {
                "volume_history": {5000.0: [100, 102, 98, 101, 99]},
                "iv_history": {5000.0: [0.19, 0.20, 0.21, 0.19, 0.20]},
                "voi_history": [0.1, 0.12, 0.09, 0.11, 0.10],
            }

            flow_data = {
                "flow_source": "unusual_whales",
                "total_premium": 500000.0,
                "sweep_count": 15,
                "block_count": 5,
                "net_sentiment": 0.3,
                "anomaly_flags": [
                    {"type": "sweep_surge", "is_anomaly": True, "z_score": 3.5},
                    {"type": "premium_spike", "is_anomaly": False, "z_score": 1.2},
                    {"type": "dark_pool_divergence", "is_anomaly": False, "z_score": 0.5},
                ],
            }

            report = await mgr.update(chain, historical_data, flow_data=flow_data)

            assert isinstance(report, AnomalyReport)
            assert 0.0 <= report.overall_score <= 1.0
            assert len(report.flow_anomalies) == 3

    @pytest.mark.asyncio
    async def test_update_without_flow_data_maintains_original_behavior(self):
        """AnomalyManager without flow data maintains original z-score weighting."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            contracts = [
                _make_contract(5000, "call", volume=99999, open_interest=100, iv=0.80),
            ]
            chain = _make_chain(contracts)
            historical_data = {
                "volume_history": {5000.0: [100, 102, 98, 101, 99]},
                "iv_history": {5000.0: [0.19, 0.20, 0.21, 0.19, 0.20]},
                "voi_history": [0.1, 0.12, 0.09, 0.11, 0.10],
            }

            # Without flow_data — should use original weighting
            report_no_flow = await mgr.update(chain, historical_data, flow_data=None)

            # Without forest, overall_score = z_score_raw
            z_report = scan_chain_anomalies(chain, historical_data)
            assert report_no_flow.overall_score == pytest.approx(z_report.overall_score)
            assert report_no_flow.flow_anomalies == []

    @pytest.mark.asyncio
    async def test_flow_data_with_all_anomalies_increases_score(self):
        """Flow data with all flags anomalous contributes to higher score."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            contracts = [_make_contract(5000, "call")]
            chain = _make_chain(contracts)

            # Run without flow first
            report_no_flow = await mgr.update(chain, None, ticker="TEST1", flow_data=None)

            # Run with all-anomaly flow data
            flow_data = {
                "flow_source": "unusual_whales",
                "total_premium": 500000.0,
                "anomaly_flags": [
                    {"type": "sweep_surge", "is_anomaly": True},
                    {"type": "premium_spike", "is_anomaly": True},
                    {"type": "dark_pool_divergence", "is_anomaly": True},
                ],
            }
            report_with_flow = await mgr.update(chain, None, ticker="TEST2", flow_data=flow_data)

            # Flow with all anomalies should give higher score than no flow
            assert report_with_flow.overall_score >= report_no_flow.overall_score

    @pytest.mark.asyncio
    async def test_flow_anomalies_stored_in_report(self):
        """Flow anomaly flags are stored in the AnomalyReport."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            contracts = [_make_contract(5000, "call")]
            chain = _make_chain(contracts)

            flow_data = {
                "flow_source": "unusual_whales",
                "total_premium": 500000.0,
                "anomaly_flags": [
                    {"type": "sweep_surge", "is_anomaly": True, "z_score": 3.0},
                ],
            }

            report = await mgr.update(chain, None, flow_data=flow_data)

            assert len(report.flow_anomalies) == 1
            assert report.flow_anomalies[0]["type"] == "sweep_surge"
            assert report.flow_anomalies[0]["is_anomaly"] is True

    @pytest.mark.asyncio
    async def test_flow_data_none_source_treated_as_no_flow(self):
        """Flow data with 'none' source is treated as no flow data."""
        store = _make_mock_feature_store()
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = AnomalyManager(store, tmpdir)

            contracts = [_make_contract(5000, "call")]
            chain = _make_chain(contracts)

            flow_data = {
                "flow_source": "none",
                "total_premium": 0.0,
                "anomaly_flags": [],
            }

            report = await mgr.update(chain, None, flow_data=flow_data)

            # Should behave same as no flow data
            assert report.flow_anomalies == []


class TestAnomalyReportFlowField:
    """Tests for the flow_anomalies field on AnomalyReport."""

    def test_default_flow_anomalies_empty(self):
        """Default report has empty flow_anomalies list."""
        report = AnomalyReport()
        assert report.flow_anomalies == []

    def test_custom_flow_anomalies(self):
        """Can set custom flow_anomalies."""
        report = AnomalyReport(
            flow_anomalies=[{"type": "sweep_surge", "is_anomaly": True}],
        )
        assert len(report.flow_anomalies) == 1
        assert report.flow_anomalies[0]["type"] == "sweep_surge"
