"""Monte Carlo simulation for strategy robustness testing.

Uses bootstrap resampling of trade returns to generate a distribution
of performance outcomes. Tests if a strategy survives random perturbation
of trade ordering.

Pass criteria: 5th-percentile Sharpe > 0
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class MonteCarloResult:
    """Result of Monte Carlo simulation."""

    strategy_name: str
    n_simulations: int
    sharpe_distribution: list[float]
    sharpe_mean: float
    sharpe_std: float
    sharpe_5th_pct: float
    max_drawdown_95th_pct: float
    final_return_5th_pct: float
    passed: bool  # 5th-pct Sharpe > 0


class MonteCarloSimulator:
    """Bootstrap resampling Monte Carlo simulator.

    Args:
        n_simulations: Number of simulation runs.
        seed: Optional random seed for reproducibility.
    """

    def __init__(self, n_simulations: int = 1000, seed: int | None = None) -> None:
        self._n_simulations = n_simulations
        self._rng = np.random.default_rng(seed)

    def run(
        self,
        trade_returns: pd.Series | list[float] | np.ndarray,
        strategy_name: str = "",
    ) -> MonteCarloResult:
        """Run Monte Carlo simulation via bootstrap resampling.

        For each simulation:
        1. Resample trades with replacement (same number of trades)
        2. Compute equity curve from resampled trades
        3. Calculate Sharpe, max drawdown, final return

        Args:
            trade_returns: Individual trade P&L values.
            strategy_name: Name for labeling results.

        Returns:
            MonteCarloResult with distributional statistics.
        """
        if isinstance(trade_returns, pd.Series):
            returns = trade_returns.values.astype(float)
        elif isinstance(trade_returns, list):
            returns = np.array(trade_returns, dtype=float)
        else:
            returns = np.asarray(trade_returns, dtype=float)

        n_trades = len(returns)
        if n_trades == 0:
            return MonteCarloResult(
                strategy_name=strategy_name,
                n_simulations=0,
                sharpe_distribution=[],
                sharpe_mean=0.0,
                sharpe_std=0.0,
                sharpe_5th_pct=0.0,
                max_drawdown_95th_pct=0.0,
                final_return_5th_pct=0.0,
                passed=False,
            )

        sharpes = []
        max_drawdowns = []
        final_returns = []

        for _ in range(self._n_simulations):
            indices = self._rng.integers(0, n_trades, size=n_trades)
            resampled = returns[indices]

            # Equity curve
            equity = np.cumsum(resampled)

            # Sharpe (annualized, assuming trade-level returns)
            mean_ret = np.mean(resampled)
            std_ret = np.std(resampled)
            sharpe = float((mean_ret / std_ret) * np.sqrt(252)) if std_ret > 0 else 0.0
            sharpes.append(sharpe)

            # Max drawdown
            running_max = np.maximum.accumulate(equity)
            drawdown = equity - running_max
            max_dd = float(np.min(drawdown))
            max_drawdowns.append(max_dd)

            # Final return
            final_returns.append(float(equity[-1]))

        sharpes_arr = np.array(sharpes)
        dd_arr = np.array(max_drawdowns)
        fr_arr = np.array(final_returns)

        sharpe_5th = float(np.percentile(sharpes_arr, 5))

        return MonteCarloResult(
            strategy_name=strategy_name,
            n_simulations=self._n_simulations,
            sharpe_distribution=sharpes,
            sharpe_mean=float(np.mean(sharpes_arr)),
            sharpe_std=float(np.std(sharpes_arr)),
            sharpe_5th_pct=sharpe_5th,
            max_drawdown_95th_pct=float(np.percentile(dd_arr, 95)),
            final_return_5th_pct=float(np.percentile(fr_arr, 5)),
            passed=sharpe_5th > 0,
        )
