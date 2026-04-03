"""AI commentary generator for SPY/SPX options analysis.

Uses Claude Haiku to produce concise, actionable trading commentary from
analysis results. Each call sends structured market data and receives back
a 2-3 sentence interpretation focusing on GEX levels, dealer positioning,
and any extreme conditions.

Rate budget: ~195 calls/day at 2-minute intervals during market hours
(6.5 hours x 30/hr x 2 tickers = 390, but batched to ~195).
"""

import logging

import anthropic
import httpx

from src.analysis.analyzer import AnalysisResult
from src.config import config

logger = logging.getLogger(__name__)

# Module-level reusable client (lazy-initialized)
_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    """Return a shared AsyncAnthropic client, creating it on first use."""
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(
            api_key=config.claude_api_key,
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
    return _client

SYSTEM_PROMPT = """\
You are a concise options market analyst. Given structured SPY/SPX analysis \
data, produce a 2-3 sentence commentary that:

- Focuses on actionable intelligence (what the data means for price action)
- References specific price levels from GEX (gamma flip, ceiling, floor)
- Highlights extreme conditions: gamma flip crossover, squeeze probability \
>30%, extreme PCR readings, dealer short-gamma positioning
- Mentions max pain as a gravitational target near expiry
- States directional bias with the qualifying GEX level (e.g. "bearish below $595")
- Do NOT give trading advice or recommend trades -- present data interpretation only
- Do NOT use hedging phrases like "it's important to note" or "traders should be aware"
- Keep it tight: 2-3 sentences, no bullet points, no headers\
"""


def _build_user_prompt(result: AnalysisResult) -> str:
    """Build a structured user prompt from an AnalysisResult.

    Formats all relevant metrics into a readable block that Claude can
    interpret without needing to parse JSON or complex structures.

    Args:
        result: The consolidated analysis result.

    Returns:
        Formatted prompt string with all analysis metrics.
    """
    gex = result.gex
    mp = result.max_pain
    pcr = result.pcr

    # Format gamma flip line
    if gex.gamma_flip is not None:
        gamma_flip_line = f"Gamma Flip Level: ${gex.gamma_flip:.2f}"
        # Determine if spot is above or below flip
        if result.spot_price > gex.gamma_flip:
            gamma_flip_line += (
                f" (spot is ${result.spot_price - gex.gamma_flip:.2f} ABOVE flip "
                "-- positive gamma territory)"
            )
        else:
            gamma_flip_line += (
                f" (spot is ${gex.gamma_flip - result.spot_price:.2f} BELOW flip "
                "-- negative gamma territory)"
            )
    else:
        gamma_flip_line = "Gamma Flip Level: None detected (uniformly positive or negative GEX)"

    # Format net GEX direction
    gex_direction = "POSITIVE (dealers long gamma, dampening moves)" if gex.net_gex >= 0 \
        else "NEGATIVE (dealers short gamma, amplifying moves)"

    # Key levels summary
    key_levels_str = ""
    if result.strike_intel.key_levels:
        top_levels = result.strike_intel.key_levels[:6]
        level_parts = []
        for level in top_levels:
            level_parts.append(
                f"  ${level.price:.2f} ({level.level_type}, significance: {level.significance:.2f})"
            )
        key_levels_str = "\n".join(level_parts)
    else:
        key_levels_str = "  No key levels identified"

    prompt = f"""\
Ticker: {result.ticker}
Spot Price: ${result.spot_price:.2f}

--- GEX (Gamma Exposure) ---
Net GEX: {gex.net_gex:.2e} -- {gex_direction}
{gamma_flip_line}
Gamma Ceiling (call wall): ${gex.gamma_ceiling:.2f}
Gamma Floor (put wall): ${gex.gamma_floor:.2f}
Squeeze Probability: {gex.squeeze_probability:.0%}

--- Max Pain ---
Max Pain Price: ${mp.max_pain_price:.2f} (expiry: {mp.expiry})
Distance from Spot: {mp.distance_pct:+.2f}%

--- Put/Call Ratio ---
Volume PCR: {pcr.volume_pcr:.3f}
OI PCR: {pcr.oi_pcr:.3f}
Signal: {pcr.signal}
Dealer Positioning: {pcr.dealer_positioning}

--- Key Levels ---
{key_levels_str}

Provide your 2-3 sentence commentary.\
"""
    return prompt


async def generate_commentary(result: AnalysisResult) -> str:
    """Generate AI commentary for an analysis result.

    Sends structured analysis data to Claude Haiku and gets back
    a concise, actionable trading commentary.

    Args:
        result: Consolidated analysis result from all engines.

    Returns:
        Commentary string. Empty string if Claude API is unavailable or errors.
    """
    if not config.claude_api_key:
        logger.warning("Claude API key not configured -- skipping commentary generation")
        return ""

    user_prompt = _build_user_prompt(result)

    try:
        client = _get_client()

        message = await client.messages.create(
            model=config.claude_model,
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )

        # Extract text from the response content blocks
        commentary = ""
        for block in message.content:
            if block.type == "text":
                commentary += block.text

        commentary = commentary.strip()

        if not commentary:
            logger.warning(
                "Claude returned empty commentary for %s at $%.2f",
                result.ticker,
                result.spot_price,
            )
            return ""

        logger.info(
            "Generated commentary for %s (%d chars, %d input tokens, %d output tokens)",
            result.ticker,
            len(commentary),
            message.usage.input_tokens,
            message.usage.output_tokens,
        )
        return commentary

    except anthropic.AuthenticationError:
        logger.error("Claude API authentication failed -- check CLAUDE_API_KEY")
        return ""

    except anthropic.RateLimitError:
        logger.warning("Claude API rate limit hit -- skipping commentary this cycle")
        return ""

    except anthropic.APIConnectionError:
        logger.error("Could not connect to Claude API -- network issue or API down")
        return ""

    except anthropic.APIStatusError as exc:
        logger.error(
            "Claude API returned status %d: %s",
            exc.status_code,
            exc.message,
        )
        return ""

    except Exception:
        logger.exception("Unexpected error generating commentary for %s", result.ticker)
        return ""
