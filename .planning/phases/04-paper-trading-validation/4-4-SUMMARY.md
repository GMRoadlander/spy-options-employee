---
phase: 04-paper-trading-validation
plan: 04
subsystem: paper-trading, scheduling
tags: [shadow-mode, exit-monitor, settlement, AM-PM, delta-selection, 0DTE, scheduler]

# Dependency graph
requires:
  - phase: 04-paper-trading-validation plan 02
    provides: PaperTradingEngine, OrderManager, PositionTracker, PnLCalculator
  - phase: 04-paper-trading-validation plan 03
    provides: SlippageModel, FillSimulator with DynamicSpreadSlippage
provides:
  - ShadowModeManager for automatic paper trade generation from PAPER strategies
  - ExitMonitor with 5 exit conditions and AM/PM settlement handling
  - Full tick cycle wired into PaperTradingEngine
  - Scheduler integration (premarket/intraday/postmarket paper trading hooks)
affects: [04-paper-trading-validation plans 05-10, risk-management, promotion-workflow]

# Tech tracking
tech-stack:
  added: []
  patterns: [shadow mode auto-entry, exit priority ordering, AM/PM settlement detection, 3PM 0DTE rule, scheduler paper engine hooks]

key-files:
  created:
    - src/paper/shadow.py
    - src/paper/exits.py
    - tests/test_shadow_mode.py
    - tests/test_exit_monitor.py
    - tests/test_paper_engine_lifecycle.py
  modified:
    - src/paper/engine.py
    - src/discord_bot/cog_scheduler.py
    - tests/test_paper_engine.py

key-decisions:
  - "Exit checks in priority order: expiration > profit_target > stop_loss > dte_exit > time_stop"
  - "Template caching in ExitMonitor to avoid repeated DB lookups"
  - "3rd Friday detection for AM-settled SPX monthly vs PM-settled SPXW"
  - "3:00 PM rule blocks new 0DTE positions after 15:00 ET"

patterns-established:
  - "Shadow mode: scan PAPER strategies, check schedule/conditions/limits, select strikes by delta, auto-submit"
  - "Settlement detection: 3rd Friday = AM-settled (close Thursday EOD), all others = PM-settled (close 16:00 ET)"
  - "Scheduler paper hooks: premarket start_of_day, intraday tick(), postmarket settlement+snapshot"

issues-created: []

# Metrics
duration: 16min
completed: 2026-02-24
---

# Phase 4 Plan 4: Shadow Mode & Exit Monitor Summary

**ShadowModeManager auto-generates paper trades from PAPER strategies with delta-based strike selection; ExitMonitor handles 5 exit conditions plus AM/PM settlement; full tick cycle wired into engine and scheduler**

## Performance

- **Duration:** 16 min
- **Started:** 2026-02-24T05:41:54Z
- **Completed:** 2026-02-24T05:58:15Z
- **Tasks:** 5
- **Files modified:** 8 (3 source created + 2 source modified + 3 test files)

## Accomplishments
- ShadowModeManager scans PAPER strategies, checks schedule/conditions/position limits, selects strikes by delta, auto-submits orders
- ExitMonitor checks 5 exit conditions in priority order (expiration, profit target, stop loss, DTE exit, time stop)
- AM/PM settlement handling: 3rd Friday detection for AM-settled SPX monthly, all others PM-settled SPXW
- 3:00 PM rule blocks new 0DTE positions after 15:00 ET
- Full 8-step tick cycle in PaperTradingEngine: entry signals → expire stale → fill pending → open positions → mark-to-market → check exits → submit close orders → return result
- Scheduler wired: premarket `start_of_day()`, intraday `tick(chains)`, postmarket settlement + daily snapshot

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ShadowModeManager** - `67782f5` (feat)
2. **Task 2: Create ExitMonitor** - `69db574` (feat)
3. **Task 3: Wire into PaperTradingEngine** - `0908c2f` (feat)
4. **Task 4: Wire into scheduler** - `f51bfd7` (feat)
5. **Task 5: Write tests (56 new)** - `d8cbc9f` (test)

**Plan metadata:** (this commit)

## Files Created/Modified
- `src/paper/shadow.py` — ShadowModeManager: check_entry_signals(), select_strikes(), schedule filtering, position limits, 3PM rule, daily state reset
- `src/paper/exits.py` — ExitMonitor: check_all_positions(), handle_settlements(), AM/PM detection, template caching, is_0dte_blocked()
- `src/paper/engine.py` — Wired ShadowModeManager + ExitMonitor into tick(), handle_eod_settlement(), start_of_day()
- `src/discord_bot/cog_scheduler.py` — Paper engine hooks in _run_full_cycle(), _handle_premarket(), _handle_postmarket()
- `tests/test_shadow_mode.py` — 20 tests: strike selection, entry signals, schedule, position limits, 3PM rule
- `tests/test_exit_monitor.py` — 21 tests: settlement types, profit/stop/DTE/time exits, AM/PM settlement handling
- `tests/test_paper_engine_lifecycle.py` — 15 tests: full lifecycle, start_of_day, tick counter, EOD settlement, multi-strategy
- `tests/test_paper_engine.py` — Fixed hardcoded past expiry dates to dynamic future dates

## Decisions Made
- Exit conditions checked in priority order: expiration > profit_target > stop_loss > dte_exit > time_stop
- Template caching in ExitMonitor avoids repeated DB lookups per position
- 3rd Friday of month = AM-settled SPX monthly (close Thursday EOD), all other Fridays = PM-settled SPXW (close 16:00 ET)
- 3:00 PM rule: block new 0DTE positions after 15:00 ET to avoid end-of-day execution risk

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed hardcoded past expiry dates in test_paper_engine.py**
- **Found during:** Task 5 (Write tests)
- **Issue:** Existing tests used `date(2025, 3, 21)` which is now in the past, causing ExitMonitor to auto-close positions as expired
- **Fix:** Replaced with `date.today() + timedelta(days=30)` for time-proof tests
- **Files modified:** tests/test_paper_engine.py
- **Verification:** All existing engine tests pass
- **Committed in:** d8cbc9f (part of Task 5 commit)

**2. [Rule 1 - Bug] Fixed sum() returning int instead of float for empty positions**
- **Found during:** Task 3 (Wire into PaperTradingEngine)
- **Issue:** `sum([])` returns `0` (int), but `total_unrealized_pnl` should be `float`
- **Fix:** Changed to `sum(..., 0.0)` to guarantee float return type
- **Files modified:** src/paper/engine.py
- **Committed in:** 0908c2f (part of Task 3 commit)

---

**Total deviations:** 2 auto-fixed (both bugs), 0 deferred
**Impact on plan:** Minimal — test data fix and type correctness. No scope creep.

## Issues Encountered
None — all 5 tasks completed without blocking issues.

## Next Phase Readiness
- Shadow mode and exit monitoring fully operational
- Paper trading engine now has complete entry→track→exit lifecycle
- Scheduler integration enables autonomous paper trading during market hours
- Ready for 4-5 (Portfolio Risk Management)

---
*Phase: 04-paper-trading-validation*
*Completed: 2026-02-24*
