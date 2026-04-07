# SpotGamma Integration — Implementation Plan

## Strategy

**Network interception, not DOM scraping.** SpotGamma's dashboard is a JavaScript SPA that makes fetch/XHR calls returning structured JSON. We intercept those API calls, then call them directly with aiohttp. Playwright is the auth broker and fallback scraper only.

### Three-layer approach:
1. **Playwright auth broker** — Logs into SpotGamma, extracts auth token (JWT/cookie)
2. **Direct aiohttp API client** — Calls SpotGamma's internal API endpoints with the auth token
3. **Fallback: Playwright page scraping** — If specific endpoints resist direct calls

### Data extraction schedule:
| Product | Frequency | Requests/Day |
|---------|-----------|-------------|
| Key Levels (Call Wall, Put Wall, Vol Trigger, Hedge Wall, Abs Gamma) | Pre-market + every 30 min | ~15 |
| HIRO (hedging impact) | Every 5 min during market hours | ~78 |
| TRACE (S&P heatmap data) | Every 15 min | ~26 |
| Equity Hub (SPX/SPY levels) | Once daily | ~2 |
| Founder's Notes | 2x daily | ~2 |
| **Total** | | **~123/day** |

---

## PRE-SUBSCRIPTION PHASE (Build April 6-26)

### STEP 0: Webhook HMAC Security Fix [0.5 day]

**Problem**: `src/webhook/tradingview.py` line 55 uses shared-secret comparison, not HMAC body signing. Replay attacks possible.

**Files to modify**:
- `src/webhook/tradingview.py` — Change to HMAC-SHA256 of raw request body. Expect `X-Webhook-Signature` header.
- `tests/test_webhook_tradingview.py` — Test valid/invalid/missing signatures

**Dependencies**: None. First step.
**Effort**: 2-3 hours

---

### STEP 1: SpotGamma Data Models and DB Schema [0.5 day]

**Files to create**:
- `src/data/spotgamma_models.py` — Pure dataclasses:
  - `SpotGammaLevels` (call_wall, put_wall, vol_trigger, hedge_wall, abs_gamma, timestamp, source)
  - `SpotGammaHIRO` (timestamp, hedging_impact, cumulative_impact, delta_adjusted, source)
  - `SpotGammaNote` (timestamp, summary, key_levels_mentioned, market_outlook, raw_text)

**Files to modify**:
- `src/db/store.py` — Add migrations for 3 new tables: `spotgamma_levels`, `spotgamma_hiro`, `spotgamma_notes`

**Dependencies**: None
**Tests**: `tests/test_spotgamma_models.py`, `tests/test_spotgamma_store.py`
**Effort**: 3-4 hours

---

### STEP 2: SpotGamma Level Store (Repository Layer) [0.5 day]

**Files to create**:
- `src/data/spotgamma_store.py` — CRUD async operations following FeatureStore pattern:
  - `save_levels()` / `get_latest_levels()` / `get_levels_history()`
  - `save_hiro()` / `get_hiro_since()` / `get_latest_hiro()`
  - `save_note()` / `get_latest_note()`
  - `cleanup_old_hiro()` — HIRO accumulates fast

**Dependencies**: Step 1
**Tests**: `tests/test_spotgamma_store.py` — Full CRUD with in-memory SQLite
**Effort**: 3-4 hours

---

### STEP 3: SpotGamma Auth Broker (Playwright) [1 day]

**Files to create**:
- `src/data/spotgamma_auth.py` — Playwright-based authentication:
  - `SpotGammaAuthBroker` class
  - `authenticate()` → returns headers dict with auth token
  - `refresh_if_needed()` → checks token freshness
  - Uses `playwright-stealth` plugin
  - Persistent browser context (saves cookies to `data/spotgamma_auth/`)
  - Credentials from env: `SPOTGAMMA_EMAIL`, `SPOTGAMMA_PASSWORD`

**Config additions** (`src/config.py`):
- `spotgamma_email`, `spotgamma_password`, `spotgamma_enabled`, `spotgamma_auth_dir`

**New dependencies**: `playwright>=1.40`, `playwright-stealth>=1.0`

**Dependencies**: None (parallel with Steps 1-2)
**Tests**: `tests/test_spotgamma_auth.py` — Mock Playwright, no real browser
**Effort**: 6-8 hours

---

### STEP 4: SpotGamma API Client (aiohttp) [1 day]

**Files to create**:
- `src/data/spotgamma_client.py` — Direct HTTP client following PolygonClient/UnusualWhalesClient pattern:
  - Lazy aiohttp session, rate limiting (max 10 req/min)
  - Custom errors: `SpotGammaAuthError`, `SpotGammaRateLimitError`
  - Skeleton methods: `get_levels()`, `get_hiro()`, `get_equity_hub()`, `get_trace()`
  - Anti-detection: randomized jitter (0-30s), human-like User-Agent
  - Base URL placeholder: `https://dashboard.spotgamma.com/api` (refined Day 1)

**Dependencies**: Step 3 (for auth headers)
**Tests**: `tests/test_spotgamma_client.py` — Mock HTTP, rate limiting, auth errors, graceful degradation
**Effort**: 6-8 hours

---

### STEP 5: SpotGamma Playwright Fallback Scraper [0.5 day]

**Files to create**:
- `src/data/spotgamma_scraper.py` — Playwright page scraping fallback:
  - Methods mirror `SpotGammaClient`: `get_levels()`, `get_hiro()`
  - Uses auth broker's browser context
  - Caches results with TTL to minimize page loads
  - Only used if direct API calls fail

**Dependencies**: Step 3
**Tests**: `tests/test_spotgamma_scraper.py` — Mock Playwright page interactions
**Effort**: 4 hours

---

### STEP 6: SpotGamma Discord Cog [1 day]

**Files to create**:
- `src/discord_bot/cog_spotgamma.py` — Slash commands:
  - `/spotgamma set <levels>` — Borey manual input (highest-ROI path)
  - `/spotgamma show` — Display current SpotGamma levels alongside DIY levels
  - `/spotgamma compare` — Side-by-side: gamma_flip vs vol_trigger, gamma_ceiling vs call_wall
  - `/spotgamma hiro` — Current HIRO with chart
  - `/spotgamma notes` — Latest founder's notes summary
  - `/spotgamma status` — Auth status, data freshness
  - Conditional loading (`if not config.spotgamma_enabled: return`)

**Embed/chart additions**:
- `src/discord_bot/embeds.py` — `build_spotgamma_levels_embed()`, `build_spotgamma_hiro_embed()`, `build_spotgamma_comparison_embed()`
- `src/discord_bot/charts.py` — `create_hiro_chart()`, `create_levels_comparison_chart()`

**Dependencies**: Steps 1, 2
**Tests**: `tests/test_cog_spotgamma.py`, `tests/test_spotgamma_embeds.py`, `tests/test_spotgamma_charts.py`
**Effort**: 6-8 hours

---

### STEP 7: ServiceRegistry + Bot Wiring [0.5 day]

**Files to modify**:
- `src/services.py` — Add `spotgamma_store`, `spotgamma_client`, `spotgamma_auth` (all Optional, None default)
- `src/bot.py` — Add `_init_spotgamma()` following `_init_ml_components()` pattern. Conditional on `config.spotgamma_enabled`. Add cog to extensions list. Add cleanup in `close()`.

**Dependencies**: Steps 1-6
**Tests**: Existing bot tests pass. Test init with SpotGamma disabled (no-op) and enabled without credentials (graceful degradation)
**Effort**: 3-4 hours

---

### STEP 8: Scheduler Integration [0.5 day]

**Files to modify**:
- `src/discord_bot/cog_scheduler.py` — Add SpotGamma polling:
  - 8:00 AM ET: Auth broker login
  - 9:15 AM ET: Fetch levels (pre-market)
  - Every 30 min: Refresh levels
  - Every 5 min: Poll HIRO (if endpoint found)
  - 4:10 PM ET: Inject SpotGamma features into daily_features
  - Jitter helper: `_jitter(base_seconds, max_jitter=30)`

**Dependencies**: Steps 4, 6, 7
**Tests**: Scheduling logic with mocked time, graceful skip when service unavailable
**Effort**: 4 hours

---

### STEP 9: Multi-Expiry GEX Upgrade [1 day]

**Files to modify**:
- `src/analysis/gex.py` — `calculate_gex()` aggregates across ALL expirations weighted by notional gamma when `expiry=None`. New `gex_by_expiry` field on `GEXResult` showing per-expiry contribution.

**Dependencies**: None (parallel with all other steps)
**Tests**: 8-10 new tests in `tests/test_gex.py` with multi-expiry chains
**Effort**: 6-8 hours

---

### STEP 10: DIY HIRO Indicator [1.5 days]

**Files to create**:
- `src/analysis/hiro.py` — `DIYHIROCalculator`:
  1. Classify trades as buyer/seller-initiated (trade vs quote comparison)
  2. Compute delta-weighted volume per trade
  3. Infer dealer hedging direction
  4. Aggregate into cumulative hedging impact over rolling window
  - Output: `DIYHIROResult(hedging_impact, cumulative, call_pressure, put_pressure)`
  - Uses `PolygonOptionsStream` WebSocket for real-time, REST for backfill

**Files to modify**:
- `src/ml/anomaly.py` — Add HIRO to `FlowAnalyzer.get_flow_summary()`
- `src/discord_bot/embeds.py` — `build_diy_hiro_embed()`

**Dependencies**: Polygon client (existing)
**Tests**: `tests/test_hiro.py` — 15-20 tests with synthetic trade sequences
**Effort**: 10-12 hours

---

### STEP 11: Signal Reconciliation Engine [0.5 day]

**Files to create**:
- `src/analysis/reconciliation.py` — Compare conflicting signals:
  - `reconcile_levels(sg_levels, our_gex)` — vol_trigger vs gamma_flip, call_wall vs gamma_ceiling, etc.
  - `reconcile_hiro(sg_hiro, diy_hiro)` — direction agreement, correlation
  - Output: `ReconciliationResult(agreements, conflicts, confidence_adjustment)`

**Dependencies**: Steps 1, 10
**Tests**: `tests/test_reconciliation.py` — 10-12 tests
**Effort**: 4 hours

---

### STEP 12: Feature Store Integration [0.5 day]

**Files to modify**:
- `src/ml/feature_store.py` — Add columns: `sg_vol_trigger`, `sg_call_wall`, `sg_put_wall`, `sg_abs_gamma`, `sg_hiro_eod`, `diy_hiro_eod`, `gex_sg_agreement`
- `src/db/store.py` — Migration: ALTER TABLE daily_features ADD COLUMN for each

**Dependencies**: Steps 1, 2, 10
**Tests**: Extend `tests/test_feature_store.py`
**Effort**: 3-4 hours

---

### STEP 13: Integration Testing [0.5 day]

**Files to create**:
- `tests/test_spotgamma_integration.py` — End-to-end: manual input → store → compare with GEX → reconciliation → feature store → Discord embed. All external calls mocked.

**Dependencies**: All previous steps
**Tests**: 8-10 integration tests
**Effort**: 4 hours

---

## DAY-1 PHASE (April 27 — First Day of Subscription)

### STEP D1: Network Reconnaissance [2-4 hours]

1. Log into SpotGamma dashboard in Chrome
2. DevTools → Network tab → filter XHR/Fetch
3. Navigate: Key Levels, HIRO, Equity Hub, TRACE, Founder's Notes
4. Document every endpoint: URL, method, headers, auth, response schema
5. Check `dashboard.spotgamma.com/docs/api/` for Swagger docs
6. Test endpoints with curl using extracted auth token
7. Output: `docs/spotgamma_endpoints.md` + sample JSON for test fixtures

### STEP D2: Wire Real Endpoints [4-6 hours]

- `src/data/spotgamma_client.py` — Replace placeholder endpoints
- `src/data/spotgamma_auth.py` — Adjust auth extraction for actual mechanism
- `src/data/spotgamma_models.py` — Adjust fields to match real schema

### STEP D3: Live Integration Test [2-4 hours]

1. Run auth broker → verify login
2. Call each endpoint → verify data
3. Run full scheduler cycle
4. Verify Discord output
5. Run full test suite → all pass

---

## WEEK-1 PHASE (April 28 - May 2 — Stabilization)

### STEP W1: Polling Frequency Tuning [0.5 day]
Adjust intervals based on real API behavior and rate limits.

### STEP W2: Conflicting Signal Display [0.5 day]
Color-coded agreement/conflict indicators in Discord embeds.

### STEP W3: Edge Case Handling [0.5 day]
Market holidays, pre/after-hours, SpotGamma maintenance, token expiry mid-day.

### STEP W4: Borey Training [0.5 day]
Walk through commands, document in `docs/spotgamma_guide.md`.

---

## EFFORT SUMMARY

| Phase | Steps | Effort |
|-------|-------|--------|
| Security Fix | 0 | 0.5 day |
| Core Infrastructure | 1-8 | 5 days |
| GEX Upgrade + DIY HIRO | 9-10 | 2.5 days |
| Reconciliation + Integration | 11-13 | 1.5 days |
| Day-1 (Recon + Wiring) | D1-D3 | 1 day |
| Week-1 (Stabilization) | W1-W4 | 2 days |
| **TOTAL** | | **~12.5 days** |

---

## DEPENDENCY GRAPH

```
Step 0 (Webhook Fix) ────────> independent, do first
Step 1 (Models) ──────> Step 2 (Store) ──────> Step 6 (Cog)
Step 3 (Auth) ────────> Step 4 (Client) ─────> Step 7 (Wiring) ──> Step 8 (Scheduler)
Step 3 (Auth) ────────> Step 5 (Scraper) ────> Step 7 (Wiring)
Step 9 (Multi-GEX) ──> independent, parallel
Step 10 (DIY HIRO) ──> depends on Polygon (existing)
Steps 1+10 ──────────> Step 11 (Reconciliation)
Steps 1+2+10 ────────> Step 12 (Feature Store)
All ──────────────────> Step 13 (Integration Tests)
All ──────────────────> Day-1 (D1-D3)
```

**Critical path**: Step 3 → Step 4 → Step 7 → Step 8

---

## RISK MITIGATIONS

1. **SpotGamma blocks API calls** → Fallback to Playwright scraping (Step 5) → Further fallback to Borey manual input (`/spotgamma set`)
2. **Auth token expires frequently** → Proactive refresh with 401 detection. Worst case: re-login via Playwright every 2 hours.
3. **No HIRO endpoint found** → DIY HIRO (Step 10) provides the signal independently.
4. **SpotGamma changes API schema** → Defensive `.get()` with defaults. Unknown fields logged but not fatal.
5. **Existing tests break** → All new tables are additive migrations. All services Optional. All cog loading conditional.
