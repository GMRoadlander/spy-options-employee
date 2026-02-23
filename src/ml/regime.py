"""HMM-based regime detection for SPX options trading.

Uses a Gaussian Hidden Markov Model to classify market regimes based on
daily returns and VIX levels.  States are sorted by volatility so that
labels are consistent across refits:

- State 0: **risk-on** (lowest volatility)
- State 1: **risk-off** (highest vol for 2-state, medium for 3-state)
- State 2: **crisis** (highest vol, 3-state only)

Classes:
    RegimeDetector -- core HMM fitting, prediction, and persistence.
    RegimeManager  -- daily update pipeline with feature store integration.

Usage::

    detector = RegimeDetector(n_states=2)
    detector.fit(returns, vix)
    result = detector.predict(returns, vix)
    print(result["state_name"])  # "risk-on" or "risk-off"
"""

from __future__ import annotations

import logging
import os
import pickle
from datetime import date, datetime
from typing import TYPE_CHECKING

import numpy as np
from hmmlearn.hmm import GaussianHMM

if TYPE_CHECKING:
    from src.ml.feature_store import FeatureStore

logger = logging.getLogger(__name__)

# Minimum number of observations required for a valid HMM fit (1 trading year).
MIN_OBSERVATIONS = 252

# State name lookup by (n_states, state_index).
_STATE_NAMES: dict[tuple[int, int], str] = {
    (2, 0): "risk-on",
    (2, 1): "risk-off",
    (3, 0): "risk-on",
    (3, 1): "risk-off",
    (3, 2): "crisis",
}


class RegimeDetector:
    """Gaussian HMM regime detector for market state classification.

    Fits a :class:`hmmlearn.hmm.GaussianHMM` on a 2-D feature matrix
    of ``[daily_returns, vix_level]`` and provides prediction utilities
    with consistent state labelling.

    Args:
        n_states: Number of hidden states (2 or 3).
        random_state: Random seed for reproducibility.
    """

    def __init__(self, n_states: int = 2, random_state: int = 42) -> None:
        if n_states not in (2, 3):
            raise ValueError(f"n_states must be 2 or 3, got {n_states}")

        self.n_states = n_states
        self.random_state = random_state

        self.model: GaussianHMM | None = None
        self._fitted = False

        # Standardisation parameters (mean, std for each feature column).
        self._feature_mean: np.ndarray | None = None
        self._feature_std: np.ndarray | None = None

        # Permutation mapping from raw HMM state to sorted state.
        self._state_perm: np.ndarray | None = None

        # Number of training observations (for BIC computation).
        self._n_train_obs: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self, returns: np.ndarray, vix: np.ndarray) -> None:
        """Fit the HMM on daily returns and VIX levels.

        Features are standardised before fitting.  After fitting, states
        are re-ordered by ascending variance of the first feature
        (returns) so that state 0 is always the lowest-volatility regime.

        Args:
            returns: 1-D array of daily log or simple returns.
            vix: 1-D array of daily VIX closing levels.

        Raises:
            ValueError: If fewer than :data:`MIN_OBSERVATIONS` are provided
                or array lengths do not match.
        """
        returns = np.asarray(returns, dtype=np.float64).ravel()
        vix = np.asarray(vix, dtype=np.float64).ravel()

        if len(returns) != len(vix):
            raise ValueError(
                f"returns and vix must have the same length, got {len(returns)} and {len(vix)}"
            )
        if len(returns) < MIN_OBSERVATIONS:
            raise ValueError(
                f"Need at least {MIN_OBSERVATIONS} observations, got {len(returns)}"
            )

        X = self._build_features(returns, vix)
        self._n_train_obs = len(returns)

        # Standardise and store scaler params.
        self._feature_mean = X.mean(axis=0)
        self._feature_std = X.std(axis=0)
        # Prevent division by zero.
        self._feature_std[self._feature_std == 0] = 1.0
        X_scaled = (X - self._feature_mean) / self._feature_std

        # Fit HMM.
        hmm = GaussianHMM(
            n_components=self.n_states,
            covariance_type="full",
            n_iter=200,
            random_state=self.random_state,
            tol=1e-4,
        )
        hmm.fit(X_scaled)

        # Sort states by variance of the first feature (returns) — ascending.
        variances = np.array(
            [hmm.covars_[s][0, 0] for s in range(self.n_states)]
        )
        self._state_perm = np.argsort(variances)  # index[i] = raw state for sorted state i

        self.model = hmm
        self._fitted = True
        logger.info(
            "HMM fitted with %d states on %d observations",
            self.n_states,
            len(returns),
        )

    def predict(self, returns: np.ndarray, vix: np.ndarray) -> dict:
        """Predict the current regime from a sequence of observations.

        Uses the last observation's filtered probability as the current
        regime estimate.

        Args:
            returns: 1-D array of daily returns (same scale as training).
            vix: 1-D array of daily VIX levels.

        Returns:
            Dict with keys:
                - ``state`` (int): sorted state index
                - ``state_name`` (str): human-readable label
                - ``probabilities`` (list[float]): P(state) for each state
                - ``transition_matrix`` (list[list[float]]): sorted transition probs
                - ``expected_duration`` (dict[str, float]): expected days in each regime

        Raises:
            RuntimeError: If the model has not been fitted.
            ValueError: If array lengths do not match.
        """
        self._check_fitted()
        returns = np.asarray(returns, dtype=np.float64).ravel()
        vix = np.asarray(vix, dtype=np.float64).ravel()

        if len(returns) != len(vix):
            raise ValueError(
                f"returns and vix must have the same length, got {len(returns)} and {len(vix)}"
            )

        X = self._build_features(returns, vix)
        X_scaled = (X - self._feature_mean) / self._feature_std

        # Filtered state probabilities for the full sequence.
        raw_probs = self.model.predict_proba(X_scaled)  # (T, n_states)
        last_raw_probs = raw_probs[-1]  # last timestep

        # Re-order probabilities to sorted state order.
        sorted_probs = self._permute_probs(last_raw_probs)
        state = int(np.argmax(sorted_probs))
        state_name = _STATE_NAMES.get((self.n_states, state), f"state-{state}")

        # Transition matrix in sorted state order.
        sorted_transmat = self._permute_transmat()

        # Expected durations: 1 / (1 - P(stay in state)).
        expected_duration: dict[str, float] = {}
        for s in range(self.n_states):
            s_name = _STATE_NAMES.get((self.n_states, s), f"state-{s}")
            p_stay = sorted_transmat[s][s]
            dur = 1.0 / (1.0 - p_stay) if p_stay < 1.0 else float("inf")
            expected_duration[s_name] = round(dur, 1)

        return {
            "state": state,
            "state_name": state_name,
            "probabilities": [round(float(p), 6) for p in sorted_probs],
            "transition_matrix": sorted_transmat,
            "expected_duration": expected_duration,
        }

    def select_n_states(
        self,
        returns: np.ndarray,
        vix: np.ndarray,
        candidates: list[int] | None = None,
    ) -> int:
        """Select the best number of states via BIC.

        Fits a separate :class:`RegimeDetector` for each candidate and
        returns the ``n_states`` with the lowest BIC score.

        Args:
            returns: 1-D array of daily returns.
            vix: 1-D array of daily VIX levels.
            candidates: List of n_states to try (default ``[2, 3]``).

        Returns:
            The ``n_states`` with the lowest BIC.
        """
        if candidates is None:
            candidates = [2, 3]

        returns = np.asarray(returns, dtype=np.float64).ravel()
        vix = np.asarray(vix, dtype=np.float64).ravel()

        best_n: int = candidates[0]
        best_bic: float = float("inf")

        for n in candidates:
            try:
                det = RegimeDetector(n_states=n, random_state=self.random_state)
                det.fit(returns, vix)
                bic = det._compute_bic()
                logger.info("BIC for %d states: %.2f", n, bic)
                if bic < best_bic:
                    best_bic = bic
                    best_n = n
            except Exception:
                logger.warning("Failed to fit HMM with %d states", n, exc_info=True)

        return best_n

    def save(self, path: str) -> None:
        """Serialize the fitted model to *path* using pickle.

        Args:
            path: Filesystem path for the pickle file.

        Raises:
            RuntimeError: If the model has not been fitted.
        """
        self._check_fitted()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        payload = {
            "n_states": self.n_states,
            "random_state": self.random_state,
            "model": self.model,
            "feature_mean": self._feature_mean,
            "feature_std": self._feature_std,
            "state_perm": self._state_perm,
            "n_train_obs": self._n_train_obs,
        }
        with open(path, "wb") as fh:
            pickle.dump(payload, fh)
        logger.info("Saved regime model to %s", path)

    def load(self, path: str) -> None:
        """Deserialize a fitted model from *path*.

        Args:
            path: Filesystem path of the pickle file.

        Raises:
            FileNotFoundError: If *path* does not exist.
        """
        with open(path, "rb") as fh:
            payload = pickle.load(fh)  # noqa: S301

        self.n_states = payload["n_states"]
        self.random_state = payload["random_state"]
        self.model = payload["model"]
        self._feature_mean = payload["feature_mean"]
        self._feature_std = payload["feature_std"]
        self._state_perm = payload["state_perm"]
        self._n_train_obs = payload.get("n_train_obs", 0)
        self._fitted = True
        logger.info("Loaded regime model from %s (%d states)", path, self.n_states)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_features(returns: np.ndarray, vix: np.ndarray) -> np.ndarray:
        """Stack returns and VIX into a (T, 2) feature matrix."""
        return np.column_stack([returns, vix])

    def _check_fitted(self) -> None:
        if not self._fitted or self.model is None:
            raise RuntimeError("Model has not been fitted. Call fit() first.")

    def _permute_probs(self, raw_probs: np.ndarray) -> list[float]:
        """Re-order raw state probabilities into sorted order."""
        assert self._state_perm is not None
        sorted_probs = np.zeros(self.n_states)
        for sorted_idx, raw_idx in enumerate(self._state_perm):
            sorted_probs[sorted_idx] = raw_probs[raw_idx]
        return sorted_probs.tolist()

    def _permute_transmat(self) -> list[list[float]]:
        """Re-order the transition matrix into sorted state order."""
        assert self.model is not None and self._state_perm is not None
        raw = self.model.transmat_
        n = self.n_states
        sorted_mat = np.zeros((n, n))
        for si in range(n):
            for sj in range(n):
                sorted_mat[si, sj] = raw[self._state_perm[si], self._state_perm[sj]]
        return [[round(float(v), 6) for v in row] for row in sorted_mat]

    def _compute_bic(self) -> float:
        """Compute the Bayesian Information Criterion for the fitted model.

        BIC = -2 * log_likelihood + k * ln(T)

        where k is the number of free parameters.
        """
        self._check_fitted()
        assert self._feature_mean is not None and self._feature_std is not None

        # Number of free parameters for GaussianHMM with full covariance:
        # start probs: n-1, transmat: n*(n-1), means: n*d, covars: n*d*(d+1)/2
        n = self.n_states
        d = 2  # feature dimension
        k = (n - 1) + n * (n - 1) + n * d + n * d * (d + 1) // 2

        # Score gives per-sample average log-likelihood; multiply by T.
        # hmmlearn's score() returns the total log-likelihood.
        # We need the training data to compute score, but we don't store it.
        # Use model.score on dummy — but actually we need the original data.
        # Instead use the model's internal score from the last fit.
        # hmmlearn stores monitor_.history which has the final log-likelihood.
        if hasattr(self.model, "monitor_") and self.model.monitor_.history:
            ll = self.model.monitor_.history[-1]
        else:
            # Fallback: can't compute BIC without log-likelihood.
            return float("inf")

        # We don't have T stored, so estimate from the monitor.
        # Actually, the log-likelihood from hmmlearn IS the total LL.
        # We need T for BIC; store it during fit.
        # For now, use a rough estimate.  We'll fix this properly.
        # The log-likelihood is already the total for all observations.
        # We just need T for the penalty term.
        # Store T during fit -- let's use an attribute.
        t = getattr(self, "_n_train_obs", 1000)
        bic = -2.0 * ll + k * np.log(t)
        return float(bic)
