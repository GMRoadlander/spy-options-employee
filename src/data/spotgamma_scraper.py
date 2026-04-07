"""SpotGamma Playwright-based fallback scraper.

Navigates SpotGamma's dashboard pages using a headless browser and
extracts data from the rendered DOM.  This is the *fallback* path --
used only when direct API calls fail.

Key design decisions:
  - Reuses the auth broker's browser context (no second browser).
  - All DOM selectors are PLACEHOLDERS -- they will be updated on Day 1
    of the SpotGamma subscription when we can inspect the real pages.
  - Results are cached with a 5-minute TTL to avoid hammering pages.
  - Returns ``None`` on any failure (graceful degradation).
  - Soft-imports playwright so the rest of the system works when the
    library isn't installed.

Requires:
  pip install playwright playwright-stealth
  playwright install chromium
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Soft-import Playwright -- all methods return None if missing
# ---------------------------------------------------------------------------

_PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import Page  # type: ignore[import-untyped]

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    Page = None  # type: ignore[assignment,misc]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LEVELS_URL = "https://spotgamma.com/dashboard/levels/"
_HIRO_URL = "https://spotgamma.com/dashboard/hiro/"

# Timeout for page navigation (ms)
_NAV_TIMEOUT_MS = 30_000

# Default cache TTL (seconds)
_DEFAULT_CACHE_TTL = 300  # 5 minutes


class SpotGammaScraper:
    """Fallback scraper using Playwright to extract data from SpotGamma's dashboard.

    Used only when direct API calls fail. Requires an authenticated
    :class:`~src.data.spotgamma_auth.SpotGammaAuthBroker` for login.
    """

    def __init__(self, auth_broker: Any) -> None:
        from src.data.spotgamma_auth import SpotGammaAuthBroker  # local to avoid circular

        if not isinstance(auth_broker, SpotGammaAuthBroker):
            raise TypeError(
                f"auth_broker must be a SpotGammaAuthBroker, got {type(auth_broker).__name__}"
            )
        self._auth = auth_broker
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl = _DEFAULT_CACHE_TTL

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_levels(self, ticker: str = "SPX") -> Any:
        """Navigate to key levels page and extract from rendered DOM.

        Uses cache to minimise page loads.  All selectors are
        PLACEHOLDERS for Day 1.

        Returns:
            :class:`SpotGammaLevels` or ``None`` on failure.
        """
        if not _PLAYWRIGHT_AVAILABLE:
            logger.warning(
                "playwright not installed -- SpotGamma scraper disabled"
            )
            return None

        cache_key = f"levels:{ticker}"
        return await self._navigate_and_extract(
            url=_LEVELS_URL,
            cache_key=cache_key,
            extractor=lambda page: self._extract_levels(page, ticker),
        )

    async def get_hiro(self, ticker: str = "SPX") -> Any:
        """Navigate to HIRO page and extract current reading.

        All selectors are PLACEHOLDERS for Day 1.

        Returns:
            :class:`SpotGammaHIRO` or ``None`` on failure.
        """
        if not _PLAYWRIGHT_AVAILABLE:
            logger.warning(
                "playwright not installed -- SpotGamma scraper disabled"
            )
            return None

        cache_key = f"hiro:{ticker}"
        return await self._navigate_and_extract(
            url=_HIRO_URL,
            cache_key=cache_key,
            extractor=lambda page: self._extract_hiro(page, ticker),
        )

    async def close(self) -> None:
        """Clear cache.  Does NOT close the auth broker (caller owns it)."""
        self._cache.clear()

    # ------------------------------------------------------------------
    # Core navigation
    # ------------------------------------------------------------------

    async def _navigate_and_extract(
        self,
        url: str,
        cache_key: str,
        extractor: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        """Navigate to *url*, wait for content, extract with *extractor*.

        - Uses the auth broker's browser context (no second browser).
        - Waits for ``networkidle`` to let React hydrate.
        - Returns extracted data or ``None`` on failure.
        - Implements TTL cache by *cache_key*.
        """
        # Check cache first
        if self._is_cached(cache_key):
            logger.debug("Cache hit for %s", cache_key)
            return self._cache[cache_key][1]

        # Ensure the auth broker has a browser context ready
        if self._auth._context is None:
            logger.warning(
                "SpotGamma auth broker has no browser context -- "
                "call authenticate() first"
            )
            return None

        page: Any = None
        try:
            page = await self._auth._context.new_page()
            await page.goto(url, timeout=_NAV_TIMEOUT_MS, wait_until="networkidle")

            result = await extractor(page)
            if result is not None:
                self._cache[cache_key] = (time.monotonic(), result)
                logger.info("Scraped %s successfully", cache_key)
            return result

        except Exception as exc:
            logger.warning("SpotGamma scrape failed for %s: %s", cache_key, exc)
            return None

        finally:
            if page is not None:
                try:
                    await page.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _is_cached(self, key: str) -> bool:
        """Return ``True`` if *key* exists in cache and has not expired."""
        if key not in self._cache:
            return False
        cached_time, _ = self._cache[key]
        return (time.monotonic() - cached_time) < self._cache_ttl

    # ------------------------------------------------------------------
    # DOM extractors -- PLACEHOLDERS for Day 1
    # ------------------------------------------------------------------

    async def _extract_levels(self, page: Any, ticker: str) -> Any:
        """Extract key levels from the DOM.

        PLACEHOLDER: all selectors are TBD Day 1.  This skeleton returns
        ``None`` until real selectors are wired up.
        """
        from src.data.spotgamma_models import SpotGammaLevels

        try:
            # PLACEHOLDER: selector TBD Day 1
            # Example of what real extraction might look like:
            #   call_wall = await page.text_content(".call-wall-value")
            #   put_wall  = await page.text_content(".put-wall-value")
            #   ...
            # For now, return None to signal "not yet implemented"
            logger.debug(
                "SpotGamma levels extraction is a placeholder -- "
                "selectors TBD Day 1 (ticker=%s)",
                ticker,
            )
            return None
        except Exception as exc:
            logger.warning("Failed to extract SpotGamma levels: %s", exc)
            return None

    async def _extract_hiro(self, page: Any, ticker: str) -> Any:
        """Extract HIRO reading from the DOM.

        PLACEHOLDER: all selectors are TBD Day 1.  This skeleton returns
        ``None`` until real selectors are wired up.
        """
        from src.data.spotgamma_models import SpotGammaHIRO

        try:
            # PLACEHOLDER: selector TBD Day 1
            # Example of what real extraction might look like:
            #   impact = await page.text_content(".hiro-impact-value")
            #   cumulative = await page.text_content(".hiro-cumulative-value")
            #   ...
            # For now, return None to signal "not yet implemented"
            logger.debug(
                "SpotGamma HIRO extraction is a placeholder -- "
                "selectors TBD Day 1 (ticker=%s)",
                ticker,
            )
            return None
        except Exception as exc:
            logger.warning("Failed to extract SpotGamma HIRO: %s", exc)
            return None


__all__ = ["SpotGammaScraper"]
