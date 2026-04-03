"""Exit monitor for paper trading positions.

ExitMonitor checks all open positions against their strategy's exit rules
and generates ExitSignal objects when conditions are met. It also handles
AM/PM settlement logic for SPX options.

Exit conditions checked (in order):
1. Expiration: any leg expiring today -> immediate
2. Profit target: unrealized >= max_profit * target_pct
3. Stop loss: unrealized <= -max_profit * stop_loss_pct
4. DTE exit: days to nearest expiry <= dte_close
5. Time stop: days held >= time_stop_days

Settlement handling:
- PM-settled (SPXW, 0DTE): auto-close at 16:00 ET using last quote
- AM-settled (SPX monthly, 3rd Friday): auto-close Thursday EOD
- Detection: 3rd Friday = AM, all others = PM
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, time, timedelta
from typing import Any

from src.data import OptionsChain
from src.paper.models import ExitSignal, PaperTradingConfig
from src.utils import ET, now_et as _now_et

logger = logging.getLogger(__name__)


def _is_third_friday(d: date) -> bool:
    """Check if a date is the 3rd Friday of its month.

    AM-settled SPX options expire on the 3rd Friday of the month.
    All other expiry dates are PM-settled (SPXW).
    """
    if d.weekday() != 4:  # Friday = 4
        return False
    # Count Fridays in the month up to this date
    friday_count = 0
    for day in range(1, d.day + 1):
        if date(d.year, d.month, day).weekday() == 4:
            friday_count += 1
    return friday_count == 3


def _get_settlement_type(expiry: date) -> str:
    """Determine settlement type for an expiry date.

    Returns 'am' for 3rd Friday (monthly SPX), 'pm' for all others (SPXW).
    """
    return "am" if _is_third_friday(expiry) else "pm"


class ExitMonitor:
    """Monitors open positions and generates exit signals.

    Called by PaperTradingEngine on each tick to check all open positions
    against their strategy's exit rules. Produces ExitSignal objects that
    the engine uses to submit close orders.

    Also handles end-of-day settlement for expiring positions, correctly
    distinguishing between AM-settled (3rd Friday) and PM-settled (all
    other dates) SPX options.

    Usage::

        monitor = ExitMonitor(db, strategy_manager, position_tracker, config)
        signals = await monitor.check_all_positions(chains)
        for signal in signals:
            await engine.submit_exit_order(signal.position_id, reason=signal.reason)
    """

    def __init__(
        self,
        db: Any,  # aiosqlite.Connection
        strategy_manager: Any,  # StrategyManager
        position_tracker: Any,  # PositionTracker
        config: PaperTradingConfig,
    ) -> None:
        self._db = db
        self._strategy_manager = strategy_manager
        self._position_tracker = position_tracker
        self._config = config

        # Cache strategy templates to avoid repeated DB/YAML lookups
        self._template_cache: dict[int, Any] = {}

    async def check_all_positions(
        self,
        chains: dict[str, OptionsChain],
    ) -> list[ExitSignal]:
        """Check every open position against exit rules.

        Iterates all open positions and checks each against the strategy's
        exit rules in priority order: expiration > profit target > stop loss >
        DTE exit > time stop.

        Args:
            chains: Dict of ticker -> live OptionsChain.

        Returns:
            List of ExitSignal objects for positions that should be closed.
        """
        signals: list[ExitSignal] = []

        try:
            positions = await self._position_tracker.get_open_positions()
        except Exception as exc:
            logger.error("Failed to load open positions: %s", exc)
            return signals

        today = date.today()
        now = _now_et()

        for position in positions:
            try:
                signal = await self._check_position(position, chains, today, now)
                if signal is not None:
                    signals.append(signal)
            except Exception as exc:
                logger.error(
                    "Error checking exit for position #%d: %s",
                    position["id"],
                    exc,
                    exc_info=True,
                )

        if signals:
            logger.info(
                "Exit monitor: %d exit signals generated (%s)",
                len(signals),
                ", ".join(f"#{s.position_id}:{s.reason}" for s in signals),
            )

        return signals

    async def _check_position(
        self,
        position: dict[str, Any],
        chains: dict[str, OptionsChain],
        today: date,
        now: datetime,
    ) -> ExitSignal | None:
        """Check a single position against all exit conditions.

        Returns an ExitSignal if any exit condition is met, None otherwise.
        Checks are evaluated in priority order.
        """
        position_id = position["id"]
        strategy_id = position["strategy_id"]

        # Parse legs
        legs = position.get("legs", [])
        if isinstance(legs, str):
            legs = json.loads(legs)

        # Get expiry dates from legs
        expiries = self._get_leg_expiries(legs)

        # Check 1: Expiration -- any leg expiring today
        for expiry in expiries:
            if expiry <= today:
                return ExitSignal(
                    position_id=position_id,
                    reason="expiration",
                    urgency="immediate",
                )

        # Load the strategy's exit rules
        exit_rule = await self._get_exit_rule(strategy_id)

        # Check 2: Profit target
        max_profit = position.get("max_profit", 0.0)
        unrealized_pnl = position.get("unrealized_pnl", 0.0)

        if max_profit > 0 and exit_rule is not None:
            profit_target_pct = exit_rule.profit_target_pct
            if unrealized_pnl >= max_profit * profit_target_pct:
                return ExitSignal(
                    position_id=position_id,
                    reason="profit_target",
                    urgency="normal",
                )

        # Check 3: Stop loss
        if max_profit > 0 and exit_rule is not None:
            stop_loss_pct = exit_rule.stop_loss_pct
            # Stop loss: loss exceeds stop_loss_pct * max_profit
            if unrealized_pnl <= -(max_profit * stop_loss_pct):
                return ExitSignal(
                    position_id=position_id,
                    reason="stop_loss",
                    urgency="immediate",
                )

        # Check 4: DTE exit
        if exit_rule is not None and expiries:
            nearest_expiry = min(expiries)
            dte_remaining = (nearest_expiry - today).days
            if dte_remaining <= exit_rule.dte_close and exit_rule.dte_close > 0:
                return ExitSignal(
                    position_id=position_id,
                    reason="dte_exit",
                    urgency="normal",
                )

        # Check 5: Time stop
        if exit_rule is not None and exit_rule.time_stop_days is not None:
            opened_at_str = position.get("opened_at", "")
            if opened_at_str:
                try:
                    from src.utils import parse_dt
                    opened_at = parse_dt(opened_at_str)
                    days_held = (_now_et() - opened_at).days
                    if days_held >= exit_rule.time_stop_days:
                        return ExitSignal(
                            position_id=position_id,
                            reason="time_stop",
                            urgency="normal",
                        )
                except (ValueError, TypeError):
                    pass

        return None

    async def handle_settlements(
        self,
        chains: dict[str, OptionsChain],
    ) -> list[int]:
        """Handle end-of-day settlement for expiring positions.

        Settlement rules:
        - PM-settled (SPXW, 0DTE): auto-close at 16:00 ET using last quote
        - AM-settled (SPX monthly, 3rd Friday): auto-close Thursday EOD
          (the Thursday before the 3rd Friday)

        This method is called at post-market (16:05 ET) by the engine.

        Args:
            chains: Dict of ticker -> live OptionsChain for settlement pricing.

        Returns:
            List of closed position IDs.
        """
        closed_ids: list[int] = []
        today = date.today()

        try:
            positions = await self._position_tracker.get_open_positions()
        except Exception as exc:
            logger.error("Failed to load positions for settlement: %s", exc)
            return closed_ids

        # Get the spot price for settlement calculation
        chain = chains.get("SPX") or chains.get("SPY")
        if chain is None and chains:
            chain = next(iter(chains.values()))

        spot_price = chain.spot_price if chain else 0.0

        for position in positions:
            try:
                settlement_result = await self._check_settlement(
                    position, today, spot_price, chain,
                )
                if settlement_result is not None:
                    closed_ids.append(settlement_result)
            except Exception as exc:
                logger.error(
                    "Error settling position #%d: %s",
                    position["id"],
                    exc,
                    exc_info=True,
                )

        if closed_ids:
            logger.info(
                "Settlement: closed %d positions (%s)",
                len(closed_ids),
                ", ".join(f"#{pid}" for pid in closed_ids),
            )

        return closed_ids

    async def _check_settlement(
        self,
        position: dict[str, Any],
        today: date,
        spot_price: float,
        chain: OptionsChain | None,
    ) -> int | None:
        """Check if a position should be settled today.

        PM-settled: Positions with SPXW (non-3rd-Friday) expiry today
                    settle at 16:00 ET using the last available quote.
        AM-settled: Positions with 3rd Friday expiry settle Thursday EOD
                    (the day before the 3rd Friday).

        Returns position_id if settled, None otherwise.
        """
        legs = position.get("legs", [])
        if isinstance(legs, str):
            legs = json.loads(legs)

        expiries = self._get_leg_expiries(legs)
        if not expiries:
            return None

        should_settle = False

        for expiry in expiries:
            settlement_type = _get_settlement_type(expiry)

            if settlement_type == "pm":
                # PM-settled: settle on expiry day
                if expiry <= today:
                    should_settle = True
                    break
            elif settlement_type == "am":
                # AM-settled: settle Thursday EOD (day before 3rd Friday)
                thursday_before = expiry - timedelta(days=1)
                if today >= thursday_before:
                    should_settle = True
                    break

        if not should_settle:
            return None

        # Settle the position using spot price
        try:
            trade_id = await self._position_tracker.handle_expiration(
                position_id=position["id"],
                settlement_price=spot_price,
            )
            logger.info(
                "Settled position #%d at spot=%.2f -> trade #%d",
                position["id"],
                spot_price,
                trade_id,
            )
            return position["id"]
        except Exception as exc:
            logger.error(
                "Failed to settle position #%d: %s",
                position["id"],
                exc,
                exc_info=True,
            )
            return None

    async def _get_exit_rule(self, strategy_id: int) -> Any:
        """Get exit rule for a strategy, with caching.

        Loads the strategy's template YAML and extracts the ExitRule.
        Results are cached to avoid repeated YAML parsing.

        Returns ExitRule or None if template cannot be loaded.
        """
        if strategy_id in self._template_cache:
            template = self._template_cache[strategy_id]
            return template.exit if template else None

        template = None
        if self._strategy_manager is not None:
            try:
                strategy = await self._strategy_manager.get(strategy_id)
                if strategy and strategy.get("template_yaml"):
                    template = self._load_template(strategy["template_yaml"])
            except Exception as exc:
                logger.warning(
                    "Failed to load template for strategy #%d: %s",
                    strategy_id,
                    exc,
                )

        self._template_cache[strategy_id] = template
        return template.exit if template else None

    def _load_template(self, template_yaml: str) -> Any:
        """Load a StrategyTemplate from a YAML string or file path."""
        try:
            from src.strategy.loader import StrategyLoader

            loader = StrategyLoader()

            if template_yaml.endswith((".yaml", ".yml")):
                return loader.load_yaml(template_yaml)

            import yaml

            raw = yaml.safe_load(template_yaml)
            if isinstance(raw, dict):
                return loader._dict_to_template(raw)

            return None
        except Exception as exc:
            logger.warning("Failed to load strategy template: %s", exc)
            return None

    def _get_leg_expiries(self, legs: list[dict]) -> list[date]:
        """Extract expiry dates from position legs.

        Returns a list of unique expiry dates parsed from the legs JSON.
        """
        expiries: list[date] = []
        seen: set[str] = set()

        for leg in legs:
            expiry_str = leg.get("expiry", "")
            if expiry_str and expiry_str not in seen:
                seen.add(expiry_str)
                try:
                    if isinstance(expiry_str, str):
                        expiries.append(date.fromisoformat(expiry_str))
                    else:
                        expiries.append(expiry_str)
                except (ValueError, TypeError):
                    continue

        return expiries

    def clear_template_cache(self) -> None:
        """Clear the template cache. Called on start of day."""
        self._template_cache.clear()

    @staticmethod
    def is_0dte_blocked() -> bool:
        """Check if new 0DTE entries should be blocked (after 3:00 PM ET).

        The 3:00 PM rule blocks new 0DTE position entries after 15:00 ET
        to avoid excessive gamma risk near close.

        Returns:
            True if 0DTE entries should be blocked.
        """
        now = _now_et()
        return now.time() >= time(15, 0)
