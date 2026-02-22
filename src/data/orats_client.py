"""ORATS API client for historical options chain data.

Wraps the ORATS Data API v2 (https://api.orats.io/datav2) for fetching
historical options chains, IV rank data, and ticker metadata. Transforms
ORATS combined rows (which have both call and put data in one row) into
separate OptionContract objects for compatibility with the analysis layer.

Rate limits:
  - 1,000 requests per minute
  - 20,000 requests per month

Requires:
  pip install aiohttp

Environment:
  ORATS_API_KEY -- API token from orats.com account
"""

import asyncio
import logging
import time
from datetime import date, datetime
from typing import Any

import aiohttp

from src.data import OptionContract, OptionsChain

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when ORATS rate limits are exceeded."""


class ORATSClient:
    """Async client for the ORATS Data API v2.

    Usage:
        client = ORATSClient(api_key="...")
        chain = await client.get_historical_chain("SPY", date(2024, 1, 15))
        await client.close()
    """

    BASE_URL = "https://api.orats.io/datav2"

    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession | None = None,
        requests_per_minute: int = 1000,
        requests_per_month: int = 20_000,
    ) -> None:
        self._api_key = api_key
        self._session = session
        self._owns_session = session is None

        # Rate limit tracking
        self._requests_per_minute = requests_per_minute
        self._requests_per_month = requests_per_month
        self._minute_requests: list[float] = []  # timestamps of requests this minute
        self._month_request_count: int = 0
        self._month_reset_time: float = time.time()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limits before making a request.

        Raises:
            RateLimitError: If either per-minute or per-month limit is exceeded.
        """
        now = time.time()

        # Clean up old minute-window entries
        cutoff = now - 60.0
        self._minute_requests = [t for t in self._minute_requests if t > cutoff]

        # Check per-minute limit
        if len(self._minute_requests) >= self._requests_per_minute:
            raise RateLimitError(
                f"Rate limit exceeded: {self._requests_per_minute} requests/minute. "
                f"Try again in {60.0 - (now - self._minute_requests[0]):.1f}s."
            )

        # Reset monthly counter if a new month has started (30 days approximation)
        if now - self._month_reset_time > 30 * 24 * 3600:
            self._month_request_count = 0
            self._month_reset_time = now

        # Check per-month limit
        if self._month_request_count >= self._requests_per_month:
            raise RateLimitError(
                f"Monthly rate limit exceeded: {self._requests_per_month} requests/month."
            )

    def _record_request(self) -> None:
        """Record a request for rate limit tracking."""
        self._minute_requests.append(time.time())
        self._month_request_count += 1

    @property
    def rate_limit_status(self) -> dict[str, Any]:
        """Return current rate limit usage."""
        now = time.time()
        cutoff = now - 60.0
        recent = [t for t in self._minute_requests if t > cutoff]
        return {
            "minute_used": len(recent),
            "minute_limit": self._requests_per_minute,
            "month_used": self._month_request_count,
            "month_limit": self._requests_per_month,
        }

    async def _request(self, endpoint: str, params: dict[str, str] | None = None) -> dict:
        """Make an authenticated GET request to the ORATS API.

        Args:
            endpoint: API endpoint path (e.g., "/hist/strikes").
            params: Additional query parameters.

        Returns:
            Parsed JSON response as a dict.

        Raises:
            RateLimitError: If rate limits are exceeded.
            aiohttp.ClientError: On network errors.
            ValueError: On non-200 responses or invalid JSON.
        """
        self._check_rate_limit()

        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"

        # Auth via query param
        query_params = {"token": self._api_key}
        if params:
            query_params.update(params)

        logger.debug("ORATS request: GET %s params=%s", endpoint, {k: v for k, v in query_params.items() if k != "token"})

        async with session.get(url, params=query_params) as resp:
            self._record_request()

            if resp.status == 429:
                raise RateLimitError("ORATS API returned 429 Too Many Requests")

            if resp.status != 200:
                text = await resp.text()
                raise ValueError(
                    f"ORATS API error {resp.status}: {text[:200]}"
                )

            data = await resp.json()
            return data

    async def get_tickers(self) -> list[str]:
        """Get list of available tickers from ORATS.

        Returns:
            List of ticker symbols.
        """
        try:
            data = await self._request("/tickers")
            rows = data.get("data", [])
            return [row["ticker"] for row in rows if "ticker" in row]
        except Exception as exc:
            logger.error("Failed to fetch ORATS tickers: %s", exc)
            return []

    async def get_historical_chain(
        self,
        ticker: str,
        trade_date: date,
    ) -> OptionsChain | None:
        """Fetch a historical options chain for a specific date.

        ORATS returns combined rows with both call and put data in each row.
        This method transforms them into separate OptionContract objects.

        Args:
            ticker: Ticker symbol (e.g., "SPY").
            trade_date: The historical trade date.

        Returns:
            OptionsChain with all contracts for that date, or None on error.
        """
        ticker = ticker.upper()

        try:
            data = await self._request(
                "/hist/strikes",
                params={
                    "ticker": ticker,
                    "tradeDate": trade_date.isoformat(),
                },
            )

            rows = data.get("data", [])
            if not rows:
                logger.info("No ORATS data for %s on %s", ticker, trade_date)
                return None

            contracts = []
            spot_price = 0.0

            for row in rows:
                spot_price = float(row.get("stkPx", 0.0))
                contracts.extend(self._transform_row(ticker, row))

            if not contracts:
                return None

            chain = OptionsChain(
                ticker=ticker,
                spot_price=spot_price,
                timestamp=datetime.combine(trade_date, datetime.min.time()),
                contracts=contracts,
                source="orats",
            )

            logger.debug(
                "Fetched ORATS chain for %s on %s: %d contracts, spot=$%.2f",
                ticker, trade_date, len(contracts), spot_price,
            )
            return chain

        except RateLimitError:
            raise
        except Exception as exc:
            logger.error("Failed to fetch ORATS chain for %s on %s: %s", ticker, trade_date, exc)
            return None

    async def get_historical_range(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> list[OptionsChain]:
        """Fetch historical chains for a date range.

        Makes one request per trading day. Skips weekends automatically.
        Results are returned in chronological order.

        Args:
            ticker: Ticker symbol.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            List of OptionsChain objects, one per trading day with data.
        """
        ticker = ticker.upper()
        chains: list[OptionsChain] = []

        try:
            data = await self._request(
                "/hist/strikes",
                params={
                    "ticker": ticker,
                    "tradeDate": f"{start_date.isoformat()},{end_date.isoformat()}",
                },
            )

            rows = data.get("data", [])
            if not rows:
                logger.info("No ORATS data for %s from %s to %s", ticker, start_date, end_date)
                return []

            # Group rows by trade date
            by_date: dict[str, list[dict]] = {}
            for row in rows:
                td = row.get("tradeDate", "")
                if td:
                    by_date.setdefault(td, []).append(row)

            # Build chains for each date
            for td_str in sorted(by_date.keys()):
                date_rows = by_date[td_str]
                trade_date = date.fromisoformat(td_str)

                contracts = []
                spot_price = 0.0
                for row in date_rows:
                    spot_price = float(row.get("stkPx", 0.0))
                    contracts.extend(self._transform_row(ticker, row))

                if contracts:
                    chain = OptionsChain(
                        ticker=ticker,
                        spot_price=spot_price,
                        timestamp=datetime.combine(trade_date, datetime.min.time()),
                        contracts=contracts,
                        source="orats",
                    )
                    chains.append(chain)

            logger.debug(
                "Fetched ORATS range for %s: %d days from %s to %s",
                ticker, len(chains), start_date, end_date,
            )

        except RateLimitError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch ORATS range for %s %s-%s: %s",
                ticker, start_date, end_date, exc,
            )

        return chains

    async def get_iv_rank(self, ticker: str) -> dict[str, float] | None:
        """Get current IV rank and percentile for a ticker.

        Args:
            ticker: Ticker symbol.

        Returns:
            Dict with iv_rank, iv_percentile, current_iv, or None on error.
        """
        ticker = ticker.upper()

        try:
            data = await self._request(
                "/hist/dailies",
                params={"ticker": ticker},
            )

            rows = data.get("data", [])
            if not rows:
                return None

            # Most recent row
            latest = rows[-1]
            return {
                "iv_rank": float(latest.get("ivRank", 0.0)),
                "iv_percentile": float(latest.get("ivPct", 0.0)),
                "current_iv": float(latest.get("orIvFcst20d", 0.0)),
                "hv_20d": float(latest.get("orHv20d", 0.0)),
            }

        except Exception as exc:
            logger.error("Failed to fetch ORATS IV rank for %s: %s", ticker, exc)
            return None

    @staticmethod
    def _transform_row(ticker: str, row: dict) -> list[OptionContract]:
        """Transform an ORATS combined row into separate call and put OptionContracts.

        ORATS returns each strike as a single row with both call and put data:
          callBidPrice, callAskPrice, callVolume, callOpenInterest, callValue, ...
          putBidPrice, putAskPrice, putVolume, putOpenInterest, putValue, ...

        Args:
            ticker: Ticker symbol.
            row: Raw ORATS data row.

        Returns:
            List of 0-2 OptionContract objects (call, put, or both).
        """
        contracts = []

        try:
            expiry_str = row.get("expirDate", "")
            if not expiry_str:
                return contracts
            expiry = date.fromisoformat(expiry_str)

            strike = float(row.get("strike", 0.0))
            if strike <= 0:
                return contracts

            # Call contract
            call_bid = float(row.get("callBidPrice", 0.0))
            call_ask = float(row.get("callAskPrice", 0.0))
            call_volume = int(row.get("callVolume", 0))
            call_oi = int(row.get("callOpenInterest", 0))
            call_iv = float(row.get("callIv", 0.0))

            # Only include if there's meaningful data
            if call_bid > 0 or call_ask > 0 or call_volume > 0 or call_oi > 0:
                contracts.append(OptionContract(
                    ticker=ticker,
                    expiry=expiry,
                    strike=strike,
                    option_type="call",
                    bid=call_bid,
                    ask=call_ask,
                    last=(call_bid + call_ask) / 2.0 if (call_bid + call_ask) > 0 else 0.0,
                    volume=call_volume,
                    open_interest=call_oi,
                    iv=call_iv,
                    delta=float(row.get("callDelta", 0.0)),
                    gamma=float(row.get("callGamma", 0.0)),
                    theta=float(row.get("callTheta", 0.0)),
                    vega=float(row.get("callVega", 0.0)),
                    rho=float(row.get("callRho", 0.0)),
                ))

            # Put contract
            put_bid = float(row.get("putBidPrice", 0.0))
            put_ask = float(row.get("putAskPrice", 0.0))
            put_volume = int(row.get("putVolume", 0))
            put_oi = int(row.get("putOpenInterest", 0))
            put_iv = float(row.get("putIv", 0.0))

            if put_bid > 0 or put_ask > 0 or put_volume > 0 or put_oi > 0:
                contracts.append(OptionContract(
                    ticker=ticker,
                    expiry=expiry,
                    strike=strike,
                    option_type="put",
                    bid=put_bid,
                    ask=put_ask,
                    last=(put_bid + put_ask) / 2.0 if (put_bid + put_ask) > 0 else 0.0,
                    volume=put_volume,
                    open_interest=put_oi,
                    iv=put_iv,
                    delta=float(row.get("putDelta", 0.0)),
                    gamma=float(row.get("putGamma", 0.0)),
                    theta=float(row.get("putTheta", 0.0)),
                    vega=float(row.get("putVega", 0.0)),
                    rho=float(row.get("putRho", 0.0)),
                ))

        except (ValueError, TypeError, KeyError) as exc:
            logger.warning("Failed to transform ORATS row: %s", exc)

        return contracts

    async def close(self) -> None:
        """Close the aiohttp session if we own it."""
        if self._session is not None and self._owns_session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.debug("ORATS client session closed")
