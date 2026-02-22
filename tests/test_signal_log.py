"""Tests for SignalLogger -- signal logging and statistics.

Uses in-memory SQLite for fast, isolated tests. Covers logging,
outcome tracking, querying, and statistics.
"""

import pytest
import pytest_asyncio
import aiosqlite
from datetime import datetime, timedelta

from src.db.signal_log import SignalEvent, SignalLogger


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db():
    """Create an in-memory SQLite database for testing."""
    conn = await aiosqlite.connect(":memory:")
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def logger(db):
    """Create a SignalLogger with initialized table."""
    sl = SignalLogger(db)
    await sl.init_table()
    return sl


# ---------------------------------------------------------------------------
# Tests: SignalEvent dataclass
# ---------------------------------------------------------------------------


class TestSignalEvent:
    """Tests for the SignalEvent dataclass."""

    def test_defaults(self):
        """SignalEvent has sensible defaults."""
        event = SignalEvent(signal_type="test", ticker="SPY")
        assert event.direction == "neutral"
        assert event.strength == 0.5
        assert event.source == ""
        assert event.metadata == {}
        assert event.timestamp is not None

    def test_auto_timestamp(self):
        """Timestamp is auto-filled when None."""
        event = SignalEvent(signal_type="test", ticker="SPY")
        assert isinstance(event.timestamp, datetime)

    def test_explicit_timestamp(self):
        """Explicit timestamp is preserved."""
        ts = datetime(2024, 1, 15, 10, 30)
        event = SignalEvent(signal_type="test", ticker="SPY", timestamp=ts)
        assert event.timestamp == ts


# ---------------------------------------------------------------------------
# Tests: Logging signals
# ---------------------------------------------------------------------------


class TestLogSignal:
    """Tests for log_signal method."""

    @pytest.mark.asyncio
    async def test_log_basic_signal(self, logger):
        """Basic signal logging returns an ID."""
        event = SignalEvent(
            signal_type="gamma_flip",
            ticker="SPY",
            direction="bearish",
            strength=0.8,
            source="cog_alerts",
        )
        signal_id = await logger.log_signal(event)
        assert signal_id > 0

    @pytest.mark.asyncio
    async def test_log_with_metadata(self, logger):
        """Metadata dict is stored and retrievable."""
        event = SignalEvent(
            signal_type="flow",
            ticker="SPX",
            metadata={"strike": 4800, "premium": 250000},
        )
        signal_id = await logger.log_signal(event)
        signals = await logger.get_signals(ticker="SPX")
        assert signals[0]["metadata"]["strike"] == 4800


# ---------------------------------------------------------------------------
# Tests: Outcome tracking
# ---------------------------------------------------------------------------


class TestOutcomeTracking:
    """Tests for update_outcome method."""

    @pytest.mark.asyncio
    async def test_update_outcome(self, logger):
        """Outcome and PnL are recorded."""
        event = SignalEvent(signal_type="squeeze", ticker="SPY")
        signal_id = await logger.log_signal(event)

        await logger.update_outcome(signal_id, "win", pnl=150.0)

        signals = await logger.get_signals(ticker="SPY")
        assert signals[0]["outcome"] == "win"
        assert signals[0]["outcome_pnl"] == 150.0

    @pytest.mark.asyncio
    async def test_update_outcome_no_pnl(self, logger):
        """Outcome without PnL is valid."""
        event = SignalEvent(signal_type="test", ticker="SPY")
        signal_id = await logger.log_signal(event)

        await logger.update_outcome(signal_id, "expired")

        signals = await logger.get_signals(ticker="SPY")
        assert signals[0]["outcome"] == "expired"
        assert signals[0]["outcome_pnl"] is None


# ---------------------------------------------------------------------------
# Tests: Querying signals
# ---------------------------------------------------------------------------


class TestGetSignals:
    """Tests for get_signals method."""

    @pytest.mark.asyncio
    async def test_filter_by_ticker(self, logger):
        """Filtering by ticker returns only matching signals."""
        await logger.log_signal(SignalEvent(signal_type="test", ticker="SPY"))
        await logger.log_signal(SignalEvent(signal_type="test", ticker="SPX"))

        spy_signals = await logger.get_signals(ticker="SPY")
        assert len(spy_signals) == 1
        assert spy_signals[0]["ticker"] == "SPY"

    @pytest.mark.asyncio
    async def test_filter_by_type(self, logger):
        """Filtering by signal_type returns only matching signals."""
        await logger.log_signal(SignalEvent(signal_type="gamma_flip", ticker="SPY"))
        await logger.log_signal(SignalEvent(signal_type="squeeze", ticker="SPY"))

        gamma_signals = await logger.get_signals(signal_type="gamma_flip")
        assert len(gamma_signals) == 1
        assert gamma_signals[0]["signal_type"] == "gamma_flip"

    @pytest.mark.asyncio
    async def test_limit(self, logger):
        """Limit parameter caps the number of results."""
        for i in range(10):
            await logger.log_signal(SignalEvent(signal_type="test", ticker="SPY"))

        signals = await logger.get_signals(limit=3)
        assert len(signals) == 3

    @pytest.mark.asyncio
    async def test_since_filter(self, logger):
        """Since filter returns only signals after the timestamp."""
        old_event = SignalEvent(
            signal_type="test", ticker="SPY",
            timestamp=datetime(2024, 1, 1),
        )
        new_event = SignalEvent(
            signal_type="test", ticker="SPY",
            timestamp=datetime(2024, 6, 1),
        )
        await logger.log_signal(old_event)
        await logger.log_signal(new_event)

        signals = await logger.get_signals(since=datetime(2024, 3, 1))
        assert len(signals) == 1


# ---------------------------------------------------------------------------
# Tests: Statistics
# ---------------------------------------------------------------------------


class TestSignalStats:
    """Tests for get_signal_stats method."""

    @pytest.mark.asyncio
    async def test_basic_stats(self, logger):
        """Stats reflect logged signals."""
        await logger.log_signal(SignalEvent(signal_type="gamma_flip", ticker="SPY", direction="bearish"))
        await logger.log_signal(SignalEvent(signal_type="squeeze", ticker="SPY", direction="bullish"))
        await logger.log_signal(SignalEvent(signal_type="gamma_flip", ticker="SPX", direction="bearish"))

        stats = await logger.get_signal_stats()
        assert stats["total_signals"] == 3
        assert stats["by_type"]["gamma_flip"] == 2
        assert stats["by_type"]["squeeze"] == 1
        assert stats["by_direction"]["bearish"] == 2
        assert stats["by_direction"]["bullish"] == 1

    @pytest.mark.asyncio
    async def test_stats_with_ticker_filter(self, logger):
        """Stats respect ticker filter."""
        await logger.log_signal(SignalEvent(signal_type="test", ticker="SPY"))
        await logger.log_signal(SignalEvent(signal_type="test", ticker="SPX"))

        stats = await logger.get_signal_stats(ticker="SPY")
        assert stats["total_signals"] == 1
