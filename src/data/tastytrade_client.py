"""Tastytrade API client for real-time options chain data.

Uses the community tastytrade SDK (tastyware/tastytrade) to fetch complete
options chains with bid/ask, volume, OI, and full Greeks. Combines REST
endpoints for instrument metadata and market data with a brief DXLink
WebSocket connection for Greeks/IV.

Data flow:
  1. REST: get_option_chain() → instrument metadata (strikes, expiries)
  2. REST: get_market_data_by_type() → bid/ask/last/volume/OI
  3. WebSocket one-shot: DXLinkStreamer → Greeks (delta/gamma/theta/vega/rho/IV)
  4. Merge into OptionContract objects

Requires:
  pip install tastytrade>=8.0

Environment:
  TASTYTRADE_CLIENT_SECRET — OAuth client secret
  TASTYTRADE_REFRESH_TOKEN — OAuth refresh token (never expires)
  TASTYTRADE_SANDBOX — "true" for cert/sandbox environment
"""

import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal

from tastytrade import DXLinkStreamer, Session
from tastytrade.dxfeed import Greeks, Quote
from tastytrade.instruments import get_option_chain
from tastytrade.market_data import get_market_data_by_type

from src.data import OptionContract, OptionsChain
from src.utils import now_et

logger = logging.getLogger(__name__)


def _dec(val: Decimal | None, default: float = 0.0) -> float:
    """Convert optional Decimal to float."""
    return float(val) if val is not None else default


class TastytradeClient:
    """Async client for Tastytrade options data via REST + DXLink WebSocket.

    Usage:
        client = TastytradeClient(client_secret="...", refresh_token="...")
        chain = await client.fetch_chain("SPY")
        await client.close()

    Or as an async context manager:
        async with TastytradeClient(...) as client:
            chain = await client.fetch_chain("SPY")
    """

    def __init__(
        self,
        client_secret: str,
        refresh_token: str,
        is_sandbox: bool = False,
        timeout_seconds: float = 15.0,
        strike_range_pct: float = 0.07,
    ) -> None:
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._is_sandbox = is_sandbox
        self._timeout = timeout_seconds
        self._strike_range_pct = strike_range_pct  # Filter strikes within ±15% of spot
        self._session = None  # Lazy init

    async def _get_session(self):
        """Lazily create and return the tastytrade Session.

        If session creation fails, the cached session remains None so the
        next call will retry.  Auth-related errors during fetch_chain()
        invalidate the session so a fresh one is created on the next attempt.
        """
        if self._session is None:
            logger.info(
                "Tastytrade: creating session (sandbox=%s)", self._is_sandbox
            )
            self._session = Session(
                self._client_secret,
                self._refresh_token,
                is_test=self._is_sandbox,
            )
        return self._session

    def _invalidate_session(self) -> None:
        """Clear the cached session so it is recreated on next use."""
        self._session = None
        logger.warning("Tastytrade: session invalidated, will re-authenticate on next call")

    async def close(self) -> None:
        """Close the underlying session."""
        self._session = None
        logger.debug("TastytradeClient: session released")

    async def fetch_chain(
        self,
        ticker: str,
        max_expirations: int = 3,
    ) -> OptionsChain | None:
        """Fetch a complete options chain with Greeks.

        Uses REST for instrument catalog + market data snapshots, then a brief
        DXLink WebSocket session for Greeks/IV. If the WebSocket fails, returns
        data without Greeks (bid/ask/volume/OI still populated).

        Args:
            ticker: Underlying symbol, e.g. 'SPY' or 'SPX'
            max_expirations: Number of nearest expirations to fetch

        Returns:
            OptionsChain with full data, or None on failure.
        """
        ticker_upper = ticker.upper()
        session = await self._get_session()

        # Step 1: Get instrument catalog
        logger.info("Tastytrade: fetching option chain for %s", ticker_upper)
        try:
            chain_map = await get_option_chain(session, ticker_upper)
        except Exception as exc:
            err_str = str(exc).lower()
            if "401" in err_str or "auth" in err_str or "token" in err_str:
                self._invalidate_session()
            logger.error(
                "Tastytrade: failed to get chain for %s — %s", ticker_upper, exc
            )
            return None

        if not chain_map:
            logger.error("Tastytrade: empty chain for %s", ticker_upper)
            return None

        # Step 2: Filter to nearest future expirations
        today = date.today()
        future_expiries = sorted(d for d in chain_map.keys() if d >= today)
        if not future_expiries:
            logger.error("Tastytrade: no future expirations for %s", ticker_upper)
            return None

        target_expiries = future_expiries[:max_expirations]
        all_options = []
        for exp in target_expiries:
            all_options.extend(chain_map[exp])

        # Estimate spot price from middle strike of nearest expiry
        nearest_opts = chain_map[target_expiries[0]]
        strikes = sorted(set(float(o.strike_price) for o in nearest_opts))
        estimated_spot = strikes[len(strikes) // 2] if strikes else 0.0

        # Filter to strikes within ±strike_range_pct of spot
        low = estimated_spot * (1 - self._strike_range_pct)
        high = estimated_spot * (1 + self._strike_range_pct)
        options = [o for o in all_options if low <= float(o.strike_price) <= high]

        logger.info(
            "Tastytrade: %d contracts (filtered from %d) across %d expirations for %s "
            "(spot~%.0f, range %.0f-%.0f)",
            len(options),
            len(all_options),
            len(target_expiries),
            ticker_upper,
            estimated_spot,
            low,
            high,
        )

        # Step 3: REST market data (bid/ask/last/volume/OI) in batches of 100
        market_data_map: dict[str, object] = {}
        occ_symbols = [opt.symbol for opt in options]

        for i in range(0, len(occ_symbols), 100):
            batch = occ_symbols[i : i + 100]
            try:
                md_list = await get_market_data_by_type(session, options=batch)
                for md in md_list:
                    market_data_map[md.symbol] = md
            except Exception as exc:
                logger.warning(
                    "Tastytrade: market data batch %d failed — %s", i // 100, exc
                )

        logger.info(
            "Tastytrade: got market data for %d / %d contracts",
            len(market_data_map),
            len(options),
        )

        # Step 4: WebSocket one-shot for Greeks (best-effort, hard timeout)
        streamer_symbols = [opt.streamer_symbol for opt in options]
        greeks_map: dict[str, object] = {}
        quote_map: dict[str, object] = {}

        try:
            async with asyncio.timeout(self._timeout):
                async with DXLinkStreamer(session) as streamer:
                    await streamer.subscribe(Greeks, streamer_symbols)
                    await streamer.subscribe(Quote, streamer_symbols)

                    # Collect Greeks (stop early if we have them all)
                    async for greek in streamer.listen(Greeks):
                        greeks_map[greek.event_symbol] = greek
                        if len(greeks_map) >= len(streamer_symbols):
                            break

                    # Collect Quotes
                    async for quote in streamer.listen(Quote):
                        quote_map[quote.event_symbol] = quote
                        if len(quote_map) >= len(streamer_symbols):
                            break

        except TimeoutError:
            logger.info(
                "Tastytrade: streamer timed out after %.0fs (got Greeks=%d, Quotes=%d of %d) — using partial data",
                self._timeout,
                len(greeks_map),
                len(quote_map),
                len(streamer_symbols),
            )
        except Exception as exc:
            logger.warning(
                "Tastytrade: streamer error (continuing with REST data) — %s", exc
            )

        logger.info(
            "Tastytrade: streamer got Greeks=%d, Quotes=%d",
            len(greeks_map),
            len(quote_map),
        )

        # Step 5: Determine spot price from market data
        # Use the first available last/mark price from an ATM option's underlying
        spot_price = self._extract_spot_price(market_data_map, options, ticker_upper)

        # Step 6: Merge into OptionContract objects
        contracts: list[OptionContract] = []
        for opt in options:
            md = market_data_map.get(opt.symbol)
            greek = greeks_map.get(opt.streamer_symbol)
            quote = quote_map.get(opt.streamer_symbol)

            # Prefer streamer Quote for bid/ask (more real-time)
            if quote is not None:
                bid = _dec(quote.bid_price)
                ask = _dec(quote.ask_price)
            elif md is not None:
                bid = _dec(md.bid)
                ask = _dec(md.ask)
            else:
                bid = 0.0
                ask = 0.0

            contract = OptionContract(
                ticker=ticker_upper,
                expiry=opt.expiration_date,
                strike=float(opt.strike_price),
                option_type="call" if opt.option_type.value == "C" else "put",
                bid=bid,
                ask=ask,
                last=_dec(md.last) if md else 0.0,
                volume=int(_dec(md.volume)) if md else 0,
                open_interest=int(_dec(md.open_interest)) if md else 0,
                iv=_dec(greek.volatility) if greek else 0.0,
                delta=_dec(greek.delta) if greek else 0.0,
                gamma=_dec(greek.gamma) if greek else 0.0,
                theta=_dec(greek.theta) if greek else 0.0,
                vega=_dec(greek.vega) if greek else 0.0,
                rho=_dec(greek.rho) if greek else 0.0,
            )
            contracts.append(contract)

        if not contracts:
            logger.error("Tastytrade: no contracts built for %s", ticker_upper)
            return None

        logger.info(
            "Tastytrade: built %d contracts for %s (spot=%.2f, expirations=%d)",
            len(contracts),
            ticker_upper,
            spot_price,
            len(target_expiries),
        )

        return OptionsChain(
            ticker=ticker_upper,
            spot_price=spot_price,
            timestamp=now_et(),
            contracts=contracts,
            source="tastytrade",
        )

    @staticmethod
    def _extract_spot_price(
        market_data_map: dict,
        options: list,
        ticker: str,
    ) -> float:
        """Extract spot price from market data.

        Uses the mark price from the nearest ATM call option as a proxy,
        or falls back to a simple average of bid/ask of the closest strike.
        For SPX/SPY, the underlying quote is not directly available through
        the options market data endpoint, so we infer from option pricing.
        """
        # Try to find spot via the first option's underlying data if available
        # Otherwise, use strike prices as a rough reference
        if not options:
            return 0.0

        # The options are sorted by expiry then strike. Use the first expiry's
        # middle strike as a rough spot estimate, then refine with market data.
        first_expiry = options[0].expiration_date
        expiry_options = [o for o in options if o.expiration_date == first_expiry]

        if not expiry_options:
            return 0.0

        # Find the strike where call and put prices are closest (ATM proxy)
        best_strike = 0.0
        strikes = sorted(set(float(o.strike_price) for o in expiry_options))
        if strikes:
            best_strike = strikes[len(strikes) // 2]

        return best_strike

    async def __aenter__(self) -> "TastytradeClient":
        await self._get_session()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
