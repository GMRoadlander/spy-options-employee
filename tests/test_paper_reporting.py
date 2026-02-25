"""Tests for PaperPerformanceReporter -- Step 3 of 4-7.

Covers daily, weekly, monthly reports, strategy performance, comparison,
degradation checks, rolling metrics, and equity curve helpers.

Uses AsyncMock for PaperTradingEngine, StrategyManager, and Store.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
import pytest_asyncio

from src.discord_bot.paper_reporting import PaperPerformanceReporter
from src.paper.models import PaperResults, PortfolioSummary


# ---------------------------------------------------------------------------
# Helper dataclass to mimic StrategyMetrics
# ---------------------------------------------------------------------------


@dataclass
class _FakeMetrics:
    sharpe_ratio: float = 1.5
    sortino_ratio: float = 2.0
    calmar_ratio: float = 1.2
    win_rate: float = 0.62
    profit_factor: float = 1.8
    expectancy: float = 45.0
    max_drawdown: float = -0.08
    max_drawdown_duration: float = 5.0
    avg_drawdown: float = -0.03
    avg_win: float = 120.0
    avg_loss: float = -60.0
    avg_holding_days: float = 2.5
    skewness: float = 0.3
    kurtosis: float = 3.1
    num_trades: int = 45


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_portfolio(**overrides: Any) -> PortfolioSummary:
    defaults = dict(
        starting_capital=100_000.0,
        total_equity=101_200.0,
        realized_pnl=1_000.0,
        unrealized_pnl=200.0,
        open_positions=3,
        total_trades=25,
        win_rate=0.60,
        sharpe_ratio=1.2,
        max_drawdown=-0.04,
        daily_pnl=150.0,
        strategies_active=["Iron Condor", "Put Spread"],
    )
    defaults.update(overrides)
    return PortfolioSummary(**defaults)


def _make_trades(count: int = 5, pnl_positive: bool = True) -> list[dict]:
    trades = []
    for i in range(count):
        pnl = 50.0 + i * 10 if pnl_positive else -(50.0 + i * 10)
        trades.append({
            "id": i + 1,
            "strategy_id": 1,
            "entry_date": "2025-01-10",
            "exit_date": "2025-01-15",
            "entry_price": 2.50,
            "exit_price": 2.00,
            "total_pnl": pnl,
            "fees": 5.20,
            "close_reason": "profit_target",
            "slippage_cost": 0.50,
            "strategy_name": "Iron Condor",
            "holding_days": 3,
        })
    return trades


def _make_paper_results(**overrides: Any) -> PaperResults:
    defaults = dict(
        strategy_id=1,
        strategy_name="Iron Condor",
        trades=_make_trades(15),
        metrics=_FakeMetrics(),
        equity_curve=[100000 + i * 100 for i in range(15)],
        days_in_paper=30,
        recommendation="PROMOTE",
    )
    defaults.update(overrides)
    return PaperResults(**defaults)


def _mock_cursor(rows: list | None = None, fetchone_val: Any = None):
    """Create a mock cursor that supports fetchall() and fetchone()."""
    cursor = AsyncMock()
    cursor.fetchall = AsyncMock(return_value=rows or [])
    cursor.fetchone = AsyncMock(return_value=fetchone_val)
    return cursor


def _make_db_mock(
    trade_rows: list | None = None,
    portfolio_rows: list | None = None,
    backtest_row: tuple | None = None,
    slippage_row: tuple | None = None,
    lifecycle_rows: list | None = None,
):
    """Build a DB mock whose .execute() returns appropriate cursors based on query."""
    db = AsyncMock()

    async def _execute(query: str, params=None):
        q = query.strip().lower()
        cursor = AsyncMock()

        if "from paper_trades" in q:
            cursor.fetchall = AsyncMock(return_value=trade_rows or [])
            cursor.fetchone = AsyncMock(return_value=None)
        elif "from paper_portfolio" in q:
            rows = portfolio_rows or []
            cursor.fetchall = AsyncMock(return_value=rows)
            cursor.fetchone = AsyncMock(
                return_value=rows[0] if rows else None,
            )
        elif "from backtest_results" in q:
            cursor.fetchall = AsyncMock(return_value=[backtest_row] if backtest_row else [])
            cursor.fetchone = AsyncMock(return_value=backtest_row)
        elif "from slippage_log" in q:
            cursor.fetchall = AsyncMock(return_value=[slippage_row] if slippage_row else [])
            cursor.fetchone = AsyncMock(return_value=slippage_row or (0.0, 0.0, 0, 0.0, None))
        elif "from strategy_transitions" in q:
            cursor.fetchall = AsyncMock(return_value=lifecycle_rows or [])
            cursor.fetchone = AsyncMock(return_value=None)
        else:
            cursor.fetchall = AsyncMock(return_value=[])
            cursor.fetchone = AsyncMock(return_value=None)
        return cursor

    db.execute = AsyncMock(side_effect=_execute)
    return db


def _make_reporter(
    engine: Any = None,
    manager: Any = None,
    store: Any = None,
    db: Any = None,
) -> PaperPerformanceReporter:
    if engine is None:
        engine = AsyncMock()
        engine.get_portfolio_summary = AsyncMock(return_value=_make_portfolio())
        engine.pnl_calculator = AsyncMock()
        engine.pnl_calculator.get_equity_curve = AsyncMock(return_value=[])
        engine.get_strategy_paper_results = AsyncMock(
            return_value=_make_paper_results(),
        )

    if manager is None:
        manager = AsyncMock()
        manager.list_strategies = AsyncMock(return_value=[
            {"id": 1, "name": "Iron Condor", "status": "paper",
             "template_yaml": "", "metadata": {}, "created_at": "", "updated_at": ""},
        ])
        manager.get = AsyncMock(return_value={
            "id": 1, "name": "Iron Condor", "status": "paper",
            "template_yaml": "", "metadata": {}, "created_at": "", "updated_at": "",
        })

    if store is None:
        store = MagicMock()
        if db is None:
            db = _make_db_mock()
        store._ensure_connected = MagicMock(return_value=db)

    return PaperPerformanceReporter(engine, manager, store)


# ---------------------------------------------------------------------------
# Tests: Daily Report (3b)
# ---------------------------------------------------------------------------


class TestDailyReport:
    @pytest.mark.asyncio
    async def test_daily_report_returns_embed_and_optional_chart(self):
        """Daily report returns at least one embed, optional chart."""
        reporter = _make_reporter()
        embeds, files = await reporter.daily_report(report_date=date(2025, 1, 15))

        assert len(embeds) >= 1
        assert isinstance(embeds[0], discord.Embed)
        assert isinstance(files, list)

    @pytest.mark.asyncio
    async def test_daily_report_no_paper_engine_returns_empty(self):
        """If paper engine is None, return empty."""
        reporter = _make_reporter(engine=None)
        reporter._engine = None
        embeds, files = await reporter.daily_report()

        assert embeds == []
        assert files == []

    @pytest.mark.asyncio
    async def test_daily_report_no_trades_still_shows_portfolio(self):
        """Even with no trades today, portfolio embed is generated."""
        db = _make_db_mock(trade_rows=[])
        reporter = _make_reporter(db=db)
        embeds, files = await reporter.daily_report(report_date=date(2025, 1, 15))

        assert len(embeds) >= 1
        # Should contain portfolio info
        assert "Paper Trading Daily Summary" in embeds[0].title


# ---------------------------------------------------------------------------
# Tests: Weekly Report (3c)
# ---------------------------------------------------------------------------


class TestWeeklyReport:
    @pytest.mark.asyncio
    async def test_weekly_report_returns_embeds_and_charts(self):
        """Weekly report returns 2 embeds and chart files."""
        reporter = _make_reporter()
        embeds, files = await reporter.weekly_report(
            week_end=date(2025, 1, 17),
        )

        assert len(embeds) == 2
        assert isinstance(files, list)

    @pytest.mark.asyncio
    async def test_weekly_report_two_strategies_shows_comparison(self):
        """With 2+ strategies, comparison chart is generated."""
        manager = AsyncMock()
        manager.list_strategies = AsyncMock(return_value=[
            {"id": 1, "name": "Iron Condor", "status": "paper",
             "template_yaml": "", "metadata": {}, "created_at": "", "updated_at": ""},
            {"id": 2, "name": "Put Spread", "status": "paper",
             "template_yaml": "", "metadata": {}, "created_at": "", "updated_at": ""},
        ])

        engine = AsyncMock()
        engine.get_portfolio_summary = AsyncMock(return_value=_make_portfolio())
        engine.pnl_calculator = AsyncMock()
        engine.pnl_calculator.get_equity_curve = AsyncMock(return_value=[])
        engine.get_strategy_paper_results = AsyncMock(
            return_value=_make_paper_results(),
        )

        reporter = _make_reporter(engine=engine, manager=manager)

        with patch(
            "src.discord_bot.paper_reporting.create_strategy_comparison_chart",
            return_value=MagicMock(spec=discord.File),
        ) as mock_chart:
            embeds, files = await reporter.weekly_report(
                week_end=date(2025, 1, 17),
            )
            mock_chart.assert_called_once()

    @pytest.mark.asyncio
    async def test_weekly_report_single_strategy_no_comparison_chart(self):
        """With only 1 strategy, no comparison chart is generated."""
        reporter = _make_reporter()

        with patch(
            "src.discord_bot.paper_reporting.create_strategy_comparison_chart",
        ) as mock_chart:
            embeds, files = await reporter.weekly_report(
                week_end=date(2025, 1, 17),
            )
            mock_chart.assert_not_called()

    @pytest.mark.asyncio
    async def test_weekly_report_promotion_readiness_format(self):
        """Promotion readiness is included in weekly embeds."""
        reporter = _make_reporter()
        embeds, _ = await reporter.weekly_report(week_end=date(2025, 1, 17))

        # Second embed should contain promotion readiness
        assert len(embeds) == 2
        fields = [f.name for f in embeds[1].fields]
        assert "Promotion Readiness" in fields


# ---------------------------------------------------------------------------
# Tests: Monthly Report (3d)
# ---------------------------------------------------------------------------


class TestMonthlyReport:
    @pytest.mark.asyncio
    async def test_monthly_report_returns_multiple_embeds(self):
        """Monthly report returns 3+ embeds."""
        reporter = _make_reporter()
        embeds, files = await reporter.monthly_report(month=date(2025, 1, 1))

        assert len(embeds) >= 3
        assert isinstance(files, list)

    @pytest.mark.asyncio
    async def test_monthly_report_slippage_analysis_queries(self):
        """Monthly report queries slippage data."""
        db = _make_db_mock(
            slippage_row=(0.04, 32.40, 150, 0.12, "2025-01-10"),
        )
        reporter = _make_reporter(db=db)
        embeds, _ = await reporter.monthly_report(month=date(2025, 1, 1))

        # Should have execution quality embed
        titles = [e.title for e in embeds]
        assert "Execution Quality Analysis" in titles

    @pytest.mark.asyncio
    async def test_monthly_report_shadow_comparison_per_strategy(self):
        """Monthly report includes shadow comparison for each strategy."""
        reporter = _make_reporter()
        embeds, _ = await reporter.monthly_report(month=date(2025, 1, 1))

        titles = [e.title for e in embeds]
        assert "Paper vs Backtest Comparison" in titles

    @pytest.mark.asyncio
    async def test_monthly_report_lifecycle_events_conditional(self):
        """Lifecycle embed only appears if events exist."""
        # No lifecycle events
        reporter = _make_reporter()
        embeds_no_events, _ = await reporter.monthly_report(month=date(2025, 1, 1))
        titles_no = [e.title for e in embeds_no_events]
        assert "Strategy Lifecycle Events" not in titles_no

        # With lifecycle events
        db = _make_db_mock(
            lifecycle_rows=[
                ("2025-01-05T10:00:00", "Iron Condor", "backtest", "paper", "passed gates"),
            ],
        )
        reporter2 = _make_reporter(db=db)
        embeds_with, _ = await reporter2.monthly_report(month=date(2025, 1, 1))
        titles_with = [e.title for e in embeds_with]
        assert "Strategy Lifecycle Events" in titles_with

    @pytest.mark.asyncio
    async def test_monthly_report_degradation_chart_generated(self):
        """Monthly report generates degradation chart."""
        reporter = _make_reporter()
        with patch(
            "src.discord_bot.paper_reporting.create_degradation_chart",
            return_value=MagicMock(spec=discord.File),
        ) as mock_chart:
            _, files = await reporter.monthly_report(month=date(2025, 1, 1))
            mock_chart.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: Strategy Performance Report (3e)
# ---------------------------------------------------------------------------


class TestStrategyPerformance:
    @pytest.mark.asyncio
    async def test_strategy_performance_report_with_backtest(self):
        """Strategy report with backtest comparison data."""
        bt_row = (1.45, 2.1, 0.65, -0.06, 2.1, 40)
        db = _make_db_mock(backtest_row=bt_row)
        reporter = _make_reporter(db=db)

        embeds, files = await reporter.strategy_performance_report("Iron Condor")

        assert len(embeds) == 2
        assert "Paper Performance" in embeds[0].title

    @pytest.mark.asyncio
    async def test_strategy_performance_report_without_backtest(self):
        """Strategy report works gracefully without backtest data."""
        db = _make_db_mock(backtest_row=None)
        reporter = _make_reporter(db=db)

        embeds, files = await reporter.strategy_performance_report("Iron Condor")

        assert len(embeds) == 2
        # Should show "No backtest data"
        comparison_embed = embeds[1]
        shadow_fields = [f for f in comparison_embed.fields if f.name == "Shadow Comparison"]
        assert len(shadow_fields) == 1
        assert "No backtest data" in shadow_fields[0].value

    @pytest.mark.asyncio
    async def test_strategy_performance_charts_generated(self):
        """Strategy report attempts to generate charts."""
        db = _make_db_mock(
            trade_rows=[
                ("2025-01-10", 50.0, 5.0),
                ("2025-01-11", 60.0, 5.0),
                ("2025-01-12", -30.0, 5.0),
            ],
        )
        reporter = _make_reporter(db=db)

        with patch(
            "src.discord_bot.paper_reporting.create_paper_equity_drawdown_chart",
        ) as mock_eq, patch(
            "src.discord_bot.paper_reporting.create_rolling_sharpe_chart",
        ) as mock_rs, patch(
            "src.discord_bot.paper_reporting.create_win_rate_trend_chart",
        ) as mock_wr:
            embeds, files = await reporter.strategy_performance_report("Iron Condor")
            assert len(embeds) == 2


# ---------------------------------------------------------------------------
# Tests: Strategy Comparison Report (3f)
# ---------------------------------------------------------------------------


class TestStrategyComparison:
    @pytest.mark.asyncio
    async def test_strategy_comparison_all_paper_strategies(self):
        """Comparison with no explicit names compares all PAPER strategies."""
        manager = AsyncMock()
        manager.list_strategies = AsyncMock(return_value=[
            {"id": 1, "name": "IC", "status": "paper",
             "template_yaml": "", "metadata": {}, "created_at": "", "updated_at": ""},
            {"id": 2, "name": "PS", "status": "paper",
             "template_yaml": "", "metadata": {}, "created_at": "", "updated_at": ""},
        ])
        engine = AsyncMock()
        engine.get_strategy_paper_results = AsyncMock(
            return_value=_make_paper_results(),
        )

        reporter = _make_reporter(engine=engine, manager=manager)
        embeds, files = await reporter.strategy_comparison_report()

        assert len(embeds) == 1
        assert embeds[0].title == "Paper Strategy Comparison"

    @pytest.mark.asyncio
    async def test_strategy_comparison_specific_names(self):
        """Comparison with specific names filters correctly."""
        manager = AsyncMock()
        manager.list_strategies = AsyncMock(return_value=[
            {"id": 1, "name": "IC", "status": "paper",
             "template_yaml": "", "metadata": {}, "created_at": "", "updated_at": ""},
            {"id": 2, "name": "PS", "status": "paper",
             "template_yaml": "", "metadata": {}, "created_at": "", "updated_at": ""},
            {"id": 3, "name": "Straddle", "status": "paper",
             "template_yaml": "", "metadata": {}, "created_at": "", "updated_at": ""},
        ])
        manager.get = AsyncMock(return_value=None)

        # find_strategy uses get() for int, list_strategies for name
        async def _find_by_name(name_or_id):
            for s in await manager.list_strategies():
                if s["name"].lower() == name_or_id.lower():
                    return s
            return None

        engine = AsyncMock()
        engine.get_strategy_paper_results = AsyncMock(
            return_value=_make_paper_results(),
        )

        reporter = _make_reporter(engine=engine, manager=manager)
        reporter._find_strategy = _find_by_name

        embeds, _ = await reporter.strategy_comparison_report(
            strategy_names=["IC", "PS"],
        )
        assert len(embeds) == 1

    @pytest.mark.asyncio
    async def test_strategy_comparison_max_four(self):
        """Comparison caps at 4 strategies."""
        names = [f"Strategy{i}" for i in range(6)]
        manager = AsyncMock()
        strats = [
            {"id": i, "name": n, "status": "paper",
             "template_yaml": "", "metadata": {}, "created_at": "", "updated_at": ""}
            for i, n in enumerate(names, 1)
        ]
        manager.list_strategies = AsyncMock(return_value=strats)
        engine = AsyncMock()
        engine.get_strategy_paper_results = AsyncMock(
            return_value=_make_paper_results(),
        )

        reporter = _make_reporter(engine=engine, manager=manager)
        embeds, _ = await reporter.strategy_comparison_report()

        # The embed should have at most 4 strategy fields
        embed = embeds[0]
        # Count strategy fields (non-"No Strategies" fields)
        strat_fields = [
            f for f in embed.fields
            if f.name != "No Strategies"
        ]
        assert len(strat_fields) <= 4


# ---------------------------------------------------------------------------
# Tests: Degradation Check (3g)
# ---------------------------------------------------------------------------


class TestDegradation:
    @pytest.mark.asyncio
    async def test_check_degradation_no_alerts_when_consistent(self):
        """No alerts when paper metrics are consistent with backtest."""
        # Paper sharpe=1.5, bt sharpe=1.45 => deviation = +0.05, no alert
        bt_row = (1.45, 2.0, 0.60, -0.06, 1.8, 40)
        db = _make_db_mock(backtest_row=bt_row)
        reporter = _make_reporter(db=db)

        alerts = await reporter.check_degradation()
        assert alerts == []

    @pytest.mark.asyncio
    async def test_check_degradation_sharpe_alert(self):
        """Alert fires when paper Sharpe is much lower than backtest."""
        # Paper sharpe=1.5, bt sharpe=2.5 => deviation = -1.0, alert
        bt_row = (2.5, 3.0, 0.62, -0.06, 2.0, 40)
        db = _make_db_mock(backtest_row=bt_row)

        metrics = _FakeMetrics(sharpe_ratio=1.5)
        results = _make_paper_results(metrics=metrics)
        engine = AsyncMock()
        engine.get_strategy_paper_results = AsyncMock(return_value=results)

        reporter = _make_reporter(engine=engine, db=db)

        alerts = await reporter.check_degradation()
        assert len(alerts) >= 1
        # Verify the alert mentions Sharpe in its fields
        field_texts = " ".join(f.value for a in alerts for f in a.fields)
        assert "Sharpe" in field_texts

    @pytest.mark.asyncio
    async def test_check_degradation_win_rate_alert(self):
        """Alert fires when paper win rate deviates significantly."""
        # Paper wr=0.40, bt wr=0.65 => deviation = -0.25, alert
        bt_row = (1.5, 2.0, 0.65, -0.06, 1.8, 40)
        db = _make_db_mock(backtest_row=bt_row)

        metrics = _FakeMetrics(win_rate=0.40)
        results = _make_paper_results(metrics=metrics)
        engine = AsyncMock()
        engine.get_strategy_paper_results = AsyncMock(return_value=results)

        reporter = _make_reporter(engine=engine, db=db)

        alerts = await reporter.check_degradation()
        assert len(alerts) >= 1
        # Verify the alert mentions Win Rate in its fields
        field_texts = " ".join(f.value for a in alerts for f in a.fields)
        assert "Win Rate" in field_texts

    @pytest.mark.asyncio
    async def test_check_degradation_max_dd_alert(self):
        """Alert fires when paper max DD exceeds threshold ratio of backtest."""
        # Paper DD=-0.20, bt DD=-0.05 => ratio = 4.0 > 1.5, alert
        bt_row = (1.5, 2.0, 0.62, -0.05, 1.8, 40)
        db = _make_db_mock(backtest_row=bt_row)

        metrics = _FakeMetrics(max_drawdown=-0.20)
        results = _make_paper_results(metrics=metrics)
        engine = AsyncMock()
        engine.get_strategy_paper_results = AsyncMock(return_value=results)

        reporter = _make_reporter(engine=engine, db=db)

        alerts = await reporter.check_degradation()
        assert len(alerts) >= 1
        # Verify the alert mentions Max Drawdown in its fields
        field_texts = " ".join(f.value for a in alerts for f in a.fields)
        assert "Max Drawdown" in field_texts

    @pytest.mark.asyncio
    async def test_check_degradation_skips_strategies_under_10_trades(self):
        """Strategies with < 10 trades are skipped."""
        results = _make_paper_results(trades=_make_trades(5))
        engine = AsyncMock()
        engine.get_strategy_paper_results = AsyncMock(return_value=results)

        bt_row = (2.5, 3.0, 0.65, -0.06, 2.0, 40)
        db = _make_db_mock(backtest_row=bt_row)

        reporter = _make_reporter(engine=engine, db=db)

        alerts = await reporter.check_degradation()
        assert alerts == []


# ---------------------------------------------------------------------------
# Tests: Rolling Metrics Helper (3h)
# ---------------------------------------------------------------------------


class TestRollingMetrics:
    @pytest.mark.asyncio
    async def test_rolling_metrics_correct_window(self):
        """Rolling metrics uses the correct window of trades."""
        # Build DB rows: (exit_date, total_pnl, fees)
        trade_rows = [
            (f"2025-01-{20 - i:02d}", 50.0 + i * 10, 5.0)
            for i in range(10)
        ]
        db = _make_db_mock(trade_rows=trade_rows)
        reporter = _make_reporter(db=db)

        result = await reporter._get_rolling_metrics(strategy_id=1, window_trades=10)

        assert result["trade_count"] == 10
        assert result["rolling_wr"] > 0
        assert result["rolling_sharpe"] != 0

    @pytest.mark.asyncio
    async def test_rolling_metrics_consecutive_losses(self):
        """Consecutive losses counted from the most recent trade backwards."""
        # SQL returns DESC order (most recent first); mock must match.
        # After reversed() in the code, chronological order is:
        #   win, win, loss, loss, loss  => 3 consecutive losses at end
        trade_rows = [
            ("2025-01-14", -30.0, 5.0),  # loss (most recent)
            ("2025-01-13", -20.0, 5.0),  # loss
            ("2025-01-12", -10.0, 5.0),  # loss
            ("2025-01-11", 60.0, 5.0),   # win
            ("2025-01-10", 50.0, 5.0),   # win (oldest)
        ]
        db = _make_db_mock(trade_rows=trade_rows)
        reporter = _make_reporter(db=db)

        result = await reporter._get_rolling_metrics(strategy_id=1, window_trades=5)

        # After reversal to chronological order, last 3 are losses
        assert result["consecutive_losses"] == 3

    @pytest.mark.asyncio
    async def test_rolling_metrics_empty_trades(self):
        """Empty trades return zero metrics."""
        db = _make_db_mock(trade_rows=[])
        reporter = _make_reporter(db=db)

        result = await reporter._get_rolling_metrics(strategy_id=1)

        assert result["trade_count"] == 0
        assert result["rolling_sharpe"] == 0.0
        assert result["rolling_wr"] == 0.0
        assert result["consecutive_losses"] == 0


# ---------------------------------------------------------------------------
# Tests: Strategy Equity Curve Helper (3i)
# ---------------------------------------------------------------------------


class TestEquityCurve:
    @pytest.mark.asyncio
    async def test_strategy_equity_curve_cumulative(self):
        """Equity curve builds cumulative PnL correctly."""
        trade_rows = [
            ("2025-01-10", 100.0),  # net_pnl (total_pnl - fees)
            ("2025-01-10", 50.0),
            ("2025-01-12", -30.0),
        ]

        db = AsyncMock()

        async def _execute(query, params=None):
            cursor = AsyncMock()
            cursor.fetchall = AsyncMock(return_value=trade_rows)
            cursor.fetchone = AsyncMock(return_value=None)
            return cursor

        db.execute = AsyncMock(side_effect=_execute)
        store = MagicMock()
        store._ensure_connected = MagicMock(return_value=db)

        reporter = _make_reporter(store=store)

        result = await reporter._get_strategy_equity_curve(strategy_id=1, days=30)

        assert len(result) > 0
        # First day: 100 + 50 = 150
        first_day = [r for r in result if r["date"] == "2025-01-10"]
        assert len(first_day) == 1
        assert first_day[0]["cumulative_pnl"] == 150.0

    @pytest.mark.asyncio
    async def test_strategy_equity_curve_fills_gaps(self):
        """Equity curve fills forward for dates with no trades."""
        trade_rows = [
            ("2025-01-10", 100.0),
            ("2025-01-13", 50.0),
        ]

        db = AsyncMock()

        async def _execute(query, params=None):
            cursor = AsyncMock()
            cursor.fetchall = AsyncMock(return_value=trade_rows)
            cursor.fetchone = AsyncMock(return_value=None)
            return cursor

        db.execute = AsyncMock(side_effect=_execute)
        store = MagicMock()
        store._ensure_connected = MagicMock(return_value=db)

        reporter = _make_reporter(store=store)

        result = await reporter._get_strategy_equity_curve(strategy_id=1, days=30)

        # Should have entries for 2025-01-10, 11, 12, 13, ...
        dates = [r["date"] for r in result]
        assert "2025-01-10" in dates
        assert "2025-01-11" in dates
        assert "2025-01-12" in dates
        assert "2025-01-13" in dates

        # Jan 11 and 12 should carry forward the cumulative from Jan 10
        jan11 = [r for r in result if r["date"] == "2025-01-11"]
        assert len(jan11) == 1
        assert jan11[0]["cumulative_pnl"] == 100.0  # forward fill
