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
import random
from datetime import datetime, time, timedelta

import discord
from discord.ext import commands, tasks

from src.analysis.analyzer import AnalysisResult, analyze
from src.config import config
from src.discord_bot.charts import create_gex_chart
from src.discord_bot.embeds import build_dashboard_embed, build_full_analysis_embed

logger = logging.getLogger(__name__)

from src.utils import ET, now_et as _now_et


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
        self.services = bot.services  # type: ignore[attr-defined]
        self.last_update_time: datetime | None = None
        self.last_results: dict[str, AnalysisResult] = {}
        self._premarket_posted_today: bool = False
        self._postmarket_posted_today: bool = False
        self._ml_daily_posted_today: bool = False
        self._ml_reasoning_posted_today: bool = False
        self._spotgamma_auth_today: bool = False
        self._spotgamma_premarket_today: bool = False
        self._spotgamma_eod_today: bool = False
        self._spotgamma_last_levels_tick: datetime | None = None
        self._spotgamma_last_hiro_tick: datetime | None = None
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
            self._spotgamma_auth_today = False
            self._spotgamma_premarket_today = False
            self._spotgamma_eod_today = False
            self._spotgamma_last_levels_tick = None
            self._spotgamma_last_hiro_tick = None
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
        dm = self.services.data_manager  # type: ignore[attr-defined]
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
        paper_engine = self.services.paper_engine
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
            paper_engine = self.services.paper_engine
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
            paper_engine = self.services.paper_engine
            if paper_engine is not None:
                # Get the latest chains for settlement pricing
                try:
                    dm = self.services.data_manager  # type: ignore[attr-defined]
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
                portfolio_analyzer = self.services.portfolio_analyzer
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
            store = self.services.store
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

        reasoning_mgr = self.services.reasoning_manager
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

    # -- SpotGamma integration (Phase 4) ----------------------------------------

    async def _jitter(self, max_seconds: int = 30) -> None:
        """Sleep for a random duration to avoid request-pattern detection.

        Args:
            max_seconds: Upper bound for the random sleep (seconds).
        """
        await asyncio.sleep(random.uniform(0, max_seconds))

    def _spotgamma_available(self) -> bool:
        """Return True if SpotGamma client and store are configured."""
        return (
            self.services.spotgamma_client is not None
            and self.services.spotgamma_store is not None
        )

    async def _handle_spotgamma_auth(self) -> None:
        """8:00 AM ET: Authenticate with SpotGamma.

        Called once at start of day so that subsequent data fetches have
        a valid session token.  Skips silently if SpotGamma is not
        configured or if auth has already been done today.
        """
        if self._spotgamma_auth_today:
            return

        now = _now_et()
        auth_time = time(8, 0)

        if now.time() < auth_time:
            return

        if self.services.spotgamma_auth is None:
            return

        self._spotgamma_auth_today = True

        try:
            await self._jitter(10)
            await self.services.spotgamma_auth.authenticate()
            logger.info("SpotGamma: daily authentication complete")
        except Exception as exc:
            logger.error("SpotGamma: authentication failed: %s", exc, exc_info=True)

    async def _handle_spotgamma_levels(self) -> None:
        """Fetch SpotGamma key levels and save to store.

        Called at 9:15 AM ET (pre-market) and every 30 minutes during
        market hours.  Includes jitter to avoid detection.

        PLACEHOLDER: The dict-to-dataclass conversion uses ``.get()`` with
        defaults.  Update on Day 1 when real API response schema is known.
        """
        if not self._spotgamma_available():
            return

        now = _now_et()

        # Pre-market fetch at 9:15 ET (once)
        premarket_time = time(
            config.market_open_hour,
            config.premarket_post_minute,
        )
        is_premarket_window = (
            now.time() >= premarket_time
            and not self._spotgamma_premarket_today
        )

        # During market hours: every 30 minutes
        is_market_tick = False
        if _is_market_hours():
            if (
                self._spotgamma_last_levels_tick is None
                or (now - self._spotgamma_last_levels_tick) >= timedelta(minutes=30)
            ):
                is_market_tick = True

        if not is_premarket_window and not is_market_tick:
            return

        if is_premarket_window:
            self._spotgamma_premarket_today = True

        try:
            await self._jitter(30)
            client = self.services.spotgamma_client
            raw = await client.get_levels("SPX")  # type: ignore[union-attr]

            if raw is None:
                logger.debug("SpotGamma: get_levels returned None — skipping")
                return

            # PLACEHOLDER: dict → dataclass conversion.
            # Keys and structure will be updated on Day 1 when we can
            # inspect the real SpotGamma API response.
            from src.data.spotgamma_models import SpotGammaLevels

            levels = SpotGammaLevels(
                call_wall=float(raw.get("call_wall", 0.0)),
                put_wall=float(raw.get("put_wall", 0.0)),
                vol_trigger=float(raw.get("vol_trigger", 0.0)),
                hedge_wall=float(raw.get("hedge_wall", 0.0)),
                abs_gamma=float(raw.get("abs_gamma", 0.0)),
                timestamp=now,
                ticker=raw.get("ticker", "SPX"),
                source="api",
            )

            store = self.services.spotgamma_store
            await store.save_levels(levels)  # type: ignore[union-attr]
            self._spotgamma_last_levels_tick = now
            logger.info(
                "SpotGamma: saved levels (call_wall=%.1f put_wall=%.1f vol_trigger=%.1f)",
                levels.call_wall,
                levels.put_wall,
                levels.vol_trigger,
            )
        except Exception as exc:
            logger.error("SpotGamma: levels fetch failed: %s", exc, exc_info=True)

    async def _handle_spotgamma_hiro(self) -> None:
        """Fetch HIRO data and save to store.

        Called every 5 minutes during market hours.
        Includes jitter to avoid detection.

        PLACEHOLDER: The dict-to-dataclass conversion uses ``.get()`` with
        defaults.  Update on Day 1 when real API response schema is known.
        """
        if not self._spotgamma_available():
            return

        if not _is_market_hours():
            return

        now = _now_et()

        # Throttle: only fetch every 5 minutes
        if (
            self._spotgamma_last_hiro_tick is not None
            and (now - self._spotgamma_last_hiro_tick) < timedelta(minutes=5)
        ):
            return

        try:
            await self._jitter(15)
            client = self.services.spotgamma_client
            raw = await client.get_hiro("SPX")  # type: ignore[union-attr]

            if raw is None:
                logger.debug("SpotGamma: get_hiro returned None — skipping")
                return

            # PLACEHOLDER: dict → dataclass conversion.
            # Keys and structure will be updated on Day 1.
            from src.data.spotgamma_models import SpotGammaHIRO

            hiro = SpotGammaHIRO(
                timestamp=now,
                hedging_impact=float(raw.get("hedging_impact", 0.0)),
                cumulative_impact=float(raw.get("cumulative_impact", 0.0)),
                ticker=raw.get("ticker", "SPX"),
                source="api",
            )

            store = self.services.spotgamma_store
            await store.save_hiro(hiro)  # type: ignore[union-attr]
            self._spotgamma_last_hiro_tick = now
            logger.debug(
                "SpotGamma: saved HIRO (impact=%.2f cumulative=%.2f)",
                hiro.hedging_impact,
                hiro.cumulative_impact,
            )
        except Exception as exc:
            logger.error("SpotGamma: HIRO fetch failed: %s", exc, exc_info=True)

    async def _handle_spotgamma_eod(self) -> None:
        """Post-market: inject SpotGamma data into daily_features via feature store.

        Called at 4:10 PM ET (same window as ML daily update).  Reads the
        latest levels and HIRO from the SpotGamma store and saves them as
        feature columns: sg_vol_trigger, sg_call_wall, sg_put_wall,
        sg_abs_gamma, sg_hiro_eod.
        """
        if self._spotgamma_eod_today:
            return

        now = _now_et()
        eod_time = time(
            config.market_close_hour,
            config.postmarket_post_minute + 5,  # 16:10 ET
        )

        if now.time() < eod_time:
            return

        if not self._spotgamma_available():
            self._spotgamma_eod_today = True
            return

        feature_store = self.services.feature_store
        if feature_store is None:
            self._spotgamma_eod_today = True
            return

        self._spotgamma_eod_today = True

        try:
            sg_store = self.services.spotgamma_store
            levels = await sg_store.get_latest_levels("SPX")  # type: ignore[union-attr]
            hiro = await sg_store.get_latest_hiro("SPX")  # type: ignore[union-attr]

            features: dict[str, float | int | None] = {}

            if levels is not None:
                features["sg_vol_trigger"] = levels.vol_trigger
                features["sg_call_wall"] = levels.call_wall
                features["sg_put_wall"] = levels.put_wall
                features["sg_abs_gamma"] = levels.abs_gamma

            if hiro is not None:
                features["sg_hiro_eod"] = hiro.cumulative_impact

            if not features:
                logger.info("SpotGamma EOD: no data available — skipping feature save")
                return

            date_str = now.strftime("%Y-%m-%d")
            await feature_store.save_features("SPX", date_str, features)
            logger.info(
                "SpotGamma EOD: saved %d features to daily_features for %s",
                len(features),
                date_str,
            )
        except Exception as exc:
            logger.error("SpotGamma EOD: feature save failed: %s", exc, exc_info=True)

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

        # Handle SpotGamma daily auth (8:00 AM ET)
        await self._handle_spotgamma_auth()

        # Handle pre-market post
        await self._handle_premarket()

        # Handle SpotGamma levels (pre-market at 9:15, then every 30 min)
        await self._handle_spotgamma_levels()

        # Handle SpotGamma HIRO (every 5 min during market hours)
        await self._handle_spotgamma_hiro()

        # Handle post-market post
        await self._handle_postmarket()

        # Handle SpotGamma EOD (16:10 ET — inject into daily_features)
        await self._handle_spotgamma_eod()

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
