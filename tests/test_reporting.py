"""Tests for strategy performance reporting and chart generation."""

import pytest
import pytest_asyncio
import aiosqlite
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import discord
import numpy as np

from src.discord_bot.reporting import StrategyReporter
from src.discord_bot.charts import (
    draw_equity_curve,
    draw_monte_carlo_fan,
    draw_wfa_windows,
    draw_strategy_comparison,
)


# -- Fixtures ----------------------------------------------------------------


@pytest_asyncio.fixture
async def db():
    """Create an in-memory SQLite database with all required tables."""
    conn = await aiosqlite.connect(":memory:")

    # Create required tables
    await conn.execute("""
        CREATE TABLE strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'idea',
            template_yaml TEXT,
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    await conn.execute("""
        CREATE TABLE backtest_results (
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
    await conn.execute("""
        CREATE TABLE signal_log (
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
    await conn.commit()

    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def store(db):
    """Create a mock Store wrapping the test database."""
    mock_store = MagicMock()
    mock_store._db = db
    mock_store._ensure_connected = MagicMock(return_value=db)
    return mock_store


@pytest_asyncio.fixture
async def manager(db):
    """Create a StrategyManager with test data."""
    from src.strategy.lifecycle import StrategyManager
    mgr = StrategyManager(db)
    await mgr.init_tables()
    return mgr


@pytest_asyncio.fixture
async def reporter(store, manager):
    """Create a StrategyReporter."""
    return StrategyReporter(store, manager)


async def _seed_strategy(manager, db, name="SPX IC", sharpe=1.5, rec="PROMOTE"):
    """Helper to seed a strategy with backtest results."""
    sid = await manager.create(name)
    await db.execute(
        """INSERT INTO backtest_results
           (strategy_id, run_at, start_date, end_date, num_trades,
            sharpe, sortino, max_drawdown, win_rate, profit_factor,
            wfa_passed, cpcv_pbo, cpcv_passed, dsr, dsr_passed,
            mc_5th_sharpe, mc_passed, all_passed, recommendation, full_result)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (str(sid), "2024-01-15T14:00:00", "2019-01-01", "2024-01-01",
         250, sharpe, 2.1, -5200.0, 0.72, 2.1,
         1, 0.32, 1, 0.97, 1, 0.85, 1, 1, rec, "{}"),
    )
    await db.commit()
    return sid


# -- Monthly Report Tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_monthly_report_empty(reporter):
    """Test monthly report with no strategies."""
    embeds = await reporter.monthly_report(date(2024, 1, 1))

    assert isinstance(embeds, list)
    assert len(embeds) >= 3  # header, scoreboard, accuracy, recommendations


@pytest.mark.asyncio
async def test_monthly_report_with_data(reporter, manager, db):
    """Test monthly report with strategy data."""
    await _seed_strategy(manager, db, "SPX IC", 1.5, "PROMOTE")
    await _seed_strategy(manager, db, "Put Spread", 0.8, "REFINE")

    embeds = await reporter.monthly_report(date(2024, 1, 1))

    assert len(embeds) >= 3
    # Check scoreboard has strategy data
    scoreboard = embeds[1]
    assert isinstance(scoreboard, discord.Embed)


# -- Strategy Comparison Tests -----------------------------------------------


@pytest.mark.asyncio
async def test_strategy_comparison_2_strategies(reporter, manager, db):
    """Test comparing 2 strategies."""
    await _seed_strategy(manager, db, "SPX IC", 1.5, "PROMOTE")
    await _seed_strategy(manager, db, "Put Spread", 0.8, "REFINE")

    embed = await reporter.strategy_comparison(["SPX IC", "Put Spread"])

    assert isinstance(embed, discord.Embed)
    assert "Comparison" in embed.title
    assert len(embed.fields) == 2


@pytest.mark.asyncio
async def test_strategy_comparison_not_found(reporter):
    """Test comparison with nonexistent strategy."""
    embed = await reporter.strategy_comparison(["Nonexistent"])

    assert isinstance(embed, discord.Embed)
    assert any("not found" in f.value for f in embed.fields)


@pytest.mark.asyncio
async def test_strategy_comparison_no_backtest(reporter, manager, db):
    """Test comparison when strategy has no backtest results."""
    await manager.create("New Strategy")

    embed = await reporter.strategy_comparison(["New Strategy"])

    assert isinstance(embed, discord.Embed)
    assert any("No backtest" in f.value for f in embed.fields)


# -- Signal Accuracy Tests ---------------------------------------------------


@pytest.mark.asyncio
async def test_signal_accuracy_empty(reporter):
    """Test signal accuracy with no data."""
    embed = await reporter.signal_accuracy_report(date(2024, 1, 1), date(2024, 1, 31))

    assert isinstance(embed, discord.Embed)
    assert any("No" in f.value for f in embed.fields)


@pytest.mark.asyncio
async def test_signal_accuracy_with_data(reporter, db):
    """Test signal accuracy with signal data."""
    # Seed some signals
    for i in range(5):
        await db.execute(
            """INSERT INTO signal_log (timestamp, signal_type, ticker, source, outcome)
               VALUES (?, ?, ?, ?, ?)""",
            (f"2024-01-{10 + i}T12:00:00", "gamma_flip", "SPY", "alerts", "win" if i < 3 else "loss"),
        )
    await db.commit()

    embed = await reporter.signal_accuracy_report(date(2024, 1, 1), date(2024, 1, 31))

    assert isinstance(embed, discord.Embed)
    assert any("Overall" in f.name for f in embed.fields)


# -- Chart Generation Tests --------------------------------------------------


def test_draw_equity_curve():
    """Test equity curve chart generation."""
    returns = np.random.randn(100) * 10
    result = draw_equity_curve(returns, "TestStrategy")

    assert result is not None
    assert isinstance(result, discord.File)
    assert "equity_" in result.filename


def test_draw_equity_curve_empty():
    """Test equity curve with empty data returns None."""
    result = draw_equity_curve([], "TestStrategy")
    assert result is None


def test_draw_monte_carlo_fan():
    """Test Monte Carlo fan chart generation."""
    np.random.seed(42)
    paths = np.cumsum(np.random.randn(100, 50) * 5, axis=1)
    result = draw_monte_carlo_fan(paths, "TestStrategy")

    assert result is not None
    assert isinstance(result, discord.File)
    assert "mc_fan_" in result.filename


def test_draw_monte_carlo_fan_empty():
    """Test MC fan chart with empty data returns None."""
    result = draw_monte_carlo_fan([], "TestStrategy")
    assert result is None


def test_draw_wfa_windows():
    """Test WFA window chart generation."""
    is_sharpes = [1.2, 1.5, 1.1, 0.9, 1.3]
    oos_sharpes = [0.8, 1.0, 0.7, 0.6, 0.9]

    result = draw_wfa_windows(is_sharpes, oos_sharpes, "TestStrategy")

    assert result is not None
    assert isinstance(result, discord.File)
    assert "wfa_" in result.filename


def test_draw_wfa_windows_empty():
    """Test WFA chart with empty data returns None."""
    result = draw_wfa_windows([], [], "TestStrategy")
    assert result is None


def test_draw_strategy_comparison():
    """Test strategy comparison chart generation."""
    metrics = [
        {"name": "IC", "sharpe": 1.5, "sortino": 2.1, "win_rate": 0.72, "profit_factor": 2.1},
        {"name": "Spread", "sharpe": 0.8, "sortino": 1.2, "win_rate": 0.65, "profit_factor": 1.5},
    ]

    result = draw_strategy_comparison(metrics)

    assert result is not None
    assert isinstance(result, discord.File)
    assert "comparison_" in result.filename


def test_draw_strategy_comparison_empty():
    """Test comparison chart with empty data returns None."""
    result = draw_strategy_comparison([])
    assert result is None


# -- Helpers for Paper Trading Tests -----------------------------------------


async def _create_paper_trades_table(db):
    """Create paper_trades table in the test DB."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            exit_date TEXT NOT NULL,
            total_pnl REAL NOT NULL DEFAULT 0,
            fees REAL NOT NULL DEFAULT 0,
            slippage REAL NOT NULL DEFAULT 0,
            slippage_cost REAL NOT NULL DEFAULT 0
        )
    """)
    await db.commit()


async def _seed_paper_trades(db, strategy_id, month="2024-01", count=10):
    """Seed paper trades for a strategy in the given month."""
    for i in range(count):
        day = min(i + 1, 28)
        pnl = 50.0 if i % 3 != 0 else -30.0  # ~67% win rate
        await db.execute(
            """INSERT INTO paper_trades
               (strategy_id, entry_date, exit_date, total_pnl, fees, slippage, slippage_cost)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (str(strategy_id), f"{month}-{day:02d}", f"{month}-{day:02d}",
             pnl, 1.50, 0.03, 0.60),
        )
    await db.commit()


async def _seed_paper_strategy(manager, db, name="Paper IC", sharpe=1.2,
                                rec="PROMOTE", paper_trade_count=10,
                                month="2024-01"):
    """Create a strategy in PAPER status with backtest results and paper trades."""
    from src.strategy.lifecycle import StrategyStatus

    sid = await manager.create(name)
    # Transition to PAPER: IDEA -> DEFINED -> BACKTEST -> PAPER
    await manager.transition(sid, StrategyStatus.DEFINED, reason="test")
    await manager.transition(sid, StrategyStatus.BACKTEST, reason="test")
    await manager.transition(sid, StrategyStatus.PAPER, reason="test")

    await db.execute(
        """INSERT INTO backtest_results
           (strategy_id, run_at, start_date, end_date, num_trades,
            sharpe, sortino, max_drawdown, win_rate, profit_factor,
            wfa_passed, cpcv_pbo, cpcv_passed, dsr, dsr_passed,
            mc_5th_sharpe, mc_passed, all_passed, recommendation, full_result)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (str(sid), "2024-01-15T14:00:00", "2019-01-01", "2024-01-01",
         250, sharpe, 2.1, -5200.0, 0.72, 2.1,
         1, 0.32, 1, 0.97, 1, 0.85, 1, 1, rec, "{}"),
    )
    await db.commit()

    if paper_trade_count > 0:
        await _seed_paper_trades(db, sid, month=month, count=paper_trade_count)

    return sid


# -- Monthly Report Paper Summary Tests (Step 5b) ---------------------------


@pytest.mark.asyncio
async def test_monthly_report_includes_paper_summary(reporter, manager, db):
    """Verify paper summary embed is appended when paper trades exist."""
    await _create_paper_trades_table(db)
    await _seed_paper_strategy(manager, db, name="Paper IC", paper_trade_count=10)

    embeds = await reporter.monthly_report(date(2024, 1, 1))

    # Should have header + scoreboard + accuracy + recommendations + paper summary
    assert len(embeds) == 5
    paper_embed = embeds[4]
    assert paper_embed.title == "Paper Trading Summary"


@pytest.mark.asyncio
async def test_monthly_report_no_paper_table(reporter, manager, db):
    """Verify graceful behavior when paper_trades table does not exist."""
    await _seed_strategy(manager, db, "SPX IC", 1.5, "PROMOTE")

    embeds = await reporter.monthly_report(date(2024, 1, 1))

    # Should only have the 4 standard embeds (no paper summary)
    assert len(embeds) == 4
    assert all(e.title != "Paper Trading Summary" for e in embeds)


@pytest.mark.asyncio
async def test_monthly_report_no_paper_trades(reporter, manager, db):
    """Verify None returned when table exists but has no trades for the month."""
    await _create_paper_trades_table(db)
    await _seed_strategy(manager, db, "SPX IC", 1.5, "PROMOTE")

    embeds = await reporter.monthly_report(date(2024, 1, 1))

    # No paper trades, so no paper summary embed
    assert len(embeds) == 4
    assert all(e.title != "Paper Trading Summary" for e in embeds)


@pytest.mark.asyncio
async def test_monthly_report_paper_summary_fields(reporter, manager, db):
    """Verify paper summary embed contains all 6 expected fields."""
    await _create_paper_trades_table(db)
    await _seed_paper_strategy(manager, db, name="Paper IC", paper_trade_count=10)

    embeds = await reporter.monthly_report(date(2024, 1, 1))

    paper_embed = [e for e in embeds if e.title == "Paper Trading Summary"]
    assert len(paper_embed) == 1
    embed = paper_embed[0]

    field_names = [f.name for f in embed.fields]
    assert "Total Trades" in field_names
    assert "Net P/L" in field_names
    assert "Win Rate" in field_names
    assert "Strategies Active" in field_names
    assert "Avg Slippage" in field_names
    assert "Total Slip Cost" in field_names
    assert len(embed.fields) == 6


# -- Scoreboard Paper Info Tests (Step 5a) -----------------------------------


@pytest.mark.asyncio
async def test_scoreboard_shows_paper_info_for_paper_strategies(reporter, manager, db):
    """Verify scoreboard includes paper trade count and Sharpe for PAPER strategies."""
    await _create_paper_trades_table(db)
    await _seed_paper_strategy(manager, db, name="Paper IC", paper_trade_count=10)

    embeds = await reporter.monthly_report(date(2024, 1, 1))
    scoreboard = embeds[1]

    # The single strategy field should contain paper info
    assert len(scoreboard.fields) >= 1
    field_value = scoreboard.fields[0].value
    assert "Paper: 10 trades" in field_value
    assert "Sharpe" in field_value  # paper Sharpe should be present (10 >= 5)


@pytest.mark.asyncio
async def test_scoreboard_no_paper_info_for_non_paper_strategies(reporter, manager, db):
    """Verify scoreboard does not include paper info for non-PAPER strategies."""
    await _create_paper_trades_table(db)
    await _seed_strategy(manager, db, "SPX IC", 1.5, "PROMOTE")

    embeds = await reporter.monthly_report(date(2024, 1, 1))
    scoreboard = embeds[1]

    # The strategy is in IDEA status, not PAPER, so no paper info
    assert len(scoreboard.fields) >= 1
    field_value = scoreboard.fields[0].value
    assert "Paper:" not in field_value
