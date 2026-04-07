"""Gamma Exposure (GEX) engine for SPY/SPX options analysis.

Calculates net gamma exposure across all strikes to identify key support/resistance
levels created by dealer hedging activity. When dealers are short gamma (negative
net GEX), their hedging amplifies moves. When long gamma (positive net GEX), their
hedging dampens moves.

GEX formula per contract:
    GEX = gamma * OI * 100 * S^2 * 0.01

Convention:
    - Calls contribute POSITIVE GEX (dealers short calls -> long gamma when hedging)
    - Puts contribute NEGATIVE GEX (dealers short puts -> short gamma when hedging)
"""

import logging
from dataclasses import dataclass, field
from datetime import date

import numpy as np

from src.analysis.greeks import black_scholes_gamma
from src.config import config
from src.data import OptionContract, OptionsChain

logger = logging.getLogger(__name__)


@dataclass
class GEXResult:
    """Results from gamma exposure analysis."""

    net_gex: float  # Total net GEX across all strikes
    gamma_flip: float | None  # Price level where net GEX crosses zero
    gamma_ceiling: float | None  # Strike with highest call GEX (None if no data)
    gamma_floor: float | None  # Strike with highest put GEX (None if no data)
    squeeze_probability: float  # 0-1 score
    strikes: list[float] = field(default_factory=list)  # Strike prices
    call_gex: list[float] = field(default_factory=list)  # GEX per strike for calls
    put_gex: list[float] = field(default_factory=list)  # GEX per strike for puts
    net_gex_by_strike: list[float] = field(
        default_factory=list
    )  # Net GEX per strike
    gex_by_expiry: dict[str, float] | None = None  # Per-expiry net GEX breakdown


def _compute_contract_gex(
    contract: OptionContract,
    spot: float,
    risk_free_rate: float,
) -> float:
    """Compute GEX contribution for a single contract.

    Args:
        contract: The option contract.
        spot: Current spot price of the underlying.
        risk_free_rate: Risk-free rate as a decimal.

    Returns:
        Signed GEX value (positive for calls, negative for puts).
    """
    if contract.open_interest <= 0:
        return 0.0

    # Time to expiry in years
    days_to_expiry = (contract.expiry - date.today()).days
    T = max(days_to_expiry, 0) / 365.0

    if T <= 0:
        return 0.0

    # Calculate gamma from the contract's IV using Black-Scholes
    gamma = black_scholes_gamma(
        S=spot,
        K=contract.strike,
        T=T,
        sigma=contract.iv,
        r=risk_free_rate,
    )

    if gamma <= 0:
        return 0.0

    # GEX = gamma * OI * 100 * S^2 * 0.01
    raw_gex = gamma * contract.open_interest * 100.0 * spot**2 * 0.01

    # Calls: positive GEX, Puts: negative GEX
    if contract.is_call:
        return raw_gex
    else:
        return -raw_gex


def _find_gamma_flip(
    strikes: list[float], net_gex_by_strike: list[float]
) -> float | None:
    """Find the price level where net GEX crosses zero by linear interpolation.

    Scans from low strikes to high strikes and returns the first zero crossing.
    If net GEX is uniformly positive or negative, returns None.

    Args:
        strikes: Sorted list of strike prices.
        net_gex_by_strike: Net GEX at each corresponding strike.

    Returns:
        Interpolated price where GEX flips sign, or None if no crossing found.
    """
    if len(strikes) < 2:
        return None

    for i in range(len(strikes) - 1):
        gex_a = net_gex_by_strike[i]
        gex_b = net_gex_by_strike[i + 1]

        # Check for sign change
        if gex_a * gex_b < 0:
            # Linear interpolation: find where the line crosses zero
            strike_a = strikes[i]
            strike_b = strikes[i + 1]
            # 0 = gex_a + (gex_b - gex_a) * (x - strike_a) / (strike_b - strike_a)
            # x = strike_a - gex_a * (strike_b - strike_a) / (gex_b - gex_a)
            flip = strike_a - gex_a * (strike_b - strike_a) / (gex_b - gex_a)
            return float(flip)

    return None


def _compute_squeeze_probability(
    net_gex: float,
    volume_pcr: float,
    net_gex_by_strike: list[float],
) -> float:
    """Compute a 0-1 squeeze probability score.

    A squeeze is more likely when:
    - Net GEX is very negative (dealers short gamma -> amplify moves)
    - Put/call volume ratio indicates extreme fear (high PCR)

    The score combines:
    1. Normalized magnitude of negative net GEX (0 if positive)
    2. Put/call ratio extremity

    Args:
        net_gex: Total net GEX across all strikes.
        volume_pcr: Put/call volume ratio (higher = more bearish).
        net_gex_by_strike: Net GEX at each strike for scale reference.

    Returns:
        Float between 0.0 and 1.0.
    """
    if not net_gex_by_strike:
        return 0.0

    # Component 1: Negative GEX magnitude score (0-1)
    # Use the range of net GEX values as the normalization reference
    gex_values = np.array(net_gex_by_strike)
    gex_range = float(np.max(np.abs(gex_values))) if len(gex_values) > 0 else 1.0
    if gex_range == 0:
        gex_range = 1.0

    if net_gex < 0:
        # Normalize: how negative is net_gex relative to the scale of all GEX?
        # Use total absolute GEX as denominator for context
        total_abs_gex = float(np.sum(np.abs(gex_values)))
        if total_abs_gex > 0:
            neg_score = min(abs(net_gex) / total_abs_gex, 1.0)
        else:
            neg_score = 0.0
    else:
        neg_score = 0.0

    # Component 2: PCR extremity score (0-1)
    # PCR > 1.15 is "extreme_fear", > 1.5 is panic
    if volume_pcr > 1.5:
        pcr_score = 1.0
    elif volume_pcr > 1.0:
        # Linear scale from 1.0 to 1.5 -> 0.0 to 1.0
        pcr_score = (volume_pcr - 1.0) / 0.5
    else:
        pcr_score = 0.0

    # Combine: weighted average (GEX is the primary signal)
    squeeze = 0.6 * neg_score + 0.4 * pcr_score
    return float(np.clip(squeeze, 0.0, 1.0))


def calculate_gex(
    chain: OptionsChain,
    expiry: date | None = None,
    volume_pcr: float = 0.7,
) -> GEXResult:
    """Calculate Gamma Exposure profile for an options chain.

    Filters contracts to within `config.gex_lookback_strikes` of the spot price,
    then computes per-strike and aggregate GEX metrics.

    Args:
        chain: The full options chain with spot price and contracts.
        expiry: If specified, only include contracts for this expiration.
                If None, uses all expirations (total GEX).
        volume_pcr: Put/call volume ratio for squeeze calculation.
                    Pass from PCR analysis; defaults to neutral 0.7.

    Returns:
        GEXResult with all computed fields.
    """
    spot = chain.spot_price
    r = config.risk_free_rate
    lookback = config.gex_lookback_strikes

    # Define strike range filter
    strike_low = spot - lookback
    strike_high = spot + lookback

    # Filter contracts
    multi_expiry = expiry is None
    contracts = chain.contracts
    if expiry is not None:
        contracts = [c for c in contracts if c.expiry == expiry]

    contracts = [c for c in contracts if strike_low <= c.strike <= strike_high]

    if not contracts:
        logger.warning(
            "No contracts found within %d strikes of spot %.2f",
            lookback, spot,
        )
        return GEXResult(
            net_gex=0.0,
            gamma_flip=None,
            gamma_ceiling=None,
            gamma_floor=None,
            squeeze_probability=0.0,
        )

    # Collect unique sorted strikes
    unique_strikes = sorted(set(c.strike for c in contracts))

    # Accumulate GEX per strike for calls and puts separately
    call_gex_map: dict[float, float] = {k: 0.0 for k in unique_strikes}
    put_gex_map: dict[float, float] = {k: 0.0 for k in unique_strikes}

    # Track per-expiry net GEX when aggregating across all expirations
    expiry_gex_map: dict[str, float] = {} if multi_expiry else {}

    for contract in contracts:
        gex_val = _compute_contract_gex(contract, spot, r)
        if contract.is_call:
            call_gex_map[contract.strike] += gex_val
        else:
            put_gex_map[contract.strike] += gex_val

        # Accumulate per-expiry breakdown
        if multi_expiry:
            exp_key = contract.expiry.isoformat()
            expiry_gex_map[exp_key] = expiry_gex_map.get(exp_key, 0.0) + gex_val

    # Build output lists
    strikes_list: list[float] = []
    call_gex_list: list[float] = []
    put_gex_list: list[float] = []
    net_gex_list: list[float] = []

    for k in unique_strikes:
        c_gex = call_gex_map[k]
        p_gex = put_gex_map[k]
        strikes_list.append(k)
        call_gex_list.append(c_gex)
        put_gex_list.append(p_gex)
        net_gex_list.append(c_gex + p_gex)

    # Aggregate metrics
    net_gex = sum(net_gex_list)

    # Gamma ceiling: strike with highest CALL GEX
    if call_gex_list and max(call_gex_list) > 0:
        max_call_idx = int(np.argmax(call_gex_list))
        gamma_ceiling = strikes_list[max_call_idx]
    else:
        gamma_ceiling = None

    # Gamma floor: strike with highest absolute PUT GEX
    if put_gex_list and max(abs(p) for p in put_gex_list) > 0:
        max_put_idx = int(np.argmax([abs(p) for p in put_gex_list]))
        gamma_floor = strikes_list[max_put_idx]
    else:
        gamma_floor = None

    # Gamma flip: where net GEX crosses zero
    gamma_flip = _find_gamma_flip(strikes_list, net_gex_list)

    # Squeeze probability
    squeeze_prob = _compute_squeeze_probability(net_gex, volume_pcr, net_gex_list)

    logger.info(
        "GEX computed: net=%.2e, flip=%s, ceiling=%s, floor=%s, "
        "squeeze=%.2f, %d strikes analyzed",
        net_gex,
        f"{gamma_flip:.2f}" if gamma_flip is not None else "None",
        f"{gamma_ceiling:.2f}" if gamma_ceiling is not None else "None",
        f"{gamma_floor:.2f}" if gamma_floor is not None else "None",
        squeeze_prob,
        len(strikes_list),
    )

    return GEXResult(
        net_gex=net_gex,
        gamma_flip=gamma_flip,
        gamma_ceiling=gamma_ceiling,
        gamma_floor=gamma_floor,
        squeeze_probability=squeeze_prob,
        strikes=strikes_list,
        call_gex=call_gex_list,
        put_gex=put_gex_list,
        net_gex_by_strike=net_gex_list,
        gex_by_expiry=expiry_gex_map if multi_expiry else None,
    )
