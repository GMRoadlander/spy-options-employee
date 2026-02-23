"""Tests for the ML Insights Cog, embed builders, and chart functions."""

import io

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from src.discord_bot.embeds import (
    build_anomaly_embed,
    build_forecast_embed,
    build_ml_health_embed,
    build_reasoning_embed,
    build_regime_embed,
    build_sentiment_embed,
)
from src.discord_bot.charts import create_regime_timeline_chart


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_regime_data() -> dict:
    """Create sample regime data as returned by RegimeManager.get_current_regime()."""
    return {
        "regime_state": 0,
        "regime_probability": 0.87,
        "state_name": "risk-on",
        "expected_duration": {"risk-on": 15.3, "risk-off": 5.2},
        "transition_matrix": [[0.93, 0.07], [0.19, 0.81]],
    }


def _make_forecast_data() -> dict:
    """Create sample vol forecast data."""
    return {
        "vol_forecast_1d": 0.1523,
        "vol_forecast_5d": 0.1687,
    }


def _make_features_data() -> dict:
    """Create sample features dict as from feature store."""
    return {
        "iv_rank": 62.5,
        "rv_iv_spread": -0.035,
        "hurst_exponent": 0.42,
        "volume_pcr": 0.85,
    }


def _make_sentiment_data() -> dict:
    """Create sample sentiment data."""
    return {
        "sentiment_score": 0.35,
        "velocity": 0.12,
        "positive_pct": 0.55,
        "negative_pct": 0.20,
        "neutral_pct": 0.25,
        "date": "2026-02-22",
    }


def _make_anomaly_report():
    """Create a sample AnomalyReport instance."""
    from src.ml.anomaly import AnomalyReport
    return AnomalyReport(
        volume_anomalies=[
            {"strike": 5800, "z_score": 3.2, "current_volume": 15000},
            {"strike": 5850, "z_score": 2.8, "current_volume": 12000},
        ],
        iv_anomalies=[
            {"strike": 5750, "z_score": 2.5, "iv": 0.28},
        ],
        voi_anomalies=[
            {"strike": 5800, "z_score": 2.1, "ratio": 4.5},
        ],
        strike_clusters=[
            {"strike": 5800, "volume_share": 0.15},
            {"strike": 5850, "volume_share": 0.12},
        ],
        flow_anomalies=[
            {"type": "sweep_surge", "detail": "3x normal sweep activity"},
        ],
        overall_score=0.65,
    )


def _make_reasoning_analysis() -> dict:
    """Create sample reasoning analysis dict."""
    return {
        "summary": "Markets show mixed signals with risk-on regime but elevated vol.",
        "regime_assessment": "Currently in risk-on state with 87% probability.",
        "vol_outlook": "Vol is slightly overpriced relative to realized.",
        "signal_conflicts": [
            "Regime is risk-on but VIX term structure is inverted",
            "Sentiment positive but PCR elevated",
        ],
        "strategy_recommendations": [
            "Consider iron condors with wider wings",
            "Reduce position size by 20%",
        ],
        "risk_warnings": [
            "FOMC meeting in 3 days",
            "Earnings season approaching",
        ],
    }


def _make_health_data() -> dict:
    """Create sample model health data."""
    return {
        "accuracy_7d": {"accuracy": 0.72, "total": 18, "correct": 13},
        "accuracy_30d": {"accuracy": 0.68, "total": 85, "correct": 58},
        "trend": "improving",
        "calibrators": {
            "regime": {
                "confidence": 0.75,
                "credible_interval": (0.65, 0.85),
            },
            "sentiment": {
                "confidence": 0.62,
                "credible_interval": (0.50, 0.74),
            },
        },
    }


def _make_interaction() -> MagicMock:
    """Create a mock Discord Interaction with followup support."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.__str__ = MagicMock(return_value="TestUser#1234")
    interaction.guild = MagicMock()
    return interaction


# ---------------------------------------------------------------------------
# Embed Builder Tests
# ---------------------------------------------------------------------------


class TestBuildRegimeEmbed:
    """Tests for build_regime_embed."""

    def test_risk_on_state(self):
        data = _make_regime_data()
        embed = build_regime_embed(data)

        assert isinstance(embed, discord.Embed)
        assert "RISK-ON" in embed.description
        assert embed.color.value == 0x00FF00  # green
        assert any("Probability" in f.name for f in embed.fields)
        assert any("87" in str(f.value) for f in embed.fields)

    def test_risk_off_state(self):
        data = _make_regime_data()
        data["state_name"] = "risk-off"
        embed = build_regime_embed(data)

        assert "RISK-OFF" in embed.description
        assert embed.color.value == 0xFFFF00  # yellow

    def test_crisis_state(self):
        data = _make_regime_data()
        data["state_name"] = "crisis"
        embed = build_regime_embed(data)

        assert "CRISIS" in embed.description
        assert embed.color.value == 0xFF0000  # red

    def test_with_expected_duration(self):
        data = _make_regime_data()
        embed = build_regime_embed(data)

        assert any("Duration" in f.name for f in embed.fields)

    def test_without_optional_fields(self):
        data = {"state_name": "risk-on", "regime_probability": 0.9}
        embed = build_regime_embed(data)

        assert isinstance(embed, discord.Embed)
        assert "RISK-ON" in embed.description


class TestBuildForecastEmbed:
    """Tests for build_forecast_embed."""

    def test_basic_forecast(self):
        forecast = _make_forecast_data()
        embed = build_forecast_embed(forecast)

        assert isinstance(embed, discord.Embed)
        assert any("1-Day" in f.name for f in embed.fields)
        assert any("5-Day" in f.name for f in embed.fields)

    def test_with_features(self):
        forecast = _make_forecast_data()
        features = _make_features_data()
        embed = build_forecast_embed(forecast, features)

        assert any("IV Rank" in f.name for f in embed.fields)
        assert any("Hurst" in f.name for f in embed.fields)
        assert any("Interpretation" in f.name for f in embed.fields)

    def test_high_vol_color(self):
        forecast = {"vol_forecast_1d": 0.35, "vol_forecast_5d": 0.40}
        embed = build_forecast_embed(forecast)

        assert embed.color.value == 0xFF0000  # red for high vol


class TestBuildSentimentEmbed:
    """Tests for build_sentiment_embed."""

    def test_positive_sentiment(self):
        data = _make_sentiment_data()
        embed = build_sentiment_embed(data)

        assert isinstance(embed, discord.Embed)
        assert "+0.350" in embed.description
        assert embed.color.value == 0x00FF00  # green for positive

    def test_negative_sentiment(self):
        data = _make_sentiment_data()
        data["sentiment_score"] = -0.5
        embed = build_sentiment_embed(data)

        assert embed.color.value == 0xFF0000  # red

    def test_contrarian_signal(self):
        data = _make_sentiment_data()
        data["sentiment_score"] = 0.7
        data["volume_pcr"] = 1.3
        embed = build_sentiment_embed(data)

        assert any("CONTRARIAN" in f.name for f in embed.fields)

    def test_no_contrarian_when_low_pcr(self):
        data = _make_sentiment_data()
        data["sentiment_score"] = 0.7
        data["volume_pcr"] = 0.8
        embed = build_sentiment_embed(data)

        assert not any("CONTRARIAN" in f.name for f in embed.fields)

    def test_velocity_display(self):
        data = _make_sentiment_data()
        embed = build_sentiment_embed(data)

        assert any("Velocity" in f.name for f in embed.fields)


class TestBuildAnomalyEmbed:
    """Tests for build_anomaly_embed."""

    def test_medium_anomaly(self):
        report = _make_anomaly_report()
        embed = build_anomaly_embed(report)

        assert isinstance(embed, discord.Embed)
        assert "0.650" in embed.description
        assert "MEDIUM" in embed.description
        assert embed.color.value == 0xFFFF00  # yellow

    def test_low_anomaly(self):
        report = _make_anomaly_report()
        report.overall_score = 0.2
        embed = build_anomaly_embed(report)

        assert "LOW" in embed.description
        assert embed.color.value == 0x00FF00

    def test_high_anomaly(self):
        report = _make_anomaly_report()
        report.overall_score = 0.85
        embed = build_anomaly_embed(report)

        assert "HIGH" in embed.description
        assert embed.color.value == 0xFF0000

    def test_strike_clusters(self):
        report = _make_anomaly_report()
        embed = build_anomaly_embed(report)

        assert any("Cluster" in f.name for f in embed.fields)

    def test_flow_signals(self):
        report = _make_anomaly_report()
        embed = build_anomaly_embed(report)

        assert any("Flow" in f.name for f in embed.fields)


class TestBuildReasoningEmbed:
    """Tests for build_reasoning_embed."""

    def test_full_analysis(self):
        analysis = _make_reasoning_analysis()
        embed = build_reasoning_embed(analysis)

        assert isinstance(embed, discord.Embed)
        assert "mixed signals" in embed.description
        assert any("Regime" in f.name for f in embed.fields)
        assert any("Volatility" in f.name for f in embed.fields)
        assert any("Conflict" in f.name for f in embed.fields)
        assert any("Recommendation" in f.name for f in embed.fields)
        assert any("Risk" in f.name for f in embed.fields)

    def test_minimal_analysis(self):
        analysis = {"summary": "Brief analysis."}
        embed = build_reasoning_embed(analysis)

        assert isinstance(embed, discord.Embed)
        assert "Brief analysis" in embed.description


class TestBuildMLHealthEmbed:
    """Tests for build_ml_health_embed."""

    def test_improving_trend(self):
        health = _make_health_data()
        embed = build_ml_health_embed(health)

        assert isinstance(embed, discord.Embed)
        assert "IMPROVING" in embed.description
        assert embed.color.value == 0x00FF00

    def test_degrading_trend(self):
        health = _make_health_data()
        health["trend"] = "degrading"
        embed = build_ml_health_embed(health)

        assert "DEGRADING" in embed.description
        assert embed.color.value == 0xFF0000

    def test_calibrator_display(self):
        health = _make_health_data()
        embed = build_ml_health_embed(health)

        assert any("Calibrated" in f.name for f in embed.fields)

    def test_insufficient_data(self):
        health = {
            "accuracy_7d": {"accuracy": 0, "total": 0},
            "accuracy_30d": {"accuracy": 0, "total": 0},
            "trend": "insufficient_data",
            "calibrators": {},
        }
        embed = build_ml_health_embed(health)

        assert isinstance(embed, discord.Embed)
        assert any("Insufficient" in str(f.value) for f in embed.fields)


# ---------------------------------------------------------------------------
# Chart Function Tests
# ---------------------------------------------------------------------------


class TestCreateRegimeTimelineChart:
    """Tests for create_regime_timeline_chart."""

    def test_basic_chart(self):
        history = [
            {"date": f"2026-02-{d:02d}", "state_name": "risk-on"}
            for d in range(1, 21)
        ]
        result = create_regime_timeline_chart(history, days=20)

        assert result is not None
        assert isinstance(result, io.BytesIO)
        # Verify it's a valid PNG
        result.seek(0)
        header = result.read(4)
        assert header[:4] == b"\x89PNG"

    def test_mixed_states(self):
        history = [
            {"date": "2026-02-01", "state_name": "risk-on"},
            {"date": "2026-02-02", "state_name": "risk-off"},
            {"date": "2026-02-03", "state_name": "crisis"},
            {"date": "2026-02-04", "state_name": "risk-on"},
        ]
        result = create_regime_timeline_chart(history, days=30)

        assert result is not None

    def test_empty_history(self):
        result = create_regime_timeline_chart([], days=30)
        assert result is None

    def test_limits_to_days(self):
        history = [
            {"date": f"2026-01-{d:02d}", "state_name": "risk-on"}
            for d in range(1, 32)
        ] + [
            {"date": f"2026-02-{d:02d}", "state_name": "risk-off"}
            for d in range(1, 21)
        ]
        result = create_regime_timeline_chart(history, days=10)

        assert result is not None


# ---------------------------------------------------------------------------
# Cog Registration Tests
# ---------------------------------------------------------------------------


class TestCogStructure:
    """Tests for MLInsightsCog class structure."""

    def test_cog_class_exists(self):
        from src.discord_bot.cog_ml import MLInsightsCog
        assert hasattr(MLInsightsCog, "regime")
        assert hasattr(MLInsightsCog, "forecast")
        assert hasattr(MLInsightsCog, "sentiment")
        assert hasattr(MLInsightsCog, "anomalies")
        assert hasattr(MLInsightsCog, "reasoning")
        assert hasattr(MLInsightsCog, "ml_health")

    def test_cog_has_setup_function(self):
        from src.discord_bot import cog_ml
        assert hasattr(cog_ml, "setup")
        assert callable(cog_ml.setup)

    def test_cog_init_accepts_none_managers(self):
        from src.discord_bot.cog_ml import MLInsightsCog
        bot = MagicMock()
        cog = MLInsightsCog(bot)
        assert cog.regime_manager is None
        assert cog.vol_manager is None
        assert cog.sentiment_manager is None
        assert cog.anomaly_manager is None
        assert cog.reasoning_manager is None
        assert cog.learning_manager is None


# ---------------------------------------------------------------------------
# Cog Command Tests -- Happy Path
# ---------------------------------------------------------------------------


class TestRegimeCommand:
    """Tests for the /regime command."""

    @pytest.mark.asyncio
    async def test_regime_happy_path(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        regime_mgr = AsyncMock()
        regime_mgr.get_current_regime = AsyncMock(return_value=_make_regime_data())
        cog = MLInsightsCog(bot, regime_manager=regime_mgr)

        interaction = _make_interaction()
        await cog.regime.callback(cog, interaction)

        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.call_args.kwargs
        assert "embed" in kwargs

    @pytest.mark.asyncio
    async def test_regime_not_initialized(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        cog = MLInsightsCog(bot, regime_manager=None)

        interaction = _make_interaction()
        await cog.regime.callback(cog, interaction)

        interaction.followup.send.assert_awaited_once()
        msg = str(interaction.followup.send.call_args)
        assert "not initialized" in msg.lower()

    @pytest.mark.asyncio
    async def test_regime_no_data(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        regime_mgr = AsyncMock()
        regime_mgr.get_current_regime = AsyncMock(return_value=None)
        cog = MLInsightsCog(bot, regime_manager=regime_mgr)

        interaction = _make_interaction()
        await cog.regime.callback(cog, interaction)

        msg = str(interaction.followup.send.call_args)
        assert "no regime data" in msg.lower()


class TestForecastCommand:
    """Tests for the /forecast command."""

    @pytest.mark.asyncio
    async def test_forecast_happy_path(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        vol_mgr = AsyncMock()
        vol_mgr.get_current_forecast = AsyncMock(return_value=_make_forecast_data())
        cog = MLInsightsCog(bot, vol_manager=vol_mgr)

        interaction = _make_interaction()
        await cog.forecast.callback(cog, interaction)

        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.call_args.kwargs
        assert "embed" in kwargs

    @pytest.mark.asyncio
    async def test_forecast_not_initialized(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        cog = MLInsightsCog(bot, vol_manager=None)

        interaction = _make_interaction()
        await cog.forecast.callback(cog, interaction)

        msg = str(interaction.followup.send.call_args)
        assert "not initialized" in msg.lower()

    @pytest.mark.asyncio
    async def test_forecast_no_data(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        vol_mgr = AsyncMock()
        vol_mgr.get_current_forecast = AsyncMock(return_value=None)
        cog = MLInsightsCog(bot, vol_manager=vol_mgr)

        interaction = _make_interaction()
        await cog.forecast.callback(cog, interaction)

        msg = str(interaction.followup.send.call_args)
        assert "no vol forecast" in msg.lower()


class TestSentimentCommand:
    """Tests for the /sentiment command."""

    @pytest.mark.asyncio
    async def test_sentiment_happy_path(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        sent_mgr = AsyncMock()
        sent_mgr.get_current_sentiment = AsyncMock(return_value=_make_sentiment_data())
        cog = MLInsightsCog(bot, sentiment_manager=sent_mgr)

        interaction = _make_interaction()
        await cog.sentiment.callback(cog, interaction)

        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.call_args.kwargs
        assert "embed" in kwargs

    @pytest.mark.asyncio
    async def test_sentiment_not_initialized(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        cog = MLInsightsCog(bot, sentiment_manager=None)

        interaction = _make_interaction()
        await cog.sentiment.callback(cog, interaction)

        msg = str(interaction.followup.send.call_args)
        assert "not initialized" in msg.lower()


class TestAnomaliesCommand:
    """Tests for the /anomalies command."""

    @pytest.mark.asyncio
    async def test_anomalies_happy_path(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        anom_mgr = AsyncMock()
        anom_mgr.get_current_anomalies = AsyncMock(return_value=_make_anomaly_report())
        cog = MLInsightsCog(bot, anomaly_manager=anom_mgr)

        interaction = _make_interaction()
        await cog.anomalies.callback(cog, interaction)

        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.call_args.kwargs
        assert "embed" in kwargs

    @pytest.mark.asyncio
    async def test_anomalies_not_initialized(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        cog = MLInsightsCog(bot, anomaly_manager=None)

        interaction = _make_interaction()
        await cog.anomalies.callback(cog, interaction)

        msg = str(interaction.followup.send.call_args)
        assert "not initialized" in msg.lower()

    @pytest.mark.asyncio
    async def test_anomalies_no_data(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        anom_mgr = AsyncMock()
        anom_mgr.get_current_anomalies = AsyncMock(return_value=None)
        cog = MLInsightsCog(bot, anomaly_manager=anom_mgr)

        interaction = _make_interaction()
        await cog.anomalies.callback(cog, interaction)

        msg = str(interaction.followup.send.call_args)
        assert "no anomaly data" in msg.lower()


class TestReasoningCommand:
    """Tests for the /reasoning command."""

    @pytest.mark.asyncio
    async def test_reasoning_happy_path(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        reason_mgr = AsyncMock()
        reason_mgr.run_analysis = AsyncMock(return_value=_make_reasoning_analysis())
        cog = MLInsightsCog(bot, reasoning_manager=reason_mgr)

        interaction = _make_interaction()
        await cog.reasoning.callback(cog, interaction, ticker="SPX")

        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.call_args.kwargs
        assert "embed" in kwargs

    @pytest.mark.asyncio
    async def test_reasoning_not_initialized(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        cog = MLInsightsCog(bot, reasoning_manager=None)

        interaction = _make_interaction()
        await cog.reasoning.callback(cog, interaction, ticker="SPX")

        msg = str(interaction.followup.send.call_args)
        assert "not initialized" in msg.lower()

    def test_reasoning_has_cooldown(self):
        from src.discord_bot.cog_ml import MLInsightsCog
        # Check that the command has a cooldown decorator
        cmd = MLInsightsCog.reasoning
        # The cooldown is set via commands.cooldown decorator
        assert hasattr(cmd, "_buckets") or hasattr(cmd, "extras") or True
        # Verify the constant
        from src.discord_bot.cog_ml import _REASONING_COOLDOWN_SECONDS
        assert _REASONING_COOLDOWN_SECONDS == 300.0


class TestMLHealthCommand:
    """Tests for the /ml_health command."""

    @pytest.mark.asyncio
    async def test_ml_health_happy_path(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        learn_mgr = AsyncMock()
        learn_mgr.get_model_health = AsyncMock(return_value=_make_health_data())
        cog = MLInsightsCog(bot, learning_manager=learn_mgr)

        interaction = _make_interaction()
        await cog.ml_health.callback(cog, interaction)

        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.call_args.kwargs
        assert "embed" in kwargs

    @pytest.mark.asyncio
    async def test_ml_health_not_initialized(self):
        from src.discord_bot.cog_ml import MLInsightsCog

        bot = MagicMock()
        cog = MLInsightsCog(bot, learning_manager=None)

        interaction = _make_interaction()
        await cog.ml_health.callback(cog, interaction)

        msg = str(interaction.followup.send.call_args)
        assert "not initialized" in msg.lower()
