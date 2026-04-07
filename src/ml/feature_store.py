"""Feature store for persisting daily computed ML features.

Provides CRUD operations over the ``daily_features`` SQLite table that
is created by :class:`src.db.store.Store`.  Each row represents a
single ticker on a single date with nullable columns for every Phase 3
feature.  Features are populated incrementally as individual ML models
come online.

Usage::

    store = Store()
    await store.init()
    fs = FeatureStore(store)
    await fs.save_features("SPX", "2024-06-15", {"iv_rank": 72.3, "skew_25d": 4.1})
    latest = await fs.get_latest_features("SPX")
"""

import logging
from datetime import datetime

import aiosqlite

from src.db.store import Store
from src.utils import now_et

logger = logging.getLogger(__name__)

# All feature columns in the daily_features table (excluding id, date,
# ticker, computed_at which are metadata).
FEATURE_COLUMNS: list[str] = [
    "iv_rank",
    "iv_percentile",
    "skew_25d",
    "term_structure_slope",
    "rv_iv_spread",
    "hurst_exponent",
    "net_gex",
    "volume_pcr",
    "oi_pcr",
    "regime_state",
    "regime_probability",
    "vol_forecast_1d",
    "vol_forecast_5d",
    "sentiment_score",
    "anomaly_score",
    # SpotGamma-derived features (Step 12)
    "sg_vol_trigger",
    "sg_call_wall",
    "sg_put_wall",
    "sg_abs_gamma",
    "sg_hiro_eod",
    "diy_hiro_eod",
    "gex_sg_agreement",
]


class FeatureStore:
    """Async CRUD wrapper for the ``daily_features`` table.

    Follows the same connection pattern as :class:`src.db.store.Store` —
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

    async def save_features(
        self,
        ticker: str,
        date: str,
        features: dict[str, float | int | None],
    ) -> None:
        """Upsert a row of features for a ticker/date combination.

        Uses ``INSERT INTO ... ON CONFLICT(date, ticker) DO UPDATE SET``
        so that only the explicitly provided (non-None) feature columns
        are written.  Columns managed by other ML models are left
        untouched on conflict.

        Args:
            ticker: Ticker symbol (e.g. ``"SPX"``).
            date: ISO-format date string (``"YYYY-MM-DD"``).
            features: Mapping of column name to value.  Keys must be
                valid feature column names.  Only non-None values are
                written on conflict.
        """
        db = self._get_db()

        # Only include columns explicitly provided with non-None values.
        provided = {
            k: v for k, v in features.items()
            if k in FEATURE_COLUMNS and v is not None
        }

        if not provided:
            logger.debug("No non-None features provided for %s on %s — skipping", ticker, date)
            return

        computed_at = now_et().isoformat()

        # Build INSERT columns: metadata + provided features.
        insert_cols = ["date", "ticker", "computed_at"] + list(provided.keys())
        insert_vals: list[object] = [date, ticker, computed_at] + list(provided.values())
        columns_str = ", ".join(insert_cols)
        placeholders = ", ".join(["?"] * len(insert_vals))

        # ON CONFLICT: only update the provided feature columns + computed_at.
        update_parts = ["computed_at = excluded.computed_at"]
        for col in provided:
            update_parts.append(f"{col} = excluded.{col}")
        update_clause = ", ".join(update_parts)

        sql = (
            f"INSERT INTO daily_features ({columns_str}) VALUES ({placeholders}) "
            f"ON CONFLICT(date, ticker) DO UPDATE SET {update_clause}"
        )

        try:
            await db.execute(sql, tuple(insert_vals))
            await db.commit()
            logger.debug("Saved features for %s on %s", ticker, date)
        except aiosqlite.Error as exc:
            logger.error("Error saving features for %s on %s: %s", ticker, date, exc)

    async def get_features(self, ticker: str, date: str) -> dict[str, float | int | None] | None:
        """Retrieve the feature row for a specific ticker and date.

        Args:
            ticker: Ticker symbol.
            date: ISO-format date string.

        Returns:
            Dict mapping feature column names to values, or ``None``
            if no row exists.
        """
        db = self._get_db()

        try:
            cursor = await db.execute(
                "SELECT * FROM daily_features WHERE ticker = ? AND date = ?",
                (ticker, date),
            )
            row = await cursor.fetchone()

            if row is None:
                return None

            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

        except aiosqlite.Error as exc:
            logger.error("Error getting features for %s on %s: %s", ticker, date, exc)
            return None

    async def get_feature_history(
        self,
        ticker: str,
        feature_name: str,
        days: int = 252,
    ) -> list[tuple[str, float | None]]:
        """Retrieve a time series of a single feature for a ticker.

        Returns the most recent *days* entries ordered chronologically
        (oldest first).

        Args:
            ticker: Ticker symbol.
            feature_name: Column name of the feature (must be in
                :data:`FEATURE_COLUMNS`).
            days: Maximum number of data points to return.

        Returns:
            List of ``(date, value)`` tuples ordered oldest-first.
            Returns an empty list on error or if the feature name is
            invalid.
        """
        if feature_name not in FEATURE_COLUMNS:
            logger.warning("Invalid feature name: %s", feature_name)
            return []

        db = self._get_db()

        try:
            cursor = await db.execute(
                f"""
                SELECT date, {feature_name}
                FROM daily_features
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (ticker, days),
            )
            rows = await cursor.fetchall()

            # Reverse to chronological order (oldest first)
            return [(row[0], row[1]) for row in reversed(rows)]

        except aiosqlite.Error as exc:
            logger.error(
                "Error getting feature history for %s/%s: %s",
                ticker,
                feature_name,
                exc,
            )
            return []

    async def get_latest_features(self, ticker: str) -> dict[str, float | int | None] | None:
        """Retrieve the most recent feature row for a ticker.

        Args:
            ticker: Ticker symbol.

        Returns:
            Dict mapping feature column names to values, or ``None``
            if no rows exist for this ticker.
        """
        db = self._get_db()

        try:
            cursor = await db.execute(
                "SELECT * FROM daily_features WHERE ticker = ? ORDER BY date DESC LIMIT 1",
                (ticker,),
            )
            row = await cursor.fetchone()

            if row is None:
                return None

            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

        except aiosqlite.Error as exc:
            logger.error("Error getting latest features for %s: %s", ticker, exc)
            return None
