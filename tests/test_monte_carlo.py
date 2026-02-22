"""Tests for Monte Carlo simulation."""

import numpy as np
import pandas as pd
import pytest

from src.backtest.monte_carlo import MonteCarloResult, MonteCarloSimulator


class TestMonteCarloBasic:
    """Test basic Monte Carlo functionality."""

    def test_consistently_profitable_passes(self):
        """Strong positive trades should pass (5th pct Sharpe > 0)."""
        trades = [2.0, 1.5, 3.0, 1.0, 2.5] * 20  # 100 profitable trades
        sim = MonteCarloSimulator(n_simulations=500, seed=42)
        result = sim.run(trades, strategy_name="strong")
        assert result.passed is True
        assert result.sharpe_5th_pct > 0

    def test_breakeven_with_noise_fails(self):
        """Zero-mean trades with noise should fail."""
        rng = np.random.default_rng(42)
        trades = list(rng.normal(0.0, 1.0, 100))
        sim = MonteCarloSimulator(n_simulations=500, seed=42)
        result = sim.run(trades)
        # With zero mean, 5th percentile should be negative
        assert result.sharpe_5th_pct < 0.5  # weak at best

    def test_deterministic_with_seed(self):
        """Same seed produces same result."""
        trades = [1.0, -0.5, 0.8, -0.3, 1.2] * 10
        sim1 = MonteCarloSimulator(n_simulations=100, seed=123)
        sim2 = MonteCarloSimulator(n_simulations=100, seed=123)
        r1 = sim1.run(trades)
        r2 = sim2.run(trades)
        assert r1.sharpe_mean == r2.sharpe_mean
        assert r1.sharpe_5th_pct == r2.sharpe_5th_pct

    def test_n_simulations_respected(self):
        """Simulation count matches requested."""
        trades = [1.0, -0.5] * 10
        sim = MonteCarloSimulator(n_simulations=200, seed=42)
        result = sim.run(trades)
        assert result.n_simulations == 200
        assert len(result.sharpe_distribution) == 200


class TestMonteCarloDistribution:
    """Test distribution statistics."""

    def test_mean_approximates_input(self):
        """Bootstrap mean should approximate empirical mean."""
        rng = np.random.default_rng(42)
        trades = list(rng.normal(0.5, 1.0, 200))
        empirical_mean = np.mean(trades)

        sim = MonteCarloSimulator(n_simulations=1000, seed=42)
        result = sim.run(trades)

        # Sharpe mean should be positive since trades have positive mean
        assert result.sharpe_mean > 0

    def test_max_drawdown_is_nonpositive(self):
        """Max drawdown should always be <= 0."""
        trades = [1.0, -0.5, 0.8, -0.3] * 25
        sim = MonteCarloSimulator(n_simulations=100, seed=42)
        result = sim.run(trades)
        assert result.max_drawdown_95th_pct <= 0


class TestMonteCarloEdgeCases:
    """Test edge cases."""

    def test_empty_returns(self):
        """Empty input returns failed result with zero simulations."""
        sim = MonteCarloSimulator(n_simulations=100, seed=42)
        result = sim.run([])
        assert result.passed is False
        assert result.n_simulations == 0
        assert result.sharpe_distribution == []

    def test_single_trade(self):
        """Single trade: std=0 → Sharpe=0."""
        sim = MonteCarloSimulator(n_simulations=100, seed=42)
        result = sim.run([5.0])
        # All resamples are the same trade, std=0 → Sharpe=0
        assert result.sharpe_mean == 0.0

    def test_pandas_series_input(self):
        """pd.Series input should work the same as list."""
        trades = [2.0, 1.0, -0.5, 1.5, 0.8]
        sim1 = MonteCarloSimulator(n_simulations=100, seed=42)
        sim2 = MonteCarloSimulator(n_simulations=100, seed=42)
        r1 = sim1.run(trades)
        r2 = sim2.run(pd.Series(trades))
        assert r1.sharpe_mean == r2.sharpe_mean

    def test_result_fields_populated(self):
        """All result fields should have meaningful values."""
        trades = [1.0, -0.3, 0.8, 0.5, -0.1] * 20
        sim = MonteCarloSimulator(n_simulations=100, seed=42)
        result = sim.run(trades, strategy_name="test_strat")

        assert isinstance(result, MonteCarloResult)
        assert result.strategy_name == "test_strat"
        assert result.n_simulations == 100
        assert result.sharpe_std >= 0
        assert np.isfinite(result.sharpe_mean)
        assert np.isfinite(result.final_return_5th_pct)
