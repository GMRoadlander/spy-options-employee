"""Tests for paper trading database schema.

Verifies table creation, column types, indexes, foreign key constraints,
and idempotent initialization using in-memory SQLite databases.
"""

import json
from datetime import datetime

import aiosqlite
import pytest
import pytest_asyncio

from src.paper.schema import init_paper_tables


@pytest_asyncio.fixture
async def db():
    """Create an in-memory database with required prerequisite tables."""
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys = ON")

    # Create the strategies table that paper tables reference
    await conn.execute("""
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
    await conn.commit()

    yield conn
    await conn.close()


@pytest.mark.asyncio
async def test_init_paper_tables_creates_all_tables(db):
    """All 5 paper trading tables should be created."""
    await init_paper_tables(db)

    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row[0] for row in await cursor.fetchall()}

    assert "paper_orders" in tables
    assert "paper_fills" in tables
    assert "paper_positions" in tables
    assert "paper_trades" in tables
    assert "paper_portfolio" in tables


@pytest.mark.asyncio
async def test_init_paper_tables_idempotent(db):
    """Calling init_paper_tables() twice should not fail."""
    await init_paper_tables(db)
    await init_paper_tables(db)  # Should not raise

    cursor = await db.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'paper_%'"
    )
    count = (await cursor.fetchone())[0]
    assert count == 5


@pytest.mark.asyncio
async def test_indexes_created(db):
    """All expected indexes should be created."""
    await init_paper_tables(db)

    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_paper_%'"
    )
    indexes = {row[0] for row in await cursor.fetchall()}

    expected = {
        "idx_paper_orders_strategy",
        "idx_paper_orders_status",
        "idx_paper_fills_order",
        "idx_paper_positions_strategy",
        "idx_paper_positions_open",
        "idx_paper_trades_strategy",
        # paper_portfolio.snapshot_date UNIQUE constraint creates an implicit index
    }
    assert expected.issubset(indexes)


@pytest.mark.asyncio
async def test_paper_orders_insert(db):
    """Can insert and query paper orders."""
    await init_paper_tables(db)

    # Create a strategy first
    now = datetime.now().isoformat()
    cursor = await db.execute(
        "INSERT INTO strategies (name, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("Test IC", "paper", now, now),
    )
    strategy_id = cursor.lastrowid
    await db.commit()

    # Insert an order
    legs = json.dumps([{"leg_name": "short_put", "strike": 5800}])
    cursor = await db.execute(
        """
        INSERT INTO paper_orders
            (strategy_id, order_type, direction, legs, quantity, status, submitted_at)
        VALUES (?, 'market', 'open', ?, 1, 'pending', ?)
        """,
        (strategy_id, legs, now),
    )
    order_id = cursor.lastrowid
    await db.commit()

    # Verify
    cursor = await db.execute("SELECT * FROM paper_orders WHERE id = ?", (order_id,))
    row = await cursor.fetchone()
    assert row is not None


@pytest.mark.asyncio
async def test_paper_fills_foreign_key(db):
    """paper_fills.order_id should reference paper_orders.id."""
    await init_paper_tables(db)

    now = datetime.now().isoformat()

    # Create strategy
    cursor = await db.execute(
        "INSERT INTO strategies (name, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("Test", "paper", now, now),
    )
    strategy_id = cursor.lastrowid

    # Create order
    cursor = await db.execute(
        """
        INSERT INTO paper_orders
            (strategy_id, order_type, direction, legs, quantity, status, submitted_at)
        VALUES (?, 'market', 'open', '[]', 1, 'pending', ?)
        """,
        (strategy_id, now),
    )
    order_id = cursor.lastrowid
    await db.commit()

    # Insert fill referencing the order -- should succeed
    await db.execute(
        """
        INSERT INTO paper_fills
            (order_id, leg_name, option_type, strike, expiry, action,
             quantity, fill_price, bid_at_fill, ask_at_fill, mid_at_fill, filled_at)
        VALUES (?, 'short_put', 'put', 5800.0, '2025-03-21', 'sell',
                1, 3.50, 3.40, 3.60, 3.50, ?)
        """,
        (order_id, now),
    )
    await db.commit()

    # Insert fill with non-existent order_id -- should fail
    with pytest.raises(aiosqlite.IntegrityError):
        await db.execute(
            """
            INSERT INTO paper_fills
                (order_id, leg_name, option_type, strike, expiry, action,
                 quantity, fill_price, bid_at_fill, ask_at_fill, mid_at_fill, filled_at)
            VALUES (9999, 'short_put', 'put', 5800.0, '2025-03-21', 'sell',
                    1, 3.50, 3.40, 3.60, 3.50, ?)
            """,
            (now,),
        )


@pytest.mark.asyncio
async def test_paper_positions_columns(db):
    """paper_positions should have all expected columns."""
    await init_paper_tables(db)

    cursor = await db.execute("PRAGMA table_info(paper_positions)")
    columns = {row[1] for row in await cursor.fetchall()}

    expected = {
        "id", "strategy_id", "open_order_id", "status", "legs",
        "entry_price", "quantity", "max_profit", "max_loss",
        "current_mark", "unrealized_pnl", "last_mark_at",
        "opened_at", "closed_at", "close_reason", "close_order_id",
        "metadata",
    }
    assert expected.issubset(columns)


@pytest.mark.asyncio
async def test_paper_trades_columns(db):
    """paper_trades should have all expected columns."""
    await init_paper_tables(db)

    cursor = await db.execute("PRAGMA table_info(paper_trades)")
    columns = {row[1] for row in await cursor.fetchall()}

    expected = {
        "id", "strategy_id", "position_id", "entry_date", "exit_date",
        "holding_days", "entry_price", "exit_price", "realized_pnl",
        "total_pnl", "fees", "slippage_cost", "settlement_type",
        "close_reason", "legs_detail", "metadata",
    }
    assert expected.issubset(columns)


@pytest.mark.asyncio
async def test_paper_portfolio_columns(db):
    """paper_portfolio should have all expected columns."""
    await init_paper_tables(db)

    cursor = await db.execute("PRAGMA table_info(paper_portfolio)")
    columns = {row[1] for row in await cursor.fetchall()}

    expected = {
        "id", "snapshot_date", "starting_capital", "realized_pnl",
        "unrealized_pnl", "total_equity", "open_positions",
        "total_trades", "daily_pnl", "max_drawdown", "metadata",
    }
    assert expected.issubset(columns)


@pytest.mark.asyncio
async def test_paper_orders_default_status(db):
    """Default order status should be 'pending'."""
    await init_paper_tables(db)
    now = datetime.now().isoformat()

    cursor = await db.execute(
        "INSERT INTO strategies (name, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("Test", "paper", now, now),
    )
    strategy_id = cursor.lastrowid

    cursor = await db.execute(
        """
        INSERT INTO paper_orders
            (strategy_id, order_type, direction, legs, quantity, submitted_at)
        VALUES (?, 'market', 'open', '[]', 1, ?)
        """,
        (strategy_id, now),
    )
    order_id = cursor.lastrowid
    await db.commit()

    cursor = await db.execute(
        "SELECT status FROM paper_orders WHERE id = ?", (order_id,)
    )
    status = (await cursor.fetchone())[0]
    assert status == "pending"


@pytest.mark.asyncio
async def test_paper_positions_default_values(db):
    """Default position values should be correct."""
    await init_paper_tables(db)
    now = datetime.now().isoformat()

    # Create strategy and order
    cursor = await db.execute(
        "INSERT INTO strategies (name, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("Test", "paper", now, now),
    )
    strategy_id = cursor.lastrowid

    cursor = await db.execute(
        """
        INSERT INTO paper_orders
            (strategy_id, order_type, direction, legs, quantity, status, submitted_at)
        VALUES (?, 'market', 'open', '[]', 1, 'filled', ?)
        """,
        (strategy_id, now),
    )
    order_id = cursor.lastrowid
    await db.commit()

    # Create position with defaults
    cursor = await db.execute(
        """
        INSERT INTO paper_positions
            (strategy_id, open_order_id, legs, entry_price, opened_at)
        VALUES (?, ?, '[]', 2.50, ?)
        """,
        (strategy_id, order_id, now),
    )
    pos_id = cursor.lastrowid
    await db.commit()

    cursor = await db.execute(
        "SELECT status, quantity, unrealized_pnl FROM paper_positions WHERE id = ?",
        (pos_id,),
    )
    row = await cursor.fetchone()
    assert row[0] == "open"
    assert row[1] == 1
    assert row[2] == 0.0


@pytest.mark.asyncio
async def test_paper_portfolio_daily_snapshot(db):
    """Can insert and query portfolio snapshots."""
    await init_paper_tables(db)

    await db.execute(
        """
        INSERT INTO paper_portfolio
            (snapshot_date, starting_capital, realized_pnl, unrealized_pnl,
             total_equity, open_positions, total_trades, daily_pnl, max_drawdown)
        VALUES ('2025-03-21', 100000, 500, 200, 100700, 3, 10, 150, -0.02)
        """
    )
    await db.commit()

    cursor = await db.execute(
        "SELECT total_equity, daily_pnl FROM paper_portfolio WHERE snapshot_date = '2025-03-21'"
    )
    row = await cursor.fetchone()
    assert row[0] == 100700
    assert row[1] == 150
