"""CBOE CDN client for fetching delayed options chain data.

CBOE provides free 15-minute delayed options data via their CDN.
No API key required. Data includes full greeks and pricing.

Endpoints:
  SPY: https://cdn.cboe.com/api/global/delayed_quotes/options/SPY.json
  SPX: https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json
"""

import logging
import re
from datetime import date, datetime

import aiohttp

from src.data import OptionContract, OptionsChain
from src.utils import now_et

logger = logging.getLogger(__name__)

# Pattern for OCC option symbols: {TICKER}{YYMMDD}{C/P}{STRIKE*1000}
# Example: SPY240119C00590000 = SPY, 2024-01-19, Call, $590.00
# Ticker can be 1-6 chars, rest is fixed-width numeric
_OPTION_SYMBOL_RE = re.compile(
    r"^(?P<ticker>[A-Z]{1,6})"
    r"(?P<year>\d{2})(?P<month>\d{2})(?P<day>\d{2})"
    r"(?P<cp>[CP])"
    r"(?P<strike>\d{8})$"
)


def parse_option_symbol(symbol: str) -> dict[str, object] | None:
    """Parse an OCC option symbol into its components.

    Args:
        symbol: OCC option symbol, e.g. 'SPY240119C00590000'

    Returns:
        Dict with ticker, expiry (date), option_type ('call'/'put'), strike (float),
        or None if the symbol doesn't match the expected format.
    """
    m = _OPTION_SYMBOL_RE.match(symbol)
    if not m:
        return None

    year = 2000 + int(m.group("year"))
    month = int(m.group("month"))
    day = int(m.group("day"))
    try:
        expiry = date(year, month, day)
    except ValueError:
        return None

    strike = int(m.group("strike")) / 1000.0
    option_type = "call" if m.group("cp") == "C" else "put"

    return {
        "ticker": m.group("ticker"),
        "expiry": expiry,
        "option_type": option_type,
        "strike": strike,
    }


class CBOEClient:
    """Async client for CBOE CDN delayed options data."""

    # Map tickers to their CBOE CDN URLs.
    # SPX uses an underscore prefix on CBOE's CDN.
    URLS: dict[str, str] = {
        "SPY": "https://cdn.cboe.com/api/global/delayed_quotes/options/SPY.json",
        "SPX": "https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json",
    }

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Lazily create and return the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; spy-options-employee/1.0)",
                    "Accept": "application/json",
                },
            )
        return self._session

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def fetch_chain(self, ticker: str) -> OptionsChain | None:
        """Fetch the full options chain for a ticker from CBOE CDN.

        Args:
            ticker: 'SPY' or 'SPX'

        Returns:
            OptionsChain with all available contracts, or None on failure.
        """
        ticker_upper = ticker.upper()
        url = self.URLS.get(ticker_upper)
        if url is None:
            logger.error("CBOE: unsupported ticker '%s'. Supported: %s", ticker, list(self.URLS.keys()))
            return None

        logger.info("CBOE: fetching options chain for %s", ticker_upper)

        try:
            session = await self._get_session()
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.error(
                        "CBOE: HTTP %d for %s — %s",
                        resp.status,
                        ticker_upper,
                        await resp.text(),
                    )
                    return None

                payload = await resp.json(content_type=None)

        except aiohttp.ClientError as exc:
            logger.error("CBOE: network error fetching %s — %s", ticker_upper, exc)
            return None
        except Exception as exc:
            logger.exception("CBOE: unexpected error fetching %s — %s", ticker_upper, exc)
            return None

        return self._parse_response(ticker_upper, payload)

    def _parse_response(self, ticker: str, payload: dict) -> OptionsChain | None:
        """Parse CBOE JSON response into an OptionsChain.

        Expected structure:
            {
                "timestamp": "2024-01-15 15:45:00",
                "data": {
                    "close": 595.23,
                    "options": [ { ... }, ... ]
                }
            }
        """
        try:
            timestamp_str = payload.get("timestamp", "")
            timestamp = self._parse_timestamp(timestamp_str)

            data = payload.get("data")
            if data is None:
                logger.error("CBOE: missing 'data' key in response for %s", ticker)
                return None

            spot_price = float(data.get("close", 0.0))
            if spot_price <= 0:
                logger.warning("CBOE: spot price is %s for %s, may be invalid", spot_price, ticker)

            raw_options = data.get("options", [])
            if not raw_options:
                logger.warning("CBOE: no options data in response for %s", ticker)
                return OptionsChain(
                    ticker=ticker,
                    spot_price=spot_price,
                    timestamp=timestamp,
                    contracts=[],
                    source="cboe",
                )

            contracts = self._parse_contracts(ticker, raw_options)

            logger.info(
                "CBOE: parsed %d contracts for %s (spot=%.2f, expirations=%d)",
                len(contracts),
                ticker,
                spot_price,
                len(set(c.expiry for c in contracts)),
            )

            return OptionsChain(
                ticker=ticker,
                spot_price=spot_price,
                timestamp=timestamp,
                contracts=contracts,
                source="cboe",
            )

        except Exception as exc:
            logger.exception("CBOE: failed to parse response for %s — %s", ticker, exc)
            return None

    def _parse_contracts(self, ticker: str, raw_options: list[dict]) -> list[OptionContract]:
        """Parse individual option entries from CBOE response."""
        contracts: list[OptionContract] = []
        parse_errors = 0

        for entry in raw_options:
            symbol = entry.get("option", "")
            parsed = parse_option_symbol(symbol)
            if parsed is None:
                parse_errors += 1
                continue

            try:
                contract = OptionContract(
                    ticker=str(parsed["ticker"]),
                    expiry=parsed["expiry"],  # type: ignore[arg-type]
                    strike=float(parsed["strike"]),  # type: ignore[arg-type]
                    option_type=str(parsed["option_type"]),
                    bid=float(entry.get("bid", 0.0)),
                    ask=float(entry.get("ask", 0.0)),
                    last=float(entry.get("last", 0.0)),
                    volume=int(entry.get("volume", 0)),
                    open_interest=int(entry.get("open_interest", 0)),
                    iv=float(entry.get("iv", 0.0)),
                    delta=float(entry.get("delta", 0.0)),
                    gamma=float(entry.get("gamma", 0.0)),
                    theta=float(entry.get("theta", 0.0)),
                    vega=float(entry.get("vega", 0.0)),
                    rho=float(entry.get("rho", 0.0)),
                )
                contracts.append(contract)
            except (ValueError, TypeError) as exc:
                parse_errors += 1
                logger.debug("CBOE: skipping contract '%s' — %s", symbol, exc)

        if parse_errors > 0:
            logger.warning(
                "CBOE: %d contracts failed to parse for %s (out of %d total)",
                parse_errors,
                ticker,
                len(raw_options),
            )

        return contracts

    @staticmethod
    def _parse_timestamp(ts_str: str) -> datetime:
        """Parse CBOE timestamp string into datetime.

        Tries common formats and falls back to now() if none match.
        """
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S.%f",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue

        logger.warning("CBOE: could not parse timestamp '%s', using current time", ts_str)
        return now_et()

    async def __aenter__(self) -> "CBOEClient":
        await self._get_session()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
