"""FastAPI application for webhook ingestion.

Co-hosted alongside discord.py in a single asyncio event loop.
"""

from fastapi import FastAPI

from src.webhook.tradingview import router as tradingview_router

app = FastAPI(title="SPX Options Webhook Receiver")
app.include_router(tradingview_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
