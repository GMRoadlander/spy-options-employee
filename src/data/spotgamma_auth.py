"""SpotGamma Playwright-based authentication broker.

Logs into SpotGamma's dashboard using a headless browser and extracts
auth tokens (cookies or JWT) for use with subsequent aiohttp API requests.

Key design decisions:
  - Uses ``playwright.async_api`` for async browser automation.
  - Uses ``playwright_stealth`` to patch browser fingerprints and avoid
    bot-detection heuristics.
  - Persistent browser context saves cookies to disk so that restarts
    don't require a fresh login every time.
  - All login-page selectors are PLACEHOLDERS -- they will be updated on
    Day 1 of the SpotGamma subscription when we can inspect the real page.
  - Gracefully degrades if playwright or playwright-stealth are not
    installed (logs a warning, returns empty headers).

Requires:
  pip install playwright playwright-stealth
  playwright install chromium   # only needed on the machine that runs auth

Environment:
  SPOTGAMMA_EMAIL     -- account email
  SPOTGAMMA_PASSWORD  -- account password
  SPOTGAMMA_ENABLED   -- "true" to activate
  SPOTGAMMA_AUTH_DIR  -- path for persistent browser context (default data/spotgamma_auth)
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Soft-import Playwright so the rest of the system keeps running even when
# the library isn't installed.
# ---------------------------------------------------------------------------

_PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import (  # type: ignore[import-untyped]
        async_playwright,
        Browser,
        BrowserContext,
        Page,
        Playwright,
    )

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None  # type: ignore[assignment,misc]
    Browser = None  # type: ignore[assignment,misc]
    BrowserContext = None  # type: ignore[assignment,misc]
    Page = None  # type: ignore[assignment,misc]
    Playwright = None  # type: ignore[assignment,misc]

_STEALTH_AVAILABLE = False
try:
    from playwright_stealth import stealth_async  # type: ignore[import-untyped]

    _STEALTH_AVAILABLE = True
except ImportError:
    stealth_async = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Constants & placeholder selectors
# ---------------------------------------------------------------------------

_LOGIN_URL = "https://spotgamma.com/login/"
# After login, dashboard.spotgamma.com is the SPA host. The SPA's first
# real route is /home (or /home?eh-model=legacy), NOT /dashboard. We
# match on the host so any post-login URL counts as success. Verified
# live on 2026-04-28.
_DASHBOARD_URL_FRAGMENT = "dashboard.spotgamma.com"

# Login form selectors. Manual login establishes the persistent context;
# subsequent runs reuse it without filling the form. Auto-fill is
# best-effort -- if the live form HTML diverges from these guesses, the
# user is prompted to log in by hand in the visible browser window.
_EMAIL_SELECTOR = 'input[name="email"], input[type="email"], #email'
_PASSWORD_SELECTOR = 'input[name="password"], input[type="password"], #password'
_SUBMIT_SELECTOR = 'button[type="submit"], input[type="submit"], #login-submit'

# Re-authenticate when token is older than this many seconds (4 hours)
_TOKEN_TTL_SECONDS = 4 * 60 * 60

# Timeout for page navigations (ms)
_NAV_TIMEOUT_MS = 30_000


class SpotGammaAuthError(Exception):
    """Raised when authentication with SpotGamma fails."""


class SpotGammaAuthBroker:
    """Browser-based auth broker for SpotGamma.

    Usage::

        broker = SpotGammaAuthBroker(email="...", password="...")
        headers = await broker.get_auth_headers()
        # pass *headers* to aiohttp session
        await broker.close()

    The broker lazily creates the ``auth_dir`` on first authentication so
    that no filesystem side-effects happen at import time.
    """

    def __init__(
        self,
        email: str,
        password: str,
        auth_dir: str = "data/spotgamma_auth",
    ) -> None:
        self._email = email
        self._password = password
        self._auth_dir = Path(auth_dir)

        # Runtime state
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None

        # Cached auth
        self._auth_headers: dict[str, str] = {}
        self._last_auth_time: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_authenticated(self) -> bool:
        """Whether we have a current, non-expired auth token."""
        if not self._auth_headers:
            return False
        elapsed = time.monotonic() - self._last_auth_time
        return elapsed < _TOKEN_TTL_SECONDS

    async def get_auth_headers(self) -> dict[str, str]:
        """Return current valid auth headers, authenticating if needed."""
        return await self.refresh_if_needed()

    async def refresh_if_needed(self) -> dict[str, str]:
        """Re-authenticate only when the current token has expired."""
        if self.is_authenticated:
            return self._auth_headers
        return await self.authenticate()

    async def authenticate(self) -> dict[str, str]:
        """Login to SpotGamma and extract auth headers.

        Returns:
            dict suitable for passing as ``headers`` to aiohttp requests.
            Contains either ``Cookie`` or ``Authorization`` keys depending
            on how SpotGamma issues tokens.

        Raises:
            SpotGammaAuthError: on login failure (wrong credentials,
                page structure change, etc.).
        """
        if not _PLAYWRIGHT_AVAILABLE:
            logger.warning(
                "playwright is not installed -- SpotGamma auth disabled. "
                "Install with: pip install playwright && playwright install chromium"
            )
            return {}

        if not _STEALTH_AVAILABLE:
            logger.warning(
                "playwright-stealth is not installed -- bot detection evasion "
                "will be skipped. Install with: pip install playwright-stealth"
            )

        try:
            await self._ensure_browser()
            page = await self._context.new_page()

            # Apply stealth patches if available
            if _STEALTH_AVAILABLE and stealth_async is not None:
                await stealth_async(page)

            # Strategy 1: try the dashboard first. If the persistent context
            # already holds a valid session (the common steady-state case),
            # sgToken will be in localStorage and we can skip the login form
            # entirely. Verified live on 2026-04-28.
            try:
                await page.goto(
                    f"https://{_DASHBOARD_URL_FRAGMENT}/",
                    timeout=_NAV_TIMEOUT_MS,
                    wait_until="domcontentloaded",
                )
                # Give the SPA a moment to read sgToken from disk into localStorage
                import asyncio as _asyncio
                await _asyncio.sleep(2)
                self._auth_headers = await self._extract_auth(page)
                if self._auth_headers:
                    logger.info("SpotGamma session reused from persistent context")
                    self._last_auth_time = time.monotonic()
                    await page.close()
                    return self._auth_headers
            except Exception as exc:
                logger.debug("Dashboard probe failed (%s) -- falling back to login form", exc)

            # Strategy 2: no live session -- fill the login form. Selectors
            # are best-effort; if they don't match, the user must log in
            # manually once via scripts/spotgamma_recon.py to seed the
            # persistent context. Subsequent runs will hit Strategy 1.
            await page.goto(_LOGIN_URL, timeout=_NAV_TIMEOUT_MS, wait_until="domcontentloaded")

            await page.fill(_EMAIL_SELECTOR, self._email)
            await page.fill(_PASSWORD_SELECTOR, self._password)
            await page.click(_SUBMIT_SELECTOR)

            try:
                await page.wait_for_url(
                    f"**{_DASHBOARD_URL_FRAGMENT}*",
                    timeout=_NAV_TIMEOUT_MS,
                )
            except Exception as exc:
                raise SpotGammaAuthError(
                    f"Login failed -- did not redirect to dashboard. "
                    f"Current URL: {page.url}. "
                    f"If selectors changed, log in manually once via "
                    f"scripts/spotgamma_recon.py to seed the persistent context."
                ) from exc

            self._auth_headers = await self._extract_auth(page)
            self._last_auth_time = time.monotonic()

            await page.close()

            if self._auth_headers:
                logger.info("SpotGamma authentication successful")
            else:
                logger.warning(
                    "SpotGamma login appeared to succeed (dashboard redirect) "
                    "but no auth tokens were found in cookies or localStorage"
                )

            return self._auth_headers

        except SpotGammaAuthError:
            raise
        except Exception as exc:
            logger.error("SpotGamma authentication error: %s", exc, exc_info=True)
            return {}

    async def close(self) -> None:
        """Clean up browser context and Playwright instance."""
        if self._context is not None:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _ensure_browser(self) -> None:
        """Launch (or reuse) a headless Chromium with persistent context."""
        if self._context is not None:
            return

        # Lazy-create auth dir
        self._auth_dir.mkdir(parents=True, exist_ok=True)

        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self._auth_dir),
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        logger.debug("SpotGamma browser context launched (auth_dir=%s)", self._auth_dir)

    async def _extract_auth(self, page: Any) -> dict[str, str]:
        """Extract auth credentials from localStorage (preferred) or cookies.

        Strategy 1 (preferred): JWT from localStorage key 'sgToken'.
        Verified live on 2026-04-28: the SpotGamma Alpha SPA stores its
        Bearer JWT in localStorage under the key 'sgToken' (camelCase,
        ~632 chars). Other keys checked as fallbacks in case SpotGamma
        renames in future. Returns ``Authorization: Bearer <token>``.

        Strategy 2 (fallback): Session cookies. Used only if no JWT
        is found in localStorage. Returns ``Cookie: name=value; ...``.

        Returns a headers dict ready for aiohttp.
        """
        headers: dict[str, str] = {}

        # Strategy 1: JWT from localStorage. 'sgToken' is the actual
        # key SpotGamma's dashboard SPA uses; the others are defensive
        # fallbacks in case of future renames.
        for key in ("sgToken", "token", "jwt", "auth_token", "access_token", "sg_token"):
            try:
                token = await page.evaluate(f"localStorage.getItem('{key}')")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    logger.debug("Found JWT in localStorage key '%s'", key)
                    return headers
            except Exception:
                continue

        # Strategy 2: cookies (fallback only).
        cookies = await self._context.cookies(_LOGIN_URL.rstrip("/"))
        if cookies:
            cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
            headers["Cookie"] = cookie_str
            logger.debug("Built Cookie header from %d cookies", len(cookies))

        return headers


__all__ = ["SpotGammaAuthBroker", "SpotGammaAuthError"]
