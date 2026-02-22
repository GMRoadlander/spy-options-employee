"""Deflated Sharpe Ratio -- Bailey & Lopez de Prado (2014).

Guards against selection bias when multiple strategy variants are tested.
A strategy must exceed the *expected* best Sharpe among N independent trials
under the null hypothesis (all strategies have zero true Sharpe).

Part of the anti-overfitting pipeline (WFA + CPCV + DSR + Monte Carlo).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

EULER_MASCHERONI = 0.5772156649015329


@dataclass
class DSRResult:
    strategy_name: str
    estimated_sharpe: float     # raw SR of selected strategy
    expected_max_sharpe: float  # SR_0 (expected best under null)
    dsr: float                  # deflated SR in [0, 1]
    n_trials: int               # number of strategies/variants tested
    backtest_horizon: int       # trading days
    skewness: float
    kurtosis: float
    passed: bool                # dsr > 0.95 (p < 0.05)


def expected_max_sharpe(
    n_trials: int,
    mean_sr: float = 0.0,
    var_sr: float = 1.0,
) -> float:
    """Expected maximum SR from N independent trials under the null.

    E[max(SR)] = sqrt(Var[SR]) * [(1-gamma)*Phi_inv(1-1/N) + gamma*Phi_inv(1-1/(N*e))]
    where gamma = Euler-Mascheroni constant.
    """
    if n_trials <= 1:
        return mean_sr

    e = np.e
    gamma = EULER_MASCHERONI
    z1 = stats.norm.ppf(1 - 1.0 / n_trials)
    z2 = stats.norm.ppf(1 - 1.0 / (n_trials * e))
    sr0 = np.sqrt(var_sr) * ((1 - gamma) * z1 + gamma * z2)
    return sr0 + mean_sr


def deflated_sharpe_ratio(
    estimated_sharpe: float,
    expected_max_sr: float,
    backtest_horizon: int,
    skew: float = 0.0,
    kurtosis: float = 3.0,   # total kurtosis (excess = kurtosis - 3)
) -> float:
    """Compute the Deflated Sharpe Ratio.

    Returns a value in [0, 1].  Values > 0.95 pass at the 5% significance
    level (i.e. p < 0.05 that the observed SR is due to luck).

    DSR = Phi[(SR* - SR_0) * sqrt(T-1) / sqrt(1 - skew*SR* + (kurt_exc/4)*SR*^2)]
    """
    if backtest_horizon <= 1:
        return 0.0

    numerator = (estimated_sharpe - expected_max_sr) * np.sqrt(backtest_horizon - 1)

    # Adjust denominator for non-normal returns
    excess_kurt = kurtosis - 3.0
    denominator_sq = (
        1.0
        - skew * estimated_sharpe
        + (excess_kurt / 4.0) * estimated_sharpe ** 2
    )

    if denominator_sq <= 0:
        return 0.0

    denominator = np.sqrt(denominator_sq)

    if denominator == 0:
        return 0.0

    test_stat = numerator / denominator
    return float(stats.norm.cdf(test_stat))


def evaluate_dsr(
    strategy_sharpe: float,
    all_sharpes: list[float],
    backtest_horizon: int,
    skew: float = 0.0,
    kurtosis: float = 3.0,
    strategy_name: str = "",
) -> DSRResult:
    """Convenience wrapper: compute DSR from a strategy SR and comparison set."""
    n_trials = len(all_sharpes) if all_sharpes else 1

    if n_trials > 1:
        mean_sr = float(np.mean(all_sharpes))
        var_sr = float(np.var(all_sharpes))
    else:
        mean_sr = 0.0
        var_sr = 1.0

    sr0 = expected_max_sharpe(n_trials, mean_sr, var_sr)
    dsr_val = deflated_sharpe_ratio(
        strategy_sharpe, sr0, backtest_horizon, skew, kurtosis,
    )

    return DSRResult(
        strategy_name=strategy_name,
        estimated_sharpe=strategy_sharpe,
        expected_max_sharpe=sr0,
        dsr=dsr_val,
        n_trials=n_trials,
        backtest_horizon=backtest_horizon,
        skewness=skew,
        kurtosis=kurtosis,
        passed=dsr_val > 0.95,
    )
