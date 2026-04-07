# SpotGamma Integration Architecture Review

**Reviewer**: Boris Cherney (adversarial)
**Date**: 2026-04-06
**Codebase snapshot**: commit 48cd5f0 (master)
**Scope**: Pattern fit, data flow, ServiceRegistry impact, schema design, coupling risks

---

## 1. PATTERN FIT ANALYSIS

### 1.1 Existing Client Pattern

Every client in `src/data/` follows the same contract:

| File | Transport | Auth | Returns | Lifecycle |
|------|-----------|------|---------|-----------|
| `cboe_client.py` | HTTP GET (aiohttp) | None | `OptionsChain` | `close()` |
| `tastytrade_client.py` | HTTP (aiohttp, OAuth2) | Token | `OptionsChain` | `close()` |
| `tradier_client.py` | HTTP GET (aiohttp) | Bearer token | `OptionsChain` | `close()` |
| `orats_client.py` | HTTP GET (aiohttp) | API key | `OptionsChain` | `close()` |
| `polygon_client.py` | HTTP + WebSocket (aiohttp) | API key | Various dicts | `close()` |
| `news_client.py` | HTTP GET (aiohttp) | API key | `list[dict]` | `close()` |
| `unusual_whales_client.py` | HTTP GET (aiohttp) | Bearer token | `list[dict]` / `dict` | `close()` |

**There is no formal base class or Protocol.** The "pattern" is informal: lazy aiohttp session, rate limit tracking, `close()` method, and returning either `OptionsChain` or raw dicts. There is no abstract interface enforced.

### 1.2 SpotGamma Does NOT Fit This Pattern

SpotGamma has four proposed integration paths. None of them cleanly map to the existing client pattern:

**Path 1: Email parsing (Founder's Notes)**
- Transport: IMAP/SMTP, not HTTP. No existing client uses email.
- Data format: Unstructured prose with embedded levels, not JSON API responses.
- Cadence: Once daily (pre-market), not on-demand request/response.
- **Verdict: Fundamentally different.** You would need an entirely new transport layer (`imaplib` or `aiohttp` via a Gmail API). The parse logic is fragile NLP/regex, not JSON deserialization. This is the CheddarFlow embed parser problem (see `cog_cheddarflow.py` lines 20-131) but worse, because at least CheddarFlow embeds have semi-structured fields. An email is free-form prose.

**Path 2: TradingView webhook bridge**
- Transport: Inbound HTTP POST, not outbound HTTP GET.
- The existing webhook infrastructure (`src/webhook/app.py`, `src/webhook/tradingview.py`) receives TradingView alerts via a FastAPI endpoint.
- SpotGamma levels would need to be manually configured as TradingView alerts that fire when price crosses a level.
- **Verdict: Partially fits**, but this is not a "data client" -- it's an event source. The data doesn't come from SpotGamma directly; Borey or a Pine Script has to manually encode the levels into TradingView. This defeats the purpose of automation.

**Path 3: HIRO API (real-time hedging pressure)**
- Transport: HTTP REST or WebSocket (likely proprietary).
- Auth: SpotGamma Alpha subscription API key.
- Returns: Hedging impact data (structured JSON, presumably).
- **Verdict: Best pattern fit**, but SpotGamma's API documentation is thin/nonexistent for HIRO. You're building against an undocumented or semi-documented API. If they even expose one.

**Path 4: Manual Borey input via Discord**
- Transport: Discord message listener (like CheddarFlow).
- Data format: Borey types levels into a channel or uses a slash command.
- **Verdict: Fits the CheddarFlow pattern** (`cog_cheddarflow.py`), not the data client pattern. This is a Discord cog, not a data client.

### 1.3 Conclusion: You Need THREE Different Integration Patterns, Not One

A single `SpotGammaClient` class is architecturally dishonest. The four paths use fundamentally different transports, cadences, and data shapes. Attempting to unify them behind one class will produce a god object with `fetch_from_email()`, `receive_webhook()`, `poll_hiro_api()`, and `parse_discord_message()` methods -- each with completely different error modes.

**Recommendation: Separate concerns.**
- `src/data/spotgamma_client.py` -- HTTP REST client for HIRO API only (if it exists). Follows the existing aiohttp pattern.
- `src/discord_bot/cog_spotgamma.py` -- Discord cog for Borey manual input AND email-forwarded levels. Follows the CheddarFlow pattern.
- Webhook path is handled by extending the existing `src/webhook/tradingview.py` or adding a parallel `src/webhook/spotgamma.py` endpoint.

Do NOT create a data client for email parsing. That's a scheduled job, not a client.

---

## 2. DATA FLOW MAPPING

### 2.1 Path 1: Email Parsing

```
Founder's Notes email (6:30 AM ET)
    |
    v
[Email fetch job] -- new component, no precedent in codebase
    |
    v
[Parse unstructured text] -- regex/NLP extraction of key levels
    |                         (gamma flip, call wall, put wall, vol trigger)
    |
    v
[SpotGammaLevels dataclass] -- new data model
    |
    +---> [FeatureStore.save_features()] -- but daily_features table
    |     has no columns for SpotGamma levels (lines 30-46 of
    |     feature_store.py). Schema change required.
    |
    +---> [Discord notification] -- post extracted levels to channel
    |
    +---> [In-memory cache for intraday use] -- reasoning engine,
          alert checks, etc.
```

**Failure points:**
1. Email authentication (Gmail API tokens expire, 2FA complications)
2. Email format changes (SpotGamma redesigns their newsletter -- instant breakage)
3. Parse errors (new terminology, changed number formats, added sections)
4. Timing (email arrives late or not at all -- what's the fallback?)
5. No existing scheduling mechanism for pre-market email fetch. The scheduler cog (`cog_scheduler.py` line 231) handles pre-market at 9:15 ET, but email needs to be fetched earlier.

### 2.2 Path 2: TradingView Webhook

```
TradingView alert fires (price crosses SpotGamma level)
    |
    v
POST /webhook/tradingview (or new /webhook/spotgamma)
    |
    v
[FastAPI endpoint] -- src/webhook/tradingview.py line 44
    |
    v
[alert_queue] -- asyncio.Queue (tradingview.py line 22)
    |
    v
[WebhooksCog._poll_queue] -- cog_webhooks.py line 36
    |
    v
[Discord embed + signal_logger] -- cog_webhooks.py lines 54-74
```

**Failure points:**
1. TradingView alerts require Borey to manually update levels every day. This is a $299/mo product whose value proposition is that YOU automate this. Making Borey copy-paste levels defeats the purpose.
2. The existing `TradingViewAlert` model (tradingview.py line 25) has `action`, `ticker`, `price`, `strategy` fields -- but no concept of "level type" (gamma flip vs call wall vs put wall). You'd need to extend the model.
3. No backpressure on `alert_queue`. If levels are hit rapidly (volatile session), queue grows unbounded. Not a new problem but exacerbated by more alert sources.

### 2.3 Path 3: HIRO API

```
HIRO API (polled every N minutes during market hours)
    |
    v
[SpotGammaHIROClient.fetch_hiro()] -- new client, aiohttp pattern
    |
    v
[HIROData dataclass] -- hedging impact, net gamma, delta exposure
    |
    +---> [FeatureStore] -- schema change needed for HIRO columns
    |
    +---> [ReasoningManager] -- context for Claude analysis
    |     (src/ai/reasoning.py -- would need HIROData in MarketContext)
    |
    +---> [Discord notification on significant shifts]
```

**Failure points:**
1. API availability: Does SpotGamma even expose HIRO via REST API to Alpha subscribers? The public product is a dashboard, not an API. VERIFY THIS BEFORE WRITING ANY CODE.
2. Rate limits: Unknown. If HIRO is polled every 2 minutes (matching `config.update_interval_minutes`), that's ~195 requests per trading session. Within reasonable API limits, but unknown.
3. Authentication: API key? OAuth? Session cookie scraping? Each has different failure modes.
4. Data staleness: If the API goes down mid-session, stale HIRO data is worse than no HIRO data (you'd be making decisions on old hedging flow).

### 2.4 Path 4: Manual Borey Input

```
Borey types /levels command (or posts in #spotgamma channel)
    |
    v
[SpotGammaCog.levels_command()] -- new cog, slash command
    |
    v
[Parse structured input] -- "gamma_flip=5800 call_wall=5850 put_wall=5720"
    |
    v
[SpotGammaLevels dataclass] -- same as email path
    |
    +---> [FeatureStore or dedicated SpotGamma table]
    +---> [In-memory cache for intraday alerts]
    +---> [Confirmation embed back to Discord]
```

**Failure points:**
1. Borey forgets to enter levels. There is no forcing function. The system must work without SpotGamma data -- this is advisory only.
2. Input validation: What if Borey typos "5800" as "58000"? Need sanity checks (e.g., within 5% of current SPX spot price).
3. This path works. It's the simplest, most reliable, and most testable. But it requires Borey's daily attention, which the project constraints say is ~5 min/day. Entering 4-6 levels with context takes 30 seconds. Feasible.

---

## 3. SERVICEREGISTRY IMPACT

### 3.1 Current State

`src/services.py` (lines 47-82) defines a flat `@dataclass` with 18 optional service slots plus `data_manager`. There is no grouping or namespacing.

### 3.2 New Services Required

Depending on which paths are implemented:

| Service | Type | Depends On | Path |
|---------|------|------------|------|
| `spotgamma_client` | `SpotGammaHIROClient` | aiohttp, API key | Path 3 |
| `spotgamma_levels` | `SpotGammaLevelStore` | Store (aiosqlite) | All paths |

The `spotgamma_levels` service would be a thin wrapper around the SpotGamma-specific table, similar to how `FeatureStore` wraps `daily_features`.

### 3.3 Startup Order

The current startup order in `bot.py` is:
1. `DataManager` (line 64)
2. `Store` (line 69)
3. `HistoricalStore` (line 82)
4. `StrategyManager` (line 92, requires Store)
5. `SignalLogger` (line 104, requires Store)
6. `StrategyParser` (line 117)
7. `HypothesisManager` (line 127, requires Store)
8. ML components (line 139, requires Store/FeatureStore)
9. Paper trading (line 142, requires Store + StrategyManager)
10. `_sync_services()` (line 145)

SpotGamma HIRO client should initialize between steps 1 and 2 (it's a data client, no DB dependency). SpotGamma level store should initialize after step 2 (requires Store for DB connection).

### 3.4 Graceful Degradation

This is critical. SpotGamma is a $299/mo subscription. It WILL lapse, it WILL have outages, and you WILL cancel it if ROI doesn't justify cost. Every consumer of SpotGamma data must handle `None`:

```python
# In ServiceRegistry
spotgamma_client: SpotGammaHIROClient | None = None
spotgamma_levels: SpotGammaLevelStore | None = None
```

**The bot must run identically with or without SpotGamma data.** This is already the pattern for FlowAnalyzer, SentimentManager, etc. (bot.py lines 379-396). But I want to emphasize: SpotGamma data should NEVER be in any decision path that doesn't have a `if spotgamma is None: skip` guard.

### 3.5 Shutdown

`bot.py` `close()` (lines 481-531) needs to close the HIRO client's aiohttp session. Follow the existing pattern:

```python
if self.spotgamma_client is not None:
    await self.spotgamma_client.close()
```

---

## 4. SCHEMA DESIGN

### 4.1 The Problem

The `daily_features` table (`store.py` lines 280-304, `feature_store.py` lines 30-46) has:
- `UNIQUE(date, ticker)` constraint -- one row per ticker per day.
- 15 feature columns, all nullable REALs.
- No SpotGamma columns.

SpotGamma data is fundamentally different:
1. **Key levels** (gamma flip, call wall, put wall, vol trigger) are **daily** -- set pre-market, valid all day. This fits `daily_features` granularity.
2. **HIRO data** (hedging impact) is **intraday** -- changes every minute. This does NOT fit `daily_features`.

### 4.2 Option A: Add Columns to daily_features (BAD)

```sql
ALTER TABLE daily_features ADD COLUMN sg_gamma_flip REAL;
ALTER TABLE daily_features ADD COLUMN sg_call_wall REAL;
ALTER TABLE daily_features ADD COLUMN sg_put_wall REAL;
ALTER TABLE daily_features ADD COLUMN sg_vol_trigger REAL;
ALTER TABLE daily_features ADD COLUMN sg_hiro_net REAL;
```

**Why this is wrong:**
- `daily_features` is one row per day. HIRO updates intraday. You'd be overwriting `sg_hiro_net` 195 times per day, losing the intraday time series.
- The `FeatureStore.save_features()` method (feature_store.py lines 70-126) uses `ON CONFLICT DO UPDATE`, which means every HIRO update overwrites the daily row. You only keep the last value.
- The `FEATURE_COLUMNS` list (feature_store.py lines 30-46) would need to be extended. Every ML model that reads features now gets SpotGamma columns it doesn't understand. Coupling.

### 4.3 Option B: Separate Table for Levels, Separate Table for HIRO (CORRECT)

**Table 1: `spotgamma_levels` (daily key levels)**

```sql
CREATE TABLE IF NOT EXISTS spotgamma_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    ticker TEXT NOT NULL DEFAULT 'SPX',
    gamma_flip REAL,
    call_wall REAL,
    put_wall REAL,
    vol_trigger REAL,
    zero_gamma REAL,
    source TEXT NOT NULL DEFAULT 'manual',  -- 'manual', 'email', 'api'
    raw_text TEXT,  -- original source text for debugging
    created_at TEXT NOT NULL,
    UNIQUE(date, ticker)
);
```

Rationale:
- One row per day per ticker. Same granularity as `daily_features` but decoupled.
- `source` column tracks provenance (manual input vs email parse vs API).
- `raw_text` preserves the original input for debugging parse failures.
- `UNIQUE(date, ticker)` with `ON CONFLICT REPLACE` so re-entering levels overwrites cleanly.

**Table 2: `spotgamma_hiro` (intraday HIRO snapshots)**

```sql
CREATE TABLE IF NOT EXISTS spotgamma_hiro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    ticker TEXT NOT NULL DEFAULT 'SPX',
    net_hiro REAL,
    call_hiro REAL,
    put_hiro REAL,
    net_gamma REAL,
    delta_exposure REAL,
    metadata TEXT DEFAULT '{}',
    UNIQUE(timestamp, ticker)
);
CREATE INDEX IF NOT EXISTS idx_hiro_ticker_ts
ON spotgamma_hiro (ticker, timestamp);
```

Rationale:
- One row per poll interval (~2 min) per ticker.
- Preserves the full intraday time series.
- Can query "what was HIRO at the time we entered this trade?" for paper trading post-mortem.
- Needs a cleanup job: at 195 rows/day, 252 trading days/year = ~49,000 rows/year. Manageable, but add a retention policy (e.g., keep 30 days of intraday, aggregate to daily EOD after that).

### 4.4 Feature Store Integration

For ML models that need SpotGamma signals as features, inject a **derived** value into `daily_features` at EOD:

```python
# In the ML daily update pipeline (cog_scheduler.py ~line 350)
sg_levels = await spotgamma_level_store.get_levels("SPX", today)
if sg_levels:
    spot = chain.spot_price
    # Distance from spot to gamma flip as % of spot
    gamma_flip_dist = (sg_levels.gamma_flip - spot) / spot if sg_levels.gamma_flip else None
    await feature_store.save_features("SPX", today, {
        "sg_gamma_flip_dist": gamma_flip_dist,
        # ... other derived features
    })
```

This keeps SpotGamma raw data in its own table and only injects derived features into the ML pipeline. Clean separation.

### 4.5 Migration

Add to `store.py` `_run_migrations()` (line 347):

```python
(3, """
    CREATE TABLE IF NOT EXISTS spotgamma_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        ticker TEXT NOT NULL DEFAULT 'SPX',
        gamma_flip REAL,
        call_wall REAL,
        put_wall REAL,
        vol_trigger REAL,
        zero_gamma REAL,
        source TEXT NOT NULL DEFAULT 'manual',
        raw_text TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(date, ticker)
    )
"""),
(4, """
    CREATE TABLE IF NOT EXISTS spotgamma_hiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        ticker TEXT NOT NULL DEFAULT 'SPX',
        net_hiro REAL,
        call_hiro REAL,
        put_hiro REAL,
        net_gamma REAL,
        delta_exposure REAL,
        metadata TEXT DEFAULT '{}',
        UNIQUE(timestamp, ticker)
    )
"""),
(5, """
    CREATE INDEX IF NOT EXISTS idx_hiro_ticker_ts
    ON spotgamma_hiro (ticker, timestamp)
"""),
```

---

## 5. COUPLING RISKS

### 5.1 Email Format Changes

**Risk: CRITICAL.**

SpotGamma's Founder's Notes are written by a human (Brent Kochuba). The format changes without notice. New sections appear. Terminology evolves. Numbers get formatted differently ("5,800" vs "5800" vs "5.8K"). Images replace text. The email moves from text to HTML-only.

**Mitigation:**
1. Parse with fallback: attempt structured parsing first, fall back to regex, fall back to "unparseable -- post raw text to Discord for Borey to read manually."
2. Version the parser. When parsing fails for 3 consecutive days, alert Borey and disable the email path.
3. Store `raw_text` in the database so you can re-parse after fixing the parser.
4. Acceptance test: maintain a corpus of 20+ historical emails. Run parser against corpus on every code change. If parse rate drops below 80%, block deployment.

**But honestly: email parsing is the wrong approach.** It's high-effort, high-maintenance, and breaks silently. Manual Borey input (Path 4) is more reliable and takes 30 seconds per day. The email path should be deprioritized or abandoned.

### 5.2 API Changes

**Risk: MODERATE (for HIRO), LOW (for TradingView).**

HIRO API:
- SpotGamma is a small company. Their API (if it exists) is not versioned, not documented, and not contractually stable.
- Defense: Wrap all HIRO responses in a normalizer that maps raw API fields to your internal `HIROData` dataclass. If the API changes field names, you update the normalizer, not 15 consumers.
- Circuit breaker: After N consecutive failures, disable HIRO polling and alert. Don't hammer a dead API.

TradingView:
- The webhook format is controlled by YOUR Pine Script, not SpotGamma. Stable.

### 5.3 Subscription Lapse

**Risk: CERTAIN (eventually).**

SpotGamma Alpha is $299/mo. If it doesn't demonstrably improve paper trading performance, you cancel it. When that happens:

- `spotgamma_client` returns `None` for all calls. Fine -- everything is `Optional`.
- Email parsing stops. Fine -- no new levels.
- Old levels are still in the database. **Dangerous** -- stale levels are worse than no levels. You need a TTL on levels: if the latest `spotgamma_levels.date` is > 1 trading day old, treat SpotGamma data as unavailable.

### 5.4 Dashboard Scraping (Implicit Path 5)

Nobody has proposed this, but someone will suggest it: scrape the SpotGamma web dashboard for levels. **DO NOT DO THIS.**
- Violates SpotGamma's ToS.
- Breaks every time they change CSS/JS.
- Requires headless browser (Playwright/Selenium), adding a heavyweight dependency.
- Impossible to test reliably.

### 5.5 Data Consistency

If you implement multiple input paths (email + manual + API), you have a consistency problem. Which takes precedence?

**Rule: Last write wins, with source tracking.**
- If email parsing runs at 6:30 AM and populates levels, those are the levels.
- If Borey then manually corrects a level at 9:00 AM via `/levels`, the manual input overwrites.
- The `source` column in `spotgamma_levels` tracks which path last wrote the data.
- Never silently merge. If email says gamma_flip=5800 and Borey says gamma_flip=5820, the manual input wins completely. Don't average them. Don't keep both.

---

## 6. PRIORITY RECOMMENDATION

Implement in this order:

### Phase 1: Manual Input (Path 4) -- 1-2 days

- New cog: `src/discord_bot/cog_spotgamma.py`
- New slash command: `/levels gamma_flip:5800 call_wall:5850 put_wall:5720`
- New table: `spotgamma_levels` (migration v3)
- New service: `SpotGammaLevelStore` in ServiceRegistry
- Input validation (within 5% of current spot)
- `/levels show` command to display today's levels
- Modify `ReasoningManager` to include SpotGamma levels in `MarketContext`
- Zero external dependencies. Fully testable. Works immediately.

### Phase 2: Alert Integration -- 1 day

- Alert when SPX price crosses a SpotGamma level
- Integrate with existing `cog_alerts.py` alert framework
- Add level lines to GEX chart overlay

### Phase 3: HIRO API (Path 3) -- IF and ONLY IF API exists -- 2-3 days

- Verify HIRO API exists for Alpha subscribers
- Build `src/data/spotgamma_client.py` (aiohttp pattern)
- New table: `spotgamma_hiro` (migration v4-5)
- Poll during market hours, store intraday snapshots
- Feed HIRO into reasoning engine and anomaly detection

### Phase 4: Email Parsing (Path 1) -- MAYBE -- 3-5 days

- Only if manual input becomes a bottleneck (Borey complains)
- Gmail API integration
- Parser with versioned corpus testing
- Pre-market scheduled job (before 9:15 ET)

### DO NOT IMPLEMENT: TradingView Bridge (Path 2)

- Requires Borey to manually configure TradingView alerts daily.
- Adds no value over manual `/levels` input.
- Creates a fragile dependency on TradingView Pro subscription on top of SpotGamma Alpha.

---

## 7. CRITICAL QUESTIONS BEFORE ANY IMPLEMENTATION

1. **Does SpotGamma Alpha include API access to HIRO?** If yes, document the endpoints, auth mechanism, and rate limits. If no, Path 3 is dead.

2. **What exactly is in the Founder's Notes email?** Get 5 sample emails. Identify what's consistently parseable vs. free-form commentary. If the levels are buried in prose ("I'm watching the 5800 gamma flip area closely today"), regex parsing is a losing game.

3. **How many levels does Borey actually care about?** Gamma flip, call wall, put wall -- is that it? Or does he want 15 levels including second-order walls, HVL, etc.? The slash command UX changes dramatically with >5 parameters.

4. **What's the validation baseline?** Before integrating SpotGamma, establish paper trading performance WITHOUT it. Then measure the delta. If there's no measurable improvement after 30 trading days, cancel the subscription.

---

## 8. FILES REFERENCED

| File | Lines | Relevance |
|------|-------|-----------|
| `src/services.py` | 1-82 | ServiceRegistry definition -- needs new slots |
| `src/bot.py` | 1-531 | Startup/shutdown lifecycle -- needs HIRO client init |
| `src/data/data_manager.py` | 1-357 | Existing client orchestration -- SpotGamma does NOT go here |
| `src/db/store.py` | 1-703 | Schema, migrations -- needs new tables |
| `src/ml/feature_store.py` | 1-239 | daily_features -- should NOT be modified directly |
| `src/webhook/app.py` | 1-18 | FastAPI app -- could add SpotGamma webhook route |
| `src/webhook/tradingview.py` | 1-73 | Webhook model -- SpotGamma alerts need different model |
| `src/discord_bot/cog_webhooks.py` | 1-89 | Webhook-to-Discord bridge pattern |
| `src/discord_bot/cog_cheddarflow.py` | 1-226 | Closest analog: external data parsed from Discord messages |
| `src/discord_bot/cog_scheduler.py` | 1-479 | Daily pipeline: pre-market, post-market, ML update |
| `src/config.py` | 1-136 | Config pattern -- needs SpotGamma env vars |
| `src/data/cboe_client.py` | 1-268 | Reference: clean aiohttp client pattern |
| `src/data/unusual_whales_client.py` | 1-417 | Reference: authenticated API client with rate limits |
| `src/data/news_client.py` | 1-171 | Reference: API client with rate limiting |
