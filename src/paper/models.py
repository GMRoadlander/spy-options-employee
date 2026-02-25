"""Data models for the paper trading engine.

Defines all dataclasses used across the paper trading subsystem:
orders, fills, positions, PnL, portfolio state, and configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class PaperTradingConfig:
    """Configuration for paper trading engine.

    Attributes:
        starting_capital: Initial simulated portfolio value (USD).
        spx_multiplier: SPX options contract multiplier ($100/point).
        fee_per_contract: Fee per contract per leg (Schwab standard $0.65).
        slippage_pct: Slippage as fraction of bid-ask spread (0.10 = 10%).
        max_order_age_ticks: Ticks before unfilled limit orders auto-cancel.
        snapshot_time_et: Time (ET) for daily portfolio snapshot.
    """

    starting_capital: float = 100_000.0
    spx_multiplier: float = 100.0
    fee_per_contract: float = 0.65
    slippage_pct: float = 0.10
    max_order_age_ticks: int = 5
    snapshot_time_et: str = "16:00"


@dataclass
class LegSpec:
    """Specification for a single leg in a paper order.

    Describes what to buy/sell: option type, strike, expiry, action,
    and quantity. Used by the FillSimulator to look up live quotes.

    Attributes:
        leg_name: Identifier matching strategy leg definition name.
        option_type: 'call' or 'put'.
        strike: Strike price.
        expiry: Expiration date.
        action: 'buy' or 'sell'.
        quantity: Number of contracts for this leg.
    """

    leg_name: str
    option_type: str
    strike: float
    expiry: date
    action: str
    quantity: int = 1


@dataclass
class SimulatedFill:
    """Result of a fill simulation for one leg.

    Captures the fill price and the market conditions at fill time,
    enabling post-trade slippage analysis.

    Attributes:
        leg_name: Identifier matching the LegSpec.
        fill_price: Simulated execution price per contract.
        bid: Market bid at fill time.
        ask: Market ask at fill time.
        mid: Mid-price at fill time.
        slippage: Absolute slippage from mid-price.
        iv: Implied volatility at fill time.
        delta: Option delta at fill time.
    """

    leg_name: str
    fill_price: float
    bid: float
    ask: float
    mid: float
    slippage: float
    iv: float = 0.0
    delta: float = 0.0


@dataclass
class TickResult:
    """Summary of one engine tick cycle.

    Returned by PaperTradingEngine.tick() to report what happened
    during a single scheduler cycle.

    Attributes:
        timestamp: When this tick was processed.
        orders_submitted: Number of new orders submitted.
        orders_filled: Number of orders filled this tick.
        orders_cancelled: Number of orders cancelled (stale/limit miss).
        positions_opened: Number of new positions opened.
        positions_closed: Number of positions closed.
        exit_signals: Descriptions of exit signals triggered.
        total_unrealized_pnl: Sum of unrealized PnL across all open positions.
        errors: Any errors encountered during the tick.
    """

    timestamp: datetime
    orders_submitted: int = 0
    orders_filled: int = 0
    orders_cancelled: int = 0
    positions_opened: int = 0
    positions_closed: int = 0
    exit_signals: list[str] = field(default_factory=list)
    total_unrealized_pnl: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass
class PortfolioSummary:
    """Current portfolio state for Discord display.

    Aggregates positions, PnL, and risk metrics across all
    paper-traded strategies.

    Attributes:
        starting_capital: Initial capital when paper trading started.
        total_equity: Current portfolio value (capital + realized + unrealized).
        realized_pnl: Cumulative realized PnL from closed trades.
        unrealized_pnl: Unrealized PnL from open positions.
        open_positions: Count of currently open positions.
        total_trades: Count of all completed trades.
        win_rate: Fraction of winning trades (0.0-1.0).
        sharpe_ratio: Annualized Sharpe ratio from daily returns.
        max_drawdown: Maximum drawdown from peak equity.
        daily_pnl: Today's PnL change.
        strategies_active: Names of strategies currently in PAPER state.
    """

    starting_capital: float = 0.0
    total_equity: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    open_positions: int = 0
    total_trades: int = 0
    win_rate: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    daily_pnl: float = 0.0
    strategies_active: list[str] = field(default_factory=list)

    # Risk fields (populated when RiskManager is attached)
    portfolio_delta: float = 0.0
    portfolio_gamma: float = 0.0
    portfolio_theta: float = 0.0
    portfolio_vega: float = 0.0
    var_95: float = 0.0
    circuit_breakers_active: list[str] = field(default_factory=list)
    risk_alerts_count: int = 0


@dataclass
class PaperResults:
    """Paper trading results for a single strategy.

    Used for promotion evaluation: compares paper performance against
    backtest predictions to validate strategy viability.

    Attributes:
        strategy_id: Database ID of the strategy.
        strategy_name: Human-readable strategy name.
        trades: List of completed trade records (dicts).
        metrics: StrategyMetrics computed from paper trades.
        equity_curve: Daily equity values for charting.
        days_in_paper: Calendar days since strategy entered PAPER state.
        recommendation: 'PROMOTE', 'CONTINUE', or 'DEMOTE'.
    """

    strategy_id: int = 0
    strategy_name: str = ""
    trades: list[dict] = field(default_factory=list)
    metrics: object = None  # StrategyMetrics (avoid circular import)
    equity_curve: list[float] = field(default_factory=list)
    days_in_paper: int = 0
    recommendation: str = "CONTINUE"


@dataclass
class TradePnL:
    """PnL breakdown for a completed trade.

    All values in USD. Entry and exit credits/debits follow the convention:
    positive = credit received, negative = debit paid.

    Attributes:
        entry_credit_debit: Net credit/debit at entry (positive = credit).
        exit_credit_debit: Net credit/debit at exit (positive = credit).
        raw_pnl: Per-unit raw PnL (entry + exit, before multiplier).
        total_pnl: raw_pnl * quantity * multiplier.
        fees: Total fees for all legs (open + close).
        slippage_cost: Total slippage impact across all legs.
        net_pnl: total_pnl - fees.
    """

    entry_credit_debit: float = 0.0
    exit_credit_debit: float = 0.0
    raw_pnl: float = 0.0
    total_pnl: float = 0.0
    fees: float = 0.0
    slippage_cost: float = 0.0
    net_pnl: float = 0.0


@dataclass
class ExitSignal:
    """Signal to close a position.

    Generated by the ExitMonitor when a position meets exit criteria.

    Attributes:
        position_id: Database ID of the position to close.
        reason: Why the exit was triggered (e.g., 'profit_target', 'stop_loss').
        urgency: 'immediate' for expirations, 'normal' for rule-based exits.
    """

    position_id: int = 0
    reason: str = ""
    urgency: str = "normal"
