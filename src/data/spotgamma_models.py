"""SpotGamma data models for key levels, HIRO, and founder's notes.

Pure dataclasses representing SpotGamma market-structure data used by
the ML feature pipeline and Discord cogs.  These are persisted via the
``spotgamma_levels``, ``spotgamma_hiro``, and ``spotgamma_notes``
tables in :mod:`src.db.store`.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SpotGammaLevels:
    """Daily key gamma/delta levels published by SpotGamma.

    Attributes:
        call_wall: Strike with the largest positive gamma (call OI).
        put_wall: Strike with the largest negative gamma (put OI).
        vol_trigger: SpotGamma's gamma flip equivalent -- above this
            level dealers are long gamma and suppress moves; below it
            they are short gamma and amplify moves.
        hedge_wall: Strike where dealer hedging activity is concentrated.
        abs_gamma: Strike with the largest *absolute* gamma exposure,
            regardless of sign.
        timestamp: When the levels were captured.
        ticker: Underlying symbol (default ``"SPX"``).
        source: How the data was ingested -- ``"manual"``, ``"api"``,
            or ``"playwright"``.
    """

    call_wall: float
    put_wall: float
    vol_trigger: float
    hedge_wall: float
    abs_gamma: float
    timestamp: datetime
    ticker: str = "SPX"
    source: str = "manual"


@dataclass
class SpotGammaHIRO:
    """High-frequency Hedging Impact Real-time Overview snapshot.

    HIRO captures the instantaneous dealer-hedging pressure on the
    underlying.  Positive values indicate bullish hedging flows;
    negative values indicate bearish.  Rows are append-only (no upsert)
    because the time-series granularity matters.

    Attributes:
        timestamp: UTC/ET timestamp of the snapshot.
        hedging_impact: Instantaneous hedging pressure (positive = bullish,
            negative = bearish).
        cumulative_impact: Running sum of hedging_impact since market open.
        ticker: Underlying symbol (default ``"SPX"``).
        source: How the data was ingested (default ``"api"``).
    """

    timestamp: datetime
    hedging_impact: float
    cumulative_impact: float
    ticker: str = "SPX"
    source: str = "api"


@dataclass
class SpotGammaNote:
    """Daily SpotGamma founder's note / market commentary.

    Parsed from the daily newsletter or website scrape.  The
    ``key_levels_mentioned`` dict maps human-readable labels (e.g.
    ``"resistance_1"``) to strike prices extracted from the note text.

    Attributes:
        timestamp: Publication time of the note.
        summary: Short plain-text summary of the note.
        key_levels_mentioned: Mapping of label -> strike price extracted
            from the note text.
        market_outlook: Overall directional bias --
            ``"bullish"``, ``"bearish"``, or ``"neutral"``.
        raw_text: Full original text of the note.
    """

    timestamp: datetime
    summary: str
    key_levels_mentioned: dict[str, float] = field(default_factory=dict)
    market_outlook: str = "neutral"
    raw_text: str = ""


__all__ = ["SpotGammaLevels", "SpotGammaHIRO", "SpotGammaNote"]
