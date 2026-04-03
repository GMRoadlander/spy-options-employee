"""Tests for strategy lifecycle state machine and persistence.

Uses in-memory SQLite for fast, isolated tests. Covers CRUD operations,
state transitions, validation, and transition history.
"""

import pytest
import pytest_asyncio
import aiosqlite
from datetime import datetime

from src.strategy.lifecycle import (
    InvalidTransitionError,
    StrategyManager,
    StrategyNotFoundError,
    StrategyStatus,
    VALID_TRANSITIONS,
)


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
async def manager(db):
    """Create a StrategyManager with initialized tables."""
    mgr = StrategyManager(db)
    await mgr.init_tables()
    return mgr


# ---------------------------------------------------------------------------
# Tests: CRUD operations
# ---------------------------------------------------------------------------


class TestCRUD:
    """Tests for create, read, update, delete operations."""

    @pytest.mark.asyncio
    async def test_create_strategy(self, manager):
        """Creating a strategy returns an ID and sets IDEA state."""
        sid = await manager.create("Test IC")
        assert sid > 0

        strategy = await manager.get(sid)
        assert strategy is not None
        assert strategy["name"] == "Test IC"
        assert strategy["status"] == "idea"

    @pytest.mark.asyncio
    async def test_create_with_metadata(self, manager):
        """Metadata dict is stored and retrieved."""
        sid = await manager.create("Test", metadata={"author": "Borey", "version": "1.0"})
        strategy = await manager.get(sid)
        assert strategy["metadata"]["author"] == "Borey"
        assert strategy["metadata"]["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_create_with_template_yaml(self, manager):
        """template_yaml path is stored."""
        sid = await manager.create("Test", template_yaml="strategies/examples/spx-iron-condor.yaml")
        strategy = await manager.get(sid)
        assert strategy["template_yaml"] == "strategies/examples/spx-iron-condor.yaml"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, manager):
        """Getting a nonexistent ID returns None."""
        result = await manager.get(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_strategies(self, manager):
        """list_strategies returns all strategies."""
        await manager.create("Strat A")
        await manager.create("Strat B")
        strategies = await manager.list_strategies()
        assert len(strategies) == 2

    @pytest.mark.asyncio
    async def test_list_strategies_filtered(self, manager):
        """list_strategies with status filter works."""
        sid = await manager.create("Strat A")
        await manager.create("Strat B")
        await manager.transition(sid, StrategyStatus.DEFINED)

        ideas = await manager.list_strategies(status=StrategyStatus.IDEA)
        assert len(ideas) == 1
        assert ideas[0]["name"] == "Strat B"

    @pytest.mark.asyncio
    async def test_update_metadata(self, manager):
        """update_metadata merges with existing metadata."""
        sid = await manager.create("Test", metadata={"key1": "val1"})
        await manager.update_metadata(sid, {"key2": "val2"})

        strategy = await manager.get(sid)
        assert strategy["metadata"]["key1"] == "val1"
        assert strategy["metadata"]["key2"] == "val2"

    @pytest.mark.asyncio
    async def test_delete_strategy(self, manager):
        """delete removes strategy and its transitions."""
        sid = await manager.create("To Delete")
        await manager.transition(sid, StrategyStatus.DEFINED)
        await manager.delete(sid)

        assert await manager.get(sid) is None
        history = await manager.get_transition_history(sid)
        assert len(history) == 0


# ---------------------------------------------------------------------------
# Tests: State transitions
# ---------------------------------------------------------------------------


class TestTransitions:
    """Tests for state machine transition enforcement."""

    @pytest.mark.asyncio
    async def test_idea_to_defined(self, manager):
        """IDEA -> DEFINED is valid."""
        sid = await manager.create("Test")
        await manager.transition(sid, StrategyStatus.DEFINED, reason="Template complete")
        strategy = await manager.get(sid)
        assert strategy["status"] == "defined"

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, manager):
        """Walk through the full happy path: IDEA -> DEFINED -> BACKTEST -> PAPER -> RETIRED."""
        sid = await manager.create("Full Lifecycle")

        transitions = [
            (StrategyStatus.DEFINED, "Template written"),
            (StrategyStatus.BACKTEST, "Running backtest"),
            (StrategyStatus.PAPER, "Backtest passed"),
            (StrategyStatus.RETIRED, "Seasonal end"),
        ]

        for status, reason in transitions:
            await manager.transition(sid, status, reason=reason)

        strategy = await manager.get(sid)
        assert strategy["status"] == "retired"

        history = await manager.get_transition_history(sid)
        assert len(history) == 4

    @pytest.mark.asyncio
    async def test_invalid_transition_raises(self, manager):
        """IDEA -> PAPER is not valid and raises."""
        sid = await manager.create("Test")
        with pytest.raises(InvalidTransitionError, match="Cannot transition"):
            await manager.transition(sid, StrategyStatus.PAPER)

    @pytest.mark.asyncio
    async def test_retired_is_terminal(self, manager):
        """Cannot transition out of RETIRED."""
        sid = await manager.create("Test")
        await manager.transition(sid, StrategyStatus.RETIRED)

        with pytest.raises(InvalidTransitionError):
            await manager.transition(sid, StrategyStatus.IDEA)

    @pytest.mark.asyncio
    async def test_any_state_to_retired(self, manager):
        """Any non-retired state can transition to RETIRED."""
        for from_status in [s for s in StrategyStatus if s != StrategyStatus.RETIRED]:
            sid = await manager.create(f"Test {from_status.value}")
            # Walk to the target state
            if from_status == StrategyStatus.IDEA:
                pass  # already in IDEA
            elif from_status == StrategyStatus.DEFINED:
                await manager.transition(sid, StrategyStatus.DEFINED)
            elif from_status == StrategyStatus.BACKTEST:
                await manager.transition(sid, StrategyStatus.DEFINED)
                await manager.transition(sid, StrategyStatus.BACKTEST)
            elif from_status == StrategyStatus.PAPER:
                await manager.transition(sid, StrategyStatus.DEFINED)
                await manager.transition(sid, StrategyStatus.BACKTEST)
                await manager.transition(sid, StrategyStatus.PAPER)
            await manager.transition(sid, StrategyStatus.RETIRED)
            strategy = await manager.get(sid)
            assert strategy["status"] == "retired"

    @pytest.mark.asyncio
    async def test_transition_nonexistent_raises(self, manager):
        """Transitioning a nonexistent strategy raises."""
        with pytest.raises(StrategyNotFoundError):
            await manager.transition(999, StrategyStatus.DEFINED)


# ---------------------------------------------------------------------------
# Tests: Transition history
# ---------------------------------------------------------------------------


class TestTransitionHistory:
    """Tests for transition audit log."""

    @pytest.mark.asyncio
    async def test_history_records_reason(self, manager):
        """Transition reason is recorded in history."""
        sid = await manager.create("Test")
        await manager.transition(sid, StrategyStatus.DEFINED, reason="Template done")

        history = await manager.get_transition_history(sid)
        assert len(history) == 1
        assert history[0]["from_status"] == "idea"
        assert history[0]["to_status"] == "defined"
        assert history[0]["reason"] == "Template done"

    @pytest.mark.asyncio
    async def test_history_chronological(self, manager):
        """History is returned in chronological order."""
        sid = await manager.create("Test")
        await manager.transition(sid, StrategyStatus.DEFINED)
        await manager.transition(sid, StrategyStatus.BACKTEST)

        history = await manager.get_transition_history(sid)
        assert len(history) == 2
        assert history[0]["to_status"] == "defined"
        assert history[1]["to_status"] == "backtest"
