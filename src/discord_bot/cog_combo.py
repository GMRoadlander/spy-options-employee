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


import re
from datetime import date, timedelta


def _parse_expiration(exp_str: str) -> str | None:
    """Parse expiration like 'apr17', '4/17', 'april 17', 'may8'."""
    exp_str = exp_str.strip().lower()
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "april": 4,
        "may": 5, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    # Format: apr17, april17, may8
    m = re.match(r"([a-z]+)\s*(\d{1,2})", exp_str)
    if m and m.group(1) in months:
        month = months[m.group(1)]
        day = int(m.group(2))
        year = date.today().year
        return f"{year}-{month:02d}-{day:02d}"
    # Format: 4/17, 4/7
    m = re.match(r"(\d{1,2})/(\d{1,2})", exp_str)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = date.today().year
        return f"{year}-{month:02d}-{day:02d}"
    return None


def _parse_combo_regex(description: str) -> ParsedCombo | None:
    """Try to parse combo with regex before falling back to Claude."""
    desc = description.lower().strip()
    segments = re.split(r"[,+]", desc)
    legs: list[ComboLeg] = []

    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue

        # Reverse calendar: "reverse cal 600p apr17/may8" or "600p revcal apr17/may8"
        rc = re.search(
            r"(?:reverse\s*cal(?:endar)?|revcal|rc)\s+(\d+(?:\.\d+)?)\s*([pc])\s+"
            r"([a-z]+\d+|[\d/]+)\s*/\s*([a-z]+\d+|[\d/]+)",
            seg,
        )
        if not rc:
            rc = re.search(
                r"(\d+(?:\.\d+)?)\s*([pc])\s+(?:reverse\s*cal(?:endar)?|revcal|rc)\s+"
                r"([a-z]+\d+|[\d/]+)\s*/\s*([a-z]+\d+|[\d/]+)",
                seg,
            )
        if rc:
            strike = float(rc.group(1))
            opt = "put" if rc.group(2) == "p" else "call"
            near_exp = _parse_expiration(rc.group(3))
            far_exp = _parse_expiration(rc.group(4))
            legs.append(ComboLeg(opt, "sell", strike, near_exp))
            legs.append(ComboLeg(opt, "buy", strike, far_exp))
            continue

        # Spread: "645/635 put spread apr17" or "sell 645/635p apr17"
        sp = re.search(
            r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*([pc])?",
            seg,
        )
        if sp:
            s1, s2 = float(sp.group(1)), float(sp.group(2))
            opt_raw = sp.group(3) or ""
            if not opt_raw:
                if "put" in seg:
                    opt_raw = "p"
                elif "call" in seg:
                    opt_raw = "c"
            opt = "put" if opt_raw.startswith("p") else "call"
            # Find expiration anywhere in segment
            exp = None
            exp_match = re.search(r"(?:exp\s*)?([a-z]{3,5})(\d{1,2})\b", seg)
            if exp_match:
                exp = _parse_expiration(exp_match.group(1) + exp_match.group(2))
            if not exp:
                exp_match = re.search(r"(\d{1,2})/(\d{1,2})", seg)
                if exp_match and float(exp_match.group(1)) <= 12:
                    exp = _parse_expiration(exp_match.group(0))
            direction = "sell" if "sell" in seg else "buy"
            hedge = "sell" if direction == "buy" else "buy"
            legs.append(ComboLeg(opt, direction, s1, exp))
            legs.append(ComboLeg(opt, hedge, s2, exp))
            continue

    if not legs:
        return None

    return ParsedCombo(
        strategy_name="Options Combo",
        legs=legs,
        notes="Parsed via regex (no Claude API needed)",
    )


async def _parse_combo(description: str) -> ParsedCombo:
    """Parse combo: try regex first, fall back to Claude."""
    result = _parse_combo_regex(description)
    if result is not None:
        logger.info("Parsed combo via regex: %d legs", len(result.legs))
        return result
    logger.info("Regex parse failed, trying Claude...")
    return await _parse_combo_via_claude(description)


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

def _convert_legs(parsed: ParsedCombo) -> list:
    """Convert cog ComboLeg objects to engine ComboLeg objects."""
    from src.analysis.combo_odds import ComboLeg as EngineLeg
    from datetime import date as dt_date

    engine_legs = []
    today = dt_date.today()

    # Group legs to detect spreads vs calendars
    for i, leg in enumerate(parsed.legs):
        # Calculate DTE from expiration string
        dte = 14  # default
        if leg.expiration:
            try:
                exp_date = dt_date.fromisoformat(leg.expiration)
                dte = max((exp_date - today).days, 1)
            except ValueError:
                pass

        strike = leg.strike or 0.0
        action = leg.direction if leg.direction in ("buy", "sell") else "buy"

        engine_legs.append(EngineLeg(
            leg_name=f"leg{i+1}_{action}_{leg.option_type}_{strike:.0f}",
            option_type=leg.option_type,
            strike=strike,
            dte_days=dte,
            action=action,
            quantity=leg.quantity,
            leg_role="single",
        ))

    # Detect calendar spreads (same strike, same type, different DTE, buy+sell)
    for i, a in enumerate(engine_legs):
        for j, b in enumerate(engine_legs):
            if i >= j:
                continue
            if (a.strike == b.strike and a.option_type == b.option_type
                    and a.action != b.action and a.dte_days != b.dte_days):
                # Calendar pair found
                if a.dte_days < b.dte_days:
                    near, far = a, b
                else:
                    near, far = b, a
                near.leg_role = "calendar_near"
                far.leg_role = "calendar_far"

    return engine_legs


async def _run_combo_engine(
    parsed: ParsedCombo,
    spot: float,
    iv: float,
    cost: float | None,
) -> "ComboOddsResult":
    from src.analysis.combo_odds import evaluate_combo
    from src.analysis.combo_odds import ComboOddsResult as EngineResult
    from src.config import config as cfg

    engine_legs = _convert_legs(parsed)
    result = await evaluate_combo(
        legs=engine_legs,
        spot=spot,
        atm_iv=iv,
        r=cfg.risk_free_rate,
        n_paths=100_000,
        entry_cost=cost * 100 if cost else None,
    )
    return result


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
        # Extract inline what-if params from combo text: iv:0.35 spot:640 cost:1.50
        if iv is None:
            m = re.search(r"iv[:\s]+(\d+\.?\d*)", combo)
            if m:
                iv = float(m.group(1))
                if iv > 1:
                    iv = iv / 100  # 35 -> 0.35
        if spot is None:
            m = re.search(r"spot[:\s]+(\d+\.?\d*)", combo)
            if m:
                spot = float(m.group(1))
        if cost is None:
            m = re.search(r"cost[:\s]+(\d+\.?\d*)", combo)
            if m:
                cost = float(m.group(1))

        # Strip what-if params from combo text before parsing legs
        clean_combo = re.sub(r"(?:optional\s+)?(?:what-if[:\s]*)?\/?odds\s+", " ", combo)
        clean_combo = re.sub(r"iv[:\s]+\d+\.?\d*", "", clean_combo)
        clean_combo = re.sub(r"spot[:\s]+\d+\.?\d*", "", clean_combo)
        clean_combo = re.sub(r"cost[:\s]+\d+\.?\d*", "", clean_combo)
        clean_combo = clean_combo.strip().strip(",").strip()

        try:
            parsed = await _parse_combo(clean_combo)
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
            result = await _run_combo_engine(parsed, live_spot, live_iv, cost)
        except Exception as exc:
            logger.error("Combo engine error: %s", exc, exc_info=True)
            await interaction.followup.send(
                f"Combo analysis engine error: {exc}",
                ephemeral=True,
            )
            return
        overrides_used = iv is not None or spot is not None or cost is not None
        embed = build_odds_embed(result, parsed, spot=live_spot, iv=live_iv, cost=cost, overrides_active=overrides_used)

        # Generate chart
        from src.discord_bot.charts import create_odds_chart
        chart = await asyncio.to_thread(create_odds_chart, result, live_spot)
        files: list[discord.File] = []
        if chart is not None:
            embed.set_image(url="attachment://odds_chart.png")
            files.append(chart)

        await interaction.followup.send(embed=embed, files=files if files else discord.utils.MISSING)


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
    result: Any,
    parsed: ParsedCombo,
    *,
    spot: float = 0.0,
    iv: float = 0.0,
    cost: float | None = None,
    overrides_active: bool = False,
) -> discord.Embed:
    """Build probability matrix embed from engine ComboOddsResult."""
    color = _pop_color(result.prob_profit)
    embed = discord.Embed(
        title=f"Odds: {parsed.strategy_name}",
        color=color,
    )

    # Summary
    embed.add_field(name="P(Profit)", value=_fmt_pct(result.prob_profit), inline=True)
    embed.add_field(name="E[P&L]", value=f"${result.expected_pnl:+.2f}", inline=True)
    embed.add_field(name="Median", value=f"${result.median_pnl:+.2f}", inline=True)

    # Percentiles
    p5 = result.percentiles.get(5, 0)
    p95 = result.percentiles.get(95, 0)
    embed.add_field(name="P5 / P95", value=f"${p5:+.0f} / ${p95:+.0f}", inline=True)
    embed.add_field(name="Spot", value=f"${spot:,.2f}", inline=True)
    embed.add_field(name="IV", value=_fmt_pct(iv), inline=True)

    # Scenario table
    if result.scenario_table:
        lines = []
        for s in result.scenario_table:
            pnl = s["pnl"]
            bar = "+" * min(max(1, int(pnl / 2)), 8) if pnl > 0 else "-" * min(max(1, int(abs(pnl) / 2)), 8)
            lines.append(f"{s['move_pct']:+5.1f}% ${s['spot']:>7.0f} {bar}")
        embed.add_field(
            name="Scenario Table",
            value="```\n" + "\n".join(lines) + "\n```",
            inline=False,
        )

    # Per-leg results
    if result.leg_results:
        leg_lines = []
        for lr in result.leg_results:
            leg_lines.append(f"{lr.leg_name}: E=${lr.mean_pnl:+.1f} P={lr.prob_profit:.0%}")
        embed.add_field(
            name="Legs",
            value="```\n" + "\n".join(leg_lines)[:900] + "\n```",
            inline=False,
        )

    # Risk flags
    if result.risk_flags:
        flags_text = "\n".join(f"[!] {f}" for f in result.risk_flags)
        embed.add_field(name="Risk Flags", value=flags_text[:1024], inline=False)

    footer = [f"{result.n_paths:,} paths", f"seed={result.seed_used}"]
    if overrides_active:
        footer.append("what-if active")
    embed.set_footer(text=" | ".join(footer))
    return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ComboCog(bot))
    logger.info("ComboCog registered")
