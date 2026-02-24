"""Slippage modeling for realistic paper trade fills.

Provides two tiers of slippage estimation:
- FixedSlippage: constant offset from mid (Tier 1, for comparison/testing)
- DynamicSpreadSlippage: adapts to market conditions using bid/ask (Tier 2, recommended)

All models implement the SlippageModel ABC so they can be swapped
without changing the paper trading engine.

Key formula (Tier 2):
    half_spread = (ask - bid) / 2
    fill_price = mid + direction * slippage_factor * half_spread

Where slippage_factor is computed from moneyness (delta), DTE, volume,
VIX, time of day, order size, and multi-leg discount. Clamped to [0.05, 1.50].
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """Direction of the trade from the trader's perspective."""

    BUY = "buy"
    SELL = "sell"


@dataclass
class FillResult:
    """Result of a simulated fill.

    Attributes:
        fill_price: The simulated execution price.
        mid_price: The theoretical mid price at fill time.
        slippage: Absolute slippage from mid (always positive).
        slippage_pct: Slippage as fraction of mid price.
        spread: Bid-ask spread at time of fill.
        slippage_factor: The factor used (0.05-1.50 range for dynamic model).
        model_tier: Which model produced this fill ("fixed" or "dynamic").
        metadata: Additional context for logging and analysis.
    """

    fill_price: float
    mid_price: float
    slippage: float
    slippage_pct: float
    spread: float
    slippage_factor: float
    model_tier: str
    metadata: dict = field(default_factory=dict)


class SlippageModel(ABC):
    """Base class for slippage models.

    All models must implement simulate_fill() for single-leg fills.
    The default simulate_spread_fill() calls simulate_fill() per leg
    with is_multi_leg=True for multi-leg discount.
    """

    @abstractmethod
    def simulate_fill(
        self,
        bid: float,
        ask: float,
        side: OrderSide,
        delta: float = 0.5,
        dte: int = 30,
        volume: int = 1000,
        open_interest: int = 10000,
        vix: float = 16.0,
        order_size: int = 1,
        is_multi_leg: bool = False,
        timestamp: datetime | None = None,
    ) -> FillResult:
        """Simulate a fill and return the result.

        Args:
            bid: Current best bid price.
            ask: Current best ask price.
            side: BUY or SELL.
            delta: Option delta (absolute value used internally).
            dte: Days to expiration.
            volume: Today's volume for this contract.
            open_interest: Open interest for this contract.
            vix: Current VIX level.
            order_size: Number of contracts in the order.
            is_multi_leg: True if part of a multi-leg order (COB discount).
            timestamp: When the order is placed (for time-of-day adjustment).

        Returns:
            FillResult with simulated fill price and metadata.
        """
        ...

    def simulate_spread_fill(
        self,
        legs: list[dict],
        vix: float = 16.0,
        order_size: int = 1,
        timestamp: datetime | None = None,
    ) -> list[FillResult] | None:
        """Simulate fills for a multi-leg spread order.

        All-or-nothing: returns None if any leg has invalid quotes
        (bid <= 0 and ask <= 0). Each leg dict should have keys:
        bid, ask, side (OrderSide), delta, dte, volume, open_interest.

        Returns list of FillResult, one per leg.
        """
        results: list[FillResult] = []
        for leg in legs:
            bid = leg["bid"]
            ask = leg["ask"]
            # Skip legs where both bid and ask are zero/negative
            if bid <= 0 and ask <= 0:
                return None
            result = self.simulate_fill(
                bid=bid,
                ask=ask,
                side=leg["side"],
                delta=leg.get("delta", 0.5),
                dte=leg.get("dte", 30),
                volume=leg.get("volume", 1000),
                open_interest=leg.get("open_interest", 10000),
                vix=vix,
                order_size=order_size,
                is_multi_leg=True,
                timestamp=timestamp,
            )
            results.append(result)
        return results


class FixedSlippage(SlippageModel):
    """Tier 1: Fixed slippage offset from mid price.

    Applies a constant dollar offset from mid, regardless of market
    conditions. Useful as a baseline for comparison or simple testing.

    Args:
        fixed_cents: Fixed dollar amount of slippage (default $0.10).
        min_slippage_pct: Minimum slippage as fraction of mid (default 0.5%).
    """

    def __init__(
        self,
        fixed_cents: float = 0.10,
        min_slippage_pct: float = 0.005,
    ) -> None:
        self.fixed_cents = fixed_cents
        self.min_slippage_pct = min_slippage_pct

    def simulate_fill(
        self,
        bid: float,
        ask: float,
        side: OrderSide,
        delta: float = 0.5,
        dte: int = 30,
        volume: int = 1000,
        open_interest: int = 10000,
        vix: float = 16.0,
        order_size: int = 1,
        is_multi_leg: bool = False,
        timestamp: datetime | None = None,
    ) -> FillResult:
        """Simulate fill with fixed slippage from mid."""
        mid = (bid + ask) / 2
        spread = ask - bid

        # Edge case: zero or negative mid
        if mid <= 0:
            fill_price = ask if side == OrderSide.BUY else bid
            return FillResult(
                fill_price=fill_price,
                mid_price=mid,
                slippage=0.0,
                slippage_pct=0.0,
                spread=spread,
                slippage_factor=1.0,
                model_tier="fixed",
            )

        slippage_amount = max(self.fixed_cents, mid * self.min_slippage_pct)
        direction = 1 if side == OrderSide.BUY else -1
        fill_price = mid + direction * slippage_amount

        # Clamp within bid-ask range
        if side == OrderSide.BUY:
            fill_price = max(fill_price, bid)
            fill_price = min(fill_price, ask)
        else:
            fill_price = min(fill_price, ask)
            fill_price = max(fill_price, bid)

        actual_slippage = abs(fill_price - mid)
        half_spread = spread / 2 if spread > 0 else 1.0

        return FillResult(
            fill_price=fill_price,
            mid_price=mid,
            slippage=actual_slippage,
            slippage_pct=actual_slippage / mid if mid > 0 else 0.0,
            spread=spread,
            slippage_factor=actual_slippage / half_spread if half_spread > 0 else 0.0,
            model_tier="fixed",
        )


class DynamicSpreadSlippage(SlippageModel):
    """Tier 2: Dynamic slippage based on real-time spread and market conditions.

    Uses the actual bid-ask spread from live quotes and adjusts the fill
    point within the spread based on moneyness, DTE, volume, VIX, time
    of day, order size, and multi-leg discount.

    The slippage factor (0.05-1.50) determines where within the spread
    the fill occurs:
    - 0.0 = fill at mid (unrealistically optimistic)
    - 0.30 = base case (30% of half-spread from mid)
    - 1.0 = fill at the natural side (bid for sells, ask for buys)
    - >1.0 = fill beyond quoted spread (extreme conditions)
    """

    # Default configuration -- all adjustable via constructor
    DEFAULT_CONFIG: dict = {
        "base_factor": 0.30,
        "moneyness_thresholds": {
            "atm": (0.40, 0.0),
            "near_otm": (0.20, 0.05),
            "otm": (0.05, 0.15),
            "deep_otm": (0.0, 0.30),
        },
        "dte_adjustments": {
            "0dte": (0, 0, 0.10),
            "weekly": (1, 5, 0.03),
            "monthly": (6, 30, 0.0),
            "longer": (31, 9999, 0.05),
        },
        "volume_thresholds": [
            (5000, -0.05),
            (1000, 0.0),
            (100, 0.10),
            (0, 0.20),
        ],
        "vix_thresholds": [
            (16, 0.0),
            (25, 0.05),
            (35, 0.15),
            (999, 0.30),
        ],
        "time_adjustments": {
            "pre_open": 0.15,
            "open": 0.10,
            "midday": 0.0,
            "power_hour": 0.08,
            "close": 0.15,
            "post_close": 0.30,
        },
        "size_thresholds": [
            (10, 0.0),
            (50, 0.05),
            (200, 0.10),
            (9999, 0.20),
        ],
        "multi_leg_discount": -0.05,
        "factor_min": 0.05,
        "factor_max": 1.50,
    }

    def __init__(self, config: dict | None = None) -> None:
        self.config: dict = {**self.DEFAULT_CONFIG, **(config or {})}

    @staticmethod
    def _classify_time_of_day(ts: datetime | None) -> str:
        """Classify a timestamp into time-of-day buckets.

        Buckets reflect SPX options spread behavior throughout the
        trading day (all times Eastern):
        - pre_open: before 9:30
        - open: 9:30-9:45 (opening volatility)
        - midday: 9:45-14:00 (tightest spreads)
        - power_hour: 14:00-15:00 (increasing activity)
        - close: 15:00-16:00 (widening spreads, 0DTE gamma)
        - post_close: after 16:00
        """
        if ts is None:
            return "midday"  # conservative default

        t = ts.time()
        if t < time(9, 30):
            return "pre_open"
        elif t < time(9, 45):
            return "open"
        elif t < time(14, 0):
            return "midday"
        elif t < time(15, 0):
            return "power_hour"
        elif t < time(16, 0):
            return "close"
        else:
            return "post_close"

    def compute_slippage_factor(
        self,
        delta: float,
        dte: int,
        volume: int,
        vix: float,
        time_of_day: str,
        order_size: int,
        is_multi_leg: bool,
    ) -> float:
        """Compute the slippage factor (clamped to [0.05, 1.50]).

        Combines base factor with adjustments for:
        1. Moneyness (delta): ATM=0, deep OTM=+0.30
        2. DTE: 0DTE=+0.10, monthly=0, longer=+0.05
        3. Volume: high=-0.05 (improvement), thin=+0.20
        4. VIX: calm=0, crisis=+0.30
        5. Time of day: midday=0, open/close=+0.10-0.15
        6. Order size: small=0, large=+0.20
        7. Multi-leg discount: -0.05 (COB improvement)
        """
        cfg = self.config
        factor = cfg["base_factor"]

        # 1. Moneyness adjustment
        abs_delta = abs(delta)
        thresholds = cfg["moneyness_thresholds"]
        if abs_delta >= thresholds["atm"][0]:
            factor += thresholds["atm"][1]
        elif abs_delta >= thresholds["near_otm"][0]:
            factor += thresholds["near_otm"][1]
        elif abs_delta >= thresholds["otm"][0]:
            factor += thresholds["otm"][1]
        else:
            factor += thresholds["deep_otm"][1]

        # 2. DTE adjustment
        for _name, (lo, hi, adj) in cfg["dte_adjustments"].items():
            if lo <= dte <= hi:
                factor += adj
                break

        # 3. Volume / liquidity adjustment
        for min_vol, adj in cfg["volume_thresholds"]:
            if volume >= min_vol:
                factor += adj
                break

        # 4. VIX regime adjustment
        for max_vix, adj in cfg["vix_thresholds"]:
            if vix <= max_vix:
                factor += adj
                break

        # 5. Time of day adjustment
        factor += cfg["time_adjustments"].get(time_of_day, 0.0)

        # 6. Order size penalty
        for max_size, adj in cfg["size_thresholds"]:
            if order_size <= max_size:
                factor += adj
                break

        # 7. Multi-leg discount (COB price improvement)
        if is_multi_leg:
            factor += cfg["multi_leg_discount"]

        return max(cfg["factor_min"], min(cfg["factor_max"], factor))

    def simulate_fill(
        self,
        bid: float,
        ask: float,
        side: OrderSide,
        delta: float = 0.5,
        dte: int = 30,
        volume: int = 1000,
        open_interest: int = 10000,
        vix: float = 16.0,
        order_size: int = 1,
        is_multi_leg: bool = False,
        timestamp: datetime | None = None,
    ) -> FillResult:
        """Simulate a fill using dynamic spread-based slippage."""
        mid = (bid + ask) / 2
        spread = ask - bid

        # Edge case: zero or negative mid
        if mid <= 0 or spread < 0:
            fill_price = ask if side == OrderSide.BUY else bid
            return FillResult(
                fill_price=fill_price,
                mid_price=mid,
                slippage=abs(fill_price - mid),
                slippage_pct=0.0,
                spread=spread,
                slippage_factor=1.0,
                model_tier="dynamic",
            )

        # Handle zero/stale spread: estimate from market conditions
        if spread <= 0.01:
            spread = self._estimate_spread(mid, delta, dte, vix)

        time_bucket = self._classify_time_of_day(timestamp)

        slippage_factor = self.compute_slippage_factor(
            delta=delta,
            dte=dte,
            volume=volume,
            vix=vix,
            time_of_day=time_bucket,
            order_size=order_size,
            is_multi_leg=is_multi_leg,
        )

        half_spread = spread / 2
        slippage_amount = slippage_factor * half_spread
        direction = 1 if side == OrderSide.BUY else -1
        fill_price = mid + direction * slippage_amount

        # Clamp within bid-ask range for normal factors (allow exceeding
        # for extreme conditions where factor > 1.0)
        if side == OrderSide.BUY:
            fill_price = max(fill_price, bid)
        else:
            fill_price = min(fill_price, ask)

        actual_slippage = abs(fill_price - mid)

        return FillResult(
            fill_price=fill_price,
            mid_price=mid,
            slippage=actual_slippage,
            slippage_pct=actual_slippage / mid if mid > 0 else 0.0,
            spread=spread,
            slippage_factor=slippage_factor,
            model_tier="dynamic",
            metadata={
                "time_bucket": time_bucket,
                "abs_delta": abs(delta),
                "dte": dte,
                "volume": volume,
                "vix": vix,
                "order_size": order_size,
                "is_multi_leg": is_multi_leg,
            },
        )

    @staticmethod
    def _estimate_spread(
        option_price: float,
        delta: float,
        dte: int,
        vix: float,
    ) -> float:
        """Estimate bid-ask spread when quoted spread is zero or stale.

        Uses empirical relationships between price level, delta, DTE,
        and VIX to produce a synthetic spread estimate. Returns an
        absolute dollar spread value.

        This is used as a fallback when the data source provides
        bid == ask (locked market, stale quote, or off-hours).
        """
        abs_delta = abs(delta)

        # Base spread as percentage of option price
        if abs_delta >= 0.40:
            base_pct = 0.02  # 2% for ATM
        elif abs_delta >= 0.20:
            base_pct = 0.06  # 6% for near-OTM
        elif abs_delta >= 0.05:
            base_pct = 0.15  # 15% for OTM
        else:
            base_pct = 0.40  # 40% for deep OTM

        # Minimum absolute spread (CBOE tick size convention)
        min_spread = 0.05 if option_price < 3.0 else 0.10

        # VIX multiplier (normalized to VIX=16 baseline)
        vix_mult = max(1.0, vix / 16.0)

        # 0DTE multiplier (wider spreads near expiry)
        dte_mult = 1.3 if dte == 0 else 1.0

        return max(min_spread, option_price * base_pct * vix_mult * dte_mult)
