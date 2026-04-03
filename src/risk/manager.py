"""Central risk manager: pre-trade checks, monitoring, circuit breakers.

RiskManager is the single authority for all risk decisions. Every paper
order must pass check_order() before execution. The monitor_portfolio()
method runs on each tick to check portfolio-level limits and circuit
breakers.

Integration: receives RegimeManager, VolManager, AnomalyManager
references at init. Reads cached values from feature store (fast).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import aiosqlite

from src.risk.analyzer import PortfolioAnalyzer
from src.risk.config import REGIME_MULTIPLIERS, RiskConfig
from src.risk.models import (
    PortfolioGreeks,
    RiskAlert,
    RiskCheckResult,
    RiskSnapshot,
    VaRResult,
)
from src.risk.schema import init_risk_tables
from src.risk.sizing import compute_position_size
from src.risk.stress import StressTestEngine

logger = logging.getLogger(__name__)


class RiskManager:
    """Pre-trade risk validation and continuous monitoring.

    Central risk authority for the paper trading engine. All orders
    must pass check_order() before execution. Continuous monitoring
    via monitor_portfolio() triggers alerts and circuit breakers.

    Args:
        db: aiosqlite connection for persistence.
        config: RiskConfig with all limit parameters.
        analyzer: PortfolioAnalyzer instance.
        stress_engine: StressTestEngine instance.
    """

    def __init__(
        self,
        db: aiosqlite.Connection,
        config: RiskConfig,
        analyzer: PortfolioAnalyzer | None = None,
        stress_engine: StressTestEngine | None = None,
    ) -> None:
        self._db = db
        self._config = config
        self._analyzer = analyzer or PortfolioAnalyzer(config)
        self._stress_engine = stress_engine or StressTestEngine(config)

        # Circuit breaker state (in-memory, reset on restart)
        self._circuit_breakers: dict[str, bool] = {
            "daily_loss": False,
            "drawdown": False,
            "vix_halt": False,
            "spx_crash": False,
            "anomaly_halt": False,
            "system_error": False,
        }
        self._consecutive_failures: int = 0

        # Cached state
        self._last_greeks: PortfolioGreeks | None = None
        self._last_var: VaRResult | None = None
        self._daily_realized_pnl: float = 0.0
        self._peak_equity: float = 0.0

    async def init_tables(self) -> None:
        """Create risk tables idempotently."""
        await init_risk_tables(self._db)

    async def check_order(
        self,
        order_info: dict[str, Any],
        positions: list[dict[str, Any]],
        nav: float,
        spot: float,
        regime_state: int = 0,
        anomaly_score: float = 0.0,
    ) -> RiskCheckResult:
        """Pre-trade validation against all risk limits.

        Runs checks in order: circuit breakers -> position -> strategy ->
        portfolio. Returns immediately on first failure category.

        Args:
            order_info: Dict with strategy_id, legs, quantity, direction.
            positions: All open positions.
            nav: Current portfolio NAV.
            spot: Current SPX spot price.
            regime_state: Current HMM regime (0/1/2).
            anomaly_score: Current composite anomaly score.

        Returns:
            RiskCheckResult with approved/rejected status and reasons.
        """
        now = datetime.now().isoformat()
        result = RiskCheckResult(
            regime_state=regime_state,
            regime_name=_regime_name(regime_state),
        )

        # 1. Circuit breaker check
        active_breakers = [k for k, v in self._circuit_breakers.items() if v]
        if active_breakers:
            result.checks_failed.append("circuit_breaker")
            result.reasons.append(f"Circuit breakers active: {', '.join(active_breakers)}")
            await self._log_check(order_info, result, now)
            return result
        result.checks_passed.append("circuit_breaker")

        # 2. Regime check: crisis mode = close-only
        regime_mults = REGIME_MULTIPLIERS.get(regime_state, REGIME_MULTIPLIERS[0])
        if order_info.get("direction") == "open" and regime_mults.get("position_size", 1.0) <= 0:
            result.checks_failed.append("regime_close_only")
            result.reasons.append(f"Regime {_regime_name(regime_state)}: close-only mode")
            await self._log_check(order_info, result, now)
            return result
        result.checks_passed.append("regime")

        # 3. Position-level checks (for opening orders only)
        if order_info.get("direction") == "open":
            pos_check = self._check_position_limits(order_info, nav, regime_state)
            if pos_check:
                result.checks_failed.append("position_limits")
                result.reasons.extend(pos_check)
                await self._log_check(order_info, result, now)
                return result
            result.checks_passed.append("position_limits")

            # 4. Strategy-level checks
            strat_check = self._check_strategy_limits(
                order_info, positions, nav, regime_state,
            )
            if strat_check:
                result.checks_failed.append("strategy_limits")
                result.reasons.extend(strat_check)
                await self._log_check(order_info, result, now)
                return result
            result.checks_passed.append("strategy_limits")

            # 5. Portfolio-level checks
            port_check = self._check_portfolio_limits(positions, nav, spot, regime_state)
            if port_check:
                result.checks_failed.append("portfolio_limits")
                result.reasons.extend(port_check)
                await self._log_check(order_info, result, now)
                return result
            result.checks_passed.append("portfolio_limits")

        result.approved = True
        await self._log_check(order_info, result, now)
        return result

    def _check_position_limits(
        self,
        order_info: dict[str, Any],
        nav: float,
        regime_state: int,
    ) -> list[str]:
        """Check position-level limits. Returns list of rejection reasons (empty = pass)."""
        reasons = []
        cfg = self._config
        regime_mults = REGIME_MULTIPLIERS.get(regime_state, REGIME_MULTIPLIERS[0])

        # DTE check
        legs = order_info.get("legs", [])
        today = datetime.now().date()
        for leg in legs:
            expiry_str = leg.get("expiry", "")
            try:
                from datetime import date as date_type
                if isinstance(expiry_str, str):
                    expiry = date_type.fromisoformat(expiry_str)
                elif hasattr(expiry_str, "isoformat"):
                    expiry = expiry_str
                else:
                    continue
                dte = (expiry - today).days
                if dte < cfg.min_dte:
                    reasons.append(f"DTE {dte} below minimum {cfg.min_dte}")
                if dte > cfg.max_dte:
                    reasons.append(f"DTE {dte} above maximum {cfg.max_dte}")
            except (ValueError, TypeError):
                logger.warning("Could not parse expiry '%s' for DTE check — rejecting leg", expiry_str)
                reasons.append(f"Unparseable expiry '{expiry_str}' — cannot validate DTE")

        return reasons

    def _check_strategy_limits(
        self,
        order_info: dict[str, Any],
        positions: list[dict[str, Any]],
        nav: float,
        regime_state: int,
    ) -> list[str]:
        """Check strategy-level limits. Returns list of rejection reasons."""
        reasons = []
        cfg = self._config
        regime_mults = REGIME_MULTIPLIERS.get(regime_state, REGIME_MULTIPLIERS[0])

        strategy_id = order_info.get("strategy_id")
        if strategy_id is None:
            return reasons

        # Max concurrent positions per strategy
        strat_positions = [
            p for p in positions
            if p.get("strategy_id") == strategy_id and p.get("status") == "open"
        ]
        max_concurrent = int(cfg.max_concurrent_per_strategy * regime_mults.get("max_concurrent", 1.0))
        if len(strat_positions) >= max_concurrent:
            reasons.append(
                f"Strategy {strategy_id}: {len(strat_positions)} open positions "
                f">= limit {max_concurrent}"
            )

        return reasons

    def _check_portfolio_limits(
        self,
        positions: list[dict[str, Any]],
        nav: float,
        spot: float,
        regime_state: int,
    ) -> list[str]:
        """Check portfolio-level limits. Returns list of rejection reasons."""
        reasons = []
        cfg = self._config
        regime_mults = REGIME_MULTIPLIERS.get(regime_state, REGIME_MULTIPLIERS[0])

        if self._last_greeks is not None:
            greeks = self._last_greeks

            # Delta limit
            max_delta = cfg.max_portfolio_delta * regime_mults.get("portfolio_delta", 1.0)
            if abs(greeks.delta) > max_delta:
                reasons.append(
                    f"Portfolio delta {abs(greeks.delta):.1f} exceeds "
                    f"limit {max_delta:.1f}"
                )

            # Gamma limit
            max_gamma = cfg.max_portfolio_gamma * regime_mults.get("portfolio_gamma", 1.0)
            if abs(greeks.gamma) > max_gamma:
                reasons.append(
                    f"Portfolio gamma {abs(greeks.gamma):.4f} exceeds "
                    f"limit {max_gamma:.1f}"
                )

            # Vega limit
            max_vega = cfg.max_portfolio_vega * regime_mults.get("portfolio_vega", 1.0)
            if abs(greeks.vega) > max_vega:
                reasons.append(
                    f"Portfolio vega ${abs(greeks.vega):,.0f} exceeds "
                    f"limit ${max_vega:,.0f}"
                )

        # Cash reserve check
        if nav > 0:
            total_premium = sum(
                abs(p.get("entry_price", 0.0)) * p.get("quantity", 1) * 100
                for p in positions if p.get("status") == "open"
            )
            deployed_pct = total_premium / nav
            if (1 - deployed_pct) < cfg.min_cash_reserve_pct:
                reasons.append(
                    f"Cash reserve {(1 - deployed_pct):.1%} below "
                    f"minimum {cfg.min_cash_reserve_pct:.1%}"
                )

        return reasons

    async def monitor_portfolio(
        self,
        positions: list[dict[str, Any]],
        spot: float,
        nav: float,
        daily_pnl: float = 0.0,
        vix: float = 16.0,
        anomaly_score: float = 0.0,
        regime_state: int = 0,
    ) -> list[RiskAlert]:
        """Continuous portfolio monitoring. Called every tick.

        Computes Greeks, checks all portfolio limits, updates circuit
        breakers, and returns alerts. Persists risk snapshot to DB.

        Args:
            positions: All open positions.
            spot: Current SPX price.
            nav: Current portfolio NAV.
            daily_pnl: Today's realized + unrealized P&L change.
            vix: Current VIX level.
            anomaly_score: Current composite anomaly score.
            regime_state: Current HMM regime.

        Returns:
            List of RiskAlert objects for any warnings or breaches.
        """
        now = datetime.now().isoformat()
        alerts: list[RiskAlert] = []
        cfg = self._config
        regime_mults = REGIME_MULTIPLIERS.get(regime_state, REGIME_MULTIPLIERS[0])

        # Compute Greeks
        greeks = self._analyzer.compute_greeks(positions, spot)
        self._last_greeks = greeks

        # Delta check
        max_delta = cfg.max_portfolio_delta * regime_mults.get("portfolio_delta", 1.0)
        if max_delta > 0:
            util = abs(greeks.delta) / max_delta
            if util > 1.0:
                alerts.append(RiskAlert(
                    level="breach", category="delta",
                    message=f"Portfolio delta {greeks.delta:.1f} exceeds limit {max_delta:.1f}",
                    current_value=abs(greeks.delta), limit_value=max_delta,
                    utilization_pct=round(util * 100, 1), timestamp=now,
                ))
            elif util > 0.8:
                alerts.append(RiskAlert(
                    level="warning", category="delta",
                    message=f"Portfolio delta at {util:.0%} of limit",
                    current_value=abs(greeks.delta), limit_value=max_delta,
                    utilization_pct=round(util * 100, 1), timestamp=now,
                ))

        # Daily loss circuit breaker
        if nav > 0:
            daily_loss_limit = nav * cfg.max_daily_loss_pct * regime_mults.get("daily_loss_pct", 1.0)
            if daily_pnl < -daily_loss_limit:
                self._circuit_breakers["daily_loss"] = True
                alerts.append(RiskAlert(
                    level="circuit_breaker", category="daily_loss",
                    message=f"Daily loss ${-daily_pnl:,.0f} exceeds limit ${daily_loss_limit:,.0f}",
                    current_value=daily_pnl, limit_value=-daily_loss_limit,
                    utilization_pct=100.0, timestamp=now,
                ))

        # Drawdown circuit breaker
        if nav > 0 and self._peak_equity > 0:
            drawdown_pct = (nav - self._peak_equity) / self._peak_equity
            if drawdown_pct < -cfg.max_drawdown_pct:
                self._circuit_breakers["drawdown"] = True
                alerts.append(RiskAlert(
                    level="circuit_breaker", category="drawdown",
                    message=f"Drawdown {drawdown_pct:.1%} exceeds limit {-cfg.max_drawdown_pct:.1%}",
                    current_value=drawdown_pct, limit_value=-cfg.max_drawdown_pct,
                    utilization_pct=100.0, timestamp=now,
                ))

        # VIX halt
        if vix > cfg.vix_halt_threshold:
            self._circuit_breakers["vix_halt"] = True
            alerts.append(RiskAlert(
                level="circuit_breaker", category="vix",
                message=f"VIX {vix:.1f} exceeds halt threshold {cfg.vix_halt_threshold}",
                current_value=vix, limit_value=cfg.vix_halt_threshold,
                utilization_pct=100.0, timestamp=now,
            ))
        elif vix < cfg.vix_resume_threshold and self._circuit_breakers.get("vix_halt"):
            self._circuit_breakers["vix_halt"] = False

        # Anomaly halt
        if anomaly_score > cfg.anomaly_halt_threshold:
            self._circuit_breakers["anomaly_halt"] = True
            alerts.append(RiskAlert(
                level="circuit_breaker", category="anomaly",
                message=f"Anomaly score {anomaly_score:.2f} exceeds halt threshold",
                current_value=anomaly_score, limit_value=cfg.anomaly_halt_threshold,
                utilization_pct=100.0, timestamp=now,
            ))
        elif anomaly_score < cfg.anomaly_resume_threshold and self._circuit_breakers.get("anomaly_halt"):
            self._circuit_breakers["anomaly_halt"] = False

        # Update peak equity
        if nav > self._peak_equity:
            self._peak_equity = nav

        # Persist snapshot
        await self._save_snapshot(greeks, nav, regime_state, anomaly_score, len(alerts), now)

        # Persist alerts
        for alert in alerts:
            await self._save_alert(alert)

        return alerts

    def get_active_circuit_breakers(self) -> list[str]:
        """Return names of active circuit breakers."""
        return [k for k, v in self._circuit_breakers.items() if v]

    def reset_circuit_breaker(self, name: str) -> bool:
        """Manually reset a circuit breaker (e.g. from Discord command).

        Returns True if the breaker existed and was reset.
        """
        if name in self._circuit_breakers:
            self._circuit_breakers[name] = False
            return True
        return False

    def reset_daily_state(self) -> None:
        """Reset daily state. Called at start of day."""
        self._daily_realized_pnl = 0.0
        self._circuit_breakers["daily_loss"] = False
        self._consecutive_failures = 0

    async def get_risk_snapshot(
        self,
        positions: list[dict[str, Any]],
        spot: float,
        nav: float,
        regime_state: int = 0,
        anomaly_score: float = 0.0,
        predicted_vol: float = 0.15,
    ) -> RiskSnapshot:
        """Generate complete risk snapshot for Discord reporting.

        Runs full analysis: Greeks + VaR + stress tests + concentration.
        More expensive than monitor_portfolio() -- use on-demand only.

        Args:
            positions: All open positions.
            spot: Current SPX spot price.
            nav: Current portfolio NAV.
            regime_state: Current regime.
            anomaly_score: Current anomaly score.
            predicted_vol: Vol forecast for VaR.

        Returns:
            Complete RiskSnapshot.
        """
        now = datetime.now().isoformat()

        greeks = self._analyzer.compute_greeks(positions, spot)
        var_result = self._analyzer.compute_var(greeks, spot, predicted_vol, nav)
        stress_results = self._stress_engine.run_all_scenarios(positions, spot, nav)
        concentration = self._analyzer.compute_concentration(positions, greeks, nav)

        active_breakers = self.get_active_circuit_breakers()

        # Risk utilization
        cfg = self._config
        utilization = {}
        if cfg.max_portfolio_delta > 0:
            utilization["delta"] = round(abs(greeks.delta) / cfg.max_portfolio_delta * 100, 1)
        if cfg.max_portfolio_gamma > 0:
            utilization["gamma"] = round(abs(greeks.gamma) / cfg.max_portfolio_gamma * 100, 1)
        if cfg.max_portfolio_vega > 0:
            utilization["vega"] = round(abs(greeks.vega) / cfg.max_portfolio_vega * 100, 1)
        if nav > 0 and cfg.max_var_95_pct > 0:
            utilization["var_95"] = round(var_result.pct_of_nav_95 / cfg.max_var_95_pct * 100, 1)

        return RiskSnapshot(
            portfolio_greeks=greeks,
            var_result=var_result,
            stress_results=stress_results,
            concentration=concentration,
            active_alerts=[],  # populated by caller from monitor_portfolio
            circuit_breakers_active=active_breakers,
            regime_state=regime_state,
            regime_name=_regime_name(regime_state),
            anomaly_score=anomaly_score,
            nav=nav,
            risk_utilization=utilization,
            timestamp=now,
        )

    async def _save_snapshot(
        self,
        greeks: PortfolioGreeks,
        nav: float,
        regime_state: int,
        anomaly_score: float,
        num_alerts: int,
        timestamp: str,
    ) -> None:
        """Persist risk snapshot to DB."""
        try:
            await self._db.execute(
                """
                INSERT INTO risk_snapshots
                    (timestamp, portfolio_nav, portfolio_delta, portfolio_gamma,
                     portfolio_theta, portfolio_vega, dollar_delta, dollar_gamma,
                     var_95, var_99, cvar_95, regime_state, anomaly_score,
                     num_positions, num_alerts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp, nav, greeks.delta, greeks.gamma,
                    greeks.theta, greeks.vega, greeks.dollar_delta, greeks.dollar_gamma,
                    self._last_var.dg_var_95 if self._last_var else None,
                    self._last_var.dg_var_99 if self._last_var else None,
                    self._last_var.cvar_95 if self._last_var else None,
                    regime_state, anomaly_score,
                    greeks.num_positions, num_alerts,
                ),
            )
            await self._db.commit()
        except Exception as e:
            logger.error("Failed to save risk snapshot: %s", e)

    async def _save_alert(self, alert: RiskAlert) -> None:
        """Persist alert to DB."""
        try:
            await self._db.execute(
                """
                INSERT INTO risk_alerts
                    (timestamp, level, category, message, current_value, limit_value)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (alert.timestamp, alert.level, alert.category,
                 alert.message, alert.current_value, alert.limit_value),
            )
            await self._db.commit()
        except Exception as e:
            logger.error("Failed to save risk alert: %s", e)

    async def _log_check(
        self,
        order_info: dict[str, Any],
        result: RiskCheckResult,
        timestamp: str,
    ) -> None:
        """Persist pre-trade check to audit log."""
        try:
            checks_json = json.dumps({
                "passed": result.checks_passed,
                "failed": result.checks_failed,
                "reasons": result.reasons,
            })
            await self._db.execute(
                """
                INSERT INTO risk_check_log
                    (timestamp, order_id, strategy_id, approved,
                     checks_json, regime_state, anomaly_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    order_info.get("order_id", 0),
                    order_info.get("strategy_id"),
                    1 if result.approved else 0,
                    checks_json,
                    result.regime_state,
                    0.0,
                ),
            )
            await self._db.commit()
        except Exception as e:
            logger.error("Failed to log risk check: %s", e)


def _regime_name(state: int) -> str:
    """Map regime state to name."""
    return {0: "risk-on", 1: "risk-off", 2: "crisis"}.get(state, "unknown")
