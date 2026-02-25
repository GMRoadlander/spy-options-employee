"""Tests for paper trading embed builder functions.

Phase 4-6 tests (from embeds.py):
    - build_paper_status_embed (8 tests)
    - build_paper_history_embed (5 tests)
    - build_paper_position_detail_embed (4 tests)
    - build_paper_daily_pnl_embed (3 tests)
    - build_paper_fill_alert_embed (2 tests)
    - _build_option_desc (7 tests)

Phase 4-7 tests (from paper_embeds.py):
    - build_paper_daily_summary_embed (5 tests)
    - build_paper_weekly_review_embed (3 tests)
    - build_paper_monthly_report_embeds (4 tests)
    - build_paper_strategy_performance_embed (3 tests)
    - build_degradation_alert_embed (1 test)
    - build_paper_strategy_comparison_embed (2 tests)
    - Discord limits (2 tests)
"""

import json
import unittest
from dataclasses import dataclass
from datetime import date, datetime, timezone

import discord
import pytest

from src.discord_bot.embeds import (
    COLOR_BEARISH,
    COLOR_BULLISH,
    COLOR_INFO,
    COLOR_NEUTRAL,
    _build_option_desc,
    build_paper_daily_pnl_embed,
    build_paper_fill_alert_embed,
    build_paper_history_embed,
    build_paper_position_detail_embed,
    build_paper_status_embed,
)
from src.discord_bot.paper_embeds import (
    build_paper_daily_summary_embed,
    build_paper_weekly_review_embed,
    build_paper_monthly_report_embeds,
    build_paper_strategy_performance_embed,
    build_degradation_alert_embed,
    build_paper_strategy_comparison_embed,
)
from src.paper.models import PortfolioSummary


# ===========================================================================
# Shared Fixtures / Helpers
# ===========================================================================


def _sample_portfolio(**overrides) -> PortfolioSummary:
    """Create a sample PortfolioSummary for testing."""
    defaults = dict(
        starting_capital=100_000.0,
        total_equity=101_250.0,
        realized_pnl=950.0,
        unrealized_pnl=300.0,
        open_positions=3,
        total_trades=15,
        win_rate=0.6,
        sharpe_ratio=1.23,
        max_drawdown=-0.025,
        daily_pnl=125.0,
        strategies_active=["Iron Condor Weekly", "Put Spread 0DTE"],
    )
    defaults.update(overrides)
    return PortfolioSummary(**defaults)


# ===========================================================================
# Phase 4-6 Fixtures
# ===========================================================================


def _sample_position(pid=1, strategy_id=1, **overrides):
    """Create a sample position dict."""
    legs = [
        {"leg_name": "short_call", "option_type": "call", "strike": 5100,
         "expiry": "2026-03-15", "action": "sell", "quantity": 1,
         "fill_price": 2.50, "delta": -0.15},
        {"leg_name": "long_call", "option_type": "call", "strike": 5110,
         "expiry": "2026-03-15", "action": "buy", "quantity": 1,
         "fill_price": 1.50, "delta": -0.10},
        {"leg_name": "short_put", "option_type": "put", "strike": 4900,
         "expiry": "2026-03-15", "action": "sell", "quantity": 1,
         "fill_price": 2.00, "delta": 0.12},
        {"leg_name": "long_put", "option_type": "put", "strike": 4890,
         "expiry": "2026-03-15", "action": "buy", "quantity": 1,
         "fill_price": 1.00, "delta": 0.08},
    ]
    pos = {
        "id": pid,
        "strategy_id": strategy_id,
        "status": "open",
        "opened_at": "2026-02-20 10:30:00",
        "legs": json.dumps(legs),
        "entry_price": 2.00,
        "current_mark": 1.50,
        "unrealized_pnl": 50.0,
        "max_profit": 200.0,
        "max_loss": -800.0,
        "last_mark_at": "2026-02-24 15:45:00",
        "quantity": 1,
        "open_order_id": 1,
        "strategy_name": "Iron Condor Weekly",
    }
    pos.update(overrides)
    return pos


def _sample_trade(tid=1, strategy_id=1, **overrides):
    """Create a sample trade dict."""
    trade = {
        "id": tid,
        "strategy_id": strategy_id,
        "strategy_name": "Iron Condor Weekly",
        "entry_date": "2026-02-15",
        "exit_date": "2026-02-20",
        "holding_days": 5,
        "entry_price": 2.00,
        "exit_price": 0.50,
        "total_pnl": 150.0,
        "fees": 5.20,
        "slippage_cost": 2.00,
        "close_reason": "profit_target",
    }
    trade.update(overrides)
    return trade


def _sample_fill(**overrides):
    """Create a sample fill dict."""
    fill = {
        "leg_name": "short_call",
        "action": "sell",
        "option_type": "call",
        "strike": 5100,
        "expiry": "2026-03-15",
        "fill_price": 2.5000,
        "bid": 2.40,
        "ask": 2.60,
        "mid": 2.5000,
        "slippage": 0.0050,
        "iv": 0.22,
        "delta": -0.15,
    }
    fill.update(overrides)
    return fill


# ===========================================================================
# Phase 4-7 Fixtures
# ===========================================================================


def _sample_day_trades(count: int = 3, pnl_positive: bool = True) -> list[dict]:
    """Create sample day trade dicts."""
    trades = []
    for i in range(count):
        pnl = (50.0 + i * 10) if pnl_positive else (-50.0 - i * 10)
        trades.append({
            "exit_time": f"15:{30 + i}",
            "strategy_name": f"Strategy {i + 1}",
            "close_reason": "profit_target" if pnl_positive else "stop_loss",
            "option_desc": f"SPX Mar15 {5000 + i * 10}/{5010 + i * 10} IC",
            "exit_price": 0.50,
            "total_pnl": pnl,
            "fees": 5.0,
            "exit_date": "2026-02-24",
        })
    return trades


def _sample_strategy_snapshots() -> list[dict]:
    """Create sample strategy snapshot dicts."""
    return [
        {"name": "Iron Condor", "sharpe": 1.23, "win_rate": 0.62, "pnl": 280.0},
        {"name": "Put Spread", "sharpe": 0.89, "win_rate": 0.58, "pnl": 160.0},
    ]


def _sample_risk_status(has_warnings: bool = False) -> dict:
    """Create sample risk status dict."""
    if has_warnings:
        return {"warnings": ["Max position size at 85%"]}
    return {"warnings": []}


def _sample_strategy_comparison() -> list[dict]:
    """Create sample strategy comparison dicts."""
    return [
        {
            "name": "Iron Condor",
            "paper_pnl": 280.0,
            "bt_expected": 310.0,
            "delta": -30.0,
            "sharpe": 1.23,
            "win_rate": 62.0,
        },
        {
            "name": "Put Spread",
            "paper_pnl": 160.0,
            "bt_expected": 140.0,
            "delta": 20.0,
            "sharpe": 0.89,
            "win_rate": 58.0,
        },
    ]


def _sample_weekly_trades(count: int = 5) -> list[dict]:
    """Create sample weekly trade dicts."""
    trades = []
    for i in range(count):
        pnl = 100.0 - i * 50  # Mix of wins and losses
        trades.append({
            "strategy_name": f"Strategy {(i % 2) + 1}",
            "exit_date": f"2026-02-{20 + i}",
            "total_pnl": pnl,
            "fees": 5.0,
        })
    return trades


def _sample_promotion_readiness() -> list[dict]:
    """Create sample promotion readiness dicts."""
    return [
        {
            "name": "Iron Condor Weekly",
            "ready": True,
            "criteria_met": 6,
            "criteria_total": 6,
            "detail": "",
        },
        {
            "name": "Put Credit Spread",
            "ready": False,
            "criteria_met": 2,
            "criteria_total": 6,
            "detail": "need 18 trades, 6 days",
        },
    ]


def _sample_risk_evolution() -> list[dict]:
    """Create sample risk evolution dicts."""
    return [
        {"metric": "Max Drawdown", "last_week": "$320", "this_week": "$280", "change": "Improved"},
        {"metric": "Avg Daily Theta", "last_week": "-$42", "this_week": "-$38", "change": "Improved"},
    ]


@dataclass
class _MockMetrics:
    """Mock StrategyMetrics for testing."""
    sharpe_ratio: float = 1.23
    sortino_ratio: float = 1.50
    calmar_ratio: float = 2.10
    win_rate: float = 0.62
    profit_factor: float = 1.80
    expectancy: float = 45.0
    max_drawdown: float = -0.08
    max_drawdown_duration: float = 5.0
    avg_drawdown: float = -0.03
    avg_win: float = 85.0
    avg_loss: float = -40.0
    avg_holding_days: float = 3.2
    skewness: float = 0.45
    kurtosis: float = 3.10


def _sample_promotion_criteria(all_pass: bool = True) -> list[dict]:
    """Create sample promotion criteria dicts."""
    criteria = [
        {"name": "Min Trades (30)", "passed": True, "value": "45/30"},
        {"name": "Min Days (14)", "passed": True, "value": "28/14"},
        {"name": "Sharpe > 1.0", "passed": True, "value": "1.23"},
        {"name": "Win Rate > 50%", "passed": True, "value": "62%"},
        {"name": "Max DD < 15%", "passed": True, "value": "8%"},
        {"name": "Profit Factor > 1.3", "passed": True, "value": "1.8"},
    ]
    if not all_pass:
        criteria[0]["passed"] = False
        criteria[0]["value"] = "15/30"
        criteria[4]["passed"] = False
        criteria[4]["value"] = "18%"
    return criteria


def _sample_backtest_metrics() -> dict:
    """Create sample backtest metrics dict."""
    return {
        "sharpe_ratio": 1.45,
        "win_rate": 0.65,
        "avg_pnl": 52.0,
        "max_drawdown": -0.06,
        "profit_factor": 2.1,
    }


def _sample_shadow_comparison() -> list[dict]:
    """Create sample shadow comparison dicts."""
    return [
        {
            "strategy_name": "Iron Condor",
            "paper_sharpe": 1.23,
            "backtest_sharpe": 1.45,
            "sharpe_delta": -0.22,
            "paper_wr": 0.62,
            "backtest_wr": 0.65,
            "wr_delta": -0.03,
            "paper_avg_pnl": 45.0,
            "backtest_avg_pnl": 52.0,
            "avg_pnl_delta": -7.0,
            "paper_max_dd": 0.08,
            "backtest_max_dd": 0.06,
            "max_dd_delta": 0.02,
            "verdict": "CONSISTENT",
        },
    ]


def _sample_slippage_analysis() -> dict:
    """Create sample slippage analysis dict."""
    return {
        "avg_slippage": 0.04,
        "total_slip_cost": 32.40,
        "fill_rate": 0.97,
        "fills_first_tick": 145,
        "fills_total": 150,
        "worst_slippage": 0.12,
        "worst_date": "2026-02-15",
        "worst_option_desc": "SPX Mar15 5100C",
        "by_strategy": [
            {"name": "Iron Condor", "avg_slippage": 0.03},
            {"name": "Put Spread", "avg_slippage": 0.05},
        ],
        "model_accuracy": 0.92,
    }


def _sample_aggregate_metrics() -> dict:
    """Create sample aggregate metrics."""
    return {
        "starting_equity": 100_000.0,
        "ending_equity": 101_800.0,
        "month_pnl": 1_800.0,
        "total_trades": 30,
        "win_rate": 0.60,
        "sharpe": 1.15,
        "max_drawdown": -0.05,
        "active_strategies": 3,
        "avg_holding_days": 4.2,
    }


def _sample_lifecycle_events() -> list[dict]:
    """Create sample strategy lifecycle events."""
    return [
        {
            "date": "2026-02-05",
            "strategy": "Iron Condor",
            "description": "entered PAPER",
            "recommendation": "PROMOTE",
            "rec_detail": "all criteria met, consistent with backtest",
        },
        {
            "date": "2026-02-18",
            "strategy": "Put Spread",
            "description": "met promotion criteria (30+ trades)",
            "recommendation": "CONTINUE",
            "rec_detail": "needs 12 more trades",
        },
    ]


def _total_embed_chars(embed: discord.Embed) -> int:
    """Compute total character count in an embed."""
    total = len(embed.title or "") + len(embed.description or "")
    for f in embed.fields:
        total += len(f.name) + len(f.value)
    if embed.footer and embed.footer.text:
        total += len(embed.footer.text)
    return total


def _max_field_value_len(embed: discord.Embed) -> int:
    """Get the longest field value in an embed."""
    if not embed.fields:
        return 0
    return max(len(f.value) for f in embed.fields)


# ###########################################################################
#
#  PHASE 4-6 TESTS (from src.discord_bot.embeds)
#
# ###########################################################################


# -- build_paper_status_embed tests ------------------------------------------


class TestBuildPaperStatusEmbed(unittest.TestCase):
    """Tests for build_paper_status_embed."""

    def test_positive_pnl_color(self):
        """Positive daily_pnl gives COLOR_BULLISH."""
        portfolio = _sample_portfolio(daily_pnl=125.0)
        embed = build_paper_status_embed(portfolio, [], [])
        self.assertEqual(embed.color.value, COLOR_BULLISH)

    def test_negative_pnl_color(self):
        """Negative daily_pnl gives COLOR_BEARISH."""
        portfolio = _sample_portfolio(daily_pnl=-50.0)
        embed = build_paper_status_embed(portfolio, [], [])
        self.assertEqual(embed.color.value, COLOR_BEARISH)

    def test_zero_pnl_color(self):
        """Zero daily_pnl gives COLOR_NEUTRAL."""
        portfolio = _sample_portfolio(daily_pnl=0.0)
        embed = build_paper_status_embed(portfolio, [], [])
        self.assertEqual(embed.color.value, COLOR_NEUTRAL)

    def test_positions_display(self):
        """Positions are displayed with correct count."""
        portfolio = _sample_portfolio()
        positions = [
            _sample_position(1, strategy_name="Strat A"),
            _sample_position(2, strategy_name="Strat B"),
            _sample_position(3, strategy_name="Strat C"),
        ]
        embed = build_paper_status_embed(portfolio, positions, [])

        pos_field = [f for f in embed.fields if "Active Positions" in f.name]
        self.assertEqual(len(pos_field), 1)
        self.assertIn("(3)", pos_field[0].name)
        self.assertIn("Strat A", pos_field[0].value)
        self.assertIn("Strat B", pos_field[0].value)
        self.assertIn("Strat C", pos_field[0].value)

    def test_no_positions(self):
        """Empty positions shows 'No open positions'."""
        portfolio = _sample_portfolio()
        embed = build_paper_status_embed(portfolio, [], [])

        pos_field = [f for f in embed.fields if "Active Positions" in f.name]
        self.assertEqual(len(pos_field), 1)
        self.assertIn("No open positions", pos_field[0].value)

    def test_fills_display(self):
        """Today's fills are displayed with correct count."""
        portfolio = _sample_portfolio()
        fills = [
            {"id": 1, "strategy_id": 1, "direction": "open",
             "fill_price": 2.00, "slippage": 0.005, "filled_at": "2026-02-24 10:30:00"},
            {"id": 2, "strategy_id": 1, "direction": "close",
             "fill_price": 0.50, "slippage": 0.003, "filled_at": "2026-02-24 14:30:00"},
        ]
        embed = build_paper_status_embed(portfolio, [], fills)

        trade_fields = [f for f in embed.fields if "Today's Trades" in f.name]
        self.assertEqual(len(trade_fields), 1)
        # Should have 5 fills -> "(5)" in name
        self.assertIn("(2)", trade_fields[0].name)

    def test_char_limit(self):
        """Embed total chars stay under 6000 with many positions."""
        portfolio = _sample_portfolio()
        positions = []
        for i in range(10):
            legs = [
                {"leg_name": f"leg_{j}", "option_type": "call", "strike": 5000 + j * 10,
                 "expiry": "2026-03-15", "action": "sell", "quantity": 1,
                 "fill_price": 2.50, "delta": -0.15}
                for j in range(4)
            ]
            positions.append({
                "id": i,
                "strategy_id": 1,
                "strategy_name": f"Very Long Strategy Name Number {i} for Testing",
                "legs": json.dumps(legs),
                "entry_price": 2.00,
                "current_mark": 1.50,
                "unrealized_pnl": 50.0,
            })
        embed = build_paper_status_embed(portfolio, positions, [])

        total_chars = len(embed.title or "") + len(embed.description or "")
        for f in embed.fields:
            total_chars += len(f.name) + len(f.value)
        self.assertLess(total_chars, 6000)

    def test_all_fields_present(self):
        """All required fields are present."""
        portfolio = _sample_portfolio()
        embed = build_paper_status_embed(portfolio, [], [])

        field_names = {f.name for f in embed.fields}
        self.assertIn("Active Positions (0)", field_names)
        self.assertIn("Total P/L", field_names)
        self.assertIn("Win Rate", field_names)
        self.assertIn("Trades", field_names)
        self.assertIn("Sharpe", field_names)
        self.assertIn("Max DD", field_names)
        self.assertIn("Strategies", field_names)
        self.assertGreaterEqual(len(embed.fields), 6)


# -- build_paper_history_embed tests -----------------------------------------


class TestBuildPaperHistoryEmbed(unittest.TestCase):
    """Tests for build_paper_history_embed."""

    def test_pagination(self):
        """Pagination shows correct range in description."""
        trades = [_sample_trade(i) for i in range(25)]
        embed = build_paper_history_embed(trades, None, 7, page=2, page_size=15)

        self.assertIn("16-25 of 25", embed.description)
        self.assertIn("Page 2/2", embed.footer.text)

    def test_summary_stats(self):
        """Summary stats are calculated correctly."""
        trades = [
            _sample_trade(1, total_pnl=100.0, fees=5.0),  # net 95 (win)
            _sample_trade(2, total_pnl=-50.0, fees=5.0),  # net -55 (loss)
            _sample_trade(3, total_pnl=200.0, fees=5.0),  # net 195 (win)
        ]
        embed = build_paper_history_embed(trades, None, 7)

        # Cumulative PnL: 95 + (-55) + 195 = 235
        cum_field = [f for f in embed.fields if f.name == "Cumulative P/L"]
        self.assertEqual(len(cum_field), 1)
        self.assertIn("235", cum_field[0].value)

        # Win rate: 2/3 = 66.7%
        wr_field = [f for f in embed.fields if f.name == "Win Rate"]
        self.assertEqual(len(wr_field), 1)
        self.assertIn("66.7%", wr_field[0].value)

    def test_no_trades(self):
        """No trades shows info color and appropriate text."""
        embed = build_paper_history_embed([], None, 7)
        self.assertEqual(embed.color.value, COLOR_INFO)
        self.assertIn("No trades", embed.description)

    def test_strategy_filter_title(self):
        """Strategy filter shows in title."""
        trades = [_sample_trade(1)]
        embed = build_paper_history_embed(trades, "Iron Condor Weekly", 7)
        self.assertIn("Iron Condor Weekly", embed.title)

    def test_days_title(self):
        """Days shows in title when no filter."""
        trades = [_sample_trade(1)]
        embed = build_paper_history_embed(trades, None, 30)
        self.assertIn("Last 30 days", embed.title)


# -- build_paper_position_detail_embed tests ---------------------------------


class TestBuildPaperPositionDetailEmbed(unittest.TestCase):
    """Tests for build_paper_position_detail_embed."""

    def test_all_fields_present(self):
        """All 8 expected fields are present."""
        position = _sample_position()
        fills = [_sample_fill()]
        embed = build_paper_position_detail_embed(position, "Iron Condor Weekly", fills)

        field_names = [f.name for f in embed.fields]
        self.assertIn("Legs", field_names)
        self.assertIn("Entry Price", field_names)
        self.assertIn("Current Mark", field_names)
        self.assertIn("Unrealized P/L", field_names)
        self.assertIn("Max Profit", field_names)
        self.assertIn("Max Loss", field_names)
        self.assertIn("P/L % of Max", field_names)
        self.assertIn("Last Mark", field_names)
        self.assertEqual(len(embed.fields), 8)

    def test_legs_display(self):
        """Each leg appears on separate line."""
        position = _sample_position()
        fills = [_sample_fill()]
        embed = build_paper_position_detail_embed(position, "Test", fills)

        legs_field = [f for f in embed.fields if f.name == "Legs"]
        self.assertEqual(len(legs_field), 1)
        # 4 legs = 4 lines
        lines = legs_field[0].value.strip().split("\n")
        self.assertEqual(len(lines), 4)

    def test_positive_unrealized(self):
        """Positive unrealized PnL shows [+] and bullish color."""
        position = _sample_position(unrealized_pnl=50.0)
        embed = build_paper_position_detail_embed(position, "Test", [])
        self.assertEqual(embed.color.value, COLOR_BULLISH)

        unr_field = [f for f in embed.fields if f.name == "Unrealized P/L"]
        self.assertIn("[+]", unr_field[0].value)

    def test_negative_unrealized(self):
        """Negative unrealized PnL shows [-] and bearish color."""
        position = _sample_position(unrealized_pnl=-100.0)
        embed = build_paper_position_detail_embed(position, "Test", [])
        self.assertEqual(embed.color.value, COLOR_BEARISH)


# -- build_paper_daily_pnl_embed tests ---------------------------------------


class TestBuildPaperDailyPnlEmbed(unittest.TestCase):
    """Tests for build_paper_daily_pnl_embed."""

    def test_all_fields_present(self):
        """All fields are present."""
        portfolio = _sample_portfolio()
        trades = [_sample_trade(1)]
        embed = build_paper_daily_pnl_embed(portfolio, trades, "Feb 24, 2026")

        field_names = [f.name for f in embed.fields]
        self.assertIn("Realized P/L", field_names)
        self.assertIn("Unrealized P/L", field_names)
        self.assertIn("Total Day P/L", field_names)
        self.assertIn("Cumulative P/L", field_names)
        self.assertIn("Portfolio Value", field_names)
        self.assertIn("Open Positions", field_names)

    def test_positive_color(self):
        """Positive daily P/L gives green."""
        portfolio = _sample_portfolio(daily_pnl=50.0)
        embed = build_paper_daily_pnl_embed(portfolio, [], "Feb 24, 2026")
        self.assertEqual(embed.color.value, COLOR_BULLISH)

    def test_negative_color(self):
        """Negative daily P/L gives red."""
        portfolio = _sample_portfolio(daily_pnl=-50.0)
        embed = build_paper_daily_pnl_embed(portfolio, [], "Feb 24, 2026")
        self.assertEqual(embed.color.value, COLOR_BEARISH)


# -- build_paper_fill_alert_embed tests --------------------------------------


class TestBuildPaperFillAlertEmbed(unittest.TestCase):
    """Tests for build_paper_fill_alert_embed."""

    def test_fill_alert_structure(self):
        """Fill alert has correct title and color."""
        order = {
            "id": 1, "direction": "open", "order_type": "market",
            "quantity": 1, "fill_price": 2.0, "filled_at": "2026-02-24 10:30:00",
        }
        fills = [
            _sample_fill(action="sell", option_type="call", strike=5100),
            _sample_fill(action="buy", option_type="call", strike=5110),
            _sample_fill(action="sell", option_type="put", strike=4900),
            _sample_fill(action="buy", option_type="put", strike=4890),
        ]
        embed = build_paper_fill_alert_embed(order, fills, "Iron Condor Weekly")

        self.assertIn("PAPER FILL", embed.title)
        self.assertEqual(embed.color.value, COLOR_INFO)
        self.assertIn("4 legs", embed.description)

    def test_fill_details_shown(self):
        """Individual fill details are shown."""
        order = {
            "id": 1, "direction": "open", "order_type": "market",
            "quantity": 1, "fill_price": 2.0, "filled_at": "2026-02-24 10:30:00",
        }
        fills = [_sample_fill()]
        embed = build_paper_fill_alert_embed(order, fills, "Test Strategy")

        fills_field = [f for f in embed.fields if f.name == "Fills"]
        self.assertEqual(len(fills_field), 1)
        self.assertIn("SELL", fills_field[0].value)
        self.assertIn("5100", fills_field[0].value)


# -- _build_option_desc tests ------------------------------------------------


class TestBuildOptionDesc(unittest.TestCase):
    """Tests for _build_option_desc helper."""

    def test_iron_condor(self):
        """4-leg IC position returns IC format."""
        legs = [
            {"option_type": "call", "strike": 5100, "expiry": "2026-03-15"},
            {"option_type": "call", "strike": 5110, "expiry": "2026-03-15"},
            {"option_type": "put", "strike": 4900, "expiry": "2026-03-15"},
            {"option_type": "put", "strike": 4890, "expiry": "2026-03-15"},
        ]
        result = _build_option_desc(legs)
        self.assertIn("IC", result)
        self.assertIn("SPX", result)
        self.assertIn("4890", result)
        self.assertIn("5110", result)

    def test_put_spread(self):
        """2-leg put spread returns PS format."""
        legs = [
            {"option_type": "put", "strike": 5050, "expiry": "2026-03-15"},
            {"option_type": "put", "strike": 5060, "expiry": "2026-03-15"},
        ]
        result = _build_option_desc(legs)
        self.assertIn("PS", result)
        self.assertIn("5050", result)
        self.assertIn("5060", result)

    def test_call_spread(self):
        """2-leg call spread returns CS format."""
        legs = [
            {"option_type": "call", "strike": 5100, "expiry": "2026-03-15"},
            {"option_type": "call", "strike": 5110, "expiry": "2026-03-15"},
        ]
        result = _build_option_desc(legs)
        self.assertIn("CS", result)

    def test_single_leg_call(self):
        """Single call leg returns format with C."""
        legs = [
            {"option_type": "call", "strike": 5100, "expiry": "2026-03-15"},
        ]
        result = _build_option_desc(legs)
        self.assertIn("5100C", result)
        self.assertIn("SPX", result)

    def test_single_leg_put(self):
        """Single put leg returns format with P."""
        legs = [
            {"option_type": "put", "strike": 5050, "expiry": "2026-03-15"},
        ]
        result = _build_option_desc(legs)
        self.assertIn("5050P", result)

    def test_empty_legs(self):
        """Empty legs returns fallback."""
        result = _build_option_desc([])
        self.assertIn("no legs", result)

    def test_butterfly(self):
        """3-leg butterfly returns BF format."""
        legs = [
            {"option_type": "put", "strike": 5000, "expiry": "2026-03-15"},
            {"option_type": "put", "strike": 5050, "expiry": "2026-03-15"},
            {"option_type": "put", "strike": 5100, "expiry": "2026-03-15"},
        ]
        result = _build_option_desc(legs)
        self.assertIn("BF", result)


# ###########################################################################
#
#  PHASE 4-7 TESTS (from src.discord_bot.paper_embeds)
#
# ###########################################################################


# ---------------------------------------------------------------------------
# 1a: Daily Summary Tests
# ---------------------------------------------------------------------------


class TestBuildDailySummary:
    """Tests for build_paper_daily_summary_embed."""

    def test_build_daily_summary_positive_pnl(self):
        """Positive daily PnL gives green color and correct fields."""
        portfolio = _sample_portfolio(daily_pnl=125.0)
        embed = build_paper_daily_summary_embed(
            report_date=date(2026, 2, 24),
            portfolio=portfolio,
            day_trades=_sample_day_trades(3, pnl_positive=True),
            strategy_snapshots=_sample_strategy_snapshots(),
            risk_status=_sample_risk_status(),
        )

        assert isinstance(embed, discord.Embed)
        assert embed.color.value == COLOR_BULLISH
        assert "2026-02-24" in embed.title
        assert "Paper Trading Daily Summary" in embed.title
        field_names = {f.name for f in embed.fields}
        assert "Day's Trades" in field_names
        assert "Open Positions" in field_names
        assert "Day P/L" in field_names
        assert "Cumulative P/L" in field_names
        assert "Risk Limits" in field_names

    def test_build_daily_summary_negative_pnl(self):
        """Negative daily PnL gives red color."""
        portfolio = _sample_portfolio(daily_pnl=-50.0)
        embed = build_paper_daily_summary_embed(
            report_date=date(2026, 2, 24),
            portfolio=portfolio,
            day_trades=_sample_day_trades(2, pnl_positive=False),
            strategy_snapshots=[],
            risk_status=_sample_risk_status(),
        )

        assert embed.color.value == COLOR_BEARISH

    def test_build_daily_summary_zero_pnl(self):
        """Zero daily PnL gives yellow color."""
        portfolio = _sample_portfolio(daily_pnl=0.0)
        embed = build_paper_daily_summary_embed(
            report_date=date(2026, 2, 24),
            portfolio=portfolio,
            day_trades=[],
            strategy_snapshots=[],
            risk_status=_sample_risk_status(),
        )

        assert embed.color.value == COLOR_NEUTRAL

    def test_build_daily_summary_no_trades(self):
        """No trades shows empty state message."""
        portfolio = _sample_portfolio(daily_pnl=0.0)
        embed = build_paper_daily_summary_embed(
            report_date=date(2026, 2, 24),
            portfolio=portfolio,
            day_trades=[],
            strategy_snapshots=[],
            risk_status=_sample_risk_status(),
        )

        trades_field = [f for f in embed.fields if f.name == "Day's Trades"]
        assert len(trades_field) == 1
        assert "No trades" in trades_field[0].value

    def test_build_daily_summary_truncates_trades(self):
        """More than 8 trades shows truncation message."""
        portfolio = _sample_portfolio(daily_pnl=500.0)
        trades = _sample_day_trades(12, pnl_positive=True)
        embed = build_paper_daily_summary_embed(
            report_date=date(2026, 2, 24),
            portfolio=portfolio,
            day_trades=trades,
            strategy_snapshots=[],
            risk_status=_sample_risk_status(),
        )

        trades_field = [f for f in embed.fields if f.name == "Day's Trades"]
        assert len(trades_field) == 1
        assert "...and 4 more" in trades_field[0].value


# ---------------------------------------------------------------------------
# 1b: Weekly Review Tests
# ---------------------------------------------------------------------------


class TestBuildWeeklyReview:
    """Tests for build_paper_weekly_review_embed."""

    def test_build_weekly_review_returns_two_embeds(self):
        """Weekly review returns exactly 2 embeds."""
        embeds = build_paper_weekly_review_embed(
            week_start=date(2026, 2, 17),
            week_end=date(2026, 2, 21),
            portfolio_start=100_000.0,
            portfolio_end=100_500.0,
            weekly_trades=_sample_weekly_trades(5),
            strategy_comparison=_sample_strategy_comparison(),
            risk_evolution=_sample_risk_evolution(),
            promotion_readiness=_sample_promotion_readiness(),
        )

        assert isinstance(embeds, list)
        assert len(embeds) == 2
        assert all(isinstance(e, discord.Embed) for e in embeds)

    def test_build_weekly_review_strategy_comparison_table(self):
        """Second embed contains strategy comparison table."""
        embeds = build_paper_weekly_review_embed(
            week_start=date(2026, 2, 17),
            week_end=date(2026, 2, 21),
            portfolio_start=100_000.0,
            portfolio_end=100_500.0,
            weekly_trades=_sample_weekly_trades(5),
            strategy_comparison=_sample_strategy_comparison(),
            risk_evolution=_sample_risk_evolution(),
            promotion_readiness=_sample_promotion_readiness(),
        )

        embed2 = embeds[1]
        assert "Strategy Comparison" in embed2.title
        comp_field = [f for f in embed2.fields if "Strategy Comparison" in f.name]
        assert len(comp_field) == 1
        assert "Iron Condor" in comp_field[0].value
        assert "Put Spread" in comp_field[0].value

    def test_build_weekly_review_promotion_readiness(self):
        """Second embed contains promotion readiness display."""
        embeds = build_paper_weekly_review_embed(
            week_start=date(2026, 2, 17),
            week_end=date(2026, 2, 21),
            portfolio_start=100_000.0,
            portfolio_end=100_500.0,
            weekly_trades=_sample_weekly_trades(),
            strategy_comparison=_sample_strategy_comparison(),
            risk_evolution=_sample_risk_evolution(),
            promotion_readiness=_sample_promotion_readiness(),
        )

        embed2 = embeds[1]
        readiness_field = [f for f in embed2.fields if "Promotion" in f.name]
        assert len(readiness_field) == 1
        assert "[READY]" in readiness_field[0].value
        assert "[NOT READY]" in readiness_field[0].value


# ---------------------------------------------------------------------------
# 1c: Monthly Report Tests
# ---------------------------------------------------------------------------


class TestBuildMonthlyReport:
    """Tests for build_paper_monthly_report_embeds."""

    def test_build_monthly_report_returns_multiple_embeds(self):
        """Monthly report returns 3-4 embeds."""
        embeds = build_paper_monthly_report_embeds(
            month=date(2026, 2, 1),
            monthly_pnl_by_strategy=[
                {"name": "Iron Condor", "trades": 18, "pnl": 520, "sharpe": 1.23, "win_rate": 0.62},
            ],
            aggregate_metrics=_sample_aggregate_metrics(),
            slippage_analysis=_sample_slippage_analysis(),
            shadow_comparison=_sample_shadow_comparison(),
            degradation_summary={"alerts": [], "overall_score": 0.85},
            strategy_lifecycle_events=_sample_lifecycle_events(),
        )

        assert isinstance(embeds, list)
        assert len(embeds) >= 3
        assert len(embeds) <= 4
        # With lifecycle events, should be 4
        assert len(embeds) == 4

    def test_build_monthly_report_shadow_comparison(self):
        """Monthly report contains paper vs backtest comparison."""
        embeds = build_paper_monthly_report_embeds(
            month=date(2026, 2, 1),
            monthly_pnl_by_strategy=[],
            aggregate_metrics=_sample_aggregate_metrics(),
            slippage_analysis=_sample_slippage_analysis(),
            shadow_comparison=_sample_shadow_comparison(),
            degradation_summary={"alerts": [], "overall_score": 0.85},
            strategy_lifecycle_events=[],
        )

        embed2 = embeds[1]
        assert "Paper vs Backtest" in embed2.title
        # Should have the strategy comparison field
        strategy_fields = [f for f in embed2.fields if f.name == "Iron Condor"]
        assert len(strategy_fields) == 1
        assert "Sharpe" in strategy_fields[0].value

    def test_build_monthly_report_slippage_analysis(self):
        """Monthly report contains slippage analysis fields."""
        embeds = build_paper_monthly_report_embeds(
            month=date(2026, 2, 1),
            monthly_pnl_by_strategy=[],
            aggregate_metrics=_sample_aggregate_metrics(),
            slippage_analysis=_sample_slippage_analysis(),
            shadow_comparison=[],
            degradation_summary={"alerts": [], "overall_score": 0.0},
            strategy_lifecycle_events=[],
        )

        embed3 = embeds[2]
        assert "Execution Quality" in embed3.title
        field_names = {f.name for f in embed3.fields}
        assert "Slippage Summary" in field_names
        assert "Model Accuracy" in field_names

    def test_build_monthly_report_no_lifecycle_events(self):
        """Monthly report omits embed 4 when no lifecycle events."""
        embeds = build_paper_monthly_report_embeds(
            month=date(2026, 2, 1),
            monthly_pnl_by_strategy=[],
            aggregate_metrics=_sample_aggregate_metrics(),
            slippage_analysis=_sample_slippage_analysis(),
            shadow_comparison=[],
            degradation_summary={"alerts": [], "overall_score": 0.0},
            strategy_lifecycle_events=[],
        )

        assert len(embeds) == 3
        # No "Strategy Lifecycle Events" title in any embed
        for embed in embeds:
            assert "Lifecycle" not in (embed.title or "")


# ---------------------------------------------------------------------------
# 1d: Strategy Performance Tests
# ---------------------------------------------------------------------------


class TestBuildStrategyPerformance:
    """Tests for build_paper_strategy_performance_embed."""

    def test_build_strategy_performance_metrics_fields(self):
        """All 15 metric fields are present in embed 1."""
        embeds = build_paper_strategy_performance_embed(
            strategy_name="Iron Condor Weekly",
            strategy_id=42,
            paper_metrics=_MockMetrics(),
            backtest_metrics=_sample_backtest_metrics(),
            promotion_criteria=_sample_promotion_criteria(all_pass=True),
            days_in_paper=28,
            trade_count=45,
        )

        assert len(embeds) == 2
        embed1 = embeds[0]

        # Should have all metric fields
        field_names = {f.name for f in embed1.fields}
        expected_fields = {
            "Sharpe", "Sortino", "Calmar",
            "Win Rate", "Profit Factor", "Expectancy",
            "Max DD", "Max DD Duration", "Avg DD",
            "Avg Win", "Avg Loss", "Avg Holding Days",
            "Skewness", "Kurtosis",
        }
        assert expected_fields.issubset(field_names), f"Missing: {expected_fields - field_names}"
        # 14 fields in embed1 (3+3+3+3+2)
        assert len(embed1.fields) == 14

    def test_build_strategy_performance_promotion_criteria(self):
        """Promotion criteria display shows pass/fail indicators."""
        embeds = build_paper_strategy_performance_embed(
            strategy_name="Iron Condor Weekly",
            strategy_id=42,
            paper_metrics=_MockMetrics(),
            backtest_metrics=_sample_backtest_metrics(),
            promotion_criteria=_sample_promotion_criteria(all_pass=False),
            days_in_paper=28,
            trade_count=45,
        )

        embed2 = embeds[1]
        criteria_field = [f for f in embed2.fields if "Promotion" in f.name]
        assert len(criteria_field) == 1
        assert "[PASS]" in criteria_field[0].value
        assert "[FAIL]" in criteria_field[0].value

    def test_build_strategy_performance_no_backtest(self):
        """Gracefully handles None backtest metrics."""
        embeds = build_paper_strategy_performance_embed(
            strategy_name="New Strategy",
            strategy_id=99,
            paper_metrics=_MockMetrics(),
            backtest_metrics=None,
            promotion_criteria=_sample_promotion_criteria(all_pass=True),
            days_in_paper=5,
            trade_count=10,
        )

        assert len(embeds) == 2
        embed2 = embeds[1]
        shadow_field = [f for f in embed2.fields if "Shadow" in f.name]
        assert len(shadow_field) == 1
        assert "No backtest data" in shadow_field[0].value


# ---------------------------------------------------------------------------
# 1e: Degradation Alert Tests
# ---------------------------------------------------------------------------


class TestBuildDegradationAlert:
    """Tests for build_degradation_alert_embed."""

    def test_build_degradation_alert_fields(self):
        """All alert fields are present with correct values."""
        embed = build_degradation_alert_embed(
            strategy_name="Iron Condor Weekly",
            strategy_id=42,
            metric_name="Sharpe Ratio",
            paper_value=0.85,
            backtest_value=1.45,
            deviation=-0.60,
            threshold=0.50,
        )

        assert isinstance(embed, discord.Embed)
        assert embed.color.value == COLOR_BEARISH
        assert "ALERT" in embed.title
        assert "Iron Condor Weekly" in embed.title

        field_names = {f.name for f in embed.fields}
        assert "Degraded Metric" in field_names
        assert "Recommendation" in field_names

        degraded_field = [f for f in embed.fields if f.name == "Degraded Metric"][0]
        assert "Sharpe Ratio" in degraded_field.value
        assert "0.8500" in degraded_field.value
        assert "1.4500" in degraded_field.value
        assert "0.5000" in degraded_field.value  # threshold


# ---------------------------------------------------------------------------
# 1f: Strategy Comparison Tests
# ---------------------------------------------------------------------------


class TestBuildStrategyComparison:
    """Tests for build_paper_strategy_comparison_embed."""

    def test_build_strategy_comparison_max_four(self):
        """Only 4 strategies are displayed even if more provided."""
        strategies = [
            {"name": f"Strategy {i}", "sharpe": 1.0 + i * 0.1, "sortino": 1.2,
             "win_rate": 0.6, "max_dd": -0.05, "profit_factor": 1.5,
             "trades": 20, "total_pnl": 200.0}
            for i in range(6)
        ]

        embed = build_paper_strategy_comparison_embed(strategies)

        assert isinstance(embed, discord.Embed)
        assert embed.color.value == COLOR_INFO
        # Should show max 4 strategy fields
        strat_fields = [
            f for f in embed.fields
            if f.name.startswith("Strategy")
        ]
        assert len(strat_fields) == 4

    def test_build_strategy_comparison_empty(self):
        """Empty strategies list shows appropriate message."""
        embed = build_paper_strategy_comparison_embed([])

        assert isinstance(embed, discord.Embed)
        assert "Paper Strategy Comparison" in embed.title
        no_strat_field = [f for f in embed.fields if f.name == "No Strategies"]
        assert len(no_strat_field) == 1
        assert "No paper trading strategies" in no_strat_field[0].value


# ---------------------------------------------------------------------------
# Cross-cutting: Discord Limits
# ---------------------------------------------------------------------------


class TestDiscordLimits:
    """Tests ensuring Discord embed limits are respected."""

    def test_embed_field_values_under_1024_chars(self):
        """All field values stay under 1024 chars with large inputs."""
        # Generate a large number of trades to stress field value limits
        many_trades = _sample_day_trades(12, pnl_positive=True)
        portfolio = _sample_portfolio(daily_pnl=500.0)

        daily_embed = build_paper_daily_summary_embed(
            report_date=date(2026, 2, 24),
            portfolio=portfolio,
            day_trades=many_trades,
            strategy_snapshots=_sample_strategy_snapshots(),
            risk_status=_sample_risk_status(has_warnings=True),
        )

        for f in daily_embed.fields:
            assert len(f.value) <= 1024, (
                f"Field '{f.name}' exceeds 1024 chars: {len(f.value)}"
            )

        # Also test monthly report (most embeds)
        monthly_embeds = build_paper_monthly_report_embeds(
            month=date(2026, 2, 1),
            monthly_pnl_by_strategy=[
                {"name": f"Strategy {i}", "trades": 18 + i, "pnl": 500 + i * 100,
                 "sharpe": 1.0 + i * 0.1, "win_rate": 0.55 + i * 0.02}
                for i in range(5)
            ],
            aggregate_metrics=_sample_aggregate_metrics(),
            slippage_analysis=_sample_slippage_analysis(),
            shadow_comparison=_sample_shadow_comparison(),
            degradation_summary={"alerts": ["Alert A", "Alert B"], "overall_score": 0.75},
            strategy_lifecycle_events=_sample_lifecycle_events(),
        )

        for embed in monthly_embeds:
            for f in embed.fields:
                assert len(f.value) <= 1024, (
                    f"Field '{f.name}' in '{embed.title}' exceeds 1024 chars: {len(f.value)}"
                )

    def test_embed_total_chars_under_6000(self):
        """Each embed stays under 6000 total characters."""
        # Test daily summary (single embed)
        portfolio = _sample_portfolio(daily_pnl=125.0)
        daily_embed = build_paper_daily_summary_embed(
            report_date=date(2026, 2, 24),
            portfolio=portfolio,
            day_trades=_sample_day_trades(8),
            strategy_snapshots=_sample_strategy_snapshots(),
            risk_status=_sample_risk_status(has_warnings=True),
        )
        assert _total_embed_chars(daily_embed) < 6000, (
            f"Daily embed exceeds 6000: {_total_embed_chars(daily_embed)}"
        )

        # Test weekly review (2 embeds)
        weekly_embeds = build_paper_weekly_review_embed(
            week_start=date(2026, 2, 17),
            week_end=date(2026, 2, 21),
            portfolio_start=100_000.0,
            portfolio_end=100_500.0,
            weekly_trades=_sample_weekly_trades(10),
            strategy_comparison=_sample_strategy_comparison(),
            risk_evolution=_sample_risk_evolution(),
            promotion_readiness=_sample_promotion_readiness(),
        )
        for embed in weekly_embeds:
            assert _total_embed_chars(embed) < 6000, (
                f"Weekly embed '{embed.title}' exceeds 6000: {_total_embed_chars(embed)}"
            )

        # Test monthly report (3-4 embeds)
        monthly_embeds = build_paper_monthly_report_embeds(
            month=date(2026, 2, 1),
            monthly_pnl_by_strategy=[
                {"name": "Iron Condor", "trades": 18, "pnl": 520, "sharpe": 1.23, "win_rate": 0.62},
            ],
            aggregate_metrics=_sample_aggregate_metrics(),
            slippage_analysis=_sample_slippage_analysis(),
            shadow_comparison=_sample_shadow_comparison(),
            degradation_summary={"alerts": [], "overall_score": 0.85},
            strategy_lifecycle_events=_sample_lifecycle_events(),
        )
        for embed in monthly_embeds:
            assert _total_embed_chars(embed) < 6000, (
                f"Monthly embed '{embed.title}' exceeds 6000: {_total_embed_chars(embed)}"
            )

        # Test strategy performance (2 embeds)
        perf_embeds = build_paper_strategy_performance_embed(
            strategy_name="Iron Condor Weekly",
            strategy_id=42,
            paper_metrics=_MockMetrics(),
            backtest_metrics=_sample_backtest_metrics(),
            promotion_criteria=_sample_promotion_criteria(),
            days_in_paper=28,
            trade_count=45,
        )
        for embed in perf_embeds:
            assert _total_embed_chars(embed) < 6000, (
                f"Perf embed '{embed.title}' exceeds 6000: {_total_embed_chars(embed)}"
            )

        # Test degradation alert
        alert_embed = build_degradation_alert_embed(
            strategy_name="Iron Condor Weekly",
            strategy_id=42,
            metric_name="Sharpe Ratio",
            paper_value=0.85,
            backtest_value=1.45,
            deviation=-0.60,
            threshold=0.50,
        )
        assert _total_embed_chars(alert_embed) < 6000

        # Test comparison embed
        compare_embed = build_paper_strategy_comparison_embed([
            {"name": f"Strategy {i}", "sharpe": 1.0, "sortino": 1.2,
             "win_rate": 0.6, "max_dd": -0.05, "profit_factor": 1.5,
             "trades": 20, "total_pnl": 200.0}
            for i in range(4)
        ])
        assert _total_embed_chars(compare_embed) < 6000


if __name__ == "__main__":
    unittest.main()
