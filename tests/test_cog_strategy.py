"""Tests for the Strategy Management Cog and embed builders."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from src.services import ServiceRegistry


def _make_strategy_bot(**attrs) -> MagicMock:
    """Create a mock bot with ServiceRegistry for StrategyCog tests."""
    bot = MagicMock()
    for k, v in attrs.items():
        setattr(bot, k, v)
    bot.services = ServiceRegistry(**attrs)
    return bot

from src.discord_bot.embeds import (
    build_strategy_define_embed,
    build_strategy_list_embed,
    build_strategy_detail_embed,
    build_backtest_result_embed,
    build_backtest_progress_embed,
)
from src.strategy.schema import (
    EntryRule,
    ExitRule,
    LegAction,
    LegDefinition,
    LegSide,
    ScheduleConfig,
    SizingConfig,
    StrategyTemplate,
    StrategyType,
    StructureDefinition,
)
from src.strategy.lifecycle import StrategyStatus


# -- Fixtures ----------------------------------------------------------------


def _make_iron_condor_template() -> StrategyTemplate:
    """Create a sample iron condor template for testing."""
    return StrategyTemplate(
        name="SPX Iron Condor",
        description="Sell iron condors on SPX",
        ticker="SPX",
        structure=StructureDefinition(
            strategy_type=StrategyType.IRON_CONDOR,
            legs=[
                LegDefinition(name="short_put", side=LegSide.PUT, action=LegAction.SELL, delta_value=0.16),
                LegDefinition(name="long_put", side=LegSide.PUT, action=LegAction.BUY, delta_value=0.05),
                LegDefinition(name="short_call", side=LegSide.CALL, action=LegAction.SELL, delta_value=0.16),
                LegDefinition(name="long_call", side=LegSide.CALL, action=LegAction.BUY, delta_value=0.05),
            ],
            dte_target=37,
            dte_min=30,
            dte_max=45,
        ),
        entry=EntryRule(iv_rank_min=30.0),
        exit=ExitRule(profit_target_pct=0.50, stop_loss_pct=2.0),
    )


def _make_strategy_dict(
    id: int = 1,
    name: str = "SPX Iron Condor",
    status: str = "defined",
    template_yaml: str = "name: SPX IC\n",
) -> dict:
    """Create a mock strategy dict as returned by StrategyManager."""
    return {
        "id": id,
        "name": name,
        "status": status,
        "template_yaml": template_yaml,
        "metadata": {},
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-01-15T12:00:00",
    }


def _make_backtest_result_dict() -> dict:
    """Create a mock backtest result dict."""
    return {
        "id": 1,
        "strategy_id": "1",
        "run_at": "2024-01-15T14:00:00",
        "start_date": "2019-01-01",
        "end_date": "2024-01-01",
        "num_trades": 250,
        "sharpe": 1.45,
        "sortino": 2.10,
        "max_drawdown": -5200.0,
        "win_rate": 0.72,
        "profit_factor": 2.1,
        "wfa_passed": 1,
        "cpcv_pbo": 0.32,
        "cpcv_passed": 1,
        "dsr": 0.97,
        "dsr_passed": 1,
        "mc_5th_sharpe": 0.85,
        "mc_passed": 1,
        "all_passed": 1,
        "recommendation": "PROMOTE",
        "full_result": "{}",
    }


# -- Embed Builder Tests -----------------------------------------------------


def test_build_strategy_define_embed():
    """Test that strategy define embed has correct structure."""
    template = _make_iron_condor_template()
    embed = build_strategy_define_embed(template, "Parsed iron condor successfully.", 42)

    assert isinstance(embed, discord.Embed)
    assert "SPX Iron Condor" in embed.title
    assert "#42" in embed.title
    assert "Parsed iron condor" in embed.description
    assert len(embed.fields) >= 3  # Structure, Entry, Exit, Ticker


def test_build_strategy_define_embed_no_id():
    """Test define embed without strategy ID."""
    template = _make_iron_condor_template()
    embed = build_strategy_define_embed(template, "Test", None)

    assert isinstance(embed, discord.Embed)
    assert "#" not in embed.title


def test_build_strategy_list_embed_with_strategies():
    """Test strategy list embed with multiple strategies."""
    strategies = [
        _make_strategy_dict(1, "IC Strategy", "defined"),
        _make_strategy_dict(2, "Put Spread", "backtest"),
        _make_strategy_dict(3, "Retired One", "retired"),
    ]
    embed = build_strategy_list_embed(strategies, None)

    assert isinstance(embed, discord.Embed)
    assert "3 strategies found" in embed.description
    assert len(embed.fields) == 3


def test_build_strategy_list_embed_empty():
    """Test strategy list embed with no strategies."""
    embed = build_strategy_list_embed([], None)

    assert isinstance(embed, discord.Embed)
    assert "0 strategies found" in embed.description
    assert any("None" in f.name for f in embed.fields)


def test_build_strategy_list_embed_with_filter():
    """Test strategy list embed with status filter."""
    strategies = [_make_strategy_dict(1, "IC", "defined")]
    embed = build_strategy_list_embed(strategies, StrategyStatus.DEFINED)

    assert "defined" in embed.title.lower()


def test_build_strategy_detail_embed():
    """Test strategy detail embed with full info."""
    strategy = _make_strategy_dict()
    strategy["template_yaml"] = "name: SPX IC\nticker: SPX\n"
    history = [
        {
            "from_status": "idea",
            "to_status": "defined",
            "reason": "Template complete",
            "transitioned_at": "2024-01-15T11:00:00",
        }
    ]

    embed = build_strategy_detail_embed(strategy, history)

    assert isinstance(embed, discord.Embed)
    assert "SPX Iron Condor" in embed.title
    assert any("History" in f.name for f in embed.fields)
    assert any("Template" in f.name for f in embed.fields)


def test_build_strategy_detail_embed_no_yaml():
    """Test detail embed when strategy has no YAML."""
    strategy = _make_strategy_dict()
    strategy["template_yaml"] = ""

    embed = build_strategy_detail_embed(strategy, [])

    assert isinstance(embed, discord.Embed)
    # Should not have Template YAML field
    assert not any("Template" in f.name for f in embed.fields)


def test_build_backtest_result_embed_promote():
    """Test backtest result embed with PROMOTE recommendation."""
    result = _make_backtest_result_dict()
    embed = build_backtest_result_embed(result, "SPX IC")

    assert isinstance(embed, discord.Embed)
    assert "PROMOTE" in embed.description
    assert embed.color.value == 0x00FF00  # Green
    assert any("Gates" in f.name for f in embed.fields)
    assert any("Sharpe" in f.name for f in embed.fields)


def test_build_backtest_result_embed_refine():
    """Test backtest result embed with REFINE recommendation."""
    result = _make_backtest_result_dict()
    result["recommendation"] = "REFINE"
    result["all_passed"] = 0
    result["wfa_passed"] = 0

    embed = build_backtest_result_embed(result, "SPX IC")

    assert "REFINE" in embed.description
    assert embed.color.value == 0xFFFF00  # Yellow


def test_build_backtest_result_embed_reject():
    """Test backtest result embed with REJECT recommendation."""
    result = _make_backtest_result_dict()
    result["recommendation"] = "REJECT"
    result["all_passed"] = 0

    embed = build_backtest_result_embed(result, "SPX IC")

    assert "REJECT" in embed.description
    assert embed.color.value == 0xFF0000  # Red


def test_build_backtest_progress_embed():
    """Test backtest progress embed."""
    embed = build_backtest_progress_embed("My Strategy", "Running WFA gate 2/4...")

    assert isinstance(embed, discord.Embed)
    assert "My Strategy" in embed.title
    assert "WFA" in embed.description


# -- Cog Registration Tests --------------------------------------------------


def test_cog_class_exists():
    """Test that StrategyCog class exists and has expected methods."""
    from src.discord_bot.cog_strategy import StrategyCog

    assert hasattr(StrategyCog, "strategy_define")
    assert hasattr(StrategyCog, "strategy_list")
    assert hasattr(StrategyCog, "strategy_show")
    assert hasattr(StrategyCog, "strategy_edit")
    assert hasattr(StrategyCog, "strategy_retire")
    assert hasattr(StrategyCog, "backtest")
    assert hasattr(StrategyCog, "backtest_results")


def test_cog_has_setup_function():
    """Test that the cog module has a setup function."""
    from src.discord_bot import cog_strategy
    assert hasattr(cog_strategy, "setup")
    assert callable(cog_strategy.setup)


# -- Functional Cog Tests (W15) -----------------------------------------------


def _make_interaction(*, manage_guild: bool = True) -> MagicMock:
    """Create a mock Discord Interaction with followup support."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.__str__ = MagicMock(return_value="TestUser#1234")
    perms = MagicMock()
    perms.manage_guild = manage_guild
    interaction.permissions = perms
    interaction.guild = MagicMock()
    return interaction


@pytest.mark.asyncio
async def test_strategy_define_no_parser():
    """strategy_define sends error when parser is not attached to bot."""
    from src.discord_bot.cog_strategy import StrategyCog

    bot = _make_strategy_bot(strategy_parser=None)
    cog = StrategyCog(bot)

    interaction = _make_interaction()
    await cog.strategy_define.callback(cog, interaction, description="sell iron condors")

    interaction.followup.send.assert_awaited_once()
    msg = interaction.followup.send.call_args
    assert "not available" in msg.kwargs.get("content", msg.args[0] if msg.args else "").lower() or \
           "not available" in str(msg).lower()


@pytest.mark.asyncio
async def test_strategy_list_empty():
    """strategy_list returns embed with 0 strategies when DB is empty."""
    from src.discord_bot.cog_strategy import StrategyCog

    sm = AsyncMock()
    sm.list_strategies = AsyncMock(return_value=[])
    bot = _make_strategy_bot(strategy_manager=sm)
    cog = StrategyCog(bot)

    interaction = _make_interaction()
    await cog.strategy_list.callback(cog, interaction, status=None)

    interaction.followup.send.assert_awaited_once()
    sent_kwargs = interaction.followup.send.call_args.kwargs
    embed = sent_kwargs.get("embed")
    assert embed is not None
    assert "0 strategies found" in embed.description


@pytest.mark.asyncio
async def test_strategy_show_not_found():
    """strategy_show sends 'not found' when strategy doesn't exist."""
    from src.discord_bot.cog_strategy import StrategyCog

    sm = AsyncMock()
    sm.get = AsyncMock(return_value=None)
    sm.list_strategies = AsyncMock(return_value=[])
    bot = _make_strategy_bot(strategy_manager=sm)
    cog = StrategyCog(bot)

    interaction = _make_interaction()
    await cog.strategy_show.callback(cog, interaction, name="nonexistent")

    interaction.followup.send.assert_awaited_once()
    call_args = interaction.followup.send.call_args
    msg = call_args.kwargs.get("content", call_args.args[0] if call_args.args else "")
    assert "not found" in msg.lower()


@pytest.mark.asyncio
async def test_strategy_edit_template_error_no_leak():
    """strategy_edit does not leak exception details when template load fails."""
    from src.discord_bot.cog_strategy import StrategyCog

    sp = MagicMock()
    sm = AsyncMock()
    sm.get = AsyncMock(return_value=_make_strategy_dict(
        1, "My IC", "defined", template_yaml="invalid: [yaml: {{broken"
    ))
    sm.list_strategies = AsyncMock(return_value=[])
    bot = _make_strategy_bot(strategy_parser=sp, strategy_manager=sm)
    cog = StrategyCog(bot)

    interaction = _make_interaction()

    with patch("yaml.safe_load", side_effect=Exception("YAML parse error: unexpected token at line 1")):
        await cog.strategy_edit.callback(cog, interaction, name="1", changes="widen wings")

    interaction.followup.send.assert_awaited_once()
    call_args = interaction.followup.send.call_args
    msg = call_args.kwargs.get("content", call_args.args[0] if call_args.args else "")
    # Must NOT contain the raw exception text
    assert "YAML parse error" not in msg
    assert "unexpected token" not in msg
    # Must contain a generic message
    assert "failed" in msg.lower() or "check" in msg.lower()


@pytest.mark.asyncio
async def test_backtest_template_error_no_leak():
    """backtest does not leak exception details when template load fails."""
    from src.discord_bot.cog_strategy import StrategyCog

    sm = AsyncMock()
    sm.get = AsyncMock(return_value=_make_strategy_dict(
        1, "My IC", "defined", template_yaml="some: yaml"
    ))
    sm.list_strategies = AsyncMock(return_value=[])
    sm.transition = AsyncMock()
    bot = _make_strategy_bot(strategy_manager=sm)
    cog = StrategyCog(bot)

    interaction = _make_interaction()
    interaction.channel = AsyncMock()

    with patch("yaml.safe_load", side_effect=Exception("sensitive DB path /var/lib/data.db")):
        await cog.backtest.callback(cog, interaction, name="1", years=5)

    # Find the ephemeral followup send (the one with error)
    calls = interaction.followup.send.call_args_list
    error_msg_found = False
    for call in calls:
        msg = call.kwargs.get("content", call.args[0] if call.args else "")
        if "sensitive" in msg or "/var/lib" in msg:
            error_msg_found = True
    assert not error_msg_found, "Raw exception leaked to Discord"


@pytest.mark.asyncio
async def test_strategy_retire_success():
    """strategy_retire transitions strategy and sends confirmation."""
    from src.discord_bot.cog_strategy import StrategyCog

    sm = AsyncMock()
    sm.get = AsyncMock(return_value=_make_strategy_dict(1, "My IC", "defined"))
    sm.list_strategies = AsyncMock(return_value=[])
    sm.transition = AsyncMock()
    bot = _make_strategy_bot(strategy_manager=sm)
    cog = StrategyCog(bot)

    interaction = _make_interaction(manage_guild=True)
    await cog.strategy_retire.callback(cog, interaction, name="1")

    bot.strategy_manager.transition.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()
    msg = str(interaction.followup.send.call_args)
    assert "retired" in msg.lower()
