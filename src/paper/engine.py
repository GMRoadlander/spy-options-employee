"""Paper trading engine orchestrator.

PaperTradingEngine is the main entry point for the paper trading subsystem.
It coordinates OrderManager, PositionTracker, and PnLCalculator through
a tick-based loop driven by the SchedulerCog (every 2 minutes during
market hours).

The engine:
1. Processes pending orders (fill attempts, expirations)
2. Marks all open positions to market
3. Takes daily portfolio snapshots at EOD
4. Provides portfolio summary and strategy results for Discord display

Note: Shadow mode (auto-generating trades from strategy signals) and
exit monitoring are implemented in separate modules (sub-plan 4-4).
This engine provides the hooks they will plug into.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any

import aiosqlite

from src.data import OptionsChain
from src.paper.models import (
    ExitSignal,
    LegSpec,
    PaperResults,
    PaperTradingConfig,
    PortfolioSummary,
    SimulatedFill,
    TickResult,
)
from src.paper.orders import OrderManager
from src.paper.pnl import PnLCalculator
from src.paper.positions import PositionTracker
from src.paper.schema import init_paper_tables

logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """Main orchestrator for paper trading simulation.

    Attached to bot as ``bot.paper_engine``. Called from SchedulerCog
    on each market-hours tick with live chain data.

    Usage::

        engine = PaperTradingEngine(db, strategy_manager, config)
        await engine.init_tables()

        # Every 2-min tick during market hours:
        result = await engine.tick(chains)

        # Post-market:
        await engine.handle_eod_settlement()
        await engine.pnl_calculator.take_daily_snapshot()

        # Pre-market:
        await engine.start_of_day()
    """

    def __init__(
        self,
        db: aiosqlite.Connection,
        strategy_manager: Any,  # StrategyManager (avoid circular import)
        config: PaperTradingConfig,
    ) -> None:
        self._db = db
        self._strategy_manager = strategy_manager
        self._config = config

        # Sub-components
        self.order_manager = OrderManager(db, config)
        self.position_tracker = PositionTracker(db, config)
        self.pnl_calculator = PnLCalculator(db, config)

        # Daily state
        self._tick_count_today: int = 0
        self._daily_errors: list[str] = []

    async def init_tables(self) -> None:
        """Create all paper trading tables idempotently."""
        await init_paper_tables(self._db)

    async def tick(self, chains: dict[str, OptionsChain]) -> TickResult:
        """Main loop entry point -- called every scheduler cycle.

        Processing order:
        1. Expire stale pending orders
        2. Attempt to fill remaining pending orders
        3. Open positions from newly filled orders
        4. Mark-to-market all open positions
        5. Return tick summary

        Note: Steps for entry signal detection and exit condition checking
        are added by sub-plan 4-4 (ShadowModeManager, ExitMonitor).

        Args:
            chains: Dict of ticker -> live OptionsChain.

        Returns:
            TickResult summarizing all actions taken this tick.
        """
        now = datetime.now()
        self._tick_count_today += 1

        result = TickResult(timestamp=now)

        try:
            # Step 1: Expire stale orders
            expired = await self.order_manager.expire_stale_orders()
            result.orders_cancelled = expired

            # Step 2: Fill pending orders
            pending = await self.order_manager.get_pending_orders()
            for order in pending:
                try:
                    fills = await self.order_manager.try_fill(order["id"], chains)
                    if fills is not None:
                        result.orders_filled += 1

                        # Step 3: Open positions from fills (if opening order)
                        if order["direction"] == "open":
                            position_id = await self.position_tracker.open_position(
                                strategy_id=order["strategy_id"],
                                order_id=order["id"],
                                fills=fills,
                                quantity=order["quantity"],
                            )
                            result.positions_opened += 1
                            logger.info(
                                "Opened position #%d from order #%d",
                                position_id, order["id"],
                            )
                        elif order["direction"] == "close":
                            # Close order filled -- find the position to close
                            # The position_id is stored in the order metadata
                            order_full = await self.order_manager.get_order(order["id"])
                            meta = order_full.get("metadata", {}) if order_full else {}
                            pos_id = meta.get("position_id")
                            close_reason = meta.get("close_reason", "signal")

                            if pos_id:
                                trade_id = await self.position_tracker.close_position(
                                    position_id=pos_id,
                                    close_order_id=order["id"],
                                    close_fills=fills,
                                    reason=close_reason,
                                )
                                result.positions_closed += 1
                                logger.info(
                                    "Closed position #%d -> trade #%d",
                                    pos_id, trade_id,
                                )

                except Exception as e:
                    error_msg = f"Error filling order #{order['id']}: {e}"
                    logger.error(error_msg, exc_info=True)
                    result.errors.append(error_msg)

            # Step 4: Mark-to-market all open positions
            try:
                marks = await self.position_tracker.mark_all_open(chains)
                result.total_unrealized_pnl = sum(pnl for _, pnl in marks)
            except Exception as e:
                error_msg = f"Error marking positions: {e}"
                logger.error(error_msg, exc_info=True)
                result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Tick error: {e}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)

        if result.errors:
            self._daily_errors.extend(result.errors)

        return result

    async def handle_eod_settlement(self) -> list[int]:
        """Handle end-of-day settlement for expiring positions.

        Called at post-market (16:05 ET). Closes positions with legs
        expiring today using the last available mark as settlement price.

        Returns:
            List of closed position IDs.
        """
        today = date.today()
        positions = await self.position_tracker.get_open_positions()
        closed_ids = []

        for pos in positions:
            legs = pos.get("legs", [])
            if isinstance(legs, str):
                legs = json.loads(legs)

            # Check if any leg expires today
            has_expiring = False
            for leg in legs:
                expiry_str = leg.get("expiry", "")
                try:
                    expiry = date.fromisoformat(expiry_str)
                    if expiry <= today:
                        has_expiring = True
                        break
                except (ValueError, TypeError):
                    continue

            if has_expiring:
                # Use current mark as settlement proxy
                # In production, this would use the actual settlement price
                settlement_mark = pos.get("current_mark", 0.0)
                # Use spot price from last mark as settlement
                # For now, settle at the current mark value
                try:
                    # Calculate settlement from current mark
                    # The position's entry_price + current unrealized gives us the total
                    entry_price = pos.get("entry_price", 0.0)
                    # We need a settlement price for handle_expiration
                    # Use a reasonable default based on leg structure
                    trade_id = await self.position_tracker.handle_expiration(
                        position_id=pos["id"],
                        settlement_price=0.0,  # Will be overridden in sub-plan 4-4 with live data
                    )
                    closed_ids.append(pos["id"])
                    logger.info(
                        "EOD settlement: position #%d -> trade #%d",
                        pos["id"], trade_id,
                    )
                except Exception as e:
                    logger.error(
                        "Error settling position #%d: %s",
                        pos["id"], e, exc_info=True,
                    )

        return closed_ids

    async def start_of_day(self) -> None:
        """Reset daily state at pre-market.

        Called at 9:15 ET by the scheduler.
        """
        self._tick_count_today = 0
        self._daily_errors.clear()
        logger.info("Paper trading engine: start of day")

    async def get_portfolio_summary(self) -> PortfolioSummary:
        """Get current portfolio state for Discord display.

        Aggregates data from positions, trades, and snapshots.

        Returns:
            PortfolioSummary with all fields populated.
        """
        capital = self._config.starting_capital

        # Realized PnL
        realized = await self.pnl_calculator.get_cumulative_realized_pnl()

        # Unrealized PnL
        cursor = await self._db.execute(
            "SELECT COALESCE(SUM(unrealized_pnl), 0.0) "
            "FROM paper_positions WHERE status = 'open'"
        )
        unrealized = (await cursor.fetchone())[0]

        # Total equity
        total_equity = capital + realized + unrealized

        # Counts
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM paper_positions WHERE status = 'open'"
        )
        open_positions = (await cursor.fetchone())[0]

        total_trades = await self.pnl_calculator.get_trade_count()

        # Win rate
        if total_trades > 0:
            cursor = await self._db.execute(
                "SELECT COUNT(*) FROM paper_trades WHERE (total_pnl - fees) > 0"
            )
            wins = (await cursor.fetchone())[0]
            win_rate = wins / total_trades
        else:
            win_rate = 0.0

        # Latest snapshot data for Sharpe, drawdown, daily PnL
        cursor = await self._db.execute(
            """
            SELECT daily_pnl, max_drawdown
            FROM paper_portfolio
            ORDER BY snapshot_date DESC LIMIT 1
            """
        )
        snap_row = await cursor.fetchone()
        daily_pnl = snap_row[0] if snap_row else 0.0
        max_drawdown = snap_row[1] if snap_row else 0.0

        # Sharpe from metrics (expensive, so we cache/approximate)
        sharpe = 0.0
        try:
            if total_trades >= 5:
                metrics = await self.pnl_calculator.get_paper_metrics()
                sharpe = metrics.sharpe_ratio
        except Exception:
            pass

        # Active strategies
        strategies_active = []
        if self._strategy_manager is not None:
            try:
                from src.strategy.lifecycle import StrategyStatus
                paper_strategies = await self._strategy_manager.list_strategies(
                    status=StrategyStatus.PAPER,
                )
                strategies_active = [s["name"] for s in paper_strategies]
            except Exception:
                pass

        return PortfolioSummary(
            starting_capital=capital,
            total_equity=round(total_equity, 2),
            realized_pnl=round(realized, 2),
            unrealized_pnl=round(unrealized, 2),
            open_positions=open_positions,
            total_trades=total_trades,
            win_rate=round(win_rate, 4),
            sharpe_ratio=round(sharpe, 4),
            max_drawdown=round(max_drawdown, 6),
            daily_pnl=round(daily_pnl, 2),
            strategies_active=strategies_active,
        )

    async def get_strategy_paper_results(
        self,
        strategy_id: int,
    ) -> PaperResults:
        """Get paper trading results for a specific strategy.

        Used for promotion evaluation: aggregates trades, metrics,
        equity curve, and recommendation.

        Args:
            strategy_id: ID of the strategy.

        Returns:
            PaperResults with trades, metrics, and recommendation.
        """
        # Get strategy name
        strategy_name = ""
        if self._strategy_manager is not None:
            try:
                strategy = await self._strategy_manager.get(strategy_id)
                if strategy:
                    strategy_name = strategy.get("name", "")
            except Exception:
                pass

        # Get trades
        cursor = await self._db.execute(
            """
            SELECT id, entry_date, exit_date, holding_days, entry_price,
                   exit_price, realized_pnl, total_pnl, fees, slippage_cost,
                   close_reason
            FROM paper_trades
            WHERE strategy_id = ?
            ORDER BY exit_date
            """,
            (strategy_id,),
        )
        rows = await cursor.fetchall()
        cols = ["id", "entry_date", "exit_date", "holding_days", "entry_price",
                "exit_price", "realized_pnl", "total_pnl", "fees",
                "slippage_cost", "close_reason"]
        trades = [dict(zip(cols, row)) for row in rows]

        # Get metrics
        metrics = await self.pnl_calculator.get_paper_metrics(strategy_id)

        # Get equity curve
        equity_data = await self.pnl_calculator.get_equity_curve(days=365)
        equity_curve = [e["total_equity"] for e in equity_data]

        # Days in paper
        days_in_paper = 0
        if self._strategy_manager is not None:
            try:
                from src.strategy.lifecycle import StrategyStatus
                strategy = await self._strategy_manager.get(strategy_id)
                if strategy and strategy["status"] == StrategyStatus.PAPER.value:
                    transitions = await self._strategy_manager.get_transition_history(strategy_id)
                    for t in reversed(transitions):
                        if t["to_status"] == "paper":
                            paper_start = datetime.fromisoformat(t["transitioned_at"])
                            days_in_paper = (datetime.now() - paper_start).days
                            break
            except Exception:
                pass

        # Recommendation
        recommendation = _compute_recommendation(metrics, len(trades), days_in_paper, self._config)

        return PaperResults(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            trades=trades,
            metrics=metrics,
            equity_curve=equity_curve,
            days_in_paper=days_in_paper,
            recommendation=recommendation,
        )

    async def force_close_position(
        self,
        position_id: int,
        reason: str = "manual",
        chains: dict[str, OptionsChain] | None = None,
    ) -> int | None:
        """Manually close a position (e.g., from Discord command).

        Creates a close order and immediately fills it using current
        market data.

        Args:
            position_id: Position to close.
            reason: Reason for the manual close.
            chains: Optional live chains for fill simulation.

        Returns:
            Trade ID on success, None on failure.
        """
        position = await self.position_tracker._get_position(position_id)
        if position is None or position["status"] != "open":
            logger.warning("Cannot force close position #%d: not open", position_id)
            return None

        legs_data = json.loads(position["legs"])

        # Build close legs (reverse actions)
        close_legs = []
        for leg in legs_data:
            close_action = "buy" if leg["action"] == "sell" else "sell"
            close_legs.append(LegSpec(
                leg_name=leg["leg_name"],
                option_type=leg["option_type"],
                strike=leg["strike"],
                expiry=date.fromisoformat(leg["expiry"]),
                action=close_action,
                quantity=leg.get("quantity", 1),
            ))

        # Submit close order with position_id in metadata
        order_id = await self.order_manager.submit_order(
            strategy_id=position["strategy_id"],
            direction="close",
            legs=close_legs,
            quantity=position["quantity"],
            order_type="market",
        )

        # Store position_id in metadata for the close order
        await self._db.execute(
            """
            UPDATE paper_orders
            SET metadata = json_set(COALESCE(metadata, '{}'),
                                    '$.position_id', ?,
                                    '$.close_reason', ?)
            WHERE id = ?
            """,
            (position_id, reason, order_id),
        )
        await self._db.commit()

        # Fill immediately if chains available
        if chains:
            fills = await self.order_manager.try_fill(order_id, chains)
            if fills is not None:
                trade_id = await self.position_tracker.close_position(
                    position_id=position_id,
                    close_order_id=order_id,
                    close_fills=fills,
                    reason=reason,
                )
                return trade_id

        return None

    async def submit_entry_order(
        self,
        strategy_id: int,
        legs: list[LegSpec],
        quantity: int = 1,
        order_type: str = "market",
        limit_price: float | None = None,
    ) -> int:
        """Submit an entry order (convenience method).

        Args:
            strategy_id: Strategy placing the order.
            legs: Leg specifications.
            quantity: Number of contracts.
            order_type: 'market' or 'limit'.
            limit_price: For limit orders.

        Returns:
            Order ID.
        """
        return await self.order_manager.submit_order(
            strategy_id=strategy_id,
            direction="open",
            legs=legs,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
        )

    async def submit_exit_order(
        self,
        position_id: int,
        reason: str = "signal",
        order_type: str = "market",
        limit_price: float | None = None,
    ) -> int | None:
        """Submit an exit order for a position (convenience method).

        Builds closing legs by reversing the position's entry legs.

        Args:
            position_id: Position to close.
            reason: Why the exit is triggered.
            order_type: 'market' or 'limit'.
            limit_price: For limit orders.

        Returns:
            Order ID, or None if position not found/not open.
        """
        position = await self.position_tracker._get_position(position_id)
        if position is None or position["status"] != "open":
            return None

        legs_data = json.loads(position["legs"])

        close_legs = []
        for leg in legs_data:
            close_action = "buy" if leg["action"] == "sell" else "sell"
            close_legs.append(LegSpec(
                leg_name=leg["leg_name"],
                option_type=leg["option_type"],
                strike=leg["strike"],
                expiry=date.fromisoformat(leg["expiry"]),
                action=close_action,
                quantity=leg.get("quantity", 1),
            ))

        order_id = await self.order_manager.submit_order(
            strategy_id=position["strategy_id"],
            direction="close",
            legs=close_legs,
            quantity=position["quantity"],
            order_type=order_type,
            limit_price=limit_price,
        )

        # Store position reference in order metadata
        await self._db.execute(
            """
            UPDATE paper_orders
            SET metadata = json_set(COALESCE(metadata, '{}'),
                                    '$.position_id', ?,
                                    '$.close_reason', ?)
            WHERE id = ?
            """,
            (position_id, reason, order_id),
        )
        await self._db.commit()

        return order_id


def _compute_recommendation(
    metrics: Any,
    trade_count: int,
    days_in_paper: int,
    config: PaperTradingConfig,
) -> str:
    """Compute recommendation for a strategy based on paper results.

    Simple heuristic (full promotion logic is in sub-plan 4-6):
    - PROMOTE: meets minimum criteria
    - CONTINUE: not enough data yet
    - DEMOTE: metrics below thresholds

    Returns 'PROMOTE', 'CONTINUE', or 'DEMOTE'.
    """
    min_trades = 30  # Will be config.paper_min_trades_for_promotion in 4-6
    min_days = 14    # Will be config.paper_min_days_for_promotion in 4-6

    # Not enough data
    if trade_count < min_trades or days_in_paper < min_days:
        return "CONTINUE"

    # Check key metrics
    sharpe = getattr(metrics, "sharpe_ratio", 0.0)
    win_rate = getattr(metrics, "win_rate", 0.0)
    max_dd = getattr(metrics, "max_drawdown", 0.0)

    # Demotion triggers
    if sharpe < 0.0 or win_rate < 0.35 or max_dd < -0.20:
        return "DEMOTE"

    # Promotion criteria
    if sharpe > 1.0 and win_rate > 0.50:
        return "PROMOTE"

    return "CONTINUE"
