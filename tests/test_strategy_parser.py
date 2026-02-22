"""Tests for the natural language strategy parser."""

import pytest
import yaml
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai.strategy_parser import StrategyParser, StrategyParseError
from src.strategy.schema import (
    StrategyTemplate,
    StrategyType,
    LegSide,
    LegAction,
)


# -- Fixtures ----------------------------------------------------------------

VALID_IRON_CONDOR_YAML = """\
name: SPX Iron Condor 30-45 DTE
version: "1.0"
description: Sell 30-45 DTE iron condors on SPX when IV rank is above 30
ticker: SPX
structure:
  strategy_type: iron_condor
  legs:
    - name: short_put
      side: put
      action: sell
      delta_target: fixed
      delta_value: 0.16
      quantity: 1
    - name: long_put
      side: put
      action: buy
      delta_target: fixed
      delta_value: 0.05
      quantity: 1
    - name: short_call
      side: call
      action: sell
      delta_target: fixed
      delta_value: 0.16
      quantity: 1
    - name: long_call
      side: call
      action: buy
      delta_target: fixed
      delta_value: 0.05
      quantity: 1
  dte_target: 37
  dte_min: 30
  dte_max: 45
entry:
  iv_rank_min: 30
  iv_rank_max: 100
  time_of_day: any
exit:
  profit_target_pct: 0.50
  stop_loss_pct: 2.0
  dte_close: 0
sizing:
  max_risk_pct: 0.02
  max_positions: 3
tags:
  - iron_condor
  - premium_selling
"""

VALID_PUT_SPREAD_YAML = """\
name: SPX Put Credit Spread
version: "1.0"
description: Sell put spreads on SPX
ticker: SPX
structure:
  strategy_type: vertical_spread
  legs:
    - name: short_put
      side: put
      action: sell
      delta_target: fixed
      delta_value: 0.20
      quantity: 1
    - name: long_put
      side: put
      action: buy
      delta_target: fixed
      delta_value: 0.10
      quantity: 1
  dte_target: 30
  dte_min: 25
  dte_max: 35
entry:
  iv_rank_min: 0
  iv_rank_max: 100
  time_of_day: any
exit:
  profit_target_pct: 0.50
  stop_loss_pct: 2.0
  dte_close: 0
sizing:
  max_risk_pct: 0.02
  max_positions: 3
tags: []
"""


def _mock_claude_response(yaml_text: str, explanation: str = "Parsed successfully."):
    """Build a mock Claude API response."""
    text_content = f"{yaml_text}\nEXPLANATION: {explanation}"
    block = MagicMock()
    block.type = "text"
    block.text = text_content

    message = MagicMock()
    message.content = [block]
    return message


def _make_parser() -> StrategyParser:
    """Create a parser with a fake API key."""
    return StrategyParser(api_key="test-key", model="claude-sonnet-4-6")


# -- Tests -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parse_iron_condor():
    """Test parsing a valid iron condor description into StrategyTemplate."""
    parser = _make_parser()
    mock_response = _mock_claude_response(VALID_IRON_CONDOR_YAML)

    with patch("src.ai.strategy_parser.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        template, explanation = await parser.parse(
            "Sell 30-45 DTE iron condors on SPX when IV rank is above 30"
        )

    assert isinstance(template, StrategyTemplate)
    assert template.name == "SPX Iron Condor 30-45 DTE"
    assert template.structure.strategy_type == StrategyType.IRON_CONDOR
    assert len(template.structure.legs) == 4
    assert template.entry.iv_rank_min == 30.0
    assert template.exit.profit_target_pct == 0.50
    assert "Parsed" in explanation


@pytest.mark.asyncio
async def test_parse_vertical_spread():
    """Test parsing a valid vertical spread."""
    parser = _make_parser()
    mock_response = _mock_claude_response(VALID_PUT_SPREAD_YAML)

    with patch("src.ai.strategy_parser.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        template, explanation = await parser.parse("Sell put spreads on SPX")

    assert template.structure.strategy_type == StrategyType.VERTICAL_SPREAD
    assert len(template.structure.legs) == 2


@pytest.mark.asyncio
async def test_parse_strips_code_fences():
    """Test that markdown code fences are stripped from Claude output."""
    parser = _make_parser()
    fenced_yaml = f"```yaml\n{VALID_PUT_SPREAD_YAML}```\nEXPLANATION: Parsed."
    block = MagicMock()
    block.type = "text"
    block.text = fenced_yaml
    message = MagicMock()
    message.content = [block]

    with patch("src.ai.strategy_parser.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=message)
        mock_cls.return_value = mock_client

        template, _ = await parser.parse("Sell put spreads")

    assert isinstance(template, StrategyTemplate)


@pytest.mark.asyncio
async def test_parse_invalid_yaml_raises_error():
    """Test that invalid YAML from Claude raises StrategyParseError."""
    parser = _make_parser()
    block = MagicMock()
    block.type = "text"
    block.text = "not: valid: yaml: [[[unclosed"
    message = MagicMock()
    message.content = [block]

    with patch("src.ai.strategy_parser.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=message)
        mock_cls.return_value = mock_client

        with pytest.raises(StrategyParseError, match="Invalid YAML"):
            await parser.parse("bad input")


@pytest.mark.asyncio
async def test_parse_missing_fields_raises_error():
    """Test that YAML missing required fields raises StrategyParseError."""
    parser = _make_parser()
    # Missing 'name' which is required
    bad_yaml = "ticker: SPX\nstructure:\n  strategy_type: custom\n  legs: []\n"
    mock_response = _mock_claude_response(bad_yaml)

    with patch("src.ai.strategy_parser.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        with pytest.raises(StrategyParseError):
            await parser.parse("something incomplete")


@pytest.mark.asyncio
async def test_parse_validation_failure_raises_error():
    """Test that a template failing validation raises StrategyParseError."""
    parser = _make_parser()
    # Iron condor with only 2 legs (should require 4)
    bad_yaml = """\
name: Bad IC
ticker: SPX
structure:
  strategy_type: iron_condor
  legs:
    - name: short_put
      side: put
      action: sell
      delta_target: fixed
      delta_value: 0.16
    - name: long_put
      side: put
      action: buy
      delta_target: fixed
      delta_value: 0.05
  dte_target: 30
  dte_min: 20
  dte_max: 45
entry: {}
exit:
  profit_target_pct: 0.50
  stop_loss_pct: 2.0
sizing:
  max_risk_pct: 0.02
  max_positions: 3
tags: []
"""
    mock_response = _mock_claude_response(bad_yaml)

    with patch("src.ai.strategy_parser.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        with pytest.raises(StrategyParseError, match="validation failed"):
            await parser.parse("iron condor with wrong legs")


@pytest.mark.asyncio
async def test_refine_modifies_template():
    """Test that refinement modifies the correct fields."""
    parser = _make_parser()

    # First parse the original
    original = _mock_claude_response(VALID_IRON_CONDOR_YAML)

    # Create a refined version with tighter deltas
    refined_yaml = VALID_IRON_CONDOR_YAML.replace("delta_value: 0.16", "delta_value: 0.12")
    refined_response = _mock_claude_response(
        refined_yaml, "Tightened short leg deltas from 0.16 to 0.12."
    )

    with patch("src.ai.strategy_parser.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(side_effect=[original, refined_response])
        mock_cls.return_value = mock_client

        template, _ = await parser.parse("Iron condor 16 delta")
        refined, explanation = await parser.refine(template, "Make the delta range tighter")

    assert isinstance(refined, StrategyTemplate)
    # The short legs should now have delta 0.12
    short_legs = [l for l in refined.structure.legs if l.action == LegAction.SELL]
    for leg in short_legs:
        assert leg.delta_value == 0.12
    assert "Tightened" in explanation


@pytest.mark.asyncio
async def test_parse_empty_response_raises_error():
    """Test that an empty Claude response raises StrategyParseError."""
    parser = _make_parser()
    block = MagicMock()
    block.type = "text"
    block.text = ""
    message = MagicMock()
    message.content = [block]

    with patch("src.ai.strategy_parser.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=message)
        mock_cls.return_value = mock_client

        with pytest.raises(StrategyParseError, match="Empty response"):
            await parser.parse("empty")


@pytest.mark.asyncio
async def test_parse_no_api_key_raises_error():
    """Test that missing API key raises StrategyParseError."""
    parser = _make_parser()
    # Force clear the api key after construction to bypass config fallback
    parser._api_key = ""

    with pytest.raises(StrategyParseError, match="API key not configured"):
        await parser.parse("anything")


@pytest.mark.asyncio
async def test_refine_no_api_key_raises_error():
    """Test that missing API key in refine raises StrategyParseError."""
    parser = _make_parser()
    parser._api_key = ""
    template = StrategyTemplate(name="test")

    with pytest.raises(StrategyParseError, match="API key not configured"):
        await parser.refine(template, "change something")


def test_strip_code_fences():
    """Test the code fence stripping utility."""
    parser = _make_parser()

    # With yaml fence
    assert "name: test" in parser._strip_code_fences("```yaml\nname: test\n```")

    # Without fences
    assert parser._strip_code_fences("name: test") == "name: test"

    # Nested fences
    text = "```\nfoo\n```\nbar\n```\nbaz\n```"
    result = parser._strip_code_fences(text)
    assert "foo" in result
    assert "baz" in result
    assert "bar" in result
