"""DIY HIRO (Hedging Impact Real-time Options) indicator.

Measures the aggregate delta-hedging impact of live options trades on the
underlying.  When customers buy calls, dealers sell calls and must buy
delta-equivalent shares (bullish hedging pressure).  When customers buy
puts, dealers sell puts and must sell delta-equivalent shares (bearish
hedging pressure).

The calculator is stateful: it accumulates trades over a trading session
and produces windowed and cumulative readings.

This module does NOT connect to any data source.  Trade dicts are fed in
via ``process_trade()``; Polygon WebSocket wiring happens in a later step.

Phase 4 / Step 10 of the SpotGamma integration plan.
"""

from __future__ import annotations

import logging
import math
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.analysis.greeks import black_scholes_delta

logger = logging.getLogger(__name__)

# Regex to extract call/put and strike from OCC-style option ticker.
# Format: O:SPY251219C00600000
#   - 6-digit date (YYMMDD)
#   - C or P
#   - 8-digit strike (in thousandths: 00600000 = 600.000)
_OCC_RE = re.compile(
    r"(?:O:)?[A-Z]{1,6}"       # optional O: prefix + underlying
    r"(\d{6})"                   # 6-digit expiration (YYMMDD)
    r"([CP])"                    # call or put
    r"(\d{8})"                   # 8-digit strike in thousandths
)


def _parse_occ_ticker(ticker: str) -> dict | None:
    """Extract option metadata from an OCC-style ticker.

    Returns:
        Dict with ``option_type`` ('call'/'put'), ``strike`` (float),
        ``expiry_str`` (YYMMDD), or ``None`` if not parseable.
    """
    m = _OCC_RE.search(ticker)
    if not m:
        return None
    expiry_str = m.group(1)
    opt_type = "call" if m.group(2) == "C" else "put"
    strike = int(m.group(3)) / 1000.0
    return {
        "option_type": opt_type,
        "strike": strike,
        "expiry_str": expiry_str,
    }


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class DIYHIROResult:
    """Snapshot of HIRO indicator state.

    Attributes:
        timestamp: When this snapshot was taken.
        hedging_impact: Net dealer hedging pressure in [-1.0, 1.0],
            normalized via tanh.  Positive = bullish (dealers buying shares),
            negative = bearish (dealers selling shares).
        cumulative_impact: Session-total (un-windowed) cumulative hedging
            pressure, normalized to [-1.0, 1.0].
        call_pressure: Windowed bullish hedging from call activity
            (positive value).
        put_pressure: Windowed bearish hedging from put activity
            (negative value).
        trade_count: Number of trades in the current window.
    """

    timestamp: datetime
    hedging_impact: float       # net dealer hedging pressure [-1.0, 1.0]
    cumulative_impact: float    # rolling cumulative pressure for session
    call_pressure: float        # bullish hedging from call activity
    put_pressure: float         # bearish hedging from put activity
    trade_count: int            # trades processed in this window


# ---------------------------------------------------------------------------
# Internal trade record
# ---------------------------------------------------------------------------


@dataclass
class _TradeRecord:
    """Internal record of a processed trade's hedging impact."""

    timestamp_ms: int           # trade timestamp in milliseconds
    delta_notional: float       # signed delta-notional hedging impact
    is_call: bool               # True if the option is a call


# ---------------------------------------------------------------------------
# HIRO Calculator
# ---------------------------------------------------------------------------


# Scaling constant for tanh normalization.  Chosen so that a single-window
# delta-notional of ~$50 M maps to roughly +/-0.5 on the output scale.
# Adjust empirically once live data is flowing.
_TANH_SCALE = 5_000_000.0


class DIYHIROCalculator:
    """Stateful calculator for the DIY HIRO indicator.

    Accumulates options trades, computes Black-Scholes delta for each,
    infers dealer hedging direction, and produces windowed + cumulative
    readings.

    Args:
        window_minutes: Rolling window size in minutes (default 5).
        underlying_price: Current price of the underlying.  Can be updated
            via ``update_underlying_price()``.
        risk_free_rate: Annualized risk-free rate as decimal (default 0.05).
        default_iv: Fallback implied volatility when not available on the
            trade dict (default 0.20 = 20%).
        default_dte_years: Fallback time-to-expiry in years when expiry
            cannot be parsed from the ticker (default ~7 calendar days).
    """

    def __init__(
        self,
        window_minutes: int = 5,
        underlying_price: float = 0.0,
        risk_free_rate: float = 0.05,
        default_iv: float = 0.20,
        default_dte_years: float = 7.0 / 365.0,
    ) -> None:
        self._window_ms = window_minutes * 60 * 1000
        self._underlying_price = underlying_price
        self._risk_free_rate = risk_free_rate
        self._default_iv = default_iv
        self._default_dte_years = default_dte_years

        # Rolling window of trade records (newest at right)
        self._trades: deque[_TradeRecord] = deque()

        # Session-level accumulators
        self._cumulative_raw: float = 0.0
        self._session_trade_count: int = 0

        # Session history: list of periodic snapshots
        self._history: list[DIYHIROResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_underlying_price(self, price: float) -> None:
        """Update the current underlying price used for delta computation."""
        if price > 0:
            self._underlying_price = price

    def process_trade(self, trade: dict) -> None:
        """Process a single options trade from the Polygon stream.

        Expected trade dict keys (matching ``PolygonOptionsStream._parse_event``
        output for trade events):
            - ``ticker``: OCC-style option ticker (e.g. ``O:SPY251219C00600000``)
            - ``price``: Trade price per contract
            - ``size``: Number of contracts
            - ``timestamp``: Trade timestamp in epoch milliseconds
            - ``bid`` (optional): Current best bid at time of trade
            - ``ask`` (optional): Current best ask at time of trade
            - ``iv`` (optional): Implied volatility as decimal
            - ``dte_years`` (optional): Time to expiry in years

        Computation steps:
            1. Parse option type and strike from OCC ticker.
            2. Classify trade as buyer-initiated or seller-initiated.
            3. Compute Black-Scholes delta.
            4. Derive delta-notional hedging impact.
            5. Infer dealer hedging direction and accumulate.
        """
        if self._underlying_price <= 0:
            logger.debug("HIRO: no underlying price set, skipping trade")
            return

        ticker = trade.get("ticker", "")
        parsed = _parse_occ_ticker(ticker)
        if parsed is None:
            logger.debug("HIRO: cannot parse OCC ticker '%s'", ticker)
            return

        option_type: str = parsed["option_type"]
        strike: float = parsed["strike"]
        is_call = option_type == "call"

        trade_price = float(trade.get("price", 0.0))
        size = int(trade.get("size", 0))
        ts_ms = int(trade.get("timestamp", 0))

        if size <= 0 or trade_price <= 0:
            return

        # ----- Step 1: Classify buyer vs seller initiated -----
        side = self._classify_side(trade)
        if side == 0:
            # Ambiguous trade; skip
            return

        # side: +1 = buyer initiated, -1 = seller initiated

        # ----- Step 2: Compute delta -----
        iv = float(trade.get("iv", self._default_iv))
        dte = float(trade.get("dte_years", self._default_dte_years))

        if iv <= 0:
            iv = self._default_iv
        if dte <= 0:
            dte = self._default_dte_years

        delta = black_scholes_delta(
            S=self._underlying_price,
            K=strike,
            T=dte,
            sigma=iv,
            r=self._risk_free_rate,
            option_type=option_type,
        )

        if delta == 0.0:
            return

        # ----- Step 3: Delta-notional -----
        # delta_notional = delta * contracts * 100 * underlying_price
        delta_notional = abs(delta) * size * 100 * self._underlying_price

        # ----- Step 4: Dealer hedging direction -----
        # If customer BUYS a call (side=+1, call):
        #   Dealer is SHORT the call -> must BUY shares to hedge -> POSITIVE
        # If customer SELLS a call (side=-1, call):
        #   Dealer is LONG the call -> must SELL shares to hedge -> NEGATIVE
        # If customer BUYS a put (side=+1, put):
        #   Dealer is SHORT the put -> must SELL shares to hedge -> NEGATIVE
        # If customer SELLS a put (side=-1, put):
        #   Dealer is LONG the put -> must BUY shares to hedge -> POSITIVE
        if is_call:
            hedging_sign = side   # buy call -> +1 (bullish), sell call -> -1
        else:
            hedging_sign = -side  # buy put -> -1 (bearish), sell put -> +1

        signed_impact = hedging_sign * delta_notional

        # ----- Step 5: Accumulate -----
        record = _TradeRecord(
            timestamp_ms=ts_ms,
            delta_notional=signed_impact,
            is_call=is_call,
        )
        self._trades.append(record)
        self._cumulative_raw += signed_impact
        self._session_trade_count += 1

        # Prune old trades from window
        self._prune_window(ts_ms)

    def get_current(self) -> DIYHIROResult:
        """Get current HIRO reading from the rolling window.

        Returns:
            :class:`DIYHIROResult` with normalized hedging impact and
            cumulative session impact.
        """
        now = datetime.now(timezone.utc)

        if not self._trades:
            return DIYHIROResult(
                timestamp=now,
                hedging_impact=0.0,
                cumulative_impact=0.0,
                call_pressure=0.0,
                put_pressure=0.0,
                trade_count=0,
            )

        # Sum windowed impacts
        window_total = 0.0
        call_total = 0.0
        put_total = 0.0
        count = 0

        for rec in self._trades:
            window_total += rec.delta_notional
            if rec.is_call:
                call_total += rec.delta_notional
            else:
                put_total += rec.delta_notional
            count += 1

        # Normalize via tanh for bounded output
        hedging_impact = math.tanh(window_total / _TANH_SCALE)
        cumulative_impact = math.tanh(self._cumulative_raw / _TANH_SCALE)

        return DIYHIROResult(
            timestamp=now,
            hedging_impact=hedging_impact,
            cumulative_impact=cumulative_impact,
            call_pressure=call_total,
            put_pressure=put_total,
            trade_count=count,
        )

    def reset_session(self) -> None:
        """Reset all state for a new trading session."""
        self._trades.clear()
        self._cumulative_raw = 0.0
        self._session_trade_count = 0
        self._history.clear()

    def snapshot(self) -> DIYHIROResult:
        """Take a snapshot and append it to session history.

        Returns:
            The snapshot :class:`DIYHIROResult`.
        """
        result = self.get_current()
        self._history.append(result)
        return result

    def get_session_history(self) -> list[DIYHIROResult]:
        """Get HIRO snapshots for the entire session (one per snapshot call).

        Returns:
            List of :class:`DIYHIROResult` in chronological order.
        """
        return list(self._history)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_side(trade: dict) -> int:
        """Classify a trade as buyer- or seller-initiated.

        Classification rules:
            - If trade price >= ask -> buyer initiated (+1)
            - If trade price <= bid -> seller initiated (-1)
            - If between bid and ask -> use size heuristic:
              odd lots (<10 contracts) lean buyer, else skip.
            - If no bid/ask available -> use size heuristic as fallback.

        Returns:
            +1 for buyer, -1 for seller, 0 for ambiguous/skip.
        """
        price = float(trade.get("price", 0.0))
        bid = trade.get("bid")
        ask = trade.get("ask")

        if bid is not None and ask is not None:
            bid_f = float(bid)
            ask_f = float(ask)

            if ask_f > 0 and price >= ask_f:
                return 1   # buyer initiated (lifted the ask)
            if bid_f > 0 and price <= bid_f:
                return -1  # seller initiated (hit the bid)

            # Between bid and ask — midpoint heuristic
            if ask_f > bid_f > 0:
                mid = (bid_f + ask_f) / 2.0
                if price > mid:
                    return 1
                elif price < mid:
                    return -1

            # Exactly at mid or invalid spread — ambiguous
            return 0

        # No bid/ask available — cannot reliably classify
        return 0

    def _prune_window(self, current_ts_ms: int) -> None:
        """Remove trades older than the rolling window."""
        cutoff = current_ts_ms - self._window_ms
        while self._trades and self._trades[0].timestamp_ms < cutoff:
            self._trades.popleft()
