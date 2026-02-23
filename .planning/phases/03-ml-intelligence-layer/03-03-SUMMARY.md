---
phase: 03-ml-intelligence-layer
plan: "03"
subsystem: ml
tags: [pytorch, lstm, volatility, forecasting, feature-store]

# Dependency graph
requires:
  - phase: 03-01
    provides: feature store foundation (FeatureStore, daily_features table)
  - phase: 03-02
    provides: HMM regime detection (regime_state feature)
provides:
  - VolDataset for sliding-window vol sequence creation
  - VolLSTM 2-layer model with 1-day and 5-day vol forecasts
  - VolForecaster high-level API (predict, train, evaluate, save/load)
  - VolManager daily update pipeline with feature store integration
affects: [03-04, 03-08, 03-09, paper-trading]

# Tech tracking
tech-stack:
  added: [torch>=2.0 (CPU)]
  patterns: [LSTM forecasting, temporal train/val split, early stopping, VolManager mirrors RegimeManager]

key-files:
  created: [src/ml/volatility.py, tests/test_volatility.py]
  modified: [requirements.txt]

key-decisions:
  - "CPU-only PyTorch — daily vol forecasting doesn't need GPU"
  - "1-day target uses abs(return)*sqrt(252) proxy instead of rolling(1).std() which is NaN"
  - "VolManager mirrors RegimeManager pattern for consistency"
  - "Temporal train/val split (no random) to prevent lookahead bias"
  - "Early stopping with patience=10 on validation loss"

patterns-established:
  - "VolManager pattern: initialize → train, update → daily inference, get_current_forecast → read"
  - "Feature normalization stats stored with model for portable inference"

issues-created: []

# Metrics
duration: 8 min
completed: 2026-02-23
---

# Phase 3 Plan 03: LSTM Volatility Forecasting Summary

**2-layer LSTM with VIX/regime/Hurst features predicting 1-day and 5-day realized vol, CPU-only inference with VolManager daily pipeline**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-23T02:54:29Z
- **Completed:** 2026-02-23T03:02:47Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments
- LSTM volatility forecasting model (VolLSTM: 2 layers, hidden=64, dropout=0.2, FC→32→2)
- Complete data pipeline: VolDataset sliding-window sequences, prepare_training_data with normalization
- VolForecaster API: predict, train (temporal split + early stopping), evaluate (MAE/RMSE/directional accuracy), save/load
- VolManager daily update pipeline integrating with feature store (vol_forecast_1d, vol_forecast_5d)
- 54 new tests (612 total passing)

## Task Commits

Each task was committed atomically:

1. **Task 1: LSTM model architecture and data preprocessing** - `2e5c3c7` (feat)
2. **Task 2: Training pipeline and feature store integration** - `e189d1c` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified
- `src/ml/volatility.py` - VolDataset, VolLSTM, VolForecaster, VolManager (465 lines)
- `tests/test_volatility.py` - 54 unit tests covering model, training, persistence, integration
- `requirements.txt` - Added torch>=2.0

## Decisions Made
- CPU-only PyTorch — daily vol forecasting doesn't need GPU, saves disk/memory on droplet
- 1-day realized vol target uses |return|*sqrt(252) proxy since rolling(1).std() is NaN
- VolManager mirrors RegimeManager pattern for codebase consistency
- Temporal train/val split (last 20% chronologically) — prevents lookahead bias
- Early stopping with patience=10 on validation loss to prevent overfitting

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed rv_1d target computation**
- **Found during:** Task 1 (data preprocessing)
- **Issue:** `returns.rolling(1).std()` produces all NaN (can't compute std of 1 value)
- **Fix:** Changed to `returns.shift(-1).abs() * sqrt(252)` as 1-day forward realized vol proxy
- **Files modified:** src/ml/volatility.py
- **Verification:** Tests pass, target values are finite and reasonable
- **Committed in:** 2e5c3c7 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug), 0 deferred
**Impact on plan:** Bug fix essential for correct target computation. No scope creep.

## Issues Encountered
None

## Next Phase Readiness
- LSTM vol forecasting ready for integration with strategy evaluation
- VolManager can be wired into daily update pipeline alongside RegimeManager
- Ready for 03-04-PLAN.md (FinBERT Sentiment Analysis)

---
*Phase: 03-ml-intelligence-layer*
*Completed: 2026-02-23*
