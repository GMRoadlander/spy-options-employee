"""Database schema for the paper trading engine.

Defines 6 tables for paper trading state:
- paper_orders: order lifecycle tracking
- paper_fills: per-leg fill details with market conditions
- paper_positions: open positions with mark-to-market
- paper_trades: completed trade records with final PnL
- paper_portfolio: daily equity snapshots for performance analysis
- slippage_log: per-fill slippage analysis for model calibration

All tables use foreign keys referencing the strategies table from
src/strategy/lifecycle.py. The init_paper_tables() function creates
them idempotently (IF NOT EXISTS).
"""

import logging

import aiosqlite

logger = logging.getLogger(__name__)

PAPER_ORDERS_SQL = """
CREATE TABLE IF NOT EXISTS paper_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    order_type TEXT NOT NULL DEFAULT 'market',
    direction TEXT NOT NULL,
    legs TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    limit_price REAL,
    status TEXT NOT NULL DEFAULT 'pending',
    submitted_at TEXT NOT NULL,
    filled_at TEXT,
    cancelled_at TEXT,
    fill_price REAL,
    slippage REAL,
    ticks_pending INTEGER NOT NULL DEFAULT 0,
    metadata TEXT DEFAULT '{}'
)
"""

PAPER_ORDERS_INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS idx_paper_orders_strategy
    ON paper_orders (strategy_id, status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_paper_orders_status
    ON paper_orders (status, submitted_at)
    """,
]

PAPER_FILLS_SQL = """
CREATE TABLE IF NOT EXISTS paper_fills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES paper_orders(id),
    leg_name TEXT NOT NULL,
    option_type TEXT NOT NULL,
    strike REAL NOT NULL,
    expiry TEXT NOT NULL,
    action TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    fill_price REAL NOT NULL,
    bid_at_fill REAL NOT NULL,
    ask_at_fill REAL NOT NULL,
    mid_at_fill REAL NOT NULL,
    iv_at_fill REAL,
    delta_at_fill REAL,
    filled_at TEXT NOT NULL
)
"""

PAPER_FILLS_INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS idx_paper_fills_order
    ON paper_fills (order_id)
    """,
]

PAPER_POSITIONS_SQL = """
CREATE TABLE IF NOT EXISTS paper_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    open_order_id INTEGER NOT NULL REFERENCES paper_orders(id),
    status TEXT NOT NULL DEFAULT 'open',
    legs TEXT NOT NULL,
    entry_price REAL NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    max_profit REAL,
    max_loss REAL,
    current_mark REAL,
    unrealized_pnl REAL DEFAULT 0.0,
    last_mark_at TEXT,
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    close_reason TEXT,
    close_order_id INTEGER REFERENCES paper_orders(id),
    metadata TEXT DEFAULT '{}'
)
"""

PAPER_POSITIONS_INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS idx_paper_positions_strategy
    ON paper_positions (strategy_id, status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_paper_positions_open
    ON paper_positions (status) WHERE status = 'open'
    """,
]

PAPER_TRADES_SQL = """
CREATE TABLE IF NOT EXISTS paper_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    position_id INTEGER NOT NULL REFERENCES paper_positions(id),
    entry_date TEXT NOT NULL,
    exit_date TEXT NOT NULL,
    holding_days INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL NOT NULL,
    realized_pnl REAL NOT NULL,
    total_pnl REAL NOT NULL,
    fees REAL NOT NULL DEFAULT 0.0,
    slippage_cost REAL NOT NULL DEFAULT 0.0,
    settlement_type TEXT,
    close_reason TEXT NOT NULL,
    legs_detail TEXT NOT NULL,
    metadata TEXT DEFAULT '{}'
)
"""

PAPER_TRADES_INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS idx_paper_trades_strategy
    ON paper_trades (strategy_id, exit_date)
    """,
]

PAPER_PORTFOLIO_SQL = """
CREATE TABLE IF NOT EXISTS paper_portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    starting_capital REAL NOT NULL,
    realized_pnl REAL NOT NULL DEFAULT 0.0,
    unrealized_pnl REAL NOT NULL DEFAULT 0.0,
    total_equity REAL NOT NULL,
    open_positions INTEGER NOT NULL DEFAULT 0,
    total_trades INTEGER NOT NULL DEFAULT 0,
    daily_pnl REAL NOT NULL DEFAULT 0.0,
    max_drawdown REAL NOT NULL DEFAULT 0.0,
    metadata TEXT DEFAULT '{}'
)
"""

PAPER_PORTFOLIO_INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS idx_paper_portfolio_date
    ON paper_portfolio (snapshot_date)
    """,
]

SLIPPAGE_LOG_SQL = """
CREATE TABLE IF NOT EXISTS slippage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    order_size INTEGER NOT NULL DEFAULT 1,
    bid REAL NOT NULL,
    ask REAL NOT NULL,
    mid REAL NOT NULL,
    fill_price REAL NOT NULL,
    slippage REAL NOT NULL,
    slippage_pct REAL NOT NULL,
    slippage_factor REAL NOT NULL,
    spread REAL NOT NULL,
    delta REAL,
    dte INTEGER,
    volume INTEGER,
    vix REAL,
    model_tier TEXT NOT NULL DEFAULT 'dynamic',
    strategy_id INTEGER REFERENCES strategies(id)
)
"""

SLIPPAGE_LOG_INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS idx_slippage_log_timestamp
    ON slippage_log (timestamp)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_slippage_log_strategy
    ON slippage_log (strategy_id, timestamp)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_slippage_log_model
    ON slippage_log (model_tier, timestamp)
    """,
]

ALL_TABLE_SQL = [
    PAPER_ORDERS_SQL,
    PAPER_FILLS_SQL,
    PAPER_POSITIONS_SQL,
    PAPER_TRADES_SQL,
    PAPER_PORTFOLIO_SQL,
    SLIPPAGE_LOG_SQL,
]

ALL_INDEX_SQL = (
    PAPER_ORDERS_INDEXES
    + PAPER_FILLS_INDEXES
    + PAPER_POSITIONS_INDEXES
    + PAPER_TRADES_INDEXES
    + PAPER_PORTFOLIO_INDEXES
    + SLIPPAGE_LOG_INDEXES
)


async def init_paper_tables(db: aiosqlite.Connection) -> None:
    """Create all paper trading tables and indexes idempotently.

    Safe to call multiple times -- uses CREATE TABLE IF NOT EXISTS
    and CREATE INDEX IF NOT EXISTS.

    Args:
        db: An active aiosqlite connection with foreign_keys enabled.
    """
    for sql in ALL_TABLE_SQL:
        await db.execute(sql)

    for sql in ALL_INDEX_SQL:
        await db.execute(sql)

    await db.commit()
    logger.debug("Paper trading tables initialized")
