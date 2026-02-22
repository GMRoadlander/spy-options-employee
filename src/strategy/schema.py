"""Strategy template schema -- dataclasses defining strategy structure.

Supports iron condors, verticals, straddles, naked puts, and other
multi-leg options strategies. Strategies are defined in YAML and loaded
into these dataclasses for validation and use by the backtesting engine.

Structure hierarchy:
    StrategyTemplate
        -> StructureDefinition -> [LegDefinition, ...]
        -> EntryRule
        -> ExitRule
        -> SizingConfig
        -> ScheduleConfig
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StrategyType(str, Enum):
    """Supported strategy types."""

    IRON_CONDOR = "iron_condor"
    VERTICAL_SPREAD = "vertical_spread"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    NAKED_PUT = "naked_put"
    NAKED_CALL = "naked_call"
    BUTTERFLY = "butterfly"
    CALENDAR = "calendar"
    CUSTOM = "custom"


class LegSide(str, Enum):
    """Option side for a leg."""

    CALL = "call"
    PUT = "put"


class LegAction(str, Enum):
    """Buy or sell action for a leg."""

    BUY = "buy"
    SELL = "sell"


class DeltaTarget(str, Enum):
    """Predefined delta targeting modes."""

    FIXED = "fixed"           # Exact delta value
    RANGE = "range"           # Delta between min and max
    ATM = "atm"               # At-the-money (~0.50 delta)
    OTM = "otm"               # Out-of-the-money (user-defined threshold)


@dataclass
class LegDefinition:
    """Defines a single leg of an options strategy.

    Attributes:
        name: Human-readable leg name (e.g., "short_put").
        side: Call or put.
        action: Buy or sell.
        delta_target: Target delta for strike selection.
        delta_value: The delta value (for FIXED mode) or range bounds.
        delta_min: Minimum delta (for RANGE mode).
        delta_max: Maximum delta (for RANGE mode).
        quantity: Number of contracts (relative to 1 unit).
        strike_offset: Fixed offset from ATM in points (alternative to delta).
    """

    name: str
    side: LegSide
    action: LegAction
    delta_target: DeltaTarget = DeltaTarget.FIXED
    delta_value: float = 0.0
    delta_min: float = 0.0
    delta_max: float = 0.0
    quantity: int = 1
    strike_offset: float | None = None


@dataclass
class StructureDefinition:
    """Defines the option structure (the combination of legs).

    Attributes:
        strategy_type: The type of strategy.
        legs: List of leg definitions.
        dte_target: Target days to expiration.
        dte_min: Minimum acceptable DTE.
        dte_max: Maximum acceptable DTE.
    """

    strategy_type: StrategyType
    legs: list[LegDefinition] = field(default_factory=list)
    dte_target: int = 30
    dte_min: int = 20
    dte_max: int = 45


@dataclass
class EntryRule:
    """Rules for when to enter a trade.

    Attributes:
        iv_rank_min: Minimum IV rank to enter (0-100 scale or 0-1).
        iv_rank_max: Maximum IV rank to enter.
        iv_percentile_min: Minimum IV percentile.
        iv_percentile_max: Maximum IV percentile.
        vix_min: Minimum VIX level.
        vix_max: Maximum VIX level.
        min_credit: Minimum credit received (for credit spreads).
        max_debit: Maximum debit paid (for debit spreads).
        time_of_day: Preferred entry time ("open", "close", "any").
        custom_conditions: List of custom condition strings.
    """

    iv_rank_min: float = 0.0
    iv_rank_max: float = 100.0
    iv_percentile_min: float = 0.0
    iv_percentile_max: float = 100.0
    vix_min: float = 0.0
    vix_max: float = 100.0
    min_credit: float = 0.0
    max_debit: float = float("inf")
    time_of_day: str = "any"
    custom_conditions: list[str] = field(default_factory=list)


@dataclass
class ExitRule:
    """Rules for when to exit (close) a trade.

    Attributes:
        profit_target_pct: Close at this percentage of max profit (e.g., 0.50 = 50%).
        stop_loss_pct: Close at this percentage loss of max risk (e.g., 2.0 = 200%).
        dte_close: Close when DTE reaches this value.
        trailing_stop_pct: Trailing stop as percentage of max value reached.
        time_stop_days: Close after this many days regardless.
        custom_conditions: List of custom condition strings.
    """

    profit_target_pct: float = 0.50
    stop_loss_pct: float = 2.0
    dte_close: int = 0
    trailing_stop_pct: float | None = None
    time_stop_days: int | None = None
    custom_conditions: list[str] = field(default_factory=list)


@dataclass
class SizingConfig:
    """Position sizing configuration.

    Attributes:
        max_risk_pct: Maximum risk per trade as percentage of account.
        max_positions: Maximum number of concurrent positions.
        max_contracts: Maximum contracts per trade.
        scale_with_iv: Scale size based on IV rank (True = larger in high IV).
        fixed_contracts: Use a fixed number of contracts (overrides risk-based).
    """

    max_risk_pct: float = 0.02
    max_positions: int = 3
    max_contracts: int = 10
    scale_with_iv: bool = False
    fixed_contracts: int | None = None


@dataclass
class ScheduleConfig:
    """Trading schedule configuration.

    Attributes:
        trading_days: Days of week to trade (0=Mon, 4=Fri).
        entry_window_start: Earliest entry time (HH:MM ET).
        entry_window_end: Latest entry time (HH:MM ET).
        frequency: How often to look for entries ("daily", "weekly", "custom").
        blackout_dates: Dates to skip (e.g., FOMC, earnings).
    """

    trading_days: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    entry_window_start: str = "09:35"
    entry_window_end: str = "15:30"
    frequency: str = "daily"
    blackout_dates: list[str] = field(default_factory=list)


@dataclass
class StrategyTemplate:
    """Complete strategy template definition.

    This is the top-level object that gets serialized to/from YAML.

    Attributes:
        name: Human-readable strategy name.
        version: Template version for tracking changes.
        description: Plain-English description of the strategy.
        ticker: Target ticker symbol.
        structure: Option structure definition (legs, DTE, etc.).
        entry: Entry rules.
        exit: Exit rules.
        sizing: Position sizing config.
        schedule: Trading schedule config.
        tags: Optional tags for categorization.
        metadata: Arbitrary key-value metadata.
    """

    name: str
    version: str = "1.0"
    description: str = ""
    ticker: str = "SPX"
    structure: StructureDefinition = field(default_factory=lambda: StructureDefinition(strategy_type=StrategyType.IRON_CONDOR))
    entry: EntryRule = field(default_factory=EntryRule)
    exit: ExitRule = field(default_factory=ExitRule)
    sizing: SizingConfig = field(default_factory=SizingConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def validate_strategy(template: StrategyTemplate) -> list[str]:
    """Validate a strategy template and return a list of errors.

    Returns an empty list if the strategy is valid.

    Args:
        template: The strategy template to validate.

    Returns:
        List of validation error messages. Empty if valid.
    """
    errors: list[str] = []

    # Name is required
    if not template.name or not template.name.strip():
        errors.append("Strategy name is required")

    # Ticker is required
    if not template.ticker or not template.ticker.strip():
        errors.append("Ticker is required")

    # Structure validation
    structure = template.structure
    if not structure.legs:
        errors.append("Strategy must have at least one leg")

    if structure.dte_min > structure.dte_max:
        errors.append(f"DTE min ({structure.dte_min}) cannot exceed DTE max ({structure.dte_max})")

    if structure.dte_target < structure.dte_min or structure.dte_target > structure.dte_max:
        errors.append(
            f"DTE target ({structure.dte_target}) must be between "
            f"DTE min ({structure.dte_min}) and DTE max ({structure.dte_max})"
        )

    # Validate legs
    for leg in structure.legs:
        if not leg.name or not leg.name.strip():
            errors.append("Each leg must have a name")

        if leg.quantity < 1:
            errors.append(f"Leg '{leg.name}' quantity must be >= 1")

        if leg.delta_target == DeltaTarget.RANGE:
            if leg.delta_min >= leg.delta_max:
                errors.append(
                    f"Leg '{leg.name}' delta_min ({leg.delta_min}) must be < delta_max ({leg.delta_max})"
                )

    # Validate leg balance for defined strategy types
    if structure.strategy_type == StrategyType.IRON_CONDOR:
        if len(structure.legs) != 4:
            errors.append(f"Iron condor requires exactly 4 legs, got {len(structure.legs)}")

    elif structure.strategy_type == StrategyType.VERTICAL_SPREAD:
        if len(structure.legs) != 2:
            errors.append(f"Vertical spread requires exactly 2 legs, got {len(structure.legs)}")

    elif structure.strategy_type == StrategyType.STRADDLE:
        if len(structure.legs) != 2:
            errors.append(f"Straddle requires exactly 2 legs, got {len(structure.legs)}")

    elif structure.strategy_type == StrategyType.STRANGLE:
        if len(structure.legs) != 2:
            errors.append(f"Strangle requires exactly 2 legs, got {len(structure.legs)}")

    elif structure.strategy_type == StrategyType.BUTTERFLY:
        if len(structure.legs) != 3:
            errors.append(f"Butterfly requires exactly 3 legs, got {len(structure.legs)}")

    # Entry rule validation
    entry = template.entry
    if entry.iv_rank_min > entry.iv_rank_max:
        errors.append("Entry iv_rank_min cannot exceed iv_rank_max")

    if entry.vix_min > entry.vix_max:
        errors.append("Entry vix_min cannot exceed vix_max")

    # Exit rule validation
    exit_rule = template.exit
    if exit_rule.profit_target_pct < 0 or exit_rule.profit_target_pct > 1:
        errors.append(f"Profit target must be between 0 and 1, got {exit_rule.profit_target_pct}")

    if exit_rule.stop_loss_pct < 0:
        errors.append("Stop loss percentage cannot be negative")

    # Sizing validation
    sizing = template.sizing
    if sizing.max_risk_pct <= 0 or sizing.max_risk_pct > 1:
        errors.append(f"max_risk_pct must be between 0 and 1, got {sizing.max_risk_pct}")

    if sizing.max_positions < 1:
        errors.append("max_positions must be >= 1")

    return errors
