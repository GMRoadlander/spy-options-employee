"""Tests for ORATSClient -- all HTTP calls are mocked.

Covers: authentication, rate limiting, field mapping, error handling,
date range fetching, IV rank, and session management.
"""

import pytest
import time
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.data import OptionContract, OptionsChain
from src.data.orats_client import ORATSClient, RateLimitError


# ---------------------------------------------------------------------------
# Helpers: build mock ORATS API responses
# ---------------------------------------------------------------------------


def _make_orats_row(
    trade_date: str = "2024-01-15",
    expir_date: str = "2024-02-16",
    strike: float = 480.0,
    stk_px: float = 475.50,
    call_bid: float = 8.50,
    call_ask: float = 9.00,
    call_volume: int = 1200,
    call_oi: int = 15000,
    call_iv: float = 0.18,
    call_delta: float = 0.55,
    call_gamma: float = 0.012,
    call_theta: float = -0.08,
    call_vega: float = 0.35,
    call_rho: float = 0.02,
    put_bid: float = 12.00,
    put_ask: float = 12.50,
    put_volume: int = 900,
    put_oi: int = 12000,
    put_iv: float = 0.20,
    put_delta: float = -0.45,
    put_gamma: float = 0.012,
    put_theta: float = -0.07,
    put_vega: float = 0.34,
    put_rho: float = -0.02,
) -> dict:
    """Build a mock ORATS data row with both call and put data."""
    return {
        "tradeDate": trade_date,
        "expirDate": expir_date,
        "strike": strike,
        "stkPx": stk_px,
        "callBidPrice": call_bid,
        "callAskPrice": call_ask,
        "callVolume": call_volume,
        "callOpenInterest": call_oi,
        "callIv": call_iv,
        "callDelta": call_delta,
        "callGamma": call_gamma,
        "callTheta": call_theta,
        "callVega": call_vega,
        "callRho": call_rho,
        "putBidPrice": put_bid,
        "putAskPrice": put_ask,
        "putVolume": put_volume,
        "putOpenInterest": put_oi,
        "putIv": put_iv,
        "putDelta": put_delta,
        "putGamma": put_gamma,
        "putTheta": put_theta,
        "putVega": put_vega,
        "putRho": put_rho,
    }


def _mock_response(status: int = 200, json_data: dict | None = None, text: str = "") -> AsyncMock:
    """Create a mock aiohttp response."""
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data or {})
    resp.text = AsyncMock(return_value=text)
    # Support async context manager
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# Tests: Row transformation
# ---------------------------------------------------------------------------


class TestTransformRow:
    """Tests for _transform_row static method."""

    def test_basic_call_and_put(self):
        """A standard row produces one call and one put contract."""
        row = _make_orats_row()
        contracts = ORATSClient._transform_row("SPY", row)
        assert len(contracts) == 2
        call = contracts[0]
        put = contracts[1]
        assert call.option_type == "call"
        assert put.option_type == "put"

    def test_call_fields_mapped(self):
        """Call contract fields match the ORATS row data."""
        row = _make_orats_row(
            expir_date="2024-02-16",
            strike=480.0,
            call_bid=8.50,
            call_ask=9.00,
            call_volume=1200,
            call_oi=15000,
            call_iv=0.18,
            call_delta=0.55,
            call_gamma=0.012,
            call_theta=-0.08,
            call_vega=0.35,
            call_rho=0.02,
        )
        contracts = ORATSClient._transform_row("SPY", row)
        call = contracts[0]

        assert call.ticker == "SPY"
        assert call.expiry == date(2024, 2, 16)
        assert call.strike == 480.0
        assert call.bid == pytest.approx(8.50)
        assert call.ask == pytest.approx(9.00)
        assert call.last == pytest.approx(8.75)  # mid
        assert call.volume == 1200
        assert call.open_interest == 15000
        assert call.iv == pytest.approx(0.18)
        assert call.delta == pytest.approx(0.55)
        assert call.gamma == pytest.approx(0.012)
        assert call.theta == pytest.approx(-0.08)
        assert call.vega == pytest.approx(0.35)
        assert call.rho == pytest.approx(0.02)

    def test_put_fields_mapped(self):
        """Put contract fields match the ORATS row data."""
        row = _make_orats_row(
            put_bid=12.00,
            put_ask=12.50,
            put_volume=900,
            put_oi=12000,
            put_iv=0.20,
            put_delta=-0.45,
        )
        contracts = ORATSClient._transform_row("SPY", row)
        put = contracts[1]

        assert put.option_type == "put"
        assert put.bid == pytest.approx(12.00)
        assert put.ask == pytest.approx(12.50)
        assert put.volume == 900
        assert put.open_interest == 12000
        assert put.iv == pytest.approx(0.20)
        assert put.delta == pytest.approx(-0.45)

    def test_missing_expiry_returns_empty(self):
        """Row with no expirDate produces no contracts."""
        row = _make_orats_row()
        row["expirDate"] = ""
        contracts = ORATSClient._transform_row("SPY", row)
        assert contracts == []

    def test_zero_strike_returns_empty(self):
        """Row with zero strike produces no contracts."""
        row = _make_orats_row(strike=0.0)
        contracts = ORATSClient._transform_row("SPY", row)
        assert contracts == []

    def test_call_only_when_put_has_no_data(self):
        """Only a call contract is produced when put data is all zeros."""
        row = _make_orats_row(
            put_bid=0.0,
            put_ask=0.0,
            put_volume=0,
            put_oi=0,
        )
        contracts = ORATSClient._transform_row("SPY", row)
        assert len(contracts) == 1
        assert contracts[0].option_type == "call"

    def test_ticker_passed_through(self):
        """Ticker string from caller is used, not from row."""
        row = _make_orats_row()
        contracts = ORATSClient._transform_row("SPX", row)
        for c in contracts:
            assert c.ticker == "SPX"


# ---------------------------------------------------------------------------
# Tests: API requests
# ---------------------------------------------------------------------------


class TestGetHistoricalChain:
    """Tests for get_historical_chain method."""

    @pytest.fixture
    def client(self):
        return ORATSClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_successful_fetch(self, client):
        """Returns OptionsChain with correct contracts on success."""
        row = _make_orats_row()
        mock_resp = _mock_response(200, {"data": [row]})

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            chain = await client.get_historical_chain("SPY", date(2024, 1, 15))

        assert chain is not None
        assert chain.ticker == "SPY"
        assert chain.source == "orats"
        assert chain.spot_price == pytest.approx(475.50)
        assert len(chain.contracts) == 2

    @pytest.mark.asyncio
    async def test_empty_data_returns_none(self, client):
        """Returns None when API returns no data rows."""
        mock_resp = _mock_response(200, {"data": []})
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            chain = await client.get_historical_chain("SPY", date(2024, 1, 15))

        assert chain is None

    @pytest.mark.asyncio
    async def test_api_error_returns_none(self, client):
        """Returns None on non-200 response."""
        mock_resp = _mock_response(500, text="Internal Server Error")
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            chain = await client.get_historical_chain("SPY", date(2024, 1, 15))

        assert chain is None

    @pytest.mark.asyncio
    async def test_ticker_uppercased(self, client):
        """Ticker is always uppercased in the result."""
        row = _make_orats_row()
        mock_resp = _mock_response(200, {"data": [row]})
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            chain = await client.get_historical_chain("spy", date(2024, 1, 15))

        assert chain.ticker == "SPY"


class TestGetHistoricalRange:
    """Tests for get_historical_range method."""

    @pytest.fixture
    def client(self):
        return ORATSClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_multiple_dates(self, client):
        """Returns chains grouped by trade date."""
        row1 = _make_orats_row(trade_date="2024-01-15", stk_px=475.0)
        row2 = _make_orats_row(trade_date="2024-01-16", stk_px=478.0)
        mock_resp = _mock_response(200, {"data": [row1, row2]})
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            chains = await client.get_historical_range(
                "SPY", date(2024, 1, 15), date(2024, 1, 16)
            )

        assert len(chains) == 2
        assert chains[0].spot_price == pytest.approx(475.0)
        assert chains[1].spot_price == pytest.approx(478.0)

    @pytest.mark.asyncio
    async def test_empty_range(self, client):
        """Returns empty list when no data for the range."""
        mock_resp = _mock_response(200, {"data": []})
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            chains = await client.get_historical_range(
                "SPY", date(2024, 1, 15), date(2024, 1, 16)
            )

        assert chains == []


class TestGetIvRank:
    """Tests for get_iv_rank method."""

    @pytest.fixture
    def client(self):
        return ORATSClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_returns_iv_data(self, client):
        """Returns IV rank data from the latest daily row."""
        daily_row = {
            "ivRank": 0.65,
            "ivPct": 0.72,
            "orIvFcst20d": 0.18,
            "orHv20d": 0.15,
        }
        mock_resp = _mock_response(200, {"data": [daily_row]})
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            result = await client.get_iv_rank("SPY")

        assert result is not None
        assert result["iv_rank"] == pytest.approx(0.65)
        assert result["iv_percentile"] == pytest.approx(0.72)
        assert result["current_iv"] == pytest.approx(0.18)
        assert result["hv_20d"] == pytest.approx(0.15)

    @pytest.mark.asyncio
    async def test_no_data_returns_none(self, client):
        """Returns None when no daily data exists."""
        mock_resp = _mock_response(200, {"data": []})
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            result = await client.get_iv_rank("SPY")

        assert result is None


# ---------------------------------------------------------------------------
# Tests: Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """Tests for rate limit tracking and enforcement."""

    def test_rate_limit_status_initial(self):
        """Fresh client reports zero usage."""
        client = ORATSClient(api_key="test")
        status = client.rate_limit_status
        assert status["minute_used"] == 0
        assert status["month_used"] == 0

    def test_minute_rate_limit_exceeded(self):
        """RateLimitError raised when minute limit is hit."""
        client = ORATSClient(api_key="test", requests_per_minute=3)
        now = time.time()
        client._minute_requests = [now, now, now]

        with pytest.raises(RateLimitError, match="requests/minute"):
            client._check_rate_limit()

    def test_month_rate_limit_exceeded(self):
        """RateLimitError raised when monthly limit is hit."""
        client = ORATSClient(api_key="test", requests_per_month=5)
        client._month_request_count = 5

        with pytest.raises(RateLimitError, match="requests/month"):
            client._check_rate_limit()

    def test_old_minute_requests_cleaned(self):
        """Requests older than 60 seconds are removed from tracking."""
        client = ORATSClient(api_key="test", requests_per_minute=5)
        old_time = time.time() - 120  # 2 minutes ago
        client._minute_requests = [old_time, old_time, old_time]

        # Should not raise -- old requests are cleaned up
        client._check_rate_limit()
        assert len(client._minute_requests) == 0

    def test_record_request_increments(self):
        """_record_request updates both minute and month counters."""
        client = ORATSClient(api_key="test")
        client._record_request()
        assert len(client._minute_requests) == 1
        assert client._month_request_count == 1


# ---------------------------------------------------------------------------
# Tests: Session management
# ---------------------------------------------------------------------------


class TestSessionManagement:
    """Tests for session lifecycle."""

    @pytest.mark.asyncio
    async def test_close_closes_owned_session(self):
        """close() closes a session the client owns."""
        client = ORATSClient(api_key="test")
        mock_session = AsyncMock()
        mock_session.closed = False
        client._session = mock_session
        client._owns_session = True

        await client.close()

        mock_session.close.assert_called_once()
        assert client._session is None

    @pytest.mark.asyncio
    async def test_close_does_not_close_external_session(self):
        """close() does not close a session passed from outside."""
        mock_session = AsyncMock()
        mock_session.closed = False
        client = ORATSClient(api_key="test", session=mock_session)

        await client.close()

        mock_session.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self):
        """HTTP 429 response raises RateLimitError."""
        client = ORATSClient(api_key="test")
        mock_resp = _mock_response(429)
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            with pytest.raises(RateLimitError, match="429"):
                await client._request("/test")


class TestGetTickers:
    """Tests for get_tickers method."""

    @pytest.fixture
    def client(self):
        return ORATSClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_returns_tickers(self, client):
        """Returns list of ticker strings from API."""
        mock_resp = _mock_response(200, {"data": [{"ticker": "SPY"}, {"ticker": "SPX"}, {"ticker": "QQQ"}]})
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            tickers = await client.get_tickers()

        assert tickers == ["SPY", "SPX", "QQQ"]

    @pytest.mark.asyncio
    async def test_error_returns_empty(self, client):
        """Returns empty list on API error."""
        mock_resp = _mock_response(500, text="error")
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch.object(client, "_get_session", return_value=mock_session):
            tickers = await client.get_tickers()

        assert tickers == []
