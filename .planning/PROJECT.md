# SPX Day Trader

> Permanent SPX options research + paper trading platform — Borey defines strategies in plain English, the system backtests, validates, and paper trades with realistic simulation. Advisory + paper trading only; no live order execution.

## What This Is

A Discord-based SPX options research and paper trading platform. Borey describes strategies in plain English, the system translates to structured rules, backtests against 18+ years of ORATS history, validates through a 4-gate anti-overfitting pipeline (WFA + CPCV + DSR + Monte Carlo), and paper trades with realistic simulation including 7-factor dynamic slippage, 18 stress scenarios, and Bayesian continuous learning. ML models (HMM regime detection, LSTM vol forecasting, FinBERT sentiment, anomaly detection) provide context signals. All interaction through Discord slash commands — Borey spends ~5 min/day.

## Core Value

Rigorous strategy validation that prevents overfitting — the system proves strategies work before Borey risks real capital.

## Current State (v1.0 shipped 2026-02-24)

- **Codebase:** 59,096 lines Python, 172 files, 1,466 tests passing
- **Tech stack:** Python 3.12, discord.py, FastAPI, PyTorch, hmmlearn, transformers, aiosqlite
- **Data sources:** Tastytrade (real-time), ORATS ($99/mo historical), Polygon.io ($199/mo OPRA), Unusual Whales ($99/mo flow)
- **Infrastructure:** Docker on OpenClaw s-2vcpu-8gb ($48/mo)
- **Monthly cost:** ~$400 steady state
- **Discord commands:** 20+ slash commands across analysis, strategy, ML, and paper trading cogs

## Requirements

### Validated

- ✓ Discord bot with slash commands (/gex, /maxpain, /levels, /strikes, /pcr, /status, /analyze) — existing
- ✓ GEX analysis engine (net GEX, gamma flip, ceiling, floor, squeeze probability) — existing
- ✓ Max Pain calculation with distance tracking — existing
- ✓ Put/Call Ratio analysis with dealer positioning signals — existing
- ✓ Strike Intelligence (key levels, recommendations) — existing
- ✓ Black-Scholes Greeks calculation (delta, gamma, theta, vega, P(ITM)) — existing
- ✓ AI commentary via Claude Sonnet — v1.0
- ✓ SQLite persistence (snapshots + alert cooldowns) — existing
- ✓ Background scheduler (2-min market hours loop, ET-aware) — existing
- ✓ Smart alerts (gamma flip, squeeze, max pain convergence, OI shift) — existing
- ✓ Chart generation (matplotlib GEX/max pain/equity curves/performance charts) — v1.0
- ✓ Docker deployment with docker-compose on OpenClaw — existing
- ✓ Tastytrade API real-time data (dxfeed WebSocket) — v1.0
- ✓ TradingView webhook ingestion (FastAPI) — v1.0
- ✓ CheddarFlow Discord embed parser — v1.0
- ✓ ORATS historical data ($99/mo, 2007+ EOD chains) — v1.0
- ✓ Backtesting engine (Optopsy + custom Python) — v1.0
- ✓ YAML strategy templates (Borey defines, no code) — v1.0
- ✓ NL → strategy definition (Claude parses plain English to YAML) — v1.0
- ✓ Strategy lifecycle (IDEA → DEFINED → BACKTEST → PAPER → RETIRED) — v1.0
- ✓ Anti-overfitting pipeline (WFA + CPCV + DSR + Monte Carlo, all 4 gates) — v1.0
- ✓ Signal logging (track alert outcomes for feedback) — v1.0
- ✓ Strategy evaluation metrics (Sharpe, Sortino, Calmar, drawdown, win rate, expectancy) — v1.0
- ✓ Trade journal via Discord (daily/weekly/monthly summaries) — v1.0
- ✓ Hypothesis testing framework (propose → formalize → test → prove/disprove) — v1.0
- ✓ HMM regime detection (risk-on/off/crisis via hmmlearn) — v1.0
- ✓ LSTM volatility forecasting (PyTorch, 2-layer hidden=64) — v1.0
- ✓ FinBERT sentiment analysis (ProsusAI/finbert, lazy loading) — v1.0
- ✓ Statistical anomaly detection (z-scores + IsolationForest) — v1.0
- ✓ Polygon.io real-time OPRA feed ($199/mo) — v1.0
- ✓ Unusual Whales Pro flow + dark pool data ($99/mo) — v1.0
- ✓ Structured Claude reasoning engine — v1.0
- ✓ Continuous learning with Bayesian calibration — v1.0
- ✓ Feature store pipeline (15 features, SQLite) — v1.0
- ✓ Paper trading engine with realistic fill simulation — v1.0
- ✓ 7-factor dynamic slippage model — v1.0
- ✓ Shadow mode + exit monitor (5 exit conditions, AM/PM settlement) — v1.0
- ✓ Portfolio analytics (Greeks aggregation, VaR, 18 stress scenarios) — v1.0
- ✓ Position sizing (Kelly criterion with regime/vol/anomaly adjustments) — v1.0
- ✓ Risk management (5-layer pre-trade checks, 6 circuit breakers) — v1.0
- ✓ Discord paper trading cog (6 slash commands) — v1.0
- ✓ Discord performance reporting (daily/weekly/monthly, equity curves) — v1.0
- ✓ Integration wiring + E2E tests (1,466 tests) — v1.0

### Active

(No active requirements — v1.0 complete. Next milestone scope TBD.)

### Out of Scope

- **Autonomous/live trading** — no live order execution, no broker write access, no kill switches. System is advisory + paper trading only.
- **Schwab/IBKR broker integration** — no broker API needed for permanent paper trading platform
- **Promotion to LIVE workflow** — no LIVE state in lifecycle; strategies go IDEA → DEFINED → BACKTEST → PAPER → RETIRED
- RL-based trading agents — rule-based strategies first, ML optimization later
- Full rough volatility pricing (rBergomi) — compute Hurst exponent instead
- Neural network option pricing — Black-Scholes + market IV sufficient for listed options
- Custom DSL for strategies — YAML templates + NL parsing via Claude instead
- Web dashboard — Discord is the sole UI
- Mobile app — Discord mobile serves this purpose
- High-frequency trading — Python + LLM latency makes this impossible; min 15-min hold times

## Architecture (v1.0 Shipped)

```
Tastytrade API (dxfeed WS) ──→ DataManager ──→ Analysis Pipeline ──→ Discord
                                                      ↓
TradingView Webhooks ──→ FastAPI ──────────→ Alert Processing ──→ Discord
                                                      ↓
CheddarFlow Bot ──→ Embed Parser ──────────→ Flow Filtering ──→ Discord
                                                      ↓
ORATS Historical ──→ Backtest Engine ──→ Strategy Evaluator ──→ Discord
                          ↓                     ↓
               Walk-Forward + CPCV     Deflated Sharpe + Monte Carlo
                          ↓                     ↓
                   Strategy Lifecycle (IDEA → DEFINED → BACKTEST → PAPER → RETIRED)
                          ↓
Borey (NL/YAML) ──→ Claude Parser ──→ Structured Rules ──→ Backtest
                                                            ↓
Polygon.io + Unusual Whales ──→ Flow Analyzer ──→ Anomaly Detection
                                                            ↓
HMM + LSTM + FinBERT ──→ Feature Store ──→ ML Insights ──→ Discord
                                                            ↓
                                            Paper Trading Engine
                                    ↓               ↓               ↓
                             Shadow Mode    Fill Simulator    Exit Monitor
                                    ↓               ↓               ↓
                             Risk Manager ← Portfolio Analyzer ← PnL Calculator
                                    ↓
                             Discord Reporting (daily/weekly/monthly)
                                    ↓
                             Signal Logger → Bayesian Calibrator → Continuous Learning
```

## Constraints

- **Advisory + paper trading only** — No live order execution. Borey makes all real trading decisions.
- **Anti-overfitting is non-negotiable** — Every strategy must pass WFA + CPCV + DSR + Monte Carlo before paper trading.
- **LLMs in research/signal layer only** — Not in execution path due to latency.
- **OpenClaw droplet** — DigitalOcean s-2vcpu-8gb ($48/mo)
- **Budget** — Steady state ~$400/mo
- **Tests** — 1,466 tests must remain passing
- **Data sovereignty** — All data stays on user's infrastructure
- **Python** — Python over JavaScript for all new code
- **Borey's time ≤ 5 min/day** — System does heavy lifting; Borey provides judgment via Discord

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Evolve existing bot, not rebuild | Working analysis pipeline + 186 tests already validated | ✓ Good — preserved all tests, smooth evolution |
| Tastytrade as real-time data source | Free with brokerage account, real-time via dxfeed | ✓ Good — Phase 1 complete |
| ORATS for historical backtesting | Deepest history (2007+), includes 2008 crash | ✓ Good — Phase 2 complete |
| YAML strategy templates, not DSL | LLM handles ambiguity; NL parsing via Claude | ✓ Good — Phase 2 complete |
| Anti-overfitting pipeline mandatory | WFA + CPCV + DSR + Monte Carlo prevents data-mined strategies | ✓ Good — all 4 gates implemented and tested |
| HMM for regime detection | Well-studied, fast, highest-ROI ML model | ✓ Good — Phase 3 complete |
| LLMs in research layer, not execution | 2-30s latency makes in-loop execution impossible | ✓ Good — confirmed by implementation |
| Structured Claude reasoning over multi-agent SDK | Single structured call gives 80% of value, simpler | ✓ Good — research-backed decision |
| Permanent paper trading platform | No autonomous trading — Borey trades manually | ✓ Good — decision 2026-02-23 |
| Optopsy + custom Python for backtesting | Purpose-built for options, pandas-native | ✓ Good — Phase 2 complete |
| Graceful degradation pattern | Every data source and ML model optional | ✓ Good — bot runs at any data tier |

## Research Completed

| Document | Key Finding |
|----------|-------------|
| `docs/research/01-realtime-options-apis.md` | Tastytrade free with account; Polygon.io $199 for real-time |
| `docs/research/02-tradingview-integration.md` | Webhooks are the only viable automation path |
| `docs/research/03-cheddarflow-integration.md` | No API; Discord embed parsing is only practical path |
| `docs/research/04-gex-flow-darkpool.md` | DIY GEX working; ORATS and Unusual Whales for flow |
| `docs/research/05-schwab-api.md` | OAuth2 + manual approval; no longer needed (paper only) |
| `docs/research/06-mcp-agent-sdk.md` | MCP mature; structured reasoning preferred over SDK |
| `docs/research/agent-trading/01-agent-architectures.md` | LLMs best in research/signal layer, not execution |
| `docs/research/agent-trading/02-backtesting-engines.md` | Optopsy for screening, custom Python for detail |
| `docs/research/agent-trading/03-ml-models-options.md` | HMM = highest ROI, LSTM for vol, FinBERT for sentiment |
| `docs/research/agent-trading/04-strategy-lifecycle.md` | Full lifecycle state machine, NL definition, ~5min/day |

---
*Last updated: 2026-02-24 after v1.0 milestone*
