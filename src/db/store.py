"""SQLite storage for SPY/SPX options analysis snapshots and alert cooldowns.

Uses aiosqlite for async database operations. Stores historical analysis
snapshots for trend detection and OI shift comparison, plus alert cooldown
tracking to prevent notification spam.

Tables:
    snapshots -- timestamped analysis results with key metrics + full JSON blob
    alert_cooldowns -- per-alert-type cooldown expiry timestamps
"""

import json
import logging
import os
from datetime import datetime, timedelta, date

import aiosqlite

from src.config import config

logger = logging.getLogger(__name__)

# Custom JSON encoder that handles date/datetime objects in AnalysisResult
class _AnalysisEncoder(json.JSONEncoder):
    """JSON encoder that handles date and datetime objects."""

    def default(self, obj: object) -> object:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def _serialize_result(result: object) -> str:
    """Serialize an AnalysisResult to a JSON string for the full_data column.

    Walks the dataclass tree using __dict__ and handles nested dataclasses,
    lists, dicts, dates, and datetimes.

    Args:
        result: An AnalysisResult (or any dataclass with nested dataclasses).

    Returns:
        JSON string representation of the result.
    """

    def _to_dict(obj: object) -> object:
        if hasattr(obj, "__dict__") and hasattr(obj, "__dataclass_fields__"):
            return {k: _to_dict(v) for k, v in obj.__dict__.items()}
        if isinstance(obj, list):
            return [_to_dict(item) for item in obj]
        if isinstance(obj, dict):
            return {str(k): _to_dict(v) for k, v in obj.items()}
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return obj

    return json.dumps(_to_dict(result), cls=_AnalysisEncoder)


class Store:
    """Async SQLite store for analysis snapshots and alert cooldowns.

    Usage:
        store = Store()
        await store.init()
        ...
        await store.close()

    Or as an async context manager is NOT implemented -- call init/close
    explicitly to match the bot's lifecycle (startup/shutdown hooks).
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or config.db_path
        self._db: aiosqlite.Connection | None = None

    async def init(self) -> None:
        """Initialize database connection and create tables.

        Creates the data/ directory if it does not exist, opens the SQLite
        connection, enables WAL mode for concurrent read performance, and
        creates tables and indexes.
        """
        # Ensure parent directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            logger.debug("Ensured database directory exists: %s", db_dir)

        self._db = await aiosqlite.connect(self.db_path)

        # WAL mode for better concurrent read performance
        await self._db.execute("PRAGMA journal_mode=WAL")

        # Create tables
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ticker TEXT NOT NULL,
                spot_price REAL NOT NULL,
                net_gex REAL,
                gamma_flip REAL,
                max_pain REAL,
                volume_pcr REAL,
                oi_pcr REAL,
                signal TEXT,
                dealer_positioning TEXT,
                squeeze_probability REAL,
                full_data TEXT
            )
        """)

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS alert_cooldowns (
                alert_type TEXT PRIMARY KEY,
                cooldown_until TEXT NOT NULL
            )
        """)

        # Strategy tables (Phase 2-1)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'idea',
                template_yaml TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS strategy_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER NOT NULL,
                from_status TEXT NOT NULL,
                to_status TEXT NOT NULL,
                reason TEXT,
                transitioned_at TEXT NOT NULL,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id)
            )
        """)

        # Signal log table (Phase 2-1)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS signal_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                ticker TEXT NOT NULL,
                direction TEXT NOT NULL DEFAULT 'neutral',
                strength REAL NOT NULL DEFAULT 0.5,
                source TEXT,
                metadata TEXT DEFAULT '{}',
                outcome TEXT,
                outcome_pnl REAL,
                outcome_updated_at TEXT
            )
        """)

        # Backtest results table (Phase 2-2)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT NOT NULL,
                run_at TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                num_trades INTEGER,
                sharpe REAL,
                sortino REAL,
                max_drawdown REAL,
                win_rate REAL,
                profit_factor REAL,
                wfa_passed INTEGER,
                cpcv_pbo REAL,
                cpcv_passed INTEGER,
                dsr REAL,
                dsr_passed INTEGER,
                mc_5th_sharpe REAL,
                mc_passed INTEGER,
                all_passed INTEGER,
                recommendation TEXT,
                full_result TEXT
            )
        """)

        # Indexes for fast lookups
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_ticker_timestamp
            ON snapshots (ticker, timestamp)
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_backtest_strategy
            ON backtest_results(strategy_id, run_at)
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_strategy_transitions_strategy_id
            ON strategy_transitions (strategy_id)
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_signal_log_ticker_type
            ON signal_log (ticker, signal_type)
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_signal_log_timestamp
            ON signal_log (timestamp)
        """)

        # Hypothesis tables (Phase 2-3)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS hypotheses (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                testable_prediction TEXT NOT NULL,
                null_hypothesis TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PROPOSED',
                proposed_by TEXT NOT NULL,
                proposed_at TEXT NOT NULL,
                test_result TEXT,
                p_value REAL,
                tested_at TEXT
            )
        """)

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS hypothesis_strategies (
                hypothesis_id TEXT NOT NULL REFERENCES hypotheses(id),
                strategy_id TEXT NOT NULL,
                PRIMARY KEY (hypothesis_id, strategy_id)
            )
        """)

        # Journal tables (Phase 2-3)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT NOT NULL DEFAULT 'system',
                created_at TEXT NOT NULL
            )
        """)

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS signal_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id INTEGER NOT NULL REFERENCES signal_log(id),
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                notes TEXT,
                rated_at TEXT NOT NULL
            )
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_journal_entries_type
            ON journal_entries (entry_type, created_at)
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_signal_ratings_signal
            ON signal_ratings (signal_id)
        """)

        await self._db.commit()
        logger.info("Database initialized at %s", self.db_path)

    async def close(self) -> None:
        """Close database connection.

        Safe to call multiple times or if the connection was never opened.
        """
        if self._db is not None:
            await self._db.close()
            self._db = None
            logger.info("Database connection closed")

    def _ensure_connected(self) -> aiosqlite.Connection:
        """Return the active database connection or raise.

        Returns:
            The active aiosqlite connection.

        Raises:
            RuntimeError: If init() has not been called or connection is closed.
        """
        if self._db is None:
            raise RuntimeError(
                "Store is not initialized. Call await store.init() first."
            )
        return self._db

    async def save_snapshot(self, result: object) -> None:
        """Save an AnalysisResult snapshot to the database.

        Extracts key metrics into individual columns for fast querying and
        stores the complete result as a JSON blob for detailed replay.

        Args:
            result: An AnalysisResult instance with .ticker, .spot_price,
                    .timestamp, .gex, .max_pain, .pcr attributes.
        """
        db = self._ensure_connected()

        try:
            # Extract fields from the AnalysisResult
            ticker: str = result.ticker  # type: ignore[attr-defined]
            spot_price: float = result.spot_price  # type: ignore[attr-defined]
            timestamp: datetime = result.timestamp  # type: ignore[attr-defined]
            gex = result.gex  # type: ignore[attr-defined]
            max_pain = result.max_pain  # type: ignore[attr-defined]
            pcr = result.pcr  # type: ignore[attr-defined]

            full_data = _serialize_result(result)

            await db.execute(
                """
                INSERT INTO snapshots (
                    timestamp, ticker, spot_price, net_gex, gamma_flip,
                    max_pain, volume_pcr, oi_pcr, signal, dealer_positioning,
                    squeeze_probability, full_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp.isoformat(),
                    ticker,
                    spot_price,
                    gex.net_gex,
                    gex.gamma_flip,
                    max_pain.max_pain_price,
                    pcr.volume_pcr,
                    pcr.oi_pcr,
                    pcr.signal,
                    pcr.dealer_positioning,
                    gex.squeeze_probability,
                    full_data,
                ),
            )
            await db.commit()

            logger.debug(
                "Saved snapshot for %s at $%.2f (%s)",
                ticker,
                spot_price,
                timestamp.isoformat(),
            )

        except AttributeError as exc:
            logger.error(
                "Failed to save snapshot -- result missing expected attribute: %s", exc
            )

        except aiosqlite.Error as exc:
            logger.error("Database error saving snapshot: %s", exc)

    async def get_latest_snapshot(self, ticker: str) -> dict | None:
        """Get the most recent snapshot for a ticker.

        Used for OI shift detection by comparing current values against the
        previous snapshot's metrics.

        Args:
            ticker: The ticker symbol (e.g. "SPY", "SPX").

        Returns:
            Dictionary with snapshot columns, or None if no snapshot exists.
            The full_data field is parsed back into a dict from JSON.
        """
        db = self._ensure_connected()

        try:
            cursor = await db.execute(
                """
                SELECT
                    id, timestamp, ticker, spot_price, net_gex, gamma_flip,
                    max_pain, volume_pcr, oi_pcr, signal, dealer_positioning,
                    squeeze_probability, full_data
                FROM snapshots
                WHERE ticker = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (ticker,),
            )
            row = await cursor.fetchone()

            if row is None:
                return None

            columns = [
                "id", "timestamp", "ticker", "spot_price", "net_gex",
                "gamma_flip", "max_pain", "volume_pcr", "oi_pcr", "signal",
                "dealer_positioning", "squeeze_probability", "full_data",
            ]
            snapshot = dict(zip(columns, row))

            # Parse full_data JSON back into a dict
            if snapshot.get("full_data"):
                try:
                    snapshot["full_data"] = json.loads(snapshot["full_data"])
                except json.JSONDecodeError:
                    logger.warning(
                        "Could not parse full_data JSON for snapshot %d",
                        snapshot["id"],
                    )

            return snapshot

        except aiosqlite.Error as exc:
            logger.error("Database error fetching latest snapshot for %s: %s", ticker, exc)
            return None

    async def check_cooldown(self, alert_type: str) -> bool:
        """Check if an alert type can fire (True = no active cooldown).

        Returns True if no cooldown exists for this alert type, or if the
        existing cooldown has expired.

        Args:
            alert_type: Identifier for the alert (e.g. "gamma_flip_SPY",
                        "squeeze_warning_SPX").

        Returns:
            True if the alert can fire, False if it is still in cooldown.
        """
        db = self._ensure_connected()

        try:
            cursor = await db.execute(
                "SELECT cooldown_until FROM alert_cooldowns WHERE alert_type = ?",
                (alert_type,),
            )
            row = await cursor.fetchone()

            if row is None:
                return True

            cooldown_until = datetime.fromisoformat(row[0])
            now = datetime.now()

            if now >= cooldown_until:
                # Cooldown expired -- clean it up
                await db.execute(
                    "DELETE FROM alert_cooldowns WHERE alert_type = ?",
                    (alert_type,),
                )
                await db.commit()
                return True

            remaining = cooldown_until - now
            logger.debug(
                "Alert %s is in cooldown for %.0f more seconds",
                alert_type,
                remaining.total_seconds(),
            )
            return False

        except aiosqlite.Error as exc:
            logger.error("Database error checking cooldown for %s: %s", alert_type, exc)
            # On error, allow the alert to fire (fail open)
            return True

    async def set_cooldown(self, alert_type: str, minutes: int | None = None) -> None:
        """Set a cooldown for an alert type.

        Uses INSERT OR REPLACE to upsert the cooldown. If the alert type
        already has a cooldown, it will be overwritten with the new expiry.

        Args:
            alert_type: Identifier for the alert.
            minutes: Cooldown duration in minutes. Uses
                     config.alert_cooldown_minutes if None.
        """
        db = self._ensure_connected()

        if minutes is None:
            minutes = config.alert_cooldown_minutes

        cooldown_until = datetime.now() + timedelta(minutes=minutes)

        try:
            await db.execute(
                """
                INSERT OR REPLACE INTO alert_cooldowns (alert_type, cooldown_until)
                VALUES (?, ?)
                """,
                (alert_type, cooldown_until.isoformat()),
            )
            await db.commit()

            logger.debug(
                "Set cooldown for %s until %s (%d minutes)",
                alert_type,
                cooldown_until.isoformat(),
                minutes,
            )

        except aiosqlite.Error as exc:
            logger.error("Database error setting cooldown for %s: %s", alert_type, exc)

    async def cleanup_old(self) -> None:
        """Delete snapshots older than config.history_retention_days.

        Also removes any expired cooldowns. This should be called periodically
        (e.g. once per day at market open) to keep the database size manageable.
        """
        db = self._ensure_connected()

        cutoff = datetime.now() - timedelta(days=config.history_retention_days)
        cutoff_iso = cutoff.isoformat()
        now_iso = datetime.now().isoformat()

        try:
            # Delete old snapshots
            cursor = await db.execute(
                "DELETE FROM snapshots WHERE timestamp < ?",
                (cutoff_iso,),
            )
            deleted_snapshots = cursor.rowcount

            # Delete expired cooldowns
            cursor = await db.execute(
                "DELETE FROM alert_cooldowns WHERE cooldown_until < ?",
                (now_iso,),
            )
            deleted_cooldowns = cursor.rowcount

            await db.commit()

            if deleted_snapshots > 0 or deleted_cooldowns > 0:
                logger.info(
                    "Cleanup: removed %d old snapshots (before %s) and %d expired cooldowns",
                    deleted_snapshots,
                    cutoff.strftime("%Y-%m-%d"),
                    deleted_cooldowns,
                )
            else:
                logger.debug("Cleanup: nothing to remove")

        except aiosqlite.Error as exc:
            logger.error("Database error during cleanup: %s", exc)
