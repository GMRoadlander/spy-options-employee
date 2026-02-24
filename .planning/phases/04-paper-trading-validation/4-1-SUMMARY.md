---
phase: 04-paper-trading-validation
plan: 01
subsystem: ml, security, data
tags: [feature-store, polygon, ssrf, pickle-security, torch-security, hmac, hurst, volatility, regime, sentiment, websocket]

# Dependency graph
requires:
  - phase: 03-ml-intelligence-layer
    provides: ML models (HMM, LSTM, FinBERT, Anomaly) with bugs from rapid development
provides:
  - Bug-free ML feature store with proper UPSERT (no column clobber)
  - Secure Polygon pagination (SSRF-safe)
  - Secure model serialization (HMAC-verified pickle, weights_only torch)
  - Complete regime/sentiment/vol manager outputs
  - WebSocket reconnection for Polygon OPRA
  - Sanitized Discord error messages
affects: [04-paper-trading-validation, ml-pipeline-reliability]

# Tech tracking
tech-stack:
  added: [hmac, hashlib]
  patterns: [ON CONFLICT partial UPSERT, HMAC file integrity, sidecar metadata JSON, WebSocket reconnect loop]

key-files:
  created: []
  modified:
    - src/ml/feature_store.py
    - src/data/polygon_client.py
    - src/discord_bot/cog_strategy.py
    - src/ml/regime.py
    - src/ml/sentiment.py
    - src/ml/volatility.py
    - src/discord_bot/cog_scheduler.py
    - src/ml/anomaly.py
    - src/ml/features.py
    - src/bot.py
    - .gitignore

key-decisions:
  - "HMAC-SHA256 for pickle integrity instead of signing library (stdlib only)"
  - "Sidecar .meta.json for torch model hyperparams instead of pickle in checkpoint"
  - "ON CONFLICT partial UPDATE for FeatureStore instead of full row replace"
  - "16:10 ET for ML update to avoid scheduler collision with 16:05 post-market"

patterns-established:
  - "Partial UPSERT: only update non-None columns on conflict"
  - "HMAC file integrity: secret-keyed hash verification before deserializing"
  - "Sidecar metadata: .meta.json alongside binary model files"
  - "WebSocket reconnect: exponential backoff with max_reconnects parameter"

issues-created: []

# Metrics
duration: 14min
completed: 2026-02-24
---

# Phase 4 Plan 1: Phase 3 Bug Fixes Summary

**Fixed 6 critical + 6 should-fix Phase 3 bugs across 11 source files — SSRF, info leakage, column clobber, pickle/torch security, missing ML fields, scheduler collision, dark pool math, Hurst stability, WebSocket reconnect, bot cleanup**

## Performance

- **Duration:** 14 min
- **Started:** 2026-02-24T04:48:14Z
- **Completed:** 2026-02-24T05:02:46Z
- **Tasks:** 9 steps completed
- **Files modified:** 18 (11 source + 7 test)

## Accomplishments
- FeatureStore UPSERT now preserves columns from other managers (critical data integrity fix)
- Polygon pagination SSRF-safe with BASE_URL domain validation
- Discord error messages sanitized — no internal info leakage
- RegimeManager/SentimentManager/VolForecaster return complete data after updates
- ML scheduler staggered to 16:10 ET (avoids 16:05 post-market collision)
- Dark pool ratio uses correct denominator, Hurst exponent uses stable single-loop
- Model serialization hardened: HMAC-verified pickle, weights_only torch.load with .meta.json sidecar
- WebSocket OPRA reconnect with exponential backoff
- Bot cleanup closes ML HTTP clients on shutdown
- .gitignore blocks ML model artifacts

## Task Commits

Each task was committed atomically:

1. **Step 1: .gitignore cleanup** - `11333a7` (chore)
2. **Step 2: FeatureStore UPSERT fix** - `ee7b001` (fix)
3. **Step 3: Polygon SSRF fix** - `32b2152` (security)
4. **Step 4: Error info leakage fix** - `82208a6` (security)
5. **Step 5: RegimeManager missing fields** - `8ba662c` (fix)
6. **Step 6: SentimentManager missing fields** - `482237e` (fix)
7. **Step 7: VolForecaster._stats fix** - `dff5ebb` (fix)
8. **Step 8: Scheduler timing fix** - `9286f9d` (fix)
9. **Step 9: Remaining SHOULD-FIX bugs** - `1cca06a` (fix) — dark pool ratio, Hurst exponent, bot cleanup, WebSocket reconnect, torch.load security, pickle security

**Plan metadata:** (this commit)

## Files Created/Modified
- `.gitignore` — ML model artifact patterns added
- `src/ml/feature_store.py` — ON CONFLICT partial UPSERT replacing INSERT OR REPLACE
- `src/data/polygon_client.py` — SSRF domain validation + WebSocket reconnect loop
- `src/discord_bot/cog_strategy.py` — Generic error messages, server-side exc logging
- `src/ml/regime.py` — Cached prediction fields + HMAC pickle integrity
- `src/ml/sentiment.py` — Cached aggregate fields in get_current_sentiment()
- `src/ml/volatility.py` — stats param on train() + .pt/.meta.json save + weights_only load
- `src/discord_bot/cog_scheduler.py` — ML update 16:05 → 16:10 ET
- `src/ml/anomaly.py` — Dark pool ratio denominator fix + HMAC pickle integrity
- `src/ml/features.py` — Hurst exponent single-loop stability fix
- `src/bot.py` — Close ML HTTP clients (news, UW) in close()
- `tests/test_feature_store.py` — +3 tests (partial update, no overwrite, empty noop)
- `tests/test_polygon_client.py` — +2 tests (SSRF reject, valid accept)
- `tests/test_cog_strategy.py` — +2 tests (error leak prevention)
- `tests/test_regime.py` — +2 tests (cached prediction fields)
- `tests/test_sentiment.py` — +2 tests (cached aggregate fields)
- `tests/test_volatility.py` — +2 tests (stats param enable/disable predict)
- `tests/test_anomaly.py` — Updated mocks for total_volume denominator

## Decisions Made
- HMAC-SHA256 for pickle integrity (stdlib-only, no external signing library)
- Sidecar `.meta.json` for torch model hyperparams (avoids pickle for metadata)
- Partial UPSERT with ON CONFLICT for FeatureStore (only update provided columns)
- ML update timing at 16:10 ET (5 min after post-market, avoids collision)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated anomaly test mocks for total_volume**
- **Found during:** Step 9.1 (dark pool ratio fix)
- **Issue:** Test mocks didn't include `total_volume` field needed by new denominator logic
- **Fix:** Added `total_volume` to mock UW summary in test fixtures
- **Files modified:** tests/test_anomaly.py
- **Verification:** All anomaly tests pass
- **Committed in:** 1cca06a (part of Step 9 commit)

---

**Total deviations:** 1 auto-fixed (blocking test mock), 0 deferred
**Impact on plan:** Minimal — test data update required to match source fix.

## Issues Encountered
None — all 9 steps completed without blocking issues.

## Next Phase Readiness
- All Phase 3 bugs fixed — clean foundation for Phase 4 paper trading engine
- 900 tests passing (+13 new from bug fix verification)
- ML pipeline outputs complete (regime, sentiment, vol all return full fields)
- Model serialization secure (HMAC pickle, weights_only torch)
- Ready for 4-2 (Paper Trading Engine Core)

---
*Phase: 04-paper-trading-validation*
*Completed: 2026-02-24*
