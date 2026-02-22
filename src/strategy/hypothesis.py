"""Hypothesis testing framework for structured research.

Transforms Borey's market intuitions into testable, falsifiable claims.
Hypotheses are linked to strategies (test vehicles) and evaluated via
the anti-overfitting pipeline. Results include statistical significance.

Workflow: PROPOSED -> TESTING -> CONFIRMED | REJECTED | INCONCLUSIVE
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


class HypothesisStatus(str, Enum):
    """Status of a hypothesis in the research workflow."""

    PROPOSED = "PROPOSED"
    TESTING = "TESTING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class Hypothesis:
    """A testable market hypothesis.

    Attributes:
        id: Unique identifier.
        title: Short title (e.g., "SPX IV is chronically overpriced").
        description: Detailed market belief.
        testable_prediction: Falsifiable prediction (e.g., "Short straddle Sharpe > 0.5").
        null_hypothesis: What we're testing against (e.g., "Short straddle Sharpe <= 0.5").
        status: Current hypothesis status.
        proposed_by: Who proposed it (e.g., "borey").
        proposed_at: When it was proposed.
        strategy_ids: Linked strategy IDs (test vehicles).
        test_result: Summary of findings after testing.
        p_value: Statistical significance.
        tested_at: When testing was completed.
    """

    id: str
    title: str
    description: str
    testable_prediction: str
    null_hypothesis: str
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    proposed_by: str = "borey"
    proposed_at: datetime = field(default_factory=datetime.now)
    strategy_ids: list[str] = field(default_factory=list)
    test_result: str | None = None
    p_value: float | None = None
    tested_at: datetime | None = None


# SQL DDL for hypothesis tables
HYPOTHESES_DDL = """\
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
"""

HYPOTHESIS_STRATEGIES_DDL = """\
CREATE TABLE IF NOT EXISTS hypothesis_strategies (
    hypothesis_id TEXT NOT NULL REFERENCES hypotheses(id),
    strategy_id TEXT NOT NULL,
    PRIMARY KEY (hypothesis_id, strategy_id)
)
"""


class HypothesisManager:
    """Manages hypothesis lifecycle with SQLite persistence.

    Args:
        db: Shared aiosqlite connection from Store.
    """

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def init_tables(self) -> None:
        """Create hypothesis tables if they don't exist."""
        await self._db.execute(HYPOTHESES_DDL)
        await self._db.execute(HYPOTHESIS_STRATEGIES_DDL)
        await self._db.commit()
        logger.debug("Hypothesis tables initialized")

    async def create(
        self,
        title: str,
        description: str,
        prediction: str,
        null_hypothesis: str | None = None,
        proposed_by: str = "borey",
    ) -> Hypothesis:
        """Create a new hypothesis in PROPOSED status.

        Args:
            title: Short hypothesis title.
            description: Detailed description.
            prediction: Testable, falsifiable prediction.
            null_hypothesis: What we're testing against. Auto-generated if None.
            proposed_by: Who proposed it.

        Returns:
            The created Hypothesis.
        """
        hyp_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        if null_hypothesis is None:
            null_hypothesis = f"NOT({prediction})"

        hyp = Hypothesis(
            id=hyp_id,
            title=title,
            description=description,
            testable_prediction=prediction,
            null_hypothesis=null_hypothesis,
            status=HypothesisStatus.PROPOSED,
            proposed_by=proposed_by,
            proposed_at=now,
        )

        await self._db.execute(
            """
            INSERT INTO hypotheses (id, title, description, testable_prediction,
                                    null_hypothesis, status, proposed_by, proposed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hyp.id,
                hyp.title,
                hyp.description,
                hyp.testable_prediction,
                hyp.null_hypothesis,
                hyp.status.value,
                hyp.proposed_by,
                hyp.proposed_at.isoformat(),
            ),
        )
        await self._db.commit()

        logger.info("Created hypothesis '%s' (id=%s)", title, hyp_id)
        return hyp

    async def get(self, hypothesis_id: str) -> Hypothesis | None:
        """Get a hypothesis by ID.

        Args:
            hypothesis_id: The hypothesis ID.

        Returns:
            Hypothesis or None if not found.
        """
        cursor = await self._db.execute(
            """
            SELECT id, title, description, testable_prediction, null_hypothesis,
                   status, proposed_by, proposed_at, test_result, p_value, tested_at
            FROM hypotheses WHERE id = ?
            """,
            (hypothesis_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        # Get linked strategies
        cursor = await self._db.execute(
            "SELECT strategy_id FROM hypothesis_strategies WHERE hypothesis_id = ?",
            (hypothesis_id,),
        )
        strategy_rows = await cursor.fetchall()
        strategy_ids = [r[0] for r in strategy_rows]

        return Hypothesis(
            id=row[0],
            title=row[1],
            description=row[2],
            testable_prediction=row[3],
            null_hypothesis=row[4],
            status=HypothesisStatus(row[5]),
            proposed_by=row[6],
            proposed_at=datetime.fromisoformat(row[7]),
            strategy_ids=strategy_ids,
            test_result=row[8],
            p_value=row[9],
            tested_at=datetime.fromisoformat(row[10]) if row[10] else None,
        )

    async def list_all(
        self,
        status: HypothesisStatus | None = None,
    ) -> list[Hypothesis]:
        """List all hypotheses, optionally filtered by status.

        Args:
            status: Optional status filter.

        Returns:
            List of Hypothesis objects.
        """
        if status is not None:
            cursor = await self._db.execute(
                """
                SELECT id, title, description, testable_prediction, null_hypothesis,
                       status, proposed_by, proposed_at, test_result, p_value, tested_at
                FROM hypotheses WHERE status = ?
                ORDER BY proposed_at DESC
                """,
                (status.value,),
            )
        else:
            cursor = await self._db.execute(
                """
                SELECT id, title, description, testable_prediction, null_hypothesis,
                       status, proposed_by, proposed_at, test_result, p_value, tested_at
                FROM hypotheses
                ORDER BY proposed_at DESC
                """
            )

        rows = await cursor.fetchall()
        hypotheses = []

        for row in rows:
            # Get linked strategies
            s_cursor = await self._db.execute(
                "SELECT strategy_id FROM hypothesis_strategies WHERE hypothesis_id = ?",
                (row[0],),
            )
            s_rows = await s_cursor.fetchall()
            strategy_ids = [r[0] for r in s_rows]

            hypotheses.append(Hypothesis(
                id=row[0],
                title=row[1],
                description=row[2],
                testable_prediction=row[3],
                null_hypothesis=row[4],
                status=HypothesisStatus(row[5]),
                proposed_by=row[6],
                proposed_at=datetime.fromisoformat(row[7]),
                strategy_ids=strategy_ids,
                test_result=row[8],
                p_value=row[9],
                tested_at=datetime.fromisoformat(row[10]) if row[10] else None,
            ))

        return hypotheses

    async def link_strategy(
        self,
        hypothesis_id: str,
        strategy_id: str,
    ) -> None:
        """Link a strategy to a hypothesis as a test vehicle.

        Args:
            hypothesis_id: The hypothesis ID.
            strategy_id: The strategy ID to link.
        """
        await self._db.execute(
            """
            INSERT OR IGNORE INTO hypothesis_strategies (hypothesis_id, strategy_id)
            VALUES (?, ?)
            """,
            (hypothesis_id, strategy_id),
        )
        await self._db.commit()
        logger.info("Linked strategy %s to hypothesis %s", strategy_id, hypothesis_id)

    async def unlink_strategy(
        self,
        hypothesis_id: str,
        strategy_id: str,
    ) -> None:
        """Unlink a strategy from a hypothesis.

        Args:
            hypothesis_id: The hypothesis ID.
            strategy_id: The strategy ID to unlink.
        """
        await self._db.execute(
            "DELETE FROM hypothesis_strategies WHERE hypothesis_id = ? AND strategy_id = ?",
            (hypothesis_id, strategy_id),
        )
        await self._db.commit()

    async def test(
        self,
        hypothesis_id: str,
        pipeline_result: Any,
    ) -> Hypothesis:
        """Evaluate a hypothesis based on pipeline results.

        Transitions hypothesis to CONFIRMED, REJECTED, or INCONCLUSIVE
        based on the evaluation pipeline outcome.

        Args:
            hypothesis_id: The hypothesis ID.
            pipeline_result: PipelineResult from the evaluation pipeline.

        Returns:
            Updated Hypothesis.

        Raises:
            ValueError: If hypothesis not found.
        """
        hyp = await self.get(hypothesis_id)
        if hyp is None:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")

        # Determine outcome from pipeline result
        now = datetime.now()

        # Extract metrics from pipeline result
        recommendation = getattr(pipeline_result, "recommendation", "REJECT")
        sharpe = getattr(getattr(pipeline_result, "metrics", None), "sharpe_ratio", 0.0)
        dsr_value = getattr(getattr(pipeline_result, "dsr", None), "dsr", 0.0)

        # Use DSR as a proxy for p-value (1 - DSR = probability of chance)
        p_value = max(0.0, 1.0 - dsr_value)

        # Determine status
        if recommendation == "PROMOTE" and p_value < 0.05:
            new_status = HypothesisStatus.CONFIRMED
            result_text = (
                f"Hypothesis CONFIRMED: Sharpe={sharpe:.3f}, "
                f"p-value={p_value:.4f}, recommendation={recommendation}"
            )
        elif recommendation == "REJECT" or p_value >= 0.10:
            new_status = HypothesisStatus.REJECTED
            result_text = (
                f"Hypothesis REJECTED: Sharpe={sharpe:.3f}, "
                f"p-value={p_value:.4f}, recommendation={recommendation}"
            )
        else:
            new_status = HypothesisStatus.INCONCLUSIVE
            result_text = (
                f"Hypothesis INCONCLUSIVE: Sharpe={sharpe:.3f}, "
                f"p-value={p_value:.4f}, recommendation={recommendation}"
            )

        await self._db.execute(
            """
            UPDATE hypotheses
            SET status = ?, test_result = ?, p_value = ?, tested_at = ?
            WHERE id = ?
            """,
            (new_status.value, result_text, p_value, now.isoformat(), hypothesis_id),
        )
        await self._db.commit()

        logger.info(
            "Hypothesis '%s' evaluated: %s (p=%.4f)",
            hyp.title, new_status.value, p_value,
        )

        return await self.get(hypothesis_id)

    async def update_status(
        self,
        hypothesis_id: str,
        status: HypothesisStatus,
    ) -> None:
        """Manually update hypothesis status.

        Args:
            hypothesis_id: The hypothesis ID.
            status: New status.
        """
        await self._db.execute(
            "UPDATE hypotheses SET status = ? WHERE id = ?",
            (status.value, hypothesis_id),
        )
        await self._db.commit()
