# SPX Day Trader

Active GSD project. See `.planning/PROJECT.md` for full context.

## Quick Reference

- **What**: Trading research assistant → autonomous SPX options trader. Borey defines strategies in plain English, the system backtests, validates, and ultimately executes.
- **Key constraint**: Advisory only through Phase 4. Phase 5 introduces autonomous trading with three-layer guardrails.
- **Runs on**: OpenClaw platform (DigitalOcean, scales s-1vcpu-2gb → s-4vcpu-8gb across phases)
- **Discord**: Primary UI — Borey never touches code
- **Broker**: Schwab — read-only Phase 4, write Phase 5 (or IBKR)
- **Data sources**: Tastytrade (real-time, Phase 1 ✅), ORATS (historical, Phase 2), Polygon.io + Unusual Whales (Phase 3)
- **AI**: Sonnet for routine, Opus for trade decisions (Phase 5)
- **Team**: Borey = domain expert (options trader), ~5 min/day via Discord

## Tech Stack

- Python 3.12 / discord.py 2.4+
- aiohttp, pandas, numpy, scipy, matplotlib
- Tastytrade API (real-time data, Phase 1 ✅)
- FastAPI (TradingView webhook receiver, Phase 1 ✅)
- anthropic SDK (Sonnet commentary)
- aiosqlite for persistence
- Docker deployment
- Phase 2+: Optopsy (backtesting), ORATS API, YAML strategy templates
- Phase 3+: hmmlearn (HMM), PyTorch (LSTM), transformers (FinBERT), Claude Agent SDK

## GSD Skills

Auto-load on project tasks: `/gsd:progress`, `/gsd:execute-plan`, `/gsd:plan-phase`

## Proactive Plugins

- `code-review` — after each plan step
- `superpowers:verification-before-completion` — before marking steps complete
- `everything-claude-code:security-review` — after API integration code
- `everything-claude-code:tdd-guide` — for new test coverage
- `context7` — for library docs (tastytrade SDK, FastAPI, discord.py, Optopsy, hmmlearn)

## Rules

- Never auto-trade or place orders (until Phase 5 with three-layer guardrails)
- Anti-overfitting pipeline is NON-NEGOTIABLE for any strategy (WFA + CPCV + DSR + Monte Carlo)
- LLMs in research/signal layer only, NOT execution path (latency)
- All data stays on user's infrastructure (inherited from OpenClaw platform)
- Python over JavaScript
- Use MCP tools when available
- Validate before deployment
- All 186 existing analysis tests must remain passing
- Use `commit-commands` plugin for git, not manual git
