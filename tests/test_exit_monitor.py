"""Tests for the ExitMonitor.

Tests profit target, stop loss, DTE exit, time stop, expiration,
and AM/PM settlement handling.
Uses in-memory SQLite and mock options chain data.
"""

import json
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest
import pytest_asyncio
import yaml

from src.data import OptionContract, OptionsChain
from src.paper.exits import ExitMonitor, _get_settlement_type, _is_third_friday
from src.paper.models import ExitSignal, PaperTradingConfig
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


def _make_template_yaml(
    profit_target_pct: float = 0.50,
    stop_loss_pct: float = 2.0,
    dte_close: int = 0,
    time_stop_days: int | None = None,
) -> str:
    """Build a template YAML with configurable exit rules."""
    template = {
        "name": "Test Strategy",
        "version": "1.0",
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
        "entry": {},
        "exit": {
            "profit_target_pct": profit_target_pct,
            "stop_loss_pct": stop_loss_pct,
            "dte_close": dte_close,
        },
        "sizing": {"max_positions": 3, "max_risk_pct": 0.02, "max_contracts": 10},
        "schedule": {"trading_days": [0, 1, 2, 3, 4]},
    }
    if time_stop_days is not None:
        template["exit"]["time_stop_days"] = time_stop_days
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
        ("Test Strategy", "paper", template_yaml, now, now),
    )
    await conn.commit()
    await init_paper_tables(conn)

    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def strategy_manager(db):
    from src.strategy.lifecycle import StrategyManager
    return StrategyManager(db)


@pytest_asyncio.fixture
async def position_tracker(db):
    return PositionTracker(db, _make_config())


@pytest_asyncio.fixture
async def exit_monitor(db, strategy_manager, position_tracker):
    return ExitMonitor(
        db=db,
        strategy_manager=strategy_manager,
        position_tracker=position_tracker,
        config=_make_config(),
    )


async def _create_position(
    db,
    strategy_id: int = 1,
    entry_price: float = 1.50,
    max_profit: float = 150.0,
    max_loss: float = 350.0,
    unrealized_pnl: float = 0.0,
    expiry: date | None = None,
    opened_at: str | None = None,
) -> int:
    """Helper to create an open position for testing."""
    exp = expiry or (date.today() + timedelta(days=30))
    now = opened_at or datetime.now().isoformat()

    legs = json.dumps([
        {"leg_name": "short_put", "option_type": "put", "strike": 5800.0,
         "expiry": exp.isoformat(), "action": "sell", "quantity": 1,
         "fill_price": 3.50},
        {"leg_name": "long_put", "option_type": "put", "strike": 5750.0,
         "expiry": exp.isoformat(), "action": "buy", "quantity": 1,
         "fill_price": 2.00},
    ])

    # Create a dummy order first
    order_cursor = await db.execute(
        """INSERT INTO paper_orders
           (strategy_id, order_type, direction, legs, quantity,
            status, submitted_at, ticks_pending)
           VALUES (?, 'market', 'open', ?, 1, 'filled', ?, 0)""",
        (strategy_id, legs, now),
    )
    order_id = order_cursor.lastrowid

    cursor = await db.execute(
        """INSERT INTO paper_positions
           (strategy_id, open_order_id, status, legs, entry_price,
            quantity, max_profit, max_loss, unrealized_pnl, opened_at)
           VALUES (?, ?, 'open', ?, ?, 1, ?, ?, ?, ?)""",
        (strategy_id, order_id, legs, entry_price, max_profit, max_loss,
         unrealized_pnl, now),
    )
    await db.commit()
    return cursor.lastrowid


# --- Settlement Type Tests ---


class TestSettlementType:
    """Tests for AM/PM settlement type detection."""

    def test_third_friday_is_am(self):
        """3rd Friday of January 2025 = AM settlement."""
        # January 2025: 1st=Wed, 3rd Friday = Jan 17
        assert _is_third_friday(date(2025, 1, 17)) is True
        assert _get_settlement_type(date(2025, 1, 17)) == "am"

    def test_non_third_friday_is_pm(self):
        """A non-3rd-Friday expiry = PM settlement."""
        # January 10 is the 2nd Friday
        assert _is_third_friday(date(2025, 1, 10)) is False
        assert _get_settlement_type(date(2025, 1, 10)) == "pm"

    def test_third_friday_february(self):
        """3rd Friday of February 2025 = Feb 21."""
        assert _is_third_friday(date(2025, 2, 21)) is True
        assert _get_settlement_type(date(2025, 2, 21)) == "am"

    def test_non_friday_is_pm(self):
        """Non-Friday dates are always PM settlement."""
        assert _is_third_friday(date(2025, 1, 16)) is False  # Thursday
        assert _get_settlement_type(date(2025, 1, 16)) == "pm"

    def test_fourth_friday_is_pm(self):
        """4th Friday of a month is PM settlement (not AM)."""
        # January 2025: 4th Friday = Jan 24
        assert _is_third_friday(date(2025, 1, 24)) is False
        assert _get_settlement_type(date(2025, 1, 24)) == "pm"


# --- Profit Target Tests ---


class TestProfitTarget:
    """Tests for profit target exit condition."""

    @pytest.mark.asyncio
    async def test_profit_target_triggers(self, exit_monitor, db):
        """Signal generated when unrealized PnL >= max_profit * target_pct."""
        pos_id = await _create_position(
            db,
            max_profit=150.0,
            unrealized_pnl=80.0,  # 80/150 = 53% > 50% target
        )

        chains = {"SPX": OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            signals = await exit_monitor.check_all_positions(chains)

        assert len(signals) == 1
        assert signals[0].position_id == pos_id
        assert signals[0].reason == "profit_target"
        assert signals[0].urgency == "normal"

    @pytest.mark.asyncio
    async def test_profit_target_not_met(self, exit_monitor, db):
        """No signal when unrealized PnL below target."""
        await _create_position(
            db,
            max_profit=150.0,
            unrealized_pnl=50.0,  # 50/150 = 33% < 50% target
        )

        chains = {"SPX": OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            signals = await exit_monitor.check_all_positions(chains)

        assert len(signals) == 0


# --- Stop Loss Tests ---


class TestStopLoss:
    """Tests for stop loss exit condition."""

    @pytest.mark.asyncio
    async def test_stop_loss_triggers(self, exit_monitor, db):
        """Signal generated when loss exceeds stop_loss_pct * max_profit."""
        pos_id = await _create_position(
            db,
            max_profit=150.0,
            unrealized_pnl=-310.0,  # loss > 150 * 2.0 = 300
        )

        chains = {"SPX": OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            signals = await exit_monitor.check_all_positions(chains)

        assert len(signals) == 1
        assert signals[0].position_id == pos_id
        assert signals[0].reason == "stop_loss"
        assert signals[0].urgency == "immediate"

    @pytest.mark.asyncio
    async def test_stop_loss_not_triggered(self, exit_monitor, db):
        """No signal when loss is within tolerance."""
        await _create_position(
            db,
            max_profit=150.0,
            unrealized_pnl=-200.0,  # loss < 150 * 2.0 = 300
        )

        chains = {"SPX": OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            signals = await exit_monitor.check_all_positions(chains)

        assert len(signals) == 0


# --- DTE Exit Tests ---


class TestDTEExit:
    """Tests for DTE-based exit condition."""

    @pytest.mark.asyncio
    async def test_dte_exit_triggers(self, db, strategy_manager, position_tracker):
        """Signal generated when DTE reaches dte_close threshold."""
        # Use a template with dte_close = 5
        template_yaml = _make_template_yaml(dte_close=5)
        await db.execute(
            "UPDATE strategies SET template_yaml = ? WHERE id = 1",
            (template_yaml,),
        )
        await db.commit()

        exit_monitor = ExitMonitor(
            db=db,
            strategy_manager=strategy_manager,
            position_tracker=position_tracker,
            config=_make_config(),
        )

        # Position with 3 DTE (< 5 threshold)
        near_expiry = date.today() + timedelta(days=3)
        pos_id = await _create_position(db, expiry=near_expiry, max_profit=150.0)

        chains = {"SPX": OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            signals = await exit_monitor.check_all_positions(chains)

        assert len(signals) == 1
        assert signals[0].reason == "dte_exit"


# --- Time Stop Tests ---


class TestTimeStop:
    """Tests for time-based stop (days held)."""

    @pytest.mark.asyncio
    async def test_time_stop_triggers(self, db, strategy_manager, position_tracker):
        """Signal generated when days held >= time_stop_days."""
        # Use a template with time_stop_days = 7
        template_yaml = _make_template_yaml(time_stop_days=7)
        await db.execute(
            "UPDATE strategies SET template_yaml = ? WHERE id = 1",
            (template_yaml,),
        )
        await db.commit()

        exit_monitor = ExitMonitor(
            db=db,
            strategy_manager=strategy_manager,
            position_tracker=position_tracker,
            config=_make_config(),
        )

        # Position opened 10 days ago
        opened_at = (datetime.now() - timedelta(days=10)).isoformat()
        pos_id = await _create_position(
            db, max_profit=150.0, opened_at=opened_at,
        )

        chains = {"SPX": OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            signals = await exit_monitor.check_all_positions(chains)

        assert len(signals) == 1
        assert signals[0].reason == "time_stop"


# --- Expiration Tests ---


class TestExpiration:
    """Tests for expiration-based exit."""

    @pytest.mark.asyncio
    async def test_expiration_triggers(self, exit_monitor, db):
        """Signal generated when any leg expires today."""
        today = date.today()
        pos_id = await _create_position(db, expiry=today, max_profit=150.0)

        chains = {"SPX": OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            signals = await exit_monitor.check_all_positions(chains)

        assert len(signals) == 1
        assert signals[0].position_id == pos_id
        assert signals[0].reason == "expiration"
        assert signals[0].urgency == "immediate"


# --- Settlement Handling Tests ---


class TestSettlementHandling:
    """Tests for EOD settlement logic."""

    @pytest.mark.asyncio
    async def test_pm_settlement_on_expiry(self, exit_monitor, db):
        """PM-settled position closes on expiry day."""
        # Use a non-3rd-Friday date for PM settlement
        expiry = date(2025, 3, 12)  # Wednesday
        pos_id = await _create_position(db, expiry=expiry, max_profit=150.0)

        chain = OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )
        chains = {"SPX": chain}

        # Patch today to be the expiry date
        with patch("src.paper.exits.date") as mock_date:
            mock_date.today.return_value = expiry
            mock_date.fromisoformat = date.fromisoformat
            mock_date.side_effect = lambda *a, **k: date(*a, **k)
            closed_ids = await exit_monitor.handle_settlements(chains)

        assert pos_id in closed_ids

    @pytest.mark.asyncio
    async def test_am_settlement_on_thursday(self, exit_monitor, db):
        """AM-settled position closes Thursday before 3rd Friday."""
        # 3rd Friday of March 2025 = March 21
        expiry = date(2025, 3, 21)
        thursday_before = date(2025, 3, 20)
        pos_id = await _create_position(db, expiry=expiry, max_profit=150.0)

        chain = OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )
        chains = {"SPX": chain}

        # Patch today to Thursday
        with patch("src.paper.exits.date") as mock_date:
            mock_date.today.return_value = thursday_before
            mock_date.fromisoformat = date.fromisoformat
            mock_date.side_effect = lambda *a, **k: date(*a, **k)
            closed_ids = await exit_monitor.handle_settlements(chains)

        assert pos_id in closed_ids

    @pytest.mark.asyncio
    async def test_no_settlement_before_expiry(self, exit_monitor, db):
        """No settlement if position hasn't reached expiry yet."""
        future_expiry = date.today() + timedelta(days=15)
        await _create_position(db, expiry=future_expiry, max_profit=150.0)

        chain = OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )
        chains = {"SPX": chain}

        closed_ids = await exit_monitor.handle_settlements(chains)
        assert len(closed_ids) == 0


# --- 3:00 PM Rule Tests ---


class TestThreePMRule:
    """Tests for the 3:00 PM 0DTE blocking static method."""

    def test_blocked_at_3pm(self):
        """Should be blocked at 15:00 ET."""
        mock_now = datetime(2025, 3, 10, 15, 0, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            assert ExitMonitor.is_0dte_blocked() is True

    def test_blocked_after_3pm(self):
        """Should be blocked after 15:00 ET."""
        mock_now = datetime(2025, 3, 10, 15, 30, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            assert ExitMonitor.is_0dte_blocked() is True

    def test_not_blocked_before_3pm(self):
        """Should NOT be blocked before 15:00 ET."""
        mock_now = datetime(2025, 3, 10, 14, 59, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            assert ExitMonitor.is_0dte_blocked() is False


# --- Cache Tests ---


class TestTemplateCache:
    """Tests for template caching in ExitMonitor."""

    def test_clear_template_cache(self, exit_monitor):
        """clear_template_cache() should empty the cache."""
        exit_monitor._template_cache[1] = "some_template"
        exit_monitor._template_cache[2] = "another"

        exit_monitor.clear_template_cache()

        assert exit_monitor._template_cache == {}


# --- Multiple Positions Tests ---


class TestMultiplePositions:
    """Tests for checking exit signals across multiple positions."""

    @pytest.mark.asyncio
    async def test_multiple_positions_different_signals(self, exit_monitor, db):
        """Different positions can trigger different exit signals."""
        # Position 1: profit target hit
        await _create_position(
            db,
            max_profit=150.0,
            unrealized_pnl=80.0,  # > 50% of 150
        )

        # Position 2: loss but within stop
        await _create_position(
            db,
            max_profit=200.0,
            unrealized_pnl=-100.0,  # within 2x stop
        )

        chains = {"SPX": OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            signals = await exit_monitor.check_all_positions(chains)

        # Only position 1 should trigger (profit target)
        assert len(signals) == 1
        assert signals[0].reason == "profit_target"

    @pytest.mark.asyncio
    async def test_no_positions_no_signals(self, exit_monitor):
        """No signals when there are no open positions."""
        chains = {"SPX": OptionsChain(
            ticker="SPX", spot_price=5950.0,
            timestamp=datetime.now(), contracts=[],
        )}

        mock_now = datetime(2025, 3, 10, 10, 30, tzinfo=None)
        with patch("src.paper.exits._now_et", return_value=mock_now):
            signals = await exit_monitor.check_all_positions(chains)

        assert len(signals) == 0
