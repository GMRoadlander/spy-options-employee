"""Analysis cog -- slash commands for on-demand options analysis.

Implements slash commands:
    /gex [ticker]     -- Current GEX levels with chart
    /maxpain [ticker] -- Max pain by nearest expiry
    /levels [ticker]  -- Combined key levels summary
    /strikes [ticker] -- Optimal strike suggestions
    /pcr [ticker]     -- Put/call ratios and dealer positioning
    /status           -- Last update time, data source health
    /analyze [ticker] -- Full analysis (all of the above)
"""

import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from src.analysis.analyzer import AnalysisResult, analyze
from src.config import config
from src.discord_bot.charts import create_gex_chart, create_max_pain_chart
from src.discord_bot.embeds import (
    build_full_analysis_embed,
    build_gex_embed,
    build_levels_embed,
    build_max_pain_embed,
    build_pcr_embed,
    build_status_embed,
    build_strikes_embed,
)

logger = logging.getLogger(__name__)

# Valid tickers for the autocomplete
VALID_TICKERS = ["SPY", "SPX"]


async def ticker_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete for the ticker parameter."""
    return [
        app_commands.Choice(name=t, value=t)
        for t in VALID_TICKERS
        if current.upper() in t
    ]


class AnalysisCog(commands.Cog, name="Analysis"):
    """Slash commands for on-demand SPY/SPX options analysis."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        logger.info("AnalysisCog loaded")

    async def _get_analysis(
        self,
        interaction: discord.Interaction,
        ticker: str,
    ) -> AnalysisResult | None:
        """Fetch chain and run analysis for a ticker with error handling.

        Sends an ephemeral error message to the user if data is unavailable.

        Args:
            interaction: The Discord interaction (for sending error responses).
            ticker: Ticker symbol to analyze.

        Returns:
            AnalysisResult or None if data fetch/analysis failed.
        """
        ticker = ticker.upper()
        if ticker not in VALID_TICKERS:
            await interaction.followup.send(
                f"Invalid ticker `{ticker}`. Valid options: {', '.join(VALID_TICKERS)}",
                ephemeral=True,
            )
            return None

        dm = self.bot.data_manager  # type: ignore[attr-defined]

        try:
            chain = await dm.get_chain(ticker)
        except Exception as exc:
            logger.error("Data fetch failed for %s: %s", ticker, exc, exc_info=True)
            await interaction.followup.send(
                f"Failed to fetch options data for {ticker}. Data sources may be unavailable.",
                ephemeral=True,
            )
            return None

        if chain is None:
            await interaction.followup.send(
                f"No data available for {ticker}. Both CBOE and Tradier sources are down.",
                ephemeral=True,
            )
            return None

        try:
            result = await analyze(chain)
            return result
        except Exception as exc:
            logger.error("Analysis failed for %s: %s", ticker, exc, exc_info=True)
            await interaction.followup.send(
                f"Analysis engine error for {ticker}: {exc}",
                ephemeral=True,
            )
            return None

    @app_commands.command(name="gex", description="Current Gamma Exposure (GEX) levels with chart")
    @app_commands.describe(ticker="Ticker symbol (SPY or SPX)")
    @app_commands.autocomplete(ticker=ticker_autocomplete)
    async def gex(self, interaction: discord.Interaction, ticker: str = "SPY") -> None:
        """Show current GEX levels with a bar chart."""
        await interaction.response.defer()

        result = await self._get_analysis(interaction, ticker)
        if result is None:
            return

        embed = build_gex_embed(result)
        chart = create_gex_chart(result.gex, result.ticker)

        if chart is not None:
            embed.set_image(url=f"attachment://{chart.filename}")
            await interaction.followup.send(embed=embed, file=chart)
        else:
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="maxpain", description="Max pain analysis for nearest expiry")
    @app_commands.describe(ticker="Ticker symbol (SPY or SPX)")
    @app_commands.autocomplete(ticker=ticker_autocomplete)
    async def maxpain(self, interaction: discord.Interaction, ticker: str = "SPY") -> None:
        """Show max pain analysis with pain curve chart."""
        await interaction.response.defer()

        result = await self._get_analysis(interaction, ticker)
        if result is None:
            return

        embed = build_max_pain_embed(result)
        chart = create_max_pain_chart(result.max_pain, result.ticker)

        if chart is not None:
            embed.set_image(url=f"attachment://{chart.filename}")
            await interaction.followup.send(embed=embed, file=chart)
        else:
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="levels", description="Combined key price levels from all engines")
    @app_commands.describe(ticker="Ticker symbol (SPY or SPX)")
    @app_commands.autocomplete(ticker=ticker_autocomplete)
    async def levels(self, interaction: discord.Interaction, ticker: str = "SPY") -> None:
        """Show combined key price levels summary."""
        await interaction.response.defer()

        result = await self._get_analysis(interaction, ticker)
        if result is None:
            return

        embed = build_levels_embed(result)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="strikes", description="Optimal strike recommendations based on GEX and probability")
    @app_commands.describe(ticker="Ticker symbol (SPY or SPX)")
    @app_commands.autocomplete(ticker=ticker_autocomplete)
    async def strikes(self, interaction: discord.Interaction, ticker: str = "SPY") -> None:
        """Show optimal call and put strike recommendations."""
        await interaction.response.defer()

        result = await self._get_analysis(interaction, ticker)
        if result is None:
            return

        embed = build_strikes_embed(result)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="pcr", description="Put/call ratios and dealer positioning analysis")
    @app_commands.describe(ticker="Ticker symbol (SPY or SPX)")
    @app_commands.autocomplete(ticker=ticker_autocomplete)
    async def pcr(self, interaction: discord.Interaction, ticker: str = "SPY") -> None:
        """Show put/call ratio analysis and dealer positioning."""
        await interaction.response.defer()

        result = await self._get_analysis(interaction, ticker)
        if result is None:
            return

        embed = build_pcr_embed(result)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="status", description="System status -- last update, data source health")
    async def status(self, interaction: discord.Interaction) -> None:
        """Show system status and data source health."""
        await interaction.response.defer()

        # Get last_analysis from the scheduler cog if available
        last_update: datetime | None = None
        scheduler_cog = self.bot.get_cog("Scheduler")
        if scheduler_cog is not None:
            last_update = getattr(scheduler_cog, "last_update_time", None)

        # Check data source health by attempting a lightweight cache check
        dm = self.bot.data_manager  # type: ignore[attr-defined]
        cache_info = dm.cache_info

        data_sources: dict[str, bool] = {}
        # CBOE is considered healthy if we have any cached data from it, or we can test
        has_cboe = any(info.get("source") == "cboe" for info in cache_info.values())
        has_tradier = any(info.get("source") == "tradier" for info in cache_info.values())
        data_sources["CBOE CDN"] = has_cboe or (last_update is not None)
        data_sources["Tradier Sandbox"] = has_tradier or bool(config.tradier_token)

        # Check Claude API availability
        data_sources["Claude API"] = bool(config.claude_api_key)

        embed = build_status_embed(
            last_update=last_update,
            data_sources=data_sources,
            tickers_tracked=config.tickers,
        )

        # Add cache details
        if cache_info:
            cache_lines: list[str] = []
            for t, info in cache_info.items():
                cache_lines.append(
                    f"**{t}**: {info['source']} | "
                    f"age {info['age_seconds']}s | "
                    f"TTL {info['ttl_remaining']}s | "
                    f"{info['contracts']} contracts"
                )
            embed.add_field(
                name="Cache",
                value="\n".join(cache_lines),
                inline=False,
            )
        else:
            embed.add_field(name="Cache", value="Empty (no recent fetches)", inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="analyze", description="Full analysis -- GEX, max pain, PCR, levels, strikes")
    @app_commands.describe(ticker="Ticker symbol (SPY or SPX)")
    @app_commands.autocomplete(ticker=ticker_autocomplete)
    async def analyze_cmd(self, interaction: discord.Interaction, ticker: str = "SPY") -> None:
        """Run full analysis and return all embeds with charts."""
        await interaction.response.defer()

        result = await self._get_analysis(interaction, ticker)
        if result is None:
            return

        # Try to generate AI commentary
        commentary = ""
        try:
            from src.ai.commentary import generate_commentary
            commentary = await generate_commentary(result)
        except ImportError:
            logger.debug("AI commentary module not available")
        except Exception as exc:
            logger.warning("AI commentary generation failed: %s", exc)

        embeds = build_full_analysis_embed(result, commentary)

        # Generate charts
        gex_chart = create_gex_chart(result.gex, result.ticker)
        mp_chart = create_max_pain_chart(result.max_pain, result.ticker)

        files: list[discord.File] = []

        # Attach GEX chart to the GEX embed (index 1 in the embeds list)
        if gex_chart is not None:
            embeds[1].set_image(url=f"attachment://{gex_chart.filename}")
            files.append(gex_chart)

        # Attach max pain chart to the max pain embed (index 2)
        if mp_chart is not None:
            embeds[2].set_image(url=f"attachment://{mp_chart.filename}")
            files.append(mp_chart)

        # Discord allows max 10 embeds per message
        # We have at most 6 embeds, so we're within limits
        if files:
            await interaction.followup.send(embeds=embeds, files=files)
        else:
            await interaction.followup.send(embeds=embeds)


async def setup(bot: commands.Bot) -> None:
    """Register the AnalysisCog with the bot."""
    await bot.add_cog(AnalysisCog(bot))
    logger.info("AnalysisCog registered")
