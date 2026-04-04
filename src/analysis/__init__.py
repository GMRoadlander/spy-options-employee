"""Analysis engines for SPY/SPX options positioning.

Provides:
- Greeks calculator (Black-Scholes delta, gamma, theta, vega, P(ITM))
- Gamma Exposure (GEX) engine with flip detection and squeeze scoring
- Max Pain calculator
- Put/Call Ratio and dealer positioning classifier
- Strike Intelligence consolidating all engines into key levels
- Analyzer orchestrator producing a single AnalysisResult
"""

from src.analysis.analyzer import AnalysisResult, analyze
from src.analysis.gex import GEXResult, calculate_gex
from src.analysis.greeks import (
    black_scholes_d1_d2,
    black_scholes_delta,
    black_scholes_gamma,
    black_scholes_theta,
    black_scholes_vega,
    probability_itm,
)
from src.analysis.max_pain import (
    MaxPainResult,
    calculate_max_pain,
    calculate_max_pain_all_expiries,
)
from src.analysis.pcr import PCRResult, calculate_pcr
from src.analysis.combo_odds import (
    ComboLeg,
    ComboOddsResult,
    LegResult,
    evaluate_combo,
    simulate_jump_diffusion,
)
from src.analysis.strike_intel import (
    KeyLevel,
    StrikeIntelResult,
    StrikeRecommendation,
    calculate_strike_intel,
)

__all__ = [
    # Orchestrator
    "AnalysisResult",
    "analyze",
    # Greeks
    "black_scholes_d1_d2",
    "black_scholes_delta",
    "black_scholes_gamma",
    "black_scholes_theta",
    "black_scholes_vega",
    "probability_itm",
    # GEX
    "GEXResult",
    "calculate_gex",
    # Max Pain
    "MaxPainResult",
    "calculate_max_pain",
    "calculate_max_pain_all_expiries",
    # PCR
    "PCRResult",
    "calculate_pcr",
    # Strike Intel
    "KeyLevel",
    "StrikeIntelResult",
    "StrikeRecommendation",
    "calculate_strike_intel",
    # Combo Odds
    "ComboLeg",
    "ComboOddsResult",
    "LegResult",
    "evaluate_combo",
    "simulate_jump_diffusion",
]
