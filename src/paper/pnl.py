"""PnL calculation and daily portfolio snapshots for paper trading.

PnLCalculator computes trade-level PnL, takes daily equity snapshots,
generates equity curves, and produces StrategyMetrics by reusing the
existing calculate_metrics() from the backtest engine.

SPX contract multiplier: $100/point.
Simulated fees: $0.65/contract/leg (Schwab standard).
Example: 4-leg iron condor, 1 contract = $0.65 * 4 * 2 (open+close) = $5.20.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd

import aiosqlite

from src.paper.models import PaperTradingConfig, SimulatedFill, TradePnL

logger = logging.getLogger(__name__)


class PnLCalculator:
    """Computes realized PnL, daily snapshots, and portfolio metrics.

    Works with the paper_trades and paper_portfolio tables. The
    get_paper_metrics() method bridges paper trade data to the existing
    StrategyMetrics via calculate_metrics() from src/backtest/metrics.py.
    """

    def __init__(
        self,
        db: aiosqlite.Connection,
        config: PaperTradingConfig,
    ) -> None:
        self._db = db
        self._config = config

    def calculate_trade_pnl(
        self,
        entry_fills: list[SimulatedFill],
        exit_fills: list[SimulatedFill],
        quantity: int,
        entry_legs_actions: dict[str, str] | None = None,
        exit_legs_actions: dict[str, str] | None = None,
    ) -> TradePnL:
        """Calculate final PnL for a closed trade.

        Uses the sign convention: sell = credit (+), buy = debit (-).

        Args:
            entry_fills: Fill results for the opening order.
            exit_fills: Fill results for the closing order.
            quantity: Number of contracts.
            entry_legs_actions: Dict of leg_name -> action for entry legs.
            exit_legs_actions: Dict of leg_name -> action for exit legs.

        Returns:
            TradePnL with full breakdown including fees and slippage.
        """
        multiplier = self._config.spx_multiplier
        fee_per = self._config.fee_per_contract

        # Calculate entry credit/debit
        entry_cd = 0.0
        for fill in entry_fills:
            action = "buy"
            if entry_legs_actions:
                action = entry_legs_actions.get(fill.leg_name, "buy")
            if action == "sell":
                entry_cd += fill.fill_price
            else:
                entry_cd -= fill.fill_price

        # Calculate exit credit/debit
        exit_cd = 0.0
        for fill in exit_fills:
            action = "buy"
            if exit_legs_actions:
                action = exit_legs_actions.get(fill.leg_name, "buy")
            if action == "sell":
                exit_cd += fill.fill_price
            else:
                exit_cd -= fill.fill_price

        # Raw PnL per unit = entry + exit
        raw_pnl = entry_cd + exit_cd

        # Total PnL with multiplier
        total_pnl = raw_pnl * quantity * multiplier

        # Fees: per contract per leg, for both open and close
        num_entry_legs = len(entry_fills)
        num_exit_legs = len(exit_fills)
        fees = fee_per * (num_entry_legs + num_exit_legs) * quantity

        # Slippage cost
        entry_slippage = sum(f.slippage for f in entry_fills)
        exit_slippage = sum(f.slippage for f in exit_fills)
        slippage_cost = (entry_slippage + exit_slippage) * quantity * multiplier

        net_pnl = total_pnl - fees

        return TradePnL(
            entry_credit_debit=round(entry_cd, 4),
            exit_credit_debit=round(exit_cd, 4),
            raw_pnl=round(raw_pnl, 4),
            total_pnl=round(total_pnl, 2),
            fees=round(fees, 2),
            slippage_cost=round(slippage_cost, 2),
            net_pnl=round(net_pnl, 2),
        )

    async def take_daily_snapshot(self) -> None:
        """Record daily portfolio snapshot to paper_portfolio table.

        Aggregates realized PnL from closed trades, unrealized PnL from
        open positions, and computes total equity and daily change.
        """
        today = date.today().isoformat()
        capital = self._config.starting_capital

        # Total realized PnL from all closed trades
        cursor = await self._db.execute(
            "SELECT COALESCE(SUM(total_pnl - fees), 0.0) FROM paper_trades"
        )
        row = await cursor.fetchone()
        realized_pnl = row[0] if row else 0.0

        # Total unrealized PnL from open positions
        cursor = await self._db.execute(
            "SELECT COALESCE(SUM(unrealized_pnl), 0.0) FROM paper_positions WHERE status = 'open'"
        )
        row = await cursor.fetchone()
        unrealized_pnl = row[0] if row else 0.0

        # Total equity
        total_equity = capital + realized_pnl + unrealized_pnl

        # Open position count
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM paper_positions WHERE status = 'open'"
        )
        open_positions = (await cursor.fetchone())[0]

        # Total completed trades
        cursor = await self._db.execute("SELECT COUNT(*) FROM paper_trades")
        total_trades = (await cursor.fetchone())[0]

        # Previous day's equity for daily PnL calculation
        cursor = await self._db.execute(
            """
            SELECT total_equity FROM paper_portfolio
            WHERE snapshot_date < ?
            ORDER BY snapshot_date DESC LIMIT 1
            """,
            (today,),
        )
        prev_row = await cursor.fetchone()
        prev_equity = prev_row[0] if prev_row else capital
        daily_pnl = total_equity - prev_equity

        # Max drawdown: peak equity vs current
        cursor = await self._db.execute(
            "SELECT COALESCE(MAX(total_equity), ?) FROM paper_portfolio",
            (capital,),
        )
        peak_equity = (await cursor.fetchone())[0]
        peak_equity = max(peak_equity, capital)
        if peak_equity > 0:
            max_drawdown = (total_equity - peak_equity) / peak_equity
        else:
            max_drawdown = 0.0

        # Upsert today's snapshot (replace if already exists for today)
        await self._db.execute(
            "DELETE FROM paper_portfolio WHERE snapshot_date = ?",
            (today,),
        )
        await self._db.execute(
            """
            INSERT INTO paper_portfolio
                (snapshot_date, starting_capital, realized_pnl, unrealized_pnl,
                 total_equity, open_positions, total_trades, daily_pnl, max_drawdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                today, capital, round(realized_pnl, 2), round(unrealized_pnl, 2),
                round(total_equity, 2), open_positions, total_trades,
                round(daily_pnl, 2), round(max_drawdown, 6),
            ),
        )
        await self._db.commit()

        logger.info(
            "Daily snapshot: equity=%.2f realized=%.2f unrealized=%.2f "
            "daily=%.2f positions=%d trades=%d",
            total_equity, realized_pnl, unrealized_pnl,
            daily_pnl, open_positions, total_trades,
        )

    async def get_equity_curve(
        self,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get equity curve data for charting.

        Args:
            days: Number of days of history to return.

        Returns:
            List of dicts with date, equity, daily_pnl, drawdown.
        """
        cursor = await self._db.execute(
            """
            SELECT snapshot_date, total_equity, daily_pnl, max_drawdown,
                   realized_pnl, unrealized_pnl, open_positions, total_trades
            FROM paper_portfolio
            ORDER BY snapshot_date DESC
            LIMIT ?
            """,
            (days,),
        )
        rows = await cursor.fetchall()
        cols = ["date", "total_equity", "daily_pnl", "max_drawdown",
                "realized_pnl", "unrealized_pnl", "open_positions", "total_trades"]

        results = [dict(zip(cols, row)) for row in reversed(rows)]
        return results

    async def get_paper_metrics(
        self,
        strategy_id: int | None = None,
    ) -> Any:
        """Calculate StrategyMetrics from paper trades.

        Reuses calculate_metrics() from src/backtest/metrics.py by
        constructing a compatible BacktestResult from paper trade data.

        Args:
            strategy_id: Optional strategy filter. If None, computes
                         metrics across all strategies.

        Returns:
            StrategyMetrics object with all fields populated.
        """
        from src.backtest.engine import BacktestResult
        from src.backtest.metrics import calculate_metrics

        # Load paper trades
        if strategy_id is not None:
            cursor = await self._db.execute(
                """
                SELECT entry_date, exit_date, entry_price, exit_price,
                       realized_pnl, total_pnl, fees, holding_days
                FROM paper_trades
                WHERE strategy_id = ?
                ORDER BY exit_date
                """,
                (strategy_id,),
            )
        else:
            cursor = await self._db.execute(
                """
                SELECT entry_date, exit_date, entry_price, exit_price,
                       realized_pnl, total_pnl, fees, holding_days
                FROM paper_trades
                ORDER BY exit_date
                """
            )

        rows = await cursor.fetchall()
        cols = ["entry_date", "exit_date", "entry_price", "exit_price",
                "realized_pnl", "total_pnl", "fees", "holding_days"]

        if not rows:
            # Return empty metrics
            result = BacktestResult(
                strategy_name="paper",
                strategy_id=str(strategy_id or "all"),
                start_date=date.today(),
                end_date=date.today(),
                num_trades=0,
                total_return=0.0,
                daily_returns=pd.Series(dtype=float),
                trade_log=pd.DataFrame(),
                raw_data=pd.DataFrame(),
            )
            return calculate_metrics(result)

        # Build trade_log DataFrame compatible with calculate_metrics
        trade_data = [dict(zip(cols, row)) for row in rows]
        trade_df = pd.DataFrame(trade_data)

        # calculate_metrics expects a "pnl" column
        trade_df["pnl"] = trade_df["total_pnl"] - trade_df["fees"]

        # Build daily returns from equity curve
        daily_returns = await self._build_daily_returns(strategy_id)

        total_return = trade_df["pnl"].sum()
        start_date_str = trade_data[0]["entry_date"]
        end_date_str = trade_data[-1]["exit_date"]

        result = BacktestResult(
            strategy_name="paper",
            strategy_id=str(strategy_id or "all"),
            start_date=date.fromisoformat(start_date_str),
            end_date=date.fromisoformat(end_date_str),
            num_trades=len(trade_data),
            total_return=total_return,
            daily_returns=daily_returns,
            trade_log=trade_df,
            raw_data=pd.DataFrame(),
        )

        return calculate_metrics(result)

    async def get_cumulative_realized_pnl(
        self,
        strategy_id: int | None = None,
    ) -> float:
        """Get cumulative realized PnL (net of fees).

        Args:
            strategy_id: Optional strategy filter.

        Returns:
            Total net PnL in USD.
        """
        if strategy_id is not None:
            cursor = await self._db.execute(
                "SELECT COALESCE(SUM(total_pnl - fees), 0.0) FROM paper_trades WHERE strategy_id = ?",
                (strategy_id,),
            )
        else:
            cursor = await self._db.execute(
                "SELECT COALESCE(SUM(total_pnl - fees), 0.0) FROM paper_trades"
            )
        row = await cursor.fetchone()
        return row[0] if row else 0.0

    async def get_trade_count(
        self,
        strategy_id: int | None = None,
    ) -> int:
        """Get the number of completed trades.

        Args:
            strategy_id: Optional strategy filter.

        Returns:
            Number of trades.
        """
        if strategy_id is not None:
            cursor = await self._db.execute(
                "SELECT COUNT(*) FROM paper_trades WHERE strategy_id = ?",
                (strategy_id,),
            )
        else:
            cursor = await self._db.execute("SELECT COUNT(*) FROM paper_trades")
        return (await cursor.fetchone())[0]

    async def _build_daily_returns(
        self,
        strategy_id: int | None = None,
    ) -> pd.Series:
        """Build daily returns series from portfolio snapshots.

        Falls back to computing from trade data if no snapshots exist.
        """
        cursor = await self._db.execute(
            """
            SELECT snapshot_date, daily_pnl, starting_capital
            FROM paper_portfolio
            ORDER BY snapshot_date
            """
        )
        rows = await cursor.fetchall()

        if not rows:
            # Fall back to trade-level daily returns
            return await self._trade_daily_returns(strategy_id)

        capital = rows[0][2] if rows else self._config.starting_capital
        dates = []
        returns = []
        for row in rows:
            dates.append(pd.Timestamp(row[0]))
            returns.append(row[1] / capital if capital > 0 else 0.0)

        if dates:
            return pd.Series(returns, index=pd.DatetimeIndex(dates))
        return pd.Series(dtype=float)

    async def _trade_daily_returns(
        self,
        strategy_id: int | None = None,
    ) -> pd.Series:
        """Build daily returns from individual trade PnLs.

        Groups trades by exit date and computes daily return relative
        to starting capital.
        """
        if strategy_id is not None:
            cursor = await self._db.execute(
                """
                SELECT exit_date, SUM(total_pnl - fees) as daily_pnl
                FROM paper_trades
                WHERE strategy_id = ?
                GROUP BY exit_date
                ORDER BY exit_date
                """,
                (strategy_id,),
            )
        else:
            cursor = await self._db.execute(
                """
                SELECT exit_date, SUM(total_pnl - fees) as daily_pnl
                FROM paper_trades
                GROUP BY exit_date
                ORDER BY exit_date
                """
            )

        rows = await cursor.fetchall()
        if not rows:
            return pd.Series(dtype=float)

        capital = self._config.starting_capital
        dates = [pd.Timestamp(row[0]) for row in rows]
        returns = [row[1] / capital if capital > 0 else 0.0 for row in rows]

        return pd.Series(returns, index=pd.DatetimeIndex(dates))
