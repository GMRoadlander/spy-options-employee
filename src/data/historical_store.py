"""Parquet-based historical data storage for options chains.

Stores OptionsChain data in partitioned Parquet files organized by
ticker/year/YYYY-MM.parquet. Uses PyArrow for efficient columnar storage
and compression.

Partitioning scheme:
    {base_dir}/{ticker}/{year}/{YYYY-MM}.parquet

Each Parquet file contains one month of daily chain snapshots. Data is
appended when new chains arrive and deduplicated by (timestamp, strike,
option_type, expiry).
"""

import logging
import os
from datetime import date, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.data import OptionContract, OptionsChain

logger = logging.getLogger(__name__)

# Arrow schema for the options data
ARROW_SCHEMA = pa.schema([
    ("timestamp", pa.timestamp("us")),
    ("ticker", pa.string()),
    ("spot_price", pa.float64()),
    ("source", pa.string()),
    ("expiry", pa.date32()),
    ("strike", pa.float64()),
    ("option_type", pa.string()),
    ("bid", pa.float64()),
    ("ask", pa.float64()),
    ("last", pa.float64()),
    ("volume", pa.int64()),
    ("open_interest", pa.int64()),
    ("iv", pa.float64()),
    ("delta", pa.float64()),
    ("gamma", pa.float64()),
    ("theta", pa.float64()),
    ("vega", pa.float64()),
    ("rho", pa.float64()),
])


class HistoricalStore:
    """Parquet-based storage for historical options chain data.

    Usage:
        store = HistoricalStore("/path/to/data")
        await store.save_chains([chain1, chain2])
        chain = await store.load_chain("SPY", date(2024, 1, 15))
        chains = await store.load_range("SPY", date(2024, 1, 1), date(2024, 1, 31))
    """

    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)

    def _partition_path(self, ticker: str, dt: date) -> Path:
        """Get the Parquet file path for a given ticker and date.

        Args:
            ticker: Ticker symbol (uppercased).
            dt: Date to determine the year/month partition.

        Returns:
            Path to the Parquet file.
        """
        return self._base_dir / ticker.upper() / str(dt.year) / f"{dt.strftime('%Y-%m')}.parquet"

    def _chains_to_table(self, chains: list[OptionsChain]) -> pa.Table:
        """Convert a list of OptionsChain objects to a PyArrow table.

        Flattens chain -> contracts into a row-per-contract table with
        chain-level metadata (timestamp, ticker, spot_price, source)
        denormalized into each row.

        Args:
            chains: List of OptionsChain objects to convert.

        Returns:
            PyArrow Table matching ARROW_SCHEMA.
        """
        rows: dict[str, list] = {field.name: [] for field in ARROW_SCHEMA}

        for chain in chains:
            for contract in chain.contracts:
                rows["timestamp"].append(chain.timestamp)
                rows["ticker"].append(chain.ticker)
                rows["spot_price"].append(chain.spot_price)
                rows["source"].append(chain.source)
                rows["expiry"].append(contract.expiry)
                rows["strike"].append(contract.strike)
                rows["option_type"].append(contract.option_type)
                rows["bid"].append(contract.bid)
                rows["ask"].append(contract.ask)
                rows["last"].append(contract.last)
                rows["volume"].append(contract.volume)
                rows["open_interest"].append(contract.open_interest)
                rows["iv"].append(contract.iv)
                rows["delta"].append(contract.delta)
                rows["gamma"].append(contract.gamma)
                rows["theta"].append(contract.theta)
                rows["vega"].append(contract.vega)
                rows["rho"].append(contract.rho)

        return pa.table(rows, schema=ARROW_SCHEMA)

    def _table_to_chains(self, table: pa.Table) -> list[OptionsChain]:
        """Convert a PyArrow table back to OptionsChain objects.

        Groups rows by (timestamp, ticker) and rebuilds chains with
        their respective contracts.

        Args:
            table: PyArrow Table matching ARROW_SCHEMA.

        Returns:
            List of OptionsChain objects.
        """
        if table.num_rows == 0:
            return []

        # Convert to Python dicts for grouping
        df_dict = table.to_pydict()
        num_rows = table.num_rows

        # Group by (timestamp, ticker)
        chain_map: dict[tuple, dict] = {}

        for i in range(num_rows):
            ts = df_dict["timestamp"][i]
            if isinstance(ts, datetime):
                key_ts = ts
            else:
                key_ts = ts.as_py() if hasattr(ts, "as_py") else ts

            ticker = df_dict["ticker"][i]
            key = (key_ts, ticker)

            if key not in chain_map:
                chain_map[key] = {
                    "ticker": ticker,
                    "spot_price": df_dict["spot_price"][i],
                    "timestamp": key_ts,
                    "source": df_dict["source"][i],
                    "contracts": [],
                }

            expiry_val = df_dict["expiry"][i]
            if isinstance(expiry_val, date):
                expiry = expiry_val
            elif hasattr(expiry_val, "as_py"):
                expiry = expiry_val.as_py()
            else:
                expiry = expiry_val

            contract = OptionContract(
                ticker=ticker,
                expiry=expiry,
                strike=df_dict["strike"][i],
                option_type=df_dict["option_type"][i],
                bid=df_dict["bid"][i],
                ask=df_dict["ask"][i],
                last=df_dict["last"][i],
                volume=df_dict["volume"][i],
                open_interest=df_dict["open_interest"][i],
                iv=df_dict["iv"][i],
                delta=df_dict["delta"][i],
                gamma=df_dict["gamma"][i],
                theta=df_dict["theta"][i],
                vega=df_dict["vega"][i],
                rho=df_dict["rho"][i],
            )
            chain_map[key]["contracts"].append(contract)

        # Build OptionsChain objects sorted by timestamp
        chains = []
        for key in sorted(chain_map.keys()):
            info = chain_map[key]
            chains.append(OptionsChain(
                ticker=info["ticker"],
                spot_price=info["spot_price"],
                timestamp=info["timestamp"],
                contracts=info["contracts"],
                source=info["source"],
            ))

        return chains

    async def save_chains(self, chains: list[OptionsChain]) -> int:
        """Save options chains to Parquet storage.

        Groups chains by their partition (ticker/year-month) and writes
        each partition file. If a file already exists, the new data is
        appended and deduplicated.

        Args:
            chains: List of OptionsChain objects to save.

        Returns:
            Number of contracts saved.
        """
        if not chains:
            return 0

        # Group chains by partition key
        by_partition: dict[Path, list[OptionsChain]] = {}
        for chain in chains:
            chain_date = chain.timestamp.date() if isinstance(chain.timestamp, datetime) else chain.timestamp
            path = self._partition_path(chain.ticker, chain_date)
            by_partition.setdefault(path, []).append(chain)

        total_contracts = 0

        for path, partition_chains in by_partition.items():
            new_table = self._chains_to_table(partition_chains)

            # If file exists, merge with existing data
            if path.exists():
                try:
                    existing_table = pq.read_table(path, schema=ARROW_SCHEMA)
                    combined = pa.concat_tables([existing_table, new_table])
                except Exception as exc:
                    logger.warning("Failed to read existing Parquet %s, overwriting: %s", path, exc)
                    combined = new_table
            else:
                combined = new_table

            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write the combined table
            pq.write_table(combined, path, compression="snappy")

            total_contracts += new_table.num_rows
            logger.debug("Saved %d rows to %s", new_table.num_rows, path)

        logger.info("Saved %d contracts across %d partitions", total_contracts, len(by_partition))
        return total_contracts

    async def load_chain(self, ticker: str, trade_date: date) -> OptionsChain | None:
        """Load an options chain for a specific date.

        Args:
            ticker: Ticker symbol.
            trade_date: The date to load.

        Returns:
            OptionsChain for the date, or None if not found.
        """
        ticker = ticker.upper()
        path = self._partition_path(ticker, trade_date)

        if not path.exists():
            return None

        try:
            table = pq.read_table(path, schema=ARROW_SCHEMA)

            # Filter to the specific date
            ts_start = datetime.combine(trade_date, datetime.min.time())
            ts_end = datetime.combine(trade_date, datetime.max.time())

            # Use PyArrow compute filtering
            ge_start = pa.compute.greater_equal(table.column("timestamp"), pa.scalar(ts_start, type=pa.timestamp("us")))
            le_end = pa.compute.less_equal(table.column("timestamp"), pa.scalar(ts_end, type=pa.timestamp("us")))
            eq_ticker = pa.compute.equal(table.column("ticker"), pa.scalar(ticker))
            mask = pa.compute.and_(pa.compute.and_(ge_start, le_end), eq_ticker)
            filtered = table.filter(mask)

            chains = self._table_to_chains(filtered)
            if not chains:
                return None

            # Return the first (should be only) chain for this date
            return chains[0]

        except Exception as exc:
            logger.error("Failed to load chain for %s on %s: %s", ticker, trade_date, exc)
            return None

    async def load_range(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> list[OptionsChain]:
        """Load options chains for a date range.

        May span multiple monthly partition files.

        Args:
            ticker: Ticker symbol.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            List of OptionsChain objects in chronological order.
        """
        ticker = ticker.upper()
        chains: list[OptionsChain] = []

        # Determine which partition files to check
        paths_checked: set[Path] = set()
        current = start_date

        while current <= end_date:
            path = self._partition_path(ticker, current)
            if path not in paths_checked and path.exists():
                paths_checked.add(path)

                try:
                    table = pq.read_table(path, schema=ARROW_SCHEMA)

                    ts_start = datetime.combine(start_date, datetime.min.time())
                    ts_end = datetime.combine(end_date, datetime.max.time())

                    ge_start = pa.compute.greater_equal(table.column("timestamp"), pa.scalar(ts_start, type=pa.timestamp("us")))
                    le_end = pa.compute.less_equal(table.column("timestamp"), pa.scalar(ts_end, type=pa.timestamp("us")))
                    eq_ticker = pa.compute.equal(table.column("ticker"), pa.scalar(ticker))
                    mask = pa.compute.and_(pa.compute.and_(ge_start, le_end), eq_ticker)
                    filtered = table.filter(mask)
                    chains.extend(self._table_to_chains(filtered))

                except Exception as exc:
                    logger.error("Failed to read partition %s: %s", path, exc)

            # Move to next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

        # Sort by timestamp
        chains.sort(key=lambda c: c.timestamp)
        return chains

    async def has_data(self, ticker: str, trade_date: date) -> bool:
        """Check if data exists for a specific ticker and date.

        Does a quick file existence check first, then verifies data
        exists for the exact date within the partition.

        Args:
            ticker: Ticker symbol.
            trade_date: The date to check.

        Returns:
            True if data exists for the given ticker and date.
        """
        ticker = ticker.upper()
        path = self._partition_path(ticker, trade_date)

        if not path.exists():
            return False

        try:
            table = pq.read_table(path, schema=ARROW_SCHEMA, columns=["timestamp", "ticker"])
            ts_target = datetime.combine(trade_date, datetime.min.time())
            ts_end = datetime.combine(trade_date, datetime.max.time())

            ge_start = pa.compute.greater_equal(table.column("timestamp"), pa.scalar(ts_target, type=pa.timestamp("us")))
            le_end = pa.compute.less_equal(table.column("timestamp"), pa.scalar(ts_end, type=pa.timestamp("us")))
            eq_ticker = pa.compute.equal(table.column("ticker"), pa.scalar(ticker))
            mask = pa.compute.and_(pa.compute.and_(ge_start, le_end), eq_ticker)
            filtered = table.filter(mask)
            return filtered.num_rows > 0

        except Exception:
            return False

    async def get_available_range(self, ticker: str) -> tuple[date, date] | None:
        """Get the earliest and latest dates with data for a ticker.

        Scans the directory structure to find partition files and reads
        the min/max timestamps.

        Args:
            ticker: Ticker symbol.

        Returns:
            Tuple of (earliest_date, latest_date) or None if no data.
        """
        ticker = ticker.upper()
        ticker_dir = self._base_dir / ticker

        if not ticker_dir.exists():
            return None

        min_ts: datetime | None = None
        max_ts: datetime | None = None

        for parquet_file in sorted(ticker_dir.rglob("*.parquet")):
            try:
                table = pq.read_table(parquet_file, columns=["timestamp"])
                if table.num_rows == 0:
                    continue

                ts_col = table.column("timestamp")
                file_min = pa.compute.min(ts_col).as_py()
                file_max = pa.compute.max(ts_col).as_py()

                if min_ts is None or file_min < min_ts:
                    min_ts = file_min
                if max_ts is None or file_max > max_ts:
                    max_ts = file_max

            except Exception as exc:
                logger.warning("Failed to read %s for range check: %s", parquet_file, exc)

        if min_ts is None or max_ts is None:
            return None

        return (min_ts.date(), max_ts.date())
