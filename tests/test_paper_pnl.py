"""Tests for paper PnL calculations, daily snapshots, and metrics reuse.

Tests PnLCalculator: trade-level PnL, fee calculation, SPX multiplier,
daily snapshots, equity curve generation, and StrategyMetrics reuse
from backtest/metrics.py.
"""

import json
from datetime import date, datetime

import aiosqlite
import pytest
import pytest_asyncio

from src.data import OptionContract, OptionsChain
from src.paper.models import LegSpec, PaperTradingConfig, SimulatedFill, TradePnL
from src.paper.orders import OrderManager
from src.paper.pnl import PnLCalculator
from src.paper.positions import PositionTracker
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
    await conn.commit()
    await init_paper_tables(conn)
    yield conn
    await conn.close()


class TestPnLCalculatorCalculateTradeQPnL:
    """Tests for calculate_trade_pnl method."""

    def test_credit_spread_winning_trade(self):
        """Credit spread that profits: sell high, buy back low."""
        config = _make_config(fee_per_contract=0.65)
        calc = PnLCalculator.__new__(PnLCalculator)
        calc._config = config

        entry_fills = [
            SimulatedFill("short_put", 3.48, 3.40, 3.60, 3.50, 0.02),
            SimulatedFill("long_put", 1.92, 1.80, 2.00, 1.90, 0.02),
        ]
        exit_fills = [
            SimulatedFill("short_put", 1.52, 1.40, 1.60, 1.50, 0.02),
            SimulatedFill("long_put", 0.52, 0.40, 0.60, 0.50, 0.02),
        ]

        entry_actions = {"short_put": "sell", "long_put": "buy"}
        exit_actions = {"short_put": "buy", "long_put": "sell"}

        pnl = calc.calculate_trade_pnl(
            entry_fills, exit_fills, quantity=1,
            entry_legs_actions=entry_actions,
            exit_legs_actions=exit_actions,
        )

        # Entry: sell 3.48 - buy 1.92 = 1.56 credit
        assert pnl.entry_credit_debit == pytest.approx(1.56, abs=0.01)
        # Exit: sell 0.52 - buy 1.52 = -1.00 debit
        assert pnl.exit_credit_debit == pytest.approx(-1.00, abs=0.01)
        # Raw = 1.56 + (-1.00) = 0.56
        assert pnl.raw_pnl == pytest.approx(0.56, abs=0.01)
        # Total = 0.56 * 1 * 100 = 56.00
        assert pnl.total_pnl == pytest.approx(56.00, abs=1.0)
        # Fees: 0.65 * (2 entry + 2 exit) * 1 = 2.60
        assert pnl.fees == pytest.approx(2.60, abs=0.01)
        # Net = 56 - 2.60 = 53.40
        assert pnl.net_pnl == pytest.approx(53.40, abs=0.1)

    def test_iron_condor_fees(self):
        """4-leg iron condor: fees = $0.65 * 8 legs (4 open + 4 close) * qty."""
        config = _make_config(fee_per_contract=0.65)
        calc = PnLCalculator.__new__(PnLCalculator)
        calc._config = config

        entry_fills = [
            SimulatedFill("sp", 3.0, 2.9, 3.1, 3.0, 0.01),
            SimulatedFill("lp", 1.5, 1.4, 1.6, 1.5, 0.01),
            SimulatedFill("sc", 2.5, 2.4, 2.6, 2.5, 0.01),
            SimulatedFill("lc", 1.2, 1.1, 1.3, 1.2, 0.01),
        ]
        exit_fills = [
            SimulatedFill("sp", 0.5, 0.4, 0.6, 0.5, 0.01),
            SimulatedFill("lp", 0.2, 0.1, 0.3, 0.2, 0.01),
            SimulatedFill("sc", 0.4, 0.3, 0.5, 0.4, 0.01),
            SimulatedFill("lc", 0.1, 0.0, 0.2, 0.1, 0.01),
        ]

        entry_actions = {"sp": "sell", "lp": "buy", "sc": "sell", "lc": "buy"}
        exit_actions = {"sp": "buy", "lp": "sell", "sc": "buy", "lc": "sell"}

        pnl = calc.calculate_trade_pnl(
            entry_fills, exit_fills, quantity=1,
            entry_legs_actions=entry_actions,
            exit_legs_actions=exit_actions,
        )

        # Fees: 0.65 * (4 + 4) * 1 = 5.20
        assert pnl.fees == pytest.approx(5.20, abs=0.01)

    def test_multiplier_applied(self):
        """PnL should be multiplied by SPX multiplier ($100)."""
        config = _make_config(fee_per_contract=0.0)
        calc = PnLCalculator.__new__(PnLCalculator)
        calc._config = config

        entry_fills = [SimulatedFill("sp", 5.00, 4.90, 5.10, 5.00, 0.0)]
        exit_fills = [SimulatedFill("sp", 2.00, 1.90, 2.10, 2.00, 0.0)]

        entry_actions = {"sp": "sell"}
        exit_actions = {"sp": "buy"}

        pnl = calc.calculate_trade_pnl(
            entry_fills, exit_fills, quantity=1,
            entry_legs_actions=entry_actions,
            exit_legs_actions=exit_actions,
        )

        # Raw = 5.0 - 2.0 = 3.0, total = 3.0 * 100 = 300
        assert pnl.total_pnl == pytest.approx(300.0, abs=0.1)

    def test_quantity_scaling(self):
        """Multiple contracts should scale PnL and fees."""
        config = _make_config(fee_per_contract=0.65)
        calc = PnLCalculator.__new__(PnLCalculator)
        calc._config = config

        entry_fills = [SimulatedFill("sp", 5.00, 4.90, 5.10, 5.00, 0.0)]
        exit_fills = [SimulatedFill("sp", 2.00, 1.90, 2.10, 2.00, 0.0)]

        pnl = calc.calculate_trade_pnl(
            entry_fills, exit_fills, quantity=3,
            entry_legs_actions={"sp": "sell"},
            exit_legs_actions={"sp": "buy"},
        )

        # Raw = 3.0, total = 3.0 * 3 * 100 = 900
        assert pnl.total_pnl == pytest.approx(900.0, abs=0.1)
        # Fees = 0.65 * (1 + 1) * 3 = 3.90
        assert pnl.fees == pytest.approx(3.90, abs=0.01)

    def test_slippage_cost_tracked(self):
        """Slippage should be tracked separately."""
        config = _make_config(fee_per_contract=0.0)
        calc = PnLCalculator.__new__(PnLCalculator)
        calc._config = config

        entry_fills = [SimulatedFill("sp", 3.48, 3.40, 3.60, 3.50, 0.02)]
        exit_fills = [SimulatedFill("sp", 1.52, 1.40, 1.60, 1.50, 0.02)]

        pnl = calc.calculate_trade_pnl(
            entry_fills, exit_fills, quantity=1,
            entry_legs_actions={"sp": "sell"},
            exit_legs_actions={"sp": "buy"},
        )

        # Slippage: (0.02 + 0.02) * 1 * 100 = 4.00
        assert pnl.slippage_cost == pytest.approx(4.00, abs=0.1)


class TestDailySnapshot:
    """Tests for take_daily_snapshot method."""

    @pytest.mark.asyncio
    async def test_snapshot_empty_portfolio(self, db):
        """Snapshot with no trades should record starting capital."""
        config = _make_config(starting_capital=100_000.0)
        calc = PnLCalculator(db, config)

        await calc.take_daily_snapshot()

        cursor = await db.execute(
            "SELECT total_equity, realized_pnl, unrealized_pnl FROM paper_portfolio"
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == 100_000.0  # total_equity
        assert row[1] == 0.0       # realized_pnl
        assert row[2] == 0.0       # unrealized_pnl

    @pytest.mark.asyncio
    async def test_snapshot_with_trades(self, db):
        """Snapshot should reflect realized PnL from trades."""
        config = _make_config(starting_capital=100_000.0)

        # Insert prerequisites in FK order: order -> position -> trade
        now = datetime.now().isoformat()
        await db.execute(
            """
            INSERT INTO paper_orders
                (id, strategy_id, order_type, direction, legs, status, submitted_at)
            VALUES (1, 1, 'market', 'open', '[]', 'filled', ?)
            """,
            (now,),
        )
        await db.execute(
            """
            INSERT INTO paper_positions
                (id, strategy_id, open_order_id, status, legs, entry_price, opened_at)
            VALUES (1, 1, 1, 'closed', '[]', 2.50, ?)
            """,
            (now,),
        )
        await db.execute(
            """
            INSERT INTO paper_trades
                (strategy_id, position_id, entry_date, exit_date, holding_days,
                 entry_price, exit_price, realized_pnl, total_pnl, fees,
                 close_reason, legs_detail)
            VALUES (1, 1, ?, ?, 5, 2.50, -1.00, 1.50, 150.0, 2.60,
                    'profit_target', '{}')
            """,
            (now[:10], now[:10]),
        )
        await db.commit()

        calc = PnLCalculator(db, config)
        await calc.take_daily_snapshot()

        cursor = await db.execute(
            "SELECT total_equity, realized_pnl FROM paper_portfolio"
        )
        row = await cursor.fetchone()
        # Net PnL = 150.0 - 2.60 = 147.40
        assert row[1] == pytest.approx(147.40, abs=0.1)
        assert row[0] == pytest.approx(100_147.40, abs=0.1)

    @pytest.mark.asyncio
    async def test_snapshot_idempotent_same_day(self, db):
        """Taking two snapshots on the same day should replace, not duplicate."""
        config = _make_config()
        calc = PnLCalculator(db, config)

        await calc.take_daily_snapshot()
        await calc.take_daily_snapshot()

        cursor = await db.execute("SELECT COUNT(*) FROM paper_portfolio")
        count = (await cursor.fetchone())[0]
        assert count == 1


class TestEquityCurve:
    """Tests for get_equity_curve method."""

    @pytest.mark.asyncio
    async def test_equity_curve_empty(self, db):
        """Empty portfolio should return empty curve."""
        config = _make_config()
        calc = PnLCalculator(db, config)

        curve = await calc.get_equity_curve()
        assert curve == []

    @pytest.mark.asyncio
    async def test_equity_curve_with_snapshots(self, db):
        """Equity curve should return snapshots in chronological order."""
        config = _make_config()

        # Insert multiple snapshots
        for i, d in enumerate(["2025-03-17", "2025-03-18", "2025-03-19"]):
            await db.execute(
                """
                INSERT INTO paper_portfolio
                    (snapshot_date, starting_capital, realized_pnl, unrealized_pnl,
                     total_equity, open_positions, total_trades, daily_pnl, max_drawdown)
                VALUES (?, 100000, ?, 0, ?, 0, ?, ?, 0)
                """,
                (d, i * 100, 100000 + i * 100, i, i * 100),
            )
        await db.commit()

        calc = PnLCalculator(db, config)
        curve = await calc.get_equity_curve(days=10)

        assert len(curve) == 3
        assert curve[0]["date"] == "2025-03-17"
        assert curve[2]["date"] == "2025-03-19"
        assert curve[2]["total_equity"] == 100200.0


class TestPaperMetrics:
    """Tests for get_paper_metrics method."""

    @pytest.mark.asyncio
    async def test_metrics_no_trades(self, db):
        """Empty paper trades should return zero metrics."""
        config = _make_config()
        calc = PnLCalculator(db, config)

        metrics = await calc.get_paper_metrics()
        assert metrics.num_trades == 0
        assert metrics.total_return == 0.0

    @pytest.mark.asyncio
    async def test_metrics_with_trades(self, db):
        """Metrics should be computed from paper trade data."""
        config = _make_config()
        now = datetime.now().isoformat()

        # Create prerequisite records
        await db.execute(
            "INSERT INTO paper_orders (id, strategy_id, order_type, direction, legs, status, submitted_at) VALUES (1, 1, 'market', 'open', '[]', 'filled', ?)",
            (now,),
        )
        await db.execute(
            "INSERT INTO paper_positions (id, strategy_id, open_order_id, status, legs, entry_price, opened_at) VALUES (1, 1, 1, 'closed', '[]', 2.50, ?)",
            (now,),
        )

        # Insert trades
        trades = [
            ("2025-03-10", "2025-03-12", 2, 100.0, 2.0),
            ("2025-03-11", "2025-03-14", 3, 150.0, 2.0),
            ("2025-03-12", "2025-03-15", 3, -80.0, 2.0),
            ("2025-03-13", "2025-03-17", 4, 200.0, 2.0),
            ("2025-03-14", "2025-03-18", 4, -50.0, 2.0),
        ]
        for entry, exit_, hold, pnl, fees in trades:
            await db.execute(
                """
                INSERT INTO paper_trades
                    (strategy_id, position_id, entry_date, exit_date, holding_days,
                     entry_price, exit_price, realized_pnl, total_pnl, fees,
                     close_reason, legs_detail)
                VALUES (1, 1, ?, ?, ?, 2.50, 1.00, 1.50, ?, ?, 'profit_target', '{}')
                """,
                (entry, exit_, hold, pnl, fees),
            )
        await db.commit()

        calc = PnLCalculator(db, config)
        metrics = await calc.get_paper_metrics()

        assert metrics.num_trades == 5
        # 3 wins, 2 losses
        assert metrics.win_rate == pytest.approx(0.6, abs=0.01)

    @pytest.mark.asyncio
    async def test_metrics_strategy_filter(self, db):
        """Metrics should filter by strategy_id when provided."""
        config = _make_config()
        now = datetime.now().isoformat()

        # Create second strategy
        await db.execute(
            "INSERT INTO strategies (name, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("Strategy 2", "paper", now, now),
        )
        await db.commit()

        # Create prereqs
        await db.execute(
            "INSERT INTO paper_orders (id, strategy_id, order_type, direction, legs, status, submitted_at) VALUES (1, 1, 'market', 'open', '[]', 'filled', ?)",
            (now,),
        )
        await db.execute(
            "INSERT INTO paper_positions (id, strategy_id, open_order_id, status, legs, entry_price, opened_at) VALUES (1, 1, 1, 'closed', '[]', 2.50, ?)",
            (now,),
        )
        await db.commit()

        # Strategy 1: 3 trades
        for i in range(3):
            await db.execute(
                """
                INSERT INTO paper_trades
                    (strategy_id, position_id, entry_date, exit_date, holding_days,
                     entry_price, exit_price, realized_pnl, total_pnl, fees,
                     close_reason, legs_detail)
                VALUES (1, 1, '2025-03-10', '2025-03-12', 2, 2.50, 1.00, 1.50, 100.0, 2.0,
                        'profit_target', '{}')
                """,
            )

        # Strategy 2: 2 trades
        for i in range(2):
            await db.execute(
                """
                INSERT INTO paper_trades
                    (strategy_id, position_id, entry_date, exit_date, holding_days,
                     entry_price, exit_price, realized_pnl, total_pnl, fees,
                     close_reason, legs_detail)
                VALUES (2, 1, '2025-03-10', '2025-03-12', 2, 2.50, 1.00, 1.50, -50.0, 2.0,
                        'stop_loss', '{}')
                """,
            )
        await db.commit()

        calc = PnLCalculator(db, config)

        m1 = await calc.get_paper_metrics(strategy_id=1)
        assert m1.num_trades == 3

        m2 = await calc.get_paper_metrics(strategy_id=2)
        assert m2.num_trades == 2

        m_all = await calc.get_paper_metrics()
        assert m_all.num_trades == 5


class TestHelperMethods:
    """Tests for helper methods."""

    @pytest.mark.asyncio
    async def test_cumulative_realized_pnl(self, db):
        """get_cumulative_realized_pnl should sum net PnL."""
        config = _make_config()
        now = datetime.now().isoformat()

        # Create prereqs
        await db.execute(
            "INSERT INTO paper_orders (id, strategy_id, order_type, direction, legs, status, submitted_at) VALUES (1, 1, 'market', 'open', '[]', 'filled', ?)",
            (now,),
        )
        await db.execute(
            "INSERT INTO paper_positions (id, strategy_id, open_order_id, status, legs, entry_price, opened_at) VALUES (1, 1, 1, 'closed', '[]', 2.50, ?)",
            (now,),
        )

        await db.execute(
            """
            INSERT INTO paper_trades
                (strategy_id, position_id, entry_date, exit_date, holding_days,
                 entry_price, exit_price, realized_pnl, total_pnl, fees,
                 close_reason, legs_detail)
            VALUES (1, 1, '2025-03-10', '2025-03-12', 2, 2.50, 1.00, 1.50, 200.0, 5.0,
                    'profit_target', '{}')
            """,
        )
        await db.execute(
            """
            INSERT INTO paper_trades
                (strategy_id, position_id, entry_date, exit_date, holding_days,
                 entry_price, exit_price, realized_pnl, total_pnl, fees,
                 close_reason, legs_detail)
            VALUES (1, 1, '2025-03-12', '2025-03-14', 2, 2.50, 1.00, 1.50, -100.0, 5.0,
                    'stop_loss', '{}')
            """,
        )
        await db.commit()

        calc = PnLCalculator(db, config)
        total = await calc.get_cumulative_realized_pnl()
        # (200-5) + (-100-5) = 195 + (-105) = 90
        assert total == pytest.approx(90.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_trade_count(self, db):
        """get_trade_count should return correct count."""
        config = _make_config()
        now = datetime.now().isoformat()

        # Create prereqs
        await db.execute(
            "INSERT INTO paper_orders (id, strategy_id, order_type, direction, legs, status, submitted_at) VALUES (1, 1, 'market', 'open', '[]', 'filled', ?)",
            (now,),
        )
        await db.execute(
            "INSERT INTO paper_positions (id, strategy_id, open_order_id, status, legs, entry_price, opened_at) VALUES (1, 1, 1, 'closed', '[]', 2.50, ?)",
            (now,),
        )
        await db.commit()

        calc = PnLCalculator(db, config)
        assert await calc.get_trade_count() == 0

        await db.execute(
            """
            INSERT INTO paper_trades
                (strategy_id, position_id, entry_date, exit_date, holding_days,
                 entry_price, exit_price, realized_pnl, total_pnl, fees,
                 close_reason, legs_detail)
            VALUES (1, 1, '2025-03-10', '2025-03-12', 2, 2.50, 1.00, 1.50, 100.0, 2.0,
                    'profit_target', '{}')
            """,
        )
        await db.commit()
        assert await calc.get_trade_count() == 1
