# THE CASE AGAINST SPOTGAMMA: Don't Buy It. Here's Why.

**Reviewer**: Boris Cherney (adversarial steel-man)
**Date**: 2026-04-06
**Codebase snapshot**: commit 48cd5f0 (master), 1,503 tests, 59,096 lines
**Annual cost under review**: $3,588/year ($299/mo) or $2,760/year ($230/mo annual)
**Current data spend**: ~$400/mo ($4,800/year) across Polygon, ORATS, Unusual Whales

---

## EXECUTIVE SUMMARY

SpotGamma Alpha is a $299/month retail dashboard subscription being considered for integration into an automated quantitative research platform that already computes 5 of its 8 products from raw data, cannot programmatically consume the remaining 3, and has an ML stack that exceeds SpotGamma's analytical depth in every measurable dimension. The integration has no clean API path, no backtest capability, no way to verify the proprietary claims, and a structural mismatch between what SpotGamma delivers (dashboards for humans) and what this system requires (API data for machines). The recommendation is an unambiguous NO.

---

## ARGUMENT 1: You Already Have the Raw Data -- and You're Already Running the Math

This system has the OPRA feed. Every single options trade, every quote, every open interest figure that SpotGamma uses flows through Polygon.io into `src/data/polygon_client.py`. The ORATS subscription provides historical chains going back to 2007. The GEX engine in `src/analysis/gex.py` implements the textbook formula:

```
GEX = gamma * OI * 100 * S^2 * 0.01
```

This is not an approximation. This is the same formula SpotGamma uses. The only difference is the sign convention (which this codebase gets right: calls positive, puts negative) and the gamma computation (this system uses per-contract IV via Black-Scholes, which is actually more granular than SpotGamma's smoothed approach).

The overlap is not approximate. It is nearly total:

| SpotGamma Product | Your Code | Overlap |
|---|---|---|
| Call Wall | `GEXResult.gamma_ceiling` (line 267-270) | 95% |
| Put Wall | `GEXResult.gamma_floor` (line 274-276) | 95% |
| Vol Trigger / Zero Gamma | `_find_gamma_flip()` (line 93-125) | 90% |
| Hedge Wall | `gamma_floor` + trivial below-spot filter | 90% |
| Absolute Gamma Strike | `net_gex_by_strike` argmax (2 lines of code) | 85% |
| HIRO | `FlowAnalyzer` + Polygon OPRA + UW sweeps | 40% |
| TRACE Heatmap | N/A (dashboard for humans, not bots) | 0% |
| Founder's Notes | `src/ai/commentary.py` + Claude Sonnet | 80% |

Five of eight products are fully redundant. One is partially redundant. One is irrelevant to your architecture. One is a human writing emails.

You are being asked to pay $299/month for someone to run `np.argmax()` on data you already have.

---

## ARGUMENT 2: No Programmatic Access -- the Deal-Breaker

This is the argument that ends the conversation before the others even matter.

This system is API-driven. Every data source enters through an async Python client with structured return types:

- `PolygonClient` returns dicts, feeds `PolygonOptionsStream` via WebSocket
- `UnusualWhalesClient` returns typed dicts, feeds `FlowAnalyzer`
- `ORATSClient` returns `OptionsChain` objects
- `TastytradeClient` returns `OptionsChain` objects

SpotGamma has no equivalent. Their "Dashboard API" at `dashboard.spotgamma.com/docs/api/` is designed for rendering their own web UI, not for third-party consumption. The research doc (`docs/research/04-gex-flow-darkpool.md` line 54) explicitly notes: "API access appears limited to subscribers -- not a standalone data feed product."

The architecture review (`03-integration-architecture.md`) evaluated four integration paths. All four fail:

1. **Email parsing** (Founder's Notes): IMAP transport, unstructured prose, fragile NLP/regex parsing. No existing client uses email. This is worse than the CheddarFlow embed parser, which already required 131 lines of brittle regex for semi-structured Discord embeds.

2. **TradingView webhook bridge**: Requires Borey to manually configure TradingView alerts at SpotGamma levels. Defeats automation entirely. The man spends 5 minutes a day on Discord -- you want him to also configure TradingView alerts from a dashboard he'd need to check manually?

3. **HIRO API**: Best theoretical fit. Undocumented or semi-documented. You would be building against a black box API with no SLA, no versioning guarantees, and no fallback when they change it. SpotGamma is a 15-person company, not Bloomberg.

4. **Manual Discord input**: Borey types SpotGamma levels into Discord. This is literally hiring a human to be a data entry clerk for $0/hour while paying $299/month for the privilege.

$299/month buys you a browser tab. Zero bytes flow into your pipeline.

---

## ARGUMENT 3: The Proprietary Levels Are a Black Box You Cannot Verify

"Hedge Wall" and "Vol Trigger" sound authoritative. But what are they, precisely?

SpotGamma does not publish their exact methodology. Their Vol Trigger uses gamma calculated from OI and an IV surface -- the same inputs your `_find_gamma_flip()` uses. The difference is in the details: which IV model? What OI adjustments? What filtering thresholds? You do not know. You cannot know. They consider this proprietary IP.

This creates three fatal problems:

**You cannot backtest against them.** Your anti-overfitting pipeline (`src/backtest/pipeline.py`) runs WFA + CPCV + DSR + Monte Carlo. This pipeline requires historical signal data. SpotGamma does not provide historical levels via API. You cannot run a single backtest that says "when spot crossed the SpotGamma Vol Trigger, what happened next?" You have no history, no API, and no way to acquire either.

**You cannot validate them.** Your system computes its own gamma flip. If SpotGamma's Vol Trigger differs from yours by $3, which one is right? You have no way to resolve this. You would be running two conflicting signals with no empirical basis for preferring either. That is not intelligence -- that is noise.

**You cannot improve them.** If SpotGamma's model underperforms in a specific regime (say, 0DTE-heavy environments where intraday gamma changes rapidly), you cannot adjust the model. You are locked into their interpretation. Your own GEX engine, by contrast, is 308 lines of code you control completely. You can add vanna, charm, minimum OI thresholds, expiration weighting, or volume-adjusted OI estimates. You can modify it tomorrow. SpotGamma's model is frozen behind a paywall.

The Bayesian calibration pipeline (`src/ml/learning.py`) exists specifically to track signal accuracy and adjust confidence over time. It cannot calibrate a signal it cannot backtest.

---

## ARGUMENT 4: Opportunity Cost -- What Else $3,588/Year Buys

Assume the annual plan at $230/month ($2,760/year). Here is what that money could buy instead:

### Option A: Build the HIRO-Equivalent ($0 marginal cost)

HIRO is the one SpotGamma product with genuine non-redundant value. It tracks real-time dealer hedging impact from live trade flow. Here is what building it requires:

1. **Trade classification** (Lee-Ready or BVC from tick data): Polygon OPRA stream already delivers every trade with exchange ID and conditions via `PolygonOptionsStream._parse_event()`. The missing step is inferring buyer/seller initiation from quote context. Lee-Ready is a well-documented algorithm. Estimated: 1 day.

2. **Cumulative dealer delta tracking**: For each classified trade, compute the delta change it implies for dealer positions. This uses `black_scholes_gamma()` from `src/analysis/greeks.py` and the existing per-contract IV. Estimated: 1 day.

3. **Daily aggregation curve**: Accumulate into a single HIRO-like metric that resets at market open. Feed into `FlowAnalyzer` alongside existing Unusual Whales sweep/block data. Estimated: 1 day.

Total: 3 days of engineering. Marginal cost: $0 (uses existing Polygon subscription). And you own it forever.

### Option B: Improve Your ML Stack ($2,760 of compute or data)

- 28 months of additional ORATS data at $99/month (deep historical IV surfaces)
- GPU compute time for LSTM hyperparameter search
- Alternative data source exploration (CBOE livevol, QuantConnect data)
- VIX futures term structure integration for the HMM regime model

### Option C: Reduce Existing Data Costs

$2,760/year is 69% of your current annual data budget ($4,800/year). If SpotGamma added genuine value, this might be justifiable. It does not. You would be increasing total data costs by 57% for zero incremental signal.

### The 3-Week Engineering Cost

The original integration estimate was 3 weeks. Three weeks of engineering that:

- Produces no backtestable signals
- Creates a dependency on an undocumented API
- Adds a new client that breaks the existing `src/data/` pattern
- Requires ongoing maintenance as SpotGamma changes their dashboard
- Has no test coverage path (you cannot unit test against a black box)

Those 3 weeks could instead build:
- The HIRO-equivalent (3 days)
- Vanna and charm exposure tracking (2 days, formulas already documented in `docs/research/04-gex-flow-darkpool.md` lines 348-355)
- Volume-adjusted intraday GEX estimates (2 days)
- Gamma flip confidence scoring (1 day)
- GEX-by-strike bar charts for Discord embeds (1 day)

That is 9 days of high-value, testable, backtest-compatible improvements to your own engine. You would have 6 days left over to start on whatever else matters.

---

## ARGUMENT 5: Vendor Lock-In with No Exit Strategy

Consider the lifecycle:

1. You subscribe to SpotGamma Alpha ($299/month)
2. You spend 3 weeks building integration (email parser, webhook bridge, or HIRO API client)
3. Your system starts referencing SpotGamma levels in commentary and alerts
4. Borey begins making decisions informed by SpotGamma-specific concepts ("Hedge Wall", "HIRO")
5. SpotGamma raises prices (they raised them in 2025 already)
6. You are now paying more for data you could always compute yourself
7. Ripping out SpotGamma requires re-mapping all the concepts Borey now uses back to your native metrics

Compare to what happens when you build your own:

1. You write `_compute_hedge_wall()` in 5 lines (gamma_floor filtered to below-spot strikes)
2. You name it "Hedge Wall" or whatever Borey wants
3. You own it. You backtest it. You calibrate it. You improve it.
4. Nobody raises the price. Nobody changes the API. Nobody shuts down.

Unusual Whales has an exit path: their data is supplementary flow intelligence that enriches your signals but is not structurally load-bearing. If they raise prices, you lose sweep/block/dark pool overlay but your core GEX engine keeps working. SpotGamma would become structurally embedded if you build commentary and alerts around their proprietary level names.

---

## ARGUMENT 6: The Founder's Notes Trap

SpotGamma's Founder's Notes are 2x daily emails containing a human expert's interpretation of the gamma positioning landscape. Let us be precise about what you would be paying for:

- $299/month / ~22 trading days / 2 notes per day = **$6.80 per email**
- The notes contain morning market context and intraday update
- They reference SpotGamma's own levels (which you already compute)
- They provide qualitative market opinion

Now consider what you already have:

`src/ai/commentary.py` generates real-time commentary from Claude Sonnet using:
- GEX levels (gamma flip, ceiling, floor)
- Max pain distance
- Put/call ratios
- Squeeze probability
- Spot position relative to gamma flip (positive vs negative gamma territory)

AND the ML intelligence layer adds signals SpotGamma's human writer does not have:
- HMM regime state (risk-on / risk-off / crisis) from `src/ml/regime.py`
- LSTM 1-day and 5-day volatility forecasts from `src/ml/volatility.py`
- FinBERT news sentiment with velocity tracking from `src/ml/sentiment.py`
- IsolationForest anomaly scores from `src/ml/anomaly.py`
- Hurst exponent (trending vs mean-reverting) from `src/ml/features.py`
- RV/IV spread (variance risk premium) from `src/ml/features.py`
- 25-delta skew from `src/ml/features.py`

Your AI commentary system has strictly more signal inputs than a human reading the same OI data you already have. Is a human's morning email worth $6.80 when you have a Sonnet-powered analyst with a 15-feature daily feature store running 24/7?

The honest answer: a human expert with 10+ years of pattern recognition can sometimes see things a model misses. But that value decays rapidly when: (a) the human is writing a generic newsletter, not analyzing YOUR positions, (b) the human has fewer signals than your model, and (c) the human's insights arrive via email that nobody on this team reads because the entire UX is Discord.

---

## ARGUMENT 7: The Steel-Man Case FOR SpotGamma

I said I would be honest. Here is the strongest possible case for subscribing:

### The Self-Fulfilling Prophecy Effect

SpotGamma has approximately 50,000 subscribers. When 50,000 traders are all watching the same "Call Wall at 5950" and "Put Wall at 5850," their collective behavior at those levels creates real support and resistance. Market makers know SpotGamma's levels. Retail flow clusters at SpotGamma's levels. This creates a coordination game: the levels work partly BECAUSE everyone is watching them.

Your GEX engine computes levels from the same underlying data. Your gamma flip might be at 5917 while SpotGamma's Vol Trigger is at 5920. The $3 difference does not matter analytically -- but it matters behaviorally. If 50,000 traders have orders stacked at 5920 and your bot is watching 5917, you miss the flow concentration by $3.

**This is the one thing you cannot replicate.** You can match the math. You can exceed the ML. You can beat the commentary. But you cannot replicate the coordination effect of 50,000 pairs of eyes on the same exact numbers.

### Why the Steel-Man Still Fails

Three reasons this does not justify $299/month:

1. **You cannot programmatically access the consensus levels.** The coordination effect is real, but it only helps if your bot knows the exact levels 50,000 other traders are watching. Without API access, you have no way to know. You would need Borey to manually check the dashboard and type levels into Discord -- and Borey spends 5 minutes a day on the system. The coordination effect is real but inaccessible to your architecture.

2. **The coordination effect is self-limiting.** As more traders front-run SpotGamma levels, the levels become less reliable. When everyone has the same trade, it stops working. This is Goodhart's Law applied to options positioning: when a measure becomes a target, it ceases to be a good measure.

3. **$89/month Standard tier captures 90% of the value.** If Borey personally wants to eyeball SpotGamma's morning note for his own discretionary judgment, the Standard tier ($89/month) provides key levels and Founder's Notes. The Alpha tier's premium ($210/month extra) buys HIRO and TRACE -- a real-time dashboard and heatmap that a Discord bot cannot consume. You are paying $210/month for features designed for a human sitting at a multi-monitor trading desk, not a Python process running on a 2vCPU server.

---

## FINAL VERDICT

### Do not subscribe to SpotGamma Alpha.

| Factor | Assessment |
|---|---|
| Signal redundancy | 5 of 8 products fully computed by existing code |
| API integration path | None. Dashboard-only. Fundamental architecture mismatch. |
| Backtest capability | Zero. Cannot validate, cannot calibrate, cannot improve. |
| Proprietary value-add | HIRO (partially replicable in 3 days) + consensus effect (inaccessible via API) |
| Cost efficiency | $3,588/year for zero incremental bytes into the pipeline |
| Vendor lock-in risk | High. Proprietary level names create conceptual dependency. |
| Opportunity cost | 3 weeks of engineering + $3,588 diverted from own stack improvements |
| Test coverage impact | Untestable. Black box signals cannot be unit tested or backtested. |

### If Borey wants SpotGamma for personal discretionary use:

Subscribe to **Standard** ($89/month). It includes key levels and Founder's Notes. He can read it on his phone and overlay his own judgment. This is a personal subscription for a human trader, not a system integration expense.

### What to build instead (9 engineering days, $0 marginal cost):

1. **HIRO-equivalent** (3 days): Lee-Ready trade classification on Polygon OPRA stream, cumulative dealer delta tracking, daily aggregation curve fed into FlowAnalyzer
2. **Vanna + Charm exposure** (2 days): Second-order Greek calculations in `greeks.py`, per-strike exposure aggregation
3. **Volume-adjusted intraday GEX** (2 days): Estimate intraday OI changes from volume, refresh gamma flip throughout the day
4. **Gamma flip confidence** (1 day): Slope-at-crossing metric to distinguish meaningful flips from noise
5. **GEX bar chart for Discord** (1 day): Matplotlib per-strike GEX visualization as Discord image embeds

This produces more signal, more testable signal, more backtest-compatible signal, and more maintainable signal than SpotGamma Alpha -- at zero marginal cost, with no vendor dependency, and with full coverage in your 1,503-test suite.

The answer is no.

---

*"If you can compute it yourself, from data you already pay for, and backtest it against your own history, and calibrate it with your own learning pipeline -- why would you pay someone else to compute it for you and deliver it in a format your system cannot read?"*
