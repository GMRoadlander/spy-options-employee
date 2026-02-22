"""Pure computation functions for ML features.

All functions are stateless, accept numpy arrays or Python lists, and
return a single float.  No I/O, no async, no side effects -- just math.

These functions compute the Tier 1 and Tier 2 features used by the ML
intelligence layer:

- **IV rank** -- percentile rank of current ATM IV vs trailing history
- **IV percentile** -- pct of days IV was below current level
- **25-delta skew** -- risk reversal: IV(25D put) - IV(25D call)
- **Term structure slope** -- ATM IV slope normalised by DTE difference
- **RV/IV spread** -- realised vol minus implied vol (variance risk premium)
- **Hurst exponent** -- R/S analysis for mean-reversion vs trending behaviour
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.data import OptionsChain


# ---------------------------------------------------------------------------
# IV Rank
# ---------------------------------------------------------------------------


def compute_iv_rank(current_iv: float, iv_history: list[float] | np.ndarray) -> float:
    """Percentile rank of *current_iv* within *iv_history* (0--100).

    IV rank uses the high/low range method::

        rank = (current - min) / (max - min) * 100

    Args:
        current_iv: Current ATM implied volatility.
        iv_history: Trailing IV values (e.g. 252 trading days).

    Returns:
        Rank in [0, 100].  Returns 50.0 for empty or single-value history.
    """
    arr = np.asarray(iv_history, dtype=float)
    arr = arr[np.isfinite(arr)]

    if len(arr) < 2:
        return 50.0

    lo, hi = float(np.min(arr)), float(np.max(arr))
    if hi == lo:
        return 50.0

    rank = (current_iv - lo) / (hi - lo) * 100.0
    return float(np.clip(rank, 0.0, 100.0))


# ---------------------------------------------------------------------------
# IV Percentile
# ---------------------------------------------------------------------------


def compute_iv_percentile(current_iv: float, iv_history: list[float] | np.ndarray) -> float:
    """Percentage of days in *iv_history* where IV was below *current_iv*.

    Distinct from IV rank (which uses the high/low range).

    Args:
        current_iv: Current ATM implied volatility.
        iv_history: Trailing IV values.

    Returns:
        Percentile in [0, 100].  Returns 50.0 for empty or single-value
        history.
    """
    arr = np.asarray(iv_history, dtype=float)
    arr = arr[np.isfinite(arr)]

    if len(arr) < 2:
        return 50.0

    below = float(np.sum(arr < current_iv))
    return below / len(arr) * 100.0


# ---------------------------------------------------------------------------
# 25-Delta Skew
# ---------------------------------------------------------------------------


def compute_skew_25d(chain: OptionsChain) -> float:
    """25-delta risk reversal for the nearest expiry.

    Computes IV(25-delta put) - IV(25-delta call) using linear
    interpolation between surrounding deltas.  A positive value means
    puts are more expensive than calls (normal for equities).

    Args:
        chain: An :class:`OptionsChain` with contracts that have
            populated ``delta`` and ``iv`` fields.

    Returns:
        Skew value (positive = puts more expensive).  Returns 0.0 if
        there is insufficient data.
    """
    expiry = chain.nearest_expiry()
    if expiry is None:
        return 0.0

    contracts = chain.for_expiry(expiry)
    if not contracts:
        return 0.0

    # Separate puts and calls, filter out zero-IV contracts
    puts = [(c.delta, c.iv) for c in contracts if c.is_put and c.iv > 0]
    calls = [(c.delta, c.iv) for c in contracts if c.is_call and c.iv > 0]

    if len(puts) < 2 or len(calls) < 2:
        return 0.0

    put_iv_25 = _interpolate_iv_at_delta(puts, -0.25)
    call_iv_25 = _interpolate_iv_at_delta(calls, 0.25)

    if put_iv_25 is None or call_iv_25 is None:
        return 0.0

    return put_iv_25 - call_iv_25


def _interpolate_iv_at_delta(
    delta_iv_pairs: list[tuple[float, float]],
    target_delta: float,
) -> float | None:
    """Linearly interpolate IV at *target_delta* from a list of (delta, iv).

    Sorts by delta and finds the two bracketing points.  Returns None
    if the target is outside the available range.
    """
    sorted_pairs = sorted(delta_iv_pairs, key=lambda x: x[0])
    deltas = [p[0] for p in sorted_pairs]
    ivs = [p[1] for p in sorted_pairs]

    # Find bracketing indices
    for i in range(len(deltas) - 1):
        d_lo, d_hi = deltas[i], deltas[i + 1]
        if d_lo == d_hi:
            continue
        if (d_lo <= target_delta <= d_hi) or (d_hi <= target_delta <= d_lo):
            # Linear interpolation
            t = (target_delta - d_lo) / (d_hi - d_lo)
            return ivs[i] + t * (ivs[i + 1] - ivs[i])

    return None


# ---------------------------------------------------------------------------
# Term Structure Slope
# ---------------------------------------------------------------------------


def compute_term_structure_slope(chain: OptionsChain) -> float:
    """ATM IV slope normalised by DTE difference.

    Computes::

        (IV_2nd_expiry - IV_1st_expiry) / (DTE_2nd - DTE_1st)

    using the nearest-to-ATM strike IV for each expiration.  Positive
    values indicate contango (normal term structure).

    Args:
        chain: An :class:`OptionsChain` with at least 2 expirations.

    Returns:
        Normalised slope.  Returns 0.0 if fewer than 2 expirations.
    """
    exps = chain.expirations
    if len(exps) < 2:
        return 0.0

    exp1, exp2 = exps[0], exps[1]
    spot = chain.spot_price

    iv1 = _nearest_atm_iv(chain.for_expiry(exp1), spot)
    iv2 = _nearest_atm_iv(chain.for_expiry(exp2), spot)

    if iv1 is None or iv2 is None:
        return 0.0

    from datetime import date as _date

    today = _date.today()
    dte1 = (exp1 - today).days
    dte2 = (exp2 - today).days
    dte_diff = dte2 - dte1

    if dte_diff == 0:
        return 0.0

    return (iv2 - iv1) / dte_diff


def _nearest_atm_iv(contracts: list, spot: float) -> float | None:
    """Return the IV of the call contract nearest to *spot*.

    Prefers call contracts; falls back to puts if no calls available.
    """
    calls = [c for c in contracts if c.is_call and c.iv > 0]
    if not calls:
        # Fallback to puts
        puts = [c for c in contracts if c.is_put and c.iv > 0]
        if not puts:
            return None
        calls = puts

    nearest = min(calls, key=lambda c: abs(c.strike - spot))
    return nearest.iv


# ---------------------------------------------------------------------------
# Realised Vol / Implied Vol Spread
# ---------------------------------------------------------------------------


def compute_rv_iv_spread(
    returns: list[float] | np.ndarray,
    current_atm_iv: float,
    window: int = 20,
) -> float:
    """Realised volatility minus implied volatility.

    RV is the annualised standard deviation of the trailing *window*
    daily returns (multiplied by sqrt(252)).  A negative spread means
    IV is higher than RV (variance risk premium = edge for sellers).

    Args:
        returns: Daily log or simple returns.
        current_atm_iv: Current ATM implied volatility (decimal).
        window: Number of trailing returns to use.

    Returns:
        RV - IV (decimal, not percentage).  Returns 0.0 if insufficient
        data (fewer than *window* returns).
    """
    arr = np.asarray(returns, dtype=float)
    arr = arr[np.isfinite(arr)]

    if len(arr) < window:
        return 0.0

    trailing = arr[-window:]
    rv = float(np.std(trailing, ddof=1) * math.sqrt(252))
    return rv - current_atm_iv


# ---------------------------------------------------------------------------
# Hurst Exponent (R/S Analysis)
# ---------------------------------------------------------------------------


def compute_hurst_exponent(
    prices: list[float] | np.ndarray,
    max_lag: int = 20,
) -> float:
    """Hurst exponent via rescaled range (R/S) analysis.

    For each lag tau from 2 to *max_lag*, computes the mean rescaled
    range across non-overlapping sub-series.  Fits log(R/S) vs log(tau)
    via OLS; the slope is the Hurst exponent.

    - H < 0.5 : mean-reverting
    - H ~ 0.5 : random walk
    - H > 0.5 : trending / persistent

    Args:
        prices: Price series (levels, not returns).
        max_lag: Maximum lag for R/S calculation.

    Returns:
        Hurst exponent.  Returns 0.5 if insufficient data (fewer than
        *max_lag* + 1 prices).
    """
    arr = np.asarray(prices, dtype=float)
    arr = arr[np.isfinite(arr)]

    if len(arr) < max_lag + 1:
        return 0.5

    # Compute log returns
    log_returns = np.diff(np.log(arr))

    lags = list(range(2, max_lag + 1))
    rs_values: list[float] = []

    for lag in lags:
        rs_list: list[float] = []
        n = len(log_returns)
        # Split into non-overlapping sub-series of length `lag`
        num_subseries = n // lag
        if num_subseries == 0:
            continue

        for i in range(num_subseries):
            subseries = log_returns[i * lag : (i + 1) * lag]
            mean_sub = np.mean(subseries)
            cumulative_deviate = np.cumsum(subseries - mean_sub)
            r = float(np.max(cumulative_deviate) - np.min(cumulative_deviate))
            s = float(np.std(subseries, ddof=1))

            if s > 0:
                rs_list.append(r / s)

        if rs_list:
            rs_values.append(float(np.mean(rs_list)))
        else:
            # Cannot compute R/S for this lag; skip
            lags_copy = lags  # noqa: F841
            continue

    # Need at least 2 valid points for OLS
    # Filter lags to match rs_values length
    valid_lags = []
    valid_rs = []
    lag_idx = 0
    for lag in range(2, max_lag + 1):
        n = len(log_returns)
        num_subseries = n // lag
        if num_subseries == 0:
            continue
        if lag_idx < len(rs_values):
            valid_lags.append(lag)
            valid_rs.append(rs_values[lag_idx])
            lag_idx += 1

    if len(valid_lags) < 2:
        return 0.5

    # OLS fit: log(R/S) = H * log(lag) + c
    log_lags = np.log(np.array(valid_lags, dtype=float))
    log_rs = np.log(np.array(valid_rs, dtype=float))

    # Simple OLS for slope
    n = len(log_lags)
    sum_x = np.sum(log_lags)
    sum_y = np.sum(log_rs)
    sum_xy = np.sum(log_lags * log_rs)
    sum_xx = np.sum(log_lags * log_lags)

    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return 0.5

    hurst = float((n * sum_xy - sum_x * sum_y) / denom)

    # Clamp to [0, 1] for sanity
    return float(np.clip(hurst, 0.0, 1.0))
