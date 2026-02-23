"""Tests for FinBERT sentiment scoring (src/ml/sentiment.py).

All tests mock the transformers pipeline to avoid downloading the
250 MB model in CI.  Covers scoring, batching, aggregation, edge cases,
SentimentManager update pipeline, and news client integration.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.data.news_client import NewsClient
from src.ml.sentiment import SentimentManager, SentimentScorer


# ---------------------------------------------------------------------------
# Helpers — mock pipeline factory
# ---------------------------------------------------------------------------


def _make_mock_pipeline(default_results: list[dict] | None = None):
    """Create a mock transformers pipeline.

    When called with a single string, returns a list of one result.
    When called with a list of strings, returns a matching-length list.
    """
    mock_pipe = MagicMock()

    if default_results is None:
        default_results = [{"label": "neutral", "score": 0.85}]

    def side_effect(text_or_texts, **kwargs):
        if isinstance(text_or_texts, list):
            # Batch mode — return one result per input text.
            return default_results[: len(text_or_texts)] if len(default_results) >= len(text_or_texts) else default_results * len(text_or_texts)
        # Single text — return list of one result.
        return default_results[:1]

    mock_pipe.side_effect = side_effect
    return mock_pipe


def _make_scorer_with_mock(results: list[dict] | None = None) -> SentimentScorer:
    """Create a SentimentScorer with a pre-injected mock pipeline."""
    scorer = SentimentScorer()
    scorer._pipeline = _make_mock_pipeline(results)
    return scorer


# ---------------------------------------------------------------------------
# SentimentScorer — score_text
# ---------------------------------------------------------------------------


class TestSentimentScorerScoreText:
    """score_text() returns correct labels and sentiment values."""

    def test_positive_text(self) -> None:
        scorer = _make_scorer_with_mock([{"label": "positive", "score": 0.95}])
        result = scorer.score_text("Markets rally on strong earnings beat")

        assert result["label"] == "positive"
        assert result["score"] == pytest.approx(0.95)
        assert result["sentiment_value"] == pytest.approx(0.95)

    def test_negative_text(self) -> None:
        scorer = _make_scorer_with_mock([{"label": "negative", "score": 0.88}])
        result = scorer.score_text("Stock crashes on profit warning")

        assert result["label"] == "negative"
        assert result["score"] == pytest.approx(0.88)
        assert result["sentiment_value"] == pytest.approx(-0.88)

    def test_neutral_text(self) -> None:
        scorer = _make_scorer_with_mock([{"label": "neutral", "score": 0.70}])
        result = scorer.score_text("Company reports quarterly results")

        assert result["label"] == "neutral"
        assert result["score"] == pytest.approx(0.70)
        assert result["sentiment_value"] == pytest.approx(0.0)

    def test_empty_string_returns_neutral(self) -> None:
        scorer = _make_scorer_with_mock()
        result = scorer.score_text("")

        assert result["label"] == "neutral"
        assert result["score"] == 0.0
        assert result["sentiment_value"] == 0.0

    def test_whitespace_only_returns_neutral(self) -> None:
        scorer = _make_scorer_with_mock()
        result = scorer.score_text("   \n\t  ")

        assert result["label"] == "neutral"
        assert result["score"] == 0.0
        assert result["sentiment_value"] == 0.0

    def test_sentiment_value_sign_matches_positive_label(self) -> None:
        scorer = _make_scorer_with_mock([{"label": "positive", "score": 0.99}])
        result = scorer.score_text("Great earnings")
        assert result["sentiment_value"] > 0

    def test_sentiment_value_sign_matches_negative_label(self) -> None:
        scorer = _make_scorer_with_mock([{"label": "negative", "score": 0.99}])
        result = scorer.score_text("Terrible losses")
        assert result["sentiment_value"] < 0

    def test_sentiment_value_neutral_is_zero(self) -> None:
        scorer = _make_scorer_with_mock([{"label": "neutral", "score": 0.99}])
        result = scorer.score_text("Annual report filed")
        assert result["sentiment_value"] == 0.0


# ---------------------------------------------------------------------------
# SentimentScorer — score_batch
# ---------------------------------------------------------------------------


class TestSentimentScorerScoreBatch:
    """score_batch() handles batch scoring and edge cases."""

    def test_batch_returns_correct_count(self) -> None:
        results = [
            {"label": "positive", "score": 0.9},
            {"label": "negative", "score": 0.8},
            {"label": "neutral", "score": 0.7},
        ]
        scorer = _make_scorer_with_mock(results)
        texts = [
            "Market surges on rate cut hopes",
            "Bank collapses amid crisis",
            "Fed holds rates steady",
        ]
        batch = scorer.score_batch(texts)
        assert len(batch) == 3

    def test_batch_filters_empty_strings(self) -> None:
        results = [{"label": "positive", "score": 0.9}]
        scorer = _make_scorer_with_mock(results)
        texts = ["Good news", "", "  ", ""]
        batch = scorer.score_batch(texts)
        assert len(batch) == 1

    def test_batch_all_empty_returns_empty(self) -> None:
        scorer = _make_scorer_with_mock()
        batch = scorer.score_batch(["", "  ", ""])
        assert batch == []

    def test_batch_empty_list_returns_empty(self) -> None:
        scorer = _make_scorer_with_mock()
        batch = scorer.score_batch([])
        assert batch == []

    def test_batch_result_format(self) -> None:
        results = [{"label": "positive", "score": 0.85}]
        scorer = _make_scorer_with_mock(results)
        batch = scorer.score_batch(["Strong quarter"])
        assert len(batch) == 1
        assert "label" in batch[0]
        assert "score" in batch[0]
        assert "sentiment_value" in batch[0]


# ---------------------------------------------------------------------------
# SentimentScorer — compute_aggregate
# ---------------------------------------------------------------------------


class TestSentimentScorerComputeAggregate:
    """compute_aggregate() computes correct statistics."""

    def test_aggregate_mixed_scores(self) -> None:
        scores = [
            {"label": "positive", "score": 0.9, "sentiment_value": 0.9},
            {"label": "negative", "score": 0.8, "sentiment_value": -0.8},
            {"label": "neutral", "score": 0.7, "sentiment_value": 0.0},
        ]
        agg = SentimentScorer.compute_aggregate(scores)

        assert agg["count"] == 3
        assert agg["mean_sentiment"] == pytest.approx((0.9 - 0.8 + 0.0) / 3, abs=1e-4)
        assert agg["positive_pct"] == pytest.approx(1 / 3, abs=1e-3)
        assert agg["negative_pct"] == pytest.approx(1 / 3, abs=1e-3)
        assert agg["neutral_pct"] == pytest.approx(1 / 3, abs=1e-3)
        assert agg["sentiment_velocity"] is None

    def test_aggregate_all_positive(self) -> None:
        scores = [
            {"label": "positive", "score": 0.95, "sentiment_value": 0.95},
            {"label": "positive", "score": 0.90, "sentiment_value": 0.90},
        ]
        agg = SentimentScorer.compute_aggregate(scores)

        assert agg["mean_sentiment"] == pytest.approx(0.925, abs=1e-4)
        assert agg["positive_pct"] == 1.0
        assert agg["negative_pct"] == 0.0
        assert agg["neutral_pct"] == 0.0

    def test_aggregate_all_negative(self) -> None:
        scores = [
            {"label": "negative", "score": 0.85, "sentiment_value": -0.85},
            {"label": "negative", "score": 0.75, "sentiment_value": -0.75},
        ]
        agg = SentimentScorer.compute_aggregate(scores)

        assert agg["mean_sentiment"] == pytest.approx(-0.80, abs=1e-4)
        assert agg["positive_pct"] == 0.0
        assert agg["negative_pct"] == 1.0

    def test_aggregate_empty_list(self) -> None:
        agg = SentimentScorer.compute_aggregate([])

        assert agg["count"] == 0
        assert agg["mean_sentiment"] == 0.0
        assert agg["positive_pct"] == 0.0
        assert agg["negative_pct"] == 0.0
        assert agg["neutral_pct"] == 0.0
        assert agg["sentiment_velocity"] is None

    def test_aggregate_single_score(self) -> None:
        scores = [{"label": "positive", "score": 0.99, "sentiment_value": 0.99}]
        agg = SentimentScorer.compute_aggregate(scores)

        assert agg["count"] == 1
        assert agg["mean_sentiment"] == pytest.approx(0.99, abs=1e-4)
        assert agg["positive_pct"] == 1.0


# ---------------------------------------------------------------------------
# SentimentScorer — lazy loading
# ---------------------------------------------------------------------------


class TestSentimentScorerLazyLoading:
    """The pipeline is loaded lazily, not on construction."""

    def test_pipeline_not_loaded_on_init(self) -> None:
        scorer = SentimentScorer()
        assert scorer._pipeline is None

    @patch("src.ml.sentiment.SentimentScorer._ensure_loaded")
    def test_ensure_loaded_called_on_score_text(self, mock_load: MagicMock) -> None:
        scorer = SentimentScorer()
        scorer._pipeline = _make_mock_pipeline([{"label": "neutral", "score": 0.5}])
        scorer.score_text("Test")
        mock_load.assert_called_once()

    @patch("src.ml.sentiment.SentimentScorer._ensure_loaded")
    def test_ensure_loaded_called_on_score_batch(self, mock_load: MagicMock) -> None:
        scorer = SentimentScorer()
        scorer._pipeline = _make_mock_pipeline([{"label": "neutral", "score": 0.5}])
        scorer.score_batch(["Test"])
        mock_load.assert_called_once()


# ---------------------------------------------------------------------------
# Helpers — mock factories for manager tests
# ---------------------------------------------------------------------------


def _make_mock_news_client(headlines: list[dict] | None = None) -> MagicMock:
    """Create a mock NewsClient with async fetch_headlines."""
    client = MagicMock(spec=NewsClient)
    if headlines is None:
        headlines = [
            {"title": "Markets rally on strong data", "published": "2026-02-22T10:00:00Z", "source": "Reuters", "url": "https://example.com/1"},
            {"title": "Fed holds rates steady", "published": "2026-02-22T09:00:00Z", "source": "Bloomberg", "url": "https://example.com/2"},
        ]
    client.fetch_headlines = AsyncMock(return_value=headlines)
    return client


def _make_mock_feature_store() -> MagicMock:
    """Create a mock FeatureStore with async methods."""
    store = MagicMock()
    store.save_features = AsyncMock()
    store.get_features = AsyncMock(return_value=None)
    store.get_latest_features = AsyncMock(return_value=None)
    store.get_feature_history = AsyncMock(return_value=[])
    return store


# ---------------------------------------------------------------------------
# NewsClient tests
# ---------------------------------------------------------------------------


class TestNewsClient:
    """NewsClient basic behaviour (mocked — no real HTTP)."""

    def test_init_stores_api_key(self) -> None:
        client = NewsClient(polygon_api_key="test-key")
        assert client._polygon_api_key == "test-key"

    def test_init_empty_key(self) -> None:
        client = NewsClient()
        assert client._polygon_api_key == ""

    @pytest.mark.asyncio
    async def test_fetch_headlines_no_key_returns_empty(self) -> None:
        client = NewsClient(polygon_api_key="")
        result = await client.fetch_headlines("SPX")
        assert result == []

    def test_rate_limit_tracking_initial(self) -> None:
        client = NewsClient(polygon_api_key="key")
        assert client._request_times == []


# ---------------------------------------------------------------------------
# SentimentManager tests
# ---------------------------------------------------------------------------


class TestSentimentManagerUpdate:
    """SentimentManager.update() pipeline with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_update_returns_aggregate(self) -> None:
        scorer = _make_scorer_with_mock([
            {"label": "positive", "score": 0.9},
            {"label": "neutral", "score": 0.7},
        ])
        news = _make_mock_news_client()
        store = _make_mock_feature_store()

        mgr = SentimentManager(scorer, news, store)
        result = await mgr.update("SPX")

        assert result is not None
        assert "mean_sentiment" in result
        assert "positive_pct" in result
        assert "count" in result
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_update_persists_to_feature_store(self) -> None:
        scorer = _make_scorer_with_mock([{"label": "positive", "score": 0.85}])
        news = _make_mock_news_client()
        store = _make_mock_feature_store()

        mgr = SentimentManager(scorer, news, store)
        await mgr.update("SPX")

        store.save_features.assert_called_once()
        call_args = store.save_features.call_args
        assert call_args[0][0] == "SPX"  # ticker
        features = call_args[0][2]
        assert "sentiment_score" in features

    @pytest.mark.asyncio
    async def test_update_empty_headlines_returns_none(self) -> None:
        scorer = _make_scorer_with_mock()
        news = _make_mock_news_client(headlines=[])
        store = _make_mock_feature_store()

        mgr = SentimentManager(scorer, news, store)
        result = await mgr.update("SPX")

        assert result is None
        store.save_features.assert_not_called()

    @pytest.mark.asyncio
    async def test_velocity_computed_from_yesterday(self) -> None:
        scorer = _make_scorer_with_mock([{"label": "positive", "score": 0.80}])
        news = _make_mock_news_client()
        store = _make_mock_feature_store()

        # Yesterday had sentiment of 0.5.
        store.get_features.return_value = {"sentiment_score": 0.5}

        mgr = SentimentManager(scorer, news, store)
        result = await mgr.update("SPX")

        assert result is not None
        # Today: 0.80, yesterday: 0.50 → velocity = 0.30.
        assert result["sentiment_velocity"] == pytest.approx(0.30, abs=1e-4)

    @pytest.mark.asyncio
    async def test_velocity_none_when_no_yesterday(self) -> None:
        scorer = _make_scorer_with_mock([{"label": "positive", "score": 0.80}])
        news = _make_mock_news_client()
        store = _make_mock_feature_store()
        store.get_features.return_value = None

        mgr = SentimentManager(scorer, news, store)
        result = await mgr.update("SPX")

        assert result is not None
        assert result["sentiment_velocity"] is None


class TestSentimentManagerGetCurrent:
    """SentimentManager.get_current_sentiment() reads from feature store."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_data(self) -> None:
        scorer = _make_scorer_with_mock()
        news = _make_mock_news_client()
        store = _make_mock_feature_store()
        store.get_latest_features.return_value = None

        mgr = SentimentManager(scorer, news, store)
        result = await mgr.get_current_sentiment("SPX")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_sentiment_from_store(self) -> None:
        scorer = _make_scorer_with_mock()
        news = _make_mock_news_client()
        store = _make_mock_feature_store()
        store.get_latest_features.return_value = {
            "sentiment_score": 0.45,
            "date": "2026-02-22",
        }

        mgr = SentimentManager(scorer, news, store)
        result = await mgr.get_current_sentiment("SPX")

        assert result is not None
        assert result["sentiment_score"] == pytest.approx(0.45)
        assert result["date"] == "2026-02-22"

    @pytest.mark.asyncio
    async def test_returns_none_when_score_is_null(self) -> None:
        scorer = _make_scorer_with_mock()
        news = _make_mock_news_client()
        store = _make_mock_feature_store()
        store.get_latest_features.return_value = {
            "sentiment_score": None,
            "date": "2026-02-22",
        }

        mgr = SentimentManager(scorer, news, store)
        result = await mgr.get_current_sentiment("SPX")
        assert result is None


class TestSentimentManagerGetHistory:
    """SentimentManager.get_sentiment_history() reads time series."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_history(self) -> None:
        scorer = _make_scorer_with_mock()
        news = _make_mock_news_client()
        store = _make_mock_feature_store()
        store.get_feature_history.return_value = []

        mgr = SentimentManager(scorer, news, store)
        result = await mgr.get_sentiment_history("SPX", days=30)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_history_excluding_none(self) -> None:
        scorer = _make_scorer_with_mock()
        news = _make_mock_news_client()
        store = _make_mock_feature_store()
        store.get_feature_history.return_value = [
            ("2026-02-20", 0.3),
            ("2026-02-21", None),
            ("2026-02-22", 0.5),
        ]

        mgr = SentimentManager(scorer, news, store)
        result = await mgr.get_sentiment_history("SPX", days=30)

        assert len(result) == 2
        assert result[0] == {"date": "2026-02-20", "sentiment_score": 0.3}
        assert result[1] == {"date": "2026-02-22", "sentiment_score": 0.5}
