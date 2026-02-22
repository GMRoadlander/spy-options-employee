"""CheddarFlow embed parser cog.

Monitors a configured Discord channel for CheddarFlow bot messages,
parses embeds for SPX/SPY flow data, filters by premium threshold,
and forwards matching entries to an output channel.
"""

import logging
import re

import discord
from discord.ext import commands

from src.config import config
from src.discord_bot.embeds import build_flow_alert_embed

logger = logging.getLogger(__name__)


def parse_cheddarflow_embed(embed: discord.Embed) -> dict | None:
    """Extract flow data from a CheddarFlow bot embed.

    Parses ticker, strike, expiry, premium, volume, order type, side,
    sweep indicator, and spot price from embed title/description/fields.

    Returns None if parsing fails (graceful degradation).

    Args:
        embed: A discord.Embed from a CheddarFlow bot message.

    Returns:
        Dict with: ticker, strike, expiry, premium, volume, order_type,
        side, is_sweep, spot_price. Or None if unparseable.
    """
    try:
        result: dict = {
            "ticker": None,
            "strike": None,
            "expiry": None,
            "premium": None,
            "volume": None,
            "order_type": None,
            "side": None,
            "is_sweep": False,
            "spot_price": None,
        }

        # Try to extract from embed title (common format: "TICKER STRIKE C/P EXP")
        title = embed.title or ""
        description = embed.description or ""
        combined_text = f"{title} {description}"

        # Look for ticker
        ticker_match = re.search(r"\b(SPX|SPY|QQQ|AAPL|TSLA|NVDA|AMZN|GOOG|META)\b", combined_text, re.IGNORECASE)
        if ticker_match:
            result["ticker"] = ticker_match.group(1).upper()

        # Look for strike price (number possibly with decimal)
        strike_match = re.search(r"\b(\d{3,5}(?:\.\d{1,2})?)\s*[CP]\b", combined_text, re.IGNORECASE)
        if strike_match:
            result["strike"] = float(strike_match.group(1))

        # Look for call/put side
        side_match = re.search(r"\b(CALL|PUT|[CP])\b", combined_text, re.IGNORECASE)
        if side_match:
            side_val = side_match.group(1).upper()
            result["side"] = "CALL" if side_val in ("C", "CALL") else "PUT"

        # Look for expiry (MM/DD, MM/DD/YY, YYYY-MM-DD patterns)
        expiry_match = re.search(r"\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{4}-\d{2}-\d{2})\b", combined_text)
        if expiry_match:
            result["expiry"] = expiry_match.group(1)

        # Check for sweep
        result["is_sweep"] = bool(re.search(r"\bsweep\b", combined_text, re.IGNORECASE))

        # Parse embed fields for structured data
        for field in embed.fields:
            name_lower = (field.name or "").lower()
            value = field.value or ""

            if "premium" in name_lower or "size" in name_lower:
                premium_match = re.search(r"\$?([\d,]+(?:\.\d+)?)\s*[KMB]?", value)
                if premium_match:
                    raw = premium_match.group(1).replace(",", "")
                    multiplier = 1
                    if "K" in value.upper():
                        multiplier = 1_000
                    elif "M" in value.upper():
                        multiplier = 1_000_000
                    elif "B" in value.upper():
                        multiplier = 1_000_000_000
                    result["premium"] = float(raw) * multiplier

            elif "volume" in name_lower or "vol" in name_lower:
                vol_match = re.search(r"([\d,]+)", value)
                if vol_match:
                    result["volume"] = int(vol_match.group(1).replace(",", ""))

            elif "type" in name_lower or "order" in name_lower:
                result["order_type"] = value.strip()

            elif "spot" in name_lower or "price" in name_lower or "underlying" in name_lower:
                spot_match = re.search(r"\$?([\d,]+(?:\.\d+)?)", value)
                if spot_match:
                    result["spot_price"] = float(spot_match.group(1).replace(",", ""))

            elif "strike" in name_lower:
                strike_match = re.search(r"\$?([\d,]+(?:\.\d+)?)", value)
                if strike_match:
                    result["strike"] = float(strike_match.group(1).replace(",", ""))

            elif "expir" in name_lower or "exp" in name_lower:
                result["expiry"] = value.strip()

            elif "side" in name_lower or "direction" in name_lower:
                if "call" in value.lower():
                    result["side"] = "CALL"
                elif "put" in value.lower():
                    result["side"] = "PUT"

        # Must have at least a ticker to be valid
        if result["ticker"] is None:
            logger.debug("CheddarFlow embed parse: no ticker found")
            return None

        return result

    except Exception as exc:
        logger.warning("CheddarFlow embed parse failed: %s", exc)
        return None


class CheddarFlowCog(commands.Cog, name="CheddarFlow"):
    """Monitors CheddarFlow bot embeds and forwards SPX/SPY flow."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        logger.info("CheddarFlowCog loaded")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Listen for CheddarFlow bot messages in the configured channel."""
        # Only process messages in the configured channel
        if message.channel.id != config.cheddarflow_channel_id:
            return

        # Only process bot messages (CheddarFlow is a bot)
        if not message.author.bot:
            return

        # Must have embeds
        if not message.embeds:
            return

        output_channel_id = config.cheddarflow_output_channel_id
        if not output_channel_id:
            return

        output_channel = self.bot.get_channel(output_channel_id)
        if output_channel is None:
            logger.warning("CheddarFlow output channel %d not found", output_channel_id)
            return

        for embed in message.embeds:
            flow = parse_cheddarflow_embed(embed)
            if flow is None:
                continue

            # Filter: SPX/SPY only
            if flow["ticker"] not in ("SPX", "SPY"):
                continue

            # Filter: minimum premium threshold
            if flow["premium"] is not None and flow["premium"] < config.cheddarflow_min_premium:
                continue

            # Build and send the formatted embed
            alert_embed = build_flow_alert_embed(flow)
            try:
                await output_channel.send(embed=alert_embed)  # type: ignore[union-attr]
                logger.info(
                    "Forwarded CheddarFlow: %s %s %s premium=%s",
                    flow["ticker"],
                    flow.get("strike"),
                    flow.get("side"),
                    flow.get("premium"),
                )
            except discord.HTTPException as exc:
                logger.error("Failed to send CheddarFlow alert: %s", exc)


async def setup(bot: commands.Bot) -> None:
    """Register the CheddarFlowCog with the bot (only if configured)."""
    if not config.cheddarflow_channel_id:
        logger.info("CheddarFlow channel ID not set -- skipping cog load")
        return
    await bot.add_cog(CheddarFlowCog(bot))
    logger.info("CheddarFlowCog registered")
