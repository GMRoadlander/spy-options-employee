# SPX Day Trader

> Intraday SPX/SPY options intelligence bot — spots setups, sends Discord alerts, provides charts on demand. Advisory only through Phases 1-3; Phase 4 introduces autonomous trading with its own safety framework.

## Vision

Evolve the existing Discord-based options analysis bot from delayed CBOE data and basic Haiku commentary into a multi-source real-time intelligence platform. Four-phase roadmap progressively adds data sources, AI sophistication, and ultimately autonomous trading capability.

## Requirements

### Validated

- ✓ Discord bot with slash commands (/gex, /maxpain, /levels, /strikes, /pcr, /status, /analyze) — existing
- ✓ GEX analysis engine (net GEX, gamma flip, ceiling, floor, squeeze probability) — existing
- ✓ Max Pain calculation with distance tracking — existing
- ✓ Put/Call Ratio analysis with dealer positioning signals — existing
- ✓ Strike Intelligence (key levels, recommendations) — existing
- ✓ Black-Scholes Greeks calculation (delta, gamma, theta, vega, P(ITM)) — existing
- ✓ AI commentary via Claude API — existing (Haiku)
- ✓ SQLite persistence (snapshots + alert cooldowns) — existing
- ✓ Background scheduler (2-min market hours loop, ET-aware) — existing
- ✓ Smart alerts (gamma flip, squeeze, max pain convergence, OI shift) — existing
- ✓ Chart generation (matplotlib GEX/max pain charts) — existing
- ✓ Docker deployment with docker-compose on OpenClaw — existing
- ✓ Data fetching with fallback (CBOE CDN → Tradier sandbox) — existing
- ✓ 130 unit tests covering analysis layer — existing

### Active — Phase 1 (MVP, ~$30/mo)

- [ ] **Tastytrade data swap** — Replace CBOE CDN + Tradier with Tastytrade API as primary real-time data source (free with brokerage account, dxfeed WebSocket streaming)
- [ ] **Sonnet commentary upgrade** — Upgrade from Haiku to Sonnet for all AI commentary (~20 scans/day, ~$6/mo AI cost)
- [ ] **TradingView webhook ingestion** — FastAPI endpoint on droplet receives Pine Script alert POSTs, parses JSON payload, routes to analysis pipeline and Discord
- [ ] **CheddarFlow embed parsing** — Bot listens to CheddarFlow Discord bot messages in `#cheddarflow-raw` channel, parses embeds for SPX flow data (sweeps, dark pool, unusual activity), filters and forwards to output channel
- [ ] **Existing tests remain passing** — All 130 analysis unit tests must pass through data source swap

### Active — Phase 2 (Data, ~$352/mo)

- [ ] Polygon.io real-time OPRA feed ($199/mo) — raw options trades/quotes
- [ ] Unusual Whales Pro ($99/mo) — flow + dark pool API with Python client
- [ ] Sonnet for routine + Opus for high-conviction alerts (~$30/mo AI)

### Active — Phase 3 (Intelligence, ~$513/mo)

- [ ] ORATS IV surface analytics ($99/mo)
- [ ] Schwab API read-only integration (free with account)
- [ ] Claude Agent SDK multi-agent orchestration (Sonnet + Opus, ~$72/mo AI)
- [ ] Server scale to 2vCPU/8GB ($44/mo)

### Active — Phase 4 (Auto-Trading, ~$603/mo)

- [ ] Autonomous trading via Schwab API (read + write)
- [ ] Opus-heavy AI for trade decisions (~$150/mo AI)
- [ ] Safety framework: kill switches, position sizing rules, max daily loss limits
- [ ] Borey's domain expertise defines entry/exit criteria before implementation
- [ ] Server scale to 4vCPU/8GB ($56/mo)

### Out of Scope

- Polygon.io / Unusual Whales in Phase 1 — premium data sources deferred to Phase 2
- Chart image generation (Lightweight Charts / Playwright) — text/embed alerts only in Phase 1
- Multi-agent AI (Agent SDK) — single Sonnet call in Phase 1, multi-agent in Phase 3
- Auto-trading in Phases 1-3 — advisory only until Phase 4 safety framework is built
- Schwab API in Phase 1 — deferred to Phase 3 (read-only) and Phase 4 (write)
- Web dashboard — Discord is the sole UI
- Mobile app — Discord mobile serves this purpose
- Backtesting framework — future consideration, not in any current phase

## Architecture

### Current State (being evolved)

```
CBOE CDN / Tradier → DataManager → Analysis Pipeline → Discord
                                         ↓
                                    Claude Haiku → Commentary
                                         ↓
                                    SQLite Store
```

### Phase 1 Target State

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

## Tech Stack

| Component | Current | Phase 1 Target |
|-----------|---------|---------------|
| Runtime | Python 3.12, discord.py 2.4+ | Same + FastAPI |
| Data: Primary | CBOE CDN (15-min delayed) | Tastytrade API (real-time, dxfeed) |
| Data: Fallback | Tradier sandbox | TBD (may keep Tradier as fallback) |
| Data: Flow | None | CheddarFlow embed parsing |
| Data: Signals | None | TradingView webhook ingestion |
| AI | Claude Haiku (claude-haiku-4-5-20251001) | Claude Sonnet |
| Analysis | GEX, Max Pain, PCR, Strike Intel, Greeks | Same (no changes) |
| Persistence | aiosqlite (SQLite) | Same |
| Charts | matplotlib (GEX, max pain) | Same (no Lightweight Charts yet) |
| Deploy | Docker on OpenClaw (DO 2vCPU/4GB) | Same |

## Constraints

- **Advisory only** — Bot does NOT trade in Phases 1-3. Phase 4 introduces autonomous trading as a future milestone with its own safety framework, position sizing rules, and kill switches. Borey's domain expertise is critical for defining trade entry/exit criteria before Phase 4.
- **OpenClaw droplet** — Must run on 2vCPU/4GB DigitalOcean in Phase 1 (~$24/mo)
- **Budget** — Phase 1 total ~$30/mo (droplet + Sonnet AI calls)
- **Tests** — All 130 existing analysis unit tests must remain passing
- **Tastytrade account** — Must open brokerage account to get free API access (setup task)
- **Data sovereignty** — All data stays on user's infrastructure (inherited from OpenClaw)
- **Python** — Python over JavaScript for all new code
- **Evolve, don't rebuild** — Build on existing architecture; no greenfield rewrite

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Evolve existing bot, not rebuild | Working analysis pipeline + 130 tests already validated; swap data layer only | — Pending |
| Tastytrade as Phase 1 data source | Free with brokerage account, real-time via dxfeed WebSocket, full Greeks/IV | — Pending |
| TradingView = alerting engine only | No public data API; webhooks are the official automation path (Premium plan) | Validated in research |
| CheddarFlow = Discord embed parsing | No API exists; Discord bot listener is the only practical integration path | Validated in research |
| FastAPI for webhook ingestion | Lightweight, async-native, runs alongside discord.py on same droplet | — Pending |
| Sonnet for all commentary | Better reasoning for ~$6/mo AI cost at 20 scans/day | — Pending |
| No chart generation in Phase 1 | Existing matplotlib charts sufficient; Lightweight Charts deferred | — Pending |

## Cost Structure

| Phase | Monthly Cost | Key Adds |
|-------|-------------|----------|
| Phase 1 (MVP) | ~$30 | Tastytrade (free), Sonnet (~$6), DO droplet ($24) |
| Phase 2 (Data) | ~$352 | +Polygon.io ($199), +Unusual Whales ($99), +Opus ($30) |
| Phase 3 (Intelligence) | ~$513 | +ORATS ($99), +Agent SDK AI ($72), scale server ($44) |
| Phase 4 (Auto-Trading) | ~$603 | +Opus-heavy ($150), scale server ($56) |

## Research Completed

| Document | Status | Key Finding |
|----------|--------|-------------|
| `docs/research/01-realtime-options-apis.md` | Complete | Tastytrade free with account; Polygon.io $199 for real-time |
| `docs/research/02-tradingview-integration.md` | Complete | Webhooks are the only viable automation path; FastAPI middleware recommended |
| `docs/research/03-cheddarflow-integration.md` | Complete | No API; Discord bot embed parsing is the only practical path |
| `docs/research/04-gex-flow-darkpool.md` | Complete | DIY GEX working; ORATS and Unusual Whales for Phase 2-3 |
| `docs/research/05-schwab-api.md` | Complete | OAuth2 + manual approval; read-only viable for Phase 3 |
| `docs/research/06-mcp-agent-sdk.md` | Complete | MCP ecosystem mature; Agent SDK for Phase 3 multi-agent |

---
*Last updated: 2026-02-21 after initialization*
