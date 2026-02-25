"""Tests for application configuration defaults.

Verifies that config fields added for paper trading reporting,
degradation thresholds, and rolling metrics have correct defaults.
"""

from src.config import Config


class TestConfigDegradationDefaults:
    """Verify degradation threshold defaults match plan values."""

    def test_config_degradation_defaults(self):
        cfg = Config()

        # Paper trading reporting schedule
        assert cfg.paper_daily_report_hour == 16
        assert cfg.paper_daily_report_minute == 15
        assert cfg.paper_weekly_report_day == 4      # Friday
        assert cfg.paper_monthly_report_day == 1     # 1st of month

        # Degradation thresholds
        assert cfg.degradation_sharpe_threshold == 0.5
        assert cfg.degradation_win_rate_threshold == 0.10
        assert cfg.degradation_max_dd_ratio == 1.5
        assert cfg.degradation_min_trades_for_check == 10

    def test_config_rolling_window_default(self):
        cfg = Config()
        assert cfg.rolling_metrics_window == 20
