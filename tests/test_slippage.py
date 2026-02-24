"""Tests for the slippage modeling module.

Validates FixedSlippage, DynamicSpreadSlippage, spread estimation,
time-of-day classification, clamping, multi-leg discount, and
slippage logging to the database.
"""

from __future__ import annotations

from datetime import datetime

import aiosqlite
import pytest
import pytest_asyncio

from src.paper.schema import init_paper_tables
from src.paper.slippage import (
    DynamicSpreadSlippage,
    FillResult,
    FixedSlippage,
    OrderSide,
    SlippageModel,
)


# ── Helpers ──


def _midday_ts() -> datetime:
    """Return a midday timestamp (11:00 AM) for minimal time adjustment."""
    return datetime(2025, 3, 10, 11, 0, 0)


def _close_ts() -> datetime:
    """Return a near-close timestamp (15:30) for elevated time adjustment."""
    return datetime(2025, 3, 10, 15, 30, 0)


def _open_ts() -> datetime:
    """Return an opening timestamp (9:35) for elevated time adjustment."""
    return datetime(2025, 3, 10, 9, 35, 0)


@pytest_asyncio.fixture
async def db():
    """Create an in-memory DB with required tables for slippage logging."""
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'paper',
            template_yaml TEXT,
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    now = datetime.now().isoformat()
    await conn.execute(
        "INSERT INTO strategies (name, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("Test Strategy", "paper", now, now),
    )
    await conn.commit()
    await init_paper_tables(conn)
    yield conn
    await conn.close()


# ── FixedSlippage Tests ──


class TestFixedSlippage:
    """Tests for the Tier 1 fixed slippage model."""

    def test_fixed_slippage_buy_above_mid(self):
        """Buy fills above mid price by the fixed offset."""
        model = FixedSlippage(fixed_cents=0.10)
        result = model.simulate_fill(
            bid=3.40, ask=3.60, side=OrderSide.BUY,
        )

        assert result.mid_price == pytest.approx(3.50, abs=0.001)
        assert result.fill_price > result.mid_price
        # Slippage = max(0.10, 3.50 * 0.005) = max(0.10, 0.0175) = 0.10
        assert result.fill_price == pytest.approx(3.60, abs=0.001)
        assert result.slippage == pytest.approx(0.10, abs=0.01)
        assert result.model_tier == "fixed"

    def test_fixed_slippage_sell_below_mid(self):
        """Sell fills below mid price by the fixed offset."""
        model = FixedSlippage(fixed_cents=0.10)
        result = model.simulate_fill(
            bid=3.40, ask=3.60, side=OrderSide.SELL,
        )

        assert result.fill_price < result.mid_price
        # Fill = 3.50 - 0.10 = 3.40 (clamped to bid)
        assert result.fill_price == pytest.approx(3.40, abs=0.001)
        assert result.slippage == pytest.approx(0.10, abs=0.01)

    def test_fixed_slippage_small_price_uses_min_pct(self):
        """For expensive options, min_slippage_pct may dominate."""
        model = FixedSlippage(fixed_cents=0.01, min_slippage_pct=0.02)
        result = model.simulate_fill(
            bid=9.80, ask=10.20, side=OrderSide.BUY,
        )

        # mid = 10.0, min_pct slippage = 10.0 * 0.02 = 0.20
        # fixed_cents = 0.01, so max(0.01, 0.20) = 0.20
        assert result.slippage == pytest.approx(0.20, abs=0.01)

    def test_fixed_slippage_zero_mid(self):
        """Edge case: zero mid should return ask for buy, bid for sell."""
        model = FixedSlippage(fixed_cents=0.10)
        result = model.simulate_fill(
            bid=0.0, ask=0.0, side=OrderSide.BUY,
        )
        assert result.fill_price == 0.0
        assert result.slippage == 0.0

    def test_fixed_slippage_clamped_within_bid_ask(self):
        """Fill should not exceed the bid-ask range."""
        # Very tight spread with a large fixed offset
        model = FixedSlippage(fixed_cents=1.00)
        result = model.simulate_fill(
            bid=5.00, ask=5.10, side=OrderSide.BUY,
        )
        assert result.fill_price <= 5.10  # Cannot exceed ask
        assert result.fill_price >= 5.00  # Cannot go below bid


# ── DynamicSpreadSlippage Tests ──


class TestDynamicSpreadSlippage:
    """Tests for the Tier 2 dynamic spread slippage model."""

    def test_dynamic_atm_low_vol_midday(self):
        """ATM option at midday with low VIX: factor should be near base (0.30).

        Conditions: delta=0.50 (ATM), dte=7 (weekly), volume=2000 (normal),
        VIX=14 (low), midday timestamp, order_size=1, single leg.
        Expected adjustments: moneyness=0.00, dte=+0.03, volume=0.00,
        vix=0.00, time=0.00, size=0.00, multi_leg=0.00 -> factor ~0.33
        """
        model = DynamicSpreadSlippage()
        result = model.simulate_fill(
            bid=5.00, ask=5.40, side=OrderSide.BUY,
            delta=0.50, dte=7, volume=2000, vix=14.0,
            order_size=1, is_multi_leg=False, timestamp=_midday_ts(),
        )

        assert result.model_tier == "dynamic"
        # Factor should be near 0.33 (base 0.30 + weekly 0.03)
        assert 0.25 <= result.slippage_factor <= 0.40
        # Fill should be close to mid but above it (buy)
        assert result.fill_price > result.mid_price
        assert result.fill_price <= result.mid_price + (result.spread / 2)

    def test_dynamic_deep_otm_0dte_close(self):
        """Deep OTM 0DTE near close: factor should be elevated (0.65+).

        Conditions: delta=0.03 (deep OTM), dte=0, volume=50 (thin),
        VIX=18 (moderate), close timestamp (15:30), single leg.
        Expected adjustments: moneyness=+0.30, dte=+0.10, volume=+0.20,
        vix=+0.05, time=+0.15, size=0.00 -> factor ~1.10
        """
        model = DynamicSpreadSlippage()
        result = model.simulate_fill(
            bid=0.10, ask=0.30, side=OrderSide.BUY,
            delta=0.03, dte=0, volume=50, vix=18.0,
            order_size=1, is_multi_leg=False, timestamp=_close_ts(),
        )

        # Factor should be significantly elevated
        assert result.slippage_factor >= 0.65
        # Fill price should be higher than mid for buy
        assert result.fill_price > result.mid_price

    def test_dynamic_high_vix_crisis(self):
        """High VIX crisis conditions: factor should be high (0.60+).

        Conditions: delta=0.15 (OTM), dte=2, volume=500 (moderate),
        VIX=40 (crisis), midday, order_size=1.
        Expected adjustments: moneyness=+0.15, dte=+0.03, volume=+0.10,
        vix=+0.30, time=0.00 -> factor ~0.88
        """
        model = DynamicSpreadSlippage()
        result = model.simulate_fill(
            bid=2.00, ask=3.00, side=OrderSide.BUY,
            delta=0.15, dte=2, volume=500, vix=40.0,
            order_size=1, is_multi_leg=False, timestamp=_midday_ts(),
        )

        assert result.slippage_factor >= 0.60
        assert result.fill_price > result.mid_price

    def test_dynamic_multi_leg_discount(self):
        """Multi-leg orders get COB discount of -0.05.

        Same conditions with and without multi-leg should differ by exactly
        the multi_leg_discount value.
        """
        model = DynamicSpreadSlippage()
        kwargs = dict(
            bid=5.00, ask=5.40, side=OrderSide.BUY,
            delta=0.50, dte=7, volume=2000, vix=14.0,
            order_size=1, timestamp=_midday_ts(),
        )

        single_result = model.simulate_fill(**kwargs, is_multi_leg=False)
        multi_result = model.simulate_fill(**kwargs, is_multi_leg=True)

        # Multi-leg factor should be exactly 0.05 lower
        discount = model.config["multi_leg_discount"]
        assert multi_result.slippage_factor == pytest.approx(
            single_result.slippage_factor + discount, abs=0.001
        )
        # Multi-leg fill should be cheaper for buyer (closer to mid)
        assert multi_result.fill_price < single_result.fill_price

    def test_simulate_spread_fill_all_or_nothing(self):
        """Spread fill returns None if any leg has zero quotes."""
        model = DynamicSpreadSlippage()
        legs = [
            {"bid": 5.00, "ask": 5.40, "side": OrderSide.SELL, "delta": 0.50,
             "dte": 7, "volume": 2000, "open_interest": 10000},
            {"bid": 0.0, "ask": 0.0, "side": OrderSide.BUY, "delta": 0.10,
             "dte": 7, "volume": 100, "open_interest": 500},
        ]

        result = model.simulate_spread_fill(legs, vix=16.0)
        assert result is None

    def test_simulate_spread_fill_success(self):
        """Spread fill returns results for all valid legs."""
        model = DynamicSpreadSlippage()
        legs = [
            {"bid": 3.40, "ask": 3.60, "side": OrderSide.SELL, "delta": -0.30,
             "dte": 14, "volume": 2000, "open_interest": 10000},
            {"bid": 1.80, "ask": 2.00, "side": OrderSide.BUY, "delta": -0.15,
             "dte": 14, "volume": 1500, "open_interest": 8000},
        ]

        results = model.simulate_spread_fill(legs, vix=16.0, timestamp=_midday_ts())
        assert results is not None
        assert len(results) == 2
        # All legs should have is_multi_leg=True in metadata
        for r in results:
            assert r.metadata.get("is_multi_leg") is True

    def test_estimate_spread_stale_quotes(self):
        """Stale quotes (bid == ask) should trigger spread estimation."""
        model = DynamicSpreadSlippage()

        # ATM option with zero spread (stale quote)
        result = model.simulate_fill(
            bid=5.00, ask=5.00, side=OrderSide.BUY,
            delta=0.50, dte=7, volume=2000, vix=16.0,
            timestamp=_midday_ts(),
        )

        # Should still have non-zero slippage (estimated spread used)
        assert result.slippage > 0
        assert result.spread > 0  # Estimated spread used

    def test_estimate_spread_values(self):
        """_estimate_spread produces reasonable spread estimates."""
        # ATM: 2% of price
        spread_atm = DynamicSpreadSlippage._estimate_spread(
            option_price=10.0, delta=0.50, dte=7, vix=16.0,
        )
        assert 0.10 <= spread_atm <= 0.50  # Reasonable for $10 ATM

        # Deep OTM: 40% of price
        spread_otm = DynamicSpreadSlippage._estimate_spread(
            option_price=0.50, delta=0.03, dte=0, vix=16.0,
        )
        assert spread_otm >= 0.05  # At least minimum spread

        # High VIX widens spread
        spread_high_vix = DynamicSpreadSlippage._estimate_spread(
            option_price=10.0, delta=0.50, dte=7, vix=32.0,
        )
        assert spread_high_vix > spread_atm  # Higher VIX = wider

        # 0DTE widens spread
        spread_0dte = DynamicSpreadSlippage._estimate_spread(
            option_price=10.0, delta=0.50, dte=0, vix=16.0,
        )
        assert spread_0dte > spread_atm  # 0DTE multiplier = 1.3

    def test_fill_clamped_within_bid_ask(self):
        """Fill price should stay within bid-ask range for normal factors.

        For buy orders: fill >= bid (always). For sell orders: fill <= ask.
        """
        model = DynamicSpreadSlippage()

        # Buy: fill should be between bid and ask (for factor < 1.0)
        buy_result = model.simulate_fill(
            bid=3.00, ask=3.20, side=OrderSide.BUY,
            delta=0.50, dte=7, volume=2000, vix=14.0,
            order_size=1, timestamp=_midday_ts(),
        )
        assert buy_result.fill_price >= 3.00  # >= bid
        assert buy_result.fill_price <= 3.20  # <= ask (for base factor ~0.30)

        # Sell: fill should be between bid and ask
        sell_result = model.simulate_fill(
            bid=3.00, ask=3.20, side=OrderSide.SELL,
            delta=0.50, dte=7, volume=2000, vix=14.0,
            order_size=1, timestamp=_midday_ts(),
        )
        assert sell_result.fill_price >= 3.00
        assert sell_result.fill_price <= 3.20

    def test_fill_buy_above_mid_sell_below_mid(self):
        """Buys should fill above mid; sells should fill below mid."""
        model = DynamicSpreadSlippage()
        kwargs = dict(
            bid=5.00, ask=5.40,
            delta=0.50, dte=7, volume=2000, vix=14.0,
            order_size=1, timestamp=_midday_ts(),
        )

        buy = model.simulate_fill(side=OrderSide.BUY, **kwargs)
        sell = model.simulate_fill(side=OrderSide.SELL, **kwargs)

        assert buy.fill_price > buy.mid_price
        assert sell.fill_price < sell.mid_price

    def test_factor_clamped_to_bounds(self):
        """Slippage factor should be clamped to [0.05, 1.50]."""
        model = DynamicSpreadSlippage()

        # Best case: ATM, high volume, low VIX, midday, multi-leg
        # base=0.30, moneyness=0.00, dte=0.00, vol=-0.05, vix=0.00,
        # time=0.00, size=0.00, multi=-0.05 -> 0.20
        factor_low = model.compute_slippage_factor(
            delta=0.50, dte=15, volume=10000, vix=12.0,
            time_of_day="midday", order_size=1, is_multi_leg=True,
        )
        assert factor_low >= 0.05  # Minimum

        # Worst case: deep OTM, 0DTE, thin volume, crisis VIX, post-close, large
        factor_high = model.compute_slippage_factor(
            delta=0.01, dte=0, volume=10, vix=50.0,
            time_of_day="post_close", order_size=500, is_multi_leg=False,
        )
        assert factor_high <= 1.50  # Maximum

    def test_custom_config_overrides(self):
        """Custom config should override default values."""
        model = DynamicSpreadSlippage(config={
            "base_factor": 0.50,
            "multi_leg_discount": -0.10,
        })

        assert model.config["base_factor"] == 0.50
        assert model.config["multi_leg_discount"] == -0.10
        # Other defaults preserved
        assert model.config["factor_min"] == 0.05

    def test_negative_spread_edge_case(self):
        """Negative spread (crossed market) should use edge case path."""
        model = DynamicSpreadSlippage()
        result = model.simulate_fill(
            bid=5.10, ask=5.00, side=OrderSide.BUY,
            delta=0.50, dte=7,
        )
        # Should still produce a result (edge case handling)
        assert isinstance(result, FillResult)


# ── Time Classification Tests ──


class TestTimeClassification:
    """Tests for the _classify_time_of_day helper."""

    def test_pre_open(self):
        ts = datetime(2025, 3, 10, 9, 15, 0)
        assert DynamicSpreadSlippage._classify_time_of_day(ts) == "pre_open"

    def test_open(self):
        ts = datetime(2025, 3, 10, 9, 35, 0)
        assert DynamicSpreadSlippage._classify_time_of_day(ts) == "open"

    def test_midday(self):
        ts = datetime(2025, 3, 10, 11, 0, 0)
        assert DynamicSpreadSlippage._classify_time_of_day(ts) == "midday"

    def test_power_hour(self):
        ts = datetime(2025, 3, 10, 14, 30, 0)
        assert DynamicSpreadSlippage._classify_time_of_day(ts) == "power_hour"

    def test_close(self):
        ts = datetime(2025, 3, 10, 15, 30, 0)
        assert DynamicSpreadSlippage._classify_time_of_day(ts) == "close"

    def test_post_close(self):
        ts = datetime(2025, 3, 10, 16, 30, 0)
        assert DynamicSpreadSlippage._classify_time_of_day(ts) == "post_close"

    def test_none_defaults_to_midday(self):
        assert DynamicSpreadSlippage._classify_time_of_day(None) == "midday"

    def test_boundary_930(self):
        """9:30:00 should be 'open', not 'pre_open'."""
        ts = datetime(2025, 3, 10, 9, 30, 0)
        assert DynamicSpreadSlippage._classify_time_of_day(ts) == "open"

    def test_boundary_945(self):
        """9:45:00 should be 'midday', not 'open'."""
        ts = datetime(2025, 3, 10, 9, 45, 0)
        assert DynamicSpreadSlippage._classify_time_of_day(ts) == "midday"


# ── Slippage Factor Component Tests ──


class TestSlippageFactorComponents:
    """Tests for individual factor adjustments."""

    def test_moneyness_atm_vs_deep_otm(self):
        """Deep OTM should have higher factor than ATM."""
        model = DynamicSpreadSlippage()
        base_kwargs = dict(
            dte=7, volume=2000, vix=16.0,
            time_of_day="midday", order_size=1, is_multi_leg=False,
        )

        factor_atm = model.compute_slippage_factor(delta=0.50, **base_kwargs)
        factor_otm = model.compute_slippage_factor(delta=0.03, **base_kwargs)

        assert factor_otm > factor_atm
        assert factor_otm - factor_atm == pytest.approx(0.30, abs=0.01)

    def test_volume_high_vs_thin(self):
        """Thin volume should have higher factor than high volume."""
        model = DynamicSpreadSlippage()
        base_kwargs = dict(
            delta=0.50, dte=7, vix=16.0,
            time_of_day="midday", order_size=1, is_multi_leg=False,
        )

        factor_high = model.compute_slippage_factor(volume=10000, **base_kwargs)
        factor_thin = model.compute_slippage_factor(volume=50, **base_kwargs)

        assert factor_thin > factor_high

    def test_order_size_small_vs_large(self):
        """Large orders should have higher factor than small orders."""
        model = DynamicSpreadSlippage()
        base_kwargs = dict(
            delta=0.50, dte=7, volume=2000, vix=16.0,
            time_of_day="midday", is_multi_leg=False,
        )

        factor_small = model.compute_slippage_factor(order_size=1, **base_kwargs)
        factor_large = model.compute_slippage_factor(order_size=300, **base_kwargs)

        assert factor_large > factor_small


# ── Slippage Logging Tests ──


class TestSlippageLogging:
    """Tests for slippage log database operations."""

    @pytest.mark.asyncio
    async def test_slippage_logging(self, db):
        """Slippage fills should be persistable to the slippage_log table."""
        model = DynamicSpreadSlippage()
        result = model.simulate_fill(
            bid=5.00, ask=5.40, side=OrderSide.BUY,
            delta=0.50, dte=7, volume=2000, vix=14.0,
            order_size=1, timestamp=_midday_ts(),
        )

        # Insert into slippage_log
        now = datetime.now().isoformat()
        await db.execute(
            """
            INSERT INTO slippage_log
                (timestamp, symbol, side, order_size, bid, ask, mid,
                 fill_price, slippage, slippage_pct, slippage_factor,
                 spread, delta, dte, volume, vix, model_tier, strategy_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now, "SPX", "buy", 1,
                5.00, 5.40, result.mid_price,
                result.fill_price, result.slippage, result.slippage_pct,
                result.slippage_factor, result.spread,
                0.50, 7, 2000, 14.0,
                result.model_tier, 1,
            ),
        )
        await db.commit()

        # Verify the record was inserted
        cursor = await db.execute(
            "SELECT symbol, side, fill_price, slippage_factor, model_tier "
            "FROM slippage_log WHERE strategy_id = 1"
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == "SPX"
        assert row[1] == "buy"
        assert row[2] == pytest.approx(result.fill_price, abs=0.001)
        assert row[3] == pytest.approx(result.slippage_factor, abs=0.001)
        assert row[4] == "dynamic"

    @pytest.mark.asyncio
    async def test_slippage_log_multiple_entries(self, db):
        """Multiple slippage entries can be queried by strategy."""
        model = DynamicSpreadSlippage()
        now = datetime.now().isoformat()

        for side_val, side_enum in [("buy", OrderSide.BUY), ("sell", OrderSide.SELL)]:
            result = model.simulate_fill(
                bid=3.00, ask=3.20, side=side_enum,
                delta=0.30, dte=14, volume=1500, vix=16.0,
                timestamp=_midday_ts(),
            )
            await db.execute(
                """
                INSERT INTO slippage_log
                    (timestamp, symbol, side, order_size, bid, ask, mid,
                     fill_price, slippage, slippage_pct, slippage_factor,
                     spread, delta, dte, volume, vix, model_tier, strategy_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now, "SPX", side_val, 1,
                    3.00, 3.20, result.mid_price,
                    result.fill_price, result.slippage, result.slippage_pct,
                    result.slippage_factor, result.spread,
                    0.30, 14, 1500, 16.0,
                    result.model_tier, 1,
                ),
            )
        await db.commit()

        cursor = await db.execute(
            "SELECT COUNT(*) FROM slippage_log WHERE strategy_id = 1"
        )
        row = await cursor.fetchone()
        assert row[0] == 2

    @pytest.mark.asyncio
    async def test_slippage_log_table_exists(self, db):
        """The slippage_log table should be created by init_paper_tables."""
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='slippage_log'"
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == "slippage_log"

    @pytest.mark.asyncio
    async def test_slippage_log_indexes_exist(self, db):
        """Slippage log indexes should be created."""
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name LIKE 'idx_slippage_log_%'"
        )
        rows = await cursor.fetchall()
        index_names = {row[0] for row in rows}
        assert "idx_slippage_log_timestamp" in index_names
        assert "idx_slippage_log_strategy" in index_names
        assert "idx_slippage_log_model" in index_names


# ── SlippageModel ABC Tests ──


class TestSlippageModelABC:
    """Tests for the SlippageModel abstract base class."""

    def test_abc_cannot_be_instantiated(self):
        """SlippageModel is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SlippageModel()

    def test_fill_result_dataclass(self):
        """FillResult should be a valid dataclass with defaults."""
        result = FillResult(
            fill_price=5.10,
            mid_price=5.00,
            slippage=0.10,
            slippage_pct=0.02,
            spread=0.20,
            slippage_factor=0.50,
            model_tier="dynamic",
        )
        assert result.fill_price == 5.10
        assert result.metadata == {}  # Default empty dict

    def test_fill_result_with_metadata(self):
        """FillResult should accept custom metadata."""
        result = FillResult(
            fill_price=5.10, mid_price=5.00, slippage=0.10,
            slippage_pct=0.02, spread=0.20, slippage_factor=0.50,
            model_tier="dynamic",
            metadata={"time_bucket": "midday", "dte": 7},
        )
        assert result.metadata["time_bucket"] == "midday"

    def test_order_side_enum(self):
        """OrderSide enum should have correct values."""
        assert OrderSide.BUY.value == "buy"
        assert OrderSide.SELL.value == "sell"
