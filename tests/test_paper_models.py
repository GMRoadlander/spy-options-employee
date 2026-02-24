"""Tests for paper trading data models.

Verifies dataclass construction, default values, and field types
for all paper trading model classes.
"""

from datetime import date, datetime

import pytest

from src.paper.models import (
    ExitSignal,
    LegSpec,
    PaperResults,
    PaperTradingConfig,
    PortfolioSummary,
    SimulatedFill,
    TickResult,
    TradePnL,
)


class TestPaperTradingConfig:
    """Tests for PaperTradingConfig dataclass."""

    def test_defaults(self):
        config = PaperTradingConfig()
        assert config.starting_capital == 100_000.0
        assert config.spx_multiplier == 100.0
        assert config.fee_per_contract == 0.65
        assert config.slippage_pct == 0.10
        assert config.max_order_age_ticks == 5
        assert config.snapshot_time_et == "16:00"

    def test_custom_values(self):
        config = PaperTradingConfig(
            starting_capital=50_000.0,
            slippage_pct=0.15,
            fee_per_contract=0.50,
            max_order_age_ticks=10,
        )
        assert config.starting_capital == 50_000.0
        assert config.slippage_pct == 0.15
        assert config.fee_per_contract == 0.50
        assert config.max_order_age_ticks == 10

    def test_spx_multiplier_fixed(self):
        config = PaperTradingConfig()
        assert config.spx_multiplier == 100.0


class TestLegSpec:
    """Tests for LegSpec dataclass."""

    def test_basic_construction(self):
        leg = LegSpec(
            leg_name="short_put",
            option_type="put",
            strike=5800.0,
            expiry=date(2025, 3, 21),
            action="sell",
            quantity=1,
        )
        assert leg.leg_name == "short_put"
        assert leg.option_type == "put"
        assert leg.strike == 5800.0
        assert leg.expiry == date(2025, 3, 21)
        assert leg.action == "sell"
        assert leg.quantity == 1

    def test_default_quantity(self):
        leg = LegSpec(
            leg_name="long_call",
            option_type="call",
            strike=6000.0,
            expiry=date(2025, 3, 21),
            action="buy",
        )
        assert leg.quantity == 1

    def test_call_and_put(self):
        call = LegSpec("leg1", "call", 6000.0, date(2025, 3, 21), "buy")
        put = LegSpec("leg2", "put", 5800.0, date(2025, 3, 21), "sell")
        assert call.option_type == "call"
        assert put.option_type == "put"

    def test_buy_and_sell(self):
        buy = LegSpec("leg1", "call", 6000.0, date(2025, 3, 21), "buy")
        sell = LegSpec("leg2", "call", 6100.0, date(2025, 3, 21), "sell")
        assert buy.action == "buy"
        assert sell.action == "sell"


class TestSimulatedFill:
    """Tests for SimulatedFill dataclass."""

    def test_basic_construction(self):
        fill = SimulatedFill(
            leg_name="short_put",
            fill_price=3.50,
            bid=3.40,
            ask=3.60,
            mid=3.50,
            slippage=0.02,
            iv=0.18,
            delta=-0.30,
        )
        assert fill.leg_name == "short_put"
        assert fill.fill_price == 3.50
        assert fill.bid == 3.40
        assert fill.ask == 3.60
        assert fill.mid == 3.50
        assert fill.slippage == 0.02
        assert fill.iv == 0.18
        assert fill.delta == -0.30

    def test_default_greeks(self):
        fill = SimulatedFill(
            leg_name="test", fill_price=1.0,
            bid=0.90, ask=1.10, mid=1.0, slippage=0.01,
        )
        assert fill.iv == 0.0
        assert fill.delta == 0.0

    def test_slippage_is_positive(self):
        """Slippage should always be stored as a positive value."""
        fill = SimulatedFill(
            leg_name="test", fill_price=1.05,
            bid=0.90, ask=1.10, mid=1.0, slippage=0.05,
        )
        assert fill.slippage >= 0


class TestTickResult:
    """Tests for TickResult dataclass."""

    def test_defaults(self):
        now = datetime.now()
        result = TickResult(timestamp=now)
        assert result.timestamp == now
        assert result.orders_submitted == 0
        assert result.orders_filled == 0
        assert result.orders_cancelled == 0
        assert result.positions_opened == 0
        assert result.positions_closed == 0
        assert result.exit_signals == []
        assert result.total_unrealized_pnl == 0.0
        assert result.errors == []

    def test_custom_values(self):
        now = datetime.now()
        result = TickResult(
            timestamp=now,
            orders_submitted=3,
            orders_filled=2,
            orders_cancelled=1,
            positions_opened=2,
            positions_closed=1,
            exit_signals=["profit_target"],
            total_unrealized_pnl=500.0,
            errors=["test error"],
        )
        assert result.orders_submitted == 3
        assert result.orders_filled == 2
        assert result.positions_closed == 1
        assert len(result.exit_signals) == 1
        assert result.total_unrealized_pnl == 500.0

    def test_lists_are_independent(self):
        """Verify mutable default lists are independent between instances."""
        r1 = TickResult(timestamp=datetime.now())
        r2 = TickResult(timestamp=datetime.now())
        r1.errors.append("error1")
        assert len(r2.errors) == 0


class TestPortfolioSummary:
    """Tests for PortfolioSummary dataclass."""

    def test_defaults(self):
        summary = PortfolioSummary()
        assert summary.starting_capital == 0.0
        assert summary.total_equity == 0.0
        assert summary.realized_pnl == 0.0
        assert summary.unrealized_pnl == 0.0
        assert summary.open_positions == 0
        assert summary.total_trades == 0
        assert summary.win_rate == 0.0
        assert summary.sharpe_ratio == 0.0
        assert summary.max_drawdown == 0.0
        assert summary.daily_pnl == 0.0
        assert summary.strategies_active == []

    def test_strategies_list_independent(self):
        s1 = PortfolioSummary()
        s2 = PortfolioSummary()
        s1.strategies_active.append("IC Strategy")
        assert len(s2.strategies_active) == 0


class TestPaperResults:
    """Tests for PaperResults dataclass."""

    def test_defaults(self):
        results = PaperResults()
        assert results.strategy_id == 0
        assert results.strategy_name == ""
        assert results.trades == []
        assert results.metrics is None
        assert results.equity_curve == []
        assert results.days_in_paper == 0
        assert results.recommendation == "CONTINUE"

    def test_custom_values(self):
        results = PaperResults(
            strategy_id=42,
            strategy_name="Iron Condor Weekly",
            trades=[{"id": 1, "pnl": 100}],
            days_in_paper=30,
            recommendation="PROMOTE",
        )
        assert results.strategy_id == 42
        assert results.strategy_name == "Iron Condor Weekly"
        assert len(results.trades) == 1
        assert results.recommendation == "PROMOTE"


class TestTradePnL:
    """Tests for TradePnL dataclass."""

    def test_defaults(self):
        pnl = TradePnL()
        assert pnl.entry_credit_debit == 0.0
        assert pnl.exit_credit_debit == 0.0
        assert pnl.raw_pnl == 0.0
        assert pnl.total_pnl == 0.0
        assert pnl.fees == 0.0
        assert pnl.slippage_cost == 0.0
        assert pnl.net_pnl == 0.0

    def test_credit_spread_pnl(self):
        """Simulate a winning credit spread."""
        pnl = TradePnL(
            entry_credit_debit=2.50,   # received $2.50 credit
            exit_credit_debit=-1.00,   # paid $1.00 to close
            raw_pnl=1.50,             # $1.50 per unit
            total_pnl=150.0,          # * 100 multiplier * 1 contract
            fees=2.60,               # 0.65 * 2 legs * 2 (open+close)
            slippage_cost=5.0,
            net_pnl=147.40,          # 150 - 2.60
        )
        assert pnl.net_pnl == 147.40
        assert pnl.total_pnl > 0

    def test_debit_spread_loss(self):
        """Simulate a losing debit spread."""
        pnl = TradePnL(
            entry_credit_debit=-3.00,
            exit_credit_debit=1.00,
            raw_pnl=-2.00,
            total_pnl=-200.0,
            fees=2.60,
            slippage_cost=4.0,
            net_pnl=-202.60,
        )
        assert pnl.net_pnl < 0
        assert pnl.raw_pnl < 0


class TestExitSignal:
    """Tests for ExitSignal dataclass."""

    def test_defaults(self):
        signal = ExitSignal()
        assert signal.position_id == 0
        assert signal.reason == ""
        assert signal.urgency == "normal"

    def test_profit_target(self):
        signal = ExitSignal(
            position_id=42,
            reason="profit_target",
            urgency="normal",
        )
        assert signal.position_id == 42
        assert signal.reason == "profit_target"
        assert signal.urgency == "normal"

    def test_expiration_urgent(self):
        signal = ExitSignal(
            position_id=99,
            reason="expiration",
            urgency="immediate",
        )
        assert signal.urgency == "immediate"

    def test_various_reasons(self):
        reasons = ["profit_target", "stop_loss", "dte_exit",
                    "time_stop", "expiration", "manual"]
        for reason in reasons:
            signal = ExitSignal(position_id=1, reason=reason)
            assert signal.reason == reason
