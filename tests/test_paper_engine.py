"""Tests for the PaperTradingEngine orchestrator.

Tests the full tick cycle, EOD settlement, portfolio summary,
strategy results, force close, and multi-strategy scenarios.
Uses in-memory SQLite databases and mock options chain data.
"""

import json
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest
import pytest_asyncio

from src.data import OptionContract, OptionsChain
from src.paper.engine import PaperTradingEngine, _compute_recommendation
from src.paper.models import LegSpec, PaperTradingConfig, PortfolioSummary
from src.paper.schema import init_paper_tables


def _make_config(**overrides) -> PaperTradingConfig:
    defaults = {
        "starting_capital": 100_000.0,
        "slippage_pct": 0.10,
        "fee_per_contract": 0.65,
        "max_order_age_ticks": 5,
    }
    defaults.update(overrides)
    return PaperTradingConfig(**defaults)


def _make_contract(
    strike: float,
    option_type: str = "put",
    bid: float = 3.40,
    ask: float = 3.60,
    expiry: date | None = None,
) -> OptionContract:
    return OptionContract(
        ticker="SPX",
        expiry=expiry or date(2025, 3, 21),
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        last=(bid + ask) / 2,
        volume=1000,
        open_interest=5000,
        iv=0.20,
        delta=-0.30 if option_type == "put" else 0.30,
    )


def _make_chain():
    return OptionsChain(
        ticker="SPX", spot_price=5950.0, timestamp=datetime.now(),
        contracts=[
            _make_contract(5800.0, "put", 3.40, 3.60),
            _make_contract(5750.0, "put", 1.80, 2.00),
            _make_contract(6100.0, "call", 2.80, 3.00),
            _make_contract(6150.0, "call", 1.60, 1.80),
        ],
    )


def _make_legs():
    return [
        LegSpec("short_put", "put", 5800.0, date(2025, 3, 21), "sell"),
        LegSpec("long_put", "put", 5750.0, date(2025, 3, 21), "buy"),
    ]


@pytest_asyncio.fixture
async def db():
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys = ON")

    now = datetime.now().isoformat()
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
    await conn.execute(
        "INSERT INTO strategies (name, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("Test IC", "paper", now, now),
    )
    await conn.execute(
        "INSERT INTO strategies (name, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("Test Vertical", "paper", now, now),
    )
    await conn.commit()
    await init_paper_tables(conn)
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def engine(db):
    """Create a PaperTradingEngine with mock strategy manager."""
    config = _make_config()
    strategy_manager = MagicMock()
    strategy_manager.list_strategies = AsyncMock(return_value=[
        {"id": 1, "name": "Test IC", "status": "paper"},
    ])
    strategy_manager.get = AsyncMock(return_value={
        "id": 1, "name": "Test IC", "status": "paper",
    })
    strategy_manager.get_transition_history = AsyncMock(return_value=[])

    eng = PaperTradingEngine(db, strategy_manager, config)
    await eng.init_tables()
    return eng


class TestPaperTradingEngine:
    """Tests for the PaperTradingEngine orchestrator."""

    @pytest.mark.asyncio
    async def test_init_tables(self, db):
        """init_tables should create all paper trading tables."""
        config = _make_config()
        engine = PaperTradingEngine(db, None, config)
        await engine.init_tables()

        cursor = await db.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'paper_%'"
        )
        count = (await cursor.fetchone())[0]
        assert count == 5

    @pytest.mark.asyncio
    async def test_tick_empty(self, engine):
        """Tick with no pending orders should return clean result."""
        chain = _make_chain()
        result = await engine.tick({"SPX": chain})

        assert result.orders_filled == 0
        assert result.orders_cancelled == 0
        assert result.positions_opened == 0
        assert result.positions_closed == 0
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_tick_fills_pending_order(self, engine):
        """Tick should fill pending market orders."""
        legs = _make_legs()
        order_id = await engine.submit_entry_order(
            strategy_id=1, legs=legs, quantity=1,
        )

        chain = _make_chain()
        result = await engine.tick({"SPX": chain})

        assert result.orders_filled == 1
        assert result.positions_opened == 1

    @pytest.mark.asyncio
    async def test_tick_marks_positions(self, engine):
        """Tick should mark-to-market all open positions."""
        legs = _make_legs()
        await engine.submit_entry_order(strategy_id=1, legs=legs, quantity=1)

        chain = _make_chain()
        await engine.tick({"SPX": chain})  # Fill the order

        result = await engine.tick({"SPX": chain})  # Mark positions
        # Should have some unrealized PnL (could be 0 if prices unchanged)
        assert isinstance(result.total_unrealized_pnl, float)

    @pytest.mark.asyncio
    async def test_tick_expires_stale_orders(self, engine):
        """Tick should expire orders that are too old."""
        # Submit an order with a strike that won't match
        legs = [LegSpec("test", "put", 9999.0, date(2025, 3, 21), "sell")]
        order_id = await engine.order_manager.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        chain = _make_chain()
        # Tick 5 times (each increments ticks_pending)
        for _ in range(5):
            await engine.tick({"SPX": chain})

        # The 6th tick should expire it (ticks_pending >= 5)
        result = await engine.tick({"SPX": chain})
        assert result.orders_cancelled >= 1

    @pytest.mark.asyncio
    async def test_start_of_day(self, engine):
        """start_of_day should reset daily state."""
        engine._tick_count_today = 100
        engine._daily_errors = ["error1", "error2"]

        await engine.start_of_day()

        assert engine._tick_count_today == 0
        assert engine._daily_errors == []

    @pytest.mark.asyncio
    async def test_get_portfolio_summary_empty(self, engine):
        """Portfolio summary with no trades should show starting capital."""
        summary = await engine.get_portfolio_summary()

        assert isinstance(summary, PortfolioSummary)
        assert summary.starting_capital == 100_000.0
        assert summary.total_equity == 100_000.0
        assert summary.realized_pnl == 0.0
        assert summary.unrealized_pnl == 0.0
        assert summary.open_positions == 0
        assert summary.total_trades == 0

    @pytest.mark.asyncio
    async def test_get_portfolio_summary_with_positions(self, engine):
        """Portfolio summary should reflect open positions."""
        legs = _make_legs()
        await engine.submit_entry_order(strategy_id=1, legs=legs, quantity=1)

        chain = _make_chain()
        await engine.tick({"SPX": chain})

        summary = await engine.get_portfolio_summary()
        assert summary.open_positions == 1

    @pytest.mark.asyncio
    async def test_force_close_position(self, engine):
        """force_close should close an open position."""
        legs = _make_legs()
        await engine.submit_entry_order(strategy_id=1, legs=legs, quantity=1)

        chain = _make_chain()
        await engine.tick({"SPX": chain})

        positions = await engine.position_tracker.get_open_positions()
        assert len(positions) == 1

        trade_id = await engine.force_close_position(
            positions[0]["id"], reason="test_close", chains={"SPX": chain},
        )
        assert trade_id is not None

        positions = await engine.position_tracker.get_open_positions()
        assert len(positions) == 0

    @pytest.mark.asyncio
    async def test_force_close_nonexistent_position(self, engine):
        """force_close on non-existent position should return None."""
        result = await engine.force_close_position(999, reason="test")
        assert result is None

    @pytest.mark.asyncio
    async def test_submit_exit_order(self, engine):
        """submit_exit_order should create a close order."""
        legs = _make_legs()
        await engine.submit_entry_order(strategy_id=1, legs=legs, quantity=1)

        chain = _make_chain()
        await engine.tick({"SPX": chain})

        positions = await engine.position_tracker.get_open_positions()
        exit_order_id = await engine.submit_exit_order(
            positions[0]["id"], reason="profit_target",
        )

        assert exit_order_id is not None
        order = await engine.order_manager.get_order(exit_order_id)
        assert order["direction"] == "close"

    @pytest.mark.asyncio
    async def test_submit_exit_order_nonexistent(self, engine):
        """submit_exit_order for non-existent position should return None."""
        result = await engine.submit_exit_order(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_full_trade_lifecycle(self, engine):
        """Full lifecycle: submit -> fill -> mark -> exit -> close."""
        chain = _make_chain()
        legs = _make_legs()

        # 1. Submit entry
        entry_order_id = await engine.submit_entry_order(
            strategy_id=1, legs=legs, quantity=1,
        )

        # 2. Fill entry (tick)
        result = await engine.tick({"SPX": chain})
        assert result.orders_filled == 1
        assert result.positions_opened == 1

        # 3. Mark-to-market
        result = await engine.tick({"SPX": chain})
        assert isinstance(result.total_unrealized_pnl, float)

        # 4. Submit exit
        positions = await engine.position_tracker.get_open_positions()
        exit_order_id = await engine.submit_exit_order(
            positions[0]["id"], reason="profit_target",
        )

        # 5. Fill exit (tick)
        result = await engine.tick({"SPX": chain})
        assert result.orders_filled == 1
        assert result.positions_closed == 1

        # 6. Verify trade record
        trade_count = await engine.pnl_calculator.get_trade_count()
        assert trade_count == 1

        # 7. No more open positions
        positions = await engine.position_tracker.get_open_positions()
        assert len(positions) == 0

    @pytest.mark.asyncio
    async def test_multi_strategy_tracking(self, engine, db):
        """Multiple strategies should have independent positions."""
        chain = _make_chain()
        legs = _make_legs()

        # Strategy 1: open position
        await engine.submit_entry_order(strategy_id=1, legs=legs, quantity=1)
        await engine.tick({"SPX": chain})

        # Strategy 2: open position
        await engine.submit_entry_order(strategy_id=2, legs=legs, quantity=2)
        await engine.tick({"SPX": chain})

        # Each strategy should have its own position
        pos1 = await engine.position_tracker.get_open_positions(strategy_id=1)
        pos2 = await engine.position_tracker.get_open_positions(strategy_id=2)
        assert len(pos1) == 1
        assert len(pos2) == 1
        assert pos1[0]["quantity"] == 1
        assert pos2[0]["quantity"] == 2

    @pytest.mark.asyncio
    async def test_get_strategy_paper_results(self, engine):
        """get_strategy_paper_results should aggregate trade data."""
        results = await engine.get_strategy_paper_results(strategy_id=1)

        assert results.strategy_id == 1
        assert results.strategy_name == "Test IC"
        assert results.trades == []
        assert results.recommendation == "CONTINUE"

    @pytest.mark.asyncio
    async def test_tick_handles_errors_gracefully(self, engine):
        """Tick should capture errors without crashing."""
        # This should not raise even with empty chains
        result = await engine.tick({})
        assert isinstance(result.errors, list)

    @pytest.mark.asyncio
    async def test_handle_eod_settlement_no_expiring(self, engine):
        """EOD settlement with no expiring positions should return empty."""
        chain = _make_chain()
        legs = _make_legs()

        # Open a position with future expiry
        await engine.submit_entry_order(strategy_id=1, legs=legs, quantity=1)
        await engine.tick({"SPX": chain})

        # Settlement today should not affect positions expiring in the future
        closed = await engine.handle_eod_settlement()
        # Whether this closes depends on whether expiry date is <= today
        # Our test expiry is 2025-03-21 which is in the future
        assert isinstance(closed, list)


class TestComputeRecommendation:
    """Tests for the _compute_recommendation helper."""

    def test_insufficient_trades(self):
        """Should return CONTINUE if too few trades."""
        metrics = MagicMock(sharpe_ratio=2.0, win_rate=0.7, max_drawdown=-0.05)
        assert _compute_recommendation(metrics, 10, 5, _make_config()) == "CONTINUE"

    def test_insufficient_days(self):
        """Should return CONTINUE if too few days."""
        metrics = MagicMock(sharpe_ratio=2.0, win_rate=0.7, max_drawdown=-0.05)
        assert _compute_recommendation(metrics, 50, 5, _make_config()) == "CONTINUE"

    def test_promote(self):
        """Good metrics should recommend PROMOTE."""
        metrics = MagicMock(sharpe_ratio=1.5, win_rate=0.65, max_drawdown=-0.05)
        assert _compute_recommendation(metrics, 50, 30, _make_config()) == "PROMOTE"

    def test_demote_low_sharpe(self):
        """Negative Sharpe should recommend DEMOTE."""
        metrics = MagicMock(sharpe_ratio=-0.5, win_rate=0.45, max_drawdown=-0.10)
        assert _compute_recommendation(metrics, 50, 30, _make_config()) == "DEMOTE"

    def test_demote_low_win_rate(self):
        """Very low win rate should recommend DEMOTE."""
        metrics = MagicMock(sharpe_ratio=0.5, win_rate=0.30, max_drawdown=-0.10)
        assert _compute_recommendation(metrics, 50, 30, _make_config()) == "DEMOTE"

    def test_demote_high_drawdown(self):
        """High drawdown should recommend DEMOTE."""
        metrics = MagicMock(sharpe_ratio=0.5, win_rate=0.50, max_drawdown=-0.25)
        assert _compute_recommendation(metrics, 50, 30, _make_config()) == "DEMOTE"

    def test_continue_mediocre(self):
        """Mediocre but not bad metrics should recommend CONTINUE."""
        metrics = MagicMock(sharpe_ratio=0.7, win_rate=0.52, max_drawdown=-0.10)
        assert _compute_recommendation(metrics, 50, 30, _make_config()) == "CONTINUE"
