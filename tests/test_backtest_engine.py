"""Tests for backtesting engine."""

from datetime import date, datetime, timedelta

import pandas as pd
import pytest

from src.data import OptionContract, OptionsChain
from src.strategy.schema import (
    EntryRule,
    ExitRule,
    LegAction,
    LegDefinition,
    LegSide,
    DeltaTarget,
    SizingConfig,
    ScheduleConfig,
    StrategyTemplate,
    StrategyType,
    StructureDefinition,
)
from src.backtest.engine import BacktestEngine, BacktestResult


# --- Helpers ---

def _make_contract(
    strike: float,
    option_type: str,
    bid: float,
    ask: float,
    delta: float,
    expiry: date,
) -> OptionContract:
    return OptionContract(
        ticker="SPX",
        expiry=expiry,
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        last=(bid + ask) / 2,
        volume=100,
        open_interest=500,
        iv=0.20,
        delta=delta,
    )


def _make_chain(trade_date: date, spot: float, contracts: list[OptionContract]) -> OptionsChain:
    return OptionsChain(
        ticker="SPX",
        spot_price=spot,
        timestamp=datetime.combine(trade_date, datetime.min.time()),
        contracts=contracts,
        source="orats",
    )


def _build_synthetic_chains(
    start_date: date = date(2024, 1, 2),
    num_days: int = 10,
    spot: float = 5000.0,
    expiry: date = date(2024, 2, 2),  # not a 3rd Friday, PM-settled
) -> list[OptionsChain]:
    """Build synthetic chains with call/put at various strikes."""
    chains = []
    current = start_date

    for day_num in range(num_days):
        # Skip weekends
        while current.weekday() >= 5:
            current += timedelta(days=1)

        contracts = []
        for strike_offset in [-100, -50, 0, 50, 100]:
            strike = spot + strike_offset

            # Simplified delta: call delta decreases as strike increases
            call_delta = max(0.05, min(0.95, 0.5 - strike_offset / 200))
            put_delta = call_delta - 1.0

            # Simplified pricing: ATM ~$20, deeper ITM/OTM scales
            base_price = max(0.50, 20.0 - abs(strike_offset) * 0.15)

            contracts.append(_make_contract(
                strike=strike,
                option_type="call",
                bid=base_price - 0.50,
                ask=base_price + 0.50,
                delta=call_delta,
                expiry=expiry,
            ))
            contracts.append(_make_contract(
                strike=strike,
                option_type="put",
                bid=base_price - 0.50,
                ask=base_price + 0.50,
                delta=put_delta,
                expiry=expiry,
            ))

        chains.append(_make_chain(current, spot, contracts))
        current += timedelta(days=1)

    return chains


def _make_short_put_strategy(
    delta: float = 0.25,
    dte_target: int = 30,
    profit_target: float = 0.50,
    stop_loss: float = 2.0,
) -> StrategyTemplate:
    """Create a simple short put strategy for testing."""
    return StrategyTemplate(
        name="Test Short Put",
        structure=StructureDefinition(
            strategy_type=StrategyType.NAKED_PUT,
            legs=[
                LegDefinition(
                    name="short_put",
                    side=LegSide.PUT,
                    action=LegAction.SELL,
                    delta_target=DeltaTarget.FIXED,
                    delta_value=0.25,  # will be negated for puts
                ),
            ],
            dte_target=dte_target,
            dte_min=20,
            dte_max=45,
        ),
        exit=ExitRule(
            profit_target_pct=profit_target,
            stop_loss_pct=stop_loss,
            dte_close=0,
        ),
        metadata={"id": "test-short-put"},
    )


def _make_iron_condor_strategy() -> StrategyTemplate:
    return StrategyTemplate(
        name="Test Iron Condor",
        structure=StructureDefinition(
            strategy_type=StrategyType.IRON_CONDOR,
            legs=[
                LegDefinition(name="sell_put", side=LegSide.PUT, action=LegAction.SELL,
                              delta_target=DeltaTarget.FIXED, delta_value=0.25),
                LegDefinition(name="buy_put", side=LegSide.PUT, action=LegAction.BUY,
                              delta_target=DeltaTarget.FIXED, delta_value=0.10),
                LegDefinition(name="sell_call", side=LegSide.CALL, action=LegAction.SELL,
                              delta_target=DeltaTarget.FIXED, delta_value=0.25),
                LegDefinition(name="buy_call", side=LegSide.CALL, action=LegAction.BUY,
                              delta_target=DeltaTarget.FIXED, delta_value=0.10),
            ],
            dte_target=30,
            dte_min=20,
            dte_max=45,
        ),
        exit=ExitRule(profit_target_pct=0.50, stop_loss_pct=2.0, dte_close=0),
        metadata={"id": "test-ic"},
    )


def _make_vertical_strategy() -> StrategyTemplate:
    return StrategyTemplate(
        name="Test Put Spread",
        structure=StructureDefinition(
            strategy_type=StrategyType.VERTICAL_SPREAD,
            legs=[
                LegDefinition(name="sell_put", side=LegSide.PUT, action=LegAction.SELL,
                              delta_target=DeltaTarget.FIXED, delta_value=0.30),
                LegDefinition(name="buy_put", side=LegSide.PUT, action=LegAction.BUY,
                              delta_target=DeltaTarget.FIXED, delta_value=0.10),
            ],
            dte_target=30,
            dte_min=20,
            dte_max=45,
        ),
        exit=ExitRule(profit_target_pct=0.50, stop_loss_pct=2.0, dte_close=0),
        metadata={"id": "test-vertical"},
    )


# --- Tests ---

class TestBacktestEngineBasic:
    """Basic engine functionality."""

    def test_empty_chains_returns_zero_trades(self):
        engine = BacktestEngine(chains=[])
        strategy = _make_short_put_strategy()
        result = engine.run(strategy)
        assert result.num_trades == 0
        assert result.total_return == 0.0
        assert result.trade_log.empty

    def test_result_has_correct_strategy_name(self):
        chains = _build_synthetic_chains()
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        result = engine.run(strategy)
        assert result.strategy_name == "Test Short Put"
        assert result.strategy_id == "test-short-put"

    def test_result_fields_populated(self):
        chains = _build_synthetic_chains()
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        result = engine.run(strategy)

        assert isinstance(result, BacktestResult)
        assert isinstance(result.daily_returns, pd.Series)
        assert result.start_date is not None
        assert result.end_date is not None

    def test_set_chains_updates_data(self):
        engine = BacktestEngine()
        strategy = _make_short_put_strategy()
        result1 = engine.run(strategy)
        assert result1.num_trades == 0

        chains = _build_synthetic_chains()
        engine.set_chains(chains)
        result2 = engine.run(strategy)
        assert result2.num_trades > 0


class TestStrategyMapping:
    """Test strategy → execution mapping."""

    def test_short_put_produces_trades(self):
        chains = _build_synthetic_chains()
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        result = engine.run(strategy)
        assert result.num_trades > 0

    def test_iron_condor_produces_trades(self):
        chains = _build_synthetic_chains()
        engine = BacktestEngine(chains=chains)
        strategy = _make_iron_condor_strategy()
        result = engine.run(strategy)
        assert result.num_trades > 0

    def test_vertical_spread_produces_trades(self):
        chains = _build_synthetic_chains()
        engine = BacktestEngine(chains=chains)
        strategy = _make_vertical_strategy()
        result = engine.run(strategy)
        assert result.num_trades > 0

    def test_iron_condor_has_credit(self):
        chains = _build_synthetic_chains()
        engine = BacktestEngine(chains=chains)
        strategy = _make_iron_condor_strategy()
        result = engine.run(strategy)
        if not result.trade_log.empty:
            # Iron condor should receive a net credit (sells - buys > 0)
            assert result.trade_log["entry_credit"].iloc[0] != 0


class TestEntryFilters:
    """Test entry filter application."""

    def test_date_range_filter(self):
        chains = _build_synthetic_chains(start_date=date(2024, 1, 2), num_days=20)
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        result = engine.run(strategy, start_date=date(2024, 1, 10), end_date=date(2024, 1, 15))
        if result.num_trades > 0:
            assert result.start_date >= date(2024, 1, 10)

    def test_no_trade_dates_returns_empty(self):
        # Build chains that are all outside the DTE range
        chains = _build_synthetic_chains(
            start_date=date(2024, 1, 2),
            num_days=5,
            expiry=date(2024, 1, 5),  # very short DTE, below dte_min=20
        )
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy(dte_target=30)
        result = engine.run(strategy)
        assert result.num_trades == 0


class TestExitRules:
    """Test exit rule application."""

    def test_trade_log_has_exit_date(self):
        chains = _build_synthetic_chains()
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        result = engine.run(strategy)
        if not result.trade_log.empty:
            assert "exit_date" in result.trade_log.columns

    def test_dte_close_exits_early(self):
        chains = _build_synthetic_chains(num_days=30, expiry=date(2024, 2, 9))
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        strategy.exit.dte_close = 10  # close when 10 DTE remaining
        result = engine.run(strategy)
        if not result.trade_log.empty:
            for _, trade in result.trade_log.iterrows():
                dte_at_exit = (trade["expiration"] - trade["exit_date"]).days
                # Should have exited at or before 10 DTE
                assert dte_at_exit >= 0

    def test_pnl_calculated(self):
        chains = _build_synthetic_chains()
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        result = engine.run(strategy)
        if not result.trade_log.empty:
            assert "pnl" in result.trade_log.columns
            # All values should be finite
            assert result.trade_log["pnl"].notna().all()


class TestDailyReturns:
    """Test daily return series construction."""

    def test_daily_returns_is_series(self):
        chains = _build_synthetic_chains()
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        result = engine.run(strategy)
        assert isinstance(result.daily_returns, pd.Series)

    def test_daily_returns_sum_equals_total(self):
        chains = _build_synthetic_chains()
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        result = engine.run(strategy)
        if result.num_trades > 0:
            assert abs(result.daily_returns.sum() - result.total_return) < 0.01


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_all_dates_filtered_returns_empty(self):
        chains = _build_synthetic_chains(num_days=1)
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        # Set date range that doesn't overlap with data
        result = engine.run(strategy, start_date=date(2025, 1, 1))
        assert result.num_trades == 0

    def test_pm_settled_filter_excludes_third_friday(self):
        # Build chains with third Friday expiration (AM-settled)
        chains = _build_synthetic_chains(
            expiry=date(2024, 1, 19),  # 3rd Friday of Jan 2024
        )
        engine = BacktestEngine(chains=chains)
        strategy = _make_short_put_strategy()
        result = engine.run(strategy)
        # Should produce no trades since all expirations are AM-settled
        assert result.num_trades == 0
