"""Paper order management and fill simulation.

OrderManager handles the lifecycle of simulated orders: submit, fill,
cancel, and expire. FillSimulator produces realistic fill prices using
live bid/ask quotes with configurable slippage.

Supports pluggable slippage models via the SlippageModel ABC:
- DynamicSpreadSlippage (default): adapts to delta, DTE, volume, VIX, time
- FixedSlippage: constant offset from mid (for testing/comparison)

Fill model (dynamic):
    fill_price = mid + direction * slippage_factor * half_spread

Where slippage_factor is computed from market conditions and clamped to [0.05, 1.50].
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import aiosqlite

from src.data import OptionContract, OptionsChain
from src.paper.models import LegSpec, PaperTradingConfig, SimulatedFill
from src.paper.slippage import (
    DynamicSpreadSlippage,
    OrderSide,
    SlippageModel,
)

logger = logging.getLogger(__name__)


class FillSimulator:
    """Simulates realistic fill prices using live bid/ask quotes.

    Uses a pluggable SlippageModel to compute fill prices. Defaults to
    DynamicSpreadSlippage which adapts to market conditions (delta, DTE,
    volume, VIX, time of day, order size, multi-leg discount).

    For testing, pass a FixedSlippage model for deterministic fills.
    """

    def __init__(
        self,
        config: PaperTradingConfig,
        slippage_model: SlippageModel | None = None,
    ) -> None:
        self._slippage_pct = config.slippage_pct
        self._model = slippage_model or DynamicSpreadSlippage()

    def _find_contract(
        self,
        leg: LegSpec,
        chain: OptionsChain,
    ) -> OptionContract | None:
        """Find the matching contract in the chain for a leg spec.

        Matches by option_type, strike, and expiry. Returns None if
        no matching contract is found (strike delisted, expiry passed, etc.).
        """
        for contract in chain.contracts:
            if (
                contract.option_type == leg.option_type
                and contract.strike == leg.strike
                and contract.expiry == leg.expiry
            ):
                return contract
        return None

    def simulate_fill(
        self,
        leg: LegSpec,
        chain: OptionsChain,
        vix: float = 16.0,
        order_size: int = 1,
        is_multi_leg: bool = False,
        timestamp: datetime | None = None,
    ) -> SimulatedFill | None:
        """Simulate a fill for a single leg using live chain data.

        Finds the matching contract by strike/expiry/type in the chain,
        then delegates to the pluggable SlippageModel for price computation.

        Returns None if the contract is not found in the chain.
        """
        contract = self._find_contract(leg, chain)
        if contract is None:
            return None

        side = OrderSide.BUY if leg.action == "buy" else OrderSide.SELL

        fill_result = self._model.simulate_fill(
            bid=contract.bid,
            ask=contract.ask,
            side=side,
            delta=contract.delta,
            dte=contract.days_to_expiry,
            volume=contract.volume,
            open_interest=contract.open_interest,
            vix=vix,
            order_size=order_size,
            is_multi_leg=is_multi_leg,
            timestamp=timestamp,
        )

        return SimulatedFill(
            leg_name=leg.leg_name,
            fill_price=round(fill_result.fill_price, 4),
            bid=contract.bid,
            ask=contract.ask,
            mid=round(fill_result.mid_price, 4),
            slippage=round(fill_result.slippage, 4),
            iv=contract.iv,
            delta=contract.delta,
        )

    def simulate_spread_fill(
        self,
        legs: list[LegSpec],
        chain: OptionsChain,
        vix: float = 16.0,
        order_size: int = 1,
        timestamp: datetime | None = None,
    ) -> list[SimulatedFill] | None:
        """Simulate fills for all legs of a spread.

        All-or-nothing: returns None if any leg cannot be filled.
        Returns list of SimulatedFill for each leg on success.
        Multi-leg discount is automatically applied by the slippage model.
        """
        fills: list[SimulatedFill] = []
        is_multi_leg = len(legs) > 1
        for leg in legs:
            fill = self.simulate_fill(
                leg, chain,
                vix=vix,
                order_size=order_size,
                is_multi_leg=is_multi_leg,
                timestamp=timestamp,
            )
            if fill is None:
                logger.warning(
                    "Cannot fill leg %s: %s %s %.1f exp %s not found in chain",
                    leg.leg_name, leg.action, leg.option_type,
                    leg.strike, leg.expiry,
                )
                return None
            fills.append(fill)
        return fills


class OrderManager:
    """Manages paper order lifecycle: submit, fill, cancel, expire.

    Orders go through: PENDING -> FILLED | CANCELLED | EXPIRED.
    Market orders fill immediately at the next tick. Limit orders fill
    only when the simulated price meets the limit. Orders pending for
    more than max_order_age_ticks are auto-expired.
    """

    def __init__(
        self,
        db: aiosqlite.Connection,
        config: PaperTradingConfig,
    ) -> None:
        self._db = db
        self._config = config
        self._fill_sim = FillSimulator(config)

    async def submit_order(
        self,
        strategy_id: int,
        direction: str,
        legs: list[LegSpec],
        quantity: int,
        order_type: str = "market",
        limit_price: float | None = None,
    ) -> int:
        """Submit a new paper order.

        Args:
            strategy_id: ID of the strategy placing the order.
            direction: 'open' or 'close'.
            legs: List of leg specifications (strikes, types, actions).
            quantity: Number of contracts.
            order_type: 'market' or 'limit'.
            limit_price: Required for limit orders (net credit/debit target).

        Returns:
            The new order ID.
        """
        now = datetime.now().isoformat()
        legs_json = json.dumps([
            {
                "leg_name": leg.leg_name,
                "option_type": leg.option_type,
                "strike": leg.strike,
                "expiry": leg.expiry.isoformat(),
                "action": leg.action,
                "quantity": leg.quantity,
            }
            for leg in legs
        ])

        cursor = await self._db.execute(
            """
            INSERT INTO paper_orders
                (strategy_id, order_type, direction, legs, quantity,
                 limit_price, status, submitted_at, ticks_pending)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, 0)
            """,
            (strategy_id, order_type, direction, legs_json,
             quantity, limit_price, now),
        )
        await self._db.commit()

        order_id = cursor.lastrowid
        logger.info(
            "Submitted paper order #%d: strategy=%d direction=%s type=%s qty=%d legs=%d",
            order_id, strategy_id, direction, order_type, quantity, len(legs),
        )
        return order_id

    async def try_fill(
        self,
        order_id: int,
        chains: dict[str, OptionsChain],
    ) -> list[SimulatedFill] | None:
        """Attempt to fill a pending order using live quotes.

        For market orders: fills immediately at simulated price.
        For limit orders: fills only if simulated net price meets limit.

        Returns list of SimulatedFill on success, None if cannot fill.
        Also records fills in the paper_fills table.
        """
        # Load order
        cursor = await self._db.execute(
            "SELECT id, strategy_id, order_type, direction, legs, quantity, "
            "limit_price, status, ticks_pending FROM paper_orders WHERE id = ?",
            (order_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            logger.warning("Order #%d not found", order_id)
            return None

        cols = ["id", "strategy_id", "order_type", "direction", "legs",
                "quantity", "limit_price", "status", "ticks_pending"]
        order = dict(zip(cols, row))

        if order["status"] != "pending":
            return None

        # Parse legs
        legs_data = json.loads(order["legs"])
        legs = [
            LegSpec(
                leg_name=ld["leg_name"],
                option_type=ld["option_type"],
                strike=ld["strike"],
                expiry=_parse_date(ld["expiry"]),
                action=ld["action"],
                quantity=ld.get("quantity", 1),
            )
            for ld in legs_data
        ]

        # Get chain (SPX is the primary ticker)
        chain = chains.get("SPX") or chains.get("SPY")
        if chain is None:
            # Try first available chain
            if chains:
                chain = next(iter(chains.values()))
            else:
                logger.warning("No chains available for fill simulation")
                # Increment ticks_pending
                await self._db.execute(
                    "UPDATE paper_orders SET ticks_pending = ticks_pending + 1 WHERE id = ?",
                    (order_id,),
                )
                await self._db.commit()
                return None

        # Simulate fills for all legs
        fills = self._fill_sim.simulate_spread_fill(legs, chain)
        if fills is None:
            # Cannot fill -- increment ticks_pending
            await self._db.execute(
                "UPDATE paper_orders SET ticks_pending = ticks_pending + 1 WHERE id = ?",
                (order_id,),
            )
            await self._db.commit()
            return None

        # Calculate net fill price (credit/debit of the spread)
        net_fill = _calculate_net_fill(fills, legs)
        total_slippage = sum(f.slippage for f in fills)

        # Limit order check: for sells (credit), net must be >= limit;
        # for buys (debit), net must be <= limit (in absolute terms)
        if order["order_type"] == "limit" and order["limit_price"] is not None:
            limit = order["limit_price"]
            if order["direction"] == "open":
                # Opening credit spread: net_fill should be >= limit (credit received)
                # Opening debit spread: net_fill should be <= limit (debit paid)
                # We use: if limit > 0 (credit), net_fill >= limit
                #         if limit < 0 (debit), net_fill <= limit (less negative OK)
                if limit > 0 and net_fill < limit:
                    await self._db.execute(
                        "UPDATE paper_orders SET ticks_pending = ticks_pending + 1 WHERE id = ?",
                        (order_id,),
                    )
                    await self._db.commit()
                    return None
                if limit < 0 and net_fill > limit:
                    await self._db.execute(
                        "UPDATE paper_orders SET ticks_pending = ticks_pending + 1 WHERE id = ?",
                        (order_id,),
                    )
                    await self._db.commit()
                    return None
            else:
                # Closing: inverse logic
                if limit > 0 and net_fill < limit:
                    await self._db.execute(
                        "UPDATE paper_orders SET ticks_pending = ticks_pending + 1 WHERE id = ?",
                        (order_id,),
                    )
                    await self._db.commit()
                    return None

        # Fill the order
        now = datetime.now().isoformat()
        await self._db.execute(
            """
            UPDATE paper_orders
            SET status = 'filled', filled_at = ?, fill_price = ?, slippage = ?
            WHERE id = ?
            """,
            (now, round(net_fill, 4), round(total_slippage, 4), order_id),
        )

        # Record individual leg fills
        for fill in fills:
            leg = next(l for l in legs if l.leg_name == fill.leg_name)
            await self._db.execute(
                """
                INSERT INTO paper_fills
                    (order_id, leg_name, option_type, strike, expiry, action,
                     quantity, fill_price, bid_at_fill, ask_at_fill, mid_at_fill,
                     iv_at_fill, delta_at_fill, filled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id, fill.leg_name, leg.option_type, leg.strike,
                    leg.expiry.isoformat(), leg.action, leg.quantity,
                    fill.fill_price, fill.bid, fill.ask, fill.mid,
                    fill.iv, fill.delta, now,
                ),
            )

        await self._db.commit()

        logger.info(
            "Filled paper order #%d: net=%.4f slippage=%.4f legs=%d",
            order_id, net_fill, total_slippage, len(fills),
        )
        return fills

    async def cancel_order(self, order_id: int, reason: str = "manual") -> None:
        """Cancel a pending order.

        Args:
            order_id: The order to cancel.
            reason: Reason for cancellation (stored in metadata).
        """
        now = datetime.now().isoformat()
        await self._db.execute(
            """
            UPDATE paper_orders
            SET status = 'cancelled', cancelled_at = ?,
                metadata = json_set(COALESCE(metadata, '{}'), '$.cancel_reason', ?)
            WHERE id = ? AND status = 'pending'
            """,
            (now, reason, order_id),
        )
        await self._db.commit()
        logger.info("Cancelled paper order #%d: %s", order_id, reason)

    async def expire_stale_orders(self) -> int:
        """Cancel orders pending for more than max_order_age_ticks.

        Returns the number of orders expired.
        """
        now = datetime.now().isoformat()
        max_age = self._config.max_order_age_ticks

        cursor = await self._db.execute(
            """
            UPDATE paper_orders
            SET status = 'expired', cancelled_at = ?,
                metadata = json_set(COALESCE(metadata, '{}'), '$.cancel_reason', 'stale')
            WHERE status = 'pending' AND ticks_pending >= ?
            """,
            (now, max_age),
        )
        await self._db.commit()

        expired = cursor.rowcount
        if expired > 0:
            logger.info("Expired %d stale paper orders (age >= %d ticks)", expired, max_age)
        return expired

    async def get_pending_orders(self) -> list[dict[str, Any]]:
        """Get all pending orders.

        Returns list of order dicts with parsed legs JSON.
        """
        cursor = await self._db.execute(
            """
            SELECT id, strategy_id, order_type, direction, legs, quantity,
                   limit_price, status, submitted_at, ticks_pending
            FROM paper_orders
            WHERE status = 'pending'
            ORDER BY submitted_at
            """
        )
        rows = await cursor.fetchall()
        cols = ["id", "strategy_id", "order_type", "direction", "legs",
                "quantity", "limit_price", "status", "submitted_at", "ticks_pending"]

        results = []
        for row in rows:
            result = dict(zip(cols, row))
            try:
                result["legs"] = json.loads(result["legs"])
            except (json.JSONDecodeError, TypeError):
                result["legs"] = []
            results.append(result)
        return results

    async def get_order(self, order_id: int) -> dict[str, Any] | None:
        """Get a single order by ID.

        Returns order dict with parsed legs, or None if not found.
        """
        cursor = await self._db.execute(
            """
            SELECT id, strategy_id, order_type, direction, legs, quantity,
                   limit_price, status, submitted_at, filled_at, cancelled_at,
                   fill_price, slippage, ticks_pending, metadata
            FROM paper_orders WHERE id = ?
            """,
            (order_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        cols = ["id", "strategy_id", "order_type", "direction", "legs",
                "quantity", "limit_price", "status", "submitted_at",
                "filled_at", "cancelled_at", "fill_price", "slippage",
                "ticks_pending", "metadata"]
        result = dict(zip(cols, row))
        try:
            result["legs"] = json.loads(result["legs"])
        except (json.JSONDecodeError, TypeError):
            result["legs"] = []
        try:
            result["metadata"] = json.loads(result["metadata"] or "{}")
        except (json.JSONDecodeError, TypeError):
            result["metadata"] = {}
        return result

    async def get_fills_for_order(self, order_id: int) -> list[dict[str, Any]]:
        """Get all fills for a specific order.

        Returns list of fill dicts.
        """
        cursor = await self._db.execute(
            """
            SELECT id, order_id, leg_name, option_type, strike, expiry,
                   action, quantity, fill_price, bid_at_fill, ask_at_fill,
                   mid_at_fill, iv_at_fill, delta_at_fill, filled_at
            FROM paper_fills
            WHERE order_id = ?
            ORDER BY id
            """,
            (order_id,),
        )
        rows = await cursor.fetchall()
        cols = ["id", "order_id", "leg_name", "option_type", "strike",
                "expiry", "action", "quantity", "fill_price", "bid_at_fill",
                "ask_at_fill", "mid_at_fill", "iv_at_fill", "delta_at_fill",
                "filled_at"]
        return [dict(zip(cols, row)) for row in rows]


def _calculate_net_fill(fills: list[SimulatedFill], legs: list[LegSpec]) -> float:
    """Calculate the net credit/debit of a spread fill.

    Sells produce positive (credit), buys produce negative (debit).
    Convention: net > 0 means net credit received.

    Args:
        fills: Simulated fill results for each leg.
        legs: Corresponding leg specs with action (buy/sell).

    Returns:
        Net credit/debit. Positive = net credit, negative = net debit.
    """
    leg_actions = {leg.leg_name: leg.action for leg in legs}
    net = 0.0
    for fill in fills:
        action = leg_actions.get(fill.leg_name, "buy")
        if action == "sell":
            net += fill.fill_price  # credit received
        else:
            net -= fill.fill_price  # debit paid
    return net


def _parse_date(date_str: str) -> "date":
    """Parse an ISO date string to a date object."""
    from datetime import date as date_type
    return date_type.fromisoformat(date_str)
