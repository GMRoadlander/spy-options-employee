"""Backtesting engine and anti-overfitting evaluation pipeline.

Contains:
    - data_transform: ORATS → optopsy format conversion
    - engine: Backtesting engine wrapping optopsy
    - metrics: Strategy performance metric calculations
    - wfa: Walk-Forward Analysis
    - cpcv: Combinatorial Purged Cross-Validation
    - dsr: Deflated Sharpe Ratio
    - monte_carlo: Monte Carlo simulation
    - pipeline: Anti-overfitting evaluation pipeline orchestrator
"""
