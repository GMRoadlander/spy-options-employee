"""Tests for statistical anomaly detection (src/ml/anomaly.py).

Covers z-score detectors for volume, IV, V/OI, and strike clustering,
plus the AnomalyReport dataclass and scan_chain_anomalies convenience
function.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import pytest

from src.data import OptionContract, OptionsChain
from src.ml.anomaly import (
    AnomalyReport,
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
