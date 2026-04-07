# SpotGamma Integration: ROI & Prioritization Review

**Reviewer:** Boris Cherney (adversarial)
**Date:** 2026-04-06
**Deadline:** April 27, 2026 (~3 weeks)
**Engineering capacity:** Limited (Gil solo + Claude Code)

---

## 1. Value Per Signal -- Ranked by P&L Impact

I'm going to be blunt: most of SpotGamma's products are **redundant with what you already built**. The codebase has 59k lines of GEX analysis, strike intelligence, max pain, PCR, HMM regime detection, and anomaly detection. Before chasing a shiny new data source, you need to honestly ask what SpotGamma provides that your existing pipeline does not.

### Tier 1: Would Actually Change Trading Decisions

| Signal | Impact | Why | Overlap with Existing |
|--------|--------|-----|----------------------|
| **Daily Key Levels (Call Wall, Put Wall, Vol Trigger, Hedge Wall)** | HIGH | These are SpotGamma's core value-add. They use proprietary aggregate GEX modeling across ALL expirations and ALL market makers, not just the single-expiry chain you currently analyze. Your `calculate_gex()` in `src/analysis/gex.py` only uses `nearest_expiry` by default. SpotGamma's Call Wall and Put Wall are the multi-expiry aggregate equivalents of your gamma ceiling/floor. The Vol Trigger tells you where the gamma regime flips -- your gamma_flip is the DIY version, but theirs incorporates more data. | ~60% overlap. Your GEX engine does the same math but on thinner data (single broker chain vs. aggregate OCC data). SpotGamma's edge is data breadth, not methodology. |
| **Absolute Gamma Strike** | HIGH | The strike with the highest total GEX, which acts as the strongest price magnet. Your `gamma_ceiling` is the call-side analogue, but SpotGamma computes this across the full OI surface. | ~50% overlap. Same concept, better data. |
| **Founder's Notes (expert commentary)** | MEDIUM-HIGH | Twice-daily expert interpretation. This is where SpotGamma earns its subscription -- the "so what" layer on top of the data. Your `ReasoningEngine` (Claude Sonnet) already does AI-generated commentary, but it lacks the domain expertise and intuition of a human who's been reading gamma flows for years. | ~30% overlap. Claude is generic; SpotGamma's founder is a specialist. The notes provide context your ML pipeline cannot generate. |

### Tier 2: Nice-to-Have, Won't Change Decisions

| Signal | Impact | Why | Overlap |
|--------|--------|-----|---------|
| **HIRO (real-time hedging impact)** | MEDIUM | Real-time hedging flow is interesting but your paper trading engine ticks every 2 minutes. HIRO is designed for intraday scalpers watching 1-minute bars. Your strategies have 15-min minimum hold times. The signal attenuates over your holding periods. | Low overlap, but also low relevance to your timeframe. |
| **Volatility Dashboard** | LOW | Dashboard-only. You already compute IV rank, IV percentile, 25-delta skew, term structure slope, RV/IV spread, and Hurst exponent via `src/ml/features.py`. You have an LSTM vol forecaster. A web dashboard you can look at adds zero programmatic value. | ~80% overlap. You built this already. |

### Tier 3: Noise

| Signal | Impact | Why | Overlap |
|--------|--------|-----|---------|
| **Equity Hub (3500+ tickers)** | ZERO | You trade SPX. Only SPX. This product is irrelevant. Do not waste one minute thinking about it. | N/A |
| **TRACE (S&P 500 heatmap)** | ZERO | Dashboard-only, no API, no data export. A picture you look at. Cannot be integrated. | N/A |

### Honest Assessment

Your existing GEX engine, strike intelligence, and ML pipeline cover **60-70% of what SpotGamma's Key Levels provide**. The gap is:

1. **Data breadth** -- SpotGamma uses aggregate OCC data across all market makers. You use a single broker chain.
2. **Multi-expiry aggregation** -- Your GEX defaults to `nearest_expiry`. SpotGamma aggregates across all expirations weighted by notional gamma.
3. **Expert commentary** -- Claude generates plausible-sounding analysis. SpotGamma's founder has been doing this for years and has edge-case pattern recognition that no model has.

The marginal value of SpotGamma over your existing pipeline is **30-40%**. That's real, but it's not the 10x improvement that would justify heroic engineering.

---

## 2. Engineering Effort vs. Value -- ROI per Integration Path

### Path 1: Manual Borey Input via Discord (< 1 day)

**What it is:** Borey reads SpotGamma dashboard, types key levels into Discord. Bot stores them and incorporates into analysis.

| Factor | Score | Notes |
|--------|-------|-------|
| Engineering effort | 0.5 days | Add a `/spotgamma` slash command that accepts Call Wall, Put Wall, Vol Trigger, Hedge Wall, Absolute Gamma Strike. Store in SQLite. Add to `MarketContext`. Display in existing embeds. |
| Ongoing maintenance | Near zero | No external API, no parsing, no auth. If SpotGamma changes their dashboard labels, who cares -- Borey types numbers. |
| Value captured | 70-80% | You get the key levels, which is the core trading signal. You get Borey's interpretation of Founder's Notes (he'll naturally adjust behavior based on what he reads). |
| Borey burden | 2-3 min/day | He's already spending 5 min/day in Discord. Reading SpotGamma dashboard + typing 5 numbers takes 2-3 min. Total becomes 7-8 min/day. |
| **ROI** | **Extremely high** | Value / effort = (0.75 * total_value) / 0.5_days = 1.5 value_units/day |

**What you'd build:**
- `src/data/spotgamma.py` -- SpotGammaLevels dataclass (call_wall, put_wall, vol_trigger, hedge_wall, abs_gamma, timestamp)
- SQLite table `spotgamma_levels` -- daily storage
- `/spotgamma set` slash command -- Borey inputs 5 numbers
- `/spotgamma show` slash command -- display current levels
- Inject into `MarketContext` -- add 5 fields to the reasoning engine context
- Inject into `StrikeIntelResult.key_levels` -- SpotGamma levels appear alongside your DIY levels
- Inject into `RiskManager` -- Vol Trigger can serve as a regime-flip signal (above = positive gamma, below = negative gamma)

This is ~150-200 lines of code. It could be done in a single focused session.

### Path 2: TradingView Webhook Bridge (2-3 days)

**What it is:** Set up TradingView alerts on SpotGamma TradingView indicators (if available with Alpha subscription). Alerts fire webhooks to your existing FastAPI endpoint.

| Factor | Score | Notes |
|--------|-------|-------|
| Engineering effort | 2-3 days | Extend `TradingViewAlert` model to parse SpotGamma-specific fields. Add routing logic in `WebhooksCog`. Handle duplicate/stale alerts. Test with real data. |
| Ongoing maintenance | LOW-MEDIUM | TradingView is a stable platform. Alert format is JSON you control via Pine Script. But you need to set up the alerts manually in TradingView, and SpotGamma may not expose their indicators as alertable Pine Script indicators on the Alpha plan. **This is an unknown.** |
| Value captured | 75-85% | Same levels as manual, but automated and more timely. Captures intraday changes. Does NOT capture Founder's Notes. |
| Borey burden | 0 min/day | Fully automated once set up. |
| **ROI** | **Medium-high** | Value / effort = (0.80 * total_value) / 2.5_days = 0.32 value_units/day |

**Critical unknown:** Does SpotGamma Alpha subscription include TradingView alertable indicators? If not, this path is dead on arrival. **Research this before committing a single hour.**

### Path 3: Founder's Notes Email Parser (4-5 days)

**What it is:** Parse incoming SpotGamma emails for key levels and commentary. Forward to Discord.

| Factor | Score | Notes |
|--------|-------|-------|
| Engineering effort | 4-5 days | IMAP polling or Gmail API. HTML email parsing (fragile). NLP extraction of key levels from prose. Template detection and fallback. Error handling for format changes. Testing with real emails. |
| Ongoing maintenance | **HIGH** | This is the trap. Email HTML templates change without notice. SpotGamma redesigns their email layout and your parser breaks silently -- it still runs, but extracts garbage. You won't know until Borey notices bad data. Every email template change requires debugging + fixing. Budget 2-4 hours/quarter for maintenance. |
| Value captured | 85-90% | You get both the levels AND the expert commentary (unique value). |
| Borey burden | 0 min/day | Fully automated. |
| **ROI** | **Low-medium** | Value / effort = (0.875 * total_value) / 4.5_days + maintenance = 0.19 value_units/day PLUS ongoing maintenance drain. |

**The Cherney objection:** Email parsing is the software equivalent of a Rube Goldberg machine. You're building a brittle parser for someone else's HTML, which they can change at any time, to extract data that Borey could type in 2 minutes. The incremental value over manual input (the Founder's Notes commentary) is real but not worth the maintenance burden. If you want the commentary, have Borey copy-paste the key paragraph into Discord.

### Path 4: HIRO API Real-Time Integration (5-7 days)

**What it is:** Direct API integration with SpotGamma's real-time hedging impact feed.

| Factor | Score | Notes |
|--------|-------|-------|
| Engineering effort | 5-7 days | API shape unknown. Auth mechanism unknown. Rate limits unknown. Data format unknown. You'd need to reverse-engineer or wait for documentation. WebSocket or polling? Unknown. |
| Ongoing maintenance | **UNKNOWN** | API stability unknown. SLA unknown. If SpotGamma changes their API, you're broken until you fix it. No public API documentation means no contract. |
| Value captured | 50-60% | HIRO is impressive technology but your paper trading engine ticks every 2 minutes and strategies have 15-min minimum holds. Real-time hedging impact data is overkill for your timeframe. You'd be building Ferrari engineering for a go-kart track. |
| Borey burden | 0 min/day | Fully automated. |
| **ROI** | **Negative** | Value / effort = (0.55 * total_value) / 6_days + unknown_maintenance = 0.09 value_units/day. And that's being generous about the value. |

**The Cherney objection:** You don't know the API shape. You don't know if Alpha even includes API access (it probably doesn't -- API access is typically enterprise tier). You're proposing to spend a week building an integration for a product whose primary value (real-time hedging impact) is mismatched with your system's architecture (2-minute ticks, 15-min holds). This is engineering fantasy.

### ROI Summary Table

| Path | Effort (days) | Value (%) | ROI (value/day) | Maintenance (/yr) | Recommendation |
|------|--------------|-----------|------------------|--------------------|----------------|
| 1. Manual Borey | 0.5 | 75% | 1.50 | ~0 hrs | **DO THIS** |
| 2. TradingView | 2.5 | 80% | 0.32 | ~4 hrs | Maybe later, if indicators exist |
| 3. Email parser | 4.5 | 88% | 0.19 | ~12 hrs | Don't |
| 4. HIRO API | 6.0 | 55% | 0.09 | Unknown | Absolutely not |

---

## 3. The 3-Week Deadline -- What Can Ship by April 27?

Let me be concrete about what "shipped" means. It doesn't mean "code written." It means:
- Code written and tested
- Integrated with existing 1,466 tests (none broken)
- Deployed and running
- Borey trained on how to use it
- Observed in production for at least a few trading days to catch issues

Working backwards from April 27:

| Week | Dates | What Can Ship |
|------|-------|---------------|
| Week 1 | Apr 7-11 | **Path 1: Manual input.** Build + test + deploy + train Borey. This ships by Wednesday. |
| Week 1-2 | Apr 9-16 | **Validate Path 2 feasibility.** Does SpotGamma Alpha include TradingView indicators? Can they be alerted? If no: stop here, Path 1 is your integration. If yes: continue. |
| Week 2-3 | Apr 14-23 | **Path 2: TradingView bridge (conditional).** Only if Week 1-2 validation passes. Build + test + deploy. |
| Week 3 | Apr 24-27 | **Soak period.** Watch for bugs. Fix issues. Do NOT start new features in the last 3 days. |

**What CANNOT ship by April 27:**
- Email parser (4-5 days + testing + no soak time)
- HIRO API (5-7 days + unknown unknowns)
- Any fundamental architecture changes

**What SHOULD ship by April 27:**
- Path 1 (manual input) -- this is a certainty
- Path 2 (TradingView) -- this is conditional on SpotGamma's product capabilities

---

## 4. MVP vs. Full Integration

### MVP (Day 1 -- ships before subscription even starts)

Build Path 1 in advance. On the day the SpotGamma subscription activates:
- Borey opens SpotGamma dashboard
- Types 5 numbers into `/spotgamma set`
- System incorporates them immediately
- Paper trading decisions now consider SpotGamma levels
- Done

**Technical scope:**
```
src/data/spotgamma.py          -- SpotGammaLevels dataclass + SQLite CRUD
src/discord_bot/cog_spotgamma.py -- /spotgamma set, /spotgamma show
Modify src/ai/reasoning.py     -- Add SG levels to MarketContext
Modify src/analysis/strike_intel.py -- SG levels as KeyLevel entries
Modify src/risk/manager.py     -- Vol Trigger as regime boundary
~200 lines new code, ~30 lines modified
```

### Full Dream State (3-6 months)

- TradingView webhook automation for level updates (if available)
- SpotGamma levels as features in the ML pipeline (HMM regime detection, position sizing)
- Backtest engine consuming historical SpotGamma levels (requires SpotGamma historical data -- probably not available)
- Comparative analysis: your DIY GEX vs. SpotGamma levels (who's more accurate?)
- Auto-calibration: if SpotGamma's Vol Trigger consistently predicts regime changes 30 minutes before your HMM, increase its weight

**The honest truth:** Most of the "full dream state" requires either data that SpotGamma doesn't provide (historical level data for backtesting) or engineering time that would be better spent improving your existing models. The MVP captures the majority of the value.

---

## 5. Maintenance Burden -- 12-Month Total Cost of Ownership

| Path | Build (days) | Annual Maintenance (hrs) | Break Frequency | Recovery Time | Total 12-mo Cost |
|------|-------------|-------------------------|-----------------|---------------|-------------------|
| 1. Manual | 0.5 | 0-2 | Never | N/A | 0.5 days |
| 2. TradingView | 2.5 | 4-8 | Rare (alert changes) | 1-2 hrs | 3.5-4.5 days |
| 3. Email | 4.5 | 12-20 | 2-4x/year (template changes) | 2-4 hrs each | 6-8 days |
| 4. HIRO API | 6.0 | 20-40+ | Unknown (no SLA) | Unknown | 9-16+ days |

**The compounding cost problem:** Every automated integration is a system you have to monitor. When it breaks at 9:25 AM on a Monday, you're debugging SpotGamma email HTML instead of making trading decisions. Manual input has zero breakage surface area.

---

## 6. The Uncomfortable Question

> If manual Borey input (< 1 day to build) gives 80% of the value, is it worth spending 2-3 weeks automating the remaining 20%?

**No. It is not.**

Here's the math:
- Manual input cost: 0.5 engineering days to build + 2-3 min/day of Borey's time
- Automation cost: 2.5-7 engineering days to build + 4-40 hrs/year maintenance
- Borey's time cost over 12 months: ~3 min * 252 trading days = 12.6 hours/year
- Automation payback period: 2.5 days / 12.6 hrs/yr = you need to run for ~5 years to break even vs TradingView, longer for email/API

And that's before maintenance. After maintenance, **automation never breaks even.**

The 2-3 weeks you'd spend automating SpotGamma ingestion could instead be used for:
- Fixing the multi-expiry GEX aggregation gap (your `calculate_gex()` only does `nearest_expiry`)
- Adding SpotGamma levels as ML features for regime detection improvement
- Running a comparative study: your DIY levels vs. SpotGamma levels to calibrate your existing pipeline
- Building the P&L attribution engine that tells you WHICH signals are actually driving paper trading performance

All of those have higher expected ROI than saving Borey 3 minutes a day.

**Exception:** If SpotGamma has alertable TradingView indicators AND the integration is clean AND it takes less than 2 days, do it. But only after Path 1 is shipped and running. And only if there's nothing higher-value to work on.

---

## 7. Sequencing -- Optimal Build Order

### Phase A: Ship Before Subscription Starts (Apr 7-11)

**Goal:** Have the system ready before SpotGamma data is available.

1. Build `SpotGammaLevels` dataclass and SQLite storage (2 hrs)
2. Build `/spotgamma set` and `/spotgamma show` Discord commands (2 hrs)
3. Integrate levels into `MarketContext` for Claude reasoning (1 hr)
4. Add SpotGamma levels to `StrikeIntelResult.key_levels` (1 hr)
5. Add Vol Trigger as regime signal input to risk manager (1 hr)
6. Tests (2 hrs)
7. Deploy + verify (1 hr)

**Total: ~1 day.** Could be done in a single focused session.

### Phase B: Validate TradingView Path (Apr 11-16)

**Gate:** Answer these questions BEFORE writing any code:
- Does SpotGamma Alpha include TradingView indicators?
- Are those indicators alertable (Pine Script `alertcondition()`)?
- What data comes through the alert? JSON format? Which fields?
- Does the alert include level values or just "level crossed" signals?

**How to answer:** Read SpotGamma Alpha documentation. If unclear, email their support. This takes 1-3 days of waiting, zero engineering time.

If the answer is NO to any of these: **stop. Path 1 is your final state.** Move engineering time to improving existing ML models.

### Phase C: TradingView Bridge -- Conditional (Apr 16-23)

**Only execute if Phase B answers are all YES.**

1. Design alert payload format (map SpotGamma fields to your model) (2 hrs)
2. Extend `TradingViewAlert` model for SpotGamma-specific payloads (2 hrs)
3. Add routing logic to distinguish SpotGamma alerts from regular TV alerts (2 hrs)
4. Update `SpotGammaLevels` storage to accept automated updates (1 hr)
5. Handle staleness (if no alert by 9:45 AM, warn Borey to input manually) (2 hrs)
6. Tests (3 hrs)
7. Deploy + verify with live SpotGamma data (when available) (2 hrs)

**Total: ~2 days.** Plus 2-3 days of soak time before trusting it.

### Phase D: Never

- Email parsing
- HIRO API integration
- Any other automation path

These are not worth the engineering time. Period.

---

## Summary Verdict

| Question | Answer |
|----------|--------|
| What to build first? | Manual input via `/spotgamma set` (Path 1) |
| What to build second? | TradingView bridge, ONLY if indicators are alertable (Path 2) |
| What to never build? | Email parser, HIRO API |
| Can it ship by April 27? | Path 1: easily. Path 2: probably, if feasible. |
| Is automation worth it? | Only TradingView, only if nearly free. Email/API: no. |
| Where should remaining time go? | Fix your multi-expiry GEX aggregation. Add SpotGamma levels as ML features. Build P&L attribution to measure signal value. |

The highest-ROI move is the boring one: build the manual input, get Borey using it, measure whether SpotGamma levels actually improve paper trading P&L, and only then decide if automation is justified by the evidence.

Don't spend engineering time solving a problem that 3 minutes of Borey's time solves equally well.

---

*"The best automation is the one you don't build." -- every engineer who's maintained an email parser at 3 AM*
