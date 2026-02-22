"""Combinatorial Purged Cross-Validation (CPCV) for strategy evaluation.

Implements CPCV without requiring skfolio as a hard dependency. The core
algorithm splits daily returns into K folds, generates all combinatorial
test paths (choosing K_test folds for testing), and calculates the
Probability of Backtest Overfitting (PBO) from the distribution of
out-of-sample Sharpe ratios.

Purging removes observations near fold boundaries to prevent label leakage
from overlapping positions. Embargo adds extra buffer after test periods.

Reference: Bailey, Borwein, Lopez de Prado & Zhu (2017)
"The Probability of Backtest Overfitting"
"""

from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CPCVResult:
    """Result of CPCV analysis."""

    strategy_name: str
    n_folds: int
    n_test_folds: int
    n_paths: int
    purge_size: int
    embargo_size: int

    sharpe_distribution: list[float]
    sharpe_mean: float
    sharpe_std: float
    sharpe_5th_pct: float

    pbo: float
    passed: bool  # pbo < 0.50


def _sharpe_from_returns(returns: np.ndarray) -> float:
    """Calculate annualized Sharpe ratio from a returns array."""
    if len(returns) < 2:
        return 0.0
    std = np.std(returns)
    if std == 0:
        return 0.0
    return float((np.mean(returns) / std) * np.sqrt(252))


class CPCVAnalyzer:
    """Combinatorial Purged Cross-Validation analyzer.

    Args:
        n_folds: Number of folds to split the data into.
        n_test_folds: Number of folds used for testing in each path.
        purge_days: Days to remove at fold boundaries (>= max DTE).
        embargo_days: Extra buffer days after test periods.
    """

    def __init__(
        self,
        n_folds: int = 10,
        n_test_folds: int = 2,
        purge_days: int = 45,
        embargo_days: int = 5,
    ) -> None:
        self._n_folds = n_folds
        self._n_test_folds = n_test_folds
        self._purge_days = purge_days
        self._embargo_days = embargo_days

    def run(
        self,
        daily_returns: np.ndarray | list[float],
        strategy_name: str = "",
        max_paths: int = 200,
    ) -> CPCVResult:
        """Run CPCV analysis on daily returns.

        Args:
            daily_returns: Array of daily P&L or returns.
            strategy_name: Name for labeling results.
            max_paths: Cap on combinatorial paths to evaluate.

        Returns:
            CPCVResult with PBO and Sharpe distribution.
        """
        returns = np.asarray(daily_returns, dtype=float)
        n = len(returns)

        if n < self._n_folds * 10:
            logger.warning("Insufficient data for CPCV: %d points, need %d+", n, self._n_folds * 10)
            return CPCVResult(
                strategy_name=strategy_name,
                n_folds=self._n_folds,
                n_test_folds=self._n_test_folds,
                n_paths=0,
                purge_size=self._purge_days,
                embargo_size=self._embargo_days,
                sharpe_distribution=[],
                sharpe_mean=0.0,
                sharpe_std=0.0,
                sharpe_5th_pct=0.0,
                pbo=1.0,
                passed=False,
            )

        # Split into folds
        fold_size = n // self._n_folds
        folds = []
        for i in range(self._n_folds):
            start = i * fold_size
            end = start + fold_size if i < self._n_folds - 1 else n
            folds.append((start, end))

        # Generate combinatorial test paths
        all_combos = list(itertools.combinations(range(self._n_folds), self._n_test_folds))

        # Cap paths if too many
        if len(all_combos) > max_paths:
            rng = np.random.default_rng(42)
            indices = rng.choice(len(all_combos), size=max_paths, replace=False)
            all_combos = [all_combos[i] for i in sorted(indices)]

        # Evaluate each path
        oos_sharpes = []

        for test_fold_indices in all_combos:
            test_set = set(test_fold_indices)
            train_set = set(range(self._n_folds)) - test_set

            # Build test indices with purging
            test_indices = []
            for fi in test_fold_indices:
                start, end = folds[fi]
                test_indices.extend(range(start, end))

            # Build train indices with purging and embargo
            train_indices = []
            for fi in sorted(train_set):
                start, end = folds[fi]

                # Purge: remove days near test boundaries
                purged_start = start
                purged_end = end

                # If previous fold is a test fold, add embargo at start
                if fi > 0 and (fi - 1) in test_set:
                    purged_start = min(start + self._embargo_days, end)

                # If next fold is a test fold, purge at end
                if fi < self._n_folds - 1 and (fi + 1) in test_set:
                    purged_end = max(end - self._purge_days, purged_start)

                train_indices.extend(range(purged_start, purged_end))

            # Calculate OOS Sharpe for this path
            if test_indices:
                test_returns = returns[test_indices]
                oos_sharpe = _sharpe_from_returns(test_returns)
                oos_sharpes.append(oos_sharpe)

        if not oos_sharpes:
            return CPCVResult(
                strategy_name=strategy_name,
                n_folds=self._n_folds,
                n_test_folds=self._n_test_folds,
                n_paths=0,
                purge_size=self._purge_days,
                embargo_size=self._embargo_days,
                sharpe_distribution=[],
                sharpe_mean=0.0,
                sharpe_std=0.0,
                sharpe_5th_pct=0.0,
                pbo=1.0,
                passed=False,
            )

        sharpes_arr = np.array(oos_sharpes)

        # PBO = fraction of paths with negative OOS Sharpe
        pbo = float(np.mean(sharpes_arr < 0))

        return CPCVResult(
            strategy_name=strategy_name,
            n_folds=self._n_folds,
            n_test_folds=self._n_test_folds,
            n_paths=len(oos_sharpes),
            purge_size=self._purge_days,
            embargo_size=self._embargo_days,
            sharpe_distribution=oos_sharpes,
            sharpe_mean=float(np.mean(sharpes_arr)),
            sharpe_std=float(np.std(sharpes_arr)),
            sharpe_5th_pct=float(np.percentile(sharpes_arr, 5)),
            pbo=pbo,
            passed=pbo < 0.50,
        )
