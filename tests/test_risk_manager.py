"""Tests for RiskManager: pre-trade checks, monitoring, circuit breakers.

Uses in-memory SQLite databases and mock positions to verify the full
risk management pipeline.
"""

import json
from datetime import date, datetime, timedelta

import aiosqlite
import pytest
import pytest_asyncio

from src.risk.config import RiskConfig
from src.risk.manager import RiskManager, _regime_name
from src.risk.models import PortfolioGreeks, RiskAlert
from src.risk.schema import init_risk_tables

SPOT = 5000.0
NAV = 100_000.0
def _expiry_30d() -> str:
    """Compute a 30-day future expiry per-call to avoid midnight flakiness."""
    return (date.today() + timedelta(days=30)).isoformat()


def _make_order_info(
    strategy_id=1,
    direction="open",
    legs=None,
    quantity=1,
):
    """Helper to create an order_info dict."""
    if legs is None:
        legs = [
            {
                "leg_name": "long_call",
                "option_type": "call",
                "strike": 5000.0,
                "expiry": _expiry_30d(),
                "action": "buy",
                "quantity": 1,
            }
        ]
    return {
        "order_id": 1,
        "strategy_id": strategy_id,
        "direction": direction,
        "legs": legs,
        "quantity": quantity,
    }


def _make_position(
    strategy_id=1,
    pos_id=1,
    entry_price=2.50,
    quantity=1,
    status="open",
):
    """Helper to create a position dict."""
    return {
        "id": pos_id,
        "strategy_id": strategy_id,
        "legs": [
            {
                "leg_name": "long_call",
                "option_type": "call",
                "strike": 5000.0,
                "expiry": _expiry_30d(),
                "action": "buy",
                "quantity": 1,
                "iv": 0.20,
            }
        ],
        "quantity": quantity,
        "entry_price": entry_price,
        "status": status,
    }


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


# --- Pre-Trade Check Tests ---

class TestCheckOrder:
    @pytest.mark.asyncio
    async def test_check_order_approved_basic(self, manager):
        """Simple order with no limits breached = approved."""
        order = _make_order_info()
        result = await manager.check_order(order, [], NAV, SPOT)
        assert result.approved is True
        assert "circuit_breaker" in result.checks_passed

    @pytest.mark.asyncio
    async def test_check_order_circuit_breaker_blocks(self, manager):
        """Active circuit breaker rejects all orders."""
        manager._circuit_breakers["daily_loss"] = True
        order = _make_order_info()
        result = await manager.check_order(order, [], NAV, SPOT)
        assert result.approved is False
        assert "circuit_breaker" in result.checks_failed

    @pytest.mark.asyncio
    async def test_check_order_crisis_regime_blocks_open(self, manager):
        """Regime=2 blocks opening orders."""
        order = _make_order_info(direction="open")
        result = await manager.check_order(order, [], NAV, SPOT, regime_state=2)
        assert result.approved is False
        assert "regime_close_only" in result.checks_failed

    @pytest.mark.asyncio
    async def test_check_order_crisis_regime_allows_close(self, manager):
        """Regime=2 allows closing orders."""
        order = _make_order_info(direction="close")
        result = await manager.check_order(order, [], NAV, SPOT, regime_state=2)
        assert result.approved is True

    @pytest.mark.asyncio
    async def test_check_order_dte_too_low(self, manager):
        """DTE below min_dte -> rejected."""
        near_expiry = (date.today() + timedelta(days=3)).isoformat()
        legs = [{"leg_name": "c", "option_type": "call", "strike": 5000.0,
                 "expiry": near_expiry, "action": "buy", "quantity": 1}]
        order = _make_order_info(legs=legs)
        result = await manager.check_order(order, [], NAV, SPOT)
        assert result.approved is False
        assert any("DTE" in r and "below" in r for r in result.reasons)

    @pytest.mark.asyncio
    async def test_check_order_dte_too_high(self, manager):
        """DTE above max_dte -> rejected."""
        far_expiry = (date.today() + timedelta(days=90)).isoformat()
        legs = [{"leg_name": "c", "option_type": "call", "strike": 5000.0,
                 "expiry": far_expiry, "action": "buy", "quantity": 1}]
        order = _make_order_info(legs=legs)
        result = await manager.check_order(order, [], NAV, SPOT)
        assert result.approved is False
        assert any("DTE" in r and "above" in r for r in result.reasons)

    @pytest.mark.asyncio
    async def test_check_order_strategy_max_concurrent(self, manager):
        """Too many open positions for strategy -> rejected."""
        positions = [
            _make_position(strategy_id=1, pos_id=i)
            for i in range(3)  # max_concurrent_per_strategy = 3
        ]
        order = _make_order_info(strategy_id=1)
        result = await manager.check_order(order, positions, NAV, SPOT)
        assert result.approved is False
        assert "strategy_limits" in result.checks_failed

    @pytest.mark.asyncio
    async def test_check_order_portfolio_delta_exceeded(self, manager):
        """Portfolio delta above limit -> rejected."""
        # Set cached greeks with high delta
        manager._last_greeks = PortfolioGreeks(delta=600.0)
        order = _make_order_info()
        result = await manager.check_order(order, [], NAV, SPOT)
        assert result.approved is False
        assert any("delta" in r.lower() for r in result.reasons)

    @pytest.mark.asyncio
    async def test_check_order_cash_reserve_low(self, manager):
        """Insufficient cash reserve -> rejected."""
        # Create positions consuming >70% of NAV
        # Use different strategy IDs to avoid strategy limit, and use a new
        # strategy_id for the order to avoid the concurrent limit.
        positions = [
            _make_position(pos_id=i, strategy_id=100 + i, entry_price=100.0, quantity=1)
            for i in range(8)  # 8 * 100 * 1 * 100 = $80,000 = 80% of $100k
        ]
        order = _make_order_info(strategy_id=999)
        result = await manager.check_order(order, positions, NAV, SPOT)
        assert result.approved is False
        assert any("cash reserve" in r.lower() for r in result.reasons)


# --- Monitoring Tests ---

class TestMonitorPortfolio:
    @pytest.mark.asyncio
    async def test_monitor_empty_portfolio(self, manager):
        """No positions = no alerts."""
        alerts = await manager.monitor_portfolio([], SPOT, NAV)
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_monitor_delta_warning(self, manager):
        """Delta at 85% of limit -> warning alert."""
        # Mock compute_greeks to return delta at 85% of max (500 * 0.85 = 425)
        mock_greeks = PortfolioGreeks(
            timestamp="2026-01-01T00:00:00",
            delta=425.0,
            gamma=0.5,
            theta=-10.0,
            vega=50.0,
        )
        manager._analyzer.compute_greeks = lambda positions, spot: mock_greeks

        positions = [_make_position(quantity=5)]
        alerts = await manager.monitor_portfolio(positions, SPOT, NAV)

        delta_alerts = [a for a in alerts if a.category == "delta"]
        assert len(delta_alerts) == 1
        assert delta_alerts[0].level == "warning"
        assert delta_alerts[0].utilization_pct == 85.0

    @pytest.mark.asyncio
    async def test_monitor_delta_breach(self, manager):
        """Delta over 100% of limit -> breach alert."""
        mock_greeks = PortfolioGreeks(
            timestamp="2026-01-01T00:00:00",
            delta=550.0,
            gamma=0.5,
            theta=-10.0,
            vega=50.0,
        )
        manager._analyzer.compute_greeks = lambda positions, spot: mock_greeks

        positions = [_make_position(quantity=5)]
        alerts = await manager.monitor_portfolio(positions, SPOT, NAV)

        delta_alerts = [a for a in alerts if a.category == "delta"]
        assert len(delta_alerts) == 1
        assert delta_alerts[0].level == "breach"

    @pytest.mark.asyncio
    async def test_monitor_delta_under_80pct_no_alert(self, manager):
        """Delta under 80% of limit -> no alert."""
        mock_greeks = PortfolioGreeks(
            timestamp="2026-01-01T00:00:00",
            delta=350.0,
            gamma=0.5,
            theta=-10.0,
            vega=50.0,
        )
        manager._analyzer.compute_greeks = lambda positions, spot: mock_greeks

        positions = [_make_position(quantity=5)]
        alerts = await manager.monitor_portfolio(positions, SPOT, NAV)

        delta_alerts = [a for a in alerts if a.category == "delta"]
        assert len(delta_alerts) == 0

    @pytest.mark.asyncio
    async def test_monitor_daily_loss_circuit_breaker(self, manager):
        """Loss exceeds daily limit -> CB fires."""
        # daily_pnl = -$6,000 with max_daily_loss_pct = 0.05 ($5,000 limit)
        alerts = await manager.monitor_portfolio(
            [], SPOT, NAV, daily_pnl=-6000.0)
        assert manager._circuit_breakers["daily_loss"] is True
        cb_alerts = [a for a in alerts if a.category == "daily_loss"]
        assert len(cb_alerts) > 0

    @pytest.mark.asyncio
    async def test_monitor_drawdown_circuit_breaker(self, manager):
        """Drawdown exceeds max -> CB fires."""
        manager._peak_equity = 100_000.0
        # NAV dropped to 88,000 = -12% drawdown (exceeds 10% limit)
        alerts = await manager.monitor_portfolio(
            [], SPOT, 88_000.0)
        assert manager._circuit_breakers["drawdown"] is True
        dd_alerts = [a for a in alerts if a.category == "drawdown"]
        assert len(dd_alerts) > 0

    @pytest.mark.asyncio
    async def test_monitor_vix_halt(self, manager):
        """VIX > 35 -> CB fires."""
        alerts = await manager.monitor_portfolio(
            [], SPOT, NAV, vix=40.0)
        assert manager._circuit_breakers["vix_halt"] is True
        vix_alerts = [a for a in alerts if a.category == "vix"]
        assert len(vix_alerts) > 0

    @pytest.mark.asyncio
    async def test_monitor_vix_resume(self, manager):
        """VIX drops below 30 -> CB resets."""
        manager._circuit_breakers["vix_halt"] = True
        alerts = await manager.monitor_portfolio(
            [], SPOT, NAV, vix=25.0)
        assert manager._circuit_breakers["vix_halt"] is False

    @pytest.mark.asyncio
    async def test_monitor_anomaly_halt(self, manager):
        """Score > 0.8 -> CB fires."""
        alerts = await manager.monitor_portfolio(
            [], SPOT, NAV, anomaly_score=0.9)
        assert manager._circuit_breakers["anomaly_halt"] is True

    @pytest.mark.asyncio
    async def test_monitor_persists_snapshot(self, db, manager):
        """Verify risk_snapshots row written."""
        await manager.monitor_portfolio([], SPOT, NAV)
        cursor = await db.execute("SELECT COUNT(*) FROM risk_snapshots")
        count = (await cursor.fetchone())[0]
        assert count == 1

    @pytest.mark.asyncio
    async def test_monitor_persists_alerts(self, db, manager):
        """Verify risk_alerts rows written."""
        # Trigger a circuit breaker alert
        await manager.monitor_portfolio([], SPOT, NAV, vix=40.0)
        cursor = await db.execute("SELECT COUNT(*) FROM risk_alerts")
        count = (await cursor.fetchone())[0]
        assert count >= 1


# --- Circuit Breaker Tests ---

class TestCircuitBreakers:
    @pytest.mark.asyncio
    async def test_circuit_breaker_manual_reset(self, manager):
        """reset_circuit_breaker("daily_loss") -> resets."""
        manager._circuit_breakers["daily_loss"] = True
        result = manager.reset_circuit_breaker("daily_loss")
        assert result is True
        assert manager._circuit_breakers["daily_loss"] is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_reset_unknown(self, manager):
        """Resetting unknown breaker returns False."""
        result = manager.reset_circuit_breaker("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_active_circuit_breakers(self, manager):
        """Returns list of active names."""
        manager._circuit_breakers["daily_loss"] = True
        manager._circuit_breakers["vix_halt"] = True
        active = manager.get_active_circuit_breakers()
        assert "daily_loss" in active
        assert "vix_halt" in active
        assert "drawdown" not in active

    @pytest.mark.asyncio
    async def test_reset_daily_state(self, manager):
        """daily_loss CB cleared, counter reset."""
        manager._circuit_breakers["daily_loss"] = True
        manager._consecutive_failures = 5
        manager._daily_realized_pnl = -5000.0
        manager.reset_daily_state()
        assert manager._circuit_breakers["daily_loss"] is False
        assert manager._consecutive_failures == 0
        assert manager._daily_realized_pnl == 0.0


# --- Snapshot Tests ---

class TestRiskSnapshot:
    @pytest.mark.asyncio
    async def test_get_risk_snapshot_complete(self, manager):
        """Returns populated RiskSnapshot with all fields."""
        positions = [_make_position()]
        snapshot = await manager.get_risk_snapshot(
            positions, SPOT, NAV, regime_state=0, anomaly_score=0.1)
        assert snapshot.nav == NAV
        assert snapshot.regime_state == 0
        assert snapshot.regime_name == "risk-on"
        assert snapshot.anomaly_score == 0.1
        assert snapshot.timestamp != ""
        assert len(snapshot.stress_results) > 0

    @pytest.mark.asyncio
    async def test_get_risk_snapshot_utilization(self, manager):
        """Verify risk_utilization percentages."""
        positions = [_make_position()]
        snapshot = await manager.get_risk_snapshot(positions, SPOT, NAV)
        assert "delta" in snapshot.risk_utilization
        assert "gamma" in snapshot.risk_utilization
        assert "vega" in snapshot.risk_utilization


# --- Helper Tests ---

class TestRegimeName:
    def test_regime_names(self):
        assert _regime_name(0) == "risk-on"
        assert _regime_name(1) == "risk-off"
        assert _regime_name(2) == "crisis"
        assert _regime_name(99) == "unknown"
