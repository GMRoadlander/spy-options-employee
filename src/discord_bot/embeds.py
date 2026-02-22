"""Discord embed builders for SPY/SPX options analysis.

Builds rich embeds with color coding:
    - Green (#00ff00) for bullish signals
    - Red (#ff0000) for bearish signals
    - Yellow (#ffff00) for neutral/caution
    - Blue (#0099ff) for informational
"""

import logging
from datetime import datetime

import discord

from src.analysis.analyzer import AnalysisResult
from src.analysis.gex import GEXResult
from src.analysis.max_pain import MaxPainResult
from src.analysis.pcr import PCRResult
from src.analysis.strike_intel import StrikeIntelResult

logger = logging.getLogger(__name__)

# Color constants
COLOR_BULLISH = 0x00FF00
COLOR_BEARISH = 0xFF0000
COLOR_NEUTRAL = 0xFFFF00
COLOR_INFO = 0x0099FF


def _fmt_number(value: float, decimals: int = 2) -> str:
    """Format a number with B/M/K suffixes for readability.

    Args:
        value: The number to format.
        decimals: Decimal places to keep.

    Returns:
        Formatted string like "$1.23B", "$456.7M", "$12.3K", or "$1.23".
    """
    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1_000_000_000:
        return f"{sign}${abs_val / 1_000_000_000:.{decimals}f}B"
    elif abs_val >= 1_000_000:
        return f"{sign}${abs_val / 1_000_000:.{decimals}f}M"
    elif abs_val >= 1_000:
        return f"{sign}${abs_val / 1_000:.{decimals}f}K"
    else:
        return f"{sign}${abs_val:.{decimals}f}"


def _fmt_price(value: float) -> str:
    """Format a price value."""
    return f"${value:,.2f}"


def _fmt_pct(value: float) -> str:
    """Format a percentage value."""
    return f"{value:.2f}%"


def _fmt_int(value: int) -> str:
    """Format an integer with comma separators."""
    return f"{value:,}"


def _signal_color(signal: str) -> int:
    """Map a signal string to a Discord embed color.

    Args:
        signal: One of "extreme_bullish", "bullish", "neutral", "bearish", "extreme_fear".

    Returns:
        Hex color integer.
    """
    mapping = {
        "extreme_bullish": COLOR_BULLISH,
        "bullish": COLOR_BULLISH,
        "neutral": COLOR_NEUTRAL,
        "bearish": COLOR_BEARISH,
        "extreme_fear": COLOR_BEARISH,
    }
    return mapping.get(signal, COLOR_INFO)


def _signal_emoji(signal: str) -> str:
    """Map a signal string to a text indicator."""
    mapping = {
        "extreme_bullish": "[STRONG BULL]",
        "bullish": "[BULL]",
        "neutral": "[NEUTRAL]",
        "bearish": "[BEAR]",
        "extreme_fear": "[EXTREME FEAR]",
    }
    return mapping.get(signal, "[--]")


def _gex_regime_text(net_gex: float) -> str:
    """Describe the GEX regime in plain English."""
    if net_gex > 0:
        return "Positive = dealers long gamma, dampening moves"
    elif net_gex < 0:
        return "Negative = dealers short gamma, amplifying moves"
    else:
        return "Neutral = balanced dealer positioning"


def _dealer_text(dealer_positioning: str) -> str:
    """Describe dealer positioning in plain English."""
    mapping = {
        "short_gamma": "Short Gamma (amplifying moves, buying dips/selling rips)",
        "long_gamma": "Long Gamma (dampening moves, selling dips/buying rips)",
        "neutral": "Neutral (balanced hedging)",
    }
    return mapping.get(dealer_positioning, dealer_positioning)


def build_gex_embed(result: AnalysisResult) -> discord.Embed:
    """Build a rich embed for GEX analysis.

    Args:
        result: Full analysis result.

    Returns:
        Discord Embed with GEX fields.
    """
    gex = result.gex
    color = COLOR_BULLISH if gex.net_gex > 0 else COLOR_BEARISH if gex.net_gex < 0 else COLOR_NEUTRAL

    embed = discord.Embed(
        title=f"Gamma Exposure (GEX) -- {result.ticker}",
        description=_gex_regime_text(gex.net_gex),
        color=color,
        timestamp=result.timestamp,
    )

    embed.add_field(
        name="Net GEX",
        value=_fmt_number(gex.net_gex),
        inline=True,
    )
    embed.add_field(
        name="Gamma Flip",
        value=_fmt_price(gex.gamma_flip) if gex.gamma_flip is not None else "None",
        inline=True,
    )
    embed.add_field(
        name="Squeeze Probability",
        value=_fmt_pct(gex.squeeze_probability * 100),
        inline=True,
    )
    embed.add_field(
        name="Gamma Ceiling (resistance)",
        value=_fmt_price(gex.gamma_ceiling),
        inline=True,
    )
    embed.add_field(
        name="Gamma Floor (support)",
        value=_fmt_price(gex.gamma_floor),
        inline=True,
    )
    embed.add_field(
        name="Spot Price",
        value=_fmt_price(result.spot_price),
        inline=True,
    )

    embed.set_footer(text=f"SPY Options Employee | {result.ticker}")
    return embed


def build_max_pain_embed(result: AnalysisResult) -> discord.Embed:
    """Build a rich embed for Max Pain analysis.

    Args:
        result: Full analysis result.

    Returns:
        Discord Embed with max pain fields.
    """
    mp = result.max_pain
    # Color based on distance: green if price is near max pain, red if far
    abs_dist = abs(mp.distance_pct)
    if abs_dist < 0.5:
        color = COLOR_NEUTRAL
    elif mp.distance_pct > 0:
        color = COLOR_BULLISH  # price above max pain
    else:
        color = COLOR_BEARISH  # price below max pain

    embed = discord.Embed(
        title=f"Max Pain Analysis -- {result.ticker}",
        description="Price where total option writer payout is minimized",
        color=color,
        timestamp=result.timestamp,
    )

    embed.add_field(
        name="Max Pain Price",
        value=_fmt_price(mp.max_pain_price),
        inline=True,
    )
    embed.add_field(
        name="Current Price",
        value=_fmt_price(mp.current_price),
        inline=True,
    )
    embed.add_field(
        name="Distance",
        value=f"{mp.distance_pct:+.2f}%",
        inline=True,
    )
    embed.add_field(
        name="Expiry",
        value=str(mp.expiry),
        inline=True,
    )
    embed.add_field(
        name="Total Pain at Max",
        value=_fmt_number(mp.total_pain_at_max),
        inline=True,
    )

    # Add interpretation
    if abs_dist < 0.5:
        interp = "Price is converging on max pain -- expiry magnet effect likely"
    elif mp.distance_pct > 0:
        interp = "Price is ABOVE max pain -- gravitational pull downward toward expiry"
    else:
        interp = "Price is BELOW max pain -- gravitational pull upward toward expiry"

    embed.add_field(
        name="Interpretation",
        value=interp,
        inline=False,
    )

    embed.set_footer(text=f"SPY Options Employee | {result.ticker}")
    return embed


def build_pcr_embed(result: AnalysisResult) -> discord.Embed:
    """Build a rich embed for Put/Call Ratio analysis.

    Args:
        result: Full analysis result.

    Returns:
        Discord Embed with PCR fields.
    """
    pcr = result.pcr
    color = _signal_color(pcr.signal)

    embed = discord.Embed(
        title=f"Put/Call Ratio -- {result.ticker}",
        description=f"Signal: {_signal_emoji(pcr.signal)}  |  Dealer: {_dealer_text(pcr.dealer_positioning)}",
        color=color,
        timestamp=result.timestamp,
    )

    embed.add_field(
        name="Volume PCR",
        value=f"{pcr.volume_pcr:.3f}",
        inline=True,
    )
    embed.add_field(
        name="OI PCR",
        value=f"{pcr.oi_pcr:.3f}",
        inline=True,
    )
    embed.add_field(
        name="Signal",
        value=pcr.signal.replace("_", " ").title(),
        inline=True,
    )
    embed.add_field(
        name="Call Volume",
        value=_fmt_int(pcr.total_call_volume),
        inline=True,
    )
    embed.add_field(
        name="Put Volume",
        value=_fmt_int(pcr.total_put_volume),
        inline=True,
    )
    embed.add_field(
        name="Vol Ratio",
        value=f"P:{pcr.total_put_volume} / C:{pcr.total_call_volume}",
        inline=True,
    )
    embed.add_field(
        name="Call OI",
        value=_fmt_int(pcr.total_call_oi),
        inline=True,
    )
    embed.add_field(
        name="Put OI",
        value=_fmt_int(pcr.total_put_oi),
        inline=True,
    )
    embed.add_field(
        name="Dealer Positioning",
        value=pcr.dealer_positioning.replace("_", " ").title(),
        inline=True,
    )

    embed.set_footer(text=f"SPY Options Employee | {result.ticker}")
    return embed


def build_levels_embed(result: AnalysisResult) -> discord.Embed:
    """Build a rich embed for combined key levels.

    Args:
        result: Full analysis result.

    Returns:
        Discord Embed with key level fields.
    """
    si = result.strike_intel
    embed = discord.Embed(
        title=f"Key Price Levels -- {result.ticker}",
        description=f"Spot: {_fmt_price(result.spot_price)} | {len(si.key_levels)} levels identified",
        color=COLOR_INFO,
        timestamp=result.timestamp,
    )

    if not si.key_levels:
        embed.add_field(name="No Levels", value="No key levels identified", inline=False)
        return embed

    # Group levels by type for cleaner display
    level_type_labels = {
        "gamma_flip": "Gamma Flip",
        "gamma_ceiling": "Gamma Ceiling",
        "gamma_floor": "Gamma Floor",
        "max_pain": "Max Pain",
        "high_oi_call": "High OI Call",
        "high_oi_put": "High OI Put",
    }

    # Show top 12 levels to stay within embed limits
    for level in si.key_levels[:12]:
        label = level_type_labels.get(level.level_type, level.level_type)
        sig_bar = "=" * int(level.significance * 10)
        embed.add_field(
            name=f"{label} -- {_fmt_price(level.price)}",
            value=f"Significance: {level.significance:.2f} [{sig_bar}]",
            inline=True,
        )

    embed.set_footer(text=f"SPY Options Employee | {result.ticker}")
    return embed


def build_strikes_embed(result: AnalysisResult) -> discord.Embed:
    """Build a rich embed for optimal strike recommendations.

    Args:
        result: Full analysis result.

    Returns:
        Discord Embed with strike recommendation fields.
    """
    si = result.strike_intel
    color = COLOR_INFO

    embed = discord.Embed(
        title=f"Optimal Strikes -- {result.ticker}",
        description=f"Spot: {_fmt_price(result.spot_price)} | GEX-aligned strike recommendations",
        color=color,
        timestamp=result.timestamp,
    )

    # Calls section
    if si.optimal_calls:
        call_lines: list[str] = []
        for rec in si.optimal_calls[:5]:
            gex_tag = "[GEX OK]" if rec.gex_support == "aligned" else "[GEX WARN]"
            call_lines.append(
                f"**{_fmt_price(rec.strike)}** {rec.expiry} | "
                f"P(ITM) {rec.probability_itm:.1%} | "
                f"P(OTM) {rec.probability_otm:.1%} | {gex_tag}"
            )
        embed.add_field(
            name="Optimal Calls (bullish)",
            value="\n".join(call_lines) if call_lines else "No recommendations",
            inline=False,
        )
    else:
        embed.add_field(name="Optimal Calls", value="No recommendations", inline=False)

    # Puts section
    if si.optimal_puts:
        put_lines: list[str] = []
        for rec in si.optimal_puts[:5]:
            gex_tag = "[GEX OK]" if rec.gex_support == "aligned" else "[GEX WARN]"
            put_lines.append(
                f"**{_fmt_price(rec.strike)}** {rec.expiry} | "
                f"P(ITM) {rec.probability_itm:.1%} | "
                f"P(OTM) {rec.probability_otm:.1%} | {gex_tag}"
            )
        embed.add_field(
            name="Optimal Puts (bearish)",
            value="\n".join(put_lines) if put_lines else "No recommendations",
            inline=False,
        )
    else:
        embed.add_field(name="Optimal Puts", value="No recommendations", inline=False)

    embed.set_footer(text=f"SPY Options Employee | {result.ticker}")
    return embed


def build_status_embed(
    last_update: datetime | None,
    data_sources: dict[str, bool],
    tickers_tracked: list[str],
) -> discord.Embed:
    """Build a status/health embed.

    Args:
        last_update: Timestamp of the last successful analysis cycle.
        data_sources: Dict mapping source name to health status (True = healthy).
        tickers_tracked: List of tickers being tracked.

    Returns:
        Discord Embed with status fields.
    """
    all_healthy = all(data_sources.values()) if data_sources else False
    color = COLOR_BULLISH if all_healthy else COLOR_NEUTRAL if data_sources else COLOR_BEARISH

    embed = discord.Embed(
        title="SPY Options Employee -- Status",
        description="System health and data source status",
        color=color,
        timestamp=datetime.utcnow(),
    )

    embed.add_field(
        name="Last Update",
        value=last_update.strftime("%Y-%m-%d %H:%M:%S ET") if last_update else "Never",
        inline=True,
    )
    embed.add_field(
        name="Tickers",
        value=", ".join(tickers_tracked) if tickers_tracked else "None",
        inline=True,
    )

    # Data source health
    source_lines: list[str] = []
    for source, healthy in data_sources.items():
        status = "[OK]" if healthy else "[DOWN]"
        source_lines.append(f"{status} {source}")

    embed.add_field(
        name="Data Sources",
        value="\n".join(source_lines) if source_lines else "No sources configured",
        inline=False,
    )

    embed.set_footer(text="SPY Options Employee")
    return embed


def build_dashboard_embed(
    results: dict[str, AnalysisResult],
    commentary: str = "",
) -> discord.Embed:
    """Build a compact dashboard embed for the scheduled update cycle.

    This is the periodic update posted to the analysis channel during market hours.

    Args:
        results: Dict mapping ticker to AnalysisResult.
        commentary: Optional AI-generated commentary string.

    Returns:
        Discord Embed with a compact multi-ticker summary.
    """
    embed = discord.Embed(
        title="Market Dashboard Update",
        color=COLOR_INFO,
        timestamp=datetime.utcnow(),
    )

    if commentary:
        embed.description = commentary

    for ticker, result in results.items():
        gex = result.gex
        mp = result.max_pain
        pcr = result.pcr

        gex_direction = "+" if gex.net_gex > 0 else ""
        flip_str = _fmt_price(gex.gamma_flip) if gex.gamma_flip is not None else "N/A"

        summary = (
            f"**Spot:** {_fmt_price(result.spot_price)}\n"
            f"**GEX:** {gex_direction}{_fmt_number(gex.net_gex)} | "
            f"Flip: {flip_str}\n"
            f"**Max Pain:** {_fmt_price(mp.max_pain_price)} ({mp.distance_pct:+.2f}%)\n"
            f"**PCR:** {pcr.volume_pcr:.3f} ({pcr.signal.replace('_', ' ').title()}) | "
            f"Dealer: {pcr.dealer_positioning.replace('_', ' ').title()}\n"
            f"**Squeeze:** {gex.squeeze_probability:.0%} | "
            f"Ceiling: {_fmt_price(gex.gamma_ceiling)} | "
            f"Floor: {_fmt_price(gex.gamma_floor)}"
        )

        embed.add_field(name=ticker, value=summary, inline=False)

    embed.set_footer(text="SPY Options Employee | Auto-update")
    return embed


def build_full_analysis_embed(result: AnalysisResult, commentary: str = "") -> list[discord.Embed]:
    """Build a list of embeds for a full analysis (/analyze command).

    Returns all embed types in a single list for sending as a batch.

    Args:
        result: Full analysis result for a single ticker.
        commentary: Optional AI-generated commentary string.

    Returns:
        List of Discord Embeds covering GEX, max pain, PCR, levels, and strikes.
    """
    embeds: list[discord.Embed] = []

    # Header embed with commentary
    header = discord.Embed(
        title=f"Full Analysis -- {result.ticker}",
        description=commentary if commentary else f"Complete options analysis for {result.ticker} at {_fmt_price(result.spot_price)}",
        color=COLOR_INFO,
        timestamp=result.timestamp,
    )
    header.set_footer(text="SPY Options Employee")
    embeds.append(header)

    embeds.append(build_gex_embed(result))
    embeds.append(build_max_pain_embed(result))
    embeds.append(build_pcr_embed(result))
    embeds.append(build_levels_embed(result))
    embeds.append(build_strikes_embed(result))

    return embeds


def build_alert_embed(
    alert_type: str,
    ticker: str,
    title: str,
    description: str,
    fields: dict[str, str],
    color: int | None = None,
) -> discord.Embed:
    """Build a generic alert embed.

    Args:
        alert_type: Type of alert (e.g., "gamma_flip", "squeeze", "max_pain_convergence").
        ticker: The ticker symbol.
        title: Alert title.
        description: Alert description.
        fields: Dict of field_name -> field_value for inline fields.
        color: Optional override color. Defaults to red (alert).

    Returns:
        Discord Embed for the alert.
    """
    if color is None:
        color = COLOR_BEARISH

    embed = discord.Embed(
        title=f"ALERT: {title}",
        description=description,
        color=color,
        timestamp=datetime.utcnow(),
    )

    for name, value in fields.items():
        embed.add_field(name=name, value=value, inline=True)

    embed.set_footer(text=f"SPY Options Employee | {alert_type} | {ticker}")
    return embed


# -- TradingView webhook embeds ------------------------------------------------


def build_tradingview_alert_embed(alert: "TradingViewAlert") -> discord.Embed:
    """Build a formatted embed for a TradingView webhook alert.

    Color-codes by action type:
        - Green for bullish (buy_call, long, bullish)
        - Red for bearish (buy_put, short, bearish)
        - Blue for neutral/informational

    Args:
        alert: Parsed TradingViewAlert from the webhook endpoint.

    Returns:
        Discord Embed with alert details.
    """
    from src.webhook.tradingview import TradingViewAlert  # noqa: F811

    action_lower = alert.action.lower()
    bullish_keywords = {"buy_call", "long", "bullish", "buy"}
    bearish_keywords = {"buy_put", "short", "bearish", "sell"}

    if action_lower in bullish_keywords:
        color = COLOR_BULLISH
    elif action_lower in bearish_keywords:
        color = COLOR_BEARISH
    else:
        color = COLOR_INFO

    embed = discord.Embed(
        title=f"TradingView Alert -- {alert.ticker}",
        description=alert.message or f"Action: **{alert.action}**",
        color=color,
        timestamp=datetime.utcnow(),
    )

    embed.add_field(name="Action", value=alert.action, inline=True)
    embed.add_field(name="Ticker", value=alert.ticker, inline=True)

    if alert.price is not None:
        embed.add_field(name="Price", value=_fmt_price(alert.price), inline=True)
    if alert.time is not None:
        embed.add_field(name="Time", value=alert.time, inline=True)
    if alert.interval is not None:
        embed.add_field(name="Interval", value=alert.interval, inline=True)
    if alert.volume is not None:
        embed.add_field(name="Volume", value=_fmt_number(alert.volume, 0), inline=True)
    if alert.strategy is not None:
        embed.add_field(name="Strategy", value=alert.strategy, inline=True)

    embed.set_footer(text="SPY Options Employee | TradingView")
    return embed


# -- CheddarFlow embeds --------------------------------------------------------


def build_flow_alert_embed(flow: dict) -> discord.Embed:
    """Build a formatted embed for a parsed CheddarFlow entry.

    Color-codes:
        - Green for calls
        - Red for puts
        - Yellow for sweeps

    Args:
        flow: Dict with keys: ticker, strike, expiry, premium, volume,
              order_type, side, is_sweep, spot_price.

    Returns:
        Discord Embed with flow data.
    """
    side = flow.get("side", "").upper()
    is_sweep = flow.get("is_sweep", False)

    if is_sweep:
        color = COLOR_NEUTRAL  # yellow for sweeps
    elif side == "CALL":
        color = COLOR_BULLISH
    elif side == "PUT":
        color = COLOR_BEARISH
    else:
        color = COLOR_INFO

    sweep_tag = " [SWEEP]" if is_sweep else ""
    embed = discord.Embed(
        title=f"Flow Alert -- {flow.get('ticker', '???')}{sweep_tag}",
        description=f"{side} {flow.get('strike', '?')} {flow.get('expiry', '?')}",
        color=color,
        timestamp=datetime.utcnow(),
    )

    if flow.get("premium") is not None:
        embed.add_field(name="Premium", value=_fmt_number(flow["premium"]), inline=True)
    if flow.get("volume") is not None:
        embed.add_field(name="Volume", value=_fmt_int(int(flow["volume"])), inline=True)
    if flow.get("order_type"):
        embed.add_field(name="Order Type", value=flow["order_type"], inline=True)
    if flow.get("strike") is not None:
        embed.add_field(name="Strike", value=_fmt_price(float(flow["strike"])), inline=True)
    if flow.get("expiry"):
        embed.add_field(name="Expiry", value=flow["expiry"], inline=True)
    if flow.get("spot_price") is not None:
        embed.add_field(name="Spot", value=_fmt_price(float(flow["spot_price"])), inline=True)

    embed.set_footer(text="SPY Options Employee | CheddarFlow")
    return embed
