"""Tradier sandbox API client for options chain data.

Used as a backup data source when CBOE CDN is unavailable.
Requires a free Tradier sandbox API token (set TRADIER_TOKEN in .env).

Sandbox base URL: https://sandbox.tradier.com/v1
Key endpoints:
  - /markets/options/expirations?symbol=SPY
  - /markets/options/chains?symbol=SPY&expiration=YYYY-MM-DD&greeks=true
  - /markets/quotes?symbols=SPY
"""

import logging
from datetime import date, datetime

import aiohttp

from src.data import OptionContract, OptionsChain
from src.utils import now_et

logger = logging.getLogger(__name__)


class TradierClient:
    """Async client for Tradier sandbox options data."""

    def __init__(self, token: str, base_url: str = "https://sandbox.tradier.com/v1", timeout_seconds: float = 30.0) -> None:
        if not token:
            logger.warning("Tradier: no API token provided — requests will fail with 401")
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Lazily create and return the aiohttp session with auth headers."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Accept": "application/json",
                },
            )
        return self._session

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _get_json(self, endpoint: str, params: dict[str, str] | None = None) -> dict | None:
        """Make a GET request to the Tradier API and return parsed JSON.

        Args:
            endpoint: API path, e.g. '/markets/options/expirations'
            params: Query parameters

        Returns:
            Parsed JSON dict, or None on failure.
        """
        url = f"{self._base_url}{endpoint}"
        try:
            session = await self._get_session()
            async with session.get(url, params=params) as resp:
                if resp.status == 401:
                    logger.error("Tradier: authentication failed (401). Check TRADIER_TOKEN.")
                    return None
                if resp.status == 429:
                    logger.error("Tradier: rate limited (429). Try again later.")
                    return None
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("Tradier: HTTP %d for %s — %s", resp.status, endpoint, body[:500])
                    return None

                return await resp.json(content_type=None)

        except aiohttp.ClientError as exc:
            logger.error("Tradier: network error for %s — %s", endpoint, exc)
            return None
        except Exception as exc:
            logger.exception("Tradier: unexpected error for %s — %s", endpoint, exc)
            return None

    async def get_expirations(self, ticker: str) -> list[date]:
        """Fetch available expiration dates for a ticker.

        Args:
            ticker: Stock symbol, e.g. 'SPY'

        Returns:
            Sorted list of expiration dates, or empty list on failure.
        """
        logger.info("Tradier: fetching expirations for %s", ticker)

        data = await self._get_json(
            "/markets/options/expirations",
            params={"symbol": ticker},
        )
        if data is None:
            return []

        try:
            expirations_data = data.get("expirations")
            if expirations_data is None:
                logger.warning("Tradier: no 'expirations' key in response for %s", ticker)
                return []

            date_strings = expirations_data.get("date", [])
            if isinstance(date_strings, str):
                # Single expiration returned as a string instead of list
                date_strings = [date_strings]

            dates: list[date] = []
            for ds in date_strings:
                try:
                    dates.append(date.fromisoformat(ds))
                except ValueError:
                    logger.debug("Tradier: skipping unparseable expiration date '%s'", ds)

            dates.sort()
            logger.info("Tradier: found %d expirations for %s", len(dates), ticker)
            return dates

        except Exception as exc:
            logger.exception("Tradier: failed to parse expirations for %s — %s", ticker, exc)
            return []

    async def get_quote(self, ticker: str) -> float:
        """Fetch the current/last price for a ticker.

        Args:
            ticker: Stock symbol, e.g. 'SPY'

        Returns:
            Last price as float, or 0.0 on failure.
        """
        data = await self._get_json(
            "/markets/quotes",
            params={"symbols": ticker},
        )
        if data is None:
            return 0.0

        try:
            quotes = data.get("quotes", {})
            quote = quotes.get("quote", {})
            # Tradier may return a list if multiple symbols queried
            if isinstance(quote, list):
                quote = quote[0] if quote else {}
            return float(quote.get("last", 0.0))
        except (ValueError, TypeError, IndexError) as exc:
            logger.error("Tradier: failed to parse quote for %s — %s", ticker, exc)
            return 0.0

    async def get_chain_for_expiration(
        self, ticker: str, expiration: date
    ) -> list[OptionContract]:
        """Fetch the options chain for a specific ticker and expiration.

        Args:
            ticker: Stock symbol, e.g. 'SPY'
            expiration: Expiration date

        Returns:
            List of OptionContract, or empty list on failure.
        """
        exp_str = expiration.isoformat()
        logger.debug("Tradier: fetching chain for %s exp=%s", ticker, exp_str)

        data = await self._get_json(
            "/markets/options/chains",
            params={
                "symbol": ticker,
                "expiration": exp_str,
                "greeks": "true",
            },
        )
        if data is None:
            return []

        try:
            options_wrapper = data.get("options")
            if options_wrapper is None:
                logger.debug("Tradier: no 'options' key for %s exp=%s", ticker, exp_str)
                return []

            raw_options = options_wrapper.get("option", [])
            if isinstance(raw_options, dict):
                # Single option returned as dict instead of list
                raw_options = [raw_options]

            return self._parse_contracts(ticker, expiration, raw_options)

        except Exception as exc:
            logger.exception(
                "Tradier: failed to parse chain for %s exp=%s — %s",
                ticker,
                exp_str,
                exc,
            )
            return []

    def _parse_contracts(
        self, ticker: str, expiration: date, raw_options: list[dict]
    ) -> list[OptionContract]:
        """Parse Tradier option entries into OptionContract objects.

        Tradier contract structure:
            {
                "symbol": "SPY240119C00590000",
                "strike": 590.0,
                "option_type": "call",
                "bid": 6.50, "ask": 6.60, "last": 6.55,
                "volume": 12345, "open_interest": 50000,
                "greeks": { "delta": 0.65, "gamma": 0.03, "theta": -0.05,
                            "vega": 0.12, "mid_iv": 0.15 }
            }
        """
        contracts: list[OptionContract] = []
        parse_errors = 0

        for entry in raw_options:
            try:
                option_type_raw = entry.get("option_type", "").lower()
                if option_type_raw not in ("call", "put"):
                    parse_errors += 1
                    continue

                greeks = entry.get("greeks") or {}

                contract = OptionContract(
                    ticker=ticker,
                    expiry=expiration,
                    strike=float(entry.get("strike", 0.0)),
                    option_type=option_type_raw,
                    bid=float(entry.get("bid", 0.0)),
                    ask=float(entry.get("ask", 0.0)),
                    last=float(entry.get("last", 0.0)),
                    volume=int(entry.get("volume", 0)),
                    open_interest=int(entry.get("open_interest", 0)),
                    iv=float(greeks.get("mid_iv", 0.0)),
                    delta=float(greeks.get("delta", 0.0)),
                    gamma=float(greeks.get("gamma", 0.0)),
                    theta=float(greeks.get("theta", 0.0)),
                    vega=float(greeks.get("vega", 0.0)),
                    rho=float(greeks.get("rho", 0.0)),
                )
                contracts.append(contract)
            except (ValueError, TypeError) as exc:
                parse_errors += 1
                logger.debug(
                    "Tradier: skipping contract '%s' — %s",
                    entry.get("symbol", "unknown"),
                    exc,
                )

        if parse_errors > 0:
            logger.warning(
                "Tradier: %d contracts failed to parse for %s (out of %d total)",
                parse_errors,
                ticker,
                len(raw_options),
            )

        return contracts

    async def fetch_chain(self, ticker: str, max_expirations: int = 3) -> OptionsChain | None:
        """Fetch the full options chain for a ticker across the nearest expirations.

        Fetches expiration dates first, then chains for the nearest N expirations,
        and combines them into a single OptionsChain.

        Args:
            ticker: Stock symbol, e.g. 'SPY' or 'SPX'
            max_expirations: Maximum number of nearest expirations to fetch (default 3)

        Returns:
            OptionsChain with combined contracts, or None on failure.
        """
        ticker_upper = ticker.upper()
        logger.info("Tradier: fetching chain for %s (max %d expirations)", ticker_upper, max_expirations)

        # Get available expirations
        expirations = await self.get_expirations(ticker_upper)
        if not expirations:
            logger.error("Tradier: no expirations found for %s", ticker_upper)
            return None

        # Filter to future expirations and take nearest N
        today = date.today()
        future_exps = [exp for exp in expirations if exp >= today]
        if not future_exps:
            logger.error("Tradier: no future expirations for %s", ticker_upper)
            return None

        target_exps = future_exps[:max_expirations]
        logger.info(
            "Tradier: fetching %d expirations for %s: %s",
            len(target_exps),
            ticker_upper,
            [e.isoformat() for e in target_exps],
        )

        # Get spot price
        spot_price = await self.get_quote(ticker_upper)
        if spot_price <= 0:
            logger.warning("Tradier: could not get spot price for %s, using 0.0", ticker_upper)

        # Fetch chains for each expiration
        all_contracts: list[OptionContract] = []
        for exp in target_exps:
            contracts = await self.get_chain_for_expiration(ticker_upper, exp)
            all_contracts.extend(contracts)

        if not all_contracts:
            logger.error("Tradier: no contracts returned for %s across %d expirations", ticker_upper, len(target_exps))
            return None

        logger.info(
            "Tradier: total %d contracts for %s (spot=%.2f, expirations=%d)",
            len(all_contracts),
            ticker_upper,
            spot_price,
            len(target_exps),
        )

        return OptionsChain(
            ticker=ticker_upper,
            spot_price=spot_price,
            timestamp=now_et(),
            contracts=all_contracts,
            source="tradier",
        )

    async def __aenter__(self) -> "TradierClient":
        await self._get_session()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
