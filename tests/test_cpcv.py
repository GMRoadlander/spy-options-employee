"""Tests for CPCV (Combinatorial Purged Cross-Validation)."""

import numpy as np
import pytest

from src.backtest.cpcv import CPCVAnalyzer, CPCVResult, _sharpe_from_returns


class TestSharpeHelper:
    """Test internal Sharpe calculation."""

    def test_positive_returns(self):
        returns = np.array([0.01] * 100)
        sharpe = _sharpe_from_returns(returns)
        # Constant positive returns → very high Sharpe (near-zero std)
        assert sharpe > 0

    def test_varying_positive_returns(self):
        rng = np.random.default_rng(42)
        returns = rng.normal(0.001, 0.01, 252)
        sharpe = _sharpe_from_returns(returns)
        assert sharpe > 0

    def test_empty_returns(self):
        assert _sharpe_from_returns(np.array([])) == 0.0

    def test_single_return(self):
        assert _sharpe_from_returns(np.array([1.0])) == 0.0


class TestCPCVAnalyzer:
    """Test CPCV analyzer."""

    def test_strong_strategy_passes(self):
        """Consistently profitable strategy should have PBO < 0.50."""
        rng = np.random.default_rng(42)
        # Strong positive mean with moderate vol
        returns = rng.normal(0.002, 0.01, 500)
        analyzer = CPCVAnalyzer(n_folds=5, n_test_folds=1, purge_days=5, embargo_days=2)
        result = analyzer.run(returns, strategy_name="strong")

        assert result.passed is True
        assert result.pbo < 0.50
        assert result.n_paths > 0

    def test_random_strategy_likely_fails(self):
        """Zero-mean returns should have high PBO (many paths negative)."""
        rng = np.random.default_rng(123)
        returns = rng.normal(0.0, 0.01, 500)
        analyzer = CPCVAnalyzer(n_folds=5, n_test_folds=1, purge_days=5, embargo_days=2)
        result = analyzer.run(returns, strategy_name="random")

        # With zero mean, roughly half paths should be negative
        assert result.pbo >= 0.30  # at least 30% negative

    def test_purge_size_enforcement(self):
        """Purge days should be configurable."""
        analyzer = CPCVAnalyzer(purge_days=45)
        assert analyzer._purge_days == 45

    def test_pbo_range(self):
        """PBO should be between 0 and 1."""
        rng = np.random.default_rng(42)
        returns = rng.normal(0.001, 0.01, 500)
        analyzer = CPCVAnalyzer(n_folds=5, n_test_folds=1, purge_days=5, embargo_days=2)
        result = analyzer.run(returns)

        assert 0.0 <= result.pbo <= 1.0

    def test_insufficient_data(self):
        """Too few data points should return failed result."""
        returns = [0.01] * 10  # way too few
        analyzer = CPCVAnalyzer(n_folds=10)
        result = analyzer.run(returns)

        assert result.passed is False
        assert result.pbo == 1.0
        assert result.n_paths == 0

    def test_n_paths_matches_combinations(self):
        """Number of paths should match C(n_folds, n_test_folds)."""
        rng = np.random.default_rng(42)
        returns = rng.normal(0.001, 0.01, 500)
        analyzer = CPCVAnalyzer(n_folds=5, n_test_folds=2, purge_days=5, embargo_days=2)
        result = analyzer.run(returns)

        # C(5, 2) = 10
        assert result.n_paths == 10

    def test_sharpe_distribution_length(self):
        """Sharpe distribution should have one entry per path."""
        rng = np.random.default_rng(42)
        returns = rng.normal(0.001, 0.01, 500)
        analyzer = CPCVAnalyzer(n_folds=5, n_test_folds=1, purge_days=5, embargo_days=2)
        result = analyzer.run(returns)

        assert len(result.sharpe_distribution) == result.n_paths

    def test_max_paths_cap(self):
        """Should cap combinatorial explosion."""
        rng = np.random.default_rng(42)
        returns = rng.normal(0.001, 0.01, 1000)
        analyzer = CPCVAnalyzer(n_folds=20, n_test_folds=2, purge_days=5, embargo_days=2)
        # C(20, 2) = 190, set max_paths=50
        result = analyzer.run(returns, max_paths=50)

        assert result.n_paths <= 50
