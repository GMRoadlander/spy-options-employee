"""News client for fetching financial headlines from Polygon.io.

Provides headline data for sentiment scoring.  Falls back gracefully
when no API key is configured — returns an empty list with a warning.

Rate limits:
  - 5 requests per minute (Polygon.io free tier)

Requires:
  pip install aiohttp

Environment:
  POLYGON_API_KEY -- API key from polygon.io account
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class NewsClient:
    """Async client for fetching financial news headlines.

    Currently supports Polygon.io as the news source.  When no API key
    is provided, all fetches return an empty list with a log warning.

    Args:
        polygon_api_key: Polygon.io API key.  Empty string disables
            fetching.
        session: Optional shared :class:`aiohttp.ClientSession`.
    """

    POLYGON_BASE_URL = "https://api.polygon.io/v2/reference/news"

    # Polygon free tier: 5 requests per minute.
    _RATE_LIMIT_PER_MINUTE = 5

    def __init__(
        self,
        polygon_api_key: str = "",
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._polygon_api_key = polygon_api_key
        self._session = session
        self._owns_session = session is None

        # Rate limit tracking (timestamps of recent requests).
        self._request_times: list[float] = []

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    def _check_rate_limit(self) -> None:
        """Enforce per-minute rate limit.

        Raises:
            RuntimeError: If the rate limit has been exceeded.
        """
        now = time.time()
        cutoff = now - 60.0
        self._request_times = [t for t in self._request_times if t > cutoff]

        if len(self._request_times) >= self._RATE_LIMIT_PER_MINUTE:
            wait_time = 60.0 - (now - self._request_times[0])
            raise RuntimeError(
                f"News API rate limit exceeded ({self._RATE_LIMIT_PER_MINUTE}/min). "
                f"Try again in {wait_time:.1f}s."
            )

    def _record_request(self) -> None:
        """Record a request timestamp for rate limiting."""
        self._request_times.append(time.time())

    async def fetch_headlines(
        self,
        ticker: str = "SPX",
        limit: int = 50,
    ) -> list[dict[str, str]]:
        """Fetch recent news headlines for a ticker.

        Args:
            ticker: Ticker symbol to search for.
            limit: Maximum number of headlines to return.

        Returns:
            List of dicts with keys ``title``, ``published``, ``source``,
            ``url``.  Returns an empty list if no API key is configured
            or on any error.
        """
        if not self._polygon_api_key:
            logger.warning(
                "No Polygon API key configured — sentiment scoring unavailable. "
                "Set POLYGON_API_KEY to enable news fetching."
            )
            return []

        self._check_rate_limit()

        # Polygon uses standard ticker symbols; map SPX → SPY for broader
        # coverage since SPX headlines are sparse.
        search_ticker = ticker if ticker != "SPX" else "SPY"

        params: dict[str, Any] = {
            "ticker": search_ticker,
            "limit": str(limit),
            "order": "desc",
            "sort": "published_utc",
            "apiKey": self._polygon_api_key,
        }

        try:
            session = await self._get_session()
            async with session.get(self.POLYGON_BASE_URL, params=params) as resp:
                self._record_request()

                if resp.status == 429:
                    logger.warning("Polygon news API returned 429 — rate limited")
                    return []

                if resp.status != 200:
                    text = await resp.text()
                    logger.error(
                        "Polygon news API error %d: %s", resp.status, text[:200]
                    )
                    return []

                data = await resp.json()

            results = data.get("results", [])
            headlines: list[dict[str, str]] = []

            for article in results:
                title = article.get("title", "").strip()
                if not title:
                    continue
                headlines.append({
                    "title": title,
                    "published": article.get("published_utc", ""),
                    "source": article.get("publisher", {}).get("name", "unknown"),
                    "url": article.get("article_url", ""),
                })

            logger.info(
                "Fetched %d headlines for %s from Polygon", len(headlines), ticker
            )
            return headlines

        except RuntimeError:
            # Re-raise rate limit errors.
            raise
        except Exception as exc:
            logger.error("Failed to fetch news for %s: %s", ticker, exc)
            return []

    async def close(self) -> None:
        """Close the aiohttp session if we own it."""
        if self._session is not None and self._owns_session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.debug("News client session closed")
