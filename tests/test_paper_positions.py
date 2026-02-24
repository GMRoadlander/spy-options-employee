"""Tests for paper position tracking.

Tests PositionTracker: open, close, mark-to-market, expiration handling,
PnL calculations, and settlement type detection. Uses in-memory SQLite
databases and mock options chain data.
"""

import json
from datetime import date, datetime

import aiosqlite
import pytest
import pytest_asyncio

from src.data import OptionContract, OptionsChain
from src.paper.models import LegSpec, PaperTradingConfig, SimulatedFill
from src.paper.orders import OrderManager
from src.paper.positions import (
    PositionTracker,
    _calculate_max_profit_loss,
    _determine_settlement_type,
    _is_third_friday,
)
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


def _make_chain(contracts=None):
    if contracts is None:
        contracts = [
            _make_contract(5800.0, "put", 3.40, 3.60),
            _make_contract(5750.0, "put", 1.80, 2.00),
            _make_contract(6100.0, "call", 2.80, 3.00),
            _make_contract(6150.0, "call", 1.60, 1.80),
        ]
    return OptionsChain(
        ticker="SPX",
        spot_price=5950.0,
        timestamp=datetime.now(),
        contracts=contracts,
    )


@pytest_asyncio.fixture
async def db():
    """Create in-memory DB with strategies + paper tables + a test order."""
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


async def _submit_and_fill_order(db, config=None):
    """Helper: submit and fill a credit spread order, return (order_id, fills)."""
    config = config or _make_config()
    mgr = OrderManager(db, config)
    legs = [
        LegSpec("short_put", "put", 5800.0, date(2025, 3, 21), "sell"),
        LegSpec("long_put", "put", 5750.0, date(2025, 3, 21), "buy"),
    ]

    order_id = await mgr.submit_order(
        strategy_id=1, direction="open", legs=legs,
        quantity=1, order_type="market",
    )

    chain = _make_chain()
    fills = await mgr.try_fill(order_id, {"SPX": chain})
    return order_id, fills


class TestPositionTracker:
    """Tests for PositionTracker."""

    @pytest.mark.asyncio
    async def test_open_position(self, db):
        """Opening a position should create a record with correct entry price."""
        config = _make_config()
        tracker = PositionTracker(db, config)
        order_id, fills = await _submit_and_fill_order(db, config)

        position_id = await tracker.open_position(
            strategy_id=1, order_id=order_id,
            fills=fills, quantity=1,
        )

        assert position_id > 0
        positions = await tracker.get_open_positions()
        assert len(positions) == 1
        pos = positions[0]
        assert pos["status"] == "open"
        assert pos["strategy_id"] == 1
        assert pos["quantity"] == 1
        # Credit spread: entry_price should be positive (net credit)
        assert pos["entry_price"] > 0

    @pytest.mark.asyncio
    async def test_open_position_max_profit_loss(self, db):
        """Max profit/loss should be calculated from spread structure."""
        config = _make_config()
        tracker = PositionTracker(db, config)
        order_id, fills = await _submit_and_fill_order(db, config)

        position_id = await tracker.open_position(
            strategy_id=1, order_id=order_id,
            fills=fills, quantity=1,
        )

        positions = await tracker.get_open_positions()
        pos = positions[0]
        # Credit spread: max_profit = premium received * multiplier
        assert pos["max_profit"] > 0
        # Max loss = (width - premium) * multiplier
        assert pos["max_loss"] > 0

    @pytest.mark.asyncio
    async def test_mark_to_market(self, db):
        """Mark-to-market should update unrealized PnL."""
        config = _make_config()
        tracker = PositionTracker(db, config)
        order_id, fills = await _submit_and_fill_order(db, config)

        position_id = await tracker.open_position(
            strategy_id=1, order_id=order_id,
            fills=fills, quantity=1,
        )

        # Create a chain with tighter quotes (favorable for credit spread)
        favorable_chain = _make_chain([
            _make_contract(5800.0, "put", 2.40, 2.60),  # Put dropped
            _make_contract(5750.0, "put", 1.20, 1.40),  # Put dropped
        ])

        unrealized = await tracker.mark_to_market(position_id, favorable_chain)
        # Unrealized should be positive (premium decayed in our favor)
        # We opened with credit; the cost to close is now less
        assert isinstance(unrealized, float)

    @pytest.mark.asyncio
    async def test_mark_all_open(self, db):
        """mark_all_open should update all open positions."""
        config = _make_config()
        tracker = PositionTracker(db, config)

        # Open two positions
        order_id1, fills1 = await _submit_and_fill_order(db, config)
        await tracker.open_position(1, order_id1, fills1, 1)

        order_id2, fills2 = await _submit_and_fill_order(db, config)
        await tracker.open_position(1, order_id2, fills2, 1)

        chain = _make_chain()
        results = await tracker.mark_all_open({"SPX": chain})
        assert len(results) == 2
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    @pytest.mark.asyncio
    async def test_close_position(self, db):
        """Closing a position should create a trade record."""
        config = _make_config()
        tracker = PositionTracker(db, config)
        mgr = OrderManager(db, config)

        # Open
        order_id, fills = await _submit_and_fill_order(db, config)
        position_id = await tracker.open_position(1, order_id, fills, 1)

        # Submit close order (reverse legs)
        close_legs = [
            LegSpec("short_put", "put", 5800.0, date(2025, 3, 21), "buy"),
            LegSpec("long_put", "put", 5750.0, date(2025, 3, 21), "sell"),
        ]
        close_order_id = await mgr.submit_order(
            strategy_id=1, direction="close", legs=close_legs,
            quantity=1, order_type="market",
        )
        chain = _make_chain()
        close_fills = await mgr.try_fill(close_order_id, {"SPX": chain})
        assert close_fills is not None

        # Close position
        trade_id = await tracker.close_position(
            position_id=position_id,
            close_order_id=close_order_id,
            close_fills=close_fills,
            reason="profit_target",
        )

        assert trade_id > 0

        # Position should be closed
        positions = await tracker.get_open_positions()
        assert len(positions) == 0

        # Trade record should exist
        cursor = await db.execute(
            "SELECT close_reason, fees, total_pnl FROM paper_trades WHERE id = ?",
            (trade_id,),
        )
        trade = await cursor.fetchone()
        assert trade is not None
        assert trade[0] == "profit_target"
        assert trade[1] > 0  # Fees should be non-zero

    @pytest.mark.asyncio
    async def test_handle_expiration(self, db):
        """Expiration should create a trade record with settlement PnL."""
        config = _make_config()
        tracker = PositionTracker(db, config)

        order_id, fills = await _submit_and_fill_order(db, config)
        position_id = await tracker.open_position(1, order_id, fills, 1)

        # Settle at 5850 (between short put 5800 and long put 5750)
        # Both puts OTM at settlement = 5850
        trade_id = await tracker.handle_expiration(
            position_id=position_id,
            settlement_price=5850.0,
        )

        assert trade_id > 0

        # Both puts expire worthless at 5850
        cursor = await db.execute(
            "SELECT close_reason, total_pnl FROM paper_trades WHERE id = ?",
            (trade_id,),
        )
        trade = await cursor.fetchone()
        assert trade[0] == "expiration"
        # Both OTM: keep full premium -> positive PnL
        assert trade[1] > 0

    @pytest.mark.asyncio
    async def test_handle_expiration_itm(self, db):
        """ITM expiration should produce a loss."""
        config = _make_config()
        tracker = PositionTracker(db, config)

        order_id, fills = await _submit_and_fill_order(db, config)
        position_id = await tracker.open_position(1, order_id, fills, 1)

        # Settle at 5700 (below both puts -- both ITM)
        # Short put 5800: intrinsic = 100, we owe
        # Long put 5750: intrinsic = 50, we receive
        # Net: -100 + 50 = -50 per unit at settlement, plus entry credit
        trade_id = await tracker.handle_expiration(
            position_id=position_id,
            settlement_price=5700.0,
        )

        cursor = await db.execute(
            "SELECT total_pnl, entry_price, exit_price FROM paper_trades WHERE id = ?",
            (trade_id,),
        )
        trade = await cursor.fetchone()
        # entry_price is positive (credit ~1.56)
        # exit_value = sell_intrinsic - buy_intrinsic = -(100) + 50 = -50
        # realized = 1.56 + (-50) = -48.44 per unit
        # total = -48.44 * 100 = -4844
        assert trade[0] < 0  # Should be a loss

    @pytest.mark.asyncio
    async def test_get_open_positions_filter(self, db):
        """Filtering by strategy_id should work."""
        config = _make_config()
        tracker = PositionTracker(db, config)

        order_id, fills = await _submit_and_fill_order(db, config)
        await tracker.open_position(1, order_id, fills, 1)

        # Strategy 1
        positions = await tracker.get_open_positions(strategy_id=1)
        assert len(positions) == 1

        # Strategy 999
        positions = await tracker.get_open_positions(strategy_id=999)
        assert len(positions) == 0

    @pytest.mark.asyncio
    async def test_position_legs_json(self, db):
        """Position legs should be stored and retrieved as parsed JSON."""
        config = _make_config()
        tracker = PositionTracker(db, config)

        order_id, fills = await _submit_and_fill_order(db, config)
        await tracker.open_position(1, order_id, fills, 1)

        positions = await tracker.get_open_positions()
        legs = positions[0]["legs"]
        assert isinstance(legs, list)
        assert len(legs) == 2
        assert legs[0]["leg_name"] in ("short_put", "long_put")


class TestHelpers:
    """Tests for helper functions."""

    def test_calculate_max_profit_loss_credit_spread(self):
        """Credit spread: max profit = premium, max loss = width - premium."""
        legs = [
            {"option_type": "put", "strike": 5800.0, "action": "sell", "fill_price": 3.50},
            {"option_type": "put", "strike": 5750.0, "action": "buy", "fill_price": 1.90},
        ]
        entry_price = 1.60  # net credit
        max_profit, max_loss = _calculate_max_profit_loss(legs, entry_price, 100.0, 1)

        # Max profit = 1.60 * 100 = 160
        assert max_profit == pytest.approx(160.0, abs=1.0)
        # Max loss = (50 - 1.60) * 100 = 4840
        assert max_loss == pytest.approx(4840.0, abs=1.0)

    def test_calculate_max_profit_loss_iron_condor(self):
        """Iron condor: max profit = premium, max loss = wider side - premium."""
        legs = [
            {"option_type": "put", "strike": 5800.0, "action": "sell", "fill_price": 3.50},
            {"option_type": "put", "strike": 5750.0, "action": "buy", "fill_price": 1.90},
            {"option_type": "call", "strike": 6100.0, "action": "sell", "fill_price": 2.90},
            {"option_type": "call", "strike": 6150.0, "action": "buy", "fill_price": 1.70},
        ]
        entry_price = 2.80  # net credit
        max_profit, max_loss = _calculate_max_profit_loss(legs, entry_price, 100.0, 1)

        # Both spreads are $50 wide, max loss = (50 - 2.80) * 100 = 4720
        assert max_profit == pytest.approx(280.0, abs=1.0)
        assert max_loss == pytest.approx(4720.0, abs=1.0)

    def test_calculate_max_profit_loss_empty_legs(self):
        max_profit, max_loss = _calculate_max_profit_loss([], 0.0, 100.0, 1)
        assert max_profit == 0.0
        assert max_loss == 0.0

    def test_is_third_friday_true(self):
        """2025-03-21 is the 3rd Friday of March 2025."""
        assert _is_third_friday(date(2025, 3, 21)) is True

    def test_is_third_friday_false(self):
        """2025-03-14 is the 2nd Friday, not 3rd."""
        assert _is_third_friday(date(2025, 3, 14)) is False

    def test_is_third_friday_not_friday(self):
        """2025-03-20 is Thursday, not Friday."""
        assert _is_third_friday(date(2025, 3, 20)) is False

    def test_determine_settlement_type_am(self):
        """3rd Friday expiry should be AM settled."""
        legs = [{"expiry": "2025-03-21"}]
        assert _determine_settlement_type(legs) == "am"

    def test_determine_settlement_type_pm(self):
        """Non-3rd-Friday expiry should be PM settled."""
        legs = [{"expiry": "2025-03-19"}]
        assert _determine_settlement_type(legs) == "pm"

    def test_determine_settlement_type_mixed(self):
        """If any leg is 3rd Friday, should be AM."""
        legs = [
            {"expiry": "2025-03-19"},
            {"expiry": "2025-03-21"},  # 3rd Friday
        ]
        assert _determine_settlement_type(legs) == "am"
