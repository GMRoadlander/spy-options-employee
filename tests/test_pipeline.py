"""Tests for anti-overfitting evaluation pipeline."""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
import pytest_asyncio
import aiosqlite

from src.data import OptionContract, OptionsChain
from src.strategy.schema import (
    DeltaTarget,
    ExitRule,
    LegAction,
    LegDefinition,
    LegSide,
    StrategyTemplate,
    StrategyType,
    StructureDefinition,
)
from src.backtest.engine import BacktestEngine, BacktestResult
from src.backtest.metrics import StrategyMetrics
from src.backtest.pipeline import (
    EvaluationPipeline,
    PipelineResult,
    BACKTEST_RESULTS_DDL,
    BACKTEST_RESULTS_INDEX,
)


# --- Helpers ---

def _make_contract(strike, option_type, bid, ask, delta, expiry):
    return OptionContract(
        ticker="SPX", expiry=expiry, strike=strike, option_type=option_type,
        bid=bid, ask=ask, last=(bid + ask) / 2, volume=100, open_interest=500,
        iv=0.20, delta=delta,
    )


def _make_chain(trade_date, spot, contracts):
    return OptionsChain(
        ticker="SPX", spot_price=spot,
        timestamp=datetime.combine(trade_date, datetime.min.time()),
        contracts=contracts, source="orats",
    )


def _build_chains(start_date=date(2024, 1, 2), num_days=60, spot=5000.0,
                   expiry=date(2024, 3, 8)):
    """Build synthetic chains with enough data for pipeline."""
    chains = []
    current = start_date
    for _ in range(num_days):
        while current.weekday() >= 5:
            current += timedelta(days=1)
        contracts = []
        for offset in [-100, -50, 0, 50, 100]:
            strike = spot + offset
            call_delta = max(0.05, min(0.95, 0.5 - offset / 200))
            price = max(0.50, 20.0 - abs(offset) * 0.15)
            contracts.append(_make_contract(strike, "call", price - 0.5, price + 0.5, call_delta, expiry))
            contracts.append(_make_contract(strike, "put", price - 0.5, price + 0.5, call_delta - 1.0, expiry))
        chains.append(_make_chain(current, spot, contracts))
        current += timedelta(days=1)
    return chains


def _make_strategy():
    return StrategyTemplate(
        name="Test Short Put",
        structure=StructureDefinition(
            strategy_type=StrategyType.NAKED_PUT,
            legs=[LegDefinition(name="sp", side=LegSide.PUT, action=LegAction.SELL,
                                delta_target=DeltaTarget.FIXED, delta_value=0.25)],
            dte_target=30, dte_min=20, dte_max=65,
        ),
        exit=ExitRule(profit_target_pct=0.50, stop_loss_pct=2.0, dte_close=0),
        metadata={"id": "test-sp"},
    )


def _make_pipeline_result(
    passed_gates: dict[str, bool] | None = None,
) -> PipelineResult:
    """Create a PipelineResult with controlled gate pass/fail."""
    from src.backtest.wfa import WFAResult
    from src.backtest.cpcv import CPCVResult
    from src.backtest.dsr import DSRResult
    from src.backtest.monte_carlo import MonteCarloResult

    gates = passed_gates or {"WFA": True, "CPCV": True, "DSR": True, "MC": True}

    wfa = WFAResult(strategy_name="test", num_windows=4,
                    is_periods=[], oos_periods=[],
                    is_sharpes=[1.0], oos_sharpes=[0.8],
                    degradation=0.8, oos_sharpe_mean=0.8,
                    oos_sharpe_std=0.1, passed=gates.get("WFA", True))

    cpcv = CPCVResult(strategy_name="test", n_folds=10, n_test_folds=2,
                      n_paths=45, purge_size=45, embargo_size=5,
                      sharpe_distribution=[0.5] * 45, sharpe_mean=0.5,
                      sharpe_std=0.1, sharpe_5th_pct=0.3,
                      pbo=0.2, passed=gates.get("CPCV", True))

    dsr = DSRResult(strategy_name="test", estimated_sharpe=1.5,
                    expected_max_sharpe=1.0, dsr=0.97,
                    n_trials=1, backtest_horizon=252,
                    skewness=0.0, kurtosis=3.0,
                    passed=gates.get("DSR", True))

    mc = MonteCarloResult(strategy_name="test", n_simulations=1000,
                          sharpe_distribution=[0.5] * 1000, sharpe_mean=0.5,
                          sharpe_std=0.1, sharpe_5th_pct=0.2,
                          max_drawdown_95th_pct=-5.0,
                          final_return_5th_pct=100.0,
                          passed=gates.get("MC", True))

    metrics = StrategyMetrics(num_trades=50, sharpe_ratio=1.5, win_rate=0.65)

    daily = pd.Series([0.01] * 252, index=pd.bdate_range("2024-01-02", periods=252))
    bt = BacktestResult(
        strategy_name="test", strategy_id="test-1",
        start_date=date(2024, 1, 2), end_date=date(2024, 12, 31),
        num_trades=50, total_return=100.0,
        daily_returns=daily, trade_log=pd.DataFrame({"pnl": [2.0] * 50}),
        raw_data=pd.DataFrame(),
    )

    failed = []
    for name, key in [("WFA", "WFA"), ("CPCV", "CPCV"), ("DSR", "DSR"), ("Monte Carlo", "MC")]:
        if not gates.get(key, True):
            failed.append(name)

    passed_count = sum(1 for v in gates.values() if v)
    if passed_count == 4:
        rec = "PROMOTE"
    elif passed_count == 3:
        rec = "REFINE"
    else:
        rec = "REJECT"

    return PipelineResult(
        strategy_name="test", strategy_id="test-1",
        timestamp=datetime.now(),
        wfa=wfa, cpcv=cpcv, dsr=dsr, monte_carlo=mc,
        all_gates_passed=passed_count == 4,
        failed_gates=failed,
        recommendation=rec,
        metrics=metrics, backtest=bt,
    )


# --- Tests ---

class TestPipelineRecommendation:
    """Test recommendation logic."""

    def test_all_pass_promote(self):
        result = _make_pipeline_result({"WFA": True, "CPCV": True, "DSR": True, "MC": True})
        assert result.recommendation == "PROMOTE"
        assert result.all_gates_passed is True
        assert result.failed_gates == []

    def test_three_pass_refine(self):
        result = _make_pipeline_result({"WFA": True, "CPCV": True, "DSR": True, "MC": False})
        assert result.recommendation == "REFINE"
        assert result.all_gates_passed is False
        assert "Monte Carlo" in result.failed_gates

    def test_two_pass_reject(self):
        result = _make_pipeline_result({"WFA": True, "CPCV": True, "DSR": False, "MC": False})
        assert result.recommendation == "REJECT"

    def test_zero_pass_reject(self):
        result = _make_pipeline_result({"WFA": False, "CPCV": False, "DSR": False, "MC": False})
        assert result.recommendation == "REJECT"
        assert len(result.failed_gates) == 4


class TestPipelineExecution:
    """Test pipeline execution with real engine."""

    def test_pipeline_runs_end_to_end(self):
        chains = _build_chains()
        engine = BacktestEngine(chains=chains)
        pipeline = EvaluationPipeline(engine)
        strategy = _make_strategy()

        result = pipeline.evaluate(strategy)

        assert isinstance(result, PipelineResult)
        assert result.strategy_name == "Test Short Put"
        assert result.recommendation in ("PROMOTE", "REFINE", "REJECT")
        assert isinstance(result.metrics, StrategyMetrics)
        assert isinstance(result.backtest, BacktestResult)

    def test_pipeline_with_no_trades(self):
        engine = BacktestEngine(chains=[])
        pipeline = EvaluationPipeline(engine)
        strategy = _make_strategy()

        result = pipeline.evaluate(strategy)

        assert result.recommendation == "REJECT"
        assert result.backtest.num_trades == 0


class TestPipelinePersistence:
    """Test database persistence."""

    @pytest.mark.asyncio
    async def test_save_result(self):
        db = await aiosqlite.connect(":memory:")
        await db.execute(BACKTEST_RESULTS_DDL)
        await db.execute(BACKTEST_RESULTS_INDEX)
        await db.commit()

        engine = BacktestEngine(chains=[])
        pipeline = EvaluationPipeline(engine, db=db)

        result = _make_pipeline_result()
        row_id = await pipeline.save_result(result)

        assert row_id is not None
        assert row_id > 0

        # Verify data was saved
        cursor = await db.execute("SELECT recommendation FROM backtest_results WHERE id = ?", (row_id,))
        row = await cursor.fetchone()
        assert row[0] == "PROMOTE"

        await db.close()

    @pytest.mark.asyncio
    async def test_save_without_db_returns_none(self):
        engine = BacktestEngine(chains=[])
        pipeline = EvaluationPipeline(engine, db=None)

        result = _make_pipeline_result()
        row_id = await pipeline.save_result(result)
        assert row_id is None

    @pytest.mark.asyncio
    async def test_init_tables(self):
        db = await aiosqlite.connect(":memory:")
        engine = BacktestEngine(chains=[])
        pipeline = EvaluationPipeline(engine, db=db)

        await pipeline.init_tables()

        # Table should exist
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='backtest_results'"
        )
        row = await cursor.fetchone()
        assert row is not None

        await db.close()
