"""Tests for paper trading embed builder functions."""

import unittest
from datetime import datetime, timezone

import discord

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
from src.paper.models import PortfolioSummary


# -- Fixtures ----------------------------------------------------------------


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


def _sample_position(pid=1, strategy_id=1, **overrides):
    """Create a sample position dict."""
    import json
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
        import json
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


if __name__ == "__main__":
    unittest.main()
