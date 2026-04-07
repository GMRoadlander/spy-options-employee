"""Tests for SpotGamma Playwright fallback scraper -- all browser calls mocked.

Covers: cache hit / miss / expiry, navigation success / failure,
graceful degradation when playwright is absent, close() cleanup,
type-checking on auth_broker, and the placeholder extractors.
"""

import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.data.spotgamma_auth import SpotGammaAuthBroker
from src.data.spotgamma_models import SpotGammaLevels, SpotGammaHIRO


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_auth_broker(*, has_context: bool = True) -> SpotGammaAuthBroker:
    """Build a SpotGammaAuthBroker with mocked internals."""
    broker = SpotGammaAuthBroker(email="test@example.com", password="pw")
    if has_context:
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.close = AsyncMock()
        mock_ctx = AsyncMock()
        mock_ctx.new_page = AsyncMock(return_value=mock_page)
        broker._context = mock_ctx
    else:
        broker._context = None
    return broker


def _make_scraper(*, has_context: bool = True):
    """Build a SpotGammaScraper backed by a mocked auth broker."""
    from src.data.spotgamma_scraper import SpotGammaScraper

    broker = _make_auth_broker(has_context=has_context)
    return SpotGammaScraper(auth_broker=broker), broker


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInit:
    """Construction and type-checking."""

    def test_valid_auth_broker(self):
        """Scraper accepts a real SpotGammaAuthBroker."""
        from src.data.spotgamma_scraper import SpotGammaScraper

        broker = _make_auth_broker()
        scraper = SpotGammaScraper(auth_broker=broker)
        assert scraper._auth is broker
        assert scraper._cache == {}

    def test_invalid_auth_broker_raises(self):
        """Passing a non-broker object raises TypeError."""
        from src.data.spotgamma_scraper import SpotGammaScraper

        with pytest.raises(TypeError, match="SpotGammaAuthBroker"):
            SpotGammaScraper(auth_broker="not-a-broker")


class TestCacheHit:
    """When data is cached and fresh, no navigation should happen."""

    @pytest.mark.asyncio
    async def test_get_levels_cache_hit(self):
        """Cached levels are returned without navigating."""
        scraper, broker = _make_scraper()

        sentinel = object()
        scraper._cache["levels:SPX"] = (time.monotonic(), sentinel)

        with patch("src.data.spotgamma_scraper._PLAYWRIGHT_AVAILABLE", True):
            result = await scraper.get_levels("SPX")
        assert result is sentinel
        # new_page should NOT have been called
        broker._context.new_page.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_hiro_cache_hit(self):
        """Cached HIRO is returned without navigating."""
        scraper, broker = _make_scraper()

        sentinel = object()
        scraper._cache["hiro:SPX"] = (time.monotonic(), sentinel)

        with patch("src.data.spotgamma_scraper._PLAYWRIGHT_AVAILABLE", True):
            result = await scraper.get_hiro("SPX")
        assert result is sentinel
        broker._context.new_page.assert_not_awaited()


class TestCacheMiss:
    """When cache is empty or expired, navigation is triggered."""

    @pytest.mark.asyncio
    async def test_get_levels_cache_miss_navigates(self):
        """Empty cache triggers page navigation."""
        scraper, broker = _make_scraper()

        with patch("src.data.spotgamma_scraper._PLAYWRIGHT_AVAILABLE", True):
            result = await scraper.get_levels("SPX")
        # Placeholder extractor returns None, but navigation should happen
        broker._context.new_page.assert_awaited_once()
        # Placeholder returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_get_hiro_cache_miss_navigates(self):
        """Empty cache triggers page navigation for HIRO."""
        scraper, broker = _make_scraper()

        with patch("src.data.spotgamma_scraper._PLAYWRIGHT_AVAILABLE", True):
            result = await scraper.get_hiro("SPX")
        broker._context.new_page.assert_awaited_once()
        assert result is None


class TestCacheExpiry:
    """Expired cache entries trigger fresh navigation."""

    @pytest.mark.asyncio
    async def test_expired_cache_triggers_navigation(self):
        """Data older than TTL causes a re-scrape."""
        scraper, broker = _make_scraper()

        # Insert stale cache entry (6 minutes ago, TTL is 5 minutes)
        stale_time = time.monotonic() - 360
        scraper._cache["levels:SPX"] = (stale_time, "stale-data")

        with patch("src.data.spotgamma_scraper._PLAYWRIGHT_AVAILABLE", True):
            result = await scraper.get_levels("SPX")
        # Should have navigated because cache expired
        broker._context.new_page.assert_awaited_once()
        # Placeholder extractor returns None
        assert result is None

    def test_is_cached_false_for_expired(self):
        """_is_cached returns False for entries past TTL."""
        scraper, _ = _make_scraper()

        scraper._cache["test"] = (time.monotonic() - 600, "old")
        assert scraper._is_cached("test") is False

    def test_is_cached_true_for_fresh(self):
        """_is_cached returns True for entries within TTL."""
        scraper, _ = _make_scraper()

        scraper._cache["test"] = (time.monotonic(), "fresh")
        assert scraper._is_cached("test") is True

    def test_is_cached_false_for_missing(self):
        """_is_cached returns False for keys that don't exist."""
        scraper, _ = _make_scraper()

        assert scraper._is_cached("nonexistent") is False


class TestNavigationFailure:
    """Failures during navigation return None gracefully."""

    @pytest.mark.asyncio
    async def test_goto_failure_returns_none(self):
        """If page.goto raises, get_levels returns None."""
        scraper, broker = _make_scraper()

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=Exception("Network error"))
        mock_page.close = AsyncMock()
        broker._context.new_page = AsyncMock(return_value=mock_page)

        with patch("src.data.spotgamma_scraper._PLAYWRIGHT_AVAILABLE", True):
            result = await scraper.get_levels("SPX")
        assert result is None
        # Page should still be closed in finally block
        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_context_returns_none(self):
        """If auth broker has no browser context, returns None."""
        scraper, broker = _make_scraper(has_context=False)

        result = await scraper.get_levels("SPX")
        assert result is None

    @pytest.mark.asyncio
    async def test_page_close_failure_swallowed(self):
        """Exception in page.close() is swallowed (no crash)."""
        scraper, broker = _make_scraper()

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.close = AsyncMock(side_effect=RuntimeError("close failed"))
        broker._context.new_page = AsyncMock(return_value=mock_page)

        # Should not raise despite page.close() failing
        result = await scraper.get_levels("SPX")
        assert result is None  # placeholder returns None


class TestGracefulDegradation:
    """Behaviour when playwright is not installed."""

    @pytest.mark.asyncio
    async def test_no_playwright_get_levels_returns_none(self):
        """Without playwright, get_levels returns None."""
        scraper, _ = _make_scraper()

        with patch("src.data.spotgamma_scraper._PLAYWRIGHT_AVAILABLE", False):
            result = await scraper.get_levels("SPX")

        assert result is None

    @pytest.mark.asyncio
    async def test_no_playwright_get_hiro_returns_none(self):
        """Without playwright, get_hiro returns None."""
        scraper, _ = _make_scraper()

        with patch("src.data.spotgamma_scraper._PLAYWRIGHT_AVAILABLE", False):
            result = await scraper.get_hiro("SPX")

        assert result is None


class TestClose:
    """close() cleanup."""

    @pytest.mark.asyncio
    async def test_close_clears_cache(self):
        """close() empties the internal cache."""
        scraper, _ = _make_scraper()

        scraper._cache["levels:SPX"] = (time.monotonic(), "data")
        scraper._cache["hiro:SPX"] = (time.monotonic(), "data")

        await scraper.close()

        assert scraper._cache == {}

    @pytest.mark.asyncio
    async def test_close_does_not_close_auth_broker(self):
        """close() should NOT close the auth broker (caller owns it)."""
        scraper, broker = _make_scraper()

        # Give the broker a mock context to verify it's not touched
        broker._context.close = AsyncMock()

        await scraper.close()

        broker._context.close.assert_not_awaited()


class TestNavigateAndExtractCaching:
    """Verify that successful extraction populates the cache."""

    @pytest.mark.asyncio
    async def test_successful_extraction_populates_cache(self):
        """When the extractor returns a value, it gets cached."""
        scraper, broker = _make_scraper()

        sentinel = {"key": "value"}

        async def mock_extractor(page):
            return sentinel

        result = await scraper._navigate_and_extract(
            url="https://example.com",
            cache_key="test:key",
            extractor=mock_extractor,
        )

        assert result is sentinel
        assert "test:key" in scraper._cache
        assert scraper._cache["test:key"][1] is sentinel

    @pytest.mark.asyncio
    async def test_none_extraction_does_not_cache(self):
        """When the extractor returns None, nothing is cached."""
        scraper, broker = _make_scraper()

        async def mock_extractor(page):
            return None

        result = await scraper._navigate_and_extract(
            url="https://example.com",
            cache_key="test:nothing",
            extractor=mock_extractor,
        )

        assert result is None
        assert "test:nothing" not in scraper._cache
