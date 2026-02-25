"""Position sizing: Kelly criterion with regime and volatility adjustments.

Computes optimal position sizes for paper trading by combining:
1. Kelly fraction from backtest win rate / avg win / avg loss
2. Fractional Kelly scaling (1/4 for new, 1/3 for proven)
3. Regime adjustment (from HMM state)
4. Volatility adjustment (inverse scaling with predicted vol)
5. Anomaly adjustment (reduce/halt on high anomaly scores)
6. Hard cap at max_position_premium_pct of NAV

All computations are for paper trading -- no real money is at risk.
"""

from __future__ import annotations

import logging
from typing import Any

from src.risk.config import KELLY_FRACTIONS, REGIME_MULTIPLIERS, RiskConfig
from src.risk.models import PositionSizeResult

logger = logging.getLogger(__name__)


def kelly_fraction(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
) -> float:
    """Compute raw Kelly fraction from backtest statistics.

    f* = (p * b - q) / b
    where p = win_rate, q = 1-p, b = avg_win / |avg_loss|

    Args:
        win_rate: Fraction of winning trades (0.0 to 1.0).
        avg_win: Average winning trade P&L (positive).
        avg_loss: Average losing trade P&L (negative).

    Returns:
        Kelly fraction in [0, 1]. Negative values clamped to 0.
    """
    if avg_loss >= 0 or avg_win <= 0 or win_rate <= 0:
        return 0.0

    b = avg_win / abs(avg_loss)
    p = win_rate
    q = 1 - p

    kelly = (p * b - q) / b
    return max(kelly, 0.0)


def vol_adjusted_multiplier(
    predicted_vol_1d: float,
    historical_avg_vol: float = 0.15,
) -> float:
    """Scale position size inversely with predicted volatility.

    When vol is 2x average, multiplier = 0.5 (halved).
    When vol is at or below average, multiplier = 1.0 (no increase).

    Args:
        predicted_vol_1d: 1-day vol forecast (annualized decimal).
        historical_avg_vol: Long-term average (default 15%).

    Returns:
        Multiplier in (0, 1.0]. Never exceeds 1.0.
    """
    if predicted_vol_1d <= 0 or historical_avg_vol <= 0:
        return 1.0

    vol_ratio = predicted_vol_1d / historical_avg_vol
    if vol_ratio <= 1.0:
        return 1.0
    return min(1.0, 1.0 / vol_ratio)


def anomaly_multiplier(anomaly_score: float) -> float:
    """Compute anomaly-based position size multiplier.

    | Score Range | Multiplier | Action |
    |------------|------------|--------|
    | < 0.3      | 1.0        | Normal |
    | 0.3 - 0.5  | 1.0        | Log warning, continue |
    | 0.5 - 0.7  | 0.5        | Reduce size 50% |
    | 0.7 - 0.8  | 0.0        | No new positions |
    | > 0.8      | 0.0        | Circuit breaker |

    Args:
        anomaly_score: Composite anomaly score (0.0 to 1.0).

    Returns:
        Multiplier in [0.0, 1.0].
    """
    if anomaly_score > 0.7:
        return 0.0
    elif anomaly_score > 0.5:
        return 0.5
    return 1.0


def compute_position_size(
    nav: float,
    strategy_metrics: Any,
    regime_state: int,
    predicted_vol_1d: float,
    anomaly_score_val: float,
    config: RiskConfig,
    kelly_level: str = "paper_new",
) -> PositionSizeResult:
    """Compute position size incorporating all risk factors.

    Pipeline: Kelly -> fractional scaling -> hard cap -> regime ->
              vol -> anomaly -> final size.

    Args:
        nav: Current portfolio NAV.
        strategy_metrics: StrategyMetrics with win_rate, avg_win, avg_loss.
        regime_state: Current HMM regime (0=risk-on, 1=risk-off, 2=crisis).
        predicted_vol_1d: 1-day vol forecast (annualized decimal).
        anomaly_score_val: Current composite anomaly score (0-1).
        config: RiskConfig with limit parameters.
        kelly_level: "paper_new" or "paper_proven".

    Returns:
        PositionSizeResult with final max_premium and all multipliers.
    """
    # Step 1: Raw Kelly
    win_rate = getattr(strategy_metrics, "win_rate", 0.0)
    avg_win = getattr(strategy_metrics, "avg_win", 0.0)
    avg_loss = getattr(strategy_metrics, "avg_loss", 0.0)
    kelly_raw = kelly_fraction(win_rate, avg_win, avg_loss)

    # Step 2: Fractional Kelly
    frac = KELLY_FRACTIONS.get(kelly_level, 0.25)
    kelly_allocation = nav * kelly_raw * frac

    # Step 3: Hard cap
    hard_cap = nav * config.max_position_premium_pct

    # Step 4: Regime
    regime_mults = REGIME_MULTIPLIERS.get(regime_state, REGIME_MULTIPLIERS[0])
    regime_mult = regime_mults.get("position_size", 1.0)

    # Step 5: Vol
    vol_mult = vol_adjusted_multiplier(predicted_vol_1d)

    # Step 6: Anomaly
    anom_mult = anomaly_multiplier(anomaly_score_val)

    # Final
    base = min(kelly_allocation, hard_cap) if kelly_allocation > 0 else hard_cap
    max_premium = base * regime_mult * vol_mult * anom_mult
    max_premium = max(max_premium, 0.0)

    # Estimate max contracts (rough: assume $3 avg premium per contract for SPX spreads)
    avg_premium_per_contract = 3.0 * 100  # $300 per contract
    max_contracts = int(max_premium / avg_premium_per_contract) if avg_premium_per_contract > 0 else 0

    # Build rationale
    parts = []
    parts.append(f"Kelly raw={kelly_raw:.3f}, frac={frac}")
    parts.append(f"Kelly alloc=${kelly_allocation:,.0f}, cap=${hard_cap:,.0f}")
    parts.append(f"Regime={regime_state} ({regime_mult:.2f}x)")
    parts.append(f"Vol={predicted_vol_1d:.3f} ({vol_mult:.2f}x)")
    parts.append(f"Anomaly={anomaly_score_val:.2f} ({anom_mult:.2f}x)")
    parts.append(f"Final=${max_premium:,.0f}")

    return PositionSizeResult(
        max_premium=round(max_premium, 2),
        max_contracts=max_contracts,
        kelly_raw=round(kelly_raw, 4),
        kelly_fraction=frac,
        regime_multiplier=regime_mult,
        vol_multiplier=round(vol_mult, 4),
        anomaly_multiplier=anom_mult,
        rationale="; ".join(parts),
    )
