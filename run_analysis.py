"""Standalone analysis pipeline runner.

Fetches live SPX/SPY options chain data and runs the full analysis pipeline
(GEX, max pain, PCR, strike intel) to produce real platform-computed levels.

Usage:
    python run_analysis.py [--ticker SPY] [--json] [--all-expiries]

Outputs key levels for use in strategy development and agent swarms.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from src.analysis.analyzer import AnalysisResult, analyze
from src.analysis.gex import calculate_gex
from src.data.data_manager import DataManager


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_analysis")


def format_analysis(result: AnalysisResult, chain) -> str:
    """Format analysis result as a readable report."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"  {result.ticker} ANALYSIS — {result.timestamp.strftime('%Y-%m-%d %H:%M ET')}")
    lines.append(f"  Spot: ${result.spot_price:.2f} | Source: {chain.source}")
    lines.append(f"  Contracts: {len(chain.contracts)} | Expirations: {len(chain.expirations)}")
    lines.append("=" * 60)

    # GEX
    g = result.gex
    lines.append("")
    lines.append("--- GEX (Gamma Exposure) ---")
    lines.append(f"  Net GEX:            {g.net_gex:>15.2e}")
    if g.gamma_flip is not None:
        lines.append(f"  Gamma Flip:         ${g.gamma_flip:>12.2f}  {'<-- ABOVE SPOT (bullish regime)' if g.gamma_flip < result.spot_price else '<-- BELOW SPOT (bearish regime)' if g.gamma_flip > result.spot_price else '<-- AT SPOT (inflection point)'}")
    else:
        lines.append("  Gamma Flip:         N/A")
    if g.gamma_ceiling is not None:
        lines.append(f"  Gamma Ceiling:      ${g.gamma_ceiling:>12.2f}  (call wall / resistance)")
    if g.gamma_floor is not None:
        lines.append(f"  Gamma Floor:        ${g.gamma_floor:>12.2f}  (put wall / support)")
    lines.append(f"  Squeeze Prob:       {g.squeeze_probability:>12.1%}")

    # Multi-expiry breakdown
    if g.gex_by_expiry:
        lines.append("")
        lines.append("  Per-Expiry GEX:")
        sorted_expiries = sorted(g.gex_by_expiry.items(), key=lambda x: x[0])
        for exp, gex_val in sorted_expiries[:5]:
            lines.append(f"    {exp}: {gex_val:>15.2e}")
        if len(sorted_expiries) > 5:
            lines.append(f"    ... and {len(sorted_expiries) - 5} more")

    # Max Pain
    mp = result.max_pain
    lines.append("")
    lines.append("--- MAX PAIN ---")
    lines.append(f"  Max Pain Price:     ${mp.max_pain_price:>12.2f}")
    lines.append(f"  Distance from Spot: {mp.distance_pct:>12.2f}%")

    # PCR
    p = result.pcr
    lines.append("")
    lines.append("--- PUT/CALL RATIO ---")
    lines.append(f"  Volume PCR:         {p.volume_pcr:>12.3f}  ({p.signal})")
    lines.append(f"  OI PCR:             {p.oi_pcr:>12.3f}  (Dealer: {p.dealer_positioning})")
    lines.append(f"  Call Volume:        {p.total_call_volume:>12,}")
    lines.append(f"  Put Volume:         {p.total_put_volume:>12,}")
    lines.append(f"  Call OI:            {p.total_call_oi:>12,}")
    lines.append(f"  Put OI:             {p.total_put_oi:>12,}")

    # Strike Intel
    si = result.strike_intel
    lines.append("")
    lines.append("--- KEY LEVELS ---")
    if si.key_levels:
        for level in si.key_levels:
            lines.append(f"  ${level.price:>8.2f}  {level.level_type:<20s}  significance: {level.significance:.2f}")
    else:
        lines.append("  No key levels computed")

    # Recommendations
    lines.append("")
    lines.append("--- OPTIMAL PUT STRIKES ---")
    if si.optimal_puts:
        for rec in si.optimal_puts[:5]:
            lines.append(f"  ${rec.strike:>8.2f}  {rec.expiry}  P(ITM)={rec.probability_itm:.1%}  GEX: {rec.gex_support}")
    else:
        lines.append("  No put recommendations")

    lines.append("")
    lines.append("--- OPTIMAL CALL STRIKES ---")
    if si.optimal_calls:
        for rec in si.optimal_calls[:5]:
            lines.append(f"  ${rec.strike:>8.2f}  {rec.expiry}  P(ITM)={rec.probability_itm:.1%}  GEX: {rec.gex_support}")
    else:
        lines.append("  No call recommendations")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def to_json(result: AnalysisResult) -> dict:
    """Convert analysis result to JSON-serializable dict."""
    g = result.gex
    mp = result.max_pain
    p = result.pcr
    si = result.strike_intel

    return {
        "ticker": result.ticker,
        "spot_price": result.spot_price,
        "timestamp": result.timestamp.isoformat(),
        "gex": {
            "net_gex": g.net_gex,
            "gamma_flip": g.gamma_flip,
            "gamma_ceiling": g.gamma_ceiling,
            "gamma_floor": g.gamma_floor,
            "squeeze_probability": g.squeeze_probability,
            "gex_by_expiry": g.gex_by_expiry,
        },
        "max_pain": {
            "price": mp.max_pain_price,
            "distance_pct": mp.distance_pct,
        },
        "pcr": {
            "volume_pcr": p.volume_pcr,
            "oi_pcr": p.oi_pcr,
            "signal": p.signal,
            "dealer_positioning": p.dealer_positioning,
        },
        "key_levels": [
            {
                "price": lv.price,
                "type": lv.level_type,
                "significance": lv.significance,
            }
            for lv in si.key_levels
        ],
        "optimal_puts": [
            {
                "strike": r.strike,
                "expiry": r.expiry.isoformat(),
                "p_itm": r.probability_itm,
                "gex_support": r.gex_support,
            }
            for r in si.optimal_puts[:5]
        ],
        "optimal_calls": [
            {
                "strike": r.strike,
                "expiry": r.expiry.isoformat(),
                "p_itm": r.probability_itm,
                "gex_support": r.gex_support,
            }
            for r in si.optimal_calls[:5]
        ],
    }


async def run(ticker: str, output_json: bool, all_expiries: bool) -> None:
    """Fetch chain and run full analysis pipeline."""

    logger.info("Initializing DataManager...")
    manager = DataManager(cache_ttl_seconds=60.0)

    try:
        logger.info("Fetching %s chain...", ticker)
        chain = await manager.get_chain(ticker)

        if chain is None:
            logger.error(
                "Could not fetch chain for %s. Check API credentials:\n"
                "  TASTYTRADE_CLIENT_SECRET: %s\n"
                "  TRADIER_TOKEN: %s\n"
                "  (CBOE CDN requires no auth but may be down)",
                ticker,
                "set" if os.getenv("TASTYTRADE_CLIENT_SECRET") else "NOT SET",
                "set" if os.getenv("TRADIER_TOKEN") else "NOT SET",
            )
            return

        logger.info(
            "Chain fetched: %d contracts, spot $%.2f, source %s, quality %s",
            len(chain.contracts),
            chain.spot_price,
            chain.source,
            chain.data_quality,
        )

        # Run full analysis (nearest expiry)
        logger.info("Running analysis (nearest expiry)...")
        result = await analyze(chain)

        # Print report
        print(format_analysis(result, chain))

        # Also run multi-expiry GEX if requested
        if all_expiries:
            logger.info("Running multi-expiry GEX (all expirations)...")
            from src.analysis.pcr import calculate_pcr

            pcr = calculate_pcr(chain)
            multi_gex = calculate_gex(chain, expiry=None, volume_pcr=pcr.volume_pcr)
            print("\n--- MULTI-EXPIRY GEX (all expirations aggregated) ---")
            print(f"  Net GEX (all):      {multi_gex.net_gex:>15.2e}")
            if multi_gex.gamma_flip is not None:
                print(f"  Gamma Flip (all):   ${multi_gex.gamma_flip:>12.2f}")
            if multi_gex.gamma_ceiling is not None:
                print(f"  Gamma Ceiling (all):${multi_gex.gamma_ceiling:>12.2f}")
            if multi_gex.gamma_floor is not None:
                print(f"  Gamma Floor (all):  ${multi_gex.gamma_floor:>12.2f}")
            if multi_gex.gex_by_expiry:
                print(f"\n  Per-Expiry Breakdown:")
                for exp, val in sorted(multi_gex.gex_by_expiry.items()):
                    print(f"    {exp}: {val:>15.2e}")

        # JSON output
        if output_json:
            json_data = to_json(result)
            out_path = Path(f".planning/strategy-positions-v3/LIVE-{ticker}-LEVELS.json")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(json_data, indent=2))
            logger.info("JSON written to %s", out_path)
            print(f"\nJSON output saved to: {out_path}")

    finally:
        await manager.close()


def main():
    parser = argparse.ArgumentParser(description="Run SPX/SPY analysis pipeline")
    parser.add_argument("--ticker", default="SPY", help="Ticker to analyze (default: SPY)")
    parser.add_argument("--json", action="store_true", help="Output JSON to .planning/strategy-positions-v3/")
    parser.add_argument("--all-expiries", action="store_true", help="Also run multi-expiry GEX")
    args = parser.parse_args()

    asyncio.run(run(args.ticker, args.json, args.all_expiries))


if __name__ == "__main__":
    main()
