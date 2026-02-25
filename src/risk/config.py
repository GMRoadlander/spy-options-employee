"""Risk configuration with all limit parameters.

All limits are for a PAPER portfolio. Values default to conservative
settings for a $100,000 paper portfolio. Every numeric limit can be
overridden via environment variable.

Regime multipliers scale limits based on HMM regime state:
- State 0 (risk-on / GREEN): 1.0x (full limits)
- State 1 (risk-off / YELLOW): reduced limits
- State 2 (crisis / RED): minimal limits, close-only mode
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class RiskConfig:
    """All risk limit parameters in one place.

    Attributes are grouped by scope: position -> strategy -> portfolio.
    Circuit breaker thresholds are separate.
    """

    # --- Position-level limits ---
    max_position_premium_pct: float = 0.02       # 2% of NAV
    max_loss_multiplier: float = 1.5             # 1.5x entry premium
    max_position_delta: float = 200.0            # Abs delta per position
    max_position_notional_pct: float = 0.10      # 10% of NAV
    min_dte: int = 7                             # Min DTE at entry
    max_dte: int = 60                            # Max DTE at entry

    # --- Strategy-level limits ---
    max_strategy_allocation_pct: float = 0.20    # 20% of NAV per strategy
    max_concurrent_per_strategy: int = 3         # Max open positions per strategy
    max_strategy_delta: float = 300.0            # Abs delta per strategy
    max_strategy_vega: float = 5000.0            # Dollar vega per strategy
    max_strategy_daily_loss_pct: float = 0.03    # 3% of NAV daily loss per strategy
    max_strategy_weekly_loss_pct: float = 0.05   # 5% of NAV weekly loss per strategy

    # --- Portfolio-level limits ---
    max_portfolio_delta: float = 500.0           # Abs delta across all positions
    max_portfolio_gamma: float = 100.0           # Abs gamma across all positions
    max_portfolio_vega: float = 15000.0          # Dollar vega across all positions
    max_daily_theta: float = -2000.0             # Max daily theta burn (negative = decay cost)
    max_daily_loss_pct: float = 0.05             # 5% of NAV single-day loss
    max_drawdown_pct: float = 0.10               # 10% of NAV from peak
    max_expiry_concentration_pct: float = 0.40   # 40% of portfolio delta in one expiry
    max_strike_concentration_pct: float = 0.30   # 30% of premium in one 25-pt strike range
    max_correlated_strategies: int = 3           # Max strategies with correlation > 0.60
    min_cash_reserve_pct: float = 0.30           # 30% of NAV kept as cash reserve

    # --- VaR limits ---
    max_var_95_pct: float = 0.03                 # 3% of NAV (warning)
    max_var_99_pct: float = 0.05                 # 5% of NAV (block new positions)

    # --- Circuit breakers ---
    vix_halt_threshold: float = 35.0             # Halt new positions when VIX > 35
    vix_resume_threshold: float = 30.0           # Resume when VIX < 30 for 2 days
    spx_crash_threshold: float = -0.03           # -3% intraday SPX move
    anomaly_halt_threshold: float = 0.8          # Halt when anomaly score > 0.8
    anomaly_resume_threshold: float = 0.5        # Resume when anomaly < 0.5
    max_consecutive_order_failures: int = 3      # Halt after 3 consecutive fill failures

    # --- Correlation thresholds ---
    high_correlation_threshold: float = 0.80     # Same bet -- only one at a time
    moderate_correlation_threshold: float = 0.60 # Correlated -- combined allocation limit

    # --- Risk-free rate (for Greeks / VaR) ---
    risk_free_rate: float = 0.05                 # 5% annual

    @classmethod
    def from_env(cls) -> "RiskConfig":
        """Create RiskConfig from environment variables.

        Each field can be overridden by RISK_<FIELD_NAME_UPPER> env var.
        Example: RISK_MAX_PORTFOLIO_DELTA=300
        """
        kwargs: dict = {}
        for field_name in cls.__dataclass_fields__:
            env_key = f"RISK_{field_name.upper()}"
            env_val = os.getenv(env_key)
            if env_val is not None:
                field_type = cls.__dataclass_fields__[field_name].type
                if field_type == "int":
                    kwargs[field_name] = int(env_val)
                else:
                    kwargs[field_name] = float(env_val)
        return cls(**kwargs)


# Regime multipliers: state -> {limit_category: multiplier}
REGIME_MULTIPLIERS: dict[int, dict[str, float]] = {
    0: {  # risk-on (GREEN)
        "position_size": 1.0,
        "portfolio_delta": 1.0,
        "portfolio_gamma": 1.0,
        "portfolio_vega": 1.0,
        "max_concurrent": 1.0,
        "daily_loss_pct": 1.0,
    },
    1: {  # risk-off (YELLOW)
        "position_size": 0.5,
        "portfolio_delta": 0.6,
        "portfolio_gamma": 0.6,
        "portfolio_vega": 0.67,
        "max_concurrent": 0.67,
        "daily_loss_pct": 0.6,
    },
    2: {  # crisis (RED)
        "position_size": 0.0,
        "portfolio_delta": 0.2,
        "portfolio_gamma": 0.3,
        "portfolio_vega": 0.33,
        "max_concurrent": 0.33,
        "daily_loss_pct": 0.2,
    },
}

# Kelly fraction scaling for different confidence levels
KELLY_FRACTIONS: dict[str, float] = {
    "paper_new": 0.25,       # 1/4 Kelly: new strategies in paper trading
    "paper_proven": 0.33,    # 1/3 Kelly: strategies with 30+ paper trades
}
