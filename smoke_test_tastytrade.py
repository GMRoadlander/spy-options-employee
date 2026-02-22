"""Smoke test: fetch live SPY data via Tastytrade and run full analysis.

Requires real Tastytrade credentials in .env:
  TASTYTRADE_CLIENT_SECRET=...
  TASTYTRADE_REFRESH_TOKEN=...

Usage:
  python smoke_test_tastytrade.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()


async def main():
    # Check credentials
    client_secret = os.getenv("TASTYTRADE_CLIENT_SECRET", "")
    refresh_token = os.getenv("TASTYTRADE_REFRESH_TOKEN", "")

    if not client_secret or not refresh_token:
        print("ERROR: Set TASTYTRADE_CLIENT_SECRET and TASTYTRADE_REFRESH_TOKEN in .env")
        sys.exit(1)

    is_sandbox = os.getenv("TASTYTRADE_SANDBOX", "false").lower() == "true"

    from src.data.tastytrade_client import TastytradeClient
    from src.analysis.analyzer import analyze

    print(f"Connecting to Tastytrade ({'sandbox' if is_sandbox else 'production'})...")

    async with TastytradeClient(
        client_secret=client_secret,
        refresh_token=refresh_token,
        is_sandbox=is_sandbox,
    ) as client:
        chain = await client.fetch_chain("SPY")
        if not chain:
            print("Failed to fetch SPY chain from Tastytrade")
            sys.exit(1)

        print(f"SPY @ ${chain.spot_price:.2f} | {len(chain.contracts)} contracts | {len(chain.expirations)} expirations | source={chain.source}")

        # Check Greeks are populated
        greeks_count = sum(1 for c in chain.contracts if c.delta != 0.0)
        print(f"Contracts with Greeks: {greeks_count}/{len(chain.contracts)}")
        print()

        # Show a few sample contracts
        print("=== Sample Contracts ===")
        for c in chain.contracts[:6]:
            print(
                f"  {c.option_type.upper():4s} ${c.strike:>8.2f} "
                f"exp={c.expiry} bid={c.bid:.2f} ask={c.ask:.2f} "
                f"vol={c.volume:>6d} OI={c.open_interest:>6d} "
                f"IV={c.iv:.3f} delta={c.delta:+.3f} gamma={c.gamma:.4f}"
            )

        print()
        result = await analyze(chain)

        print("=== GEX ===")
        print(f"  Net GEX: {result.gex.net_gex:,.0f}")
        flip = f"${result.gex.gamma_flip:.2f}" if result.gex.gamma_flip else "None"
        print(f"  Gamma Flip: {flip}")
        print(f"  Gamma Ceiling: ${result.gex.gamma_ceiling:.2f}")
        print(f"  Gamma Floor: ${result.gex.gamma_floor:.2f}")
        print(f"  Squeeze Prob: {result.gex.squeeze_probability:.1%}")

        print()
        print("=== Max Pain ===")
        print(f"  Max Pain: ${result.max_pain.max_pain_price:.2f}")
        print(f"  Distance: {result.max_pain.distance_pct:+.2f}%")
        print(f"  Expiry: {result.max_pain.expiry}")

        print()
        print("=== PCR ===")
        print(f"  Volume PCR: {result.pcr.volume_pcr:.3f}")
        print(f"  OI PCR: {result.pcr.oi_pcr:.3f}")
        print(f"  Signal: {result.pcr.signal}")
        print(f"  Dealer: {result.pcr.dealer_positioning}")

        print()
        print("=== Key Levels ===")
        for level in result.strike_intel.key_levels[:8]:
            print(f"  ${level.price:.2f} ({level.level_type}, sig={level.significance:.2f})")

        print()
        print("Tastytrade smoke test PASSED")


if __name__ == "__main__":
    asyncio.run(main())
