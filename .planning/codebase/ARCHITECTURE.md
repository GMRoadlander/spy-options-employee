# Architecture

## System Design

**Event-driven async Discord bot** with layered architecture:
- Data layer → Analysis layer → Output layer
- Pull-based: scheduler periodically fetches data, runs analysis, publishes to Discord

## Entry Points

1. **Primary**: `src/main.py` → `main()` → configures logging, validates token, runs `SpyBot`
2. **Package**: `src/__main__.py` → allows `python -m src`
3. **Docker**: `CMD ["python", "-m", "src.main"]`

## Data Flow

```
CBOE CDN (primary) ──┐
                     ├─→ DataManager (cache + fallback) ─→ OptionsChain
Tradier API (backup) ┘
                                                              │
                          ┌───────────────────────────────────┘
                          ▼
                    Analysis Pipeline
                    1. PCR (independent)
                    2. GEX (uses PCR.volume_pcr for squeeze)
                    3. Max Pain (independent)
                    4. Strike Intel (consolidates 1-3)
                          │
                          ▼
                    AnalysisResult
                    ┌─────┼─────────────┐
                    ▼     ▼             ▼
                 Store  Commentary    Discord
                (SQLite) (Claude     (Embeds +
                         Haiku)      Charts)
```

## Key Abstractions

- **OptionContract** — single options contract with greeks, pricing
- **OptionsChain** — full chain snapshot (ticker, spot, timestamp, contracts)
- **AnalysisResult** — composite of PCR, GEX, MaxPain, StrikeIntel results
- **DataManager** — orchestrates fetching with cache + fallback
- **Store** — async SQLite wrapper (snapshots + cooldowns)
- **SpyBot** — extends `discord.ext.commands.Bot`, manages lifecycle

## Async Patterns

- All I/O is async: aiohttp, aiosqlite, discord.py
- Lifecycle hooks: `setup_hook()`, `on_ready()`, `close()`
- Background loop: `@tasks.loop(minutes=2)` in SchedulerCog
- HTTP sessions: lazy-initialized, reused across calls

## State Management

| Component | State Type | What |
|-----------|-----------|------|
| DataManager | In-memory cache | OptionsChain per ticker, 60s TTL |
| SchedulerCog | Runtime tracking | Previous results, GEX sign, pre/post market flags |
| AlertsCog | Runtime tracking | Previous results for condition detection |
| Store | Persistent (SQLite) | Historical snapshots, alert cooldowns |

## Error Handling Strategy

- **Data fetch**: CBOE → Tradier fallback → None if both fail
- **HTTP errors**: Specific handling for 401, 429, timeouts; logged, returns None
- **Analysis**: Invalid inputs return 0.0 or raise ValueError
- **Discord**: Failed cog loads logged but bot continues; command errors sent as ephemeral
- **Database**: Import/init failures set store=None, bot runs without persistence

## Configuration

- Centralized frozen dataclass (`src/config.py`)
- Sources: env vars → .env file → hardcoded defaults
- Global singleton: `from src.config import config`

---
*Generated: 2026-02-21*
