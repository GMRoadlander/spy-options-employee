"""Scenario-based stress testing for paper options portfolios.

Reprices all positions under hypothetical market moves using full
Black-Scholes repricing (not Greek approximation). This captures
non-linear payoff effects that the delta-gamma VaR approximation misses.

Standard scenarios: spot shocks, vol shocks, time decay, and combined
(e.g. "Black Monday", "Flash Crash", "COVID Crash").
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

import numpy as np

from src.analysis.greeks import black_scholes_d1_d2
from src.risk.config import RiskConfig
from src.risk.models import StressScenario, StressTestResult

logger = logging.getLogger(__name__)

SPX_MULTIPLIER = 100.0

# --- Standard Scenarios ---

SPOT_SCENARIOS: list[StressScenario] = [
    StressScenario(name="SPX -10%", spot_shock=-0.10),
    StressScenario(name="SPX -5%", spot_shock=-0.05),
    StressScenario(name="SPX -2%", spot_shock=-0.02),
    StressScenario(name="SPX -1%", spot_shock=-0.01),
    StressScenario(name="SPX +1%", spot_shock=+0.01),
    StressScenario(name="SPX +2%", spot_shock=+0.02),
    StressScenario(name="SPX +5%", spot_shock=+0.05),
    StressScenario(name="SPX +10%", spot_shock=+0.10),
]

VOL_SCENARIOS: list[StressScenario] = [
    StressScenario(name="VIX +5", vol_shock=+0.05),
    StressScenario(name="VIX +10", vol_shock=+0.10),
    StressScenario(name="VIX +20", vol_shock=+0.20),
    StressScenario(name="VIX -5", vol_shock=-0.05),
]

COMBINED_SCENARIOS: list[StressScenario] = [
    StressScenario(name="Black Monday", spot_shock=-0.07, vol_shock=+0.25, time_days=1),
    StressScenario(name="Flash Crash", spot_shock=-0.05, vol_shock=+0.15, time_days=0.5),
    StressScenario(name="COVID Crash", spot_shock=-0.12, vol_shock=+0.30, time_days=5),
    StressScenario(name="Rate Hike", spot_shock=-0.03, vol_shock=+0.05, time_days=1),
    StressScenario(name="Melt-Up", spot_shock=+0.05, vol_shock=-0.05, time_days=3),
    StressScenario(name="Vol Crush", spot_shock=+0.01, vol_shock=-0.10, time_days=1),
]

ALL_SCENARIOS = SPOT_SCENARIOS + VOL_SCENARIOS + COMBINED_SCENARIOS


def _bs_price(
    S: float, K: float, T: float, sigma: float, r: float, option_type: str,
) -> float:
    """Black-Scholes option price. Returns 0.0 for invalid inputs."""
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        # Intrinsic value at expiry
        if option_type == "call":
            return max(S - K, 0.0)
        else:
            return max(K - S, 0.0)

    try:
        from scipy.stats import norm as norm_dist
        d1, d2 = black_scholes_d1_d2(S, K, T, sigma, r)
        if option_type == "call":
            return float(S * norm_dist.cdf(d1) - K * np.exp(-r * T) * norm_dist.cdf(d2))
        else:
            return float(K * np.exp(-r * T) * norm_dist.cdf(-d2) - S * norm_dist.cdf(-d1))
    except (ValueError, ZeroDivisionError):
        if option_type == "call":
            return max(S - K, 0.0)
        else:
            return max(K - S, 0.0)


class StressTestEngine:
    """Scenario-based stress testing with full Black-Scholes repricing.

    For each scenario, every leg of every open position is repriced
    using Black-Scholes with modified inputs (S, sigma, T). The P&L
    difference from current value gives the scenario impact.

    Args:
        config: RiskConfig with risk-free rate.
    """

    def __init__(self, config: RiskConfig) -> None:
        self._config = config
        self._r = config.risk_free_rate

    def run_scenario(
        self,
        positions: list[dict[str, Any]],
        spot: float,
        scenario: StressScenario,
        nav: float,
    ) -> StressTestResult:
        """Run a single stress scenario with full repricing.

        Args:
            positions: Open position dicts with legs, quantity, entry_price.
            spot: Current SPX spot price.
            scenario: The scenario to simulate.
            nav: Portfolio NAV for percentage calculations.

        Returns:
            StressTestResult with P&L impact.
        """
        spot_new = spot * (1 + scenario.spot_shock)
        dt = scenario.time_days / 365.0
        today = date.today()

        total_pnl = 0.0
        position_pnls: dict[int, float] = {}

        for pos in positions:
            pos_id = pos.get("id", 0)
            legs = pos.get("legs", [])
            if isinstance(legs, str):
                try:
                    legs = json.loads(legs)
                except (json.JSONDecodeError, TypeError):
                    continue

            quantity = pos.get("quantity", 1)
            pos_pnl = 0.0

            for leg in legs:
                strike = leg.get("strike", 0.0)
                option_type = leg.get("option_type", "call")
                action = leg.get("action", "buy")
                iv = leg.get("iv_at_fill") or leg.get("iv", 0.20)
                leg_qty = leg.get("quantity", 1)

                # Time to expiry
                expiry_str = leg.get("expiry", "")
                try:
                    if isinstance(expiry_str, str):
                        expiry_date = date.fromisoformat(expiry_str)
                    else:
                        expiry_date = expiry_str
                    dte = (expiry_date - today).days
                    T = max(dte / 365.0, 0.001)
                except (ValueError, TypeError):
                    T = 0.001

                # Stressed inputs
                T_new = max(T - dt, 0.001)
                sigma_new = max(iv + scenario.vol_shock, 0.01)

                # Price before and after
                price_before = _bs_price(spot, strike, T, iv, self._r, option_type)
                price_after = _bs_price(spot_new, strike, T_new, sigma_new, self._r, option_type)

                # P&L per contract per leg
                sign = 1.0 if action == "buy" else -1.0
                leg_pnl = (price_after - price_before) * sign * leg_qty * quantity * SPX_MULTIPLIER
                pos_pnl += leg_pnl

            total_pnl += pos_pnl
            position_pnls[pos_id] = round(pos_pnl, 2)

        # Classify result
        pnl_pct = total_pnl / nav if nav > 0 else 0.0
        if abs(pnl_pct) > 0.10:
            status = "breach"
        elif abs(pnl_pct) > 0.05:
            status = "warn"
        else:
            status = "ok"

        return StressTestResult(
            scenario=scenario,
            portfolio_pnl=round(total_pnl, 2),
            pnl_pct_of_nav=round(pnl_pct, 6),
            status=status,
            position_pnls=position_pnls,
        )

    def run_all_scenarios(
        self,
        positions: list[dict[str, Any]],
        spot: float,
        nav: float,
        scenarios: list[StressScenario] | None = None,
    ) -> list[StressTestResult]:
        """Run all standard scenarios (spot + vol + combined).

        Args:
            positions: Open position dicts.
            spot: Current SPX price.
            nav: Portfolio NAV.
            scenarios: Override scenario list (defaults to ALL_SCENARIOS).

        Returns:
            List of StressTestResult, one per scenario.
        """
        if scenarios is None:
            scenarios = ALL_SCENARIOS

        results = []
        for scenario in scenarios:
            try:
                result = self.run_scenario(positions, spot, scenario, nav)
                results.append(result)
            except Exception as e:
                logger.error("Stress test '%s' failed: %s", scenario.name, e)
                results.append(StressTestResult(
                    scenario=scenario,
                    portfolio_pnl=0.0,
                    pnl_pct_of_nav=0.0,
                    status="error",
                ))
        return results
