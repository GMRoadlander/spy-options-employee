"""SpotGamma cog -- Discord slash commands for SpotGamma levels and HIRO.

Implements slash commands via a ``spotgamma`` command group:
    /spotgamma set <levels>  -- Manual input of today's SpotGamma levels
    /spotgamma show          -- Display current SpotGamma levels
    /spotgamma compare       -- Side-by-side comparison with our GEX levels
    /spotgamma hiro          -- Show current HIRO reading
    /spotgamma status        -- Auth status, data freshness, enabled flag

All commands degrade gracefully when the SpotGammaStore is not configured.
"""

import logging
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from src.config import config
from src.discord_bot.embeds import (
    build_spotgamma_comparison_embed,
    build_spotgamma_levels_embed,
)

logger = logging.getLogger(__name__)

# Color constants (match embeds.py)
COLOR_BULLISH = 0x00FF00
COLOR_BEARISH = 0xFF0000
COLOR_NEUTRAL = 0xFFFF00
COLOR_INFO = 0x0099FF


class SpotGammaCog(commands.GroupCog, name="spotgamma"):
    """Slash commands for SpotGamma level management and comparison."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.services = bot.services  # type: ignore[attr-defined]
        logger.info("SpotGammaCog loaded")

    def _get_store(self):
        """Return SpotGammaStore or None if not configured."""
        return self.services.spotgamma_store

    # -- /spotgamma set --------------------------------------------------------

    @app_commands.command(
        name="set",
        description="Manually input today's SpotGamma levels",
    )
    @app_commands.describe(
        call_wall="Call Wall strike (largest positive gamma)",
        put_wall="Put Wall strike (largest negative gamma)",
        vol_trigger="Vol Trigger level (gamma flip equivalent)",
        hedge_wall="Hedge Wall strike (concentrated hedging)",
        abs_gamma="Absolute Gamma strike (largest absolute gamma)",
    )
    async def sg_set(
        self,
        interaction: discord.Interaction,
        call_wall: float,
        put_wall: float,
        vol_trigger: float,
        hedge_wall: float,
        abs_gamma: float,
    ) -> None:
        """Save manually entered SpotGamma levels."""
        await interaction.response.defer()

        store = self._get_store()
        if store is None:
            await interaction.followup.send(
                "SpotGamma not configured. Database store is unavailable.",
                ephemeral=True,
            )
            return

        from src.data.spotgamma_models import SpotGammaLevels

        levels = SpotGammaLevels(
            call_wall=call_wall,
            put_wall=put_wall,
            vol_trigger=vol_trigger,
            hedge_wall=hedge_wall,
            abs_gamma=abs_gamma,
            timestamp=datetime.now(timezone.utc),
            ticker="SPX",
            source="manual",
        )

        try:
            await store.save_levels(levels)
        except Exception as exc:
            logger.error("Failed to save SpotGamma levels: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to save SpotGamma levels. Check logs for details.",
                ephemeral=True,
            )
            return

        embed = build_spotgamma_levels_embed(levels)
        embed.title = "SpotGamma Levels Saved"
        await interaction.followup.send(embed=embed)

    # -- /spotgamma show -------------------------------------------------------

    @app_commands.command(
        name="show",
        description="Display current SpotGamma levels",
    )
    async def sg_show(self, interaction: discord.Interaction) -> None:
        """Show the most recently saved SpotGamma levels."""
        await interaction.response.defer()

        store = self._get_store()
        if store is None:
            await interaction.followup.send(
                "SpotGamma not configured. Database store is unavailable.",
                ephemeral=True,
            )
            return

        try:
            levels = await store.get_latest_levels("SPX")
        except Exception as exc:
            logger.error("Failed to fetch SpotGamma levels: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to fetch SpotGamma levels. Check logs for details.",
                ephemeral=True,
            )
            return

        if levels is None:
            await interaction.followup.send(
                "No levels set today. Use `/spotgamma set` or wait for auto-fetch.",
                ephemeral=True,
            )
            return

        # Check if levels are from today
        now = datetime.now(timezone.utc)
        level_date = levels.timestamp.strftime("%Y-%m-%d")
        today_str = now.strftime("%Y-%m-%d")

        embed = build_spotgamma_levels_embed(levels)

        if level_date != today_str:
            embed.add_field(
                name="Staleness Warning",
                value=f"These levels are from **{level_date}**, not today.",
                inline=False,
            )

        await interaction.followup.send(embed=embed)

    # -- /spotgamma compare ----------------------------------------------------

    @app_commands.command(
        name="compare",
        description="Compare SpotGamma levels with our GEX analysis",
    )
    async def sg_compare(self, interaction: discord.Interaction) -> None:
        """Side-by-side comparison of our GEX levels vs SpotGamma levels."""
        await interaction.response.defer()

        store = self._get_store()
        if store is None:
            await interaction.followup.send(
                "SpotGamma not configured. Database store is unavailable.",
                ephemeral=True,
            )
            return

        # Fetch SpotGamma levels
        try:
            sg_levels = await store.get_latest_levels("SPX")
        except Exception as exc:
            logger.error("Failed to fetch SpotGamma levels: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to fetch SpotGamma levels.",
                ephemeral=True,
            )
            return

        if sg_levels is None:
            await interaction.followup.send(
                "No SpotGamma levels available. Use `/spotgamma set` first.",
                ephemeral=True,
            )
            return

        # Run our own GEX analysis
        dm = self.services.data_manager
        if dm is None:
            await interaction.followup.send(
                "Data manager not available. Cannot run GEX comparison.",
                ephemeral=True,
            )
            return

        try:
            chain = await dm.get_chain("SPY")
        except Exception as exc:
            logger.error("Data fetch failed for comparison: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to fetch options chain data for comparison.",
                ephemeral=True,
            )
            return

        if chain is None:
            await interaction.followup.send(
                "No options chain data available for comparison.",
                ephemeral=True,
            )
            return

        from src.analysis.gex import calculate_gex

        try:
            gex_result = calculate_gex(chain)
        except Exception as exc:
            logger.error("GEX calculation failed: %s", exc, exc_info=True)
            await interaction.followup.send(
                "GEX analysis failed. Check logs for details.",
                ephemeral=True,
            )
            return

        embed = build_spotgamma_comparison_embed(
            sg_levels=sg_levels,
            gex_result=gex_result,
            spot_price=chain.spot_price,
        )
        await interaction.followup.send(embed=embed)

    # -- /spotgamma hiro -------------------------------------------------------

    @app_commands.command(
        name="hiro",
        description="Show current HIRO (Hedging Impact Real-time Overview)",
    )
    async def sg_hiro(self, interaction: discord.Interaction) -> None:
        """Show the latest HIRO snapshot."""
        await interaction.response.defer()

        store = self._get_store()
        if store is None:
            await interaction.followup.send(
                "SpotGamma not configured. Database store is unavailable.",
                ephemeral=True,
            )
            return

        try:
            hiro = await store.get_latest_hiro("SPX")
        except Exception as exc:
            logger.error("Failed to fetch HIRO data: %s", exc, exc_info=True)
            await interaction.followup.send(
                "Failed to fetch HIRO data. Check logs for details.",
                ephemeral=True,
            )
            return

        if hiro is None:
            await interaction.followup.send(
                "HIRO data not available.",
                ephemeral=True,
            )
            return

        # Determine color from hedging impact
        if hiro.hedging_impact > 0:
            color = COLOR_BULLISH
        elif hiro.hedging_impact < 0:
            color = COLOR_BEARISH
        else:
            color = COLOR_NEUTRAL

        embed = discord.Embed(
            title="HIRO -- Hedging Impact Real-time Overview",
            description=(
                "Positive = bullish hedging flows | "
                "Negative = bearish hedging flows"
            ),
            color=color,
            timestamp=hiro.timestamp,
        )
        embed.add_field(
            name="Hedging Impact",
            value=f"{hiro.hedging_impact:+,.2f}",
            inline=True,
        )
        embed.add_field(
            name="Cumulative Impact",
            value=f"{hiro.cumulative_impact:+,.2f}",
            inline=True,
        )
        embed.add_field(
            name="Source",
            value=hiro.source,
            inline=True,
        )
        embed.set_footer(text=f"SPY Options Employee | {hiro.ticker}")

        await interaction.followup.send(embed=embed)

    # -- /spotgamma status -----------------------------------------------------

    @app_commands.command(
        name="status",
        description="SpotGamma integration status and data freshness",
    )
    async def sg_status(self, interaction: discord.Interaction) -> None:
        """Show SpotGamma auth status, last fetch, data freshness."""
        await interaction.response.defer()

        enabled = config.spotgamma_enabled
        has_credentials = bool(config.spotgamma_email and config.spotgamma_password)

        store = self._get_store()
        store_available = store is not None

        embed = discord.Embed(
            title="SpotGamma Integration Status",
            color=COLOR_BULLISH if (enabled and store_available) else COLOR_INFO,
            timestamp=datetime.now(timezone.utc),
        )

        # Config status
        embed.add_field(
            name="Enabled",
            value="Yes" if enabled else "No",
            inline=True,
        )
        embed.add_field(
            name="Credentials",
            value="Configured" if has_credentials else "Not set",
            inline=True,
        )
        embed.add_field(
            name="Store",
            value="Available" if store_available else "Not configured",
            inline=True,
        )

        # Data freshness
        if store_available:
            try:
                levels = await store.get_latest_levels("SPX")
                if levels is not None:
                    embed.add_field(
                        name="Last Levels",
                        value=(
                            f"{levels.timestamp.strftime('%Y-%m-%d %H:%M')} UTC\n"
                            f"Source: {levels.source}"
                        ),
                        inline=True,
                    )
                else:
                    embed.add_field(
                        name="Last Levels",
                        value="No data",
                        inline=True,
                    )

                hiro = await store.get_latest_hiro("SPX")
                if hiro is not None:
                    embed.add_field(
                        name="Last HIRO",
                        value=(
                            f"{hiro.timestamp.strftime('%Y-%m-%d %H:%M')} UTC\n"
                            f"Source: {hiro.source}"
                        ),
                        inline=True,
                    )
                else:
                    embed.add_field(
                        name="Last HIRO",
                        value="No data",
                        inline=True,
                    )
            except Exception as exc:
                logger.error("Failed to query SpotGamma status: %s", exc)
                embed.add_field(
                    name="Data Query",
                    value="Error querying data",
                    inline=False,
                )

        embed.set_footer(text="SPY Options Employee | SpotGamma")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Register the SpotGammaCog with the bot."""
    await bot.add_cog(SpotGammaCog(bot))
    logger.info("SpotGammaCog registered")
