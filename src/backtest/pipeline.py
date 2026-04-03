"""Anti-overfitting evaluation pipeline orchestrator.

Runs all four validation gates in sequence:
1. Walk-Forward Analysis (WFA)
2. Combinatorial Purged Cross-Validation (CPCV)
3. Deflated Sharpe Ratio (DSR)
4. Monte Carlo Simulation

Gates strategy promotion based on results:
- All 4 pass → PROMOTE (can go to PAPER)
- 3/4 pass → REFINE (adjust and re-test)
- ≤2/4 pass → REJECT

Results are persisted to SQLite for audit trail.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, datetime

import aiosqlite
import numpy as np
import pandas as pd

from src.backtest.cpcv import CPCVAnalyzer, CPCVResult
from src.backtest.dsr import DSRResult, evaluate_dsr
from src.backtest.engine import BacktestEngine, BacktestResult
from src.backtest.metrics import StrategyMetrics, calculate_metrics
from src.backtest.monte_carlo import MonteCarloResult, MonteCarloSimulator
from src.backtest.wfa import WFAResult, WalkForwardAnalyzer
from src.strategy.schema import StrategyTemplate
from src.utils import now_et

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete evaluation pipeline result."""

    strategy_name: str
    strategy_id: str
    timestamp: datetime

    wfa: WFAResult
    cpcv: CPCVResult
    dsr: DSRResult
    monte_carlo: MonteCarloResult

    all_gates_passed: bool
    failed_gates: list[str]
    recommendation: str  # "PROMOTE", "REFINE", or "REJECT"

    metrics: StrategyMetrics
    backtest: BacktestResult


BACKTEST_RESULTS_DDL = """
CREATE TABLE IF NOT EXISTS backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id TEXT NOT NULL,
    run_at TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    num_trades INTEGER,
    sharpe REAL,
    sortino REAL,
    max_drawdown REAL,
    win_rate REAL,
    profit_factor REAL,
    wfa_passed INTEGER,
    cpcv_pbo REAL,
    cpcv_passed INTEGER,
    dsr REAL,
    dsr_passed INTEGER,
    mc_5th_sharpe REAL,
    mc_passed INTEGER,
    all_passed INTEGER,
    recommendation TEXT,
    full_result TEXT
)
"""

BACKTEST_RESULTS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_backtest_strategy
ON backtest_results(strategy_id, run_at)
"""


class EvaluationPipeline:
    """Orchestrates the full anti-overfitting evaluation pipeline.

    Args:
        engine: BacktestEngine with historical data loaded.
        db: Optional aiosqlite connection for persisting results.
    """

    def __init__(
        self,
        engine: BacktestEngine,
        db: aiosqlite.Connection | None = None,
    ) -> None:
        self._engine = engine
        self._db = db

    async def init_tables(self) -> None:
        """Create backtest_results table if DB is configured."""
        if self._db is not None:
            await self._db.execute(BACKTEST_RESULTS_DDL)
            await self._db.execute(BACKTEST_RESULTS_INDEX)
            await self._db.commit()

    def evaluate(
        self,
        strategy: StrategyTemplate,
        start_date: date | None = None,
        end_date: date | None = None,
        all_sharpes: list[float] | None = None,
    ) -> PipelineResult:
        """Run full anti-overfitting evaluation pipeline.

        1. Run backtest → BacktestResult
        2. Calculate metrics → StrategyMetrics
        3. Run WFA (12mo IS / 3mo OOS)
        4. Run CPCV (PBO < 0.50)
        5. Run DSR (> 0.95)
        6. Run Monte Carlo (1000 runs, 5th-pct Sharpe > 0)
        7. Determine recommendation

        Args:
            strategy: Strategy template to evaluate.
            start_date: Optional backtest start date.
            end_date: Optional backtest end date.
            all_sharpes: Sharpe ratios of all tested variants (for DSR).

        Returns:
            PipelineResult with all gate results and recommendation.
        """
        # Step 1: Run backtest
        bt_result = self._engine.run(strategy, start_date, end_date)

        # Step 2: Calculate metrics
        metrics = calculate_metrics(bt_result)

        # Step 3: WFA
        wfa = self._run_wfa(bt_result, metrics)

        # Step 4: CPCV
        cpcv = self._run_cpcv(bt_result)

        # Step 5: DSR
        dsr = self._run_dsr(metrics, bt_result, all_sharpes)

        # Step 6: Monte Carlo
        mc = self._run_monte_carlo(bt_result)

        # Step 7: Determine recommendation
        gates = {
            "WFA": wfa.passed,
            "CPCV": cpcv.passed,
            "DSR": dsr.passed,
            "Monte Carlo": mc.passed,
        }

        failed = [name for name, passed in gates.items() if not passed]
        passed_count = sum(1 for p in gates.values() if p)

        if passed_count == 4:
            recommendation = "PROMOTE"
        elif passed_count == 3:
            recommendation = "REFINE"
        else:
            recommendation = "REJECT"

        return PipelineResult(
            strategy_name=strategy.name,
            strategy_id=strategy.metadata.get("id", ""),
            timestamp=now_et(),
            wfa=wfa,
            cpcv=cpcv,
            dsr=dsr,
            monte_carlo=mc,
            all_gates_passed=passed_count == 4,
            failed_gates=failed,
            recommendation=recommendation,
            metrics=metrics,
            backtest=bt_result,
        )

    def _run_wfa(self, bt_result: BacktestResult, metrics: StrategyMetrics) -> WFAResult:
        """Run Walk-Forward Analysis."""
        analyzer = WalkForwardAnalyzer(is_months=12, oos_months=3, step_months=3)

        # Generate windows
        windows = analyzer.generate_windows(bt_result.start_date, bt_result.end_date)

        if not windows:
            return analyzer.evaluate([], [], strategy_name=bt_result.strategy_name)

        # For simplified WFA: use overall Sharpe as IS proxy,
        # split daily returns by time windows
        daily = bt_result.daily_returns
        is_sharpes = []
        oos_sharpes = []

        for is_start, is_end, oos_start, oos_end in windows:
            is_returns = daily[
                (daily.index >= pd.Timestamp(is_start)) &
                (daily.index <= pd.Timestamp(is_end))
            ]
            oos_returns = daily[
                (daily.index >= pd.Timestamp(oos_start)) &
                (daily.index <= pd.Timestamp(oos_end))
            ]

            is_sharpe = self._sharpe_from_series(is_returns)
            oos_sharpe = self._sharpe_from_series(oos_returns)
            is_sharpes.append(is_sharpe)
            oos_sharpes.append(oos_sharpe)

        return analyzer.evaluate(is_sharpes, oos_sharpes, bt_result.strategy_name)

    def _run_cpcv(self, bt_result: BacktestResult) -> CPCVResult:
        """Run CPCV analysis."""
        max_dte = 45  # default purge based on typical strategy DTE
        analyzer = CPCVAnalyzer(
            n_folds=10,
            n_test_folds=2,
            purge_days=max_dte,
            embargo_days=5,
        )
        daily = bt_result.daily_returns
        if len(daily) == 0:
            return analyzer.run([], strategy_name=bt_result.strategy_name)
        return analyzer.run(daily.values, strategy_name=bt_result.strategy_name)

    def _run_dsr(
        self,
        metrics: StrategyMetrics,
        bt_result: BacktestResult,
        all_sharpes: list[float] | None,
    ) -> DSRResult:
        """Run DSR analysis."""
        if all_sharpes is None:
            all_sharpes = [metrics.sharpe_ratio]

        horizon = len(bt_result.daily_returns) if len(bt_result.daily_returns) > 0 else 1

        return evaluate_dsr(
            strategy_sharpe=metrics.sharpe_ratio,
            all_sharpes=all_sharpes,
            backtest_horizon=horizon,
            skew=metrics.skewness,
            kurtosis=metrics.kurtosis + 3.0,  # convert excess → raw
            strategy_name=bt_result.strategy_name,
        )

    def _run_monte_carlo(self, bt_result: BacktestResult) -> MonteCarloResult:
        """Run Monte Carlo simulation."""
        sim = MonteCarloSimulator(n_simulations=1000, seed=None)

        if bt_result.trade_log.empty or "pnl" not in bt_result.trade_log.columns:
            return sim.run([], strategy_name=bt_result.strategy_name)

        trade_returns = bt_result.trade_log["pnl"]
        return sim.run(trade_returns, strategy_name=bt_result.strategy_name)

    @staticmethod
    def _sharpe_from_series(returns: pd.Series) -> float:
        """Calculate annualized Sharpe from a returns series."""
        if len(returns) < 2:
            return 0.0
        std = returns.std()
        if std == 0 or np.isnan(std):
            return 0.0
        return float((returns.mean() / std) * np.sqrt(252))

    async def save_result(self, result: PipelineResult) -> int | None:
        """Persist evaluation results to database.

        Args:
            result: Pipeline result to save.

        Returns:
            Row ID of saved result, or None if no DB configured.
        """
        if self._db is None:
            return None

        # Serialize full result to JSON
        full_json = json.dumps({
            "strategy_name": result.strategy_name,
            "strategy_id": result.strategy_id,
            "recommendation": result.recommendation,
            "failed_gates": result.failed_gates,
            "wfa_passed": result.wfa.passed,
            "cpcv_pbo": result.cpcv.pbo,
            "cpcv_passed": result.cpcv.passed,
            "dsr": result.dsr.dsr,
            "dsr_passed": result.dsr.passed,
            "mc_5th_sharpe": result.monte_carlo.sharpe_5th_pct,
            "mc_passed": result.monte_carlo.passed,
            "sharpe": result.metrics.sharpe_ratio,
            "sortino": result.metrics.sortino_ratio,
            "win_rate": result.metrics.win_rate,
            "profit_factor": result.metrics.profit_factor,
        })

        cursor = await self._db.execute(
            """
            INSERT INTO backtest_results (
                strategy_id, run_at, start_date, end_date, num_trades,
                sharpe, sortino, max_drawdown, win_rate, profit_factor,
                wfa_passed, cpcv_pbo, cpcv_passed, dsr, dsr_passed,
                mc_5th_sharpe, mc_passed, all_passed, recommendation, full_result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.strategy_id,
                result.timestamp.isoformat(),
                result.backtest.start_date.isoformat(),
                result.backtest.end_date.isoformat(),
                result.backtest.num_trades,
                result.metrics.sharpe_ratio,
                result.metrics.sortino_ratio,
                result.metrics.max_drawdown,
                result.metrics.win_rate,
                result.metrics.profit_factor,
                int(result.wfa.passed),
                result.cpcv.pbo,
                int(result.cpcv.passed),
                result.dsr.dsr,
                int(result.dsr.passed),
                result.monte_carlo.sharpe_5th_pct,
                int(result.monte_carlo.passed),
                int(result.all_gates_passed),
                result.recommendation,
                full_json,
            ),
        )
        await self._db.commit()

        row_id = cursor.lastrowid
        logger.info(
            "Saved pipeline result for '%s': %s (row %d)",
            result.strategy_name, result.recommendation, row_id,
        )
        return row_id
