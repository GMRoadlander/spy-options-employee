---
phase: 02-strategy-research-engine
plan: "03"
subsystem: discord, ai, strategy
tags: [discord.py, claude-sonnet, yaml, matplotlib, hypothesis-testing, trade-journal]

# Dependency graph
requires:
  - phase: 02-strategy-research-engine (plan 01)
    provides: strategy templates, lifecycle state machine, signal logging
  - phase: 02-strategy-research-engine (plan 02)
    provides: backtesting engine, evaluation pipeline, anti-overfitting gates
provides:
  - Natural language → YAML strategy parser via Claude Sonnet
  - Discord slash commands for strategy CRUD + backtesting
  - Hypothesis testing framework (propose → test → confirm/reject)
  - Trade journal with auto daily/weekly summaries
  - Strategy performance reporting with charts
  - Full bot integration wiring
affects: [phase-3-ml-intelligence, phase-4-paper-trading, phase-5-autonomous-trading]

# Tech tracking
tech-stack:
  added: [matplotlib (charts)]
  patterns: [NL→YAML parsing via LLM, hypothesis-driven research workflow, auto-posting background tasks]

key-files:
  created:
    - src/ai/strategy_parser.py
    - src/discord_bot/cog_strategy.py
    - src/discord_bot/cog_journal.py
    - src/discord_bot/reporting.py
    - src/strategy/hypothesis.py
    - tests/test_strategy_parser.py
    - tests/test_cog_strategy.py
    - tests/test_hypothesis.py
    - tests/test_cog_journal.py
    - tests/test_reporting.py
  modified:
    - src/discord_bot/embeds.py
    - src/discord_bot/charts.py
    - src/bot.py
    - src/db/store.py
    - src/config.py
    - .env.template
    - docker-compose.yml

key-decisions:
  - "Claude Sonnet for NL→YAML parsing — same model as commentary, proven pattern"
  - "DSR as p-value proxy for hypothesis evaluation — reuses anti-overfitting pipeline"
  - "Background tasks for auto-posting journal summaries at fixed times (4:30 PM ET daily, Monday 10 AM ET weekly)"

patterns-established:
  - "NL→structured data: LLM parses free text → validate against schema → confirm with user"
  - "Hypothesis-driven research: propose → link strategies → backtest → evaluate → confirm/reject"
  - "Auto-posting cog pattern: discord.ext.tasks.loop with timezone-aware scheduling"

issues-created: []

# Metrics
duration: 15min
completed: 2026-02-22
---

# Phase 2 Plan 3: Discord Research Interface + Strategy Automation Summary

**NL→YAML strategy parser via Claude Sonnet, Discord cogs for strategy CRUD/backtesting/journal, hypothesis testing framework, and performance reporting with equity curve and Monte Carlo charts**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-22T05:15:03Z
- **Completed:** 2026-02-22T05:29:50Z
- **Tasks:** 7
- **Files modified:** 17

## Accomplishments

- Borey can define strategies in plain English — Claude Sonnet parses NL descriptions into validated YAML templates
- Full Discord slash command suite: `/strategy_define`, `/strategy_list`, `/strategy_show`, `/strategy_edit`, `/strategy_retire`, `/backtest`, `/backtest_results`
- Hypothesis testing framework for structured research (propose → test → confirm/reject with statistical significance)
- Trade journal with auto-posting: daily summaries at 4:30 PM ET, weekly reviews Monday 10 AM ET, signal ratings 1-5 stars
- Strategy performance reporting with equity curves, Monte Carlo fan charts, WFA window charts, and strategy comparison radar charts
- All new components wired into bot with DB tables for hypotheses, journal entries, and signal ratings

## Task Commits

Each task was committed atomically:

1. **Task 1: Natural language strategy parser** - `90a10a6` (feat)
2. **Task 2: Strategy management cog** - `ca3390e` (feat)
3. **Task 3: Hypothesis testing framework** - `cf20646` (feat)
4. **Task 4: Trade journal system** - `421c879` (feat)
5. **Task 5: Strategy performance reporting** - `9ca3f62` (feat)
6. **Task 6: Wire cogs + bot integration** - `e059cf0` (feat)
7. **Task 7: Full integration test + scaling docs** - `2d3f0c9` (chore)

## Files Created/Modified

**Created (10):**
- `src/ai/strategy_parser.py` — NL→YAML strategy parser using Claude Sonnet
- `src/discord_bot/cog_strategy.py` — Discord slash commands for strategy CRUD + backtesting
- `src/discord_bot/cog_journal.py` — Trade journal with daily/weekly auto-posting
- `src/discord_bot/reporting.py` — Monthly reports, strategy comparison, signal accuracy
- `src/strategy/hypothesis.py` — Hypothesis dataclass, manager, and status workflow
- `tests/test_strategy_parser.py` — 11 tests
- `tests/test_cog_strategy.py` — 13 tests
- `tests/test_hypothesis.py` — 13 tests
- `tests/test_cog_journal.py` — 12 tests
- `tests/test_reporting.py` — 15 tests

**Modified (7):**
- `src/discord_bot/embeds.py` — 8 new embed builders (strategy define/list/detail, backtest result/progress, daily/weekly/rating)
- `src/discord_bot/charts.py` — 4 new chart functions (equity curve, MC fan, WFA windows, strategy comparison)
- `src/bot.py` — strategy_parser + hypothesis_manager init, new cog loading
- `src/db/store.py` — hypotheses, hypothesis_strategies, journal_entries, signal_ratings tables
- `src/config.py` — journal_channel_id, monthly_report_day settings
- `.env.template` — DISCORD_JOURNAL_CHANNEL_ID, MONTHLY_REPORT_DAY vars
- `docker-compose.yml` — Phase 2 scaling notes (s-2vcpu-4gb)

## Decisions Made

- Claude Sonnet for NL→YAML parsing — consistent with existing commentary pattern, proven reliable
- DSR as p-value proxy for hypothesis evaluation — reuses anti-overfitting pipeline results rather than introducing new statistical tests
- Background tasks for auto-posting at fixed Eastern Time — simple scheduling, timezone-aware

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed async fixtures for pytest-asyncio strict mode**
- **Found during:** Task 3 (Hypothesis testing framework)
- **Issue:** Tests used `@pytest.fixture` for async fixtures instead of `@pytest_asyncio.fixture`, causing failures in strict mode
- **Fix:** Changed to `@pytest_asyncio.fixture` matching existing test_strategy_lifecycle.py pattern
- **Committed in:** `cf20646` (part of Task 3 commit)

**2. [Rule 1 - Bug] Fixed test_parse_no_api_key picking up real API key**
- **Found during:** Task 1 (Strategy parser)
- **Issue:** Tests expecting "no API key" error were picking up real `CLAUDE_API_KEY` from .env via config defaults
- **Fix:** Tests now explicitly clear `_api_key` attribute after construction
- **Committed in:** `90a10a6` (part of Task 1 commit)

**3. [Rule 3 - Blocking] Installed matplotlib**
- **Found during:** Task 5 (Reporting/charts)
- **Issue:** matplotlib listed in requirements.txt but not installed in test environment
- **Fix:** Installed matplotlib
- **Committed in:** N/A (pip install, not a code change)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocker), 0 deferred
**Impact on plan:** All auto-fixes necessary for test correctness. No scope creep.

## Issues Encountered

None — all tasks executed smoothly.

## Next Phase Readiness

- Phase 2 Strategy Research Engine is fully complete (3/3 plans)
- Borey has full Discord interface: define strategies in plain English, run backtests, track hypotheses, review daily/weekly journals
- 450 tests passing (386 existing + 64 new, no regressions)
- Ready for Phase 3: ML Intelligence Layer

---
*Phase: 02-strategy-research-engine*
*Completed: 2026-02-22*
