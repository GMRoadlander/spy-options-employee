"""Tests for risk data models.

Verifies default values, field types, and dataclass behavior
for all risk analytics models.
"""

import pytest

from src.risk.models import (
    ConcentrationReport,
    CorrelationReport,
    PortfolioGreeks,
    PositionSizeResult,
    RiskAlert,
    RiskCheckResult,
    RiskSnapshot,
    StressScenario,
    StressTestResult,
    VaRResult,
)


class TestPortfolioGreeks:
    def test_portfolio_greeks_defaults(self):
        """All zeros, empty dicts."""
        g = PortfolioGreeks()
        assert g.delta == 0.0
        assert g.gamma == 0.0
        assert g.theta == 0.0
        assert g.vega == 0.0
        assert g.dollar_delta == 0.0
        assert g.dollar_gamma == 0.0
        assert g.net_premium == 0.0
        assert g.num_positions == 0
        assert g.num_legs == 0
        assert g.timestamp == ""
        assert g.greeks_by_expiry == {}
        assert g.greeks_by_strategy == {}


class TestVaRResult:
    def test_var_result_defaults(self):
        """All zeros, None optionals."""
        v = VaRResult()
        assert v.dg_var_95 == 0.0
        assert v.dg_var_99 == 0.0
        assert v.hist_var_95 is None
        assert v.hist_var_99 is None
        assert v.cvar_95 is None
        assert v.worst_case is None
        assert v.pct_of_nav_95 == 0.0
        assert v.pct_of_nav_99 == 0.0
        assert v.daily_vol_used == 0.0
        assert v.timestamp == ""


class TestStressScenario:
    def test_stress_scenario_defaults(self):
        s = StressScenario()
        assert s.name == ""
        assert s.spot_shock == 0.0
        assert s.vol_shock == 0.0
        assert s.time_days == 0.0


class TestStressTestResult:
    def test_stress_test_result_defaults(self):
        r = StressTestResult()
        assert r.portfolio_pnl == 0.0
        assert r.pnl_pct_of_nav == 0.0
        assert r.status == "ok"
        assert r.position_pnls == {}
        assert isinstance(r.scenario, StressScenario)


class TestRiskAlert:
    def test_risk_alert_defaults(self):
        """Info level default."""
        a = RiskAlert()
        assert a.level == "info"
        assert a.category == ""
        assert a.message == ""
        assert a.current_value == 0.0
        assert a.limit_value == 0.0
        assert a.utilization_pct == 0.0
        assert a.timestamp == ""


class TestRiskCheckResult:
    def test_risk_check_result_approved(self):
        """Verify approved=True path."""
        r = RiskCheckResult(approved=True, checks_passed=["circuit_breaker", "regime"])
        assert r.approved is True
        assert len(r.checks_passed) == 2
        assert r.checks_failed == []
        assert r.reasons == []
        assert r.adjusted_size is None

    def test_risk_check_result_rejected(self):
        """Verify checks_failed populated."""
        r = RiskCheckResult(
            approved=False,
            checks_failed=["position_limits"],
            reasons=["DTE too low"],
        )
        assert r.approved is False
        assert len(r.checks_failed) == 1
        assert len(r.reasons) == 1


class TestPositionSizeResult:
    def test_position_size_result_defaults(self):
        """All zeros."""
        p = PositionSizeResult()
        assert p.max_premium == 0.0
        assert p.max_contracts == 0
        assert p.kelly_raw == 0.0
        assert p.kelly_fraction == 0.0
        assert p.regime_multiplier == 1.0
        assert p.vol_multiplier == 1.0
        assert p.anomaly_multiplier == 1.0
        assert p.rationale == ""


class TestConcentrationReport:
    def test_concentration_report_defaults(self):
        """Empty dicts."""
        c = ConcentrationReport()
        assert c.by_expiry == {}
        assert c.by_strategy == {}
        assert c.by_strike_range == {}
        assert c.max_expiry_concentration == 0.0
        assert c.max_strategy_concentration == 0.0
        assert c.max_strike_concentration == 0.0
        assert c.warnings == []


class TestCorrelationReport:
    def test_correlation_report_defaults(self):
        c = CorrelationReport()
        assert c.pnl_correlation == {}
        assert c.greeks_similarity == {}
        assert c.high_correlation_pairs == []
        assert c.moderate_correlation_pairs == []
        assert c.warnings == []


class TestRiskSnapshot:
    def test_risk_snapshot_defaults(self):
        """Nested defaults all created."""
        s = RiskSnapshot()
        assert isinstance(s.portfolio_greeks, PortfolioGreeks)
        assert isinstance(s.var_result, VaRResult)
        assert s.stress_results == []
        assert isinstance(s.concentration, ConcentrationReport)
        assert s.active_alerts == []
        assert s.circuit_breakers_active == []
        assert s.regime_state == 0
        assert s.regime_name == "risk-on"
        assert s.anomaly_score == 0.0
        assert s.nav == 0.0
        assert s.risk_utilization == {}
        assert s.timestamp == ""
