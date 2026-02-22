"""FastAPI application for webhook ingestion.

Co-hosted alongside discord.py in a single asyncio event loop.
"""

from fastapi import FastAPI

app = FastAPI(title="SPX Options Webhook Receiver")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
