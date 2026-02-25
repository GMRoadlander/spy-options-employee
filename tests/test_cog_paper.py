"""Tests for the PaperTrading cog, views, and autocomplete."""

import json
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from src.paper.models import PortfolioSummary


# -- Fixtures ----------------------------------------------------------------


def _make_bot():
    """Create a mock bot with paper_engine and strategy_manager."""
    bot = MagicMock()
    bot.paper_engine = MagicMock()
    bot.strategy_manager = MagicMock()
    bot.get_channel = MagicMock(return_value=MagicMock(spec=discord.TextChannel))
    # Needed for background tasks
    bot.wait_until_ready = AsyncMock()
    return bot


def _make_interaction():
    """Create a mock Discord interaction."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.__str__ = MagicMock(return_value="TestUser#1234")
    interaction.client = _make_bot()
    return interaction


def _sample_portfolio(**overrides):
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


def _make_cog(bot=None):
    """Create a PaperTradingCog instance without starting background tasks."""
    from src.discord_bot.cog_paper import PaperTradingCog
    if bot is None:
        bot = _make_bot()
    cog = PaperTradingCog.__new__(PaperTradingCog)
    cog.bot = bot
    cog._daily_posted_date = ""
    return cog


def _mock_cursor_with_rows(rows):
    """Create an AsyncMock cursor that returns given rows."""
    cursor = AsyncMock()
    cursor.fetchall = AsyncMock(return_value=rows)
    cursor.fetchone = AsyncMock(return_value=rows[0] if rows else None)
    return cursor


def _get_followup_content(interaction):
    """Extract the content string from a followup.send call (args or kwargs)."""
    call_args = interaction.followup.send.call_args
    # Check positional args first
    if call_args.args:
        return str(call_args.args[0])
    # Then keyword args
    return call_args.kwargs.get("content", "")


# -- paper_status tests ------------------------------------------------------


class TestPaperStatus(unittest.IsolatedAsyncioTestCase):
    """Tests for /paper_status command."""

    async def test_paper_status_success(self):
        """paper_status returns embed with portfolio data."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        portfolio = _sample_portfolio()
        bot.paper_engine.get_portfolio_summary = AsyncMock(return_value=portfolio)
        bot.paper_engine.position_tracker.get_open_positions = AsyncMock(return_value=[
            {"id": 1, "strategy_id": 1, "legs": "[]", "entry_price": 2.0,
             "current_mark": 1.5, "unrealized_pnl": 50.0},
            {"id": 2, "strategy_id": 2, "legs": "[]", "entry_price": 1.5,
             "current_mark": 1.0, "unrealized_pnl": -25.0},
        ])
        bot.strategy_manager.get = AsyncMock(return_value={"name": "Test Strategy"})
        bot.paper_engine.order_manager.get_fills_for_order = AsyncMock(return_value=[])

        # Mock DB for _get_todays_fills
        cursor = _mock_cursor_with_rows([])
        bot.paper_engine._db = AsyncMock()
        bot.paper_engine._db.execute = AsyncMock(return_value=cursor)

        await cog.paper_status.callback(cog, interaction)

        interaction.response.defer.assert_awaited_once()
        interaction.followup.send.assert_awaited_once()
        call_kwargs = interaction.followup.send.call_args.kwargs
        self.assertIn("embed", call_kwargs)
        self.assertEqual(call_kwargs["embed"].title, "Paper Trading Status")
        self.assertGreaterEqual(len(call_kwargs["embed"].fields), 6)

    async def test_paper_status_no_engine(self):
        """paper_status with no engine sends ephemeral error."""
        bot = _make_bot()
        bot.paper_engine = None
        cog = _make_cog(bot)
        interaction = _make_interaction()

        await cog.paper_status.callback(cog, interaction)

        interaction.followup.send.assert_awaited_once()
        content = _get_followup_content(interaction)
        self.assertIn("not available", content.lower())

    async def test_paper_status_engine_error(self):
        """paper_status handles engine errors gracefully."""
        bot = _make_bot()
        bot.paper_engine.get_portfolio_summary = AsyncMock(
            side_effect=RuntimeError("DB error"),
        )
        cog = _make_cog(bot)
        interaction = _make_interaction()

        await cog.paper_status.callback(cog, interaction)

        interaction.followup.send.assert_awaited_once()
        call_kwargs = interaction.followup.send.call_args.kwargs
        self.assertTrue(call_kwargs.get("ephemeral", False))

    async def test_paper_status_no_positions(self):
        """paper_status with no positions shows 'No open positions'."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        portfolio = _sample_portfolio(open_positions=0)
        bot.paper_engine.get_portfolio_summary = AsyncMock(return_value=portfolio)
        bot.paper_engine.position_tracker.get_open_positions = AsyncMock(return_value=[])

        cursor = _mock_cursor_with_rows([])
        bot.paper_engine._db = AsyncMock()
        bot.paper_engine._db.execute = AsyncMock(return_value=cursor)

        await cog.paper_status.callback(cog, interaction)

        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        pos_field = [f for f in embed.fields if "Active Positions" in f.name]
        self.assertIn("No open positions", pos_field[0].value)


# -- paper_history tests -----------------------------------------------------


class TestPaperHistory(unittest.IsolatedAsyncioTestCase):
    """Tests for /paper_history command."""

    async def test_paper_history_success(self):
        """paper_history returns embed with trade data."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        rows = [(i, 1, "2026-02-15", "2026-02-20", 5, 2.0, 0.5, 100.0, 5.0, 1.0, "profit_target")
                for i in range(5)]
        cursor = _mock_cursor_with_rows(rows)
        bot.paper_engine._db = AsyncMock()
        bot.paper_engine._db.execute = AsyncMock(return_value=cursor)
        bot.strategy_manager.get = AsyncMock(return_value={"name": "Test"})

        await cog.paper_history.callback(cog, interaction, strategy="", days=7)

        interaction.response.defer.assert_awaited_once()
        interaction.followup.send.assert_awaited_once()
        call_kwargs = interaction.followup.send.call_args.kwargs
        self.assertIn("embed", call_kwargs)
        self.assertIn("Last 7 days", call_kwargs["embed"].title)
        # No pagination for < 15 trades
        self.assertNotIn("view", call_kwargs)

    async def test_paper_history_pagination(self):
        """paper_history with > 15 trades includes pagination view."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        rows = [(i, 1, "2026-02-15", "2026-02-20", 5, 2.0, 0.5, 100.0, 5.0, 1.0, "profit_target")
                for i in range(25)]
        cursor = _mock_cursor_with_rows(rows)
        bot.paper_engine._db = AsyncMock()
        bot.paper_engine._db.execute = AsyncMock(return_value=cursor)
        bot.strategy_manager.get = AsyncMock(return_value={"name": "Test"})

        await cog.paper_history.callback(cog, interaction, strategy="", days=30)

        call_kwargs = interaction.followup.send.call_args.kwargs
        self.assertIn("view", call_kwargs)
        from src.discord_bot.cog_paper import PaginatedHistoryView
        self.assertIsInstance(call_kwargs["view"], PaginatedHistoryView)

    async def test_paper_history_strategy_filter(self):
        """paper_history with strategy filter uses strategy_id in query."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        bot.strategy_manager.list_strategies = AsyncMock(return_value=[
            {"id": 1, "name": "Iron Condor Weekly"},
        ])

        rows = [(1, 1, "2026-02-15", "2026-02-20", 5, 2.0, 0.5, 100.0, 5.0, 1.0, "profit_target")]
        cursor = _mock_cursor_with_rows(rows)
        bot.paper_engine._db = AsyncMock()
        bot.paper_engine._db.execute = AsyncMock(return_value=cursor)
        bot.strategy_manager.get = AsyncMock(return_value={"name": "Iron Condor Weekly"})

        await cog.paper_history.callback(
            cog, interaction, strategy="Iron Condor Weekly", days=7,
        )

        # Verify SQL used strategy_id filter
        execute_calls = bot.paper_engine._db.execute.call_args_list
        self.assertTrue(len(execute_calls) > 0)
        sql = execute_calls[0].args[0]
        self.assertIn("strategy_id", sql)

    async def test_paper_history_days_clamped(self):
        """paper_history clamps days to 1-90 range."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        cursor = _mock_cursor_with_rows([])
        bot.paper_engine._db = AsyncMock()
        bot.paper_engine._db.execute = AsyncMock(return_value=cursor)

        # days=0 should be clamped to 1
        await cog.paper_history.callback(cog, interaction, strategy="", days=0)
        call_kwargs = interaction.followup.send.call_args.kwargs
        self.assertIn("Last 1 days", call_kwargs["embed"].title)

    async def test_paper_history_no_trades(self):
        """paper_history with no trades shows info message."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        cursor = _mock_cursor_with_rows([])
        bot.paper_engine._db = AsyncMock()
        bot.paper_engine._db.execute = AsyncMock(return_value=cursor)

        await cog.paper_history.callback(cog, interaction, strategy="", days=7)

        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        self.assertIn("No trades", embed.description)


# -- paper_position tests ---------------------------------------------------


class TestPaperPosition(unittest.IsolatedAsyncioTestCase):
    """Tests for /paper_position command."""

    async def test_paper_position_found(self):
        """paper_position with valid ID returns detailed embed."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        position = {
            "id": 1, "strategy_id": 1, "status": "open",
            "opened_at": "2026-02-20 10:30:00",
            "legs": json.dumps([
                {"leg_name": "short_call", "option_type": "call", "strike": 5100,
                 "expiry": "2026-03-15", "action": "sell", "quantity": 1,
                 "fill_price": 2.50, "delta": -0.15},
            ]),
            "entry_price": 2.50, "current_mark": 2.00,
            "unrealized_pnl": 50.0, "max_profit": 250.0, "max_loss": -750.0,
            "last_mark_at": "2026-02-24 15:45:00",
            "open_order_id": 1,
        }
        bot.paper_engine.position_tracker._get_position = AsyncMock(return_value=position)
        bot.strategy_manager.get = AsyncMock(return_value={"name": "Iron Condor"})
        bot.paper_engine.order_manager.get_fills_for_order = AsyncMock(return_value=[])

        await cog.paper_position.callback(cog, interaction, position_id=1)

        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        self.assertIn("Position #1", embed.title)
        self.assertIn("Iron Condor", embed.title)
        self.assertEqual(len(embed.fields), 8)

    async def test_paper_position_not_found(self):
        """paper_position with invalid ID sends ephemeral error."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        bot.paper_engine.position_tracker._get_position = AsyncMock(return_value=None)

        await cog.paper_position.callback(cog, interaction, position_id=999)

        content = _get_followup_content(interaction)
        self.assertIn("not found", content.lower())


# -- paper_close tests ------------------------------------------------------


class TestPaperClose(unittest.IsolatedAsyncioTestCase):
    """Tests for /paper_close command."""

    async def test_paper_close_already_closed(self):
        """paper_close on already closed position sends error."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        position = {"id": 1, "strategy_id": 1, "status": "closed"}
        bot.paper_engine.position_tracker._get_position = AsyncMock(return_value=position)

        await cog.paper_close.callback(cog, interaction, position_id=1, reason="manual")

        content = _get_followup_content(interaction)
        self.assertIn("already closed", content.lower())

    async def test_paper_close_not_found(self):
        """paper_close on non-existent position sends error."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        bot.paper_engine.position_tracker._get_position = AsyncMock(return_value=None)

        await cog.paper_close.callback(cog, interaction, position_id=999, reason="manual")

        content = _get_followup_content(interaction)
        self.assertIn("not found", content.lower())


# -- paper_orders tests -----------------------------------------------------


class TestPaperOrders(unittest.IsolatedAsyncioTestCase):
    """Tests for /paper_orders command."""

    async def test_paper_orders_all(self):
        """paper_orders with status=all shows recent orders."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        rows = [
            (i, 1, "market", "open", 1, None, "filled",
             "2026-02-24 10:00:00", "2026-02-24 10:01:00", 2.0, 0.005)
            for i in range(5)
        ]
        cursor = _mock_cursor_with_rows(rows)
        bot.paper_engine._db = AsyncMock()
        bot.paper_engine._db.execute = AsyncMock(return_value=cursor)

        await cog.paper_orders.callback(cog, interaction, status="all")

        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        self.assertIn("5 orders", embed.description)

    async def test_paper_orders_pending(self):
        """paper_orders with status=pending calls get_pending_orders."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        bot.paper_engine.order_manager.get_pending_orders = AsyncMock(return_value=[
            {"id": 1, "strategy_id": 1, "order_type": "limit", "direction": "open",
             "quantity": 1, "limit_price": 2.0, "status": "pending",
             "submitted_at": "2026-02-24 10:00:00", "filled_at": None,
             "fill_price": None, "slippage": None},
        ])

        await cog.paper_orders.callback(cog, interaction, status="pending")

        bot.paper_engine.order_manager.get_pending_orders.assert_awaited_once()
        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        self.assertIn("1 orders", embed.description)

    async def test_paper_orders_empty(self):
        """paper_orders with no results shows 'No matching orders found'."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        cursor = _mock_cursor_with_rows([])
        bot.paper_engine._db = AsyncMock()
        bot.paper_engine._db.execute = AsyncMock(return_value=cursor)

        await cog.paper_orders.callback(cog, interaction, status="all")

        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        no_orders_field = [f for f in embed.fields if f.name == "No Orders"]
        self.assertEqual(len(no_orders_field), 1)
        self.assertIn("No matching orders found", no_orders_field[0].value)


# -- paper_pnl tests --------------------------------------------------------


class TestPaperPnl(unittest.IsolatedAsyncioTestCase):
    """Tests for /paper_pnl command."""

    async def test_paper_pnl_success(self):
        """paper_pnl returns embed with P/L statistics."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        equity_data = [
            {"date": f"2026-02-{i+1:02d}", "total_equity": 100_000 + i * 50,
             "daily_pnl": 50.0, "max_drawdown": -0.01}
            for i in range(10)
        ]
        bot.paper_engine.pnl_calculator.get_equity_curve = AsyncMock(return_value=equity_data)
        bot.paper_engine._config = MagicMock(starting_capital=100_000)

        with patch("src.discord_bot.charts.create_pnl_curve_chart", return_value=None):
            await cog.paper_pnl.callback(cog, interaction, days=30)

        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        self.assertIn("30 Days", embed.title)

    async def test_paper_pnl_no_data(self):
        """paper_pnl with no equity data sends ephemeral error."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        bot.paper_engine.pnl_calculator.get_equity_curve = AsyncMock(return_value=[])

        await cog.paper_pnl.callback(cog, interaction, days=30)

        content = _get_followup_content(interaction)
        self.assertIn("no portfolio data", content.lower())

    async def test_paper_pnl_chart_failure_graceful(self):
        """paper_pnl still sends embed when chart generation returns None."""
        bot = _make_bot()
        cog = _make_cog(bot)
        interaction = _make_interaction()

        equity_data = [
            {"date": f"2026-02-{i+1:02d}", "total_equity": 100_000 + i * 50,
             "daily_pnl": 50.0, "max_drawdown": -0.01}
            for i in range(10)
        ]
        bot.paper_engine.pnl_calculator.get_equity_curve = AsyncMock(return_value=equity_data)
        bot.paper_engine._config = MagicMock(starting_capital=100_000)

        with patch("src.discord_bot.charts.create_pnl_curve_chart", return_value=None):
            await cog.paper_pnl.callback(cog, interaction, days=30)

        call_kwargs = interaction.followup.send.call_args.kwargs
        # Embed still sent (without files kwarg or with empty files)
        self.assertIn("embed", call_kwargs)
        self.assertNotIn("files", call_kwargs)


# -- auto_paper_daily tests --------------------------------------------------


class TestAutoPaperDaily(unittest.IsolatedAsyncioTestCase):
    """Tests for the auto_paper_daily background task."""

    @patch("src.discord_bot.cog_paper._now_et")
    async def test_auto_paper_daily_weekday(self, mock_now):
        """Daily summary posts on weekday with activity."""
        mock_now.return_value = datetime(2026, 2, 24, 16, 15)  # Tuesday

        bot = _make_bot()
        cog = _make_cog(bot)

        channel = MagicMock(spec=discord.TextChannel)
        channel.send = AsyncMock()
        cog._get_paper_channel = MagicMock(return_value=channel)

        portfolio = _sample_portfolio()
        bot.paper_engine.get_portfolio_summary = AsyncMock(return_value=portfolio)

        cursor = _mock_cursor_with_rows([])
        bot.paper_engine._db = AsyncMock()
        bot.paper_engine._db.execute = AsyncMock(return_value=cursor)
        bot.strategy_manager.get = AsyncMock(return_value={"name": "Test"})

        # Mock equity curve (optional chart)
        bot.paper_engine.pnl_calculator.get_equity_curve = AsyncMock(return_value=[])

        await cog.auto_paper_daily()

        channel.send.assert_awaited_once()
        call_kwargs = channel.send.call_args.kwargs
        self.assertIn("embed", call_kwargs)

    @patch("src.discord_bot.cog_paper._now_et")
    async def test_auto_paper_daily_weekend_skip(self, mock_now):
        """Daily summary skips on Saturday."""
        mock_now.return_value = datetime(2026, 2, 28, 16, 15)  # Saturday

        bot = _make_bot()
        cog = _make_cog(bot)
        channel = MagicMock(spec=discord.TextChannel)
        channel.send = AsyncMock()
        cog._get_paper_channel = MagicMock(return_value=channel)

        await cog.auto_paper_daily()

        channel.send.assert_not_awaited()

    @patch("src.discord_bot.cog_paper._now_et")
    async def test_auto_paper_daily_no_activity_skip(self, mock_now):
        """Daily summary skips when no trades and no positions."""
        mock_now.return_value = datetime(2026, 2, 24, 16, 15)  # Tuesday

        bot = _make_bot()
        cog = _make_cog(bot)
        channel = MagicMock(spec=discord.TextChannel)
        channel.send = AsyncMock()
        cog._get_paper_channel = MagicMock(return_value=channel)

        portfolio = _sample_portfolio(total_trades=0, open_positions=0)
        bot.paper_engine.get_portfolio_summary = AsyncMock(return_value=portfolio)

        await cog.auto_paper_daily()

        channel.send.assert_not_awaited()

    @patch("src.discord_bot.cog_paper._now_et")
    async def test_auto_paper_daily_double_post_guard(self, mock_now):
        """Daily summary does not double-post on same day."""
        mock_now.return_value = datetime(2026, 2, 24, 16, 15)

        bot = _make_bot()
        cog = _make_cog(bot)
        cog._daily_posted_date = "2026-02-24"  # Already posted today

        channel = MagicMock(spec=discord.TextChannel)
        channel.send = AsyncMock()
        cog._get_paper_channel = MagicMock(return_value=channel)

        await cog.auto_paper_daily()

        channel.send.assert_not_awaited()


# -- post_fill_notification tests -------------------------------------------


class TestPostFillNotification(unittest.IsolatedAsyncioTestCase):
    """Tests for post_fill_notification method."""

    async def test_post_fill_notification(self):
        """Fill notification sends embed to channel."""
        bot = _make_bot()
        cog = _make_cog(bot)

        channel = MagicMock(spec=discord.TextChannel)
        channel.send = AsyncMock()
        cog._get_paper_channel = MagicMock(return_value=channel)

        order = {
            "id": 1, "direction": "open", "order_type": "market",
            "quantity": 1, "fill_price": 2.0, "filled_at": "2026-02-24 10:30:00",
        }
        fills = [{
            "leg_name": "short_call", "action": "sell", "option_type": "call",
            "strike": 5100, "expiry": "2026-03-15", "fill_price": 2.50,
            "bid": 2.40, "ask": 2.60, "mid": 2.50, "slippage": 0.005,
        }]

        await cog.post_fill_notification(order, fills, "Iron Condor Weekly")

        channel.send.assert_awaited_once()
        call_kwargs = channel.send.call_args.kwargs
        self.assertIn("embed", call_kwargs)
        self.assertIn("PAPER FILL", call_kwargs["embed"].title)

    async def test_post_fill_notification_no_channel(self):
        """Fill notification with no channel does not raise."""
        bot = _make_bot()
        cog = _make_cog(bot)
        cog._get_paper_channel = MagicMock(return_value=None)

        order = {"id": 1, "direction": "open", "order_type": "market",
                 "quantity": 1, "fill_price": 2.0, "filled_at": "2026-02-24 10:30:00"}
        fills = []

        # Should not raise
        await cog.post_fill_notification(order, fills, "Test")


# -- strategy_autocomplete tests --------------------------------------------


class TestStrategyAutocomplete(unittest.IsolatedAsyncioTestCase):
    """Tests for strategy_autocomplete function."""

    async def test_strategy_autocomplete_returns_matches(self):
        """Autocomplete returns matching PAPER strategies."""
        from src.discord_bot.cog_paper import strategy_autocomplete

        interaction = _make_interaction()
        interaction.client.strategy_manager = MagicMock()
        interaction.client.strategy_manager.list_strategies = AsyncMock(return_value=[
            {"name": "Iron Condor Weekly"},
            {"name": "Put Spread 0DTE"},
            {"name": "Iron Butterfly Monthly"},
        ])

        results = await strategy_autocomplete(interaction, "iron")

        self.assertEqual(len(results), 2)
        names = [r.name for r in results]
        self.assertIn("Iron Condor Weekly", names)
        self.assertIn("Iron Butterfly Monthly", names)

    async def test_strategy_autocomplete_no_manager(self):
        """Autocomplete returns empty when no strategy_manager."""
        from src.discord_bot.cog_paper import strategy_autocomplete

        interaction = _make_interaction()
        interaction.client.strategy_manager = None

        results = await strategy_autocomplete(interaction, "test")
        self.assertEqual(results, [])


# -- View tests --------------------------------------------------------------

# Note: discord.ui.View requires an event loop, so all View instantiation
# must happen inside async test methods (IsolatedAsyncioTestCase).


class TestPaginatedHistoryView(unittest.IsolatedAsyncioTestCase):
    """Tests for PaginatedHistoryView."""

    async def test_initial_state(self):
        """Initial state: page 1, prev disabled, next enabled."""
        from src.discord_bot.cog_paper import PaginatedHistoryView

        trades = [{"id": i} for i in range(25)]
        view = PaginatedHistoryView(trades, None, 7, page=1)

        self.assertEqual(view.total_pages, 2)
        self.assertTrue(view.prev_button.disabled)
        self.assertFalse(view.next_button.disabled)

    async def test_last_page(self):
        """Last page: prev enabled, next disabled."""
        from src.discord_bot.cog_paper import PaginatedHistoryView

        trades = [{"id": i} for i in range(25)]
        view = PaginatedHistoryView(trades, None, 7, page=2)

        self.assertFalse(view.prev_button.disabled)
        self.assertTrue(view.next_button.disabled)

    async def test_single_page(self):
        """Single page: both buttons disabled."""
        from src.discord_bot.cog_paper import PaginatedHistoryView

        trades = [{"id": i} for i in range(5)]
        view = PaginatedHistoryView(trades, None, 7, page=1)

        self.assertEqual(view.total_pages, 1)
        self.assertTrue(view.prev_button.disabled)
        self.assertTrue(view.next_button.disabled)

    async def test_next_click(self):
        """Next button increments page."""
        from src.discord_bot.cog_paper import PaginatedHistoryView

        trades = [
            {"id": i, "strategy_id": 1, "strategy_name": "Test",
             "entry_date": "2026-02-15", "exit_date": "2026-02-20",
             "entry_price": 2.0, "exit_price": 0.5,
             "total_pnl": 100.0, "fees": 5.0, "close_reason": "profit_target"}
            for i in range(25)
        ]
        view = PaginatedHistoryView(trades, None, 7, page=1)
        interaction = AsyncMock()

        await view.next_button.callback(interaction)

        self.assertEqual(view.page, 2)
        interaction.response.edit_message.assert_awaited_once()

    async def test_prev_click(self):
        """Prev button decrements page."""
        from src.discord_bot.cog_paper import PaginatedHistoryView

        trades = [
            {"id": i, "strategy_id": 1, "strategy_name": "Test",
             "entry_date": "2026-02-15", "exit_date": "2026-02-20",
             "entry_price": 2.0, "exit_price": 0.5,
             "total_pnl": 100.0, "fees": 5.0, "close_reason": "profit_target"}
            for i in range(25)
        ]
        view = PaginatedHistoryView(trades, None, 7, page=2)
        interaction = AsyncMock()

        await view.prev_button.callback(interaction)

        self.assertEqual(view.page, 1)
        interaction.response.edit_message.assert_awaited_once()


class TestCloseConfirmView(unittest.IsolatedAsyncioTestCase):
    """Tests for CloseConfirmView."""

    async def test_initial_state(self):
        """Initial state: confirmed is None."""
        from src.discord_bot.cog_paper import CloseConfirmView

        view = CloseConfirmView(position_id=1, reason="manual")
        self.assertIsNone(view.confirmed)
        self.assertEqual(view.position_id, 1)
        self.assertEqual(view.reason, "manual")

    async def test_confirm_click(self):
        """Confirm button sets confirmed=True and stops."""
        from src.discord_bot.cog_paper import CloseConfirmView

        view = CloseConfirmView(position_id=1, reason="manual")
        interaction = AsyncMock()

        await view.confirm.callback(interaction)

        self.assertTrue(view.confirmed)
        self.assertTrue(view.is_finished())

    async def test_cancel_click(self):
        """Cancel button sets confirmed=False and stops."""
        from src.discord_bot.cog_paper import CloseConfirmView

        view = CloseConfirmView(position_id=1, reason="manual")
        interaction = AsyncMock()

        await view.cancel.callback(interaction)

        self.assertFalse(view.confirmed)
        self.assertTrue(view.is_finished())


# -- Integration tests -------------------------------------------------------


class TestCogSetup(unittest.IsolatedAsyncioTestCase):
    """Tests for cog setup function."""

    async def test_cog_setup_registers(self):
        """setup() calls bot.add_cog with PaperTradingCog."""
        from src.discord_bot.cog_paper import setup, PaperTradingCog

        bot = _make_bot()
        bot.add_cog = AsyncMock()

        await setup(bot)

        bot.add_cog.assert_awaited_once()
        args = bot.add_cog.call_args.args
        self.assertIsInstance(args[0], PaperTradingCog)


if __name__ == "__main__":
    unittest.main()
