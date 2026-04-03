"""Position tracking for the paper trading engine.

PositionTracker manages open positions: opening from fills, mark-to-market
using live quotes, closing with trade record creation, and expiration
handling for cash-settled SPX options.

Positions are tracked per-spread (not per-leg). Individual legs are stored
as JSON within each position record. Mark-to-market uses live bid/ask mid.
Max profit/max loss are calculated from spread structure at open.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any

import aiosqlite

from src.data import OptionContract, OptionsChain
from src.paper.models import PaperTradingConfig, SimulatedFill
from src.utils import now_et, parse_dt

logger = logging.getLogger(__name__)


class PositionTracker:
    """Tracks open paper positions with mark-to-market updates.

    Positions flow: open -> marked (repeatedly) -> closed/expired.
    Each position represents a complete spread entry (all legs together).
    """

    def __init__(
        self,
        db: aiosqlite.Connection,
        config: PaperTradingConfig,
    ) -> None:
        self._db = db
        self._config = config

    async def open_position(
        self,
        strategy_id: int,
        order_id: int,
        fills: list[SimulatedFill],
        quantity: int,
    ) -> int:
        """Create a new open position from fills.

        Calculates entry price (net credit/debit), max profit, and max loss
        from the fill data and spread structure.

        Args:
            strategy_id: ID of the strategy that owns this position.
            order_id: ID of the opening order.
            fills: List of simulated fills for each leg.
            quantity: Number of contracts.

        Returns:
            The new position ID.
        """
        now = now_et().isoformat()

        # Build legs detail from fills + the order's leg data
        fills_cursor = await self._db.execute(
            """
            SELECT leg_name, option_type, strike, expiry, action,
                   quantity, fill_price
            FROM paper_fills WHERE order_id = ?
            """,
            (order_id,),
        )
        fill_rows = await fills_cursor.fetchall()
        fill_cols = ["leg_name", "option_type", "strike", "expiry",
                     "action", "quantity", "fill_price"]
        legs_detail = [dict(zip(fill_cols, row)) for row in fill_rows]

        # Calculate entry price from fill data
        # Convention: sell legs produce credit (+), buy legs produce debit (-)
        entry_price = 0.0
        for leg in legs_detail:
            if leg["action"] == "sell":
                entry_price += leg["fill_price"]
            else:
                entry_price -= leg["fill_price"]

        # Calculate max profit and max loss from spread structure
        max_profit, max_loss = _calculate_max_profit_loss(
            legs_detail, entry_price, self._config.spx_multiplier, quantity,
        )

        legs_json = json.dumps(legs_detail)

        cursor = await self._db.execute(
            """
            INSERT INTO paper_positions
                (strategy_id, open_order_id, status, legs, entry_price,
                 quantity, max_profit, max_loss, current_mark,
                 unrealized_pnl, opened_at)
            VALUES (?, ?, 'open', ?, ?, ?, ?, ?, ?, 0.0, ?)
            """,
            (
                strategy_id, order_id, legs_json, round(entry_price, 4),
                quantity, round(max_profit, 2), round(max_loss, 2),
                round(entry_price, 4), now,
            ),
        )
        await self._db.commit()

        position_id = cursor.lastrowid
        logger.info(
            "Opened position #%d: strategy=%d entry=%.4f max_profit=%.2f max_loss=%.2f",
            position_id, strategy_id, entry_price, max_profit, max_loss,
        )
        return position_id

    async def mark_to_market(
        self,
        position_id: int,
        chain: OptionsChain,
    ) -> float:
        """Update position mark using live quotes.

        Recalculates the current market value of the spread using mid-prices,
        then computes unrealized PnL relative to entry price.

        Args:
            position_id: Position to update.
            chain: Live options chain with current quotes.

        Returns:
            Updated unrealized PnL.
        """
        position = await self._get_position(position_id)
        if position is None or position["status"] != "open":
            return 0.0

        legs = json.loads(position["legs"])
        entry_price = position["entry_price"]
        quantity = position["quantity"]

        # Calculate current mark (what we'd pay/receive to close now)
        # To close: reverse each leg's action. If we sold at open, we buy back.
        # Current mark = cost to close = sum of (buy_back_price for sells) - (sell_price for buys)
        current_mark = 0.0
        valid_marks = 0
        for leg in legs:
            contract = _find_contract_in_chain(
                chain, leg["option_type"], leg["strike"], leg["expiry"],
            )
            if contract is None:
                # Use last fill price as fallback for missing contracts
                if leg["action"] == "sell":
                    current_mark -= leg["fill_price"]
                else:
                    current_mark += leg["fill_price"]
                continue

            valid_marks += 1
            mid = contract.mid
            # To close, we reverse: if we sold at open, we buy back at mid
            if leg["action"] == "sell":
                current_mark -= mid  # cost to buy back
            else:
                current_mark += mid  # credit from selling

        # Unrealized PnL = entry_price + current_mark (cost to close)
        # If entry was credit (+) and close costs less than received -> profit
        # Example: sold for $2.00 (entry=+2.00), buy back for $1.00 (mark=-1.00)
        #          unrealized = 2.00 + (-1.00) = $1.00 profit per unit
        unrealized_per_unit = entry_price + current_mark
        unrealized_pnl = unrealized_per_unit * quantity * self._config.spx_multiplier

        now = now_et().isoformat()
        await self._db.execute(
            """
            UPDATE paper_positions
            SET current_mark = ?, unrealized_pnl = ?, last_mark_at = ?
            WHERE id = ?
            """,
            (round(current_mark, 4), round(unrealized_pnl, 2), now, position_id),
        )
        await self._db.commit()

        return round(unrealized_pnl, 2)

    async def mark_all_open(
        self,
        chains: dict[str, OptionsChain],
    ) -> list[tuple[int, float]]:
        """Mark all open positions to market.

        Args:
            chains: Dict of ticker -> live OptionsChain.

        Returns:
            List of (position_id, unrealized_pnl) tuples.
        """
        chain = chains.get("SPX") or chains.get("SPY")
        if chain is None and chains:
            chain = next(iter(chains.values()))
        if chain is None:
            return []

        positions = await self.get_open_positions()
        results = []
        for pos in positions:
            pnl = await self.mark_to_market(pos["id"], chain)
            results.append((pos["id"], pnl))
        return results

    async def close_position(
        self,
        position_id: int,
        close_order_id: int,
        close_fills: list[SimulatedFill],
        reason: str,
    ) -> int:
        """Close a position and create a trade record.

        Args:
            position_id: Position to close.
            close_order_id: ID of the closing order.
            close_fills: Fill results for the closing order.
            reason: Why the position was closed (e.g., 'profit_target').

        Returns:
            The new trade ID.
        """
        position = await self._get_position(position_id)
        if position is None:
            raise ValueError(f"Position #{position_id} not found")

        now = now_et()
        entry_legs = json.loads(position["legs"])
        entry_price = position["entry_price"]
        quantity = position["quantity"]

        # Calculate exit price from close fills
        # Close reverses: sells become buys, buys become sells
        # The close order's fill price is already the net of the close
        close_order = await self._db.execute(
            "SELECT fill_price FROM paper_orders WHERE id = ?",
            (close_order_id,),
        )
        close_row = await close_order.fetchone()
        exit_price = close_row[0] if close_row else 0.0

        # PnL calculation
        # entry_price is net credit/debit at open (+ = credit, - = debit)
        # exit_price is net credit/debit at close (from closing order)
        # For close: if we opened by selling (credit), we close by buying back (debit)
        # realized_pnl per unit = entry_price + exit_price
        realized_pnl = entry_price + exit_price
        total_pnl = realized_pnl * quantity * self._config.spx_multiplier

        # Calculate fees: fee_per_contract * legs * quantity * 2 (open + close)
        num_legs = len(entry_legs)
        fees = self._config.fee_per_contract * num_legs * quantity * 2

        # Slippage cost (from both opening and closing orders)
        open_order = await self._db.execute(
            "SELECT slippage FROM paper_orders WHERE id = ?",
            (position["open_order_id"],),
        )
        open_row = await open_order.fetchone()
        open_slippage = open_row[0] if open_row and open_row[0] else 0.0

        close_slippage_q = await self._db.execute(
            "SELECT slippage FROM paper_orders WHERE id = ?",
            (close_order_id,),
        )
        close_slippage_row = await close_slippage_q.fetchone()
        close_slippage = close_slippage_row[0] if close_slippage_row and close_slippage_row[0] else 0.0

        slippage_cost = (open_slippage + close_slippage) * quantity * self._config.spx_multiplier
        net_pnl = total_pnl - fees

        # Holding days
        opened_at = parse_dt(position["opened_at"])
        holding_days = (now - opened_at).days

        # Determine settlement type
        settlement_type = _determine_settlement_type(entry_legs)

        # Build legs detail for trade record
        close_fills_data = await self._db.execute(
            """
            SELECT leg_name, option_type, strike, expiry, action,
                   quantity, fill_price
            FROM paper_fills WHERE order_id = ?
            """,
            (close_order_id,),
        )
        close_fill_rows = await close_fills_data.fetchall()
        close_legs = [
            dict(zip(
                ["leg_name", "option_type", "strike", "expiry", "action",
                 "quantity", "fill_price"],
                row,
            ))
            for row in close_fill_rows
        ]

        legs_detail = json.dumps({
            "entry": entry_legs,
            "exit": close_legs,
        })

        # Create trade record + update position in explicit transaction
        # to prevent partial writes on crash (trade exists but position not closed)
        await self._db.execute("BEGIN IMMEDIATE")
        try:
            trade_cursor = await self._db.execute(
                """
                INSERT INTO paper_trades
                    (strategy_id, position_id, entry_date, exit_date,
                     holding_days, entry_price, exit_price, realized_pnl,
                     total_pnl, fees, slippage_cost, settlement_type,
                     close_reason, legs_detail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    position["strategy_id"], position_id,
                    position["opened_at"][:10], now.isoformat()[:10],
                    holding_days, round(entry_price, 4), round(exit_price, 4),
                    round(realized_pnl, 4), round(total_pnl, 2),
                    round(fees, 2), round(slippage_cost, 2),
                    settlement_type, reason, legs_detail,
                ),
            )

            trade_id = trade_cursor.lastrowid

            # Update position status
            await self._db.execute(
                """
                UPDATE paper_positions
                SET status = 'closed', closed_at = ?, close_reason = ?,
                    close_order_id = ?, unrealized_pnl = 0.0
                WHERE id = ?
                """,
                (now.isoformat(), reason, close_order_id, position_id),
            )
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise

        logger.info(
            "Closed position #%d: trade #%d pnl=%.2f fees=%.2f net=%.2f reason=%s",
            position_id, trade_id, total_pnl, fees, net_pnl, reason,
        )
        return trade_id

    async def get_open_positions(
        self,
        strategy_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get all open positions, optionally filtered by strategy.

        Args:
            strategy_id: Optional strategy filter.

        Returns:
            List of position dicts with parsed legs.
        """
        if strategy_id is not None:
            cursor = await self._db.execute(
                """
                SELECT id, strategy_id, open_order_id, status, legs,
                       entry_price, quantity, max_profit, max_loss,
                       current_mark, unrealized_pnl, last_mark_at,
                       opened_at, closed_at, close_reason
                FROM paper_positions
                WHERE status = 'open' AND strategy_id = ?
                ORDER BY opened_at
                """,
                (strategy_id,),
            )
        else:
            cursor = await self._db.execute(
                """
                SELECT id, strategy_id, open_order_id, status, legs,
                       entry_price, quantity, max_profit, max_loss,
                       current_mark, unrealized_pnl, last_mark_at,
                       opened_at, closed_at, close_reason
                FROM paper_positions
                WHERE status = 'open'
                ORDER BY opened_at
                """
            )

        rows = await cursor.fetchall()
        cols = ["id", "strategy_id", "open_order_id", "status", "legs",
                "entry_price", "quantity", "max_profit", "max_loss",
                "current_mark", "unrealized_pnl", "last_mark_at",
                "opened_at", "closed_at", "close_reason"]

        results = []
        for row in rows:
            result = dict(zip(cols, row))
            try:
                result["legs"] = json.loads(result["legs"])
            except (json.JSONDecodeError, TypeError):
                result["legs"] = []
            results.append(result)
        return results

    async def handle_expiration(
        self,
        position_id: int,
        settlement_price: float,
    ) -> int:
        """Handle expiration/settlement for a position.

        For SPX options (European, cash-settled): calculates intrinsic value
        of each leg at the settlement price and records the trade.

        Args:
            position_id: Position expiring/settling.
            settlement_price: SPX settlement price.

        Returns:
            The new trade ID.
        """
        position = await self._get_position(position_id)
        if position is None:
            raise ValueError(f"Position #{position_id} not found")

        now = now_et()
        entry_legs = json.loads(position["legs"])
        entry_price = position["entry_price"]
        quantity = position["quantity"]

        # Calculate settlement value: intrinsic value of each leg at settlement
        # For calls: max(0, settlement - strike)
        # For puts: max(0, strike - settlement)
        # Then: sell legs produce liability (pay intrinsic), buy legs produce asset (receive intrinsic)
        exit_value = 0.0
        for leg in entry_legs:
            strike = leg["strike"]
            opt_type = leg["option_type"]
            action = leg["action"]

            if opt_type == "call":
                intrinsic = max(0.0, settlement_price - strike)
            else:
                intrinsic = max(0.0, strike - settlement_price)

            # At settlement: if we sold, we owe intrinsic value (debit)
            # if we bought, we receive intrinsic value (credit)
            if action == "sell":
                exit_value -= intrinsic
            else:
                exit_value += intrinsic

        # PnL: entry + exit (exit is the settlement outcome)
        realized_pnl = entry_price + exit_value
        total_pnl = realized_pnl * quantity * self._config.spx_multiplier

        num_legs = len(entry_legs)
        # Only opening fees for expired positions (no close order)
        fees = self._config.fee_per_contract * num_legs * quantity

        settlement_type = _determine_settlement_type(entry_legs)

        opened_at = parse_dt(position["opened_at"])
        holding_days = (now - opened_at).days

        legs_detail = json.dumps({
            "entry": entry_legs,
            "exit": {"settlement_price": settlement_price, "type": "expiration"},
        })

        # Atomic transaction: trade record + position update together
        await self._db.execute("BEGIN IMMEDIATE")
        try:
            trade_cursor = await self._db.execute(
                """
                INSERT INTO paper_trades
                    (strategy_id, position_id, entry_date, exit_date,
                     holding_days, entry_price, exit_price, realized_pnl,
                     total_pnl, fees, slippage_cost, settlement_type,
                     close_reason, legs_detail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, ?, 'expiration', ?)
                """,
                (
                    position["strategy_id"], position_id,
                    position["opened_at"][:10], now.isoformat()[:10],
                    holding_days, round(entry_price, 4), round(exit_value, 4),
                    round(realized_pnl, 4), round(total_pnl, 2),
                    round(fees, 2), settlement_type, legs_detail,
                ),
            )

            trade_id = trade_cursor.lastrowid

            await self._db.execute(
                """
                UPDATE paper_positions
                SET status = 'expired', closed_at = ?, close_reason = 'expiration',
                    unrealized_pnl = 0.0
                WHERE id = ?
                """,
                (now.isoformat(), position_id),
            )
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise

        logger.info(
            "Expired position #%d: trade #%d settlement=%.2f pnl=%.2f",
            position_id, trade_id, settlement_price, total_pnl,
        )
        return trade_id

    async def _get_position(self, position_id: int) -> dict[str, Any] | None:
        """Get a single position by ID."""
        cursor = await self._db.execute(
            """
            SELECT id, strategy_id, open_order_id, status, legs,
                   entry_price, quantity, max_profit, max_loss,
                   current_mark, unrealized_pnl, last_mark_at,
                   opened_at, closed_at, close_reason, close_order_id
            FROM paper_positions WHERE id = ?
            """,
            (position_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        cols = ["id", "strategy_id", "open_order_id", "status", "legs",
                "entry_price", "quantity", "max_profit", "max_loss",
                "current_mark", "unrealized_pnl", "last_mark_at",
                "opened_at", "closed_at", "close_reason", "close_order_id"]
        return dict(zip(cols, row))


def _calculate_max_profit_loss(
    legs: list[dict],
    entry_price: float,
    multiplier: float,
    quantity: int,
) -> tuple[float, float]:
    """Calculate max profit and max loss for a spread position.

    For defined-risk strategies (verticals, iron condors, butterflies),
    max loss is bounded by the spread width minus premium received.
    For credit spreads: max profit = premium, max loss = width - premium.
    For debit spreads: max profit = width - premium, max loss = premium.

    Args:
        legs: List of leg dicts with strike, action, option_type.
        entry_price: Net credit/debit at entry (+ = credit).
        multiplier: SPX contract multiplier ($100).
        quantity: Number of contracts.

    Returns:
        (max_profit, max_loss) in USD including multiplier.
    """
    if not legs:
        return 0.0, 0.0

    # Separate by option type
    calls = [l for l in legs if l["option_type"] == "call"]
    puts = [l for l in legs if l["option_type"] == "put"]

    # Calculate spread width for each side
    call_width = _get_spread_width(calls)
    put_width = _get_spread_width(puts)

    # For iron condors and similar: max risk is the widest side minus premium
    max_width = max(call_width, put_width)

    if entry_price > 0:
        # Credit spread/condor
        max_profit = entry_price * multiplier * quantity
        if max_width > 0:
            max_loss = (max_width - entry_price) * multiplier * quantity
        else:
            # No spread width calculable, use entry as estimate
            max_loss = entry_price * multiplier * quantity
    else:
        # Debit spread
        max_profit = (max_width + entry_price) * multiplier * quantity if max_width > 0 else abs(entry_price) * multiplier * quantity
        max_loss = abs(entry_price) * multiplier * quantity

    return round(max_profit, 2), round(max_loss, 2)


def _get_spread_width(legs: list[dict]) -> float:
    """Get the width of a vertical spread from its legs.

    Width = difference between the highest and lowest strikes.
    Returns 0 if fewer than 2 legs.
    """
    if len(legs) < 2:
        return 0.0
    strikes = [l["strike"] for l in legs]
    return max(strikes) - min(strikes)


def _find_contract_in_chain(
    chain: OptionsChain,
    option_type: str,
    strike: float,
    expiry_str: str,
) -> OptionContract | None:
    """Find a matching contract in the chain by type, strike, and expiry."""
    from datetime import date as date_type

    if isinstance(expiry_str, str):
        expiry = date_type.fromisoformat(expiry_str)
    else:
        expiry = expiry_str

    for contract in chain.contracts:
        if (
            contract.option_type == option_type
            and contract.strike == strike
            and contract.expiry == expiry
        ):
            return contract
    return None


def _determine_settlement_type(legs: list[dict]) -> str:
    """Determine if position is AM or PM settled.

    AM settlement: 3rd Friday of month (monthly SPX options).
    PM settlement: all other dates (SPXW weekly/daily/0DTE).

    Returns 'am' or 'pm'.
    """
    from datetime import date as date_type
    import calendar

    for leg in legs:
        expiry_str = leg.get("expiry", "")
        if isinstance(expiry_str, str):
            try:
                expiry = date_type.fromisoformat(expiry_str)
            except ValueError:
                continue
        else:
            expiry = expiry_str

        # Check if this is the 3rd Friday of the month
        if _is_third_friday(expiry):
            return "am"

    return "pm"


def _is_third_friday(d: date) -> bool:
    """Check if a date is the 3rd Friday of its month."""
    import calendar
    if d.weekday() != 4:  # Friday = 4
        return False
    # Count Fridays up to this date
    friday_count = 0
    for day in range(1, d.day + 1):
        if date(d.year, d.month, day).weekday() == 4:
            friday_count += 1
    return friday_count == 3
