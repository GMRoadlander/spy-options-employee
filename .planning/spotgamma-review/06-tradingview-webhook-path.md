# 06 -- TradingView Webhook Path: Full Viability Analysis

**Reviewer**: Boris Cherney (adversarial)
**Date**: 2026-04-06
**Verdict**: The TradingView webhook path is a **Rube Goldberg machine** with a manual bottleneck that cannot be automated, delivering data too late and too unreliably for intraday SPX options trading. It adds three failure points to solve a problem that doesn't need to exist.

---

## 1. The Manual Bottleneck

### The Actual Daily Workflow

Every morning before market open, someone must:

1. Log into `dashboard.spotgamma.com`
2. Open the daily key levels popup (Gamma Flip, Call Wall, Put Wall, Zero Gamma, Absolute Gamma Strike)
3. Copy each level value
4. Open TradingView
5. Edit the Pine Script indicator's input parameters with the new values
6. Save the script
7. Delete yesterday's alerts (they reference yesterday's price levels)
8. Create new alerts on each level, configuring the webhook URL and JSON payload for each
9. Verify the alerts are active

This takes 5-10 minutes if nothing goes wrong. It requires a human who understands both SpotGamma's dashboard and TradingView's alert system.

### Can This Be Automated?

**Option A: Borey does it manually every morning.**
- Borey has ~5 min/day via Discord. This would consume his entire daily budget on copy-paste logistics before any actual trading analysis happens.
- If Borey is late, sick, traveling, or forgets, the system has no levels for the day. Silent failure.
- **Verdict: Non-starter.** You can't build a "permanent platform" on a daily manual ritual from someone with 5 minutes of availability.

**Option B: Scrape SpotGamma dashboard programmatically.**
- SpotGamma's dashboard is behind authentication (subscriber login).
- The dashboard API at `dashboard.spotgamma.com/docs/api/` exists but documentation suggests it's limited to subscriber-authenticated sessions, not standalone API keys for bots.
- Even if you could authenticate programmatically, scraping a subscriber dashboard violates SpotGamma's ToS (Section 4: "You shall not... use any automated system, including without limitation 'robots,' 'spiders,' 'offline readers,' etc., to access the Service").
- Browser automation (Playwright/Selenium) against their authenticated dashboard is both fragile (UI changes break it) and a ToS violation.
- **Verdict: Technically possible, legally prohibited, operationally fragile.**

**Option C: SpotGamma API access.**
- Per the existing research in `docs/research/04-gex-flow-darkpool.md`: "API access appears limited to subscribers -- not a standalone data feed product. You get dashboard access and platform integrations, not raw API endpoints for building custom apps."
- There is no documented public API endpoint that returns daily key levels as structured data.
- SpotGamma's TradingView integration is itself a manual process -- they provide a Pine Script *template* that the user must populate with levels each day.
- **Verdict: No API exists for this data. This is the fundamental problem.**

**Option D: Gil scripts the TradingView side (auto-update Pine Script inputs + alerts).**
- TradingView has no official API for creating or modifying alerts programmatically.
- TradingView's Pine Script inputs cannot be updated via API -- they're set through the UI.
- The TradingView "API" that exists is for chart embedding and widget display, not account automation.
- Browser automation against TradingView is possible but: (a) violates their ToS, (b) requires maintaining a browser session with 2FA, (c) breaks every time TV updates their UI, (d) is absurd complexity for setting 5 price levels.
- **Verdict: Cannot be automated without ToS-violating browser automation on both SpotGamma and TradingView.**

### The Bottleneck is Insurmountable

There is no legitimate automated path from SpotGamma's daily key levels to TradingView alerts. The entire proposed pipeline is predicated on a human performing a daily ritual that:

- Cannot be delegated to code
- Has no fallback when the human is unavailable
- Produces no audit trail of whether levels were entered correctly
- Fails silently (no alert fires because nobody set up today's alerts)

---

## 2. Pine Script Alert Payload Limitations

### What the Existing Webhook Expects

The `TradingViewAlert` Pydantic model in `src/webhook/tradingview.py` (lines 25-41) expects:

```python
action: str       # e.g., "buy_call", "sell_put", "alert"
ticker: str       # e.g., "SPX", "SPY"
price: float | None
time: str | None
interval: str | None
volume: float | None
strategy: str | None
message: str | None
```

With `extra="allow"` so unknown fields pass through.

### What Pine Script Alerts Can Actually Send

Pine Script alert messages support **static text with placeholders**. The available placeholders are:

- `{{ticker}}` -- symbol
- `{{close}}` -- current price at trigger
- `{{time}}` -- trigger time
- `{{interval}}` -- chart timeframe
- `{{volume}}` -- current volume
- `{{open}}`, `{{high}}`, `{{low}}` -- OHLC at trigger
- `{{plot_N}}` -- value of the Nth plot at trigger
- `{{timenow}}` -- current time

You can construct a JSON webhook body like:

```json
{
  "action": "alert",
  "ticker": "{{ticker}}",
  "price": {{close}},
  "time": "{{time}}",
  "message": "Price crossed Call Wall at 5850"
}
```

### The Critical Problem

The `message` field is **static text set when the alert is created**. Pine Script cannot dynamically determine:

- Which SpotGamma level was crossed (Call Wall vs. Put Wall vs. Gamma Flip)
- The direction of the cross (breaking above vs. breaking below)
- The significance of the cross (first touch vs. third rejection)

You'd have to create **separate alerts for each level** with hardcoded metadata in each alert's JSON body:

- Alert 1: "Price crosses Call Wall at 5850" -> `{"action": "alert", "strategy": "spotgamma_call_wall", "message": "Call Wall breach at 5850", ...}`
- Alert 2: "Price crosses Put Wall at 5720" -> `{"action": "alert", "strategy": "spotgamma_put_wall", "message": "Put Wall breach at 5720", ...}`
- etc.

This means:

1. **5-7 separate alerts per day** (one per SpotGamma level)
2. **Each must be manually configured** with the correct level type in the static JSON
3. **No way to distinguish "crossing above" from "crossing below"** unless you create TWO alerts per level (one for crossing up, one for crossing down) -- now you need **10-14 alerts per day**
4. **No retest/rejection logic** -- Pine Script alerts fire once when triggered (or every bar, but that creates alert spam)

### Data Fidelity Assessment

The existing `TradingViewAlert` model is designed for generic trading signals ("buy_call", "sell_put"). It has no fields for:

- `level_type` (gamma_flip, call_wall, put_wall, zero_gamma)
- `cross_direction` (above, below)
- `level_value` (the actual SpotGamma level price)
- `significance` (first test, retest, sustained break)

You'd have to shoehorn SpotGamma context into `strategy` and `message` as free-form text, then parse it back out on the receiving end. This is stringly-typed data masquerading as structured data.

---

## 3. Alert Management

### Daily Churn

SpotGamma levels change every trading day. The workflow requires:

1. **Delete all previous day's alerts** (5-14 alerts)
2. **Create new alerts** with updated levels (5-14 alerts)
3. **Verify each alert** has the correct webhook URL, JSON payload, and trigger conditions

This must happen every morning before 9:30 ET. Every single day.

### TradingView Alert Limits by Plan

| Plan | Price | Alert Limit |
|------|-------|-------------|
| Basic | Free | 1 alert |
| Essential | $12.95/mo | 20 alerts |
| Plus | $24.95/mo | 100 alerts |
| Premium | $49.95/mo | 400 alerts |
| Expert | $99.95/mo | 800 alerts |
| Ultimate | $199.95/mo | Unlimited |

If you need 10-14 alerts per day just for SpotGamma levels, the Essential plan ($12.95/mo) works -- but ONLY if you have no other alerts. If the system also monitors other signals via TradingView (which it likely would, given the existing webhook infrastructure), you'll quickly hit limits.

### Can Alert Creation Be Scripted?

**No.** TradingView provides no API for alert management. Period.

- No REST API for CRUD operations on alerts
- No WebSocket API for alert management
- No CLI tool
- No browser extension API
- The only path is browser automation (Playwright/Selenium against the TV web UI), which violates ToS and is maintenance hell

There are third-party services (e.g., TradingView Alert Manager Chrome extensions) that attempt to automate this. They all:
- Use browser DOM manipulation
- Break with every TradingView UI update
- Are not officially supported
- Cannot be run headlessly on a server

### Cost Analysis

To use TradingView as a webhook relay, you need:

- TradingView plan: $12.95-$24.95/mo (Essential or Plus)
- SpotGamma subscription: $89-$299/mo (for the levels data)
- **Total: $102-$324/mo** to achieve what a direct SpotGamma API client would do for $89-$299/mo alone -- if such an API existed

You're paying for TradingView as a middleman that adds no value and significant complexity.

---

## 4. Latency Analysis

### End-to-End Path

```
SPX price crosses SpotGamma level
  |
  v  [~0s] TradingView chart detects cross on next bar close
  |         (depends on chart timeframe: 1m = up to 60s latency)
  |
  v  [0-5s] TradingView evaluates alert condition
  |
  v  [0-30s] TradingView queues and fires webhook
  |           (TV does not guarantee instant delivery)
  |
  v  [50-200ms] HTTPS POST traverses internet to FastAPI endpoint
  |
  v  [<1ms] FastAPI validates payload, queues alert
  |
  v  [0-1s] WebhooksCog polls queue (1-second loop in cog_webhooks.py, line 35)
  |
  v  [100-500ms] Discord API processes embed send
  |
  v  [~0s] User sees alert in Discord
```

### Realistic End-to-End Latency

| Scenario | Latency |
|----------|---------|
| Best case (1-min chart, TV fires immediately) | 1-5 seconds |
| Typical case (1-min chart, TV webhook queue delay) | 5-30 seconds |
| Degraded case (TV under load, webhook delayed) | 30-120 seconds |
| Chart timeframe is 5-min | 0-5 minutes before condition even evaluates |

### Is This Fast Enough?

For intraday SPX options trading: **No.**

SPX moves 10-30 points in under a minute during volatile sessions. A 30-second latency on a gamma flip breach means the price may have already moved 5-15 points past the level by the time the alert reaches Discord. For 0DTE SPX options, that's potentially $500-$1,500 per contract of adverse movement.

The 1-second polling loop in `cog_webhooks.py` (line 35: `@tasks.loop(seconds=1)`) is actually fine -- it's the fastest link in the chain. The bottleneck is TradingView's alert-to-webhook delivery, which is documented as "best effort" with no SLA.

For comparison, the system already has real-time Tastytrade data flowing through the Tastytrade client. A direct SpotGamma level check against the live price feed would have sub-second latency. The TradingView detour adds 5-120 seconds of latency for zero benefit.

---

## 5. Reliability

### TradingView Webhook Delivery Guarantees

TradingView's webhook delivery is:

- **Best-effort**: No guaranteed delivery
- **No retry**: If the POST fails (endpoint down, timeout, network error), the alert is lost
- **No acknowledgment**: TV doesn't check if the webhook was received/processed
- **No delivery receipt**: No way to know a webhook failed to send
- **No webhook logs**: TV doesn't expose delivery history for debugging
- **Rate-limited under load**: During high-volatility market events (exactly when SpotGamma levels matter most), TV's infrastructure is under peak load and webhook delivery degrades

### Failure Modes

| Failure | Probability | Detection | Recovery |
|---------|-------------|-----------|----------|
| TV webhook doesn't fire | Low-Medium | None (silent) | None (missed signal) |
| TV webhook fires but FastAPI is down | Low | FastAPI health check | Alert is permanently lost |
| TV fires webhook, HMAC mismatch | Low | 401 logged server-side | Fix config, but alert is lost |
| TV alert condition missed (chart gap, market halt) | Low | None | None |
| TV alert deleted by TV (maintenance, account issue) | Very Low | None until next expected alert | Re-create manually |
| Internet connectivity to FastAPI endpoint | Low | Health monitoring | Alert lost during outage |

### The Existing Endpoint Has No Dead Letter Queue

Looking at `src/webhook/tradingview.py`:

```python
await alert_queue.put(alert)
```

This is an in-memory `asyncio.Queue`. If the process restarts, all queued alerts are lost. There's no persistence layer, no dead letter queue, no replay capability.

Looking at `src/discord_bot/cog_webhooks.py`:

```python
while not alert_queue.empty():
    try:
        alert: TradingViewAlert = alert_queue.get_nowait()
    except Exception:
        break
```

If `channel.send()` fails (Discord rate limit, channel not found), the alert is logged as an error and dropped. No retry. No re-queue.

The signal logger (lines 60-74) is explicitly non-blocking with `try/except` -- failures are silently swallowed.

### What the System Does When a Webhook Doesn't Fire

**Nothing.** There is no mechanism to detect a missed webhook. The system has no concept of "expected alerts" -- it doesn't know SpotGamma levels exist, so it can't know when one should have triggered and didn't.

This is the fundamental reliability problem with a push-based architecture for critical trading signals: the system cannot distinguish "no signal because the market didn't cross any levels" from "no signal because the webhook pipeline silently failed."

---

## 6. The Fundamental Question: TradingView Path vs. Direct Client

### What the TradingView Path Actually Is

```
[SpotGamma Dashboard]
    |
    v (MANUAL: human copies levels)
    |
[TradingView Pine Script]
    |
    v (Pine Script evaluates on each bar close)
    |
[TradingView Alert System]
    |
    v (Best-effort webhook POST)
    |
[FastAPI Endpoint]  <-- src/webhook/tradingview.py
    |
    v (In-memory asyncio.Queue)
    |
[WebhooksCog]  <-- src/discord_bot/cog_webhooks.py
    |
    v (Discord embed)
    |
[Discord Channel]
```

**Seven hops. One is manual. Two are third-party services with no SLA. Two are in-memory with no persistence.**

### What a Direct SpotGamma Client Would Be

```
[SpotGamma API/Scrape]
    |
    v (Automated: scheduled task fetches levels at 9:15 ET)
    |
[SpotGamma Level Store]  <-- e.g., dataclass in memory or SQLite row
    |
    v (Tastytrade price feed triggers comparison)
    |
[Level Monitor]  <-- new module: checks price vs. levels on each tick
    |
    v (Discord embed)
    |
[Discord Channel]
```

**Four hops. Zero manual. Zero third-party relay. Sub-second latency.**

### Comparison

| Dimension | TradingView Path | Direct Client |
|-----------|-----------------|---------------|
| **Manual steps** | Daily (copy-paste levels + create alerts) | None after initial setup |
| **Latency** | 5-120 seconds | <1 second (price feed tick) |
| **Reliability** | Best-effort, no retry, silent failure | Controlled, with retry and monitoring |
| **Failure detection** | None | Can detect stale levels, missed checks |
| **Cost** | SpotGamma ($89-299) + TradingView ($13-25) | SpotGamma ($89-299) only |
| **Maintenance** | Pine Script + alert config + webhook config | One Python module |
| **Data richness** | Static text in alert message | Full structured data |
| **Dependencies** | SpotGamma + TradingView + Internet x2 | SpotGamma + Internet x1 |
| **ToS compliance** | Compliant (manual workflow) | Depends on access method |

### The Honest Assessment

The TradingView webhook path is a **Rube Goldberg machine**. It takes a simple problem ("check if SPX price crossed a SpotGamma level") and routes it through:

1. A manual human workflow (copy-paste levels)
2. A charting platform with no automation API (TradingView)
3. A best-effort webhook system with no delivery guarantees
4. A generic webhook endpoint designed for a different use case
5. An in-memory queue with no persistence

...when the direct path is:

1. Fetch today's levels (one HTTP call)
2. Compare price to levels on each tick (one comparison per tick)
3. Post to Discord when crossed (one API call)

The existing `src/webhook/tradingview.py` endpoint is well-built for its intended purpose: receiving arbitrary TradingView alerts. It has proper validation, HMAC auth, async queuing, and clean Pydantic modeling. The `cog_webhooks.py` consumer is solid: 1-second polling, graceful degradation, signal logging.

**But using this infrastructure as a SpotGamma delivery mechanism is a category error.** The webhook endpoint exists because TradingView pushes data. SpotGamma levels are a pull problem -- you need to fetch them and monitor against a live price feed. Forcing a pull problem through a push pipeline by inserting a human in the middle is architectural malpractice.

---

## 7. Recommendations

### Do Not Pursue the TradingView Webhook Path for SpotGamma

The manual bottleneck alone is disqualifying. Everything else (latency, reliability, data fidelity, cost) reinforces the conclusion.

### Keep the Existing Webhook Infrastructure for Its Intended Use

The TradingView webhook endpoint is valuable for:

- Manual TradingView alerts that Borey or Gil set up for their own discretionary signals
- Strategy alerts from Pine Script indicators they're actively watching
- Any push-based signal source that speaks HTTP/JSON

Do not repurpose it as a SpotGamma relay.

### Investigate SpotGamma Data Access Directly

Before building anything, answer the actual prerequisite question:

1. **Does SpotGamma's Dashboard API expose daily key levels as structured data?** The docs at `dashboard.spotgamma.com/docs/api/` need to be read. If yes, build a client. If no, this entire integration path is moot regardless of architecture.

2. **Does SpotGamma offer any data export?** CSV download, email delivery of levels, API webhook from their side? Any structured output avoids the manual bottleneck.

3. **Is the DIY approach sufficient?** The system already calculates its own GEX, gamma flip, call wall, and put wall in `src/analysis/gex.py`. The existing research (`docs/research/04-gex-flow-darkpool.md`) explicitly concluded: "The existing `gex.py` implementation is correct and produces the same core output as SpotGamma's basic model." If the DIY GEX is already producing equivalent levels, the entire SpotGamma integration question is moot -- you already have the data.

### If SpotGamma API Access Exists

Build `src/data/spotgamma_client.py`:

- Authenticated HTTP client (aiohttp, following existing Tastytrade client patterns)
- Scheduled fetch at 9:15 ET daily (before market open)
- Store levels in `SpotGammaLevels` dataclass
- Level monitor compares Tastytrade real-time price against stored levels
- Discord alert on cross with full context (level type, direction, price, time)
- Retry logic, stale-level detection, health monitoring

### If SpotGamma API Access Does Not Exist

- Do not scrape their dashboard (ToS violation, fragile)
- Do not route through TradingView (this document's entire argument)
- Enhance the existing DIY GEX calculation in `src/analysis/gex.py` with the improvements listed in the existing research: minimum OI thresholds, vanna/charm, volume-adjusted OI estimates, gamma flip confidence scoring
- The DIY path costs $0/mo and produces the same fundamental data

---

## 8. Summary of Defects in the Proposed Path

| # | Defect | Severity | Mitigable? |
|---|--------|----------|------------|
| 1 | Daily manual copy-paste required | **Critical** | No -- no API exists to automate |
| 2 | TradingView has no alert management API | **High** | No -- platform limitation |
| 3 | Pine Script alerts carry no structured SpotGamma metadata | **High** | Partially -- workaround with static JSON |
| 4 | Webhook delivery is best-effort, no retry | **High** | No -- TV platform limitation |
| 5 | 5-120 second latency too slow for intraday SPX | **High** | No -- inherent to the architecture |
| 6 | Silent failure with no detection mechanism | **High** | Partially -- could add heartbeat monitoring |
| 7 | In-memory queue loses alerts on restart | **Medium** | Yes -- add persistence (but this is existing tech debt, not specific to SpotGamma) |
| 8 | Additional $13-25/mo for TradingView plan | **Low** | N/A -- cost of the approach |
| 9 | Alert limits constrain scaling | **Medium** | Yes -- upgrade TV plan |
| 10 | System already calculates equivalent data via DIY GEX | **Critical** | N/A -- this makes the entire integration questionable |

**Final verdict: Kill this path. Either investigate SpotGamma's API directly for a proper client integration, or -- more pragmatically -- invest in enhancing the DIY GEX system that already exists and already works.**
