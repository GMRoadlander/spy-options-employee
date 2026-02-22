"""Data manager that orchestrates options chain fetching with fallback and caching.

Strategy:
  1. Try Tastytrade first (real-time, if credentials configured)
  2. Fall back to CBOE CDN (free, no auth required)
  3. If CBOE fails, fall back to Tradier sandbox API
  4. Cache results with configurable TTL to avoid hammering APIs
"""

import logging
import time
from dataclasses import dataclass, field

from src.config import config
from src.data import OptionsChain
from src.data.cboe_client import CBOEClient
from src.data.tastytrade_client import TastytradeClient
from src.data.tradier_client import TradierClient

logger = logging.getLogger(__name__)


@dataclass
class _CacheEntry:
    """Internal cache entry with TTL tracking."""
    chain: OptionsChain
    fetched_at: float  # time.monotonic() value
    source: str


class DataManager:
    """Orchestrates options data fetching with fallback and caching.

    Usage:
        manager = DataManager()
        chain = await manager.get_chain("SPY")
        all_chains = await manager.get_all_chains()
        await manager.close()

    Or as an async context manager:
        async with DataManager() as manager:
            chain = await manager.get_chain("SPY")
    """

    def __init__(self, cache_ttl_seconds: float = 60.0) -> None:
        self._cache_ttl = cache_ttl_seconds
        self._cache: dict[str, _CacheEntry] = {}

        # Initialize clients
        self._tastytrade: TastytradeClient | None = None
        if config.tastytrade_client_secret and config.tastytrade_refresh_token:
            self._tastytrade = TastytradeClient(
                client_secret=config.tastytrade_client_secret,
                refresh_token=config.tastytrade_refresh_token,
                is_sandbox=config.tastytrade_sandbox,
            )

        self._cboe = CBOEClient()
        self._tradier = TradierClient(
            token=config.tradier_token,
            base_url=config.tradier_base_url,
        )

        sources = ["CBOE", "Tradier"]
        if self._tastytrade:
            sources.insert(0, "Tastytrade")

        logger.info(
            "DataManager initialized (cache TTL=%ds, tickers=%s, sources=%s)",
            int(self._cache_ttl),
            config.tickers,
            sources,
        )

    async def close(self) -> None:
        """Close all underlying HTTP sessions."""
        if self._tastytrade:
            await self._tastytrade.close()
        await self._cboe.close()
        await self._tradier.close()
        logger.debug("DataManager: all sessions closed")

    def _get_cached(self, ticker: str) -> OptionsChain | None:
        """Return cached chain if still valid, otherwise None."""
        entry = self._cache.get(ticker)
        if entry is None:
            return None

        age = time.monotonic() - entry.fetched_at
        if age > self._cache_ttl:
            logger.debug(
                "DataManager: cache expired for %s (age=%.1fs, ttl=%.1fs)",
                ticker,
                age,
                self._cache_ttl,
            )
            del self._cache[ticker]
            return None

        logger.debug(
            "DataManager: cache hit for %s (age=%.1fs, source=%s)",
            ticker,
            age,
            entry.source,
        )
        return entry.chain

    def _set_cached(self, ticker: str, chain: OptionsChain) -> None:
        """Store a chain in the cache."""
        self._cache[ticker] = _CacheEntry(
            chain=chain,
            fetched_at=time.monotonic(),
            source=chain.source,
        )

    def invalidate(self, ticker: str | None = None) -> None:
        """Invalidate cache for a specific ticker, or all tickers if None."""
        if ticker is None:
            self._cache.clear()
            logger.debug("DataManager: all cache entries invalidated")
        elif ticker in self._cache:
            del self._cache[ticker]
            logger.debug("DataManager: cache invalidated for %s", ticker)

    async def get_chain(self, ticker: str) -> OptionsChain | None:
        """Fetch the options chain for a ticker, with caching and fallback.

        Strategy:
          1. Return cached data if fresh
          2. Try Tastytrade (if configured)
          3. Fall back to CBOE CDN
          4. Fall back to Tradier sandbox
          5. Cache successful result

        Args:
            ticker: 'SPY' or 'SPX'

        Returns:
            OptionsChain or None if all sources fail.
        """
        ticker_upper = ticker.upper()

        # Check cache first
        cached = self._get_cached(ticker_upper)
        if cached is not None:
            return cached

        # Try Tastytrade first (if configured)
        chain = await self._try_tastytrade(ticker_upper)

        # Fallback to CBOE
        if chain is None:
            chain = await self._try_cboe(ticker_upper)

        # Fallback to Tradier
        if chain is None:
            chain = await self._try_tradier(ticker_upper)

        # Cache and return
        if chain is not None:
            self._set_cached(ticker_upper, chain)
            logger.info(
                "DataManager: %s chain ready — %d contracts, spot=%.2f, source=%s",
                ticker_upper,
                len(chain.contracts),
                chain.spot_price,
                chain.source,
            )
        else:
            logger.error(
                "DataManager: all data sources failed for %s",
                ticker_upper,
            )

        return chain

    async def _try_tastytrade(self, ticker: str) -> OptionsChain | None:
        """Attempt to fetch from Tastytrade API."""
        if self._tastytrade is None:
            logger.debug("DataManager: Tastytrade not configured, skipping for %s", ticker)
            return None

        try:
            chain = await self._tastytrade.fetch_chain(ticker)
            if chain is not None and chain.contracts:
                return chain
            if chain is not None and not chain.contracts:
                logger.warning("DataManager: Tastytrade returned empty chain for %s", ticker)
            return None
        except Exception as exc:
            logger.error("DataManager: Tastytrade failed for %s — %s", ticker, exc)
            return None

    async def _try_cboe(self, ticker: str) -> OptionsChain | None:
        """Attempt to fetch from CBOE CDN."""
        try:
            chain = await self._cboe.fetch_chain(ticker)
            if chain is not None and chain.contracts:
                return chain
            if chain is not None and not chain.contracts:
                logger.warning("DataManager: CBOE returned empty chain for %s", ticker)
            return None
        except Exception as exc:
            logger.error("DataManager: CBOE failed for %s — %s", ticker, exc)
            return None

    async def _try_tradier(self, ticker: str) -> OptionsChain | None:
        """Attempt to fetch from Tradier sandbox."""
        if not config.tradier_token:
            logger.debug("DataManager: Tradier token not configured, skipping fallback for %s", ticker)
            return None

        try:
            chain = await self._tradier.fetch_chain(ticker)
            if chain is not None and chain.contracts:
                return chain
            if chain is not None and not chain.contracts:
                logger.warning("DataManager: Tradier returned empty chain for %s", ticker)
            return None
        except Exception as exc:
            logger.error("DataManager: Tradier failed for %s — %s", ticker, exc)
            return None

    async def get_all_chains(self) -> dict[str, OptionsChain]:
        """Fetch options chains for all configured tickers.

        Returns:
            Dict mapping ticker to OptionsChain. Only includes tickers
            where data was successfully retrieved.
        """
        results: dict[str, OptionsChain] = {}

        for ticker in config.tickers:
            chain = await self.get_chain(ticker)
            if chain is not None:
                results[ticker] = chain

        fetched = list(results.keys())
        missed = [t for t in config.tickers if t not in results]

        if fetched:
            logger.info("DataManager: fetched chains for %s", fetched)
        if missed:
            logger.warning("DataManager: failed to fetch chains for %s", missed)

        return results

    @property
    def cache_info(self) -> dict[str, dict[str, object]]:
        """Return current cache state for debugging."""
        now = time.monotonic()
        info: dict[str, dict[str, object]] = {}
        for ticker, entry in self._cache.items():
            age = now - entry.fetched_at
            info[ticker] = {
                "source": entry.source,
                "age_seconds": round(age, 1),
                "ttl_remaining": round(max(0, self._cache_ttl - age), 1),
                "contracts": len(entry.chain.contracts),
                "spot_price": entry.chain.spot_price,
            }
        return info

    async def __aenter__(self) -> "DataManager":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
