"""Tests for paper order management and fill simulation.

Tests OrderManager (submit, fill, cancel, expire) and FillSimulator
(realistic fills with slippage). Uses in-memory SQLite databases
and mock options chain data.
"""

import json
from datetime import date, datetime

import aiosqlite
import pytest
import pytest_asyncio

from src.data import OptionContract, OptionsChain
from src.paper.models import LegSpec, PaperTradingConfig, SimulatedFill
from src.paper.orders import FillSimulator, OrderManager, _calculate_net_fill
from src.paper.schema import init_paper_tables
from src.paper.slippage import FixedSlippage


def _make_config(**overrides) -> PaperTradingConfig:
    """Create a PaperTradingConfig with optional overrides."""
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
    iv: float = 0.20,
    delta: float = -0.30,
) -> OptionContract:
    """Create a mock OptionContract."""
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
        iv=iv,
        delta=delta,
    )


def _make_chain(contracts: list[OptionContract] | None = None) -> OptionsChain:
    """Create a mock OptionsChain."""
    if contracts is None:
        contracts = [
            _make_contract(5800.0, "put", 3.40, 3.60, delta=-0.30),
            _make_contract(5750.0, "put", 1.80, 2.00, delta=-0.15),
            _make_contract(6100.0, "call", 2.80, 3.00, delta=0.25),
            _make_contract(6150.0, "call", 1.60, 1.80, delta=0.15),
        ]
    return OptionsChain(
        ticker="SPX",
        spot_price=5950.0,
        timestamp=datetime.now(),
        contracts=contracts,
    )


def _make_legs() -> list[LegSpec]:
    """Create a standard 2-leg put credit spread."""
    return [
        LegSpec("short_put", "put", 5800.0, date(2025, 3, 21), "sell"),
        LegSpec("long_put", "put", 5750.0, date(2025, 3, 21), "buy"),
    ]


def _make_ic_legs() -> list[LegSpec]:
    """Create a 4-leg iron condor."""
    return [
        LegSpec("short_put", "put", 5800.0, date(2025, 3, 21), "sell"),
        LegSpec("long_put", "put", 5750.0, date(2025, 3, 21), "buy"),
        LegSpec("short_call", "call", 6100.0, date(2025, 3, 21), "sell"),
        LegSpec("long_call", "call", 6150.0, date(2025, 3, 21), "buy"),
    ]


@pytest_asyncio.fixture
async def db():
    """Create an in-memory DB with required tables."""
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys = ON")
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
    now = datetime.now().isoformat()
    await conn.execute(
        "INSERT INTO strategies (name, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("Test IC", "paper", now, now),
    )
    await conn.commit()
    await init_paper_tables(conn)
    yield conn
    await conn.close()


# ── FillSimulator Tests ──


class TestFillSimulator:
    """Tests for the FillSimulator class."""

    def test_simulate_fill_buy(self):
        """Buy should fill above mid-price (using FixedSlippage for determinism)."""
        config = _make_config(slippage_pct=0.10)
        sim = FillSimulator(config, slippage_model=FixedSlippage(fixed_cents=0.02))
        chain = _make_chain()

        leg = LegSpec("long_put", "put", 5750.0, date(2025, 3, 21), "buy")
        fill = sim.simulate_fill(leg, chain)

        assert fill is not None
        assert fill.leg_name == "long_put"
        # Mid = 1.90, fixed slippage = $0.02
        # Fill = 1.90 + 0.02 = 1.92
        assert fill.fill_price == pytest.approx(1.92, abs=0.01)
        assert fill.mid == pytest.approx(1.90, abs=0.01)
        assert fill.fill_price > fill.mid  # Buy costs more than mid

    def test_simulate_fill_sell(self):
        """Sell should fill below mid-price."""
        config = _make_config(slippage_pct=0.10)
        sim = FillSimulator(config)
        chain = _make_chain()

        leg = LegSpec("short_put", "put", 5800.0, date(2025, 3, 21), "sell")
        fill = sim.simulate_fill(leg, chain)

        assert fill is not None
        assert fill.fill_price < fill.mid  # Sell receives less than mid

    def test_simulate_fill_contract_not_found(self):
        """Fill should return None if contract not in chain."""
        config = _make_config()
        sim = FillSimulator(config)
        chain = _make_chain()

        leg = LegSpec("missing", "put", 9999.0, date(2025, 3, 21), "sell")
        fill = sim.simulate_fill(leg, chain)
        assert fill is None

    def test_simulate_fill_captures_greeks(self):
        """Fill should capture IV and delta from the contract."""
        config = _make_config()
        sim = FillSimulator(config)
        contract = _make_contract(5800.0, iv=0.25, delta=-0.35)
        chain = _make_chain([contract])

        leg = LegSpec("test", "put", 5800.0, date(2025, 3, 21), "sell")
        fill = sim.simulate_fill(leg, chain)

        assert fill is not None
        assert fill.iv == 0.25
        assert fill.delta == -0.35

    def test_simulate_fill_clamped_to_bid_ask(self):
        """Fill price should be within bid-ask range."""
        config = _make_config(slippage_pct=2.0)  # Extreme slippage
        sim = FillSimulator(config)
        chain = _make_chain()

        leg = LegSpec("test", "put", 5800.0, date(2025, 3, 21), "buy")
        fill = sim.simulate_fill(leg, chain)

        assert fill is not None
        assert fill.fill_price >= fill.bid
        assert fill.fill_price <= fill.ask

    def test_simulate_spread_fill_all_or_nothing(self):
        """Spread fill returns None if any leg cannot be filled."""
        config = _make_config()
        sim = FillSimulator(config)
        chain = _make_chain()

        legs = [
            LegSpec("exists", "put", 5800.0, date(2025, 3, 21), "sell"),
            LegSpec("missing", "put", 9999.0, date(2025, 3, 21), "buy"),
        ]
        result = sim.simulate_spread_fill(legs, chain)
        assert result is None

    def test_simulate_spread_fill_success(self):
        """Full spread fill should return all legs."""
        config = _make_config()
        sim = FillSimulator(config)
        chain = _make_chain()

        legs = _make_legs()
        fills = sim.simulate_spread_fill(legs, chain)

        assert fills is not None
        assert len(fills) == 2
        assert fills[0].leg_name == "short_put"
        assert fills[1].leg_name == "long_put"

    def test_simulate_fill_zero_spread(self):
        """Zero spread with FixedSlippage should produce fill at mid (no spread to offset).

        Note: DynamicSpreadSlippage estimates a synthetic spread when
        bid == ask (stale quote), so we use FixedSlippage here to test
        the zero-spread behavior deterministically.
        """
        config = _make_config(slippage_pct=0.10)
        sim = FillSimulator(config, slippage_model=FixedSlippage(fixed_cents=0.02))
        contract = _make_contract(5800.0, bid=3.50, ask=3.50)
        chain = _make_chain([contract])

        leg = LegSpec("test", "put", 5800.0, date(2025, 3, 21), "buy")
        fill = sim.simulate_fill(leg, chain)

        assert fill is not None
        # FixedSlippage with bid==ask clamps fill to bid-ask range
        # So fill_price == mid == 3.50
        assert fill.fill_price == fill.mid
        assert fill.slippage == 0.0


# ── OrderManager Tests ──


class TestOrderManager:
    """Tests for the OrderManager class."""

    @pytest.mark.asyncio
    async def test_submit_order(self, db):
        """Submit a market order and verify it's pending."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_legs()

        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        assert order_id > 0
        order = await mgr.get_order(order_id)
        assert order is not None
        assert order["status"] == "pending"
        assert order["direction"] == "open"
        assert order["order_type"] == "market"
        assert order["quantity"] == 1
        assert len(order["legs"]) == 2

    @pytest.mark.asyncio
    async def test_submit_limit_order(self, db):
        """Submit a limit order with a price."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_legs()

        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=2, order_type="limit", limit_price=1.50,
        )

        order = await mgr.get_order(order_id)
        assert order["order_type"] == "limit"
        assert order["limit_price"] == 1.50
        assert order["quantity"] == 2

    @pytest.mark.asyncio
    async def test_try_fill_market_order(self, db):
        """Market orders should fill immediately."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_legs()

        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        chain = _make_chain()
        fills = await mgr.try_fill(order_id, {"SPX": chain})

        assert fills is not None
        assert len(fills) == 2

        # Order should now be filled
        order = await mgr.get_order(order_id)
        assert order["status"] == "filled"
        assert order["fill_price"] is not None
        assert order["filled_at"] is not None

    @pytest.mark.asyncio
    async def test_try_fill_records_fills(self, db):
        """Fill should create paper_fills records for each leg."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_legs()

        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        chain = _make_chain()
        await mgr.try_fill(order_id, {"SPX": chain})

        fills = await mgr.get_fills_for_order(order_id)
        assert len(fills) == 2
        assert fills[0]["leg_name"] == "short_put"
        assert fills[1]["leg_name"] == "long_put"
        assert fills[0]["bid_at_fill"] > 0
        assert fills[0]["ask_at_fill"] > 0

    @pytest.mark.asyncio
    async def test_try_fill_already_filled(self, db):
        """Trying to fill an already-filled order should return None."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_legs()

        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        chain = _make_chain()
        await mgr.try_fill(order_id, {"SPX": chain})
        second = await mgr.try_fill(order_id, {"SPX": chain})
        assert second is None

    @pytest.mark.asyncio
    async def test_try_fill_no_chain(self, db):
        """Fill should fail gracefully with empty chains."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_legs()

        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        result = await mgr.try_fill(order_id, {})
        assert result is None

        # Order should still be pending with incremented tick count
        order = await mgr.get_order(order_id)
        assert order["status"] == "pending"
        assert order["ticks_pending"] == 1

    @pytest.mark.asyncio
    async def test_cancel_order(self, db):
        """Cancel should change status and record reason."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_legs()

        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        await mgr.cancel_order(order_id, "test cancellation")

        order = await mgr.get_order(order_id)
        assert order["status"] == "cancelled"
        assert order["cancelled_at"] is not None

    @pytest.mark.asyncio
    async def test_cancel_filled_order_noop(self, db):
        """Cancelling a filled order should be a no-op."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_legs()

        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        chain = _make_chain()
        await mgr.try_fill(order_id, {"SPX": chain})
        await mgr.cancel_order(order_id, "too late")

        order = await mgr.get_order(order_id)
        assert order["status"] == "filled"

    @pytest.mark.asyncio
    async def test_expire_stale_orders(self, db):
        """Orders pending >= max_order_age_ticks should be expired."""
        config = _make_config(max_order_age_ticks=3)
        mgr = OrderManager(db, config)

        # Create a leg with a strike that won't be found in our chain
        legs = [LegSpec("test", "put", 9999.0, date(2025, 3, 21), "sell")]
        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        # Simulate 3 failed fill attempts (incrementing ticks_pending)
        chain = _make_chain()
        for _ in range(3):
            await mgr.try_fill(order_id, {"SPX": chain})

        order = await mgr.get_order(order_id)
        assert order["ticks_pending"] == 3

        expired = await mgr.expire_stale_orders()
        assert expired == 1

        order = await mgr.get_order(order_id)
        assert order["status"] == "expired"

    @pytest.mark.asyncio
    async def test_expire_stale_orders_leaves_fresh(self, db):
        """Orders below max_order_age_ticks should not be expired."""
        config = _make_config(max_order_age_ticks=5)
        mgr = OrderManager(db, config)

        legs = [LegSpec("test", "put", 9999.0, date(2025, 3, 21), "sell")]
        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        # Only 2 ticks
        chain = _make_chain()
        for _ in range(2):
            await mgr.try_fill(order_id, {"SPX": chain})

        expired = await mgr.expire_stale_orders()
        assert expired == 0

        order = await mgr.get_order(order_id)
        assert order["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_pending_orders(self, db):
        """Should return only pending orders."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_legs()

        id1 = await mgr.submit_order(1, "open", legs, 1, "market")
        id2 = await mgr.submit_order(1, "open", legs, 1, "market")

        # Fill one
        chain = _make_chain()
        await mgr.try_fill(id1, {"SPX": chain})

        pending = await mgr.get_pending_orders()
        assert len(pending) == 1
        assert pending[0]["id"] == id2

    @pytest.mark.asyncio
    async def test_iron_condor_fill(self, db):
        """4-leg iron condor should fill all legs."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_ic_legs()

        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        chain = _make_chain()
        fills = await mgr.try_fill(order_id, {"SPX": chain})

        assert fills is not None
        assert len(fills) == 4
        assert {f.leg_name for f in fills} == {"short_put", "long_put", "short_call", "long_call"}

    @pytest.mark.asyncio
    async def test_net_fill_credit_spread(self, db):
        """Net fill for credit spread should be positive (credit)."""
        config = _make_config()
        mgr = OrderManager(db, config)
        legs = _make_legs()  # sell 5800 put, buy 5750 put

        order_id = await mgr.submit_order(
            strategy_id=1, direction="open", legs=legs,
            quantity=1, order_type="market",
        )

        chain = _make_chain()
        fills = await mgr.try_fill(order_id, {"SPX": chain})

        assert fills is not None
        order = await mgr.get_order(order_id)
        # Sell at ~3.48, buy at ~1.92 -> net credit ~1.56
        assert order["fill_price"] > 0  # Net credit


# ── _calculate_net_fill Tests ──


class TestCalculateNetFill:
    """Tests for the _calculate_net_fill helper."""

    def test_credit_spread(self):
        """Credit spread: sell > buy = positive net."""
        fills = [
            SimulatedFill("short_put", 3.48, 3.40, 3.60, 3.50, 0.02),
            SimulatedFill("long_put", 1.92, 1.80, 2.00, 1.90, 0.02),
        ]
        legs = [
            LegSpec("short_put", "put", 5800.0, date(2025, 3, 21), "sell"),
            LegSpec("long_put", "put", 5750.0, date(2025, 3, 21), "buy"),
        ]
        net = _calculate_net_fill(fills, legs)
        assert net > 0  # Net credit: sell 3.48 - buy 1.92 = 1.56

    def test_debit_spread(self):
        """Debit spread: buy > sell = negative net."""
        fills = [
            SimulatedFill("long_call", 3.02, 2.80, 3.00, 2.90, 0.03),
            SimulatedFill("short_call", 1.68, 1.60, 1.80, 1.70, 0.02),
        ]
        legs = [
            LegSpec("long_call", "call", 6100.0, date(2025, 3, 21), "buy"),
            LegSpec("short_call", "call", 6150.0, date(2025, 3, 21), "sell"),
        ]
        net = _calculate_net_fill(fills, legs)
        assert net < 0  # Net debit: sell 1.68 - buy 3.02 = -1.34

    def test_iron_condor_credit(self):
        """Iron condor should produce net credit."""
        fills = [
            SimulatedFill("short_put", 3.48, 3.40, 3.60, 3.50, 0.02),
            SimulatedFill("long_put", 1.92, 1.80, 2.00, 1.90, 0.02),
            SimulatedFill("short_call", 2.88, 2.80, 3.00, 2.90, 0.02),
            SimulatedFill("long_call", 1.72, 1.60, 1.80, 1.70, 0.02),
        ]
        legs = _make_ic_legs()
        net = _calculate_net_fill(fills, legs)
        # sell (3.48 + 2.88) - buy (1.92 + 1.72) = 6.36 - 3.64 = 2.72
        assert net > 0
        assert net == pytest.approx(2.72, abs=0.01)
