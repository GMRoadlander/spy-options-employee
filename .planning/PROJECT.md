# SPX Day Trader

> Trading research assistant that evolves into an autonomous SPX options trader — Borey defines strategies in plain English, the system backtests, validates, paper trades, and ultimately executes with three-layer guardrails. Advisory only through Phases 1-4; Phase 5 introduces autonomous trading.

## Vision

Evolve the existing Discord-based options analysis bot into a full strategy research and trading platform. Five-phase roadmap: real-time data (done), strategy research engine with rigorous backtesting, ML intelligence layer, paper trading validation, and finally autonomous execution. The system's core loop is: Borey describes a strategy → AI translates to structured rules → backtest against 18+ years of history → anti-overfitting pipeline → paper trade → prove it works → go live.

## Requirements

### Validated

- ✓ Discord bot with slash commands (/gex, /maxpain, /levels, /strikes, /pcr, /status, /analyze) — existing
- ✓ GEX analysis engine (net GEX, gamma flip, ceiling, floor, squeeze probability) — existing
- ✓ Max Pain calculation with distance tracking — existing
- ✓ Put/Call Ratio analysis with dealer positioning signals — existing
- ✓ Strike Intelligence (key levels, recommendations) — existing
- ✓ Black-Scholes Greeks calculation (delta, gamma, theta, vega, P(ITM)) — existing
- ✓ AI commentary via Claude Sonnet — upgraded from Haiku
- ✓ SQLite persistence (snapshots + alert cooldowns) — existing
- ✓ Background scheduler (2-min market hours loop, ET-aware) — existing
- ✓ Smart alerts (gamma flip, squeeze, max pain convergence, OI shift) — existing
- ✓ Chart generation (matplotlib GEX/max pain charts) — existing
- ✓ Docker deployment with docker-compose on OpenClaw — existing
- ✓ Tastytrade API real-time data (dxfeed WebSocket) — Phase 1
- ✓ TradingView webhook ingestion (FastAPI) — Phase 1
- ✓ CheddarFlow Discord embed parser — Phase 1
- ✓ 186 unit tests passing — Phase 1

### Active — Phase 2 (Strategy Research Engine, ~$150/mo)

- [ ] **ORATS historical data** ($99/mo) — EOD option chains back to 2007 for backtesting
- [ ] **Backtesting engine** — Optopsy + custom Python for SPX options strategies
- [ ] **YAML strategy templates** — Borey defines strategies in structured YAML, no code
- [ ] **NL → strategy definition** — Claude parses Borey's plain English descriptions into structured rules
- [ ] **Strategy lifecycle** — IDEA → DEFINED → BACKTEST → PAPER → LIVE → RETIRED state machine
- [ ] **Anti-overfitting pipeline** — Walk-Forward + CPCV + Deflated Sharpe + Monte Carlo (non-negotiable)
- [ ] **Signal logging** — Track all alert outcomes to build feedback dataset
- [ ] **Strategy evaluation metrics** — Sharpe, Sortino, Calmar, drawdown, regime-conditional analysis
- [ ] **Trade journal** — Discord-based daily/weekly/monthly summaries, Borey reviews
- [ ] **Hypothesis testing framework** — Propose → formalize → test → prove/disprove

### Future — Phase 3 (ML Intelligence Layer, ~$400/mo)

- [ ] HMM regime detection (risk-on/off/crisis) — highest-ROI ML model
- [ ] LSTM volatility forecasting → DeepAR upgrade path
- [ ] FinBERT sentiment analysis (free, CPU-only, context signal)
- [ ] Statistical anomaly detection (z-scores, isolation forest)
- [ ] Unusual Whales Pro ($99/mo) + Polygon.io ($199/mo) for institutional-grade data
- [ ] Claude Agent SDK multi-agent orchestration
- [ ] Continuous learning with Bayesian confidence calibration

### Future — Phase 4 (Paper Trading & Validation, ~$450/mo)

- [ ] Shadow alert mode + paper trading engine with realistic slippage
- [ ] Promotion criteria: 30+ trades, Sharpe > 1.0, win rate > 55%
- [ ] Schwab API read-only integration
- [ ] Portfolio-level risk management (correlation, allocation, concentration limits)
- [ ] Borey approval gate for all LIVE promotions

### Future — Phase 5 (Autonomous Trading, ~$600/mo)

- [ ] Schwab API write access (or IBKR)
- [ ] Three-layer guardrails: strategy-level, portfolio-level, system-level circuit breakers
- [ ] Kill switches (drawdown, VIX, SPX move, manual)
- [ ] Volatility-adjusted position sizing (Kelly-VIX hybrid)
- [ ] Opus for trade decisions
- [ ] Gradual rollout: one strategy, minimum size, scale with proof

### Out of Scope

- Polygon.io / Unusual Whales in Phase 2 — premium data deferred to Phase 3
- RL-based trading agents — rule-based strategies first, ML optimization later (research doc recommendation)
- Full rough volatility pricing (rBergomi) — compute Hurst exponent instead (1 day vs 6 months)
- Neural network option pricing — Black-Scholes + market IV sufficient for listed options
- Custom DSL for strategies — YAML templates + NL parsing via Claude instead
- Web dashboard — Discord is the sole UI
- Mobile app — Discord mobile serves this purpose
- High-frequency trading — Python + LLM latency makes this impossible; min 15-min hold times

## Architecture

### Phase 1 State (Complete)

```
Tastytrade API (dxfeed WS) ──→ DataManager ──→ Analysis Pipeline ──→ Discord
                                                      ↓
TradingView Webhooks ──→ FastAPI ──────────→ Alert Processing ──→ Discord
                                                      ↓
CheddarFlow Bot ──→ Embed Parser ──────────→ Flow Filtering ──→ Discord
                                                      ↓
                                              Claude Sonnet → Commentary
                                                      ↓
                                              SQLite Store
```

### Phase 2 Target State

```
Tastytrade API ──→ DataManager ──→ Analysis Pipeline ──→ Discord
                                        ↓
ORATS Historical ──→ Backtest Engine ──→ Strategy Evaluator ──→ Discord
                          ↓                     ↓
               Walk-Forward + CPCV     Deflated Sharpe + Monte Carlo
                          ↓                     ↓
                   Strategy Lifecycle (IDEA → DEFINED → BACKTEST → PAPER → LIVE)
                          ↓
Borey (NL/YAML) ──→ Claude Parser ──→ Structured Rules ──→ Backtest
                                                            ↓
                                                    Signal Logger → SQLite
                                                            ↓
                                                    Trade Journal → Discord
```

### Phase 5 Target State

```
Data Feeds ──→ Feature Store ──→ ML Models (HMM, LSTM, FinBERT) ──→ Signals
                                        ↓
Strategy Engine ──→ Risk Gatekeeper (3 layers) ──→ Order Manager ──→ Schwab API
                          ↓                              ↓
                  Circuit Breakers              Kill Switches (Discord mobile)
                          ↓                              ↓
                  Claude Agent SDK              Borey Oversight (Discord)
                  (analyst, risk mgr,                    ↓
                   researcher agents)           Audit Trail → SQLite
```

## Tech Stack

| Component | Phase 1 (Complete) | Phase 2 Target | Phase 5 Target |
|-----------|-------------------|----------------|----------------|
| Runtime | Python 3.12, discord.py 2.4+, FastAPI | Same + Optopsy | Same |
| Data: Primary | Tastytrade API (real-time, dxfeed) | Same + ORATS ($99/mo) | + Polygon ($199), Unusual Whales ($99) |
| Data: Flow | CheddarFlow embed parsing | Same + signal logging | + anomaly detection |
| Data: Signals | TradingView webhooks | Same + strategy engine | + ML models |
| AI | Claude Sonnet | Same + NL strategy parsing | + Opus for trades, Agent SDK multi-agent |
| ML | None | None | HMM, LSTM/DeepAR, FinBERT, isolation forest |
| Analysis | GEX, Max Pain, PCR, Strike Intel, Greeks | + backtesting, WFA, CPCV, DSR, Monte Carlo | + vol forecasting, regime detection |
| Strategy | Manual alerts | YAML templates + lifecycle management | Autonomous execution + guardrails |
| Persistence | aiosqlite (SQLite) | Same + strategy/signal/journal tables | Same + trade execution audit trail |
| Charts | matplotlib (GEX, max pain) | Same + equity curves, performance | Same |
| Deploy | Docker on OpenClaw (s-1vcpu-2gb) | Scale to s-2vcpu-4gb ($24/mo) | Scale to s-4vcpu-8gb ($48/mo) |

## Constraints

- **Advisory only through Phase 4** — Bot does NOT trade until Phase 5. Phase 4 paper trades to prove system works. Phase 5 introduces autonomous trading with three-layer guardrails.
- **Anti-overfitting is non-negotiable** — Every strategy must pass WFA + CPCV + DSR + Monte Carlo before paper trading. 90%+ of backtested strategies fail in production.
- **LLMs in research/signal layer only** — LLMs cannot be in the hot execution path due to latency. Pre-market planning and post-market review, not tick-by-tick decisions.
- **HMM regime detection before live trading** — Prevents catastrophic strategy-regime mismatches. Highest-ROI ML model.
- **OpenClaw droplet** — DigitalOcean; scales from s-1vcpu-2gb to s-4vcpu-8gb across phases
- **Budget** — Phase 2 ~$150/mo; Phase 5 ~$600/mo
- **Tests** — All 186 existing tests must remain passing
- **Data sovereignty** — All data stays on user's infrastructure
- **Python** — Python over JavaScript for all new code
- **Evolve, don't rebuild** — Build on existing architecture; no greenfield rewrite
- **Borey's time ≤ 5 min/day** — System does heavy lifting; Borey provides judgment via Discord

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Evolve existing bot, not rebuild | Working analysis pipeline + 186 tests already validated | Validated |
| Tastytrade as Phase 1 data source | Free with brokerage account, real-time via dxfeed | Validated (Phase 1 complete) |
| ORATS for historical backtesting | Deepest history (2007+), includes 2008 crash, proprietary indicators, IV surface data | Research validated |
| YAML strategy templates, not DSL | LLM handles ambiguity; Borey describes in plain English, Claude parses to YAML | Research validated |
| Anti-overfitting pipeline mandatory | WFA + CPCV + DSR + Monte Carlo prevents data-mined strategies | Research validated |
| HMM for regime detection | Well-studied, fast, highest-ROI ML model for preventing strategy-regime mismatches | Research validated |
| LLMs in research layer, not execution | 2-30s latency per LLM call makes in-loop execution impossible for intraday | Research validated |
| Paper trade before live (30+ trades) | 90%+ of backtested strategies fail live; paper trading is the final gate | Research validated |
| Three-layer guardrails for Phase 5 | Strategy-level, portfolio-level, system-level circuit breakers | Research validated |
| Optopsy + custom Python for backtesting | Purpose-built for options, 28 built-in strategies, pandas-native, no framework lock-in | Research validated |

## Cost Structure

| Phase | Monthly Cost | Key Adds |
|-------|-------------|----------|
| Phase 1 (MVP) ✅ | ~$18 | Tastytrade (free), Sonnet (~$6), DO droplet ($12) |
| Phase 2 (Research) | ~$150 | +ORATS ($99), scale droplet ($24), +Sonnet ($25) |
| Phase 3 (ML) | ~$400 | +Polygon ($199), +Unusual Whales ($99), scale droplet ($48), +AI ($50) |
| Phase 4 (Paper) | ~$450 | +Schwab (free), +AI ($75) |
| Phase 5 (Auto-Trading) | ~$600 | +Opus-heavy ($150), scale droplet ($48) |

## Research Completed

| Document | Status | Key Finding |
|----------|--------|-------------|
| `docs/research/01-realtime-options-apis.md` | Complete | Tastytrade free with account; Polygon.io $199 for real-time |
| `docs/research/02-tradingview-integration.md` | Complete | Webhooks are the only viable automation path; FastAPI middleware recommended |
| `docs/research/03-cheddarflow-integration.md` | Complete | No API; Discord bot embed parsing is the only practical path |
| `docs/research/04-gex-flow-darkpool.md` | Complete | DIY GEX working; ORATS and Unusual Whales for Phase 2-3 |
| `docs/research/05-schwab-api.md` | Complete | OAuth2 + manual approval; read-only viable for Phase 4 |
| `docs/research/06-mcp-agent-sdk.md` | Complete | MCP ecosystem mature; Agent SDK for Phase 3 multi-agent |
| `docs/research/agent-trading/01-agent-architectures.md` | Complete | LLMs best in research/signal layer, not execution path. Multi-agent patterns validated. |
| `docs/research/agent-trading/02-backtesting-engines.md` | Complete | Optopsy for fast screening, custom Python for detailed backtest. ORATS for 2007+ history. |
| `docs/research/agent-trading/03-ml-models-options.md` | Complete | HMM regime detection = highest ROI. LSTM for vol forecasting. FinBERT for sentiment context. |
| `docs/research/agent-trading/04-strategy-lifecycle.md` | Complete | Full lifecycle state machine, NL strategy definition, guardrails architecture, Borey's ~5min/day workflow. |

---
*Last updated: 2026-02-21 after roadmap restructure*
