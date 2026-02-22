"""Tests for CheddarFlow embed parser.

Validates embed parsing, SPX/SPY filtering, premium threshold filtering,
and resilience to malformed/changed embed formats.
"""

from unittest.mock import MagicMock

import pytest

from src.discord_bot.cog_cheddarflow import parse_cheddarflow_embed


# ---------------------------------------------------------------------------
# Helper: build synthetic Discord embeds
# ---------------------------------------------------------------------------


def make_embed(
    title: str = "",
    description: str = "",
    fields: list[tuple[str, str]] | None = None,
) -> MagicMock:
    """Create a mock discord.Embed with the given attributes.

    Args:
        title: Embed title.
        description: Embed description.
        fields: List of (name, value) tuples for embed fields.

    Returns:
        Mock object mimicking discord.Embed.
    """
    embed = MagicMock()
    embed.title = title
    embed.description = description

    mock_fields = []
    if fields:
        for name, value in fields:
            field = MagicMock()
            field.name = name
            field.value = value
            mock_fields.append(field)
    embed.fields = mock_fields

    return embed


# ---------------------------------------------------------------------------
# Successful parsing
# ---------------------------------------------------------------------------


class TestParseSuccess:
    """Tests for successfully parsed CheddarFlow embeds."""

    def test_full_embed_parsing(self):
        """Full embed with title + fields parses correctly."""
        embed = make_embed(
            title="SPX 5950 C 02/21",
            fields=[
                ("Premium", "$125K"),
                ("Volume", "500"),
                ("Order Type", "SWEEP"),
                ("Spot Price", "$5,945.50"),
            ],
        )
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["ticker"] == "SPX"
        assert result["strike"] == 5950.0
        assert result["side"] == "CALL"
        assert result["expiry"] == "02/21"
        assert result["premium"] == 125_000.0
        assert result["volume"] == 500
        assert result["order_type"] == "SWEEP"
        assert result["spot_price"] == 5945.50

    def test_spy_put_parsing(self):
        """SPY put embed parses correctly."""
        embed = make_embed(
            title="SPY 590 P 03/15",
            fields=[
                ("Premium", "$75K"),
                ("Volume", "1,200"),
            ],
        )
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["ticker"] == "SPY"
        assert result["strike"] == 590.0
        assert result["side"] == "PUT"
        assert result["premium"] == 75_000.0
        assert result["volume"] == 1200

    def test_sweep_detection_in_description(self):
        """Sweep keyword in description is detected."""
        embed = make_embed(
            title="SPX 6000 C 02/28",
            description="Aggressive SWEEP detected on the ask",
        )
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["is_sweep"] is True

    def test_sweep_detection_case_insensitive(self):
        """Sweep keyword detection is case-insensitive."""
        embed = make_embed(
            title="SPX 5900 P 02/21",
            description="Large sweep order",
        )
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["is_sweep"] is True

    def test_premium_millions(self):
        """Premium in millions parses correctly."""
        embed = make_embed(
            title="SPX 6000 C 03/01",
            fields=[("Premium", "$2.5M")],
        )
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["premium"] == 2_500_000.0

    def test_premium_plain_number(self):
        """Premium without suffix parses as raw value."""
        embed = make_embed(
            title="SPX 5800 P 02/28",
            fields=[("Size", "$150,000")],
        )
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["premium"] == 150_000.0

    def test_field_based_side_detection(self):
        """Side detected from dedicated field."""
        embed = make_embed(
            title="SPX Flow Alert",
            description="SPX 5950",
            fields=[
                ("Side", "Call"),
                ("Strike", "$5,950.00"),
            ],
        )
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["side"] == "CALL"
        assert result["strike"] == 5950.0

    def test_field_based_expiry(self):
        """Expiry detected from dedicated field."""
        embed = make_embed(
            title="SPX 5900 C",
            fields=[("Expiration", "2026-03-15")],
        )
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["expiry"] == "2026-03-15"

    def test_iso_date_expiry_in_title(self):
        """ISO date format expiry in title is parsed."""
        embed = make_embed(title="SPX 5950 C 2026-02-28")
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["expiry"] == "2026-02-28"


# ---------------------------------------------------------------------------
# SPX/SPY filtering
# ---------------------------------------------------------------------------


class TestFiltering:
    """Tests for ticker filtering logic (used by the cog)."""

    def test_non_spx_ticker_parsed(self):
        """Non-SPX tickers are parsed (filtering happens in the cog, not parser)."""
        embed = make_embed(title="AAPL 185 C 03/21")
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["ticker"] == "AAPL"

    def test_spx_ticker_detected(self):
        """SPX ticker is correctly detected."""
        embed = make_embed(title="SPX 5950 C 02/21")
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["ticker"] == "SPX"

    def test_spy_ticker_detected(self):
        """SPY ticker is correctly detected."""
        embed = make_embed(title="SPY 595 P 02/21")
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["ticker"] == "SPY"


# ---------------------------------------------------------------------------
# Premium threshold
# ---------------------------------------------------------------------------


class TestPremiumThreshold:
    """Tests for premium threshold filtering (happens in the cog)."""

    def test_premium_above_threshold(self):
        """Premium above $50K is parsed for the cog to filter."""
        embed = make_embed(
            title="SPX 5950 C 02/21",
            fields=[("Premium", "$75K")],
        )
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["premium"] == 75_000.0

    def test_premium_below_threshold(self):
        """Premium below $50K is still parsed (cog handles filtering)."""
        embed = make_embed(
            title="SPX 5900 P 02/21",
            fields=[("Premium", "$10K")],
        )
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["premium"] == 10_000.0

    def test_no_premium_field(self):
        """Missing premium field results in None (cog skips threshold check)."""
        embed = make_embed(title="SPX 5950 C 02/21")
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["premium"] is None


# ---------------------------------------------------------------------------
# Resilience to malformed/changed formats
# ---------------------------------------------------------------------------


class TestResilience:
    """Tests for parser resilience to unexpected embed formats."""

    def test_empty_embed_returns_none(self):
        """Embed with no title/description/fields returns None."""
        embed = make_embed()
        result = parse_cheddarflow_embed(embed)
        assert result is None

    def test_no_ticker_returns_none(self):
        """Embed without a recognizable ticker returns None."""
        embed = make_embed(
            title="Unknown Flow Alert",
            description="Something happened",
        )
        result = parse_cheddarflow_embed(embed)
        assert result is None

    def test_none_title_handled(self):
        """Embed with None title doesn't crash."""
        embed = make_embed(description="SPX 5950 C")
        embed.title = None
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["ticker"] == "SPX"

    def test_none_description_handled(self):
        """Embed with None description doesn't crash."""
        embed = make_embed(title="SPX 5950 C 02/21")
        embed.description = None
        result = parse_cheddarflow_embed(embed)
        assert result is not None

    def test_none_field_name_handled(self):
        """Field with None name doesn't crash."""
        embed = make_embed(title="SPX 5950 C 02/21")
        field = MagicMock()
        field.name = None
        field.value = "$50K"
        embed.fields = [field]
        result = parse_cheddarflow_embed(embed)
        assert result is not None

    def test_none_field_value_handled(self):
        """Field with None value doesn't crash."""
        embed = make_embed(title="SPX 5950 C 02/21")
        field = MagicMock()
        field.name = "Premium"
        field.value = None
        embed.fields = [field]
        result = parse_cheddarflow_embed(embed)
        assert result is not None

    def test_partial_data_still_parses(self):
        """Embed with only ticker parses (other fields None)."""
        embed = make_embed(title="SPX alert")
        result = parse_cheddarflow_embed(embed)
        assert result is not None
        assert result["ticker"] == "SPX"
        assert result["strike"] is None
        assert result["side"] is None
        assert result["premium"] is None

    def test_exception_returns_none(self):
        """If parsing throws an unexpected exception, returns None."""
        embed = MagicMock()
        embed.title = "SPX 5950 C"
        embed.description = "test"
        # Make fields iteration throw
        type(embed).fields = property(lambda self: (_ for _ in ()).throw(RuntimeError("boom")))
        result = parse_cheddarflow_embed(embed)
        assert result is None
