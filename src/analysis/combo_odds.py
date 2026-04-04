"""Combo options odds engine for SPY/SPX Discord bot.

Provides jump-diffusion Monte Carlo simulation of multi-leg options positions.
Supports single options, vertical spreads, and calendar spreads.

Key entry point:
    await evaluate_combo(legs, spot, atm_iv, r) -> ComboOddsResult

Memory budget on s-2vcpu-8gb: 100K paths * ~8 bytes * 4 arrays ~ 3.2 MB peak.
Only one simulation runs at a time via _sim_semaphore.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

import numpy as np
from scipy.stats import norm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
MAX_PATHS: int = 100_000
_CALENDAR_DAYS_PER_YEAR: float = 365.0

# Log-moneyness linear skew coefficient: IV increases by _SKEW_SLOPE per unit
# of ln(K/S) below ATM. Calibrated to SPX skew at moderate DTE.
_SKEW_SLOPE: float = 0.10

# Merton jump-diffusion parameters tuned to SPX historical tail behaviour.
_JUMP_INTENSITY: float = 0.05    # expected jumps per calendar year
_JUMP_MEAN: float = -0.02        # mean log-jump size (slightly negative = left tail)
_JUMP_STD: float = 0.04          # log-jump volatility

# Concurrency gate: one simulation at a time to cap memory on the droplet.
_sim_semaphore: asyncio.Semaphore = asyncio.Semaphore(1)

# Spot-move factors for the deterministic scenario table.
_SCENARIO_MOVES: list[float] = [-0.15, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ComboLeg:
    """Specification for one leg of an options combo.

    Attributes:
        leg_name: Human-readable identifier (e.g. "short_put").
        option_type: "call" or "put".
        strike: Strike price in dollars.
        dte_days: Calendar days to expiration at trade entry.
        action: "buy" or "sell".
        quantity: Number of contracts (positive; action determines sign).
        entry_premium: Per-contract premium paid (buy) or received (sell).
            For calendar spreads on the "calendar_near" leg, this must hold
            the NET debit/credit for the entire spread.
        leg_role: Dispatch key for P&L computation.
            "single"         -- standalone long or short option
            "vertical_long"  -- long strike of a vertical spread
            "vertical_short" -- short strike of a vertical spread
            "calendar_near"  -- short near-month; entry_premium = net spread debit
            "calendar_far"   -- long far-month paired with calendar_near
    """

    leg_name: str
    option_type: str
    strike: float
    dte_days: int
    action: str
    quantity: int = 1
    entry_premium: float = 0.0
    leg_role: str = "single"


@dataclass
class LegResult:
    """Per-leg Monte Carlo statistics."""

    leg_name: str
    mean_pnl: float
    std_pnl: float
    prob_profit: float


@dataclass
class ComboOddsResult:
    """Output from evaluate_combo.

    All P&L values are per-unit (single contract, no multiplier).

    Attributes:
        prob_profit: Fraction of paths where total P&L > 0.
        expected_pnl: Mean total P&L across all paths.
        median_pnl: 50th-percentile total P&L.
        percentiles: {1, 5, 10, 25, 50, 75, 90, 95, 99} -> dollar P&L.
        leg_results: Per-leg simulation statistics.
        scenario_table: Deterministic P&L at seven spot-move levels.
            Each entry: {"move_pct": float, "spot": float, "pnl": float}.
        risk_flags: Risk warning strings; empty if no issues detected.
        n_paths: Actual number of paths used.
        seed_used: RNG seed (for audit / replay).
    """

    prob_profit: float
    expected_pnl: float
    median_pnl: float
    percentiles: dict[int, float]
    leg_results: list[LegResult] = field(default_factory=list)
    scenario_table: list[dict] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    n_paths: int = 0
    seed_used: int = 0


# ---------------------------------------------------------------------------
# IV skew helpers
# ---------------------------------------------------------------------------

def estimate_iv(
    strike: float,
    spot: float,
    atm_vol: float,
    dte_trading: int,
    fear_regime: bool = False,
    skew_slope: float = _SKEW_SLOPE,
) -> float:
    """Estimate IV for a strike using a log-moneyness skew model.

    IV = atm_vol * (1 + skew_slope * max(-ln(K/S), 0) * term_scale)

    Skew is applied only to the downside to match observed SPX negative skew.
    Term structure: skew flattens at longer tenors (scale = 1 / (1 + dte/180)).

    Args:
        strike: Target strike in dollars.
        spot: Current spot price.
        atm_vol: ATM implied volatility (decimal, e.g. 0.18).
        dte_trading: Calendar days to expiry (for term-structure scaling).
        fear_regime: If True, apply additional near-term premium.
        skew_slope: Log-moneyness skew magnitude. Default 0.10.

    Returns:
        Estimated IV as a decimal, clamped to [0.05, 2.0].
    """
    if spot <= 0 or strike <= 0:
        return atm_vol
    log_moneyness = np.log(strike / spot)
    dte_scale = 1.0 / (1.0 + dte_trading / 180.0)
    skew_adj = skew_slope * max(-log_moneyness, 0.0) * dte_scale
    iv = atm_vol * (1.0 + skew_adj)
    if fear_regime and dte_trading > 0:
        import math
        iv += 0.05 * math.exp(-0.12 * (dte_trading - 1))
    return float(np.clip(iv, 0.05, 2.0))


def estimate_future_iv(
    strike: float,
    future_spot: np.ndarray | float,
    entry_spot: float,
    entry_atm_vol: float,
) -> np.ndarray | float:
    """Estimate far-leg IV at the near-leg expiry (sticky-strike model).

    Under sticky-strike, each absolute strike retains its entry-time IV while
    ATM vol shifts proportionally with the underlying:
        new_atm_vol = entry_atm_vol * (entry_spot / future_spot)

    Fully vectorized: future_spot may be a scalar or a numpy array.

    Args:
        strike: Far-leg strike in dollars.
        future_spot: Spot at the near-leg expiry; scalar or array.
        entry_spot: Spot at trade entry.
        entry_atm_vol: ATM vol at entry (decimal).

    Returns:
        Estimated IV matching shape of future_spot, clamped to [0.05, 2.0].
    """
    if entry_spot <= 0:
        return entry_atm_vol
    future_spot_arr = np.asarray(future_spot, dtype=float)
    safe_spot = np.where(future_spot_arr > 0, future_spot_arr, entry_spot)
    new_atm = entry_atm_vol * (entry_spot / safe_spot)
    log_m = np.log(strike / safe_spot)
    skew_adj = _SKEW_SLOPE * np.maximum(-log_m, 0.0)
    iv = np.clip(new_atm * (1.0 + skew_adj), 0.05, 2.0)
    return float(iv) if np.ndim(future_spot) == 0 else iv


# ---------------------------------------------------------------------------
# Vectorized Black-Scholes pricer
# ---------------------------------------------------------------------------

def _bs_price(
    S: np.ndarray,
    K: float,
    T: float,
    sigma: np.ndarray | float,
    r: float,
    option_type: str,
) -> np.ndarray:
    """Vectorized Black-Scholes option price.

    Accepts S and sigma as arrays (same shape) for per-path repricing.
    For T <= 0 returns intrinsic value; sigma is clamped to [0.001, 10.0].
    """
    if T <= 0.0:
        if option_type == "call":
            return np.maximum(S - K, 0.0)
        return np.maximum(K - S, 0.0)
    sigma_arr = np.clip(np.asarray(sigma, dtype=float), 0.001, 10.0)
    sqrt_T = np.sqrt(T)
    d1 = (np.log(S / K) + (r + 0.5 * sigma_arr ** 2) * T) / (sigma_arr * sqrt_T)
    d2 = d1 - sigma_arr * sqrt_T
    if option_type == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


# ---------------------------------------------------------------------------
# Per-leg P&L (vectorized over paths)
# ---------------------------------------------------------------------------

def compute_leg_pnl(
    leg: ComboLeg,
    spot_at_expiry: np.ndarray,
    entry_spot: float,
    atm_iv: float,
    r: float,
    far_leg: ComboLeg | None = None,
) -> np.ndarray:
    """Compute per-path P&L for a leg at its own expiry horizon.

    Dispatches on leg.leg_role:
    - "single" / "vertical_long" / "vertical_short": intrinsic at expiry.
    - "calendar_near": near-leg intrinsic + vectorized far-leg BS reprice.
    - "calendar_far": zero array (accounted for in calendar_near).
    """
    n = len(spot_at_expiry)
    sign = 1.0 if leg.action == "buy" else -1.0

    if leg.leg_role in ("single", "vertical_long", "vertical_short"):
        value = _bs_price(spot_at_expiry, leg.strike, 0.0, atm_iv, r, leg.option_type)
        return sign * (value - leg.entry_premium) * leg.quantity

    if leg.leg_role == "calendar_near":
        if far_leg is None:
            logger.error("calendar_near '%s' missing far_leg", leg.leg_name)
            return np.zeros(n)

        # Near leg expires to intrinsic
        near_value = _bs_price(
            spot_at_expiry, leg.strike, 0.0, atm_iv, r, leg.option_type,
        )

        # Far leg: vectorized reprice at remaining DTE using sticky-strike IV
        remaining_T = max(far_leg.dte_days - leg.dte_days, 0) / _CALENDAR_DAYS_PER_YEAR
        far_iv = estimate_future_iv(far_leg.strike, spot_at_expiry, entry_spot, atm_iv)
        far_value = _bs_price(
            spot_at_expiry, far_leg.strike, remaining_T,
            far_iv, r, far_leg.option_type,
        )

        # Long calendar: long far, short near; entry_premium = net debit paid
        spread_value = far_value - near_value
        return (spread_value - leg.entry_premium) * leg.quantity

    if leg.leg_role == "calendar_far":
        return np.zeros(n)

    logger.warning("Unknown leg_role '%s' for leg '%s'", leg.leg_role, leg.leg_name)
    return np.zeros(n)


# ---------------------------------------------------------------------------
# Jump-diffusion simulation
# ---------------------------------------------------------------------------

def simulate_jump_diffusion(
    S0: float,
    sigma: float,
    horizons_days: list[int],
    n_paths: int = MAX_PATHS,
    r: float = 0.0,
    seed: int | None = None,
    jump_intensity: float = _JUMP_INTENSITY,
    jump_mean: float = _JUMP_MEAN,
    jump_std: float = _JUMP_STD,
) -> dict[int, np.ndarray]:
    """Simulate terminal spot prices via Merton jump-diffusion GBM.

    Returns dict mapping each horizon (calendar days) to shape-(n_paths,) array.
    """
    n_paths = min(n_paths, MAX_PATHS)
    rng = np.random.default_rng(seed)

    horizons_sorted = sorted(horizons_days)
    T_max = horizons_sorted[-1] / _CALENDAR_DAYS_PER_YEAR

    # Jump-compensation drift
    k_bar = np.exp(jump_mean + 0.5 * jump_std ** 2) - 1.0
    drift = (r - 0.5 * sigma ** 2 - jump_intensity * k_bar) * T_max

    # Diffusion
    z = rng.standard_normal(size=n_paths)
    log_diffusion = drift + sigma * np.sqrt(T_max) * z

    # Jumps
    n_jumps = rng.poisson(lam=jump_intensity * T_max, size=n_paths)
    max_j = int(n_jumps.max()) if n_jumps.size > 0 and n_jumps.max() > 0 else 0
    log_jumps = np.zeros(n_paths)
    if max_j > 0:
        sizes = rng.normal(loc=jump_mean, scale=jump_std, size=(n_paths, max_j))
        mask = np.arange(max_j)[np.newaxis, :] < n_jumps[:, np.newaxis]
        log_jumps = (sizes * mask).sum(axis=1)

    log_return_max = log_diffusion + log_jumps

    result: dict[int, np.ndarray] = {}
    for h in horizons_sorted:
        scale = (h / _CALENDAR_DAYS_PER_YEAR) / T_max
        result[h] = S0 * np.exp(log_return_max * scale)

    logger.debug(
        "simulate_jump_diffusion: S0=%.2f sigma=%.3f horizons=%s n_paths=%d",
        S0, sigma, horizons_days, n_paths,
    )
    return result


# ---------------------------------------------------------------------------
# Risk flag detection
# ---------------------------------------------------------------------------

def _detect_risk_flags(
    legs: list[ComboLeg],
    pnl_array: np.ndarray,
    entry_cost: float | None,
) -> list[str]:
    """Scan legs and simulation output for known risk patterns."""
    flags: list[str] = []
    buy_legs = [lg for lg in legs if lg.action == "buy"]

    for lg in legs:
        if lg.action != "sell" or lg.leg_role != "single":
            continue
        protected = any(
            bl.option_type == lg.option_type
            and (
                (lg.option_type == "call" and bl.strike >= lg.strike)
                or (lg.option_type == "put" and bl.strike <= lg.strike)
            )
            for bl in buy_legs
        )
        if not protected:
            flags.append(
                f"NAKED_SHORT: {lg.leg_name} ({lg.option_type} @ {lg.strike:.0f})"
                " -- undefined downside risk"
            )

    if entry_cost is not None and abs(entry_cost) > 0:
        tail_loss = abs(float(np.percentile(pnl_array, 1)))
        if tail_loss > 3.0 * abs(entry_cost):
            flags.append(
                f"TAIL_RISK: 1st-pct loss ${tail_loss:.0f} is "
                f"{tail_loss / abs(entry_cost):.1f}x entry cost ${abs(entry_cost):.0f}"
            )

    return flags


# ---------------------------------------------------------------------------
# Top-level async entry point
# ---------------------------------------------------------------------------

async def evaluate_combo(
    legs: list[ComboLeg],
    spot: float,
    atm_iv: float,
    r: float,
    n_paths: int = MAX_PATHS,
    entry_cost: float | None = None,
    seed: int | None = None,
) -> ComboOddsResult:
    """Evaluate a multi-leg options combo via jump-diffusion Monte Carlo.

    Acquires _sim_semaphore before simulating to ensure at most one heavy
    simulation runs at a time on the shared droplet (memory safety).
    """
    n_paths = min(n_paths, MAX_PATHS)
    if seed is None:
        seed = int(time.time() * 1000) % (2 ** 31 - 1)

    async with _sim_semaphore:
        logger.info(
            "evaluate_combo: %d legs spot=%.2f atm_iv=%.3f n_paths=%d seed=%d",
            len(legs), spot, atm_iv, n_paths, seed,
        )

        horizons = sorted({lg.dte_days for lg in legs if lg.dte_days > 0}) or [1]
        spot_by_horizon = simulate_jump_diffusion(
            S0=spot, sigma=atm_iv, horizons_days=horizons,
            n_paths=n_paths, r=r, seed=seed,
        )

        # Map calendar_near legs to their paired calendar_far counterpart
        far_leg_map: dict[str, ComboLeg] = {}
        near_by_type = {
            lg.option_type: lg for lg in legs if lg.leg_role == "calendar_near"
        }
        for lg in legs:
            if lg.leg_role == "calendar_far" and lg.option_type in near_by_type:
                far_leg_map[near_by_type[lg.option_type].leg_name] = lg

        total_pnl = np.zeros(n_paths)
        leg_results: list[LegResult] = []

        for leg in legs:
            if leg.leg_role == "calendar_far":
                continue  # accounted for inside calendar_near dispatch
            spot_arr = spot_by_horizon.get(leg.dte_days, spot_by_horizon[horizons[-1]])
            leg_pnl = compute_leg_pnl(
                leg, spot_arr, spot, atm_iv, r,
                far_leg=far_leg_map.get(leg.leg_name),
            )
            total_pnl += leg_pnl
            leg_results.append(LegResult(
                leg_name=leg.leg_name,
                mean_pnl=float(np.mean(leg_pnl)),
                std_pnl=float(np.std(leg_pnl)),
                prob_profit=float(np.mean(leg_pnl > 0)),
            ))

        pct_keys = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        percentiles = {k: float(np.percentile(total_pnl, k)) for k in pct_keys}

        # Deterministic scenario table
        scenario_table: list[dict] = []
        for move in _SCENARIO_MOVES:
            s_arr = np.array([spot * (1.0 + move)])
            s_pnl = sum(
                compute_leg_pnl(
                    lg, s_arr, spot, atm_iv, r,
                    far_leg=far_leg_map.get(lg.leg_name),
                )[0]
                for lg in legs if lg.leg_role != "calendar_far"
            )
            scenario_table.append({
                "move_pct": round(move * 100, 1),
                "spot": round(spot * (1.0 + move), 2),
                "pnl": round(float(s_pnl), 2),
            })

        return ComboOddsResult(
            prob_profit=float(np.mean(total_pnl > 0)),
            expected_pnl=float(np.mean(total_pnl)),
            median_pnl=percentiles[50],
            percentiles=percentiles,
            leg_results=leg_results,
            scenario_table=scenario_table,
            risk_flags=_detect_risk_flags(legs, total_pnl, entry_cost),
            n_paths=n_paths,
            seed_used=seed,
        )
