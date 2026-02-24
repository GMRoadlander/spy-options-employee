---
phase: 04-paper-trading-validation
plan: 02
subsystem: paper-trading, engine
tags: [paper-trading, orders, positions, pnl, aiosqlite, dataclasses, fill-simulation, mark-to-market, equity-curve]

# Dependency graph
requires:
  - phase: 04-paper-trading-validation plan 01
    provides: Bug-free ML pipeline, secure model serialization, clean feature store UPSERT
  - phase: 02-strategy-research-engine
    provides: Strategy lifecycle state machine, backtest metrics module
provides:
  - Paper trading data models (8 dataclasses)
  - Paper trading database schema (5 tables + indexes)
  - OrderManager with fill simulation (submit/fill/cancel/expire)
  - PositionTracker with mark-to-market and settlement
  - PnLCalculator with metrics reuse from backtest module
  - PaperTradingEngine orchestrator (tick loop, EOD settlement, portfolio summary)
  - Paper trading config values
affects: [04-paper-trading-validation plans 03-10, paper-slippage, shadow-mode, exit-monitor, risk-management, promotion]

# Tech tracking
tech-stack:
  added: []
  patterns: [async service-injection, orchestrator-delegates pattern, FillSimulator slippage model, per-spread position tracking]

key-files:
  created:
    - src/paper/__init__.py
    - src/paper/models.py
    - src/paper/schema.py
    - src/paper/orders.py
    - src/paper/positions.py
    - src/paper/pnl.py
    - src/paper/engine.py
    - tests/test_paper_models.py
    - tests/test_paper_schema.py
    - tests/test_paper_orders.py
    - tests/test_paper_positions.py
    - tests/test_paper_pnl.py
    - tests/test_paper_engine.py
  modified:
    - src/config.py

key-decisions:
  - "FillSimulator kept in orders.py for cohesion (only used by OrderManager)"
  - "Per-spread position tracking (not per-leg) with legs stored as JSON"
  - "Reuse calculate_metrics() from src/backtest/metrics.py for paper trade metrics"
  - "SPX $100 multiplier, $0.65/contract/leg fee (Schwab standard)"

patterns-established:
  - "Orchestrator-delegates: PaperTradingEngine delegates to OrderManager, PositionTracker, PnLCalculator"
  - "FillSimulator injectable: accepts SlippageModel for testing with FixedSlippage vs DynamicSpreadSlippage"
  - "Paper tables idempotent: init_paper_tables() uses CREATE TABLE IF NOT EXISTS"

issues-created: []

# Metrics
duration: 19min
completed: 2026-02-24
---

# Phase 4 Plan 2: Paper Trading Engine Core Summary

**Built complete paper trading engine with OrderManager, PositionTracker, PnLCalculator orchestrated by PaperTradingEngine — 8 dataclasses, 5 DB tables, tick-driven architecture, 116 new tests**

## Performance

- **Duration:** 19 min
- **Started:** 2026-02-24T05:08:54Z
- **Completed:** 2026-02-24T05:28:25Z
- **Tasks:** 8 steps completed
- **Files modified:** 14 (7 source + 7 test)

## Accomplishments
- 8 paper trading dataclasses (PaperTradingConfig, LegSpec, SimulatedFill, TickResult, PortfolioSummary, PaperResults, TradePnL, ExitSignal)
- 5 database tables (paper_orders, paper_fills, paper_positions, paper_trades, paper_portfolio) with proper FK constraints and indexes
- OrderManager with FillSimulator supporting market/limit orders, bid/ask slippage, stale order expiration
- PositionTracker with per-spread tracking, mark-to-market, AM/PM settlement detection, expiration handling
- PnLCalculator reusing backtest `calculate_metrics()` for consistent evaluation, daily equity snapshots
- PaperTradingEngine orchestrator with tick loop (entry signals → fill orders → mark positions → check exits → handle settlements → snapshot)
- Paper trading config values with env var overrides (starting capital, slippage, fees, promotion thresholds)

## Task Commits

Each task was committed atomically:

1. **Step 1: Create data models** - `8e6e4cf` (feat)
2. **Step 2: Create database schema** - `1e7f39d` (feat)
3. **Step 3: Create OrderManager** - `1c4d60f` (feat)
4. **Step 4: Create PositionTracker** - `cc83b2f` (feat)
5. **Step 5: Create PnLCalculator** - `4193703` (feat)
6. **Step 6: Create PaperTradingEngine** - `fe21d29` (feat)
7. **Step 7: Add config values** - `62d88f6` (chore)
8. **Step 8: Write tests** - `848b97a` (test)

## Files Created/Modified
- `src/paper/__init__.py` — Package init with public API exports
- `src/paper/models.py` — 8 dataclasses for paper trading domain
- `src/paper/schema.py` — 5 SQL tables with FK constraints and indexes
- `src/paper/orders.py` — OrderManager + FillSimulator (498 LOC)
- `src/paper/positions.py` — PositionTracker with settlement handling (657 LOC)
- `src/paper/pnl.py` — PnLCalculator with metrics reuse (440 LOC)
- `src/paper/engine.py` — PaperTradingEngine orchestrator (623 LOC)
- `src/config.py` — 8 new paper trading config fields
- `tests/test_paper_models.py` — 25 tests for dataclass validation
- `tests/test_paper_schema.py` — 12 tests for table creation and FK constraints
- `tests/test_paper_orders.py` — 25 tests for order lifecycle
- `tests/test_paper_positions.py` — 17 tests for position tracking
- `tests/test_paper_pnl.py` — 16 tests for PnL calculation
- `tests/test_paper_engine.py` — 21 tests for engine orchestration

## Decisions Made
- FillSimulator in orders.py (not separate file) — only used by OrderManager, better cohesion
- Per-spread position tracking with legs as JSON — matches how options spreads are traded
- Reuse backtest `calculate_metrics()` for paper trade evaluation — consistent Sharpe/drawdown calculation
- SPX $100 multiplier, $0.65/contract/leg Schwab fee — realistic cost simulation
- Injectable SlippageModel on FillSimulator — allows FixedSlippage for testing, DynamicSpreadSlippage for production (sub-plan 4-3)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added legs parameter to _calculate_net_fill**
- **Found during:** Step 5 (PnLCalculator)
- **Issue:** Cannot determine buy/sell direction from SimulatedFill alone; need LegSpec action field
- **Fix:** Added `legs: list[LegSpec]` parameter to properly compute net credit/debit sign
- **Verification:** PnL tests pass with correct credit/debit calculation
- **Committed in:** `4193703` (part of Step 5 commit)

---

**Total deviations:** 1 auto-fixed (blocking design issue), 0 deferred
**Impact on plan:** Minimal — parameter signature adjustment for correctness. No scope creep.

## Issues Encountered
None — all 8 steps completed without blocking issues.

## Next Phase Readiness
- Paper trading engine core complete — OrderManager, PositionTracker, PnLCalculator, Engine all functional
- 1016 tests passing (900 existing + 116 new, no regressions)
- Engine tick loop has placeholder hooks for ShadowModeManager and ExitMonitor (sub-plan 4-4)
- FillSimulator accepts injectable SlippageModel — ready for DynamicSpreadSlippage (sub-plan 4-3)
- Ready for 4-3 (Slippage Model)

---
*Phase: 04-paper-trading-validation*
*Completed: 2026-02-24*
