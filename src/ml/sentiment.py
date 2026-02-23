"""FinBERT sentiment scoring for financial news headlines.

Uses the ProsusAI/finbert pre-trained model to classify financial text as
positive, negative, or neutral with confidence scores.  The model is loaded
lazily on first use (~250 MB download) and cached by Hugging Face.

Classes:
    SentimentScorer -- FinBERT wrapper with single/batch scoring and aggregation.
    SentimentManager -- daily update pipeline with news fetching, rolling
        sentiment index, and feature store integration.

Usage::

    scorer = SentimentScorer()
    result = scorer.score_text("Markets rally on strong earnings")
    print(result)  # {"label": "positive", "score": 0.98, "sentiment_value": 0.98}
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.data.news_client import NewsClient
    from src.ml.feature_store import FeatureStore

logger = logging.getLogger(__name__)


class SentimentScorer:
    """FinBERT-based sentiment scorer for financial text.

    Wraps a Hugging Face ``sentiment-analysis`` pipeline with lazy model
    loading.  The model is downloaded on the first call to any scoring
    method and cached in the default Hugging Face cache directory.

    Args:
        model_name: Hugging Face model identifier.  Defaults to
            ``"ProsusAI/finbert"``.
    """

    def __init__(self, model_name: str = "ProsusAI/finbert") -> None:
        self._model_name = model_name
        self._pipeline: Any | None = None

    def _ensure_loaded(self) -> None:
        """Download and load the model + tokenizer on first call.

        Uses ``transformers.pipeline("sentiment-analysis", ...)`` for
        simplicity.  The pipeline instance is cached for subsequent calls.
        """
        if self._pipeline is not None:
            return

        from transformers import pipeline  # noqa: C0415

        logger.info("Loading FinBERT model: %s", self._model_name)
        self._pipeline = pipeline(
            "sentiment-analysis",
            model=self._model_name,
        )
        logger.info("FinBERT model loaded successfully")

    @staticmethod
    def _map_sentiment_value(label: str, score: float) -> float:
        """Map a label + confidence to a signed sentiment value in [-1, 1].

        Positive -> +score, Negative -> -score, Neutral -> 0.0.
        """
        label_lower = label.lower()
        if label_lower == "positive":
            return score
        if label_lower == "negative":
            return -score
        return 0.0

    def score_text(self, text: str) -> dict:
        """Score a single piece of text.

        Args:
            text: Financial text to classify.

        Returns:
            Dict with keys ``label`` (str), ``score`` (float, 0-1
            confidence), and ``sentiment_value`` (float, -1 to +1).
        """
        if not text or not text.strip():
            return {
                "label": "neutral",
                "score": 0.0,
                "sentiment_value": 0.0,
            }

        self._ensure_loaded()
        result = self._pipeline(text, truncation=True)[0]  # type: ignore[misc]

        label = result["label"]
        score = float(result["score"])
        return {
            "label": label.lower(),
            "score": score,
            "sentiment_value": self._map_sentiment_value(label, score),
        }

    def score_batch(self, texts: list[str]) -> list[dict]:
        """Score a batch of texts for efficiency.

        Empty strings are filtered out.  The pipeline's internal batching
        is used for throughput.

        Args:
            texts: List of financial texts.

        Returns:
            List of score dicts (same format as :meth:`score_text`).
            Length matches the number of non-empty input texts.
        """
        # Filter empties, preserving order.
        valid = [(i, t) for i, t in enumerate(texts) if t and t.strip()]

        if not valid:
            return []

        self._ensure_loaded()
        valid_texts = [t for _, t in valid]
        raw_results = self._pipeline(valid_texts, truncation=True, batch_size=32)  # type: ignore[misc]

        results: list[dict] = []
        for raw in raw_results:
            label = raw["label"]
            score = float(raw["score"])
            results.append({
                "label": label.lower(),
                "score": score,
                "sentiment_value": self._map_sentiment_value(label, score),
            })

        return results

    @staticmethod
    def compute_aggregate(scores: list[dict]) -> dict:
        """Compute aggregate statistics from a list of score dicts.

        Args:
            scores: List of dicts as returned by :meth:`score_text` or
                :meth:`score_batch`.

        Returns:
            Dict with keys:
                - ``mean_sentiment`` (float): average sentiment_value
                - ``positive_pct`` (float): fraction of positive labels
                - ``negative_pct`` (float): fraction of negative labels
                - ``neutral_pct`` (float): fraction of neutral labels
                - ``sentiment_velocity`` (float | None): always None here;
                  computed by :class:`SentimentManager` using historical data.
                - ``count`` (int): number of scores aggregated
        """
        if not scores:
            return {
                "mean_sentiment": 0.0,
                "positive_pct": 0.0,
                "negative_pct": 0.0,
                "neutral_pct": 0.0,
                "sentiment_velocity": None,
                "count": 0,
            }

        total = len(scores)
        sentiment_values = [s["sentiment_value"] for s in scores]
        mean_sentiment = sum(sentiment_values) / total

        positive_count = sum(1 for s in scores if s["label"] == "positive")
        negative_count = sum(1 for s in scores if s["label"] == "negative")
        neutral_count = sum(1 for s in scores if s["label"] == "neutral")

        return {
            "mean_sentiment": round(mean_sentiment, 6),
            "positive_pct": round(positive_count / total, 4),
            "negative_pct": round(negative_count / total, 4),
            "neutral_pct": round(neutral_count / total, 4),
            "sentiment_velocity": None,
            "count": total,
        }


# ======================================================================
# SentimentManager — daily update pipeline with feature store integration
# ======================================================================


class SentimentManager:
    """Orchestrates daily sentiment scoring and feature store persistence.

    Fetches headlines via :class:`NewsClient`, scores them with
    :class:`SentimentScorer`, computes an aggregate, derives velocity
    (today vs. yesterday), and persists the ``sentiment_score`` to the
    feature store.

    Args:
        scorer: A :class:`SentimentScorer` instance.
        news_client: A :class:`NewsClient` instance for headline fetching.
        feature_store: An initialised :class:`FeatureStore` for persistence.
    """

    def __init__(
        self,
        scorer: SentimentScorer,
        news_client: NewsClient,
        feature_store: FeatureStore,
    ) -> None:
        self._scorer = scorer
        self._news_client = news_client
        self._feature_store = feature_store

    async def update(self, ticker: str = "SPX") -> dict | None:
        """Fetch headlines, score, aggregate, compute velocity, and persist.

        Args:
            ticker: Ticker symbol for headline search and persistence.

        Returns:
            Aggregate sentiment dict with velocity, or ``None`` if no
            headlines were found.
        """
        # Fetch headlines.
        headlines = await self._news_client.fetch_headlines(ticker=ticker)

        if not headlines:
            logger.info("No headlines for %s — skipping sentiment update", ticker)
            return None

        # Score all headline titles.
        texts = [h["title"] for h in headlines]
        scores = self._scorer.score_batch(texts)

        if not scores:
            logger.warning("All headlines empty after filtering for %s", ticker)
            return None

        # Compute aggregate.
        aggregate = self._scorer.compute_aggregate(scores)

        # Compute velocity vs. yesterday.
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        yesterday_features = await self._feature_store.get_features(ticker, yesterday)

        velocity: float | None = None
        if yesterday_features and yesterday_features.get("sentiment_score") is not None:
            yesterday_sentiment = float(yesterday_features["sentiment_score"])
            velocity = round(aggregate["mean_sentiment"] - yesterday_sentiment, 6)

        aggregate["sentiment_velocity"] = velocity

        # Persist to feature store.
        today = date.today().isoformat()
        await self._feature_store.save_features(
            ticker,
            today,
            {"sentiment_score": aggregate["mean_sentiment"]},
        )

        logger.info(
            "Sentiment update for %s: mean=%.4f, velocity=%s, headlines=%d",
            ticker,
            aggregate["mean_sentiment"],
            velocity,
            aggregate["count"],
        )
        return aggregate

    async def get_current_sentiment(self, ticker: str = "SPX") -> dict | None:
        """Read the latest sentiment score from the feature store.

        Args:
            ticker: Ticker symbol.

        Returns:
            Dict with ``sentiment_score`` key, or ``None`` if no data.
        """
        latest = await self._feature_store.get_latest_features(ticker)
        if latest is None:
            return None

        sentiment_score = latest.get("sentiment_score")
        if sentiment_score is None:
            return None

        return {
            "sentiment_score": float(sentiment_score),
            "date": latest.get("date"),
        }

    async def get_sentiment_history(
        self,
        ticker: str = "SPX",
        days: int = 30,
    ) -> list[dict]:
        """Read sentiment time series from the feature store.

        Args:
            ticker: Ticker symbol.
            days: Number of historical days to retrieve.

        Returns:
            List of dicts with ``date`` and ``sentiment_score`` keys,
            ordered oldest-first.  Entries with ``None`` scores are
            excluded.
        """
        history = await self._feature_store.get_feature_history(
            ticker, "sentiment_score", days=days
        )

        return [
            {"date": dt, "sentiment_score": float(val)}
            for dt, val in history
            if val is not None
        ]
