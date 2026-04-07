"""TradingView webhook endpoint.

Receives Pine Script alert POSTs, validates optional HMAC signature,
and queues alerts for Discord delivery.
"""

import asyncio
import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, ValidationError

from src.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])

# Shared queue for webhook -> Discord cog delivery
alert_queue: asyncio.Queue["TradingViewAlert"] = asyncio.Queue()


class TradingViewAlert(BaseModel):
    """Parsed TradingView webhook payload.

    Uses extra="allow" so unknown fields from Pine Script
    placeholders are accepted without breaking validation.
    """

    model_config = ConfigDict(extra="allow")

    action: str  # e.g., "buy_call", "sell_put", "alert"
    ticker: str  # e.g., "SPX", "SPY"
    price: float | None = None
    time: str | None = None
    interval: str | None = None
    volume: float | None = None
    strategy: str | None = None
    message: str | None = None  # free-form text


def _verify_hmac(body: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature over the raw request body.

    Uses timing-safe comparison to prevent timing attacks.
    """
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/tradingview")
async def receive_tradingview_alert(
    request: Request,
    x_webhook_signature: str | None = Header(default=None),
) -> dict[str, Any]:
    """Receive a TradingView Pine Script alert.

    Validates optional HMAC-SHA256 signature over the raw request body,
    parses JSON payload, and queues the alert for Discord delivery.
    """
    # Read raw body for HMAC verification
    body = await request.body()

    # Validate HMAC signature if secret is configured
    if config.webhook_secret:
        if not x_webhook_signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        if not _verify_hmac(body, x_webhook_signature, config.webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse and validate the JSON payload
    try:
        alert = TradingViewAlert.model_validate_json(body)
    except ValidationError as exc:
        # Convert to JSON-safe error details (input may contain raw bytes)
        errors = []
        for err in exc.errors():
            safe_err = {k: v for k, v in err.items() if k != "input"}
            errors.append(safe_err)
        raise HTTPException(status_code=422, detail=errors) from exc

    logger.info(
        "Received TradingView alert: action=%s ticker=%s price=%s",
        alert.action,
        alert.ticker,
        alert.price,
    )

    await alert_queue.put(alert)

    return {
        "status": "received",
        "action": alert.action,
        "ticker": alert.ticker,
    }
