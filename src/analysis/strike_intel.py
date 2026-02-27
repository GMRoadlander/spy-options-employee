"""Strike Intelligence module for SPY/SPX options analysis.

Consolidates GEX levels, max pain, and high-OI strikes into a unified list of
key price levels. Provides optimal strike recommendations based on probability
of profit and GEX alignment.
"""

import logging
from dataclasses import dataclass, field
from datetime import date

from src.analysis.gex import GEXResult
from src.analysis.greeks import probability_itm
from src.analysis.max_pain import MaxPainResult
from src.analysis.pcr import PCRResult
from src.config import config
from src.data import OptionContract, OptionsChain

logger = logging.getLogger(__name__)


@dataclass
class KeyLevel:
    """A significant price level identified by the analysis engines."""

    price: float
    level_type: str
    # One of: "gamma_ceiling", "gamma_floor", "gamma_flip",
    #         "max_pain", "high_oi_call", "high_oi_put"
    significance: float  # 0-1 importance score


@dataclass
class StrikeRecommendation:
    """An optimal strike recommendation with supporting analysis."""

    strike: float
    expiry: date
    option_type: str  # "call" or "put"
    probability_itm: float
    probability_otm: float
    gex_support: str  # "aligned" or "against"


@dataclass
class StrikeIntelResult:
    """Consolidated strike intelligence from all analysis engines."""

    key_levels: list[KeyLevel] = field(default_factory=list)
    optimal_calls: list[StrikeRecommendation] = field(default_factory=list)
    optimal_puts: list[StrikeRecommendation] = field(default_factory=list)


def _find_high_oi_strikes(
    chain: OptionsChain,
    expiry: date,
    top_n: int = 5,
) -> tuple[list[tuple[float, int]], list[tuple[float, int]]]:
    """Find strikes with highest open interest for calls and puts.

    Args:
        chain: Options chain.
        expiry: Expiration date to filter.
        top_n: Number of top strikes to return.

    Returns:
        Tuple of (call_strikes, put_strikes) where each is a list of
        (strike, open_interest) sorted by OI descending.
    """
    contracts = chain.for_expiry(expiry)

    call_oi: dict[float, int] = {}
    put_oi: dict[float, int] = {}

    for c in contracts:
        if c.is_call:
            call_oi[c.strike] = call_oi.get(c.strike, 0) + c.open_interest
        else:
            put_oi[c.strike] = put_oi.get(c.strike, 0) + c.open_interest

    top_calls = sorted(call_oi.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_puts = sorted(put_oi.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return top_calls, top_puts


def _build_key_levels(
    gex: GEXResult,
    max_pain: MaxPainResult,
    high_oi_calls: list[tuple[float, int]],
    high_oi_puts: list[tuple[float, int]],
) -> list[KeyLevel]:
    """Build a consolidated list of key price levels from all engines.

    Significance is assigned based on the relative importance of each level:
    - Gamma flip: highest significance (directly affects dealer hedging behavior)
    - Gamma ceiling/floor: high significance (major hedging boundaries)
    - Max pain: moderate-high significance (expiry magnet)
    - High OI strikes: moderate significance (support/resistance from positioning)

    Args:
        gex: GEX analysis result.
        max_pain: Max pain analysis result.
        high_oi_calls: Top call strikes by OI.
        high_oi_puts: Top put strikes by OI.

    Returns:
        List of KeyLevel sorted by significance descending.
    """
    levels: list[KeyLevel] = []

    # Gamma flip is the most significant level
    if gex.gamma_flip is not None:
        levels.append(
            KeyLevel(
                price=gex.gamma_flip,
                level_type="gamma_flip",
                significance=1.0,
            )
        )

    # Gamma ceiling and floor
    if gex.gamma_ceiling is not None:
        levels.append(
            KeyLevel(
                price=gex.gamma_ceiling,
                level_type="gamma_ceiling",
                significance=0.9,
            )
        )

    if gex.gamma_floor is not None:
        levels.append(
            KeyLevel(
                price=gex.gamma_floor,
                level_type="gamma_floor",
                significance=0.85,
            )
        )

    # Max pain
    levels.append(
        KeyLevel(
            price=max_pain.max_pain_price,
            level_type="max_pain",
            significance=0.8,
        )
    )

    # High OI strikes with decaying significance
    max_call_oi = max((oi for _, oi in high_oi_calls), default=1)
    for strike, oi in high_oi_calls:
        # Normalize significance relative to highest OI call
        relative_oi = oi / max_call_oi if max_call_oi > 0 else 0.0
        significance = 0.5 + 0.2 * relative_oi  # Range: 0.5 - 0.7
        levels.append(
            KeyLevel(
                price=strike,
                level_type="high_oi_call",
                significance=round(significance, 3),
            )
        )

    max_put_oi = max((oi for _, oi in high_oi_puts), default=1)
    for strike, oi in high_oi_puts:
        relative_oi = oi / max_put_oi if max_put_oi > 0 else 0.0
        significance = 0.5 + 0.2 * relative_oi  # Range: 0.5 - 0.7
        levels.append(
            KeyLevel(
                price=strike,
                level_type="high_oi_put",
                significance=round(significance, 3),
            )
        )

    # Sort by significance descending
    levels.sort(key=lambda x: x.significance, reverse=True)

    return levels


def _assess_gex_support(
    strike: float,
    option_type: str,
    gex: GEXResult,
    spot: float,
) -> str:
    """Determine if GEX levels support or oppose a trade at this strike.

    For calls (bullish trade):
    - "aligned" if spot is below gamma ceiling (price has room to move up
      toward the ceiling, where positive GEX provides support)
    - "against" if spot is above gamma ceiling or net GEX is very negative

    For puts (bearish trade):
    - "aligned" if spot is above gamma floor (price has room to move down
      toward the floor, where negative GEX amplifies the drop)
    - "against" if spot is below gamma floor or net GEX is very positive

    Args:
        strike: The option strike being evaluated.
        option_type: "call" or "put".
        gex: GEX analysis result.
        spot: Current spot price.

    Returns:
        "aligned" or "against".
    """
    if option_type == "call":
        # Bullish: want room to run up, positive GEX regime
        if gex.gamma_ceiling is not None and spot < gex.gamma_ceiling and gex.net_gex >= 0:
            return "aligned"
        # If gamma flip exists and spot is near or below it, positive momentum possible
        if gex.gamma_flip is not None and spot <= gex.gamma_flip:
            return "aligned"
        return "against"

    elif option_type == "put":
        # Bearish: want room to drop, negative GEX regime amplifies drops
        if gex.gamma_floor is not None and spot > gex.gamma_floor and gex.net_gex < 0:
            return "aligned"
        # If gamma flip exists and spot is above it, still in negative GEX territory
        if gex.gamma_flip is not None and spot > gex.gamma_flip:
            return "aligned"
        return "against"

    return "against"


def _find_optimal_strikes(
    chain: OptionsChain,
    expiry: date,
    option_type: str,
    gex: GEXResult,
    top_n: int = 5,
) -> list[StrikeRecommendation]:
    """Find optimal strikes with best risk/reward for a given direction.

    Selection criteria:
    1. Filter to OTM strikes (calls above spot, puts below spot)
    2. Require minimum open interest (liquidity filter)
    3. Score by: probability of profit zone + GEX alignment + bid-ask spread

    Args:
        chain: Options chain.
        expiry: Target expiration.
        option_type: "call" or "put".
        gex: GEX result for alignment checks.
        top_n: Number of recommendations to return.

    Returns:
        List of StrikeRecommendation sorted by probability_itm descending.
    """
    spot = chain.spot_price
    r = config.risk_free_rate
    contracts = chain.for_expiry(expiry)

    # Filter to the correct type and OTM
    if option_type == "call":
        candidates = [
            c for c in contracts
            if c.is_call and c.strike > spot and c.open_interest >= 100
        ]
    else:
        candidates = [
            c for c in contracts
            if c.is_put and c.strike < spot and c.open_interest >= 100
        ]

    if not candidates:
        return []

    # Time to expiry
    days = (expiry - date.today()).days
    T = max(days, 1) / 365.0

    recommendations: list[StrikeRecommendation] = []

    for c in candidates:
        p_itm = probability_itm(spot, c.strike, T, c.iv, r, option_type)
        p_otm = 1.0 - p_itm
        gex_support = _assess_gex_support(c.strike, option_type, gex, spot)

        recommendations.append(
            StrikeRecommendation(
                strike=c.strike,
                expiry=expiry,
                option_type=option_type,
                probability_itm=round(p_itm, 4),
                probability_otm=round(p_otm, 4),
                gex_support=gex_support,
            )
        )

    # Sort by probability ITM descending (highest probability first)
    # Among equal probabilities, prefer "aligned" GEX support
    recommendations.sort(
        key=lambda r: (r.probability_itm, 1 if r.gex_support == "aligned" else 0),
        reverse=True,
    )

    return recommendations[:top_n]


def calculate_strike_intel(
    chain: OptionsChain,
    gex: GEXResult,
    max_pain: MaxPainResult,
    pcr: PCRResult,
    expiry: date | None = None,
) -> StrikeIntelResult:
    """Build consolidated strike intelligence from all analysis engines.

    Combines GEX levels, max pain, high OI strikes, and probability analysis
    into a unified view of key price levels and optimal trade strikes.

    Args:
        chain: Full options chain.
        gex: GEX analysis result.
        max_pain: Max pain analysis result.
        pcr: Put/call ratio result (used for context, not directly in levels).
        expiry: Target expiration for strike recommendations.
                Defaults to nearest expiry.

    Returns:
        StrikeIntelResult with key levels and optimal strikes.
    """
    if expiry is None:
        expiry = chain.nearest_expiry()
        if expiry is None:
            logger.warning("No expirations found in chain for strike intel")
            return StrikeIntelResult()

    # Find high OI strikes
    high_oi_calls, high_oi_puts = _find_high_oi_strikes(chain, expiry)

    # Build key levels
    key_levels = _build_key_levels(gex, max_pain, high_oi_calls, high_oi_puts)

    # Find optimal call and put strikes
    optimal_calls = _find_optimal_strikes(chain, expiry, "call", gex)
    optimal_puts = _find_optimal_strikes(chain, expiry, "put", gex)

    logger.info(
        "Strike intel: %d key levels, %d call recs, %d put recs for %s expiry %s",
        len(key_levels),
        len(optimal_calls),
        len(optimal_puts),
        chain.ticker,
        expiry,
    )

    return StrikeIntelResult(
        key_levels=key_levels,
        optimal_calls=optimal_calls,
        optimal_puts=optimal_puts,
    )
