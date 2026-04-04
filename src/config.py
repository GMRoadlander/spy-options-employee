"""Configuration settings for the SPY/SPX options employee."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    # Discord
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    analysis_channel_id: int = int(os.getenv("DISCORD_ANALYSIS_CHANNEL_ID", "0"))
    alerts_channel_id: int = int(os.getenv("DISCORD_ALERTS_CHANNEL_ID", "0"))
    commands_channel_id: int = int(os.getenv("DISCORD_COMMANDS_CHANNEL_ID", "0"))

    # Claude API
    claude_api_key: str = os.getenv("CLAUDE_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    # Tastytrade (primary data source — OAuth2)
    tastytrade_client_secret: str = os.getenv("TASTYTRADE_CLIENT_SECRET", "")
    tastytrade_refresh_token: str = os.getenv("TASTYTRADE_REFRESH_TOKEN", "")
    tastytrade_sandbox: bool = os.getenv("TASTYTRADE_SANDBOX", "false").lower() == "true"

    # Tradier
    tradier_token: str = os.getenv("TRADIER_TOKEN", "")
    tradier_base_url: str = "https://sandbox.tradier.com/v1"

    # CBOE CDN
    cboe_spy_url: str = "https://cdn.cboe.com/api/global/delayed_quotes/options/SPY.json"
    cboe_spx_url: str = "https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json"

    # Schedule
    update_interval_minutes: int = 2
    market_open_hour: int = 9
    market_open_minute: int = 30
    market_close_hour: int = 16
    market_close_minute: int = 0
    premarket_post_minute: int = 15  # 9:15 ET
    postmarket_post_minute: int = 5  # 16:05 ET
    timezone: str = "US/Eastern"

    # Analysis
    tickers: list[str] = field(default_factory=lambda: ["SPY", "SPX"])
    risk_free_rate: float = 0.05  # 5% — update as needed
    gex_lookback_strikes: int = 50  # strikes above/below current price

    # Alerts
    alert_cooldown_minutes: int = 30
    gamma_flip_threshold: float = 0.0
    squeeze_pcr_threshold: float = 0.3
    max_pain_convergence_pct: float = 0.005  # 0.5%
    oi_shift_threshold_pct: float = 0.10  # 10%

    # Webhook server
    webhook_port: int = int(os.getenv("WEBHOOK_PORT", "8000"))
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")

    # TradingView webhook alerts
    webhook_alerts_channel_id: int = int(os.getenv("DISCORD_WEBHOOK_ALERTS_CHANNEL_ID", "0"))

    # CheddarFlow
    cheddarflow_channel_id: int = int(os.getenv("DISCORD_CHEDDARFLOW_CHANNEL_ID", "0"))
    cheddarflow_output_channel_id: int = int(os.getenv("DISCORD_CHEDDARFLOW_OUTPUT_CHANNEL_ID", "0"))
    cheddarflow_min_premium: float = float(os.getenv("CHEDDARFLOW_MIN_PREMIUM", "50000"))

    # Database
    db_path: str = "data/spy_employee.db"
    history_retention_days: int = 30

    # ORATS (historical data source — Phase 2)
    orats_api_key: str = os.getenv("ORATS_API_KEY", "")

    # Strategy system (Phase 2)
    strategy_dir: str = os.getenv("STRATEGY_DIR", "strategies")

    # Historical data storage (Phase 2)
    historical_data_dir: str = os.getenv("HISTORICAL_DATA_DIR", "data/historical")

    # Journal system (Phase 2-3)
    journal_channel_id: int = int(os.getenv("DISCORD_JOURNAL_CHANNEL_ID", "0"))
    monthly_report_day: int = int(os.getenv("MONTHLY_REPORT_DAY", "1"))

    # ML Intelligence Layer (Phase 3)
    ml_features_dir: str = os.getenv("ML_FEATURES_DIR", "data/ml_models")

    # Polygon.io (news + full market data — Phase 3+)
    polygon_api_key: str = os.getenv("POLYGON_API_KEY", "")
    polygon_rate_limit: int = int(os.getenv("POLYGON_RATE_LIMIT", "5"))
    news_lookback_hours: int = int(os.getenv("NEWS_LOOKBACK_HOURS", "24"))

    # Unusual Whales (institutional flow + dark pool — Phase 3)
    unusual_whales_api_key: str = os.getenv("UNUSUAL_WHALES_API_KEY", "")

    # Paper Trading (Phase 4)
    paper_starting_capital: float = float(os.getenv("PAPER_STARTING_CAPITAL", "100000"))
    paper_slippage_pct: float = float(os.getenv("PAPER_SLIPPAGE_PCT", "0.10"))
    paper_fee_per_contract: float = float(os.getenv("PAPER_FEE_PER_CONTRACT", "0.65"))
    paper_spx_multiplier: float = 100.0
    paper_min_trades_for_promotion: int = int(os.getenv("PAPER_MIN_TRADES", "30"))
    paper_min_days_for_promotion: int = int(os.getenv("PAPER_MIN_DAYS", "14"))
    paper_max_order_age_ticks: int = int(os.getenv("PAPER_MAX_ORDER_AGE", "5"))
    paper_channel_id: int = int(os.getenv("DISCORD_PAPER_TRADING_CHANNEL_ID", "0"))

    # Paper trading auto-post time (16:15 ET -- between post-market and journal)
    paper_daily_post_hour: int = 16
    paper_daily_post_minute: int = 15

    # Paper trading reporting schedule
    paper_daily_report_hour: int = 16
    paper_daily_report_minute: int = 15
    paper_weekly_report_day: int = 4      # 0=Mon, 4=Fri
    paper_monthly_report_day: int = 1     # 1st of month

    # Degradation thresholds
    degradation_sharpe_threshold: float = 0.5
    degradation_win_rate_threshold: float = 0.10
    degradation_max_dd_ratio: float = 1.5
    degradation_min_trades_for_check: int = 10

    # Rolling metrics window
    rolling_metrics_window: int = 20

    # Risk management (Phase 4, sub-plan 4-5)
    risk_max_portfolio_delta: float = float(os.getenv("RISK_MAX_PORTFOLIO_DELTA", "500"))
    risk_max_portfolio_gamma: float = float(os.getenv("RISK_MAX_PORTFOLIO_GAMMA", "100"))
    risk_max_portfolio_vega: float = float(os.getenv("RISK_MAX_PORTFOLIO_VEGA", "15000"))
    risk_max_daily_loss_pct: float = float(os.getenv("RISK_MAX_DAILY_LOSS_PCT", "0.05"))
    risk_max_drawdown_pct: float = float(os.getenv("RISK_MAX_DRAWDOWN_PCT", "0.10"))
    risk_vix_halt_threshold: float = float(os.getenv("RISK_VIX_HALT_THRESHOLD", "35"))


config = Config()
