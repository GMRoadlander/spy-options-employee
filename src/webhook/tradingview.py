"""TradingView webhook endpoint.

Receives Pine Script alert POSTs, validates optional secret,
and queues alerts for Discord delivery.
"""

import asyncio
import hmac
import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict

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


@router.post("/tradingview")
async def receive_tradingview_alert(
    alert: TradingViewAlert,
    x_webhook_secret: str | None = Header(default=None),
) -> dict[str, Any]:
    """Receive a TradingView Pine Script alert.

    Validates optional webhook secret, parses JSON body,
    and queues the alert for Discord delivery.
    """
    # Validate secret if configured
    if config.webhook_secret:
        if not hmac.compare_digest(x_webhook_secret or "", config.webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook secret")

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
