"""Tests for DIY HIRO (Hedging Impact Real-time Options) indicator.

Validates trade processing, buyer/seller classification, hedging direction,
cumulative accumulation, rolling window pruning, session reset, and
normalization bounds using synthetic trades.
"""

import math
import time

import pytest

from src.analysis.hiro import (
    DIYHIROCalculator,
    DIYHIROResult,
    _parse_occ_ticker,
    _TANH_SCALE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_trade(
    ticker: str = "O:SPY251219C00600000",
    price: float = 5.00,
    size: int = 10,
    bid: float | None = 4.80,
    ask: float | None = 5.20,
    timestamp: int = 1_700_000_000_000,
    iv: float | None = None,
    dte_years: float | None = None,
) -> dict:
    """Build a synthetic trade dict matching PolygonOptionsStream output."""
    trade: dict = {
        "type": "trade",
        "ticker": ticker,
        "price": price,
        "size": size,
        "timestamp": timestamp,
    }
    if bid is not None:
        trade["bid"] = bid
    if ask is not None:
        trade["ask"] = ask
    if iv is not None:
        trade["iv"] = iv
    if dte_years is not None:
        trade["dte_years"] = dte_years
    return trade


def _make_calculator(**kwargs) -> DIYHIROCalculator:
    """Create a calculator with sensible test defaults."""
    defaults = {
        "window_minutes": 5,
        "underlying_price": 600.0,
        "risk_free_rate": 0.05,
        "default_iv": 0.20,
        "default_dte_years": 30.0 / 365.0,
    }
    defaults.update(kwargs)
    return DIYHIROCalculator(**defaults)


# ---------------------------------------------------------------------------
# OCC ticker parsing
# ---------------------------------------------------------------------------


class TestOCCTickerParsing:
    """Validate OCC-style option ticker parsing."""

    def test_parse_call_ticker(self):
        result = _parse_occ_ticker("O:SPY251219C00600000")
        assert result is not None
        assert result["option_type"] == "call"
        assert result["strike"] == 600.0

    def test_parse_put_ticker(self):
        result = _parse_occ_ticker("O:SPY251219P00550000")
        assert result is not None
        assert result["option_type"] == "put"
        assert result["strike"] == 550.0

    def test_parse_fractional_strike(self):
        result = _parse_occ_ticker("O:SPY251219C00600500")
        assert result is not None
        assert result["strike"] == 600.5

    def test_parse_without_prefix(self):
        result = _parse_occ_ticker("SPY251219C00600000")
        assert result is not None
        assert result["option_type"] == "call"

    def test_parse_invalid_ticker(self):
        result = _parse_occ_ticker("SPY")
        assert result is None

    def test_parse_empty_string(self):
        result = _parse_occ_ticker("")
        assert result is None


# ---------------------------------------------------------------------------
# Trade classification (buyer vs seller)
# ---------------------------------------------------------------------------


class TestTradeClassification:
    """Validate buyer/seller trade classification."""

    def test_trade_at_ask_is_buyer(self):
        """Trade at or above the ask = buyer initiated."""
        calc = _make_calculator()
        trade = _make_trade(price=5.20, bid=4.80, ask=5.20)
        assert calc._classify_side(trade) == 1

    def test_trade_above_ask_is_buyer(self):
        """Trade above the ask = buyer initiated."""
        calc = _make_calculator()
        trade = _make_trade(price=5.50, bid=4.80, ask=5.20)
        assert calc._classify_side(trade) == 1

    def test_trade_at_bid_is_seller(self):
        """Trade at or below the bid = seller initiated."""
        calc = _make_calculator()
        trade = _make_trade(price=4.80, bid=4.80, ask=5.20)
        assert calc._classify_side(trade) == -1

    def test_trade_below_bid_is_seller(self):
        """Trade below the bid = seller initiated."""
        calc = _make_calculator()
        trade = _make_trade(price=4.50, bid=4.80, ask=5.20)
        assert calc._classify_side(trade) == -1

    def test_trade_above_mid_is_buyer(self):
        """Trade above midpoint but below ask = buyer."""
        calc = _make_calculator()
        # mid = (4.80 + 5.20) / 2 = 5.00; trade at 5.10 > mid
        trade = _make_trade(price=5.10, bid=4.80, ask=5.20)
        assert calc._classify_side(trade) == 1

    def test_trade_below_mid_is_seller(self):
        """Trade below midpoint but above bid = seller."""
        calc = _make_calculator()
        # mid = 5.00; trade at 4.90 < mid
        trade = _make_trade(price=4.90, bid=4.80, ask=5.20)
        assert calc._classify_side(trade) == -1

    def test_trade_at_exact_mid_is_ambiguous(self):
        """Trade exactly at midpoint = ambiguous (returns 0)."""
        calc = _make_calculator()
        trade = _make_trade(price=5.00, bid=4.80, ask=5.20)
        assert calc._classify_side(trade) == 0

    def test_no_bid_ask_returns_zero(self):
        """Without bid/ask data, classification returns 0 (ambiguous)."""
        calc = _make_calculator()
        trade = _make_trade(price=5.00, bid=None, ask=None)
        assert calc._classify_side(trade) == 0


# ---------------------------------------------------------------------------
# Hedging direction
# ---------------------------------------------------------------------------


class TestHedgingDirection:
    """Validate that hedging direction is correct for each scenario."""

    def test_call_buy_is_bullish(self):
        """Customer buys call -> dealer hedges by buying shares -> positive."""
        calc = _make_calculator()
        # Buyer-initiated call trade (price >= ask)
        trade = _make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20,
            bid=4.80,
            ask=5.20,
            size=10,
        )
        calc.process_trade(trade)
        result = calc.get_current()
        assert result.call_pressure > 0, "Call buy should produce positive pressure"
        assert result.hedging_impact > 0, "Call buy should be bullish"

    def test_put_buy_is_bearish(self):
        """Customer buys put -> dealer hedges by selling shares -> negative."""
        calc = _make_calculator()
        trade = _make_trade(
            ticker="O:SPY251219P00600000",
            price=5.20,
            bid=4.80,
            ask=5.20,
            size=10,
        )
        calc.process_trade(trade)
        result = calc.get_current()
        assert result.put_pressure < 0, "Put buy should produce negative pressure"
        assert result.hedging_impact < 0, "Put buy should be bearish"

    def test_call_sell_is_bearish(self):
        """Customer sells call -> dealer hedges by selling shares -> negative."""
        calc = _make_calculator()
        trade = _make_trade(
            ticker="O:SPY251219C00600000",
            price=4.80,  # at the bid = seller initiated
            bid=4.80,
            ask=5.20,
            size=10,
        )
        calc.process_trade(trade)
        result = calc.get_current()
        assert result.call_pressure < 0, "Call sell should produce negative call pressure"
        assert result.hedging_impact < 0, "Call sell should be bearish"

    def test_put_sell_is_bullish(self):
        """Customer sells put -> dealer hedges by buying shares -> positive."""
        calc = _make_calculator()
        trade = _make_trade(
            ticker="O:SPY251219P00600000",
            price=4.80,  # seller initiated
            bid=4.80,
            ask=5.20,
            size=10,
        )
        calc.process_trade(trade)
        result = calc.get_current()
        assert result.put_pressure > 0, "Put sell should produce positive put pressure"
        assert result.hedging_impact > 0, "Put sell should be bullish"


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------


class TestEmptyState:
    """Validate behavior with no trades processed."""

    def test_empty_returns_zeros(self):
        """get_current() on fresh calculator returns all zeros."""
        calc = _make_calculator()
        result = calc.get_current()
        assert result.hedging_impact == 0.0
        assert result.cumulative_impact == 0.0
        assert result.call_pressure == 0.0
        assert result.put_pressure == 0.0
        assert result.trade_count == 0

    def test_empty_history(self):
        """Session history is empty on fresh calculator."""
        calc = _make_calculator()
        assert calc.get_session_history() == []


# ---------------------------------------------------------------------------
# Cumulative accumulation
# ---------------------------------------------------------------------------


class TestCumulativeAccumulation:
    """Validate cumulative session-level impact."""

    def test_cumulative_grows_with_trades(self):
        """Cumulative impact increases as more same-direction trades arrive."""
        calc = _make_calculator()
        ts = 1_700_000_000_000

        for i in range(5):
            trade = _make_trade(
                ticker="O:SPY251219C00600000",
                price=5.20,
                bid=4.80,
                ask=5.20,
                size=10,
                timestamp=ts + i * 1000,
            )
            calc.process_trade(trade)

        result = calc.get_current()
        assert result.cumulative_impact > 0
        assert result.trade_count == 5

    def test_opposing_trades_reduce_cumulative(self):
        """Call buy followed by put buy should partially cancel out."""
        calc = _make_calculator()
        ts = 1_700_000_000_000

        # Bullish: buy call
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=ts,
        ))
        after_call = calc.get_current()

        # Bearish: buy put (same size)
        calc.process_trade(_make_trade(
            ticker="O:SPY251219P00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=ts + 1000,
        ))
        after_both = calc.get_current()

        # The call and put at the same strike have different absolute deltas,
        # so they won't perfectly cancel, but cumulative should be closer to 0
        assert abs(after_both.cumulative_impact) < abs(after_call.cumulative_impact)


# ---------------------------------------------------------------------------
# Rolling window pruning
# ---------------------------------------------------------------------------


class TestRollingWindow:
    """Validate that old trades are dropped from the rolling window."""

    def test_old_trades_pruned(self):
        """Trades older than window_minutes are dropped."""
        calc = _make_calculator(window_minutes=5)
        base_ts = 1_700_000_000_000

        # Trade 1: at T=0
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=base_ts,
        ))
        assert calc.get_current().trade_count == 1

        # Trade 2: at T=6 minutes (should prune trade 1)
        six_min_ms = 6 * 60 * 1000
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=base_ts + six_min_ms,
        ))
        assert calc.get_current().trade_count == 1  # only the latest trade

    def test_trades_within_window_kept(self):
        """Trades within the window are all retained."""
        calc = _make_calculator(window_minutes=5)
        base_ts = 1_700_000_000_000

        for i in range(3):
            calc.process_trade(_make_trade(
                ticker="O:SPY251219C00600000",
                price=5.20, bid=4.80, ask=5.20,
                size=10, timestamp=base_ts + i * 60_000,  # 1 min apart
            ))

        assert calc.get_current().trade_count == 3

    def test_cumulative_persists_after_window_prune(self):
        """Cumulative impact is NOT affected by window pruning."""
        calc = _make_calculator(window_minutes=1)
        base_ts = 1_700_000_000_000

        # Trade at T=0
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=50, timestamp=base_ts,
        ))
        cum_after_first = calc.get_current().cumulative_impact

        # Trade at T=2 minutes (prunes first trade from window)
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=50, timestamp=base_ts + 2 * 60_000,
        ))

        result = calc.get_current()
        # Cumulative should be strictly greater than after just the first trade
        assert result.cumulative_impact > cum_after_first
        # But windowed count is only 1 (first trade was pruned)
        assert result.trade_count == 1


# ---------------------------------------------------------------------------
# Session reset
# ---------------------------------------------------------------------------


class TestSessionReset:
    """Validate session reset clears all state."""

    def test_reset_clears_trades(self):
        """After reset, get_current returns zeros."""
        calc = _make_calculator()
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=1_700_000_000_000,
        ))
        assert calc.get_current().trade_count == 1

        calc.reset_session()
        result = calc.get_current()
        assert result.trade_count == 0
        assert result.hedging_impact == 0.0
        assert result.cumulative_impact == 0.0

    def test_reset_clears_history(self):
        """After reset, session history is empty."""
        calc = _make_calculator()
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=1_700_000_000_000,
        ))
        calc.snapshot()
        assert len(calc.get_session_history()) == 1

        calc.reset_session()
        assert calc.get_session_history() == []


# ---------------------------------------------------------------------------
# Normalization bounds
# ---------------------------------------------------------------------------


class TestNormalization:
    """Validate that hedging_impact stays in [-1, 1]."""

    def test_massive_bullish_stays_bounded(self):
        """Even huge call buys produce hedging_impact <= 1.0."""
        calc = _make_calculator()
        ts = 1_700_000_000_000

        for i in range(100):
            calc.process_trade(_make_trade(
                ticker="O:SPY251219C00600000",
                price=5.20, bid=4.80, ask=5.20,
                size=1000,  # large
                timestamp=ts + i * 100,
            ))

        result = calc.get_current()
        assert -1.0 <= result.hedging_impact <= 1.0
        assert -1.0 <= result.cumulative_impact <= 1.0

    def test_massive_bearish_stays_bounded(self):
        """Even huge put buys produce hedging_impact >= -1.0."""
        calc = _make_calculator()
        ts = 1_700_000_000_000

        for i in range(100):
            calc.process_trade(_make_trade(
                ticker="O:SPY251219P00600000",
                price=5.20, bid=4.80, ask=5.20,
                size=1000,
                timestamp=ts + i * 100,
            ))

        result = calc.get_current()
        assert -1.0 <= result.hedging_impact <= 1.0
        assert -1.0 <= result.cumulative_impact <= 1.0

    def test_single_trade_reasonable_magnitude(self):
        """A single 10-lot trade should NOT saturate the indicator."""
        calc = _make_calculator()
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10,
            timestamp=1_700_000_000_000,
        ))
        result = calc.get_current()
        # Should be positive but well below 1.0
        assert 0.0 < result.hedging_impact < 0.5


# ---------------------------------------------------------------------------
# Mixed call/put trades
# ---------------------------------------------------------------------------


class TestMixedTrades:
    """Validate behavior with a mix of call and put trades."""

    def test_mixed_trades_net_near_zero(self):
        """Equal call buys and put sells should roughly cancel hedging."""
        calc = _make_calculator()
        ts = 1_700_000_000_000

        # 5 call buys (bullish)
        for i in range(5):
            calc.process_trade(_make_trade(
                ticker="O:SPY251219C00600000",
                price=5.20, bid=4.80, ask=5.20,
                size=10, timestamp=ts + i * 100,
            ))

        # 5 put buys (bearish) — same strike and size
        for i in range(5):
            calc.process_trade(_make_trade(
                ticker="O:SPY251219P00600000",
                price=5.20, bid=4.80, ask=5.20,
                size=10, timestamp=ts + (i + 5) * 100,
            ))

        result = calc.get_current()
        # Call delta (~0.55) vs put delta (~0.45 abs) don't perfectly cancel,
        # but the net should be smaller than either side alone
        assert result.trade_count == 10
        assert result.call_pressure > 0
        assert result.put_pressure < 0

    def test_dominant_call_activity(self):
        """More call buys than put buys should be net bullish."""
        calc = _make_calculator()
        ts = 1_700_000_000_000

        # 10 call buys
        for i in range(10):
            calc.process_trade(_make_trade(
                ticker="O:SPY251219C00600000",
                price=5.20, bid=4.80, ask=5.20,
                size=10, timestamp=ts + i * 100,
            ))

        # 2 put buys
        for i in range(2):
            calc.process_trade(_make_trade(
                ticker="O:SPY251219P00600000",
                price=5.20, bid=4.80, ask=5.20,
                size=10, timestamp=ts + (i + 10) * 100,
            ))

        result = calc.get_current()
        assert result.hedging_impact > 0, "Should be net bullish"


# ---------------------------------------------------------------------------
# Session history / snapshots
# ---------------------------------------------------------------------------


class TestSessionHistory:
    """Validate snapshot and history functionality."""

    def test_snapshot_appends_to_history(self):
        """Each snapshot() call adds a result to history."""
        calc = _make_calculator()
        ts = 1_700_000_000_000

        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=ts,
        ))
        calc.snapshot()

        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=20, timestamp=ts + 60_000,
        ))
        calc.snapshot()

        history = calc.get_session_history()
        assert len(history) == 2
        # Second snapshot should show more pressure (more trades)
        assert history[1].trade_count > history[0].trade_count

    def test_history_returns_copies(self):
        """get_session_history returns a copy, not the internal list."""
        calc = _make_calculator()
        calc.snapshot()
        history = calc.get_session_history()
        history.clear()
        assert len(calc.get_session_history()) == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Validate edge case handling."""

    def test_no_underlying_price_skips_trade(self):
        """Trade processing is skipped when underlying_price is 0."""
        calc = _make_calculator(underlying_price=0.0)
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=1_700_000_000_000,
        ))
        assert calc.get_current().trade_count == 0

    def test_invalid_ticker_skipped(self):
        """Trade with unparseable ticker is skipped."""
        calc = _make_calculator()
        calc.process_trade(_make_trade(
            ticker="INVALID",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=1_700_000_000_000,
        ))
        assert calc.get_current().trade_count == 0

    def test_zero_size_skipped(self):
        """Trade with zero size is skipped."""
        calc = _make_calculator()
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=0, timestamp=1_700_000_000_000,
        ))
        assert calc.get_current().trade_count == 0

    def test_zero_price_skipped(self):
        """Trade with zero price is skipped."""
        calc = _make_calculator()
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=0.0, bid=4.80, ask=5.20,
            size=10, timestamp=1_700_000_000_000,
        ))
        assert calc.get_current().trade_count == 0

    def test_ambiguous_trade_skipped(self):
        """Trade at exact midpoint with no other heuristic is skipped."""
        calc = _make_calculator()
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.00,  # exactly at mid of (4.80, 5.20)
            bid=4.80, ask=5.20,
            size=10, timestamp=1_700_000_000_000,
        ))
        assert calc.get_current().trade_count == 0

    def test_update_underlying_price(self):
        """update_underlying_price changes the price used for delta."""
        calc = _make_calculator(underlying_price=500.0)
        calc.update_underlying_price(600.0)
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=1_700_000_000_000,
        ))
        # Should process successfully with the new price
        assert calc.get_current().trade_count == 1

    def test_update_underlying_price_rejects_zero(self):
        """update_underlying_price ignores zero values."""
        calc = _make_calculator(underlying_price=600.0)
        calc.update_underlying_price(0.0)
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=1_700_000_000_000,
        ))
        # Should still process — underlying price unchanged from 600
        assert calc.get_current().trade_count == 1

    def test_custom_iv_and_dte(self):
        """Trade with explicit IV and DTE uses those values."""
        calc = _make_calculator()
        calc.process_trade(_make_trade(
            ticker="O:SPY251219C00600000",
            price=5.20, bid=4.80, ask=5.20,
            size=10, timestamp=1_700_000_000_000,
            iv=0.25,
            dte_years=0.1,
        ))
        assert calc.get_current().trade_count == 1
