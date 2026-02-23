---
phase: 03-ml-intelligence-layer
plan: "09"
subsystem: discord, integration
tags: [discord-cog, slash-commands, ml-scheduling, bot-integration, graceful-degradation]

# Dependency graph
requires:
  - phase: 03-01
    provides: FeatureStore for ML data persistence
  - phase: 03-02
    provides: RegimeManager for /regime command
  - phase: 03-03
    provides: VolManager for /forecast command
  - phase: 03-04
    provides: SentimentManager for /sentiment command
  - phase: 03-05
    provides: AnomalyManager for /anomalies command
  - phase: 03-06
    provides: PolygonClient for flow data and news
  - phase: 03-07
    provides: UnusualWhalesClient and FlowAnalyzer for flow integration
  - phase: 03-08
    provides: ReasoningEngine for /reasoning command, LearningManager for /ml_health
provides:
  - MLInsightsCog with 6 slash commands (/regime, /forecast, /sentiment, /anomalies, /reasoning, /ml_health)
  - 6 ML embed builders for rich Discord visualization
  - Regime timeline chart (color-coded horizontal bar)
  - Daily ML pipeline scheduling (16:05 ET features, 16:30 ET reasoning briefing)
  - Bot-level ML component initialization with graceful degradation
  - Complete Phase 3 ML Intelligence Layer integration
affects: [phase-4, phase-5]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Graceful degradation: each ML component optional, bot runs without any"
    - "ML scheduling at market close: features at 16:05 ET, reasoning at 16:30 ET"
    - "5-minute cooldown on /reasoning to control Claude API costs (~$0.01-0.03/call)"
    - "Per-component error isolation in both bot init and scheduler"

key-files:
  created:
    - src/discord_bot/cog_ml.py
    - tests/test_cog_ml.py
    - .env.template
  modified:
    - src/discord_bot/embeds.py
    - src/discord_bot/charts.py
    - src/bot.py
    - src/discord_bot/cog_scheduler.py
    - docker-compose.yml

key-decisions:
  - "Each ML component initialized independently with try/except — bot runs without any"
  - "ML daily update at 16:05 ET (after post-market), reasoning briefing at 16:30 ET"
  - "5-minute cooldown on /reasoning to control API costs"
  - "Contrarian signal detection: |sentiment| > 0.6 AND PCR > 1.2"
  - "Color-coded regime states: green=risk-on, yellow=risk-off, red=crisis"

patterns-established:
  - "ML cog pattern: manager-based commands with None-check graceful fallback"
  - "Scheduled ML pipeline: sequential feature→regime→vol→sentiment→anomaly→reasoning"

issues-created: []

# Metrics
duration: 17min
completed: 2026-02-23
---

# Phase 3 Plan 9: Discord ML Cog + Full Integration Summary

**MLInsightsCog with 6 slash commands, daily ML pipeline scheduling, and full Phase 3 integration with graceful degradation for all 8 ML components**

## Performance

- **Duration:** 17 min
- **Started:** 2026-02-23T05:28:52Z
- **Completed:** 2026-02-23T05:45:59Z
- **Tasks:** 2 auto + 1 checkpoint
- **Files created:** 3
- **Files modified:** 5

## Accomplishments
- MLInsightsCog with 6 slash commands: /regime, /forecast, /sentiment, /anomalies, /reasoning (5-min cooldown), /ml_health
- 6 ML embed builders with color-coded regime states, contrarian signal detection, and anomaly severity coloring
- Regime timeline chart (matplotlib horizontal bar, color-coded risk-on/risk-off/crisis)
- Bot setup_hook initializes 8 ML components with per-component error isolation
- Daily ML pipeline: features at 16:05 ET → regime → vol → sentiment → anomaly → calibration, then reasoning briefing at 16:30 ET
- .env.template documenting all Phase 1-3 environment variables
- Docker scaling notes: s-2vcpu-8gb recommended (~2GB for bot + ML models)
- 887 total tests passing (47 new from test_cog_ml.py)

## Task Commits

Each task was committed atomically:

1. **Task 1: Discord ML insights cog with slash commands** — `d4c404b` (feat)
2. **Task 2: Bot integration, ML scheduling, and full verification** — `68272e6` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified
- `src/discord_bot/cog_ml.py` — MLInsightsCog with 6 slash commands, manager-based architecture
- `tests/test_cog_ml.py` — 47 tests covering commands, embeds, charts, edge cases
- `.env.template` — All Phase 1-3 environment variables documented
- `src/discord_bot/embeds.py` — Added 6 ML embed builders (regime, forecast, sentiment, anomaly, reasoning, ml_health)
- `src/discord_bot/charts.py` — Added create_regime_timeline_chart (color-coded horizontal bar)
- `src/bot.py` — Added _init_ml_components() with 8 manager attributes and graceful degradation
- `src/discord_bot/cog_scheduler.py` — Added ml_daily_update (16:05 ET) and ml_reasoning_briefing (16:30 ET)
- `docker-compose.yml` — Phase 3 scaling notes (s-2vcpu-8gb, ~2GB memory estimate)

## Decisions Made
- Each ML component initialized independently with try/except — bot runs fully without any ML components
- Daily ML update at 16:05 ET (5 min after post-market to ensure data is available), reasoning briefing at 16:30 ET
- 5-minute cooldown on /reasoning to control Claude API costs (~$0.01-0.03 per invocation)
- Contrarian signal detection in /sentiment: |sentiment| > 0.6 AND PCR > 1.2 triggers flag
- Color-coded regime states across embeds and charts: green=risk-on, yellow=risk-off, red=crisis

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- **Phase 3: ML Intelligence Layer COMPLETE** (9/9 plans)
- All ML components built, tested, and wired into Discord
- Daily ML pipeline runs automatically at market close
- Borey can query all ML insights via Discord slash commands
- Bot runs with or without ML components (graceful degradation)
- Ready for **Phase 4: Paper Trading & Validation**

---
*Phase: 03-ml-intelligence-layer*
*Completed: 2026-02-23*
