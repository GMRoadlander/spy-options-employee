"""Tests for the hypothesis testing framework."""

import pytest
import pytest_asyncio
import aiosqlite

from src.strategy.hypothesis import (
    Hypothesis,
    HypothesisManager,
    HypothesisStatus,
)


@pytest_asyncio.fixture
async def db():
    """Create an in-memory SQLite database for testing."""
    conn = await aiosqlite.connect(":memory:")
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def manager(db):
    """Create a HypothesisManager with initialized tables."""
    mgr = HypothesisManager(db)
    await mgr.init_tables()
    return mgr


# -- CRUD Tests --------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_hypothesis(manager):
    """Test creating a new hypothesis."""
    hyp = await manager.create(
        title="SPX IV is chronically overpriced",
        description="The implied volatility of SPX options exceeds realized vol consistently.",
        prediction="Short straddle Sharpe > 0.5 over 5 years",
        proposed_by="borey",
    )

    assert isinstance(hyp, Hypothesis)
    assert hyp.title == "SPX IV is chronically overpriced"
    assert hyp.status == HypothesisStatus.PROPOSED
    assert hyp.proposed_by == "borey"
    assert len(hyp.id) == 12


@pytest.mark.asyncio
async def test_get_hypothesis(manager):
    """Test retrieving a hypothesis by ID."""
    created = await manager.create(
        title="Test Hypothesis",
        description="Test description",
        prediction="Sharpe > 1.0",
    )

    retrieved = await manager.get(created.id)
    assert retrieved is not None
    assert retrieved.title == "Test Hypothesis"
    assert retrieved.testable_prediction == "Sharpe > 1.0"


@pytest.mark.asyncio
async def test_get_nonexistent_hypothesis(manager):
    """Test getting a hypothesis that doesn't exist."""
    result = await manager.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_list_all_hypotheses(manager):
    """Test listing all hypotheses."""
    await manager.create(title="H1", description="D1", prediction="P1")
    await manager.create(title="H2", description="D2", prediction="P2")
    await manager.create(title="H3", description="D3", prediction="P3")

    all_hyps = await manager.list_all()
    assert len(all_hyps) == 3


@pytest.mark.asyncio
async def test_list_hypotheses_by_status(manager):
    """Test listing hypotheses filtered by status."""
    h1 = await manager.create(title="H1", description="D1", prediction="P1")
    await manager.create(title="H2", description="D2", prediction="P2")

    # Change H1 to TESTING
    await manager.update_status(h1.id, HypothesisStatus.TESTING)

    proposed = await manager.list_all(status=HypothesisStatus.PROPOSED)
    assert len(proposed) == 1
    assert proposed[0].title == "H2"

    testing = await manager.list_all(status=HypothesisStatus.TESTING)
    assert len(testing) == 1
    assert testing[0].title == "H1"


# -- Strategy Linking Tests --------------------------------------------------


@pytest.mark.asyncio
async def test_link_strategy(manager):
    """Test linking a strategy to a hypothesis."""
    hyp = await manager.create(title="H1", description="D1", prediction="P1")

    await manager.link_strategy(hyp.id, "strategy_42")
    await manager.link_strategy(hyp.id, "strategy_43")

    retrieved = await manager.get(hyp.id)
    assert len(retrieved.strategy_ids) == 2
    assert "strategy_42" in retrieved.strategy_ids
    assert "strategy_43" in retrieved.strategy_ids


@pytest.mark.asyncio
async def test_link_strategy_idempotent(manager):
    """Test that linking the same strategy twice is idempotent."""
    hyp = await manager.create(title="H1", description="D1", prediction="P1")

    await manager.link_strategy(hyp.id, "strategy_42")
    await manager.link_strategy(hyp.id, "strategy_42")  # duplicate

    retrieved = await manager.get(hyp.id)
    assert len(retrieved.strategy_ids) == 1


@pytest.mark.asyncio
async def test_unlink_strategy(manager):
    """Test unlinking a strategy from a hypothesis."""
    hyp = await manager.create(title="H1", description="D1", prediction="P1")
    await manager.link_strategy(hyp.id, "strategy_42")
    await manager.link_strategy(hyp.id, "strategy_43")

    await manager.unlink_strategy(hyp.id, "strategy_42")

    retrieved = await manager.get(hyp.id)
    assert len(retrieved.strategy_ids) == 1
    assert "strategy_43" in retrieved.strategy_ids


# -- Test Evaluation ----------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_confirmed(manager):
    """Test hypothesis evaluation resulting in CONFIRMED."""

    class MockMetrics:
        sharpe_ratio = 1.5

    class MockDSR:
        dsr = 0.98  # p_value = 0.02 < 0.05

    class MockResult:
        recommendation = "PROMOTE"
        metrics = MockMetrics()
        dsr = MockDSR()

    hyp = await manager.create(title="H1", description="D1", prediction="Sharpe > 0.5")
    result = await manager.test(hyp.id, MockResult())

    assert result.status == HypothesisStatus.CONFIRMED
    assert result.p_value < 0.05
    assert result.test_result is not None
    assert "CONFIRMED" in result.test_result


@pytest.mark.asyncio
async def test_evaluate_rejected(manager):
    """Test hypothesis evaluation resulting in REJECTED."""

    class MockMetrics:
        sharpe_ratio = 0.1

    class MockDSR:
        dsr = 0.5  # p_value = 0.5 >= 0.10

    class MockResult:
        recommendation = "REJECT"
        metrics = MockMetrics()
        dsr = MockDSR()

    hyp = await manager.create(title="H1", description="D1", prediction="Sharpe > 0.5")
    result = await manager.test(hyp.id, MockResult())

    assert result.status == HypothesisStatus.REJECTED


@pytest.mark.asyncio
async def test_evaluate_inconclusive(manager):
    """Test hypothesis evaluation resulting in INCONCLUSIVE."""

    class MockMetrics:
        sharpe_ratio = 0.8

    class MockDSR:
        dsr = 0.93  # p_value = 0.07 — between 0.05 and 0.10

    class MockResult:
        recommendation = "REFINE"
        metrics = MockMetrics()
        dsr = MockDSR()

    hyp = await manager.create(title="H1", description="D1", prediction="Sharpe > 0.5")
    result = await manager.test(hyp.id, MockResult())

    assert result.status == HypothesisStatus.INCONCLUSIVE


@pytest.mark.asyncio
async def test_evaluate_nonexistent_raises(manager):
    """Test that evaluating a nonexistent hypothesis raises ValueError."""

    class MockResult:
        recommendation = "REJECT"
        metrics = None
        dsr = None

    with pytest.raises(ValueError, match="not found"):
        await manager.test("nonexistent", MockResult())


# -- Auto null hypothesis ---------------------------------------------------


@pytest.mark.asyncio
async def test_auto_null_hypothesis(manager):
    """Test that null hypothesis is auto-generated when not provided."""
    hyp = await manager.create(
        title="H1", description="D1", prediction="Sharpe > 0.5"
    )

    retrieved = await manager.get(hyp.id)
    assert "NOT" in retrieved.null_hypothesis
    assert "Sharpe > 0.5" in retrieved.null_hypothesis
