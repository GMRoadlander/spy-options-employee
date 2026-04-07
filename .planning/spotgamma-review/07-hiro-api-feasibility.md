# HIRO API Feasibility -- Adversarial Review

**Reviewer**: Boris Cherney mode (adversarial)
**Date**: 2026-04-06
**Verdict**: DO NOT BUY. BUILD YOUR OWN.

---

## 1. What Does "API Access" Actually Mean?

**Answer: Almost certainly NOT what you think.**

SpotGamma's marketing says "API access is available for Alpha subscribers." Let me enumerate every possible interpretation of those words, ranked by likelihood:

1. **Dashboard embed URL or iframe token** (most likely). You get a unique URL to embed HIRO charts in your own webpage. This is what 90% of fintech companies mean by "API access" on a marketing page. You get a rendered chart, not data.

2. **Authenticated dashboard with export buttons**. The `dashboard.spotgamma.com/docs/api/` URL suggests Swagger docs exist. But "docs/api" could be documenting a *frontend API* that their own dashboard consumes -- internal endpoints that return JSON to render their React charts. These may exist, may even be documented, but they are NOT a public contract. They can change without notice, rate-limit you to uselessness, or gate features behind higher tiers.

3. **CSV/Excel download**. Many "API access" claims at this price point mean: you can click Export and get a CSV. That is not programmatic access. That is a file download button.

4. **Actual REST API with documented endpoints, authentication, rate limits, and a data contract** (least likely at $299/mo). Companies that offer genuine data APIs at this quality level charge $500-2000/mo minimum (see: ORATS, Quandl/Nasdaq Data Link, OptionMetrics).

**The dev.to article saying "no public API or programmatic access" is probably correct.** The SpotGamma support page saying "API access is available" is marketing language. These two statements are not contradictory -- one is technical, one is sales.

**What I would need to believe otherwise**: Show me a `curl` command that returns JSON with HIRO values. Until I see that, "API access" is a marketing claim, not an engineering fact.

---

## 2. The `dashboard.spotgamma.com/docs/api/` URL

**What it probably is**: Swagger/OpenAPI documentation for the endpoints that their dashboard frontend calls. This is actually common -- React SPAs backed by FastAPI or Flask will auto-generate `/docs` if you don't disable it. The fact that it exists at `/docs/api/index.html` (note: `index.html`, not `/docs` which is the FastAPI default) suggests a custom static build, possibly Redoc or Swagger UI.

**What this tells us**:
- SpotGamma's dashboard has a backend API. Obviously. Every web dashboard does.
- That API serves JSON. Obviously.
- That API is *probably* authenticated with session cookies or JWT from their auth flow.
- The question is: **can you call it with a simple Bearer token, or does it require a full browser auth flow with CSRF tokens, cookies, and OAuth?**

**What we CANNOT infer**:
- Whether HIRO data is exposed through these endpoints at all (it may be a separate WebSocket or SSE stream)
- Whether the rate limits are sane for programmatic use
- Whether the response format is stable
- Whether they actively block non-browser User-Agents

**Without a $299 subscription to verify, this is all speculation.** And $299/mo to find out is an expensive experiment when the answer might be "it's a cookie-authenticated SPA backend that breaks if you look at it wrong."

---

## 3. The Bookmap Angle

**This is a legitimate backdoor, but it is ugly.**

Facts:
- HIRO is available as a Bookmap plugin ($49/mo standalone, or included in SpotGamma Alpha)
- Bookmap has a documented API: `com.bookmap.api.simple.SimpleIndicator`
- Bookmap plugins run as Java addons that can intercept indicator data
- Bookmap can export data to CSV or stream to external processes

**Viable approaches**:
1. **Write a Bookmap addon** that receives HIRO indicator updates and forwards them via a local WebSocket or writes to a shared SQLite file. This is technically sound but requires:
   - Running Bookmap as a headless (or minimized) process on the trading machine
   - Writing Java (Bookmap's plugin API is Java)
   - Maintaining compatibility as Bookmap updates its API
   - Paying $49/mo for the Bookmap HIRO subscription

2. **Screen-scrape Bookmap's HIRO panel** with Playwright or pyautogui. This is fragile, slow (100ms+ per capture), and a maintenance nightmare.

**My assessment**: The Bookmap addon approach works but violates KISS. You are now maintaining a Java plugin, a Bookmap process, and a local WebSocket relay just to get one indicator. If HIRO is the ONLY thing you need from SpotGamma, this is a $49/mo Rube Goldberg machine.

---

## 4. The `dxfeed-rust-api` Repo

**This is the most interesting signal, and it changes the calculus entirely.**

SpotGamma's GitHub (github.com/spotgamma) has a `dxfeed-rust-api` repository. dxfeed is the market data platform used by:
- Tastytrade (which you already use)
- thinkorswim / TD Ameritrade (now Schwab)
- Multiple options exchanges

**What this tells us about SpotGamma's pipeline**:
1. SpotGamma consumes raw OPRA options data via dxfeed
2. They compute HIRO from that raw data (it's not magic -- it's delta-notional aggregation)
3. They render it on their dashboard

**Critical implication**: If SpotGamma computes HIRO from dxfeed OPRA data, and Tastytrade also uses dxfeed, then the raw data flowing through your existing Tastytrade WebSocket is the SAME data SpotGamma uses. You have the ingredients. You just need the recipe.

**But wait** -- dxfeed provides different data levels. SpotGamma may be consuming full OPRA Level 2 with individual trade attribution, while the Tastytrade streamer gives you consolidated quotes. More on this in section 7.

---

## 5. Real-Time Constraints

**What HIRO actually measures**:
HIRO tracks the delta-hedging impact of live options trades in real-time. Specifically:
- When a large call trade executes, dealers (assuming they sold the call) must buy stock to delta-hedge
- HIRO quantifies this expected stock buying/selling pressure from dealer hedging
- The signal is: "options activity X implies dealers will buy/sell Y million dollars of stock"

**Update frequency requirements**:
- HIRO on SpotGamma's dashboard updates tick-by-tick or every few seconds
- For our use case (paper trading, Discord advisory), 5-30 second resolution is MORE than sufficient
- We are not HFT. We do not need sub-second HIRO updates. Anyone claiming we do is solving the wrong problem.

**If a SpotGamma API existed, what would it look like?**
- WebSocket or SSE for streaming (most likely)
- REST polling every 5-10 seconds (possible but wasteful)
- The latency from API -> our bot -> Discord message is already 1-5 seconds, so sub-second source latency is irrelevant

**Acceptable latency for this system**: 30 seconds. Period. Borey is reading Discord on his phone. He is not executing HFT algos.

---

## 6. The Worst Case: No API Exists

**If SpotGamma has no usable API, here are the fallback options in order of sanity:**

### 6a. Dashboard scraping with Playwright ($299/mo + engineering pain)
- Log into dashboard.spotgamma.com with Playwright
- Navigate to HIRO page
- Extract values from the DOM or intercept XHR/fetch calls
- Polling interval: 15-30 seconds

**Problems**:
- Fragile. Any dashboard redesign breaks the scraper.
- Requires maintaining a headless browser process.
- Violates SpotGamma's ToS (almost certainly).
- The $299/mo subscription becomes a permanent cost for a brittle integration.

### 6b. Intercept XHR from the dashboard (one-time reverse engineering)
- Use browser DevTools to identify the API endpoints the HIRO chart calls
- Replicate those calls with aiohttp using session cookies from a manual login
- This is essentially building an unofficial API client by reverse engineering

**Problems**:
- Auth tokens expire. You need to re-authenticate regularly.
- Endpoints can change without notice.
- May require solving CAPTCHAs or handling MFA.

### 6c. Give up on SpotGamma HIRO entirely
- Accept that HIRO from SpotGamma is a proprietary visualization
- Build our own hedging impact indicator (see section 7)
- Save $299/mo permanently

**This is my recommendation.** See below.

---

## 7. Can We Replicate HIRO? YES, AND WE SHOULD.

### What HIRO Actually Computes

HIRO is not magic. The algorithm, at its core:

```
For each options trade that executes:
  1. Determine trade direction (buyer-initiated vs seller-initiated via trade conditions)
  2. Compute delta of the option at time of trade (Black-Scholes, you already have this)
  3. Compute delta-notional = trade_size * delta * 100 * spot_price
  4. Assign sign: if buyer-initiated call OR seller-initiated put -> positive (dealers sell stock)
                  if seller-initiated call OR buyer-initiated put -> negative (dealers buy stock)
  5. Accumulate running sum over time window
```

The output is a cumulative or rolling delta-notional flow, showing whether dealer hedging activity is creating buying pressure (positive HIRO) or selling pressure (negative HIRO) on the underlying.

### What You Already Have

I reviewed the codebase. Here is what exists today:

**`src/data/polygon_client.py` -- PolygonOptionsStream**:
- WebSocket connection to `wss://socket.polygon.io/options`
- Receives real-time trade events with: ticker, price, size, exchange, conditions, timestamp
- Already classifies trades as sweep/block/standard
- Already has a `PolygonFlowAggregator` that tracks call_volume, put_volume, premium, sweep/block counts

**`src/analysis/greeks.py`**:
- Full Black-Scholes implementation: `black_scholes_delta()`, `black_scholes_gamma()`
- Already used by GEX engine and risk analyzer

**`src/analysis/gex.py`**:
- GEX (Gamma Exposure) engine that computes dealer hedging impact per strike
- Uses OI-weighted gamma to find gamma flip, ceiling, floor
- Already understands the dealer hedging model (calls = positive GEX, puts = negative GEX)

**`src/analysis/pcr.py`**:
- Dealer positioning classifier (short_gamma, long_gamma, neutral) from OI PCR
- Directly relevant context for hedging pressure interpretation

**`src/ml/anomaly.py` -- FlowAnalyzer**:
- Combines Unusual Whales flow data with Polygon real-time data
- Detects sweep surges, premium spikes, dark pool divergence
- Already has the architecture for multi-source flow analysis

**`src/data/unusual_whales_client.py`**:
- Flow data with classification (sweep/block/golden_sweep), side (buyer/seller), premium, volume
- Dark pool prints with price, size, notional

### What You Are Missing (to build HIRO equivalent)

1. **Trade direction inference**. The Polygon trade event includes `conditions` (an array of condition codes). Condition codes can indicate:
   - Trade executed at ask (buyer-initiated) vs at bid (seller-initiated)
   - You need the mapping: Polygon condition codes -> buy/sell classification
   - The Unusual Whales `side` field already gives you this for UW data

2. **Real-time delta computation per trade**. When a trade comes in via Polygon WebSocket:
   - Parse the OCC ticker to extract strike, expiry, call/put
   - Compute delta using `black_scholes_delta(spot, strike, T, iv, r, option_type)`
   - You need current spot price (available from your Tastytrade stream) and current IV (available from Polygon chain snapshot or from the trade's implied IV)

3. **Rolling accumulation with time decay**. HIRO is not a simple sum. It typically uses an exponentially-weighted rolling window (e.g., 5-minute EMA or 30-minute cumulative) so the signal fades as hedging pressure is absorbed.

4. **Normalization**. Raw delta-notional in dollar terms needs to be normalized relative to typical daily hedging flow to produce a -1 to +1 or similar bounded signal.

### Implementation Estimate

Given the existing codebase, building a HIRO equivalent requires:

| Component | Effort | Exists? |
|-----------|--------|---------|
| Trade direction from Polygon conditions | 2-3 hours | No -- need condition code mapping |
| Real-time delta computation per trade | 1-2 hours | Partial -- `black_scholes_delta` exists, need to wire it to stream |
| OCC ticker parser (strike/expiry/type) | Already done | Yes -- `_option_type_from_ticker()` exists, needs extension for strike/expiry |
| Rolling delta-notional accumulator | 2-3 hours | No -- new class, similar to `PolygonFlowAggregator` |
| Normalization + signal output | 1-2 hours | No |
| Integration with FlowAnalyzer | 1-2 hours | Partial -- architecture exists |
| Tests | 3-4 hours | No |
| **Total** | **~12-16 hours** | |

### What You Get vs. What SpotGamma Charges

| Feature | SpotGamma HIRO | DIY HIRO |
|---------|---------------|----------|
| Cost | $299/mo ($3,588/yr) | $0/mo after build |
| Data source | dxfeed OPRA (same as Tastytrade) | Polygon OPRA WebSocket ($199/mo, already paying) |
| Latency | ~1s | ~5-30s (acceptable) |
| Customizable | No | Fully |
| Can add gamma-weighted HIRO | No | Yes |
| Can combine with UW flow | No | Yes (FlowAnalyzer already does multi-source) |
| Breaks when vendor changes dashboard | Yes | No |
| Dependency on third party | Complete | None |

---

## 8. Concrete Gaps in Current Architecture

Even with the "build it yourself" approach, I need to flag things the current code does NOT handle:

### 8a. OCC Ticker Parsing is Incomplete
`_option_type_from_ticker()` in `polygon_client.py` extracts only C/P. For HIRO you need the full parse:
```
O:SPY251219C00600000
  ^^^--- underlying
       ^^^^^^--- expiry (YYMMDD)
             ^--- type (C/P)
              ^^^^^^^^--- strike * 1000 (i.e., 600.000)
```
This is trivial but currently missing.

### 8b. No Trade Condition Code Mapping
Polygon's trade condition codes (integers in the `conditions` array) tell you:
- 0 = regular trade
- Trade at bid vs ask (varies by exchange)
- Spread trade, combo, etc.

Without this mapping, you cannot reliably determine trade direction. You can fall back to "price relative to NBBO" heuristic (price >= ask = buyer, price <= bid = seller, between = unknown), but this is less accurate.

### 8c. Spot Price Staleness
To compute delta per trade, you need current spot price. The Polygon Options WebSocket does not provide underlying quotes. You need either:
- A separate Polygon equity WebSocket subscription (`wss://socket.polygon.io/stocks`)
- The Tastytrade streamer (which you already have)
- A periodic REST poll (introduces latency)

The Tastytrade streamer is already running. Use that for spot price. But make sure the architecture pipes it to the HIRO calculator.

### 8d. IV per Strike at Time of Trade
Computing delta accurately requires the IV of the specific option at the moment the trade executes. Options:
- Use the last known IV from the Polygon chain snapshot (stale by seconds to minutes)
- Infer IV from the trade price itself (iterative BS solve -- expensive per trade)
- Use a flat IV estimate from the VIX or ATM IV (fast, less accurate)

For HIRO's purposes, using the chain snapshot IV updated every 30-60 seconds is accurate enough. Do not over-engineer this.

---

## 9. Recommendation

**DO NOT subscribe to SpotGamma Alpha ($299/mo).** The probability of getting a clean, documented, stable REST API for HIRO is low. The cost is high. The dependency is permanent.

**DO build a HIRO-equivalent "Hedging Impact" indicator.** You have:
- Polygon OPRA WebSocket (already integrated, already paying for it)
- Black-Scholes delta computation (already built and tested)
- GEX engine that already models dealer hedging (already built)
- FlowAnalyzer that already combines multiple flow sources (already built)
- Unusual Whales flow data with buy/sell classification (already integrated)

The incremental work is 12-16 hours. The annual savings is $3,588. The indicator is customizable, testable, and owned.

**Name it something distinct**: "Dealer Hedging Pressure" or "DHP" -- not "HIRO" (that is SpotGamma's trademark). Make it clear in the Discord output that this is a proprietary calculation, not SpotGamma data.

**If Borey insists on SpotGamma HIRO specifically** (because he trusts their specific calibration), then:
1. Subscribe to one month of Alpha ($299) as a research expense
2. Open DevTools on the dashboard, find the XHR endpoints for HIRO data
3. Document the request/response format
4. Build a reverse-engineered client
5. Cancel after one month if the API is undocumented/unstable
6. Fall back to DIY if the reverse engineering is too fragile

But I would not recommend this path. The DIY version will be better for this system's needs.

---

## 10. Summary of Destroyed Assumptions

| Assumption | Status | Reality |
|------------|--------|---------|
| SpotGamma has a REST API for HIRO | **UNVERIFIED** | Marketing language; likely dashboard embed or SPA backend |
| $299/mo gets programmatic data access | **UNLIKELY** | At this price point, you get a dashboard, not a data feed |
| The dashboard API URL proves an API exists | **MISLEADING** | It proves a frontend has a backend; does not prove external access |
| Bookmap is a viable backdoor | **TECHNICALLY YES, PRACTICALLY NO** | Java plugin + headless Bookmap = over-engineered for one indicator |
| We need SpotGamma to get HIRO-like data | **FALSE** | We have all the raw ingredients; we just need to cook them |
| HIRO requires special data we don't have | **FALSE** | It uses OPRA trades (Polygon) + Black-Scholes delta (built) |
| Real-time means sub-second | **FALSE** | 30-second resolution is more than adequate for Discord advisory |

---

*End of review. The math is on our side. Build it.*
