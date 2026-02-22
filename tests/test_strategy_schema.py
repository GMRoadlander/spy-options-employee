"""Tests for strategy YAML schema, validation, and loader.

Covers: dataclass creation, validation rules, YAML round-trip,
strategy loading, and example file loading.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path

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
from src.strategy.loader import StrategyLoader, StrategyLoadError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iron_condor_legs() -> list[LegDefinition]:
    """Create standard iron condor legs."""
    return [
        LegDefinition(name="short_put", side=LegSide.PUT, action=LegAction.SELL, delta_value=0.16),
        LegDefinition(name="long_put", side=LegSide.PUT, action=LegAction.BUY, delta_value=0.05),
        LegDefinition(name="short_call", side=LegSide.CALL, action=LegAction.SELL, delta_value=0.16),
        LegDefinition(name="long_call", side=LegSide.CALL, action=LegAction.BUY, delta_value=0.05),
    ]


def _valid_template(**overrides) -> StrategyTemplate:
    """Create a valid StrategyTemplate with optional overrides."""
    defaults = {
        "name": "Test Iron Condor",
        "ticker": "SPX",
        "structure": StructureDefinition(
            strategy_type=StrategyType.IRON_CONDOR,
            legs=_iron_condor_legs(),
        ),
    }
    defaults.update(overrides)
    return StrategyTemplate(**defaults)


# ---------------------------------------------------------------------------
# Tests: Dataclass creation
# ---------------------------------------------------------------------------


class TestDataclassCreation:
    """Tests for creating strategy dataclasses."""

    def test_leg_definition_defaults(self):
        """LegDefinition has sensible defaults."""
        leg = LegDefinition(name="test", side=LegSide.CALL, action=LegAction.BUY)
        assert leg.delta_target == DeltaTarget.FIXED
        assert leg.delta_value == 0.0
        assert leg.quantity == 1
        assert leg.strike_offset is None

    def test_strategy_template_defaults(self):
        """StrategyTemplate fills in defaults for optional fields."""
        template = StrategyTemplate(name="Test")
        assert template.version == "1.0"
        assert template.ticker == "SPX"
        assert template.tags == []
        assert template.metadata == {}

    def test_strategy_type_enum_values(self):
        """Strategy types match expected values."""
        assert StrategyType.IRON_CONDOR.value == "iron_condor"
        assert StrategyType.VERTICAL_SPREAD.value == "vertical_spread"
        assert StrategyType.STRADDLE.value == "straddle"
        assert StrategyType.NAKED_PUT.value == "naked_put"

    def test_entry_rule_defaults(self):
        """EntryRule defaults are permissive."""
        entry = EntryRule()
        assert entry.iv_rank_min == 0.0
        assert entry.iv_rank_max == 100.0
        assert entry.time_of_day == "any"

    def test_exit_rule_defaults(self):
        """ExitRule defaults are standard."""
        exit_rule = ExitRule()
        assert exit_rule.profit_target_pct == 0.50
        assert exit_rule.stop_loss_pct == 2.0
        assert exit_rule.dte_close == 0


# ---------------------------------------------------------------------------
# Tests: Validation
# ---------------------------------------------------------------------------


class TestValidation:
    """Tests for validate_strategy function."""

    def test_valid_iron_condor(self):
        """A properly configured iron condor passes validation."""
        template = _valid_template()
        errors = validate_strategy(template)
        assert errors == []

    def test_missing_name(self):
        """Empty name fails validation."""
        template = _valid_template(name="")
        errors = validate_strategy(template)
        assert any("name" in e.lower() for e in errors)

    def test_missing_ticker(self):
        """Empty ticker fails validation."""
        template = _valid_template(ticker="")
        errors = validate_strategy(template)
        assert any("ticker" in e.lower() for e in errors)

    def test_no_legs(self):
        """Strategy with zero legs fails validation."""
        template = _valid_template(
            structure=StructureDefinition(
                strategy_type=StrategyType.CUSTOM,
                legs=[],
            )
        )
        errors = validate_strategy(template)
        assert any("leg" in e.lower() for e in errors)

    def test_dte_min_exceeds_max(self):
        """DTE min > max fails validation."""
        template = _valid_template(
            structure=StructureDefinition(
                strategy_type=StrategyType.IRON_CONDOR,
                legs=_iron_condor_legs(),
                dte_min=45,
                dte_max=20,
                dte_target=30,
            )
        )
        errors = validate_strategy(template)
        assert any("dte" in e.lower() for e in errors)

    def test_iron_condor_wrong_leg_count(self):
        """Iron condor with != 4 legs fails."""
        template = _valid_template(
            structure=StructureDefinition(
                strategy_type=StrategyType.IRON_CONDOR,
                legs=_iron_condor_legs()[:2],
            )
        )
        errors = validate_strategy(template)
        assert any("4 legs" in e for e in errors)

    def test_vertical_spread_wrong_leg_count(self):
        """Vertical spread with != 2 legs fails."""
        template = _valid_template(
            structure=StructureDefinition(
                strategy_type=StrategyType.VERTICAL_SPREAD,
                legs=_iron_condor_legs(),  # 4 legs, should be 2
            )
        )
        errors = validate_strategy(template)
        assert any("2 legs" in e for e in errors)

    def test_invalid_profit_target(self):
        """Profit target > 1 fails validation."""
        template = _valid_template(exit=ExitRule(profit_target_pct=1.5))
        errors = validate_strategy(template)
        assert any("profit target" in e.lower() for e in errors)

    def test_invalid_risk_pct(self):
        """max_risk_pct > 1 fails validation."""
        template = _valid_template(sizing=SizingConfig(max_risk_pct=2.0))
        errors = validate_strategy(template)
        assert any("max_risk_pct" in e for e in errors)

    def test_delta_range_validation(self):
        """Delta range where min >= max fails."""
        legs = [
            LegDefinition(
                name="test",
                side=LegSide.PUT,
                action=LegAction.SELL,
                delta_target=DeltaTarget.RANGE,
                delta_min=0.20,
                delta_max=0.10,  # invalid: min > max
            ),
        ]
        template = _valid_template(
            structure=StructureDefinition(
                strategy_type=StrategyType.CUSTOM,
                legs=legs,
            )
        )
        errors = validate_strategy(template)
        assert any("delta_min" in e for e in errors)


# ---------------------------------------------------------------------------
# Tests: YAML Loader
# ---------------------------------------------------------------------------


class TestYamlLoader:
    """Tests for StrategyLoader YAML operations."""

    @pytest.fixture
    def tmp_dir(self):
        d = tempfile.mkdtemp(prefix="strategy_test_")
        yield d
        shutil.rmtree(d, ignore_errors=True)

    @pytest.fixture
    def loader(self, tmp_dir):
        return StrategyLoader(tmp_dir)

    def test_save_and_load_roundtrip(self, loader):
        """Template survives YAML save/load round-trip."""
        template = _valid_template()
        loader.save_yaml(template, "test.yaml")
        loaded = loader.load_yaml("test.yaml")

        assert loaded.name == template.name
        assert loaded.ticker == template.ticker
        assert loaded.structure.strategy_type == template.structure.strategy_type
        assert len(loaded.structure.legs) == 4

    def test_load_nonexistent_file(self, loader):
        """Loading nonexistent file raises StrategyLoadError."""
        with pytest.raises(StrategyLoadError, match="not found"):
            loader.load_yaml("does-not-exist.yaml")

    def test_list_strategies(self, loader):
        """list_strategies returns available YAML files."""
        template = _valid_template()
        loader.save_yaml(template, "strat1.yaml")
        loader.save_yaml(template, "strat2.yaml")

        files = loader.list_strategies()
        assert "strat1.yaml" in files
        assert "strat2.yaml" in files

    def test_validate_method(self, loader):
        """validate() returns empty list for valid strategy."""
        template = _valid_template()
        loader.save_yaml(template, "valid.yaml")
        errors = loader.validate("valid.yaml")
        assert errors == []


# ---------------------------------------------------------------------------
# Tests: Example YAML files
# ---------------------------------------------------------------------------


class TestExampleYamlFiles:
    """Tests that the example YAML files load and validate correctly."""

    def test_iron_condor_example(self):
        """SPX iron condor example loads and validates."""
        loader = StrategyLoader("strategies")
        template = loader.load_yaml("examples/spx-iron-condor-30dte.yaml")

        assert template.name == "SPX Iron Condor 30 DTE"
        assert template.ticker == "SPX"
        assert template.structure.strategy_type == StrategyType.IRON_CONDOR
        assert len(template.structure.legs) == 4
        assert template.structure.dte_target == 30

    def test_put_spread_example(self):
        """SPX put spread example loads and validates."""
        loader = StrategyLoader("strategies")
        template = loader.load_yaml("examples/spx-put-spread-weekly.yaml")

        assert template.name == "SPX Weekly Put Spread"
        assert template.ticker == "SPX"
        assert template.structure.strategy_type == StrategyType.VERTICAL_SPREAD
        assert len(template.structure.legs) == 2
        assert template.structure.dte_target == 7
