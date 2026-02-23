"""Discord embed builders for SPY/SPX options analysis.

Builds rich embeds with color coding:
    - Green (#00ff00) for bullish signals
    - Red (#ff0000) for bearish signals
    - Yellow (#ffff00) for neutral/caution
    - Blue (#0099ff) for informational
"""

import logging
from datetime import datetime, timezone

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
        timestamp=datetime.now(timezone.utc),
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
        timestamp=datetime.now(timezone.utc),
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
        timestamp=datetime.now(timezone.utc),
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
        timestamp=datetime.now(timezone.utc),
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
        timestamp=datetime.now(timezone.utc),
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


# -- Strategy management embeds ------------------------------------------------


def build_strategy_define_embed(
    template: "StrategyTemplate",
    explanation: str,
    strategy_id: int | None = None,
) -> discord.Embed:
    """Build an embed showing a parsed strategy for confirmation.

    Args:
        template: The parsed StrategyTemplate.
        explanation: Claude's explanation of what it understood.
        strategy_id: Optional DB ID if already saved.

    Returns:
        Discord Embed with strategy summary.
    """
    from src.strategy.schema import StrategyTemplate  # noqa: F811

    color = COLOR_INFO
    title = f"Strategy Defined -- {template.name}"
    if strategy_id is not None:
        title += f" (#{strategy_id})"

    embed = discord.Embed(
        title=title,
        description=explanation if explanation else template.description,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    # Structure
    structure = template.structure
    legs_str = ""
    for leg in structure.legs:
        action = leg.action.value.upper()
        side = leg.side.value.upper()
        delta = f"{leg.delta_value:.0%}" if leg.delta_value else "ATM"
        legs_str += f"  {action} {delta} {side}\n"

    embed.add_field(
        name="Structure",
        value=(
            f"**Type:** {structure.strategy_type.value.replace('_', ' ').title()}\n"
            f"**DTE:** {structure.dte_min}-{structure.dte_max} (target {structure.dte_target})\n"
            f"**Legs:**\n{legs_str}"
        ),
        inline=False,
    )

    # Entry rules
    entry = template.entry
    entry_parts = []
    if entry.iv_rank_min > 0:
        entry_parts.append(f"IV Rank >= {entry.iv_rank_min:.0f}")
    if entry.iv_rank_max < 100:
        entry_parts.append(f"IV Rank <= {entry.iv_rank_max:.0f}")
    if entry.vix_min > 0:
        entry_parts.append(f"VIX >= {entry.vix_min:.1f}")
    if entry.vix_max < 100:
        entry_parts.append(f"VIX <= {entry.vix_max:.1f}")

    embed.add_field(
        name="Entry",
        value="\n".join(entry_parts) if entry_parts else "No filters",
        inline=True,
    )

    # Exit rules
    exit_rule = template.exit
    embed.add_field(
        name="Exit",
        value=(
            f"Profit: {exit_rule.profit_target_pct:.0%}\n"
            f"Stop: {exit_rule.stop_loss_pct:.0f}x\n"
            f"DTE Close: {exit_rule.dte_close}"
        ),
        inline=True,
    )

    embed.add_field(
        name="Ticker",
        value=template.ticker,
        inline=True,
    )

    embed.set_footer(text="SPY Options Employee | Strategy")
    return embed


def build_strategy_list_embed(
    strategies: list[dict],
    status_filter: "StrategyStatus | None" = None,
) -> discord.Embed:
    """Build an embed listing strategies with status indicators.

    Args:
        strategies: List of strategy dicts from StrategyManager.
        status_filter: Optional status filter that was applied.

    Returns:
        Discord Embed with strategy table.
    """
    filter_text = f" ({status_filter.value})" if status_filter else ""
    embed = discord.Embed(
        title=f"Strategies{filter_text}",
        description=f"{len(strategies)} strategies found",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    if not strategies:
        embed.add_field(name="None", value="No strategies found.", inline=False)
        return embed

    STATUS_ICONS = {
        "idea": "[IDEA]",
        "defined": "[DEF]",
        "backtest": "[BT]",
        "paper": "[PAPER]",
        "live": "[LIVE]",
        "retired": "[RET]",
    }

    for s in strategies[:20]:  # Discord embed limit
        icon = STATUS_ICONS.get(s["status"], "[?]")
        created = s.get("created_at", "")[:10]
        embed.add_field(
            name=f"#{s['id']} {icon} {s['name']}",
            value=f"Status: {s['status'].title()} | Created: {created}",
            inline=False,
        )

    if len(strategies) > 20:
        embed.set_footer(text=f"Showing 20 of {len(strategies)} | SPY Options Employee")
    else:
        embed.set_footer(text="SPY Options Employee | Strategy")

    return embed


def build_strategy_detail_embed(
    strategy: dict,
    history: list[dict] | None = None,
) -> discord.Embed:
    """Build a detailed embed for a single strategy.

    Args:
        strategy: Strategy dict from StrategyManager.
        history: Optional transition history.

    Returns:
        Discord Embed with full strategy details.
    """
    STATUS_COLORS = {
        "idea": COLOR_INFO,
        "defined": COLOR_INFO,
        "backtest": COLOR_NEUTRAL,
        "paper": COLOR_NEUTRAL,
        "live": COLOR_BULLISH,
        "retired": COLOR_BEARISH,
    }

    color = STATUS_COLORS.get(strategy["status"], COLOR_INFO)

    embed = discord.Embed(
        title=f"Strategy #{strategy['id']} -- {strategy['name']}",
        description=f"Status: **{strategy['status'].title()}**",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    # Show YAML snippet (truncated for Discord)
    yaml_str = strategy.get("template_yaml", "")
    if yaml_str:
        truncated = yaml_str[:800]
        if len(yaml_str) > 800:
            truncated += "\n... (truncated)"
        embed.add_field(
            name="Template YAML",
            value=f"```yaml\n{truncated}\n```",
            inline=False,
        )

    # Metadata
    embed.add_field(
        name="Created",
        value=strategy.get("created_at", "N/A")[:19],
        inline=True,
    )
    embed.add_field(
        name="Updated",
        value=strategy.get("updated_at", "N/A")[:19],
        inline=True,
    )

    # Transition history
    if history:
        hist_lines = []
        for h in history[-5:]:  # Last 5 transitions
            ts = h.get("transitioned_at", "")[:10]
            reason = h.get("reason", "")
            hist_lines.append(
                f"`{ts}` {h['from_status']} -> {h['to_status']}"
                + (f" ({reason})" if reason else "")
            )
        embed.add_field(
            name="History",
            value="\n".join(hist_lines) if hist_lines else "No transitions",
            inline=False,
        )

    embed.set_footer(text="SPY Options Employee | Strategy")
    return embed


def build_backtest_result_embed(
    result: dict,
    strategy_name: str,
) -> discord.Embed:
    """Build an embed showing backtest/evaluation results with gate indicators.

    Color coding:
        - Green: all gates passed (PROMOTE)
        - Yellow: 3/4 passed (REFINE)
        - Red: <=2/4 passed (REJECT)

    Args:
        result: Dict from backtest_results table row.
        strategy_name: Strategy name for the title.

    Returns:
        Discord Embed with metrics and gate results.
    """
    recommendation = result.get("recommendation", "UNKNOWN")
    if recommendation == "PROMOTE":
        color = COLOR_BULLISH
    elif recommendation == "REFINE":
        color = COLOR_NEUTRAL
    else:
        color = COLOR_BEARISH

    all_passed = bool(result.get("all_passed", 0))

    embed = discord.Embed(
        title=f"Backtest Results -- {strategy_name}",
        description=f"Recommendation: **{recommendation}**",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    # Key metrics
    embed.add_field(
        name="Trades",
        value=str(result.get("num_trades", 0)),
        inline=True,
    )
    embed.add_field(
        name="Sharpe",
        value=f"{result.get('sharpe', 0):.3f}",
        inline=True,
    )
    embed.add_field(
        name="Sortino",
        value=f"{result.get('sortino', 0):.3f}",
        inline=True,
    )
    embed.add_field(
        name="Win Rate",
        value=f"{(result.get('win_rate', 0) or 0) * 100:.1f}%",
        inline=True,
    )
    embed.add_field(
        name="Max Drawdown",
        value=f"${result.get('max_drawdown', 0):,.2f}",
        inline=True,
    )
    embed.add_field(
        name="Profit Factor",
        value=f"{result.get('profit_factor', 0):.2f}",
        inline=True,
    )

    # Gate results
    def _gate(passed: int | bool) -> str:
        return "[PASS]" if passed else "[FAIL]"

    gates_text = (
        f"WFA: {_gate(result.get('wfa_passed', 0))}\n"
        f"CPCV: {_gate(result.get('cpcv_passed', 0))} (PBO: {result.get('cpcv_pbo', 0):.3f})\n"
        f"DSR: {_gate(result.get('dsr_passed', 0))} (DSR: {result.get('dsr', 0):.3f})\n"
        f"Monte Carlo: {_gate(result.get('mc_passed', 0))} (5th-pct Sharpe: {result.get('mc_5th_sharpe', 0):.3f})"
    )

    embed.add_field(
        name="Anti-Overfitting Gates",
        value=gates_text,
        inline=False,
    )

    embed.add_field(
        name="Period",
        value=f"{result.get('start_date', 'N/A')} to {result.get('end_date', 'N/A')}",
        inline=False,
    )

    embed.set_footer(text=f"SPY Options Employee | Run: {result.get('run_at', 'N/A')[:19]}")
    return embed


def build_backtest_progress_embed(
    strategy_name: str,
    status_message: str,
) -> discord.Embed:
    """Build a progress embed for long-running backtests.

    Args:
        strategy_name: Name of the strategy being backtested.
        status_message: Current progress status.

    Returns:
        Discord Embed with progress info.
    """
    embed = discord.Embed(
        title=f"Backtest In Progress -- {strategy_name}",
        description=status_message,
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="SPY Options Employee | Backtest")
    return embed


# -- Journal embeds -----------------------------------------------------------


def build_daily_summary_embed(
    date: "date_type",
    signal_stats: dict,
    strategy_summary: list[dict],
    rating_stats: dict,
) -> discord.Embed:
    """Build a daily trading journal summary embed.

    Args:
        date: The date for the summary.
        signal_stats: Signal statistics from SignalLogger.get_signal_stats().
        strategy_summary: List of strategy dicts.
        rating_stats: Rating stats dict with count and avg_rating.

    Returns:
        Discord Embed with daily summary.
    """
    from datetime import date as date_type  # noqa: F811

    embed = discord.Embed(
        title=f"Daily Journal -- {date}",
        description="End-of-day trading summary",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    # Signals
    total = signal_stats.get("total_signals", 0)
    by_type = signal_stats.get("by_type", {})
    by_dir = signal_stats.get("by_direction", {})
    outcomes = signal_stats.get("outcome_counts", {})

    signals_text = f"**Total:** {total}\n"
    if by_type:
        type_parts = [f"{t}: {c}" for t, c in sorted(by_type.items())]
        signals_text += f"**By Type:** {', '.join(type_parts)}\n"
    if by_dir:
        dir_parts = [f"{d}: {c}" for d, c in sorted(by_dir.items())]
        signals_text += f"**By Direction:** {', '.join(dir_parts)}\n"
    if outcomes:
        out_parts = [f"{o}: {c}" for o, c in sorted(outcomes.items())]
        signals_text += f"**Outcomes:** {', '.join(out_parts)}"

    embed.add_field(name="Signals", value=signals_text or "No signals", inline=False)

    # Strategies
    active = [s for s in strategy_summary if s.get("status") not in ("retired",)]
    if active:
        strat_lines = []
        for s in active[:5]:
            strat_lines.append(f"#{s['id']} {s['name']} ({s['status']})")
        embed.add_field(
            name=f"Active Strategies ({len(active)})",
            value="\n".join(strat_lines),
            inline=False,
        )
    else:
        embed.add_field(name="Strategies", value="None active", inline=False)

    # Ratings
    if rating_stats.get("count", 0) > 0:
        embed.add_field(
            name="Ratings Today",
            value=f"{rating_stats['count']} ratings, avg {rating_stats['avg_rating']:.1f}/5",
            inline=True,
        )

    embed.set_footer(text="SPY Options Employee | Journal")
    return embed


def build_weekly_review_embed(
    start_date: "date_type",
    end_date: "date_type",
    signal_stats: dict,
    strategy_summary: list[dict],
    rating_stats: dict,
) -> discord.Embed:
    """Build a weekly trading review embed.

    Args:
        start_date: Start of the review period.
        end_date: End of the review period.
        signal_stats: Aggregated signal stats for the week.
        strategy_summary: Current strategy statuses.
        rating_stats: Aggregated rating stats for the week.

    Returns:
        Discord Embed with weekly review.
    """
    from datetime import date as date_type  # noqa: F811

    embed = discord.Embed(
        title=f"Weekly Review -- {start_date} to {end_date}",
        description="Weekly trading performance summary",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    # Signals section
    total = signal_stats.get("total_signals", 0)
    outcomes = signal_stats.get("outcome_counts", {})

    wins = outcomes.get("win", 0)
    total_outcomes = sum(outcomes.values()) if outcomes else 0
    hit_rate = wins / total_outcomes if total_outcomes > 0 else 0

    embed.add_field(
        name="Signal Summary",
        value=(
            f"**Total Signals:** {total}\n"
            f"**With Outcomes:** {total_outcomes}\n"
            f"**Hit Rate:** {hit_rate:.1%}"
        ),
        inline=True,
    )

    # Strategy performance
    status_counts: dict[str, int] = {}
    for s in strategy_summary:
        st = s.get("status", "unknown")
        status_counts[st] = status_counts.get(st, 0) + 1

    strat_text = "\n".join(f"{k.title()}: {v}" for k, v in sorted(status_counts.items()))
    embed.add_field(
        name="Strategy Status",
        value=strat_text or "No strategies",
        inline=True,
    )

    # Ratings
    if rating_stats.get("count", 0) > 0:
        embed.add_field(
            name="Borey's Ratings",
            value=f"{rating_stats['count']} ratings, avg {rating_stats['avg_rating']:.1f}/5",
            inline=True,
        )

    embed.set_footer(text="SPY Options Employee | Journal")
    return embed


def build_rating_confirmation_embed(
    signal_id: int,
    rating: int,
    notes: str = "",
) -> discord.Embed:
    """Build a confirmation embed for a signal rating.

    Args:
        signal_id: The signal log ID that was rated.
        rating: The rating value (1-5).
        notes: Optional notes.

    Returns:
        Discord Embed confirming the rating.
    """
    stars = "+" * rating + "-" * (5 - rating)

    embed = discord.Embed(
        title=f"Signal #{signal_id} Rated",
        description=f"Rating: **{stars}** ({rating}/5)",
        color=COLOR_BULLISH if rating >= 4 else COLOR_NEUTRAL if rating >= 3 else COLOR_BEARISH,
        timestamp=datetime.now(timezone.utc),
    )

    if notes:
        embed.add_field(name="Notes", value=notes, inline=False)

    embed.set_footer(text="SPY Options Employee | Journal")
    return embed


# -- ML Intelligence Layer embeds (Phase 3) -----------------------------------


# Regime state color mapping
_REGIME_COLORS: dict[str, int] = {
    "risk-on": COLOR_BULLISH,
    "risk-off": COLOR_NEUTRAL,
    "crisis": COLOR_BEARISH,
}


def build_regime_embed(regime_data: dict) -> discord.Embed:
    """Build an embed for the current market regime state.

    Args:
        regime_data: Dict with ``state_name``, ``regime_probability``,
            and optionally ``expected_duration`` and ``transition_matrix``.

    Returns:
        Discord Embed with regime state info.
    """
    state_name = regime_data.get("state_name", "unknown")
    probability = regime_data.get("regime_probability", 0.0)
    color = _REGIME_COLORS.get(state_name, COLOR_INFO)

    embed = discord.Embed(
        title="Market Regime",
        description=f"Current regime: **{state_name.upper()}**",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    embed.add_field(
        name="State",
        value=state_name.replace("-", " ").title(),
        inline=True,
    )
    embed.add_field(
        name="Probability",
        value=f"{probability:.1%}",
        inline=True,
    )

    # Expected duration (if available from predict())
    expected_duration = regime_data.get("expected_duration", {})
    if expected_duration:
        dur_lines = [f"{k}: {v:.1f} days" for k, v in expected_duration.items()]
        embed.add_field(
            name="Expected Duration",
            value="\n".join(dur_lines),
            inline=False,
        )

    # Transition matrix summary
    transmat = regime_data.get("transition_matrix")
    if transmat is not None:
        try:
            import numpy as np
            mat = np.array(transmat)
            mat_lines = []
            n = mat.shape[0]
            state_labels = ["risk-on", "risk-off", "crisis"][:n]
            for i, row_label in enumerate(state_labels):
                probs = " ".join(f"{mat[i, j]:.2f}" for j in range(n))
                mat_lines.append(f"{row_label}: [{probs}]")
            embed.add_field(
                name="Transition Probabilities",
                value="```\n" + "\n".join(mat_lines) + "\n```",
                inline=False,
            )
        except Exception:
            pass

    embed.set_footer(text="SPY Options Employee | Regime")
    return embed


def build_forecast_embed(forecast: dict, features: dict | None = None) -> discord.Embed:
    """Build an embed for volatility forecast data.

    Args:
        forecast: Dict with ``vol_forecast_1d``, ``vol_forecast_5d``.
        features: Optional dict with ``iv_rank``, ``rv_iv_spread``, ``hurst_exponent``.

    Returns:
        Discord Embed with vol forecast and interpretation.
    """
    vol_1d = forecast.get("vol_forecast_1d", 0.0)
    vol_5d = forecast.get("vol_forecast_5d", 0.0)

    # Color based on vol level
    if vol_1d is not None and vol_1d > 0.25:
        color = COLOR_BEARISH  # High vol
    elif vol_1d is not None and vol_1d > 0.15:
        color = COLOR_NEUTRAL
    else:
        color = COLOR_BULLISH

    embed = discord.Embed(
        title="Volatility Forecast",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    embed.add_field(
        name="1-Day Forecast",
        value=f"{vol_1d:.4f}" if vol_1d is not None else "N/A",
        inline=True,
    )
    embed.add_field(
        name="5-Day Forecast",
        value=f"{vol_5d:.4f}" if vol_5d is not None else "N/A",
        inline=True,
    )

    # Additional features if available
    if features:
        iv_rank = features.get("iv_rank")
        rv_iv_spread = features.get("rv_iv_spread")
        hurst = features.get("hurst_exponent")

        if iv_rank is not None:
            embed.add_field(name="IV Rank", value=f"{iv_rank:.1f}", inline=True)
        if rv_iv_spread is not None:
            embed.add_field(
                name="RV/IV Spread",
                value=f"{rv_iv_spread:.4f}",
                inline=True,
            )
        if hurst is not None:
            embed.add_field(name="Hurst Exponent", value=f"{hurst:.3f}", inline=True)

    # Interpretation
    if iv_rank is not None if features else False:
        iv_r = features["iv_rank"]
        if rv_iv_spread is not None:
            spread = features["rv_iv_spread"]
            if spread < -0.02:
                pricing = "overpriced"
            elif spread > 0.02:
                pricing = "underpriced"
            else:
                pricing = "fair"
        else:
            pricing = "unknown"

        if iv_r > 50:
            timing = "favorable"
        else:
            timing = "unfavorable"

        embed.add_field(
            name="Interpretation",
            value=f"Vol is **{pricing}**. Entry timing **{timing}** for premium selling.",
            inline=False,
        )

    embed.set_footer(text="SPY Options Employee | Volatility")
    return embed


def build_sentiment_embed(sentiment: dict) -> discord.Embed:
    """Build an embed for market sentiment data.

    Args:
        sentiment: Dict with ``sentiment_score`` and optionally
            ``velocity``, ``positive_pct``, ``negative_pct``, ``neutral_pct``,
            ``volume_pcr``.

    Returns:
        Discord Embed with sentiment breakdown.
    """
    score = sentiment.get("sentiment_score", 0.0)

    if score > 0.3:
        color = COLOR_BULLISH
    elif score < -0.3:
        color = COLOR_BEARISH
    else:
        color = COLOR_NEUTRAL

    embed = discord.Embed(
        title="Market Sentiment",
        description=f"Composite score: **{score:+.3f}**",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    embed.add_field(
        name="Sentiment Score",
        value=f"{score:+.3f} (range: -1 to +1)",
        inline=True,
    )

    velocity = sentiment.get("velocity", 0.0)
    if velocity is not None:
        direction = "accelerating" if velocity > 0 else "decelerating" if velocity < 0 else "flat"
        embed.add_field(
            name="Velocity",
            value=f"{velocity:+.3f} ({direction})",
            inline=True,
        )

    # Breakdown percentages
    pos = sentiment.get("positive_pct")
    neg = sentiment.get("negative_pct")
    neu = sentiment.get("neutral_pct")
    if pos is not None:
        embed.add_field(
            name="Breakdown",
            value=f"Positive: {pos:.0%}\nNegative: {neg:.0%}\nNeutral: {neu:.0%}",
            inline=True,
        )

    # Contrarian signal
    pcr = sentiment.get("volume_pcr", 0.0)
    if abs(score) > 0.6 and pcr is not None and pcr > 1.2:
        embed.add_field(
            name="CONTRARIAN SIGNAL",
            value="Extreme sentiment + high PCR detected. Contrarian reversal may be imminent.",
            inline=False,
        )

    embed.set_footer(text="SPY Options Employee | Sentiment")
    return embed


def build_anomaly_embed(report: "AnomalyReport") -> discord.Embed:
    """Build an embed for anomaly detection results.

    Args:
        report: An :class:`AnomalyReport` dataclass instance.

    Returns:
        Discord Embed with anomaly flags and score.
    """
    score = report.overall_score

    if score < 0.4:
        color = COLOR_BULLISH
        level = "LOW"
    elif score < 0.7:
        color = COLOR_NEUTRAL
        level = "MEDIUM"
    else:
        color = COLOR_BEARISH
        level = "HIGH"

    embed = discord.Embed(
        title="Anomaly Detection Scan",
        description=f"Overall anomaly score: **{score:.3f}** [{level}]",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    embed.add_field(
        name="Overall Score",
        value=f"{score:.3f}",
        inline=True,
    )

    # Top anomaly flags
    anomaly_flags = []
    if report.volume_anomalies:
        for a in report.volume_anomalies[:3]:
            anomaly_flags.append(f"Volume: z={a.get('z_score', 0):.1f}")
    if report.iv_anomalies:
        for a in report.iv_anomalies[:3]:
            anomaly_flags.append(f"IV: z={a.get('z_score', 0):.1f}")
    if report.voi_anomalies:
        for a in report.voi_anomalies[:2]:
            anomaly_flags.append(f"V/OI: z={a.get('z_score', 0):.1f}")

    embed.add_field(
        name="Top Anomaly Flags",
        value="\n".join(anomaly_flags) if anomaly_flags else "No anomalies detected",
        inline=False,
    )

    # Strike clusters
    if report.strike_clusters:
        cluster_lines = []
        for c in report.strike_clusters[:5]:
            strike = c.get("strike", "?")
            vol_pct = c.get("volume_share", 0)
            cluster_lines.append(f"${strike}: {vol_pct:.1%} of volume")
        embed.add_field(
            name="Top Strike Clusters",
            value="\n".join(cluster_lines),
            inline=False,
        )

    # Flow summary if available
    if report.flow_anomalies:
        flow_lines = []
        for f in report.flow_anomalies[:3]:
            flag_type = f.get("type", "unknown")
            detail = f.get("detail", "")
            flow_lines.append(f"[{flag_type.upper()}] {detail}")
        embed.add_field(
            name="Flow Signals",
            value="\n".join(flow_lines) if flow_lines else "No flow data",
            inline=False,
        )

    embed.set_footer(text="SPY Options Employee | Anomaly")
    return embed


def build_reasoning_embed(analysis: dict) -> discord.Embed:
    """Build an embed for Claude reasoning analysis results.

    Args:
        analysis: Structured analysis dict from ReasoningEngine with keys
            like ``summary``, ``regime_assessment``, ``vol_outlook``,
            ``signal_conflicts``, ``strategy_recommendations``, ``risk_warnings``.

    Returns:
        Discord Embed with reasoning analysis summary.
    """
    embed = discord.Embed(
        title="ML Reasoning Analysis",
        description=analysis.get("summary", "No summary available."),
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    regime_assessment = analysis.get("regime_assessment", "")
    if regime_assessment:
        embed.add_field(
            name="Regime Assessment",
            value=str(regime_assessment)[:1024],
            inline=False,
        )

    vol_outlook = analysis.get("vol_outlook", "")
    if vol_outlook:
        embed.add_field(
            name="Volatility Outlook",
            value=str(vol_outlook)[:1024],
            inline=False,
        )

    conflicts = analysis.get("signal_conflicts", [])
    if conflicts:
        if isinstance(conflicts, list):
            conflicts_text = "\n".join(f"- {c}" for c in conflicts[:5])
        else:
            conflicts_text = str(conflicts)[:1024]
        embed.add_field(
            name="Signal Conflicts",
            value=conflicts_text,
            inline=False,
        )

    recs = analysis.get("strategy_recommendations", [])
    if recs:
        if isinstance(recs, list):
            recs_text = "\n".join(f"- {r}" for r in recs[:5])
        else:
            recs_text = str(recs)[:1024]
        embed.add_field(
            name="Strategy Recommendations",
            value=recs_text,
            inline=False,
        )

    warnings = analysis.get("risk_warnings", [])
    if warnings:
        if isinstance(warnings, list):
            warnings_text = "\n".join(f"- {w}" for w in warnings[:5])
        else:
            warnings_text = str(warnings)[:1024]
        embed.add_field(
            name="Risk Warnings",
            value=warnings_text,
            inline=False,
        )

    embed.set_footer(text="SPY Options Employee | Reasoning (~$0.01-0.03)")
    return embed


def build_ml_health_embed(health: dict) -> discord.Embed:
    """Build an embed for ML model health dashboard.

    Args:
        health: Dict from LearningManager.get_model_health() with keys
            ``accuracy_7d``, ``accuracy_30d``, ``trend``, ``calibrators``.

    Returns:
        Discord Embed with model health metrics.
    """
    trend = health.get("trend", "unknown")
    if trend == "improving":
        color = COLOR_BULLISH
    elif trend == "degrading":
        color = COLOR_BEARISH
    elif trend == "stable":
        color = COLOR_NEUTRAL
    else:
        color = COLOR_INFO

    embed = discord.Embed(
        title="ML Model Health Dashboard",
        description=f"Overall trend: **{trend.upper()}**",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    # Accuracy metrics
    acc_7d = health.get("accuracy_7d", {})
    acc_30d = health.get("accuracy_30d", {})

    embed.add_field(
        name="7-Day Accuracy",
        value=(
            f"{acc_7d.get('accuracy', 0):.1%} ({acc_7d.get('total', 0)} signals)"
            if acc_7d.get("total", 0) > 0
            else "Insufficient data"
        ),
        inline=True,
    )
    embed.add_field(
        name="30-Day Accuracy",
        value=(
            f"{acc_30d.get('accuracy', 0):.1%} ({acc_30d.get('total', 0)} signals)"
            if acc_30d.get("total", 0) > 0
            else "Insufficient data"
        ),
        inline=True,
    )
    embed.add_field(name="Trend", value=trend.title(), inline=True)

    # Calibrator status
    calibrators = health.get("calibrators", {})
    if calibrators:
        cal_lines = []
        for signal_type, cal_data in calibrators.items():
            confidence = cal_data.get("confidence", 0)
            interval = cal_data.get("credible_interval", (0, 0))
            cal_lines.append(
                f"**{signal_type}**: {confidence:.1%} "
                f"[{interval[0]:.2f}-{interval[1]:.2f}]"
            )
        embed.add_field(
            name="Calibrated Confidence",
            value="\n".join(cal_lines) if cal_lines else "No calibrators",
            inline=False,
        )

    embed.set_footer(text="SPY Options Employee | ML Health")
    return embed
