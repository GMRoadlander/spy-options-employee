"""Structured context assembly and Claude reasoning engine for market analysis.

Assembles data from all Phase 3 ML managers (regime, volatility, sentiment,
anomaly, flow) into a unified MarketContext, then sends it to Claude for
structured analysis.  The reasoning engine produces regime assessment,
volatility outlook, key levels, strategy implications, risk factors, and
conflict identification.

Classes:
    MarketContext -- dataclass holding ~27 fields of assembled market data.
    ReasoningEngine -- Claude API wrapper with retry + circuit breaker.
    ReasoningManager -- orchestrates context assembly from all ML managers.

Usage::

    engine = ReasoningEngine()
    manager = ReasoningManager(engine, feature_store)
    analysis = await manager.run_analysis("SPX", spot_price=5800.0)
    print(analysis["summary"])
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import anthropic
import httpx

from src.config import config

if TYPE_CHECKING:
    from src.ml.anomaly import AnomalyManager, FlowAnalyzer
    from src.ml.feature_store import FeatureStore
    from src.ml.regime import RegimeManager
    from src.ml.sentiment import SentimentManager
    from src.ml.volatility import VolManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MarketContext dataclass
# ---------------------------------------------------------------------------


@dataclass
class MarketContext:
    """Unified market context assembled from all Phase 3 ML managers.

    Contains ~27 fields covering regime, volatility, sentiment, GEX,
    flow/anomaly, and derived features.  String fields should be XML-safe
    before insertion into prompts.
    """

    timestamp: str
    ticker: str
    spot_price: float
    # Regime
    regime_state: str  # "risk-on", "risk-off", "crisis", "unknown"
    regime_probability: float
    regime_duration_est: float
    # Volatility
    vol_forecast_1d: float
    vol_forecast_5d: float
    current_iv_rank: float
    rv_iv_spread: float
    current_vix: float
    # Sentiment
    sentiment_score: float  # -1 to 1
    sentiment_velocity: float
    # GEX (expanded)
    gex_net: float
    gex_gamma_flip: float | None
    gex_squeeze_probability: float
    # Flow/Anomaly
    anomaly_score: float
    anomaly_flags: list[dict] = field(default_factory=list)
    flow_summary: dict = field(default_factory=dict)
    dark_pool_ratio: float = 0.0
    # Features
    skew_25d: float = 0.0
    term_structure_slope: float = 0.0
    hurst_exponent: float = 0.0
    pcr: float = 0.0  # volume PCR
    oi_pcr: float = 0.0
    dealer_positioning: str = "neutral"  # "short_gamma"/"long_gamma"/"neutral"
    max_pain_price: float = 0.0
    # Data quality
    data_sources: list[str] = field(default_factory=list)
    staleness_warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class ReasoningError(Exception):
    """Raised when reasoning analysis fails."""


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------


def _escape_xml(text: str) -> str:
    """Escape XML special characters in text."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_context_prompt(ctx: MarketContext) -> str:
    """Format a MarketContext into an XML-delimited prompt for Claude.

    Creates human-readable structured text with sections for regime,
    volatility, sentiment, gamma exposure, flow/anomaly, features,
    and data quality.  String fields are escaped for XML safety.

    Args:
        ctx: Assembled market context.

    Returns:
        XML-delimited prompt string.
    """
    # Sentiment direction label
    if ctx.sentiment_score > 0.2:
        sentiment_dir = "bullish"
    elif ctx.sentiment_score < -0.2:
        sentiment_dir = "bearish"
    else:
        sentiment_dir = "neutral"

    # Gamma flip label
    if ctx.gex_gamma_flip is not None:
        gamma_flip_str = f"${ctx.gex_gamma_flip:.2f}"
    else:
        gamma_flip_str = "not detected"

    # Anomaly flags summary
    anomaly_lines = ""
    for flag in ctx.anomaly_flags:
        flag_type = _escape_xml(str(flag.get("type", "unknown")))
        flag_val = flag.get("value", 0)
        is_anom = flag.get("is_anomaly", False)
        anomaly_lines += f"\n    - {flag_type}: value={flag_val}, anomaly={is_anom}"
    if not anomaly_lines:
        anomaly_lines = "\n    None"

    # Staleness warnings
    staleness_lines = ""
    for w in ctx.staleness_warnings:
        staleness_lines += f"\n    - {_escape_xml(w)}"
    if not staleness_lines:
        staleness_lines = "\n    None"

    # Data sources
    sources_str = ", ".join(ctx.data_sources) if ctx.data_sources else "none"

    prompt = f"""\
<market_context>
  Ticker: {_escape_xml(ctx.ticker)}
  Spot Price: ${ctx.spot_price:.2f}
  Timestamp: {_escape_xml(ctx.timestamp)}
</market_context>

<regime>
  Current State: {_escape_xml(ctx.regime_state)}
  Regime Probability: {ctx.regime_probability:.1%}
  Estimated Duration: {ctx.regime_duration_est:.1f} days
</regime>

<volatility>
  1-Day Vol Forecast: {ctx.vol_forecast_1d:.4f}
  5-Day Vol Forecast: {ctx.vol_forecast_5d:.4f}
  IV Rank: {ctx.current_iv_rank:.1f}
  RV-IV Spread: {ctx.rv_iv_spread:.4f}
  Current VIX: {ctx.current_vix:.2f}
</volatility>

<sentiment>
  Score: {ctx.sentiment_score:.4f} ({sentiment_dir})
  Velocity: {ctx.sentiment_velocity:.4f}
</sentiment>

<gamma_exposure>
  Net GEX: {ctx.gex_net:.2e}
  Gamma Flip Level: {gamma_flip_str}
  Squeeze Probability: {ctx.gex_squeeze_probability:.1%}
</gamma_exposure>

<flow_anomaly>
  Anomaly Score: {ctx.anomaly_score:.4f}
  Dark Pool Ratio: {ctx.dark_pool_ratio:.4f}
  Anomaly Flags:{anomaly_lines}
</flow_anomaly>

<features>
  25-Delta Skew: {ctx.skew_25d:.4f}
  Term Structure Slope: {ctx.term_structure_slope:.4f}
  Hurst Exponent: {ctx.hurst_exponent:.4f}
  Volume PCR: {ctx.pcr:.4f}
  OI PCR: {ctx.oi_pcr:.4f}
  Dealer Positioning: {_escape_xml(ctx.dealer_positioning)}
  Max Pain Price: ${ctx.max_pain_price:.2f}
</features>

<data_quality>
  Sources: {_escape_xml(sources_str)}
  Staleness Warnings:{staleness_lines}
</data_quality>"""

    return prompt


# ---------------------------------------------------------------------------
# Default analysis result
# ---------------------------------------------------------------------------

DEFAULT_ANALYSIS: dict[str, Any] = {
    "summary": "Analysis unavailable \u2014 using defaults.",
    "regime_assessment": "unknown",
    "volatility_outlook": "unknown",
    "key_levels": [],
    "strategy_implications": [],
    "risk_factors": [],
    "raw_confidence": 0.5,
    "conflicts": [],
    "parse_quality": 0.0,
}


# ---------------------------------------------------------------------------
# System prompt for the reasoning engine
# ---------------------------------------------------------------------------

REASONING_SYSTEM_PROMPT = """\
You are an expert SPX options market analyst. Given structured market context data, \
provide a thorough analysis following these steps:

1. Assess the current market regime and its implications for options trading
2. Evaluate volatility conditions and forecasts
3. Identify any conflicts between signals (e.g., bullish sentiment but bearish GEX)
4. Determine key price levels from gamma exposure analysis
5. Provide strategy implications for premium-selling strategies
6. Flag risk factors and areas of uncertainty

Do NOT predict market direction. Focus on structural analysis.

Wrap your response in the following XML sections:
<summary>1-2 sentence overview</summary>
<regime_assessment>Regime analysis with duration and transition probabilities</regime_assessment>
<volatility_outlook>Vol forecast interpretation with IV rank context</volatility_outlook>
<key_levels>Key gamma levels, max pain, support/resistance</key_levels>
<strategy_implications>Specific strategy recommendations based on conditions</strategy_implications>
<risk_factors>Risks, tail events, data staleness concerns</risk_factors>
<conflicts>Any conflicting signals between data sources</conflicts>
<confidence>0.0-1.0 confidence in overall assessment</confidence>\
"""


# ---------------------------------------------------------------------------
# ReasoningEngine — Claude API wrapper
# ---------------------------------------------------------------------------


class ReasoningEngine:
    """Claude-based reasoning engine for structured market analysis.

    Follows the strategy_parser.py pattern with lazy client initialisation,
    retry logic, and a circuit breaker for consecutive failures.

    Args:
        api_key: Claude API key.  Defaults to ``config.claude_api_key``.
        model: Claude model identifier.  Defaults to ``config.claude_model``.
    """

    _MAX_RETRIES = 2
    _RETRY_DELAY = 1.0
    _MAX_CONSECUTIVE_FAILURES = 3
    _CIRCUIT_BREAKER_COOLDOWN = 900  # 15 minutes in seconds

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or config.claude_api_key
        self._model = model or config.claude_model
        self._client: anthropic.AsyncAnthropic | None = None
        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0

    @property
    def client(self) -> anthropic.AsyncAnthropic:
        """Lazy-initialized, reusable AsyncAnthropic client."""
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(
                api_key=self._api_key,
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    def _is_circuit_open(self) -> bool:
        """Check whether the circuit breaker is currently open."""
        if self._consecutive_failures >= self._MAX_CONSECUTIVE_FAILURES:
            if time.monotonic() < self._circuit_open_until:
                return True
            # Reset after cooldown
            self._consecutive_failures = 0
        return False

    async def _call_with_retry(self, system: str, user_content: str) -> str:
        """Call Claude API with retry logic and circuit breaker.

        Args:
            system: System prompt.
            user_content: User message content.

        Returns:
            Claude's response text.

        Raises:
            ReasoningError: If all retries are exhausted or circuit is open.
        """
        if self._is_circuit_open():
            raise ReasoningError("Circuit breaker open \u2014 too many consecutive failures")

        last_exc: Exception | None = None
        for attempt in range(1 + self._MAX_RETRIES):
            try:
                message = await self.client.messages.create(
                    model=self._model,
                    max_tokens=2048,
                    temperature=0,
                    system=system,
                    messages=[{"role": "user", "content": user_content}],
                )
                response_text = ""
                for block in message.content:
                    if block.type == "text":
                        response_text += block.text
                self._consecutive_failures = 0  # Reset on success
                return response_text.strip()
            except anthropic.RateLimitError as exc:
                last_exc = exc
                if attempt < self._MAX_RETRIES:
                    logger.warning(
                        "Rate limited, retrying in %.1fs",
                        self._RETRY_DELAY * (attempt + 1),
                    )
                    await asyncio.sleep(self._RETRY_DELAY * (attempt + 1))
            except (anthropic.APIConnectionError, anthropic.InternalServerError) as exc:
                last_exc = exc
                if attempt < self._MAX_RETRIES:
                    logger.warning("Transient API error, retrying: %s", exc)
                    await asyncio.sleep(self._RETRY_DELAY)
            except anthropic.APIError as exc:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self._MAX_CONSECUTIVE_FAILURES:
                    self._circuit_open_until = (
                        time.monotonic() + self._CIRCUIT_BREAKER_COOLDOWN
                    )
                raise ReasoningError(f"Claude API error: {exc}") from exc

        self._consecutive_failures += 1
        if self._consecutive_failures >= self._MAX_CONSECUTIVE_FAILURES:
            self._circuit_open_until = time.monotonic() + self._CIRCUIT_BREAKER_COOLDOWN
        raise ReasoningError(
            f"Claude API failed after {self._MAX_RETRIES + 1} attempts: {last_exc}"
        ) from last_exc

    @staticmethod
    def _extract_section(text: str, tag: str, default: str = "") -> str:
        """Extract content between XML tags.  Never raises.

        Args:
            text: Full response text.
            tag: XML tag name to extract.
            default: Value to return if tag is not found.

        Returns:
            Stripped content between tags, or *default*.
        """
        pattern = rf"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else default

    def _parse_analysis(
        self, text: str, active_strategies: list[str] | None = None
    ) -> dict[str, Any]:
        """Parse Claude's XML response into a structured analysis dict.

        Args:
            text: Raw XML response from Claude.
            active_strategies: Optional list of active strategy names.

        Returns:
            Structured analysis dict with all expected keys.
        """
        if not text:
            return dict(DEFAULT_ANALYSIS)

        expected_sections = [
            "summary",
            "regime_assessment",
            "volatility_outlook",
            "key_levels",
            "strategy_implications",
            "risk_factors",
            "conflicts",
            "confidence",
        ]

        result: dict[str, Any] = {}
        found = 0
        for section in expected_sections:
            value = self._extract_section(text, section, "")
            if value:
                found += 1
            if section == "confidence":
                # Clamp to [0, 1] and label as raw_confidence
                try:
                    conf = max(0.0, min(1.0, float(value)))
                except (ValueError, TypeError):
                    conf = 0.5
                result["raw_confidence"] = conf
            elif section in (
                "key_levels",
                "strategy_implications",
                "risk_factors",
                "conflicts",
            ):
                # Parse as list (split on newlines, filter empty)
                lines = [
                    line.strip().lstrip("- ").strip()
                    for line in value.split("\n")
                    if line.strip()
                ]
                result[section] = lines
            else:
                result[section] = value or DEFAULT_ANALYSIS.get(section, "")

        result["parse_quality"] = (
            found / len(expected_sections) if expected_sections else 0.0
        )

        # If nothing was parsed, return defaults
        if found == 0:
            return dict(DEFAULT_ANALYSIS)

        # Fill missing keys from defaults
        for key, default_val in DEFAULT_ANALYSIS.items():
            if key not in result:
                result[key] = default_val

        return result

    async def analyze(
        self,
        context: MarketContext,
        active_strategies: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run Claude analysis on assembled market context.

        Args:
            context: Assembled market context.
            active_strategies: Optional list of active strategy names.

        Returns:
            Structured analysis dict.  Returns ``DEFAULT_ANALYSIS`` on
            failure or missing API key.
        """
        if not self._api_key:
            logger.warning("No Claude API key configured \u2014 returning defaults")
            return dict(DEFAULT_ANALYSIS)

        prompt = format_context_prompt(context)
        try:
            response = await self._call_with_retry(REASONING_SYSTEM_PROMPT, prompt)
            return self._parse_analysis(response, active_strategies)
        except ReasoningError:
            logger.error("Reasoning analysis failed", exc_info=True)
            return dict(DEFAULT_ANALYSIS)


# ---------------------------------------------------------------------------
# ReasoningManager — context assembly + orchestration
# ---------------------------------------------------------------------------


class ReasoningManager:
    """Orchestrates context assembly from all ML managers and runs reasoning.

    Gathers data from regime, volatility, sentiment, anomaly, and flow
    managers in parallel, assembles a :class:`MarketContext`, and passes
    it to the :class:`ReasoningEngine` for structured analysis.

    Args:
        engine: A :class:`ReasoningEngine` instance.
        feature_store: An initialised :class:`FeatureStore`.
        regime_manager: Optional :class:`RegimeManager`.
        vol_manager: Optional :class:`VolManager`.
        sentiment_manager: Optional :class:`SentimentManager`.
        anomaly_manager: Optional :class:`AnomalyManager`.
        flow_analyzer: Optional :class:`FlowAnalyzer`.
    """

    def __init__(
        self,
        engine: ReasoningEngine,
        feature_store: FeatureStore,
        regime_manager: RegimeManager | None = None,
        vol_manager: VolManager | None = None,
        sentiment_manager: SentimentManager | None = None,
        anomaly_manager: AnomalyManager | None = None,
        flow_analyzer: FlowAnalyzer | None = None,
    ) -> None:
        self._engine = engine
        self._feature_store = feature_store
        self._regime_manager = regime_manager
        self._vol_manager = vol_manager
        self._sentiment_manager = sentiment_manager
        self._anomaly_manager = anomaly_manager
        self._flow_analyzer = flow_analyzer
        self._latest_analysis: dict | None = None

    @staticmethod
    async def _safe_get(coro: Any, label: str) -> Any:
        """Execute an async call with error isolation.

        Args:
            coro: Awaitable to execute.
            label: Human-readable label for logging on failure.

        Returns:
            The coroutine result, or ``None`` on any exception.
        """
        try:
            return await coro
        except Exception as exc:
            logger.warning("Failed to get %s: %s", label, exc)
            return None

    async def _assemble_context(
        self, ticker: str, spot_price: float = 0.0
    ) -> MarketContext:
        """Gather data from all available managers in parallel.

        Args:
            ticker: Underlying ticker symbol.
            spot_price: Current spot price.

        Returns:
            Populated :class:`MarketContext`.
        """
        from datetime import datetime

        data_sources: list[str] = []
        staleness_warnings: list[str] = []

        # Parallel fetch from all managers
        tasks: dict[str, Any] = {}
        if self._regime_manager:
            tasks["regime"] = self._safe_get(
                self._regime_manager.get_current_regime(ticker), "regime"
            )
        if self._vol_manager:
            tasks["vol"] = self._safe_get(
                self._vol_manager.get_current_forecast(ticker), "volatility"
            )
        if self._sentiment_manager:
            tasks["sentiment"] = self._safe_get(
                self._sentiment_manager.get_current_sentiment(ticker), "sentiment"
            )
        if self._anomaly_manager:
            tasks["anomaly"] = self._safe_get(
                self._anomaly_manager.get_current_anomalies(ticker), "anomaly"
            )
        if self._flow_analyzer:
            tasks["flow"] = self._safe_get(
                self._flow_analyzer.get_enriched_flow(ticker), "flow"
            )

        # Also get feature store data
        tasks["features"] = self._safe_get(
            self._feature_store.get_latest_features(ticker), "features"
        )

        results: dict[str, Any] = {}
        if tasks:
            keys = list(tasks.keys())
            values = await asyncio.gather(*tasks.values())
            results = dict(zip(keys, values))

        # Extract results with defaults
        regime = results.get("regime") or {}
        vol = results.get("vol") or {}
        sentiment = results.get("sentiment") or {}
        anomaly = results.get("anomaly")  # AnomalyReport or None
        flow = results.get("flow") or {}
        features = results.get("features") or {}

        # Track data sources
        if regime:
            data_sources.append("regime")
        if vol:
            data_sources.append("volatility")
        if sentiment:
            data_sources.append("sentiment")
        if anomaly:
            data_sources.append("anomaly")
        if flow and flow.get("flow_source", "none") != "none":
            data_sources.append("flow")
        if features:
            data_sources.append("features")

        # Check staleness (feature store date > 6 hours old)
        if features and features.get("computed_at"):
            try:
                computed = datetime.fromisoformat(features["computed_at"])
                age_hours = (datetime.now() - computed).total_seconds() / 3600
                if age_hours > 6:
                    staleness_warnings.append(
                        f"Feature store data is {age_hours:.1f} hours old"
                    )
            except (ValueError, TypeError):
                pass

        # Map regime state name
        regime_state_name = regime.get("state_name", "unknown")

        return MarketContext(
            timestamp=datetime.now().isoformat(),
            ticker=ticker,
            spot_price=spot_price,
            regime_state=regime_state_name,
            regime_probability=regime.get("regime_probability", 0.0),
            regime_duration_est=0.0,  # Not available from current API
            vol_forecast_1d=vol.get("vol_forecast_1d") or 0.0,
            vol_forecast_5d=vol.get("vol_forecast_5d") or 0.0,
            current_iv_rank=features.get("iv_rank") or 0.0,
            rv_iv_spread=features.get("rv_iv_spread") or 0.0,
            current_vix=0.0,  # Will be available when VIX data source is wired
            sentiment_score=sentiment.get("sentiment_score") or 0.0,
            sentiment_velocity=0.0,  # Velocity requires historical comparison
            gex_net=features.get("net_gex") or 0.0,
            gex_gamma_flip=None,  # From snapshot data, not feature store
            gex_squeeze_probability=0.0,
            anomaly_score=anomaly.overall_score if anomaly else 0.0,
            anomaly_flags=[
                f.__dict__ if hasattr(f, "__dict__") else f
                for f in (anomaly.flow_anomalies if anomaly else [])
            ],
            flow_summary=flow,
            dark_pool_ratio=flow.get("dark_pool_ratio", 0.0),
            skew_25d=features.get("skew_25d") or 0.0,
            term_structure_slope=features.get("term_structure_slope") or 0.0,
            hurst_exponent=features.get("hurst_exponent") or 0.0,
            pcr=features.get("volume_pcr") or 0.0,
            oi_pcr=features.get("oi_pcr") or 0.0,
            dealer_positioning="neutral",  # From snapshot, not feature store
            max_pain_price=0.0,  # From snapshot, not feature store
            data_sources=data_sources,
            staleness_warnings=staleness_warnings,
        )

    async def run_analysis(
        self,
        ticker: str,
        spot_price: float = 0.0,
        active_strategies: list[str] | None = None,
    ) -> dict[str, Any]:
        """Assemble context and run reasoning engine.

        Args:
            ticker: Underlying ticker symbol.
            spot_price: Current spot price.
            active_strategies: Optional list of active strategy names.

        Returns:
            Structured analysis dict from the reasoning engine.
        """
        ctx = await self._assemble_context(ticker, spot_price)
        analysis = await self._engine.analyze(ctx, active_strategies)
        self._latest_analysis = analysis
        return analysis

    async def get_latest_analysis(self) -> dict | None:
        """Return the cached latest analysis or None."""
        return self._latest_analysis
