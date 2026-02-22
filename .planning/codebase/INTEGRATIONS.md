# Integrations

## Discord API (discord.py 2.4+)

- **Role**: Primary user interface — all interaction via Discord
- **Auth**: Bearer token via `DISCORD_TOKEN` env var
- **Channels**: 3 configured — analysis, alerts, commands (channel IDs via env vars)
- **Features**: Slash commands, rich embeds, file attachments (charts), bot presence
- **Cogs**: AnalysisCog (on-demand), SchedulerCog (background loop), AlertsCog (smart notifications)

## Claude API (anthropic SDK 0.40+)

- **Role**: AI commentary on analysis results
- **Model**: `claude-haiku-4-5-20251001` (hardcoded in config.py)
- **Auth**: API key via `CLAUDE_API_KEY` env var
- **Usage**: ~195 calls/day (2-min intervals × market hours × 2 tickers)
- **Max tokens**: 256 per response
- **Error handling**: AuthenticationError, RateLimitError, APIConnectionError, APIStatusError

## CBOE CDN (Primary data source)

- **Role**: 15-minute delayed options data for SPY and SPX
- **Auth**: None required (public CDN)
- **URLs**: `cdn.cboe.com/api/global/delayed_quotes/options/SPY.json` (and `_SPX.json`)
- **Client**: Async aiohttp with 30s timeout, User-Agent header
- **Parsing**: OCC option symbol regex extraction
- **Data**: Pricing, Greeks (delta, gamma, theta, vega, rho), IV, volume, OI

## Tradier Sandbox API (Backup data source)

- **Role**: Fallback when CBOE fails
- **Auth**: Bearer token via `TRADIER_TOKEN` env var (optional)
- **Base URL**: `sandbox.tradier.com/v1`
- **Endpoints**: `/markets/options/expirations`, `/markets/options/chains`, `/markets/quotes`
- **Fetches**: Up to 3 nearest expirations with full greeks

## SQLite (Persistence)

- **Driver**: aiosqlite (async)
- **Path**: `data/spy_employee.db` (Docker volume mounted)
- **Tables**: `snapshots` (historical analysis), `alert_cooldowns` (spam prevention)
- **Features**: WAL mode, 30-day retention, auto-cleanup

## Environment Variables

| Variable | Required | Service |
|----------|----------|---------|
| `DISCORD_TOKEN` | Yes | Discord |
| `DISCORD_ANALYSIS_CHANNEL_ID` | Yes | Discord |
| `DISCORD_ALERTS_CHANNEL_ID` | Yes | Discord |
| `DISCORD_COMMANDS_CHANNEL_ID` | Yes | Discord |
| `CLAUDE_API_KEY` | Yes | Anthropic |
| `TRADIER_TOKEN` | No | Tradier (optional fallback) |

## Credential Management

- All secrets via environment variables
- `.env` file loaded via python-dotenv
- `.env.template` provided with placeholder values
- No OAuth flows — all simple token/key auth

---
*Generated: 2026-02-21*
