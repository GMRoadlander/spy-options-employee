"""Strategy lifecycle state machine with SQLite persistence.

Manages strategy states from IDEA through PAPER to RETIRED, enforcing
valid transitions and recording transition history. Backed by the
shared Store's SQLite database.

State machine:
    IDEA -> DEFINED -> BACKTEST -> PAPER -> RETIRED
    (Any state can transition directly to RETIRED)

Tables (added to Store.init()):
    strategies -- current strategy state and metadata
    strategy_transitions -- audit log of all state changes
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any

import aiosqlite
from src.utils import now_et

logger = logging.getLogger(__name__)


class StrategyStatus(str, Enum):
    """Strategy lifecycle states."""

    IDEA = "idea"
    DEFINED = "defined"
    BACKTEST = "backtest"
    PAPER = "paper"
    RETIRED = "retired"


# Valid state transitions (from -> set of allowed to states)
VALID_TRANSITIONS: dict[StrategyStatus, set[StrategyStatus]] = {
    StrategyStatus.IDEA: {StrategyStatus.DEFINED, StrategyStatus.RETIRED},
    StrategyStatus.DEFINED: {StrategyStatus.BACKTEST, StrategyStatus.RETIRED},
    StrategyStatus.BACKTEST: {StrategyStatus.PAPER, StrategyStatus.DEFINED, StrategyStatus.RETIRED},
    StrategyStatus.PAPER: {StrategyStatus.BACKTEST, StrategyStatus.RETIRED},
    StrategyStatus.RETIRED: set(),  # terminal state
}


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


class StrategyNotFoundError(Exception):
    """Raised when a strategy ID is not found."""


class StrategyManager:
    """Manages strategy lifecycle with SQLite persistence.

    Requires a shared aiosqlite connection (from Store). Call init_tables()
    to create the required tables, or let Store.init() handle it.

    Usage:
        manager = StrategyManager(db)
        strategy_id = await manager.create("My Iron Condor", template_yaml="path.yaml")
        await manager.transition(strategy_id, StrategyStatus.DEFINED, reason="Template complete")
        strategies = await manager.list_strategies()
    """

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def init_tables(self) -> None:
        """Create strategy tables if they don't exist."""
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

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_strategy_transitions_strategy_id
            ON strategy_transitions (strategy_id)
        """)

        await self._db.commit()
        logger.debug("Strategy tables initialized")

    async def create(
        self,
        name: str,
        template_yaml: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Create a new strategy in IDEA state.

        Args:
            name: Human-readable strategy name.
            template_yaml: Path to the strategy YAML template file.
            metadata: Optional metadata dict.

        Returns:
            The new strategy's ID.
        """
        now = now_et().isoformat()
        meta_json = json.dumps(metadata or {})

        cursor = await self._db.execute(
            """
            INSERT INTO strategies (name, status, template_yaml, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, StrategyStatus.IDEA.value, template_yaml, meta_json, now, now),
        )
        await self._db.commit()

        strategy_id = cursor.lastrowid
        logger.info("Created strategy #%d '%s' in IDEA state", strategy_id, name)
        return strategy_id

    async def get(self, strategy_id: int) -> dict[str, Any] | None:
        """Get a strategy by ID.

        Args:
            strategy_id: The strategy ID.

        Returns:
            Strategy dict or None if not found.
        """
        cursor = await self._db.execute(
            "SELECT id, name, status, template_yaml, metadata, created_at, updated_at "
            "FROM strategies WHERE id = ?",
            (strategy_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        columns = ["id", "name", "status", "template_yaml", "metadata", "created_at", "updated_at"]
        result = dict(zip(columns, row))

        # Parse metadata JSON
        try:
            result["metadata"] = json.loads(result["metadata"] or "{}")
        except json.JSONDecodeError:
            result["metadata"] = {}

        return result

    async def transition(
        self,
        strategy_id: int,
        new_status: StrategyStatus,
        reason: str | None = None,
    ) -> None:
        """Transition a strategy to a new state.

        Args:
            strategy_id: The strategy ID.
            new_status: The target state.
            reason: Optional reason for the transition.

        Raises:
            StrategyNotFoundError: If the strategy doesn't exist.
            InvalidTransitionError: If the transition is not valid.
        """
        strategy = await self.get(strategy_id)
        if strategy is None:
            raise StrategyNotFoundError(f"Strategy #{strategy_id} not found")

        current_status = StrategyStatus(strategy["status"])

        # Check if transition is valid
        allowed = VALID_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition strategy #{strategy_id} from {current_status.value} "
                f"to {new_status.value}. Allowed: {', '.join(s.value for s in allowed) or 'none'}"
            )

        now = now_et().isoformat()

        # Optimistic lock: only update if status hasn't changed since we read it
        cursor = await self._db.execute(
            "UPDATE strategies SET status = ?, updated_at = ? WHERE id = ? AND status = ?",
            (new_status.value, now, strategy_id, current_status.value),
        )
        if cursor.rowcount == 0:
            raise InvalidTransitionError(
                f"Strategy #{strategy_id} status changed concurrently "
                f"(expected {current_status.value})"
            )

        # Record transition
        await self._db.execute(
            """
            INSERT INTO strategy_transitions (strategy_id, from_status, to_status, reason, transitioned_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (strategy_id, current_status.value, new_status.value, reason, now),
        )

        await self._db.commit()

        logger.info(
            "Strategy #%d '%s': %s -> %s (reason: %s)",
            strategy_id, strategy["name"], current_status.value, new_status.value, reason,
        )

    async def update_template(self, strategy_id: int, template_yaml: str) -> None:
        """Update a strategy's template YAML.

        Args:
            strategy_id: The strategy ID.
            template_yaml: New YAML string for the template.

        Raises:
            StrategyNotFoundError: If the strategy doesn't exist.
        """
        strategy = await self.get(strategy_id)
        if strategy is None:
            raise StrategyNotFoundError(f"Strategy #{strategy_id} not found")

        await self._db.execute(
            "UPDATE strategies SET template_yaml = ?, updated_at = ? WHERE id = ?",
            (template_yaml, now_et().isoformat(), strategy_id),
        )
        await self._db.commit()

    async def update_metadata(self, strategy_id: int, metadata: dict[str, Any]) -> None:
        """Update strategy metadata (merge with existing).

        Args:
            strategy_id: The strategy ID.
            metadata: Metadata dict to merge.

        Raises:
            StrategyNotFoundError: If the strategy doesn't exist.
        """
        strategy = await self.get(strategy_id)
        if strategy is None:
            raise StrategyNotFoundError(f"Strategy #{strategy_id} not found")

        existing = strategy.get("metadata", {})
        existing.update(metadata)

        await self._db.execute(
            "UPDATE strategies SET metadata = ?, updated_at = ? WHERE id = ?",
            (json.dumps(existing), now_et().isoformat(), strategy_id),
        )
        await self._db.commit()

    async def list_strategies(self, status: StrategyStatus | None = None) -> list[dict[str, Any]]:
        """List all strategies, optionally filtered by status.

        Args:
            status: Optional status filter.

        Returns:
            List of strategy dicts.
        """
        if status is not None:
            cursor = await self._db.execute(
                "SELECT id, name, status, template_yaml, metadata, created_at, updated_at "
                "FROM strategies WHERE status = ? ORDER BY id",
                (status.value,),
            )
        else:
            cursor = await self._db.execute(
                "SELECT id, name, status, template_yaml, metadata, created_at, updated_at "
                "FROM strategies ORDER BY id"
            )

        rows = await cursor.fetchall()
        columns = ["id", "name", "status", "template_yaml", "metadata", "created_at", "updated_at"]

        strategies = []
        for row in rows:
            result = dict(zip(columns, row))
            try:
                result["metadata"] = json.loads(result["metadata"] or "{}")
            except json.JSONDecodeError:
                result["metadata"] = {}
            strategies.append(result)

        return strategies

    async def get_transition_history(self, strategy_id: int) -> list[dict[str, Any]]:
        """Get the transition history for a strategy.

        Args:
            strategy_id: The strategy ID.

        Returns:
            List of transition records in chronological order.
        """
        cursor = await self._db.execute(
            """
            SELECT id, strategy_id, from_status, to_status, reason, transitioned_at
            FROM strategy_transitions
            WHERE strategy_id = ?
            ORDER BY transitioned_at
            """,
            (strategy_id,),
        )

        rows = await cursor.fetchall()
        columns = ["id", "strategy_id", "from_status", "to_status", "reason", "transitioned_at"]

        return [dict(zip(columns, row)) for row in rows]

    async def delete(self, strategy_id: int) -> None:
        """Delete a strategy and its transition history.

        Args:
            strategy_id: The strategy ID.

        Raises:
            StrategyNotFoundError: If the strategy doesn't exist.
        """
        strategy = await self.get(strategy_id)
        if strategy is None:
            raise StrategyNotFoundError(f"Strategy #{strategy_id} not found")

        # Clean up hypothesis links if the table exists
        try:
            await self._db.execute(
                "DELETE FROM hypothesis_strategies WHERE strategy_id = ?",
                (str(strategy_id),),
            )
        except Exception:
            pass  # table may not exist in standalone StrategyManager usage
        await self._db.execute(
            "DELETE FROM strategy_transitions WHERE strategy_id = ?",
            (strategy_id,),
        )
        await self._db.execute(
            "DELETE FROM strategies WHERE id = ?",
            (strategy_id,),
        )
        await self._db.commit()

        logger.info("Deleted strategy #%d '%s'", strategy_id, strategy["name"])
