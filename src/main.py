"""Entry point for the SPY/SPX options analysis Discord bot.

Co-hosts FastAPI (webhook receiver) alongside discord.py in a single
asyncio event loop.

Usage:
    python -m src.main
    python src/main.py
"""

import asyncio
import logging
import sys

import uvicorn

from src.bot import SpyBot
from src.config import config
from src.webhook.app import app


def main() -> None:
    """Configure logging and start the bot + webhook server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Reduce noise from discord.py internals
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)

    if not config.discord_token:
        logger.error("DISCORD_TOKEN not set. Please set it in .env or environment variables.")
        sys.exit(1)

    logger.info("Starting SPY Options Employee bot")
    logger.info("Tickers: %s", config.tickers)
    logger.info("Update interval: %d minutes", config.update_interval_minutes)
    logger.info("Analysis channel: %d", config.analysis_channel_id)
    logger.info("Alerts channel: %d", config.alerts_channel_id)

    bot = SpyBot()

    # Share bot reference with FastAPI for webhook-to-Discord routing
    app.state.bot = bot

    asyncio.run(_run(bot, logger))


async def _run(bot: SpyBot, logger: logging.Logger) -> None:
    """Run both discord.py and FastAPI concurrently."""
    uvi_config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=config.webhook_port,
        log_level="info",
    )
    server = uvicorn.Server(uvi_config)

    async with bot:
        try:
            await asyncio.gather(
                bot.start(config.discord_token),
                server.serve(),
            )
        except Exception:
            logger.exception("Error in bot/webhook server co-hosting")
            raise


if __name__ == "__main__":
    main()
