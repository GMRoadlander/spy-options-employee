"""Database schema for the risk analytics system.

4 tables:
- risk_snapshots: periodic risk state snapshots (every 2 min during market hours)
- risk_alerts: persistent alert audit trail
- risk_check_log: pre-trade check audit trail
- risk_limit_changes: track limit changes (regime transitions, manual)
"""

import logging

import aiosqlite

logger = logging.getLogger(__name__)

RISK_SNAPSHOTS_SQL = """
CREATE TABLE IF NOT EXISTS risk_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    portfolio_nav REAL NOT NULL,
    portfolio_delta REAL,
    portfolio_gamma REAL,
    portfolio_theta REAL,
    portfolio_vega REAL,
    dollar_delta REAL,
    dollar_gamma REAL,
    var_95 REAL,
    var_99 REAL,
    cvar_95 REAL,
    regime_state INTEGER,
    anomaly_score REAL,
    num_positions INTEGER,
    num_alerts INTEGER,
    snapshot_json TEXT
)
"""

RISK_ALERTS_SQL = """
CREATE TABLE IF NOT EXISTS risk_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    level TEXT NOT NULL,
    category TEXT NOT NULL,
    message TEXT NOT NULL,
    current_value REAL,
    limit_value REAL,
    resolved_at TEXT
)
"""

RISK_CHECK_LOG_SQL = """
CREATE TABLE IF NOT EXISTS risk_check_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    order_id INTEGER NOT NULL,
    strategy_id INTEGER,
    approved INTEGER NOT NULL,
    checks_json TEXT,
    regime_state INTEGER,
    anomaly_score REAL
)
"""

RISK_LIMIT_CHANGES_SQL = """
CREATE TABLE IF NOT EXISTS risk_limit_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    limit_name TEXT NOT NULL,
    old_value REAL,
    new_value REAL,
    reason TEXT
)
"""

RISK_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_risk_snapshots_ts ON risk_snapshots(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_risk_alerts_ts ON risk_alerts(timestamp, level)",
    "CREATE INDEX IF NOT EXISTS idx_risk_alerts_active ON risk_alerts(level) WHERE resolved_at IS NULL",
    "CREATE INDEX IF NOT EXISTS idx_risk_check_log_ts ON risk_check_log(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_risk_check_log_order ON risk_check_log(order_id)",
    "CREATE INDEX IF NOT EXISTS idx_risk_limit_changes_ts ON risk_limit_changes(timestamp)",
]

ALL_RISK_TABLE_SQL = [
    RISK_SNAPSHOTS_SQL,
    RISK_ALERTS_SQL,
    RISK_CHECK_LOG_SQL,
    RISK_LIMIT_CHANGES_SQL,
]


async def init_risk_tables(db: aiosqlite.Connection) -> None:
    """Create all risk tables and indexes idempotently.

    Safe to call multiple times (IF NOT EXISTS).

    Args:
        db: Active aiosqlite connection with foreign_keys enabled.
    """
    for sql in ALL_RISK_TABLE_SQL:
        await db.execute(sql)
    for sql in RISK_INDEXES:
        await db.execute(sql)
    await db.commit()
    logger.debug("Risk tables initialized")
