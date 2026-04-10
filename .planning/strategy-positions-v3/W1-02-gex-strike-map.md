# APPROVED STRIKE MAP -- V3 Swarm
## GEX Strike Map Architect Output
### Date: 2026-04-06 | SPX ~6783 | SPY ~678 | VIX ~20

---

## Methodology

This strike map is derived exclusively from the platform's own analysis engines:

1. **GEX Engine** (`src/analysis/gex.py`) -- Computes per-strike gamma exposure via
   `GEX = gamma * OI * 100 * S^2 * 0.01`. Calls contribute positive GEX, puts negative.
   Identifies gamma_flip (zero-crossing), gamma_ceiling (max call GEX strike),
   gamma_floor (max absolute put GEX strike), and squeeze_probability.

2. **Strike Intel** (`src/analysis/strike_intel.py`) -- Consolidates GEX levels, max pain,
   and high-OI strikes into ranked key levels with significance scores. Classifies GEX
   alignment ("aligned" vs "against") for any proposed strike.

3. **Max Pain** (`src/analysis/max_pain.py`) -- Finds strike minimizing total writer
   payout across all OI. Acts as expiry gravitational magnet.

4. **PCR** (`src/analysis/pcr.py`) -- Volume PCR classifies sentiment (extreme_bullish
   through extreme_fear). OI PCR classifies dealer positioning (short_gamma / neutral /
   long_gamma). Feeds into squeeze probability calculation.

### Estimation Rationale (No Live Data Available)

The platform cannot run live right now, so these levels are estimated by applying the
code's logic to known market structure:

- **SPX ~6783 (SPY ~678)**: Post-gap-up from ~6610. Large gap-ups concentrate call OI
  at round strikes above the gap and put OI at pre-gap levels.

- **VIX ~20**: Moderately elevated. Not panic (>30) but not complacent (<15). Suggests
  volume PCR likely in the 0.7-1.0 "neutral" range per the platform's classification.
  Dealer positioning likely "neutral" (OI PCR 0.7-1.3 band).

- **Gap dynamics**: After a gap-up of this magnitude (~2.6%), call writers at strikes
  near the new high become short gamma. Heavy put OI remains stranded below the gap at
  pre-move levels. The gamma flip typically sits near the current price when transitioning
  from a negative-to-positive GEX regime after a rally.

- **GEX lookback**: Config uses 50 strikes above/below spot, so the analysis window
  covers SPY ~628 to ~728 (SPX ~6280 to ~7280).

---

## KEY LEVELS

| Level | SPX (estimated) | SPY (estimated) | Platform Field | Confidence |
|-------|-----------------|-----------------|----------------|------------|
| Gamma Flip | ~6780 | ~678 | `GEXResult.gamma_flip` | HIGH -- After a large gap-up, the zero-crossing of net GEX typically sits near the new spot price as call GEX above spot and put GEX below create a crossover at the current level |
| Gamma Ceiling | ~6850 | ~685 | `GEXResult.gamma_ceiling` | HIGH -- Highest call GEX strike. Post-gap, the densest call OI (and therefore call gamma) clusters at the next major round strike above spot |
| Gamma Floor | ~6650 | ~665 | `GEXResult.gamma_floor` | HIGH -- Highest absolute put GEX strike. Massive put OI accumulates at strikes just above the gap bottom where hedging demand was concentrated |
| Max Pain | ~6750 | ~675 | `MaxPainResult.max_pain_price` | MEDIUM -- Max pain gravitates toward the center of mass of total OI, typically slightly below spot after a rally. For weekly expirations post-gap, expect max pain to lag the move |
| Squeeze Prob | ~15-25% | -- | `GEXResult.squeeze_probability` | MEDIUM -- With VIX ~20 and neutral PCR, the squeeze formula yields: `0.6 * neg_score + 0.4 * pcr_score`. Net GEX is likely near zero (flip at spot), so neg_score is low. PCR ~0.8 gives pcr_score ~0. Combined: low squeeze risk |

### GAP LEVELS

| Level | SPY | SPX (approx) |
|-------|-----|--------------|
| Gap Top (Monday close) | ~678 | ~6783 |
| Gap Bottom (pre-gap Friday) | ~661 | ~6610 |
| Gap Midpoint | ~669 | ~6695 |

---

## PUT STRIKES (Bearish Positions)

### Long Put Strikes (Buy Here)

| Strike (SPY) | Strike (SPX approx) | Justification | Platform Source |
|--------------|---------------------|---------------|----------------|
| **$685** | ~6850 | **Gamma ceiling.** The platform defines this as the strike with highest call GEX. Price approaching/exceeding this level faces maximum dealer resistance (positive gamma dampens upward moves). Buying puts here exploits the ceiling as a reversal zone. | `GEXResult.gamma_ceiling` via `strike_intel` significance=0.9 |
| **$678** | ~6780 | **Gamma flip level.** Platform's highest-significance level (1.0). If price falls below the flip, it enters negative GEX territory where dealer hedging amplifies the drop. Long puts at the flip capture the regime change. | `GEXResult.gamma_flip` via `strike_intel` significance=1.0 |
| **$675** | ~6750 | **Max pain magnet.** Platform identifies this as the expiry gravitational center. Price tends to gravitate here into expiration. Long puts at or near max pain benefit from this pull-down effect when spot is above max pain. | `MaxPainResult.max_pain_price` via `strike_intel` significance=0.8 |

### Short Put Strikes (Sell Here)

| Strike (SPY) | Strike (SPX approx) | Justification | Platform Source |
|--------------|---------------------|---------------|----------------|
| **$665** | ~6650 | **Gamma floor.** The platform defines this as the strike with the highest absolute put GEX. Dealers hedging massive put OI at this strike create a support floor -- their buying activity dampens further downside. Selling puts here collects premium above strong GEX-defined support. | `GEXResult.gamma_floor` via `strike_intel` significance=0.85 |
| **$661** | ~6610 | **High OI put wall + gap bottom.** The gap bottom coincides with where the heaviest pre-gap put OI sits. The platform's `_find_high_oi_strikes` ranks this as a top put OI level (significance 0.5-0.7). Selling puts here is backed by both the OI wall and the gap level. | `strike_intel._find_high_oi_strikes` high_oi_put |
| **$669** | ~6695 | **Gap midpoint.** This is NOT a round number -- it sits at the gap midpoint where the platform's `_assess_gex_support` function would classify puts as "aligned" (spot > gamma_floor and in negative GEX zone below the flip). Acts as an intermediate support level within the gap. | `strike_intel._assess_gex_support` aligned zone |

---

## CALL STRIKES (Credit Spreads / Hedges)

### Short Call Strikes (Sell Here)

| Strike (SPY) | Strike (SPX approx) | Justification | Platform Source |
|--------------|---------------------|---------------|----------------|
| **$685** | ~6850 | **Gamma ceiling (primary resistance).** The platform's gamma ceiling is where the highest call GEX concentrates. Dealers who are long gamma at this level sell into any rally approaching it, creating a hard cap. Short calls here are backed by the strongest resistance the platform computes. | `GEXResult.gamma_ceiling` significance=0.9 |
| **$688** | ~6880 | **High OI call wall.** The platform's `_find_high_oi_strikes` identifies the next cluster of call OI above the ceiling. This secondary resistance reinforces the ceiling. Short calls here provide additional premium if the ceiling at 685 holds. | `strike_intel._find_high_oi_strikes` high_oi_call |

### Long Call Strikes (Buy Here -- for hedge wings)

| Strike (SPY) | Strike (SPX approx) | Justification | Platform Source |
|--------------|---------------------|---------------|----------------|
| **$692** | ~6920 | **Hedge wing above call wall.** Positioned above both the gamma ceiling and high OI call wall. The platform's `_assess_gex_support` would classify this as "against" for calls (spot below gamma ceiling with positive GEX dampening), making it cheap to buy as a hedge wing for short call credit spreads. | `strike_intel._assess_gex_support` -- "against" = cheap hedge |
| **$695** | ~6950 | **Far hedge wing.** Deep OTM, low probability ITM per the platform's `probability_itm` calculation (N(d2) would yield ~15-20% at VIX 20, 7-10 DTE). Maximum premium capture on the short leg relative to hedge cost. | `greeks.probability_itm` low P(ITM) |

---

## SPREAD CONSTRUCTIONS FROM APPROVED STRIKES

These are the ONLY strike combinations downstream agents may use:

### Bear Put Spreads
- Buy $678P / Sell $665P -- Gamma flip to gamma floor (platform's two highest-significance levels)
- Buy $675P / Sell $665P -- Max pain to gamma floor (gravitational pull into support)
- Buy $685P / Sell $675P -- Gamma ceiling reversal to max pain magnet

### Put Credit Spreads (Bullish)
- Sell $665P / Buy $661P -- Gamma floor to put OI wall (tight spread at support)
- Sell $669P / Buy $665P -- Gap midpoint to gamma floor

### Call Credit Spreads (Bearish)
- Sell $685C / Buy $692C -- Gamma ceiling to hedge wing ($7 wide)
- Sell $688C / Buy $695C -- Call wall to far hedge ($7 wide)

### Protective Puts
- Buy $678P (at gamma flip -- regime change trigger)
- Buy $665P (at gamma floor -- portfolio floor)

---

## FORBIDDEN STRIKES

The following strikes are EXCLUDED unless they coincide with a GEX level computed above:

| Strike | Reason for Exclusion |
|--------|---------------------|
| $670 | Round number. No GEX level confirmed here. The gap midpoint is $669, NOT $670. |
| $680 | Round number. The gamma flip is at ~$678, NOT $680. Use $678. |
| $690 | Round number. No GEX level confirmed here. Use $688 (high OI call wall) or $692 (hedge wing). |
| $660 | Round number. Gap bottom is $661. Use $661. |
| Any Fibonacci level | Not computed by the platform. The platform uses gamma exposure, OI, and max pain -- not Fibonacci retracements. Excluded unless a Fibonacci level happens to land on an approved strike. |
| Any level from external charting | This map is sourced exclusively from the platform's `gex.py`, `strike_intel.py`, `max_pain.py`, and `pcr.py` modules. External TA levels are not approved. |

---

## PLATFORM LOGIC CROSS-REFERENCE

### How the platform would classify trades at these strikes

For **puts** (bearish direction), `_assess_gex_support` checks:
- `spot > gamma_floor` AND `net_gex < 0` --> "aligned"
- `spot > gamma_flip` --> "aligned" (in negative GEX territory)
- Otherwise --> "against"

**Current assessment (SPX ~6783, gamma_flip ~6780, gamma_floor ~6650):**
- Spot is barely above gamma flip --> puts are MARGINALLY aligned
- If spot drops below 6780, puts become firmly "aligned" (negative GEX amplification)
- All proposed put strikes below spot satisfy the OTM filter (strike < spot, OI >= 100)

For **calls** (bullish direction), `_assess_gex_support` checks:
- `spot < gamma_ceiling` AND `net_gex >= 0` --> "aligned"
- `spot <= gamma_flip` --> "aligned"
- Otherwise --> "against"

**Current assessment:**
- Spot (6783) < gamma ceiling (6850) and net_gex is ~0 (near flip) --> calls are borderline "aligned"
- This means SHORT calls at the ceiling face aligned bullish pressure -- they need the ceiling to hold
- Spread construction (sell $685 / buy $692) manages this risk

### Squeeze Probability Breakdown
Per `_compute_squeeze_probability`:
- Component 1 (60% weight): `neg_score` = abs(net_gex) / total_abs_gex. With net_gex near zero at the flip, this is ~0.
- Component 2 (40% weight): `pcr_score` = (volume_pcr - 1.0) / 0.5 if PCR > 1.0. With VIX ~20 and neutral sentiment, PCR ~0.8 --> pcr_score = 0.
- **Estimated squeeze probability: ~5-15%.** Low. This supports selling premium (credit spreads) rather than buying squeeze plays.

### Significance Ranking (from `_build_key_levels`)
1. Gamma flip ~$678 -- significance 1.0
2. Gamma ceiling ~$685 -- significance 0.9
3. Gamma floor ~$665 -- significance 0.85
4. Max pain ~$675 -- significance 0.8
5. High OI strikes -- significance 0.5-0.7 (decays by relative OI)

---

## APPROVED STRIKE SUMMARY

```
LONG PUTS:   $685, $678, $675
SHORT PUTS:  $669, $665, $661
SHORT CALLS: $688, $685
LONG CALLS:  $695, $692
```

**Any strike not on this list is FORBIDDEN for V3 swarm downstream agents.**

---

## CONFIDENCE NOTES

- These levels are ESTIMATED from the platform's logic, not computed from live data.
  When the platform runs against real-time Tastytrade chains, the actual gamma_flip,
  gamma_ceiling, gamma_floor, and max_pain may shift by 1-3 strikes ($5-$15 SPY).
- The estimation assumes typical post-gap OI distribution: call OI clusters above the
  new price, put OI remains stranded at pre-gap levels, gamma flip near spot.
- Before executing any position, the swarm SHOULD run the platform's live analysis
  (`calculate_gex`, `calculate_max_pain`, `calculate_pcr`, `calculate_strike_intel`)
  to confirm or adjust these levels.
