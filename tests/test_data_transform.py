"""Tests for ORATS → optopsy data transform."""

from datetime import date, datetime

import pandas as pd
import pytest

from src.data import OptionContract, OptionsChain
from src.backtest.data_transform import (
    chains_to_optopsy_df,
    filter_pm_settled,
    _is_third_friday,
)


def _make_contract(
    strike: float = 5000.0,
    option_type: str = "call",
    bid: float = 10.0,
    ask: float = 12.0,
    delta: float = 0.30,
    expiry: date | None = None,
) -> OptionContract:
    return OptionContract(
        ticker="SPX",
        expiry=expiry or date(2024, 3, 22),
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        last=(bid + ask) / 2,
        volume=100,
        open_interest=500,
        iv=0.20,
        delta=delta,
    )


_DEFAULT_CONTRACTS = None  # sentinel


def _make_chain(
    contracts: list[OptionContract] | None = _DEFAULT_CONTRACTS,
    trade_date: date | None = None,
    spot: float = 5050.0,
) -> OptionsChain:
    trade_date = trade_date or date(2024, 3, 1)
    if contracts is _DEFAULT_CONTRACTS:
        contracts = [
            _make_contract(strike=5000.0, option_type="call", delta=0.30),
            _make_contract(strike=5000.0, option_type="put", delta=-0.70),
        ]
    return OptionsChain(
        ticker="SPX",
        spot_price=spot,
        timestamp=datetime.combine(trade_date, datetime.min.time()),
        contracts=contracts,
        source="orats",
    )


class TestChainsToOptopsyDf:
    """Test chains_to_optopsy_df conversion."""

    def test_splits_call_and_put_into_separate_rows(self):
        chain = _make_chain()
        df = chains_to_optopsy_df([chain])
        assert len(df) == 2
        assert set(df["option_type"]) == {"c", "p"}

    def test_field_mapping_matches_optopsy_positions(self):
        chain = _make_chain()
        df = chains_to_optopsy_df([chain])

        expected_cols = [
            "underlying_symbol", "underlying_price", "option_type",
            "expiration", "quote_date", "strike", "bid", "ask", "delta",
        ]
        assert list(df.columns) == expected_cols

    def test_call_row_values(self):
        chain = _make_chain()
        df = chains_to_optopsy_df([chain])
        call_row = df[df["option_type"] == "c"].iloc[0]

        assert call_row["underlying_symbol"] == "SPX"
        assert call_row["underlying_price"] == 5050.0
        assert call_row["strike"] == 5000.0
        assert call_row["bid"] == 10.0
        assert call_row["ask"] == 12.0
        assert call_row["delta"] == 0.30

    def test_put_row_values(self):
        chain = _make_chain()
        df = chains_to_optopsy_df([chain])
        put_row = df[df["option_type"] == "p"].iloc[0]

        assert put_row["underlying_symbol"] == "SPX"
        assert put_row["delta"] == -0.70

    def test_quote_date_from_chain_timestamp(self):
        chain = _make_chain(trade_date=date(2024, 6, 15))
        df = chains_to_optopsy_df([chain])
        expected = datetime(2024, 6, 15)
        assert df["quote_date"].iloc[0] == expected

    def test_expiration_from_contract_expiry(self):
        contracts = [_make_contract(expiry=date(2024, 4, 19))]
        chain = _make_chain(contracts=contracts)
        df = chains_to_optopsy_df([chain])
        expected = datetime(2024, 4, 19)
        assert df["expiration"].iloc[0] == expected

    def test_handles_multiple_dates_and_expirations(self):
        chain1 = _make_chain(trade_date=date(2024, 3, 1))
        chain2 = _make_chain(trade_date=date(2024, 3, 4))
        df = chains_to_optopsy_df([chain1, chain2])
        assert len(df) == 4  # 2 contracts per chain × 2 chains
        assert df["quote_date"].nunique() == 2

    def test_handles_zero_bid_ask(self):
        contracts = [_make_contract(bid=0.0, ask=0.0)]
        chain = _make_chain(contracts=contracts)
        df = chains_to_optopsy_df([chain])
        assert len(df) == 1
        assert df["bid"].iloc[0] == 0.0
        assert df["ask"].iloc[0] == 0.0

    def test_empty_chains_returns_empty_df(self):
        df = chains_to_optopsy_df([])
        assert len(df) == 0
        assert "underlying_symbol" in df.columns

    def test_chain_with_no_contracts(self):
        chain = _make_chain(contracts=[])
        df = chains_to_optopsy_df([chain])
        assert len(df) == 0


class TestIsThirdFriday:
    """Test third Friday detection."""

    def test_third_friday_jan_2024(self):
        assert _is_third_friday(date(2024, 1, 19)) is True

    def test_not_third_friday(self):
        assert _is_third_friday(date(2024, 1, 12)) is False  # second friday
        assert _is_third_friday(date(2024, 1, 26)) is False  # fourth friday

    def test_non_friday(self):
        assert _is_third_friday(date(2024, 1, 18)) is False  # thursday

    def test_third_friday_various_months(self):
        # Feb 2024: 3rd Friday = Feb 16
        assert _is_third_friday(date(2024, 2, 16)) is True
        # Mar 2024: 3rd Friday = Mar 15
        assert _is_third_friday(date(2024, 3, 15)) is True
        # Dec 2024: 3rd Friday = Dec 20
        assert _is_third_friday(date(2024, 12, 20)) is True


class TestFilterPmSettled:
    """Test PM-settled filter."""

    def test_excludes_third_friday_monthlies(self):
        # Jan 19, 2024 is a third Friday → should be excluded
        contracts = [
            _make_contract(expiry=date(2024, 1, 19)),  # 3rd Friday - exclude
            _make_contract(expiry=date(2024, 1, 22)),  # Monday - keep
        ]
        chain = _make_chain(contracts=contracts)
        df = chains_to_optopsy_df([chain])
        filtered = filter_pm_settled(df)

        assert len(filtered) == 1
        assert filtered["expiration"].iloc[0] == datetime(2024, 1, 22)

    def test_keeps_non_third_friday_expirations(self):
        contracts = [
            _make_contract(expiry=date(2024, 1, 12)),  # 2nd Friday - keep
            _make_contract(expiry=date(2024, 1, 17)),  # Wednesday - keep
        ]
        chain = _make_chain(contracts=contracts)
        df = chains_to_optopsy_df([chain])
        filtered = filter_pm_settled(df)

        assert len(filtered) == 2

    def test_empty_df_returns_empty(self):
        df = chains_to_optopsy_df([])
        filtered = filter_pm_settled(df)
        assert len(filtered) == 0
