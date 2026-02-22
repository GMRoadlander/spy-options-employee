"""Trade journal cog -- daily summaries, weekly reviews, signal ratings.

Implements slash commands:
    /journal daily          -- Post today's summary
    /journal weekly         -- Post weekly review
    /journal rate <id> <n>  -- Rate a signal 1-5 stars
    /journal note <content> -- Add a free-form journal note

Background tasks:
    - Auto-post daily summary at 4:30 PM ET
    - Auto-post weekly review Monday 10 AM ET
"""

import logging
from datetime import datetime, time, timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

from src.config import config

logger = logging.getLogger(__name__)

try:
    import zoneinfo
    ET = zoneinfo.ZoneInfo(config.timezone)
except ImportError:
    from datetime import timezone
    ET = timezone(timedelta(hours=-5))  # type: ignore[assignment]


def _now_et() -> datetime:
    """Get the current time in Eastern Time."""
    return datetime.now(ET)


class JournalCog(commands.Cog, name="Journal"):
    """Trade journal commands and automated summaries."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        logger.info("JournalCog loaded")

    async def cog_load(self) -> None:
        """Start background tasks when the cog is loaded."""
        self.auto_daily_summary.start()
        self.auto_weekly_review.start()
        logger.info("Journal background tasks started")

    async def cog_unload(self) -> None:
        """Stop background tasks when the cog is unloaded."""
        self.auto_daily_summary.cancel()
        self.auto_weekly_review.cancel()
        logger.info("Journal background tasks stopped")

    def _get_journal_channel(self) -> discord.TextChannel | None:
        """Get the journal channel from config."""
        channel_id = getattr(config, "journal_channel_id", 0)
        if channel_id == 0:
            # Fall back to analysis channel
            channel_id = config.analysis_channel_id
        if channel_id == 0:
            logger.warning("No journal/analysis channel configured")
            return None

        channel = self.bot.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.TextChannel):
            logger.warning("Journal channel %d not found or not text channel", channel_id)
            return None
        return channel

    # -- /journal daily --------------------------------------------------

    @app_commands.command(
        name="journal_daily",
        description="Post daily trading journal summary",
    )
    async def journal_daily(self, interaction: discord.Interaction) -> None:
        """Generate and post daily summary."""
        await interaction.response.defer()

        embed = await self._build_daily_embed()
        await interaction.followup.send(embed=embed)

        # Save to journal entries
        await self._save_journal_entry("daily", self._embed_to_text(embed))

    # -- /journal weekly -------------------------------------------------

    @app_commands.command(
        name="journal_weekly",
        description="Post weekly trading journal review",
    )
    async def journal_weekly(self, interaction: discord.Interaction) -> None:
        """Generate and post weekly review."""
        await interaction.response.defer()

        embed = await self._build_weekly_embed()
        await interaction.followup.send(embed=embed)

        await self._save_journal_entry("weekly", self._embed_to_text(embed))

    # -- /journal rate ---------------------------------------------------

    @app_commands.command(
        name="journal_rate",
        description="Rate a signal 1-5 stars",
    )
    @app_commands.describe(
        signal_id="Signal log ID to rate",
        rating="Rating from 1 (poor) to 5 (excellent)",
        notes="Optional notes about the rating",
    )
    async def journal_rate(
        self,
        interaction: discord.Interaction,
        signal_id: int,
        rating: int,
        notes: str = "",
    ) -> None:
        """Rate a signal from the signal log."""
        await interaction.response.defer()

        if rating < 1 or rating > 5:
            await interaction.followup.send(
                "Rating must be between 1 and 5.", ephemeral=True,
            )
            return

        store = getattr(self.bot, "store", None)
        if store is None:
            await interaction.followup.send(
                "Store not available.", ephemeral=True,
            )
            return

        db = store._ensure_connected()
        now = datetime.now().isoformat()

        await db.execute(
            """
            INSERT INTO signal_ratings (signal_id, rating, notes, rated_at)
            VALUES (?, ?, ?, ?)
            """,
            (signal_id, rating, notes, now),
        )
        await db.commit()

        stars = "+" * rating + "-" * (5 - rating)
        from src.discord_bot.embeds import build_rating_confirmation_embed
        embed = build_rating_confirmation_embed(signal_id, rating, notes)
        await interaction.followup.send(embed=embed)

    # -- /journal note ---------------------------------------------------

    @app_commands.command(
        name="journal_note",
        description="Add a free-form journal note",
    )
    @app_commands.describe(content="Your journal note")
    async def journal_note(
        self,
        interaction: discord.Interaction,
        content: str,
    ) -> None:
        """Add a timestamped journal note."""
        await interaction.response.defer()

        await self._save_journal_entry(
            "note", content, author=str(interaction.user),
        )

        embed = discord.Embed(
            title="Journal Note Saved",
            description=content,
            color=0x0099FF,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"By {interaction.user} | SPY Options Employee")
        await interaction.followup.send(embed=embed)

    # -- Background tasks ------------------------------------------------

    @tasks.loop(time=time(16, 30, tzinfo=ET))
    async def auto_daily_summary(self) -> None:
        """Auto-post daily summary at 4:30 PM ET."""
        now = _now_et()
        # Skip weekends
        if now.weekday() >= 5:
            return

        channel = self._get_journal_channel()
        if channel is None:
            return

        embed = await self._build_daily_embed()
        try:
            await channel.send(embed=embed)
            await self._save_journal_entry("daily", self._embed_to_text(embed))
            logger.info("Auto daily summary posted")
        except discord.HTTPException as exc:
            logger.error("Failed to post daily summary: %s", exc)

    @auto_daily_summary.before_loop
    async def before_daily_summary(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()

    @tasks.loop(time=time(10, 0, tzinfo=ET))
    async def auto_weekly_review(self) -> None:
        """Auto-post weekly review Monday 10 AM ET."""
        now = _now_et()
        # Only run on Mondays
        if now.weekday() != 0:
            return

        channel = self._get_journal_channel()
        if channel is None:
            return

        embed = await self._build_weekly_embed()
        try:
            await channel.send(embed=embed)
            await self._save_journal_entry("weekly", self._embed_to_text(embed))
            logger.info("Auto weekly review posted")
        except discord.HTTPException as exc:
            logger.error("Failed to post weekly review: %s", exc)

    @auto_weekly_review.before_loop
    async def before_weekly_review(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()

    # -- Helper methods --------------------------------------------------

    async def _build_daily_embed(self) -> discord.Embed:
        """Build a daily summary embed from store data.

        Aggregates: signals fired, outcomes, strategy alerts, market context.
        """
        from src.discord_bot.embeds import build_daily_summary_embed

        today = _now_et().date()
        start_of_day = datetime(today.year, today.month, today.day, tzinfo=ET)

        # Gather signal stats
        signal_stats = await self._get_signal_stats_since(start_of_day)

        # Gather strategy statuses
        strategy_summary = await self._get_strategy_summary()

        # Gather today's ratings
        rating_stats = await self._get_rating_stats_since(start_of_day)

        return build_daily_summary_embed(
            date=today,
            signal_stats=signal_stats,
            strategy_summary=strategy_summary,
            rating_stats=rating_stats,
        )

    async def _build_weekly_embed(self) -> discord.Embed:
        """Build a weekly review embed from store data."""
        from src.discord_bot.embeds import build_weekly_review_embed

        now = _now_et()
        # Monday of this week (the review covers the prior week)
        start_of_week = now - timedelta(days=now.weekday() + 7)
        start_of_week = datetime(
            start_of_week.year, start_of_week.month, start_of_week.day,
            tzinfo=ET,
        )
        end_of_week = start_of_week + timedelta(days=7)

        signal_stats = await self._get_signal_stats_since(start_of_week)
        strategy_summary = await self._get_strategy_summary()
        rating_stats = await self._get_rating_stats_since(start_of_week)

        return build_weekly_review_embed(
            start_date=start_of_week.date(),
            end_date=end_of_week.date(),
            signal_stats=signal_stats,
            strategy_summary=strategy_summary,
            rating_stats=rating_stats,
        )

    async def _get_signal_stats_since(self, since: datetime) -> dict:
        """Get signal statistics since a given time."""
        signal_logger = getattr(self.bot, "signal_logger", None)
        if signal_logger is None:
            return {"total_signals": 0, "by_type": {}, "by_direction": {}, "outcome_counts": {}}

        return await signal_logger.get_signal_stats(since=since)

    async def _get_strategy_summary(self) -> list[dict]:
        """Get summary of active strategies."""
        manager = getattr(self.bot, "strategy_manager", None)
        if manager is None:
            return []

        try:
            return await manager.list_strategies()
        except Exception:
            return []

    async def _get_rating_stats_since(self, since: datetime) -> dict:
        """Get signal rating statistics since a given time."""
        store = getattr(self.bot, "store", None)
        if store is None:
            return {"count": 0, "avg_rating": 0.0}

        try:
            db = store._ensure_connected()
            cursor = await db.execute(
                """
                SELECT COUNT(*), COALESCE(AVG(rating), 0)
                FROM signal_ratings
                WHERE rated_at >= ?
                """,
                (since.isoformat(),),
            )
            row = await cursor.fetchone()
            return {"count": row[0], "avg_rating": float(row[1])}
        except Exception:
            return {"count": 0, "avg_rating": 0.0}

    async def _save_journal_entry(
        self,
        entry_type: str,
        content: str,
        author: str = "system",
    ) -> None:
        """Save a journal entry to the database."""
        store = getattr(self.bot, "store", None)
        if store is None:
            return

        try:
            db = store._ensure_connected()
            now = datetime.now().isoformat()
            await db.execute(
                """
                INSERT INTO journal_entries (entry_type, content, author, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (entry_type, content, author, now),
            )
            await db.commit()
        except Exception as exc:
            logger.error("Failed to save journal entry: %s", exc)

    @staticmethod
    def _embed_to_text(embed: discord.Embed) -> str:
        """Convert an embed to plain text for storage."""
        parts = []
        if embed.title:
            parts.append(embed.title)
        if embed.description:
            parts.append(embed.description)
        for field in embed.fields:
            parts.append(f"{field.name}: {field.value}")
        return "\n".join(parts)


async def setup(bot: commands.Bot) -> None:
    """Register the JournalCog with the bot."""
    await bot.add_cog(JournalCog(bot))
    logger.info("JournalCog registered")
