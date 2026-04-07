"""Tests for SpotGamma scheduler integration in SchedulerCog.

Covers:
  - ``_jitter()`` helper sleeps within bounds
  - ``_handle_spotgamma_levels()`` with data, with None, and when not configured
  - ``_handle_spotgamma_hiro()`` with data, with None, and when not configured
  - ``_handle_spotgamma_auth()`` happy path and exception safety
  - ``_handle_spotgamma_eod()`` injects features via feature store
  - All handlers survive exceptions without crashing
"""

import asyncio
from datetime import datetime, time, timedelta
from dataclasses import dataclass, field
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from src.data.spotgamma_models import SpotGammaHIRO, SpotGammaLevels


# ---------------------------------------------------------------------------
# Minimal stubs for bot / services -- just enough for SchedulerCog.__init__
# ---------------------------------------------------------------------------


class _StubServices:
    """Minimal stand-in for ServiceRegistry."""

    def __init__(self) -> None:
        self.data_manager = MagicMock()
        self.paper_engine = None
        self.store = None
        self.portfolio_analyzer = None
        self.reasoning_manager = None
        self.feature_store = None
        self.spotgamma_client = None
        self.spotgamma_store = None
        self.spotgamma_auth = None


def _make_bot() -> MagicMock:
    """Create a minimal bot mock with services attached."""
    bot = MagicMock()
    bot.services = _StubServices()
    return bot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cog(bot: MagicMock | None = None):
    """Instantiate SchedulerCog without starting the loop."""
    from src.discord_bot.cog_scheduler import SchedulerCog

    if bot is None:
        bot = _make_bot()

    # Prevent the tasks loop from actually starting
    with patch.object(SchedulerCog, "market_loop", new_callable=MagicMock):
        cog = SchedulerCog(bot)
    return cog


def _set_now(year=2026, month=4, day=6, hour=10, minute=0, weekday=0):
    """Return a ``_now_et`` replacement that returns a fixed datetime.

    ``weekday`` is ignored here; the real day of the week for
    2026-04-06 is a Monday (0), which is fine for market-hours tests.
    """
    from zoneinfo import ZoneInfo

    dt = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("America/New_York"))
    return lambda: dt


# ---------------------------------------------------------------------------
# Tests: _jitter
# ---------------------------------------------------------------------------


class TestJitter:
    @pytest.mark.asyncio
    async def test_jitter_sleeps_within_bounds(self):
        """_jitter should call asyncio.sleep with a value in [0, max_seconds]."""
        cog = _make_cog()
        with patch("src.discord_bot.cog_scheduler.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with patch("src.discord_bot.cog_scheduler.random.uniform", return_value=7.5):
                await cog._jitter(20)
                mock_sleep.assert_awaited_once_with(7.5)

    @pytest.mark.asyncio
    async def test_jitter_zero_max(self):
        """_jitter(0) should sleep between 0 and 0."""
        cog = _make_cog()
        with patch("src.discord_bot.cog_scheduler.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with patch("src.discord_bot.cog_scheduler.random.uniform", return_value=0.0):
                await cog._jitter(0)
                mock_sleep.assert_awaited_once_with(0.0)


# ---------------------------------------------------------------------------
# Tests: _handle_spotgamma_levels
# ---------------------------------------------------------------------------


class TestHandleSpotGammaLevels:
    @pytest.mark.asyncio
    async def test_skips_when_not_configured(self):
        """Handler should silently return when spotgamma_client is None."""
        cog = _make_cog()
        # spotgamma_client is already None by default
        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=10)):
            await cog._handle_spotgamma_levels()
        # No error, no call

    @pytest.mark.asyncio
    async def test_fetches_and_saves_levels(self):
        """Handler should convert raw dict to SpotGammaLevels and save."""
        bot = _make_bot()
        mock_client = AsyncMock()
        mock_client.get_levels = AsyncMock(return_value={
            "call_wall": 5300.0,
            "put_wall": 5100.0,
            "vol_trigger": 5200.0,
            "hedge_wall": 5250.0,
            "abs_gamma": 5275.0,
            "ticker": "SPX",
        })
        mock_store = AsyncMock()
        mock_store.save_levels = AsyncMock()

        bot.services.spotgamma_client = mock_client
        bot.services.spotgamma_store = mock_store

        cog = _make_cog(bot)

        # Simulate pre-market window (9:15 AM)
        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=9, minute=16)):
            with patch("src.discord_bot.cog_scheduler.asyncio.sleep", new_callable=AsyncMock):
                await cog._handle_spotgamma_levels()

        mock_client.get_levels.assert_awaited_once_with("SPX")
        mock_store.save_levels.assert_awaited_once()

        saved_levels = mock_store.save_levels.call_args[0][0]
        assert isinstance(saved_levels, SpotGammaLevels)
        assert saved_levels.call_wall == 5300.0
        assert saved_levels.put_wall == 5100.0
        assert saved_levels.vol_trigger == 5200.0
        assert saved_levels.source == "api"

    @pytest.mark.asyncio
    async def test_skips_when_client_returns_none(self):
        """Handler should skip gracefully when get_levels returns None."""
        bot = _make_bot()
        mock_client = AsyncMock()
        mock_client.get_levels = AsyncMock(return_value=None)
        mock_store = AsyncMock()

        bot.services.spotgamma_client = mock_client
        bot.services.spotgamma_store = mock_store

        cog = _make_cog(bot)

        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=9, minute=16)):
            with patch("src.discord_bot.cog_scheduler.asyncio.sleep", new_callable=AsyncMock):
                await cog._handle_spotgamma_levels()

        mock_store.save_levels.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_survives_exception(self):
        """Handler should log and continue if client raises."""
        bot = _make_bot()
        mock_client = AsyncMock()
        mock_client.get_levels = AsyncMock(side_effect=RuntimeError("network down"))
        mock_store = AsyncMock()

        bot.services.spotgamma_client = mock_client
        bot.services.spotgamma_store = mock_store

        cog = _make_cog(bot)

        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=9, minute=16)):
            with patch("src.discord_bot.cog_scheduler.asyncio.sleep", new_callable=AsyncMock):
                # Must not raise
                await cog._handle_spotgamma_levels()


# ---------------------------------------------------------------------------
# Tests: _handle_spotgamma_hiro
# ---------------------------------------------------------------------------


class TestHandleSpotGammaHIRO:
    @pytest.mark.asyncio
    async def test_skips_when_not_configured(self):
        """Handler should silently return when spotgamma services are None."""
        cog = _make_cog()
        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=10)):
            with patch("src.discord_bot.cog_scheduler._is_market_hours", return_value=True):
                await cog._handle_spotgamma_hiro()

    @pytest.mark.asyncio
    async def test_skips_outside_market_hours(self):
        """Handler should skip when market is closed."""
        bot = _make_bot()
        bot.services.spotgamma_client = AsyncMock()
        bot.services.spotgamma_store = AsyncMock()

        cog = _make_cog(bot)

        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=7)):
            with patch("src.discord_bot.cog_scheduler._is_market_hours", return_value=False):
                await cog._handle_spotgamma_hiro()

        bot.services.spotgamma_client.get_hiro.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fetches_and_saves_hiro(self):
        """Handler should convert raw dict to SpotGammaHIRO and save."""
        bot = _make_bot()
        mock_client = AsyncMock()
        mock_client.get_hiro = AsyncMock(return_value={
            "hedging_impact": 1.5,
            "cumulative_impact": 12.3,
            "ticker": "SPX",
        })
        mock_store = AsyncMock()
        mock_store.save_hiro = AsyncMock()

        bot.services.spotgamma_client = mock_client
        bot.services.spotgamma_store = mock_store

        cog = _make_cog(bot)

        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=10, minute=30)):
            with patch("src.discord_bot.cog_scheduler._is_market_hours", return_value=True):
                with patch("src.discord_bot.cog_scheduler.asyncio.sleep", new_callable=AsyncMock):
                    await cog._handle_spotgamma_hiro()

        mock_client.get_hiro.assert_awaited_once_with("SPX")
        mock_store.save_hiro.assert_awaited_once()

        saved = mock_store.save_hiro.call_args[0][0]
        assert isinstance(saved, SpotGammaHIRO)
        assert saved.hedging_impact == 1.5
        assert saved.cumulative_impact == 12.3

    @pytest.mark.asyncio
    async def test_survives_exception(self):
        """Handler should log and continue if client raises."""
        bot = _make_bot()
        mock_client = AsyncMock()
        mock_client.get_hiro = AsyncMock(side_effect=RuntimeError("boom"))
        mock_store = AsyncMock()

        bot.services.spotgamma_client = mock_client
        bot.services.spotgamma_store = mock_store

        cog = _make_cog(bot)

        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=10)):
            with patch("src.discord_bot.cog_scheduler._is_market_hours", return_value=True):
                with patch("src.discord_bot.cog_scheduler.asyncio.sleep", new_callable=AsyncMock):
                    await cog._handle_spotgamma_hiro()


# ---------------------------------------------------------------------------
# Tests: _handle_spotgamma_auth
# ---------------------------------------------------------------------------


class TestHandleSpotGammaAuth:
    @pytest.mark.asyncio
    async def test_skips_when_not_configured(self):
        """Should silently return when spotgamma_auth is None."""
        cog = _make_cog()
        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=8, minute=5)):
            await cog._handle_spotgamma_auth()

    @pytest.mark.asyncio
    async def test_authenticates_once_per_day(self):
        """Should call authenticate() exactly once, then set flag."""
        bot = _make_bot()
        mock_auth = AsyncMock()
        mock_auth.authenticate = AsyncMock(return_value={})
        bot.services.spotgamma_auth = mock_auth

        cog = _make_cog(bot)

        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=8, minute=5)):
            with patch("src.discord_bot.cog_scheduler.asyncio.sleep", new_callable=AsyncMock):
                await cog._handle_spotgamma_auth()
                await cog._handle_spotgamma_auth()  # second call should be no-op

        mock_auth.authenticate.assert_awaited_once()
        assert cog._spotgamma_auth_today is True

    @pytest.mark.asyncio
    async def test_survives_auth_exception(self):
        """Should not crash when authenticate() raises."""
        bot = _make_bot()
        mock_auth = AsyncMock()
        mock_auth.authenticate = AsyncMock(side_effect=RuntimeError("auth exploded"))
        bot.services.spotgamma_auth = mock_auth

        cog = _make_cog(bot)

        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=8, minute=5)):
            with patch("src.discord_bot.cog_scheduler.asyncio.sleep", new_callable=AsyncMock):
                await cog._handle_spotgamma_auth()

        assert cog._spotgamma_auth_today is True  # flag set even on error


# ---------------------------------------------------------------------------
# Tests: _handle_spotgamma_eod
# ---------------------------------------------------------------------------


class TestHandleSpotGammaEOD:
    @pytest.mark.asyncio
    async def test_skips_when_not_configured(self):
        """Should silently return when SpotGamma store is None."""
        cog = _make_cog()
        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=16, minute=11)):
            await cog._handle_spotgamma_eod()
        assert cog._spotgamma_eod_today is True

    @pytest.mark.asyncio
    async def test_saves_features_from_levels_and_hiro(self):
        """Should read latest levels/HIRO and save as features."""
        bot = _make_bot()

        mock_sg_store = AsyncMock()
        mock_levels = SpotGammaLevels(
            call_wall=5300.0,
            put_wall=5100.0,
            vol_trigger=5200.0,
            hedge_wall=5250.0,
            abs_gamma=5275.0,
            timestamp=datetime(2026, 4, 6, 15, 30),
            ticker="SPX",
            source="api",
        )
        mock_hiro = SpotGammaHIRO(
            timestamp=datetime(2026, 4, 6, 15, 55),
            hedging_impact=2.0,
            cumulative_impact=25.0,
            ticker="SPX",
            source="api",
        )
        mock_sg_store.get_latest_levels = AsyncMock(return_value=mock_levels)
        mock_sg_store.get_latest_hiro = AsyncMock(return_value=mock_hiro)

        mock_feature_store = AsyncMock()
        mock_feature_store.save_features = AsyncMock()

        bot.services.spotgamma_client = AsyncMock()  # Must be non-None for _spotgamma_available
        bot.services.spotgamma_store = mock_sg_store
        bot.services.feature_store = mock_feature_store

        cog = _make_cog(bot)

        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=16, minute=11)):
            await cog._handle_spotgamma_eod()

        mock_feature_store.save_features.assert_awaited_once()
        call_args = mock_feature_store.save_features.call_args
        assert call_args[0][0] == "SPX"  # ticker
        features = call_args[0][2]
        assert features["sg_vol_trigger"] == 5200.0
        assert features["sg_call_wall"] == 5300.0
        assert features["sg_put_wall"] == 5100.0
        assert features["sg_abs_gamma"] == 5275.0
        assert features["sg_hiro_eod"] == 25.0

    @pytest.mark.asyncio
    async def test_handles_no_data_gracefully(self):
        """Should skip feature save when no levels or HIRO data exists."""
        bot = _make_bot()

        mock_sg_store = AsyncMock()
        mock_sg_store.get_latest_levels = AsyncMock(return_value=None)
        mock_sg_store.get_latest_hiro = AsyncMock(return_value=None)

        mock_feature_store = AsyncMock()

        bot.services.spotgamma_client = AsyncMock()
        bot.services.spotgamma_store = mock_sg_store
        bot.services.feature_store = mock_feature_store

        cog = _make_cog(bot)

        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=16, minute=11)):
            await cog._handle_spotgamma_eod()

        mock_feature_store.save_features.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_survives_exception(self):
        """Should not crash when store raises."""
        bot = _make_bot()

        mock_sg_store = AsyncMock()
        mock_sg_store.get_latest_levels = AsyncMock(side_effect=RuntimeError("db dead"))

        bot.services.spotgamma_client = AsyncMock()
        bot.services.spotgamma_store = mock_sg_store
        bot.services.feature_store = AsyncMock()

        cog = _make_cog(bot)

        with patch("src.discord_bot.cog_scheduler._now_et", _set_now(hour=16, minute=11)):
            await cog._handle_spotgamma_eod()

        assert cog._spotgamma_eod_today is True
