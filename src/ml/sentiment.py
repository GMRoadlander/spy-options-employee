"""FinBERT sentiment scoring for financial news headlines.

Uses the ProsusAI/finbert pre-trained model to classify financial text as
positive, negative, or neutral with confidence scores.  The model is loaded
lazily on first use (~250 MB download) and cached by Hugging Face.

Classes:
    SentimentScorer -- FinBERT wrapper with single/batch scoring and aggregation.

Usage::

    scorer = SentimentScorer()
    result = scorer.score_text("Markets rally on strong earnings")
    print(result)  # {"label": "positive", "score": 0.98, "sentiment_value": 0.98}
"""

from __future__ import annotations

import logging
from typing import Any

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
