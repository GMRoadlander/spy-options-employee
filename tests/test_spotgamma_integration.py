"""End-to-end integration tests for the SpotGamma pipeline.

Verifies the full data flow: manual input -> store -> reconciliation ->
feature store, as well as HIRO pipeline, embed generation, and graceful
degradation when SpotGamma data is unavailable.

All tests use in-memory SQLite and synthetic data.  No real network,
browser, or Discord calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from src.data.spotgamma_models import SpotGammaHIRO, SpotGammaLevels
from src.data.spotgamma_store import SpotGammaStore
from src.db.store import Store
from src.ml.feature_store import FeatureStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def store():
    """Create an in-memory Store with all tables initialised."""
    s = Store(db_path=":memory:")
    await s.init()
    yield s
    await s.close()


@pytest_asyncio.fixture
async def sg(store):
    """SpotGammaStore backed by the in-memory Store."""
    return SpotGammaStore(store)


@pytest_asyncio.fixture
async def fs(store):
    """FeatureStore backed by the in-memory Store."""
    return FeatureStore(store)


# ---------------------------------------------------------------------------
# Lightweight stand-ins (avoid coupling to full GEX/HIRO internals)
# ---------------------------------------------------------------------------


@dataclass
class _FakeGEXResult:
    """Mimics src.analysis.gex.GEXResult with only the reconciliation fields."""

    gamma_flip: float | None
    gamma_ceiling: float | None
    gamma_floor: float | None
    net_gex: float = 0.0
    squeeze_probability: float = 0.0
    gex_by_expiry: dict[str, float] | None = None


# ---------------------------------------------------------------------------
# Test 1: Manual Input -> Store -> Retrieve
# ---------------------------------------------------------------------------


class TestManualInputStoreRetrieve:
    """Simulate /spotgamma set -> save -> get_latest_levels round-trip."""

    @pytest.mark.asyncio
    async def test_manual_levels_round_trip(self, sg):
        levels = SpotGammaLevels(
            call_wall=5900.0,
            put_wall=5700.0,
            vol_trigger=5800.0,
            hedge_wall=5850.0,
            abs_gamma=5825.0,
            timestamp=datetime(2026, 4, 6, 9, 30),
            ticker="SPX",
            source="manual",
        )
        await sg.save_levels(levels)

        result = await sg.get_latest_levels("SPX")
        assert result is not None
        assert result.call_wall == pytest.approx(5900.0)
        assert result.put_wall == pytest.approx(5700.0)
        assert result.vol_trigger == pytest.approx(5800.0)
        assert result.hedge_wall == pytest.approx(5850.0)
        assert result.abs_gamma == pytest.approx(5825.0)
        assert result.ticker == "SPX"
        assert result.source == "manual"
        assert result.timestamp == datetime(2026, 4, 6, 9, 30)


# ---------------------------------------------------------------------------
# Test 2: Levels -> Reconciliation -> Agreement
# ---------------------------------------------------------------------------


class TestLevelsReconciliationAgreement:
    """SpotGamma levels agree with our GEX levels within threshold."""

    def test_within_threshold_is_agreement(self):
        from src.analysis.reconciliation import reconcile_levels

        sg_levels = SpotGammaLevels(
            call_wall=5900.0,
            put_wall=5700.0,
            vol_trigger=5800.0,
            hedge_wall=5850.0,
            abs_gamma=5825.0,
            timestamp=datetime(2026, 4, 6, 9, 30),
        )
        gex = _FakeGEXResult(
            gamma_flip=5812.0,       # 12 pts from vol_trigger -> within 15
            gamma_ceiling=5905.0,    # 5 pts from call_wall -> within 15
            gamma_floor=5690.0,      # 10 pts from put_wall -> within 15
        )

        result = reconcile_levels(sg_levels, gex, threshold=15.0)

        assert result.agreement_count == 3
        assert result.conflict_count == 0
        assert result.agreement_ratio == pytest.approx(1.0)
        assert result.confidence_adjustment == pytest.approx(1.0)
        assert "3/3" in result.summary


# ---------------------------------------------------------------------------
# Test 3: Levels -> Reconciliation -> Conflict
# ---------------------------------------------------------------------------


class TestLevelsReconciliationConflict:
    """SpotGamma levels conflict with our GEX (50pt difference)."""

    def test_large_difference_is_conflict(self):
        from src.analysis.reconciliation import reconcile_levels

        sg_levels = SpotGammaLevels(
            call_wall=5900.0,
            put_wall=5700.0,
            vol_trigger=5800.0,
            hedge_wall=5850.0,
            abs_gamma=5825.0,
            timestamp=datetime(2026, 4, 6, 9, 30),
        )
        gex = _FakeGEXResult(
            gamma_flip=5850.0,       # 50 pts from vol_trigger -> conflict
            gamma_ceiling=5950.0,    # 50 pts from call_wall -> conflict
            gamma_floor=5650.0,      # 50 pts from put_wall -> conflict
        )

        result = reconcile_levels(sg_levels, gex, threshold=15.0)

        assert result.agreement_count == 0
        assert result.conflict_count == 3
        assert result.agreement_ratio == pytest.approx(0.0)
        assert result.confidence_adjustment == pytest.approx(0.5)
        assert "CONFLICT" in result.summary


# ---------------------------------------------------------------------------
# Test 4: HIRO Pipeline
# ---------------------------------------------------------------------------


class TestHIROPipeline:
    """Process synthetic trades through DIY HIRO, compare with SG HIRO."""

    def test_direction_agreement(self):
        from src.analysis.hiro import DIYHIROCalculator
        from src.analysis.reconciliation import reconcile_hiro

        # Build DIY HIRO from synthetic call-buy trades
        calc = DIYHIROCalculator(
            window_minutes=5,
            underlying_price=600.0,
            risk_free_rate=0.05,
            default_iv=0.20,
            default_dte_years=30.0 / 365.0,
        )
        ts = 1_700_000_000_000
        for i in range(5):
            calc.process_trade({
                "ticker": "O:SPY251219C00600000",
                "price": 5.20,
                "size": 10,
                "bid": 4.80,
                "ask": 5.20,
                "timestamp": ts + i * 1000,
            })
        diy_result = calc.get_current()

        # DIY should be bullish (positive hedging_impact)
        assert diy_result.hedging_impact > 0

        # SpotGamma HIRO also bullish
        sg_hiro = SpotGammaHIRO(
            timestamp=datetime(2026, 4, 6, 10, 0),
            hedging_impact=0.4,
            cumulative_impact=2.5,
        )

        reconciled = reconcile_hiro(sg_hiro, diy_result)

        # Direction should agree (both positive)
        direction_comp = reconciled.level_comparisons[0]
        assert direction_comp.name == "HIRO Direction"
        assert direction_comp.agrees is True
        assert reconciled.agreement_count >= 1


# ---------------------------------------------------------------------------
# Test 5: Feature Store Integration
# ---------------------------------------------------------------------------


class TestFeatureStoreIntegration:
    """Save SpotGamma-derived features and retrieve them."""

    @pytest.mark.asyncio
    async def test_spotgamma_features_round_trip(self, sg, fs):
        # Step 1: Save SpotGamma levels to store
        levels = SpotGammaLevels(
            call_wall=5900.0,
            put_wall=5700.0,
            vol_trigger=5800.0,
            hedge_wall=5850.0,
            abs_gamma=5825.0,
            timestamp=datetime(2026, 4, 6, 9, 30),
        )
        await sg.save_levels(levels)

        # Step 2: Extract level values and save to feature store
        retrieved = await sg.get_latest_levels("SPX")
        assert retrieved is not None

        features = {
            "sg_vol_trigger": retrieved.vol_trigger,
            "sg_call_wall": retrieved.call_wall,
            "sg_put_wall": retrieved.put_wall,
            "sg_abs_gamma": retrieved.abs_gamma,
        }
        await fs.save_features("SPX", "2026-04-06", features)

        # Step 3: Retrieve from feature store and verify
        row = await fs.get_features("SPX", "2026-04-06")
        assert row is not None
        assert row["sg_vol_trigger"] == pytest.approx(5800.0)
        assert row["sg_call_wall"] == pytest.approx(5900.0)
        assert row["sg_put_wall"] == pytest.approx(5700.0)
        assert row["sg_abs_gamma"] == pytest.approx(5825.0)


# ---------------------------------------------------------------------------
# Test 6: Multi-Expiry GEX + Reconciliation
# ---------------------------------------------------------------------------


class TestMultiExpiryGEXReconciliation:
    """Reconcile with a GEX result that includes gex_by_expiry."""

    def test_reconcile_with_expiry_breakdown(self):
        from src.analysis.reconciliation import reconcile_levels

        sg_levels = SpotGammaLevels(
            call_wall=5900.0,
            put_wall=5700.0,
            vol_trigger=5800.0,
            hedge_wall=5850.0,
            abs_gamma=5825.0,
            timestamp=datetime(2026, 4, 6, 9, 30),
        )
        gex = _FakeGEXResult(
            gamma_flip=5805.0,
            gamma_ceiling=5895.0,
            gamma_floor=5710.0,
            net_gex=1_500_000_000.0,
            gex_by_expiry={
                "2026-04-07": 800_000_000.0,
                "2026-04-09": 400_000_000.0,
                "2026-04-11": 300_000_000.0,
            },
        )

        result = reconcile_levels(sg_levels, gex)

        # All three levels agree (within 15 pts)
        assert result.agreement_count == 3
        assert result.confidence_adjustment == pytest.approx(1.0)

        # gex_by_expiry is preserved on the GEX result (pipeline passes it through)
        assert gex.gex_by_expiry is not None
        assert len(gex.gex_by_expiry) == 3


# ---------------------------------------------------------------------------
# Test 7: Full Pipeline -- Manual to Feature Store
# ---------------------------------------------------------------------------


class TestFullPipelineManualToFeatureStore:
    """Complete flow: manual levels -> store -> reconcile -> feature store."""

    @pytest.mark.asyncio
    async def test_end_to_end(self, sg, fs):
        from src.analysis.reconciliation import reconcile_levels

        # Stage 1: Manual input -> store
        levels = SpotGammaLevels(
            call_wall=5900.0,
            put_wall=5700.0,
            vol_trigger=5800.0,
            hedge_wall=5850.0,
            abs_gamma=5825.0,
            timestamp=datetime(2026, 4, 6, 9, 30),
            source="manual",
        )
        await sg.save_levels(levels)

        # Stage 2: Retrieve from store
        stored_levels = await sg.get_latest_levels("SPX")
        assert stored_levels is not None
        assert stored_levels.vol_trigger == pytest.approx(5800.0)

        # Stage 3: Reconcile with GEX
        gex = _FakeGEXResult(
            gamma_flip=5808.0,
            gamma_ceiling=5903.0,
            gamma_floor=5695.0,
        )
        reconciled = reconcile_levels(stored_levels, gex)
        assert reconciled.agreement_count == 3
        assert reconciled.confidence_adjustment == pytest.approx(1.0)

        # Stage 4: Save SpotGamma + reconciliation results to feature store
        features = {
            "sg_vol_trigger": stored_levels.vol_trigger,
            "sg_call_wall": stored_levels.call_wall,
            "sg_put_wall": stored_levels.put_wall,
            "sg_abs_gamma": stored_levels.abs_gamma,
            "gex_sg_agreement": reconciled.agreement_ratio,
        }
        await fs.save_features("SPX", "2026-04-06", features)

        # Stage 5: Verify feature store has everything
        row = await fs.get_features("SPX", "2026-04-06")
        assert row is not None
        assert row["sg_vol_trigger"] == pytest.approx(5800.0)
        assert row["sg_call_wall"] == pytest.approx(5900.0)
        assert row["gex_sg_agreement"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Test 8: Graceful Degradation -- No SpotGamma
# ---------------------------------------------------------------------------


class TestGracefulDegradationNoSpotGamma:
    """System produces a valid result when SpotGamma data is unavailable."""

    def test_reconcile_with_none_sg_levels(self):
        from src.analysis.reconciliation import reconcile_levels

        gex = _FakeGEXResult(
            gamma_flip=5800.0,
            gamma_ceiling=5900.0,
            gamma_floor=5700.0,
        )

        result = reconcile_levels(None, gex)

        assert result.agreement_count == 0
        assert result.conflict_count == 3
        # All comparisons disagree because SG side is None
        for comp in result.level_comparisons:
            assert comp.sg_value is None
            assert comp.agrees is False
        # Confidence is degraded but not below 0.5
        assert result.confidence_adjustment >= 0.5
        assert "unavailable" in result.summary.lower()

    def test_reconcile_with_none_both(self):
        from src.analysis.reconciliation import reconcile_levels

        result = reconcile_levels(None, None)

        assert result.agreement_count == 0
        assert result.conflict_count == 0
        assert result.confidence_adjustment == 0.0
        assert "unavailable" in result.summary.lower()


# ---------------------------------------------------------------------------
# Test 9: Embed Generation
# ---------------------------------------------------------------------------


class TestEmbedGeneration:
    """Build SpotGamma embeds and verify structure."""

    def test_levels_embed_has_expected_fields(self):
        from src.discord_bot.embeds import build_spotgamma_levels_embed

        levels = SpotGammaLevels(
            call_wall=5900.0,
            put_wall=5700.0,
            vol_trigger=5800.0,
            hedge_wall=5850.0,
            abs_gamma=5825.0,
            timestamp=datetime(2026, 4, 6, 9, 30, tzinfo=timezone.utc),
            ticker="SPX",
            source="manual",
        )

        embed = build_spotgamma_levels_embed(levels)

        assert embed.title is not None
        assert "SPX" in embed.title

        # Should have fields for all five levels + source
        field_names = [f.name for f in embed.fields]
        assert "Call Wall" in field_names
        assert "Put Wall" in field_names
        assert "Vol Trigger" in field_names
        assert "Hedge Wall" in field_names
        assert "Abs Gamma" in field_names
        assert "Source" in field_names

        # Source field should say "manual"
        source_field = next(f for f in embed.fields if f.name == "Source")
        assert "manual" in source_field.value

    def test_comparison_embed_has_expected_structure(self):
        from src.discord_bot.embeds import build_spotgamma_comparison_embed

        levels = SpotGammaLevels(
            call_wall=5900.0,
            put_wall=5700.0,
            vol_trigger=5800.0,
            hedge_wall=5850.0,
            abs_gamma=5825.0,
            timestamp=datetime(2026, 4, 6, 9, 30, tzinfo=timezone.utc),
            ticker="SPX",
            source="manual",
        )
        gex = _FakeGEXResult(
            gamma_flip=5805.0,
            gamma_ceiling=5895.0,
            gamma_floor=5710.0,
        )

        embed = build_spotgamma_comparison_embed(
            sg_levels=levels,
            gex_result=gex,
            spot_price=5810.0,
        )

        assert embed.title is not None
        assert "SPX" in embed.title

        # Should have Resistance, Support, Gamma Flip, and SpotGamma Only fields
        field_names = [f.name for f in embed.fields]
        assert "Resistance" in field_names
        assert "Support" in field_names
        assert "Gamma Flip / Vol Trigger" in field_names
        assert "SpotGamma Only" in field_names

        # Description should mention spot price and agreement count
        assert embed.description is not None
        assert "5,810" in embed.description or "Agreement" in embed.description

    def test_comparison_embed_agree_diverge_labels(self):
        from src.discord_bot.embeds import build_spotgamma_comparison_embed

        # All agree within 10 pts
        levels = SpotGammaLevels(
            call_wall=5900.0,
            put_wall=5700.0,
            vol_trigger=5800.0,
            hedge_wall=5850.0,
            abs_gamma=5825.0,
            timestamp=datetime(2026, 4, 6, 9, 30, tzinfo=timezone.utc),
        )
        gex_agree = _FakeGEXResult(
            gamma_flip=5802.0,
            gamma_ceiling=5898.0,
            gamma_floor=5703.0,
        )

        embed = build_spotgamma_comparison_embed(
            sg_levels=levels,
            gex_result=gex_agree,
            spot_price=5810.0,
        )

        # Look for AGREE indicators in field values
        all_text = " ".join(f.value for f in embed.fields)
        assert "AGREE" in all_text


# ---------------------------------------------------------------------------
# Test 10: Store Cleanup
# ---------------------------------------------------------------------------


class TestStoreCleanup:
    """Save multiple HIRO entries, run cleanup, verify old ones removed."""

    @pytest.mark.asyncio
    async def test_cleanup_removes_old_preserves_recent(self, sg):
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Save 5 old entries (10 days ago)
        old_base = now - timedelta(days=10)
        for i in range(5):
            await sg.save_hiro(SpotGammaHIRO(
                timestamp=old_base + timedelta(hours=i),
                hedging_impact=float(i),
                cumulative_impact=float(i * 2),
            ))

        # Save 3 recent entries (today)
        for i in range(3):
            await sg.save_hiro(SpotGammaHIRO(
                timestamp=now - timedelta(hours=i),
                hedging_impact=float(i + 10),
                cumulative_impact=float(i * 3),
            ))

        # Verify all 8 entries exist
        all_rows = await sg.get_hiro_since(
            since=datetime(2000, 1, 1), ticker="SPX",
        )
        assert len(all_rows) == 8

        # Run cleanup (7-day threshold)
        deleted = await sg.cleanup_old_hiro(days=7)
        assert deleted == 5

        # Verify only recent entries survive
        remaining = await sg.get_hiro_since(
            since=datetime(2000, 1, 1), ticker="SPX",
        )
        assert len(remaining) == 3

        # Verify the surviving entries are the recent ones
        for row in remaining:
            assert row.hedging_impact >= 10.0
