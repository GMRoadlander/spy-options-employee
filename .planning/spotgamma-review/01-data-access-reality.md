# SpotGamma Integration: Data Access Reality Check

**Reviewer**: Adversarial (Cherney-style)
**Date**: 2026-04-06
**Verdict**: The proposed 3-path integration plan is built on assumptions that collapse under scrutiny. Two of three paths are not automatable. The third is unverifiable. The $299/mo spend buys data the system mostly already computes.

---

## 1. Founder's Notes Parsing: A Fragile Fantasy

### What the plan assumes

Parse twice-daily Founder's Notes emails for structured key levels (Call Wall, Put Wall, Vol Trigger, Hedge Wall, Absolute Gamma Strike).

### What actually happens

The Founder's Notes are **not emailed as structured data**. SpotGamma sends an email *notification* with a preview, then redirects users to `spotgamma.com` to read the full note on the web. The email itself is a teaser, not the payload.

The note structure includes these sections: Macro Theme, Key Levels, Macro Note, Ref Price, SG Implied 1-Day Move, SG Implied 5-Day Move, Volatility Trigger, Absolute Gamma Strike, Call Wall, Put Wall, and a free-form Daily Note. The levels ARE present as named fields with numeric values. But the surrounding content is **human-written prose by Brent Kochuba** -- "no academic jargon, just practical analysis."

### Why parsing is fragile

1. **Format instability**: These are editorial products, not API responses. Brent changes his template when he wants to. He has already restructured the notes multiple times since launch. There is no versioned schema. There is no changelog.

2. **Holiday/event gaps**: No notes on market holidays. Irregular notes during shortened sessions (day before Thanksgiving, etc.). The parser must handle missing data gracefully, but more importantly, the system must know *when to expect data and when not to*.

3. **Web-hosted content**: The actual levels live on `spotgamma.com`, not in the email body. To parse them, you need either:
   - **Email parsing** of the notification (may only contain a subset/preview of levels)
   - **Web scraping** of the full note page (requires authentication, JavaScript rendering, anti-bot measures)
   - **Gmail API + web scraping combo** (fragile chain of two independently breakable systems)

4. **Anti-scraping risk**: SpotGamma's Terms of Service almost certainly prohibit automated scraping of subscriber content. Getting caught means losing the $299/mo subscription and any data pipeline built on it.

5. **Latency**: Notes arrive pre-market (~7-8 AM ET) and post-market close. By the time you parse them, the levels are already hours old. The pre-market note is the useful one, but you're parsing prose at 7 AM to extract numbers that the system could compute from raw chain data at 6 AM when CBOE OI updates.

### The real question nobody is asking

**Why parse prose to extract numbers that are derived from public OI data?**

Call Wall = strike with largest net call gamma. Put Wall = strike with largest net put gamma. Absolute Gamma Strike = strike with largest total (absolute) gamma. These are ALL computable from the existing `gex.py` module with minor modifications (see Section 5).

The only levels you *cannot* trivially replicate are:
- **Vol Trigger** (proprietary weighting of gamma distribution across 4 nearest expirations, including their OI/volume adjustment model)
- **Hedge Wall** (proprietary volatility regime indicator for individual equities)

### Verdict: DO NOT BUILD THIS

The email parsing path is a maintenance nightmare for data you mostly already have. The two proprietary levels (Vol Trigger, Hedge Wall) are the only unique value, and they cannot be reliably extracted from prose without constant parser maintenance.

---

## 2. TradingView Webhook Bridge: Manual Copy-Paste Is Not Automation

### What the plan assumes

Set TradingView alerts on SpotGamma levels, fire webhooks into existing FastAPI endpoint when price touches levels.

### What actually happens -- the full data flow

1. SpotGamma updates level data on their backend at **3:00 AM ET daily**
2. SpotGamma's TradingView indicator fetches from a **URL that changes monthly** (second Sunday of each month, email notification sent)
3. For the TradingView indicator to show SpotGamma levels, the subscriber must:
   - Log into SpotGamma Portal
   - Find the "Daily Key Levels SPX" popup
   - **Manually copy the levels**
   - **Manually paste them into the TradingView indicator settings**
4. Only THEN do the levels appear on the chart
5. Only THEN can TV alerts be set on those levels
6. Only THEN can webhooks fire

### Why this is not automatable

**Step 3 is manual.** There is no API. There is no CSV download endpoint. There is no programmatic way to get levels into TradingView without a human copying and pasting numbers every morning.

Pine Script cannot fetch external data from arbitrary URLs. The only external data mechanism is `request.seed()`, which reads from a user-maintained GitHub repository -- meaning you would need a separate automation pipeline to:
1. Somehow extract SpotGamma levels (see Section 1 -- this is the same unsolved problem)
2. Push them to a GitHub repo in the correct format
3. Have the Pine Script indicator read from that repo
4. Wait for TradingView to pick up the update

This is a Rube Goldberg machine with at least 4 failure points.

### The URL that changes monthly

Even if you discovered the SpotGamma data URL that the TradingView indicator fetches from, that URL **rotates on the second Sunday of every month**. You would need to:
- Monitor notification emails for the new URL
- Parse the email to extract the new URL
- Update your fetching automation
- Every month. Forever.

### What the existing webhook infrastructure actually needs

The FastAPI webhook endpoint at `src/webhook/tradingview.py` is solid -- it accepts JSON with action, ticker, price, etc. The problem is not the receiving end. The problem is that **there is no automated sender**. Someone (Borey?) must manually update TradingView levels every morning. Borey's time budget is 5 minutes/day. Adding "log into SpotGamma, copy levels, paste into TradingView" eats that entire budget.

### Verdict: ARCHITECTURALLY BROKEN

The TradingView bridge requires daily human intervention that contradicts the project's core design principle (Borey spends <=5 min/day, never touches infrastructure). This is not an integration -- it is a manual workflow disguised as automation.

---

## 3. HIRO API: The "API" That Probably Isn't One

### What the plan assumes

Use HIRO API for real-time hedging pressure signals. Alpha subscribers get "API access."

### What "API access" actually means

SpotGamma's marketing says: *"API access is available for Alpha subscribers."*

Third-party analysis (FlashAlpha comparison, DEV.to) says: *"There is no public API or programmatic access to the data. If you want to build automated systems, scanners, or bots using SpotGamma's levels, you can't."*

Both of these statements are from 2025-2026. They directly contradict each other. Here is what I believe is actually happening:

1. **"API access" means platform integrations**, not REST endpoints. SpotGamma "integrates" with TradingView, Bookmap, NinjaTrader, ThinkorSwim, etc. These are **vendor-specific plugins**, not general-purpose APIs.

2. **HIRO is available via Bookmap plugin** as a native indicator. This is a Bookmap-specific integration, not a REST/WebSocket API you can call from Python.

3. **HIRO is available on the SpotGamma web dashboard** at `dashboard.spotgamma.com/hiro`. This is a web application, not an API endpoint.

4. The `dashboard.spotgamma.com/docs/api/` URL exists but **requires JavaScript to render** and is not publicly documented. This may be an internal API that powers the dashboard, not a subscriber-facing REST API.

### What you would need to do to get HIRO data

- **Option A**: Scrape the dashboard web app with Selenium/Playwright. Requires authentication. Almost certainly violates ToS. Brittle. Real-time scraping of a React app is a nightmare.
- **Option B**: Reverse-engineer the dashboard's internal API by watching network requests. Undocumented. Could change at any time. Probably violates ToS.
- **Option C**: Use the Bookmap plugin and somehow extract data from Bookmap. Requires running Bookmap ($50+/mo additional), plus writing a custom Bookmap add-on to intercept the data stream.
- **Option D**: Contact SpotGamma and ask for real API access. They will probably say no, or offer an enterprise tier at dramatically higher cost.

### What HIRO actually measures

HIRO = Hedging Impact Real-Time Options. It aggregates the delta-notional value of every option trade to estimate real-time hedging pressure. This is conceptually similar to:
- Computing net delta of all trades hitting the tape in real-time
- Classifying each trade as opening/closing (SpotGamma has proprietary models for this)
- Estimating the resulting dealer hedge requirement

You COULD build a crude approximation using Polygon.io's OPRA feed ($199/mo, already in the stack) or Unusual Whales' real-time flow data ($99/mo, already in the stack). It would not be identical to HIRO, but it would capture the same signal: "are options trades right now requiring dealers to buy or sell the underlying?"

### Verdict: UNVERIFIABLE AND LIKELY INACCESSIBLE

Nobody outside SpotGamma can confirm whether Alpha subscribers get actual REST/WebSocket API endpoints for HIRO. The weight of evidence says NO. Plan accordingly: assume no API access until proven otherwise, and only prove it by subscribing and testing -- not by assuming the marketing copy is literal.

---

## 4. TRACE and Equity Hub: Dashboard-Only, No Path Out

### TRACE (S&P 500 Options Heatmap)

TRACE visualizes how the options market exerts pressure on SPX in real-time. It shows:
- Zones of support and resistance from options positioning
- Areas of heightened volatility
- Price consolidation zones
- Built on SpotGamma's proprietary "Options Inventory Model"

**Data access**: Dashboard only. No export. No API. No CSV. No way to get this data out programmatically. It is a visual tool designed to be looked at by a human on a screen.

**Scraping feasibility**: TRACE is almost certainly a canvas/WebGL visualization, not HTML elements you can scrape. The data behind it is not exposed in the DOM.

### Equity Hub (3,500+ Stock/ETF Levels)

Equity Hub provides Call Wall, Put Wall, and other levels for individual equities. It includes "Total OI & Synthetic OI Lens."

**Data access**: Dashboard only. SpotGamma's own FAQ: *"Can I see historical data in Equity Hub?"* -- the fact this is a FAQ suggests data access is limited to the dashboard view. No export, no API.

**What "Synthetic OI" means**: SpotGamma adjusts published OI using intraday volume to estimate current OI before the next day's official OI update. This is their proprietary model. You cannot replicate this without their methodology, but you CAN build a crude version using the volume-adjusted OI approach already documented in the project's research (`docs/research/04-gex-flow-darkpool.md`, Section 7: "Track intraday volume per strike and adjust OI estimates").

### Verdict: NO PROGRAMMATIC PATH EXISTS

TRACE and Equity Hub are visual dashboard products. They have no API, no export, no data portability. Any plan that depends on consuming TRACE or Equity Hub data programmatically is fictional.

---

## 5. What SpotGamma Data Is ACTUALLY Unique vs. Already Computed

This is the most important section. The system already computes GEX from raw chain data. What does $299/mo buy that the system cannot compute itself?

### Already computed by the system (src/analysis/gex.py)

| SpotGamma Concept | System Equivalent | Status |
|---|---|---|
| **GEX by strike** | `gex.py` calculates per-strike GEX using BS gamma * OI * 100 * S^2 * 0.01 | IDENTICAL methodology |
| **Call Wall** (strike with largest net call gamma) | `gamma_ceiling` in `GEXResult` -- strike with highest call GEX | IDENTICAL. Rename the field. |
| **Put Wall** (strike with largest net put gamma) | `gamma_floor` in `GEXResult` -- strike with highest put GEX magnitude | IDENTICAL. Rename the field. |
| **Gamma Flip / Zero Gamma** | `gamma_flip` in `GEXResult` -- linear interpolation of net GEX zero crossing | IDENTICAL methodology |
| **Absolute Gamma Strike** | NOT computed, but trivially derivable: `strike with max(abs(call_gex) + abs(put_gex))` | **15-minute addition to gex.py** |
| **Dealer positioning** (short/long gamma) | `pcr.py` provides `dealer_positioning` via OI PCR thresholds | Different methodology, same intent |
| **Squeeze probability** | `squeeze_probability` in `GEXResult` combines negative GEX + high PCR | Comparable |
| **Key levels consolidation** | `strike_intel.py` merges GEX + max pain + high OI into ranked key levels | More comprehensive than SpotGamma's 5 levels |

### What SpotGamma computes that the system DOES NOT

| SpotGamma Feature | Can It Be Replicated? | Effort |
|---|---|---|
| **Volatility Trigger** | PARTIALLY. SpotGamma uses proprietary weighting across 4 nearest expirations with their OI/volume adjustment model. You can approximate with a weighted-expiry gamma flip, but it will not match exactly. | Medium -- build weighted multi-expiry gamma analysis, ~2-3 days |
| **Hedge Wall** (equity-specific vol regime) | NO. Proprietary statistical model for individual stocks. Not applicable anyway -- the system trades SPX only. | N/A for SPX |
| **HIRO** (real-time hedging flow) | PARTIALLY. Requires real-time OPRA trade tape + trade classification model. Polygon.io OPRA feed + custom aggregation could approximate. | Large -- 1-2 weeks minimum, requires OPRA feed |
| **TRACE** (visual heatmap) | NO. Proprietary visualization of proprietary Options Inventory Model. | Not replicable |
| **Synthetic OI** (intraday OI estimate) | PARTIALLY. Volume-adjusted OI is a known technique. Already documented in project research. | Small -- 1-2 days |
| **4-expiry aggregation** | YES. `gex.py` already supports all-expiry aggregation (`expiry=None`). Could add weighted aggregation favoring near-term. | Small -- half day |
| **Commentary/interpretation** | YES. Claude Sonnet already provides AI commentary on analysis results. | Already built |

### The uncomfortable truth

**Call Wall, Put Wall, and Absolute Gamma Strike are trivially computable from the system's existing GEX engine.** They are literally fields that already exist or can be derived from existing `GEXResult` data with a few lines of code:

```python
# Absolute Gamma Strike -- add to gex.py
abs_gex_by_strike = [abs(c) + abs(p) for c, p in zip(call_gex_list, put_gex_list)]
absolute_gamma_strike = strikes_list[int(np.argmax(abs_gex_by_strike))]
```

The system's `gamma_ceiling` IS the Call Wall. The system's `gamma_floor` IS the Put Wall. SpotGamma uses fancier names for the same math.

### What $299/mo actually buys

1. **Brent's interpretation** -- genuine alpha from 20+ years of derivatives experience. Claude Sonnet provides an approximation but cannot replicate domain expertise on novel market structures.
2. **Vol Trigger** -- a weighted, proprietary version of gamma flip. The system's gamma flip is close but not identical.
3. **HIRO** -- real-time hedging flow. No way to get this data programmatically even if you pay.
4. **TRACE** -- visual tool. No way to get this data at all.
5. **Community consensus** -- 50,000 subscribers watching the same levels creates self-fulfilling prophecy. The system has zero network effect.

Of these, only #1 (interpretation) and #5 (consensus/self-fulfilling) are genuinely non-replicable. And neither can be consumed programmatically.

---

## 6. Recommendations

### DO NOT subscribe to SpotGamma Alpha for programmatic integration

The $299/mo buys dashboard access to visual tools and editorial content. None of it feeds into a bot. You would be paying $3,588/year for data you cannot programmatically consume.

### DO build the missing SpotGamma-equivalent levels (2-3 days)

Add to `gex.py`:
- **Absolute Gamma Strike**: `max(abs(call_gex) + abs(put_gex))` per strike
- **Weighted multi-expiry gamma flip**: Weight gamma by days-to-expiry (near-term expirations weighted higher)
- **Volume-adjusted OI estimate**: `estimated_OI = yesterday_OI + net_volume_delta` (crude but better than stale OI all day)
- Rename `gamma_ceiling` to `call_wall` and `gamma_floor` to `put_wall` in outputs

### DO consider FlashAlpha as the programmatic alternative ($49/mo)

FlashAlpha provides exactly what SpotGamma does NOT:
- **REST API** with Python SDK (`pip install flashalpha`)
- **GEX, DEX, VEX, CHEX** per-strike exposure data
- **JSON responses** designed for programmatic consumption
- **Free tier** with 10 requests/day to validate before committing
- Growth tier at $49/mo gives 2,500 requests/day

This fills the exact gap: pre-computed exposure analytics via API, without the "API" being a marketing fiction.

### DO leverage existing data sources

The system already has:
- **Polygon.io OPRA feed** ($199/mo) -- raw real-time options trades, enough to build a HIRO approximation
- **Unusual Whales** ($99/mo) -- flow + dark pool data with actual REST API + Python SDK
- **CBOE CDN + Tradier** -- free options chain data with full Greeks and OI
- **ORATS** ($99/mo) -- historical chain data for backtesting

These provide MORE data access for LESS money than SpotGamma Alpha, and all of them have actual APIs.

### IF Borey wants SpotGamma for manual use -- fine

If Borey finds value in reading Brent's commentary and watching TRACE/HIRO on a screen, a Standard ($89/mo) or Pro ($129/mo) subscription is defensible as a manual trading tool. But it is a human tool, not a bot input. Do not architect around it.

---

## Sources

- [SpotGamma Plans & Pricing](https://spotgamma.com/subscribe-to-spotgamma/)
- [SpotGamma Alpha Features](https://support.spotgamma.com/hc/en-us/articles/15245866489107-Alpha)
- [SpotGamma Call Wall Definition](https://support.spotgamma.com/hc/en-us/articles/15297391724179-Call-Wall)
- [SpotGamma Put Wall Definition](https://support.spotgamma.com/hc/en-us/articles/15297856056979-Put-Wall)
- [SpotGamma Volatility Trigger](https://support.spotgamma.com/hc/en-us/articles/15297954935699-Volatility-Trigger)
- [SpotGamma Hedge Wall](https://support.spotgamma.com/hc/en-us/articles/15297582984723-Hedge-Wall)
- [SpotGamma Absolute Gamma](https://support.spotgamma.com/hc/en-us/articles/15297255426195-Absolute-Gamma)
- [SpotGamma Gamma Flip](https://support.spotgamma.com/hc/en-us/articles/15413261162387-Gamma-Flip)
- [SpotGamma HIRO Indicator](https://spotgamma.com/hiro-indicator/)
- [SpotGamma TradingView Upload](https://support.spotgamma.com/hc/en-us/articles/1500006839001-How-do-I-upload-to-TradingView)
- [SpotGamma TradingView Level Updates](https://support.spotgamma.com/hc/en-us/articles/1500006845362-When-do-the-TradingView-levels-update)
- [SpotGamma Founder's Note](https://support.spotgamma.com/hc/en-us/articles/15341610402579-What-is-the-SpotGamma-Founder-s-Note)
- [SpotGamma Dashboard API Page](https://dashboard.spotgamma.com/docs/api/index.html)
- [FlashAlpha vs SpotGamma vs Unusual Whales (DEV.to)](https://dev.to/tomasz_dobrowolski_35d32c/options-analytics-comparison-flashalpha-vs-spotgamma-vs-unusual-whales-which-fits-your-stack-ogi)
- [FlashAlpha Pricing](https://flashalpha.com/pricing)
- [FlashAlpha Exposure Analytics API](https://flashalpha.com/docs/lab-api-exposure)
- [FlashAlpha Python SDK (PyPI)](https://pypi.org/project/flashalpha/)
- [Existing GEX Research](docs/research/04-gex-flow-darkpool.md) (project internal)
- [Existing gex.py](src/analysis/gex.py) (project internal)
- [Existing strike_intel.py](src/analysis/strike_intel.py) (project internal)
