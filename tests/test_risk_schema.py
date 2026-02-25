"""Tests for risk database schema.

Verifies table creation, idempotency, indexes, and basic CRUD
operations on all risk tables.
"""

from datetime import datetime

import aiosqlite
import pytest
import pytest_asyncio

from src.risk.schema import init_risk_tables


@pytest_asyncio.fixture
async def db():
    """Create an in-memory database."""
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    await conn.close()


@pytest.mark.asyncio
async def test_init_risk_tables_creates_all(db):
    """Call init, verify 4 tables exist."""
    await init_risk_tables(db)

    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row[0] for row in await cursor.fetchall()}

    assert "risk_snapshots" in tables
    assert "risk_alerts" in tables
    assert "risk_check_log" in tables
    assert "risk_limit_changes" in tables


@pytest.mark.asyncio
async def test_init_risk_tables_idempotent(db):
    """Call twice, no error."""
    await init_risk_tables(db)
    await init_risk_tables(db)  # Should not raise


@pytest.mark.asyncio
async def test_risk_snapshots_insert(db):
    """Insert a row, read back."""
    await init_risk_tables(db)

    now = datetime.now().isoformat()
    await db.execute(
        """
        INSERT INTO risk_snapshots
            (timestamp, portfolio_nav, portfolio_delta, portfolio_gamma,
             portfolio_theta, portfolio_vega, dollar_delta, dollar_gamma,
             var_95, var_99, regime_state, anomaly_score, num_positions, num_alerts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now, 100000.0, 50.0, 2.0, -100.0, 500.0, 50.0, 10.0,
         1500.0, 2500.0, 0, 0.1, 3, 0),
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM risk_snapshots WHERE id = 1")
    row = await cursor.fetchone()
    assert row is not None
    assert row[2] == 100000.0  # portfolio_nav


@pytest.mark.asyncio
async def test_risk_alerts_insert(db):
    """Insert alert with NULL resolved_at."""
    await init_risk_tables(db)

    now = datetime.now().isoformat()
    await db.execute(
        """
        INSERT INTO risk_alerts
            (timestamp, level, category, message, current_value, limit_value)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (now, "warning", "delta", "Delta at 85% of limit", 425.0, 500.0),
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM risk_alerts WHERE id = 1")
    row = await cursor.fetchone()
    assert row is not None
    assert row[2] == "warning"  # level
    assert row[7] is None  # resolved_at should be NULL


@pytest.mark.asyncio
async def test_risk_check_log_insert(db):
    """Insert approved and rejected checks."""
    await init_risk_tables(db)

    now = datetime.now().isoformat()

    # Approved check
    await db.execute(
        """
        INSERT INTO risk_check_log
            (timestamp, order_id, strategy_id, approved, checks_json, regime_state)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (now, 1, 1, 1, '{"passed":["circuit_breaker","regime"]}', 0),
    )

    # Rejected check
    await db.execute(
        """
        INSERT INTO risk_check_log
            (timestamp, order_id, strategy_id, approved, checks_json, regime_state)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (now, 2, 1, 0, '{"failed":["position_limits"]}', 2),
    )
    await db.commit()

    cursor = await db.execute("SELECT COUNT(*) FROM risk_check_log")
    count = (await cursor.fetchone())[0]
    assert count == 2

    # Verify approved check
    cursor = await db.execute(
        "SELECT approved FROM risk_check_log WHERE order_id = 1")
    row = await cursor.fetchone()
    assert row[0] == 1

    # Verify rejected check
    cursor = await db.execute(
        "SELECT approved FROM risk_check_log WHERE order_id = 2")
    row = await cursor.fetchone()
    assert row[0] == 0


@pytest.mark.asyncio
async def test_risk_limit_changes_insert(db):
    """Insert a limit change record."""
    await init_risk_tables(db)

    now = datetime.now().isoformat()
    await db.execute(
        """
        INSERT INTO risk_limit_changes
            (timestamp, limit_name, old_value, new_value, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (now, "max_portfolio_delta", 500.0, 300.0, "Regime transition to risk-off"),
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM risk_limit_changes WHERE id = 1")
    row = await cursor.fetchone()
    assert row is not None
    assert row[2] == "max_portfolio_delta"


@pytest.mark.asyncio
async def test_indexes_created(db):
    """Verify indexes are created."""
    await init_risk_tables(db)

    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
    )
    indexes = {row[0] for row in await cursor.fetchall()}

    assert "idx_risk_snapshots_ts" in indexes
    assert "idx_risk_alerts_ts" in indexes
    assert "idx_risk_check_log_ts" in indexes
    assert "idx_risk_check_log_order" in indexes
    assert "idx_risk_limit_changes_ts" in indexes
