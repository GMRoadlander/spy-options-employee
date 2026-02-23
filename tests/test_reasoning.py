"""Tests for the structured context assembly and Claude reasoning engine."""

import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai.reasoning import (
    DEFAULT_ANALYSIS,
    REASONING_SYSTEM_PROMPT,
    MarketContext,
    ReasoningEngine,
    ReasoningError,
    ReasoningManager,
    _escape_xml,
    format_context_prompt,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_response(text: str):
    """Create a mock anthropic response."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


VALID_XML_RESPONSE = """\
<summary>Market is in risk-on regime with elevated IV rank.</summary>
<regime_assessment>Risk-on regime with 85% probability, expected to persist 15 days.</regime_assessment>
<volatility_outlook>IV rank at 65 suggests elevated premium, 1d vol forecast below realized.</volatility_outlook>
<key_levels>
- Gamma flip at $5800
- Max pain at $5750
- Put wall at $5700
</key_levels>
<strategy_implications>
- Iron condors favored given elevated IV rank
- Widen wings due to regime uncertainty
</strategy_implications>
<risk_factors>
- VIX term structure inverted
- Feature store data 8 hours stale
</risk_factors>
<conflicts>
- Bullish sentiment contradicts bearish GEX positioning
</conflicts>
<confidence>0.78</confidence>\
"""


def _make_full_context(**overrides) -> MarketContext:
    """Create a full MarketContext with sensible defaults."""
    defaults = dict(
        timestamp="2025-06-15T10:30:00",
        ticker="SPX",
        spot_price=5800.0,
        regime_state="risk-on",
        regime_probability=0.85,
        regime_duration_est=15.0,
        vol_forecast_1d=0.15,
        vol_forecast_5d=0.17,
        current_iv_rank=65.0,
        rv_iv_spread=0.02,
        current_vix=18.5,
        sentiment_score=0.35,
        sentiment_velocity=0.05,
        gex_net=1.5e9,
        gex_gamma_flip=5800.0,
        gex_squeeze_probability=0.15,
        anomaly_score=0.3,
        anomaly_flags=[{"type": "sweep_surge", "value": 42, "is_anomaly": True}],
        flow_summary={"flow_source": "unusual_whales", "total_premium": 1e6},
        dark_pool_ratio=0.2,
        skew_25d=4.1,
        term_structure_slope=0.05,
        hurst_exponent=0.45,
        pcr=0.85,
        oi_pcr=1.1,
        dealer_positioning="short_gamma",
        max_pain_price=5750.0,
        data_sources=["regime", "volatility", "sentiment"],
        staleness_warnings=[],
    )
    defaults.update(overrides)
    return MarketContext(**defaults)


# ---------------------------------------------------------------------------
# MarketContext tests
# ---------------------------------------------------------------------------


class TestMarketContext:
    def test_market_context_creation(self):
        """Test full MarketContext with all fields."""
        ctx = _make_full_context()
        assert ctx.ticker == "SPX"
        assert ctx.spot_price == 5800.0
        assert ctx.regime_state == "risk-on"
        assert ctx.regime_probability == 0.85
        assert ctx.vol_forecast_1d == 0.15
        assert ctx.sentiment_score == 0.35
        assert ctx.gex_net == 1.5e9
        assert ctx.gex_gamma_flip == 5800.0
        assert ctx.anomaly_score == 0.3
        assert len(ctx.anomaly_flags) == 1
        assert ctx.dealer_positioning == "short_gamma"
        assert len(ctx.data_sources) == 3

    def test_market_context_defaults(self):
        """Test MarketContext with minimal required fields, defaults work."""
        ctx = MarketContext(
            timestamp="2025-06-15T10:30:00",
            ticker="SPX",
            spot_price=5800.0,
            regime_state="unknown",
            regime_probability=0.0,
            regime_duration_est=0.0,
            vol_forecast_1d=0.0,
            vol_forecast_5d=0.0,
            current_iv_rank=0.0,
            rv_iv_spread=0.0,
            current_vix=0.0,
            sentiment_score=0.0,
            sentiment_velocity=0.0,
            gex_net=0.0,
            gex_gamma_flip=None,
            gex_squeeze_probability=0.0,
            anomaly_score=0.0,
        )
        # Check all default-initialized fields
        assert ctx.anomaly_flags == []
        assert ctx.flow_summary == {}
        assert ctx.dark_pool_ratio == 0.0
        assert ctx.skew_25d == 0.0
        assert ctx.term_structure_slope == 0.0
        assert ctx.hurst_exponent == 0.0
        assert ctx.pcr == 0.0
        assert ctx.oi_pcr == 0.0
        assert ctx.dealer_positioning == "neutral"
        assert ctx.max_pain_price == 0.0
        assert ctx.data_sources == []
        assert ctx.staleness_warnings == []


# ---------------------------------------------------------------------------
# format_context_prompt tests
# ---------------------------------------------------------------------------


class TestFormatContextPrompt:
    def test_format_context_prompt_contains_sections(self):
        """Check that all XML sections exist in the output."""
        ctx = _make_full_context()
        prompt = format_context_prompt(ctx)

        expected_sections = [
            "<market_context>",
            "</market_context>",
            "<regime>",
            "</regime>",
            "<volatility>",
            "</volatility>",
            "<sentiment>",
            "</sentiment>",
            "<gamma_exposure>",
            "</gamma_exposure>",
            "<flow_anomaly>",
            "</flow_anomaly>",
            "<features>",
            "</features>",
            "<data_quality>",
            "</data_quality>",
        ]
        for section in expected_sections:
            assert section in prompt, f"Missing section: {section}"

    def test_format_context_prompt_regime_labels(self):
        """Regime state appears in output."""
        ctx = _make_full_context(regime_state="crisis")
        prompt = format_context_prompt(ctx)
        assert "crisis" in prompt

    def test_format_context_prompt_special_characters(self):
        """Special XML characters in string fields get escaped."""
        ctx = _make_full_context(
            ticker="SPX<>",
            dealer_positioning="short&gamma",
            staleness_warnings=["Data < 6 hours & stale > expected"],
        )
        prompt = format_context_prompt(ctx)
        assert "SPX&lt;&gt;" in prompt
        assert "short&amp;gamma" in prompt
        assert "&lt; 6 hours" in prompt
        assert "&amp; stale" in prompt
        assert "&gt; expected" in prompt

    def test_format_context_prompt_extreme_values(self):
        """Handles float('inf'), 0.0, many anomaly flags."""
        ctx = _make_full_context(
            spot_price=float("inf"),
            anomaly_flags=[
                {"type": "sweep_surge", "value": 100, "is_anomaly": True},
                {"type": "premium_spike", "value": 999, "is_anomaly": False},
                {"type": "dark_pool_divergence", "value": 0.5, "is_anomaly": True},
            ],
        )
        prompt = format_context_prompt(ctx)
        # Should not raise; just check it contains some anomaly info
        assert "sweep_surge" in prompt
        assert "premium_spike" in prompt
        assert "dark_pool_divergence" in prompt


# ---------------------------------------------------------------------------
# _escape_xml tests
# ---------------------------------------------------------------------------


class TestEscapeXml:
    def test_escape_xml(self):
        """Test basic XML escaping."""
        assert _escape_xml("hello & world") == "hello &amp; world"
        assert _escape_xml("<tag>") == "&lt;tag&gt;"
        assert _escape_xml("no special chars") == "no special chars"
        assert _escape_xml("") == ""
        assert _escape_xml("a & b < c > d") == "a &amp; b &lt; c &gt; d"


# ---------------------------------------------------------------------------
# ReasoningEngine tests
# ---------------------------------------------------------------------------


class TestReasoningEngine:
    def test_reasoning_engine_init(self):
        """Test default config values."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        assert engine._api_key == "test-key"
        assert engine._model == "test-model"
        assert engine._client is None
        assert engine._consecutive_failures == 0
        assert engine._circuit_open_until == 0.0

    def test_reasoning_engine_lazy_client(self):
        """Client is created on first access."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        assert engine._client is None
        client = engine.client
        assert client is not None
        assert engine._client is client
        # Second access returns the same instance
        assert engine.client is client

    @pytest.mark.asyncio
    async def test_reasoning_engine_analyze_mocked(self):
        """Mock anthropic client, return valid XML, verify parsed result."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        mock_response = _make_mock_response(VALID_XML_RESPONSE)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        engine._client = mock_client

        ctx = _make_full_context()
        result = await engine.analyze(ctx)

        assert "risk-on" in result["summary"].lower() or "risk-on" in result["regime_assessment"].lower() or result["summary"] != ""
        assert result["regime_assessment"] != ""
        assert result["volatility_outlook"] != ""
        assert isinstance(result["key_levels"], list)
        assert len(result["key_levels"]) > 0
        assert isinstance(result["strategy_implications"], list)
        assert isinstance(result["risk_factors"], list)
        assert isinstance(result["conflicts"], list)
        assert 0.0 <= result["raw_confidence"] <= 1.0
        assert result["raw_confidence"] == 0.78
        assert result["parse_quality"] == 1.0  # All 8 sections found

    @pytest.mark.asyncio
    async def test_reasoning_engine_malformed_response(self):
        """Prose without XML tags returns defaults."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        mock_response = _make_mock_response(
            "The market looks bullish today with strong momentum."
        )

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        engine._client = mock_client

        ctx = _make_full_context()
        result = await engine.analyze(ctx)

        # Should fall back to defaults
        assert result["summary"] == DEFAULT_ANALYSIS["summary"]
        assert result["parse_quality"] == 0.0

    @pytest.mark.asyncio
    async def test_reasoning_engine_partial_response(self):
        """Some XML sections missing, uses defaults for missing."""
        partial_xml = """\
<summary>Partial analysis available.</summary>
<regime_assessment>Risk-on regime.</regime_assessment>
<confidence>0.6</confidence>\
"""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        mock_response = _make_mock_response(partial_xml)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        engine._client = mock_client

        ctx = _make_full_context()
        result = await engine.analyze(ctx)

        assert result["summary"] == "Partial analysis available."
        assert result["regime_assessment"] == "Risk-on regime."
        assert result["raw_confidence"] == 0.6
        # Missing sections get defaults
        assert result["key_levels"] == []
        assert result["strategy_implications"] == []
        assert result["risk_factors"] == []
        assert result["conflicts"] == []
        # parse_quality: 3 out of 8 found
        assert result["parse_quality"] == 3.0 / 8.0

    @pytest.mark.asyncio
    async def test_reasoning_engine_confidence_bounds(self):
        """Confidence >1 clamped to 1, <0 clamped to 0."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")

        # Test confidence > 1
        xml_high = "<summary>Test</summary><confidence>1.5</confidence>"
        result = engine._parse_analysis(xml_high)
        assert result["raw_confidence"] == 1.0

        # Test confidence < 0
        xml_low = "<summary>Test</summary><confidence>-0.3</confidence>"
        result = engine._parse_analysis(xml_low)
        assert result["raw_confidence"] == 0.0

        # Test non-numeric confidence
        xml_bad = "<summary>Test</summary><confidence>high</confidence>"
        result = engine._parse_analysis(xml_bad)
        assert result["raw_confidence"] == 0.5  # default

    @pytest.mark.asyncio
    async def test_reasoning_engine_rate_limit_error(self):
        """RateLimitError handled, retries."""
        import anthropic as anthropic_mod

        engine = ReasoningEngine(api_key="test-key", model="test-model")
        mock_response = _make_mock_response(VALID_XML_RESPONSE)

        mock_client = AsyncMock()
        # First call raises RateLimitError, second succeeds
        rate_limit_exc = anthropic_mod.RateLimitError(
            message="rate limited",
            response=MagicMock(status_code=429, headers={}),
            body=None,
        )
        mock_client.messages.create = AsyncMock(
            side_effect=[rate_limit_exc, mock_response]
        )
        engine._client = mock_client

        ctx = _make_full_context()
        # Should succeed on retry
        with patch("src.ai.reasoning.asyncio.sleep", new_callable=AsyncMock):
            result = await engine.analyze(ctx)

        assert result["summary"] != DEFAULT_ANALYSIS["summary"]
        assert mock_client.messages.create.call_count == 2

    @pytest.mark.asyncio
    async def test_reasoning_engine_timeout(self):
        """APIConnectionError handled."""
        import anthropic as anthropic_mod

        engine = ReasoningEngine(api_key="test-key", model="test-model")

        mock_client = AsyncMock()
        conn_exc = anthropic_mod.APIConnectionError(request=MagicMock())
        mock_client.messages.create = AsyncMock(side_effect=conn_exc)
        engine._client = mock_client

        ctx = _make_full_context()
        # Should return defaults after retries exhausted
        with patch("src.ai.reasoning.asyncio.sleep", new_callable=AsyncMock):
            result = await engine.analyze(ctx)

        assert result == DEFAULT_ANALYSIS
        # 1 + 2 retries = 3 total attempts
        assert mock_client.messages.create.call_count == 3

    @pytest.mark.asyncio
    async def test_reasoning_engine_circuit_breaker(self):
        """After 3 failures, circuit opens."""
        import anthropic as anthropic_mod

        engine = ReasoningEngine(api_key="test-key", model="test-model")

        # Simulate 3 consecutive non-retryable API errors
        api_exc = anthropic_mod.APIError(
            message="server error",
            request=MagicMock(),
            body=None,
        )

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(side_effect=api_exc)
        engine._client = mock_client

        ctx = _make_full_context()

        # First 3 calls trigger APIError -> ReasoningError, incrementing failures
        for _ in range(3):
            result = await engine.analyze(ctx)
            assert result == DEFAULT_ANALYSIS

        assert engine._consecutive_failures >= 3
        assert engine._circuit_open_until > 0

        # Now the circuit should be open — next call returns defaults
        # without even calling the API
        mock_client.messages.create.reset_mock()
        result = await engine.analyze(ctx)
        assert result == DEFAULT_ANALYSIS

    @pytest.mark.asyncio
    async def test_reasoning_engine_no_api_key(self):
        """Returns DEFAULT_ANALYSIS when no API key is set."""
        engine = ReasoningEngine(api_key="", model="test-model")
        ctx = _make_full_context()
        result = await engine.analyze(ctx)
        assert result == DEFAULT_ANALYSIS


# ---------------------------------------------------------------------------
# _parse_analysis / _extract_section tests
# ---------------------------------------------------------------------------


class TestParseHelpers:
    def test_parse_analysis_empty(self):
        """Empty string returns defaults."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        result = engine._parse_analysis("")
        assert result == DEFAULT_ANALYSIS

    def test_extract_section_found(self):
        """Regex finds tag content."""
        text = "<summary>Hello world</summary>"
        result = ReasoningEngine._extract_section(text, "summary")
        assert result == "Hello world"

    def test_extract_section_missing(self):
        """Returns default when tag is missing."""
        text = "<other>content</other>"
        result = ReasoningEngine._extract_section(text, "summary", "fallback")
        assert result == "fallback"

    def test_extract_section_multiline(self):
        """Extracts multiline content between tags."""
        text = "<key_levels>\n- Level 1\n- Level 2\n</key_levels>"
        result = ReasoningEngine._extract_section(text, "key_levels")
        assert "Level 1" in result
        assert "Level 2" in result


# ---------------------------------------------------------------------------
# ReasoningManager tests
# ---------------------------------------------------------------------------


class TestReasoningManager:
    @pytest.mark.asyncio
    async def test_reasoning_manager_assemble_all_managers(self):
        """All managers mocked, context populated."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        # Mock engine.analyze to return a known result
        mock_analysis = dict(DEFAULT_ANALYSIS)
        mock_analysis["summary"] = "All managers populated."
        engine.analyze = AsyncMock(return_value=mock_analysis)

        feature_store = AsyncMock()
        feature_store.get_latest_features = AsyncMock(
            return_value={
                "iv_rank": 65.0,
                "rv_iv_spread": 0.02,
                "net_gex": 1.5e9,
                "skew_25d": 4.1,
                "term_structure_slope": 0.05,
                "hurst_exponent": 0.45,
                "volume_pcr": 0.85,
                "oi_pcr": 1.1,
                "computed_at": "2025-06-15T10:00:00",
            }
        )

        regime_manager = AsyncMock()
        regime_manager.get_current_regime = AsyncMock(
            return_value={
                "state_name": "risk-on",
                "regime_probability": 0.85,
                "regime_state": 0,
            }
        )

        vol_manager = AsyncMock()
        vol_manager.get_current_forecast = AsyncMock(
            return_value={"vol_forecast_1d": 0.15, "vol_forecast_5d": 0.17}
        )

        sentiment_manager = AsyncMock()
        sentiment_manager.get_current_sentiment = AsyncMock(
            return_value={"sentiment_score": 0.35}
        )

        # AnomalyReport-like mock
        anomaly_report = MagicMock()
        anomaly_report.overall_score = 0.3
        anomaly_report.flow_anomalies = [
            {"type": "sweep_surge", "value": 42, "is_anomaly": True}
        ]
        anomaly_manager = AsyncMock()
        anomaly_manager.get_current_anomalies = AsyncMock(return_value=anomaly_report)

        flow_analyzer = AsyncMock()
        flow_analyzer.get_enriched_flow = AsyncMock(
            return_value={
                "flow_source": "unusual_whales",
                "dark_pool_ratio": 0.2,
                "total_premium": 1e6,
            }
        )

        manager = ReasoningManager(
            engine=engine,
            feature_store=feature_store,
            regime_manager=regime_manager,
            vol_manager=vol_manager,
            sentiment_manager=sentiment_manager,
            anomaly_manager=anomaly_manager,
            flow_analyzer=flow_analyzer,
        )

        result = await manager.run_analysis("SPX", spot_price=5800.0)
        assert result["summary"] == "All managers populated."

        # Verify the engine was called with a populated context
        engine.analyze.assert_called_once()
        ctx = engine.analyze.call_args[0][0]
        assert isinstance(ctx, MarketContext)
        assert ctx.regime_state == "risk-on"
        assert ctx.vol_forecast_1d == 0.15
        assert ctx.sentiment_score == 0.35
        assert ctx.anomaly_score == 0.3
        assert ctx.dark_pool_ratio == 0.2
        assert "regime" in ctx.data_sources
        assert "volatility" in ctx.data_sources
        assert "sentiment" in ctx.data_sources
        assert "anomaly" in ctx.data_sources
        assert "flow" in ctx.data_sources
        assert "features" in ctx.data_sources

    @pytest.mark.asyncio
    async def test_reasoning_manager_assemble_no_managers(self):
        """All managers None, context has defaults."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        engine.analyze = AsyncMock(return_value=dict(DEFAULT_ANALYSIS))

        feature_store = AsyncMock()
        feature_store.get_latest_features = AsyncMock(return_value=None)

        manager = ReasoningManager(engine=engine, feature_store=feature_store)
        result = await manager.run_analysis("SPX")

        ctx = engine.analyze.call_args[0][0]
        assert ctx.regime_state == "unknown"
        assert ctx.vol_forecast_1d == 0.0
        assert ctx.sentiment_score == 0.0
        assert ctx.anomaly_score == 0.0
        assert ctx.data_sources == []

    @pytest.mark.asyncio
    async def test_reasoning_manager_assemble_partial(self):
        """Some managers None, error isolation works."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        engine.analyze = AsyncMock(return_value=dict(DEFAULT_ANALYSIS))

        feature_store = AsyncMock()
        feature_store.get_latest_features = AsyncMock(return_value={"iv_rank": 50.0})

        regime_manager = AsyncMock()
        regime_manager.get_current_regime = AsyncMock(
            return_value={"state_name": "risk-off", "regime_probability": 0.7}
        )

        manager = ReasoningManager(
            engine=engine,
            feature_store=feature_store,
            regime_manager=regime_manager,
            # vol, sentiment, anomaly, flow all None
        )
        result = await manager.run_analysis("SPX")

        ctx = engine.analyze.call_args[0][0]
        assert ctx.regime_state == "risk-off"
        assert ctx.vol_forecast_1d == 0.0
        assert ctx.sentiment_score == 0.0
        assert "regime" in ctx.data_sources
        assert "features" in ctx.data_sources

    @pytest.mark.asyncio
    async def test_reasoning_manager_assemble_manager_exception(self):
        """One manager raises, others still work."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        engine.analyze = AsyncMock(return_value=dict(DEFAULT_ANALYSIS))

        feature_store = AsyncMock()
        feature_store.get_latest_features = AsyncMock(return_value={"iv_rank": 50.0})

        # Regime manager raises an exception
        regime_manager = AsyncMock()
        regime_manager.get_current_regime = AsyncMock(
            side_effect=RuntimeError("Model not initialized")
        )

        # Vol manager works fine
        vol_manager = AsyncMock()
        vol_manager.get_current_forecast = AsyncMock(
            return_value={"vol_forecast_1d": 0.12, "vol_forecast_5d": 0.14}
        )

        manager = ReasoningManager(
            engine=engine,
            feature_store=feature_store,
            regime_manager=regime_manager,
            vol_manager=vol_manager,
        )
        result = await manager.run_analysis("SPX")

        ctx = engine.analyze.call_args[0][0]
        # Regime should have fallen back to defaults
        assert ctx.regime_state == "unknown"
        # Vol should still be populated
        assert ctx.vol_forecast_1d == 0.12
        assert "volatility" in ctx.data_sources
        assert "regime" not in ctx.data_sources

    @pytest.mark.asyncio
    async def test_reasoning_manager_caching(self):
        """run_analysis caches, get_latest_analysis returns it."""
        engine = ReasoningEngine(api_key="test-key", model="test-model")
        mock_analysis = dict(DEFAULT_ANALYSIS)
        mock_analysis["summary"] = "Cached analysis."
        engine.analyze = AsyncMock(return_value=mock_analysis)

        feature_store = AsyncMock()
        feature_store.get_latest_features = AsyncMock(return_value=None)

        manager = ReasoningManager(engine=engine, feature_store=feature_store)

        # Initially no cached analysis
        assert await manager.get_latest_analysis() is None

        # Run analysis
        result = await manager.run_analysis("SPX")
        assert result["summary"] == "Cached analysis."

        # Cached analysis should match
        cached = await manager.get_latest_analysis()
        assert cached is not None
        assert cached["summary"] == "Cached analysis."


# ---------------------------------------------------------------------------
# Import verification
# ---------------------------------------------------------------------------


class TestImports:
    def test_import_verification(self):
        """Verify all public names are importable."""
        from src.ai.reasoning import ReasoningEngine
        from src.ai.reasoning import MarketContext
        from src.ai.reasoning import ReasoningManager
        from src.ai.reasoning import ReasoningError
        from src.ai.reasoning import format_context_prompt
        from src.ai.reasoning import DEFAULT_ANALYSIS
        from src.ai.reasoning import REASONING_SYSTEM_PROMPT
        from src.ai.reasoning import _escape_xml

        assert ReasoningEngine is not None
        assert MarketContext is not None
        assert ReasoningManager is not None
        assert ReasoningError is not None
        assert format_context_prompt is not None
        assert DEFAULT_ANALYSIS is not None
        assert REASONING_SYSTEM_PROMPT is not None
        assert _escape_xml is not None
