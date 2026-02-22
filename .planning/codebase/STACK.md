# Stack

## Primary Language

- **Python 3.12** — async-first, type-annotated throughout
- Package manager: pip with requirements.txt (no lock file)

## Frameworks

| Framework | Version | Role |
|-----------|---------|------|
| discord.py | >=2.4 | Discord bot framework, slash commands, cogs |
| aiohttp | >=3.9 | Async HTTP client for API calls |
| anthropic | >=0.40 | Claude API client for AI commentary |

## Key Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| pandas | >=2.2 | Options chain data manipulation |
| numpy | >=1.26 | Numerical computations (Greeks, GEX) |
| scipy | >=1.13 | Black-Scholes (norm.cdf), interpolation |
| matplotlib | >=3.9 | Chart generation for Discord embeds |
| aiosqlite | >=0.20 | Async SQLite persistence |
| python-dotenv | >=1.0 | Environment variable loading |

## Dev Dependencies

None specified — no dev requirements file, no linting/formatting config.

## Runtime Requirements

- Python 3.12+
- System: gcc (for matplotlib compilation in Docker)
- Database: SQLite 3 (file-based at `data/spy_employee.db`)
- Docker: `python:3.12-slim` base image

## Build & Deploy

- **Dockerfile**: Multi-stage build, installs gcc, pip dependencies, runs `python -m src.main`
- **docker-compose.yml**: Single service `spy-employee`, auto-restart, `.env` file, volume mount for `./data`
- **Platform**: OpenClaw (DigitalOcean droplet)

## Dependency Risks

- All deps use `>=` pins without upper bounds — no reproducible builds
- No lock file (requirements.lock or pip-compile output)
- No dev/test dependency separation

---
*Generated: 2026-02-21*
