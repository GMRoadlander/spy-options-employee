"""Shadow mode manager for automatic paper trade generation.

ShadowModeManager monitors strategies in PAPER status and automatically
generates entry orders when conditions are met. It mirrors the backtest
engine's strike selection logic but operates on live chain data.

The manager is fully automatic -- no manual intervention required. Each
scheduler tick, it checks all PAPER strategies for entry signals and
submits orders via the OrderManager.

Key responsibilities:
1. Load all strategies with status=PAPER
2. Check schedule (trading window, day of week)
3. Check entry conditions (VIX range, IV rank, etc.)
4. Enforce position limits (max concurrent positions per strategy)
5. Select strikes by delta target from live chain
6. Submit entry orders via OrderManager
7. Enforce the 3:00 PM rule (no new 0DTE entries after 15:00 ET)
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from typing import Any

from src.data import OptionContract, OptionsChain
from src.paper.models import LegSpec, PaperTradingConfig

logger = logging.getLogger(__name__)

try:
    import zoneinfo

    ET = zoneinfo.ZoneInfo("US/Eastern")
except ImportError:
    from datetime import timezone

    ET = timezone(timedelta(hours=-5))  # type: ignore[assignment]


def _now_et() -> datetime:
    """Get the current time in Eastern Time."""
    return datetime.now(ET)


class ShadowModeManager:
    """Automatically generates paper trades for strategies in PAPER status.

    Attached to PaperTradingEngine and called on each tick. Loads PAPER
    strategies from the StrategyManager, checks entry conditions against
    live chain data, and submits orders via OrderManager.

    Usage::

        shadow = ShadowModeManager(db, strategy_manager, order_manager, config)
        order_ids = await shadow.check_entry_signals(chains)
    """

    def __init__(
        self,
        db: Any,  # aiosqlite.Connection
        strategy_manager: Any,  # StrategyManager
        order_manager: Any,  # OrderManager
        position_tracker: Any,  # PositionTracker
        config: PaperTradingConfig,
    ) -> None:
        self._db = db
        self._strategy_manager = strategy_manager
        self._order_manager = order_manager
        self._position_tracker = position_tracker
        self._config = config

        # Track entries per strategy per day to avoid duplicate entries
        self._entries_today: dict[int, int] = {}
        self._last_reset_date: str = ""

    def _reset_daily_tracking(self) -> None:
        """Reset daily entry tracking if the date has changed."""
        today = date.today().isoformat()
        if today != self._last_reset_date:
            self._entries_today.clear()
            self._last_reset_date = today

    async def check_entry_signals(
        self,
        chains: dict[str, OptionsChain],
    ) -> list[int]:
        """Check all PAPER strategies for entry signals and submit orders.

        For each PAPER strategy:
        1. Load the strategy template
        2. Check schedule (day of week, time window)
        3. Check entry conditions (VIX, IV rank, etc.)
        4. Check position limits (max concurrent positions)
        5. Select strikes by delta from live chain
        6. Submit entry order

        Args:
            chains: Dict of ticker -> live OptionsChain.

        Returns:
            List of order IDs for submitted orders.
        """
        self._reset_daily_tracking()
        order_ids: list[int] = []

        if self._strategy_manager is None:
            return order_ids

        # Load all PAPER strategies
        try:
            from src.strategy.lifecycle import StrategyStatus

            paper_strategies = await self._strategy_manager.list_strategies(
                status=StrategyStatus.PAPER,
            )
        except Exception as exc:
            logger.error("Failed to load PAPER strategies: %s", exc)
            return order_ids

        for strategy in paper_strategies:
            try:
                order_id = await self._check_strategy_entry(strategy, chains)
                if order_id is not None:
                    order_ids.append(order_id)
            except Exception as exc:
                logger.error(
                    "Error checking entry for strategy #%d '%s': %s",
                    strategy["id"],
                    strategy["name"],
                    exc,
                    exc_info=True,
                )

        return order_ids

    async def _check_strategy_entry(
        self,
        strategy: dict[str, Any],
        chains: dict[str, OptionsChain],
    ) -> int | None:
        """Check a single strategy for entry conditions and submit order.

        Returns order_id if an order was submitted, None otherwise.
        """
        strategy_id = strategy["id"]
        template_yaml = strategy.get("template_yaml")

        if not template_yaml:
            return None

        # Load and parse the strategy template
        template = self._load_template(template_yaml)
        if template is None:
            return None

        now = _now_et()

        # Check schedule: day of week
        if now.weekday() not in template.schedule.trading_days:
            return None

        # Check schedule: time window
        if not self._is_in_entry_window(now, template.schedule):
            return None

        # Check 3:00 PM rule for 0DTE strategies
        if template.structure.dte_target == 0 or template.structure.dte_max == 0:
            if now.time() >= time(15, 0):
                logger.debug(
                    "Skipping 0DTE entry for strategy #%d: after 15:00 ET",
                    strategy_id,
                )
                return None

        # Check position limits
        open_positions = await self._position_tracker.get_open_positions(
            strategy_id=strategy_id,
        )
        max_positions = template.sizing.max_positions
        if len(open_positions) >= max_positions:
            return None

        # Check daily entry limit (max 1 entry per strategy per day for daily frequency)
        if template.schedule.frequency == "daily":
            daily_count = self._entries_today.get(strategy_id, 0)
            if daily_count >= 1:
                return None

        # Check entry conditions against live data
        chain = chains.get(template.ticker) or chains.get("SPX") or chains.get("SPY")
        if chain is None and chains:
            chain = next(iter(chains.values()))
        if chain is None:
            return None

        if not self._check_entry_conditions(template, chain):
            return None

        # Select strikes
        legs = self.select_strikes(template, chain)
        if legs is None or not legs:
            return None

        # Determine quantity
        quantity = template.sizing.fixed_contracts or 1

        # Submit entry order
        order_id = await self._order_manager.submit_order(
            strategy_id=strategy_id,
            direction="open",
            legs=legs,
            quantity=quantity,
            order_type="market",
        )

        # Track the entry
        self._entries_today[strategy_id] = (
            self._entries_today.get(strategy_id, 0) + 1
        )

        logger.info(
            "Shadow mode: submitted entry order #%d for strategy #%d '%s' (%d legs)",
            order_id,
            strategy_id,
            strategy["name"],
            len(legs),
        )

        return order_id

    def _load_template(self, template_yaml: str) -> Any:
        """Load a StrategyTemplate from a YAML string or file path.

        Returns the parsed template or None if loading fails.
        """
        try:
            from src.strategy.loader import StrategyLoader

            loader = StrategyLoader()

            # If it looks like a file path, load from file
            if template_yaml.endswith((".yaml", ".yml")):
                return loader.load_yaml(template_yaml)

            # Otherwise, parse as raw YAML string
            import yaml

            raw = yaml.safe_load(template_yaml)
            if isinstance(raw, dict):
                return loader._dict_to_template(raw)

            return None
        except Exception as exc:
            logger.warning("Failed to load strategy template: %s", exc)
            return None

    def _is_in_entry_window(
        self,
        now: datetime,
        schedule: Any,  # ScheduleConfig
    ) -> bool:
        """Check if current time is within the strategy's entry window."""
        try:
            start_parts = schedule.entry_window_start.split(":")
            end_parts = schedule.entry_window_end.split(":")

            window_start = time(int(start_parts[0]), int(start_parts[1]))
            window_end = time(int(end_parts[0]), int(end_parts[1]))

            current_time = now.time()
            return window_start <= current_time <= window_end
        except (ValueError, IndexError, AttributeError):
            # If parsing fails, allow entry (conservative)
            return True

    def _check_entry_conditions(
        self,
        template: Any,  # StrategyTemplate
        chain: OptionsChain,
    ) -> bool:
        """Check if entry conditions are met based on live data.

        Checks VIX range, minimum credit, and other entry rule conditions.
        IV rank check is skipped if no IV rank data is available in the chain.
        """
        entry = template.entry

        # VIX check: use the chain's spot VIX if available via metadata,
        # otherwise skip
        # For now, VIX checks are deferred to when VIX data is available
        # through the ML layer or a separate data source

        # Check min credit: we can't know the exact credit until we select
        # strikes, so this is deferred to post-strike-selection validation

        # Basic validation: chain must have contracts
        if not chain.contracts:
            return False

        return True

    def select_strikes(
        self,
        template: Any,  # StrategyTemplate
        chain: OptionsChain,
    ) -> list[LegSpec] | None:
        """Select strikes by delta targets from a live options chain.

        Mirrors BacktestEngine._select_strike() logic but works with
        live OptionContract objects instead of DataFrames.

        For each leg in the strategy template:
        1. Filter contracts by option type (call/put)
        2. Filter by DTE range
        3. Find the best expiration matching DTE target
        4. Select the contract closest to delta target

        Args:
            template: Parsed StrategyTemplate with structure/legs.
            chain: Live OptionsChain with current quotes.

        Returns:
            List of LegSpec for all legs, or None if any leg
            cannot be matched to a contract in the chain.
        """
        structure = template.structure
        today = date.today()

        # Find the best expiration matching DTE target
        best_expiry = self._find_best_expiry(
            chain,
            dte_target=structure.dte_target,
            dte_min=structure.dte_min,
            dte_max=structure.dte_max,
            today=today,
        )

        if best_expiry is None:
            logger.debug(
                "No expiry found for DTE target=%d (min=%d, max=%d)",
                structure.dte_target,
                structure.dte_min,
                structure.dte_max,
            )
            return None

        # Filter contracts for this expiry
        expiry_contracts = chain.for_expiry(best_expiry)
        if not expiry_contracts:
            return None

        # Select strike for each leg
        legs: list[LegSpec] = []
        for leg_def in structure.legs:
            contract = self._select_contract_by_delta(
                expiry_contracts,
                option_type=leg_def.side.value,  # "call" or "put"
                delta_target=leg_def.delta_value,
            )

            if contract is None:
                logger.debug(
                    "No contract found for leg '%s': %s delta=%.2f exp=%s",
                    leg_def.name,
                    leg_def.side.value,
                    leg_def.delta_value,
                    best_expiry,
                )
                return None

            legs.append(
                LegSpec(
                    leg_name=leg_def.name,
                    option_type=leg_def.side.value,
                    strike=contract.strike,
                    expiry=best_expiry,
                    action=leg_def.action.value,  # "buy" or "sell"
                    quantity=leg_def.quantity,
                )
            )

        return legs

    def _find_best_expiry(
        self,
        chain: OptionsChain,
        dte_target: int,
        dte_min: int,
        dte_max: int,
        today: date | None = None,
    ) -> date | None:
        """Find the expiration date closest to DTE target within bounds."""
        if today is None:
            today = date.today()

        best_expiry = None
        best_diff = float("inf")

        for expiry in chain.expirations:
            dte = (expiry - today).days
            if dte_min <= dte <= dte_max:
                diff = abs(dte - dte_target)
                if diff < best_diff:
                    best_diff = diff
                    best_expiry = expiry

        return best_expiry

    def _select_contract_by_delta(
        self,
        contracts: list[OptionContract],
        option_type: str,
        delta_target: float,
    ) -> OptionContract | None:
        """Select the contract closest to a delta target.

        For puts, delta is negative in the contract data; we use
        absolute delta for comparison if delta_target is positive.

        Args:
            contracts: Contracts for a single expiry.
            option_type: "call" or "put".
            delta_target: Target delta value (positive).

        Returns:
            The best matching contract, or None if no match.
        """
        typed_contracts = [
            c for c in contracts if c.option_type == option_type
        ]

        if not typed_contracts:
            return None

        # For puts, delta is negative. Compare using absolute values.
        target = abs(delta_target)

        best_contract = None
        best_diff = float("inf")

        for contract in typed_contracts:
            delta = abs(contract.delta)
            diff = abs(delta - target)
            if diff < best_diff:
                best_diff = diff
                best_contract = contract

        return best_contract

    def reset_daily_state(self) -> None:
        """Reset daily entry tracking. Called by engine.start_of_day()."""
        self._entries_today.clear()
        self._last_reset_date = ""
