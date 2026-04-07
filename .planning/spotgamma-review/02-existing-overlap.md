# SpotGamma Alpha ($299/mo) vs Existing Codebase: Overlap Audit

**Reviewer**: Boris Cherney (adversarial)
**Date**: 2026-04-06
**Verdict**: Do not subscribe. The overlap is massive, the proprietary edge is narrow, and the integration path is broken.

---

## Executive Summary

SpotGamma Alpha provides 8 distinct data products. Of those 8, **5 are directly computable from data we already have**, 1 is partially computable, and only 2 have genuine proprietary value. Of those 2 proprietary products, neither has a usable API for bot integration. You would be paying $299/month to manually eyeball a dashboard that cannot feed your automated pipeline. That is not a data subscription -- it is a SaaS seat license for a human who doesn't exist on this team.

---

## Signal-by-Signal Overlap Analysis

### 1. Call Wall

**What SpotGamma provides**: The strike with the largest net call open interest. This is SpotGamma's term for the strike where dealers have the most short call exposure, acting as a resistance ceiling because dealer hedging (selling into rallies) accelerates as price approaches it.

**Can we compute this?** YES -- we already do.

**Our equivalent**: `src/analysis/gex.py` line 267-270:
```python
# Gamma ceiling: strike with highest CALL GEX
if call_gex_list and max(call_gex_list) > 0:
    max_call_idx = int(np.argmax(call_gex_list))
    gamma_ceiling = strikes_list[max_call_idx]
```
Plus `src/analysis/strike_intel.py` line 80-82 (`_find_high_oi_strikes`) which finds the top-N call strikes by raw OI.

**How close?** ~95% equivalent. SpotGamma's Call Wall is the strike with max call OI. Our `gamma_ceiling` is the strike with max call GEX (gamma * OI * S^2), which is a strictly better signal because it weights by gamma exposure, not raw OI. A deep OTM strike with massive OI but near-zero gamma contributes nothing to dealer hedging; our approach correctly ignores it. SpotGamma's simpler metric can diverge from ours only when a high-OI strike is far enough OTM that its gamma is negligible -- in which case our version is right and theirs is misleading.

**Redundancy**: FULL. Our version is arguably superior.

---

### 2. Put Wall

**What SpotGamma provides**: The strike with the largest net put open interest. Support floor from dealer hedging (buying into dips as price approaches).

**Can we compute this?** YES -- we already do.

**Our equivalent**: `src/analysis/gex.py` line 274-276:
```python
# Gamma floor: strike with highest absolute PUT GEX
if put_gex_list and max(abs(p) for p in put_gex_list) > 0:
    max_put_idx = int(np.argmax([abs(p) for p in put_gex_list]))
    gamma_floor = strikes_list[max_put_idx]
```
Plus `_find_high_oi_strikes` returning top put OI strikes.

**How close?** Same analysis as Call Wall. ~95% equivalent, and the GEX-weighted version we compute is the more meaningful metric.

**Redundancy**: FULL.

---

### 3. Vol Trigger (Gamma Flip / Zero Gamma Level)

**What SpotGamma provides**: The price level where dealer net gamma exposure crosses from positive to negative. Above Vol Trigger = dealers suppress volatility (long gamma). Below Vol Trigger = dealers amplify volatility (short gamma). This is arguably SpotGamma's single most important level.

**Can we compute this?** YES -- we already do, and the implementation is textbook correct.

**Our equivalent**: `src/analysis/gex.py` line 93-125 (`_find_gamma_flip`):
```python
def _find_gamma_flip(strikes, net_gex_by_strike):
    # Scans for sign change, linear interpolation at zero crossing
    for i in range(len(strikes) - 1):
        if gex_a * gex_b < 0:
            flip = strike_a - gex_a * (strike_b - strike_a) / (gex_b - gex_a)
            return float(flip)
```

**How close?** ~90% equivalent. Both use the same OI-based GEX calculation and find the zero crossing. SpotGamma may use a slightly different gamma model (potentially incorporating their own IV surface smoothing rather than per-contract IV), but the difference is academic. The research doc at `docs/research/04-gex-flow-darkpool.md` explicitly confirms: "Nobody provides truly real-time GEX because open interest is only updated once per day (T+1 data from OCC)." SpotGamma and our code both face the same stale-OI constraint.

**What SpotGamma might do better**: They may use ORATS-style smoothed IV rather than raw per-contract IV for their gamma calculations. This could produce a slightly more stable gamma flip level. However, our approach of using each contract's own IV is also defensible and is the standard academic method.

**Redundancy**: FULL.

---

### 4. Hedge Wall

**What SpotGamma provides**: The strike level below which dealer hedging activity creates a "wall" of support -- specifically, the strike with the largest put OI that is below the current spot price. It represents the level where put-driven delta hedging flows are strongest.

**Can we compute this?** YES -- trivially derivable from existing data.

**Our equivalent**: Not explicitly named "Hedge Wall" but `_find_high_oi_strikes` returns the top put strikes by OI, and `gamma_floor` serves the same functional purpose. The strike intel module at line 99 assigns it significance 0.85 and labels it `gamma_floor`. The only difference is naming convention.

**How close?** ~90%. SpotGamma's Hedge Wall is specifically defined as the highest put OI strike below spot. Our `gamma_floor` is the highest absolute put GEX strike (which could theoretically be above spot in unusual conditions, though practically this almost never happens for SPX). A one-line filter `if strike < spot` would make them identical.

**Redundancy**: FULL.

---

### 5. Absolute Gamma Strike

**What SpotGamma provides**: The strike with the highest total (call + put) gamma exposure. Where the combined dealer hedging effect is strongest, regardless of direction.

**Can we compute this?** YES -- trivially derivable from existing data.

**Our equivalent**: We compute `net_gex_by_strike` in `gex.py` line 256-261. The absolute gamma strike is simply:
```python
max_abs_idx = int(np.argmax([abs(g) for g in net_gex_list]))
absolute_gamma_strike = strikes_list[max_abs_idx]
```
This is a 2-line addition, not a $299/month subscription.

We do not currently expose this as a named level, but the data to compute it is already in `GEXResult.net_gex_by_strike`. It could be added to `StrikeIntelResult.key_levels` in approximately 10 minutes.

**Redundancy**: FULL (with a trivial code addition).

---

### 6. HIRO (Hedging Impact Real-time Overlay)

**What SpotGamma provides**: A real-time intraday indicator that tracks the hedging impact of options trades as they occur. It uses live transaction data to estimate real-time changes in dealer delta exposure, producing an intraday flow signal that goes beyond stale OI-based GEX.

**Can we compute this?** PARTIALLY -- we have the raw ingredients but not the assembled product.

**What we have**:
- **Polygon.io OPRA WebSocket stream** (`src/data/polygon_client.py`): Real-time options trades and quotes. This is the raw feed HIRO would consume.
- **Unusual Whales flow data** (`src/data/unusual_whales_client.py`): Sweep counts, block trades, premium flows, dark pool ratio -- all already integrated into `FlowAnalyzer` (`src/ml/anomaly.py` line 550+).
- **FlowAnalyzer** (`src/ml/anomaly.py`): Already combines UW flow + Polygon real-time data into unified flow summaries with anomaly flags (sweep surge, premium spike, dark pool divergence).
- **IsolationForest anomaly detection** (`FlowAnomalyDetector`): Multi-feature anomaly scoring on live flow data, including volume, OI, V/OI ratio, IV, premium, delta, gamma, moneyness.

**What we're missing**: The specific logic to convert real-time trade flow into a cumulative delta hedging impact curve. HIRO tracks: for each options trade, estimate whether it was a customer buy or sell (from trade classification algorithms), compute the resulting dealer delta change, and accumulate over the day. We have the raw trade stream (Polygon OPRA) and the flow intelligence (Unusual Whales), but we have not built the trade classification + cumulative delta accumulation logic.

**Could we build it?** Yes, but it would require:
1. Trade classification algorithm (Lee-Ready or BVC from tick data -- moderate complexity)
2. Cumulative dealer delta tracking per strike across the day
3. Real-time aggregation into a single HIRO-like curve

Estimated effort: 2-4 days of engineering. The Polygon WebSocket stream gives us the raw trades; the missing piece is the trade-direction inference and accumulation pipeline.

**SpotGamma's proprietary edge**: Their trade classification accuracy. SpotGamma has been refining their algorithm for years using their dxFeed data feed. Our Polygon data is the same underlying OPRA feed, but SpotGamma's interpretation layer (deciding "this trade was a customer buy" vs "dealer initiation") is where their IP lies.

**Redundancy**: PARTIAL (~40% overlap). We have the data; they have the interpretation pipeline. But our FlowAnalyzer + UW sweep/block data provides a cruder version of the same signal.

---

### 7. TRACE Heatmap

**What SpotGamma provides**: A real-time visual heatmap showing how dealer positioning changes throughout the trading day across strikes and expirations. It is a dashboard visualization tool, not a data feed.

**Can we compute this?** NO -- and it would not matter if we could.

**Why it's irrelevant**: TRACE is a visual dashboard feature. This project is a Discord bot. Borey interacts via text messages, not by staring at a heatmap. There is no API to export TRACE data, and even if there were, rendering a heatmap in Discord is a poor UX compared to the text-based key levels our bot already provides. Our `GEXResult` dataclass with its per-strike breakdown (`strikes`, `call_gex`, `put_gex`, `net_gex_by_strike`) contains the same underlying data that TRACE visualizes -- we just present it differently.

**What we have instead**: Matplotlib chart generation capability (matplotlib is in the tech stack). We could generate static GEX-by-strike bar charts and post them as Discord embeds if Borey wants a visual. This is a 1-hour task, not a $299/month subscription.

**Redundancy**: N/A (wrong delivery medium for this project).

---

### 8. Founder's Notes / Commentary

**What SpotGamma provides**: 2x daily expert commentary interpreting the GEX/positioning landscape, written by the SpotGamma team. This includes market regime assessment, key level interpretations, and intraday scenarios.

**Can we compute this?** YES -- we already do, and arguably better.

**Our equivalent**: `src/ai/commentary.py` uses Claude (Sonnet) to generate real-time commentary from our analysis data. The system prompt at line 36+ instructs Claude to:
- Focus on actionable intelligence
- Reference specific GEX levels (gamma flip, ceiling, floor)
- Highlight extreme conditions (squeeze probability, PCR extremes)
- State directional bias with qualifying levels
- Mention max pain as expiry gravitational target

Additionally, our commentary system has access to signals SpotGamma's notes do not: HMM regime state (`src/ml/regime.py`), LSTM vol forecast (`src/ml/volatility.py`), FinBERT news sentiment (`src/ml/sentiment.py`), anomaly scores (`src/ml/anomaly.py`), and Unusual Whales flow data. Our AI commentary is richer in signal inputs than SpotGamma's human-written notes.

**How close?** Different modality but same purpose. SpotGamma's notes are written by experienced options traders with years of pattern recognition. Our commentary is generated by Claude from a richer feature set but without the decades of intuition. For a team where the domain expert (Borey) provides his own interpretation, the Claude commentary is a complement, not a replacement for human judgment -- and neither is SpotGamma's notes.

**Redundancy**: FULL (different source, same function).

---

## What SpotGamma CAN'T Provide That We Already Have

This is the part the sales pitch omits. Our system has capabilities SpotGamma does not offer at any price:

| Capability | Our System | SpotGamma |
|---|---|---|
| HMM regime detection (risk-on/risk-off/crisis) | `src/ml/regime.py` -- BIC-selected 2-3 state Gaussian HMM | No |
| LSTM volatility forecasting (1d + 5d ahead) | `src/ml/volatility.py` -- 60-day lookback, macro features | No |
| FinBERT news sentiment scoring | `src/ml/sentiment.py` -- ProsusAI/finbert, velocity tracking | No |
| IsolationForest anomaly detection | `src/ml/anomaly.py` -- 9-feature flow anomaly scoring | No |
| Bayesian confidence calibration | `src/ml/learning.py` -- Beta-Binomial conjugate updating | No |
| Feature store with 15 daily features | `src/ml/feature_store.py` -- persistent, queryable | No |
| IV rank, IV percentile, 25d skew | `src/ml/features.py` -- computed from raw chain data | Dashboard only |
| RV/IV spread (variance risk premium) | `src/ml/features.py` -- annualized, rolling window | No |
| Hurst exponent (trending vs mean-reverting) | `src/ml/features.py` -- R/S analysis, OLS fit | No |
| Jump-diffusion Monte Carlo odds | `src/analysis/combo_odds.py` -- regime-aware, 100K paths | No |
| Unusual Whales flow + dark pool integration | `src/ml/anomaly.py` FlowAnalyzer | No |
| Paper trading with slippage modeling | `src/paper/` | No |
| Anti-overfitting pipeline (WFA, CPCV, DSR) | `src/backtest/` | No |

SpotGamma is a retail dashboard. This system is a quantitative research platform. Subscribing to SpotGamma would be like buying a graphing calculator when you already have MATLAB.

---

## The API Problem (Deal-Breaker)

Even if SpotGamma had unique value, the integration path is broken:

1. **No clean data API**: SpotGamma's "Dashboard API" at `dashboard.spotgamma.com/docs/api/` is designed for rendering their web dashboard, not for programmatic data extraction. The research doc at `docs/research/04-gex-flow-darkpool.md` line 54 explicitly notes: "API access appears limited to subscribers -- not a standalone data feed product."

2. **No Python SDK**: Unlike Unusual Whales (which has `unusualwhales-python-client` on PyPI and an MCP server), SpotGamma offers TradingView/ThinkorSwim integrations -- visual platform integrations, not data APIs.

3. **Manual monitoring required**: The original research doc's verdict (line 72): "Pass unless manual monitoring is acceptable." Manual monitoring is explicitly not acceptable on this team -- Borey spends ~5 min/day via Discord.

4. **No webhook/push model**: Even if you scraped their dashboard, you'd need to poll for updates. Their data updates at fixed times (pre-market, mid-day), not in real-time.

This means subscribing to SpotGamma Alpha would give you a browser tab that nobody looks at. The $299/month buys zero additional data flowing into the bot.

---

## Cost-Benefit Analysis

### What $299/month buys:
- A dashboard login with HIRO and TRACE visuals
- 2x daily founder's notes emails
- EquityHub (3,500+ stock GEX levels -- irrelevant, we only trade SPX)

### What $299/month does NOT buy:
- Any data feed into our pipeline
- Any signal we cannot already compute
- Any improvement to our existing GEX accuracy
- Any real-time capability our Polygon + UW stack doesn't already provide

### Opportunity cost:
- $299/month = $3,588/year
- That buys 3 months of a $99/month Unusual Whales Pro subscription (already integrated) + $99/month ORATS IV surface data (recommended for Phase 3) with $1,200 left over
- Or: 35 hours of engineering time at $100/hr to build a proper HIRO-equivalent from our Polygon OPRA stream

---

## Specific Recommendations

### Do NOT subscribe to SpotGamma Alpha. The justification:

1. **5 of 8 products are fully redundant** with existing code in `src/analysis/gex.py`, `src/analysis/strike_intel.py`, and `src/ai/commentary.py`.

2. **1 product (TRACE) is irrelevant** to a Discord bot architecture.

3. **1 product (HIRO) is partially replicable** and the non-replicable portion (trade classification accuracy) can be approximated using our existing Unusual Whales flow data + Polygon OPRA stream.

4. **1 product (Founder's Notes) is redundant** with Claude-generated commentary that has access to more signals.

5. **The API gap is a hard blocker.** No integration path exists.

### If you want HIRO-equivalent functionality, build it:

1. Extend `PolygonOptionsStream` to classify incoming trades (buyer/seller initiated) using Lee-Ready tick test
2. Track cumulative dealer delta impact per strike
3. Aggregate into a single daily hedging flow metric
4. Feed into `FlowAnalyzer` alongside existing UW data

Estimated effort: 3 days. Estimated cost: $0 (uses existing Polygon subscription).

### If you want the ONE thing SpotGamma does better:

SpotGamma's only genuine edge is **community consensus** -- 50,000 subscribers watching the same levels creates a self-fulfilling prophecy at those exact strikes. You cannot replicate this. But you also cannot programmatically access it, so it is irrelevant to an automated system. If Borey personally finds value in reading SpotGamma's notes for his own discretionary overlay, he should subscribe at the $89/month Standard tier, not Alpha.

---

## Overlap Summary Table

| SpotGamma Product | Our Equivalent | Overlap | Monthly Value-Add |
|---|---|---|---|
| Call Wall | `GEXResult.gamma_ceiling` + `_find_high_oi_strikes` | 95% | $0 |
| Put Wall | `GEXResult.gamma_floor` + `_find_high_oi_strikes` | 95% | $0 |
| Vol Trigger | `GEXResult.gamma_flip` via `_find_gamma_flip()` | 90% | $0 |
| Hedge Wall | `GEXResult.gamma_floor` (filter to below-spot) | 90% | $0 |
| Absolute Gamma Strike | `GEXResult.net_gex_by_strike` (2-line argmax) | 85% | $0 |
| HIRO | `FlowAnalyzer` + Polygon OPRA + UW sweeps | 40% | ~$0-50 (build cost) |
| TRACE Heatmap | N/A (wrong medium for Discord bot) | 0% | $0 |
| Founder's Notes | `src/ai/commentary.py` + Claude Sonnet | 80% | $0 |
| **Total recoverable value from $299/mo** | | | **$0-50** |

**Bottom line**: You are being asked to pay $299/month for data you can already compute, delivered through a medium your system cannot consume, to solve a problem you have already solved. The answer is no.
