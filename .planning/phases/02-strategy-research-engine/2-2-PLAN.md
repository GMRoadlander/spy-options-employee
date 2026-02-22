# Plan 2-2: Backtesting Engine + Anti-Overfitting Pipeline

## Objective

Build the core research capability: a backtesting engine that runs SPX options strategies against ORATS historical data, and a rigorous anti-overfitting evaluation pipeline (WFA + CPCV + DSR + Monte Carlo) that gates strategy promotion. This is the NON-NEGOTIABLE quality bar — no strategy advances to paper trading without passing all four gates.

## Execution Context

- **Depends on**: Plan 2-1 (ORATS client, historical store, strategy schema, lifecycle)
- **Key libraries**: `optopsy>=2.2.0` (backtesting), `skfolio` (CPCV), `scipy` (DSR), `numpy` (Monte Carlo)
- **Optopsy data format**: Requires DataFrame with columns [underlying_symbol, underlying_price, option_type, expiration, quote_date, strike, bid, ask, delta(optional)] — mapped by position index
- **SPX caveat**: Restrict to SPXW PM-settled weeklies initially. Standard SPX monthlies have AM settlement that optopsy doesn't handle. SPXW weeklies are PM-settled and safe.
- **Anti-overfitting gates** (from roadmap, NON-NEGOTIABLE):
  - Walk-Forward Analysis: 12-month IS / 3-month OOS
  - CPCV: PBO < 0.50
  - DSR: p < 0.05 (DSR > 0.95)
  - Monte Carlo: 5th-percentile Sharpe > 0

## Context

- ORATS `hist/strikes` provides call/put bid/ask, Greeks, IV per row per strike per date
- Optopsy expects call and put as separate rows — need a transform layer
- Strategy templates (from Plan 2-1) define structure, entry rules, exit rules
- The backtesting engine bridges strategy templates → optopsy execution → evaluation metrics
- Evaluation pipeline runs automatically after each backtest; results determine if strategy can promote

## Tasks

### Task 1: ORATS → Optopsy Data Transform
**What**: Create `src/backtest/data_transform.py` — transform ORATS historical data into optopsy-compatible DataFrames
**Why**: Bridge between ORATS storage format and optopsy input requirements

```python
# src/backtest/data_transform.py

def chains_to_optopsy_df(chains: list[OptionsChain]) -> pd.DataFrame:
    """Transform list of OptionsChain objects into optopsy-compatible DataFrame.

    Output columns (by index position):
    0: underlying_symbol (str)
    1: underlying_price (float)
    2: option_type (str: "c" or "p")
    3: expiration (datetime)
    4: quote_date (datetime)
    5: strike (float)
    6: bid (float)
    7: ask (float)
    8: delta (float, optional)
    """

def filter_pm_settled(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to SPXW PM-settled weeklies only (exclude standard monthly AM-settled).

    Heuristic: standard SPX monthlies expire on 3rd Friday.
    SPXW weeklies expire on all other Fridays + Mon/Wed/Fri 0DTEs.
    """
```

The transform splits each ORATS row (which has both call and put data) into two rows (one call, one put), mapping:
- `callBidPrice` / `callAskPrice` → call row `bid` / `ask`
- `putBidPrice` / `putAskPrice` → put row `bid` / `ask`
- `delta` → call row delta; negate for put row
- `tradeDate` → `quote_date`
- `expirDate` → `expiration`

**Tests** (`tests/test_data_transform.py`):
- Test ORATS row splits into call + put rows correctly
- Test field mapping matches optopsy expected positions
- Test PM-settled filter excludes 3rd Friday monthlies
- Test handles missing bid/ask (zero volume strikes)
- Test handles multiple dates and expirations
- ~12 tests

**Checkpoint**: `pytest tests/test_data_transform.py` — all pass

### Task 2: Backtesting Engine
**What**: Create `src/backtest/engine.py` — wraps optopsy with strategy template integration
**Why**: Bridges the gap between YAML strategy definitions and optopsy's function-based API

```python
# src/backtest/engine.py

@dataclass
class BacktestResult:
    strategy_name: str
    strategy_id: str
    start_date: date
    end_date: date
    num_trades: int
    total_return: float
    daily_returns: pd.Series         # for metrics calculation
    trade_log: pd.DataFrame          # individual trades with entry/exit dates and P&L
    raw_optopsy_result: pd.DataFrame # optopsy output

class BacktestEngine:
    def __init__(self, historical_store: HistoricalStore)

    async def run(
        self,
        strategy: StrategyTemplate,
        ticker: str = "SPX",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> BacktestResult:
        """Run a full backtest for a strategy template.

        1. Load historical data from store for date range
        2. Transform to optopsy format (PM-settled only)
        3. Apply entry rules as pre-filters
        4. Map strategy structure to optopsy function
        5. Apply exit rules as post-filters
        6. Build trade log and daily return series
        """

    def _map_strategy_to_optopsy(self, strategy: StrategyTemplate) -> callable:
        """Map strategy structure (legs) to the appropriate optopsy function.

        Mappings:
        - 1 leg sell put → op.short_puts
        - 1 leg buy put + 1 leg sell put → op.put_spreads (vertical)
        - 2 legs sell (call+put) + 2 legs buy (call+put) → op.iron_condors
        - 1 leg sell call + 1 leg sell put → op.short_strangles
        etc.
        """

    def _apply_entry_filters(self, df: pd.DataFrame, rules: list[EntryRule]) -> pd.DataFrame:
        """Filter quote dates where entry conditions are met.

        Rule types: iv_rank, pcr_signal, market_hours, day_of_week, etc.
        """

    def _apply_exit_rules(self, trades: pd.DataFrame, rules: list[ExitRule]) -> pd.DataFrame:
        """Apply profit target, stop loss, DTE exit rules to trades.

        Scans daily marks for each open trade:
        - profit_target: close when mark-to-market >= X% of max profit
        - stop_loss: close when loss >= X% of credit received
        - dte_exit: close when DTE <= N regardless of P&L
        """
```

**Tests** (`tests/test_backtest_engine.py`):
- Test strategy → optopsy function mapping (iron condor, vertical, naked)
- Test entry filter application (IV rank, day of week)
- Test exit rule application (profit target, stop loss, DTE exit)
- Test BacktestResult fields populated correctly
- Test with synthetic historical data (no ORATS API needed)
- Test handles no-trade scenario (all dates filtered out)
- ~18 tests

**Checkpoint**: `pytest tests/test_backtest_engine.py` — all pass

### Task 3: Strategy Evaluation Metrics
**What**: Create `src/backtest/metrics.py` — compute all strategy performance metrics
**Why**: Standardized evaluation across all strategies; feeds into anti-overfitting pipeline

```python
# src/backtest/metrics.py

@dataclass
class StrategyMetrics:
    # Return metrics
    total_return: float
    annual_return: float
    monthly_returns: list[float]

    # Risk-adjusted
    sharpe_ratio: float           # annualized, excess return / std
    sortino_ratio: float          # annualized, downside deviation
    calmar_ratio: float           # annual return / max drawdown

    # Drawdown
    max_drawdown: float           # worst peak-to-trough (negative %)
    max_drawdown_duration: int    # trading days
    avg_drawdown: float

    # Trade stats
    num_trades: int
    win_rate: float               # % of profitable trades
    avg_win: float                # average winning trade P&L
    avg_loss: float               # average losing trade P&L
    expectancy: float             # (win_rate * avg_win) - ((1-win_rate) * avg_loss)
    profit_factor: float          # gross profits / gross losses
    avg_holding_days: float

    # Distribution
    skewness: float
    kurtosis: float

    # Regime-conditional (populated if regime data available)
    sharpe_by_regime: dict[str, float] | None  # risk_on, risk_off, crisis

def calculate_metrics(result: BacktestResult, risk_free_rate: float = 0.05) -> StrategyMetrics:
    """Calculate all metrics from a BacktestResult."""

def format_metrics_report(metrics: StrategyMetrics) -> str:
    """Format metrics as a human-readable text report for Discord."""
```

All calculations use standard financial formulas:
- Sharpe: `(mean_excess_return * sqrt(252)) / (std_return * sqrt(252))`
- Sortino: same but denominator uses downside deviation only
- Calmar: `annual_return / abs(max_drawdown)`
- Profit factor: `sum(winning_trades) / abs(sum(losing_trades))`
- Expectancy: `(win_rate * avg_win) + ((1 - win_rate) * avg_loss)`

**Tests** (`tests/test_metrics.py`):
- Test each metric against hand-calculated values
- Test edge cases: no trades, all winners, all losers, single trade
- Test Sharpe with known input (e.g., constant returns → infinite Sharpe)
- Test drawdown calculation with known sequence
- Test profit factor with zero losses
- ~20 tests

**Checkpoint**: `pytest tests/test_metrics.py` — all pass

### Task 4: Walk-Forward Analysis (WFA)
**What**: Create `src/backtest/wfa.py` — rolling in-sample/out-of-sample evaluation
**Why**: First gate in anti-overfitting pipeline. Tests if strategy works on unseen data.

```python
# src/backtest/wfa.py

@dataclass
class WFAResult:
    strategy_name: str
    num_windows: int
    is_periods: list[tuple[date, date]]   # in-sample date ranges
    oos_periods: list[tuple[date, date]]  # out-of-sample date ranges
    is_metrics: list[StrategyMetrics]     # per-window IS metrics
    oos_metrics: list[StrategyMetrics]    # per-window OOS metrics
    degradation: float                     # avg OOS Sharpe / avg IS Sharpe
    oos_sharpe_mean: float
    oos_sharpe_std: float
    passed: bool                           # OOS Sharpe consistently > 0?

class WalkForwardAnalyzer:
    def __init__(
        self,
        is_months: int = 12,    # in-sample window
        oos_months: int = 3,    # out-of-sample window
        step_months: int = 3,   # step size (rolling)
    )

    async def run(
        self,
        engine: BacktestEngine,
        strategy: StrategyTemplate,
        start_date: date,
        end_date: date,
    ) -> WFAResult:
        """Run walk-forward analysis.

        1. Generate rolling windows: [IS₁|OOS₁] [IS₂|OOS₂] ...
           where IS = 12 months, OOS = 3 months, step = 3 months
        2. For each window: run backtest on IS, run backtest on OOS
        3. Compare IS vs OOS performance (degradation ratio)
        4. Pass if mean OOS Sharpe > 0 and degradation < 0.5
        """
```

Window generation example with 5 years of data (2019-2024):
- Window 1: IS=2019-01 to 2019-12, OOS=2020-01 to 2020-03
- Window 2: IS=2019-04 to 2020-03, OOS=2020-04 to 2020-06
- Window 3: IS=2019-07 to 2020-06, OOS=2020-07 to 2020-09
- ... etc.

**Tests** (`tests/test_wfa.py`):
- Test window generation produces correct IS/OOS pairs
- Test degradation calculation
- Test pass/fail logic
- Test with insufficient data (too few windows)
- Test step size variations
- ~10 tests

**Checkpoint**: `pytest tests/test_wfa.py` — all pass

### Task 5: CPCV via skfolio
**What**: Create `src/backtest/cpcv.py` — Combinatorial Purged Cross-Validation integration
**Why**: Second gate. Produces distribution of strategy performance, not just one number.

```python
# src/backtest/cpcv.py

@dataclass
class CPCVResult:
    strategy_name: str
    n_folds: int
    n_test_folds: int
    n_paths: int
    purge_size: int            # trading days
    embargo_size: int          # trading days

    # Distribution of OOS metrics across paths
    sharpe_distribution: list[float]
    sharpe_mean: float
    sharpe_std: float
    sharpe_5th_pct: float      # 5th percentile

    # PBO
    pbo: float                 # Probability of Backtest Overfitting
    passed: bool               # pbo < 0.50

class CPCVAnalyzer:
    def __init__(
        self,
        target_paths: int = 100,
        purge_days: int = 45,      # must be >= max DTE in strategy
        embargo_days: int = 5,
    )

    async def run(
        self,
        daily_returns: pd.Series,
        strategy: StrategyTemplate,
    ) -> CPCVResult:
        """Run CPCV analysis.

        1. Determine fold count using skfolio.optimal_folds_number()
        2. Set purge_size >= max DTE to prevent label leakage
        3. Run CombinatorialPurgedCV to generate test paths
        4. Calculate Sharpe ratio for each test path
        5. Calculate PBO from path Sharpe distribution
        """
```

Key implementation details:
- `purge_size` MUST be >= the strategy's max DTE. A 45-DTE iron condor needs purge_size=45+ to prevent the training set from seeing the outcome of a position that overlaps with the test period.
- PBO calculation: for each CPCV path, rank all strategy variants by IS performance. PBO = fraction of paths where the best IS variant underperforms median OOS.
- For single-strategy evaluation (no variants), PBO simplifies to checking if OOS Sharpe distribution has >50% negative mass.

**Tests** (`tests/test_cpcv.py`):
- Test with synthetic returns (known Sharpe)
- Test purge size enforcement (>= max DTE)
- Test PBO calculation with controlled distribution
- Test pass/fail threshold (PBO < 0.50)
- ~8 tests

**Checkpoint**: `pytest tests/test_cpcv.py` — all pass

### Task 6: Deflated Sharpe Ratio
**What**: Create `src/backtest/dsr.py` — DSR implementation from Bailey & Lopez de Prado (2014)
**Why**: Third gate. Corrects for selection bias when testing multiple strategy variations.

```python
# src/backtest/dsr.py

@dataclass
class DSRResult:
    strategy_name: str
    estimated_sharpe: float     # raw SR of selected strategy
    expected_max_sharpe: float  # SR₀ (expected best under null)
    dsr: float                  # deflated SR in [0, 1]
    n_trials: int               # number of strategies/variants tested
    backtest_horizon: int       # trading days
    skewness: float
    kurtosis: float
    passed: bool                # dsr > 0.95 (p < 0.05)

def expected_max_sharpe(mean_sr: float, var_sr: float, n_trials: int) -> float:
    """Expected maximum SR from N independent trials under null hypothesis."""

def deflated_sharpe_ratio(
    estimated_sharpe: float,
    sharpe_variance: float,
    n_trials: int,
    backtest_horizon: int,
    skew: float,
    kurtosis: float,
) -> float:
    """Returns DSR in [0, 1]. Values > 0.95 pass at 5% significance."""

def evaluate_dsr(
    strategy_sharpe: float,
    all_sharpes: list[float],    # Sharpe ratios of ALL tested strategies
    daily_returns: pd.Series,
) -> DSRResult:
    """Convenience function: compute DSR from strategy returns and comparison set."""
```

Implementation is ~30 lines using `scipy.stats.norm` and `numpy`. The formula is well-established:

```
SR₀ = sqrt(Var[SR]) × [(1-γ)Φ⁻¹(1-1/N) + γΦ⁻¹(1-1/(Ne))]
DSR = Φ[(SR* - SR₀)√(T-1) / √(1 - γ₃·SR* + (γ₄-1)/4·SR*²)]
```

Where γ = Euler-Mascheroni constant, γ₃ = skewness, γ₄ = kurtosis.

**Tests** (`tests/test_dsr.py`):
- Test with known inputs against published examples
- Test n_trials=1 (no selection bias correction needed)
- Test with high kurtosis (options-like returns)
- Test with negative skew (short premium strategies)
- Test boundary: DSR exactly at 0.95 threshold
- ~8 tests

**Checkpoint**: `pytest tests/test_dsr.py` — all pass

### Task 7: Monte Carlo Simulation
**What**: Create `src/backtest/monte_carlo.py` — Monte Carlo simulation for robustness testing
**Why**: Fourth gate. Tests if strategy survives random perturbation of trade ordering and sizing.

```python
# src/backtest/monte_carlo.py

@dataclass
class MonteCarloResult:
    strategy_name: str
    n_simulations: int
    sharpe_distribution: list[float]
    sharpe_mean: float
    sharpe_std: float
    sharpe_5th_pct: float         # 5th percentile
    max_drawdown_95th_pct: float  # 95th percentile (worst-case DD)
    final_return_5th_pct: float   # 5th percentile terminal wealth
    passed: bool                   # 5th-pct Sharpe > 0

class MonteCarloSimulator:
    def __init__(self, n_simulations: int = 1000, seed: int | None = None)

    def run(self, trade_returns: pd.Series) -> MonteCarloResult:
        """Run Monte Carlo simulation.

        Method: Bootstrap resampling of trade returns.
        1. For each simulation:
           a. Resample trades with replacement (same number of trades)
           b. Compute equity curve from resampled trades
           c. Calculate Sharpe, max drawdown, final return
        2. Aggregate statistics across all simulations
        3. Pass if 5th-percentile Sharpe > 0
        """
```

Bootstrap resampling is the right approach for options strategies because:
- Trade returns are roughly independent (each trade is a separate position)
- Preserves the return distribution (skew, kurtosis) unlike parametric simulation
- Simple, robust, well-understood

**Tests** (`tests/test_monte_carlo.py`):
- Test with consistently profitable trades (should pass)
- Test with break-even trades (should fail — 5th pct < 0)
- Test deterministic with seed
- Test n_simulations parameter
- Test distribution statistics (mean should match input mean approximately)
- ~8 tests

**Checkpoint**: `pytest tests/test_monte_carlo.py` — all pass

### Task 8: Anti-Overfitting Pipeline Orchestrator
**What**: Create `src/backtest/pipeline.py` — orchestrate all four gates in sequence
**Why**: Single entry point to run the full evaluation; auto-logs results; gates strategy promotion

```python
# src/backtest/pipeline.py

@dataclass
class PipelineResult:
    strategy_name: str
    strategy_id: str
    timestamp: datetime

    # Individual gate results
    wfa: WFAResult
    cpcv: CPCVResult
    dsr: DSRResult
    monte_carlo: MonteCarloResult

    # Overall
    all_gates_passed: bool
    failed_gates: list[str]       # names of failed gates
    recommendation: str            # "PROMOTE", "REFINE", or "REJECT"

    # Backtest details
    metrics: StrategyMetrics
    backtest: BacktestResult

class EvaluationPipeline:
    def __init__(
        self,
        engine: BacktestEngine,
        store: Store,
    )

    async def evaluate(
        self,
        strategy: StrategyTemplate,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PipelineResult:
        """Run full anti-overfitting evaluation pipeline.

        1. Run backtest → BacktestResult
        2. Calculate metrics → StrategyMetrics
        3. Run WFA (12mo IS / 3mo OOS) → WFAResult
        4. Run CPCV (PBO < 0.50) → CPCVResult
        5. Run DSR (> 0.95) → DSRResult
        6. Run Monte Carlo (1000 runs, 5th-pct Sharpe > 0) → MonteCarloResult
        7. Determine recommendation:
           - All pass → PROMOTE (can go to PAPER)
           - 3/4 pass → REFINE (adjust and re-test)
           - ≤2/4 pass → REJECT
        8. Log results to database
        """

    async def _save_result(self, result: PipelineResult) -> None:
        """Persist evaluation results for audit trail."""
```

Add to `src/db/store.py`:

```sql
CREATE TABLE backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id TEXT NOT NULL REFERENCES strategies(id),
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
    full_result TEXT              -- JSON blob of entire PipelineResult
);
CREATE INDEX idx_backtest_strategy ON backtest_results(strategy_id, run_at);
```

**Tests** (`tests/test_pipeline.py`):
- Test all-pass scenario → PROMOTE recommendation
- Test 3/4 pass → REFINE
- Test ≤2/4 pass → REJECT
- Test result persistence
- Test strategy lifecycle transition on PROMOTE
- ~8 tests

**Checkpoint**: `pytest tests/test_pipeline.py` — all pass

### Task 9: Dependencies + Full Integration Test
**What**: Install new dependencies, run full test suite, verify integration
**Why**: Everything must work together

Changes to `requirements.txt`:
```
optopsy>=2.2.0
skfolio>=0.4.0
```

(`scipy` and `numpy` already in requirements via existing analysis code)

Run full integration:
- `pytest` — all existing 248+ tests (from Plan 2-1) + ~92 new tests pass
- Verify import chain: pipeline → engine → transform → historical_store → orats_client
- Verify pipeline can run end-to-end with synthetic data

**Checkpoint**: `pytest` — all ~340 tests green

## Verification

```bash
# All tests pass
pytest

# Pipeline end-to-end with synthetic data
python -c "
from src.backtest.pipeline import EvaluationPipeline
from src.backtest.metrics import calculate_metrics
from src.backtest.dsr import deflated_sharpe_ratio
# verify imports and basic functionality
"
```

## Success Criteria

- [ ] ORATS data transforms correctly into optopsy format (call/put split, field mapping)
- [ ] Backtesting engine maps strategy templates to optopsy functions
- [ ] All 8 evaluation metrics calculated correctly (Sharpe, Sortino, Calmar, drawdown, win rate, expectancy, profit factor, holding days)
- [ ] WFA produces rolling IS/OOS windows with degradation analysis
- [ ] CPCV integration with skfolio works; PBO calculated from path distribution
- [ ] DSR implementation matches published formula; handles options return distributions
- [ ] Monte Carlo bootstrap produces 1,000 simulations with distributional statistics
- [ ] Pipeline orchestrates all 4 gates and produces PROMOTE/REFINE/REJECT recommendation
- [ ] All ~340 tests pass (248 from Plan 2-1 + ~92 new)
- [ ] PM-settled filter correctly excludes standard SPX monthlies

## Output

New files:
- `src/backtest/__init__.py`
- `src/backtest/data_transform.py`
- `src/backtest/engine.py`
- `src/backtest/metrics.py`
- `src/backtest/wfa.py`
- `src/backtest/cpcv.py`
- `src/backtest/dsr.py`
- `src/backtest/monte_carlo.py`
- `src/backtest/pipeline.py`
- `tests/test_data_transform.py`
- `tests/test_backtest_engine.py`
- `tests/test_metrics.py`
- `tests/test_wfa.py`
- `tests/test_cpcv.py`
- `tests/test_dsr.py`
- `tests/test_monte_carlo.py`
- `tests/test_pipeline.py`

Modified files:
- `src/db/store.py` — backtest_results table
- `requirements.txt` — optopsy, skfolio
