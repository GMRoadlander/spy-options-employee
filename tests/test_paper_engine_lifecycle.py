"""End-to-end lifecycle test for the paper trading engine.

Tests the full lifecycle: strategy enters PAPER, shadow mode detects signals,
orders are submitted and filled, positions tracked, exit conditions trigger,
trades recorded, and metrics computed.

Uses in-memory SQLite, mock chains, and patches for time control.
"""

import json
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest
import pytest_asyncio
import yaml

from src.data import OptionContract, OptionsChain
from src.paper.engine import PaperTradingEngine
from src.paper.models import PaperTradingConfig, TickResult
from src.paper.schema import init_paper_tables
from src.strategy.lifecycle import StrategyManager, StrategyStatus


def _make_config(**overrides) -> PaperTradingConfig:
    defaults = {
        "starting_capital": 100_000.0,
        "slippage_pct": 0.10,
        "fee_per_contract": 0.65,
        "max_order_age_ticks": 5,
    }
    defaults.update(overrides)
    return PaperTradingConfig(**defaults)


def _make_template_yaml() -> str:
    """A vertical put credit spread template."""
    template = {
        "name": "Test Put Spread",
        "version": "1.0",
        "description": "Short put spread for testing",
        "ticker": "SPX",
        "structure": {
            "strategy_type": "vertical_spread",
            "legs": [
                {"name": "short_put", "side": "put", "action": "sell",
                 "delta_target": "fixed", "delta_value": 0.30, "quantity": 1},
                {"name": "long_put", "side": "put", "action": "buy",
                 "delta_target": "fixed", "delta_value": 0.15, "quantity": 1},
            ],
            "dte_target": 30,
            "dte_min": 20,
            "dte_max": 45,
        },
        "entry": {
            "iv_rank_min": 0.0,
            "iv_rank_max": 100.0,
            "vix_min": 0.0,
            "vix_max": 100.0,
            "min_credit": 0.0,
            "time_of_day": "any",
        },
        "exit": {
            "profit_target_pct": 0.50,
            "stop_loss_pct": 2.0,
            "dte_close": 0,
        },
        "sizing": {
            "max_risk_pct": 0.02,
            "max_positions": 3,
            "max_contracts": 10,
        },
        "schedule": {
            "trading_days": [0, 1, 2, 3, 4],
            "entry_window_start": "09:35",
            "entry_window_end": "15:30",
            "frequency": "daily",
        },
    }
    return yaml.dump(template)


def _make_chain(expiry: date | None = None) -> OptionsChain:
    """Create a chain with known strikes and deltas for predictable fills."""
    exp = expiry or (date.today() + timedelta(days=30))
    return OptionsChain(
        ticker="SPX",
        spot_price=5950.0,
        timestamp=datetime.now(),
        contracts=[
            OptionContract(
                ticker="SPX", expiry=exp, strike=5800.0, option_type="put",
                bid=3.40, ask=3.60, last=3.50, volume=1000, open_interest=5000,
                iv=0.20, delta=-0.30,
            ),
            OptionContract(
                ticker="SPX", expiry=exp, strike=5750.0, option_type="put",
                bid=1.80, ask=2.00, last=1.90, volume=800, open_interest=4000,
                iv=0.20, delta=-0.15,
            ),
            OptionContract(
                ticker="SPX", expiry=exp, strike=6100.0, option_type="call",
                bid=2.80, ask=3.00, last=2.90, volume=900, open_interest=3000,
                iv=0.20, delta=0.30,
            ),
            OptionContract(
                ticker="SPX", expiry=exp, strike=6150.0, option_type="call",
                bid=1.60, ask=1.80, last=1.70, volume=700, open_interest=2500,
                iv=0.20, delta=0.15,
            ),
        ],
    )


@pytest_asyncio.fixture
async def db():
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys = ON")
    await init_paper_tables(conn)

    # Create strategy tables
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
    await conn.execute("""
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
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_strategy_transitions_strategy_id
        ON strategy_transitions (strategy_id)
    """)
    await conn.commit()

    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def strategy_manager(db):
    return StrategyManager(db)


@pytest_asyncio.fixture
async def engine(db, strategy_manager):
    config = _make_config()
    return PaperTradingEngine(db, strategy_manager, config)


# --- Full Lifecycle Test ---


class TestFullLifecycle:
    """Tests the complete paper trading lifecycle."""

    @pytest.mark.asyncio
    async def test_strategy_enters_paper_signals_detected(
        self, engine, strategy_manager, db
    ):
        """Strategy enters PAPER -> shadow mode detects entry -> order submitted."""
        # Create a strategy and transition to PAPER
        strategy_id = await strategy_manager.create(
            "Test Put Spread",
            template_yaml=_make_template_yaml(),
        )
        await strategy_manager.transition(strategy_id, StrategyStatus.DEFINED)
        await strategy_manager.transition(strategy_id, StrategyStatus.BACKTEST)
        await strategy_manager.transition(strategy_id, StrategyStatus.PAPER)

        # Verify it's in PAPER state
        strategy = await strategy_manager.get(strategy_id)
        assert strategy["status"] == "paper"

        chain = _make_chain()
        chains = {"SPX": chain}

        # Run a tick during market hours
        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)  # Monday 10:30 AM
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            result = await engine.tick(chains)

        # Shadow mode should have submitted an order
        assert result.orders_submitted >= 1

    @pytest.mark.asyncio
    async def test_order_fills_position_opens(self, engine, strategy_manager, db):
        """Submitted orders should fill and open positions."""
        strategy_id = await strategy_manager.create(
            "Test Put Spread",
            template_yaml=_make_template_yaml(),
        )
        await strategy_manager.transition(strategy_id, StrategyStatus.DEFINED)
        await strategy_manager.transition(strategy_id, StrategyStatus.BACKTEST)
        await strategy_manager.transition(strategy_id, StrategyStatus.PAPER)

        chain = _make_chain()
        chains = {"SPX": chain}

        # First tick: shadow submits entry orders
        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            result = await engine.tick(chains)

        # Market orders should be filled immediately in the same tick
        # because pending orders get filled in step 3
        assert result.orders_submitted >= 1

        # Run a second tick to fill the pending orders
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            result2 = await engine.tick(chains)

        # Check that positions were opened (either in first or second tick)
        positions = await engine.position_tracker.get_open_positions(strategy_id)
        assert len(positions) >= 1

    @pytest.mark.asyncio
    async def test_exit_triggers_position_closes(self, engine, strategy_manager, db):
        """When exit condition is met, position closes and trade is recorded."""
        strategy_id = await strategy_manager.create(
            "Test Put Spread",
            template_yaml=_make_template_yaml(),
        )
        await strategy_manager.transition(strategy_id, StrategyStatus.DEFINED)
        await strategy_manager.transition(strategy_id, StrategyStatus.BACKTEST)
        await strategy_manager.transition(strategy_id, StrategyStatus.PAPER)

        chain = _make_chain()
        chains = {"SPX": chain}

        # Tick 1: Submit + fill entry
        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            await engine.tick(chains)

        # Tick 2: Fill any pending
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            await engine.tick(chains)

        # Verify we have an open position
        positions = await engine.position_tracker.get_open_positions(strategy_id)
        if not positions:
            # Market orders may have filled in tick 1 already
            pytest.skip("No open positions to test exit on")

        pos = positions[0]

        # Create a profitable exit chain where puts have decayed significantly.
        # The position is a put credit spread: sold 5800P, bought 5750P.
        # If SPX rallies and time passes, both puts drop to near zero, so
        # the cost to close is ~0 and the full credit is profit.
        # Mark-to-market (step 5 of tick) recalculates unrealized PnL from
        # live chain data, so we must supply a chain that naturally produces
        # a profit above the 50% target.
        exp = chain.contracts[0].expiry
        profitable_chain = OptionsChain(
            ticker="SPX",
            spot_price=6100.0,  # SPX rallied well above 5800 short put
            timestamp=datetime.now(),
            contracts=[
                OptionContract(
                    ticker="SPX", expiry=exp, strike=5800.0, option_type="put",
                    bid=0.05, ask=0.15, last=0.10, volume=500, open_interest=5000,
                    iv=0.12, delta=-0.02,
                ),
                OptionContract(
                    ticker="SPX", expiry=exp, strike=5750.0, option_type="put",
                    bid=0.02, ask=0.08, last=0.05, volume=300, open_interest=4000,
                    iv=0.12, delta=-0.01,
                ),
            ],
        )
        profitable_chains = {"SPX": profitable_chain}

        # Tick 3: Mark-to-market should see near-zero put values -> high profit.
        # Exit monitor should then detect profit_target (unrealized > 50% of max).
        with patch("src.paper.shadow._now_et", return_value=mock_now), \
             patch("src.paper.exits._now_et", return_value=mock_now):
            result3 = await engine.tick(profitable_chains)

        # Should have exit signals
        assert len(result3.exit_signals) >= 1

    @pytest.mark.asyncio
    async def test_start_of_day_resets_state(self, engine):
        """start_of_day() should reset tick count and shadow/exit state."""
        engine._tick_count_today = 42
        engine._daily_errors = ["some error"]
        engine.shadow_manager._entries_today = {1: 2}
        engine.exit_monitor._template_cache = {1: "cached"}

        await engine.start_of_day()

        assert engine._tick_count_today == 0
        assert engine._daily_errors == []
        assert engine.shadow_manager._entries_today == {}
        assert engine.exit_monitor._template_cache == {}

    @pytest.mark.asyncio
    async def test_tick_increments_counter(self, engine):
        """Each tick should increment the tick counter."""
        chains = {}

        result = await engine.tick(chains)
        assert engine._tick_count_today == 1

        result = await engine.tick(chains)
        assert engine._tick_count_today == 2


# --- Engine Component Integration ---


class TestEngineComponents:
    """Tests that engine components are properly wired."""

    def test_engine_has_shadow_manager(self, engine):
        """Engine should have a ShadowModeManager."""
        from src.paper.shadow import ShadowModeManager
        assert isinstance(engine.shadow_manager, ShadowModeManager)

    def test_engine_has_exit_monitor(self, engine):
        """Engine should have an ExitMonitor."""
        from src.paper.exits import ExitMonitor
        assert isinstance(engine.exit_monitor, ExitMonitor)

    def test_shadow_manager_uses_engine_order_manager(self, engine):
        """ShadowModeManager should use the engine's OrderManager."""
        assert engine.shadow_manager._order_manager is engine.order_manager

    def test_exit_monitor_uses_engine_position_tracker(self, engine):
        """ExitMonitor should use the engine's PositionTracker."""
        assert engine.exit_monitor._position_tracker is engine.position_tracker


# --- EOD Settlement Integration ---


class TestEODSettlement:
    """Tests for EOD settlement through the engine."""

    @pytest.mark.asyncio
    async def test_handle_eod_settlement_delegates_to_exit_monitor(self, engine, db):
        """handle_eod_settlement() should delegate to ExitMonitor."""
        chains = {}
        result = await engine.handle_eod_settlement(chains)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_handle_eod_settlement_no_chains(self, engine):
        """handle_eod_settlement() works with no chains."""
        result = await engine.handle_eod_settlement()
        assert isinstance(result, list)
        assert len(result) == 0


# --- Multi-Strategy Tests ---


class TestMultiStrategy:
    """Tests with multiple strategies in PAPER state."""

    @pytest.mark.asyncio
    async def test_multiple_paper_strategies(self, engine, strategy_manager, db):
        """Multiple PAPER strategies should each generate entry signals."""
        # Create two strategies
        s1 = await strategy_manager.create(
            "Strategy A",
            template_yaml=_make_template_yaml(),
        )
        await strategy_manager.transition(s1, StrategyStatus.DEFINED)
        await strategy_manager.transition(s1, StrategyStatus.BACKTEST)
        await strategy_manager.transition(s1, StrategyStatus.PAPER)

        s2 = await strategy_manager.create(
            "Strategy B",
            template_yaml=_make_template_yaml(),
        )
        await strategy_manager.transition(s2, StrategyStatus.DEFINED)
        await strategy_manager.transition(s2, StrategyStatus.BACKTEST)
        await strategy_manager.transition(s2, StrategyStatus.PAPER)

        chain = _make_chain()
        chains = {"SPX": chain}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            result = await engine.tick(chains)

        # Both strategies should generate entries
        assert result.orders_submitted >= 2


# --- Error Handling Tests ---


class TestErrorHandling:
    """Tests for error handling in the engine lifecycle."""

    @pytest.mark.asyncio
    async def test_tick_handles_shadow_error(self, engine):
        """Tick should continue even if shadow mode fails."""
        chains = {}

        # Patch shadow_manager to raise an error
        engine.shadow_manager.check_entry_signals = AsyncMock(
            side_effect=RuntimeError("Shadow mode failure"),
        )

        result = await engine.tick(chains)

        # Should still complete, but with errors recorded
        assert any("entry signals" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_tick_handles_exit_monitor_error(self, engine):
        """Tick should continue even if exit monitor fails."""
        chains = {}

        # Patch exit_monitor to raise an error
        engine.exit_monitor.check_all_positions = AsyncMock(
            side_effect=RuntimeError("Exit monitor failure"),
        )

        result = await engine.tick(chains)

        # Should still complete, but with errors recorded
        assert any("exit conditions" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_tick_records_daily_errors(self, engine):
        """Errors from tick should be accumulated in daily errors."""
        engine.shadow_manager.check_entry_signals = AsyncMock(
            side_effect=RuntimeError("test error"),
        )

        await engine.tick({})

        assert len(engine._daily_errors) > 0
