"""Polygon.io API client for options data.

Provides REST endpoints for options chain snapshots, individual trades,
OHLCV aggregates, and news articles. Follows the same async aiohttp
pattern established by ORATSClient.

REST endpoints:
  - /v3/snapshot/options/{underlying} — options chain snapshots
  - /v3/trades/{options_ticker} — individual option trades
  - /v2/aggs/ticker/{ticker}/range/... — OHLCV bars
  - /v2/reference/news — news articles

Rate limits (free tier):
  - 5 requests per minute (configurable via POLYGON_RATE_LIMIT)

Requires:
  pip install aiohttp

Environment:
  POLYGON_API_KEY — API key from polygon.io account
  POLYGON_RATE_LIMIT — requests per minute (default 5)
"""

import asyncio
import logging
import time
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class PolygonRateLimitError(Exception):
    """Raised when Polygon.io rate limits are exceeded."""


class PolygonAuthError(Exception):
    """Raised when Polygon.io returns 401 (invalid API key)."""


class PolygonClient:
    """Async REST client for the Polygon.io API.

    Usage:
        client = PolygonClient(api_key="...")
        chain = await client.get_options_chain("SPY")
        await client.close()
    """

    BASE_URL = "https://api.polygon.io"

    def __init__(
        self,
        api_key: str,
        requests_per_minute: int = 5,
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
            PolygonRateLimitError: If per-minute limit is exceeded.
        """
        now = time.time()

        # Clean up old minute-window entries
        cutoff = now - 60.0
        self._minute_requests = [t for t in self._minute_requests if t > cutoff]

        # Check per-minute limit
        if len(self._minute_requests) >= self._requests_per_minute:
            wait_time = 60.0 - (now - self._minute_requests[0])
            raise PolygonRateLimitError(
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
        """Make an authenticated GET request to the Polygon.io API.

        Args:
            endpoint: API endpoint path (e.g., "/v3/snapshot/options/SPY").
            params: Additional query parameters.

        Returns:
            Parsed JSON response as a dict.

        Raises:
            PolygonAuthError: On 401 (invalid API key).
            PolygonRateLimitError: On 429 or if local rate limit is exceeded.
            asyncio.TimeoutError: On request timeout.
            aiohttp.ClientError: On network errors.
            ValueError: On unexpected non-200 responses.
        """
        self._check_rate_limit()

        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"

        # Auth via query param
        query_params: dict[str, Any] = {"apiKey": self._api_key}
        if params:
            query_params.update(params)

        logger.debug(
            "Polygon request: GET %s params=%s",
            endpoint,
            {k: v for k, v in query_params.items() if k != "apiKey"},
        )

        try:
            async with session.get(
                url, params=query_params, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                self._record_request()

                if resp.status == 401:
                    raise PolygonAuthError(
                        "Polygon.io API returned 401: invalid or missing API key"
                    )

                if resp.status == 429:
                    raise PolygonRateLimitError(
                        "Polygon.io API returned 429: rate limit exceeded"
                    )

                if resp.status != 200:
                    text = await resp.text()
                    raise ValueError(
                        f"Polygon.io API error {resp.status}: {text[:200]}"
                    )

                data = await resp.json()
                return data

        except asyncio.TimeoutError:
            logger.error("Polygon.io request timed out: %s", endpoint)
            raise

    async def get_options_chain(
        self,
        underlying: str,
        expiration_date: str | None = None,
        limit: int = 250,
    ) -> list[dict]:
        """Fetch options chain snapshots for an underlying.

        Args:
            underlying: Underlying ticker (e.g., "SPY", "SPX").
            expiration_date: Optional filter by expiration (YYYY-MM-DD).
            limit: Max results per page (default 250).

        Returns:
            List of option snapshot dicts with greeks, IV, volume, OI.
            Empty list on error or if API key is not configured.
        """
        if not self._api_key:
            logger.warning(
                "Polygon API key not configured — returning empty options chain"
            )
            return []

        underlying = underlying.upper()
        all_results: list[dict] = []

        params: dict[str, Any] = {"limit": limit}
        if expiration_date:
            params["expiration_date"] = expiration_date

        try:
            # First page
            data = await self._request(
                f"/v3/snapshot/options/{underlying}", params=params
            )
            results = data.get("results", [])
            all_results.extend(results)

            # Handle pagination via next_url
            next_url = data.get("next_url")
            while next_url:
                # next_url is a full URL; extract endpoint + params
                # Polygon next_url already includes apiKey, so we request directly
                self._check_rate_limit()
                session = await self._get_session()

                # Add apiKey if not present in next_url
                separator = "&" if "?" in next_url else "?"
                if "apiKey=" not in next_url:
                    next_url = f"{next_url}{separator}apiKey={self._api_key}"

                async with session.get(
                    next_url, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    self._record_request()
                    if resp.status != 200:
                        break
                    page_data = await resp.json()
                    page_results = page_data.get("results", [])
                    all_results.extend(page_results)
                    next_url = page_data.get("next_url")

            logger.debug(
                "Polygon options chain for %s: %d snapshots",
                underlying,
                len(all_results),
            )
            return all_results

        except (PolygonAuthError, PolygonRateLimitError):
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch Polygon options chain for %s: %s",
                underlying,
                exc,
            )
            return []

    async def get_option_trades(
        self,
        options_ticker: str,
        date: str,
        limit: int = 1000,
    ) -> list[dict]:
        """Fetch individual option trades for sweep/block detection.

        Args:
            options_ticker: OCC-style options ticker (e.g., "O:SPY251219C00600000").
            date: Trade date (YYYY-MM-DD).
            limit: Max results (default 1000).

        Returns:
            List of trade dicts with price, size, exchange, conditions, timestamp.
            Empty list on error or if API key is not configured.
        """
        if not self._api_key:
            logger.warning(
                "Polygon API key not configured — returning empty trades"
            )
            return []

        try:
            data = await self._request(
                f"/v3/trades/{options_ticker}",
                params={"timestamp": date, "limit": limit},
            )
            results = data.get("results", [])
            logger.debug(
                "Polygon trades for %s on %s: %d trades",
                options_ticker,
                date,
                len(results),
            )
            return results

        except (PolygonAuthError, PolygonRateLimitError):
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch Polygon trades for %s on %s: %s",
                options_ticker,
                date,
                exc,
            )
            return []

    async def get_option_aggregates(
        self,
        options_ticker: str,
        timespan: str = "day",
        from_date: str = "",
        to_date: str = "",
        limit: int = 120,
    ) -> list[dict]:
        """Fetch OHLCV aggregate bars for an option.

        Args:
            options_ticker: OCC-style options ticker.
            timespan: Bar timespan ("minute", "hour", "day", "week", "month").
            from_date: Start date (YYYY-MM-DD).
            to_date: End date (YYYY-MM-DD).
            limit: Max results (default 120).

        Returns:
            List of OHLCV bar dicts.
            Empty list on error or if API key is not configured.
        """
        if not self._api_key:
            logger.warning(
                "Polygon API key not configured — returning empty aggregates"
            )
            return []

        try:
            endpoint = (
                f"/v2/aggs/ticker/{options_ticker}/range/1/{timespan}"
                f"/{from_date}/{to_date}"
            )
            data = await self._request(endpoint, params={"limit": limit})
            results = data.get("results", [])
            logger.debug(
                "Polygon aggregates for %s (%s): %d bars",
                options_ticker,
                timespan,
                len(results),
            )
            return results

        except (PolygonAuthError, PolygonRateLimitError):
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch Polygon aggregates for %s: %s",
                options_ticker,
                exc,
            )
            return []

    async def get_news(
        self,
        ticker: str = "SPX",
        limit: int = 50,
    ) -> list[dict]:
        """Fetch news articles for a ticker.

        Used by the sentiment pipeline (Plan 04) to feed FinBERT.

        Args:
            ticker: Ticker to search for in news (default "SPX").
            limit: Max articles to return (default 50).

        Returns:
            List of news article dicts with title, published_utc, source, url.
            Empty list on error or if API key is not configured.
        """
        if not self._api_key:
            logger.warning(
                "Polygon API key not configured — returning empty news"
            )
            return []

        try:
            data = await self._request(
                "/v2/reference/news",
                params={"ticker": ticker.upper(), "limit": limit},
            )
            results = data.get("results", [])
            logger.debug(
                "Polygon news for %s: %d articles",
                ticker,
                len(results),
            )
            return results

        except (PolygonAuthError, PolygonRateLimitError):
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch Polygon news for %s: %s", ticker, exc
            )
            return []

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.debug("Polygon client session closed")
