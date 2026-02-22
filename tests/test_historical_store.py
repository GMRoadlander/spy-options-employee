"""Tests for HistoricalStore -- Parquet-based historical options storage.

Uses temporary directories for isolation. No external services needed.
"""

import pytest
import os
import tempfile
import shutil
from datetime import date, datetime

from src.data import OptionContract, OptionsChain
from src.data.historical_store import HistoricalStore, ARROW_SCHEMA


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_contract(
    ticker: str = "SPY",
    expiry: date | None = None,
    strike: float = 480.0,
    option_type: str = "call",
    bid: float = 5.0,
    ask: float = 5.50,
    volume: int = 1000,
    oi: int = 5000,
    iv: float = 0.20,
) -> OptionContract:
    """Create a test OptionContract."""
    return OptionContract(
        ticker=ticker,
        expiry=expiry or date(2024, 2, 16),
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        last=(bid + ask) / 2,
        volume=volume,
        open_interest=oi,
        iv=iv,
        delta=0.55 if option_type == "call" else -0.45,
        gamma=0.012,
        theta=-0.08,
        vega=0.35,
        rho=0.02 if option_type == "call" else -0.02,
    )


def _make_chain(
    ticker: str = "SPY",
    trade_date: date | None = None,
    spot: float = 475.50,
    num_strikes: int = 3,
) -> OptionsChain:
    """Create a test OptionsChain with both calls and puts."""
    td = trade_date or date(2024, 1, 15)
    contracts = []
    base_strike = round(spot / 5) * 5 - (num_strikes // 2) * 5

    for i in range(num_strikes):
        strike = base_strike + i * 5
        contracts.append(_make_contract(ticker=ticker, strike=strike, option_type="call"))
        contracts.append(_make_contract(ticker=ticker, strike=strike, option_type="put"))

    return OptionsChain(
        ticker=ticker,
        spot_price=spot,
        timestamp=datetime.combine(td, datetime.min.time()),
        contracts=contracts,
        source="orats",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test data."""
    d = tempfile.mkdtemp(prefix="hist_store_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def store(tmp_dir):
    """Create a HistoricalStore with a temp directory."""
    return HistoricalStore(tmp_dir)


# ---------------------------------------------------------------------------
# Tests: Save and load
# ---------------------------------------------------------------------------


class TestSaveAndLoad:
    """Tests for saving and loading chains."""

    @pytest.mark.asyncio
    async def test_save_and_load_single_chain(self, store):
        """Save one chain and load it back by date."""
        chain = _make_chain(trade_date=date(2024, 1, 15))
        saved = await store.save_chains([chain])
        assert saved == 6  # 3 strikes * 2 (call + put)

        loaded = await store.load_chain("SPY", date(2024, 1, 15))
        assert loaded is not None
        assert loaded.ticker == "SPY"
        assert loaded.spot_price == pytest.approx(475.50)
        assert len(loaded.contracts) == 6

    @pytest.mark.asyncio
    async def test_load_nonexistent_returns_none(self, store):
        """Loading a date with no data returns None."""
        result = await store.load_chain("SPY", date(2024, 6, 15))
        assert result is None

    @pytest.mark.asyncio
    async def test_save_multiple_days(self, store):
        """Save chains for multiple days and load individually."""
        chain1 = _make_chain(trade_date=date(2024, 1, 15), spot=475.0)
        chain2 = _make_chain(trade_date=date(2024, 1, 16), spot=478.0)

        await store.save_chains([chain1, chain2])

        loaded1 = await store.load_chain("SPY", date(2024, 1, 15))
        loaded2 = await store.load_chain("SPY", date(2024, 1, 16))

        assert loaded1.spot_price == pytest.approx(475.0)
        assert loaded2.spot_price == pytest.approx(478.0)

    @pytest.mark.asyncio
    async def test_save_empty_list(self, store):
        """Saving empty list returns 0 contracts."""
        saved = await store.save_chains([])
        assert saved == 0

    @pytest.mark.asyncio
    async def test_contract_fields_preserved(self, store):
        """All contract fields survive round-trip through Parquet."""
        contract = _make_contract(
            strike=480.0,
            bid=8.50,
            ask=9.00,
            volume=1200,
            oi=15000,
            iv=0.18,
        )
        chain = OptionsChain(
            ticker="SPY",
            spot_price=475.0,
            timestamp=datetime(2024, 1, 15),
            contracts=[contract],
            source="orats",
        )

        await store.save_chains([chain])
        loaded = await store.load_chain("SPY", date(2024, 1, 15))

        c = loaded.contracts[0]
        assert c.strike == pytest.approx(480.0)
        assert c.bid == pytest.approx(8.50)
        assert c.ask == pytest.approx(9.00)
        assert c.volume == 1200
        assert c.open_interest == 15000
        assert c.iv == pytest.approx(0.18)
        assert c.delta == pytest.approx(0.55)
        assert c.gamma == pytest.approx(0.012)


# ---------------------------------------------------------------------------
# Tests: Range queries
# ---------------------------------------------------------------------------


class TestLoadRange:
    """Tests for load_range method."""

    @pytest.mark.asyncio
    async def test_load_range_single_month(self, store):
        """Load range within a single month partition."""
        chains = [
            _make_chain(trade_date=date(2024, 1, d), spot=475.0 + d)
            for d in [10, 15, 20]
        ]
        await store.save_chains(chains)

        loaded = await store.load_range("SPY", date(2024, 1, 10), date(2024, 1, 20))
        assert len(loaded) == 3
        assert loaded[0].spot_price == pytest.approx(485.0)
        assert loaded[2].spot_price == pytest.approx(495.0)

    @pytest.mark.asyncio
    async def test_load_range_cross_month(self, store):
        """Load range spanning two months."""
        chain_jan = _make_chain(trade_date=date(2024, 1, 30), spot=475.0)
        chain_feb = _make_chain(trade_date=date(2024, 2, 5), spot=480.0)

        await store.save_chains([chain_jan, chain_feb])

        loaded = await store.load_range("SPY", date(2024, 1, 1), date(2024, 2, 28))
        assert len(loaded) == 2

    @pytest.mark.asyncio
    async def test_load_range_empty(self, store):
        """Empty range returns empty list."""
        loaded = await store.load_range("SPY", date(2024, 1, 1), date(2024, 1, 31))
        assert loaded == []


# ---------------------------------------------------------------------------
# Tests: has_data and get_available_range
# ---------------------------------------------------------------------------


class TestMetadata:
    """Tests for has_data and get_available_range."""

    @pytest.mark.asyncio
    async def test_has_data_true(self, store):
        """Returns True when data exists for the date."""
        chain = _make_chain(trade_date=date(2024, 1, 15))
        await store.save_chains([chain])
        assert await store.has_data("SPY", date(2024, 1, 15)) is True

    @pytest.mark.asyncio
    async def test_has_data_false(self, store):
        """Returns False when no data exists."""
        assert await store.has_data("SPY", date(2024, 1, 15)) is False

    @pytest.mark.asyncio
    async def test_get_available_range(self, store):
        """Returns min/max dates across all partitions."""
        chains = [
            _make_chain(trade_date=date(2024, 1, 10)),
            _make_chain(trade_date=date(2024, 3, 20)),
        ]
        await store.save_chains(chains)

        result = await store.get_available_range("SPY")
        assert result is not None
        assert result[0] == date(2024, 1, 10)
        assert result[1] == date(2024, 3, 20)

    @pytest.mark.asyncio
    async def test_get_available_range_no_data(self, store):
        """Returns None when no data exists for ticker."""
        result = await store.get_available_range("SPY")
        assert result is None
