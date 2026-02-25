"""Portfolio risk analytics for the paper trading system.

Provides Greeks aggregation, VaR computation, stress testing,
position sizing, risk limits, and circuit breakers -- all operating
on paper positions (no live money).

Public API:
    RiskConfig       -- All risk limit parameters
    RiskManager      -- Pre-trade checks + continuous monitoring
    PortfolioAnalyzer -- Greeks, VaR, concentration analysis
    StressTestEngine -- Scenario-based stress tests
"""

from src.risk.config import RiskConfig
from src.risk.manager import RiskManager
from src.risk.analyzer import PortfolioAnalyzer
from src.risk.stress import StressTestEngine

__all__ = [
    "RiskConfig",
    "RiskManager",
    "PortfolioAnalyzer",
    "StressTestEngine",
]
