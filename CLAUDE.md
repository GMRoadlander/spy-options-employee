# SPX Day Trader

Active GSD project. See `.planning/PROJECT.md` for full context.

## Quick Reference

- **What**: Permanent SPX options research + paper trading platform. Borey defines strategies in plain English, the system backtests, validates, and paper trades.
- **Key constraint**: Advisory + paper trading only. No live order execution.
- **Runs on**: OpenClaw platform (DigitalOcean, s-2vcpu-8gb)
- **Discord**: Primary UI — Borey never touches code
- **Broker**: None (paper trading only)
- **Data sources**: Tastytrade (real-time, Phase 1 ✅), ORATS (historical, Phase 2), Polygon.io + Unusual Whales (Phase 3)
- **AI**: Sonnet for routine analysis and commentary
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
- Phase 3+: hmmlearn (HMM), PyTorch (LSTM), transformers (FinBERT)

## GSD Skills

Auto-load on project tasks: `/gsd:progress`, `/gsd:execute-plan`, `/gsd:plan-phase`

## Proactive Plugins

- `code-review` — after each plan step
- `superpowers:verification-before-completion` — before marking steps complete
- `everything-claude-code:security-review` — after API integration code
- `everything-claude-code:tdd-guide` — for new test coverage
- `context7` — for library docs (tastytrade SDK, FastAPI, discord.py, Optopsy, hmmlearn)

## Rules

- Never auto-trade or place orders (paper trading only, no live execution)
- Anti-overfitting pipeline is NON-NEGOTIABLE for any strategy (WFA + CPCV + DSR + Monte Carlo)
- LLMs in research/signal layer only, NOT execution path (latency)
- All data stays on user's infrastructure (inherited from OpenClaw platform)
- Python over JavaScript
- Use MCP tools when available
- Validate before deployment
- All 186 existing analysis tests must remain passing
- Use `commit-commands` plugin for git, not manual git
