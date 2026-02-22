"""Transform ORATS historical data into optopsy-compatible DataFrames.

ORATS stores each strike as a single row with both call and put data.
Optopsy expects separate rows per option type with specific column ordering.

Output columns (by index position):
    0: underlying_symbol (str)
    1: underlying_price (float)
    2: option_type (str: "c" or "p")
    3: expiration (datetime)
    4: quote_date (datetime)
    5: strike (float)
    6: bid (float)
    7: ask (float)
    8: delta (float, optional)
"""

from __future__ import annotations

import calendar
from datetime import date, datetime

import pandas as pd

from src.data import OptionsChain


def chains_to_optopsy_df(chains: list[OptionsChain]) -> pd.DataFrame:
    """Transform list of OptionsChain objects into optopsy-compatible DataFrame.

    Each OptionsChain contains contracts that are already split into call/put.
    This function flattens them into a single DataFrame with the column layout
    optopsy expects.

    Args:
        chains: List of OptionsChain objects (from HistoricalStore).

    Returns:
        DataFrame with columns: underlying_symbol, underlying_price,
        option_type, expiration, quote_date, strike, bid, ask, delta.
    """
    rows: list[dict] = []

    for chain in chains:
        quote_dt = chain.timestamp
        if isinstance(quote_dt, date) and not isinstance(quote_dt, datetime):
            quote_dt = datetime.combine(quote_dt, datetime.min.time())

        for contract in chain.contracts:
            exp_dt = contract.expiry
            if isinstance(exp_dt, date) and not isinstance(exp_dt, datetime):
                exp_dt = datetime.combine(exp_dt, datetime.min.time())

            rows.append({
                "underlying_symbol": chain.ticker,
                "underlying_price": chain.spot_price,
                "option_type": "c" if contract.option_type == "call" else "p",
                "expiration": exp_dt,
                "quote_date": quote_dt,
                "strike": contract.strike,
                "bid": contract.bid,
                "ask": contract.ask,
                "delta": contract.delta,
            })

    if not rows:
        return pd.DataFrame(columns=[
            "underlying_symbol", "underlying_price", "option_type",
            "expiration", "quote_date", "strike", "bid", "ask", "delta",
        ])

    df = pd.DataFrame(rows)
    return df


def _is_third_friday(d: date) -> bool:
    """Check if a date is the third Friday of its month.

    Standard SPX monthlies expire on the third Friday (AM-settled).
    SPXW weeklies expire on all other days (PM-settled).

    Args:
        d: Date to check.

    Returns:
        True if d is the third Friday of its month.
    """
    if d.weekday() != 4:  # 4 = Friday
        return False

    # Third Friday is the first Friday on or after the 15th
    # Find the first day of the month
    first_day = date(d.year, d.month, 1)
    # Find the first Friday
    first_friday = first_day
    while first_friday.weekday() != 4:
        first_friday = first_friday.replace(day=first_friday.day + 1)
    # Third Friday = first Friday + 14 days
    third_friday = first_friday.replace(day=first_friday.day + 14)
    return d == third_friday


def filter_pm_settled(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to SPXW PM-settled weeklies only.

    Excludes standard monthly SPX options that expire on the third Friday
    of each month (AM-settled). SPXW weeklies expire on all other days
    and are PM-settled, which optopsy handles correctly.

    Args:
        df: DataFrame with an 'expiration' column (datetime).

    Returns:
        Filtered DataFrame with only PM-settled expirations.
    """
    if df.empty:
        return df

    expiration_col = df["expiration"]

    # Convert to date for comparison
    def is_not_third_friday(exp: datetime | date) -> bool:
        if isinstance(exp, datetime):
            exp = exp.date()
        return not _is_third_friday(exp)

    mask = expiration_col.apply(is_not_third_friday)
    return df[mask].reset_index(drop=True)
