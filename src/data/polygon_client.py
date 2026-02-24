"""Polygon.io API client for options data.

Provides REST endpoints for options chain snapshots, individual trades,
OHLCV aggregates, and news articles, plus WebSocket streaming for
real-time OPRA options data. Follows the same async aiohttp pattern
established by ORATSClient.

REST endpoints:
  - /v3/snapshot/options/{underlying} — options chain snapshots
  - /v3/trades/{options_ticker} — individual option trades
  - /v2/aggs/ticker/{ticker}/range/... — OHLCV bars
  - /v2/reference/news — news articles

WebSocket:
  - wss://socket.polygon.io/options — real-time OPRA feed (trades + quotes)

Rate limits (free tier):
  - 5 requests per minute (configurable via POLYGON_RATE_LIMIT)

Requires:
  pip install aiohttp

Environment:
  POLYGON_API_KEY — API key from polygon.io account
  POLYGON_RATE_LIMIT — requests per minute (default 5)
"""

import asyncio
import json
import logging
import re
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import aiohttp

logger = logging.getLogger(__name__)

# Regex to extract call/put from OCC-style option ticker
# Format: O:SPY251219C00600000 — the C or P after 6 date digits
_OCC_TYPE_RE = re.compile(r"\d{6}([CP])")


def _option_type_from_ticker(ticker: str) -> str | None:
    """Extract option type ('C' or 'P') from an OCC-style option ticker.

    Examples:
        O:SPY251219C00600000 -> 'C'
        O:SPY251219P00550000 -> 'P'
        SPY -> None

    Returns:
        'C' for call, 'P' for put, or None if not a recognized option ticker.
    """
    m = _OCC_TYPE_RE.search(ticker)
    return m.group(1) if m else None


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
                # SSRF protection: only follow URLs on our own domain
                if not next_url.startswith(self.BASE_URL):
                    logger.warning(
                        "Polygon pagination next_url rejected (foreign domain): %s",
                        next_url[:120],
                    )
                    break

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


# ---------------------------------------------------------------------------
# WebSocket streaming for real-time OPRA data
# ---------------------------------------------------------------------------


class PolygonOptionsStream:
    """WebSocket client for real-time options data via Polygon.io OPRA feed.

    Connects to wss://socket.polygon.io/options for trade and quote events.
    Designed for the $199/mo Options plan (real-time). On the Starter plan
    ($29/mo), the stream still works but delivers 15-minute delayed data.

    Usage:
        stream = PolygonOptionsStream(api_key="...", tickers=["SPY", "SPX"])
        await stream.connect()
        await stream.listen(my_callback)
        await stream.disconnect()
    """

    WS_URL = "wss://socket.polygon.io/options"

    # Backoff settings for reconnection
    _INITIAL_BACKOFF = 1.0
    _MAX_BACKOFF = 30.0
    _BACKOFF_MULTIPLIER = 2.0

    def __init__(
        self,
        api_key: str,
        tickers: list[str] | None = None,
        block_threshold: int = 100,
        sweep_window_seconds: float = 2.0,
    ) -> None:
        self._api_key = api_key
        self._tickers = tickers or ["SPX", "SPY"]
        self._block_threshold = block_threshold
        self._sweep_window_seconds = sweep_window_seconds
        self._session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._connected = False
        self._backoff = self._INITIAL_BACKOFF

        # Sliding window for sweep detection: deque of (timestamp, exchange, ticker)
        self._recent_trades: deque[tuple[float, int, str]] = deque(maxlen=1000)

    async def connect(self) -> None:
        """Connect to the Polygon.io options WebSocket and authenticate.

        Handles connection errors with exponential backoff (1s, 2s, 4s, max 30s).

        Raises:
            PolygonAuthError: If authentication fails.
        """
        if not self._api_key:
            logger.warning(
                "Polygon API key not configured — WebSocket will not connect"
            )
            return

        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

        try:
            self._ws = await self._session.ws_connect(self.WS_URL)
            self._connected = True
            self._backoff = self._INITIAL_BACKOFF

            # Read the connection status message
            connect_msg = await self._ws.receive_json()
            if isinstance(connect_msg, list) and connect_msg:
                status = connect_msg[0].get("status", "")
                message = connect_msg[0].get("message", "")
                logger.info(
                    "Polygon WebSocket connected: status=%s message=%s",
                    status,
                    message,
                )

            # Authenticate
            auth_msg = {"action": "auth", "params": self._api_key}
            await self._ws.send_json(auth_msg)

            auth_resp = await self._ws.receive_json()
            if isinstance(auth_resp, list) and auth_resp:
                auth_status = auth_resp[0].get("status", "")
                if auth_status == "auth_success":
                    logger.info("Polygon WebSocket authenticated successfully")
                    # Log plan level if available
                    plan_msg = auth_resp[0].get("message", "")
                    if plan_msg:
                        logger.info("Polygon plan: %s", plan_msg)
                else:
                    raise PolygonAuthError(
                        f"Polygon WebSocket auth failed: {auth_resp}"
                    )

            # Subscribe to trade and quote channels
            subscribe_params = ",".join(
                [f"T.{t}" for t in self._tickers]
                + [f"Q.{t}" for t in self._tickers]
            )
            subscribe_msg = {"action": "subscribe", "params": subscribe_params}
            await self._ws.send_json(subscribe_msg)

            logger.info(
                "Polygon WebSocket subscribed to: %s", subscribe_params
            )

        except PolygonAuthError:
            raise
        except Exception as exc:
            self._connected = False
            logger.error("Polygon WebSocket connect failed: %s", exc)
            raise

    async def listen(
        self,
        callback: Callable[[dict], Awaitable[None]],
    ) -> None:
        """Listen for incoming messages and dispatch to callback.

        Parses trade (T) and quote (Q) messages into normalized dicts
        and calls the callback for each. Reconnects with exponential
        backoff on disconnection.

        Args:
            callback: Async function called with each parsed message dict.
        """
        if not self._connected or self._ws is None:
            logger.warning("Polygon WebSocket not connected — cannot listen")
            return

        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        logger.warning("Polygon WS: invalid JSON: %s", msg.data[:100])
                        continue

                    if not isinstance(data, list):
                        data = [data]

                    for event in data:
                        parsed = self._parse_event(event)
                        if parsed is not None:
                            # Classify trades
                            if parsed["type"] == "trade":
                                parsed["classification"] = self._classify_trade(parsed)
                            await callback(parsed)

                elif msg.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.ERROR,
                ):
                    logger.warning(
                        "Polygon WebSocket disconnected: %s", msg.type
                    )
                    break

        except Exception as exc:
            logger.error("Polygon WebSocket listen error: %s", exc)

        self._connected = False

        # Attempt reconnection with exponential backoff
        logger.info(
            "Polygon WebSocket reconnecting in %.1fs...", self._backoff
        )
        await asyncio.sleep(self._backoff)
        self._backoff = min(
            self._backoff * self._BACKOFF_MULTIPLIER, self._MAX_BACKOFF
        )

    def _parse_event(self, event: dict) -> dict | None:
        """Parse a raw WebSocket event into a normalized dict.

        Args:
            event: Raw event from Polygon WebSocket.

        Returns:
            Normalized dict with type, ticker, and relevant fields,
            or None if the event type is not recognized.
        """
        ev_type = event.get("ev", "")

        if ev_type == "T":
            # Trade event
            return {
                "type": "trade",
                "ticker": event.get("sym", ""),
                "price": float(event.get("p", 0.0)),
                "size": int(event.get("s", 0)),
                "exchange": int(event.get("x", 0)),
                "conditions": event.get("c", []),
                "timestamp": int(event.get("t", 0)),
            }
        elif ev_type == "Q":
            # Quote event
            return {
                "type": "quote",
                "ticker": event.get("sym", ""),
                "bid": float(event.get("bp", 0.0)),
                "ask": float(event.get("ap", 0.0)),
                "bid_size": int(event.get("bs", 0)),
                "ask_size": int(event.get("as", 0)),
                "timestamp": int(event.get("t", 0)),
            }
        else:
            # Status or other event types — skip silently
            return None

    def _classify_trade(self, trade: dict) -> str:
        """Classify a trade as sweep, block, or standard.

        Classification rules:
          - "block": Single trade with size > block_threshold (default 100 contracts).
          - "sweep": Same ticker traded on multiple exchanges within the sweep
            window (default 2 seconds). Tracked via a sliding window of recent trades.
          - "standard": Everything else.

        Args:
            trade: Normalized trade dict from _parse_event.

        Returns:
            One of "sweep", "block", or "standard".
        """
        size = trade.get("size", 0)
        exchange = trade.get("exchange", 0)
        ticker = trade.get("ticker", "")
        timestamp = trade.get("timestamp", 0)

        # Block detection: large single trade
        if size > self._block_threshold:
            return "block"

        # Record this trade for sweep detection
        now = time.time()
        self._recent_trades.append((now, exchange, ticker))

        # Sweep detection: same ticker, multiple exchanges within window
        cutoff = now - self._sweep_window_seconds
        recent_for_ticker = [
            (t, ex, tk)
            for t, ex, tk in self._recent_trades
            if t > cutoff and tk == ticker
        ]

        exchanges_seen = set(ex for _, ex, _ in recent_for_ticker)
        if len(exchanges_seen) >= 2:
            return "sweep"

        return "standard"

    async def disconnect(self) -> None:
        """Cleanly disconnect the WebSocket."""
        self._connected = False

        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
            self._ws = None
            logger.debug("Polygon WebSocket disconnected")

        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None


# ---------------------------------------------------------------------------
# Flow aggregation for windowed summaries
# ---------------------------------------------------------------------------


class PolygonFlowAggregator:
    """Aggregates streaming option trades into windowed flow summaries.

    Accumulates trades within a configurable time window and produces
    summary statistics useful for flow analysis dashboards and alerts.

    Usage:
        aggregator = PolygonFlowAggregator(window_seconds=60)
        aggregator.process_trade(trade_dict)
        summary = aggregator.get_flow_summary()
    """

    def __init__(self, window_seconds: int = 60) -> None:
        self._window_seconds = window_seconds
        self._window_start: str = datetime.now(timezone.utc).isoformat()
        self._trades: list[dict] = []
        self._total_volume: int = 0
        self._total_premium: float = 0.0
        self._call_volume: int = 0
        self._put_volume: int = 0
        self._sweep_count: int = 0
        self._block_count: int = 0
        self._largest_trade: dict = {}

    def process_trade(self, trade: dict) -> None:
        """Accumulate a trade in the current window.

        Args:
            trade: Normalized trade dict with type, ticker, price, size,
                   and optionally classification.
        """
        if trade.get("type") != "trade":
            return

        size = trade.get("size", 0)
        price = trade.get("price", 0.0)
        premium = price * size * 100  # Options are 100 shares per contract

        self._trades.append(trade)
        self._total_volume += size
        self._total_premium += premium

        # Determine call vs put from ticker convention
        # OCC format: O:SPY251219C00600000 (C=call, P=put)
        ticker = trade.get("ticker", "")
        opt_type = _option_type_from_ticker(ticker)
        if opt_type == "C":
            self._call_volume += size
        elif opt_type == "P":
            self._put_volume += size

        # Count classification types
        classification = trade.get("classification", "standard")
        if classification == "sweep":
            self._sweep_count += 1
        elif classification == "block":
            self._block_count += 1

        # Track largest trade
        if not self._largest_trade or premium > (
            self._largest_trade.get("price", 0.0)
            * self._largest_trade.get("size", 0)
            * 100
        ):
            self._largest_trade = trade

    def get_flow_summary(self) -> dict:
        """Return a summary of the current aggregation window.

        Returns:
            Dict with total_volume, total_premium, call_volume, put_volume,
            sweep_count, block_count, net_premium, largest_trade, window_start.
        """
        # Net premium: calls positive, puts negative
        call_premium = sum(
            t.get("price", 0.0) * t.get("size", 0) * 100
            for t in self._trades
            if _option_type_from_ticker(t.get("ticker", "")) == "C"
        )
        put_premium = sum(
            t.get("price", 0.0) * t.get("size", 0) * 100
            for t in self._trades
            if _option_type_from_ticker(t.get("ticker", "")) == "P"
        )
        net_premium = call_premium - put_premium

        return {
            "total_volume": self._total_volume,
            "total_premium": self._total_premium,
            "call_volume": self._call_volume,
            "put_volume": self._put_volume,
            "sweep_count": self._sweep_count,
            "block_count": self._block_count,
            "net_premium": net_premium,
            "largest_trade": self._largest_trade,
            "window_start": self._window_start,
        }

    def reset(self) -> None:
        """Clear the current aggregation window and start a new one."""
        self._window_start = datetime.now(timezone.utc).isoformat()
        self._trades = []
        self._total_volume = 0
        self._total_premium = 0.0
        self._call_volume = 0
        self._put_volume = 0
        self._sweep_count = 0
        self._block_count = 0
        self._largest_trade = {}
