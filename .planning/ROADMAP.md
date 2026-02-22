# SPX Day Trader — Roadmap

> Milestone 1.0: From delayed-data Discord bot to real-time autonomous trading platform

## Phase 1: MVP Data & Signals (~$18/mo)

**Goal**: Swap delayed CBOE data for real-time Tastytrade feed, upgrade AI to Sonnet, add TradingView webhooks and CheddarFlow flow parsing. Zero new analysis logic — just better data in, smarter commentary out.

**Deliverables**:
- [x] Tastytrade API integration (dxfeed WebSocket streaming, replaces CBOE CDN + Tradier)
- [x] Claude Sonnet commentary upgrade (replace Haiku)
- [x] TradingView webhook ingestion (FastAPI endpoint on droplet)
- [x] CheddarFlow Discord embed parser (listen to `#cheddarflow-raw`, filter SPX flow)
- [x] All 186 tests passing (130 original + 38 webhook/CheddarFlow + 18 Tastytrade)

**Research needed**: 🔬 Tastytrade API auth flow, dxfeed WebSocket protocol, FastAPI + discord.py co-hosting on single process

**Estimated cost**: ~$18/mo (droplet $12 + Sonnet ~$6)

---

## Phase 2: Premium Data Sources (~$340/mo)

**Goal**: Add institutional-grade data — real-time OPRA options feed via Polygon.io and flow/dark pool intelligence via Unusual Whales. Introduce Opus for high-conviction alerts.

**Deliverables**:
- [ ] Polygon.io real-time OPRA integration ($199/mo)
- [ ] Unusual Whales Pro API integration ($99/mo) — flow + dark pool
- [ ] Tiered AI: Sonnet for routine scans, Opus for high-conviction alerts (~$30/mo)
- [ ] Data pipeline to merge multiple sources into unified analysis

**Research needed**: 🔬 Polygon.io WebSocket API, Unusual Whales Python client, data normalization across sources

**Estimated cost**: ~$340/mo

---

## Phase 3: Intelligence Platform (~$494/mo)

**Goal**: Add IV surface analytics, read-only Schwab portfolio visibility, and multi-agent AI orchestration via Claude Agent SDK. The bot becomes a full intelligence platform.

**Deliverables**:
- [ ] ORATS IV surface analytics integration ($99/mo)
- [ ] Schwab API read-only integration (OAuth2, portfolio + positions visibility)
- [ ] Claude Agent SDK multi-agent orchestration (Sonnet + Opus, ~$72/mo AI)
- [ ] Server scale to s-2vcpu-4gb ($24/mo)

**Research needed**: 🔬 Schwab OAuth2 manual approval process, ORATS API surface data format, Agent SDK multi-agent patterns

**Estimated cost**: ~$494/mo

---

## Phase 4: Autonomous Trading (~$596/mo)

**Goal**: Enable autonomous trading via Schwab API write access. Requires safety framework with kill switches, position sizing, max daily loss limits. Borey's domain expertise defines all entry/exit criteria before a single trade is placed.

**Deliverables**:
- [ ] Schwab API read + write integration (order placement)
- [ ] Safety framework: kill switches, position sizing rules, max daily loss limits
- [ ] Borey-defined entry/exit criteria codified as trading rules
- [ ] Opus-heavy AI for trade decisions (~$150/mo)
- [ ] Server scale to s-4vcpu-8gb ($48/mo)
- [ ] Comprehensive integration tests for order flow

**Research needed**: 🔬 Schwab order API, safety framework patterns, position sizing algorithms, circuit breaker design

**Estimated cost**: ~$596/mo

---

*Roadmap created: 2026-02-21*
