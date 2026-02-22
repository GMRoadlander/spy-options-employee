# Plan 2-2 Summary: Backtesting Engine + Anti-Overfitting Pipeline

## Result

All 9 tasks completed. 386 tests passing (273 baseline + 113 new). 9 commits.

## What Was Built

### Backtesting Engine
- **Data Transform** (`src/backtest/data_transform.py`): Converts OptionsChain objects to optopsy-compatible DataFrames. PM-settled filter excludes AM-settled 3rd-Friday SPX monthlies.
- **Engine** (`src/backtest/engine.py`): Maps YAML strategy templates to historical trade execution. Delta-based strike selection. Supports short puts, iron condors, verticals. Day-by-day exit rule simulation (profit target, stop loss, DTE close).
- **Metrics** (`src/backtest/metrics.py`): Full strategy evaluation: Sharpe, Sortino, Calmar, max drawdown, drawdown duration, win rate, expectancy, profit factor, skewness, kurtosis. Discord-friendly report formatting.

### Anti-Overfitting Pipeline (4 gates — NON-NEGOTIABLE)
- **WFA** (`src/backtest/wfa.py`): Rolling 12mo IS / 3mo OOS windows. Pass: mean OOS Sharpe > 0 AND degradation ratio ≥ 0.5.
- **CPCV** (`src/backtest/cpcv.py`): Combinatorial Purged Cross-Validation. K-fold splitting with purging (≥ max DTE) and embargo. PBO from path Sharpe distribution. Pass: PBO < 0.50.
- **DSR** (`src/backtest/dsr.py`): Bailey & Lopez de Prado (2014). Corrects for multiple-testing bias. Handles options skew/kurtosis. Pass: DSR > 0.95.
- **Monte Carlo** (`src/backtest/monte_carlo.py`): 1000-run bootstrap resampling. Tracks Sharpe distribution, max drawdown, terminal wealth. Pass: 5th-pct Sharpe > 0.
- **Pipeline** (`src/backtest/pipeline.py`): Orchestrates all 4 gates. PROMOTE (4/4) / REFINE (3/4) / REJECT (≤2/4). Results persisted to `backtest_results` table.

### Database
- Added `backtest_results` table to `src/db/store.py` with full pipeline result persistence.

### Dependencies
- Added `optopsy>=2.2.0` and `skfolio>=0.4.0` to requirements.txt.

## Commits

| Hash | Type | Description |
|------|------|-------------|
| `9041732` | feat | ORATS to optopsy data transform with PM-settled filter |
| `eae2841` | feat | Backtesting engine with strategy template integration |
| `5ed9ae4` | feat | Strategy evaluation metrics |
| `175c870` | feat | Walk-forward analysis with rolling IS/OOS windows |
| `b459f8f` | feat | CPCV with combinatorial purged cross-validation and PBO |
| `32b1ebb` | feat | Deflated Sharpe ratio (Bailey & Lopez de Prado 2014) |
| `a35c52b` | feat | Monte Carlo bootstrap simulation |
| `465cb9d` | feat | Anti-overfitting pipeline orchestrator with DB persistence |
| `9ab3a7c` | chore | Add optopsy and skfolio to requirements |

## Test Coverage

| Module | Tests |
|--------|-------|
| data_transform | 17 |
| engine | 17 |
| metrics | 23 |
| wfa | 15 |
| cpcv | 12 |
| dsr | 10 |
| monte_carlo | 10 |
| pipeline | 9 |
| **New total** | **113** |
| **Full suite** | **386** |

## Deviations

- **No optopsy runtime dependency**: Engine implements its own matching/execution logic rather than calling optopsy functions directly. This gives full control over exit rules and strategy types without being limited by optopsy's API. Optopsy remains in requirements for future cross-validation.
- **CPCV without skfolio runtime**: Built standalone CPCV implementation using numpy combinatorics. Avoids heavy skfolio dependency chain while matching the algorithm. skfolio in requirements for future advanced use.

## Files

### New (16)
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

### Modified (2)
- `src/db/store.py` — backtest_results table
- `requirements.txt` — optopsy, skfolio
