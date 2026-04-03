"""Tests for TastytradeClient field mapping and error handling.

All external SDK calls are mocked — no real API connections.
"""

import pytest

pytest.importorskip("tastytrade", reason="tastytrade SDK not installed")

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from src.data import OptionContract, OptionsChain
from src.data.tastytrade_client import TastytradeClient, _dec


# ---------------------------------------------------------------------------
# Helpers: build mock SDK objects
# ---------------------------------------------------------------------------


def _mock_option(
    symbol: str = "SPY   260321C00600000",
    streamer_symbol: str = ".SPY260321C600",
    strike: float = 600.0,
    option_type: str = "C",
    expiration_date: date | None = None,
) -> MagicMock:
    """Create a mock tastytrade Option instrument object."""
    opt = MagicMock()
    opt.symbol = symbol
    opt.streamer_symbol = streamer_symbol
    opt.strike_price = Decimal(str(strike))
    opt.option_type = MagicMock()
    opt.option_type.value = option_type
    opt.expiration_date = expiration_date or (date.today() + timedelta(days=30))
    return opt


def _mock_market_data(
    symbol: str = "SPY   260321C00600000",
    bid: float = 5.0,
    ask: float = 5.50,
    last: float = 5.25,
    volume: int = 1234,
    open_interest: int = 5000,
) -> MagicMock:
    """Create a mock MarketData response object."""
    md = MagicMock()
    md.symbol = symbol
    md.bid = Decimal(str(bid))
    md.ask = Decimal(str(ask))
    md.last = Decimal(str(last))
    md.volume = Decimal(str(volume))
    md.open_interest = Decimal(str(open_interest))
    md.mark = Decimal(str((bid + ask) / 2))
    return md


def _mock_greek(
    event_symbol: str = ".SPY260321C600",
    delta: float = 0.55,
    gamma: float = 0.03,
    theta: float = -0.05,
    vega: float = 0.12,
    rho: float = 0.01,
    volatility: float = 0.20,
) -> MagicMock:
    """Create a mock Greeks event object."""
    g = MagicMock()
    g.event_symbol = event_symbol
    g.delta = Decimal(str(delta))
    g.gamma = Decimal(str(gamma))
    g.theta = Decimal(str(theta))
    g.vega = Decimal(str(vega))
    g.rho = Decimal(str(rho))
    g.volatility = Decimal(str(volatility))
    return g


def _mock_quote(
    event_symbol: str = ".SPY260321C600",
    bid_price: float = 5.10,
    ask_price: float = 5.40,
) -> MagicMock:
    """Create a mock Quote event object."""
    q = MagicMock()
    q.event_symbol = event_symbol
    q.bid_price = Decimal(str(bid_price))
    q.ask_price = Decimal(str(ask_price))
    return q


# ---------------------------------------------------------------------------
# Tests: _dec helper
# ---------------------------------------------------------------------------


class TestDecHelper:
    """Tests for the _dec() Decimal-to-float converter."""

    def test_converts_decimal(self):
        assert _dec(Decimal("1.5")) == 1.5

    def test_returns_default_for_none(self):
        assert _dec(None) == 0.0

    def test_custom_default(self):
        assert _dec(None, default=-1.0) == -1.0

    def test_zero_decimal(self):
        assert _dec(Decimal("0")) == 0.0


# ---------------------------------------------------------------------------
# Tests: Field mapping
# ---------------------------------------------------------------------------


class TestFieldMapping:
    """Tests that SDK objects are correctly mapped to OptionContract."""

    @pytest.fixture
    def client(self):
        return TastytradeClient(
            client_secret="test_secret",
            refresh_token="test_token",
        )

    @pytest.mark.asyncio
    async def test_basic_mapping_with_all_data(self, client):
        """Full mapping with REST market data, streamer Greeks, and streamer Quotes."""
        expiry = date.today() + timedelta(days=30)

        call_opt = _mock_option(
            symbol="SPY   260321C00600000",
            streamer_symbol=".SPY260321C600",
            strike=600.0,
            option_type="C",
            expiration_date=expiry,
        )
        put_opt = _mock_option(
            symbol="SPY   260321P00600000",
            streamer_symbol=".SPY260321P600",
            strike=600.0,
            option_type="P",
            expiration_date=expiry,
        )

        call_md = _mock_market_data(symbol="SPY   260321C00600000", bid=5.0, ask=5.5, last=5.25, volume=1000, open_interest=5000)
        put_md = _mock_market_data(symbol="SPY   260321P00600000", bid=4.0, ask=4.5, last=4.25, volume=800, open_interest=3000)

        call_greek = _mock_greek(event_symbol=".SPY260321C600", delta=0.55, gamma=0.03, theta=-0.05, vega=0.12, rho=0.01, volatility=0.20)
        put_greek = _mock_greek(event_symbol=".SPY260321P600", delta=-0.45, gamma=0.03, theta=-0.04, vega=0.11, rho=-0.01, volatility=0.22)

        call_quote = _mock_quote(event_symbol=".SPY260321C600", bid_price=5.10, ask_price=5.40)
        put_quote = _mock_quote(event_symbol=".SPY260321P600", bid_price=4.10, ask_price=4.40)

        chain_map = {expiry: [call_opt, put_opt]}

        # Mock all SDK calls
        mock_session = MagicMock()

        # Mock the streamer as an async context manager with async iterators
        async def _make_greeks_iter():
            yield call_greek
            yield put_greek

        async def _make_quotes_iter():
            yield call_quote
            yield put_quote

        mock_streamer = AsyncMock()
        mock_streamer.__aenter__ = AsyncMock(return_value=mock_streamer)
        mock_streamer.__aexit__ = AsyncMock(return_value=False)
        mock_streamer.subscribe = AsyncMock()
        mock_streamer.listen = MagicMock()

        listen_call_count = 0

        def listen_side_effect(event_type):
            nonlocal listen_call_count
            listen_call_count += 1
            if listen_call_count == 1:
                return _make_greeks_iter()
            else:
                return _make_quotes_iter()

        mock_streamer.listen.side_effect = listen_side_effect

        with (
            patch.object(client, "_get_session", return_value=mock_session),
            patch("src.data.tastytrade_client.get_option_chain", new_callable=AsyncMock, return_value=chain_map) as mock_chain,
            patch("src.data.tastytrade_client.get_market_data_by_type", new_callable=AsyncMock, return_value=[call_md, put_md]) as mock_md,
            patch("src.data.tastytrade_client.DXLinkStreamer", return_value=mock_streamer),
        ):
            result = await client.fetch_chain("SPY")

        assert result is not None
        assert result.ticker == "SPY"
        assert result.source == "tastytrade"
        assert len(result.contracts) == 2

        # Check call contract
        call = result.contracts[0]
        assert call.ticker == "SPY"
        assert call.expiry == expiry
        assert call.strike == 600.0
        assert call.option_type == "call"
        assert call.bid == pytest.approx(5.10)  # from streamer quote
        assert call.ask == pytest.approx(5.40)  # from streamer quote
        assert call.last == pytest.approx(5.25)
        assert call.volume == 1000
        assert call.open_interest == 5000
        assert call.iv == pytest.approx(0.20)
        assert call.delta == pytest.approx(0.55)
        assert call.gamma == pytest.approx(0.03)
        assert call.theta == pytest.approx(-0.05)
        assert call.vega == pytest.approx(0.12)
        assert call.rho == pytest.approx(0.01)

        # Check put contract
        put = result.contracts[1]
        assert put.option_type == "put"
        assert put.delta == pytest.approx(-0.45)
        assert put.iv == pytest.approx(0.22)

    @pytest.mark.asyncio
    async def test_mapping_without_greeks(self, client):
        """When streamer fails, contracts have zero Greeks but valid market data."""
        expiry = date.today() + timedelta(days=30)
        opt = _mock_option(expiration_date=expiry)
        md = _mock_market_data()

        chain_map = {expiry: [opt]}
        mock_session = MagicMock()

        # Streamer raises an exception
        mock_streamer = AsyncMock()
        mock_streamer.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
        mock_streamer.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(client, "_get_session", return_value=mock_session),
            patch("src.data.tastytrade_client.get_option_chain", new_callable=AsyncMock, return_value=chain_map),
            patch("src.data.tastytrade_client.get_market_data_by_type", new_callable=AsyncMock, return_value=[md]),
            patch("src.data.tastytrade_client.DXLinkStreamer", return_value=mock_streamer),
        ):
            result = await client.fetch_chain("SPY")

        assert result is not None
        c = result.contracts[0]
        # Market data from REST is still present
        assert c.bid == pytest.approx(5.0)
        assert c.ask == pytest.approx(5.50)
        assert c.last == pytest.approx(5.25)
        assert c.volume == 1234
        assert c.open_interest == 5000
        # Greeks are zero (streamer failed)
        assert c.delta == 0.0
        assert c.gamma == 0.0
        assert c.iv == 0.0

    @pytest.mark.asyncio
    async def test_put_option_type_mapping(self, client):
        """Tastytrade 'P' maps to our 'put'."""
        expiry = date.today() + timedelta(days=30)
        opt = _mock_option(option_type="P", expiration_date=expiry)
        md = _mock_market_data(symbol=opt.symbol)

        chain_map = {expiry: [opt]}
        mock_session = MagicMock()
        mock_streamer = AsyncMock()
        mock_streamer.__aenter__ = AsyncMock(side_effect=Exception("skip"))
        mock_streamer.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(client, "_get_session", return_value=mock_session),
            patch("src.data.tastytrade_client.get_option_chain", new_callable=AsyncMock, return_value=chain_map),
            patch("src.data.tastytrade_client.get_market_data_by_type", new_callable=AsyncMock, return_value=[md]),
            patch("src.data.tastytrade_client.DXLinkStreamer", return_value=mock_streamer),
        ):
            result = await client.fetch_chain("SPY")

        assert result.contracts[0].option_type == "put"


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    @pytest.fixture
    def client(self):
        return TastytradeClient(
            client_secret="test_secret",
            refresh_token="test_token",
        )

    @pytest.mark.asyncio
    async def test_empty_chain(self, client):
        """Returns None when get_option_chain returns empty dict."""
        mock_session = MagicMock()

        with (
            patch.object(client, "_get_session", return_value=mock_session),
            patch("src.data.tastytrade_client.get_option_chain", new_callable=AsyncMock, return_value={}),
        ):
            result = await client.fetch_chain("SPY")

        assert result is None

    @pytest.mark.asyncio
    async def test_no_future_expirations(self, client):
        """Returns None when all expirations are in the past."""
        past_date = date.today() - timedelta(days=10)
        opt = _mock_option(expiration_date=past_date)
        chain_map = {past_date: [opt]}
        mock_session = MagicMock()

        with (
            patch.object(client, "_get_session", return_value=mock_session),
            patch("src.data.tastytrade_client.get_option_chain", new_callable=AsyncMock, return_value=chain_map),
        ):
            result = await client.fetch_chain("SPY")

        assert result is None

    @pytest.mark.asyncio
    async def test_missing_market_data_for_some_contracts(self, client):
        """Contracts with no market data get zero values."""
        expiry = date.today() + timedelta(days=30)
        opt1 = _mock_option(symbol="SYM1", streamer_symbol=".SYM1", expiration_date=expiry)
        opt2 = _mock_option(symbol="SYM2", streamer_symbol=".SYM2", expiration_date=expiry)
        md1 = _mock_market_data(symbol="SYM1")
        # No market data for SYM2

        chain_map = {expiry: [opt1, opt2]}
        mock_session = MagicMock()
        mock_streamer = AsyncMock()
        mock_streamer.__aenter__ = AsyncMock(side_effect=Exception("skip"))
        mock_streamer.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(client, "_get_session", return_value=mock_session),
            patch("src.data.tastytrade_client.get_option_chain", new_callable=AsyncMock, return_value=chain_map),
            patch("src.data.tastytrade_client.get_market_data_by_type", new_callable=AsyncMock, return_value=[md1]),
            patch("src.data.tastytrade_client.DXLinkStreamer", return_value=mock_streamer),
        ):
            result = await client.fetch_chain("SPY")

        assert result is not None
        assert len(result.contracts) == 2

        # First contract has market data
        assert result.contracts[0].bid == pytest.approx(5.0)
        assert result.contracts[0].volume == 1234

        # Second contract has zero values (no market data)
        assert result.contracts[1].bid == 0.0
        assert result.contracts[1].last == 0.0
        assert result.contracts[1].volume == 0

    @pytest.mark.asyncio
    async def test_ticker_case_normalization(self, client):
        """Ticker is uppercased regardless of input."""
        expiry = date.today() + timedelta(days=30)
        opt = _mock_option(expiration_date=expiry)
        md = _mock_market_data(symbol=opt.symbol)

        chain_map = {expiry: [opt]}
        mock_session = MagicMock()
        mock_streamer = AsyncMock()
        mock_streamer.__aenter__ = AsyncMock(side_effect=Exception("skip"))
        mock_streamer.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(client, "_get_session", return_value=mock_session),
            patch("src.data.tastytrade_client.get_option_chain", new_callable=AsyncMock, return_value=chain_map) as mock_chain,
            patch("src.data.tastytrade_client.get_market_data_by_type", new_callable=AsyncMock, return_value=[md]),
            patch("src.data.tastytrade_client.DXLinkStreamer", return_value=mock_streamer),
        ):
            result = await client.fetch_chain("spy")

        assert result.ticker == "SPY"
        mock_chain.assert_called_once_with(mock_session, "SPY")


# ---------------------------------------------------------------------------
# Tests: Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for authentication, network, and API error scenarios."""

    @pytest.fixture
    def client(self):
        return TastytradeClient(
            client_secret="test_secret",
            refresh_token="test_token",
        )

    @pytest.mark.asyncio
    async def test_auth_failure(self, client):
        """Returns None when get_option_chain raises auth error."""
        mock_session = MagicMock()

        with (
            patch.object(client, "_get_session", return_value=mock_session),
            patch(
                "src.data.tastytrade_client.get_option_chain",
                new_callable=AsyncMock,
                side_effect=Exception("401 Unauthorized"),
            ),
        ):
            result = await client.fetch_chain("SPY")

        assert result is None

    @pytest.mark.asyncio
    async def test_network_timeout(self, client):
        """Returns None when SDK raises a timeout."""
        mock_session = MagicMock()

        with (
            patch.object(client, "_get_session", return_value=mock_session),
            patch(
                "src.data.tastytrade_client.get_option_chain",
                new_callable=AsyncMock,
                side_effect=TimeoutError("Connection timed out"),
            ),
        ):
            result = await client.fetch_chain("SPY")

        assert result is None

    @pytest.mark.asyncio
    async def test_market_data_batch_failure_partial(self, client):
        """Chain still builds when one market data batch fails."""
        expiry = date.today() + timedelta(days=30)
        opt = _mock_option(expiration_date=expiry)
        chain_map = {expiry: [opt]}
        mock_session = MagicMock()
        mock_streamer = AsyncMock()
        mock_streamer.__aenter__ = AsyncMock(side_effect=Exception("skip"))
        mock_streamer.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(client, "_get_session", return_value=mock_session),
            patch("src.data.tastytrade_client.get_option_chain", new_callable=AsyncMock, return_value=chain_map),
            patch("src.data.tastytrade_client.get_market_data_by_type", new_callable=AsyncMock, side_effect=Exception("batch error")),
            patch("src.data.tastytrade_client.DXLinkStreamer", return_value=mock_streamer),
        ):
            result = await client.fetch_chain("SPY")

        # Still returns a chain, just with zero market data
        assert result is not None
        assert len(result.contracts) == 1
        assert result.contracts[0].bid == 0.0

    @pytest.mark.asyncio
    async def test_close_resets_session(self, client):
        """close() sets session to None for re-creation."""
        client._session = MagicMock()
        await client.close()
        assert client._session is None


# ---------------------------------------------------------------------------
# Tests: Spot price extraction
# ---------------------------------------------------------------------------


class TestSpotPriceExtraction:
    """Tests for the _extract_spot_price static method."""

    def test_with_options(self):
        """Extracts middle strike as spot proxy."""
        opts = [
            _mock_option(strike=590.0),
            _mock_option(strike=595.0),
            _mock_option(strike=600.0),
            _mock_option(strike=605.0),
            _mock_option(strike=610.0),
        ]
        spot = TastytradeClient._extract_spot_price({}, opts, "SPY")
        assert spot == 600.0  # middle strike

    def test_with_empty_options(self):
        """Returns 0.0 for empty options list."""
        spot = TastytradeClient._extract_spot_price({}, [], "SPY")
        assert spot == 0.0

    def test_with_single_option(self):
        """Returns the only strike."""
        opts = [_mock_option(strike=600.0)]
        spot = TastytradeClient._extract_spot_price({}, opts, "SPY")
        assert spot == 600.0
