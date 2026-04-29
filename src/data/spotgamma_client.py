"""SpotGamma API client for GEX levels and flow data.

Direct HTTP client against api.spotgamma.com (Alpha tier). Uses
SpotGammaAuthBroker for JWT extraction (Authorization: Bearer <sgToken>)
and fetches dealer positioning data: per-equity gamma data, HIRO,
user profile.

Endpoints discovered via dashboard recon on 2026-04-28 (Premier/Alpha):
  - /v3/equitiesBySyms?syms=SPX  -> Call Wall (cws), Put Wall (pws),
    Abs Gamma (keyg), Max Future Strike (maxfs), per-strike gamma
    curves, IV rank, sig (1d implied move), ~90 fields total
  - /v6/running_hiro             -> 401-symbol HIRO snapshot with
    low/high bands across 1/5/20-day windows
  - /v1/me/user                  -> account profile (sanity check)
  - /v1/me/refresh               -> JWT refresh

Endpoints captured in recon but currently 403 from raw aiohttp (likely
TLS fingerprint or signed-header gating; SPA can call them, we cannot
yet -- /v3/equitiesBySyms covers their data anyway):
  - /home/keyLevels
  - /v1/eh_symbols and /synth_oi/v1/eh_symbols
  - /v1/futures/realtime

Rate limits: 30 req/min default (real API, not scraping). Jitter
disabled by default since this is an authenticated API call, not
dashboard scraping.

Auth: JWT via SpotGammaAuthBroker. Token sourced from localStorage
'sgToken' key in the persistent Playwright context.
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

    Endpoint paths verified live on 2026-04-28 against the Alpha tier
    via dashboard network reconnaissance (see scripts/spotgamma_recon.py
    and scripts/spotgamma_auth_probe.py).
    """

    BASE_URL = "https://api.spotgamma.com"

    def __init__(
        self,
        auth_broker: SpotGammaAuthBroker,
        session: aiohttp.ClientSession | None = None,
        requests_per_minute: int = 30,
        max_jitter_seconds: float = 0.0,
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
        """Fetch key GEX levels via /v3/equitiesBySyms.

        The /home/keyLevels endpoint returns 403 to raw aiohttp; the
        equivalent (and richer) data lives in /v3/equitiesBySyms which
        accepts comma-separated symbols and returns ~90 fields per symbol
        including cws (Call Wall), pws (Put Wall), keyg (Abs Gamma),
        maxfs (Max Future Strike), full per-strike gamma curves, IV rank,
        sig (1d implied move), and prev-day comparisons.

        Caller maps fields via spotgamma_models.parse_levels_from_v3().

        Args:
            ticker: Underlying ticker (default "SPX").

        Returns:
            Raw JSON dict {ticker_upper: {...90 fields...}, ...} or None on error.
        """
        sym = ticker.upper()
        return await self._request("GET", f"/v3/equitiesBySyms?syms={sym}")

    async def get_hiro(self, ticker: str = "SPX") -> dict | None:
        """Fetch HIRO snapshot via /v6/running_hiro.

        Returns ALL ~401 symbols in one response (147KB). Caller filters
        for the ticker of interest. Each row has low/high bands across
        1/5/20-day windows: low1, high1, low5, high5, low20, high20.

        Args:
            ticker: Underlying ticker (default "SPX") -- used only to
                filter the response client-side; not sent to the server.

        Returns:
            Raw JSON list of all symbols, or None on error. Caller filters.
        """
        # The server returns ALL symbols regardless of ticker arg.
        # We pass through; the caller is responsible for filtering.
        _ = ticker  # documented intent: ticker filter happens at caller
        return await self._request("GET", "/v6/running_hiro")

    async def get_equity_hub(self, ticker: str = "SPX") -> dict | None:
        """Fetch Equity Hub data via /v3/equitiesBySyms.

        Same endpoint as get_levels() -- the v3/equitiesBySyms response
        IS the Equity Hub data for a single symbol. Multi-symbol calls
        accept comma-separated `syms` (e.g. ?syms=SPY,AAPL,SPX).

        Args:
            ticker: Underlying ticker or comma-separated list.

        Returns:
            Raw JSON dict keyed by symbol, or None on error.
        """
        return await self._request("GET", f"/v3/equitiesBySyms?syms={ticker.upper()}")

    async def get_user(self) -> dict | None:
        """Fetch authenticated user profile via /v1/me/user.

        Useful as a sanity check / token-validity probe -- if this 401s,
        the JWT is expired and the auth broker should re-authenticate.

        Returns:
            Raw JSON dict with account fields, or None on error.
        """
        return await self._request("GET", "/v1/me/user")

    async def get_trace(self) -> dict | None:
        """TRACE heatmap is a canvas/WebGL visualization, no JSON endpoint.

        Returns None unconditionally. Kept for API compatibility with
        existing callers and tests; SpotGamma does not expose TRACE
        data programmatically.
        """
        logger.debug("get_trace() called -- TRACE is dashboard-only, returning None")
        return None

    async def get_notes(self) -> dict | None:
        """Founder's Notes are not exposed via the API surface we found.

        The /home/contentForCategory endpoint exists but returns
        glossary/tooltip content, not Founder's Notes. Notes appear to
        be web-rendered prose at spotgamma.com (subscriber-gated). Kept
        as a stub for API compatibility.
        """
        logger.debug("get_notes() called -- no API endpoint found, returning None")
        return None

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
