---
phase: 04-paper-trading-validation
plan: "05"
subsystem: risk
tags: [greeks, var, stress-testing, position-sizing, kelly-criterion, circuit-breakers, risk-management, scipy, numpy]

# Dependency graph
requires:
  - phase: 04-paper-trading-validation (plan 02)
    provides: PaperTradingEngine, PositionTracker, PnLCalculator, OrderManager
  - phase: 04-paper-trading-validation (plan 03)
    provides: Slippage model, FillSimulator
  - phase: 04-paper-trading-validation (plan 04)
    provides: ShadowModeManager, ExitMonitor
  - phase: 03-ml-intelligence-layer (plan 02)
    provides: RegimeDetector, RegimeManager (HMM states for regime-adjusted limits)
  - phase: 03-ml-intelligence-layer (plan 03)
    provides: VolForecaster (daily vol for VaR computation)
  - phase: 03-ml-intelligence-layer (plan 05)
    provides: AnomalyManager (anomaly score for circuit breakers)
  - phase: 01-mvp-data-signals
    provides: Black-Scholes Greeks functions (src/analysis/greeks.py)
provides:
  - RiskConfig with regime-scaled limits
  - PortfolioAnalyzer (Greeks aggregation, VaR, concentration, correlation)
  - StressTestEngine (18 scenarios, full BS repricing)
  - Position sizing (Kelly fraction, vol/regime/anomaly adjusted)
  - RiskManager (pre-trade checks, continuous monitoring, circuit breakers)
  - Risk DB schema (snapshots, alerts, check logs)
  - RiskManager wired into PaperTradingEngine tick loop
affects: [04-paper-trading-validation plan 06 (Discord paper trading cog), 04-paper-trading-validation plan 07 (Discord performance reporting), 04-paper-trading-validation plan 08 (integration tests)]

# Tech tracking
tech-stack:
  added: []
  patterns: [stateless analyzer pattern, regime-scaled risk limits, Delta-Gamma-Theta VaR, Kelly fraction position sizing, circuit breaker state machine]

key-files:
  created:
    - src/risk/__init__.py
    - src/risk/config.py
    - src/risk/models.py
    - src/risk/analyzer.py
    - src/risk/stress.py
    - src/risk/sizing.py
    - src/risk/schema.py
    - src/risk/manager.py
    - tests/test_risk_config.py
    - tests/test_risk_models.py
    - tests/test_risk_analyzer.py
    - tests/test_risk_stress.py
    - tests/test_risk_sizing.py
    - tests/test_risk_manager.py
    - tests/test_risk_schema.py
    - tests/test_risk_integration.py
  modified:
    - src/paper/engine.py
    - src/paper/models.py
    - src/config.py

key-decisions:
  - "Stateless PortfolioAnalyzer — all state from position data passed to methods (testable, usable from both RiskManager and Discord)"
  - "Delta-Gamma-Theta VaR with Cornish-Fisher expansion as primary; Historical VaR as secondary when returns available"
  - "18 standard stress scenarios covering crashes, rallies, vol spikes/crushes, rate shocks, and combinations"
  - "Kelly fraction with 1/4 scaling for new paper strategies, 1/3 for proven (30+ trades)"
  - "Circuit breakers: VIX > 35 halt, SPX -3% intraday halt, anomaly > 0.8 halt, 3 consecutive fill failures halt"

patterns-established:
  - "Risk check pipeline: pre-trade validation returns RiskCheckResult with approved/rejected + reasons"
  - "Circuit breaker state machine: normal → tripped (with reason) → resume (with hysteresis thresholds)"
  - "Regime-scaled limits via REGIME_MULTIPLIERS dict — crisis mode zeroes position sizing"
  - "Risk monitoring in tick loop: compute_greeks → compute_var → stress_test → check_limits → persist_snapshot"

issues-created: []

# Metrics
duration: 16 min
completed: 2026-02-25
---

# Phase 4 Plan 5: Paper Portfolio Analytics Summary

**Complete risk analytics subsystem — Greeks aggregation, Delta-Gamma VaR, 18-scenario stress testing, Kelly-fraction position sizing, pre-trade checks, circuit breakers, and regime-scaled limits — wired into paper trading engine tick loop**

## Performance

- **Duration:** 16 min
- **Started:** 2026-02-25T00:41:20Z
- **Completed:** 2026-02-25T00:57:39Z
- **Tasks:** 8
- **Files modified:** 19 (8 new source + 8 new test + 3 modified)

## Accomplishments
- Complete `src/risk/` package with 8 modules: config, models, analyzer, stress, sizing, schema, manager, __init__
- PortfolioAnalyzer: Greeks aggregation from position legs, Delta-Gamma-Theta VaR (parametric + historical), concentration analysis (by expiry/strategy/strike range), cross-strategy correlation
- StressTestEngine: 18 predefined scenarios (crashes to -20%, rallies to +10%, vol spikes/crushes, rate shocks, combinations), full Black-Scholes repricing per leg
- Position sizing: raw Kelly fraction from win rate + payoff ratio, scaled by regime (0x in crisis), vol forecast, and anomaly score
- RiskManager: 7 pre-trade checks (premium, delta, notional, DTE, strategy allocation, concurrent positions, cash reserve), continuous monitoring with alert generation, circuit breakers (VIX, SPX crash, anomaly, fill failures), DB persistence of snapshots/alerts/check logs
- Risk DB schema: 4 tables (risk_snapshots, risk_alerts, risk_check_log, circuit_breaker_log) + 6 indexes
- Wired into PaperTradingEngine: risk monitoring on every tick, daily circuit breaker reset, risk fields on PortfolioSummary

## Task Commits

Each task was committed atomically:

1. **Task 1: Risk config and data models** (steps 1-3) - `10f55aa` (feat)
2. **Task 2: Portfolio analyzer** (step 4) - `b68bad8` (feat)
3. **Task 3: Stress test engine** (step 5) - `a5e4621` (feat)
4. **Task 4: Position sizing** (step 6) - `b63c4a6` (feat)
5. **Task 5: Risk DB schema** (step 7) - `cdd4949` (feat)
6. **Task 6: RiskManager** (step 8) - `6bdc117` (feat)
7. **Task 7: Engine wiring** (steps 9-11) - `5b18e93` (feat)
8. **Task 8: All tests** (steps 12-16) - `dfae538` (test)

## Files Created/Modified

**New source files:**
- `src/risk/__init__.py` — Package init, public exports (RiskConfig, RiskManager, PortfolioAnalyzer, StressTestEngine)
- `src/risk/config.py` — RiskConfig dataclass (30+ limit params), REGIME_MULTIPLIERS, KELLY_FRACTIONS
- `src/risk/models.py` — 10 dataclasses: PortfolioGreeks, VaRResult, StressScenario, StressTestResult, RiskAlert, RiskCheckResult, PositionSizeResult, ConcentrationReport, CorrelationReport, RiskSnapshot
- `src/risk/analyzer.py` — PortfolioAnalyzer: compute_greeks(), compute_var(), compute_concentration(), compute_correlation()
- `src/risk/stress.py` — StressTestEngine: 18 standard scenarios, run_all()/run_scenario() with BS repricing
- `src/risk/sizing.py` — compute_position_size(): Kelly fraction + vol/regime/anomaly multipliers
- `src/risk/schema.py` — init_risk_tables(): 4 tables + 6 indexes
- `src/risk/manager.py` — RiskManager: check_order(), monitor_portfolio(), circuit breaker state machine

**Modified files:**
- `src/paper/engine.py` — Added risk_manager field, set_risk_manager(), risk monitoring in tick loop, daily reset
- `src/paper/models.py` — Added 7 risk fields to PortfolioSummary (portfolio_greeks, var_result, stress_results, concentration, active_alerts, circuit_breakers_active, risk_utilization)
- `src/config.py` — Added 6 risk management env vars

**New test files:**
- `tests/test_risk_config.py` — 10 tests (defaults, env override, regime multipliers, Kelly fractions)
- `tests/test_risk_models.py` — 12 tests (all dataclass defaults and field validation)
- `tests/test_risk_analyzer.py` — 30 tests (Greeks, VaR, historical VaR, concentration, correlation)
- `tests/test_risk_stress.py` — 18 tests (all scenarios, edge cases, empty portfolio)
- `tests/test_risk_sizing.py` — 17 tests (Kelly, regime scaling, vol/anomaly multipliers)
- `tests/test_risk_manager.py` — 22 tests (pre-trade checks, monitoring, circuit breakers)
- `tests/test_risk_schema.py` — 7 tests (table creation, indexes, persistence)
- `tests/test_risk_integration.py` — 12 tests (end-to-end risk + paper engine)

## Decisions Made

- Stateless PortfolioAnalyzer design — all state comes from position data passed to each method. Makes it easy to test and use from both RiskManager (continuous) and Discord commands (on-demand).
- Delta-Gamma-Theta parametric VaR as primary method (uses LSTM vol forecast), Historical VaR as secondary (when 20+ days of SPX returns available).
- 18 stress scenarios covering the full range: market crashes (-5% to -20%), rallies (+3% to +10%), vol spikes/crushes, rate shocks, and combined scenarios.
- Kelly fraction at 1/4 for new paper strategies, 1/3 for proven (30+ trades) — conservative scaling appropriate for paper validation.
- Circuit breakers with hysteresis: VIX halt at 35 / resume at 30, anomaly halt at 0.8 / resume at 0.5.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed dollar_delta precision mismatch in test**
- **Found during:** Task 8 (test creation)
- **Issue:** Test compared `dollar_delta == delta` with exact equality but implementation rounds to different decimal precision
- **Fix:** Used `pytest.approx` with appropriate tolerance
- **Files modified:** tests/test_risk_analyzer.py
- **Verification:** Test passes

**2. [Rule 1 - Bug] Fixed cash reserve test hitting concurrent strategy limit first**
- **Found during:** Task 8 (test creation)
- **Issue:** All test positions used strategy_id=1, causing strategy concurrent limit (max 3) to fail before cash reserve check
- **Fix:** Assigned different strategy IDs to test positions
- **Files modified:** tests/test_risk_manager.py
- **Verification:** Test correctly validates cash reserve logic

---

**Total deviations:** 2 auto-fixed (both test assertion bugs), 0 deferred
**Impact on plan:** Minor test fixes only. All source code implemented exactly as planned. No scope creep.

## Issues Encountered

None — plan executed cleanly.

## Next Phase Readiness
- Risk analytics subsystem complete and wired into paper engine
- Ready for Plan 4-6: Discord paper trading cog (will use RiskManager for pre-trade checks, RiskSnapshot for risk displays)
- Ready for Plan 4-7: Discord performance reporting (will use PortfolioAnalyzer for Greeks/VaR summaries)

---
*Phase: 04-paper-trading-validation*
*Completed: 2026-02-25*
