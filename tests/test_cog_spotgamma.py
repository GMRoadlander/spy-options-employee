"""Tests for the SpotGamma cog, embed builders, and graceful degradation."""

import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from src.analysis.gex import GEXResult
from src.data.spotgamma_models import SpotGammaHIRO, SpotGammaLevels
from src.discord_bot.embeds import (
    build_spotgamma_comparison_embed,
    build_spotgamma_levels_embed,
)
from src.services import ServiceRegistry


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _sample_levels(**overrides) -> SpotGammaLevels:
    """Create sample SpotGamma levels for testing."""
    defaults = dict(
        call_wall=5900.0,
        put_wall=5700.0,
        vol_trigger=5800.0,
        hedge_wall=5850.0,
        abs_gamma=5800.0,
        timestamp=datetime(2026, 4, 6, 14, 30, tzinfo=timezone.utc),
        ticker="SPX",
        source="manual",
    )
    defaults.update(overrides)
    return SpotGammaLevels(**defaults)


def _sample_hiro(**overrides) -> SpotGammaHIRO:
    """Create sample HIRO data for testing."""
    defaults = dict(
        timestamp=datetime(2026, 4, 6, 15, 0, tzinfo=timezone.utc),
        hedging_impact=1250.5,
        cumulative_impact=4500.0,
        ticker="SPX",
        source="api",
    )
    defaults.update(overrides)
    return SpotGammaHIRO(**defaults)


def _sample_gex_result(**overrides) -> GEXResult:
    """Create sample GEX result for comparison tests."""
    defaults = dict(
        net_gex=1_000_000.0,
        gamma_flip=5805.0,
        gamma_ceiling=5895.0,
        gamma_floor=5710.0,
        squeeze_probability=0.2,
        strikes=[5700.0, 5750.0, 5800.0, 5850.0, 5900.0],
        call_gex=[100.0, 200.0, 300.0, 400.0, 500.0],
        put_gex=[-500.0, -400.0, -300.0, -200.0, -100.0],
        net_gex_by_strike=[-400.0, -200.0, 0.0, 200.0, 400.0],
    )
    defaults.update(overrides)
    return GEXResult(**defaults)


def _make_bot(spotgamma_store=None, data_manager=None):
    """Create a mock bot with configurable services."""
    bot = MagicMock()
    bot.services = ServiceRegistry(
        spotgamma_store=spotgamma_store,
        data_manager=data_manager,
    )
    return bot


def _make_interaction(bot=None):
    """Create a mock Discord interaction."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.__str__ = MagicMock(return_value="TestUser#1234")
    if bot is not None:
        interaction.client = bot
    return interaction


def _make_cog(bot=None):
    """Create a SpotGammaCog instance."""
    from src.discord_bot.cog_spotgamma import SpotGammaCog

    if bot is None:
        bot = _make_bot()
    cog = SpotGammaCog.__new__(SpotGammaCog)
    cog.bot = bot
    cog.services = bot.services
    return cog


def _get_followup_content(interaction):
    """Extract the content string from a followup.send call."""
    call_args = interaction.followup.send.call_args
    if call_args.args:
        return str(call_args.args[0])
    return call_args.kwargs.get("content", "")


def _get_followup_embed(interaction) -> discord.Embed | None:
    """Extract the embed from a followup.send call."""
    call_args = interaction.followup.send.call_args
    return call_args.kwargs.get("embed")


# ---------------------------------------------------------------------------
# Embed builder tests
# ---------------------------------------------------------------------------


class TestSpotGammaLevelsEmbed(unittest.TestCase):
    """Tests for build_spotgamma_levels_embed."""

    def test_all_fields_present(self):
        """Embed contains all 5 levels plus source."""
        levels = _sample_levels()
        embed = build_spotgamma_levels_embed(levels)

        self.assertIsInstance(embed, discord.Embed)
        self.assertIn("SpotGamma Levels", embed.title)
        self.assertIn("SPX", embed.title)

        field_names = [f.name for f in embed.fields]
        self.assertIn("Call Wall", field_names)
        self.assertIn("Put Wall", field_names)
        self.assertIn("Vol Trigger", field_names)
        self.assertIn("Hedge Wall", field_names)
        self.assertIn("Abs Gamma", field_names)
        self.assertIn("Source", field_names)

    def test_source_displayed(self):
        """Source field shows the correct source."""
        levels = _sample_levels(source="playwright")
        embed = build_spotgamma_levels_embed(levels)

        source_field = next(f for f in embed.fields if f.name == "Source")
        self.assertEqual(source_field.value, "playwright")

    def test_price_formatting(self):
        """Prices are formatted with dollar signs."""
        levels = _sample_levels(call_wall=5900.0)
        embed = build_spotgamma_levels_embed(levels)

        cw_field = next(f for f in embed.fields if f.name == "Call Wall")
        self.assertIn("$", cw_field.value)
        self.assertIn("5,900", cw_field.value)


class TestSpotGammaComparisonEmbed(unittest.TestCase):
    """Tests for build_spotgamma_comparison_embed."""

    def test_agreement_levels_within_threshold(self):
        """When our levels agree with SG (within 10 pts), show AGREE."""
        sg_levels = _sample_levels(
            call_wall=5900.0, put_wall=5700.0, vol_trigger=5800.0,
        )
        gex = _sample_gex_result(
            gamma_ceiling=5895.0,  # 5 pts diff -> agree
            gamma_floor=5710.0,    # 10 pts diff -> agree
            gamma_flip=5805.0,     # 5 pts diff -> agree
        )
        embed = build_spotgamma_comparison_embed(sg_levels, gex, spot_price=5800.0)

        self.assertIsInstance(embed, discord.Embed)
        self.assertIn("3/3", embed.description)
        # Color should be green (bullish) for full agreement
        self.assertEqual(embed.color.value, 0x00FF00)

    def test_divergence_outside_threshold(self):
        """When our levels diverge (> 10 pts), show DIVERGE."""
        sg_levels = _sample_levels(
            call_wall=5900.0, put_wall=5700.0, vol_trigger=5800.0,
        )
        gex = _sample_gex_result(
            gamma_ceiling=5950.0,  # 50 pts diff -> diverge
            gamma_floor=5650.0,    # 50 pts diff -> diverge
            gamma_flip=5750.0,     # 50 pts diff -> diverge
        )
        embed = build_spotgamma_comparison_embed(sg_levels, gex, spot_price=5800.0)

        self.assertIn("0/3", embed.description)
        # Color should be red (bearish) for full divergence
        self.assertEqual(embed.color.value, 0xFF0000)

    def test_mixed_agreement(self):
        """Partial agreement (1/3) shows neutral color."""
        sg_levels = _sample_levels(
            call_wall=5900.0, put_wall=5700.0, vol_trigger=5800.0,
        )
        gex = _sample_gex_result(
            gamma_ceiling=5905.0,  # 5 pts -> agree
            gamma_floor=5650.0,    # 50 pts -> diverge
            gamma_flip=5750.0,     # 50 pts -> diverge
        )
        embed = build_spotgamma_comparison_embed(sg_levels, gex, spot_price=5800.0)

        self.assertIn("1/3", embed.description)
        self.assertEqual(embed.color.value, 0xFFFF00)

    def test_none_our_values_handled(self):
        """When our GEX has None values, embed shows N/A."""
        sg_levels = _sample_levels()
        gex = _sample_gex_result(
            gamma_ceiling=None,
            gamma_floor=None,
            gamma_flip=None,
        )
        embed = build_spotgamma_comparison_embed(sg_levels, gex, spot_price=5800.0)

        # Should not crash, and should show N/A
        self.assertIsInstance(embed, discord.Embed)
        # All three None -> 0 agreements
        self.assertIn("0/3", embed.description)

    def test_spotgamma_only_field(self):
        """Hedge Wall and Abs Gamma appear in SpotGamma Only field."""
        sg_levels = _sample_levels(hedge_wall=5850.0, abs_gamma=5800.0)
        gex = _sample_gex_result()
        embed = build_spotgamma_comparison_embed(sg_levels, gex, spot_price=5800.0)

        sg_only_field = next(
            f for f in embed.fields if f.name == "SpotGamma Only"
        )
        self.assertIn("5,850", sg_only_field.value)
        self.assertIn("5,800", sg_only_field.value)


# ---------------------------------------------------------------------------
# Cog command tests
# ---------------------------------------------------------------------------


class TestSpotGammaSet(unittest.IsolatedAsyncioTestCase):
    """Tests for /spotgamma set command."""

    async def test_set_saves_levels(self):
        """set command saves levels and returns confirmation embed."""
        store = AsyncMock()
        bot = _make_bot(spotgamma_store=store)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_set.callback(
            cog, interaction,
            call_wall=5900.0, put_wall=5700.0, vol_trigger=5800.0,
            hedge_wall=5850.0, abs_gamma=5800.0,
        )

        store.save_levels.assert_awaited_once()
        saved = store.save_levels.call_args[0][0]
        self.assertEqual(saved.call_wall, 5900.0)
        self.assertEqual(saved.put_wall, 5700.0)
        self.assertEqual(saved.source, "manual")

        # Should respond with an embed (not ephemeral error)
        call_kwargs = interaction.followup.send.call_args.kwargs
        self.assertIn("embed", call_kwargs)
        self.assertIn("Saved", call_kwargs["embed"].title)

    async def test_set_no_store(self):
        """set command gracefully handles missing store."""
        bot = _make_bot(spotgamma_store=None)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_set.callback(
            cog, interaction,
            call_wall=5900.0, put_wall=5700.0, vol_trigger=5800.0,
            hedge_wall=5850.0, abs_gamma=5800.0,
        )

        content = _get_followup_content(interaction)
        self.assertIn("not configured", content)


class TestSpotGammaShow(unittest.IsolatedAsyncioTestCase):
    """Tests for /spotgamma show command."""

    async def test_show_with_data(self):
        """show command returns embed when levels exist."""
        store = AsyncMock()
        store.get_latest_levels = AsyncMock(return_value=_sample_levels())
        bot = _make_bot(spotgamma_store=store)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_show.callback(cog, interaction)

        call_kwargs = interaction.followup.send.call_args.kwargs
        self.assertIn("embed", call_kwargs)
        self.assertIn("SpotGamma Levels", call_kwargs["embed"].title)

    async def test_show_no_data(self):
        """show command shows hint when no levels exist."""
        store = AsyncMock()
        store.get_latest_levels = AsyncMock(return_value=None)
        bot = _make_bot(spotgamma_store=store)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_show.callback(cog, interaction)

        content = _get_followup_content(interaction)
        self.assertIn("No levels set today", content)

    async def test_show_no_store(self):
        """show command gracefully handles missing store."""
        bot = _make_bot(spotgamma_store=None)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_show.callback(cog, interaction)

        content = _get_followup_content(interaction)
        self.assertIn("not configured", content)


class TestSpotGammaCompare(unittest.IsolatedAsyncioTestCase):
    """Tests for /spotgamma compare command."""

    async def test_compare_success(self):
        """compare command returns embed with agreement info."""
        store = AsyncMock()
        store.get_latest_levels = AsyncMock(return_value=_sample_levels())

        dm = AsyncMock()
        chain = MagicMock()
        chain.spot_price = 5800.0
        dm.get_chain = AsyncMock(return_value=chain)

        bot = _make_bot(spotgamma_store=store, data_manager=dm)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        mock_gex = _sample_gex_result()
        with patch(
            "src.analysis.gex.calculate_gex",
            return_value=mock_gex,
        ):
            await cog.sg_compare.callback(cog, interaction)

        call_kwargs = interaction.followup.send.call_args.kwargs
        self.assertIn("embed", call_kwargs)
        self.assertIn("GEX vs SpotGamma", call_kwargs["embed"].title)

    async def test_compare_no_sg_levels(self):
        """compare command shows error when no SG levels."""
        store = AsyncMock()
        store.get_latest_levels = AsyncMock(return_value=None)
        dm = AsyncMock()
        bot = _make_bot(spotgamma_store=store, data_manager=dm)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_compare.callback(cog, interaction)

        content = _get_followup_content(interaction)
        self.assertIn("No SpotGamma levels", content)

    async def test_compare_no_chain(self):
        """compare command shows error when options chain unavailable."""
        store = AsyncMock()
        store.get_latest_levels = AsyncMock(return_value=_sample_levels())
        dm = AsyncMock()
        dm.get_chain = AsyncMock(return_value=None)

        bot = _make_bot(spotgamma_store=store, data_manager=dm)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_compare.callback(cog, interaction)

        content = _get_followup_content(interaction)
        self.assertIn("No options chain", content)

    async def test_compare_no_store(self):
        """compare command gracefully handles missing store."""
        bot = _make_bot(spotgamma_store=None)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_compare.callback(cog, interaction)

        content = _get_followup_content(interaction)
        self.assertIn("not configured", content)


class TestSpotGammaHiro(unittest.IsolatedAsyncioTestCase):
    """Tests for /spotgamma hiro command."""

    async def test_hiro_with_data(self):
        """hiro command returns embed with HIRO data."""
        store = AsyncMock()
        store.get_latest_hiro = AsyncMock(return_value=_sample_hiro())
        bot = _make_bot(spotgamma_store=store)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_hiro.callback(cog, interaction)

        call_kwargs = interaction.followup.send.call_args.kwargs
        self.assertIn("embed", call_kwargs)
        self.assertIn("HIRO", call_kwargs["embed"].title)

    async def test_hiro_no_data(self):
        """hiro command shows message when no HIRO data."""
        store = AsyncMock()
        store.get_latest_hiro = AsyncMock(return_value=None)
        bot = _make_bot(spotgamma_store=store)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_hiro.callback(cog, interaction)

        content = _get_followup_content(interaction)
        self.assertIn("HIRO data not available", content)

    async def test_hiro_no_store(self):
        """hiro command gracefully handles missing store."""
        bot = _make_bot(spotgamma_store=None)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_hiro.callback(cog, interaction)

        content = _get_followup_content(interaction)
        self.assertIn("not configured", content)


class TestSpotGammaStatus(unittest.IsolatedAsyncioTestCase):
    """Tests for /spotgamma status command."""

    async def test_status_with_store(self):
        """status command shows full status when store is available."""
        store = AsyncMock()
        store.get_latest_levels = AsyncMock(return_value=_sample_levels())
        store.get_latest_hiro = AsyncMock(return_value=_sample_hiro())
        bot = _make_bot(spotgamma_store=store)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_status.callback(cog, interaction)

        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        self.assertIn("Status", embed.title)

        field_names = [f.name for f in embed.fields]
        self.assertIn("Enabled", field_names)
        self.assertIn("Store", field_names)
        self.assertIn("Last Levels", field_names)
        self.assertIn("Last HIRO", field_names)

    async def test_status_no_store(self):
        """status command shows store unavailable when not configured."""
        bot = _make_bot(spotgamma_store=None)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_status.callback(cog, interaction)

        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        store_field = next(f for f in embed.fields if f.name == "Store")
        self.assertIn("Not configured", store_field.value)

    async def test_status_no_data(self):
        """status command shows 'No data' when store has no records."""
        store = AsyncMock()
        store.get_latest_levels = AsyncMock(return_value=None)
        store.get_latest_hiro = AsyncMock(return_value=None)
        bot = _make_bot(spotgamma_store=store)
        cog = _make_cog(bot)
        interaction = _make_interaction(bot)

        await cog.sg_status.callback(cog, interaction)

        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        levels_field = next(f for f in embed.fields if f.name == "Last Levels")
        self.assertEqual(levels_field.value, "No data")


if __name__ == "__main__":
    unittest.main()
