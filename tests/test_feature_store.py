"""Tests for FeatureStore -- daily ML feature persistence layer.

Uses in-memory SQLite for fast, isolated tests.  Covers save, get,
upsert behaviour, history retrieval, and latest-feature queries.
"""

import pytest
import pytest_asyncio

from src.db.store import Store
from src.ml.feature_store import FeatureStore, FEATURE_COLUMNS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def store():
    """Create an in-memory Store with tables initialised."""
    s = Store(db_path=":memory:")
    await s.init()
    yield s
    await s.close()


@pytest_asyncio.fixture
async def fs(store):
    """Create a FeatureStore backed by the in-memory Store."""
    return FeatureStore(store)


# ---------------------------------------------------------------------------
# Tests: save_features
# ---------------------------------------------------------------------------


class TestSaveFeatures:
    """Tests for save_features method."""

    @pytest.mark.asyncio
    async def test_save_single_feature(self, fs):
        """Saving a single feature creates a retrievable row."""
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 72.3})
        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        assert row["iv_rank"] == pytest.approx(72.3)
        assert row["ticker"] == "SPX"
        assert row["date"] == "2024-06-15"

    @pytest.mark.asyncio
    async def test_save_multiple_features(self, fs):
        """Saving multiple features populates all specified columns."""
        features = {
            "iv_rank": 65.0,
            "iv_percentile": 70.0,
            "skew_25d": 4.2,
            "hurst_exponent": 0.55,
        }
        await fs.save_features("SPY", "2024-06-15", features)
        row = await fs.get_features("SPY", "2024-06-15")
        assert row is not None
        assert row["iv_rank"] == pytest.approx(65.0)
        assert row["iv_percentile"] == pytest.approx(70.0)
        assert row["skew_25d"] == pytest.approx(4.2)
        assert row["hurst_exponent"] == pytest.approx(0.55)

    @pytest.mark.asyncio
    async def test_save_sets_computed_at(self, fs):
        """computed_at timestamp is auto-populated on save."""
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 50.0})
        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        assert row["computed_at"] is not None
        assert "T" in row["computed_at"]  # ISO format

    @pytest.mark.asyncio
    async def test_unset_features_are_null(self, fs):
        """Features not provided in the dict default to NULL."""
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 50.0})
        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        assert row["skew_25d"] is None
        assert row["regime_state"] is None
        assert row["anomaly_score"] is None


# ---------------------------------------------------------------------------
# Tests: upsert behaviour
# ---------------------------------------------------------------------------


class TestUpsert:
    """Tests for ON CONFLICT DO UPDATE (upsert) behaviour."""

    @pytest.mark.asyncio
    async def test_upsert_overwrites_existing(self, fs):
        """Second save for same ticker+date replaces the first."""
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 50.0})
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 75.0})

        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        assert row["iv_rank"] == pytest.approx(75.0)

    @pytest.mark.asyncio
    async def test_upsert_does_not_duplicate_rows(self, fs):
        """Upserting the same key twice should not create two rows."""
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 50.0})
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 75.0})

        history = await fs.get_feature_history("SPX", "iv_rank", days=100)
        assert len(history) == 1

    @pytest.mark.asyncio
    async def test_different_tickers_same_date(self, fs):
        """Different tickers on the same date are separate rows."""
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 50.0})
        await fs.save_features("SPY", "2024-06-15", {"iv_rank": 60.0})

        spx = await fs.get_features("SPX", "2024-06-15")
        spy = await fs.get_features("SPY", "2024-06-15")
        assert spx is not None and spy is not None
        assert spx["iv_rank"] == pytest.approx(50.0)
        assert spy["iv_rank"] == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# Tests: get_features
# ---------------------------------------------------------------------------


class TestGetFeatures:
    """Tests for get_features method."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, fs):
        """Requesting a row that does not exist returns None."""
        result = await fs.get_features("SPX", "1999-01-01")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_all_columns(self, fs):
        """Returned dict includes id, date, ticker, computed_at, and features."""
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 42.0})
        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        assert "id" in row
        assert "date" in row
        assert "ticker" in row
        assert "computed_at" in row
        for col in FEATURE_COLUMNS:
            assert col in row


# ---------------------------------------------------------------------------
# Tests: get_feature_history
# ---------------------------------------------------------------------------


class TestGetFeatureHistory:
    """Tests for get_feature_history method."""

    @pytest.mark.asyncio
    async def test_history_chronological_order(self, fs):
        """History is returned oldest-first."""
        dates = ["2024-06-10", "2024-06-11", "2024-06-12", "2024-06-13", "2024-06-14"]
        for i, d in enumerate(dates):
            await fs.save_features("SPX", d, {"iv_rank": float(i * 10)})

        history = await fs.get_feature_history("SPX", "iv_rank", days=10)
        assert len(history) == 5
        # Oldest first
        assert history[0] == ("2024-06-10", pytest.approx(0.0))
        assert history[-1] == ("2024-06-14", pytest.approx(40.0))

    @pytest.mark.asyncio
    async def test_history_respects_days_limit(self, fs):
        """Only the most recent N days are returned."""
        for i in range(10):
            await fs.save_features("SPX", f"2024-06-{i + 1:02d}", {"iv_rank": float(i)})

        history = await fs.get_feature_history("SPX", "iv_rank", days=3)
        assert len(history) == 3
        # Should be the 3 most recent, in chronological order
        assert history[0][0] == "2024-06-08"
        assert history[1][0] == "2024-06-09"
        assert history[2][0] == "2024-06-10"

    @pytest.mark.asyncio
    async def test_history_invalid_feature_name(self, fs):
        """Invalid feature name returns empty list."""
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 50.0})
        history = await fs.get_feature_history("SPX", "not_a_real_column", days=10)
        assert history == []

    @pytest.mark.asyncio
    async def test_history_empty_for_unknown_ticker(self, fs):
        """Unknown ticker returns empty history."""
        history = await fs.get_feature_history("AAPL", "iv_rank", days=10)
        assert history == []

    @pytest.mark.asyncio
    async def test_history_includes_null_values(self, fs):
        """Rows where the feature is NULL still appear in history."""
        await fs.save_features("SPX", "2024-06-15", {"skew_25d": 3.0})
        # Save a second row without skew_25d (it will be NULL)
        await fs.save_features("SPX", "2024-06-16", {"iv_rank": 50.0})

        history = await fs.get_feature_history("SPX", "skew_25d", days=10)
        assert len(history) == 2
        assert history[0][1] == pytest.approx(3.0)
        assert history[1][1] is None


# ---------------------------------------------------------------------------
# Tests: get_latest_features
# ---------------------------------------------------------------------------


class TestGetLatestFeatures:
    """Tests for get_latest_features method."""

    @pytest.mark.asyncio
    async def test_latest_returns_most_recent_date(self, fs):
        """Latest returns the row with the most recent date."""
        await fs.save_features("SPX", "2024-06-10", {"iv_rank": 30.0})
        await fs.save_features("SPX", "2024-06-15", {"iv_rank": 70.0})

        latest = await fs.get_latest_features("SPX")
        assert latest is not None
        assert latest["date"] == "2024-06-15"
        assert latest["iv_rank"] == pytest.approx(70.0)

    @pytest.mark.asyncio
    async def test_latest_unknown_ticker_returns_none(self, fs):
        """Unknown ticker returns None."""
        result = await fs.get_latest_features("AAPL")
        assert result is None

    @pytest.mark.asyncio
    async def test_latest_scoped_to_ticker(self, fs):
        """Latest only considers rows for the requested ticker."""
        await fs.save_features("SPX", "2024-06-10", {"iv_rank": 30.0})
        await fs.save_features("SPY", "2024-06-15", {"iv_rank": 70.0})

        latest_spx = await fs.get_latest_features("SPX")
        assert latest_spx is not None
        assert latest_spx["date"] == "2024-06-10"
        assert latest_spx["iv_rank"] == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# Tests: Store not initialised
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Tests: partial upsert (ON CONFLICT preserves other columns)
# ---------------------------------------------------------------------------


class TestPartialUpsert:
    """Tests for the ON CONFLICT DO UPDATE SET fix that preserves columns
    written by other ML managers."""

    @pytest.mark.asyncio
    async def test_save_features_partial_update(self, fs):
        """Save regime, then vol for same date — regime columns preserved."""
        await fs.save_features("SPX", "2024-06-15", {
            "regime_state": 1,
            "regime_probability": 0.85,
        })
        await fs.save_features("SPX", "2024-06-15", {
            "vol_forecast_1d": 0.15,
            "vol_forecast_5d": 0.18,
        })

        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        # Regime columns must survive the vol update.
        assert row["regime_state"] == 1
        assert row["regime_probability"] == pytest.approx(0.85)
        # Vol columns must be present.
        assert row["vol_forecast_1d"] == pytest.approx(0.15)
        assert row["vol_forecast_5d"] == pytest.approx(0.18)

    @pytest.mark.asyncio
    async def test_save_features_no_overwrite_existing(self, fs):
        """Save all features, then partial update — untouched columns remain."""
        full = {
            "iv_rank": 72.0,
            "iv_percentile": 80.0,
            "skew_25d": 4.2,
            "regime_state": 0,
            "regime_probability": 0.95,
            "vol_forecast_1d": 0.12,
            "vol_forecast_5d": 0.14,
            "sentiment_score": 0.30,
            "anomaly_score": 0.10,
        }
        await fs.save_features("SPX", "2024-06-15", full)

        # Partial update: only change anomaly_score.
        await fs.save_features("SPX", "2024-06-15", {"anomaly_score": 0.55})

        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        assert row["anomaly_score"] == pytest.approx(0.55)
        # All other columns must be untouched.
        assert row["iv_rank"] == pytest.approx(72.0)
        assert row["regime_state"] == 0
        assert row["vol_forecast_1d"] == pytest.approx(0.12)
        assert row["sentiment_score"] == pytest.approx(0.30)

    @pytest.mark.asyncio
    async def test_save_features_empty_dict_noop(self, fs):
        """Empty features dict does nothing (no row created)."""
        await fs.save_features("SPX", "2024-06-15", {})
        row = await fs.get_features("SPX", "2024-06-15")
        assert row is None


# ---------------------------------------------------------------------------
# Tests: SpotGamma feature columns (Step 12)
# ---------------------------------------------------------------------------


class TestSpotGammaFeatures:
    """Tests for SpotGamma-derived feature columns."""

    @pytest.mark.asyncio
    async def test_spotgamma_columns_in_feature_columns(self):
        """All SpotGamma columns are registered in FEATURE_COLUMNS."""
        sg_cols = [
            "sg_vol_trigger",
            "sg_call_wall",
            "sg_put_wall",
            "sg_abs_gamma",
            "sg_hiro_eod",
            "diy_hiro_eod",
            "gex_sg_agreement",
        ]
        for col in sg_cols:
            assert col in FEATURE_COLUMNS, f"{col} missing from FEATURE_COLUMNS"

    @pytest.mark.asyncio
    async def test_save_spotgamma_features(self, fs):
        """SpotGamma features can be saved and retrieved."""
        sg_features = {
            "sg_vol_trigger": 5250.0,
            "sg_call_wall": 5350.0,
            "sg_put_wall": 5100.0,
            "sg_abs_gamma": 5200.0,
            "sg_hiro_eod": 1500000.0,
            "diy_hiro_eod": 1450000.0,
            "gex_sg_agreement": 1,
        }
        await fs.save_features("SPX", "2024-06-15", sg_features)
        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        assert row["sg_vol_trigger"] == pytest.approx(5250.0)
        assert row["sg_call_wall"] == pytest.approx(5350.0)
        assert row["sg_put_wall"] == pytest.approx(5100.0)
        assert row["sg_abs_gamma"] == pytest.approx(5200.0)
        assert row["sg_hiro_eod"] == pytest.approx(1500000.0)
        assert row["diy_hiro_eod"] == pytest.approx(1450000.0)
        assert row["gex_sg_agreement"] == pytest.approx(1)

    @pytest.mark.asyncio
    async def test_old_features_still_save_with_spotgamma(self, fs):
        """Existing (pre-SpotGamma) features continue to work."""
        old_features = {
            "iv_rank": 72.0,
            "skew_25d": 4.2,
            "regime_state": 1,
            "regime_probability": 0.85,
        }
        await fs.save_features("SPX", "2024-06-15", old_features)
        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        assert row["iv_rank"] == pytest.approx(72.0)
        assert row["skew_25d"] == pytest.approx(4.2)
        assert row["regime_state"] == 1
        assert row["regime_probability"] == pytest.approx(0.85)
        # SpotGamma columns should be NULL when not provided
        assert row["sg_vol_trigger"] is None
        assert row["sg_call_wall"] is None

    @pytest.mark.asyncio
    async def test_mixed_old_and_spotgamma_features(self, fs):
        """Old and SpotGamma features can be saved together."""
        mixed = {
            "iv_rank": 60.0,
            "sg_vol_trigger": 5300.0,
            "sg_call_wall": 5400.0,
            "gex_sg_agreement": 0,
        }
        await fs.save_features("SPX", "2024-06-15", mixed)
        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        assert row["iv_rank"] == pytest.approx(60.0)
        assert row["sg_vol_trigger"] == pytest.approx(5300.0)
        assert row["sg_call_wall"] == pytest.approx(5400.0)
        assert row["gex_sg_agreement"] == pytest.approx(0)

    @pytest.mark.asyncio
    async def test_spotgamma_roundtrip_via_latest(self, fs):
        """Save SpotGamma features, retrieve via get_latest_features."""
        await fs.save_features("SPX", "2024-06-14", {"sg_hiro_eod": 1000000.0})
        await fs.save_features("SPX", "2024-06-15", {"sg_hiro_eod": 2000000.0})

        latest = await fs.get_latest_features("SPX")
        assert latest is not None
        assert latest["date"] == "2024-06-15"
        assert latest["sg_hiro_eod"] == pytest.approx(2000000.0)

    @pytest.mark.asyncio
    async def test_spotgamma_history(self, fs):
        """SpotGamma columns work with get_feature_history."""
        dates = ["2024-06-10", "2024-06-11", "2024-06-12"]
        for i, d in enumerate(dates):
            await fs.save_features("SPX", d, {"sg_vol_trigger": 5200.0 + i * 10})

        history = await fs.get_feature_history("SPX", "sg_vol_trigger", days=10)
        assert len(history) == 3
        assert history[0] == ("2024-06-10", pytest.approx(5200.0))
        assert history[2] == ("2024-06-12", pytest.approx(5220.0))

    @pytest.mark.asyncio
    async def test_partial_upsert_preserves_spotgamma(self, fs):
        """Partial upsert with old features preserves SpotGamma columns."""
        await fs.save_features("SPX", "2024-06-15", {
            "sg_vol_trigger": 5250.0,
            "sg_call_wall": 5350.0,
            "diy_hiro_eod": 1400000.0,
        })
        # Second save with different features — SpotGamma cols must survive.
        await fs.save_features("SPX", "2024-06-15", {
            "iv_rank": 65.0,
            "vol_forecast_1d": 0.15,
        })

        row = await fs.get_features("SPX", "2024-06-15")
        assert row is not None
        assert row["sg_vol_trigger"] == pytest.approx(5250.0)
        assert row["sg_call_wall"] == pytest.approx(5350.0)
        assert row["diy_hiro_eod"] == pytest.approx(1400000.0)
        assert row["iv_rank"] == pytest.approx(65.0)
        assert row["vol_forecast_1d"] == pytest.approx(0.15)

    @pytest.mark.asyncio
    async def test_gex_sg_agreement_binary(self, fs):
        """gex_sg_agreement stores 0/1 values correctly."""
        await fs.save_features("SPX", "2024-06-15", {"gex_sg_agreement": 1})
        await fs.save_features("SPX", "2024-06-16", {"gex_sg_agreement": 0})

        row1 = await fs.get_features("SPX", "2024-06-15")
        row2 = await fs.get_features("SPX", "2024-06-16")
        assert row1 is not None and row2 is not None
        assert row1["gex_sg_agreement"] == pytest.approx(1)
        assert row2["gex_sg_agreement"] == pytest.approx(0)


class TestStoreNotInitialised:
    """Tests for calling FeatureStore on an uninitialised Store."""

    @pytest.mark.asyncio
    async def test_raises_on_uninitialised_store(self):
        """FeatureStore raises RuntimeError if Store.init() was not called."""
        store = Store(db_path=":memory:")
        fs = FeatureStore(store)
        with pytest.raises(RuntimeError, match="not initialized"):
            await fs.get_features("SPX", "2024-06-15")
