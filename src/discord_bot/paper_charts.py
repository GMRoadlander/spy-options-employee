"""Paper trading chart generators for Discord performance reports.

Generates equity curves, drawdown charts, strategy comparisons,
degradation visualizations, rolling Sharpe, win rate trends, and
monthly P/L heatmaps.  All functions return ``discord.File | None``.

CRITICAL: Always calls plt.close(fig) after saving to prevent memory leaks.
"""

import calendar
import logging
from datetime import date, datetime, timezone

import discord
import matplotlib

# Use non-interactive backend BEFORE importing pyplot (required for headless/bot)
matplotlib.use("Agg")

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from src.discord_bot.charts import _save_to_discord_file  # noqa: E402

# Set dark style once at module level (match charts.py convention)
plt.style.use("dark_background")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Colour palette (shared across all charts)
# ---------------------------------------------------------------------------
_GREEN = "#00ff00"
_RED = "#ff0000"
_YELLOW = "#ffff00"
_BLUE = "#0099ff"
_GRAY = "#666666"

# Maximum data points before sub-sampling for readability
_MAX_EQUITY_POINTS = 80


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_dates_and_values(
    equity_data: list[dict],
    value_key: str = "total_equity",
) -> tuple[list[datetime], "np.ndarray"]:
    """Extract (dates, values) from equity dicts.

    Returns ([], empty array) when nothing can be parsed.
    """
    dates: list[datetime] = []
    values: list[float] = []
    for d in equity_data:
        date_str = d.get("date", "")
        if isinstance(date_str, str) and len(date_str) >= 10:
            try:
                dates.append(datetime.strptime(date_str[:10], "%Y-%m-%d"))
            except ValueError:
                continue
        elif hasattr(date_str, "isoformat"):
            dates.append(date_str if isinstance(date_str, datetime) else datetime.combine(date_str, datetime.min.time()))
        else:
            continue
        values.append(d.get(value_key, 0))
    return dates, np.array(values)


def _subsample(
    dates: list[datetime],
    *arrays: "np.ndarray",
    max_points: int = _MAX_EQUITY_POINTS,
) -> tuple:
    """Uniformly sub-sample dates + companion arrays to *max_points*."""
    if len(dates) <= max_points:
        return (dates, *arrays)
    step = max(1, len(dates) // max_points)
    indices = list(range(0, len(dates), step))
    # Always include the very last point
    if indices[-1] != len(dates) - 1:
        indices.append(len(dates) - 1)
    new_dates = [dates[i] for i in indices]
    new_arrays = tuple(arr[indices] for arr in arrays)
    return (new_dates, *new_arrays)


def _strategy_slug(strategy_name: str | None) -> str:
    """Produce a filesystem-safe slug for filenames."""
    if not strategy_name:
        return "portfolio"
    return strategy_name.lower().replace(" ", "_")[:30]


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


# ---------------------------------------------------------------------------
# 2a  Equity Curve Chart
# ---------------------------------------------------------------------------

def create_paper_equity_chart(
    equity_data: list[dict],
    strategy_name: str | None = None,
) -> discord.File | None:
    """Create a paper-trading equity curve with drawdown shading.

    Args:
        equity_data: List of dicts with keys ``date``, ``total_equity``,
            ``daily_pnl``, ``max_drawdown``.
        strategy_name: Optional strategy label; *None* means portfolio-level.

    Returns:
        ``discord.File`` containing the PNG chart, or ``None`` if no usable
        data.
    """
    if not equity_data:
        return None

    try:
        dates, equity = _parse_dates_and_values(equity_data, "total_equity")
        if len(dates) == 0:
            return None

        # Sub-sample for readability
        dates, equity = _subsample(dates, equity, max_points=_MAX_EQUITY_POINTS)

        starting_capital = equity[0]

        # Compute drawdown regions
        running_max = np.maximum.accumulate(equity)
        in_drawdown = equity < running_max

        fig, ax = plt.subplots(figsize=(14, 7))

        # Equity line
        ax.plot(dates, equity, color=_GREEN, linewidth=1.5, label="Equity")
        # Fill under curve
        ax.fill_between(dates, equity, alpha=0.10, color=_GREEN)

        # Starting capital reference line
        ax.axhline(
            y=starting_capital,
            color=_GRAY,
            linestyle="--",
            linewidth=1,
            label=f"Start ${starting_capital:,.0f}",
        )

        # Red shading for drawdown regions
        ax.fill_between(
            dates, equity, running_max,
            where=in_drawdown,
            color=_RED, alpha=0.20,
            interpolate=True,
            label="Drawdown",
        )

        title = (
            f"{strategy_name} -- Paper Trading Equity Curve"
            if strategy_name
            else "Portfolio Equity Curve"
        )
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_ylabel("Equity ($)", fontsize=11)
        ax.set_xlabel("Date", fontsize=11)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax.legend(loc="upper left", fontsize=9, framealpha=0.7)
        ax.grid(alpha=0.2)
        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.tight_layout()

        slug = _strategy_slug(strategy_name)
        return _save_to_discord_file(fig, f"paper_equity_{slug}_{_timestamp()}.png")

    except Exception as exc:
        logger.error("Failed to create paper equity chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


# ---------------------------------------------------------------------------
# 2b  Drawdown Chart (standalone)
# ---------------------------------------------------------------------------

def create_paper_drawdown_chart(
    equity_data: list[dict],
    strategy_name: str | None = None,
) -> discord.File | None:
    """Create a standalone drawdown (underwater) chart.

    Args:
        equity_data: List of dicts with keys ``date``, ``total_equity``.
        strategy_name: Optional strategy label.

    Returns:
        ``discord.File`` or ``None``.
    """
    if not equity_data:
        return None

    try:
        dates, equity = _parse_dates_and_values(equity_data, "total_equity")
        if len(dates) == 0:
            return None

        dates, equity = _subsample(dates, equity, max_points=_MAX_EQUITY_POINTS)

        running_max = np.maximum.accumulate(equity)
        drawdown_pct = np.where(
            running_max > 0,
            (equity - running_max) / running_max * 100,
            0.0,
        )

        fig, ax = plt.subplots(figsize=(14, 4))

        ax.fill_between(dates, 0, drawdown_pct, color=_RED, alpha=0.3)
        ax.plot(dates, drawdown_pct, color=_RED, linewidth=1)

        # Annotate max drawdown
        min_idx = int(np.argmin(drawdown_pct))
        if drawdown_pct[min_idx] < 0:
            ax.annotate(
                f"Max DD: {drawdown_pct[min_idx]:.1f}%",
                xy=(dates[min_idx], drawdown_pct[min_idx]),
                xytext=(dates[min_idx], drawdown_pct[min_idx] * 0.5),
                arrowprops=dict(arrowstyle="->", color="white"),
                color="white",
                fontsize=9,
                fontweight="bold",
            )

        title = (
            f"{strategy_name} -- Drawdown"
            if strategy_name
            else "Portfolio Drawdown"
        )
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_ylabel("Drawdown (%)", fontsize=11)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax.grid(alpha=0.2)
        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.tight_layout()

        slug = _strategy_slug(strategy_name)
        return _save_to_discord_file(fig, f"paper_drawdown_{slug}_{_timestamp()}.png")

    except Exception as exc:
        logger.error("Failed to create paper drawdown chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


# ---------------------------------------------------------------------------
# 2c  Combined Equity + Drawdown (dual-panel)
# ---------------------------------------------------------------------------

def create_paper_equity_drawdown_chart(
    equity_data: list[dict],
    strategy_name: str | None = None,
) -> discord.File | None:
    """Create a combined equity curve (top) and drawdown (bottom) chart.

    Args:
        equity_data: List of dicts with keys ``date``, ``total_equity``.
        strategy_name: Optional strategy label.

    Returns:
        ``discord.File`` or ``None``.
    """
    if not equity_data:
        return None

    try:
        dates, equity = _parse_dates_and_values(equity_data, "total_equity")
        if len(dates) == 0:
            return None

        dates, equity = _subsample(dates, equity, max_points=_MAX_EQUITY_POINTS)

        starting_capital = equity[0]
        running_max = np.maximum.accumulate(equity)
        in_drawdown = equity < running_max
        drawdown_pct = np.where(
            running_max > 0,
            (equity - running_max) / running_max * 100,
            0.0,
        )

        fig, (ax_eq, ax_dd) = plt.subplots(
            2, 1, figsize=(14, 10), height_ratios=[7, 3], sharex=True,
        )

        # -- Top panel: equity curve --
        ax_eq.plot(dates, equity, color=_GREEN, linewidth=1.5, label="Equity")
        ax_eq.fill_between(dates, equity, alpha=0.10, color=_GREEN)
        ax_eq.axhline(y=starting_capital, color=_GRAY, linestyle="--", linewidth=1)
        ax_eq.fill_between(
            dates, equity, running_max,
            where=in_drawdown,
            color=_RED, alpha=0.20,
            interpolate=True,
        )
        title = (
            f"{strategy_name} -- Paper Equity & Drawdown"
            if strategy_name
            else "Portfolio Equity & Drawdown"
        )
        ax_eq.set_title(title, fontsize=14, fontweight="bold")
        ax_eq.set_ylabel("Equity ($)", fontsize=11)
        ax_eq.grid(alpha=0.2)

        # -- Bottom panel: drawdown --
        ax_dd.fill_between(dates, 0, drawdown_pct, color=_RED, alpha=0.3)
        ax_dd.plot(dates, drawdown_pct, color=_RED, linewidth=1)
        ax_dd.set_ylabel("Drawdown (%)", fontsize=11)
        ax_dd.set_xlabel("Date", fontsize=11)
        ax_dd.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax_dd.grid(alpha=0.2)

        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.tight_layout()

        slug = _strategy_slug(strategy_name)
        return _save_to_discord_file(fig, f"paper_equity_dd_{slug}_{_timestamp()}.png")

    except Exception as exc:
        logger.error("Failed to create combined equity/drawdown chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


# ---------------------------------------------------------------------------
# 2d  Strategy Comparison Bar Chart
# ---------------------------------------------------------------------------

_METRIC_DISPLAY = {
    "sharpe_ratio": "Sharpe Ratio",
    "win_rate": "Win Rate (%)",
    "profit_factor": "Profit Factor",
    "total_pnl": "Total P/L ($)",
    "max_drawdown": "Max Drawdown (%)",
}


def create_strategy_comparison_chart(
    strategies: list[dict],
    metric: str = "sharpe_ratio",
) -> discord.File | None:
    """Create a horizontal bar chart comparing strategies on a single metric.

    Args:
        strategies: List of dicts with at least ``name`` and the chosen
            *metric* key.
        metric: Which metric to plot (default ``sharpe_ratio``).

    Returns:
        ``discord.File`` or ``None``.
    """
    if not strategies:
        return None

    try:
        names = [s.get("name", f"Strategy {i}") for i, s in enumerate(strategies)]
        values = np.array([float(s.get(metric, 0)) for s in strategies])
        colors = [_GREEN if v >= 0 else _RED for v in values]

        fig, ax = plt.subplots(figsize=(12, max(4, len(names) * 0.8 + 2)))

        bars = ax.barh(names, values, color=colors, alpha=0.8)

        # Value labels at end of each bar
        for bar, val in zip(bars, values):
            x_pos = bar.get_width()
            offset = abs(x_pos) * 0.02 + 0.01
            ha = "left" if x_pos >= 0 else "right"
            ax.text(
                x_pos + (offset if x_pos >= 0 else -offset),
                bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}",
                va="center", ha=ha,
                color="white", fontsize=9,
            )

        display_name = _METRIC_DISPLAY.get(metric, metric.replace("_", " ").title())
        ax.set_title(f"Strategy Comparison -- {display_name}", fontsize=14, fontweight="bold")
        ax.set_xlabel(display_name, fontsize=11)
        ax.grid(axis="x", alpha=0.2)
        plt.tight_layout()

        return _save_to_discord_file(fig, f"paper_compare_{metric}_{_timestamp()}.png")

    except Exception as exc:
        logger.error("Failed to create strategy comparison chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


# ---------------------------------------------------------------------------
# 2e  Paper vs Backtest Degradation Chart
# ---------------------------------------------------------------------------

def create_degradation_chart(
    comparisons: list[dict],
) -> discord.File | None:
    """Create a grouped bar chart comparing paper vs backtest metrics.

    Args:
        comparisons: List of dicts with keys ``strategy_name``,
            ``paper_sharpe``, ``backtest_sharpe``, ``paper_win_rate``,
            ``backtest_win_rate``, ``paper_pf``, ``backtest_pf``.

    Returns:
        ``discord.File`` or ``None``.
    """
    if not comparisons:
        return None

    try:
        names = [c.get("strategy_name", f"S{i}") for i, c in enumerate(comparisons)]
        paper_sharpe = [c.get("paper_sharpe", 0) for c in comparisons]
        bt_sharpe = [c.get("backtest_sharpe", 0) for c in comparisons]

        x = np.arange(len(names))
        width = 0.35

        fig, ax = plt.subplots(figsize=(14, 6))

        bars_paper = ax.bar(x - width / 2, paper_sharpe, width, label="Paper", color=_BLUE, alpha=0.85)
        bars_bt = ax.bar(x + width / 2, bt_sharpe, width, label="Backtest", color=_GRAY, alpha=0.85)

        # Delta annotations above each pair
        for i, (pv, bv) in enumerate(zip(paper_sharpe, bt_sharpe)):
            delta = pv - bv
            y_pos = max(pv, bv) + 0.05
            sign = "+" if delta >= 0 else ""
            ax.text(
                x[i], y_pos, f"{sign}{delta:.2f}",
                ha="center", va="bottom",
                color=_GREEN if delta >= 0 else _RED,
                fontsize=9, fontweight="bold",
            )

        ax.set_title("Paper vs Backtest Comparison", fontsize=14, fontweight="bold")
        ax.set_ylabel("Sharpe Ratio", fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=10)
        ax.legend(fontsize=10, framealpha=0.7)
        ax.grid(axis="y", alpha=0.2)
        plt.tight_layout()

        return _save_to_discord_file(fig, f"paper_degradation_{_timestamp()}.png")

    except Exception as exc:
        logger.error("Failed to create degradation chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


# ---------------------------------------------------------------------------
# 2f  Rolling Sharpe Chart
# ---------------------------------------------------------------------------

def create_rolling_sharpe_chart(
    rolling_data: list[dict],
    strategy_name: str,
    window: int = 20,
) -> discord.File | None:
    """Create a rolling Sharpe ratio chart with threshold lines.

    Args:
        rolling_data: List of dicts with ``date`` and ``rolling_sharpe``.
        strategy_name: Strategy label for the title.
        window: Rolling window size (for title display).

    Returns:
        ``discord.File`` or ``None``.
    """
    if not rolling_data:
        return None

    try:
        dates: list[datetime] = []
        sharpe_vals: list[float] = []
        for d in rolling_data:
            date_str = d.get("date", "")
            if isinstance(date_str, str) and len(date_str) >= 10:
                try:
                    dates.append(datetime.strptime(date_str[:10], "%Y-%m-%d"))
                except ValueError:
                    continue
            elif hasattr(date_str, "isoformat"):
                dates.append(
                    date_str if isinstance(date_str, datetime)
                    else datetime.combine(date_str, datetime.min.time())
                )
            else:
                continue
            sharpe_vals.append(d.get("rolling_sharpe", 0))

        if not dates:
            return None

        sharpe_arr = np.array(sharpe_vals)

        fig, ax = plt.subplots(figsize=(14, 5))

        # Rolling Sharpe line
        ax.plot(dates, sharpe_arr, color=_BLUE, linewidth=1.5, label="Rolling Sharpe")

        # Threshold lines
        ax.axhline(y=1.0, color=_GREEN, linestyle="--", linewidth=1, alpha=0.8, label="Promotion (1.0)")
        ax.axhline(y=0.5, color=_YELLOW, linestyle="--", linewidth=1, alpha=0.8, label="Warning (0.5)")
        ax.axhline(y=0.0, color=_RED, linestyle="--", linewidth=1, alpha=0.8, label="Zero")

        # Fills
        ax.fill_between(
            dates, sharpe_arr, 1.0,
            where=sharpe_arr >= 1.0,
            color=_GREEN, alpha=0.08, interpolate=True,
        )
        ax.fill_between(
            dates, sharpe_arr, 0.0,
            where=sharpe_arr <= 0.0,
            color=_RED, alpha=0.08, interpolate=True,
        )

        ax.set_title(
            f"{strategy_name} -- Rolling {window}-Trade Sharpe Ratio",
            fontsize=14, fontweight="bold",
        )
        ax.set_ylabel("Sharpe Ratio", fontsize=11)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax.legend(loc="upper left", fontsize=9, framealpha=0.7)
        ax.grid(alpha=0.2)
        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.tight_layout()

        slug = _strategy_slug(strategy_name)
        return _save_to_discord_file(fig, f"paper_rolling_sharpe_{slug}_{_timestamp()}.png")

    except Exception as exc:
        logger.error("Failed to create rolling Sharpe chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


# ---------------------------------------------------------------------------
# 2g  Win Rate Trend Chart
# ---------------------------------------------------------------------------

def create_win_rate_trend_chart(
    cumulative_data: list[dict],
    strategy_name: str,
) -> discord.File | None:
    """Create a win rate trend chart showing cumulative and rolling win rates.

    Args:
        cumulative_data: List of dicts with ``trade_number``,
            ``cumulative_win_rate``, ``rolling_10_wr``.
        strategy_name: Strategy label.

    Returns:
        ``discord.File`` or ``None``.
    """
    if not cumulative_data:
        return None

    try:
        trade_nums = [d.get("trade_number", i) for i, d in enumerate(cumulative_data)]
        cum_wr = [d.get("cumulative_win_rate", 0) for d in cumulative_data]
        rolling_wr = [d.get("rolling_10_wr", 0) for d in cumulative_data]

        fig, ax = plt.subplots(figsize=(14, 5))

        ax.plot(trade_nums, cum_wr, color=_BLUE, linewidth=1.5, label="Cumulative")
        ax.plot(trade_nums, rolling_wr, color=_YELLOW, linewidth=1.5, label="Rolling 10-Trade")

        # 50 % threshold
        ax.axhline(y=50, color=_GREEN, linestyle="--", linewidth=1, alpha=0.8, label="50 % Threshold")

        ax.set_title(f"{strategy_name} -- Win Rate Trend", fontsize=14, fontweight="bold")
        ax.set_xlabel("Trade Number", fontsize=11)
        ax.set_ylabel("Win Rate (%)", fontsize=11)
        ax.legend(loc="upper left", fontsize=9, framealpha=0.7)
        ax.grid(alpha=0.2)
        plt.tight_layout()

        slug = _strategy_slug(strategy_name)
        return _save_to_discord_file(fig, f"paper_winrate_{slug}_{_timestamp()}.png")

    except Exception as exc:
        logger.error("Failed to create win rate trend chart: %s", exc, exc_info=True)
        plt.close("all")
        return None


# ---------------------------------------------------------------------------
# 2h  Monthly P/L Heatmap
# ---------------------------------------------------------------------------

def create_monthly_pnl_heatmap(
    daily_pnl: list[dict],
    month: date,
) -> discord.File | None:
    """Create a calendar-style heatmap of daily P/L for a given month.

    Args:
        daily_pnl: List of dicts with ``date`` (str ``YYYY-MM-DD``) and
            ``pnl`` (float).
        month: ``date`` object whose year/month are used.

    Returns:
        ``discord.File`` or ``None``.
    """
    if not daily_pnl:
        return None

    try:
        # Build a lookup of day -> pnl
        pnl_by_day: dict[int, float] = {}
        for d in daily_pnl:
            date_str = d.get("date", "")
            pnl_val = d.get("pnl", 0)
            if isinstance(date_str, str) and len(date_str) >= 10:
                try:
                    dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    if dt.year == month.year and dt.month == month.month:
                        pnl_by_day[dt.day] = pnl_val
                except ValueError:
                    continue
            elif hasattr(date_str, "day"):
                if date_str.year == month.year and date_str.month == month.month:
                    pnl_by_day[date_str.day] = pnl_val

        if not pnl_by_day:
            return None

        # Build the calendar grid (weeks x 7)
        cal = calendar.Calendar(firstweekday=6)  # Sunday start
        month_days = cal.monthdayscalendar(month.year, month.month)

        n_weeks = len(month_days)
        grid = np.full((n_weeks, 7), np.nan)
        for week_idx, week in enumerate(month_days):
            for dow, day in enumerate(week):
                if day != 0 and day in pnl_by_day:
                    grid[week_idx, dow] = pnl_by_day[day]

        # Determine symmetric color limits for green/red centering
        valid = grid[~np.isnan(grid)]
        if len(valid) == 0:
            return None
        abs_max = max(abs(valid.min()), abs(valid.max()), 0.01)

        fig, ax = plt.subplots(figsize=(10, max(3, n_weeks * 0.7 + 1.5)))

        # Custom colormap: red -> black -> green
        from matplotlib.colors import LinearSegmentedColormap
        cmap = LinearSegmentedColormap.from_list(
            "pnl_rg", [_RED, "#1a1a1a", _GREEN],
        )
        cmap.set_bad(color="#111111")  # NaN cells

        im = ax.imshow(
            grid, cmap=cmap, vmin=-abs_max, vmax=abs_max,
            aspect="auto",
        )

        # Day labels inside cells
        for week_idx, week in enumerate(month_days):
            for dow, day in enumerate(week):
                if day != 0:
                    val = pnl_by_day.get(day)
                    label = str(day)
                    if val is not None:
                        label += f"\n${val:+.0f}"
                    ax.text(
                        dow, week_idx, label,
                        ha="center", va="center",
                        color="white", fontsize=7,
                    )

        # Axis labels
        ax.set_xticks(range(7))
        ax.set_xticklabels(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], fontsize=9)
        ax.set_yticks([])

        month_name = calendar.month_name[month.month]
        ax.set_title(
            f"Daily P/L Heatmap -- {month_name} {month.year}",
            fontsize=14, fontweight="bold",
        )

        fig.colorbar(im, ax=ax, label="P/L ($)", shrink=0.8)
        plt.tight_layout()

        month_str = f"{month.year}{month.month:02d}"
        return _save_to_discord_file(fig, f"paper_heatmap_{month_str}_{_timestamp()}.png")

    except Exception as exc:
        logger.error("Failed to create monthly P/L heatmap: %s", exc, exc_info=True)
        plt.close("all")
        return None
