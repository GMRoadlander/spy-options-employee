"""Backtesting engine for options strategies.

Bridges YAML strategy definitions to historical trade execution. Uses
the data_transform layer to prepare optopsy-format data, then applies
entry filters, selects strikes by delta, and simulates exit rules
(profit target, stop loss, DTE exit) day-by-day.

The engine does NOT use optopsy functions directly -- it implements
its own matching/execution logic so we can support arbitrary exit rules
and strategy types without being limited by optopsy's API surface.
Optopsy remains available for future cross-validation of results.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.data import OptionsChain
from src.strategy.schema import (
    EntryRule,
    ExitRule,
    LegAction,
    LegDefinition,
    LegSide,
    StrategyTemplate,
    StrategyType,
)
from src.backtest.data_transform import chains_to_optopsy_df, filter_pm_settled

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Result of running a backtest for a single strategy."""

    strategy_name: str
    strategy_id: str
    start_date: date
    end_date: date
    num_trades: int
    total_return: float
    daily_returns: pd.Series
    trade_log: pd.DataFrame
    raw_data: pd.DataFrame


class BacktestEngine:
    """Runs backtests by simulating strategy execution on historical data."""

    def __init__(self, chains: list[OptionsChain] | None = None) -> None:
        self._chains = chains or []

    def set_chains(self, chains: list[OptionsChain]) -> None:
        self._chains = chains

    def run(
        self,
        strategy: StrategyTemplate,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> BacktestResult:
        """Run a full backtest for a strategy template.

        1. Transform chains to optopsy format (PM-settled only)
        2. Apply entry filters to select trade dates
        3. For each entry date, select strikes by delta target
        4. Simulate exit rules day-by-day
        5. Build trade log and daily return series
        """
        df = chains_to_optopsy_df(self._chains)
        df = filter_pm_settled(df)

        if df.empty:
            return self._empty_result(strategy, start_date, end_date)

        # Apply date range
        if start_date:
            df = df[df["quote_date"] >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df["quote_date"] <= pd.Timestamp(end_date)]

        if df.empty:
            return self._empty_result(strategy, start_date, end_date)

        actual_start = df["quote_date"].min().date()
        actual_end = df["quote_date"].max().date()

        # Get unique quote dates for entry evaluation
        quote_dates = sorted(df["quote_date"].unique())

        # Apply entry filters
        entry_dates = self._apply_entry_filters(df, quote_dates, strategy.entry)

        if not entry_dates:
            return self._empty_result(strategy, actual_start, actual_end)

        # Execute trades
        trades = self._execute_trades(df, entry_dates, strategy)

        if trades.empty:
            return self._empty_result(strategy, actual_start, actual_end)

        # Apply exit rules
        trades = self._apply_exit_rules(df, trades, strategy.exit)

        # Build daily returns
        daily_returns = self._build_daily_returns(trades, actual_start, actual_end)

        total_ret = trades["pnl"].sum() if not trades.empty else 0.0

        return BacktestResult(
            strategy_name=strategy.name,
            strategy_id=strategy.metadata.get("id", ""),
            start_date=actual_start,
            end_date=actual_end,
            num_trades=len(trades),
            total_return=total_ret,
            daily_returns=daily_returns,
            trade_log=trades,
            raw_data=df,
        )

    def _apply_entry_filters(
        self,
        df: pd.DataFrame,
        quote_dates: list,
        entry: EntryRule,
    ) -> list:
        """Filter quote dates where entry conditions are met."""
        filtered = []

        for qd in quote_dates:
            qd_ts = pd.Timestamp(qd)
            day_data = df[df["quote_date"] == qd_ts]

            if day_data.empty:
                continue

            # Day of week filter (schedule is separate, but entry has time_of_day)
            # For now, all days pass unless explicitly filtered

            # IV rank filter would require external IV rank data.
            # For backtesting, we include all dates and rely on strategy
            # schedule config for day filtering.

            filtered.append(qd)

        return filtered

    def _execute_trades(
        self,
        df: pd.DataFrame,
        entry_dates: list,
        strategy: StrategyTemplate,
    ) -> pd.DataFrame:
        """Open positions on entry dates by selecting strikes via delta.

        Returns a DataFrame with one row per trade:
        entry_date, expiration, legs (list of dicts), entry_credit/debit, exit_date, pnl
        """
        structure = strategy.structure
        legs = structure.legs
        dte_target = structure.dte_target
        dte_min = structure.dte_min
        dte_max = structure.dte_max

        trade_rows = []

        for qd in entry_dates:
            qd_ts = pd.Timestamp(qd)
            day_data = df[df["quote_date"] == qd_ts]

            if day_data.empty:
                continue

            qd_date = qd_ts.date() if hasattr(qd_ts, "date") else qd_ts

            # Find best expiration matching DTE target
            exps = day_data["expiration"].unique()
            best_exp = None
            best_dte_diff = float("inf")

            for exp in exps:
                exp_date = exp.date() if hasattr(exp, "date") else exp
                dte = (exp_date - qd_date).days
                if dte_min <= dte <= dte_max:
                    diff = abs(dte - dte_target)
                    if diff < best_dte_diff:
                        best_dte_diff = diff
                        best_exp = exp

            if best_exp is None:
                continue

            exp_data = day_data[day_data["expiration"] == best_exp]

            # Select strikes for each leg
            leg_fills = []
            valid = True

            for leg_def in legs:
                fill = self._select_strike(exp_data, leg_def)
                if fill is None:
                    valid = False
                    break
                leg_fills.append(fill)

            if not valid:
                continue

            # Calculate entry credit/debit
            entry_value = 0.0
            for leg_def, fill in zip(legs, leg_fills):
                mid = (fill["bid"] + fill["ask"]) / 2
                if leg_def.action == LegAction.SELL:
                    entry_value += mid  # credit
                else:
                    entry_value -= mid  # debit

            exp_date = best_exp.date() if hasattr(best_exp, "date") else best_exp

            trade_rows.append({
                "entry_date": qd_date,
                "expiration": exp_date,
                "dte_at_entry": (exp_date - qd_date).days,
                "legs": leg_fills,
                "leg_defs": [{"side": l.side.value, "action": l.action.value} for l in legs],
                "entry_credit": entry_value,
                "exit_date": exp_date,  # default: hold to expiration
                "exit_value": 0.0,
                "pnl": entry_value,  # default: full credit kept (updated by exit rules)
            })

        if not trade_rows:
            return pd.DataFrame()

        return pd.DataFrame(trade_rows)

    def _select_strike(
        self,
        exp_data: pd.DataFrame,
        leg: LegDefinition,
    ) -> dict | None:
        """Select the best strike for a leg based on delta target."""
        side = "c" if leg.side == LegSide.CALL else "p"
        options = exp_data[exp_data["option_type"] == side].copy()

        if options.empty:
            return None

        target_delta = leg.delta_value

        # For puts, delta is negative in the data; target should be absolute
        if side == "p" and target_delta > 0:
            target_delta = -target_delta

        options = options.copy()
        options["delta_diff"] = (options["delta"] - target_delta).abs()
        best = options.loc[options["delta_diff"].idxmin()]

        return {
            "strike": best["strike"],
            "side": side,
            "delta": best["delta"],
            "bid": best["bid"],
            "ask": best["ask"],
        }

    def _apply_exit_rules(
        self,
        df: pd.DataFrame,
        trades: pd.DataFrame,
        exit_rule: ExitRule,
    ) -> pd.DataFrame:
        """Apply profit target, stop loss, DTE exit rules.

        For each trade, scan daily marks from entry to expiration.
        Close when the first exit condition triggers.
        """
        if trades.empty:
            return trades

        results = []

        for _, trade in trades.iterrows():
            entry_date = trade["entry_date"]
            expiration = trade["expiration"]
            entry_credit = trade["entry_credit"]
            legs_info = trade["legs"]

            # Max profit for a credit trade is the credit received
            max_profit = abs(entry_credit) if entry_credit > 0 else 0
            # For a debit trade, max loss is the debit paid
            max_loss = abs(entry_credit) if entry_credit < 0 else 0

            exit_date = expiration
            exit_value = 0.0

            # Scan each day from entry+1 to expiration
            current = entry_date + timedelta(days=1)
            while current <= expiration:
                current_ts = pd.Timestamp(current)
                day_data = df[df["quote_date"] == current_ts]

                if day_data.empty:
                    current += timedelta(days=1)
                    continue

                # Calculate current position value
                current_value = 0.0
                for i, leg_info in enumerate(legs_info):
                    leg_options = day_data[
                        (day_data["option_type"] == leg_info["side"]) &
                        (day_data["strike"] == leg_info["strike"])
                    ]
                    if not leg_options.empty:
                        mid = (leg_options.iloc[0]["bid"] + leg_options.iloc[0]["ask"]) / 2
                        leg_defs = trade["leg_defs"]
                        if leg_defs[i]["action"] == "sell":
                            current_value -= mid  # cost to close short
                        else:
                            current_value += mid  # value of long

                # P&L = entry credit + current close cost
                unrealized_pnl = entry_credit + current_value

                dte_remaining = (expiration - current).days

                # Profit target check
                if max_profit > 0 and unrealized_pnl >= max_profit * exit_rule.profit_target_pct:
                    exit_date = current
                    exit_value = current_value
                    break

                # Stop loss check
                if max_profit > 0 and unrealized_pnl <= -max_profit * exit_rule.stop_loss_pct:
                    exit_date = current
                    exit_value = current_value
                    break

                # DTE exit check
                if dte_remaining <= exit_rule.dte_close:
                    exit_date = current
                    exit_value = current_value
                    break

                current += timedelta(days=1)

            pnl = entry_credit + exit_value

            row = trade.to_dict()
            row["exit_date"] = exit_date
            row["exit_value"] = exit_value
            row["pnl"] = pnl
            results.append(row)

        return pd.DataFrame(results)

    def _build_daily_returns(
        self,
        trades: pd.DataFrame,
        start: date,
        end: date,
    ) -> pd.Series:
        """Build a daily return series from trade P&L.

        Distributes each trade's P&L evenly across its holding period.
        """
        date_range = pd.date_range(start=start, end=end, freq="B")  # business days
        daily = pd.Series(0.0, index=date_range)

        if trades.empty:
            return daily

        for _, trade in trades.iterrows():
            entry = pd.Timestamp(trade["entry_date"])
            exit_dt = pd.Timestamp(trade["exit_date"])
            pnl = trade["pnl"]

            # Distribute P&L to the exit date
            if exit_dt in daily.index:
                daily[exit_dt] += pnl
            elif len(daily) > 0:
                # Find nearest date
                nearest_idx = daily.index.get_indexer([exit_dt], method="nearest")[0]
                if 0 <= nearest_idx < len(daily):
                    daily.iloc[nearest_idx] += pnl

        return daily

    def _empty_result(
        self,
        strategy: StrategyTemplate,
        start: date | None,
        end: date | None,
    ) -> BacktestResult:
        return BacktestResult(
            strategy_name=strategy.name,
            strategy_id=strategy.metadata.get("id", ""),
            start_date=start or date.today(),
            end_date=end or date.today(),
            num_trades=0,
            total_return=0.0,
            daily_returns=pd.Series(dtype=float),
            trade_log=pd.DataFrame(),
            raw_data=pd.DataFrame(),
        )
