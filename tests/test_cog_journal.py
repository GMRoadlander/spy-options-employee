"""Tests for the Trade Journal Cog and journal embed builders."""

import pytest
import pytest_asyncio
import aiosqlite
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from src.services import ServiceRegistry


def _attach_services(cog, bot):
    """Attach a ServiceRegistry to a cog from its mock bot's attributes."""
    attrs = {}
    for field in ("store", "strategy_manager", "signal_logger", "paper_engine",
                  "strategy_parser", "data_manager"):
        val = getattr(bot, field, None)
        if not isinstance(val, MagicMock) or val._mock_name is not None:
            attrs[field] = val
        else:
            attrs[field] = val
    bot.services = ServiceRegistry(**attrs)
    cog.services = bot.services

from src.discord_bot.embeds import (
    build_daily_summary_embed,
    build_weekly_review_embed,
    build_rating_confirmation_embed,
)


# -- Fixtures ----------------------------------------------------------------


def _make_signal_stats(total: int = 10) -> dict:
    """Create mock signal stats."""
    return {
        "total_signals": total,
        "by_type": {"gamma_flip": 3, "squeeze": 2, "flow": 5},
        "by_direction": {"bullish": 4, "bearish": 3, "neutral": 3},
        "outcome_counts": {"win": 6, "loss": 3, "scratch": 1},
    }


def _make_strategy_summary() -> list[dict]:
    """Create mock strategy summary."""
    return [
        {"id": 1, "name": "SPX IC", "status": "backtest", "created_at": "2024-01-01"},
        {"id": 2, "name": "Put Spread", "status": "defined", "created_at": "2024-01-05"},
        {"id": 3, "name": "Old Strategy", "status": "retired", "created_at": "2023-01-01"},
    ]


def _make_rating_stats(count: int = 5, avg: float = 3.8) -> dict:
    """Create mock rating stats."""
    return {"count": count, "avg_rating": avg}


# -- Daily Summary Embed Tests -----------------------------------------------


def test_build_daily_summary_embed():
    """Test daily summary embed with full data."""
    embed = build_daily_summary_embed(
        date=date(2024, 1, 15),
        signal_stats=_make_signal_stats(),
        strategy_summary=_make_strategy_summary(),
        rating_stats=_make_rating_stats(),
    )

    assert isinstance(embed, discord.Embed)
    assert "2024-01-15" in embed.title
    assert "Daily" in embed.title

    # Check signal field
    signal_fields = [f for f in embed.fields if f.name == "Signals"]
    assert len(signal_fields) == 1
    assert "10" in signal_fields[0].value

    # Check strategies field
    strat_fields = [f for f in embed.fields if "Strategies" in f.name]
    assert len(strat_fields) == 1
    assert "SPX IC" in strat_fields[0].value


def test_build_daily_summary_embed_empty():
    """Test daily summary embed with no data."""
    embed = build_daily_summary_embed(
        date=date(2024, 1, 15),
        signal_stats={"total_signals": 0, "by_type": {}, "by_direction": {}, "outcome_counts": {}},
        strategy_summary=[],
        rating_stats={"count": 0, "avg_rating": 0.0},
    )

    assert isinstance(embed, discord.Embed)
    assert "0" in str([f.value for f in embed.fields])


def test_build_daily_summary_excludes_retired():
    """Test that daily summary excludes retired strategies from active list."""
    strategies = [
        {"id": 1, "name": "Active", "status": "defined"},
        {"id": 2, "name": "Retired", "status": "retired"},
    ]

    embed = build_daily_summary_embed(
        date=date(2024, 1, 15),
        signal_stats=_make_signal_stats(0),
        strategy_summary=strategies,
        rating_stats=_make_rating_stats(0),
    )

    strat_fields = [f for f in embed.fields if "Strategies" in f.name]
    assert len(strat_fields) == 1
    assert "Active" in strat_fields[0].value
    assert "Retired" not in strat_fields[0].value


# -- Weekly Review Embed Tests ------------------------------------------------


def test_build_weekly_review_embed():
    """Test weekly review embed with full data."""
    embed = build_weekly_review_embed(
        start_date=date(2024, 1, 8),
        end_date=date(2024, 1, 15),
        signal_stats=_make_signal_stats(),
        strategy_summary=_make_strategy_summary(),
        rating_stats=_make_rating_stats(),
    )

    assert isinstance(embed, discord.Embed)
    assert "Weekly" in embed.title
    assert "2024-01-08" in embed.title
    assert "2024-01-15" in embed.title


def test_build_weekly_review_embed_empty():
    """Test weekly review embed with no data."""
    embed = build_weekly_review_embed(
        start_date=date(2024, 1, 8),
        end_date=date(2024, 1, 15),
        signal_stats={"total_signals": 0, "by_type": {}, "by_direction": {}, "outcome_counts": {}},
        strategy_summary=[],
        rating_stats={"count": 0, "avg_rating": 0.0},
    )

    assert isinstance(embed, discord.Embed)


def test_build_weekly_review_hit_rate():
    """Test that weekly review calculates hit rate correctly."""
    stats = _make_signal_stats()
    # 6 wins out of 10 outcomes = 60%
    embed = build_weekly_review_embed(
        start_date=date(2024, 1, 8),
        end_date=date(2024, 1, 15),
        signal_stats=stats,
        strategy_summary=[],
        rating_stats=_make_rating_stats(0),
    )

    signal_field = [f for f in embed.fields if "Signal" in f.name][0]
    assert "60.0%" in signal_field.value


# -- Rating Confirmation Embed Tests -----------------------------------------


def test_build_rating_confirmation_embed_high():
    """Test rating confirmation embed for high rating."""
    embed = build_rating_confirmation_embed(42, 5, "Great signal!")

    assert isinstance(embed, discord.Embed)
    assert "#42" in embed.title
    assert "5/5" in embed.description
    assert embed.color.value == 0x00FF00  # Green for 4+


def test_build_rating_confirmation_embed_medium():
    """Test rating confirmation embed for medium rating."""
    embed = build_rating_confirmation_embed(10, 3, "")

    assert "3/5" in embed.description
    assert embed.color.value == 0xFFFF00  # Yellow for 3


def test_build_rating_confirmation_embed_low():
    """Test rating confirmation embed for low rating."""
    embed = build_rating_confirmation_embed(5, 1, "Bad signal")

    assert "1/5" in embed.description
    assert embed.color.value == 0xFF0000  # Red for <=2
    # Check notes field
    notes_field = [f for f in embed.fields if f.name == "Notes"]
    assert len(notes_field) == 1
    assert "Bad signal" in notes_field[0].value


def test_build_rating_confirmation_no_notes():
    """Test rating confirmation embed without notes."""
    embed = build_rating_confirmation_embed(5, 4, "")

    notes_field = [f for f in embed.fields if f.name == "Notes"]
    assert len(notes_field) == 0


# -- Cog Tests ---------------------------------------------------------------


def test_journal_cog_class_exists():
    """Test that JournalCog class exists and has expected methods."""
    from src.discord_bot.cog_journal import JournalCog

    assert hasattr(JournalCog, "journal_daily")
    assert hasattr(JournalCog, "journal_weekly")
    assert hasattr(JournalCog, "journal_rate")
    assert hasattr(JournalCog, "journal_note")
    assert hasattr(JournalCog, "auto_daily_summary")
    assert hasattr(JournalCog, "auto_weekly_review")


def test_journal_cog_has_setup_function():
    """Test that the cog module has a setup function."""
    from src.discord_bot import cog_journal
    assert hasattr(cog_journal, "setup")
    assert callable(cog_journal.setup)


# -- Functional Cog Tests (W15) -----------------------------------------------


def _make_interaction() -> MagicMock:
    """Create a mock Discord Interaction."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.__str__ = MagicMock(return_value="Borey#0001")
    return interaction


def _make_mock_store_with_db():
    """Create a mock store with a mock DB connection."""
    db = AsyncMock()
    store = MagicMock()
    store._ensure_connected = MagicMock(return_value=db)
    return store, db


@pytest.mark.asyncio
async def test_journal_note_saves():
    """journal_note saves the note to the database and responds with embed."""
    from src.discord_bot.cog_journal import JournalCog

    store, db = _make_mock_store_with_db()

    bot = MagicMock()
    bot.store = store
    bot.services = ServiceRegistry(store=store)
    # Prevent background tasks from starting
    cog = JournalCog.__new__(JournalCog)
    cog.bot = bot
    cog.services = bot.services

    interaction = _make_interaction()
    await cog.journal_note.callback(cog, interaction, content="Market looks bullish today")

    # Verify DB write
    db.execute.assert_awaited()
    db.commit.assert_awaited()

    # Verify embed response
    interaction.followup.send.assert_awaited_once()
    sent = interaction.followup.send.call_args.kwargs
    assert "embed" in sent
    assert "Journal Note Saved" in sent["embed"].title


@pytest.mark.asyncio
async def test_journal_rate_validates_range():
    """journal_rate rejects ratings outside 1-5 range."""
    from src.discord_bot.cog_journal import JournalCog

    bot = MagicMock()
    bot.services = ServiceRegistry()
    cog = JournalCog.__new__(JournalCog)
    cog.bot = bot
    cog.services = bot.services

    interaction = _make_interaction()
    await cog.journal_rate.callback(cog, interaction, signal_id=1, rating=7, notes="")

    interaction.followup.send.assert_awaited_once()
    call_args = interaction.followup.send.call_args
    msg = call_args.kwargs.get("content", call_args.args[0] if call_args.args else "")
    assert "between 1 and 5" in msg.lower()


@pytest.mark.asyncio
async def test_journal_rate_no_store():
    """journal_rate sends error when store is not available."""
    from src.discord_bot.cog_journal import JournalCog

    bot = MagicMock()
    bot.store = None
    bot.services = ServiceRegistry(store=None)
    cog = JournalCog.__new__(JournalCog)
    cog.bot = bot
    cog.services = bot.services

    interaction = _make_interaction()
    await cog.journal_rate.callback(cog, interaction, signal_id=1, rating=4, notes="")

    interaction.followup.send.assert_awaited_once()
    call_args = interaction.followup.send.call_args
    msg = call_args.kwargs.get("content", call_args.args[0] if call_args.args else "")
    assert "not available" in msg.lower()


# -- Step 7: Paper Trading Channel Auto-Post Tests ----------------------------


def _make_cog_with_bot(**bot_attrs):
    """Create a JournalCog instance bypassing __init__ with a mock bot."""
    from src.discord_bot.cog_journal import JournalCog
    from src.services import ServiceRegistry

    cog = JournalCog.__new__(JournalCog)
    bot = MagicMock()
    for k, v in bot_attrs.items():
        setattr(bot, k, v)
    bot.services = ServiceRegistry(**bot_attrs)
    cog.bot = bot
    cog.services = bot.services
    return cog


@pytest.mark.asyncio
async def test_auto_paper_daily_skips_weekends():
    """auto_paper_daily returns early on weekends without posting."""
    from src.discord_bot import cog_journal

    cog = _make_cog_with_bot()

    # Saturday
    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 21, 16, 15)  # Saturday
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        # weekday() == 5 -> Saturday
        assert mock_now.return_value.weekday() == 5

        await cog.auto_paper_daily.coro(cog)

    # No channel lookup should have happened
    cog.bot.get_channel.assert_not_called()


@pytest.mark.asyncio
async def test_auto_paper_daily_skips_without_channel():
    """auto_paper_daily returns early when no paper channel is configured."""
    from src.discord_bot import cog_journal

    cog = _make_cog_with_bot()
    cog.bot.get_channel.return_value = None

    # Weekday -- paper_channel_id defaults to 0, so _get_paper_channel returns None
    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 15)  # Monday
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        assert mock_now.return_value.weekday() == 0

        await cog.auto_paper_daily.coro(cog)

    # Bot should not have attempted to send anything
    # _get_paper_channel returns None because config.paper_channel_id == 0


@pytest.mark.asyncio
async def test_auto_paper_daily_skips_without_paper_engine():
    """auto_paper_daily returns early when paper engine is not available."""
    from src.discord_bot import cog_journal

    # Set up a channel but no paper engine
    channel = AsyncMock(spec=discord.TextChannel)
    cog = _make_cog_with_bot(paper_engine=None, strategy_manager=MagicMock(), store=MagicMock())
    cog._get_paper_channel = MagicMock(return_value=channel)

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 15)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        await cog.auto_paper_daily.coro(cog)

    # Channel.send should NOT have been called
    channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_auto_paper_daily_posts_embeds():
    """auto_paper_daily posts daily report embeds to the paper channel."""
    from src.discord_bot import cog_journal

    channel = AsyncMock(spec=discord.TextChannel)

    mock_reporter = AsyncMock()
    embed = discord.Embed(title="Paper Trading Daily Summary")
    mock_reporter.daily_report.return_value = ([embed], [])
    mock_reporter.check_degradation.return_value = []

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
    )
    cog._get_paper_channel = MagicMock(return_value=channel)
    cog._get_paper_reporter = MagicMock(return_value=mock_reporter)

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 15)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        await cog.auto_paper_daily.coro(cog)

    # Verify channel.send was called with embeds
    channel.send.assert_awaited_once()
    call_kwargs = channel.send.call_args.kwargs
    assert "embeds" in call_kwargs
    assert len(call_kwargs["embeds"]) == 1
    assert call_kwargs["embeds"][0].title == "Paper Trading Daily Summary"


@pytest.mark.asyncio
async def test_auto_paper_daily_includes_degradation_alerts():
    """auto_paper_daily appends degradation alerts to the embeds."""
    from src.discord_bot import cog_journal

    channel = AsyncMock(spec=discord.TextChannel)

    mock_reporter = AsyncMock()
    daily_embed = discord.Embed(title="Paper Trading Daily Summary")
    alert_embed = discord.Embed(title="ALERT: Performance Degradation")
    mock_reporter.daily_report.return_value = ([daily_embed], [])
    mock_reporter.check_degradation.return_value = [alert_embed]

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
    )
    cog._get_paper_channel = MagicMock(return_value=channel)
    cog._get_paper_reporter = MagicMock(return_value=mock_reporter)

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 15)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        await cog.auto_paper_daily.coro(cog)

    channel.send.assert_awaited_once()
    call_kwargs = channel.send.call_args.kwargs
    assert len(call_kwargs["embeds"]) == 2
    assert "Degradation" in call_kwargs["embeds"][1].title


@pytest.mark.asyncio
async def test_auto_paper_daily_error_handling():
    """auto_paper_daily handles reporter errors without crashing."""
    from src.discord_bot import cog_journal

    channel = AsyncMock(spec=discord.TextChannel)

    mock_reporter = AsyncMock()
    mock_reporter.daily_report.side_effect = RuntimeError("DB connection lost")

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
    )
    cog._get_paper_channel = MagicMock(return_value=channel)
    cog._get_paper_reporter = MagicMock(return_value=mock_reporter)

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 15)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        # Should not raise
        await cog.auto_paper_daily.coro(cog)

    # Channel.send should NOT have been called since daily_report raised
    channel.send.assert_not_called()


# -- Step 4: Paper Reporting Integration Tests --------------------------------


@pytest.mark.asyncio
async def test_build_daily_embed_returns_embeds_and_files_tuple():
    """_build_daily_embed returns (list[Embed], list[File]) tuple with paper section."""
    from src.discord_bot import cog_journal

    mock_reporter = AsyncMock()
    paper_embed = discord.Embed(title="Paper Trading Daily Summary")
    paper_file = MagicMock(spec=discord.File)
    mock_reporter.daily_report.return_value = ([paper_embed], [paper_file])

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
        signal_logger=None,
    )
    cog._get_paper_reporter = MagicMock(return_value=mock_reporter)

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 30)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        embeds, files = await cog._build_daily_embed()

    assert isinstance(embeds, list)
    assert isinstance(files, list)
    # At least the main embed + paper embed
    assert len(embeds) >= 2
    assert len(files) == 1
    # First embed is the main daily summary
    assert "Daily" in embeds[0].title
    # Second embed is paper trading section
    assert embeds[1].title == "Paper Trading Daily Summary"


@pytest.mark.asyncio
async def test_build_daily_embed_without_paper_engine():
    """_build_daily_embed returns single embed when paper engine is not available."""
    from src.discord_bot import cog_journal

    cog = _make_cog_with_bot(
        paper_engine=None,
        strategy_manager=None,
        store=None,
        signal_logger=None,
    )

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 30)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        embeds, files = await cog._build_daily_embed()

    assert isinstance(embeds, list)
    assert isinstance(files, list)
    assert len(embeds) == 1  # Only the main embed
    assert len(files) == 0
    assert "Daily" in embeds[0].title


@pytest.mark.asyncio
async def test_build_daily_embed_paper_error_graceful():
    """_build_daily_embed still returns main embed if paper reporter raises."""
    from src.discord_bot import cog_journal

    mock_reporter = AsyncMock()
    mock_reporter.daily_report.side_effect = RuntimeError("Paper engine broken")

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
        signal_logger=None,
    )
    cog._get_paper_reporter = MagicMock(return_value=mock_reporter)

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 30)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        embeds, files = await cog._build_daily_embed()

    # Main embed should still be there
    assert len(embeds) == 1
    assert "Daily" in embeds[0].title
    assert len(files) == 0


@pytest.mark.asyncio
async def test_build_weekly_embed_returns_embeds_and_files_tuple():
    """_build_weekly_embed returns (list[Embed], list[File]) tuple with paper section."""
    from src.discord_bot import cog_journal

    mock_reporter = AsyncMock()
    paper_embed1 = discord.Embed(title="Paper Portfolio Weekly Review")
    paper_embed2 = discord.Embed(title="Strategy Comparison & Promotion Readiness")
    paper_file = MagicMock(spec=discord.File)
    mock_reporter.weekly_report.return_value = (
        [paper_embed1, paper_embed2],
        [paper_file],
    )

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
        signal_logger=None,
    )
    cog._get_paper_reporter = MagicMock(return_value=mock_reporter)

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 10, 0)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        embeds, files = await cog._build_weekly_embed()

    assert isinstance(embeds, list)
    assert isinstance(files, list)
    # Main embed + 2 paper embeds
    assert len(embeds) >= 3
    assert len(files) == 1
    assert "Weekly" in embeds[0].title


@pytest.mark.asyncio
async def test_build_weekly_embed_without_paper_engine():
    """_build_weekly_embed returns single embed when paper engine is not available."""
    from src.discord_bot import cog_journal

    cog = _make_cog_with_bot(
        paper_engine=None,
        strategy_manager=None,
        store=None,
        signal_logger=None,
    )

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 10, 0)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        embeds, files = await cog._build_weekly_embed()

    assert len(embeds) == 1
    assert len(files) == 0
    assert "Weekly" in embeds[0].title


@pytest.mark.asyncio
async def test_auto_daily_sends_embeds_and_files():
    """auto_daily_summary sends embeds and files when paper section has charts."""
    from src.discord_bot import cog_journal

    channel = AsyncMock(spec=discord.TextChannel)

    main_embed = discord.Embed(title="Daily Summary -- 2026-02-23")
    paper_embed = discord.Embed(title="Paper Trading Daily Summary")
    paper_file = MagicMock(spec=discord.File)

    mock_reporter = AsyncMock()
    mock_reporter.daily_report.return_value = ([paper_embed], [paper_file])

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
        signal_logger=None,
    )
    cog._get_journal_channel = MagicMock(return_value=channel)
    cog._get_paper_reporter = MagicMock(return_value=mock_reporter)
    cog._save_journal_entry = AsyncMock()

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 30)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        await cog.auto_daily_summary.coro(cog)

    channel.send.assert_awaited_once()
    call_kwargs = channel.send.call_args.kwargs
    assert "embeds" in call_kwargs
    assert "files" in call_kwargs
    assert len(call_kwargs["files"]) == 1


@pytest.mark.asyncio
async def test_auto_daily_no_files_sends_embeds_only():
    """auto_daily_summary sends only embeds when no chart files."""
    from src.discord_bot import cog_journal

    channel = AsyncMock(spec=discord.TextChannel)

    cog = _make_cog_with_bot(
        paper_engine=None,
        strategy_manager=None,
        store=None,
        signal_logger=None,
    )
    cog._get_journal_channel = MagicMock(return_value=channel)
    cog._save_journal_entry = AsyncMock()

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 30)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        await cog.auto_daily_summary.coro(cog)

    channel.send.assert_awaited_once()
    call_kwargs = channel.send.call_args.kwargs
    assert "embeds" in call_kwargs
    assert "files" not in call_kwargs


@pytest.mark.asyncio
async def test_auto_weekly_sends_embeds_and_files():
    """auto_weekly_review sends embeds and files when paper section has charts."""
    from src.discord_bot import cog_journal

    channel = AsyncMock(spec=discord.TextChannel)

    paper_embed = discord.Embed(title="Paper Portfolio Weekly Review")
    paper_file = MagicMock(spec=discord.File)

    mock_reporter = AsyncMock()
    mock_reporter.weekly_report.return_value = ([paper_embed], [paper_file])

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
        signal_logger=None,
    )
    cog._get_journal_channel = MagicMock(return_value=channel)
    cog._get_paper_reporter = MagicMock(return_value=mock_reporter)
    cog._save_journal_entry = AsyncMock()

    with patch.object(cog_journal, "_now_et") as mock_now:
        # Monday = weekday 0
        mock_now.return_value = datetime(2026, 2, 23, 10, 0)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        assert mock_now.return_value.weekday() == 0
        await cog.auto_weekly_review.coro(cog)

    channel.send.assert_awaited_once()
    call_kwargs = channel.send.call_args.kwargs
    assert "embeds" in call_kwargs
    assert "files" in call_kwargs


@pytest.mark.asyncio
async def test_auto_monthly_runs_on_first_of_month():
    """auto_monthly_report posts on the 1st of the month (weekday)."""
    from src.discord_bot import cog_journal

    channel = AsyncMock(spec=discord.TextChannel)

    mock_strategy_reporter = AsyncMock()
    mock_strategy_reporter.monthly_report.return_value = [
        discord.Embed(title="Monthly Report -- January 2026"),
    ]

    mock_paper_reporter = AsyncMock()
    mock_paper_reporter.monthly_report.return_value = (
        [discord.Embed(title="Paper Monthly Report")],
        [],
    )

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
    )
    cog._get_journal_channel = MagicMock(return_value=channel)
    cog._get_strategy_reporter = MagicMock(return_value=mock_strategy_reporter)
    cog._get_paper_reporter = MagicMock(return_value=mock_paper_reporter)
    cog._save_journal_entry = AsyncMock()

    with patch.object(cog_journal, "_now_et") as mock_now:
        # Feb 2, 2026 is a Monday (weekday 0), but day=2 so should skip
        # Dec 1, 2025 is a Monday (weekday 0), day=1 so should run
        mock_now.return_value = datetime(2025, 12, 1, 10, 0)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        assert mock_now.return_value.day == 1
        assert mock_now.return_value.weekday() == 0  # Monday
        await cog.auto_monthly_report.coro(cog)

    channel.send.assert_awaited()
    # Should have sent embeds
    call_kwargs = channel.send.call_args.kwargs
    assert "embeds" in call_kwargs


@pytest.mark.asyncio
async def test_auto_monthly_skips_non_first_day():
    """auto_monthly_report skips on days other than the 1st."""
    from src.discord_bot import cog_journal

    channel = AsyncMock(spec=discord.TextChannel)

    cog = _make_cog_with_bot()
    cog._get_journal_channel = MagicMock(return_value=channel)

    with patch.object(cog_journal, "_now_et") as mock_now:
        # Feb 23, 2026 = Monday, day=23
        mock_now.return_value = datetime(2026, 2, 23, 10, 0)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        assert mock_now.return_value.day == 23
        await cog.auto_monthly_report.coro(cog)

    channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_auto_monthly_skips_weekends():
    """auto_monthly_report skips if the 1st falls on a weekend."""
    from src.discord_bot import cog_journal

    channel = AsyncMock(spec=discord.TextChannel)

    cog = _make_cog_with_bot()
    cog._get_journal_channel = MagicMock(return_value=channel)

    with patch.object(cog_journal, "_now_et") as mock_now:
        # Nov 1, 2025 is a Saturday (weekday 5)
        mock_now.return_value = datetime(2025, 11, 1, 10, 0)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        assert mock_now.return_value.day == 1
        assert mock_now.return_value.weekday() == 5  # Saturday
        await cog.auto_monthly_report.coro(cog)

    channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_auto_monthly_splits_over_10_embeds():
    """auto_monthly_report splits embeds into batches of 10 for Discord limits."""
    from src.discord_bot import cog_journal

    channel = AsyncMock(spec=discord.TextChannel)

    # Create 12 embeds from strategy reporter
    bt_embeds = [discord.Embed(title=f"BT Embed {i}") for i in range(8)]
    mock_strategy_reporter = AsyncMock()
    mock_strategy_reporter.monthly_report.return_value = bt_embeds

    # Create 5 embeds from paper reporter
    paper_embeds = [discord.Embed(title=f"Paper Embed {i}") for i in range(5)]
    mock_paper_reporter = AsyncMock()
    mock_paper_reporter.monthly_report.return_value = (paper_embeds, [])

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
    )
    cog._get_journal_channel = MagicMock(return_value=channel)
    cog._get_strategy_reporter = MagicMock(return_value=mock_strategy_reporter)
    cog._get_paper_reporter = MagicMock(return_value=mock_paper_reporter)
    cog._save_journal_entry = AsyncMock()

    with patch.object(cog_journal, "_now_et") as mock_now:
        # Dec 1, 2025 is Monday, day=1
        mock_now.return_value = datetime(2025, 12, 1, 10, 0)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        await cog.auto_monthly_report.coro(cog)

    # Total 13 embeds = should be sent in 2 batches (10 + 3)
    assert channel.send.await_count == 2
    first_call = channel.send.call_args_list[0].kwargs
    second_call = channel.send.call_args_list[1].kwargs
    assert len(first_call["embeds"]) == 10
    assert len(second_call["embeds"]) == 3


@pytest.mark.asyncio
async def test_journal_daily_command_returns_paper_section():
    """journal_daily slash command sends embeds including paper section."""
    from src.discord_bot import cog_journal

    mock_reporter = AsyncMock()
    paper_embed = discord.Embed(title="Paper Trading Daily Summary")
    mock_reporter.daily_report.return_value = ([paper_embed], [])

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
        signal_logger=None,
    )
    cog._get_paper_reporter = MagicMock(return_value=mock_reporter)
    cog._save_journal_entry = AsyncMock()

    interaction = _make_interaction()

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 16, 30)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        await cog.journal_daily.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    call_kwargs = interaction.followup.send.call_args.kwargs
    assert "embeds" in call_kwargs
    assert len(call_kwargs["embeds"]) >= 2  # main + paper
    titles = [e.title for e in call_kwargs["embeds"]]
    assert any("Paper" in t for t in titles)


@pytest.mark.asyncio
async def test_journal_weekly_command_returns_paper_section():
    """journal_weekly slash command sends embeds including paper section."""
    from src.discord_bot import cog_journal

    mock_reporter = AsyncMock()
    paper_embed = discord.Embed(title="Paper Portfolio Weekly Review")
    mock_reporter.weekly_report.return_value = ([paper_embed], [])

    cog = _make_cog_with_bot(
        paper_engine=MagicMock(),
        strategy_manager=MagicMock(),
        store=MagicMock(),
        signal_logger=None,
    )
    cog._get_paper_reporter = MagicMock(return_value=mock_reporter)
    cog._save_journal_entry = AsyncMock()

    interaction = _make_interaction()

    with patch.object(cog_journal, "_now_et") as mock_now:
        mock_now.return_value = datetime(2026, 2, 23, 10, 0)
        mock_now.return_value = mock_now.return_value.replace(
            tzinfo=cog_journal.ET,
        )
        await cog.journal_weekly.callback(cog, interaction)

    interaction.followup.send.assert_awaited_once()
    call_kwargs = interaction.followup.send.call_args.kwargs
    assert "embeds" in call_kwargs
    assert len(call_kwargs["embeds"]) >= 2  # main + paper
    titles = [e.title for e in call_kwargs["embeds"]]
    assert any("Paper" in t for t in titles)


def test_get_paper_reporter_returns_none_without_engine():
    """_get_paper_reporter returns None when paper_engine is not on bot."""
    from src.discord_bot.cog_journal import JournalCog

    cog = JournalCog.__new__(JournalCog)
    bot = MagicMock()
    bot.paper_engine = None
    bot.strategy_manager = MagicMock()
    bot.store = MagicMock()
    bot.services = ServiceRegistry(paper_engine=None, strategy_manager=bot.strategy_manager, store=bot.store)
    cog.bot = bot
    cog.services = bot.services

    result = cog._get_paper_reporter()
    assert result is None


def test_get_paper_reporter_returns_reporter_with_engine():
    """_get_paper_reporter returns PaperPerformanceReporter when all deps available."""
    from src.discord_bot.cog_journal import JournalCog

    cog = JournalCog.__new__(JournalCog)
    bot = MagicMock()
    bot.paper_engine = MagicMock()
    bot.strategy_manager = MagicMock()
    bot.store = MagicMock()
    bot.services = ServiceRegistry(paper_engine=bot.paper_engine, strategy_manager=bot.strategy_manager, store=bot.store)
    cog.bot = bot
    cog.services = bot.services

    result = cog._get_paper_reporter()
    assert result is not None
    from src.discord_bot.paper_reporting import PaperPerformanceReporter
    assert isinstance(result, PaperPerformanceReporter)
