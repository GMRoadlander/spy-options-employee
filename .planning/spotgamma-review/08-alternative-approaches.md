# 08 -- Alternative Approaches: Should We Even Buy SpotGamma?

**Reviewer**: Boris Cherney (adversarial)
**Date**: 2026-04-06
**Verdict**: NO. Do not buy SpotGamma Alpha. The $299/mo buys a dashboard Borey looks at, not data your system can ingest. If you want pre-computed exposure analytics for the bot, FlashAlpha at $49/mo does what SpotGamma cannot: return structured JSON from a real API. If you want to build it yourself, you already have 90% of the math running in production. Either path saves $250-299/mo.

---

## 1. FlashAlpha -- The Obvious Alternative Nobody Mentioned

### What It Is

FlashAlpha (flashalpha.com) is an API-first options analytics platform launched March 2026. Python SDK (`pip install flashalpha`, v0.2.1 as of March 28, 2026). REST endpoints returning structured JSON for GEX, DEX (delta exposure), VEX (vanna exposure), CHEX (charm exposure), SVI-calibrated volatility surfaces, full BSM Greeks through third order, volatility risk premium analysis, and key levels (gamma flip, call/put walls, max pain) for 6,000+ US equities and ETFs.

### Pricing (per flashalpha.com/pricing)

| Plan | Price | Rate Limit | Features |
|------|-------|------------|----------|
| **Free** | $0 | 5-10 req/day | Core + Exposure endpoints (GEX/DEX/VEX/CHEX) |
| **Basic** | $49/mo | 100 req/day | All exposure endpoints |
| **Growth** | $299/mo | 2,500 req/day | + 0DTE analytics, volatility, all endpoints |
| **Alpha** | $1,199/mo (annual) | Unlimited | SVI surfaces, zero-cache, direct support |

### Why This Is Objectively Better Than SpotGamma For a Programmatic System

Let me be precise about why this comparison is not even close:

**SpotGamma Alpha ($299/mo):**
- No public API. Their "Dashboard API" at `dashboard.spotgamma.com/docs/api/` is for their web UI, not for third-party programmatic consumption.
- Data lives in a dashboard. Integration means scraping or screenshot-parsing. Both are fragile, against ToS, and will break.
- HIRO and TRACE are visual tools. They render in a browser. There is no endpoint that returns "HIRO value = X" in JSON.
- Platform integrations (TradingView, ThinkorSwim, NinjaTrader) overlay levels on charts. They do not expose an API.

**FlashAlpha Basic ($49/mo):**
- `GET /v1/exposure/{ticker}/gex` returns per-strike gamma exposure in JSON.
- Python SDK with typed exceptions, automatic retries, structured responses.
- 100 requests/day at $49/mo. Your bot runs analysis every 2 minutes during market hours (6.5 hours = 195 intervals). Even at 100 req/day you can get GEX snapshots every 4 minutes for a single ticker. At the Growth tier ($299/mo -- same price as SpotGamma Alpha), you get 2,500 req/day, which is absurdly more than you need.
- MCP server available (`lab.flashalpha.com/mcp`) for direct Claude agent integration. No other options analytics provider offers this.
- SDKs in Python, JavaScript, C#, Go, Java.

**The math:**
- SpotGamma Alpha: $299/mo for data you cannot programmatically access.
- FlashAlpha Basic: $49/mo for data you CAN programmatically access.
- Savings: $250/mo = $3,000/year.

### FlashAlpha Risks and Skepticism

I will not pretend FlashAlpha is perfect. Here is what worries me:

1. **It launched March 2026.** The package has three versions on PyPI (0.1.0, 0.2.0, 0.2.1). That is a one-month-old product. APIs this young die, pivot, or break backward compatibility without warning. SpotGamma has years of track record.

2. **The "comparison" articles on their blog are pure marketing.** Every article on `flashalpha.com/articles/` is "FlashAlpha vs X" and guess who wins every time? This is not independent analysis. Treat their claims with appropriate skepticism.

3. **Rate limits at the free/basic tier are tight.** 5-10 req/day (free) or 100 req/day ($49) may be insufficient if you want multiple tickers, multiple exposure types, and frequent polling. Do the capacity math before committing.

4. **No track record for accuracy.** SpotGamma's model has been validated by thousands of traders over years. FlashAlpha's gamma calculations could be subtly wrong and nobody would know yet. Their model's assumptions about dealer positioning, OI adjustments, and volume-weighted updates are undisclosed.

5. **Single point of failure.** A one-month-old startup running your options analytics. If they go down or shut down, you're back to DIY.

**Mitigation:** Use FlashAlpha as a cross-validation layer alongside your existing DIY GEX, not as a replacement. If the two diverge significantly, you have a signal. If FlashAlpha dies, you still have your own engine.

---

## 2. DIY Proprietary Levels -- You Already Have the Math

### What You Already Compute (Production Code)

From the codebase (`src/analysis/gex.py`, `src/analysis/strike_intel.py`):

| SpotGamma Level | Your Equivalent | Source File | Status |
|----------------|-----------------|-------------|--------|
| Net GEX by strike | `GEXResult.net_gex_by_strike` | `gex.py:41-43` | Running |
| Gamma Flip | `GEXResult.gamma_flip` | `gex.py:93-125` | Running |
| Call Wall (highest call gamma strike) | `GEXResult.gamma_ceiling` | `gex.py:267-269` | Running |
| Put Wall (highest put gamma strike) | `GEXResult.gamma_floor` | `gex.py:274-276` | Running |
| Squeeze probability | `GEXResult.squeeze_probability` | `gex.py:128-184` | Running |
| Key levels consolidated | `StrikeIntelResult.key_levels` | `strike_intel.py:87-179` | Running |
| High OI strikes | `_find_high_oi_strikes()` | `strike_intel.py:54-84` | Running |
| GEX alignment scoring | `_assess_gex_support()` | `strike_intel.py:182-227` | Running |
| Max pain | `MaxPainResult` | `max_pain.py` | Running |
| Put/Call ratio | `PCRResult` | `pcr.py` | Running |

### What You Could Compute But Don't Yet

| SpotGamma Level | Formula | Data Source | Effort |
|----------------|---------|-------------|--------|
| **Vol Trigger** | Strike where cumulative dealer gamma transitions from net positive to net negative (same as gamma flip, different branding) | Already computed as `gamma_flip` | **Already done** |
| **Hedge Wall** | Strike with highest absolute put OI (not put gamma -- raw OI concentration) | Polygon or Tastytrade chain data | ~20 lines of code |
| **Absolute Gamma Strike** | Strike with highest total (call + put) gamma exposure, regardless of sign | `gex.py` -- add `np.argmax(np.abs(net_gex_by_strike))` | ~5 lines of code |
| **Vanna Exposure (VEX)** | `VEX = -e^(-qT) * d2 * phi(d1) / sigma * OI * 100` | `greeks.py` extension + existing chain data | ~50 lines (formula in research doc `04-gex-flow-darkpool.md:347-349`) |
| **Charm Exposure (CHEX)** | `CHEX = -e^(-qT) * phi(d1) * [2(r-q)T - d2*sigma*sqrt(T)] / (2T*sigma*sqrt(T)) * OI * 100` | `greeks.py` extension + existing chain data | ~50 lines |
| **HIRO (real-time hedging indicator)** | Volume-weighted intraday delta/gamma changes estimated from trade flow | Polygon OPRA WebSocket (already integrated in `polygon_client.py:441-728`) | ~200 lines, significant engineering |

### The Honest Assessment

Your existing `gex.py` computes the exact same thing as SpotGamma's "Call Wall" and "Put Wall." Look at lines 267-276:

```python
# Gamma ceiling: strike with highest CALL GEX
if call_gex_list and max(call_gex_list) > 0:
    max_call_idx = int(np.argmax(call_gex_list))
    gamma_ceiling = strikes_list[max_call_idx]

# Gamma floor: strike with highest absolute PUT GEX
if put_gex_list and max(abs(p) for p in put_gex_list) > 0:
    max_put_idx = int(np.argmax([abs(p) for p in put_gex_list]))
    gamma_floor = strikes_list[max_put_idx]
```

SpotGamma calls these "Call Wall" and "Put Wall." You call them `gamma_ceiling` and `gamma_floor`. Same math, different label. SpotGamma's "Volatility Trigger" is literally their brand name for the gamma flip point, which you compute at line 281.

The only SpotGamma level you genuinely cannot replicate cheaply is HIRO, which requires building a real-time volume-weighted hedging flow estimator on top of the Polygon OPRA stream. That is ~200 lines of non-trivial code, but you already have the WebSocket infrastructure (`PolygonOptionsStream`, `PolygonFlowAggregator`).

### Known Bugs in Your DIY Implementation

Per the adversarial GEX audit (`02-gex-auditor.md`), your DIY has real issues that must be fixed regardless of whether you buy SpotGamma:

1. **SPX lookback range is broken** -- `gex_lookback_strikes=50` is dollar distance, not strike count. For SPX at ~5200, you're only analyzing +/-10 strikes. Fix: use percentage of spot.
2. **0DTE contracts excluded** -- `T=0` guard returns zero GEX for same-day expiry. On the most important trading day (every day for SPX 0DTE), your GEX engine produces nothing.
3. **Chart crashes on None ceiling/floor** -- Production bug.
4. **Squeeze terminology confusion** -- Alert fires on PCR < 0.3 but probability scores on PCR > 1.0.

These bugs exist whether or not you pay SpotGamma $299/mo. SpotGamma does not fix your code. Fix the bugs. They are more impactful than any external data source.

---

## 3. GEX.gg and Free/Cheap Alternatives

### GEX.gg

GEX.gg does not appear to exist as a distinct product with programmatic access. The search results show no API documentation, no SDK, no structured data feed. It may be a dashboard-only site, or it may have been absorbed or renamed. **Not a viable option for programmatic integration.**

### Free Alternatives That Actually Exist

| Platform | Cost | API? | What It Offers |
|----------|------|------|---------------|
| **VannaCharm.com** | Free | No API (dashboard only) | GEX, VEX (vanna), CEX (charm) per-strike. Good for validating your DIY calculations visually. |
| **OptionsGEX.com** | Free | No documented API | Real-time GEX, OI analysis. Dashboard only. |
| **GEX-Metrix** | Free | No official API (third-party MCP server exists via reverse-engineered endpoints) | Dealer positioning metrics from OI/volume. The reverse-engineered API is fragile and unsupported. |
| **Trading Volatility** | Free | No API | GEX dashboard with skew adjustments. Updated models as of May 2025. |
| **Barchart** | Premier membership | CSV export only | GEX calculated on 4 nearby expirations, updated intraday. No REST API. |
| **TanukiTrade** | TradingView subscription | TradingView indicator only | GEX Profile for 220+ symbols. Not programmable outside TradingView. |

### Verdict on Free Alternatives

Every free GEX platform is dashboard-only. None provide programmatic API access. They are useful for visual cross-validation ("does our gamma flip agree with VannaCharm's?") but cannot feed data into the Discord bot pipeline.

---

## 4. Opto / Quiver Quant / Tradytics / Optionomics

### Quiver Quantitative

- **API**: Yes, REST API with Python package. Tiered pricing: Hobbyist ($10/mo), Trader ($75/mo), Institution (custom).
- **Focus**: Congressional trading, institutional holdings, government contracts, corporate lobbying. Options flow is not their core product.
- **Options data**: Limited. This is a political/institutional intelligence platform, not an options analytics platform.
- **Verdict**: Wrong tool for this job. The API exists but the data is irrelevant to dealer positioning and GEX.

### Tradytics

- **Focus**: Options flow, unusual activity, AI-powered trade ideas.
- **API**: Not prominently documented. Appears to be primarily a dashboard/web platform.
- **Pricing**: Subscription-based (exact tiers not clearly published).
- **Verdict**: Overlaps significantly with Unusual Whales (which you already have). Does not provide GEX/exposure analytics. Not a SpotGamma alternative.

### Optionomics

- **API**: Yes -- OpenAPI 3.0 spec, auto-generated client libraries, token-based auth.
- **Focus**: Options flow, unusual activity, sentiment.
- **Pricing**: Not clearly published.
- **Verdict**: Interesting for flow data but again overlaps with Unusual Whales. Not a GEX/exposure alternative.

### QuantData

- **Focus**: GEX, DEX, VEX, CHEX, Interval Map (time-based exposure visualization). 30+ exposure metrics.
- **Pricing**: ~$75/mo.
- **API**: **No official API.** A third-party MCP server exists (`quantdata-mcp` on GitHub) that reverse-engineers their web app's REST endpoints. This is brittle, unsupported, and will break without notice.
- **Verdict**: The product is actually relevant (GEX/DEX/VEX/CHEX), but without an official API it cannot be integrated reliably. The Interval Map is a compelling visual tool but, like SpotGamma's TRACE, it is a browser feature, not a data feed.

### Summary

None of these are better than FlashAlpha for programmatic GEX/exposure integration. Most are dashboard products or flow platforms that overlap with Unusual Whales.

---

## 5. The "Interpretation" Argument -- Is Human Commentary Worth $299/mo?

### SpotGamma's Value Proposition

SpotGamma's real moat is Brent Kochuba's daily Founder's Notes. These are 2x/day market commentaries that interpret the GEX profile in the context of the current macro regime, upcoming events, and historical patterns. Twenty years of derivatives experience distilled into actionable levels.

### What You Already Have

Your system generates AI commentary via Claude Sonnet (`src/ai/commentary.py`). The commentary pipeline ingests:
- GEX levels (gamma flip, ceiling, floor, squeeze probability)
- Max pain analysis
- Put/call ratios
- HMM regime state (risk-on/risk-off/crisis)
- LSTM volatility forecasts (1d and 5d)
- FinBERT sentiment scores
- Anomaly detection scores
- 15-feature daily feature store

This is, on paper, a more comprehensive input set than what SpotGamma's Founder's Notes use. The Founder's Notes are authored by a human who has seen 20 years of markets. Claude Sonnet has seen the internet's collective knowledge of options markets but has zero lived experience.

### The Honest Trade-Off

| Dimension | SpotGamma Human | Claude Sonnet |
|-----------|----------------|---------------|
| **Experience** | 20 years of derivatives trading | Zero lived experience |
| **Consistency** | Variable (human fatigue, vacation, bias) | Perfectly consistent |
| **Speed** | 2x/day fixed schedule | Every 2 minutes if needed |
| **Contextualization** | Exceptional (macro, flows, sentiment, experience) | Good but can hallucinate context |
| **Novel situations** | Can reason about unprecedented events | Will anchor to training data patterns |
| **Cost** | $299/mo | ~$5-20/mo in API calls |
| **Accountability** | Track record can be evaluated | No long-term track record |
| **Integration** | Borey reads it manually | Feeds directly into Discord bot |

### The Brutal Question

Is Borey reading SpotGamma's Founder's Notes and mentally applying them to his trading? If yes, he is already getting value from SpotGamma through his eyeballs, not through your system's API. Adding $299/mo to your bot's budget does not give your bot access to the Founder's Notes in any programmatic way.

Your bot generates its own commentary from richer data (GEX + regime + vol forecast + sentiment + anomaly). The commentary may be worse than Kochuba's, but it is integrated, automated, and costs $5-20/mo in Claude API calls instead of $299/mo for a dashboard Borey looks at separately.

**If SpotGamma's value is interpretation, Borey should subscribe personally and use it as a human overlay on the bot's signals. That is a $299/mo personal expense for Borey, not a system integration expense for the project.**

---

## 6. Cost-Benefit Math

### Current Monthly Data Spend

| Service | Monthly Cost | What It Provides | Used By System? |
|---------|-------------|-----------------|-----------------|
| Tastytrade | $0 (OAuth2) | Real-time SPX/SPY chains, Greeks | Yes (primary data) |
| ORATS | $99/mo | Historical chains, IV rank/percentile, backtesting | Yes |
| Polygon.io | $199/mo | OPRA real-time feed, trade-level data, news | Yes |
| Unusual Whales | $99/mo | Options flow, dark pool, sweep/block detection | Yes |
| **Current total** | **~$397/mo** | | |

### What $299/mo Buys Elsewhere

| Alternative Use | Monthly Cost | What You Get |
|----------------|-------------|-------------|
| FlashAlpha Basic | $49/mo | Pre-computed GEX/DEX/VEX/CHEX via real API. 100 req/day. |
| FlashAlpha Growth | $299/mo | Same as Basic + 0DTE analytics, vol surfaces, 2,500 req/day. |
| Claude API budget increase | $299/mo | ~150,000 additional Sonnet tokens/day for richer commentary |
| GPU compute (RunPod) | $299/mo | A100-80GB for ~100 hours. Train better LSTM/HMM models. |
| ORATS Intraday | $199/mo | 1-minute interval data for all options. Feed into DIY GEX for intraday updates. |
| Additional Polygon.io tier | $200/mo | Move from Starter to Developer. WebSocket streaming, more granular data. |
| Developer time (3 weeks) | $0 | Fix the 4 known GEX bugs, add vanna/charm calculations, build HIRO proxy. This costs engineering time but zero dollars. |

### The $3,588/Year Question

SpotGamma Alpha costs $3,588/year. For that money:

1. **FlashAlpha Basic for the entire year ($588) + save $3,000.** You get programmatic GEX/DEX/VEX/CHEX that actually feeds into the bot. Save the rest.

2. **Fix your own GEX engine ($0) + FlashAlpha for cross-validation ($588/year).** Fix the SPX lookback bug, the 0DTE exclusion, add vanna/charm. Use FlashAlpha to validate your calculations. Total: $588/year, and you own the IP.

3. **FlashAlpha Basic ($588) + ORATS Intraday upgrade ($2,388/year) = $2,976/year.** Still cheaper than SpotGamma, and you get 1-minute options data for intraday GEX recalculation. This is closer to what HIRO does.

4. **Do nothing extra ($0).** Your DIY GEX already computes Call Wall, Put Wall, gamma flip, and squeeze probability. Fix the bugs. The marginal value of SpotGamma over your existing system is the interpretation layer, which Borey can get by subscribing personally if he wants.

---

## 7. The Real Question: Data or Dashboard?

### This Is the Only Question That Matters

Ask Borey one question: **"When you look at SpotGamma, what exactly do you look at?"**

#### If the answer is "I look at the dashboard/TRACE/HIRO during trading":

Then SpotGamma is a **personal trading tool**, not a **system data source**. Integration is pointless because:
- The dashboard cannot be scraped reliably.
- HIRO and TRACE are visual, real-time browser tools.
- Borey is already getting the value by looking at it.
- The bot cannot consume what Borey sees.

In this case: **Borey should pay for SpotGamma personally if he finds it valuable.** Do not charge it to the system budget. Do not spend engineering time trying to "integrate" a dashboard.

#### If the answer is "I want the bot to know the SpotGamma levels (Call Wall, Put Wall, Vol Trigger)":

Then you do NOT need SpotGamma. You need:
1. **Your own `gex.py` with bugs fixed** (gamma_ceiling = Call Wall, gamma_floor = Put Wall, gamma_flip = Vol Trigger). Cost: $0.
2. **OR FlashAlpha Basic at $49/mo** for pre-computed levels via API if you don't trust your own math.

In this case: **Do not buy SpotGamma.** Buy FlashAlpha or fix your own engine.

#### If the answer is "I want both -- the dashboard for me and the data for the bot":

Then the correct architecture is:
- Borey subscribes to SpotGamma personally ($299/mo, his personal expense).
- The bot uses FlashAlpha Basic ($49/mo, system expense) or DIY GEX ($0).
- Total system cost: $0-49/mo instead of $299/mo.
- Borey still gets his dashboard.

---

## Recommendation

### Do This (in priority order):

1. **Do NOT subscribe to SpotGamma Alpha for the system.** The $299/mo buys a dashboard, not an API. Zero integration value for a programmatic system.

2. **Fix the known GEX bugs first** (SPX lookback, 0DTE exclusion, chart crash, squeeze terminology). This is free, high-impact, and makes your existing DIY engine production-grade. Estimated effort: 1-2 days.

3. **Add vanna and charm calculations to `greeks.py`** using the formulas already documented in `docs/research/04-gex-flow-darkpool.md:347-356`. This gives you VEX and CHEX without any external dependency. Estimated effort: 1 day.

4. **Evaluate FlashAlpha Basic ($49/mo) as a cross-validation layer.** Use it to compare your DIY GEX levels against an independent calculation. If they agree, you have confidence. If they diverge, investigate. Do NOT replace your DIY engine with FlashAlpha -- use it as a second opinion.

5. **If Borey wants SpotGamma's dashboard**, he should subscribe personally and treat it as a personal trading tool, separate from the system budget.

### Do NOT Do This:

- Do not spend 3 weeks integrating SpotGamma when there is no API.
- Do not scrape the SpotGamma dashboard. It will break.
- Do not pay $299/mo for data you already compute yourself.
- Do not assume FlashAlpha is reliable just because it has a nice API. It is one month old. Treat it as supplementary, not primary.
- Do not build HIRO from scratch right now. It is a significant engineering effort (~200 lines of non-trivial real-time logic) and the marginal value over your existing GEX analysis is uncertain. Revisit after the DIY bugs are fixed and vanna/charm are added.

### Cost Summary

| Scenario | Monthly System Cost | Annual | vs. SpotGamma Alpha |
|----------|-------------------|--------|---------------------|
| Fix DIY only | $0 | $0 | Save $3,588/year |
| Fix DIY + FlashAlpha Basic | $49 | $588 | Save $3,000/year |
| SpotGamma Alpha (proposed) | $299 | $3,588 | Baseline |
| SpotGamma Alpha + integration engineering | $299 + 3 weeks dev time | $3,588 + opportunity cost | Worst option |

---

## Sources

- [FlashAlpha Homepage](https://flashalpha.com/)
- [FlashAlpha Pricing](https://flashalpha.com/pricing)
- [FlashAlpha Python SDK (PyPI)](https://pypi.org/project/flashalpha/)
- [FlashAlpha Exposure API Docs](https://flashalpha.com/docs/lab-api-exposure)
- [FlashAlpha MCP Server](https://lobehub.com/mcp/flashalpha-lab-flashalpha-mcp)
- [FlashAlpha vs SpotGamma vs Unusual Whales Comparison (DEV Community)](https://dev.to/tomasz_dobrowolski_35d32c/options-analytics-comparison-flashalpha-vs-spotgamma-vs-unusual-whales-which-fits-your-stack-ogi)
- [FlashAlpha GitHub](https://github.com/FlashAlpha-lab)
- [SpotGamma Plans & Pricing](https://spotgamma.com/subscribe-to-spotgamma/)
- [SpotGamma Dashboard API (limited)](https://dashboard.spotgamma.com/docs/api/index.html)
- [SpotGamma Vol Trigger Explanation](https://support.spotgamma.com/hc/en-us/articles/15297954935699-Volatility-Trigger)
- [SpotGamma Call Wall Explanation](https://support.spotgamma.com/hc/en-us/articles/15297391724179-Call-Wall)
- [SpotGamma Put Wall Explanation](https://support.spotgamma.com/hc/en-us/articles/15297856056979-Put-Wall)
- [QuantData Platform](https://quantdata.us/)
- [QuantData MCP Server (third-party)](https://glama.ai/mcp/servers/zzulanas/quantdata-mcp)
- [Quiver Quantitative API](https://api.quiverquant.com/)
- [Optionomics API](https://optionomics.ai/features/api)
- [VannaCharm.com (free)](https://vannacharm.com/)
- [OptionsGEX.com (free)](https://optionsgex.com/)
- [GEX-Metrix (free)](https://www.gexmetrix.com/gamma_dashboard)
- [Project GEX Auditor Review](../../.planning/adversarial-review/02-gex-auditor.md)
- [Project GEX/Flow/Dark Pool Research](../../docs/research/04-gex-flow-darkpool.md)
