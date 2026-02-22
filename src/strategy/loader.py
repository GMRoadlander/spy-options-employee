"""Strategy YAML loader -- reads and writes strategy templates.

Handles serialization/deserialization between YAML files and
StrategyTemplate dataclasses. Includes validation on load.
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from src.strategy.schema import (
    DeltaTarget,
    EntryRule,
    ExitRule,
    LegAction,
    LegDefinition,
    LegSide,
    ScheduleConfig,
    SizingConfig,
    StrategyTemplate,
    StrategyType,
    StructureDefinition,
    validate_strategy,
)

logger = logging.getLogger(__name__)


class StrategyLoadError(Exception):
    """Raised when a strategy YAML file cannot be loaded or parsed."""


class StrategyLoader:
    """Loads and saves strategy templates from/to YAML files.

    Usage:
        loader = StrategyLoader("/path/to/strategies")
        template = loader.load_yaml("my-strategy.yaml")
        loader.save_yaml(template, "my-strategy.yaml")
    """

    def __init__(self, strategy_dir: str | None = None) -> None:
        self._strategy_dir = Path(strategy_dir) if strategy_dir else Path("strategies")

    @property
    def strategy_dir(self) -> Path:
        return self._strategy_dir

    def load_yaml(self, filename: str) -> StrategyTemplate:
        """Load a strategy template from a YAML file.

        Args:
            filename: YAML filename (relative to strategy_dir or absolute).

        Returns:
            Parsed and validated StrategyTemplate.

        Raises:
            StrategyLoadError: If the file cannot be read, parsed, or validated.
        """
        path = Path(filename)
        if not path.is_absolute():
            path = self._strategy_dir / path

        if not path.exists():
            raise StrategyLoadError(f"Strategy file not found: {path}")

        try:
            with open(path, "r") as f:
                raw = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise StrategyLoadError(f"Invalid YAML in {path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise StrategyLoadError(f"Strategy YAML must be a mapping, got {type(raw).__name__}")

        try:
            template = self._dict_to_template(raw)
        except (KeyError, ValueError, TypeError) as exc:
            raise StrategyLoadError(f"Failed to parse strategy from {path}: {exc}") from exc

        # Validate
        errors = validate_strategy(template)
        if errors:
            raise StrategyLoadError(
                f"Strategy validation failed for {path}:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        logger.info("Loaded strategy '%s' from %s", template.name, path)
        return template

    def save_yaml(self, template: StrategyTemplate, filename: str) -> Path:
        """Save a strategy template to a YAML file.

        Args:
            template: The strategy template to save.
            filename: YAML filename (relative to strategy_dir or absolute).

        Returns:
            Path to the saved file.

        Raises:
            StrategyLoadError: If validation fails before saving.
        """
        # Validate before saving
        errors = validate_strategy(template)
        if errors:
            raise StrategyLoadError(
                "Cannot save invalid strategy:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        path = Path(filename)
        if not path.is_absolute():
            path = self._strategy_dir / path

        path.parent.mkdir(parents=True, exist_ok=True)

        raw = self._template_to_dict(template)

        with open(path, "w") as f:
            yaml.dump(raw, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        logger.info("Saved strategy '%s' to %s", template.name, path)
        return path

    def list_strategies(self) -> list[str]:
        """List all YAML strategy files in the strategy directory.

        Returns:
            List of YAML filenames (relative to strategy_dir).
        """
        if not self._strategy_dir.exists():
            return []

        files = []
        for p in sorted(self._strategy_dir.rglob("*.yaml")):
            files.append(str(p.relative_to(self._strategy_dir)))
        for p in sorted(self._strategy_dir.rglob("*.yml")):
            files.append(str(p.relative_to(self._strategy_dir)))

        return files

    def validate(self, filename: str) -> list[str]:
        """Validate a strategy YAML file and return errors.

        Args:
            filename: YAML filename.

        Returns:
            List of validation error messages. Empty if valid.
        """
        try:
            self.load_yaml(filename)
            return []
        except StrategyLoadError as exc:
            return [str(exc)]

    @staticmethod
    def _dict_to_template(raw: dict) -> StrategyTemplate:
        """Convert a raw dict (from YAML) into a StrategyTemplate."""
        # Parse structure
        structure_raw = raw.get("structure", {})
        legs_raw = structure_raw.get("legs", [])

        legs = []
        for leg_raw in legs_raw:
            legs.append(LegDefinition(
                name=leg_raw["name"],
                side=LegSide(leg_raw["side"]),
                action=LegAction(leg_raw["action"]),
                delta_target=DeltaTarget(leg_raw.get("delta_target", "fixed")),
                delta_value=float(leg_raw.get("delta_value", 0.0)),
                delta_min=float(leg_raw.get("delta_min", 0.0)),
                delta_max=float(leg_raw.get("delta_max", 0.0)),
                quantity=int(leg_raw.get("quantity", 1)),
                strike_offset=leg_raw.get("strike_offset"),
            ))

        structure = StructureDefinition(
            strategy_type=StrategyType(structure_raw.get("strategy_type", "custom")),
            legs=legs,
            dte_target=int(structure_raw.get("dte_target", 30)),
            dte_min=int(structure_raw.get("dte_min", 20)),
            dte_max=int(structure_raw.get("dte_max", 45)),
        )

        # Parse entry rules
        entry_raw = raw.get("entry", {})
        entry = EntryRule(
            iv_rank_min=float(entry_raw.get("iv_rank_min", 0.0)),
            iv_rank_max=float(entry_raw.get("iv_rank_max", 100.0)),
            iv_percentile_min=float(entry_raw.get("iv_percentile_min", 0.0)),
            iv_percentile_max=float(entry_raw.get("iv_percentile_max", 100.0)),
            vix_min=float(entry_raw.get("vix_min", 0.0)),
            vix_max=float(entry_raw.get("vix_max", 100.0)),
            min_credit=float(entry_raw.get("min_credit", 0.0)),
            max_debit=float(entry_raw.get("max_debit", float("inf"))),
            time_of_day=entry_raw.get("time_of_day", "any"),
            custom_conditions=entry_raw.get("custom_conditions", []),
        )

        # Parse exit rules
        exit_raw = raw.get("exit", {})
        exit_rule = ExitRule(
            profit_target_pct=float(exit_raw.get("profit_target_pct", 0.50)),
            stop_loss_pct=float(exit_raw.get("stop_loss_pct", 2.0)),
            dte_close=int(exit_raw.get("dte_close", 0)),
            trailing_stop_pct=exit_raw.get("trailing_stop_pct"),
            time_stop_days=exit_raw.get("time_stop_days"),
            custom_conditions=exit_raw.get("custom_conditions", []),
        )

        # Parse sizing
        sizing_raw = raw.get("sizing", {})
        sizing = SizingConfig(
            max_risk_pct=float(sizing_raw.get("max_risk_pct", 0.02)),
            max_positions=int(sizing_raw.get("max_positions", 3)),
            max_contracts=int(sizing_raw.get("max_contracts", 10)),
            scale_with_iv=bool(sizing_raw.get("scale_with_iv", False)),
            fixed_contracts=sizing_raw.get("fixed_contracts"),
        )

        # Parse schedule
        schedule_raw = raw.get("schedule", {})
        schedule = ScheduleConfig(
            trading_days=schedule_raw.get("trading_days", [0, 1, 2, 3, 4]),
            entry_window_start=schedule_raw.get("entry_window_start", "09:35"),
            entry_window_end=schedule_raw.get("entry_window_end", "15:30"),
            frequency=schedule_raw.get("frequency", "daily"),
            blackout_dates=schedule_raw.get("blackout_dates", []),
        )

        return StrategyTemplate(
            name=raw["name"],
            version=raw.get("version", "1.0"),
            description=raw.get("description", ""),
            ticker=raw.get("ticker", "SPX"),
            structure=structure,
            entry=entry,
            exit=exit_rule,
            sizing=sizing,
            schedule=schedule,
            tags=raw.get("tags", []),
            metadata=raw.get("metadata", {}),
        )

    @staticmethod
    def _template_to_dict(template: StrategyTemplate) -> dict:
        """Convert a StrategyTemplate into a dict for YAML serialization."""
        legs_list = []
        for leg in template.structure.legs:
            leg_dict: dict[str, Any] = {
                "name": leg.name,
                "side": leg.side.value,
                "action": leg.action.value,
                "delta_target": leg.delta_target.value,
                "delta_value": leg.delta_value,
                "quantity": leg.quantity,
            }
            if leg.delta_target == DeltaTarget.RANGE:
                leg_dict["delta_min"] = leg.delta_min
                leg_dict["delta_max"] = leg.delta_max
            if leg.strike_offset is not None:
                leg_dict["strike_offset"] = leg.strike_offset
            legs_list.append(leg_dict)

        result: dict[str, Any] = {
            "name": template.name,
            "version": template.version,
            "description": template.description,
            "ticker": template.ticker,
            "structure": {
                "strategy_type": template.structure.strategy_type.value,
                "legs": legs_list,
                "dte_target": template.structure.dte_target,
                "dte_min": template.structure.dte_min,
                "dte_max": template.structure.dte_max,
            },
            "entry": {
                "iv_rank_min": template.entry.iv_rank_min,
                "iv_rank_max": template.entry.iv_rank_max,
                "vix_min": template.entry.vix_min,
                "vix_max": template.entry.vix_max,
                "min_credit": template.entry.min_credit,
                "time_of_day": template.entry.time_of_day,
            },
            "exit": {
                "profit_target_pct": template.exit.profit_target_pct,
                "stop_loss_pct": template.exit.stop_loss_pct,
                "dte_close": template.exit.dte_close,
            },
            "sizing": {
                "max_risk_pct": template.sizing.max_risk_pct,
                "max_positions": template.sizing.max_positions,
                "max_contracts": template.sizing.max_contracts,
                "scale_with_iv": template.sizing.scale_with_iv,
            },
            "schedule": {
                "trading_days": template.schedule.trading_days,
                "entry_window_start": template.schedule.entry_window_start,
                "entry_window_end": template.schedule.entry_window_end,
                "frequency": template.schedule.frequency,
            },
            "tags": template.tags,
        }

        if template.exit.trailing_stop_pct is not None:
            result["exit"]["trailing_stop_pct"] = template.exit.trailing_stop_pct
        if template.exit.time_stop_days is not None:
            result["exit"]["time_stop_days"] = template.exit.time_stop_days
        if template.sizing.fixed_contracts is not None:
            result["sizing"]["fixed_contracts"] = template.sizing.fixed_contracts
        if template.entry.custom_conditions:
            result["entry"]["custom_conditions"] = template.entry.custom_conditions
        if template.exit.custom_conditions:
            result["exit"]["custom_conditions"] = template.exit.custom_conditions
        if template.schedule.blackout_dates:
            result["schedule"]["blackout_dates"] = template.schedule.blackout_dates
        if template.metadata:
            result["metadata"] = template.metadata

        return result
