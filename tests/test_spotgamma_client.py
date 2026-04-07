"""Tests for SpotGammaClient -- all API calls and auth are mocked.

Covers: request method (success, auth retry, rate limits, error handling),
each endpoint method routing, session lifecycle, jitter configuration,
and graceful degradation on network errors.
"""

import asyncio
import time

import aiohttp
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.data.spotgamma_client import (
    SpotGammaAuthError,
    SpotGammaClient,
    SpotGammaError,
    SpotGammaRateLimitError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_auth_broker(headers: dict[str, str] | None = None) -> AsyncMock:
    """Create a mock SpotGammaAuthBroker that returns test headers."""
    broker = AsyncMock()
    broker.get_auth_headers = AsyncMock(
        return_value=headers or {"Cookie": "session=test_token_123"}
    )
    broker.authenticate = AsyncMock(
        return_value=headers or {"Cookie": "session=refreshed_token"}
    )
    return broker


def _mock_response(
    status: int = 200,
    json_data: dict | None = None,
    text: str = "",
) -> AsyncMock:
    """Create a mock aiohttp response supporting async context manager."""
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data or {})
    resp.text = AsyncMock(return_value=text)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def _make_client(
    auth_headers: dict[str, str] | None = None,
    requests_per_minute: int = 100,
    max_jitter_seconds: float = 0.0,
) -> tuple[SpotGammaClient, AsyncMock]:
    """Create a SpotGammaClient with mocked auth broker and zero jitter.

    Returns (client, mock_broker) tuple.
    """
    broker = _mock_auth_broker(auth_headers)
    client = SpotGammaClient(
        auth_broker=broker,
        requests_per_minute=requests_per_minute,
        max_jitter_seconds=max_jitter_seconds,
    )
    return client, broker


# ---------------------------------------------------------------------------
# Tests: _request / _do_request
# ---------------------------------------------------------------------------


class TestRequest:
    """Tests for the core request method."""

    @pytest.mark.asyncio
    async def test_successful_request_returns_json(self):
        """Returns parsed JSON dict on 200 response."""
        client, broker = _make_client()
        expected = {"levels": {"call_wall": 5500, "put_wall": 5200}}
        mock_resp = _mock_response(200, expected)
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            result = await client._request("GET", "/api/levels/SPX")

        assert result == expected

    @pytest.mark.asyncio
    async def test_auth_headers_included_in_request(self):
        """Auth headers from broker are sent with each request."""
        client, broker = _make_client(
            auth_headers={"Authorization": "Bearer jwt_test_token"}
        )
        mock_resp = _mock_response(200, {"ok": True})
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            await client._request("GET", "/api/levels/SPX")

        call_kwargs = mock_session.request.call_args[1]
        headers = call_kwargs.get("headers", {})
        assert headers["Authorization"] == "Bearer jwt_test_token"
        assert "User-Agent" in headers

    @pytest.mark.asyncio
    async def test_user_agent_is_browser_like(self):
        """User-Agent header looks like a real browser."""
        client, _ = _make_client()
        mock_resp = _mock_response(200, {"ok": True})
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            await client._request("GET", "/api/levels/SPX")

        call_kwargs = mock_session.request.call_args[1]
        ua = call_kwargs["headers"]["User-Agent"]
        assert "Mozilla" in ua
        assert "Chrome" in ua

    @pytest.mark.asyncio
    async def test_401_triggers_reauth_and_retry(self):
        """HTTP 401 triggers re-authentication and a single retry."""
        client, broker = _make_client()

        # First call returns 401, second returns 200 after re-auth
        resp_401 = _mock_response(401)
        resp_200 = _mock_response(200, {"levels": {"call_wall": 5500}})

        mock_session = AsyncMock()
        mock_session.request = MagicMock(side_effect=[resp_401, resp_200])

        with patch.object(client, "_get_session", return_value=mock_session):
            result = await client._request("GET", "/api/levels/SPX")

        assert result == {"levels": {"call_wall": 5500}}
        broker.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_401_after_reauth_raises(self):
        """HTTP 401 after re-auth raises SpotGammaAuthError."""
        client, broker = _make_client()

        resp_401 = _mock_response(401)

        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=resp_401)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(SpotGammaAuthError, match="401"):
                await client._request("GET", "/api/levels/SPX")

        broker.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self):
        """HTTP 429 raises SpotGammaRateLimitError."""
        client, _ = _make_client()
        mock_resp = _mock_response(429)
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(SpotGammaRateLimitError, match="429"):
                await client._request("GET", "/api/levels/SPX")

    @pytest.mark.asyncio
    async def test_500_returns_none(self):
        """HTTP 500 returns None (graceful degradation)."""
        client, _ = _make_client()
        mock_resp = _mock_response(500, text="Internal Server Error")
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            result = await client._request("GET", "/api/levels/SPX")

        assert result is None

    @pytest.mark.asyncio
    async def test_timeout_returns_none(self):
        """Request timeout returns None (graceful degradation)."""
        client, _ = _make_client()

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_cm)

        with patch.object(client, "_get_session", return_value=mock_session):
            result = await client._request("GET", "/api/levels/SPX")

        assert result is None

    @pytest.mark.asyncio
    async def test_network_error_returns_none(self):
        """Network error (aiohttp.ClientError) returns None."""
        client, _ = _make_client()

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(
            side_effect=aiohttp.ClientError("Connection refused")
        )
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_cm)

        with patch.object(client, "_get_session", return_value=mock_session):
            result = await client._request("GET", "/api/levels/SPX")

        assert result is None


# ---------------------------------------------------------------------------
# Tests: Endpoint methods
# ---------------------------------------------------------------------------


class TestEndpoints:
    """Tests that each endpoint method calls _request with the correct path."""

    @pytest.mark.asyncio
    async def test_get_levels_default_ticker(self):
        """get_levels('SPX') calls _request with /api/levels/SPX."""
        client, _ = _make_client()
        expected = {"call_wall": 5500}

        with patch.object(client, "_request", return_value=expected) as mock_req:
            result = await client.get_levels()

        mock_req.assert_called_once_with("GET", "/api/levels/SPX")
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_levels_custom_ticker(self):
        """get_levels('SPY') calls _request with /api/levels/SPY."""
        client, _ = _make_client()

        with patch.object(client, "_request", return_value={"ok": True}) as mock_req:
            await client.get_levels("spy")

        mock_req.assert_called_once_with("GET", "/api/levels/SPY")

    @pytest.mark.asyncio
    async def test_get_hiro(self):
        """get_hiro calls _request with /api/hiro/{ticker}."""
        client, _ = _make_client()

        with patch.object(client, "_request", return_value={"hiro": 1.5}) as mock_req:
            result = await client.get_hiro("SPX")

        mock_req.assert_called_once_with("GET", "/api/hiro/SPX")
        assert result == {"hiro": 1.5}

    @pytest.mark.asyncio
    async def test_get_equity_hub(self):
        """get_equity_hub calls _request with /api/equity-hub/{ticker}."""
        client, _ = _make_client()

        with patch.object(client, "_request", return_value={"levels": []}) as mock_req:
            result = await client.get_equity_hub("SPX")

        mock_req.assert_called_once_with("GET", "/api/equity-hub/SPX")
        assert result == {"levels": []}

    @pytest.mark.asyncio
    async def test_get_trace(self):
        """get_trace calls _request with /api/trace."""
        client, _ = _make_client()

        with patch.object(client, "_request", return_value={"heatmap": []}) as mock_req:
            result = await client.get_trace()

        mock_req.assert_called_once_with("GET", "/api/trace")
        assert result == {"heatmap": []}

    @pytest.mark.asyncio
    async def test_get_notes(self):
        """get_notes calls _request with /api/notes."""
        client, _ = _make_client()

        with patch.object(client, "_request", return_value={"text": "Bullish"}) as mock_req:
            result = await client.get_notes()

        mock_req.assert_called_once_with("GET", "/api/notes")
        assert result == {"text": "Bullish"}


# ---------------------------------------------------------------------------
# Tests: Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """Tests for rate limit tracking and enforcement."""

    def test_rate_limit_status_initial(self):
        """Fresh client reports zero usage."""
        client, _ = _make_client(requests_per_minute=10)
        status = client.rate_limit_status
        assert status["minute_used"] == 0
        assert status["minute_limit"] == 10

    def test_minute_rate_limit_exceeded(self):
        """SpotGammaRateLimitError raised when minute limit is hit."""
        client, _ = _make_client(requests_per_minute=3)
        now = time.time()
        client._minute_requests = [now, now, now]

        with pytest.raises(SpotGammaRateLimitError, match="requests/minute"):
            client._check_rate_limit()

    def test_old_requests_cleaned(self):
        """Requests older than 60 seconds are removed from tracking."""
        client, _ = _make_client(requests_per_minute=5)
        old_time = time.time() - 120  # 2 minutes ago
        client._minute_requests = [old_time, old_time, old_time]

        client._check_rate_limit()
        assert len(client._minute_requests) == 0

    def test_record_request_increments(self):
        """_record_request adds a timestamp to minute tracking."""
        client, _ = _make_client()
        client._record_request()
        assert len(client._minute_requests) == 1

    @pytest.mark.asyncio
    async def test_rate_limit_checked_before_request(self):
        """_request raises SpotGammaRateLimitError when limit is already hit."""
        client, _ = _make_client(requests_per_minute=2)
        now = time.time()
        client._minute_requests = [now, now]

        with pytest.raises(SpotGammaRateLimitError):
            await client._request("GET", "/api/levels/SPX")


# ---------------------------------------------------------------------------
# Tests: Jitter configuration
# ---------------------------------------------------------------------------


class TestJitter:
    """Tests for anti-detection jitter."""

    @pytest.mark.asyncio
    async def test_zero_jitter_skips_sleep(self):
        """When max_jitter_seconds=0, asyncio.sleep is not called."""
        client, _ = _make_client(max_jitter_seconds=0.0)
        mock_resp = _mock_response(200, {"ok": True})
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            with patch("src.data.spotgamma_client.asyncio.sleep") as mock_sleep:
                await client._request("GET", "/api/levels/SPX")
                mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_positive_jitter_calls_sleep(self):
        """When max_jitter_seconds > 0, asyncio.sleep is called with value in range."""
        client, _ = _make_client(max_jitter_seconds=5.0)
        mock_resp = _mock_response(200, {"ok": True})
        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            with patch("src.data.spotgamma_client.asyncio.sleep") as mock_sleep:
                with patch("src.data.spotgamma_client.random.uniform", return_value=2.5):
                    await client._request("GET", "/api/levels/SPX")
                    mock_sleep.assert_called_once_with(2.5)


# ---------------------------------------------------------------------------
# Tests: Session management
# ---------------------------------------------------------------------------


class TestSessionManagement:
    """Tests for session lifecycle."""

    @pytest.mark.asyncio
    async def test_close_closes_session(self):
        """close() closes the aiohttp session when we own it."""
        client, _ = _make_client()
        mock_session = AsyncMock()
        mock_session.closed = False
        client._session = mock_session
        client._owns_session = True

        await client.close()

        mock_session.close.assert_called_once()
        assert client._session is None

    @pytest.mark.asyncio
    async def test_close_noop_when_no_session(self):
        """close() is safe to call when no session exists."""
        client, _ = _make_client()
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_close_does_not_close_external_session(self):
        """close() does not close a session we don't own."""
        broker = _mock_auth_broker()
        mock_session = AsyncMock()
        mock_session.closed = False

        client = SpotGammaClient(
            auth_broker=broker,
            session=mock_session,
            max_jitter_seconds=0.0,
        )

        await client.close()

        # We don't own it, so close should NOT be called
        # _owns_session is False because we passed a session in
        mock_session.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_lazy_session_init(self):
        """Session is created on first request when none provided."""
        client, _ = _make_client()
        assert client._session is None

        with patch("aiohttp.ClientSession") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.closed = False
            mock_cls.return_value = mock_instance
            session = await client._get_session()
            assert session is mock_instance


# ---------------------------------------------------------------------------
# Tests: Exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptionHierarchy:
    """Tests that exception classes have the right inheritance."""

    def test_auth_error_is_spotgamma_error(self):
        """SpotGammaAuthError is a subclass of SpotGammaError."""
        assert issubclass(SpotGammaAuthError, SpotGammaError)

    def test_rate_limit_error_is_spotgamma_error(self):
        """SpotGammaRateLimitError is a subclass of SpotGammaError."""
        assert issubclass(SpotGammaRateLimitError, SpotGammaError)
