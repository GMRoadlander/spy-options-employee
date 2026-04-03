"""Scheduler cog -- background loop for periodic analysis during market hours.

Behavior:
    - Runs a @tasks.loop every config.update_interval_minutes during market hours (9:30-16:00 ET)
    - Waits until 9:15 ET to post a pre-market analysis and call paper engine start_of_day()
    - Each market-hours tick: fetch chains, analyze, run paper engine tick
    - At 16:05 ET, sends a post-market summary, runs paper EOD settlement + daily snapshot
    - At 16:10 ET, runs ML daily update (features, regime, vol, sentiment, anomaly)
    - At 16:30 ET, runs ML reasoning briefing and posts to journal channel
    - Tracks last_analysis for the /status command
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Optional

import discord
from discord.ext import commands, tasks

from src.analysis.analyzer import AnalysisResult, analyze
from src.config import config
from src.discord_bot.charts import create_gex_chart
from src.discord_bot.embeds import build_dashboard_embed, build_full_analysis_embed

logger = logging.getLogger(__name__)

try:
    import zoneinfo
    ET = zoneinfo.ZoneInfo(config.timezone)
except ImportError:
    # Fallback for older Python without zoneinfo
    from datetime import timezone
    ET = timezone(timedelta(hours=-5))  # type: ignore[assignment]


def _now_et() -> datetime:
    """Get the current time in Eastern Time."""
    return datetime.now(ET)


def _is_market_hours() -> bool:
    """Check if current time is within market hours (9:30 AM - 4:00 PM ET).

    Returns:
        True if current time is within market trading hours.
    """
    now = _now_et()

    # Skip weekends (Monday=0, Sunday=6)
    if now.weekday() >= 5:
        return False

    market_open = time(config.market_open_hour, config.market_open_minute)
    market_close = time(config.market_close_hour, config.market_close_minute)

    return market_open <= now.time() <= market_close


def _seconds_until(target_hour: int, target_minute: int) -> float:
    """Calculate seconds until a specific time today (or tomorrow if passed).

    Args:
        target_hour: Target hour in ET (24h format).
        target_minute: Target minute.

    Returns:
        Seconds until the target time.
    """
    now = _now_et()
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

    if target <= now:
        # Target time has passed today; calculate for tomorrow
        target += timedelta(days=1)

    delta = target - now
    return delta.total_seconds()


class SchedulerCog(commands.Cog, name="Scheduler"):
    """Background task that posts periodic market analysis during trading hours."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.last_update_time: datetime | None = None
        self.last_results: dict[str, AnalysisResult] = {}
        self._premarket_posted_today: bool = False
        self._postmarket_posted_today: bool = False
        self._ml_daily_posted_today: bool = False
        self._ml_reasoning_posted_today: bool = False
        self._last_date: str = ""  # Track date for resetting daily flags
        logger.info("SchedulerCog loaded")

    async def cog_load(self) -> None:
        """Start the background loop when the cog is loaded."""
        self.market_loop.start()
        logger.info("Scheduler market loop started")

    async def cog_unload(self) -> None:
        """Stop the background loop when the cog is unloaded."""
        self.market_loop.cancel()
        logger.info("Scheduler market loop stopped")

    def _reset_daily_flags(self) -> None:
        """Reset daily flags if the date has changed."""
        today = _now_et().strftime("%Y-%m-%d")
        if today != self._last_date:
            self._premarket_posted_today = False
            self._postmarket_posted_today = False
            self._ml_daily_posted_today = False
            self._ml_reasoning_posted_today = False
            self._last_date = today
            logger.info("Daily flags reset for %s", today)

    def _get_analysis_channel(self) -> discord.TextChannel | None:
        """Get the analysis channel from config."""
        if config.analysis_channel_id == 0:
            logger.warning("Analysis channel ID not configured")
            return None
        channel = self.bot.get_channel(config.analysis_channel_id)
        if channel is None:
            logger.warning("Analysis channel %d not found", config.analysis_channel_id)
            return None
        if not isinstance(channel, discord.TextChannel):
            logger.warning("Analysis channel %d is not a text channel", config.analysis_channel_id)
            return None
        return channel

    async def _run_full_cycle(self) -> dict[str, AnalysisResult]:
        """Fetch all chains, run analysis on each, and return results.

        After analysis, runs the paper trading engine tick if available,
        passing the live chain data for order fills and mark-to-market.

        Returns:
            Dict mapping ticker to AnalysisResult for successful analyses.
        """
        dm = self.bot.data_manager  # type: ignore[attr-defined]
        results: dict[str, AnalysisResult] = {}

        try:
            chains = await dm.get_all_chains()
        except Exception as exc:
            logger.error("Failed to fetch chains in scheduler cycle: %s", exc, exc_info=True)
            return results

        for ticker, chain in chains.items():
            try:
                result = await analyze(chain)
                results[ticker] = result
            except Exception as exc:
                logger.error("Analysis failed for %s in scheduler cycle: %s", ticker, exc, exc_info=True)

        if results:
            self.last_update_time = _now_et()
            self.last_results = results
            logger.info("Scheduler cycle complete: analyzed %s", list(results.keys()))
        else:
            logger.warning("Scheduler cycle produced no results")

        # Run paper trading engine tick with live chain data
        paper_engine = getattr(self.bot, "paper_engine", None)
        if paper_engine is not None and chains:
            try:
                tick_result = await paper_engine.tick(chains)
                if tick_result.orders_submitted or tick_result.orders_filled or tick_result.positions_closed:
                    logger.info(
                        "Paper engine tick: submitted=%d filled=%d opened=%d closed=%d exits=%d",
                        tick_result.orders_submitted,
                        tick_result.orders_filled,
                        tick_result.positions_opened,
                        tick_result.positions_closed,
                        len(tick_result.exit_signals),
                    )
                if tick_result.errors:
                    logger.warning("Paper engine tick errors: %s", tick_result.errors)
            except Exception as exc:
                logger.error("Paper engine tick failed: %s", exc, exc_info=True)

        return results

    async def _generate_commentary(self, result: AnalysisResult) -> str:
        """Attempt to generate AI commentary, returning empty string on failure.

        Args:
            result: Analysis result to generate commentary for.

        Returns:
            Commentary string, or empty string if unavailable.
        """
        try:
            from src.ai.commentary import generate_commentary
            return await generate_commentary(result)
        except ImportError:
            logger.debug("AI commentary module not available")
            return ""
        except Exception as exc:
            logger.warning("AI commentary generation failed: %s", exc)
            return ""

    async def _post_dashboard(self, results: dict[str, AnalysisResult], title_prefix: str = "") -> None:
        """Post a dashboard embed to the analysis channel.

        Args:
            results: Dict of ticker -> AnalysisResult.
            title_prefix: Optional prefix for the embed title (e.g., "Pre-Market" or "Post-Market").
        """
        channel = self._get_analysis_channel()
        if channel is None:
            return

        # Generate commentary for the first available ticker
        commentary = ""
        for result in results.values():
            commentary = await self._generate_commentary(result)
            if commentary:
                break

        embed = build_dashboard_embed(results, commentary)
        if title_prefix:
            embed.title = f"{title_prefix} | {embed.title}"

        # Attach GEX chart for the primary ticker (SPY) if available
        files: list[discord.File] = []
        if "SPY" in results:
            chart = create_gex_chart(results["SPY"].gex, "SPY")
            if chart is not None:
                embed.set_image(url=f"attachment://{chart.filename}")
                files.append(chart)

        try:
            if files:
                await channel.send(embed=embed, files=files)
            else:
                await channel.send(embed=embed)
            logger.info("Dashboard posted to channel %d", config.analysis_channel_id)
        except discord.HTTPException as exc:
            logger.error("Failed to post dashboard: %s", exc)

    async def _handle_premarket(self) -> None:
        """Post pre-market analysis at 9:15 ET and initialize paper engine."""
        if self._premarket_posted_today:
            return

        now = _now_et()
        premarket_time = time(
            config.market_open_hour,
            config.premarket_post_minute,
        )

        if now.time() >= premarket_time:
            logger.info("Posting pre-market analysis")

            # Initialize paper trading engine for the day
            paper_engine = getattr(self.bot, "paper_engine", None)
            if paper_engine is not None:
                try:
                    await paper_engine.start_of_day()
                    logger.info("Paper engine: start of day complete")
                except Exception as exc:
                    logger.error("Paper engine start_of_day failed: %s", exc, exc_info=True)

            results = await self._run_full_cycle()
            if results:
                await self._post_dashboard(results, title_prefix="Pre-Market")
                self._premarket_posted_today = True

                # Fire alerts for the first cycle
                alerts_cog = self.bot.get_cog("Alerts")
                if alerts_cog is not None:
                    for ticker, result in results.items():
                        await alerts_cog.check_alerts(result)  # type: ignore[attr-defined]

    async def _handle_postmarket(self) -> None:
        """Post post-market summary at 16:05 ET, run paper EOD settlement."""
        if self._postmarket_posted_today:
            return

        now = _now_et()
        postmarket_time = time(
            config.market_close_hour,
            config.postmarket_post_minute,
        )

        if now.time() >= postmarket_time:
            logger.info("Posting post-market summary")
            results = await self._run_full_cycle()
            if results:
                await self._post_dashboard(results, title_prefix="Post-Market Summary")
                self._postmarket_posted_today = True

            # Paper trading: EOD settlement and daily snapshot
            paper_engine = getattr(self.bot, "paper_engine", None)
            if paper_engine is not None:
                # Get the latest chains for settlement pricing
                try:
                    dm = self.bot.data_manager  # type: ignore[attr-defined]
                    chains = await dm.get_all_chains()
                except Exception:
                    chains = {}

                # Handle EOD settlement (AM/PM)
                try:
                    closed_ids = await paper_engine.handle_eod_settlement(chains)
                    if closed_ids:
                        logger.info(
                            "Paper engine EOD: settled %d positions (%s)",
                            len(closed_ids),
                            ", ".join(f"#{pid}" for pid in closed_ids),
                        )
                except Exception as exc:
                    logger.error("Paper engine EOD settlement failed: %s", exc, exc_info=True)

                # Take daily portfolio snapshot
                try:
                    await paper_engine.pnl_calculator.take_daily_snapshot()
                    logger.info("Paper engine: daily snapshot complete")
                except Exception as exc:
                    logger.error("Paper engine daily snapshot failed: %s", exc, exc_info=True)

                # Portfolio risk analysis (Phase 4-5)
                portfolio_analyzer = getattr(self.bot, "portfolio_analyzer", None)
                if portfolio_analyzer is not None:
                    try:
                        open_pos = await paper_engine.position_tracker.get_open_positions()
                        if open_pos:
                            chain = chains.get("SPX") or chains.get("SPY")
                            spot = chain.spot_price if chain else 0.0
                            if spot > 0:
                                greeks = portfolio_analyzer.compute_greeks(open_pos, spot)
                                logger.info(
                                    "Portfolio daily analysis complete: delta=%.1f gamma=%.4f theta=%.1f vega=%.1f",
                                    greeks.delta, greeks.gamma, greeks.theta, greeks.vega,
                                )
                    except Exception as exc:
                        logger.error("Portfolio daily analysis failed: %s", exc, exc_info=True)

                # Paper trading alerts (Phase 4-7)
                try:
                    summary = await paper_engine.get_portfolio_summary()
                    # Alert on significant daily PnL (>2% of capital)
                    if abs(summary.daily_pnl) > paper_engine._config.starting_capital * 0.02:
                        paper_cog = self.bot.get_cog("PaperTrading")
                        if paper_cog is not None and hasattr(paper_cog, "post_daily_pnl_alert"):
                            await paper_cog.post_daily_pnl_alert(summary)
                except Exception as exc:
                    logger.error("Paper alert check failed: %s", exc, exc_info=True)

            # Recurring database cleanup (don't rely solely on shutdown)
            store = getattr(self.bot, "store", None)
            if store is not None:
                try:
                    await store.cleanup_old()
                    logger.info("Post-market: database cleanup complete")
                except Exception as exc:
                    logger.error("Post-market: database cleanup failed: %s", exc, exc_info=True)

    # -- ML daily update pipeline (Phase 3) ------------------------------------

    async def _handle_ml_daily_update(self) -> None:
        """Run ML daily update at 16:10 ET (after post-market summary at 16:05).

        Sequentially updates: features -> regime -> vol -> sentiment -> anomaly.
        Each step has error handling -- if one model fails, others continue.
        """
        if self._ml_daily_posted_today:
            return

        now = _now_et()
        ml_update_time = time(
            config.market_close_hour,
            config.postmarket_post_minute + 5,  # 16:10 ET (5 min after post-market)
        )

        if now.time() < ml_update_time:
            return

        self._ml_daily_posted_today = True
        logger.info("Starting ML daily update pipeline")

        bot = self.bot

        # Step 1: Update regime state
        regime_mgr = getattr(bot, "regime_manager", None)
        if regime_mgr is not None:
            try:
                regime_result = await regime_mgr.get_current_regime()
                logger.info("ML daily: regime update complete (state=%s)",
                            regime_result.get("state_name") if regime_result else "none")
            except Exception as exc:
                logger.error("ML daily: regime update failed: %s", exc)

        # Step 2: Update vol forecast
        vol_mgr = getattr(bot, "vol_manager", None)
        if vol_mgr is not None:
            try:
                vol_result = await vol_mgr.get_current_forecast()
                logger.info("ML daily: vol forecast update complete (1d=%s)",
                            vol_result.get("vol_forecast_1d") if vol_result else "none")
            except Exception as exc:
                logger.error("ML daily: vol forecast update failed: %s", exc)

        # Step 3: Update sentiment
        sentiment_mgr = getattr(bot, "sentiment_manager", None)
        if sentiment_mgr is not None:
            try:
                sent_result = await sentiment_mgr.get_current_sentiment()
                logger.info("ML daily: sentiment update complete (score=%s)",
                            sent_result.get("sentiment_score") if sent_result else "none")
            except Exception as exc:
                logger.error("ML daily: sentiment update failed: %s", exc)

        # Step 4: Update anomaly detection
        anomaly_mgr = getattr(bot, "anomaly_manager", None)
        if anomaly_mgr is not None:
            try:
                anomaly_result = await anomaly_mgr.get_current_anomalies()
                score = anomaly_result.overall_score if anomaly_result else "none"
                logger.info("ML daily: anomaly scan complete (score=%s)", score)
            except Exception as exc:
                logger.error("ML daily: anomaly scan failed: %s", exc)

        # Step 5: Update calibration (continuous learning)
        learning_mgr = getattr(bot, "learning_manager", None)
        if learning_mgr is not None:
            try:
                cal_result = await learning_mgr.update_calibration()
                logger.info("ML daily: calibration update complete (%s)", cal_result)
            except Exception as exc:
                logger.error("ML daily: calibration update failed: %s", exc)

        logger.info("ML daily update pipeline complete")

    async def _handle_ml_reasoning_briefing(self) -> None:
        """Run ML reasoning analysis at 16:30 ET and post to journal channel.

        Assembles MarketContext and runs Claude reasoning analysis, then
        posts the summary to the journal channel as an automated briefing.
        """
        if self._ml_reasoning_posted_today:
            return

        now = _now_et()
        reasoning_time = time(16, 30)  # 4:30 PM ET

        if now.time() < reasoning_time:
            return

        self._ml_reasoning_posted_today = True

        reasoning_mgr = getattr(self.bot, "reasoning_manager", None)
        if reasoning_mgr is None:
            logger.debug("ML reasoning briefing skipped -- ReasoningManager not available")
            return

        logger.info("Starting ML reasoning briefing")

        try:
            analysis = await reasoning_mgr.run_analysis("SPX")
        except Exception as exc:
            logger.error("ML reasoning briefing failed: %s", exc)
            return

        if analysis is None:
            logger.warning("ML reasoning briefing produced no result")
            return

        # Post to journal channel
        journal_channel = self._get_journal_channel()
        if journal_channel is None:
            logger.debug("ML reasoning briefing skipped -- no journal channel configured")
            return

        try:
            from src.discord_bot.embeds import build_reasoning_embed
            embed = build_reasoning_embed(analysis)
            embed.title = "Daily ML Intelligence Briefing"
            await journal_channel.send(embed=embed)
            logger.info("ML reasoning briefing posted to journal channel")
        except Exception as exc:
            logger.error("Failed to post ML reasoning briefing: %s", exc)

    def _get_journal_channel(self) -> discord.TextChannel | None:
        """Get the journal channel from config."""
        channel_id = getattr(config, "journal_channel_id", 0)
        if channel_id == 0:
            channel_id = config.analysis_channel_id
        if channel_id == 0:
            return None
        channel = self.bot.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.TextChannel):
            return None
        return channel

    @tasks.loop(minutes=config.update_interval_minutes)
    async def market_loop(self) -> None:
        """Main background loop that runs every update_interval_minutes."""
        self._reset_daily_flags()

        now = _now_et()
        logger.debug("Scheduler tick at %s (weekday=%d)", now.strftime("%H:%M:%S"), now.weekday())

        # Skip weekends
        if now.weekday() >= 5:
            logger.debug("Skipping scheduler tick -- weekend")
            return

        # Handle pre-market post
        await self._handle_premarket()

        # Handle post-market post
        await self._handle_postmarket()

        # Handle ML daily update (16:05 ET, after post-market)
        await self._handle_ml_daily_update()

        # Handle ML reasoning briefing (16:30 ET, after features are computed)
        await self._handle_ml_reasoning_briefing()

        # Regular market hours update
        if _is_market_hours():
            results = await self._run_full_cycle()
            if results:
                await self._post_dashboard(results)

                # Check alerts after each analysis
                alerts_cog = self.bot.get_cog("Alerts")
                if alerts_cog is not None:
                    for ticker, result in results.items():
                        await alerts_cog.check_alerts(result)  # type: ignore[attr-defined]

    @market_loop.before_loop
    async def before_market_loop(self) -> None:
        """Wait for bot to be ready and optionally wait until near market open."""
        await self.bot.wait_until_ready()
        logger.info("Bot is ready, scheduler loop will begin")

        # If it's a weekday and before 9:15 ET, wait until 9:15
        now = _now_et()
        if now.weekday() < 5:
            premarket_time = time(
                config.market_open_hour,
                config.premarket_post_minute,
            )
            if now.time() < premarket_time:
                wait_secs = _seconds_until(
                    config.market_open_hour,
                    config.premarket_post_minute,
                )
                logger.info(
                    "Waiting %.0f seconds until pre-market time (%02d:%02d ET)",
                    wait_secs,
                    config.market_open_hour,
                    config.premarket_post_minute,
                )
                await asyncio.sleep(wait_secs)

    @market_loop.error
    async def market_loop_error(self, error: BaseException) -> None:
        """Handle errors in the market loop to prevent it from stopping."""
        logger.error("Scheduler loop error: %s", error, exc_info=True)
        # The loop will automatically restart on the next interval


async def setup(bot: commands.Bot) -> None:
    """Register the SchedulerCog with the bot."""
    await bot.add_cog(SchedulerCog(bot))
    logger.info("SchedulerCog registered")
