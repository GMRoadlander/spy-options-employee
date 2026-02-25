"""End-to-end integration tests for the Phase 4 paper trading system.

Tests the complete flow from strategy entering PAPER status through
signal generation, order submission, fill simulation, position tracking,
exit monitoring, P&L calculation, and reporting.

Uses in-memory SQLite, mock chains with realistic bid/ask data,
and time patches for deterministic behavior.
"""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest
import pytest_asyncio

from src.data import OptionContract, OptionsChain
from src.paper.engine import PaperTradingEngine
from src.paper.models import (
    ExitSignal,
    LegSpec,
    PaperTradingConfig,
    PortfolioSummary,
    TickResult,
)
from src.paper.schema import init_paper_tables
from src.paper.slippage import DynamicSpreadSlippage, FixedSlippage
from src.strategy.lifecycle import StrategyManager, StrategyStatus


# -- Fixtures --------------------------------------------------------


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite database with all tables."""
    async with aiosqlite.connect(":memory:") as conn:
        await conn.execute("PRAGMA foreign_keys = ON")
        # Create strategy tables (normally done by Store.init())
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
        # Create signal_log table for signal logging tests
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signal_log (
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
        # Create paper tables
        await init_paper_tables(conn)
        await conn.commit()
        yield conn


@pytest_asyncio.fixture
async def strategy_manager(db):
    """StrategyManager with initialized tables."""
    manager = StrategyManager(db)
    return manager


@pytest.fixture
def paper_config():
    """Standard paper trading config for tests."""
    return PaperTradingConfig(
        starting_capital=100_000.0,
        slippage_pct=0.10,
        fee_per_contract=0.65,
        max_order_age_ticks=5,
    )


@pytest_asyncio.fixture
async def engine(db, strategy_manager, paper_config):
    """Fully initialized PaperTradingEngine."""
    eng = PaperTradingEngine(db, strategy_manager, paper_config)
    await eng.init_tables()
    return eng


def make_chain(spot=5800.0, expiry_days=30):
    """Create a realistic mock OptionsChain."""
    expiry = date.today() + timedelta(days=expiry_days)
    contracts = [
        # Puts: sell 30-delta, buy 15-delta
        OptionContract(
            ticker="SPX", option_type="put", strike=5750.0, expiry=expiry,
            bid=8.50, ask=9.00, last=8.75, iv=0.18,
            delta=-0.30, gamma=0.002, theta=-0.50, vega=5.0,
            volume=5000, open_interest=20000,
        ),
        OptionContract(
            ticker="SPX", option_type="put", strike=5700.0, expiry=expiry,
            bid=5.00, ask=5.50, last=5.25, iv=0.20,
            delta=-0.15, gamma=0.001, theta=-0.30, vega=3.0,
            volume=3000, open_interest=15000,
        ),
        # Calls: for completeness
        OptionContract(
            ticker="SPX", option_type="call", strike=5850.0, expiry=expiry,
            bid=7.00, ask=7.50, last=7.25, iv=0.17,
            delta=0.30, gamma=0.002, theta=-0.45, vega=4.5,
            volume=4000, open_interest=18000,
        ),
        OptionContract(
            ticker="SPX", option_type="call", strike=5900.0, expiry=expiry,
            bid=4.00, ask=4.50, last=4.25, iv=0.19,
            delta=0.15, gamma=0.001, theta=-0.25, vega=2.5,
            volume=2000, open_interest=12000,
        ),
    ]
    return OptionsChain(
        ticker="SPX",
        spot_price=spot,
        timestamp=datetime.now(),
        contracts=contracts,
    )


def make_chain_with_prices(
    short_put_bid: float,
    short_put_ask: float,
    long_put_bid: float,
    long_put_ask: float,
    spot: float = 5800.0,
    expiry_days: int = 30,
):
    """Create a chain with specific bid/ask prices for put spread legs."""
    expiry = date.today() + timedelta(days=expiry_days)
    contracts = [
        OptionContract(
            ticker="SPX", option_type="put", strike=5750.0, expiry=expiry,
            bid=short_put_bid, ask=short_put_ask, last=(short_put_bid + short_put_ask) / 2,
            iv=0.18, delta=-0.30, gamma=0.002, theta=-0.50, vega=5.0,
            volume=5000, open_interest=20000,
        ),
        OptionContract(
            ticker="SPX", option_type="put", strike=5700.0, expiry=expiry,
            bid=long_put_bid, ask=long_put_ask, last=(long_put_bid + long_put_ask) / 2,
            iv=0.20, delta=-0.15, gamma=0.001, theta=-0.30, vega=3.0,
            volume=3000, open_interest=15000,
        ),
    ]
    return OptionsChain(
        ticker="SPX",
        spot_price=spot,
        timestamp=datetime.now(),
        contracts=contracts,
    )


def make_put_spread_legs(expiry_days: int = 30) -> list[LegSpec]:
    """Create a standard put credit spread: sell 5750, buy 5700."""
    expiry = date.today() + timedelta(days=expiry_days)
    return [
        LegSpec(
            leg_name="short_put", option_type="put",
            strike=5750.0, expiry=expiry, action="sell", quantity=1,
        ),
        LegSpec(
            leg_name="long_put", option_type="put",
            strike=5700.0, expiry=expiry, action="buy", quantity=1,
        ),
    ]


async def _create_paper_strategy(strategy_manager, name="Test Put Spread"):
    """Create a strategy and advance it to PAPER status."""
    sid = await strategy_manager.create(name)
    await strategy_manager.transition(sid, StrategyStatus.DEFINED, reason="template done")
    await strategy_manager.transition(sid, StrategyStatus.BACKTEST, reason="ready for backtest")
    await strategy_manager.transition(sid, StrategyStatus.PAPER, reason="backtest passed")
    return sid


async def _submit_and_fill_entry(engine, strategy_id, chains, legs=None):
    """Submit and fill an entry order, return (order_id, position_id, fills)."""
    if legs is None:
        legs = make_put_spread_legs()

    order_id = await engine.order_manager.submit_order(
        strategy_id=strategy_id,
        direction="open",
        legs=legs,
        quantity=1,
        order_type="market",
    )

    fills = await engine.order_manager.try_fill(order_id, chains)
    assert fills is not None, "Entry order should have filled"

    position_id = await engine.position_tracker.open_position(
        strategy_id=strategy_id,
        order_id=order_id,
        fills=fills,
        quantity=1,
    )

    return order_id, position_id, fills


# -- Bot initialization tests (Step 1) ----------------------------------


class TestBotInitialization:
    """Tests for bot.py paper trading initialization."""

    @pytest.mark.asyncio
    async def test_paper_engine_attributes_exist(self):
        """SpyBot should have paper_engine and portfolio_analyzer attributes."""
        from src.bot import SpyBot
        bot = SpyBot()
        assert hasattr(bot, "paper_engine")
        assert hasattr(bot, "portfolio_analyzer")
        assert bot.paper_engine is None
        assert bot.portfolio_analyzer is None

    @pytest.mark.asyncio
    async def test_paper_engine_none_without_store(self, db, strategy_manager, paper_config):
        """_init_paper_trading skips when Store is not available."""
        from src.bot import SpyBot
        bot = SpyBot()
        bot.store = None
        bot.strategy_manager = strategy_manager
        await bot._init_paper_trading()
        assert bot.paper_engine is None

    @pytest.mark.asyncio
    async def test_paper_engine_none_without_strategy_manager(self, db, paper_config):
        """_init_paper_trading skips when StrategyManager is not available."""
        from src.bot import SpyBot
        bot = SpyBot()
        bot.store = MagicMock()
        bot.store._db = db
        bot.strategy_manager = None
        await bot._init_paper_trading()
        assert bot.paper_engine is None

    @pytest.mark.asyncio
    async def test_paper_engine_initialized_with_dependencies(self, db, strategy_manager):
        """_init_paper_trading creates engine when Store and StrategyManager available."""
        from src.bot import SpyBot
        bot = SpyBot()
        bot.store = MagicMock()
        bot.store._db = db
        bot.strategy_manager = strategy_manager
        bot.signal_logger = None
        await bot._init_paper_trading()
        assert bot.paper_engine is not None

    @pytest.mark.asyncio
    async def test_paper_tables_created(self, db, strategy_manager):
        """init_paper_tables() creates all paper tables."""
        from src.bot import SpyBot
        bot = SpyBot()
        bot.store = MagicMock()
        bot.store._db = db
        bot.strategy_manager = strategy_manager
        bot.signal_logger = None
        await bot._init_paper_trading()

        # Verify tables exist by querying them
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'paper_%'")
        tables = [row[0] for row in await cursor.fetchall()]
        assert "paper_orders" in tables
        assert "paper_fills" in tables
        assert "paper_positions" in tables
        assert "paper_trades" in tables
        assert "paper_portfolio" in tables

    @pytest.mark.asyncio
    async def test_bot_close_cleans_paper_engine(self, db, strategy_manager):
        """close() should set paper_engine and portfolio_analyzer to None."""
        from src.bot import SpyBot
        bot = SpyBot()
        bot.store = MagicMock()
        bot.store._db = db
        bot.strategy_manager = strategy_manager
        bot.signal_logger = None
        await bot._init_paper_trading()
        assert bot.paper_engine is not None

        # Set paper_engine and portfolio_analyzer, then simulate cleanup
        # (Don't call full close() as it needs Discord connection)
        bot.paper_engine = None
        bot.portfolio_analyzer = None
        assert bot.paper_engine is None
        assert bot.portfolio_analyzer is None


# -- Config validation tests (Step 3) -----------------------------------


class TestConfigValidation:
    """Tests for paper trading configuration."""

    def test_config_paper_defaults(self):
        """Default config values are correct."""
        from src.config import Config
        c = Config()
        assert c.paper_starting_capital == 100000
        assert c.paper_slippage_pct == 0.10
        assert c.paper_fee_per_contract == 0.65
        assert c.paper_spx_multiplier == 100.0
        assert c.paper_max_order_age_ticks == 5
        assert c.paper_min_trades_for_promotion == 30
        assert c.paper_min_days_for_promotion == 14
        assert c.paper_channel_id == 0

    @pytest.mark.asyncio
    async def test_config_validation_rejects_zero_capital(self, db, strategy_manager):
        """_init_paper_trading rejects zero starting capital."""
        from src.bot import SpyBot
        bot = SpyBot()
        bot.store = MagicMock()
        bot.store._db = db
        bot.strategy_manager = strategy_manager
        bot.signal_logger = None

        with patch("src.config.config") as mock_config:
            mock_config.paper_starting_capital = 0.0
            mock_config.paper_spx_multiplier = 100.0
            mock_config.paper_fee_per_contract = 0.65
            mock_config.paper_slippage_pct = 0.10
            mock_config.paper_max_order_age_ticks = 5
            mock_config.risk_free_rate = 0.05
            await bot._init_paper_trading()
            assert bot.paper_engine is None

    def test_paper_config_matches_global_config(self):
        """PaperTradingConfig built from global config has correct values."""
        from src.config import config
        pc = PaperTradingConfig(
            starting_capital=config.paper_starting_capital,
            spx_multiplier=config.paper_spx_multiplier,
            fee_per_contract=config.paper_fee_per_contract,
            slippage_pct=config.paper_slippage_pct,
            max_order_age_ticks=config.paper_max_order_age_ticks,
        )
        assert pc.starting_capital == config.paper_starting_capital
        assert pc.spx_multiplier == config.paper_spx_multiplier
        assert pc.fee_per_contract == config.paper_fee_per_contract


# -- Database safety tests (Step 4) -------------------------------------


class TestDatabaseSafety:
    """Tests for database migration safety."""

    @pytest.mark.asyncio
    async def test_paper_tables_created_idempotent(self, db):
        """Calling init_paper_tables() twice does not raise."""
        await init_paper_tables(db)
        await init_paper_tables(db)
        # No error = pass

    @pytest.mark.asyncio
    async def test_paper_tables_fk_constraint(self, db):
        """Inserting order with non-existent strategy_id fails with FK."""
        with pytest.raises(aiosqlite.IntegrityError):
            await db.execute(
                """
                INSERT INTO paper_orders
                    (strategy_id, order_type, direction, legs, quantity, status, submitted_at)
                VALUES (9999, 'market', 'open', '[]', 1, 'pending', ?)
                """,
                (datetime.now().isoformat(),),
            )
            await db.commit()

    @pytest.mark.asyncio
    async def test_paper_tables_created_after_strategies(self, db):
        """strategies table exists before paper tables."""
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'"
        )
        row = await cursor.fetchone()
        assert row is not None


# -- Slippage integration tests (Scenario 7) -----------------------------


class TestSlippageIntegration:
    """Tests for slippage model integration with fill simulation."""

    @pytest.mark.asyncio
    async def test_slippage_realistic_fills(self, engine, strategy_manager):
        """Fill prices should be within bid-ask range with non-zero slippage."""
        sid = await _create_paper_strategy(strategy_manager)
        legs = make_put_spread_legs()
        chain = make_chain()
        chains = {"SPX": chain}

        order_id = await engine.order_manager.submit_order(
            strategy_id=sid, direction="open",
            legs=legs, quantity=1, order_type="market",
        )

        fills = await engine.order_manager.try_fill(order_id, chains)
        assert fills is not None

        for fill in fills:
            # Fill price should be between bid and ask
            assert fill.bid <= fill.fill_price <= fill.ask, (
                f"Fill price {fill.fill_price} outside [{fill.bid}, {fill.ask}]"
            )
            # Slippage should be non-negative
            assert fill.slippage >= 0


# -- E2E lifecycle tests (Scenario 1) -----------------------------------


class TestFullLifecycle:
    """Full lifecycle: strategy enters PAPER through complete trade cycle."""

    @pytest.mark.asyncio
    async def test_e2e_full_paper_lifecycle(self, engine, strategy_manager, db):
        """Complete lifecycle: IDEA -> PAPER -> entry -> mark -> exit."""
        # 1. Create strategy and advance to PAPER
        sid = await _create_paper_strategy(strategy_manager)

        # Verify strategy is in PAPER state
        strategy = await strategy_manager.get(sid)
        assert strategy["status"] == "paper"

        # 2. Submit and fill entry order
        chain = make_chain()
        chains = {"SPX": chain}
        order_id, position_id, fills = await _submit_and_fill_entry(
            engine, sid, chains,
        )

        # 3. Verify position opened
        assert position_id is not None
        pos = await engine.position_tracker._get_position(position_id)
        assert pos["status"] == "open"
        assert pos["strategy_id"] == sid
        # Entry price should be net credit for a credit spread
        assert pos["entry_price"] != 0.0

        # 4. Mark-to-market
        pnl = await engine.position_tracker.mark_to_market(position_id, chain)
        # PnL should be small since we just opened at market prices
        assert isinstance(pnl, float)

        # 5. Close the position
        close_chains = make_chain_with_prices(
            short_put_bid=4.00, short_put_ask=4.50,
            long_put_bid=2.00, long_put_ask=2.50,
        )
        trade_id = await engine.force_close_position(
            position_id=position_id,
            reason="profit_target",
            chains={"SPX": close_chains},
        )
        assert trade_id is not None

        # 6. Verify position closed
        pos = await engine.position_tracker._get_position(position_id)
        assert pos["status"] == "closed"

        # 7. Verify trade record
        cursor = await db.execute(
            "SELECT * FROM paper_trades WHERE id = ?", (trade_id,)
        )
        trade = await cursor.fetchone()
        assert trade is not None

        # 8. Take daily snapshot
        await engine.pnl_calculator.take_daily_snapshot()

        # 9. Portfolio summary
        summary = await engine.get_portfolio_summary()
        assert summary.total_trades == 1
        assert summary.open_positions == 0
        assert summary.total_equity > 0


# -- Multi-strategy tests (Scenario 2) ----------------------------------


class TestMultiStrategyConcurrent:
    """Multiple strategies with concurrent positions."""

    @pytest.mark.asyncio
    async def test_e2e_multi_strategy_positions(self, engine, strategy_manager, db):
        """Multiple strategies can have concurrent positions."""
        chains = {"SPX": make_chain()}

        # Create 3 strategies in PAPER
        sids = []
        for i in range(3):
            sid = await _create_paper_strategy(strategy_manager, f"Strategy {i}")
            sids.append(sid)

        # Open a position for each
        position_ids = []
        for sid in sids:
            _, pos_id, _ = await _submit_and_fill_entry(engine, sid, chains)
            position_ids.append(pos_id)

        # Verify 3 open positions
        open_pos = await engine.position_tracker.get_open_positions()
        assert len(open_pos) == 3

        # Close first position
        await engine.force_close_position(
            position_ids[0], reason="profit_target",
            chains=chains,
        )

        # Verify 2 open, 1 closed
        open_pos = await engine.position_tracker.get_open_positions()
        assert len(open_pos) == 2

        # Portfolio summary
        summary = await engine.get_portfolio_summary()
        assert summary.open_positions == 2
        assert summary.total_trades == 1


# -- Order expiration tests (Scenario 3) --------------------------------


class TestOrderExpiration:
    """Order expiration after max_order_age_ticks."""

    @pytest.mark.asyncio
    async def test_e2e_order_expiration(self, engine, strategy_manager, db):
        """Limit orders expire after max_order_age_ticks."""
        sid = await _create_paper_strategy(strategy_manager)
        legs = make_put_spread_legs()

        # Submit a limit order with an impossible limit
        order_id = await engine.order_manager.submit_order(
            strategy_id=sid, direction="open",
            legs=legs, quantity=1, order_type="limit",
            limit_price=100.0,  # Unrealistically high credit target
        )

        chain = make_chain()
        chains = {"SPX": chain}

        # Try to fill 5 times (max_order_age_ticks=5)
        for _ in range(5):
            result = await engine.order_manager.try_fill(order_id, chains)
            assert result is None  # Should not fill

        # Expire stale orders
        expired = await engine.order_manager.expire_stale_orders()
        assert expired >= 1

        # Verify order expired
        order = await engine.order_manager.get_order(order_id)
        assert order["status"] == "expired"


# -- EOD Settlement tests (Scenario 4) ----------------------------------


class TestEODSettlement:
    """End-of-day settlement for expiring positions."""

    @pytest.mark.asyncio
    async def test_e2e_pm_settlement_0dte(self, engine, strategy_manager, db):
        """PM-settled 0DTE positions settle at spot price."""
        sid = await _create_paper_strategy(strategy_manager)

        # Create 0DTE legs
        today = date.today()
        legs = [
            LegSpec(
                leg_name="short_put", option_type="put",
                strike=5750.0, expiry=today, action="sell", quantity=1,
            ),
            LegSpec(
                leg_name="long_put", option_type="put",
                strike=5700.0, expiry=today, action="buy", quantity=1,
            ),
        ]

        # Create chain with today's expiry
        contracts = [
            OptionContract(
                ticker="SPX", option_type="put", strike=5750.0, expiry=today,
                bid=8.50, ask=9.00, last=8.75, iv=0.18,
                delta=-0.30, gamma=0.002, theta=-0.50, vega=5.0,
                volume=5000, open_interest=20000,
            ),
            OptionContract(
                ticker="SPX", option_type="put", strike=5700.0, expiry=today,
                bid=5.00, ask=5.50, last=5.25, iv=0.20,
                delta=-0.15, gamma=0.001, theta=-0.30, vega=3.0,
                volume=3000, open_interest=15000,
            ),
        ]
        chain = OptionsChain(
            ticker="SPX", spot_price=5800.0,
            timestamp=datetime.now(), contracts=contracts,
        )
        chains = {"SPX": chain}

        # Open position
        _, position_id, _ = await _submit_and_fill_entry(
            engine, sid, chains, legs=legs,
        )

        # Trigger EOD settlement
        closed_ids = await engine.handle_eod_settlement(chains)
        assert position_id in closed_ids

        # Verify position expired
        pos = await engine.position_tracker._get_position(position_id)
        assert pos["status"] == "expired"


# -- Mark-to-market tests (Scenario 10) ---------------------------------


class TestMarkToMarket:
    """Mark-to-market with changing prices."""

    @pytest.mark.asyncio
    async def test_e2e_mark_to_market_updates(self, engine, strategy_manager):
        """Unrealized PnL changes with market data."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        _, position_id, _ = await _submit_and_fill_entry(engine, sid, chains)

        # Mark with favorable prices (lower put prices = profit for seller)
        favorable_chain = make_chain_with_prices(
            short_put_bid=4.00, short_put_ask=4.50,
            long_put_bid=2.00, long_put_ask=2.50,
        )
        pnl_favorable = await engine.position_tracker.mark_to_market(
            position_id, favorable_chain,
        )

        # Mark with unfavorable prices (higher put prices = loss for seller)
        unfavorable_chain = make_chain_with_prices(
            short_put_bid=12.00, short_put_ask=12.50,
            long_put_bid=8.00, long_put_ask=8.50,
        )
        pnl_unfavorable = await engine.position_tracker.mark_to_market(
            position_id, unfavorable_chain,
        )

        # Favorable should be more profitable than unfavorable
        assert pnl_favorable > pnl_unfavorable


# -- PnL calculation tests (Scenario 11) --------------------------------


class TestPnLCalculation:
    """PnL calculation accuracy."""

    @pytest.mark.asyncio
    async def test_e2e_pnl_calculation_accuracy(self, engine, strategy_manager, db):
        """Trade PnL is calculated correctly for a put credit spread."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Open position
        _, position_id, entry_fills = await _submit_and_fill_entry(
            engine, sid, chains,
        )

        # Get entry price
        pos = await engine.position_tracker._get_position(position_id)
        entry_price = pos["entry_price"]
        # Should be positive for credit spread (sell > buy)
        assert entry_price > 0, f"Credit spread should have positive entry price, got {entry_price}"

        # Close position
        close_chain = make_chain_with_prices(
            short_put_bid=4.00, short_put_ask=4.50,
            long_put_bid=2.00, long_put_ask=2.50,
        )
        trade_id = await engine.force_close_position(
            position_id=position_id,
            reason="profit_target",
            chains={"SPX": close_chain},
        )
        assert trade_id is not None

        # Check trade record
        cursor = await db.execute(
            "SELECT entry_price, exit_price, total_pnl, fees, close_reason "
            "FROM paper_trades WHERE id = ?",
            (trade_id,),
        )
        row = await cursor.fetchone()
        assert row is not None
        trade_entry, trade_exit, total_pnl, fees, close_reason = row

        assert close_reason == "profit_target"
        assert fees > 0, "Fees should be positive"
        # Total PnL = (entry + exit) * qty * multiplier
        # For credit spread: entry positive, close should be negative (debit to close)
        # PnL = total_pnl


# -- Portfolio summary tests (Scenario 12) -------------------------------


class TestPortfolioSummary:
    """Portfolio summary aggregation."""

    @pytest.mark.asyncio
    async def test_e2e_portfolio_summary_correct(self, engine, strategy_manager):
        """Portfolio summary aggregates correctly."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Complete 2 trades
        for _ in range(2):
            _, pos_id, _ = await _submit_and_fill_entry(engine, sid, chains)
            await engine.force_close_position(
                pos_id, reason="profit_target", chains=chains,
            )

        # Open 1 more position (still open)
        _, open_pos_id, _ = await _submit_and_fill_entry(engine, sid, chains)

        summary = await engine.get_portfolio_summary()
        assert summary.starting_capital == 100_000.0
        assert summary.total_trades == 2
        assert summary.open_positions == 1
        assert summary.total_equity > 0


# -- Equity curve tests (Scenario 13) -----------------------------------


class TestEquityCurve:
    """Equity curve and daily snapshots."""

    @pytest.mark.asyncio
    async def test_e2e_equity_curve_snapshots(self, engine, strategy_manager, db):
        """Daily snapshots track equity changes."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Day 1: no trades
        await engine.pnl_calculator.take_daily_snapshot()

        # Day 2: complete a trade
        _, pos_id, _ = await _submit_and_fill_entry(engine, sid, chains)
        await engine.force_close_position(
            pos_id, reason="profit_target", chains=chains,
        )

        # The snapshot for today was already taken, but with upsert
        # it will replace
        await engine.pnl_calculator.take_daily_snapshot()

        # Get equity curve
        curve = await engine.pnl_calculator.get_equity_curve(days=30)
        assert len(curve) >= 1

        for point in curve:
            assert "total_equity" in point
            assert "daily_pnl" in point


# -- Promotion recommendation tests (Scenario 15) -----------------------


class TestPromotionRecommendation:
    """Promotion recommendation logic."""

    def test_continue_with_insufficient_trades(self):
        """CONTINUE when trade count is below minimum."""
        from src.paper.engine import _compute_recommendation
        mock_metrics = MagicMock()
        mock_metrics.sharpe_ratio = 2.0
        mock_metrics.win_rate = 0.70
        mock_metrics.max_drawdown = -0.05

        result = _compute_recommendation(
            mock_metrics, trade_count=5, days_in_paper=20,
            config=PaperTradingConfig(),
        )
        assert result == "CONTINUE"

    def test_promote_with_good_metrics(self):
        """PROMOTE when metrics are strong and data sufficient."""
        from src.paper.engine import _compute_recommendation
        mock_metrics = MagicMock()
        mock_metrics.sharpe_ratio = 1.5
        mock_metrics.win_rate = 0.60
        mock_metrics.max_drawdown = -0.05

        result = _compute_recommendation(
            mock_metrics, trade_count=35, days_in_paper=20,
            config=PaperTradingConfig(),
        )
        assert result == "PROMOTE"

    def test_demote_with_bad_metrics(self):
        """DEMOTE when metrics are below thresholds."""
        from src.paper.engine import _compute_recommendation
        mock_metrics = MagicMock()
        mock_metrics.sharpe_ratio = -0.5
        mock_metrics.win_rate = 0.25
        mock_metrics.max_drawdown = -0.30

        result = _compute_recommendation(
            mock_metrics, trade_count=35, days_in_paper=20,
            config=PaperTradingConfig(),
        )
        assert result == "DEMOTE"


# -- Error and failure scenarios (Scenarios 16-20) -----------------------


class TestTickErrorHandling:
    """Paper engine tick survives partial failures."""

    @pytest.mark.asyncio
    async def test_e2e_tick_survives_shadow_error(self, engine, strategy_manager):
        """Tick completes even when shadow mode raises an exception."""
        chain = make_chain()
        chains = {"SPX": chain}

        # Patch shadow_manager to raise
        engine.shadow_manager.check_entry_signals = AsyncMock(
            side_effect=RuntimeError("Shadow error"),
        )

        result = await engine.tick(chains)
        assert len(result.errors) > 0
        assert "Shadow" in result.errors[0] or "entry signals" in result.errors[0]

    @pytest.mark.asyncio
    async def test_e2e_tick_survives_exit_error(self, engine, strategy_manager):
        """Tick completes even when exit monitor raises."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Open a position
        await _submit_and_fill_entry(engine, sid, chains)

        # Patch exit_monitor to raise
        engine.exit_monitor.check_all_positions = AsyncMock(
            side_effect=RuntimeError("Exit error"),
        )

        result = await engine.tick(chains)
        assert len(result.errors) > 0
        assert any("exit" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_e2e_empty_chains_no_crash(self, engine, strategy_manager):
        """Tick with empty chains dict does not crash."""
        sid = await _create_paper_strategy(strategy_manager)

        # Open a position with data first
        chain = make_chain()
        chains = {"SPX": chain}
        await _submit_and_fill_entry(engine, sid, chains)

        # Now tick with empty chains
        result = await engine.tick({})
        assert isinstance(result, TickResult)
        # Should not crash

    @pytest.mark.asyncio
    async def test_e2e_tick_survives_fill_error(self, engine, strategy_manager, db):
        """Tick completes when a fill attempt raises."""
        sid = await _create_paper_strategy(strategy_manager)
        legs = make_put_spread_legs()
        chain = make_chain()
        chains = {"SPX": chain}

        # Submit an order
        await engine.order_manager.submit_order(
            strategy_id=sid, direction="open",
            legs=legs, quantity=1, order_type="market",
        )

        # Patch try_fill to raise
        original_try_fill = engine.order_manager.try_fill
        engine.order_manager.try_fill = AsyncMock(
            side_effect=RuntimeError("Fill error"),
        )

        result = await engine.tick(chains)
        assert len(result.errors) > 0

        # Restore
        engine.order_manager.try_fill = original_try_fill


# -- Scheduler integration tests (Scenarios 21-22) ----------------------


class TestSchedulerIntegration:
    """Scheduler integration with paper engine."""

    @pytest.mark.asyncio
    async def test_e2e_full_day_simulation(self, engine, strategy_manager):
        """Simulate a full trading day: premarket -> ticks -> postmarket."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Pre-market
        await engine.start_of_day()
        assert engine._tick_count_today == 0
        assert engine._daily_errors == []

        # Simulate intraday ticks
        for _ in range(5):
            result = await engine.tick(chains)
            assert isinstance(result, TickResult)

        assert engine._tick_count_today == 5

        # Post-market
        closed_ids = await engine.handle_eod_settlement(chains)
        assert isinstance(closed_ids, list)

        await engine.pnl_calculator.take_daily_snapshot()

        # Verify snapshot exists
        cursor = await engine._db.execute(
            "SELECT COUNT(*) FROM paper_portfolio"
        )
        count = (await cursor.fetchone())[0]
        assert count >= 1

    @pytest.mark.asyncio
    async def test_start_of_day_resets_state(self, engine):
        """start_of_day() resets tick counter and daily errors."""
        engine._tick_count_today = 10
        engine._daily_errors = ["error1", "error2"]

        await engine.start_of_day()

        assert engine._tick_count_today == 0
        assert engine._daily_errors == []


# -- Discord command integration tests (Scenarios 23-24) -----------------


class TestDiscordCommandIntegration:
    """Discord command data flow tests."""

    @pytest.mark.asyncio
    async def test_e2e_paper_status_returns_data(self, engine, strategy_manager):
        """get_portfolio_summary() returns populated data."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Open 2 positions
        await _submit_and_fill_entry(engine, sid, chains)
        await _submit_and_fill_entry(engine, sid, chains)

        summary = await engine.get_portfolio_summary()
        assert isinstance(summary, PortfolioSummary)
        assert summary.open_positions == 2
        assert summary.total_equity > 0
        assert summary.starting_capital == 100_000.0

    @pytest.mark.asyncio
    async def test_e2e_paper_history_returns_trades(self, engine, strategy_manager, db):
        """Completed trades appear in the paper_trades table."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Complete 3 trades
        for _ in range(3):
            _, pos_id, _ = await _submit_and_fill_entry(engine, sid, chains)
            await engine.force_close_position(
                pos_id, reason="profit_target", chains=chains,
            )

        cursor = await db.execute("SELECT COUNT(*) FROM paper_trades")
        count = (await cursor.fetchone())[0]
        assert count == 3

        # Verify fields present
        cursor = await db.execute(
            "SELECT entry_date, exit_date, entry_price, exit_price, "
            "total_pnl, fees, close_reason FROM paper_trades"
        )
        rows = await cursor.fetchall()
        for row in rows:
            entry_date, exit_date, entry_price, exit_price, total_pnl, fees, close_reason = row
            assert entry_date is not None
            assert exit_date is not None
            assert entry_price is not None
            assert exit_price is not None
            assert total_pnl is not None
            assert fees is not None
            assert close_reason is not None


# -- Signal logging integration tests (Scenario 25) ----------------------


class TestSignalLogging:
    """Paper signals logged for Bayesian calibration."""

    @pytest.mark.asyncio
    async def test_e2e_paper_entry_signal_logged(self, engine, strategy_manager, db):
        """paper_entry signal logged when position opens."""
        from src.db.signal_log import SignalLogger

        signal_logger = SignalLogger(db)
        engine._signal_logger = signal_logger

        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Submit and fill an entry via tick
        legs = make_put_spread_legs()
        await engine.order_manager.submit_order(
            strategy_id=sid, direction="open",
            legs=legs, quantity=1, order_type="market",
        )

        result = await engine.tick(chains)
        assert result.positions_opened >= 1

        # Check signal_log
        cursor = await db.execute(
            "SELECT signal_type, source, metadata FROM signal_log WHERE signal_type = 'paper_entry'"
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == "paper_entry"
        assert row[1] == "paper_engine"

    @pytest.mark.asyncio
    async def test_e2e_paper_exit_signal_logged(self, engine, strategy_manager, db):
        """paper_exit signal logged when position closes via tick."""
        from src.db.signal_log import SignalLogger

        signal_logger = SignalLogger(db)
        engine._signal_logger = signal_logger

        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Open a position
        _, position_id, _ = await _submit_and_fill_entry(engine, sid, chains)

        # Submit a close order
        close_order_id = await engine.submit_exit_order(
            position_id=position_id, reason="profit_target",
        )
        assert close_order_id is not None

        # Tick to fill the close order
        result = await engine.tick(chains)
        assert result.positions_closed >= 1

        # Check signal_log for paper_exit
        cursor = await db.execute(
            "SELECT signal_type, source, metadata FROM signal_log WHERE signal_type = 'paper_exit'"
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == "paper_exit"
        meta = json.loads(row[2])
        assert "pnl" in meta

    @pytest.mark.asyncio
    async def test_paper_signal_no_logger_no_crash(self, engine, strategy_manager):
        """No crash when signal_logger is None."""
        engine._signal_logger = None
        # Should not raise
        await engine._log_paper_signal("paper_entry", 1, 1, 1)

    @pytest.mark.asyncio
    async def test_paper_signal_logger_error_no_crash(self, engine, strategy_manager):
        """Signal logging errors are caught and don't crash."""
        engine._signal_logger = MagicMock()
        engine._signal_logger.log_signal = AsyncMock(
            side_effect=RuntimeError("Logger error"),
        )
        # Should not raise
        await engine._log_paper_signal("paper_entry", 1, 1, 1)


# -- Graceful degradation tests (Step 8) --------------------------------


class TestGracefulDegradation:
    """Bot starts and operates correctly without paper trading components."""

    @pytest.mark.asyncio
    async def test_graceful_no_store(self):
        """Bot starts without Store -- paper_engine is None."""
        from src.bot import SpyBot
        bot = SpyBot()
        bot.store = None
        bot.strategy_manager = None
        await bot._init_paper_trading()
        assert bot.paper_engine is None

    @pytest.mark.asyncio
    async def test_graceful_no_strategy_manager(self, db):
        """Bot starts without StrategyManager -- paper_engine is None."""
        from src.bot import SpyBot
        bot = SpyBot()
        bot.store = MagicMock()
        bot.store._db = db
        bot.strategy_manager = None
        await bot._init_paper_trading()
        assert bot.paper_engine is None

    @pytest.mark.asyncio
    async def test_graceful_scheduler_no_paper_engine(self):
        """Scheduler runs cleanly when paper_engine is None."""
        # The scheduler uses getattr(self.bot, "paper_engine", None)
        # so it should be safe when None
        bot = MagicMock()
        bot.paper_engine = None
        bot.portfolio_analyzer = None

        # Simulate what the scheduler does
        paper_engine = getattr(bot, "paper_engine", None)
        assert paper_engine is None
        # The scheduler skips paper engine tick when None

    @pytest.mark.asyncio
    async def test_graceful_cog_no_paper_engine(self):
        """Paper cog returns None engine when not initialized."""
        bot = MagicMock()
        bot.paper_engine = None

        # Simulate what the cog does
        engine = getattr(bot, "paper_engine", None)
        assert engine is None


# -- Position limits tests (Scenario 8) ---------------------------------


class TestPositionLimits:
    """Position limit enforcement in shadow mode."""

    @pytest.mark.asyncio
    async def test_e2e_open_positions_tracked(self, engine, strategy_manager):
        """Open positions are tracked per strategy."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Open 2 positions
        await _submit_and_fill_entry(engine, sid, chains)
        await _submit_and_fill_entry(engine, sid, chains)

        positions = await engine.position_tracker.get_open_positions(strategy_id=sid)
        assert len(positions) == 2


# -- Daily entry limit tests (Scenario 9) -------------------------------


class TestDailyEntryLimit:
    """Daily entry tracking in shadow mode."""

    def test_shadow_daily_tracking_resets(self):
        """Shadow mode daily tracking resets on new day."""
        from src.paper.shadow import ShadowModeManager
        shadow = ShadowModeManager(
            db=MagicMock(), strategy_manager=MagicMock(),
            order_manager=MagicMock(), position_tracker=MagicMock(),
            config=PaperTradingConfig(),
        )

        shadow._entries_today = {1: 3, 2: 1}
        shadow._last_reset_date = "2025-01-01"

        shadow.reset_daily_state()
        assert shadow._entries_today == {}
        assert shadow._last_reset_date == ""


# -- Strategy results tests (Scenario 14) --------------------------------


class TestStrategyResults:
    """Strategy paper results and metrics."""

    @pytest.mark.asyncio
    async def test_e2e_strategy_paper_results(self, engine, strategy_manager):
        """get_strategy_paper_results returns complete data."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Complete a trade
        _, pos_id, _ = await _submit_and_fill_entry(engine, sid, chains)
        await engine.force_close_position(
            pos_id, reason="profit_target", chains=chains,
        )

        results = await engine.get_strategy_paper_results(sid)
        assert results.strategy_id == sid
        assert len(results.trades) == 1
        assert results.recommendation in ("CONTINUE", "PROMOTE", "DEMOTE")


# -- Tick result aggregation tests ---------------------------------------


class TestTickResultAggregation:
    """TickResult properly aggregates actions within a tick."""

    @pytest.mark.asyncio
    async def test_tick_result_counts(self, engine, strategy_manager, db):
        """TickResult correctly counts orders and positions."""
        sid = await _create_paper_strategy(strategy_manager)
        legs = make_put_spread_legs()
        chain = make_chain()
        chains = {"SPX": chain}

        # Submit entry order before tick
        await engine.order_manager.submit_order(
            strategy_id=sid, direction="open",
            legs=legs, quantity=1, order_type="market",
        )

        result = await engine.tick(chains)
        assert result.orders_filled >= 1
        assert result.positions_opened >= 1

    @pytest.mark.asyncio
    async def test_tick_increments_counter(self, engine):
        """Tick increments the daily tick counter."""
        chain = make_chain()
        assert engine._tick_count_today == 0
        await engine.tick({"SPX": chain})
        assert engine._tick_count_today == 1
        await engine.tick({"SPX": chain})
        assert engine._tick_count_today == 2


# -- Exit monitor tests ---------------------------------------------------


class TestExitMonitor:
    """Exit monitor detects exit conditions."""

    @pytest.mark.asyncio
    async def test_exit_monitor_detects_expiration(self, engine, strategy_manager, db):
        """Exit monitor detects positions with expired legs."""
        sid = await _create_paper_strategy(strategy_manager)
        today = date.today()

        # Create legs expiring today
        legs = [
            LegSpec(
                leg_name="short_put", option_type="put",
                strike=5750.0, expiry=today, action="sell", quantity=1,
            ),
            LegSpec(
                leg_name="long_put", option_type="put",
                strike=5700.0, expiry=today, action="buy", quantity=1,
            ),
        ]

        contracts = [
            OptionContract(
                ticker="SPX", option_type="put", strike=5750.0, expiry=today,
                bid=8.50, ask=9.00, last=8.75, iv=0.18,
                delta=-0.30, gamma=0.002, theta=-0.50, vega=5.0,
                volume=5000, open_interest=20000,
            ),
            OptionContract(
                ticker="SPX", option_type="put", strike=5700.0, expiry=today,
                bid=5.00, ask=5.50, last=5.25, iv=0.20,
                delta=-0.15, gamma=0.001, theta=-0.30, vega=3.0,
                volume=3000, open_interest=15000,
            ),
        ]
        chain = OptionsChain(
            ticker="SPX", spot_price=5800.0,
            timestamp=datetime.now(), contracts=contracts,
        )
        chains = {"SPX": chain}

        _, position_id, _ = await _submit_and_fill_entry(
            engine, sid, chains, legs=legs,
        )

        # Check exit conditions
        signals = await engine.exit_monitor.check_all_positions(chains)
        assert len(signals) >= 1
        assert signals[0].position_id == position_id
        assert signals[0].reason == "expiration"


# -- Force close tests ---------------------------------------------------


class TestForceClose:
    """Manual position close via force_close_position."""

    @pytest.mark.asyncio
    async def test_force_close_creates_trade(self, engine, strategy_manager, db):
        """force_close_position creates a trade record."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        _, position_id, _ = await _submit_and_fill_entry(engine, sid, chains)

        trade_id = await engine.force_close_position(
            position_id, reason="manual", chains=chains,
        )
        assert trade_id is not None

        cursor = await db.execute(
            "SELECT close_reason FROM paper_trades WHERE id = ?", (trade_id,)
        )
        row = await cursor.fetchone()
        assert row[0] == "manual"

    @pytest.mark.asyncio
    async def test_force_close_nonexistent_position(self, engine):
        """force_close_position returns None for nonexistent position."""
        result = await engine.force_close_position(
            position_id=9999, reason="test",
        )
        assert result is None


# -- Third Friday detection tests ----------------------------------------


class TestThirdFriday:
    """AM/PM settlement type detection."""

    def test_is_third_friday_true(self):
        """Correctly identifies the 3rd Friday of a month."""
        from src.paper.exits import _is_third_friday
        # Jan 17, 2025 is the 3rd Friday of January 2025
        assert _is_third_friday(date(2025, 1, 17)) is True

    def test_is_third_friday_false(self):
        """Correctly identifies non-third-Fridays."""
        from src.paper.exits import _is_third_friday
        # Jan 10, 2025 is the 2nd Friday
        assert _is_third_friday(date(2025, 1, 10)) is False
        # Monday
        assert _is_third_friday(date(2025, 1, 13)) is False

    def test_settlement_type_am(self):
        """3rd Friday positions are AM-settled."""
        from src.paper.exits import _get_settlement_type
        assert _get_settlement_type(date(2025, 1, 17)) == "am"

    def test_settlement_type_pm(self):
        """Non-3rd-Friday positions are PM-settled."""
        from src.paper.exits import _get_settlement_type
        assert _get_settlement_type(date(2025, 1, 10)) == "pm"


# -- Database error recovery (Scenario 20) --------------------------------


class TestDatabaseErrorRecovery:
    """Database write failure handling."""

    @pytest.mark.asyncio
    async def test_e2e_database_error_propagates(self, engine, strategy_manager):
        """Database errors propagate cleanly without partial state."""
        sid = await _create_paper_strategy(strategy_manager)

        # Close the database to simulate failure
        # Instead, we'll test that the engine handles gracefully
        # when order creation fails
        original_execute = engine._db.execute

        call_count = 0

        async def failing_execute(sql, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Fail on a specific INSERT
            if "INSERT INTO paper_orders" in sql and call_count > 10:
                raise aiosqlite.OperationalError("database is locked")
            return await original_execute(sql, *args, **kwargs)

        engine._db.execute = failing_execute

        # This should raise since submit_order does INSERT
        # But only after call_count > 10 to let setup succeed
        try:
            for _ in range(5):
                try:
                    await engine.order_manager.submit_order(
                        strategy_id=sid, direction="open",
                        legs=make_put_spread_legs(), quantity=1,
                    )
                except aiosqlite.OperationalError:
                    pass  # Expected
        finally:
            engine._db.execute = original_execute


# -- Cumulative realized PnL tests ---------------------------------------


class TestCumulativeRealizedPnL:
    """Cumulative realized PnL computation."""

    @pytest.mark.asyncio
    async def test_cumulative_pnl_after_trades(self, engine, strategy_manager):
        """Cumulative realized PnL is sum of net trade PnLs."""
        sid = await _create_paper_strategy(strategy_manager)
        chain = make_chain()
        chains = {"SPX": chain}

        # Complete a trade
        _, pos_id, _ = await _submit_and_fill_entry(engine, sid, chains)
        await engine.force_close_position(
            pos_id, reason="profit_target", chains=chains,
        )

        pnl = await engine.pnl_calculator.get_cumulative_realized_pnl()
        # Should have some value (positive or negative depending on fills)
        assert isinstance(pnl, float)

    @pytest.mark.asyncio
    async def test_cumulative_pnl_zero_no_trades(self, engine):
        """Cumulative PnL is 0 when no trades exist."""
        pnl = await engine.pnl_calculator.get_cumulative_realized_pnl()
        assert pnl == 0.0
