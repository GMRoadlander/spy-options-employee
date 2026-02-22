"""Walk-Forward Analysis (WFA) module.

Splits a date range into rolling in-sample / out-of-sample windows,
then evaluates whether a strategy's OOS performance degrades acceptably
relative to its IS performance.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
from typing import List, Tuple


def _add_months(d: date, months: int) -> date:
    """Add *months* to a date, clamping day to month end if needed."""
    month = d.month + months
    year = d.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    max_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, max_day))


@dataclass
class WFAResult:
    """Container for walk-forward analysis results."""

    strategy_name: str
    num_windows: int
    is_periods: List[Tuple[date, date]] = field(default_factory=list)
    oos_periods: List[Tuple[date, date]] = field(default_factory=list)
    is_sharpes: List[float] = field(default_factory=list)
    oos_sharpes: List[float] = field(default_factory=list)
    degradation: float = 0.0
    oos_sharpe_mean: float = 0.0
    oos_sharpe_std: float = 0.0
    passed: bool = False


class WalkForwardAnalyzer:
    """Rolling walk-forward window generator and evaluator.

    Parameters
    ----------
    is_months : int
        Length of the in-sample window in months (default 12).
    oos_months : int
        Length of the out-of-sample window in months (default 3).
    step_months : int
        How many months to advance between consecutive windows (default 3).
    """

    def __init__(
        self,
        is_months: int = 12,
        oos_months: int = 3,
        step_months: int = 3,
    ) -> None:
        if is_months <= 0 or oos_months <= 0 or step_months <= 0:
            raise ValueError("is_months, oos_months, and step_months must be > 0")
        self.is_months = is_months
        self.oos_months = oos_months
        self.step_months = step_months

    # ------------------------------------------------------------------
    # Window generation
    # ------------------------------------------------------------------

    def generate_windows(
        self, start_date: date, end_date: date
    ) -> List[Tuple[date, date, date, date]]:
        """Generate rolling (IS_start, IS_end, OOS_start, OOS_end) tuples.

        The IS window covers ``[is_start, is_end)`` and the OOS window
        covers ``[oos_start, oos_end)``.  Windows are advanced by
        ``step_months`` each iteration until the OOS end would exceed
        ``end_date``.
        """
        windows: List[Tuple[date, date, date, date]] = []
        cursor = start_date

        while True:
            is_start = cursor
            is_end = _add_months(cursor, self.is_months)
            oos_start = is_end
            oos_end = _add_months(is_end, self.oos_months)

            if oos_end > end_date:
                break

            windows.append((is_start, is_end, oos_start, oos_end))
            cursor = _add_months(cursor, self.step_months)

        return windows

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        is_sharpes: List[float],
        oos_sharpes: List[float],
        strategy_name: str = "unnamed",
    ) -> WFAResult:
        """Compute degradation ratio and pass/fail for a set of windows.

        Pass criteria
        -------------
        * Mean OOS Sharpe > 0
        * Degradation ratio (mean_OOS / mean_IS) >= 0.5  -- i.e. the
          *drop* is less than 50 %, meaning the ratio is **at least** 0.5.

        If there are no sharpe values, the result is automatically a fail.
        """
        n = len(oos_sharpes)

        if n == 0 or len(is_sharpes) == 0:
            return WFAResult(
                strategy_name=strategy_name,
                num_windows=0,
                passed=False,
            )

        mean_is = sum(is_sharpes) / len(is_sharpes)
        mean_oos = sum(oos_sharpes) / n

        # Standard deviation of OOS sharpes (sample std)
        if n > 1:
            variance = sum((s - mean_oos) ** 2 for s in oos_sharpes) / (n - 1)
            std_oos = variance ** 0.5
        else:
            std_oos = 0.0

        # Degradation: ratio of OOS to IS.  Guard against zero IS mean.
        if mean_is == 0:
            degradation = 0.0 if mean_oos == 0 else float("inf")
        else:
            degradation = mean_oos / mean_is

        # Pass: OOS > 0 AND degradation >= 0.5 (less than 50 % drop)
        passed = mean_oos > 0 and degradation >= 0.5

        return WFAResult(
            strategy_name=strategy_name,
            num_windows=n,
            is_sharpes=list(is_sharpes),
            oos_sharpes=list(oos_sharpes),
            is_periods=[],
            oos_periods=[],
            degradation=degradation,
            oos_sharpe_mean=mean_oos,
            oos_sharpe_std=std_oos,
            passed=passed,
        )
