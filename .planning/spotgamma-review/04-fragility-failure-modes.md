# 04 - Fragility & Failure Mode Analysis: SpotGamma Integration

**Reviewer**: Boris Cherney (adversarial)
**Date**: 2026-04-06
**Status**: Review complete
**Scope**: Three proposed SpotGamma Alpha integration paths -- Founder's Notes email parsing, TradingView webhook bridge, HIRO API

---

## Preamble: What the Existing Codebase Does Right (and Where It Sets a Trap)

Before tearing these integration paths apart, I need to acknowledge what your existing data layer does well, because it sets a standard the SpotGamma integrations will be measured against -- and will almost certainly fail to meet.

**Existing resilience patterns worth noting:**

1. **DataManager fallback chain** (`data_manager.py`): Tastytrade -> CBOE -> Tradier, with quality checks (`_check_chain_quality`) that reject "unusable" data (0% OI and 0% IV). This is the correct architecture. Every SpotGamma path should degrade this gracefully.

2. **Session invalidation on auth failures** (`tastytrade_client.py:91`): Auth errors clear cached sessions so next call retries fresh. SpotGamma integrations need this too, but email parsing has no "session" concept -- so what does "retry" even mean?

3. **Quality tagging** (`data_quality` field on `OptionsChain`): Data is labeled "ok", "degraded", or "unusable". SpotGamma levels need equivalent quality classification, but the failure modes are fundamentally different -- you are not receiving raw data you can assess, you are receiving pre-computed levels from a black box model.

4. **WebSocket with exponential backoff** (`polygon_client.py:456-634`): Up to 30s max backoff with reconnect budget. HIRO API (if WebSocket-based) needs this pattern, but SpotGamma's reconnect semantics are undocumented.

**The trap**: Your existing system has layered fallbacks because all data sources provide the same type of data (options chains). SpotGamma levels have NO FALLBACK. There is no second vendor selling the same Call Wall / Put Wall / Vol Trigger levels. If SpotGamma fails, you either have stale levels or no levels. This asymmetry is the single biggest architectural risk in the entire integration.

---

## Integration Path 1: Founder's Notes Email Parsing

### 1.1 Silent Failure Modes

| # | Failure | How It Happens | Severity | Detection Difficulty |
|---|---------|---------------|----------|---------------------|
| S1 | **Email template changes** | SpotGamma redesigns email layout, changes header text, reorders sections. Has happened before per the task description. | CRITICAL | HIGH -- parser returns partial/empty results without error |
| S2 | **Levels present but wrong format** | SpotGamma changes "Call Wall: 5,900" to "CW: 5900" or "Call Wall 5900" (drops colon, drops comma). Regex/pattern match silently skips. | HIGH | HIGH -- no error raised, level simply missing from output |
| S3 | **Half the levels parse, half don't** | Template partially changes. You get Call Wall and Put Wall but miss Vol Trigger and Hedge Wall. System proceeds with incomplete data, no alarm raised. | HIGH | VERY HIGH -- system looks like it's working, acts on incomplete picture |
| S4 | **Stale email used as "today's" data** | Gmail delivers email 30-60 minutes late. System parses it and stamps with current time. Or: no email arrives today, yesterday's cached levels persist past TTL reset. | HIGH | MEDIUM -- timestamp comparison could detect, but only if implemented |
| S5 | **Levels are numerically correct but contextually wrong** | SpotGamma starts reporting "Adjusted Call Wall" or changes their model methodology. Values parse fine but mean something different. | HIGH | IMPOSSIBLE without human review |
| S6 | **Email contains conditional levels** | "If SPX trades above 5,900, the Call Wall shifts to 5,950." Parser extracts 5,900 OR 5,950 depending on regex greediness. Both are "correct" in different regimes. | MEDIUM | VERY HIGH |
| S7 | **Duplicate emails** | SpotGamma sends a correction email. Parser uses the first one. Or parser processes both and last-write-wins with the correction. No guarantee of ordering. | MEDIUM | MEDIUM |
| S8 | **Email encoding issues** | HTML entity encoding changes numbers: `&#8203;5,900` (zero-width space), `5\u200b900` (Unicode zero-width space). Regex fails to match, no error. | MEDIUM | HIGH |

### 1.2 Loud Failure Modes

| # | Failure | How It Happens | Impact |
|---|---------|---------------|--------|
| L1 | **Gmail API auth token expires** | OAuth2 refresh token revoked (Google security policy change, account 2FA reset, 6-month idle). All email fetch calls return 401. | System-wide email ingestion stops |
| L2 | **Gmail API rate limit** | Polling too frequently, or Google imposes new quotas. Returns 429. | Temporary loss of email access |
| L3 | **SpotGamma subscription lapses** | Credit card expired, billing issue. No more Founder's Notes emails. System gets no new levels indefinitely. | Gradual stale-data poisoning -- no error, just silence |
| L4 | **Email parsing exception** | Malformed HTML, unexpected encoding, None where string expected. Python raises ValueError/AttributeError/TypeError. | Single fetch cycle fails, visible in logs |
| L5 | **Gmail account compromise** | Account hacked, emails deleted, forwarding rules changed. | Complete loss of data source, possible data exfiltration |

### 1.3 External Dependencies

| Dependency | Must Be Up | SLA | Your Control |
|-----------|-----------|-----|-------------|
| Gmail API | Yes | 99.95% (Google Workspace) | Zero |
| Gmail IMAP/OAuth2 | Yes | Same | Zero |
| SpotGamma email delivery | Yes | None (no SLA) | Zero |
| SpotGamma email template | Stable | None | Zero |
| SpotGamma model accuracy | Correct | None | Zero |
| SpotGamma subscription | Active | Manual renewal | Partial (billing) |
| DNS resolution | Yes | ISP-dependent | Zero |
| Local machine network | Yes | Home internet | Low |

**Total chain**: 8 external dependencies, 0 with contractual guarantees relevant to email content format.

### 1.4 Format Change Risk

**Likelihood**: HIGH. SpotGamma has changed their email template before. They are a small company (~20 employees based on LinkedIn) with active development. Template changes happen for marketing reasons (rebranding, adding new features, A/B testing), not just data format reasons. You will get zero notice.

**Detection strategy**: The only reliable approach is a **canary test** on every parse:
1. Define a set of expected field names (Call Wall, Put Wall, Vol Trigger, Hedge Wall, Gamma Flip)
2. After parsing, count how many fields were extracted
3. If count < expected threshold (e.g., 4 of 5), flag as `degraded`
4. If count == 0, flag as `format_change_suspected`
5. Alert Borey via Discord immediately

**What will NOT work**: Schema validation. There is no schema. It is free-text email HTML. You are doing NLP on marketing content, not parsing an API response.

### 1.5 Recovery Path

**When parsing fails**: Fall back to manual entry via Discord command (`/levels set call_wall=5900 put_wall=5800 ...`). Borey manually types levels from the SpotGamma dashboard.

**Problem with this fallback**: Borey spends ~5 min/day on this system. Manual level entry adds friction. If he forgets (see scenario analysis below), system runs with stale or no levels. There is no reminder mechanism unless you build one.

**Degradation behavior**: System should clearly mark analysis as "SpotGamma levels unavailable" in Discord output rather than silently omitting them. The existing `data_quality` pattern on `OptionsChain` is the right model -- but SpotGamma levels are not an `OptionsChain`, so you need a new quality-tracking structure.

---

## Integration Path 2: TradingView Webhook Bridge

### 2.1 Silent Failure Modes

| # | Failure | How It Happens | Severity | Detection Difficulty |
|---|---------|---------------|----------|---------------------|
| S1 | **Alert auto-deleted by TradingView** | TV limits free accounts to 1 active alert. Pro users can have more, but alerts auto-delete if the underlying indicator changes or TV updates the chart. User doesn't notice. | CRITICAL | VERY HIGH -- no notification when alert stops firing |
| S2 | **Webhook fires but with stale data** | TV alert triggers on a price crossing the level, but the level itself hasn't been updated because the user forgot to update it in TV. Webhook payload contains correct signal but wrong level. | HIGH | HIGH -- payload looks valid |
| S3 | **Webhook delivers out-of-order** | Two alerts fire simultaneously (price whips through Call Wall and Put Wall). Delivery order is not guaranteed. If system depends on sequence, behavior is undefined. | MEDIUM | MEDIUM |
| S4 | **Webhook fires during market close** | After-hours price movement triggers alert. System processes it as an intraday signal. | MEDIUM | LOW -- timestamp check can catch this |
| S5 | **Payload format varies by alert type** | Different Pine Script alert types produce different JSON shapes. `action`, `ticker`, `price` fields may be named differently or missing depending on how the alert was configured. | MEDIUM | MEDIUM -- Pydantic's `extra="allow"` means unknown fields are silently accepted |
| S6 | **Rate limiting by TradingView** | TV may throttle webhook delivery during volatile markets. Alerts queue on TV's side, arrive late or are dropped entirely. | HIGH | VERY HIGH -- TV does not report dropped webhooks |
| S7 | **Duplicate webhook delivery** | TV retries on perceived failure (your server was slow to respond, returned 5xx). Same alert processed twice. | LOW | MEDIUM |

### 2.2 Loud Failure Modes

| # | Failure | How It Happens | Impact |
|---|---------|---------------|--------|
| L1 | **Webhook server unreachable** | Local machine restarted, firewall blocked port, ngrok/tunnel expired, ISP outage. | All webhooks lost until server recovers |
| L2 | **TradingView outage** | TV platform goes down. No alerts fire. | Complete loss of signal delivery |
| L3 | **Webhook secret mismatch** | Secret rotated on one side but not the other. All incoming webhooks rejected with 401. | Complete loss of signal delivery, visible in logs |
| L4 | **FastAPI process crash** | Unhandled exception in webhook handler brings down the co-hosted server. | Webhook and health endpoints both fail |
| L5 | **SSL/TLS certificate expiration** | If using HTTPS (required by many webhook sources), cert expires. TradingView refuses to deliver to expired cert. | Silent delivery failure on TV's side |

### 2.3 External Dependencies

| Dependency | Must Be Up | SLA | Your Control |
|-----------|-----------|-----|-------------|
| TradingView platform | Yes | ~99.9% | Zero |
| TradingView alert system | Yes | No separate SLA | Zero |
| Network path TV -> your server | Yes | ISP + tunnel provider | Low |
| FastAPI webhook server | Yes | Your code | Full |
| ngrok/Cloudflare Tunnel (if used) | Yes | Varies | Partial |
| DNS for webhook URL | Yes | Registrar | Partial |
| SpotGamma (for level values) | Yes, for accuracy | None | Zero |

**Critical observation**: The webhook bridge is a **Rube Goldberg machine** for getting SpotGamma levels into your bot. The chain is: SpotGamma -> Dashboard -> User manually enters into TradingView -> TradingView evaluates alert condition -> TradingView sends webhook -> ngrok/tunnel -> your FastAPI -> alert queue -> Discord cog. **Seven hops. Every one can fail.**

### 2.4 Format Change Risk

**Likelihood**: MEDIUM. The existing `TradingViewAlert` Pydantic model (`webhook/tradingview.py`) uses `extra="allow"`, which means unknown fields are silently accepted. But the `action`, `ticker`, and `price` fields are required -- if the Pine Script alert format changes, these could break.

The deeper risk: the TradingView webhook is a **manually-configured** data pipeline. Its reliability depends entirely on a human (Borey) correctly configuring Pine Script alerts and not accidentally deleting them. This is not a resilience pattern; this is a prayer.

### 2.5 Recovery Path

**When webhooks stop arriving**: The system has no way to know. There is no heartbeat. There is no "I expected a webhook by 9:45 AM and didn't get one" check. The webhook is fire-and-forget from TV's perspective.

**Required mitigation**: Implement a "levels freshness" monitor:
1. Track timestamp of last received SpotGamma levels webhook
2. If market is open and no levels received by 9:45 AM ET, alert Borey on Discord: "SpotGamma levels not received today. Use `/levels set` to enter manually."
3. If levels are >4 hours old during market hours, mark as `stale` and annotate all analysis output

**Degradation behavior**: Same as Path 1 -- manual entry fallback. But now you have TWO things that need to work (TV + webhook) instead of one (Gmail).

---

## Integration Path 3: HIRO API (Real-Time Hedging Pressure)

### 3.1 Silent Failure Modes

| # | Failure | How It Happens | Severity | Detection Difficulty |
|---|---------|---------------|----------|---------------------|
| S1 | **API returns 200 with yesterday's data** | SpotGamma's backend caches aggressively. During startup or after maintenance, API returns stale data with current timestamp or no timestamp at all. | CRITICAL | VERY HIGH unless you validate data recency independently |
| S2 | **HIRO values are correct but model is wrong** | SpotGamma's HIRO model has a bad day -- misreads hedging flow, produces bullish signal during a selloff. Their model is a black box; you cannot validate it. | CRITICAL | IMPOSSIBLE programmatically |
| S3 | **Rate limiting during high-vol events** | VIX spikes to 35+. Everyone hammers the API. SpotGamma throttles requests. Your polling interval drops from every 30s to every 5 minutes. You get data, just less of it, exactly when you need it most. | HIGH | MEDIUM -- HTTP 429 is detectable, but implicit throttling (slower responses) is not |
| S4 | **Partial response** | API returns some HIRO data fields but not others. Missing fields default to 0 or null. System treats null HIRO signal as "neutral" when it should be "unknown". | HIGH | HIGH -- requires explicit null-vs-zero discrimination |
| S5 | **HIRO data covers wrong symbol** | You request SPX HIRO but get SPY HIRO (or vice versa). API does not error; the values are plausible but for the wrong instrument. | MEDIUM | HIGH unless you validate response symbol matches request |
| S6 | **Gradual model drift** | SpotGamma adjusts HIRO calibration over weeks/months. Historical HIRO=+50 meant "strong bullish hedging pressure." After recalibration, HIRO=+50 means "moderate." Your thresholds become stale. | MEDIUM | IMPOSSIBLE without SpotGamma changelog monitoring |
| S7 | **Timezone confusion** | HIRO timestamps are in UTC, your system assumes ET, or vice versa. Data appears fresh when it is 5 hours old, or stale when it is current. | MEDIUM | MEDIUM -- unit test can catch, but only if you know the API's timezone convention |

### 3.2 Loud Failure Modes

| # | Failure | How It Happens | Impact |
|---|---------|---------------|--------|
| L1 | **403 Forbidden** | Subscription lapses. API key revoked. Plan downgraded from Alpha. | Complete loss of HIRO data |
| L2 | **API endpoint moved/renamed** | SpotGamma updates their API. Old endpoint returns 404. | Complete loss of HIRO data |
| L3 | **Connection timeout** | SpotGamma servers overloaded (market open, OpEx). | Temporary loss, retryable |
| L4 | **JSON schema change** | Response body changes field names (`hiro_value` -> `hiro_reading`, `signal` -> `direction`). JSON parsing succeeds but field extraction fails. | KeyError / silent zero-default |
| L5 | **WebSocket disconnect** (if WS-based) | Network hiccup, SpotGamma restart. | Temporary loss, requires reconnect logic |
| L6 | **SSL certificate error** | SpotGamma rotates certs, intermediate CA changes. Python's `certifi` bundle doesn't include new CA. | Connection refused, visible error |
| L7 | **API returns 500** | SpotGamma internal error during market hours. | Temporary loss, retryable |

### 3.3 External Dependencies

| Dependency | Must Be Up | SLA | Your Control |
|-----------|-----------|-----|-------------|
| SpotGamma API servers | Yes | No public SLA | Zero |
| SpotGamma subscription (Alpha tier) | Yes | Manual renewal | Partial (billing) |
| SpotGamma HIRO model | Correct | None | Zero |
| Network path to SpotGamma | Yes | ISP | Low |
| DNS resolution | Yes | ISP | Low |
| SpotGamma API schema | Stable | No versioning guarantee | Zero |

### 3.4 Format Change Risk

**Likelihood**: MEDIUM-HIGH. SpotGamma's Dashboard API (`dashboard.spotgamma.com/docs/api/`) is described in their research doc as "limited to subscribers" and not a "standalone data feed product." This means:
- No public API versioning or deprecation policy
- No contractual obligation to maintain backward compatibility
- Changes can happen without notice
- No developer community to raise alarms

**Detection strategy**:
1. **Response schema validation**: Define expected fields and types. On every response, validate that all expected fields are present and within plausible ranges (e.g., HIRO value between -200 and +200, or whatever the documented range is).
2. **Smoke test on startup**: At 9:25 AM ET, make a test API call. If it fails or returns unexpected shape, alert immediately before market open.
3. **Canary comparison**: If you also calculate your own GEX-based hedging signal, compare HIRO direction with your signal. Persistent divergence may indicate HIRO model change.

### 3.5 Recovery Path

**When HIRO API fails**: Unlike options chain data, there is no fallback HIRO provider. The only recovery options are:

1. **Degrade to DIY GEX-based hedging estimate**: Your existing `gex.py` calculates gamma exposure and gamma flip. You could derive a crude hedging pressure proxy from GEX magnitude changes between poll intervals. This is NOT the same thing as HIRO, but it is not nothing.

2. **Cache last known good value with decay**: Keep the last valid HIRO reading and exponentially decay its confidence. After 15 minutes, weight it at 50%. After 30 minutes, weight it at 25%. After 1 hour, discard entirely.

3. **Alert and continue without**: Mark all analysis output with "HIRO unavailable" and let Borey decide whether to trust the remaining signals.

---

## Cross-Cutting Failure Scenarios

### Scenario A: SpotGamma Changes Founder's Notes Email Template

**Impact**: Path 1 breaks silently. Parser extracts 0 of 5 levels (format unrecognizable) or 2 of 5 (partial match on unchanged sections).

**Cascade**: If Path 1 is primary and Path 2/3 are not implemented, system operates with NO SpotGamma levels. If Path 2 is backup (TradingView), it still requires Borey to manually update TV alerts with levels he reads from the SpotGamma dashboard -- which defeats the purpose of automation.

**Detection time**: Unknown. Could be hours (if someone checks logs) or days (if no one does). The system will continue running, producing analysis WITHOUT SpotGamma levels, and Borey may not notice the absence.

**Required mitigation**: Parse completeness check with Discord alert. "Today's Founder's Notes email was received but only 2 of 5 levels could be extracted. Possible template change. Use `/levels set` for manual override."

### Scenario B: SpotGamma Goes Down During Market Hours

**Impact**: Path 3 (HIRO API) returns errors or timeouts. Path 1 (email) is unaffected (email was already received pre-market). Path 2 (TradingView) is unaffected (levels already loaded into TV).

**This is the LEAST catastrophic scenario.** Pre-market levels (Call Wall, Put Wall, etc.) are daily numbers that don't change intraday. Only HIRO (real-time flow) is lost. System degrades to GEX-only analysis, which is exactly what it does today without SpotGamma.

**Required mitigation**: Log the HIRO outage, continue with existing signals, annotate Discord output with "HIRO data unavailable -- using GEX-only analysis."

### Scenario C: HIRO API Rate-Limited During High-Vol Days

**Impact**: This is the worst possible timing failure. VIX spikes, gamma flip is being tested, you NEED hedging flow data, and SpotGamma throttles you because 50,000 other Alpha subscribers are also hammering the API.

**The fundamental problem**: SpotGamma is a retail product. Their infrastructure is designed for 50,000 dashboard users refreshing a browser, not 50,000 API clients polling every 30 seconds. Rate limits during high-vol events are not a bug; they are a capacity constraint.

**Required mitigation**:
1. Implement adaptive polling: Normal = every 60s, elevated vol = every 30s, but NEVER below 30s.
2. On 429, exponential backoff starting at 2 minutes. Do NOT retry aggressively -- you will make it worse.
3. Cache the last good HIRO value with timestamp and confidence decay.
4. Most importantly: **do not make trading decisions based on the ABSENCE of HIRO data.** If HIRO is unavailable, the system should increase conservatism, not maintain the same risk posture.

### Scenario D: TradingView Webhook Fails to Fire

**Causes**: Network outage, TV alert deleted, TV outage, alert condition never met (levels were wrong), webhook URL expired (ngrok free tier rotates URLs), firewall rule changed.

**Impact**: System receives no intraday level-crossing alerts. If SpotGamma levels were loaded via Path 1 (email) at market open, the levels themselves are available but the system doesn't know when price interacts with them.

**Detection**: The freshness monitor proposed in Path 2 recovery. If no webhook received by 10:00 AM and market is open, alert.

**But here's the deeper issue**: TradingView webhooks are designed for a human trader who watches a chart and also gets alerts. They are NOT designed as the sole data delivery mechanism for an automated system. There is no "webhook health check" endpoint. There is no "list my active alerts" API. You cannot programmatically verify that your alerts still exist and are correctly configured.

### Scenario E: Borey Forgets to Paste Levels Manually

**Impact**: If email parsing (Path 1) fails and TradingView (Path 2) is the backup, but Borey was supposed to enter levels into TradingView or via `/levels set`, the system runs with stale/no levels.

**Probability**: HIGH. Borey spends ~5 min/day on this. Manual data entry is the first thing to be skipped when he is busy.

**Required mitigation**: Make manual entry the FALLBACK, not the primary path. The system should be designed so that zero human intervention is needed for the happy path. If human intervention is required, it should be because something BROKE, and the system should be actively nagging (Discord alert every 30 minutes: "SpotGamma levels missing. Reply with `/levels set call_wall=X put_wall=Y ...`").

### Scenario F: SpotGamma Key Levels Are WRONG

**Impact**: This is the failure mode that cannot be detected and cannot be mitigated. SpotGamma's model is a black box. If their Call Wall is at 5,900 but the "real" (whatever that means) call wall is at 5,850, your system will generate incorrect analysis.

**How this happens**:
- SpotGamma's OI data is T+1 (yesterday's). Massive overnight flow changes positioning.
- SpotGamma's dealer assumption (who is long/short) is wrong for a specific strike range.
- SpotGamma's model doesn't account for a structural change (e.g., 0DTE options now dominate gamma).

**Your existing DIY GEX has the same vulnerability.** Both use the same underlying data (OI) with the same lag (T+1). Adding SpotGamma doesn't make this worse, but it also doesn't make it better -- it just adds another black box with the same input limitations.

**Required mitigation**: Cross-validate. If your DIY GEX gamma flip is at 5,860 and SpotGamma's is at 5,900, flag the divergence. Don't blindly trust either one. This is the only defense against model error.

### Scenario G: Email Delayed by 30+ Minutes

**Impact**: Market opens at 9:30 AM ET. SpotGamma sends Founder's Notes at 9:15 AM. Gmail queues it. You receive it at 9:45 AM. For 15 minutes after market open, you operate with yesterday's levels (if cached) or no levels.

**Likelihood**: LOW on normal days. MEDIUM-HIGH on days with Gmail maintenance or high email volume.

**Required mitigation**:
1. Pre-market polling: Start checking for email at 8:00 AM, every 5 minutes.
2. If no email by 9:25 AM, alert Borey: "Founder's Notes not received. Check SpotGamma dashboard and use `/levels set`."
3. Use yesterday's levels as degraded fallback with "stale" annotation.
4. When email finally arrives, update levels and note the delay in logs.

### Scenario H: Half the Levels Parse, Half Don't

**Impact**: System has Call Wall and Put Wall but not Vol Trigger and Hedge Wall. Analysis proceeds with partial data. Some Discord outputs reference missing levels as 0 or null.

**This is worse than total failure.** Total failure is detectable. Partial failure is insidious. The system appears to work but produces incomplete analysis that Borey may trust without realizing key levels are missing.

**Required mitigation**:
1. Every parse result must report a completeness score: `{"parsed": 3, "expected": 5, "missing": ["vol_trigger", "hedge_wall"]}`
2. If completeness < 80% (4 of 5), mark as `degraded`
3. If completeness < 40% (2 of 5), mark as `unusable`
4. In Discord output, explicitly list which levels are available and which are missing. Never silently omit.

### Scenario I: API Returns 200 with Yesterday's Data

**Impact**: System ingests stale HIRO data, believes hedging pressure is (for example) bullish when it has shifted bearish. Trading signals are wrong.

**Detection**: Compare the response's internal timestamp (if any) with the current date/time. If the response says `"date": "2026-04-05"` and today is `2026-04-06`, reject the data.

**But what if there is no timestamp in the response?** Then you cannot detect this. And API responses from small companies frequently lack timestamps.

**Required mitigation**:
1. If the API response has a timestamp, validate it is today and within the last N minutes.
2. If the API response lacks a timestamp, compare the HIRO value against the previous reading. If identical across 10+ consecutive polls, flag as possibly stale. (Caveat: HIRO could genuinely be flat. So this is a heuristic, not a guarantee.)
3. Cross-reference with your own GEX calculations. If GEX has moved significantly but HIRO hasn't, something is wrong with one of them.

### Scenario J: Subscription Lapses, API Returns 403

**Impact**: Path 1 (email) -- Founder's Notes stop arriving. No error, just no emails. Path 3 (HIRO API) -- 403 Forbidden on every call.

**Detection time for email**: Could be 1-2 days before anyone notices, unless the "no email received by 9:25 AM" alert is implemented.

**Detection time for API**: Immediate. 403 is an unambiguous error code. The existing codebase handles 401/403 correctly in all clients (Polygon, Unusual Whales, Tradier).

**Required mitigation**: On 403 from HIRO, alert Borey with: "SpotGamma API returning 403 Forbidden. Subscription may have lapsed. Check billing at spotgamma.com." Do NOT silently retry for hours -- a billing issue won't fix itself.

---

## Comparative Risk Assessment

| Criterion | Path 1: Email | Path 2: TradingView Webhook | Path 3: HIRO API |
|-----------|--------------|---------------------------|-----------------|
| **Silent failure risk** | VERY HIGH (format changes) | HIGH (alert deletion, stale levels) | HIGH (stale data, model drift) |
| **Loud failure risk** | MEDIUM (Gmail auth) | MEDIUM (server unreachable) | MEDIUM (403, 429, timeout) |
| **External dependencies** | 8 | 7 | 6 |
| **Human-in-the-loop risk** | MEDIUM (SpotGamma writes email) | VERY HIGH (Borey configures alerts) | LOW (API is automated) |
| **Format change risk** | HIGH (free-text HTML) | MEDIUM (Pine Script payload) | MEDIUM-HIGH (undocumented API) |
| **Detection difficulty** | VERY HIGH | HIGH | MEDIUM |
| **Fallback when broken** | Manual entry | Manual entry | DIY GEX degradation |
| **Data freshness** | Once daily (pre-market) | Event-driven (delayed if TV queues) | Real-time (when working) |
| **Automation quality** | Medium (parser can break) | Low (human-dependent) | High (fully automated) |

---

## Architectural Recommendations

### 1. Do NOT Make SpotGamma a Hard Dependency

The existing `DataManager` pattern treats data sources as optional: if Tastytrade fails, CBOE is tried; if CBOE fails, Tradier is tried. SpotGamma levels must follow the same pattern. The system must produce useful analysis WITH or WITHOUT SpotGamma data. SpotGamma should ENHANCE, not ENABLE.

### 2. Implement a SpotGammaLevels Data Structure with Quality Tracking

```python
@dataclass
class SpotGammaLevels:
    call_wall: float | None = None
    put_wall: float | None = None
    vol_trigger: float | None = None
    hedge_wall: float | None = None
    gamma_flip: float | None = None
    timestamp: datetime | None = None
    source: str = ""  # "email", "webhook", "api", "manual"
    quality: str = "unknown"  # "ok", "degraded", "stale", "unusable"
    completeness: float = 0.0  # 0.0 to 1.0
```

### 3. Build Staleness Detection Into Every Path

Every path must track `last_updated` and implement a staleness check:
- Pre-market levels (email/webhook): Stale after market close (16:00 ET)
- Real-time data (HIRO): Stale after 15 minutes of no updates during market hours
- All paths: If `last_updated` is yesterday or older, mark as `stale` and alert

### 4. Cross-Validate SpotGamma Levels Against DIY GEX

When both SpotGamma levels and DIY GEX are available, compare:
- SpotGamma gamma flip vs. DIY gamma flip: Divergence > 20 points = flag
- SpotGamma Call Wall vs. DIY highest call GEX strike: Divergence > 30 points = flag
- Log divergences for model confidence tracking over time

### 5. Path 2 (TradingView) Should Be Rejected

Path 2 adds complexity with no reliability gain. It introduces the highest human-in-the-loop risk (Borey must configure and maintain alerts), has no health check mechanism, and its failure modes are nearly impossible to detect. The TradingView webhook server is useful for OTHER purposes (Pine Script strategy alerts), but not as a SpotGamma data delivery mechanism.

### 6. If Budget Allows, Implement Path 3 (HIRO API) as Primary, Path 1 (Email) as Backup

- Path 3 for real-time HIRO data during market hours
- Path 1 for pre-market daily levels (Call Wall, Put Wall, etc.)
- Manual `/levels set` as last-resort fallback
- Path 2 eliminated

### 7. Error Handling Must Match Existing Codebase Patterns

Every SpotGamma client must implement:
- Session invalidation on auth errors (like `TastytradeClient._invalidate_session()`)
- Rate limit tracking (like `PolygonClient._check_rate_limit()`)
- Explicit error classes (like `PolygonAuthError`, `PolygonRateLimitError`)
- Graceful fallback to empty/default values (like `NewsClient.fetch_headlines()` returning `[]`)
- Quality-gated acceptance (like `DataManager._check_chain_quality()`)

---

## Summary of Mandatory Mitigations Before Any Path Ships

| # | Mitigation | Applies To | Effort |
|---|-----------|-----------|--------|
| M1 | Parse completeness scoring (N of M fields extracted) | Path 1 | Small |
| M2 | Staleness detection with Discord alert at 9:25 AM ET | Path 1, 2, 3 | Medium |
| M3 | Cross-validation against DIY GEX gamma flip | All paths | Medium |
| M4 | `SpotGammaLevels` dataclass with quality tracking | All paths | Small |
| M5 | Discord annotation when levels are missing/stale/degraded | All paths | Small |
| M6 | 403 billing alert to Borey | Path 1 (no email), Path 3 (API) | Small |
| M7 | Manual fallback command (`/levels set`) | All paths | Medium |
| M8 | Adaptive polling with exponential backoff on 429 | Path 3 | Small (pattern exists) |
| M9 | Response timestamp validation (reject stale 200s) | Path 3 | Small |
| M10 | HIRO confidence decay over time when no fresh data | Path 3 | Medium |
| M11 | Reject Path 2 (TradingView) for SpotGamma delivery | Architecture | Zero (just don't build it) |

---

## Final Verdict

The highest-value, lowest-risk integration is **Path 3 (HIRO API) for real-time data + Path 1 (email parsing) for daily levels**, with every mitigation from M1-M10 implemented. Path 2 (TradingView webhook) should be rejected for SpotGamma specifically -- it is the wrong tool for this job.

The biggest risk across all paths is not technical failure -- it is **silent correctness failure**. The system can parse a level, ingest it, and use it for analysis, and the level can be WRONG (stale, misinterpreted, or model error), and nobody will know until a trade goes bad. The only defense is cross-validation with your own calculations (M3) and conservative position sizing that does not rely on any single signal source being correct.
