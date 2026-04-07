"""Tests for SpotGammaStore -- SpotGamma data persistence layer.

Uses in-memory SQLite for fast, isolated tests.  Covers save, get,
upsert behaviour for levels, append behaviour for HIRO, date-range
queries, cleanup, and JSON round-tripping for notes.
"""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from src.data.spotgamma_models import SpotGammaHIRO, SpotGammaLevels, SpotGammaNote
from src.data.spotgamma_store import SpotGammaStore
from src.db.store import Store


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def store():
    """Create an in-memory Store with tables initialised."""
    s = Store(db_path=":memory:")
    await s.init()
    yield s
    await s.close()


@pytest_asyncio.fixture
async def sg(store):
    """Create a SpotGammaStore backed by the in-memory Store."""
    return SpotGammaStore(store)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_levels(
    ts: datetime | None = None,
    ticker: str = "SPX",
    source: str = "manual",
    call_wall: float = 5900.0,
    put_wall: float = 5700.0,
    vol_trigger: float = 5800.0,
    hedge_wall: float = 5850.0,
    abs_gamma: float = 5825.0,
) -> SpotGammaLevels:
    return SpotGammaLevels(
        call_wall=call_wall,
        put_wall=put_wall,
        vol_trigger=vol_trigger,
        hedge_wall=hedge_wall,
        abs_gamma=abs_gamma,
        timestamp=ts or datetime(2026, 4, 6, 9, 30),
        ticker=ticker,
        source=source,
    )


def _make_hiro(
    ts: datetime | None = None,
    ticker: str = "SPX",
    hedging_impact: float = 1.5,
    cumulative_impact: float = 10.0,
) -> SpotGammaHIRO:
    return SpotGammaHIRO(
        timestamp=ts or datetime(2026, 4, 6, 10, 0),
        hedging_impact=hedging_impact,
        cumulative_impact=cumulative_impact,
        ticker=ticker,
    )


_SENTINEL_LEVELS: dict[str, float] = {"resistance_1": 5900.0, "support_1": 5700.0}


def _make_note(
    ts: datetime | None = None,
    summary: str = "Dealers are long gamma above 5800.",
    key_levels: dict[str, float] | None = None,
    outlook: str = "bullish",
    raw_text: str = "Full note text here.",
) -> SpotGammaNote:
    if key_levels is None:
        key_levels = dict(_SENTINEL_LEVELS)
    return SpotGammaNote(
        timestamp=ts or datetime(2026, 4, 6, 7, 0),
        summary=summary,
        key_levels_mentioned=key_levels,
        market_outlook=outlook,
        raw_text=raw_text,
    )


# ---------------------------------------------------------------------------
# Tests: Levels
# ---------------------------------------------------------------------------


class TestSaveLevels:
    """Tests for save_levels and get_latest_levels."""

    @pytest.mark.asyncio
    async def test_save_and_retrieve(self, sg):
        """Saving levels creates a retrievable row."""
        levels = _make_levels()
        await sg.save_levels(levels)

        result = await sg.get_latest_levels("SPX")
        assert result is not None
        assert result.call_wall == pytest.approx(5900.0)
        assert result.put_wall == pytest.approx(5700.0)
        assert result.vol_trigger == pytest.approx(5800.0)
        assert result.hedge_wall == pytest.approx(5850.0)
        assert result.abs_gamma == pytest.approx(5825.0)
        assert result.ticker == "SPX"
        assert result.source == "manual"

    @pytest.mark.asyncio
    async def test_upsert_same_date_overwrites(self, sg):
        """Second save for same date+ticker replaces the first."""
        levels1 = _make_levels(call_wall=5900.0)
        await sg.save_levels(levels1)

        levels2 = _make_levels(
            ts=datetime(2026, 4, 6, 15, 0),  # same date, later time
            call_wall=5950.0,
        )
        await sg.save_levels(levels2)

        result = await sg.get_latest_levels("SPX")
        assert result is not None
        assert result.call_wall == pytest.approx(5950.0)

    @pytest.mark.asyncio
    async def test_upsert_does_not_duplicate(self, sg):
        """Upserting same date should not create two rows."""
        await sg.save_levels(_make_levels())
        await sg.save_levels(_make_levels(
            ts=datetime(2026, 4, 6, 16, 0),
            call_wall=5999.0,
        ))

        history = await sg.get_levels_history("SPX", days=100)
        assert len(history) == 1

    @pytest.mark.asyncio
    async def test_different_dates_separate_rows(self, sg):
        """Different dates create separate rows."""
        await sg.save_levels(_make_levels(ts=datetime(2026, 4, 5, 9, 30)))
        await sg.save_levels(_make_levels(ts=datetime(2026, 4, 6, 9, 30)))

        history = await sg.get_levels_history("SPX", days=100)
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_different_tickers_separate_rows(self, sg):
        """Different tickers on the same date are separate rows."""
        await sg.save_levels(_make_levels(ticker="SPX"))
        await sg.save_levels(_make_levels(ticker="SPY"))

        spx = await sg.get_latest_levels("SPX")
        spy = await sg.get_latest_levels("SPY")
        assert spx is not None
        assert spy is not None
        assert spx.ticker == "SPX"
        assert spy.ticker == "SPY"

    @pytest.mark.asyncio
    async def test_get_latest_empty_returns_none(self, sg):
        """Empty table returns None."""
        result = await sg.get_latest_levels("SPX")
        assert result is None


class TestGetLevelsHistory:
    """Tests for get_levels_history."""

    @pytest.mark.asyncio
    async def test_returns_correct_count(self, sg):
        """History returns correct number of rows."""
        for day in range(1, 6):
            await sg.save_levels(_make_levels(
                ts=datetime(2026, 4, day, 9, 30),
            ))

        history = await sg.get_levels_history("SPX", days=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_newest_first_ordering(self, sg):
        """History is returned newest-first."""
        for day in range(1, 4):
            await sg.save_levels(_make_levels(
                ts=datetime(2026, 4, day, 9, 30),
                call_wall=5900.0 + day,
            ))

        history = await sg.get_levels_history("SPX", days=10)
        assert len(history) == 3
        # Newest first
        assert history[0].timestamp.day == 3
        assert history[-1].timestamp.day == 1

    @pytest.mark.asyncio
    async def test_empty_history(self, sg):
        """Empty table returns empty list."""
        history = await sg.get_levels_history("SPX")
        assert history == []


# ---------------------------------------------------------------------------
# Tests: HIRO
# ---------------------------------------------------------------------------


class TestSaveHIRO:
    """Tests for save_hiro and get_latest_hiro."""

    @pytest.mark.asyncio
    async def test_save_and_retrieve(self, sg):
        """Saving HIRO creates a retrievable row."""
        hiro = _make_hiro()
        await sg.save_hiro(hiro)

        result = await sg.get_latest_hiro("SPX")
        assert result is not None
        assert result.hedging_impact == pytest.approx(1.5)
        assert result.cumulative_impact == pytest.approx(10.0)
        assert result.ticker == "SPX"

    @pytest.mark.asyncio
    async def test_append_not_upsert(self, sg):
        """Same timestamp creates multiple rows (append-only)."""
        ts = datetime(2026, 4, 6, 10, 0)
        await sg.save_hiro(_make_hiro(ts=ts, hedging_impact=1.0))
        await sg.save_hiro(_make_hiro(ts=ts, hedging_impact=2.0))

        rows = await sg.get_hiro_since(
            since=datetime(2026, 4, 6, 0, 0), ticker="SPX",
        )
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_get_latest_empty_returns_none(self, sg):
        """Empty table returns None."""
        result = await sg.get_latest_hiro("SPX")
        assert result is None


class TestGetHIROSince:
    """Tests for get_hiro_since."""

    @pytest.mark.asyncio
    async def test_filters_by_time(self, sg):
        """Only rows at or after 'since' are returned."""
        base = datetime(2026, 4, 6, 9, 0)
        for i in range(5):
            await sg.save_hiro(_make_hiro(
                ts=base + timedelta(hours=i),
                hedging_impact=float(i),
            ))

        # Since 11:00 should get 11:00, 12:00, 13:00
        rows = await sg.get_hiro_since(
            since=datetime(2026, 4, 6, 11, 0), ticker="SPX",
        )
        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_oldest_first_ordering(self, sg):
        """Results are ordered oldest-first."""
        base = datetime(2026, 4, 6, 9, 0)
        for i in range(3):
            await sg.save_hiro(_make_hiro(
                ts=base + timedelta(hours=i),
                hedging_impact=float(i),
            ))

        rows = await sg.get_hiro_since(
            since=datetime(2026, 4, 6, 0, 0), ticker="SPX",
        )
        assert len(rows) == 3
        assert rows[0].hedging_impact == pytest.approx(0.0)
        assert rows[2].hedging_impact == pytest.approx(2.0)

    @pytest.mark.asyncio
    async def test_filters_by_ticker(self, sg):
        """Only rows for the requested ticker are returned."""
        ts = datetime(2026, 4, 6, 10, 0)
        await sg.save_hiro(_make_hiro(ts=ts, ticker="SPX"))
        await sg.save_hiro(_make_hiro(ts=ts, ticker="SPY"))

        rows = await sg.get_hiro_since(
            since=datetime(2026, 4, 6, 0, 0), ticker="SPX",
        )
        assert len(rows) == 1
        assert rows[0].ticker == "SPX"

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self, sg):
        """No matching rows returns empty list."""
        rows = await sg.get_hiro_since(
            since=datetime(2026, 4, 6, 0, 0), ticker="SPX",
        )
        assert rows == []


class TestCleanupOldHIRO:
    """Tests for cleanup_old_hiro."""

    @pytest.mark.asyncio
    async def test_deletes_old_rows(self, sg):
        """Rows older than the threshold are deleted."""
        old_ts = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=10)
        recent_ts = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)

        await sg.save_hiro(_make_hiro(ts=old_ts))
        await sg.save_hiro(_make_hiro(ts=recent_ts))

        deleted = await sg.cleanup_old_hiro(days=7)
        assert deleted == 1

        # Recent row should survive
        rows = await sg.get_hiro_since(
            since=datetime(2000, 1, 1), ticker="SPX",
        )
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_returns_count_deleted(self, sg):
        """Return value is the count of deleted rows."""
        old = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=20)
        for i in range(5):
            await sg.save_hiro(_make_hiro(
                ts=old + timedelta(hours=i),
            ))

        deleted = await sg.cleanup_old_hiro(days=7)
        assert deleted == 5

    @pytest.mark.asyncio
    async def test_nothing_to_delete(self, sg):
        """Returns 0 when no old rows exist."""
        recent = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        await sg.save_hiro(_make_hiro(ts=recent))

        deleted = await sg.cleanup_old_hiro(days=7)
        assert deleted == 0


# ---------------------------------------------------------------------------
# Tests: Notes
# ---------------------------------------------------------------------------


class TestSaveNote:
    """Tests for save_note and get_latest_note."""

    @pytest.mark.asyncio
    async def test_save_and_retrieve(self, sg):
        """Saving a note creates a retrievable row."""
        note = _make_note()
        await sg.save_note(note)

        result = await sg.get_latest_note()
        assert result is not None
        assert result.summary == "Dealers are long gamma above 5800."
        assert result.market_outlook == "bullish"
        assert result.raw_text == "Full note text here."

    @pytest.mark.asyncio
    async def test_key_levels_json_roundtrip(self, sg):
        """key_levels_mentioned dict survives JSON serialization."""
        key_levels = {"resistance_1": 5900.0, "support_1": 5700.0, "pivot": 5800.0}
        note = _make_note(key_levels=key_levels)
        await sg.save_note(note)

        result = await sg.get_latest_note()
        assert result is not None
        assert result.key_levels_mentioned == key_levels
        assert result.key_levels_mentioned["pivot"] == pytest.approx(5800.0)

    @pytest.mark.asyncio
    async def test_empty_key_levels(self, sg):
        """Empty key_levels_mentioned dict round-trips correctly."""
        note = _make_note(key_levels={})
        await sg.save_note(note)

        result = await sg.get_latest_note()
        assert result is not None
        assert result.key_levels_mentioned == {}

    @pytest.mark.asyncio
    async def test_upsert_same_date_overwrites(self, sg):
        """Second note for same date replaces the first."""
        await sg.save_note(_make_note(summary="Morning view"))
        await sg.save_note(_make_note(
            ts=datetime(2026, 4, 6, 12, 0),  # same date, later time
            summary="Updated midday view",
        ))

        result = await sg.get_latest_note()
        assert result is not None
        assert result.summary == "Updated midday view"

    @pytest.mark.asyncio
    async def test_get_latest_empty_returns_none(self, sg):
        """Empty table returns None."""
        result = await sg.get_latest_note()
        assert result is None

    @pytest.mark.asyncio
    async def test_latest_returns_most_recent(self, sg):
        """get_latest_note returns the note with the newest timestamp."""
        await sg.save_note(_make_note(
            ts=datetime(2026, 4, 5, 7, 0), summary="Yesterday",
        ))
        await sg.save_note(_make_note(
            ts=datetime(2026, 4, 6, 7, 0), summary="Today",
        ))

        result = await sg.get_latest_note()
        assert result is not None
        assert result.summary == "Today"


# ---------------------------------------------------------------------------
# Tests: Store not initialised
# ---------------------------------------------------------------------------


class TestStoreNotInitialised:
    """Tests for calling SpotGammaStore on an uninitialised Store."""

    @pytest.mark.asyncio
    async def test_raises_on_uninitialised_store(self):
        """SpotGammaStore raises RuntimeError if Store.init() was not called."""
        s = Store(db_path=":memory:")
        sg = SpotGammaStore(s)
        with pytest.raises(RuntimeError, match="not initialized"):
            await sg.get_latest_levels("SPX")
