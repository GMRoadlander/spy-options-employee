"""Repository layer for SpotGamma data (levels, HIRO, notes).

Provides async CRUD operations over the ``spotgamma_levels``,
``spotgamma_hiro``, and ``spotgamma_notes`` SQLite tables created
by :class:`src.db.store.Store`.

Usage::

    store = Store()
    await store.init()
    sg = SpotGammaStore(store)
    await sg.save_levels(levels)
    latest = await sg.get_latest_levels("SPX")
"""

import json
import logging
from datetime import datetime

import aiosqlite

from src.data.spotgamma_models import SpotGammaHIRO, SpotGammaLevels, SpotGammaNote
from src.db.store import Store

logger = logging.getLogger(__name__)


class SpotGammaStore:
    """Async CRUD wrapper for the SpotGamma tables.

    Follows the same connection pattern as :class:`src.ml.feature_store.FeatureStore` --
    call ``Store.init()`` first, then pass the store instance here.

    Args:
        store: An initialised :class:`Store` instance.
    """

    def __init__(self, store: Store) -> None:
        self._store = store

    def _get_db(self) -> aiosqlite.Connection:
        """Return the active database connection from the underlying Store.

        Raises:
            RuntimeError: If the Store has not been initialised.
        """
        return self._store._ensure_connected()

    # ------------------------------------------------------------------
    # Levels CRUD
    # ------------------------------------------------------------------

    async def save_levels(self, levels: SpotGammaLevels) -> None:
        """Upsert daily SpotGamma levels (replace if same date + ticker).

        Uses the date portion of ``levels.timestamp`` and ``levels.ticker``
        as the conflict key.  If a row already exists for that combination
        the entire row is replaced.

        Args:
            levels: A :class:`SpotGammaLevels` instance to persist.
        """
        db = self._get_db()

        ts_iso = levels.timestamp.isoformat()
        date_str = levels.timestamp.strftime("%Y-%m-%d")

        try:
            # Delete any existing row for same date + ticker, then insert.
            # This implements upsert semantics without needing a UNIQUE
            # constraint on (date, ticker) in the migration.
            await db.execute(
                "DELETE FROM spotgamma_levels "
                "WHERE ticker = ? AND DATE(timestamp) = ?",
                (levels.ticker, date_str),
            )
            await db.execute(
                "INSERT INTO spotgamma_levels "
                "(timestamp, ticker, call_wall, put_wall, vol_trigger, "
                "hedge_wall, abs_gamma, source) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ts_iso,
                    levels.ticker,
                    levels.call_wall,
                    levels.put_wall,
                    levels.vol_trigger,
                    levels.hedge_wall,
                    levels.abs_gamma,
                    levels.source,
                ),
            )
            await db.commit()
            logger.debug(
                "Saved SpotGamma levels for %s on %s", levels.ticker, date_str,
            )
        except aiosqlite.Error as exc:
            logger.error("Error saving SpotGamma levels: %s", exc)

    async def get_latest_levels(self, ticker: str = "SPX") -> SpotGammaLevels | None:
        """Retrieve the most recent SpotGamma levels for a ticker.

        Args:
            ticker: Underlying symbol (default ``"SPX"``).

        Returns:
            A :class:`SpotGammaLevels` instance or ``None`` if no data exists.
        """
        db = self._get_db()

        try:
            cursor = await db.execute(
                "SELECT timestamp, ticker, call_wall, put_wall, vol_trigger, "
                "hedge_wall, abs_gamma, source "
                "FROM spotgamma_levels "
                "WHERE ticker = ? "
                "ORDER BY timestamp DESC LIMIT 1",
                (ticker,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return self._row_to_levels(row)
        except aiosqlite.Error as exc:
            logger.error("Error getting latest SpotGamma levels for %s: %s", ticker, exc)
            return None

    async def get_levels_history(
        self, ticker: str = "SPX", days: int = 30,
    ) -> list[SpotGammaLevels]:
        """Retrieve recent SpotGamma levels history.

        Returns up to *days* rows ordered newest-first.

        Args:
            ticker: Underlying symbol (default ``"SPX"``).
            days: Maximum number of rows to return.

        Returns:
            List of :class:`SpotGammaLevels` instances, newest first.
        """
        db = self._get_db()

        try:
            cursor = await db.execute(
                "SELECT timestamp, ticker, call_wall, put_wall, vol_trigger, "
                "hedge_wall, abs_gamma, source "
                "FROM spotgamma_levels "
                "WHERE ticker = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (ticker, days),
            )
            rows = await cursor.fetchall()
            return [self._row_to_levels(r) for r in rows]
        except aiosqlite.Error as exc:
            logger.error("Error getting SpotGamma levels history: %s", exc)
            return []

    @staticmethod
    def _row_to_levels(row: tuple) -> SpotGammaLevels:
        """Convert a database row to a SpotGammaLevels dataclass."""
        return SpotGammaLevels(
            timestamp=datetime.fromisoformat(row[0]),
            ticker=row[1],
            call_wall=row[2],
            put_wall=row[3],
            vol_trigger=row[4],
            hedge_wall=row[5],
            abs_gamma=row[6],
            source=row[7],
        )

    # ------------------------------------------------------------------
    # HIRO CRUD
    # ------------------------------------------------------------------

    async def save_hiro(self, hiro: SpotGammaHIRO) -> None:
        """Append a HIRO snapshot (time-series, NOT upsert).

        Each call creates a new row regardless of whether a row with
        the same timestamp already exists.

        Args:
            hiro: A :class:`SpotGammaHIRO` instance to persist.
        """
        db = self._get_db()

        try:
            await db.execute(
                "INSERT INTO spotgamma_hiro "
                "(timestamp, ticker, hedging_impact, cumulative_impact, source) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    hiro.timestamp.isoformat(),
                    hiro.ticker,
                    hiro.hedging_impact,
                    hiro.cumulative_impact,
                    hiro.source,
                ),
            )
            await db.commit()
            logger.debug(
                "Saved HIRO snapshot for %s at %s",
                hiro.ticker,
                hiro.timestamp.isoformat(),
            )
        except aiosqlite.Error as exc:
            logger.error("Error saving HIRO snapshot: %s", exc)

    async def get_latest_hiro(self, ticker: str = "SPX") -> SpotGammaHIRO | None:
        """Retrieve the most recent HIRO snapshot for a ticker.

        Args:
            ticker: Underlying symbol (default ``"SPX"``).

        Returns:
            A :class:`SpotGammaHIRO` instance or ``None`` if no data exists.
        """
        db = self._get_db()

        try:
            cursor = await db.execute(
                "SELECT timestamp, ticker, hedging_impact, cumulative_impact, source "
                "FROM spotgamma_hiro "
                "WHERE ticker = ? "
                "ORDER BY timestamp DESC LIMIT 1",
                (ticker,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return self._row_to_hiro(row)
        except aiosqlite.Error as exc:
            logger.error("Error getting latest HIRO for %s: %s", ticker, exc)
            return None

    async def get_hiro_since(
        self, since: datetime, ticker: str = "SPX",
    ) -> list[SpotGammaHIRO]:
        """Retrieve HIRO snapshots since a given timestamp.

        Args:
            since: Only return rows at or after this time.
            ticker: Underlying symbol (default ``"SPX"``).

        Returns:
            List of :class:`SpotGammaHIRO` instances, oldest first.
        """
        db = self._get_db()

        try:
            cursor = await db.execute(
                "SELECT timestamp, ticker, hedging_impact, cumulative_impact, source "
                "FROM spotgamma_hiro "
                "WHERE ticker = ? AND timestamp >= ? "
                "ORDER BY timestamp ASC",
                (ticker, since.isoformat()),
            )
            rows = await cursor.fetchall()
            return [self._row_to_hiro(r) for r in rows]
        except aiosqlite.Error as exc:
            logger.error("Error getting HIRO since %s: %s", since.isoformat(), exc)
            return []

    async def cleanup_old_hiro(self, days: int = 7) -> int:
        """Delete HIRO rows older than *days* days.

        Args:
            days: Age threshold in days.  Rows with a timestamp older
                  than ``now - days`` are deleted.

        Returns:
            Number of rows deleted.
        """
        db = self._get_db()

        from datetime import timedelta, timezone

        cutoff = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=None,
        )
        cutoff = cutoff - timedelta(days=days)

        try:
            cursor = await db.execute(
                "DELETE FROM spotgamma_hiro WHERE timestamp < ?",
                (cutoff.isoformat(),),
            )
            deleted = cursor.rowcount
            await db.commit()
            if deleted:
                logger.info("Cleaned up %d old HIRO rows (before %s)", deleted, cutoff.isoformat())
            return deleted
        except aiosqlite.Error as exc:
            logger.error("Error cleaning up old HIRO data: %s", exc)
            return 0

    @staticmethod
    def _row_to_hiro(row: tuple) -> SpotGammaHIRO:
        """Convert a database row to a SpotGammaHIRO dataclass."""
        return SpotGammaHIRO(
            timestamp=datetime.fromisoformat(row[0]),
            ticker=row[1],
            hedging_impact=row[2],
            cumulative_impact=row[3],
            source=row[4],
        )

    # ------------------------------------------------------------------
    # Notes CRUD
    # ------------------------------------------------------------------

    async def save_note(self, note: SpotGammaNote) -> None:
        """Upsert a daily SpotGamma founder's note (replace if same date).

        Uses the date portion of ``note.timestamp`` as the conflict key.

        Args:
            note: A :class:`SpotGammaNote` instance to persist.
        """
        db = self._get_db()

        ts_iso = note.timestamp.isoformat()
        date_str = note.timestamp.strftime("%Y-%m-%d")
        key_levels_json = json.dumps(note.key_levels_mentioned)

        try:
            # Delete existing note for same date, then insert.
            await db.execute(
                "DELETE FROM spotgamma_notes WHERE DATE(timestamp) = ?",
                (date_str,),
            )
            await db.execute(
                "INSERT INTO spotgamma_notes "
                "(timestamp, summary, key_levels_mentioned, market_outlook, raw_text) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    ts_iso,
                    note.summary,
                    key_levels_json,
                    note.market_outlook,
                    note.raw_text,
                ),
            )
            await db.commit()
            logger.debug("Saved SpotGamma note for %s", date_str)
        except aiosqlite.Error as exc:
            logger.error("Error saving SpotGamma note: %s", exc)

    async def get_latest_note(self) -> SpotGammaNote | None:
        """Retrieve the most recent SpotGamma founder's note.

        Returns:
            A :class:`SpotGammaNote` instance or ``None`` if no notes exist.
        """
        db = self._get_db()

        try:
            cursor = await db.execute(
                "SELECT timestamp, summary, key_levels_mentioned, "
                "market_outlook, raw_text "
                "FROM spotgamma_notes "
                "ORDER BY timestamp DESC LIMIT 1",
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return self._row_to_note(row)
        except aiosqlite.Error as exc:
            logger.error("Error getting latest SpotGamma note: %s", exc)
            return None

    @staticmethod
    def _row_to_note(row: tuple) -> SpotGammaNote:
        """Convert a database row to a SpotGammaNote dataclass."""
        key_levels: dict[str, float] = {}
        if row[2]:
            try:
                key_levels = json.loads(row[2])
            except json.JSONDecodeError:
                logger.warning("Could not parse key_levels_mentioned JSON")

        return SpotGammaNote(
            timestamp=datetime.fromisoformat(row[0]),
            summary=row[1],
            key_levels_mentioned=key_levels,
            market_outlook=row[3],
            raw_text=row[4],
        )


__all__ = ["SpotGammaStore"]
