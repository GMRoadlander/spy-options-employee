# Structure

## Directory Layout

```
spy-options-employee/
├── Dockerfile                    # Container build (python:3.12-slim)
├── docker-compose.yml            # Service orchestration
├── requirements.txt              # Python dependencies
├── CLAUDE.md                     # Project instructions
├── smoke_test.py                 # Manual end-to-end integration test
├── validate.py                   # Data quality validation utility
│
├── docs/research/                # Research notes (6 documents)
│   ├── 01-realtime-options-apis.md
│   ├── 02-tradingview-integration.md
│   ├── 03-cheddarflow-integration.md
│   ├── 04-gex-flow-darkpool.md
│   ├── 05-schwab-api.md
│   └── 06-mcp-agent-sdk.md
│
├── src/                          # Main application package
│   ├── __init__.py
│   ├── __main__.py               # Package entry (python -m src)
│   ├── main.py                   # CLI entry point
│   ├── bot.py                    # SpyBot class + lifecycle hooks
│   ├── config.py                 # Configuration (frozen dataclass)
│   │
│   ├── ai/                       # AI commentary generation
│   │   ├── __init__.py
│   │   └── commentary.py         # Claude Haiku integration
│   │
│   ├── analysis/                 # Analysis engines (pure math, no I/O)
│   │   ├── __init__.py           # Exports all analysis functions
│   │   ├── analyzer.py           # Orchestrator (PCR→GEX→MP→SI)
│   │   ├── greeks.py             # Black-Scholes calculations
│   │   ├── gex.py                # Gamma Exposure engine
│   │   ├── max_pain.py           # Max Pain engine
│   │   ├── pcr.py                # Put/Call Ratio engine
│   │   └── strike_intel.py       # Key levels & recommendations
│   │
│   ├── data/                     # Data fetching & models
│   │   ├── __init__.py           # Exports OptionContract, OptionsChain
│   │   ├── data_manager.py       # Fetch orchestrator (cache + fallback)
│   │   ├── cboe_client.py        # CBOE CDN async client
│   │   └── tradier_client.py     # Tradier sandbox async client
│   │
│   ├── db/                       # Persistence layer
│   │   ├── __init__.py
│   │   └── store.py              # SQLite async store (snapshots + cooldowns)
│   │
│   └── discord_bot/              # Discord bot layer
│       ├── __init__.py
│       ├── cog_analysis.py       # Slash commands (/gex, /pcr, /analyze, etc.)
│       ├── cog_scheduler.py      # Background loop (2-min updates, market hours)
│       ├── cog_alerts.py         # Smart alerts (gamma flip, squeeze, convergence)
│       ├── embeds.py             # Discord embed builders
│       └── charts.py             # Matplotlib chart generation
│
└── tests/                        # Unit tests (130 tests)
    ├── __init__.py
    ├── test_greeks.py            # 45 tests — Black-Scholes calculations
    ├── test_gex.py               # 27 tests — Gamma exposure
    ├── test_max_pain.py          # 23 tests — Max pain algorithm
    └── test_pcr.py               # 35 tests — Put/call ratio
```

## Module Organization

| Package | Role | I/O? |
|---------|------|------|
| `src/ai/` | AI commentary generation | Yes (Claude API) |
| `src/analysis/` | Pure math analysis engines | No (stateless) |
| `src/data/` | Data fetching, models, caching | Yes (HTTP) |
| `src/db/` | SQLite persistence | Yes (disk) |
| `src/discord_bot/` | Discord integration (cogs, embeds, charts) | Yes (Discord API) |

## Dependency Direction

```
main.py → bot.py → config.py
                 → data/ (DataManager)
                 → db/ (Store)
                 → discord_bot/ (cogs)
                      → analysis/ (engines)
                      → ai/ (commentary)
                      → data/ (via bot shared resources)
```

## Codebase Size

~4,893 lines of Python across 26 modules.

---
*Generated: 2026-02-21*
