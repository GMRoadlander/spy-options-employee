"""Tests for SpotGamma data models and database schema.

Covers dataclass construction, default values, type correctness,
and the migration-created tables in the Store.
"""

from datetime import datetime

import pytest
import pytest_asyncio

from src.data.spotgamma_models import SpotGammaLevels, SpotGammaHIRO, SpotGammaNote
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


# ---------------------------------------------------------------------------
# Tests: SpotGammaLevels
# ---------------------------------------------------------------------------


class TestSpotGammaLevels:
    """Tests for SpotGammaLevels dataclass."""

    def test_construct_with_all_fields(self):
        """All fields can be explicitly provided."""
        ts = datetime(2026, 4, 6, 9, 30, 0)
        levels = SpotGammaLevels(
            call_wall=5300.0,
            put_wall=5100.0,
            vol_trigger=5200.0,
            hedge_wall=5250.0,
            abs_gamma=5225.0,
            timestamp=ts,
            ticker="SPX",
            source="api",
        )
        assert levels.call_wall == 5300.0
        assert levels.put_wall == 5100.0
        assert levels.vol_trigger == 5200.0
        assert levels.hedge_wall == 5250.0
        assert levels.abs_gamma == 5225.0
        assert levels.timestamp == ts
        assert levels.ticker == "SPX"
        assert levels.source == "api"

    def test_default_ticker_and_source(self):
        """Ticker defaults to 'SPX' and source to 'manual'."""
        levels = SpotGammaLevels(
            call_wall=5300.0,
            put_wall=5100.0,
            vol_trigger=5200.0,
            hedge_wall=5250.0,
            abs_gamma=5225.0,
            timestamp=datetime.now(),
        )
        assert levels.ticker == "SPX"
        assert levels.source == "manual"

    def test_field_types(self):
        """Fields have the expected types."""
        levels = SpotGammaLevels(
            call_wall=5300.0,
            put_wall=5100.0,
            vol_trigger=5200.0,
            hedge_wall=5250.0,
            abs_gamma=5225.0,
            timestamp=datetime.now(),
        )
        assert isinstance(levels.call_wall, float)
        assert isinstance(levels.put_wall, float)
        assert isinstance(levels.vol_trigger, float)
        assert isinstance(levels.hedge_wall, float)
        assert isinstance(levels.abs_gamma, float)
        assert isinstance(levels.timestamp, datetime)
        assert isinstance(levels.ticker, str)
        assert isinstance(levels.source, str)


# ---------------------------------------------------------------------------
# Tests: SpotGammaHIRO
# ---------------------------------------------------------------------------


class TestSpotGammaHIRO:
    """Tests for SpotGammaHIRO dataclass."""

    def test_construct_with_all_fields(self):
        """All fields can be explicitly provided."""
        ts = datetime(2026, 4, 6, 10, 15, 0)
        hiro = SpotGammaHIRO(
            timestamp=ts,
            hedging_impact=1250.5,
            cumulative_impact=8400.0,
            ticker="SPX",
            source="api",
        )
        assert hiro.timestamp == ts
        assert hiro.hedging_impact == 1250.5
        assert hiro.cumulative_impact == 8400.0
        assert hiro.ticker == "SPX"
        assert hiro.source == "api"

    def test_default_ticker_and_source(self):
        """Ticker defaults to 'SPX' and source to 'api'."""
        hiro = SpotGammaHIRO(
            timestamp=datetime.now(),
            hedging_impact=-500.0,
            cumulative_impact=-1200.0,
        )
        assert hiro.ticker == "SPX"
        assert hiro.source == "api"

    def test_negative_hedging_impact(self):
        """Negative hedging_impact represents bearish pressure."""
        hiro = SpotGammaHIRO(
            timestamp=datetime.now(),
            hedging_impact=-750.0,
            cumulative_impact=-3000.0,
        )
        assert hiro.hedging_impact < 0
        assert hiro.cumulative_impact < 0

    def test_field_types(self):
        """Fields have the expected types."""
        hiro = SpotGammaHIRO(
            timestamp=datetime.now(),
            hedging_impact=100.0,
            cumulative_impact=500.0,
        )
        assert isinstance(hiro.timestamp, datetime)
        assert isinstance(hiro.hedging_impact, float)
        assert isinstance(hiro.cumulative_impact, float)
        assert isinstance(hiro.ticker, str)
        assert isinstance(hiro.source, str)


# ---------------------------------------------------------------------------
# Tests: SpotGammaNote
# ---------------------------------------------------------------------------


class TestSpotGammaNote:
    """Tests for SpotGammaNote dataclass."""

    def test_construct_with_all_fields(self):
        """All fields can be explicitly provided."""
        ts = datetime(2026, 4, 6, 7, 0, 0)
        note = SpotGammaNote(
            timestamp=ts,
            summary="Markets expected to consolidate around 5200 vol trigger.",
            key_levels_mentioned={"resistance_1": 5300.0, "support_1": 5100.0},
            market_outlook="neutral",
            raw_text="Full note text here...",
        )
        assert note.timestamp == ts
        assert note.summary == "Markets expected to consolidate around 5200 vol trigger."
        assert note.key_levels_mentioned == {"resistance_1": 5300.0, "support_1": 5100.0}
        assert note.market_outlook == "neutral"
        assert note.raw_text == "Full note text here..."

    def test_default_values(self):
        """key_levels_mentioned defaults to empty dict, outlook to neutral, raw_text to empty."""
        note = SpotGammaNote(
            timestamp=datetime.now(),
            summary="Short summary.",
        )
        assert note.key_levels_mentioned == {}
        assert note.market_outlook == "neutral"
        assert note.raw_text == ""

    def test_default_dict_is_independent(self):
        """Each instance gets its own default dict (no shared mutable default)."""
        note_a = SpotGammaNote(timestamp=datetime.now(), summary="A")
        note_b = SpotGammaNote(timestamp=datetime.now(), summary="B")
        note_a.key_levels_mentioned["key"] = 999.0
        assert "key" not in note_b.key_levels_mentioned

    def test_field_types(self):
        """Fields have the expected types."""
        note = SpotGammaNote(
            timestamp=datetime.now(),
            summary="Summary",
            key_levels_mentioned={"level": 5200.0},
            market_outlook="bullish",
            raw_text="Raw text",
        )
        assert isinstance(note.timestamp, datetime)
        assert isinstance(note.summary, str)
        assert isinstance(note.key_levels_mentioned, dict)
        assert isinstance(note.market_outlook, str)
        assert isinstance(note.raw_text, str)

    def test_market_outlook_values(self):
        """Outlook can be set to bullish, bearish, or neutral."""
        for outlook in ("bullish", "bearish", "neutral"):
            note = SpotGammaNote(
                timestamp=datetime.now(),
                summary="Test",
                market_outlook=outlook,
            )
            assert note.market_outlook == outlook


# ---------------------------------------------------------------------------
# Tests: Database schema (migration creates tables)
# ---------------------------------------------------------------------------


class TestSpotGammaSchema:
    """Verify that Store migrations create the SpotGamma tables."""

    @pytest.mark.asyncio
    async def test_spotgamma_levels_table_exists(self, store):
        """Migration creates the spotgamma_levels table."""
        cursor = await store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='spotgamma_levels'"
        )
        row = await cursor.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_spotgamma_hiro_table_exists(self, store):
        """Migration creates the spotgamma_hiro table."""
        cursor = await store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='spotgamma_hiro'"
        )
        row = await cursor.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_spotgamma_notes_table_exists(self, store):
        """Migration creates the spotgamma_notes table."""
        cursor = await store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='spotgamma_notes'"
        )
        row = await cursor.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_insert_and_read_levels(self, store):
        """Can insert and read back a spotgamma_levels row."""
        db = store.connection
        await db.execute(
            "INSERT INTO spotgamma_levels (timestamp, ticker, call_wall, put_wall, "
            "vol_trigger, hedge_wall, abs_gamma, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("2026-04-06T09:30:00", "SPX", 5300.0, 5100.0, 5200.0, 5250.0, 5225.0, "manual"),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM spotgamma_levels WHERE ticker = 'SPX'")
        row = await cursor.fetchone()
        assert row is not None
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        assert data["call_wall"] == 5300.0
        assert data["put_wall"] == 5100.0
        assert data["vol_trigger"] == 5200.0

    @pytest.mark.asyncio
    async def test_insert_and_read_hiro(self, store):
        """Can insert and read back a spotgamma_hiro row (append-only)."""
        db = store.connection
        for i in range(3):
            await db.execute(
                "INSERT INTO spotgamma_hiro (timestamp, ticker, hedging_impact, "
                "cumulative_impact, source) VALUES (?, ?, ?, ?, ?)",
                (f"2026-04-06T10:{i:02d}:00", "SPX", 100.0 * (i + 1), 100.0 * (i + 1), "api"),
            )
        await db.commit()

        cursor = await db.execute("SELECT COUNT(*) FROM spotgamma_hiro")
        row = await cursor.fetchone()
        assert row[0] == 3  # all three appended, no upsert

    @pytest.mark.asyncio
    async def test_insert_and_read_notes(self, store):
        """Can insert and read back a spotgamma_notes row."""
        db = store.connection
        import json

        levels = json.dumps({"resistance": 5300.0, "support": 5100.0})
        await db.execute(
            "INSERT INTO spotgamma_notes (timestamp, summary, key_levels_mentioned, "
            "market_outlook, raw_text) VALUES (?, ?, ?, ?, ?)",
            ("2026-04-06T07:00:00", "Markets consolidating", levels, "neutral", "Full text..."),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM spotgamma_notes LIMIT 1")
        row = await cursor.fetchone()
        assert row is not None
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        assert data["summary"] == "Markets consolidating"
        assert data["market_outlook"] == "neutral"
        parsed_levels = json.loads(data["key_levels_mentioned"])
        assert parsed_levels["resistance"] == 5300.0

    @pytest.mark.asyncio
    async def test_schema_version_updated(self, store):
        """Migrations update the schema_version table to v8."""
        cursor = await store.connection.execute("SELECT MAX(version) FROM schema_version")
        row = await cursor.fetchone()
        assert row[0] >= 8
