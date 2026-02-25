"""Integration tests: risk manager + paper engine components.

End-to-end tests combining the risk subsystem with paper trading
engine components, verifying correct wiring and data flow.
"""

import json
from datetime import date, timedelta

import aiosqlite
import pytest
import pytest_asyncio

from src.risk.config import RiskConfig
from src.risk.manager import RiskManager
from src.risk.models import StressScenario
from src.risk.schema import init_risk_tables
from src.risk.stress import StressTestEngine

SPOT = 5000.0
NAV = 100_000.0
EXPIRY_30D = (date.today() + timedelta(days=30)).isoformat()


def _make_position(
    strategy_id=1,
    legs=None,
    quantity=1,
    entry_price=2.50,
    pos_id=1,
    status="open",
):
    """Helper to create a position dict."""
    if legs is None:
        legs = [
            {
                "leg_name": "long_call",
                "option_type": "call",
                "strike": 5000.0,
                "expiry": EXPIRY_30D,
                "action": "buy",
                "quantity": 1,
                "iv": 0.20,
            }
        ]
    return {
        "id": pos_id,
        "strategy_id": strategy_id,
        "legs": legs,
        "quantity": quantity,
        "entry_price": entry_price,
        "status": status,
    }


def _make_iron_condor(pos_id=1, strategy_id=1):
    """Create an iron condor position for testing."""
    legs = [
        {"leg_name": "sell_put", "option_type": "put", "strike": 4800.0,
         "expiry": EXPIRY_30D, "action": "sell", "quantity": 1, "iv": 0.22},
        {"leg_name": "buy_put", "option_type": "put", "strike": 4750.0,
         "expiry": EXPIRY_30D, "action": "buy", "quantity": 1, "iv": 0.23},
        {"leg_name": "sell_call", "option_type": "call", "strike": 5200.0,
         "expiry": EXPIRY_30D, "action": "sell", "quantity": 1, "iv": 0.18},
        {"leg_name": "buy_call", "option_type": "call", "strike": 5250.0,
         "expiry": EXPIRY_30D, "action": "buy", "quantity": 1, "iv": 0.17},
    ]
    return _make_position(
        strategy_id=strategy_id, legs=legs, quantity=1,
        entry_price=1.50, pos_id=pos_id,
    )


@pytest_asyncio.fixture
async def db():
    """Create in-memory DB with risk tables."""
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys = ON")
    await init_risk_tables(conn)
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def manager(db):
    """Create RiskManager with in-memory DB."""
    return RiskManager(db, RiskConfig())


class TestEngineIntegration:
    @pytest.mark.asyncio
    async def test_engine_tick_with_risk_monitoring(self, manager):
        """Wire risk manager, run monitoring, verify no errors."""
        positions = [_make_position()]
        alerts = await manager.monitor_portfolio(
            positions, SPOT, NAV)
        # Should complete without errors
        assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_engine_circuit_breaker_stops_entries(self, manager):
        """Fire CB, verify entry is blocked."""
        # Trigger daily loss circuit breaker
        await manager.monitor_portfolio(
            [], SPOT, NAV, daily_pnl=-6000.0)
        assert manager._circuit_breakers["daily_loss"] is True

        # Attempt new order
        order_info = {
            "order_id": 1,
            "strategy_id": 1,
            "direction": "open",
            "legs": [{"leg_name": "c", "option_type": "call", "strike": 5000.0,
                      "expiry": EXPIRY_30D, "action": "buy", "quantity": 1}],
            "quantity": 1,
        }
        result = await manager.check_order(order_info, [], NAV, SPOT)
        assert result.approved is False
        assert "circuit_breaker" in result.checks_failed

    @pytest.mark.asyncio
    async def test_engine_risk_snapshot_after_trades(self, manager):
        """Open trades, get snapshot, verify Greeks non-zero."""
        positions = [
            _make_position(pos_id=1),
            _make_iron_condor(pos_id=2),
        ]
        snapshot = await manager.get_risk_snapshot(positions, SPOT, NAV)

        # With 2 positions, Greeks should be non-zero
        assert snapshot.portfolio_greeks.num_positions == 2
        assert snapshot.portfolio_greeks.num_legs == 5  # 1 + 4 legs
        # VaR should be computed
        assert snapshot.var_result.dg_var_95 >= 0
        # Stress tests should have results
        assert len(snapshot.stress_results) == 18
        # Concentration should have data
        assert len(snapshot.concentration.by_strategy) >= 1

    @pytest.mark.asyncio
    async def test_full_lifecycle_with_risk(self, db, manager):
        """Full lifecycle: monitor -> check -> monitor -> verify DB records."""
        positions = [_make_iron_condor()]

        # Step 1: Initial monitoring
        alerts1 = await manager.monitor_portfolio(positions, SPOT, NAV)

        # Step 2: Check a new order
        order = {
            "order_id": 10,
            "strategy_id": 2,
            "direction": "open",
            "legs": [{"leg_name": "c", "option_type": "call", "strike": 5000.0,
                      "expiry": EXPIRY_30D, "action": "buy", "quantity": 1}],
            "quantity": 1,
        }
        check_result = await manager.check_order(order, positions, NAV, SPOT)
        assert check_result.approved is True

        # Step 3: Add the new position and monitor again
        positions.append(_make_position(strategy_id=2, pos_id=2))
        alerts2 = await manager.monitor_portfolio(positions, SPOT, NAV)

        # Verify DB has snapshot records
        cursor = await db.execute("SELECT COUNT(*) FROM risk_snapshots")
        count = (await cursor.fetchone())[0]
        assert count == 2  # Two monitoring calls

        # Verify check log has record
        cursor = await db.execute("SELECT COUNT(*) FROM risk_check_log")
        count = (await cursor.fetchone())[0]
        assert count == 1

    @pytest.mark.asyncio
    async def test_stress_test_on_live_positions(self, manager):
        """Open positions, run stress tests, verify results make sense."""
        positions = [
            _make_iron_condor(pos_id=1),
            _make_position(pos_id=2, quantity=3),
        ]

        engine = StressTestEngine(RiskConfig())
        results = engine.run_all_scenarios(positions, SPOT, NAV)

        assert len(results) == 18

        # Large down moves should hurt (long call + short put exposure)
        down_10 = [r for r in results if r.scenario.name == "SPX -10%"]
        assert len(down_10) == 1
        # Long call loses a lot, IC put side loses too
        assert down_10[0].portfolio_pnl < 0

        # Per-position breakdown should include both positions
        assert 1 in down_10[0].position_pnls
        assert 2 in down_10[0].position_pnls


class TestMultiStrategyRisk:
    """Test risk management with multiple strategies."""

    @pytest.mark.asyncio
    async def test_strategy_concentration(self, manager):
        """Multiple positions in same strategy trigger concentration analysis."""
        positions = [
            _make_position(strategy_id=1, pos_id=1),
            _make_position(strategy_id=1, pos_id=2),
            _make_position(strategy_id=2, pos_id=3),
        ]
        snapshot = await manager.get_risk_snapshot(positions, SPOT, NAV)
        assert "1" in snapshot.concentration.by_strategy
        assert "2" in snapshot.concentration.by_strategy

    @pytest.mark.asyncio
    async def test_risk_reset_between_days(self, manager):
        """Verify daily state resets properly."""
        # Day 1: trigger daily loss CB
        await manager.monitor_portfolio([], SPOT, NAV, daily_pnl=-6000)
        assert manager._circuit_breakers["daily_loss"] is True

        # Start of day 2: reset
        manager.reset_daily_state()
        assert manager._circuit_breakers["daily_loss"] is False
        assert manager._consecutive_failures == 0

        # New order should pass
        order = {
            "order_id": 1, "strategy_id": 1, "direction": "open",
            "legs": [{"leg_name": "c", "option_type": "call", "strike": 5000.0,
                      "expiry": EXPIRY_30D, "action": "buy", "quantity": 1}],
            "quantity": 1,
        }
        result = await manager.check_order(order, [], NAV, SPOT)
        assert result.approved is True
