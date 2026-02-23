"""Tests for PolygonClient -- all HTTP calls are mocked.

Covers: authentication, rate limiting, options chain fetching, trade fetching,
news fetching, error handling, graceful degradation without API key,
and session management.
"""

import asyncio
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.data.polygon_client import (
    PolygonAuthError,
    PolygonClient,
    PolygonRateLimitError,
)


# ---------------------------------------------------------------------------
# Helpers: build mock responses
# ---------------------------------------------------------------------------


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


def _make_option_snapshot(
    ticker: str = "O:SPY251219C00600000",
    iv: float = 0.25,
    delta: float = 0.55,
    gamma: float = 0.012,
    theta: float = -0.08,
    vega: float = 0.35,
    volume: int = 1200,
    open_interest: int = 15000,
) -> dict:
    """Build a mock Polygon option snapshot result."""
    return {
        "break_even_price": 605.50,
        "details": {
            "contract_type": "call",
            "exercise_style": "american",
            "expiration_date": "2025-12-19",
            "shares_per_contract": 100,
            "strike_price": 600.0,
            "ticker": ticker,
        },
        "greeks": {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
        },
        "implied_volatility": iv,
        "day": {
            "volume": volume,
            "open_interest": open_interest,
        },
        "last_quote": {
            "bid": 8.50,
            "ask": 9.00,
            "bid_size": 10,
            "ask_size": 15,
        },
        "last_trade": {
            "price": 8.75,
            "size": 5,
        },
        "underlying_asset": {
            "ticker": "SPY",
            "price": 595.50,
        },
    }


def _make_trade(
    price: float = 8.75,
    size: int = 10,
    exchange: int = 316,
    conditions: list | None = None,
    sip_timestamp: int = 1700000000000000000,
) -> dict:
    """Build a mock Polygon trade result."""
    return {
        "price": price,
        "size": size,
        "exchange": exchange,
        "conditions": conditions or [209],
        "sip_timestamp": sip_timestamp,
    }


def _make_news_article(
    title: str = "SPX hits record high",
    published_utc: str = "2024-01-15T14:30:00Z",
    source: str = "Reuters",
    article_url: str = "https://example.com/article",
) -> dict:
    """Build a mock Polygon news article result."""
    return {
        "title": title,
        "published_utc": published_utc,
        "author": "Test Author",
        "article_url": article_url,
        "tickers": ["SPX"],
        "publisher": {"name": source},
    }


# ---------------------------------------------------------------------------
# Tests: _request method
# ---------------------------------------------------------------------------


class TestRequest:
    """Tests for the base _request method."""

    @pytest.fixture
    def client(self):
        return PolygonClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_successful_request(self, client):
        """Returns parsed JSON on 200 response."""
        expected = {"results": [{"ticker": "SPY"}]}
        mock_resp = _mock_response(200, expected)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            result = await client._request("/v3/test")

        assert result == expected

    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self, client):
        """HTTP 401 raises PolygonAuthError."""
        mock_resp = _mock_response(401)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(PolygonAuthError, match="401"):
                await client._request("/v3/test")

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, client):
        """HTTP 429 raises PolygonRateLimitError."""
        mock_resp = _mock_response(429)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(PolygonRateLimitError, match="429"):
                await client._request("/v3/test")

    @pytest.mark.asyncio
    async def test_timeout_raises(self, client):
        """Request timeout raises asyncio.TimeoutError."""
        mock_session = AsyncMock()

        # Simulate timeout by making the context manager raise
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=mock_cm)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(asyncio.TimeoutError):
                await client._request("/v3/test")

    @pytest.mark.asyncio
    async def test_500_raises_value_error(self, client):
        """HTTP 500 raises ValueError with status and body."""
        mock_resp = _mock_response(500, text="Internal Server Error")
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(ValueError, match="500"):
                await client._request("/v3/test")

    @pytest.mark.asyncio
    async def test_apikey_in_params(self, client):
        """API key is added to query parameters."""
        expected = {"results": []}
        mock_resp = _mock_response(200, expected)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            await client._request("/v3/test", params={"foo": "bar"})

        # Verify the call included apiKey
        call_args = mock_session.get.call_args
        params = call_args[1].get("params") or call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params", {})
        assert params["apiKey"] == "test_key"
        assert params["foo"] == "bar"


# ---------------------------------------------------------------------------
# Tests: get_options_chain
# ---------------------------------------------------------------------------


class TestGetOptionsChain:
    """Tests for get_options_chain method."""

    @pytest.fixture
    def client(self):
        return PolygonClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_parses_snapshots(self, client):
        """Returns list of option snapshots on success."""
        snapshot = _make_option_snapshot()
        response_data = {"results": [snapshot], "status": "OK"}
        mock_resp = _mock_response(200, response_data)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            results = await client.get_options_chain("SPY")

        assert len(results) == 1
        assert results[0]["implied_volatility"] == 0.25
        assert results[0]["greeks"]["delta"] == 0.55

    @pytest.mark.asyncio
    async def test_handles_pagination(self, client):
        """Follows next_url for pagination."""
        snapshot1 = _make_option_snapshot(ticker="O:SPY251219C00600000")
        snapshot2 = _make_option_snapshot(ticker="O:SPY251219C00610000")

        # First page with next_url
        page1 = {"results": [snapshot1], "next_url": "https://api.polygon.io/v3/snapshot/options/SPY?cursor=abc123"}
        # Second page without next_url
        page2 = {"results": [snapshot2]}

        mock_resp1 = _mock_response(200, page1)
        mock_resp2 = _mock_response(200, page2)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(side_effect=[mock_resp1, mock_resp2])

        with patch.object(client, "_get_session", return_value=mock_session):
            results = await client.get_options_chain("SPY")

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_with_expiration_date(self, client):
        """Passes expiration_date filter to API."""
        response_data = {"results": [], "status": "OK"}
        mock_resp = _mock_response(200, response_data)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            results = await client.get_options_chain(
                "SPY", expiration_date="2025-12-19"
            )

        assert results == []
        # Verify expiration_date was passed
        call_args = mock_session.get.call_args
        params = call_args[1].get("params", {})
        assert params.get("expiration_date") == "2025-12-19"


# ---------------------------------------------------------------------------
# Tests: get_option_trades
# ---------------------------------------------------------------------------


class TestGetOptionTrades:
    """Tests for get_option_trades method."""

    @pytest.fixture
    def client(self):
        return PolygonClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_returns_trade_list(self, client):
        """Returns list of trade dicts on success."""
        trade = _make_trade()
        response_data = {"results": [trade], "status": "OK"}
        mock_resp = _mock_response(200, response_data)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            results = await client.get_option_trades(
                "O:SPY251219C00600000", "2024-01-15"
            )

        assert len(results) == 1
        assert results[0]["price"] == 8.75
        assert results[0]["size"] == 10

    @pytest.mark.asyncio
    async def test_error_returns_empty(self, client):
        """Returns empty list on API error."""
        mock_resp = _mock_response(500, text="Server Error")
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            results = await client.get_option_trades(
                "O:SPY251219C00600000", "2024-01-15"
            )

        assert results == []


# ---------------------------------------------------------------------------
# Tests: get_option_aggregates
# ---------------------------------------------------------------------------


class TestGetOptionAggregates:
    """Tests for get_option_aggregates method."""

    @pytest.fixture
    def client(self):
        return PolygonClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_returns_bars(self, client):
        """Returns list of OHLCV bars on success."""
        bar = {
            "o": 8.50, "h": 9.25, "l": 8.30, "c": 9.00,
            "v": 1500, "t": 1700000000000,
        }
        response_data = {"results": [bar], "status": "OK"}
        mock_resp = _mock_response(200, response_data)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            results = await client.get_option_aggregates(
                "O:SPY251219C00600000",
                timespan="day",
                from_date="2024-01-01",
                to_date="2024-01-31",
            )

        assert len(results) == 1
        assert results[0]["o"] == 8.50
        assert results[0]["c"] == 9.00


# ---------------------------------------------------------------------------
# Tests: get_news
# ---------------------------------------------------------------------------


class TestGetNews:
    """Tests for get_news method."""

    @pytest.fixture
    def client(self):
        return PolygonClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_returns_articles(self, client):
        """Returns list of news articles in expected format."""
        article = _make_news_article()
        response_data = {"results": [article], "status": "OK"}
        mock_resp = _mock_response(200, response_data)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            results = await client.get_news("SPX")

        assert len(results) == 1
        assert results[0]["title"] == "SPX hits record high"
        assert results[0]["published_utc"] == "2024-01-15T14:30:00Z"
        assert results[0]["publisher"]["name"] == "Reuters"

    @pytest.mark.asyncio
    async def test_default_ticker(self, client):
        """Uses SPX as default ticker."""
        response_data = {"results": [], "status": "OK"}
        mock_resp = _mock_response(200, response_data)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            results = await client.get_news()

        assert results == []


# ---------------------------------------------------------------------------
# Tests: Empty API key (graceful degradation)
# ---------------------------------------------------------------------------


class TestEmptyApiKey:
    """Tests for graceful degradation when API key is empty."""

    @pytest.fixture
    def client(self):
        return PolygonClient(api_key="")

    @pytest.mark.asyncio
    async def test_options_chain_returns_empty(self, client):
        """get_options_chain returns empty list without API key."""
        results = await client.get_options_chain("SPY")
        assert results == []

    @pytest.mark.asyncio
    async def test_trades_returns_empty(self, client):
        """get_option_trades returns empty list without API key."""
        results = await client.get_option_trades(
            "O:SPY251219C00600000", "2024-01-15"
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_aggregates_returns_empty(self, client):
        """get_option_aggregates returns empty list without API key."""
        results = await client.get_option_aggregates(
            "O:SPY251219C00600000"
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_news_returns_empty(self, client):
        """get_news returns empty list without API key."""
        results = await client.get_news()
        assert results == []


# ---------------------------------------------------------------------------
# Tests: Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """Tests for rate limit tracking and enforcement."""

    def test_rate_limit_status_initial(self):
        """Fresh client reports zero usage."""
        client = PolygonClient(api_key="test")
        status = client.rate_limit_status
        assert status["minute_used"] == 0
        assert status["minute_limit"] == 5

    def test_minute_rate_limit_exceeded(self):
        """PolygonRateLimitError raised when minute limit is hit."""
        client = PolygonClient(api_key="test", requests_per_minute=3)
        now = time.time()
        client._minute_requests = [now, now, now]

        with pytest.raises(PolygonRateLimitError, match="requests/minute"):
            client._check_rate_limit()

    def test_old_requests_cleaned(self):
        """Requests older than 60 seconds are removed from tracking."""
        client = PolygonClient(api_key="test", requests_per_minute=5)
        old_time = time.time() - 120  # 2 minutes ago
        client._minute_requests = [old_time, old_time, old_time]

        # Should not raise -- old requests are cleaned up
        client._check_rate_limit()
        assert len(client._minute_requests) == 0

    def test_record_request_increments(self):
        """_record_request adds a timestamp to minute tracking."""
        client = PolygonClient(api_key="test")
        client._record_request()
        assert len(client._minute_requests) == 1

    def test_configurable_rate_limit(self):
        """Rate limit can be configured via constructor."""
        client = PolygonClient(api_key="test", requests_per_minute=100)
        assert client._requests_per_minute == 100
        assert client.rate_limit_status["minute_limit"] == 100


# ---------------------------------------------------------------------------
# Tests: Session management
# ---------------------------------------------------------------------------


class TestSessionManagement:
    """Tests for session lifecycle."""

    @pytest.mark.asyncio
    async def test_close_closes_session(self):
        """close() closes the aiohttp session."""
        client = PolygonClient(api_key="test")
        mock_session = AsyncMock()
        mock_session.closed = False
        client._session = mock_session

        await client.close()

        mock_session.close.assert_called_once()
        assert client._session is None

    @pytest.mark.asyncio
    async def test_close_noop_when_no_session(self):
        """close() is safe to call when no session exists."""
        client = PolygonClient(api_key="test")
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_lazy_session_init(self):
        """Session is created on first request."""
        client = PolygonClient(api_key="test")
        assert client._session is None

        with patch("aiohttp.ClientSession") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.closed = False
            mock_cls.return_value = mock_instance
            session = await client._get_session()
            assert session is mock_instance
