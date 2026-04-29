"""SpotGamma data models for key levels, HIRO, and founder's notes.

Pure dataclasses representing SpotGamma market-structure data used by
the ML feature pipeline and Discord cogs.  These are persisted via the
``spotgamma_levels``, ``spotgamma_hiro``, and ``spotgamma_notes``
tables in :mod:`src.db.store`.

Field-name mapping from the live v3/equitiesBySyms response (verified
2026-04-28):
  cws        -> call_wall            (Call Wall strike)
  pws        -> put_wall             (Put Wall strike)
  keyg       -> abs_gamma            (Key Gamma / Absolute Gamma strike)
  maxfs      -> max_future_strike    (Max Future Strike)
  sig        -> sg_implied_1d_move   (1-day implied move, decimal)
  upx        -> spot                 (current underlying price)
  iv_rank    -> iv_rank
  vol_trigger and hedge_wall are NOT in v3/equitiesBySyms; available
  only via /home/keyLevels (currently 403). They remain Optional.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class SpotGammaLevels:
    """Daily key gamma/delta levels published by SpotGamma.

    Attributes:
        call_wall: Strike with the largest positive gamma (call OI).
            Maps from ``cws`` in /v3/equitiesBySyms.
        put_wall: Strike with the largest negative gamma (put OI).
            Maps from ``pws`` in /v3/equitiesBySyms.
        abs_gamma: Strike with the largest absolute gamma exposure.
            Maps from ``keyg`` in /v3/equitiesBySyms.
        timestamp: When the levels were captured.
        vol_trigger: SpotGamma's gamma flip (only available from
            /home/keyLevels which currently 403s -- Optional).
        hedge_wall: Strike where dealer hedging concentrates (Equity
            Hub stock-specific concept; not in /v3/equitiesBySyms for
            SPX -- Optional).
        max_future_strike: Maps from ``maxfs`` in /v3/equitiesBySyms.
        sg_implied_1d_move: Maps from ``sig`` (decimal, e.g. 0.0069 = 0.69%).
        spot: Current underlying price. Maps from ``upx``.
        iv_rank: 0.0-1.0 IV rank for the underlying.
        ticker: Underlying symbol (default ``"SPX"``).
        source: How the data was ingested -- ``"manual"``, ``"api"``,
            or ``"playwright"``.
    """

    call_wall: float
    put_wall: float
    abs_gamma: float
    timestamp: datetime
    vol_trigger: Optional[float] = None
    hedge_wall: Optional[float] = None
    max_future_strike: Optional[float] = None
    sg_implied_1d_move: Optional[float] = None
    spot: Optional[float] = None
    iv_rank: Optional[float] = None
    ticker: str = "SPX"
    source: str = "manual"


def parse_levels_from_v3(
    response: Any,
    ticker: str = "SPX",
    source: str = "api",
) -> Optional[SpotGammaLevels]:
    """Parse a /v3/equitiesBySyms response into SpotGammaLevels.

    The endpoint returns a dict keyed by symbol, e.g.::

        {"SPX": {"cws": 7200, "pws": 6800, "keyg": 7000, ...90 fields...}}

    Returns None if the response is missing the symbol or required fields
    (cws, pws, keyg).
    """
    if not isinstance(response, dict):
        return None
    sym = ticker.upper()
    row = response.get(sym)
    if not isinstance(row, dict):
        return None

    cws = row.get("cws")
    pws = row.get("pws")
    keyg = row.get("keyg")
    if cws is None or pws is None or keyg is None:
        return None

    ts_raw = row.get("trade_date") or row.get("quote_date")
    timestamp: datetime
    if isinstance(ts_raw, str):
        try:
            timestamp = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except ValueError:
            timestamp = datetime.now(timezone.utc)
    else:
        timestamp = datetime.now(timezone.utc)

    return SpotGammaLevels(
        call_wall=float(cws),
        put_wall=float(pws),
        abs_gamma=float(keyg),
        timestamp=timestamp,
        max_future_strike=_to_float(row.get("maxfs")),
        sg_implied_1d_move=_to_float(row.get("sig")),
        spot=_to_float(row.get("upx")),
        iv_rank=_to_float(row.get("iv_rank")),
        ticker=sym,
        source=source,
    )


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


__all__ = ["SpotGammaLevels", "SpotGammaHIRO", "SpotGammaNote", "parse_levels_from_v3"]
