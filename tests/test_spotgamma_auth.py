"""Tests for SpotGamma Playwright auth broker -- all browser calls are mocked.

Covers: successful login, failed login, token refresh / expiry,
is_authenticated property, close() cleanup, persistent context reuse,
graceful degradation when playwright is missing, and cookie vs JWT
extraction strategies.
"""

import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_page(url_after_login: str = "https://spotgamma.com/dashboard/") -> AsyncMock:
    """Build a mock Playwright Page that simulates a successful login."""
    page = AsyncMock()
    page.url = url_after_login
    page.goto = AsyncMock()
    page.fill = AsyncMock()
    page.click = AsyncMock()
    page.wait_for_url = AsyncMock()
    page.evaluate = AsyncMock(return_value=None)
    page.close = AsyncMock()
    return page


def _make_mock_context(page: AsyncMock | None = None) -> AsyncMock:
    """Build a mock Playwright BrowserContext."""
    ctx = AsyncMock()
    ctx.new_page = AsyncMock(return_value=page or _make_mock_page())
    ctx.cookies = AsyncMock(return_value=[])
    ctx.close = AsyncMock()
    return ctx


def _make_mock_playwright(context: AsyncMock | None = None) -> AsyncMock:
    """Build a mock Playwright instance with chromium launcher."""
    pw = AsyncMock()
    pw.chromium = AsyncMock()
    pw.chromium.launch_persistent_context = AsyncMock(
        return_value=context or _make_mock_context()
    )
    pw.stop = AsyncMock()
    return pw


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSpotGammaAuthBrokerInit:
    """Construction and basic properties."""

    def test_init_defaults(self):
        """Broker initialises with empty headers and not-authenticated."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(email="a@b.com", password="pw")
        assert broker.is_authenticated is False
        assert broker._auth_headers == {}

    def test_init_custom_auth_dir(self):
        """Custom auth_dir is stored correctly."""
        from pathlib import Path
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(
            email="a@b.com", password="pw", auth_dir="/tmp/sg_auth"
        )
        assert broker._auth_dir == Path("/tmp/sg_auth")


class TestAuthenticate:
    """Login flow (mocked browser)."""

    @pytest.mark.asyncio
    async def test_successful_login_jwt(self):
        """Persistent context already has a JWT -- skip login form, reuse session."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        page = _make_mock_page()
        # Simulate JWT already present in localStorage (persistent context active)
        page.evaluate = AsyncMock(side_effect=lambda expr: "fake-jwt-token" if "token" in expr.lower() else None)

        ctx = _make_mock_context(page)
        pw = _make_mock_playwright(ctx)

        broker = SpotGammaAuthBroker(email="user@example.com", password="secret")

        with patch("src.data.spotgamma_auth.async_playwright") as mock_pw_func, \
             patch("src.data.spotgamma_auth._PLAYWRIGHT_AVAILABLE", True), \
             patch("src.data.spotgamma_auth._STEALTH_AVAILABLE", False):
            mock_pw_func.return_value.start = AsyncMock(return_value=pw)
            headers = await broker.authenticate()

        assert headers.get("Authorization") == "Bearer fake-jwt-token"
        assert broker.is_authenticated is True
        # New behavior: dashboard probe succeeded; login form was never filled.
        page.fill.assert_not_called()
        page.close.assert_awaited_once()

        await broker.close()

    @pytest.mark.asyncio
    async def test_successful_login_cookies(self):
        """Successful login falling back to cookies when no JWT is found."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        page = _make_mock_page()
        page.evaluate = AsyncMock(return_value=None)  # no JWT

        ctx = _make_mock_context(page)
        ctx.cookies = AsyncMock(return_value=[
            {"name": "session_id", "value": "abc123"},
            {"name": "csrf", "value": "xyz789"},
        ])
        pw = _make_mock_playwright(ctx)

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")

        with patch("src.data.spotgamma_auth.async_playwright") as mock_pw_func, \
             patch("src.data.spotgamma_auth._PLAYWRIGHT_AVAILABLE", True), \
             patch("src.data.spotgamma_auth._STEALTH_AVAILABLE", False):
            mock_pw_func.return_value.start = AsyncMock(return_value=pw)
            headers = await broker.authenticate()

        assert "Cookie" in headers
        assert "session_id=abc123" in headers["Cookie"]
        assert "csrf=xyz789" in headers["Cookie"]
        assert broker.is_authenticated is True

        await broker.close()

    @pytest.mark.asyncio
    async def test_failed_login_no_redirect(self):
        """Login that doesn't reach dashboard raises SpotGammaAuthError."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker, SpotGammaAuthError

        page = _make_mock_page(url_after_login="https://spotgamma.com/login/?error=1")
        page.wait_for_url = AsyncMock(side_effect=Exception("Timeout"))

        ctx = _make_mock_context(page)
        pw = _make_mock_playwright(ctx)

        broker = SpotGammaAuthBroker(email="bad@e.com", password="wrong")

        with patch("src.data.spotgamma_auth.async_playwright") as mock_pw_func, \
             patch("src.data.spotgamma_auth._PLAYWRIGHT_AVAILABLE", True), \
             patch("src.data.spotgamma_auth._STEALTH_AVAILABLE", False):
            mock_pw_func.return_value.start = AsyncMock(return_value=pw)
            with pytest.raises(SpotGammaAuthError, match="did not redirect"):
                await broker.authenticate()

        assert broker.is_authenticated is False

        await broker.close()

    @pytest.mark.asyncio
    async def test_login_general_exception_returns_empty(self):
        """An unexpected exception during login returns empty headers (graceful)."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")

        with patch("src.data.spotgamma_auth.async_playwright") as mock_pw_func, \
             patch("src.data.spotgamma_auth._PLAYWRIGHT_AVAILABLE", True), \
             patch("src.data.spotgamma_auth._STEALTH_AVAILABLE", False):
            mock_pw_func.return_value.start = AsyncMock(
                side_effect=RuntimeError("Browser crashed")
            )
            headers = await broker.authenticate()

        assert headers == {}
        assert broker.is_authenticated is False


class TestRefreshLogic:
    """Token freshness checks and automatic re-auth."""

    @pytest.mark.asyncio
    async def test_fresh_token_skips_reauth(self):
        """refresh_if_needed returns cached headers when token is fresh."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")
        # Simulate a prior successful auth
        broker._auth_headers = {"Authorization": "Bearer cached"}
        broker._last_auth_time = time.monotonic()  # just now

        headers = await broker.refresh_if_needed()
        assert headers == {"Authorization": "Bearer cached"}

    @pytest.mark.asyncio
    async def test_expired_token_triggers_reauth(self):
        """refresh_if_needed re-authenticates when token is older than TTL."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker, _TOKEN_TTL_SECONDS

        page = _make_mock_page()
        page.evaluate = AsyncMock(side_effect=lambda expr: "new-jwt" if "token" in expr else None)
        ctx = _make_mock_context(page)
        pw = _make_mock_playwright(ctx)

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")
        # Simulate expired token
        broker._auth_headers = {"Authorization": "Bearer old"}
        broker._last_auth_time = time.monotonic() - _TOKEN_TTL_SECONDS - 1

        assert broker.is_authenticated is False  # expired

        with patch("src.data.spotgamma_auth.async_playwright") as mock_pw_func, \
             patch("src.data.spotgamma_auth._PLAYWRIGHT_AVAILABLE", True), \
             patch("src.data.spotgamma_auth._STEALTH_AVAILABLE", False):
            mock_pw_func.return_value.start = AsyncMock(return_value=pw)
            headers = await broker.refresh_if_needed()

        assert headers.get("Authorization") == "Bearer new-jwt"
        assert broker.is_authenticated is True

        await broker.close()


class TestIsAuthenticated:
    """is_authenticated property edge cases."""

    def test_false_when_no_headers(self):
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")
        assert broker.is_authenticated is False

    def test_false_when_expired(self):
        from src.data.spotgamma_auth import SpotGammaAuthBroker, _TOKEN_TTL_SECONDS

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")
        broker._auth_headers = {"Cookie": "x=y"}
        broker._last_auth_time = time.monotonic() - _TOKEN_TTL_SECONDS - 10
        assert broker.is_authenticated is False

    def test_true_when_fresh(self):
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")
        broker._auth_headers = {"Cookie": "x=y"}
        broker._last_auth_time = time.monotonic()
        assert broker.is_authenticated is True


class TestClose:
    """close() cleanup."""

    @pytest.mark.asyncio
    async def test_close_cleans_up(self):
        """close() calls close/stop on context, browser, playwright."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")
        mock_ctx = AsyncMock()
        mock_browser = AsyncMock()
        mock_pw = AsyncMock()

        broker._context = mock_ctx
        broker._browser = mock_browser
        broker._playwright = mock_pw

        await broker.close()

        mock_ctx.close.assert_awaited_once()
        mock_browser.close.assert_awaited_once()
        mock_pw.stop.assert_awaited_once()

        assert broker._context is None
        assert broker._browser is None
        assert broker._playwright is None

    @pytest.mark.asyncio
    async def test_close_is_idempotent(self):
        """Calling close() when nothing is initialised does not raise."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")
        await broker.close()  # should not raise

    @pytest.mark.asyncio
    async def test_close_swallows_exceptions(self):
        """close() ignores exceptions from underlying close/stop calls."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")
        broker._context = AsyncMock(close=AsyncMock(side_effect=RuntimeError("boom")))
        broker._browser = AsyncMock(close=AsyncMock(side_effect=RuntimeError("crash")))
        broker._playwright = AsyncMock(stop=AsyncMock(side_effect=RuntimeError("fail")))

        await broker.close()  # should not raise
        assert broker._context is None


class TestGracefulDegradation:
    """Behaviour when playwright is not installed."""

    @pytest.mark.asyncio
    async def test_no_playwright_returns_empty_headers(self):
        """Without playwright, authenticate() returns empty headers gracefully."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")

        with patch("src.data.spotgamma_auth._PLAYWRIGHT_AVAILABLE", False):
            headers = await broker.authenticate()

        assert headers == {}
        assert broker.is_authenticated is False

    @pytest.mark.asyncio
    async def test_get_auth_headers_delegates(self):
        """get_auth_headers() delegates to refresh_if_needed()."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")
        broker._auth_headers = {"Authorization": "Bearer test"}
        broker._last_auth_time = time.monotonic()

        headers = await broker.get_auth_headers()
        assert headers == {"Authorization": "Bearer test"}


class TestStealthIntegration:
    """Verify stealth is applied when available."""

    @pytest.mark.asyncio
    async def test_stealth_applied_when_available(self):
        """stealth_async is called on the page when playwright-stealth is present."""
        from src.data.spotgamma_auth import SpotGammaAuthBroker

        page = _make_mock_page()
        page.evaluate = AsyncMock(side_effect=lambda expr: "jwt" if "token" in expr else None)
        ctx = _make_mock_context(page)
        pw = _make_mock_playwright(ctx)

        broker = SpotGammaAuthBroker(email="u@e.com", password="p")

        mock_stealth = AsyncMock()
        with patch("src.data.spotgamma_auth.async_playwright") as mock_pw_func, \
             patch("src.data.spotgamma_auth._PLAYWRIGHT_AVAILABLE", True), \
             patch("src.data.spotgamma_auth._STEALTH_AVAILABLE", True), \
             patch("src.data.spotgamma_auth.stealth_async", mock_stealth):
            mock_pw_func.return_value.start = AsyncMock(return_value=pw)
            await broker.authenticate()

        mock_stealth.assert_awaited_once_with(page)

        await broker.close()
