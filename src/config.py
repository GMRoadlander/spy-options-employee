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
    claude_api_key: str = os.getenv("CLAUDE_API_KEY", "")
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


config = Config()
