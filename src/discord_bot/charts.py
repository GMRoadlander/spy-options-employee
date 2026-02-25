"""Matplotlib chart generation for Discord embeds.

Creates charts that return discord.File objects for attaching to messages.
Uses dark theme for Discord readability and BytesIO buffers to avoid disk I/O.

CRITICAL: Always calls plt.close(fig) after saving to prevent memory leaks.
"""

import io
import logging
from datetime import datetime, timezone

import discord
import matplotlib

# Use non-interactive backend BEFORE importing pyplot (required for headless/bot)
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402

from src.analysis.gex import GEXResult  # noqa: E402
from src.analysis.max_pain import MaxPainResult  # noqa: E402

# Set dark style once at module level (W13: avoid per-function duplication)
plt.style.use("dark_background")

logger = logging.getLogger(__name__)


def _save_to_discord_file(fig: plt.Figure, filename: str) -> discord.File:
    """Save a matplotlib figure to a BytesIO buffer and return as discord.File.

    Args:
        fig: The matplotlib figure to save.
        filename: The filename to use for the Discord attachment.

    Returns:
        discord.File wrapping the PNG image.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return discord.File(buf, filename=filename)


def create_gex_chart(gex: GEXResult, ticker: str) -> discord.File | None:
    """Create a GEX bar chart with call/put bars and net GEX line overlay.

    Shows:
    - Green bars for call GEX (positive)
    - Red bars for put GEX (negative)
    - White line for net GEX overlay
    - Dashed horizontal line at zero
    - Vertical dashed line at gamma flip point (if exists)

    Args:
        gex: GEX analysis result with per-strike data.
        ticker: Ticker symbol for the chart title.

    Returns:
        discord.File containing the PNG chart, or None if no data.
    """
    if not gex.strikes or not gex.call_gex or not gex.put_gex:
        logger.warning("No GEX strike data available for chart generation")
        return None

    try:
        strikes = np.array(gex.strikes)
        call_gex_vals = np.array(gex.call_gex)
        put_gex_vals = np.array(gex.put_gex)
        net_gex_vals = np.array(gex.net_gex_by_strike)

        # Subsample if too many strikes for readability
        max_bars = 60
        if len(strikes) > max_bars:
            step = len(strikes) // max_bars
            indices = list(range(0, len(strikes), step))
            strikes = strikes[indices]
            call_gex_vals = call_gex_vals[indices]
            put_gex_vals = put_gex_vals[indices]
            net_gex_vals = net_gex_vals[indices]

        fig, ax = plt.subplots(figsize=(14, 7))

        bar_width = (strikes[-1] - strikes[0]) / len(strikes) * 0.35 if len(strikes) > 1 else 1.0

        # Call GEX bars (green)
        ax.bar(
            strikes - bar_width / 2,
            call_gex_vals,
            width=bar_width,
            color="#00ff00",
            alpha=0.7,
            label="Call GEX",
        )

        # Put GEX bars (red)
        ax.bar(
            strikes + bar_width / 2,
            put_gex_vals,
            width=bar_width,
            color="#ff0000",
            alpha=0.7,
            label="Put GEX",
        )

        # Net GEX line overlay
        ax.plot(
            strikes,
            net_gex_vals,
            color="white",
            linewidth=1.5,
            label="Net GEX",
            zorder=5,
        )

        # Zero line
        ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)

        # Gamma flip marker
        if gex.gamma_flip is not None:
            ax.axvline(
                x=gex.gamma_flip,
                color="#ffff00",
                linestyle="--",
                linewidth=1.5,
                label=f"Gamma Flip ${gex.gamma_flip:.2f}",
                zorder=4,
            )

        # Gamma ceiling and floor
        ax.axvline(
            x=gex.gamma_ceiling,
            color="#00ccff",
            linestyle=":",
            linewidth=1.2,
            label=f"Ceiling ${gex.gamma_ceiling:.2f}",
            alpha=0.8,
        )
        ax.axvline(
            x=gex.gamma_floor,
            color="#ff6600",
            linestyle=":",
            linewidth=1.2,
            label=f"Floor ${gex.gamma_floor:.2f}",
            alpha=0.8,
        )

        # Formatting
        ax.set_title(f"{ticker} Gamma Exposure by Strike", fontsize=14, fontweight="bold")
        ax.set_xlabel("Strike Price", fontsize=11)
        ax.set_ylabel("GEX ($)", fontsize=11)
        ax.legend(loc="upper left", fontsize=9, framealpha=0.7)

        # Format y-axis with suffixes
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_gex_y_formatter))

        # Rotate x labels for readability
        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.tight_layout()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return _save_to_discord_file(fig, f"gex_{ticker}_{timestamp}.png")

    except Exception as exc:
        logger.error("Failed to create GEX chart for %s: %s", ticker, exc, exc_info=True)
        plt.close("all")
        return None


def create_max_pain_chart(max_pain: MaxPainResult, ticker: str) -> discord.File | None:
    """Create a max pain curve chart with the minimum point highlighted.

    Shows:
    - Pain curve (total writer payout at each settlement price)
    - Highlighted minimum point (max pain price)
    - Vertical line at current spot price
    - Shaded region near the minimum

    Args:
        max_pain: Max pain analysis result with per-strike pain values.
        ticker: Ticker symbol for the chart title.

    Returns:
        discord.File containing the PNG chart, or None if no data.
    """
    if not max_pain.pain_by_strike:
        logger.warning("No max pain strike data available for chart generation")
        return None

    try:
        # Sort by strike price
        sorted_strikes = sorted(max_pain.pain_by_strike.keys())
        pain_values = [max_pain.pain_by_strike[k] for k in sorted_strikes]

        strikes = np.array(sorted_strikes)
        pain = np.array(pain_values)

        # Subsample if too many points
        max_points = 80
        if len(strikes) > max_points:
            step = len(strikes) // max_points
            indices = list(range(0, len(strikes), step))
            # Always include the max pain strike index
            mp_idx = sorted_strikes.index(max_pain.max_pain_price) if max_pain.max_pain_price in sorted_strikes else None
            if mp_idx is not None and mp_idx not in indices:
                indices.append(mp_idx)
                indices.sort()
            strikes = strikes[indices]
            pain = pain[indices]

        fig, ax = plt.subplots(figsize=(14, 7))

        # Pain curve
        ax.fill_between(strikes, pain, alpha=0.15, color="#0099ff")
        ax.plot(strikes, pain, color="#0099ff", linewidth=2, label="Pain Curve")

        # Max pain point
        ax.scatter(
            [max_pain.max_pain_price],
            [max_pain.total_pain_at_max],
            color="#ffff00",
            s=120,
            zorder=5,
            marker="*",
            label=f"Max Pain ${max_pain.max_pain_price:.2f}",
        )

        # Current price vertical line
        ax.axvline(
            x=max_pain.current_price,
            color="#00ff00",
            linestyle="--",
            linewidth=1.5,
            label=f"Current ${max_pain.current_price:.2f}",
        )

        # Max pain vertical line
        ax.axvline(
            x=max_pain.max_pain_price,
            color="#ffff00",
            linestyle=":",
            linewidth=1.2,
            alpha=0.6,
        )

        # Formatting
        ax.set_title(
            f"{ticker} Max Pain -- Expiry {max_pain.expiry}",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_xlabel("Settlement Price", fontsize=11)
        ax.set_ylabel("Total Pain to Writers ($)", fontsize=11)
        ax.legend(loc="upper right", fontsize=9, framealpha=0.7)

        # Format y-axis
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pain_y_formatter))

        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.tight_layout()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return _save_to_discord_file(fig, f"maxpain_{ticker}_{timestamp}.png")

    except Exception as exc:
        logger.error("Failed to create max pain chart for %s: %s", ticker, exc, exc_info=True)
        plt.close("all")
        return None


def _gex_y_formatter(value: float, _pos: int) -> str:
    """Format GEX y-axis values with B/M/K suffixes."""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1e9:
        return f"{sign}{abs_val / 1e9:.1f}B"
    elif abs_val >= 1e6:
        return f"{sign}{abs_val / 1e6:.1f}M"
    elif abs_val >= 1e3:
        return f"{sign}{abs_val / 1e3:.1f}K"
    else:
        return f"{sign}{abs_val:.0f}"


def _pain_y_formatter(value: float, _pos: int) -> str:
    """Format pain y-axis values with B/M/K suffixes."""
    abs_val = abs(value)
    if abs_val >= 1e9:
        return f"${abs_val / 1e9:.1f}B"
    elif abs_val >= 1e6:
        return f"${abs_val / 1e6:.1f}M"
    elif abs_val >= 1e3:
        return f"${abs_val / 1e3:.0f}K"
    else:
        return f"${abs_val:.0f}"


# -- Strategy reporting charts ------------------------------------------------


def draw_equity_curve(
    daily_returns: "np.ndarray | list[float]",
    strategy_name: str,
) -> discord.File | None:
    """Create an equity curve chart with cumulative returns and drawdown overlay.

    Args:
        daily_returns: Array-like of daily P&L values.
        strategy_name: Strategy name for the chart title.

    Returns:
        discord.File containing the PNG chart, or None if no data.
    """
    returns = np.array(daily_returns)
    if len(returns) == 0:
        return None

    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[3, 1], sharex=True)

        # Equity curve
        cumulative = np.cumsum(returns)
        ax1.plot(range(len(cumulative)), cumulative, color="#00ff00", linewidth=1.5, label="Equity")
        ax1.fill_between(range(len(cumulative)), cumulative, alpha=0.15, color="#00ff00")
        ax1.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
        ax1.set_title(f"{strategy_name} -- Equity Curve", fontsize=14, fontweight="bold")
        ax1.set_ylabel("Cumulative P&L ($)", fontsize=11)
        ax1.legend(loc="upper left", fontsize=9, framealpha=0.7)

        # Drawdown
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        ax2.fill_between(range(len(drawdown)), drawdown, color="#ff0000", alpha=0.5)
        ax2.plot(range(len(drawdown)), drawdown, color="#ff0000", linewidth=1, label="Drawdown")
        ax2.set_xlabel("Trading Days", fontsize=11)
        ax2.set_ylabel("Drawdown ($)", fontsize=11)
        ax2.legend(loc="lower left", fontsize=9, framealpha=0.7)

        plt.tight_layout()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return _save_to_discord_file(fig, f"equity_{strategy_name}_{timestamp}.png")

    except Exception as exc:
        logger.error("Failed to create equity curve: %s", exc, exc_info=True)
        plt.close("all")
        return None


def draw_monte_carlo_fan(
    simulation_paths: "np.ndarray | list[list[float]]",
    strategy_name: str,
) -> discord.File | None:
    """Create a Monte Carlo fan chart showing simulation paths with percentile bands.

    Args:
        simulation_paths: 2D array where each row is a simulated equity path.
        strategy_name: Strategy name for the chart title.

    Returns:
        discord.File containing the PNG chart, or None if no data.
    """
    paths = np.array(simulation_paths)
    if paths.size == 0 or len(paths.shape) < 2:
        return None

    try:
        fig, ax = plt.subplots(figsize=(14, 7))

        n_steps = paths.shape[1]
        x = range(n_steps)

        # Plot percentile bands
        p5 = np.percentile(paths, 5, axis=0)
        p25 = np.percentile(paths, 25, axis=0)
        p50 = np.percentile(paths, 50, axis=0)
        p75 = np.percentile(paths, 75, axis=0)
        p95 = np.percentile(paths, 95, axis=0)

        ax.fill_between(x, p5, p95, alpha=0.15, color="#0099ff", label="5th-95th pct")
        ax.fill_between(x, p25, p75, alpha=0.3, color="#0099ff", label="25th-75th pct")
        ax.plot(x, p50, color="#0099ff", linewidth=2, label="Median")
        ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)

        # Sample paths (max 50 for visual clarity)
        n_show = min(50, paths.shape[0])
        for i in range(n_show):
            ax.plot(x, paths[i], color="white", alpha=0.05, linewidth=0.5)

        ax.set_title(f"{strategy_name} -- Monte Carlo Simulation", fontsize=14, fontweight="bold")
        ax.set_xlabel("Trade Number", fontsize=11)
        ax.set_ylabel("Cumulative P&L ($)", fontsize=11)
        ax.legend(loc="upper left", fontsize=9, framealpha=0.7)

        plt.tight_layout()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return _save_to_discord_file(fig, f"mc_fan_{strategy_name}_{timestamp}.png")

    except Exception as exc:
        logger.error("Failed to create MC fan chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


def draw_wfa_windows(
    is_sharpes: list[float],
    oos_sharpes: list[float],
    strategy_name: str,
) -> discord.File | None:
    """Create a WFA chart comparing IS vs OOS Sharpe ratios per window.

    Args:
        is_sharpes: In-sample Sharpe ratios per WFA window.
        oos_sharpes: Out-of-sample Sharpe ratios per WFA window.
        strategy_name: Strategy name for the chart title.

    Returns:
        discord.File containing the PNG chart, or None if no data.
    """
    if not is_sharpes or not oos_sharpes:
        return None

    try:
        fig, ax = plt.subplots(figsize=(12, 6))

        n_windows = len(is_sharpes)
        x = np.arange(n_windows)
        width = 0.35

        bars_is = ax.bar(x - width / 2, is_sharpes, width, label="In-Sample", color="#0099ff", alpha=0.8)
        bars_oos = ax.bar(x + width / 2, oos_sharpes, width, label="Out-of-Sample", color="#00ff00", alpha=0.8)

        ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
        ax.set_title(f"{strategy_name} -- Walk-Forward Analysis", fontsize=14, fontweight="bold")
        ax.set_xlabel("Window", fontsize=11)
        ax.set_ylabel("Sharpe Ratio", fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels([f"W{i + 1}" for i in range(n_windows)])
        ax.legend(fontsize=10, framealpha=0.7)

        plt.tight_layout()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return _save_to_discord_file(fig, f"wfa_{strategy_name}_{timestamp}.png")

    except Exception as exc:
        logger.error("Failed to create WFA chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


def draw_strategy_comparison(
    metrics_list: list[dict],
) -> discord.File | None:
    """Create a grouped bar chart comparing strategy metrics.

    Args:
        metrics_list: List of dicts with keys: name, sharpe, sortino, win_rate,
                      profit_factor. Each dict is one strategy.

    Returns:
        discord.File containing the PNG chart, or None if no data.
    """
    if not metrics_list:
        return None

    try:
        fig, ax = plt.subplots(figsize=(12, 6))

        categories = ["Sharpe", "Sortino", "Win Rate", "Profit Factor"]
        n_strategies = len(metrics_list)
        n_cats = len(categories)

        x = np.arange(n_cats)
        width = 0.8 / n_strategies

        base_colors = ["#0099ff", "#00ff00", "#ffff00", "#ff6600"]
        # Cycle colors for >4 strategies to avoid IndexError (W11)
        colors = [base_colors[i % len(base_colors)] for i in range(n_strategies)]

        for i, m in enumerate(metrics_list):
            values = [
                m.get("sharpe", 0),
                m.get("sortino", 0),
                m.get("win_rate", 0) * 100,  # percent
                m.get("profit_factor", 0),
            ]
            offset = (i - n_strategies / 2 + 0.5) * width
            ax.bar(x + offset, values, width, label=m.get("name", f"Strategy {i + 1}"),
                   color=colors[i], alpha=0.8)

        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_title("Strategy Comparison", fontsize=14, fontweight="bold")
        ax.set_ylabel("Value", fontsize=11)
        ax.legend(fontsize=9, framealpha=0.7)
        ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)

        plt.tight_layout()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return _save_to_discord_file(fig, f"comparison_{timestamp}.png")

    except Exception as exc:
        logger.error("Failed to create comparison chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


# -- Paper trading charts (Phase 4, sub-plan 4-6) -----------------------------


def create_pnl_curve_chart(
    equity_data: list[dict],
    strategy_name: str | None = None,
) -> discord.File | None:
    """Create a P/L equity curve chart for paper trading.

    Shows cumulative P/L as a line chart with green/red fill for above/below
    zero, suitable for mobile Discord viewing.

    Args:
        equity_data: From PnLCalculator.get_equity_curve() -- list of dicts
            with ``date``, ``total_equity``, ``daily_pnl``.
        strategy_name: Optional, for title customization.

    Returns:
        discord.File with filename ``pnl_curve_{timestamp}.png``, or None.
    """
    if not equity_data or len(equity_data) < 2:
        return None

    try:
        import matplotlib.dates as mdates

        # Extract data
        starting_capital = equity_data[0].get("total_equity", 0)
        dates = []
        pnl_values = []
        for d in equity_data:
            date_str = d.get("date", "")
            if isinstance(date_str, str) and len(date_str) >= 10:
                try:
                    dates.append(datetime.strptime(date_str[:10], "%Y-%m-%d"))
                except ValueError:
                    continue
            elif hasattr(date_str, "isoformat"):
                dates.append(date_str)
            else:
                continue
            pnl_values.append(d.get("total_equity", 0) - starting_capital)

        if len(dates) < 2:
            return None

        pnl_arr = np.array(pnl_values)

        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot line
        ax.plot(dates, pnl_arr, color="#00ff00", linewidth=1.5, label="Cumulative P/L")

        # Green fill above zero, red fill below zero
        ax.fill_between(
            dates, pnl_arr, 0,
            where=pnl_arr >= 0,
            color="#00ff00", alpha=0.15,
            interpolate=True,
        )
        ax.fill_between(
            dates, pnl_arr, 0,
            where=pnl_arr < 0,
            color="#ff0000", alpha=0.15,
            interpolate=True,
        )

        # Zero line
        ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)

        # Formatting
        title = f"{strategy_name} -- Paper P/L Curve" if strategy_name else "Portfolio -- Paper P/L Curve"
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Date", fontsize=11)
        ax.set_ylabel("Cumulative P/L ($)", fontsize=11)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.grid(alpha=0.2)

        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.tight_layout()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return _save_to_discord_file(fig, f"pnl_curve_{timestamp}.png")

    except Exception as exc:
        logger.error("Failed to create P/L curve chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


def create_drawdown_chart(
    equity_data: list[dict],
    strategy_name: str | None = None,
) -> discord.File | None:
    """Create a drawdown underwater chart for paper trading.

    Shows drawdown percentage from peak equity as a filled area chart.

    Args:
        equity_data: From PnLCalculator.get_equity_curve() -- list of dicts
            with ``date``, ``total_equity``.
        strategy_name: Optional, for title customization.

    Returns:
        discord.File with filename ``drawdown_{timestamp}.png``, or None.
    """
    if not equity_data or len(equity_data) < 2:
        return None

    try:
        import matplotlib.dates as mdates

        dates = []
        equity_values = []
        for d in equity_data:
            date_str = d.get("date", "")
            if isinstance(date_str, str) and len(date_str) >= 10:
                try:
                    dates.append(datetime.strptime(date_str[:10], "%Y-%m-%d"))
                except ValueError:
                    continue
            elif hasattr(date_str, "isoformat"):
                dates.append(date_str)
            else:
                continue
            equity_values.append(d.get("total_equity", 0))

        if len(dates) < 2:
            return None

        equity_arr = np.array(equity_values)
        running_max = np.maximum.accumulate(equity_arr)
        drawdown_pct = np.where(
            running_max > 0,
            (equity_arr - running_max) / running_max,
            0.0,
        )

        fig, ax = plt.subplots(figsize=(12, 3))

        # Red fill from 0 to drawdown
        ax.fill_between(dates, drawdown_pct, 0, color="#ff0000", alpha=0.4)
        ax.plot(dates, drawdown_pct, color="#ff0000", linewidth=1)

        # Annotate max drawdown point
        min_idx = np.argmin(drawdown_pct)
        if drawdown_pct[min_idx] < 0:
            ax.annotate(
                f"{drawdown_pct[min_idx]:.2%}",
                xy=(dates[min_idx], drawdown_pct[min_idx]),
                xytext=(dates[min_idx], drawdown_pct[min_idx] * 0.5),
                arrowprops=dict(arrowstyle="->", color="white"),
                color="white",
                fontsize=9,
                fontweight="bold",
            )

        # Formatting
        title = f"{strategy_name} -- Drawdown" if strategy_name else "Portfolio -- Drawdown"
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        ax.grid(alpha=0.2)

        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.tight_layout()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return _save_to_discord_file(fig, f"drawdown_{timestamp}.png")

    except Exception as exc:
        logger.error("Failed to create drawdown chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


def create_daily_pnl_bar_chart(
    equity_data: list[dict],
    days: int = 30,
) -> discord.File | None:
    """Create a daily P/L bar chart for paper trading.

    Shows daily P/L as green/red bars for the last N days.

    Args:
        equity_data: From PnLCalculator.get_equity_curve() -- list of dicts
            with ``date``, ``daily_pnl``.
        days: Number of days to display.

    Returns:
        discord.File with filename ``daily_pnl_{timestamp}.png``, or None.
    """
    if not equity_data:
        return None

    try:
        import matplotlib.dates as mdates

        # Use last N days
        data = equity_data[-days:]

        dates = []
        daily_pnls = []
        for d in data:
            date_str = d.get("date", "")
            if isinstance(date_str, str) and len(date_str) >= 10:
                try:
                    dates.append(datetime.strptime(date_str[:10], "%Y-%m-%d"))
                except ValueError:
                    continue
            elif hasattr(date_str, "isoformat"):
                dates.append(date_str)
            else:
                continue
            daily_pnls.append(d.get("daily_pnl", 0))

        if not dates:
            return None

        pnl_arr = np.array(daily_pnls)
        colors = ["#00ff00" if p >= 0 else "#ff0000" for p in pnl_arr]

        fig, ax = plt.subplots(figsize=(12, 5))

        ax.bar(dates, pnl_arr, color=colors, alpha=0.8, width=0.8)

        # Zero line
        ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)

        # Formatting
        ax.set_title(f"Daily P/L -- Last {days} Days", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date", fontsize=11)
        ax.set_ylabel("Daily P/L ($)", fontsize=11)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.grid(alpha=0.2)

        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.tight_layout()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return _save_to_discord_file(fig, f"daily_pnl_{timestamp}.png")

    except Exception as exc:
        logger.error("Failed to create daily P/L bar chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


# -- ML Intelligence Layer charts (Phase 3) ------------------------------------

# Regime state colors for the timeline chart
_REGIME_CHART_COLORS: dict[str, str] = {
    "risk-on": "#00ff00",
    "risk-off": "#ffff00",
    "crisis": "#ff0000",
    "unknown": "#666666",
}


def create_regime_timeline_chart(
    regime_history: list[dict],
    days: int = 30,
) -> io.BytesIO | None:
    """Create a horizontal bar chart showing regime states over time.

    Each day is shown as a colored bar: green for risk-on, yellow for
    risk-off, red for crisis.

    Args:
        regime_history: List of dicts with ``date`` and ``state_name`` keys,
            ordered oldest-first.
        days: Maximum number of days to display.

    Returns:
        BytesIO buffer containing the PNG chart, or None if no data.
    """
    if not regime_history:
        return None

    # Limit to requested days
    history = regime_history[-days:]

    try:
        dates = [h.get("date", "") for h in history]
        states = [h.get("state_name", "unknown") for h in history]
        colors = [_REGIME_CHART_COLORS.get(s, "#666666") for s in states]

        fig, ax = plt.subplots(figsize=(14, 4))

        # Horizontal bar chart: each date gets a bar of height 1
        y_positions = range(len(dates))
        ax.barh(
            y_positions,
            [1] * len(dates),
            color=colors,
            edgecolor="none",
            height=0.8,
        )

        # Y-axis labels (dates)
        ax.set_yticks(list(y_positions))
        # Show every Nth label to avoid clutter
        n_labels = min(15, len(dates))
        step = max(1, len(dates) // n_labels)
        labels = [dates[i] if i % step == 0 else "" for i in range(len(dates))]
        ax.set_yticklabels(labels, fontsize=8)

        ax.set_xlim(0, 1)
        ax.set_xticks([])
        ax.set_title("Market Regime Timeline", fontsize=14, fontweight="bold")
        ax.invert_yaxis()  # Most recent at top

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#00ff00", label="Risk-On"),
            Patch(facecolor="#ffff00", label="Risk-Off"),
            Patch(facecolor="#ff0000", label="Crisis"),
        ]
        ax.legend(handles=legend_elements, loc="lower right", fontsize=9, framealpha=0.7)

        plt.tight_layout()

        # Return as BytesIO (not discord.File, since cog will wrap it)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close(fig)
        return buf

    except Exception as exc:
        logger.error("Failed to create regime timeline chart: %s", exc, exc_info=True)
        plt.close("all")
        return None
