"""Trade journal cog -- daily summaries, weekly reviews, signal ratings.

Implements slash commands:
    /journal daily          -- Post today's summary
    /journal weekly         -- Post weekly review
    /journal rate <id> <n>  -- Rate a signal 1-5 stars
    /journal note <content> -- Add a free-form journal note

Background tasks:
    - Auto-post daily summary at 4:30 PM ET
    - Auto-post weekly review Monday 10 AM ET
    - Auto-post monthly report on 1st of month at 10 AM ET
    - Auto-post paper trading daily summary at 4:15 PM ET
"""

import logging
from datetime import datetime, time, timedelta, timezone
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands, tasks

from src.config import config

logger = logging.getLogger(__name__)

from src.utils import ET, now_et as _now_et


class JournalCog(commands.Cog, name="Journal"):
    """Trade journal commands and automated summaries."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.services = bot.services  # type: ignore[attr-defined]
        logger.info("JournalCog loaded")

    async def cog_load(self) -> None:
        """Start background tasks when the cog is loaded."""
        self.auto_daily_summary.start()
        self.auto_weekly_review.start()
        self.auto_monthly_report.start()
        self.auto_paper_daily.start()
        logger.info("Journal background tasks started")

    async def cog_unload(self) -> None:
        """Stop background tasks when the cog is unloaded."""
        self.auto_daily_summary.cancel()
        self.auto_weekly_review.cancel()
        self.auto_monthly_report.cancel()
        self.auto_paper_daily.cancel()
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

    def _get_paper_channel(self) -> discord.TextChannel | None:
        """Get the paper trading channel from config."""
        channel_id = getattr(config, "paper_trading_channel_id", 0)
        if channel_id == 0:
            channel_id = getattr(config, "paper_channel_id", 0)
        if channel_id == 0:
            return None
        channel = self.bot.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.TextChannel):
            logger.warning("Paper trading channel %d not found", channel_id)
            return None
        return channel

    # -- Helper methods for reporters ----------------------------------------

    def _get_paper_reporter(self) -> Any:
        """Get PaperPerformanceReporter if paper engine is available.

        Returns:
            PaperPerformanceReporter instance or None.
        """
        paper_engine = self.services.paper_engine
        strategy_manager = self.services.strategy_manager
        store = self.services.store
        if paper_engine is None or strategy_manager is None or store is None:
            return None
        from src.discord_bot.paper_reporting import PaperPerformanceReporter
        return PaperPerformanceReporter(paper_engine, strategy_manager, store)

    def _get_strategy_reporter(self) -> Any:
        """Get StrategyReporter if store and strategy_manager are available.

        Returns:
            StrategyReporter instance or None.
        """
        store = self.services.store
        manager = self.services.strategy_manager
        if store is None or manager is None:
            return None
        from src.discord_bot.reporting import StrategyReporter
        return StrategyReporter(store, manager)

    # -- /journal daily --------------------------------------------------

    @app_commands.command(
        name="journal_daily",
        description="Post daily trading journal summary",
    )
    async def journal_daily(self, interaction: discord.Interaction) -> None:
        """Generate and post daily summary."""
        await interaction.response.defer()

        embeds, files = await self._build_daily_embed()
        if files:
            await interaction.followup.send(embeds=embeds, files=files)
        else:
            await interaction.followup.send(embeds=embeds)

        # Save to journal entries
        await self._save_journal_entry("daily", self._embed_to_text(embeds[0]))

    # -- /journal weekly -------------------------------------------------

    @app_commands.command(
        name="journal_weekly",
        description="Post weekly trading journal review",
    )
    async def journal_weekly(self, interaction: discord.Interaction) -> None:
        """Generate and post weekly review."""
        await interaction.response.defer()

        embeds, files = await self._build_weekly_embed()
        if files:
            await interaction.followup.send(embeds=embeds, files=files)
        else:
            await interaction.followup.send(embeds=embeds)

        await self._save_journal_entry("weekly", self._embed_to_text(embeds[0]))

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

        store = self.services.store
        if store is None:
            await interaction.followup.send(
                "Store not available.", ephemeral=True,
            )
            return

        db = store._ensure_connected()
        now = _now_et().isoformat()

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
            timestamp=datetime.now(timezone.utc),
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

        embeds, files = await self._build_daily_embed()
        try:
            if files:
                await channel.send(embeds=embeds, files=files)
            else:
                await channel.send(embeds=embeds)
            await self._save_journal_entry("daily", self._embed_to_text(embeds[0]))
            logger.info(
                "Auto daily summary posted (%d embeds, %d files)",
                len(embeds), len(files),
            )
        except discord.HTTPException as exc:
            logger.error("Failed to post daily summary: %s", exc)

    @auto_daily_summary.error
    async def on_daily_summary_error(self, error: Exception) -> None:
        """Log errors from the daily summary background task."""
        logger.error("Daily summary task error: %s", error, exc_info=error)

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

        embeds, files = await self._build_weekly_embed()
        try:
            if files:
                await channel.send(embeds=embeds, files=files)
            else:
                await channel.send(embeds=embeds)
            await self._save_journal_entry("weekly", self._embed_to_text(embeds[0]))
            logger.info(
                "Auto weekly review posted (%d embeds, %d files)",
                len(embeds), len(files),
            )
        except discord.HTTPException as exc:
            logger.error("Failed to post weekly review: %s", exc)

    @auto_weekly_review.error
    async def on_weekly_review_error(self, error: Exception) -> None:
        """Log errors from the weekly review background task."""
        logger.error("Weekly review task error: %s", error, exc_info=error)

    @auto_weekly_review.before_loop
    async def before_weekly_review(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()

    @tasks.loop(time=time(10, 0, tzinfo=ET))
    async def auto_monthly_report(self) -> None:
        """Auto-post monthly deep report on the 1st of each month at 10 AM ET."""
        now = _now_et()
        # Only run on 1st of month, weekdays
        if now.day != 1 or now.weekday() >= 5:
            return

        channel = self._get_journal_channel()
        if channel is None:
            return

        # Report on previous month
        prev_month = now.replace(day=1) - timedelta(days=1)

        paper_reporter = self._get_paper_reporter()
        strategy_reporter = self._get_strategy_reporter()

        embeds: list[discord.Embed] = []
        files: list[discord.File] = []

        # Existing monthly report (backtest-based)
        if strategy_reporter is not None:
            try:
                bt_embeds = await strategy_reporter.monthly_report(prev_month.date())
                embeds.extend(bt_embeds)
            except Exception as exc:
                logger.error("Failed to build monthly backtest report: %s", exc)

        # Paper trading monthly report
        if paper_reporter is not None:
            try:
                paper_embeds, paper_files = await paper_reporter.monthly_report(
                    month=prev_month.date(),
                )
                embeds.extend(paper_embeds)
                files.extend(paper_files)
            except Exception as exc:
                logger.error("Failed to build paper monthly report: %s", exc)

        if embeds:
            try:
                # Discord max 10 embeds per message -- split if needed
                for i in range(0, len(embeds), 10):
                    batch_embeds = embeds[i:i + 10]
                    batch_files = files if i == 0 else []  # attach files to first message only
                    if batch_files:
                        await channel.send(embeds=batch_embeds, files=batch_files)
                    else:
                        await channel.send(embeds=batch_embeds)
                await self._save_journal_entry(
                    "monthly",
                    f"Monthly report for {prev_month.strftime('%B %Y')}",
                )
                logger.info("Auto monthly report posted")
            except discord.HTTPException as exc:
                logger.error("Failed to post monthly report: %s", exc)

    @auto_monthly_report.before_loop
    async def before_monthly_report(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()

    @auto_monthly_report.error
    async def on_monthly_report_error(self, error: Exception) -> None:
        """Log errors from the monthly report background task."""
        logger.error("Monthly report task error: %s", error, exc_info=error)

    @tasks.loop(time=time(16, 15, tzinfo=ET))
    async def auto_paper_daily(self) -> None:
        """Auto-post paper trading daily summary to #paper-trading at 16:15 ET."""
        now = _now_et()
        if now.weekday() >= 5:
            return

        channel = self._get_paper_channel()
        if channel is None:
            return

        paper_reporter = self._get_paper_reporter()
        if paper_reporter is None:
            return

        try:
            embeds, files = await paper_reporter.daily_report()
            if not embeds:
                return

            # Also run degradation check
            alerts = await paper_reporter.check_degradation()
            embeds.extend(alerts)

            if files:
                await channel.send(embeds=embeds, files=files)
            else:
                await channel.send(embeds=embeds)

            logger.info(
                "Paper daily summary posted to #paper-trading (%d embeds)",
                len(embeds),
            )
        except discord.HTTPException as exc:
            logger.error("Failed to post paper daily summary: %s", exc)
        except Exception as exc:
            logger.error("Paper daily report error: %s", exc, exc_info=True)

    @auto_paper_daily.before_loop
    async def before_paper_daily(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()

    @auto_paper_daily.error
    async def on_paper_daily_error(self, error: Exception) -> None:
        """Log errors from the paper daily background task."""
        logger.error("Paper daily task error: %s", error, exc_info=error)

    # -- Helper methods --------------------------------------------------

    async def _build_daily_embed(
        self,
    ) -> tuple[list[discord.Embed], list[discord.File]]:
        """Build daily summary with paper trading section.

        Returns:
            Tuple of (embeds, chart_files).
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

        main_embed = build_daily_summary_embed(
            date=today,
            signal_stats=signal_stats,
            strategy_summary=strategy_summary,
            rating_stats=rating_stats,
        )

        embeds = [main_embed]
        files: list[discord.File] = []

        # Paper trading section
        paper_reporter = self._get_paper_reporter()
        if paper_reporter is not None:
            try:
                paper_embeds, paper_files = await paper_reporter.daily_report()
                embeds.extend(paper_embeds)
                files.extend(paper_files)
            except Exception as exc:
                logger.error("Failed to build paper daily report: %s", exc)

        return embeds, files

    async def _build_weekly_embed(
        self,
    ) -> tuple[list[discord.Embed], list[discord.File]]:
        """Build weekly review with paper trading section.

        Returns:
            Tuple of (embeds, chart_files).
        """
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

        main_embed = build_weekly_review_embed(
            start_date=start_of_week.date(),
            end_date=end_of_week.date(),
            signal_stats=signal_stats,
            strategy_summary=strategy_summary,
            rating_stats=rating_stats,
        )

        embeds = [main_embed]
        files: list[discord.File] = []

        # Paper trading section
        paper_reporter = self._get_paper_reporter()
        if paper_reporter is not None:
            try:
                paper_embeds, paper_files = await paper_reporter.weekly_report(
                    week_end=end_of_week.date(),
                )
                embeds.extend(paper_embeds)
                files.extend(paper_files)
            except Exception as exc:
                logger.error("Failed to build paper weekly report: %s", exc)

        return embeds, files

    async def _get_signal_stats_since(self, since: datetime) -> dict:
        """Get signal statistics since a given time."""
        signal_logger = self.services.signal_logger
        if signal_logger is None:
            return {"total_signals": 0, "by_type": {}, "by_direction": {}, "outcome_counts": {}}

        return await signal_logger.get_signal_stats(since=since)

    async def _get_strategy_summary(self) -> list[dict]:
        """Get summary of active strategies."""
        manager = self.services.strategy_manager
        if manager is None:
            return []

        try:
            return await manager.list_strategies()
        except Exception:
            return []

    async def _get_rating_stats_since(self, since: datetime) -> dict:
        """Get signal rating statistics since a given time."""
        store = self.services.store
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
        store = self.services.store
        if store is None:
            return

        try:
            db = store._ensure_connected()
            now = _now_et().isoformat()
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
