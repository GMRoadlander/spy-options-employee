# SPX Day Trader — Roadmap

> Milestone 1.0: From options alert bot to permanent research + paper trading platform

## Phase 1: MVP Data & Signals (~$18/mo) ✅ COMPLETE

**Goal**: Swap delayed CBOE data for real-time Tastytrade feed, upgrade AI to Sonnet, add TradingView webhooks and CheddarFlow flow parsing. Zero new analysis logic — just better data in, smarter commentary out.

**Deliverables**:
- [x] Tastytrade API integration (dxfeed WebSocket streaming, replaces CBOE CDN + Tradier)
- [x] Claude Sonnet commentary upgrade (replace Haiku)
- [x] TradingView webhook ingestion (FastAPI endpoint on droplet)
- [x] CheddarFlow Discord embed parser (listen to `#cheddarflow-raw`, filter SPX flow)
- [x] All 186 tests passing (130 original + 38 webhook/CheddarFlow + 18 Tastytrade)

**Estimated cost**: ~$18/mo (droplet $12 + Sonnet ~$6)

---

## Phase 2: Strategy Research Engine (~$150/mo) ✅ COMPLETE

**Goal**: Build the core strategy research loop. Borey defines strategies in plain English or YAML, the system backtests them against 18+ years of history, evaluates with a rigorous anti-overfitting pipeline, and reports results. This is where the bot's identity shifts from "alerting tool" to "trading research assistant."

**Deliverables**:
- [x] ORATS historical data integration ($99/mo) — EOD option chains back to 2007
- [x] Optopsy + custom Python backtesting engine for SPX options strategies
- [x] YAML-based strategy template system (Borey defines strategies, no code)
- [x] Natural language → structured strategy definition (Claude parses Borey's descriptions into YAML/JSON)
- [x] Strategy lifecycle state machine (IDEA → DEFINED → BACKTEST → PAPER → RETIRED)
- [x] Anti-overfitting evaluation pipeline:
  - Walk-Forward Analysis (12-month IS / 3-month OOS)
  - Combinatorial Purged Cross-Validation (CPCV, PBO < 0.50 gate)
  - Deflated Sharpe Ratio (DSR, p < 0.05 gate)
  - Monte Carlo simulation (1,000 runs, 5th-percentile Sharpe gate)
- [x] Signal logging — start tracking all alert outcomes now to build feedback dataset
- [x] Strategy evaluation metrics: Sharpe, Sortino, Calmar, max drawdown, win rate, expectancy, profit factor, regime-conditional analysis
- [x] Trade journal via Discord (daily summaries, weekly reviews, Borey rates and reviews)
- [x] Hypothesis testing framework (propose → formalize → test → prove/disprove)
- [x] Scale droplet to s-2vcpu-4gb ($24/mo)

**Research needed**: 🔬 ORATS API data format and rate limits, Optopsy integration with custom data, CPCV implementation via `skfolio` or `mlfinlab`, strategy template schema design

**Estimated cost**: ~$150/mo (ORATS $99 + droplet $24 + Sonnet ~$25)

---

## Phase 2.1: Code Review Fixes ✅ COMPLETE

**Goal**: Fix 7 critical and 15 warning issues found in Phase 2-3 (Discord Research Interface) code review. Security hardening, deprecated API replacement, error handling, type safety, and test coverage.

**Deliverables**:
- [x] `.gitignore`, matplotlib backend ordering, FK enforcement, style deduplication
- [x] Lifecycle `update_template()`, background task error handlers, sanitized exceptions, off-by-one fix, `_get_db()` helper
- [x] `datetime.utcnow()` -> `datetime.now(timezone.utc)` (23 replacements), timezone consistency
- [x] Color IndexError fix for >4 strategies, cooldowns, auth checks, AI client hardening (timeout, retry, reuse)
- [x] XML delimiters for prompts, typed PipelineResult, N+1 query fix, longer UUIDs
- [x] 7 new functional cog tests (457 total)

---

## Phase 3: ML Intelligence Layer (~$400/mo) ✅ COMPLETE

**Goal**: Add ML models that make the research engine smarter. Regime detection prevents wrong-strategy-in-wrong-market. Volatility forecasting improves entry timing. Anomaly detection catches institutional flow. Sentiment adds context signals.

**Deliverables**:
- [x] HMM regime detection (2-3 state: risk-on/risk-off/crisis) via `hmmlearn` — prevents catastrophic strategy-regime mismatches
- [x] LSTM volatility forecasting — predict IV changes for better entry timing, upgrade path to DeepAR for probabilistic forecasts
- [x] FinBERT sentiment analysis — free, CPU-only, use as regime context signal (not standalone predictor)
- [x] Statistical anomaly detection (z-scores on volume/OI, isolation forest on options flow features)
- [x] Feature store pipeline: IV rank, skew, term structure, GEX, P/C ratio, regime state, sentiment score, vol forecast → SQLite/Parquet
- [x] Unusual Whales Pro API ($99/mo) — flow + dark pool data
- [x] Polygon.io real-time OPRA feed ($199/mo) — tick-level options trades/quotes
- [x] Structured Claude reasoning engine (replaces multi-agent SDK per research — single call gives 80% of value)
- [x] Continuous learning — track which alerts/strategies worked, update confidence scores with Bayesian calibration
- [x] Discord ML cog with 6 slash commands + daily ML pipeline scheduling
- [x] Scale droplet to s-2vcpu-8gb ($48/mo)
- [x] 887 tests passing (430 new across 9 plans)

**Research needed**: 🔬 HMM state count tuning (2 vs 3 vs 4), LSTM feature selection (VIX + macro variables), FinBERT deployment on droplet CPU, Agent SDK sub-agent patterns, Polygon.io WebSocket integration

**Estimated cost**: ~$400/mo (Unusual Whales $99 + Polygon $199 + droplet $48 + AI ~$50)

---

## Phase 4: Paper Trading & Validation (~$400/mo) — IN PROGRESS (5/8 plans) — FINAL PHASE

**Goal**: Validate strategies with realistic paper trading simulation. Shadow mode generates signals. Paper trading engine simulates realistic fills with slippage. Strategies prove themselves with real market data. This is the final phase — the system is a permanent research + paper trading platform.

**Deliverables**:
- [x] Phase 3 bug fixes (prerequisite cleanup)
- [x] Paper trading engine core with realistic fill simulation
- [x] Slippage model (dynamic spread, configurable per strategy type)
- [x] Shadow mode & exit monitor
- [x] Paper portfolio analytics — Greeks aggregation, VaR, stress testing, position sizing, risk limits, circuit breakers
- [ ] Discord paper trading cog — interactive paper trading commands
- [ ] Discord performance reporting — daily summaries, weekly reviews, monthly deep reports, equity curves, strategy comparison
- [ ] Integration, wiring & E2E tests

**Research needed**: 🔬 Realistic SPX slippage modeling (bid-ask width by strike/DTE), portfolio correlation computation

**Estimated cost**: ~$400/mo (data sources carry forward + AI ~$50)

---

## Borey's Daily Workflow (Target State)

| Activity | Frequency | Time |
|----------|-----------|------|
| Read morning briefing | Daily | 1 min |
| Read/rate alerts during market | Real-time | 30 sec each |
| Read daily summary | Daily | 2 min |
| Weekly strategy review | Weekly | 10 min |
| Monthly deep review + new ideas | Monthly | 20 min |
| Define new strategy (NL or YAML) | As needed | 5 min |
| Review backtest results | As needed | 5 min |
| Review paper trading performance | As needed | 5 min |

**Total daily**: ~5 minutes. All via Discord — never touches code.

---

## Key Constraints (from Research)

- **LLMs in research/signal layer, NOT execution path** — latency makes LLM-in-the-loop execution impossible for intraday
- **Anti-overfitting pipeline is NON-NEGOTIABLE** — 90%+ of backtested strategies fail in production; WFA + CPCV + DSR + Monte Carlo is the minimum
- **HMM regime detection is highest-ROI ML model** — prevents catastrophic strategy-regime mismatches
- **SPX European/cash-settled** — eliminates early exercise, assignment, pin risk complexity
- **Strategy templates in YAML** — Borey defines, not a custom DSL
- **Advisory + paper trading permanently** — no live order execution; the system researches and validates, Borey decides

## Cost Structure

| Phase | Monthly Cost | Key Adds |
|-------|-------------|----------|
| Phase 1 (MVP) ✅ | ~$18 | Tastytrade (free), Sonnet (~$6), DO droplet ($12) |
| Phase 2 (Research) ✅ | ~$150 | +ORATS ($99), scale droplet ($24), +Sonnet ($25) |
| Phase 3 (ML) ✅ | ~$400 | +Polygon ($199), +Unusual Whales ($99), scale droplet ($48), +AI ($50) |
| Phase 4 (Paper) — FINAL | ~$400 | +AI ($50) |

---

*Roadmap created: 2026-02-21*
*Restructured: 2026-02-21 — identity shift from alert bot to trading research platform*
*Restructured: 2026-02-23 — removed Phase 5 (autonomous trading), system is permanent research + paper trading platform*
