"""Portfolio analytics: Greeks aggregation, VaR, and concentration.

PortfolioAnalyzer is stateless -- all state comes from the positions
and chain data passed to each method. This makes it easy to test
and to use from both the RiskManager (continuous) and Discord commands
(on-demand).

Greeks are computed using the existing Black-Scholes functions from
src/analysis/greeks.py. VaR uses the Delta-Gamma-Theta approximation
with Cornish-Fisher expansion.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any

import numpy as np
from scipy.stats import norm

from src.analysis.greeks import (
    black_scholes_delta,
    black_scholes_gamma,
    black_scholes_theta,
    black_scholes_vega,
)
from src.risk.config import RiskConfig
from src.risk.models import (
    ConcentrationReport,
    CorrelationReport,
    PortfolioGreeks,
    VaRResult,
)

logger = logging.getLogger(__name__)

# SPX multiplier for dollar conversion
SPX_MULTIPLIER = 100.0


class PortfolioAnalyzer:
    """Real-time portfolio risk analytics.

    Computes aggregated Greeks, VaR, concentration, and correlation.
    Stateless: all state comes from position data passed to methods.

    Args:
        config: RiskConfig with risk-free rate and limit parameters.
    """

    def __init__(self, config: RiskConfig) -> None:
        self._config = config
        self._risk_free_rate = config.risk_free_rate

    def compute_greeks(
        self,
        positions: list[dict[str, Any]],
        spot: float,
    ) -> PortfolioGreeks:
        """Aggregate Greeks across all open positions.

        For each position, parses the legs JSON and computes per-leg
        Greeks using Black-Scholes. Sums across all legs with proper
        sign convention (sell legs contribute negative delta for calls,
        positive delta for puts, etc.).

        Args:
            positions: List of open position dicts from PositionTracker.
                       Each must have 'legs' (JSON or list), 'quantity',
                       'strategy_id', 'entry_price'.
            spot: Current SPX spot price.

        Returns:
            PortfolioGreeks with raw and dollar-denominated values.
        """
        now = datetime.now().isoformat()
        result = PortfolioGreeks(timestamp=now)

        if not positions or spot <= 0:
            return result

        today = date.today()
        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0
        total_premium = 0.0
        total_legs = 0

        by_expiry: dict[str, dict[str, float]] = {}
        by_strategy: dict[str, dict[str, float]] = {}

        for pos in positions:
            legs = pos.get("legs", [])
            if isinstance(legs, str):
                try:
                    legs = json.loads(legs)
                except (json.JSONDecodeError, TypeError):
                    continue

            quantity = pos.get("quantity", 1)
            strategy_id = str(pos.get("strategy_id", "unknown"))
            entry_price = pos.get("entry_price", 0.0)

            # Track premium at risk per position
            total_premium += abs(entry_price) * quantity * SPX_MULTIPLIER

            for leg in legs:
                total_legs += 1
                strike = leg.get("strike", 0.0)
                option_type = leg.get("option_type", "call")
                action = leg.get("action", "buy")
                expiry_str = leg.get("expiry", "")
                iv = leg.get("iv_at_fill") or leg.get("iv", 0.20)
                leg_qty = leg.get("quantity", 1)

                # Compute T (time to expiry in years)
                try:
                    if isinstance(expiry_str, str):
                        expiry_date = date.fromisoformat(expiry_str)
                    else:
                        expiry_date = expiry_str
                    dte = (expiry_date - today).days
                    T = max(dte / 365.0, 0.001)
                except (ValueError, TypeError):
                    T = 0.001
                    expiry_str = "unknown"

                if strike <= 0 or iv <= 0:
                    continue

                # Compute per-leg Greeks
                delta = black_scholes_delta(
                    spot, strike, T, iv, self._risk_free_rate, option_type,
                )
                gamma = black_scholes_gamma(
                    spot, strike, T, iv, self._risk_free_rate,
                )
                theta = black_scholes_theta(
                    spot, strike, T, iv, self._risk_free_rate, option_type,
                )
                vega = black_scholes_vega(
                    spot, strike, T, iv, self._risk_free_rate,
                )

                # Sign convention: sell legs reverse the Greek contribution
                # Buy +1 contract of a call: +delta
                # Sell +1 contract of a call: -delta
                sign = 1.0 if action == "buy" else -1.0
                effective_qty = sign * quantity * leg_qty

                leg_delta = delta * effective_qty * SPX_MULTIPLIER
                leg_gamma = gamma * effective_qty * SPX_MULTIPLIER
                leg_theta = theta * effective_qty * SPX_MULTIPLIER
                leg_vega = vega * effective_qty * SPX_MULTIPLIER

                total_delta += leg_delta
                total_gamma += leg_gamma
                total_theta += leg_theta
                total_vega += leg_vega

                # Accumulate per-expiry
                exp_key = str(expiry_str)
                if exp_key not in by_expiry:
                    by_expiry[exp_key] = {
                        "delta": 0.0, "gamma": 0.0,
                        "theta": 0.0, "vega": 0.0,
                    }
                by_expiry[exp_key]["delta"] += leg_delta
                by_expiry[exp_key]["gamma"] += leg_gamma
                by_expiry[exp_key]["theta"] += leg_theta
                by_expiry[exp_key]["vega"] += leg_vega

                # Accumulate per-strategy
                if strategy_id not in by_strategy:
                    by_strategy[strategy_id] = {
                        "delta": 0.0, "gamma": 0.0,
                        "theta": 0.0, "vega": 0.0,
                    }
                by_strategy[strategy_id]["delta"] += leg_delta
                by_strategy[strategy_id]["gamma"] += leg_gamma
                by_strategy[strategy_id]["theta"] += leg_theta
                by_strategy[strategy_id]["vega"] += leg_vega

        # Dollar Greeks
        dollar_delta = total_delta  # Already in $ terms from multiplier
        dollar_gamma = total_gamma * spot * 0.01  # Delta change per 1% SPX move

        result.delta = round(total_delta, 4)
        result.gamma = round(total_gamma, 6)
        result.theta = round(total_theta, 2)
        result.vega = round(total_vega, 2)
        result.dollar_delta = round(dollar_delta, 2)
        result.dollar_gamma = round(dollar_gamma, 2)
        result.net_premium = round(total_premium, 2)
        result.num_positions = len(positions)
        result.num_legs = total_legs
        result.greeks_by_expiry = by_expiry
        result.greeks_by_strategy = by_strategy

        return result

    def compute_var(
        self,
        greeks: PortfolioGreeks,
        spot: float,
        daily_vol: float,
        nav: float,
        historical_returns: np.ndarray | None = None,
    ) -> VaRResult:
        """Compute Delta-Gamma-Theta VaR and optionally Historical VaR.

        Primary method: parametric Delta-Gamma VaR using the LSTM
        vol forecast (daily_vol). Secondary: historical simulation
        using past SPX returns if provided.

        Args:
            greeks: Aggregated portfolio Greeks.
            spot: Current SPX spot price.
            daily_vol: Predicted 1-day volatility (annualized decimal,
                       e.g. 0.15 for 15%). Converted internally to daily.
            nav: Current portfolio NAV for percentage calculations.
            historical_returns: Optional array of historical daily SPX
                               returns for historical VaR (e.g. last 252 days).

        Returns:
            VaRResult with parametric and (optionally) historical VaR.
        """
        now = datetime.now().isoformat()
        result = VaRResult(timestamp=now, daily_vol_used=daily_vol)

        if spot <= 0 or daily_vol <= 0:
            return result

        # Convert annualized vol to daily
        daily_vol_actual = daily_vol / np.sqrt(252)
        dS = spot * daily_vol_actual  # 1-sigma daily dollar move

        # Delta-Gamma VaR at 95% and 99%
        for confidence, attr_suffix in [(0.95, "95"), (0.99, "99")]:
            z = norm.ppf(confidence)

            # First-order (delta) component
            delta_pnl = abs(greeks.dollar_delta) * dS * z

            # Second-order (gamma) component
            gamma_pnl = 0.5 * abs(greeks.dollar_gamma) * (dS * z) ** 2

            # Theta component (1-day decay, always a cost for premium sellers)
            theta_pnl = abs(greeks.theta)

            var = delta_pnl + gamma_pnl + theta_pnl

            setattr(result, f"dg_var_{attr_suffix}", round(var, 2))
            if nav > 0:
                setattr(result, f"pct_of_nav_{attr_suffix}", round(var / nav, 6))

        # Historical VaR (if returns provided)
        if historical_returns is not None and len(historical_returns) > 20:
            result = self._compute_historical_var(
                result, greeks, spot, historical_returns, nav,
            )

        return result

    def _compute_historical_var(
        self,
        result: VaRResult,
        greeks: PortfolioGreeks,
        spot: float,
        historical_returns: np.ndarray,
        nav: float,
    ) -> VaRResult:
        """Add historical VaR to an existing VaRResult.

        Replays each historical daily return through the current
        portfolio Greeks to build a P&L distribution.
        """
        dS_values = spot * historical_returns

        # P&L for each scenario (delta-gamma approximation)
        pnl_scenarios = (
            greeks.dollar_delta * dS_values
            + 0.5 * greeks.dollar_gamma * dS_values ** 2
            + greeks.theta
        )

        sorted_pnl = np.sort(pnl_scenarios)
        n = len(sorted_pnl)

        idx_95 = max(int(n * 0.05), 0)
        idx_99 = max(int(n * 0.01), 0)

        result.hist_var_95 = round(float(-sorted_pnl[idx_95]), 2)
        result.hist_var_99 = round(float(-sorted_pnl[idx_99]), 2)

        # CVaR (Expected Shortfall): average of losses beyond VaR
        if idx_95 > 0:
            result.cvar_95 = round(float(-np.mean(sorted_pnl[:idx_95])), 2)
        else:
            result.cvar_95 = result.hist_var_95

        result.worst_case = round(float(-sorted_pnl[0]), 2)

        return result

    def compute_concentration(
        self,
        positions: list[dict[str, Any]],
        greeks: PortfolioGreeks,
        nav: float,
    ) -> ConcentrationReport:
        """Analyze portfolio concentration by expiry, strategy, and strike range.

        Args:
            positions: Open position dicts.
            greeks: Pre-computed portfolio Greeks (with by_expiry/by_strategy).
            nav: Current portfolio NAV.

        Returns:
            ConcentrationReport with concentration percentages and warnings.
        """
        report = ConcentrationReport()

        total_abs_delta = abs(greeks.delta) if greeks.delta != 0 else 1.0
        total_premium = greeks.net_premium if greeks.net_premium > 0 else 1.0

        # By expiry
        for expiry, exp_greeks in greeks.greeks_by_expiry.items():
            delta_pct = abs(exp_greeks["delta"]) / total_abs_delta if total_abs_delta > 0 else 0.0
            # Count positions with this expiry
            pos_count = 0
            premium_in_expiry = 0.0
            for pos in positions:
                legs = pos.get("legs", [])
                if isinstance(legs, str):
                    try:
                        legs = json.loads(legs)
                    except (json.JSONDecodeError, TypeError):
                        continue
                for leg in legs:
                    if str(leg.get("expiry", "")) == expiry:
                        pos_count += 1
                        premium_in_expiry += abs(pos.get("entry_price", 0.0)) * pos.get("quantity", 1) * SPX_MULTIPLIER
                        break

            report.by_expiry[expiry] = {
                "delta_pct": round(delta_pct, 4),
                "premium_pct": round(premium_in_expiry / total_premium, 4) if total_premium > 0 else 0.0,
                "position_count": pos_count,
            }

        # By strategy
        for strat_id, strat_greeks in greeks.greeks_by_strategy.items():
            delta_pct = abs(strat_greeks["delta"]) / total_abs_delta if total_abs_delta > 0 else 0.0
            premium_in_strat = sum(
                abs(pos.get("entry_price", 0.0)) * pos.get("quantity", 1) * SPX_MULTIPLIER
                for pos in positions
                if str(pos.get("strategy_id", "")) == strat_id
            )
            pos_count = sum(
                1 for pos in positions
                if str(pos.get("strategy_id", "")) == strat_id
            )

            report.by_strategy[strat_id] = {
                "delta_pct": round(delta_pct, 4),
                "premium_pct": round(premium_in_strat / total_premium, 4) if total_premium > 0 else 0.0,
                "position_count": pos_count,
            }

        # By 25-point strike range
        strike_ranges: dict[str, float] = {}
        for pos in positions:
            legs = pos.get("legs", [])
            if isinstance(legs, str):
                try:
                    legs = json.loads(legs)
                except (json.JSONDecodeError, TypeError):
                    continue
            for leg in legs:
                strike = leg.get("strike", 0.0)
                range_low = int(strike // 25) * 25
                range_label = f"{range_low}-{range_low + 25}"
                premium = abs(leg.get("fill_price", 0.0)) * pos.get("quantity", 1) * SPX_MULTIPLIER
                strike_ranges[range_label] = strike_ranges.get(range_label, 0.0) + premium

        for label, premium in strike_ranges.items():
            report.by_strike_range[label] = {
                "premium_pct": round(premium / total_premium, 4) if total_premium > 0 else 0.0,
            }

        # Max concentrations
        if report.by_expiry:
            report.max_expiry_concentration = max(
                v["delta_pct"] for v in report.by_expiry.values()
            )
        if report.by_strategy:
            report.max_strategy_concentration = max(
                v["premium_pct"] for v in report.by_strategy.values()
            )
        if report.by_strike_range:
            report.max_strike_concentration = max(
                v["premium_pct"] for v in report.by_strike_range.values()
            )

        # Warnings
        cfg = self._config
        if report.max_expiry_concentration > cfg.max_expiry_concentration_pct:
            report.warnings.append(
                f"Expiry concentration {report.max_expiry_concentration:.1%} "
                f"exceeds limit {cfg.max_expiry_concentration_pct:.1%}"
            )
        if report.max_strike_concentration > cfg.max_strike_concentration_pct:
            report.warnings.append(
                f"Strike concentration {report.max_strike_concentration:.1%} "
                f"exceeds limit {cfg.max_strike_concentration_pct:.1%}"
            )

        return report

    def compute_correlation(
        self,
        strategy_daily_pnls: dict[int, list[float]] | None,
        strategy_greeks: dict[int, dict[str, float]] | None,
    ) -> CorrelationReport:
        """Compute cross-strategy correlation using P&L and/or Greeks.

        Uses Pearson correlation of daily P&L when available, falling
        back to cosine similarity of Greeks vectors for new strategies.

        Args:
            strategy_daily_pnls: {strategy_id: list of daily P&L values}.
                                 None if not enough history.
            strategy_greeks: {strategy_id: {delta, gamma, theta, vega}}.

        Returns:
            CorrelationReport with correlation data and warnings.
        """
        report = CorrelationReport()
        cfg = self._config

        # P&L correlation
        if strategy_daily_pnls and len(strategy_daily_pnls) >= 2:
            ids = sorted(strategy_daily_pnls.keys())
            for i, id_a in enumerate(ids):
                for id_b in ids[i + 1:]:
                    pnl_a = np.array(strategy_daily_pnls[id_a])
                    pnl_b = np.array(strategy_daily_pnls[id_b])

                    # Align lengths
                    min_len = min(len(pnl_a), len(pnl_b))
                    if min_len < 10:
                        continue

                    pnl_a = pnl_a[:min_len]
                    pnl_b = pnl_b[:min_len]

                    # Skip if either is constant
                    if np.std(pnl_a) < 1e-10 or np.std(pnl_b) < 1e-10:
                        continue

                    corr = float(np.corrcoef(pnl_a, pnl_b)[0, 1])
                    report.pnl_correlation[(id_a, id_b)] = round(corr, 4)

                    if corr >= cfg.high_correlation_threshold:
                        report.high_correlation_pairs.append((id_a, id_b, corr))
                        report.warnings.append(
                            f"Strategies {id_a} and {id_b} highly correlated "
                            f"({corr:.2f} >= {cfg.high_correlation_threshold})"
                        )
                    elif corr >= cfg.moderate_correlation_threshold:
                        report.moderate_correlation_pairs.append((id_a, id_b, corr))

        # Greeks similarity (always available if positions exist)
        if strategy_greeks and len(strategy_greeks) >= 2:
            ids = sorted(strategy_greeks.keys())
            for i, id_a in enumerate(ids):
                for id_b in ids[i + 1:]:
                    sim = _greeks_cosine_similarity(
                        strategy_greeks[id_a], strategy_greeks[id_b],
                    )
                    report.greeks_similarity[(id_a, id_b)] = round(sim, 4)

        return report


def _greeks_cosine_similarity(
    greeks_a: dict[str, float],
    greeks_b: dict[str, float],
) -> float:
    """Compute cosine similarity of two strategies' Greeks vectors.

    Returns value in [-1, 1]. +1 = same profile, -1 = perfect hedge.
    """
    keys = ["delta", "gamma", "theta", "vega"]
    a = np.array([greeks_a.get(k, 0.0) for k in keys])
    b = np.array([greeks_b.get(k, 0.0) for k in keys])

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a < 1e-10 or norm_b < 1e-10:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))
