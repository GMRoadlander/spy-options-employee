"""Webhook routing cog -- bridges FastAPI alerts to Discord.

Polls an asyncio.Queue shared with the FastAPI webhook endpoint
and posts formatted embeds to the configured alerts channel.
"""

import logging

import discord
from discord.ext import commands, tasks

from src.config import config
from src.discord_bot.embeds import build_tradingview_alert_embed
from src.webhook.tradingview import TradingViewAlert, alert_queue

logger = logging.getLogger(__name__)


class WebhooksCog(commands.Cog, name="Webhooks"):
    """Routes incoming webhook alerts to Discord channels."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        logger.info("WebhooksCog loaded")

    async def cog_load(self) -> None:
        """Start the queue polling loop when the cog loads."""
        self._poll_queue.start()

    async def cog_unload(self) -> None:
        """Stop the queue polling loop when the cog unloads."""
        self._poll_queue.cancel()

    @tasks.loop(seconds=1)
    async def _poll_queue(self) -> None:
        """Poll the alert queue and forward to Discord."""
        while not alert_queue.empty():
            try:
                alert: TradingViewAlert = alert_queue.get_nowait()
            except Exception:
                break

            channel_id = config.webhook_alerts_channel_id
            if not channel_id:
                logger.warning("DISCORD_WEBHOOK_ALERTS_CHANNEL_ID not set -- dropping alert")
                continue

            channel = self.bot.get_channel(channel_id)
            if channel is None:
                logger.warning("Webhook alerts channel %d not found", channel_id)
                continue

            embed = build_tradingview_alert_embed(alert)
            try:
                await channel.send(embed=embed)  # type: ignore[union-attr]
                logger.info("Posted TradingView alert to channel %d", channel_id)

                # Log signal (non-blocking, graceful degradation)
                signal_logger = getattr(self.bot, "signal_logger", None)
                if signal_logger is not None:
                    try:
                        from src.db.signal_log import SignalEvent
                        event = SignalEvent(
                            signal_type="webhook",
                            ticker=alert.ticker,
                            direction=alert.action if hasattr(alert, "action") else "neutral",
                            strength=0.6,
                            source="cog_webhooks",
                            metadata={"strategy": getattr(alert, "strategy", ""), "timeframe": getattr(alert, "timeframe", "")},
                        )
                        await signal_logger.log_signal(event)
                    except Exception as exc:
                        logger.debug("Signal logging failed (non-critical): %s", exc)

            except discord.HTTPException as exc:
                logger.error("Failed to send webhook alert embed: %s", exc)

    @_poll_queue.before_loop
    async def _before_poll(self) -> None:
        """Wait for the bot to be ready before polling."""
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """Register the WebhooksCog with the bot."""
    await bot.add_cog(WebhooksCog(bot))
    logger.info("WebhooksCog registered")
