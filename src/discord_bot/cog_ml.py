"""ML Insights cog -- Discord slash commands for ML model outputs.

Implements slash commands:
    /regime       -- Show current market regime state
    /forecast     -- Show volatility forecast
    /sentiment    -- Show market sentiment
    /anomalies    -- Show current anomaly scan
    /reasoning    -- Run Claude reasoning analysis (5-min cooldown)
    /ml_health    -- Show model health dashboard

All commands handle missing/uninitialized ML components gracefully.
"""

import io
import logging

import discord
from discord import app_commands
from discord.ext import commands

from src.discord_bot.embeds import (
    build_anomaly_embed,
    build_forecast_embed,
    build_ml_health_embed,
    build_reasoning_embed,
    build_regime_embed,
    build_sentiment_embed,
)

logger = logging.getLogger(__name__)

# Cooldown for the /reasoning command (seconds)
_REASONING_COOLDOWN_SECONDS = 300.0  # 5 minutes


class MLInsightsCog(commands.Cog, name="MLInsights"):
    """Slash commands exposing Phase 3 ML model outputs to Borey."""

    def __init__(
        self,
        bot: commands.Bot,
        regime_manager=None,
        vol_manager=None,
        sentiment_manager=None,
        anomaly_manager=None,
        flow_analyzer=None,
        reasoning_manager=None,
        learning_manager=None,
        feature_store=None,
    ) -> None:
        self.bot = bot
        self.regime_manager = regime_manager
        self.vol_manager = vol_manager
        self.sentiment_manager = sentiment_manager
        self.anomaly_manager = anomaly_manager
        self.flow_analyzer = flow_analyzer
        self.reasoning_manager = reasoning_manager
        self.learning_manager = learning_manager
        self.feature_store = feature_store
        logger.info("MLInsightsCog loaded")

    # -- /regime ---------------------------------------------------------------

    @app_commands.command(
        name="regime",
        description="Show current market regime (risk-on / risk-off / crisis)",
    )
    async def regime(self, interaction: discord.Interaction) -> None:
        """Show the current HMM regime state with probabilities."""
        await interaction.response.defer()

        if self.regime_manager is None:
            await interaction.followup.send(
                "Regime model not initialized. Run model training first.",
                ephemeral=True,
            )
            return

        try:
            regime_data = await self.regime_manager.get_current_regime()
        except Exception as exc:
            logger.error("Regime query failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to query regime state. Please try again later.",
                ephemeral=True,
            )
            return

        if regime_data is None:
            await interaction.followup.send(
                "No regime data available yet. The model may need training or a daily update.",
                ephemeral=True,
            )
            return

        embed = build_regime_embed(regime_data)

        # Attempt to attach regime timeline chart
        files: list[discord.File] = []
        try:
            if self.feature_store is not None:
                history = await self.feature_store.get_feature_history(
                    "SPX", "regime_state", days=30,
                )
                if history:
                    from src.ml.regime import _STATE_NAMES
                    regime_history = []
                    n_states = 2
                    if self.regime_manager.detector is not None:
                        n_states = self.regime_manager.detector.n_states
                    for date_str, state_val in history:
                        if state_val is not None:
                            state_int = int(state_val)
                            state_name = _STATE_NAMES.get(
                                (n_states, state_int), f"state-{state_int}"
                            )
                            regime_history.append({
                                "date": date_str,
                                "state_name": state_name,
                            })

                    if regime_history:
                        from src.discord_bot.charts import create_regime_timeline_chart
                        chart_buf = create_regime_timeline_chart(regime_history, days=30)
                        if chart_buf is not None:
                            chart_file = discord.File(chart_buf, filename="regime_timeline.png")
                            embed.set_image(url="attachment://regime_timeline.png")
                            files.append(chart_file)
        except Exception as exc:
            logger.warning("Failed to generate regime chart: %s", exc)

        if files:
            await interaction.followup.send(embed=embed, files=files)
        else:
            await interaction.followup.send(embed=embed)

    # -- /forecast -------------------------------------------------------------

    @app_commands.command(
        name="forecast",
        description="Show volatility forecast (1-day and 5-day)",
    )
    async def forecast(self, interaction: discord.Interaction) -> None:
        """Show current vol forecast with IV rank and interpretation."""
        await interaction.response.defer()

        if self.vol_manager is None:
            await interaction.followup.send(
                "Vol model not initialized. Run model training first.",
                ephemeral=True,
            )
            return

        try:
            forecast_data = await self.vol_manager.get_current_forecast()
        except Exception as exc:
            logger.error("Vol forecast query failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to query vol forecast. Please try again later.",
                ephemeral=True,
            )
            return

        if forecast_data is None:
            await interaction.followup.send(
                "No vol forecast data available. The model may need training or a daily update.",
                ephemeral=True,
            )
            return

        # Get additional features for interpretation
        features = None
        if self.feature_store is not None:
            try:
                features = await self.feature_store.get_latest_features("SPX")
            except Exception:
                pass

        embed = build_forecast_embed(forecast_data, features)
        await interaction.followup.send(embed=embed)

    # -- /sentiment ------------------------------------------------------------

    @app_commands.command(
        name="sentiment",
        description="Show current market sentiment score and velocity",
    )
    async def sentiment(self, interaction: discord.Interaction) -> None:
        """Show FinBERT sentiment with contrarian signal detection."""
        await interaction.response.defer()

        if self.sentiment_manager is None:
            await interaction.followup.send(
                "Sentiment model not initialized. Check API key configuration.",
                ephemeral=True,
            )
            return

        try:
            sentiment_data = await self.sentiment_manager.get_current_sentiment()
        except Exception as exc:
            logger.error("Sentiment query failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to query sentiment. Please try again later.",
                ephemeral=True,
            )
            return

        if sentiment_data is None:
            await interaction.followup.send(
                "No sentiment data available. Run a daily update first.",
                ephemeral=True,
            )
            return

        # Enrich with PCR from feature store for contrarian signal
        if self.feature_store is not None:
            try:
                latest = await self.feature_store.get_latest_features("SPX")
                if latest:
                    sentiment_data["volume_pcr"] = latest.get("volume_pcr", 0.0)
            except Exception:
                pass

        embed = build_sentiment_embed(sentiment_data)
        await interaction.followup.send(embed=embed)

    # -- /anomalies ------------------------------------------------------------

    @app_commands.command(
        name="anomalies",
        description="Show current anomaly detection scan results",
    )
    async def anomalies(self, interaction: discord.Interaction) -> None:
        """Show anomaly detection flags with flow summary."""
        await interaction.response.defer()

        if self.anomaly_manager is None:
            await interaction.followup.send(
                "Anomaly detection not initialized. Check bot configuration.",
                ephemeral=True,
            )
            return

        try:
            report = await self.anomaly_manager.get_current_anomalies()
        except Exception as exc:
            logger.error("Anomaly query failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to query anomaly data. Please try again later.",
                ephemeral=True,
            )
            return

        if report is None:
            await interaction.followup.send(
                "No anomaly data available. Run a daily update first.",
                ephemeral=True,
            )
            return

        embed = build_anomaly_embed(report)
        await interaction.followup.send(embed=embed)

    # -- /reasoning ------------------------------------------------------------

    @app_commands.command(
        name="reasoning",
        description="Run Claude reasoning analysis (~$0.01-0.03 per call, 5-min cooldown)",
    )
    @app_commands.describe(ticker="Ticker symbol (default: SPX)")
    @commands.cooldown(1, _REASONING_COOLDOWN_SECONDS, commands.BucketType.user)
    async def reasoning(
        self,
        interaction: discord.Interaction,
        ticker: str = "SPX",
    ) -> None:
        """Run full Claude reasoning analysis with assembled market context."""
        await interaction.response.defer()

        if self.reasoning_manager is None:
            await interaction.followup.send(
                "Reasoning engine not initialized. Check Claude API key configuration.",
                ephemeral=True,
            )
            return

        try:
            analysis = await self.reasoning_manager.run_analysis(ticker)
        except Exception as exc:
            logger.error("Reasoning analysis failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Reasoning analysis failed. Please try again later.",
                ephemeral=True,
            )
            return

        if analysis is None:
            await interaction.followup.send(
                "No analysis could be generated. The reasoning engine may be unavailable.",
                ephemeral=True,
            )
            return

        embed = build_reasoning_embed(analysis)
        await interaction.followup.send(embed=embed)

    # -- /ml_health ------------------------------------------------------------

    @app_commands.command(
        name="ml_health",
        description="Show ML model health dashboard and data source status",
    )
    async def ml_health(self, interaction: discord.Interaction) -> None:
        """Show model accuracy, calibration, and data source status."""
        await interaction.response.defer()

        if self.learning_manager is None:
            await interaction.followup.send(
                "Learning manager not initialized. Check bot configuration.",
                ephemeral=True,
            )
            return

        try:
            health = await self.learning_manager.get_model_health()
        except Exception as exc:
            logger.error("ML health query failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to query model health. Please try again later.",
                ephemeral=True,
            )
            return

        # Enrich with data source status
        from src.config import config
        health["data_sources"] = {
            "Polygon.io": bool(config.polygon_api_key),
            "Unusual Whales": bool(config.unusual_whales_api_key),
            "Claude API": bool(config.claude_api_key),
            "Tastytrade": bool(config.tastytrade_client_secret),
        }

        embed = build_ml_health_embed(health)

        # Add data source status field
        source_lines = []
        for source, configured in health["data_sources"].items():
            status = "[OK]" if configured else "[NOT CONFIGURED]"
            source_lines.append(f"{status} {source}")
        embed.add_field(
            name="Data Sources",
            value="\n".join(source_lines),
            inline=False,
        )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Register the MLInsightsCog with the bot.

    This is called by bot.load_extension(). The cog picks up ML managers
    from bot attributes set during setup_hook().
    """
    cog = MLInsightsCog(
        bot,
        regime_manager=getattr(bot, "regime_manager", None),
        vol_manager=getattr(bot, "vol_manager", None),
        sentiment_manager=getattr(bot, "sentiment_manager", None),
        anomaly_manager=getattr(bot, "anomaly_manager", None),
        flow_analyzer=getattr(bot, "flow_analyzer", None),
        reasoning_manager=getattr(bot, "reasoning_manager", None),
        learning_manager=getattr(bot, "learning_manager", None),
        feature_store=getattr(bot, "feature_store", None),
    )
    await bot.add_cog(cog)
    logger.info("MLInsightsCog registered")
