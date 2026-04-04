"""Combo odds cog -- slash command for multi-leg options analysis.

Implements slash commands:
    /odds <combo> [iv] [spot] [cost] -- Evaluate a combo trade description
                                        and return probability + Greeks summary.

Borey describes trades in plain English (e.g. 'sell 580/575 put spread expiring
this Friday').  Claude parses the text into structured leg data, then the
combo engine prices the position, estimates probability of profit, and reports
the Greeks.  Optional what-if overrides (iv, spot, cost) let Borey stress-test
without re-typing the whole description.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

import anthropic
import discord
import httpx
from discord import app_commands
from discord.ext import commands

from src.config import config
from src.discord_bot.embeds import COLOR_BEARISH, COLOR_BULLISH, COLOR_INFO, COLOR_NEUTRAL

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Parsing layer
# ---------------------------------------------------------------------------

_COMBO_PARSE_SYSTEM = (
    "You are an options trade parser. Given a plain-English trade description,"
    " return ONLY a JSON object with no markdown fences or text outside the JSON."
    " Schema: strategy_name (string), legs (list of: option_type call|put,"
    " direction buy|sell, strike float or null, expiration string or null,"
    " quantity int default 1), notes (string for ambiguities)."
    " Rules: infer option_type from context. For vertical spreads, short leg first."
    " If a field is unknown use null. Return ONLY the JSON object."
)


@dataclass
class ComboLeg:
    """Parsed representation of a single option leg."""
    option_type: str
    direction: str
    strike: float | None
    expiration: str | None
    quantity: int = 1


@dataclass
class ParsedCombo:
    """Structured output of Claude natural-language parsing."""
    strategy_name: str
    legs: list[ComboLeg]
    notes: str


class ComboParseError(Exception):
    """Raised when the combo description cannot be parsed."""


_claude_client: anthropic.AsyncAnthropic | None = None


def _get_claude_client() -> anthropic.AsyncAnthropic:
    global _claude_client
    if _claude_client is None:
        _claude_client = anthropic.AsyncAnthropic(
            api_key=config.claude_api_key,
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
    return _claude_client


async def _parse_combo_via_claude(description: str) -> ParsedCombo:
    if not config.claude_api_key:
        raise ComboParseError("Claude API key not configured")
    client = _get_claude_client()
    user_msg = f"<combo_description>{description}</combo_description>"
    try:
        message = await client.messages.create(
            model=config.claude_model,
            max_tokens=512,
            system=_COMBO_PARSE_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
    except anthropic.RateLimitError as exc:
        raise ComboParseError("Claude rate limit hit -- try again in a moment") from exc
    except (anthropic.APIConnectionError, anthropic.InternalServerError) as exc:
        raise ComboParseError(f"Claude API unreachable: {exc}") from exc
    except anthropic.APIError as exc:
        raise ComboParseError(f"Claude API error: {exc}") from exc
    raw_text = "".join(
        block.text for block in message.content if block.type == "text"
    ).strip()
    if not raw_text:
        raise ComboParseError("Empty response from Claude")
    if raw_text.startswith("```"):
        raw_text = "\n".join(
            ln for ln in raw_text.splitlines() if not ln.strip().startswith("```")
        )
    try:
        data: dict[str, Any] = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ComboParseError(f"Claude returned non-JSON response: {exc}") from exc
    try:
        legs = [
            ComboLeg(
                option_type=leg["option_type"],
                direction=leg["direction"],
                strike=float(leg["strike"]) if leg.get("strike") is not None else None,
                expiration=leg.get("expiration"),
                quantity=int(leg.get("quantity") or 1),
            )
            for leg in data.get("legs", [])
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise ComboParseError(f"Unexpected leg structure in Claude response: {exc}") from exc
    if not legs:
        raise ComboParseError("No legs found in parsed combo")
    return ParsedCombo(
        strategy_name=data.get("strategy_name", "Options Combo"),
        legs=legs,
        notes=data.get("notes", ""),
    )


# ---------------------------------------------------------------------------
# Combo engine bridge
# The real module lives at src.analysis.combo_odds and is imported lazily so
# the cog loads cleanly even when that module is not yet implemented.
# ---------------------------------------------------------------------------

@dataclass
class ComboOddsResult:
    """Output from the combo odds engine."""
    strategy_name: str
    probability_of_profit: float
    expected_value: float
    max_profit: float | None
    max_loss: float | None
    delta: float
    gamma: float
    theta: float
    vega: float
    spot_used: float
    iv_used: float
    cost_used: float | None
    notes: str = ""


def _run_combo_engine(
    parsed: ParsedCombo,
    spot: float,
    iv: float,
    cost: float | None,
) -> ComboOddsResult:
    try:
        from src.analysis.combo_odds import evaluate_combo  # type: ignore[import]
        return evaluate_combo(parsed, spot=spot, iv=iv, cost=cost)
    except ImportError:
        logger.warning("src.analysis.combo_odds not yet implemented -- returning stub result")
        return ComboOddsResult(
            strategy_name=parsed.strategy_name,
            probability_of_profit=0.0,
            expected_value=0.0,
            max_profit=None,
            max_loss=None,
            delta=0.0,
            gamma=0.0,
            theta=0.0,
            vega=0.0,
            spot_used=spot,
            iv_used=iv,
            cost_used=cost,
            notes="combo_odds engine not yet implemented",
        )


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class ComboCog(commands.Cog, name="Combo"):
    """Slash commands for combo trade probability and Greeks analysis."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.services = bot.services  # type: ignore[attr-defined]
        self._semaphore = asyncio.Semaphore(1)
        logger.info("ComboCog loaded")

    @app_commands.command(
        name="odds",
        description="Evaluate a combo trade -- probability of profit, Greeks, max P&L",
    )
    @app_commands.describe(
        combo="Plain-English trade description, e.g. sell 580/575 put spread 3DTE",
        iv="Override implied volatility, e.g. 0.18 for 18% (optional)",
        spot="Override spot price, e.g. 582.50 (optional)",
        cost="Override net debit/credit in dollars, e.g. 1.25 (optional)",
    )
    async def odds(
        self,
        interaction: discord.Interaction,
        combo: str,
        iv: float | None = None,
        spot: float | None = None,
        cost: float | None = None,
    ) -> None:
        await interaction.response.defer()
        if self._semaphore.locked():
            await interaction.followup.send(
                "Analysis already running -- try again in a few seconds.",
                ephemeral=True,
            )
            return
        async with self._semaphore:
            await self._run_odds(interaction, combo, iv=iv, spot=spot, cost=cost)

    async def _run_odds(
        self,
        interaction: discord.Interaction,
        combo: str,
        *,
        iv: float | None,
        spot: float | None,
        cost: float | None,
    ) -> None:
        try:
            parsed = await _parse_combo_via_claude(combo)
        except ComboParseError as exc:
            logger.error("Combo parse failed: %s", exc)
            await interaction.followup.send(
                f"Could not parse combo description: {exc}",
                ephemeral=True,
            )
            return
        logger.info(
            "Parsed combo %r with %d leg(s): %s",
            parsed.strategy_name,
            len(parsed.legs),
            combo[:120],
        )
        live_spot: float = spot if spot is not None else 0.0
        live_iv: float = iv if iv is not None else 0.0
        if spot is None or iv is None:
            dm = self.services.data_manager
            if dm is None:
                await interaction.followup.send(
                    "DataManager not available -- provide spot and iv overrides.",
                    ephemeral=True,
                )
                return
            try:
                chain = await dm.get_chain("SPY")
            except Exception as exc:
                logger.error("Chain fetch failed during /odds: %s", exc, exc_info=True)
                await interaction.followup.send(
                    "Failed to fetch live SPY data. Provide spot and iv overrides or try again.",
                    ephemeral=True,
                )
                return
            if chain is None:
                await interaction.followup.send(
                    "No live SPY data. Provide spot and iv overrides.",
                    ephemeral=True,
                )
                return
            if spot is None:
                live_spot = float(getattr(chain, "spot_price", 0.0))
            if iv is None:
                live_iv = float(getattr(chain, "atm_iv", 0.20))
        try:
            result: ComboOddsResult = await asyncio.to_thread(
                _run_combo_engine, parsed, live_spot, live_iv, cost
            )
        except Exception as exc:
            logger.error("Combo engine error: %s", exc, exc_info=True)
            await interaction.followup.send(
                f"Combo analysis engine error: {exc}",
                ephemeral=True,
            )
            return
        overrides_used = iv is not None or spot is not None or cost is not None
        primary = build_odds_embed(result, parsed, overrides_active=overrides_used)
        detail_embeds = build_odds_detail_embeds(result, parsed)
        await interaction.followup.send(embeds=[primary, *detail_embeds])


# ---------------------------------------------------------------------------
# Embed builders -- move to embeds.py once the API stabilises
# ---------------------------------------------------------------------------

def _fmt_price(value: float) -> str:
    return f"${value:,.2f}"


def _fmt_pct(value: float) -> str:
    return f"{value:.1%}"


def _fmt_greek(value: float) -> str:
    return f"{value:+.4f}"


def _pop_color(pop: float) -> int:
    if pop >= 0.65:
        return COLOR_BULLISH
    if pop >= 0.45:
        return COLOR_NEUTRAL
    return COLOR_BEARISH


def build_odds_embed(
    result: ComboOddsResult,
    parsed: ParsedCombo,
    *,
    overrides_active: bool = False,
) -> discord.Embed:
    color = _pop_color(result.probability_of_profit)
    embed = discord.Embed(title=f"Odds: {result.strategy_name}", color=color)
    embed.add_field(name="Prob. of Profit", value=_fmt_pct(result.probability_of_profit), inline=True)
    embed.add_field(name="Expected Value", value=_fmt_price(result.expected_value), inline=True)
    max_profit_str = _fmt_price(result.max_profit) if result.max_profit is not None else "Unlimited"
    max_loss_str = _fmt_price(result.max_loss) if result.max_loss is not None else "Unlimited"
    embed.add_field(name="Max Profit", value=max_profit_str, inline=True)
    embed.add_field(name="Max Loss", value=max_loss_str, inline=True)
    embed.add_field(name="Spot Used", value=_fmt_price(result.spot_used), inline=True)
    embed.add_field(name="IV Used", value=_fmt_pct(result.iv_used), inline=True)
    if result.cost_used is not None:
        embed.add_field(name="Cost Override", value=_fmt_price(result.cost_used), inline=True)
    if result.notes:
        embed.add_field(name="Notes", value=result.notes[:1024], inline=False)
    footer_parts = [f"{len(parsed.legs)} leg(s)"]
    if overrides_active:
        footer_parts.append("what-if overrides applied")
    embed.set_footer(text=" | ".join(footer_parts))
    return embed


def build_odds_detail_embeds(
    result: ComboOddsResult,
    parsed: ParsedCombo,
) -> list[discord.Embed]:
    embeds: list[discord.Embed] = []
    greeks_embed = discord.Embed(title="Greeks", color=COLOR_INFO)
    greeks_embed.add_field(name="Delta", value=_fmt_greek(result.delta), inline=True)
    greeks_embed.add_field(name="Gamma", value=_fmt_greek(result.gamma), inline=True)
    greeks_embed.add_field(name="Theta", value=_fmt_greek(result.theta), inline=True)
    greeks_embed.add_field(name="Vega", value=_fmt_greek(result.vega), inline=True)
    embeds.append(greeks_embed)
    if parsed.legs:
        legs_embed = discord.Embed(title="Parsed Legs", color=COLOR_INFO)
        leg_lines: list[str] = []
        for i, leg in enumerate(parsed.legs, start=1):
            strike_str = _fmt_price(leg.strike) if leg.strike is not None else "n/a"
            leg_lines.append(
                f"**{i}.** {leg.direction.upper()} {leg.quantity}x "
                f"{leg.option_type.upper()} {strike_str} exp {leg.expiration or 'n/a'}"
            )
        legs_embed.add_field(
            name="Legs",
            value="\n".join(leg_lines)[:1024],
            inline=False,
        )
        embeds.append(legs_embed)
    return embeds


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ComboCog(bot))
    logger.info("ComboCog registered")
