"""Tests for DataManager fallback chain and caching.

Covers the Tastytrade → CBOE → Tradier fallback strategy,
cache TTL behavior, quality checks, and concurrent fetching.
All external API calls are mocked — no real network access.
"""

from __future__ import annotations

import pytest

pytest.importorskip("tastytrade", reason="tastytrade SDK not installed")

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest_asyncio

from src.data import OptionContract, OptionsChain
from src.data.data_manager import DataManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chain(
    source: str = "test",
    n_contracts: int = 20,
    with_oi: bool = True,
    with_iv: bool = True,
) -> OptionsChain:
    """Create a realistic OptionsChain for testing."""
    expiry = date.today() + timedelta(days=30)
    contracts = []
    for i in range(n_contracts):
        strike = 4900.0 + i * 10
        contracts.append(OptionContract(
            ticker="SPX",
            expiry=expiry,
            strike=strike,
            option_type="call",
            bid=2.0,
            ask=2.50,
            last=2.25,
            volume=100,
            open_interest=500 if with_oi else 0,
            iv=0.20 if with_iv else 0.0,
            delta=0.5,
            gamma=0.01,
            theta=-0.05,
            vega=0.15,
        ))
    chain = OptionsChain(
        ticker="SPX",
        spot_price=5000.0,
        contracts=contracts,
        source=source,
    )
    return chain


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def dm():
    """Create a DataManager with mocked clients."""
    with patch("src.data.data_manager.config") as mock_config:
        mock_config.tastytrade_client_secret = "fake"
        mock_config.tastytrade_refresh_token = "fake"
        mock_config.tradier_token = "fake"
        mock_config.tickers = ["SPX", "SPY"]
        mock_config.cache_ttl_seconds = 120

        manager = DataManager.__new__(DataManager)
        manager._tastytrade = AsyncMock()
        manager._cboe = AsyncMock()
        manager._tradier = AsyncMock()
        manager._cache = {}
        yield manager


# ---------------------------------------------------------------------------
# Fallback chain tests
# ---------------------------------------------------------------------------

class TestFallbackChain:
    @pytest.mark.asyncio
    async def test_tastytrade_succeeds(self, dm):
        """When Tastytrade returns good data, CBOE and Tradier are not called."""
        chain = _make_chain(source="tastytrade")
        dm._tastytrade.fetch_chain = AsyncMock(return_value=chain)

        result = await dm.get_chain("SPX")

        assert result is not None
        assert result.source == "tastytrade"
        dm._cboe.fetch_chain.assert_not_called()
        dm._tradier.fetch_chain.assert_not_called()

    @pytest.mark.asyncio
    async def test_tastytrade_fails_cboe_succeeds(self, dm):
        """When Tastytrade fails, falls back to CBOE."""
        dm._tastytrade.fetch_chain = AsyncMock(return_value=None)
        chain = _make_chain(source="cboe")
        dm._cboe.fetch_chain = AsyncMock(return_value=chain)

        result = await dm.get_chain("SPX")

        assert result is not None
        assert result.source == "cboe"
        dm._tradier.fetch_chain.assert_not_called()

    @pytest.mark.asyncio
    async def test_tastytrade_and_cboe_fail_tradier_succeeds(self, dm):
        """When both Tastytrade and CBOE fail, falls back to Tradier."""
        dm._tastytrade.fetch_chain = AsyncMock(return_value=None)
        dm._cboe.fetch_chain = AsyncMock(return_value=None)
        chain = _make_chain(source="tradier")
        dm._tradier.fetch_chain = AsyncMock(return_value=chain)

        result = await dm.get_chain("SPX")

        assert result is not None
        assert result.source == "tradier"

    @pytest.mark.asyncio
    async def test_all_sources_fail(self, dm):
        """When all three sources fail, returns None."""
        dm._tastytrade.fetch_chain = AsyncMock(return_value=None)
        dm._cboe.fetch_chain = AsyncMock(return_value=None)
        dm._tradier.fetch_chain = AsyncMock(return_value=None)

        result = await dm.get_chain("SPX")

        assert result is None

    @pytest.mark.asyncio
    async def test_tastytrade_exception_falls_through(self, dm):
        """Tastytrade raising an exception falls through to CBOE."""
        dm._tastytrade.fetch_chain = AsyncMock(side_effect=Exception("connection reset"))
        chain = _make_chain(source="cboe")
        dm._cboe.fetch_chain = AsyncMock(return_value=chain)

        result = await dm.get_chain("SPX")

        assert result is not None
        assert result.source == "cboe"

    @pytest.mark.asyncio
    async def test_tastytrade_not_configured(self, dm):
        """When Tastytrade is None (not configured), skips to CBOE."""
        dm._tastytrade = None
        chain = _make_chain(source="cboe")
        dm._cboe.fetch_chain = AsyncMock(return_value=chain)

        result = await dm.get_chain("SPX")

        assert result is not None
        assert result.source == "cboe"


# ---------------------------------------------------------------------------
# Quality check tests
# ---------------------------------------------------------------------------

class TestQualityChecks:
    @pytest.mark.asyncio
    async def test_unusable_chain_skipped(self, dm):
        """A chain with zero OI and zero IV is skipped as unusable."""
        bad_chain = _make_chain(source="tastytrade", with_oi=False, with_iv=False)
        dm._tastytrade.fetch_chain = AsyncMock(return_value=bad_chain)
        good_chain = _make_chain(source="cboe")
        dm._cboe.fetch_chain = AsyncMock(return_value=good_chain)

        result = await dm.get_chain("SPX")

        assert result is not None
        assert result.source == "cboe"

    @pytest.mark.asyncio
    async def test_degraded_chain_accepted(self, dm):
        """A chain with low OI but some IV is accepted as degraded."""
        chain = _make_chain(source="tastytrade", with_oi=False, with_iv=True)
        dm._tastytrade.fetch_chain = AsyncMock(return_value=chain)

        result = await dm.get_chain("SPX")

        assert result is not None
        assert result.data_quality == "degraded"

    @pytest.mark.asyncio
    async def test_empty_chain_skipped(self, dm):
        """A chain with empty contracts list is treated as failure."""
        empty_chain = OptionsChain(
            ticker="SPX", spot_price=5000.0, contracts=[], source="tastytrade"
        )
        dm._tastytrade.fetch_chain = AsyncMock(return_value=empty_chain)
        dm._cboe.fetch_chain = AsyncMock(return_value=None)
        dm._tradier.fetch_chain = AsyncMock(return_value=None)

        result = await dm.get_chain("SPX")
        assert result is None


# ---------------------------------------------------------------------------
# Concurrent fetching tests
# ---------------------------------------------------------------------------

class TestGetAllChains:
    @pytest.mark.asyncio
    async def test_concurrent_fetch_both_succeed(self, dm):
        """get_all_chains fetches SPX and SPY concurrently."""
        spx_chain = _make_chain(source="tastytrade")
        spy_chain = _make_chain(source="tastytrade")
        spy_chain.ticker = "SPY"

        async def mock_fetch(ticker):
            if ticker == "SPX":
                return spx_chain
            return spy_chain

        dm._tastytrade.fetch_chain = AsyncMock(side_effect=mock_fetch)

        results = await dm.get_all_chains()

        assert "SPX" in results
        assert "SPY" in results

    @pytest.mark.asyncio
    async def test_concurrent_fetch_partial_failure(self, dm):
        """If one ticker fails, the other still succeeds."""
        chain = _make_chain(source="tastytrade")

        async def mock_fetch(ticker):
            if ticker == "SPX":
                return chain
            return None  # SPY fails

        dm._tastytrade.fetch_chain = AsyncMock(side_effect=mock_fetch)
        dm._cboe.fetch_chain = AsyncMock(return_value=None)
        dm._tradier.fetch_chain = AsyncMock(return_value=None)

        results = await dm.get_all_chains()

        assert "SPX" in results
        assert "SPY" not in results
