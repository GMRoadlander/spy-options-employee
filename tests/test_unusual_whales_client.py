"""Tests for UnusualWhalesClient -- all API calls are mocked.

Covers: REST authentication, rate limiting, flow data fetching, dark pool
fetching, flow summary computation, error handling, graceful degradation
without API key, missing/extra fields, and session management.
"""

import asyncio
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.data.unusual_whales_client import (
    UnusualWhalesAuthError,
    UnusualWhalesClient,
    UnusualWhalesRateLimitError,
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


def _make_flow_entry(
    ticker: str = "SPX",
    strike: float = 5000.0,
    expiry: str = "2025-03-21",
    put_call: str = "call",
    side: str = "ask",
    premium: float = 125000.0,
    volume: int = 500,
    open_interest: int = 2000,
    iv: float = 0.22,
    classification: str = "sweep",
    sentiment: str = "bullish",
    timestamp: str = "2025-01-15T14:30:00Z",
) -> dict:
    """Build a mock Unusual Whales flow entry."""
    return {
        "ticker": ticker,
        "strike_price": strike,
        "expires_date": expiry,
        "put_call": put_call,
        "side": side,
        "premium": premium,
        "volume": volume,
        "open_interest": open_interest,
        "implied_volatility": iv,
        "option_activity_type": classification,
        "sentiment": sentiment,
        "date": timestamp,
    }


def _make_dark_pool_entry(
    ticker: str = "SPX",
    price: float = 5050.25,
    size: int = 10000,
    notional: float = 50502500.0,
    exchange: str = "FADF",
    timestamp: str = "2025-01-15T14:30:00Z",
) -> dict:
    """Build a mock Unusual Whales dark pool entry."""
    return {
        "ticker": ticker,
        "price": price,
        "size": size,
        "notional": notional,
        "exchange": exchange,
        "date": timestamp,
    }


# ---------------------------------------------------------------------------
# Tests: _request method
# ---------------------------------------------------------------------------


class TestRequest:
    """Tests for the base _request method."""

    @pytest.fixture
    def client(self):
        return UnusualWhalesClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_successful_request(self, client):
        """Returns parsed JSON on 200 response."""
        expected = {"data": [{"ticker": "SPX"}]}
        mock_resp = _mock_response(200, expected)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            result = await client._request("/stock/SPX/option-contracts")

        assert result == expected

    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self, client):
        """HTTP 401 raises UnusualWhalesAuthError."""
        mock_resp = _mock_response(401)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(UnusualWhalesAuthError, match="401"):
                await client._request("/stock/SPX/option-contracts")

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, client):
        """HTTP 429 raises UnusualWhalesRateLimitError."""
        mock_resp = _mock_response(429)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(UnusualWhalesRateLimitError, match="429"):
                await client._request("/stock/SPX/option-contracts")

    @pytest.mark.asyncio
    async def test_timeout_raises(self, client):
        """Request timeout raises asyncio.TimeoutError."""
        mock_session = AsyncMock()

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=mock_cm)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(asyncio.TimeoutError):
                await client._request("/stock/SPX/option-contracts")

    @pytest.mark.asyncio
    async def test_500_raises_value_error(self, client):
        """HTTP 500 raises ValueError with status and body."""
        mock_resp = _mock_response(500, text="Internal Server Error")
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(ValueError, match="500"):
                await client._request("/stock/SPX/option-contracts")

    @pytest.mark.asyncio
    async def test_bearer_token_in_headers(self, client):
        """Authorization Bearer token is set in request headers."""
        expected = {"data": []}
        mock_resp = _mock_response(200, expected)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            await client._request("/stock/SPX/option-contracts", params={"limit": 10})

        call_args = mock_session.get.call_args
        headers = call_args[1].get("headers", {})
        assert headers["Authorization"] == "Bearer test_key"
        params = call_args[1].get("params", {})
        assert params["limit"] == 10


# ---------------------------------------------------------------------------
# Tests: get_flow
# ---------------------------------------------------------------------------


class TestGetFlow:
    """Tests for get_flow method."""

    @pytest.fixture
    def client(self):
        return UnusualWhalesClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_parses_flow_data(self, client):
        """Returns list of normalized flow dicts on success."""
        flow_entry = _make_flow_entry()
        response_data = {"data": [flow_entry]}

        with patch.object(client, "_request", return_value=response_data):
            results = await client.get_flow("SPX")

        assert len(results) == 1
        assert results[0]["ticker"] == "SPX"
        assert results[0]["strike"] == 5000.0
        assert results[0]["expiry"] == "2025-03-21"
        assert results[0]["type"] == "call"
        assert results[0]["premium"] == 125000.0
        assert results[0]["classification"] == "sweep"
        assert results[0]["sentiment"] == "bullish"

    @pytest.mark.asyncio
    async def test_respects_limit(self, client):
        """Results are trimmed to limit."""
        entries = [_make_flow_entry() for _ in range(5)]
        response_data = {"data": entries}

        with patch.object(client, "_request", return_value=response_data):
            results = await client.get_flow("SPX", limit=3)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_handles_missing_fields(self, client):
        """Missing fields in API response use defaults gracefully."""
        # Minimal entry with only a few fields
        minimal_entry = {"ticker": "SPX", "premium": 50000.0}
        response_data = {"data": [minimal_entry]}

        with patch.object(client, "_request", return_value=response_data):
            results = await client.get_flow("SPX")

        assert len(results) == 1
        assert results[0]["ticker"] == "SPX"
        assert results[0]["premium"] == 50000.0
        assert results[0]["strike"] == 0.0  # default
        assert results[0]["volume"] == 0  # default
        assert results[0]["classification"] == "standard"  # default

    @pytest.mark.asyncio
    async def test_handles_extra_fields(self, client):
        """Extra fields in API response are ignored gracefully."""
        entry = _make_flow_entry()
        entry["some_future_field"] = "unexpected_data"
        entry["another_new_field"] = 12345
        response_data = {"data": [entry]}

        with patch.object(client, "_request", return_value=response_data):
            results = await client.get_flow("SPX")

        assert len(results) == 1
        # Extra fields should not appear in normalized output
        assert "some_future_field" not in results[0]
        assert "another_new_field" not in results[0]


# ---------------------------------------------------------------------------
# Tests: get_dark_pool
# ---------------------------------------------------------------------------


class TestGetDarkPool:
    """Tests for get_dark_pool method."""

    @pytest.fixture
    def client(self):
        return UnusualWhalesClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_parses_dark_pool_data(self, client):
        """Returns list of normalized dark pool dicts on success."""
        dp_entry = _make_dark_pool_entry()
        response_data = {"data": [dp_entry]}

        with patch.object(client, "_request", return_value=response_data):
            results = await client.get_dark_pool("SPX")

        assert len(results) == 1
        assert results[0]["ticker"] == "SPX"
        assert results[0]["price"] == 5050.25
        assert results[0]["size"] == 10000
        assert results[0]["notional"] == 50502500.0
        assert results[0]["exchange"] == "FADF"

    @pytest.mark.asyncio
    async def test_computes_notional_if_missing(self, client):
        """Notional is computed from price * size when not in response."""
        entry = {"ticker": "SPX", "price": 100.0, "size": 500}
        response_data = {"data": [entry]}

        with patch.object(client, "_request", return_value=response_data):
            results = await client.get_dark_pool("SPX")

        assert len(results) == 1
        assert results[0]["notional"] == pytest.approx(50000.0)


# ---------------------------------------------------------------------------
# Tests: get_flow_summary
# ---------------------------------------------------------------------------


class TestGetFlowSummary:
    """Tests for get_flow_summary method."""

    @pytest.fixture
    def client(self):
        return UnusualWhalesClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_computes_summary(self, client):
        """Summary aggregates flow and dark pool data correctly."""
        flow_entries = [
            _make_flow_entry(put_call="call", premium=100000.0, classification="sweep", sentiment="bullish"),
            _make_flow_entry(put_call="call", premium=75000.0, classification="block", sentiment="bullish"),
            _make_flow_entry(put_call="put", premium=50000.0, classification="sweep", sentiment="bearish"),
            _make_flow_entry(put_call="put", premium=30000.0, classification="standard", sentiment="neutral"),
            _make_flow_entry(put_call="call", premium=200000.0, classification="golden_sweep", sentiment="bullish"),
        ]
        dark_pool_entries = [
            _make_dark_pool_entry(size=10000),
            _make_dark_pool_entry(size=5000),
        ]

        async def mock_get_flow(ticker, limit=500):
            return [
                {
                    "ticker": e["ticker"],
                    "strike": float(e["strike_price"]),
                    "expiry": e["expires_date"],
                    "type": e["put_call"].lower(),
                    "side": e["side"].lower(),
                    "premium": float(e["premium"]),
                    "volume": int(e["volume"]),
                    "open_interest": int(e["open_interest"]),
                    "iv": float(e["implied_volatility"]),
                    "classification": e["option_activity_type"].lower(),
                    "sentiment": e["sentiment"].lower(),
                    "timestamp": e["date"],
                }
                for e in flow_entries
            ]

        async def mock_get_dark_pool(ticker, limit=100):
            return [
                {
                    "ticker": e["ticker"],
                    "price": float(e["price"]),
                    "size": int(e["size"]),
                    "notional": float(e["notional"]),
                    "exchange": e["exchange"],
                    "timestamp": e["date"],
                }
                for e in dark_pool_entries
            ]

        with patch.object(client, "get_flow", side_effect=mock_get_flow):
            with patch.object(client, "get_dark_pool", side_effect=mock_get_dark_pool):
                summary = await client.get_flow_summary("SPX")

        assert summary["total_premium"] == pytest.approx(455000.0)
        assert summary["call_premium"] == pytest.approx(375000.0)
        assert summary["put_premium"] == pytest.approx(80000.0)
        assert summary["sweep_count"] == 2
        assert summary["block_count"] == 1
        assert summary["golden_sweep_count"] == 1
        # 3 bullish, 1 bearish -> net_sentiment = (3-1)/4 = 0.5
        assert summary["net_sentiment"] == pytest.approx(0.5)
        assert summary["dark_pool_volume"] == 15000

    @pytest.mark.asyncio
    async def test_all_neutral_sentiment(self, client):
        """Net sentiment is 0 when all entries are neutral."""
        flow_entries = [
            _make_flow_entry(sentiment="neutral"),
            _make_flow_entry(sentiment="neutral"),
        ]

        async def mock_get_flow(ticker, limit=500):
            return [
                {
                    "ticker": "SPX",
                    "strike": 5000.0,
                    "expiry": "2025-03-21",
                    "type": "call",
                    "side": "ask",
                    "premium": 100000.0,
                    "volume": 100,
                    "open_interest": 1000,
                    "iv": 0.22,
                    "classification": "standard",
                    "sentiment": "neutral",
                    "timestamp": "2025-01-15T14:30:00Z",
                }
                for _ in flow_entries
            ]

        async def mock_get_dark_pool(ticker, limit=100):
            return []

        with patch.object(client, "get_flow", side_effect=mock_get_flow):
            with patch.object(client, "get_dark_pool", side_effect=mock_get_dark_pool):
                summary = await client.get_flow_summary("SPX")

        assert summary["net_sentiment"] == 0.0


# ---------------------------------------------------------------------------
# Tests: Empty API key (graceful degradation)
# ---------------------------------------------------------------------------


class TestEmptyApiKey:
    """Tests for graceful degradation when API key is empty."""

    @pytest.fixture
    def client(self):
        return UnusualWhalesClient(api_key="")

    @pytest.mark.asyncio
    async def test_flow_returns_empty(self, client):
        """get_flow returns empty list without API key."""
        results = await client.get_flow("SPX")
        assert results == []

    @pytest.mark.asyncio
    async def test_dark_pool_returns_empty(self, client):
        """get_dark_pool returns empty list without API key."""
        results = await client.get_dark_pool("SPX")
        assert results == []

    @pytest.mark.asyncio
    async def test_flow_summary_returns_zeroed(self, client):
        """get_flow_summary returns zeroed dict without API key."""
        summary = await client.get_flow_summary("SPX")
        assert summary["total_premium"] == 0.0
        assert summary["sweep_count"] == 0
        assert summary["net_sentiment"] == 0.0
        assert summary["dark_pool_volume"] == 0


# ---------------------------------------------------------------------------
# Tests: Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """Tests for rate limit tracking and enforcement."""

    def test_rate_limit_status_initial(self):
        """Fresh client reports zero usage."""
        client = UnusualWhalesClient(api_key="test")
        status = client.rate_limit_status
        assert status["minute_used"] == 0
        assert status["minute_limit"] == 120

    def test_minute_rate_limit_exceeded(self):
        """UnusualWhalesRateLimitError raised when minute limit is hit."""
        client = UnusualWhalesClient(api_key="test", requests_per_minute=3)
        now = time.time()
        client._minute_requests = [now, now, now]

        with pytest.raises(UnusualWhalesRateLimitError, match="requests/minute"):
            client._check_rate_limit()

    def test_old_requests_cleaned(self):
        """Requests older than 60 seconds are removed from tracking."""
        client = UnusualWhalesClient(api_key="test", requests_per_minute=5)
        old_time = time.time() - 120  # 2 minutes ago
        client._minute_requests = [old_time, old_time, old_time]

        client._check_rate_limit()
        assert len(client._minute_requests) == 0

    def test_record_request_increments(self):
        """_record_request adds a timestamp to minute tracking."""
        client = UnusualWhalesClient(api_key="test")
        client._record_request()
        assert len(client._minute_requests) == 1


# ---------------------------------------------------------------------------
# Tests: Session management
# ---------------------------------------------------------------------------


class TestSessionManagement:
    """Tests for session lifecycle."""

    @pytest.mark.asyncio
    async def test_close_closes_session(self):
        """close() closes the aiohttp session."""
        client = UnusualWhalesClient(api_key="test")
        mock_session = AsyncMock()
        mock_session.closed = False
        client._session = mock_session

        await client.close()

        mock_session.close.assert_called_once()
        assert client._session is None

    @pytest.mark.asyncio
    async def test_close_noop_when_no_session(self):
        """close() is safe to call when no session exists."""
        client = UnusualWhalesClient(api_key="test")
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_lazy_session_init(self):
        """Session is created on first request."""
        client = UnusualWhalesClient(api_key="test")
        assert client._session is None

        with patch("aiohttp.ClientSession") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.closed = False
            mock_cls.return_value = mock_instance
            session = await client._get_session()
            assert session is mock_instance
