"""Statistical anomaly detection for unusual options activity.

Provides z-score based detectors for volume spikes, IV anomalies,
volume/OI ratio anomalies, and strike clustering.  All pure-stat
functions are stateless and synchronous (no I/O).

A convenience ``scan_chain_anomalies`` function runs all detectors on
an :class:`OptionsChain` in one call.

Phase 3-05 of the ML intelligence layer.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.data import OptionsChain

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
