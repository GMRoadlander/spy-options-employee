"""SpotGamma dashboard API client for GEX levels and flow data.

Direct HTTP client that uses SpotGammaAuthBroker for authentication and
fetches key dealer positioning data: GEX levels, HIRO indicator, Equity
Hub, TRACE heatmap, and Founder's Notes.

Follows the same async aiohttp pattern established by ORATSClient and
PolygonClient, with additional anti-detection measures (jitter, browser
User-Agent) since this scrapes a dashboard rather than hitting an
official API.

Key data:
  - Levels: Call Wall, Put Wall, Vol Trigger, Gamma Flip, etc.
  - HIRO: Hedging Impact & Real-time Options indicator
  - Equity Hub: support/resistance levels from dealer positioning
  - TRACE: institutional flow heatmap
  - Notes: Founder's Notes daily commentary

Rate limits:
  - 10 requests per minute (conservative default — dashboard, not API)

Anti-detection:
  - Randomized jitter (0-30s) before each request (configurable)
  - Realistic browser User-Agent header
  - Auth via browser-extracted cookies/JWT (see spotgamma_auth.py)

Requires:
  pip install aiohttp

Environment:
  SPOTGAMMA_EMAIL    -- account email (used by auth broker)
  SPOTGAMMA_PASSWORD -- account password (used by auth broker)
  SPOTGAMMA_ENABLED  -- "true" to activate

NOTE: All endpoint paths are PLACEHOLDERS — they will be updated on
Day 1 of the SpotGamma subscription when we can inspect real traffic.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

import aiohttp

from src.data.spotgamma_auth import SpotGammaAuthBroker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Realistic browser User-Agent for anti-detection
# ---------------------------------------------------------------------------

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class SpotGammaError(Exception):
    """Base error for SpotGamma client operations."""


class SpotGammaAuthError(SpotGammaError):
    """Raised when SpotGamma returns 401 or auth headers are invalid."""


class SpotGammaRateLimitError(SpotGammaError):
    """Raised when SpotGamma rate limits are exceeded (local or server 429)."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class SpotGammaClient:
    """Async HTTP client for the SpotGamma dashboard.

    Usage::

        auth_broker = SpotGammaAuthBroker(email="...", password="...")
        client = SpotGammaClient(auth_broker)
        levels = await client.get_levels("SPX")
        await client.close()

    All endpoint paths are **placeholders** — update on Day 1 when we can
    inspect real network traffic from the SpotGamma dashboard.
    """

    BASE_URL = "https://dashboard.spotgamma.com"

    def __init__(
        self,
        auth_broker: SpotGammaAuthBroker,
        session: aiohttp.ClientSession | None = None,
        requests_per_minute: int = 10,
        max_jitter_seconds: float = 30.0,
    ) -> None:
        self._auth_broker = auth_broker
        self._session = session
        self._owns_session = session is None
        self._requests_per_minute = requests_per_minute
        self._max_jitter_seconds = max_jitter_seconds
        self._minute_requests: list[float] = []

    # ------------------------------------------------------------------
    # Public endpoint methods
    # ------------------------------------------------------------------

    async def get_levels(self, ticker: str = "SPX") -> dict | None:
        """Fetch key GEX levels (Call Wall, Put Wall, Vol Trigger, etc.).

        Returns raw JSON dict. Parsing to SpotGammaLevels happens in the
        caller/store layer.

        Endpoint path is a PLACEHOLDER — update on Day 1.

        Args:
            ticker: Underlying ticker (default "SPX").

        Returns:
            Raw JSON dict or None on error.
        """
        # PLACEHOLDER endpoint — update on Day 1
        return await self._request("GET", f"/api/levels/{ticker.upper()}")

    async def get_hiro(self, ticker: str = "SPX") -> dict | None:
        """Fetch HIRO (Hedging Impact & Real-time Options) indicator data.

        Endpoint path is a PLACEHOLDER — update on Day 1.

        Args:
            ticker: Underlying ticker (default "SPX").

        Returns:
            Raw JSON dict or None on error.
        """
        # PLACEHOLDER endpoint — update on Day 1
        return await self._request("GET", f"/api/hiro/{ticker.upper()}")

    async def get_equity_hub(self, ticker: str = "SPX") -> dict | None:
        """Fetch Equity Hub levels for a ticker.

        Endpoint path is a PLACEHOLDER — update on Day 1.

        Args:
            ticker: Underlying ticker (default "SPX").

        Returns:
            Raw JSON dict or None on error.
        """
        # PLACEHOLDER endpoint — update on Day 1
        return await self._request("GET", f"/api/equity-hub/{ticker.upper()}")

    async def get_trace(self) -> dict | None:
        """Fetch TRACE heatmap data.

        Endpoint path is a PLACEHOLDER — update on Day 1.

        Returns:
            Raw JSON dict or None on error.
        """
        # PLACEHOLDER endpoint — update on Day 1
        return await self._request("GET", "/api/trace")

    async def get_notes(self) -> dict | None:
        """Fetch latest Founder's Notes.

        Endpoint path is a PLACEHOLDER — update on Day 1.

        Returns:
            Raw JSON dict or None on error.
        """
        # PLACEHOLDER endpoint — update on Day 1
        return await self._request("GET", "/api/notes")

    # ------------------------------------------------------------------
    # Core request method
    # ------------------------------------------------------------------

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict | None:
        """Core request method with rate limiting, auth, jitter, and error handling.

        Flow:
          1. Check local rate limit
          2. Apply randomized jitter (anti-detection)
          3. Get auth headers from broker
          4. Make request with browser-like User-Agent
          5. On 401: trigger re-auth via broker, retry once
          6. On 429: raise SpotGammaRateLimitError
          7. On other errors: log warning, return None (graceful degradation)

        Args:
            method: HTTP method (GET, POST, etc.).
            path: URL path relative to BASE_URL.
            **kwargs: Extra keyword args passed to aiohttp request.

        Returns:
            Parsed JSON dict, or None on non-critical errors.

        Raises:
            SpotGammaRateLimitError: On 429 or local rate limit exceeded.
        """
        self._check_rate_limit()

        # Anti-detection jitter
        if self._max_jitter_seconds > 0:
            jitter = random.uniform(0, self._max_jitter_seconds)
            await asyncio.sleep(jitter)

        return await self._do_request(method, path, retry_auth=True, **kwargs)

    async def _do_request(
        self,
        method: str,
        path: str,
        *,
        retry_auth: bool = True,
        **kwargs: Any,
    ) -> dict | None:
        """Execute the actual HTTP request (inner method for retry logic).

        Args:
            method: HTTP method.
            path: URL path.
            retry_auth: If True and we get 401, re-authenticate and retry once.
            **kwargs: Extra args for the aiohttp request.

        Returns:
            Parsed JSON dict, or None on non-critical errors.
        """
        session = await self._get_session()
        url = f"{self.BASE_URL}{path}"

        # Build headers: auth + browser UA
        auth_headers = await self._auth_broker.get_auth_headers()
        headers = {
            "User-Agent": _USER_AGENT,
            **auth_headers,
        }

        logger.debug("SpotGamma request: %s %s", method, path)

        try:
            async with session.request(
                method,
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
                **kwargs,
            ) as resp:
                self._record_request()

                if resp.status == 401:
                    if retry_auth:
                        logger.info(
                            "SpotGamma 401 — triggering re-auth and retrying"
                        )
                        await self._auth_broker.authenticate()
                        return await self._do_request(
                            method, path, retry_auth=False, **kwargs
                        )
                    raise SpotGammaAuthError(
                        "SpotGamma returned 401 after re-authentication"
                    )

                if resp.status == 429:
                    raise SpotGammaRateLimitError(
                        "SpotGamma returned 429: rate limit exceeded"
                    )

                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(
                        "SpotGamma %s %s returned %d: %s",
                        method,
                        path,
                        resp.status,
                        text[:200],
                    )
                    return None

                data = await resp.json()
                return data

        except (SpotGammaAuthError, SpotGammaRateLimitError):
            raise
        except asyncio.TimeoutError:
            logger.warning("SpotGamma request timed out: %s %s", method, path)
            return None
        except aiohttp.ClientError as exc:
            logger.warning(
                "SpotGamma network error for %s %s: %s", method, path, exc
            )
            return None
        except Exception as exc:
            logger.warning(
                "SpotGamma unexpected error for %s %s: %s", method, path, exc
            )
            return None

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limits before making a request.

        Raises:
            SpotGammaRateLimitError: If per-minute limit is exceeded.
        """
        now = time.time()

        # Clean up old minute-window entries
        cutoff = now - 60.0
        self._minute_requests = [t for t in self._minute_requests if t > cutoff]

        # Check per-minute limit
        if len(self._minute_requests) >= self._requests_per_minute:
            wait_time = 60.0 - (now - self._minute_requests[0])
            raise SpotGammaRateLimitError(
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

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session (lazy init)."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session if we own it."""
        if self._session is not None and self._owns_session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.debug("SpotGamma client session closed")


__all__ = [
    "SpotGammaClient",
    "SpotGammaError",
    "SpotGammaAuthError",
    "SpotGammaRateLimitError",
]
