"""Tests for the Trade Journal Cog and journal embed builders."""

import pytest
import pytest_asyncio
import aiosqlite
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord

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
