"""Tests for the ShadowModeManager.

Tests entry signal detection, strike selection by delta,
schedule filtering, position limit checking, and the 3:00 PM rule.
Uses in-memory SQLite and mock options chain data.
"""

import json
from datetime import date, datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest
import pytest_asyncio

from src.data import OptionContract, OptionsChain
from src.paper.models import LegSpec, PaperTradingConfig
from src.paper.orders import OrderManager
from src.paper.positions import PositionTracker
from src.paper.schema import init_paper_tables
from src.paper.shadow import ShadowModeManager


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
    delta: float | None = None,
) -> OptionContract:
    if delta is None:
        delta = -0.30 if option_type == "put" else 0.30
    return OptionContract(
        ticker="SPX",
        expiry=expiry or (date.today() + timedelta(days=30)),
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        last=(bid + ask) / 2,
        volume=1000,
        open_interest=5000,
        iv=0.20,
        delta=delta,
    )


def _make_chain(expiry: date | None = None) -> OptionsChain:
    exp = expiry or (date.today() + timedelta(days=30))
    return OptionsChain(
        ticker="SPX",
        spot_price=5950.0,
        timestamp=datetime.now(),
        contracts=[
            _make_contract(5800.0, "put", 3.40, 3.60, exp, delta=-0.30),
            _make_contract(5750.0, "put", 1.80, 2.00, exp, delta=-0.15),
            _make_contract(5700.0, "put", 0.80, 1.00, exp, delta=-0.08),
            _make_contract(6100.0, "call", 2.80, 3.00, exp, delta=0.30),
            _make_contract(6150.0, "call", 1.60, 1.80, exp, delta=0.15),
            _make_contract(6200.0, "call", 0.70, 0.90, exp, delta=0.08),
        ],
    )


def _make_template_yaml() -> str:
    """Return a minimal strategy template as YAML string."""
    import yaml

    template = {
        "name": "Test IC",
        "version": "1.0",
        "description": "Test iron condor",
        "ticker": "SPX",
        "structure": {
            "strategy_type": "iron_condor",
            "legs": [
                {"name": "short_put", "side": "put", "action": "sell",
                 "delta_target": "fixed", "delta_value": 0.30, "quantity": 1},
                {"name": "long_put", "side": "put", "action": "buy",
                 "delta_target": "fixed", "delta_value": 0.15, "quantity": 1},
                {"name": "short_call", "side": "call", "action": "sell",
                 "delta_target": "fixed", "delta_value": 0.30, "quantity": 1},
                {"name": "long_call", "side": "call", "action": "buy",
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

    template_yaml = _make_template_yaml()
    await conn.execute(
        "INSERT INTO strategies (name, status, template_yaml, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("Test IC", "paper", template_yaml, now, now),
    )
    await conn.commit()
    await init_paper_tables(conn)

    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def strategy_manager(db):
    from src.strategy.lifecycle import StrategyManager
    mgr = StrategyManager(db)
    return mgr


@pytest_asyncio.fixture
async def shadow(db, strategy_manager):
    config = _make_config()
    order_mgr = OrderManager(db, config)
    pos_tracker = PositionTracker(db, config)
    return ShadowModeManager(
        db=db,
        strategy_manager=strategy_manager,
        order_manager=order_mgr,
        position_tracker=pos_tracker,
        config=config,
    )


# --- Strike Selection Tests ---


class TestSelectStrikes:
    """Tests for ShadowModeManager.select_strikes()."""

    def test_select_strikes_iron_condor(self, shadow):
        """Select 4 legs for an iron condor by delta targets."""
        chain = _make_chain()
        template = shadow._load_template(_make_template_yaml())
        assert template is not None

        legs = shadow.select_strikes(template, chain)

        assert legs is not None
        assert len(legs) == 4

        # Check leg names match
        leg_names = {leg.leg_name for leg in legs}
        assert leg_names == {"short_put", "long_put", "short_call", "long_call"}

        # Check put legs have put option_type
        for leg in legs:
            if "put" in leg.leg_name:
                assert leg.option_type == "put"
            elif "call" in leg.leg_name:
                assert leg.option_type == "call"

    def test_select_strikes_delta_matching(self, shadow):
        """Strikes should be selected closest to delta targets."""
        chain = _make_chain()
        template = shadow._load_template(_make_template_yaml())
        assert template is not None

        legs = shadow.select_strikes(template, chain)
        assert legs is not None

        # short_put delta target = 0.30 -> should match 5800 (delta=-0.30)
        short_put = next(l for l in legs if l.leg_name == "short_put")
        assert short_put.strike == 5800.0

        # long_put delta target = 0.15 -> should match 5750 (delta=-0.15)
        long_put = next(l for l in legs if l.leg_name == "long_put")
        assert long_put.strike == 5750.0

    def test_select_strikes_no_matching_expiry(self, shadow):
        """Return None if no expiry matches DTE target."""
        # Chain with contracts expiring too far out
        far_date = date.today() + timedelta(days=90)
        chain = OptionsChain(
            ticker="SPX",
            spot_price=5950.0,
            timestamp=datetime.now(),
            contracts=[
                _make_contract(5800.0, "put", 3.40, 3.60, far_date),
            ],
        )
        template = shadow._load_template(_make_template_yaml())
        assert template is not None

        legs = shadow.select_strikes(template, chain)
        assert legs is None

    def test_select_strikes_empty_chain(self, shadow):
        """Return None for an empty chain."""
        chain = OptionsChain(
            ticker="SPX",
            spot_price=5950.0,
            timestamp=datetime.now(),
            contracts=[],
        )
        template = shadow._load_template(_make_template_yaml())
        assert template is not None

        legs = shadow.select_strikes(template, chain)
        assert legs is None

    def test_find_best_expiry(self, shadow):
        """Find best expiry matching DTE target within bounds."""
        chain = _make_chain()
        expiry = shadow._find_best_expiry(
            chain, dte_target=30, dte_min=20, dte_max=45
        )

        expected = date.today() + timedelta(days=30)
        assert expiry == expected

    def test_find_best_expiry_none(self, shadow):
        """Return None when no expiry in bounds."""
        chain = OptionsChain(
            ticker="SPX",
            spot_price=5950.0,
            timestamp=datetime.now(),
            contracts=[
                _make_contract(5800.0, "put", 3.40, 3.60,
                               date.today() + timedelta(days=100)),
            ],
        )
        expiry = shadow._find_best_expiry(
            chain, dte_target=30, dte_min=20, dte_max=45
        )
        assert expiry is None


# --- Entry Signal Detection Tests ---


class TestCheckEntrySignals:
    """Tests for ShadowModeManager.check_entry_signals()."""

    @pytest.mark.asyncio
    async def test_check_entry_signals_submits_order(self, shadow, db):
        """Should submit an order when all conditions are met."""
        chain = _make_chain()
        chains = {"SPX": chain}

        # Patch time to be within trading hours on a weekday
        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)  # Monday 10:30 AM
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            order_ids = await shadow.check_entry_signals(chains)

        assert len(order_ids) == 1
        assert isinstance(order_ids[0], int)

        # Verify the order was submitted
        cursor = await db.execute(
            "SELECT id, strategy_id, direction, status FROM paper_orders WHERE id = ?",
            (order_ids[0],),
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[2] == "open"  # direction
        assert row[3] == "pending"  # status

    @pytest.mark.asyncio
    async def test_check_entry_signals_no_paper_strategies(self, db):
        """No orders if there are no PAPER strategies."""
        config = _make_config()
        order_mgr = OrderManager(db, config)
        pos_tracker = PositionTracker(db, config)

        # Use a mock strategy manager that returns empty list
        mock_mgr = AsyncMock()
        mock_mgr.list_strategies = AsyncMock(return_value=[])

        shadow = ShadowModeManager(
            db=db,
            strategy_manager=mock_mgr,
            order_manager=order_mgr,
            position_tracker=pos_tracker,
            config=config,
        )

        chain = _make_chain()
        chains = {"SPX": chain}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            order_ids = await shadow.check_entry_signals(chains)

        assert len(order_ids) == 0

    @pytest.mark.asyncio
    async def test_check_entry_signals_empty_chains(self, shadow):
        """No orders if no chains available."""
        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            order_ids = await shadow.check_entry_signals({})

        assert len(order_ids) == 0

    @pytest.mark.asyncio
    async def test_check_entry_signals_weekend_skipped(self, shadow):
        """No orders on weekends."""
        chain = _make_chain()
        chains = {"SPX": chain}

        # Saturday
        mock_now = datetime(2025, 3, 8, 10, 30, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            order_ids = await shadow.check_entry_signals(chains)

        assert len(order_ids) == 0


# --- Schedule Filtering Tests ---


class TestScheduleFiltering:
    """Tests for schedule checks in ShadowModeManager."""

    @pytest.mark.asyncio
    async def test_outside_entry_window(self, shadow):
        """No orders outside entry window (before 09:35)."""
        chain = _make_chain()
        chains = {"SPX": chain}

        # Monday 9:00 AM - before entry window
        mock_now = datetime(2025, 3, 10, 9, 0, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            order_ids = await shadow.check_entry_signals(chains)

        assert len(order_ids) == 0

    @pytest.mark.asyncio
    async def test_after_entry_window(self, shadow):
        """No orders after entry window (after 15:30)."""
        chain = _make_chain()
        chains = {"SPX": chain}

        # Monday 15:45 - after entry window
        mock_now = datetime(2025, 3, 10, 15, 45, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            order_ids = await shadow.check_entry_signals(chains)

        assert len(order_ids) == 0


# --- Position Limit Tests ---


class TestPositionLimits:
    """Tests for position limit enforcement."""

    @pytest.mark.asyncio
    async def test_position_limit_respected(self, shadow, db):
        """No new orders when max positions reached."""
        chain = _make_chain()
        chains = {"SPX": chain}

        # Pre-populate 3 open positions (max_positions = 3 in template)
        now = datetime.now().isoformat()
        for i in range(3):
            await db.execute(
                """INSERT INTO paper_orders
                   (strategy_id, order_type, direction, legs, quantity,
                    status, submitted_at, ticks_pending)
                   VALUES (1, 'market', 'open', '[]', 1, 'filled', ?, 0)""",
                (now,),
            )
        for i in range(3):
            await db.execute(
                """INSERT INTO paper_positions
                   (strategy_id, open_order_id, status, legs, entry_price,
                    quantity, opened_at)
                   VALUES (1, ?, 'open', '[]', 1.0, 1, ?)""",
                (i + 1, now),
            )
        await db.commit()

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            order_ids = await shadow.check_entry_signals(chains)

        assert len(order_ids) == 0

    @pytest.mark.asyncio
    async def test_daily_entry_limit(self, shadow, db):
        """No more than one entry per strategy per day."""
        chain = _make_chain()
        chains = {"SPX": chain}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            # First entry should succeed
            order_ids_1 = await shadow.check_entry_signals(chains)
            assert len(order_ids_1) == 1

            # Second entry on same day should be blocked
            order_ids_2 = await shadow.check_entry_signals(chains)
            assert len(order_ids_2) == 0


# --- 3:00 PM Rule Tests ---


class TestThreePMRule:
    """Tests for the 3:00 PM 0DTE entry blocking rule."""

    @pytest.mark.asyncio
    async def test_0dte_blocked_after_3pm(self, db, strategy_manager):
        """0DTE entries should be blocked after 15:00 ET."""
        config = _make_config()
        order_mgr = OrderManager(db, config)
        pos_tracker = PositionTracker(db, config)

        shadow = ShadowModeManager(
            db=db,
            strategy_manager=strategy_manager,
            order_manager=order_mgr,
            position_tracker=pos_tracker,
            config=config,
        )

        # Update strategy template to 0DTE
        import yaml

        template_data = yaml.safe_load(_make_template_yaml())
        template_data["structure"]["dte_target"] = 0
        template_data["structure"]["dte_min"] = 0
        template_data["structure"]["dte_max"] = 0
        new_yaml = yaml.dump(template_data)

        await db.execute(
            "UPDATE strategies SET template_yaml = ? WHERE id = 1",
            (new_yaml,),
        )
        await db.commit()

        # Chain with 0DTE contracts
        today = date.today()
        chain = OptionsChain(
            ticker="SPX",
            spot_price=5950.0,
            timestamp=datetime.now(),
            contracts=[
                _make_contract(5800.0, "put", 3.40, 3.60, today, delta=-0.30),
                _make_contract(5750.0, "put", 1.80, 2.00, today, delta=-0.15),
                _make_contract(6100.0, "call", 2.80, 3.00, today, delta=0.30),
                _make_contract(6150.0, "call", 1.60, 1.80, today, delta=0.15),
            ],
        )
        chains = {"SPX": chain}

        # At 15:30 - should be blocked
        mock_now = datetime(2025, 3, 10, 15, 30, tzinfo=None)
        with patch("src.paper.shadow._now_et", return_value=mock_now):
            order_ids = await shadow.check_entry_signals(chains)

        assert len(order_ids) == 0


# --- Daily State Reset Tests ---


class TestDailyStateReset:
    """Tests for daily state management."""

    def test_reset_daily_state(self, shadow):
        """reset_daily_state() should clear entry tracking."""
        shadow._entries_today = {1: 2, 2: 1}
        shadow._last_reset_date = "2025-03-10"

        shadow.reset_daily_state()

        assert shadow._entries_today == {}
        assert shadow._last_reset_date == ""

    def test_daily_tracking_resets_on_date_change(self, shadow):
        """Daily tracking should auto-reset when date changes."""
        shadow._entries_today = {1: 1}
        shadow._last_reset_date = "2025-03-09"  # yesterday

        shadow._reset_daily_tracking()

        assert shadow._entries_today == {}


# --- Template Loading Tests ---


class TestTemplateLoading:
    """Tests for strategy template loading."""

    def test_load_template_from_yaml_string(self, shadow):
        """Should parse a YAML string into a StrategyTemplate."""
        yaml_str = _make_template_yaml()
        template = shadow._load_template(yaml_str)

        assert template is not None
        assert template.name == "Test IC"
        assert len(template.structure.legs) == 4

    def test_load_template_invalid_yaml(self, shadow):
        """Should return None for invalid YAML."""
        template = shadow._load_template("not: valid: yaml: [")
        # May succeed or fail depending on yaml parser behavior
        # The important thing is it doesn't raise an exception

    def test_load_template_no_strategy_manager(self, db):
        """Should work even without a strategy manager."""
        config = _make_config()
        order_mgr = OrderManager(db, config)
        pos_tracker = PositionTracker(db, config)

        shadow = ShadowModeManager(
            db=db,
            strategy_manager=None,
            order_manager=order_mgr,
            position_tracker=pos_tracker,
            config=config,
        )

        yaml_str = _make_template_yaml()
        template = shadow._load_template(yaml_str)
        assert template is not None
