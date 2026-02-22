# Plan 1-2: TradingView Webhooks + CheddarFlow Parser

> Add TradingView webhook ingestion via FastAPI and CheddarFlow Discord embed parsing. Two new signal sources flowing into the existing Discord output.

## Objective

Add two new data input channels to the bot:
1. **TradingView webhooks** — A FastAPI endpoint that receives Pine Script alert POSTs, parses the JSON payload, and routes them to Discord as formatted embeds.
2. **CheddarFlow embed parser** — A discord.py listener cog that monitors `#cheddarflow-raw` for CheddarFlow bot messages, parses embeds for SPX flow data, filters, and forwards to an output channel.

Both are additive — no existing code is modified beyond `bot.py` (loading new cogs) and `main.py` (co-hosting FastAPI). All 130 existing tests remain passing.

## Execution Context

- `src/main.py` — entry point (needs FastAPI co-hosting)
- `src/bot.py` — SpyBot class (load new cog)
- `src/config.py` — configuration (new channel IDs, webhook secret)
- `src/discord_bot/` — existing cogs (pattern reference)
- `src/discord_bot/embeds.py` — embed builders (reuse patterns)
- `docs/research/02-tradingview-integration.md` — TradingView webhook research
- `docs/research/03-cheddarflow-integration.md` — CheddarFlow integration research

## Context

### TradingView Webhooks
- User has TradingView Premium (800 alerts, webhook support, server-side alerts)
- Pine Script alerts fire HTTP POST to a configurable URL
- Payload is JSON with dynamic placeholders: `{{ticker}}`, `{{close}}`, `{{time}}`, etc.
- Middleware server (FastAPI) receives, parses, enriches, forwards to Discord
- Must co-host FastAPI alongside discord.py on the same process/droplet

### CheddarFlow Integration
- No API exists — Discord bot embed parsing is the only viable path
- CheddarFlow's Discord bot posts to a dedicated channel
- Our bot listens via `on_message`, parses embed fields, filters for SPX, re-posts
- Embed format is undocumented and may change — parser must be resilient

### Co-hosting Pattern
FastAPI and discord.py both need an asyncio event loop. The standard approach:
```python
import asyncio
import uvicorn
from fastapi import FastAPI

app = FastAPI()
bot = SpyBot()

async def main():
    # Run both concurrently
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=8000))
    await asyncio.gather(
        server.serve(),
        bot.start(token),
    )
```

---

## Tasks

### Task 1: Add FastAPI dependency and co-hosting infrastructure
**Type:** Code
**Verify:** Bot starts and FastAPI responds to `GET /health` on port 8000

1. Add to `requirements.txt`:
   ```
   fastapi>=0.115
   uvicorn>=0.34
   ```

2. Create `src/webhook/__init__.py` and `src/webhook/app.py`:
   ```python
   from fastapi import FastAPI

   app = FastAPI(title="SPX Options Webhook Receiver")

   @app.get("/health")
   async def health():
       return {"status": "ok"}
   ```

3. Modify `src/main.py` to co-host FastAPI + discord.py:
   - Import uvicorn and the FastAPI app
   - Run both in the same asyncio event loop using `asyncio.gather()`
   - FastAPI binds to `0.0.0.0:8000` (configurable via env var)
   - If FastAPI fails to start (port conflict, etc.), bot continues without it

4. Add to `src/config.py`:
   ```python
   webhook_port: int = int(os.getenv("WEBHOOK_PORT", "8000"))
   webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")
   ```

### Task 2: Create TradingView webhook endpoint
**Type:** Code
**Verify:** `curl -X POST http://localhost:8000/webhook/tradingview -d '{"action":"alert","ticker":"SPX","price":5950.25}' -H 'Content-Type: application/json'` returns 200

Create `src/webhook/tradingview.py`:

1. Define a Pydantic model for the expected webhook payload:
   ```python
   class TradingViewAlert(BaseModel):
       action: str  # e.g., "buy_call", "sell_put", "alert"
       ticker: str  # e.g., "SPX", "SPY"
       price: float | None = None
       time: str | None = None
       interval: str | None = None
       volume: float | None = None
       strategy: str | None = None
       message: str | None = None  # free-form text
   ```

2. Create `POST /webhook/tradingview` endpoint:
   - Validate optional webhook secret (via `X-Webhook-Secret` header or query param)
   - Parse JSON body into `TradingViewAlert`
   - Accept flexible payloads — use `model_config = ConfigDict(extra="allow")` for unknown fields from Pine Script
   - Log the received alert
   - Queue the alert for Discord delivery (via shared queue or direct bot reference)

3. Error handling:
   - 401 if secret is configured but doesn't match
   - 422 for malformed JSON (FastAPI default)
   - 200 with receipt confirmation on success

### Task 3: Route TradingView alerts to Discord
**Type:** Code
**Verify:** Webhook POST appears as a formatted embed in the configured Discord channel

1. Create `src/discord_bot/cog_webhooks.py`:
   - A cog that receives alerts from the FastAPI webhook handler
   - Uses an `asyncio.Queue` shared between FastAPI and the cog
   - Background task polls the queue and posts formatted embeds

2. Build an embed format for TradingView alerts in `src/discord_bot/embeds.py`:
   - Add `build_tradingview_alert_embed(alert: TradingViewAlert) -> discord.Embed`
   - Include: action, ticker, price, time, strategy name
   - Color-code by action type (green for bullish, red for bearish, blue for neutral)

3. Add config for the target channel:
   ```python
   webhook_alerts_channel_id: int = int(os.getenv("DISCORD_WEBHOOK_ALERTS_CHANNEL_ID", "0"))
   ```

4. Load the cog in `bot.py`:
   - Add `"src.discord_bot.cog_webhooks"` to `cog_extensions` list

### Task 4: Create CheddarFlow embed parser cog
**Type:** Code
**Verify:** When a bot message with embeds appears in `#cheddarflow-raw`, SPX entries are forwarded to the output channel

Create `src/discord_bot/cog_cheddarflow.py`:

1. Listen to `on_message` events:
   - Filter: only messages from bot users in the configured CheddarFlow channel
   - Skip messages without embeds

2. Parse CheddarFlow embed fields:
   ```python
   def parse_cheddarflow_embed(embed: discord.Embed) -> dict | None:
       """Extract flow data from a CheddarFlow bot embed.

       Returns dict with: ticker, strike, expiry, premium, volume, order_type,
       side, is_sweep, spot_price. Returns None if parsing fails.
       """
   ```
   - Parse from embed title, description, and fields
   - Be resilient to format changes — log warnings on parse failures, don't crash
   - Return structured dict or None

3. Filter for SPX/SPY:
   - Only forward entries where ticker is SPX or SPY
   - Apply configurable premium threshold (env var, default $50K)

4. Reformat and post to output channel:
   - Build a clean embed with parsed data
   - Add `build_flow_alert_embed()` to `embeds.py`
   - Color-code: green for calls, red for puts, yellow for sweeps
   - Include: ticker, strike, expiry, premium, type, sweep indicator

5. Add config:
   ```python
   cheddarflow_channel_id: int = int(os.getenv("DISCORD_CHEDDARFLOW_CHANNEL_ID", "0"))
   cheddarflow_output_channel_id: int = int(os.getenv("DISCORD_CHEDDARFLOW_OUTPUT_CHANNEL_ID", "0"))
   cheddarflow_min_premium: float = float(os.getenv("CHEDDARFLOW_MIN_PREMIUM", "50000"))
   ```

6. Load the cog in `bot.py`:
   - Add `"src.discord_bot.cog_cheddarflow"` to `cog_extensions` list
   - Only load if `cheddarflow_channel_id` is configured (non-zero)

### Task 5: Write tests for webhook endpoint and CheddarFlow parser
**Type:** Test
**Verify:** `pytest tests/test_webhooks.py tests/test_cheddarflow.py -v` passes

Create `tests/test_webhooks.py`:
1. Test FastAPI endpoint with httpx TestClient
2. Test valid TradingView payload parsing
3. Test secret validation (when configured vs not)
4. Test malformed payloads return 422

Create `tests/test_cheddarflow.py`:
1. Test embed parsing with synthetic Discord embeds
2. Test SPX/SPY filtering
3. Test premium threshold filtering
4. Test resilience to malformed/changed embed formats (graceful None return)
5. Mock discord.Embed objects — do NOT connect to real Discord

### Task 6: Update Docker and environment configuration
**Type:** Code
**Verify:** `docker build -t spy-employee .` succeeds; `docker-compose.yml` exposes port 8000

1. Update `Dockerfile`:
   - `EXPOSE 8000` (for webhook endpoint)

2. Update `docker-compose.yml`:
   - Add port mapping: `"8000:8000"` for webhook ingestion

3. Update `.env.template` with all new variables:
   ```
   # TradingView Webhook
   WEBHOOK_PORT=8000
   WEBHOOK_SECRET=your_webhook_secret_here
   DISCORD_WEBHOOK_ALERTS_CHANNEL_ID=0

   # CheddarFlow
   DISCORD_CHEDDARFLOW_CHANNEL_ID=0
   DISCORD_CHEDDARFLOW_OUTPUT_CHANNEL_ID=0
   CHEDDARFLOW_MIN_PREMIUM=50000
   ```

### Task 7: Verify all tests pass
**Type:** Test (checkpoint)
**Verify:** `pytest tests/ -v` — all tests pass (130 existing + new webhook + CheddarFlow tests)

Run the full test suite. Ensure:
- All 130 existing analysis tests still pass
- New webhook tests pass
- New CheddarFlow parser tests pass
- No import errors from new modules

---

## Verification

- [ ] `pytest tests/ -v` — all tests pass
- [ ] `GET /health` returns 200 on port 8000 when bot is running
- [ ] `POST /webhook/tradingview` with valid JSON → appears as embed in Discord
- [ ] `POST /webhook/tradingview` with wrong secret → 401
- [ ] CheddarFlow bot message in `#cheddarflow-raw` with SPX embed → forwarded to output channel
- [ ] CheddarFlow bot message with non-SPX embed → ignored
- [ ] Bot starts and runs normally when CheddarFlow channel ID is 0 (disabled)
- [ ] Bot starts and runs normally when webhook port is unavailable (graceful degradation)
- [ ] `docker build -t spy-employee .` succeeds

## Success Criteria

1. TradingView webhook endpoint receives and processes Pine Script alerts
2. Webhook alerts appear as formatted Discord embeds in the configured channel
3. CheddarFlow embed parser filters and forwards SPX/SPY flow to output channel
4. Both features are optional — bot works without them when not configured
5. All 130 existing tests pass plus new tests for webhook and CheddarFlow logic
6. FastAPI co-hosts cleanly with discord.py in a single process

## Output

- `src/webhook/__init__.py` — webhook package
- `src/webhook/app.py` — FastAPI app with health endpoint
- `src/webhook/tradingview.py` — TradingView webhook handler
- `src/discord_bot/cog_webhooks.py` — webhook-to-Discord routing cog
- `src/discord_bot/cog_cheddarflow.py` — CheddarFlow embed parser cog
- `src/discord_bot/embeds.py` — updated with new embed builders
- `src/main.py` — updated for FastAPI co-hosting
- `src/bot.py` — updated to load new cogs
- `src/config.py` — updated with new config fields
- `tests/test_webhooks.py` — webhook tests
- `tests/test_cheddarflow.py` — CheddarFlow parser tests
- `requirements.txt` — updated
- `.env.template` — updated
- `Dockerfile` — updated
- `docker-compose.yml` — updated
