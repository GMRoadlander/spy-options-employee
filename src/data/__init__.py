"""Data layer for SPY/SPX options analysis.

Provides OptionContract and OptionsChain dataclasses used across all data sources,
plus client classes for CBOE CDN and Tradier sandbox API.
"""

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class OptionContract:
    """A single options contract with pricing and greeks."""

    ticker: str
    expiry: date
    strike: float
    option_type: str  # "call" or "put"
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    iv: float  # implied volatility as decimal (0.15 = 15%)
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0

    @property
    def mid(self) -> float:
        """Mid-price between bid and ask."""
        return (self.bid + self.ask) / 2.0

    @property
    def spread(self) -> float:
        """Bid-ask spread."""
        return self.ask - self.bid

    @property
    def is_call(self) -> bool:
        return self.option_type == "call"

    @property
    def is_put(self) -> bool:
        return self.option_type == "put"

    @property
    def days_to_expiry(self) -> int:
        """Calendar days until expiration from today."""
        return (self.expiry - date.today()).days


@dataclass
class OptionsChain:
    """Full options chain for a single ticker at a point in time."""

    ticker: str
    spot_price: float
    timestamp: datetime
    contracts: list[OptionContract] = field(default_factory=list)
    source: str = "cboe"
    data_quality: str = "ok"  # "ok", "degraded", "unusable"

    @property
    def calls(self) -> list[OptionContract]:
        """All call contracts."""
        return [c for c in self.contracts if c.is_call]

    @property
    def puts(self) -> list[OptionContract]:
        """All put contracts."""
        return [c for c in self.contracts if c.is_put]

    @property
    def expirations(self) -> list[date]:
        """Sorted list of unique expiration dates."""
        return sorted(set(c.expiry for c in self.contracts))

    @property
    def strikes(self) -> list[float]:
        """Sorted list of unique strike prices."""
        return sorted(set(c.strike for c in self.contracts))

    def for_expiry(self, expiry: date) -> list[OptionContract]:
        """Filter contracts for a specific expiration date."""
        return [c for c in self.contracts if c.expiry == expiry]

    def nearest_expiry(self) -> date | None:
        """Return the nearest future expiration date, or None if no contracts.

        Skips expiration dates that are in the past (before today).
        If all expirations are past, returns the most recent one as a fallback.
        """
        today = date.today()
        exps = self.expirations
        if not exps:
            return None
        future = [e for e in exps if e >= today]
        if future:
            return future[0]
        return exps[-1]  # fallback: most recent past expiry


__all__ = ["OptionContract", "OptionsChain"]
