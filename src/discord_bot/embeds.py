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


# -- Paper trading embeds (Phase 4, sub-plan 4-6) ----------------------------


def _build_option_desc(legs: list[dict]) -> str:
    """Build a compact option description from position legs for mobile-friendly display.

    Examples:
        "SPX Mar15 5100/5110 IC" (iron condor)
        "SPX Mar15 5050/5060 PS" (put spread)
        "SPX Mar15 5100C" (single call)

    Args:
        legs: List of leg dicts with keys: option_type, strike, expiry.

    Returns:
        Compact option description string.
    """
    if not legs:
        return "SPX (no legs)"

    # Extract unique expiry -- use shortest format
    expiries = set()
    for leg in legs:
        exp = leg.get("expiry", "")
        if isinstance(exp, str) and len(exp) >= 10:
            try:
                from datetime import datetime as _dt
                d = _dt.strptime(exp[:10], "%Y-%m-%d")
                expiries.add(d.strftime("%b%d"))
            except (ValueError, TypeError):
                expiries.add(str(exp)[:5])
        else:
            expiries.add(str(exp)[:5])

    expiry_str = sorted(expiries)[0] if expiries else ""

    # Collect all strikes sorted
    strikes = sorted(set(leg.get("strike", 0) for leg in legs))

    # Determine option types present
    option_types = set(leg.get("option_type", "").lower() for leg in legs)
    has_calls = "call" in option_types
    has_puts = "put" in option_types

    # Single leg
    if len(legs) == 1:
        leg = legs[0]
        side = "C" if leg.get("option_type", "").lower() == "call" else "P"
        return f"SPX {expiry_str} {int(strikes[0])}{side}"

    # Determine spread type abbreviation
    if len(legs) == 4 and has_calls and has_puts:
        spread_type = "IC"
    elif len(legs) == 3:
        spread_type = "BF"
    elif len(legs) == 2 and has_calls and not has_puts:
        spread_type = "CS"
    elif len(legs) == 2 and has_puts and not has_calls:
        spread_type = "PS"
    elif len(legs) == 2 and has_calls and has_puts:
        spread_type = "ST"  # strangle/straddle
    else:
        spread_type = f"{len(legs)}L"

    strike_str = "/".join(str(int(s)) for s in strikes)
    return f"SPX {expiry_str} {strike_str} {spread_type}"


def build_paper_status_embed(
    portfolio: "PortfolioSummary",
    positions: list[dict],
    todays_fills: list[dict],
) -> discord.Embed:
    """Build a paper trading status embed for /paper_status.

    Args:
        portfolio: PortfolioSummary dataclass from src.paper.models.
        positions: List of open position dicts from PositionTracker.
        todays_fills: List of fill dicts from today's orders.

    Returns:
        Discord Embed with portfolio overview.
    """
    import json as _json

    daily_pnl = portfolio.daily_pnl
    total_pnl = portfolio.realized_pnl + portfolio.unrealized_pnl

    if daily_pnl > 0:
        color = COLOR_BULLISH
    elif daily_pnl < 0:
        color = COLOR_BEARISH
    else:
        color = COLOR_NEUTRAL

    embed = discord.Embed(
        title="Paper Trading Status",
        description=(
            f"Portfolio: {_fmt_price(portfolio.total_equity)} | "
            f"Day P/L: {_fmt_price(daily_pnl)} | "
            f"Total P/L: {_fmt_price(total_pnl)}"
        ),
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    # Field 1: Active Positions
    if positions:
        pos_lines = []
        for pos in positions[:10]:
            strategy_name = pos.get("strategy_name", f"Strategy #{pos.get('strategy_id', '?')}")
            legs_data = pos.get("legs", "[]")
            if isinstance(legs_data, str):
                try:
                    legs_list = _json.loads(legs_data)
                except (ValueError, TypeError):
                    legs_list = []
            else:
                legs_list = legs_data if isinstance(legs_data, list) else []

            option_desc = _build_option_desc(legs_list)
            entry_price = pos.get("entry_price", 0.0)
            current_mark = pos.get("current_mark", 0.0)
            unrealized = pos.get("unrealized_pnl", 0.0)

            pos_lines.append(
                f"**{strategy_name}** | {option_desc} | "
                f"Entry: {_fmt_price(entry_price)} | "
                f"Now: {_fmt_price(current_mark)} | "
                f"P/L: {_fmt_price(unrealized)}"
            )
        embed.add_field(
            name=f"Active Positions ({len(positions)})",
            value="\n".join(pos_lines),
            inline=False,
        )
    else:
        embed.add_field(
            name="Active Positions (0)",
            value="No open positions",
            inline=False,
        )

    # Field 2: Today's Trades (only if there are fills)
    if todays_fills:
        fill_lines = []
        for fill in todays_fills[:8]:
            filled_at = fill.get("filled_at", "")
            time_et = filled_at[11:16] if len(filled_at) > 16 else filled_at
            direction = fill.get("direction", "")
            action = "OPEN" if direction == "open" else "CLOSE"
            fill_price = fill.get("fill_price", 0.0)
            slippage = fill.get("slippage", 0.0)

            fill_lines.append(
                f"`{time_et}` {action} @ "
                f"{_fmt_price(fill_price)} (slip: ${slippage:.4f})"
            )
        embed.add_field(
            name=f"Today's Trades ({len(todays_fills)})",
            value="\n".join(fill_lines),
            inline=False,
        )

    # Fields 3-8: Summary stats
    embed.add_field(name="Total P/L", value=_fmt_price(total_pnl), inline=True)
    embed.add_field(name="Win Rate", value=f"{portfolio.win_rate:.1%}", inline=True)
    embed.add_field(name="Trades", value=str(portfolio.total_trades), inline=True)
    embed.add_field(name="Sharpe", value=f"{portfolio.sharpe_ratio:.3f}", inline=True)
    embed.add_field(name="Max DD", value=f"{portfolio.max_drawdown:.2%}", inline=True)
    embed.add_field(
        name="Strategies",
        value=", ".join(portfolio.strategies_active) if portfolio.strategies_active else "None",
        inline=True,
    )

    embed.set_footer(text="SPY Options Employee | Paper Trading")
    return embed


def build_paper_history_embed(
    trades: list[dict],
    strategy_filter: str | None,
    days: int,
    page: int = 1,
    page_size: int = 15,
) -> discord.Embed:
    """Build a paper trade history embed with pagination.

    Args:
        trades: List of trade dicts (pre-filtered by date/strategy).
        strategy_filter: Strategy name if filtered, None for all.
        days: Lookback period used.
        page: Current page (1-indexed).
        page_size: Trades per page.

    Returns:
        Discord Embed with trade history.
    """
    total = len(trades)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)

    if strategy_filter:
        title = f"Paper Trade History -- {strategy_filter}"
    else:
        title = f"Paper Trade History -- Last {days} days"

    # Cumulative PnL across all trades (not just current page)
    cumulative_pnl = sum(
        (t.get("total_pnl", 0) - t.get("fees", 0)) for t in trades
    )

    if not trades:
        color = COLOR_INFO
    elif cumulative_pnl > 0:
        color = COLOR_BULLISH
    else:
        color = COLOR_BEARISH

    embed = discord.Embed(
        title=title,
        description=f"Showing {start_idx + 1}-{end_idx} of {total} trades" if total > 0 else "No trades found",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    # Field 1: Trades
    if total > 0:
        page_trades = trades[start_idx:end_idx]
        trade_lines = []
        for t in page_trades:
            exit_date = t.get("exit_date", "N/A")
            strategy_name = t.get("strategy_name", f"#{t.get('strategy_id', '?')}")
            entry_price = t.get("entry_price", 0.0)
            exit_price = t.get("exit_price", 0.0)
            net_pnl = t.get("total_pnl", 0.0) - t.get("fees", 0.0)
            close_reason = t.get("close_reason", "")

            trade_lines.append(
                f"`{exit_date}` {strategy_name} | "
                f"{_fmt_price(entry_price)} -> {_fmt_price(exit_price)} | "
                f"P/L: ${net_pnl:+,.2f} | {close_reason}"
            )

        embed.add_field(
            name="Trades",
            value="\n".join(trade_lines),
            inline=False,
        )
    else:
        embed.add_field(
            name="Trades",
            value="No trades in this period.",
            inline=False,
        )

    # Summary stats across all trades
    embed.add_field(name="Cumulative P/L", value=f"${cumulative_pnl:+,.2f}", inline=True)
    embed.add_field(name="Trade Count", value=str(total), inline=True)

    avg_trade = cumulative_pnl / total if total > 0 else 0.0
    embed.add_field(name="Avg Trade", value=f"${avg_trade:+,.2f}", inline=True)

    wins = sum(1 for t in trades if (t.get("total_pnl", 0) - t.get("fees", 0)) > 0)
    win_rate = wins / total if total > 0 else 0.0
    embed.add_field(name="Win Rate", value=f"{win_rate:.1%}", inline=True)

    embed.set_footer(text=f"Page {page}/{total_pages} | SPY Options Employee | Paper Trading")
    return embed


def build_paper_position_detail_embed(
    position: dict,
    strategy_name: str,
    fills: list[dict],
) -> discord.Embed:
    """Build a detailed position embed for /paper_position.

    Args:
        position: Full position dict from PositionTracker.
        strategy_name: Name of the owning strategy.
        fills: Fill records from the opening order.

    Returns:
        Discord Embed with position details.
    """
    import json as _json

    pos_id = position.get("id", "?")
    status = position.get("status", "unknown")
    opened_at = position.get("opened_at", "N/A")
    unrealized = position.get("unrealized_pnl", 0.0)

    if unrealized > 0:
        color = COLOR_BULLISH
    elif unrealized < 0:
        color = COLOR_BEARISH
    else:
        color = COLOR_INFO

    embed = discord.Embed(
        title=f"Position #{pos_id} -- {strategy_name}",
        description=f"Status: {status} | Opened: {opened_at}",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    # Field 1: Legs
    legs_data = position.get("legs", "[]")
    if isinstance(legs_data, str):
        try:
            legs_list = _json.loads(legs_data)
        except (ValueError, TypeError):
            legs_list = []
    else:
        legs_list = legs_data if isinstance(legs_data, list) else []

    if legs_list:
        leg_lines = []
        for leg in legs_list:
            action = leg.get("action", "?").upper()
            qty = leg.get("quantity", 1)
            expiry = leg.get("expiry", "?")
            strike = leg.get("strike", 0)
            side = "C" if leg.get("option_type", "").lower() == "call" else "P"
            fill_price = leg.get("fill_price", 0.0)
            delta = leg.get("delta", 0.0)
            leg_lines.append(
                f"{action} {qty}x SPX {expiry} {int(strike)}{side} "
                f"@ ${fill_price:.4f} (delta: {delta:.3f})"
            )
        embed.add_field(
            name="Legs",
            value="\n".join(leg_lines),
            inline=False,
        )
    else:
        embed.add_field(name="Legs", value="No leg data", inline=False)

    # Fields 2-8
    entry_price = position.get("entry_price", 0.0)
    current_mark = position.get("current_mark", 0.0)
    max_profit = position.get("max_profit", 0.0)
    max_loss = position.get("max_loss", 0.0)
    last_mark_at = position.get("last_mark_at", "N/A")

    pnl_sign = "[+]" if unrealized > 0 else "[-]" if unrealized < 0 else "[=]"

    embed.add_field(name="Entry Price", value=_fmt_price(entry_price), inline=True)
    embed.add_field(name="Current Mark", value=_fmt_price(current_mark), inline=True)
    embed.add_field(
        name="Unrealized P/L",
        value=f"{pnl_sign} {_fmt_price(unrealized)}",
        inline=True,
    )
    embed.add_field(name="Max Profit", value=_fmt_price(max_profit), inline=True)
    embed.add_field(name="Max Loss", value=_fmt_price(max_loss), inline=True)

    pnl_pct = (unrealized / max_profit * 100) if max_profit != 0 else 0.0
    embed.add_field(name="P/L % of Max", value=f"{pnl_pct:.1f}%", inline=True)

    embed.add_field(name="Last Mark", value=str(last_mark_at)[:19], inline=True)

    embed.set_footer(text="SPY Options Employee | Position Detail")
    return embed


def build_paper_daily_pnl_embed(
    portfolio: "PortfolioSummary",
    todays_trades: list[dict],
    date_str: str,
) -> discord.Embed:
    """Build a daily P/L summary embed for auto-post at 16:15 ET.

    Args:
        portfolio: PortfolioSummary dataclass.
        todays_trades: List of trades closed today.
        date_str: Formatted date string.

    Returns:
        Discord Embed with daily P/L summary.
    """
    daily_pnl = portfolio.daily_pnl

    if daily_pnl > 0:
        color = COLOR_BULLISH
    elif daily_pnl < 0:
        color = COLOR_BEARISH
    else:
        color = COLOR_NEUTRAL

    embed = discord.Embed(
        title=f"Paper Trading Daily P/L -- {date_str}",
        description=f"Day P/L: ${daily_pnl:+,.2f}",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    # Realized P/L from today's closed trades
    realized_today = sum(t.get("total_pnl", 0.0) - t.get("fees", 0.0) for t in todays_trades)
    embed.add_field(name="Realized P/L", value=f"${realized_today:+,.2f}", inline=True)
    embed.add_field(name="Unrealized P/L", value=f"${portfolio.unrealized_pnl:+,.2f}", inline=True)
    embed.add_field(name="Total Day P/L", value=f"${daily_pnl:+,.2f}", inline=True)

    # Trades today
    if todays_trades:
        trade_lines = []
        for t in todays_trades[:10]:
            strategy_name = t.get("strategy_name", f"#{t.get('strategy_id', '?')}")
            net_pnl = t.get("total_pnl", 0.0) - t.get("fees", 0.0)
            reason = t.get("close_reason", "")
            trade_lines.append(f"{strategy_name}: ${net_pnl:+,.2f} ({reason})")
        embed.add_field(
            name=f"Trades Today ({len(todays_trades)})",
            value="\n".join(trade_lines),
            inline=False,
        )
    else:
        embed.add_field(
            name="Trades Today (0)",
            value="No trades closed today",
            inline=False,
        )

    # Cumulative stats
    cumulative_pnl = portfolio.realized_pnl + portfolio.unrealized_pnl
    embed.add_field(name="Cumulative P/L", value=f"${cumulative_pnl:+,.2f}", inline=True)
    embed.add_field(name="Portfolio Value", value=_fmt_price(portfolio.total_equity), inline=True)
    embed.add_field(name="Open Positions", value=str(portfolio.open_positions), inline=True)

    embed.set_footer(text="SPY Options Employee | Paper Daily")
    return embed


def build_paper_fill_alert_embed(
    order: dict,
    fills: list[dict],
    strategy_name: str,
) -> discord.Embed:
    """Build a fill alert embed for real-time notifications.

    Args:
        order: The filled order dict.
        fills: List of fill dicts for the order.
        strategy_name: Name of the strategy.

    Returns:
        Discord Embed with fill details.
    """
    direction = order.get("direction", "").upper()
    order_type = order.get("order_type", "")
    num_legs = len(fills)
    quantity = order.get("quantity", 1)

    embed = discord.Embed(
        title=f"PAPER FILL -- {strategy_name}",
        description=f"{direction} {order_type} | {num_legs} legs | Qty: {quantity}",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc),
    )

    # Field 1: Fills
    if fills:
        fill_lines = []
        for f in fills:
            action = f.get("action", "?").upper()
            expiry = f.get("expiry", "?")
            strike = f.get("strike", 0)
            side = "C" if f.get("option_type", "").lower() == "call" else "P"
            fill_price = f.get("fill_price", 0.0)
            mid = f.get("mid", 0.0)
            slippage = f.get("slippage", 0.0)

            fill_lines.append(
                f"{action} SPX {expiry} {int(strike)}{side} "
                f"@ ${fill_price:.4f} (mid: ${mid:.4f}, slip: ${slippage:.4f})"
            )
        embed.add_field(
            name="Fills",
            value="\n".join(fill_lines),
            inline=False,
        )

    # Summary fields
    net_price = order.get("fill_price", 0.0)
    total_slippage = sum(f.get("slippage", 0.0) for f in fills)
    filled_at = order.get("filled_at", "")

    embed.add_field(name="Net Price", value=f"${net_price:.4f}", inline=True)
    embed.add_field(name="Total Slippage", value=f"${total_slippage:.4f}", inline=True)
    embed.add_field(name="Time", value=filled_at[:19] if filled_at else "N/A", inline=True)

    embed.set_footer(text="SPY Options Employee | Paper Fill")
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
