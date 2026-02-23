"""Unusual Whales API client for institutional flow and dark pool data.

Wraps the Unusual Whales Pro REST API (https://api.unusualwhales.com/api)
for fetching options flow data, dark pool prints, and flow summaries.
Follows the same async aiohttp pattern established by ORATSClient and
PolygonClient.

Key data:
  - Options flow: sweeps, blocks, golden sweeps with classification/sentiment
  - Dark pool: off-exchange prints with price, size, notional
  - Flow summaries: aggregated premium, sweep/block counts, net sentiment

Rate limits:
  - 120 requests per minute (default, configurable)

Requires:
  pip install aiohttp

Environment:
  UNUSUAL_WHALES_API_KEY -- API token from unusualwhales.com account
"""

import asyncio
import logging
import time
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class UnusualWhalesAuthError(Exception):
    """Raised when Unusual Whales returns 401 (invalid API key)."""


class UnusualWhalesRateLimitError(Exception):
    """Raised when Unusual Whales rate limits are exceeded."""


class UnusualWhalesClient:
    """Async REST client for the Unusual Whales Pro API.

    Usage:
        client = UnusualWhalesClient(api_key="...")
        flow = await client.get_flow("SPX")
        dark = await client.get_dark_pool("SPX")
        summary = await client.get_flow_summary("SPX")
        await client.close()
    """

    BASE_URL = "https://api.unusualwhales.com/api"

    def __init__(
        self,
        api_key: str,
        requests_per_minute: int = 120,
    ) -> None:
        self._api_key = api_key
        self._session: aiohttp.ClientSession | None = None
        self._requests_per_minute = requests_per_minute
        self._minute_requests: list[float] = []

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session (lazy init)."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limits before making a request.

        Raises:
            UnusualWhalesRateLimitError: If per-minute limit is exceeded.
        """
        now = time.time()

        # Clean up old minute-window entries
        cutoff = now - 60.0
        self._minute_requests = [t for t in self._minute_requests if t > cutoff]

        # Check per-minute limit
        if len(self._minute_requests) >= self._requests_per_minute:
            wait_time = 60.0 - (now - self._minute_requests[0])
            raise UnusualWhalesRateLimitError(
                f"Rate limit exceeded: {self._requests_per_minute} requests/minute. "
                f"Try again in {wait_time:.1f}s."
            )

    def _record_request(self) -> None:
        """Record a request for rate limit tracking."""
        self._minute_requests.append(time.time())

    @property
    def rate_limit_status(self) -> dict[str, Any]:
        """Return current rate limit usage."""
        now = time.time()
        cutoff = now - 60.0
        recent = [t for t in self._minute_requests if t > cutoff]
        return {
            "minute_used": len(recent),
            "minute_limit": self._requests_per_minute,
        }

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict:
        """Make an authenticated GET request to the Unusual Whales API.

        Auth is via ``Authorization: Bearer {key}`` header.

        Args:
            endpoint: API endpoint path (e.g., "/stock/SPX/option-contracts").
            params: Additional query parameters.

        Returns:
            Parsed JSON response as a dict.

        Raises:
            UnusualWhalesAuthError: On 401 (invalid API key).
            UnusualWhalesRateLimitError: On 429 or if local rate limit is exceeded.
            asyncio.TimeoutError: On request timeout.
            aiohttp.ClientError: On network errors.
            ValueError: On unexpected non-200 responses.
        """
        self._check_rate_limit()

        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"

        headers = {"Authorization": f"Bearer {self._api_key}"}

        logger.debug(
            "Unusual Whales request: GET %s params=%s",
            endpoint,
            params,
        )

        try:
            async with session.get(
                url,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                self._record_request()

                if resp.status == 401:
                    raise UnusualWhalesAuthError(
                        "Unusual Whales API returned 401: invalid or missing API key"
                    )

                if resp.status == 429:
                    raise UnusualWhalesRateLimitError(
                        "Unusual Whales API returned 429: rate limit exceeded"
                    )

                if resp.status != 200:
                    text = await resp.text()
                    raise ValueError(
                        f"Unusual Whales API error {resp.status}: {text[:200]}"
                    )

                data = await resp.json()
                return data

        except asyncio.TimeoutError:
            logger.error("Unusual Whales request timed out: %s", endpoint)
            raise

    async def get_flow(
        self,
        ticker: str = "SPX",
        limit: int = 100,
    ) -> list[dict]:
        """Fetch recent options flow for a ticker.

        Args:
            ticker: Underlying ticker (e.g., "SPX", "SPY").
            limit: Max results to return (default 100).

        Returns:
            List of flow dicts with ticker, strike, expiry, type, side,
            premium, volume, open_interest, iv, classification, sentiment,
            and timestamp. Empty list on error or if API key is not configured.
        """
        if not self._api_key:
            logger.warning(
                "Unusual Whales API key not configured — returning empty flow"
            )
            return []

        ticker = ticker.upper()

        try:
            data = await self._request(
                f"/stock/{ticker}/option-contracts",
                params={"limit": limit},
            )

            raw_results = data.get("data", [])
            results: list[dict] = []

            for entry in raw_results:
                results.append({
                    "ticker": str(entry.get("ticker", ticker)),
                    "strike": float(entry.get("strike_price", entry.get("strike", 0.0))),
                    "expiry": str(entry.get("expires_date", entry.get("expiry", ""))),
                    "type": str(entry.get("put_call", entry.get("type", "unknown"))).lower(),
                    "side": str(entry.get("side", entry.get("sentiment", "unknown"))).lower(),
                    "premium": float(entry.get("premium", 0.0)),
                    "volume": int(entry.get("volume", 0)),
                    "open_interest": int(entry.get("open_interest", 0)),
                    "iv": float(entry.get("implied_volatility", entry.get("iv", 0.0))),
                    "classification": str(
                        entry.get("option_activity_type", entry.get("classification", "standard"))
                    ).lower(),
                    "sentiment": str(entry.get("sentiment", "neutral")).lower(),
                    "timestamp": str(entry.get("date", entry.get("timestamp", ""))),
                })

            logger.debug(
                "Unusual Whales flow for %s: %d entries",
                ticker,
                len(results),
            )
            return results[:limit]

        except (UnusualWhalesAuthError, UnusualWhalesRateLimitError):
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch Unusual Whales flow for %s: %s",
                ticker,
                exc,
            )
            return []

    async def get_dark_pool(
        self,
        ticker: str = "SPX",
        limit: int = 50,
    ) -> list[dict]:
        """Fetch dark pool activity for a ticker.

        Args:
            ticker: Underlying ticker (e.g., "SPX", "SPY").
            limit: Max results to return (default 50).

        Returns:
            List of dark pool dicts with ticker, price, size, notional,
            exchange, and timestamp. Empty list on error or if API key
            is not configured.
        """
        if not self._api_key:
            logger.warning(
                "Unusual Whales API key not configured — returning empty dark pool data"
            )
            return []

        ticker = ticker.upper()

        try:
            data = await self._request(
                f"/stock/{ticker}/dark-pool",
                params={"limit": limit},
            )

            raw_results = data.get("data", [])
            results: list[dict] = []

            for entry in raw_results:
                price = float(entry.get("price", entry.get("avg_price", 0.0)))
                size = int(entry.get("size", entry.get("volume", 0)))
                notional = float(entry.get("notional", price * size))

                results.append({
                    "ticker": str(entry.get("ticker", ticker)),
                    "price": price,
                    "size": size,
                    "notional": notional,
                    "exchange": str(entry.get("exchange", entry.get("market_center", "unknown"))),
                    "timestamp": str(entry.get("date", entry.get("timestamp", ""))),
                })

            logger.debug(
                "Unusual Whales dark pool for %s: %d entries",
                ticker,
                len(results),
            )
            return results[:limit]

        except (UnusualWhalesAuthError, UnusualWhalesRateLimitError):
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch Unusual Whales dark pool for %s: %s",
                ticker,
                exc,
            )
            return []

    async def get_flow_summary(
        self,
        ticker: str = "SPX",
    ) -> dict:
        """Get aggregated flow summary for a ticker.

        Fetches flow and dark pool data, then aggregates into a summary
        with premium breakdowns, sweep/block counts, net sentiment, and
        dark pool volume.

        Args:
            ticker: Underlying ticker (default "SPX").

        Returns:
            Dict with total_premium, call_premium, put_premium, sweep_count,
            block_count, golden_sweep_count, net_sentiment (-1 to 1), and
            dark_pool_volume. Returns zeroed dict if API key not configured
            or on error.
        """
        empty_summary = {
            "total_premium": 0.0,
            "call_premium": 0.0,
            "put_premium": 0.0,
            "sweep_count": 0,
            "block_count": 0,
            "golden_sweep_count": 0,
            "net_sentiment": 0.0,
            "dark_pool_volume": 0,
        }

        if not self._api_key:
            logger.warning(
                "Unusual Whales API key not configured — returning empty flow summary"
            )
            return empty_summary

        try:
            flow_data = await self.get_flow(ticker, limit=500)
            dark_pool_data = await self.get_dark_pool(ticker, limit=100)

            total_premium = 0.0
            call_premium = 0.0
            put_premium = 0.0
            sweep_count = 0
            block_count = 0
            golden_sweep_count = 0
            bullish_count = 0
            bearish_count = 0

            for entry in flow_data:
                premium = entry.get("premium", 0.0)
                total_premium += premium

                opt_type = entry.get("type", "").lower()
                if opt_type == "call":
                    call_premium += premium
                elif opt_type == "put":
                    put_premium += premium

                classification = entry.get("classification", "").lower()
                if classification == "sweep":
                    sweep_count += 1
                elif classification == "block":
                    block_count += 1
                elif classification == "golden_sweep":
                    golden_sweep_count += 1

                sentiment = entry.get("sentiment", "").lower()
                if sentiment == "bullish":
                    bullish_count += 1
                elif sentiment == "bearish":
                    bearish_count += 1

            # Net sentiment: -1 (fully bearish) to 1 (fully bullish)
            total_sentiment = bullish_count + bearish_count
            if total_sentiment > 0:
                net_sentiment = (bullish_count - bearish_count) / total_sentiment
            else:
                net_sentiment = 0.0

            # Dark pool total volume
            dark_pool_volume = sum(
                entry.get("size", 0) for entry in dark_pool_data
            )

            return {
                "total_premium": total_premium,
                "call_premium": call_premium,
                "put_premium": put_premium,
                "sweep_count": sweep_count,
                "block_count": block_count,
                "golden_sweep_count": golden_sweep_count,
                "net_sentiment": net_sentiment,
                "dark_pool_volume": dark_pool_volume,
            }

        except (UnusualWhalesAuthError, UnusualWhalesRateLimitError):
            raise
        except Exception as exc:
            logger.error(
                "Failed to compute Unusual Whales flow summary for %s: %s",
                ticker,
                exc,
            )
            return empty_summary

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.debug("Unusual Whales client session closed")
