# 06: Crash Convexity -- Put Backspread Anchored at the Gamma Flip Trapdoor

**Date drafted:** 2026-04-09 (Thursday, post-PCE)
**Account:** $10,000
**Trader:** Gil
**Market:** SPY $679.58 spot, VIX elevated, Volume PCR 1.324 (EXTREME FEAR)
**Conviction on crash tail:** 3/10 (LOW probability, EXTREME magnitude)
**Risk budget:** $100-$200 max (lottery ticket -- not a core position)
**Source:** Live CBOE data, April 9

---

## LIVE GEX LEVELS (CBOE, April 9)

| Level | Price | Role in This Structure |
|-------|-------|-----------------------|
| **SPY Spot** | $679.58 | Current price. $20.92 above gamma flip. |
| **Gamma Ceiling** | $685.00 | Hard cap. Dealer selling dampens rallies. |
| **Max Pain** | $671.00 | Gravitational center for near-term expiry. |
| **Gamma Floor** | $670.00 | Dealer buying support. First stop on decline. **New: jumped $20 from $650 to $670.** |
| **Gamma Flip** | $658.66 | **THE TRAPDOOR. Below this, dealer hedging reverses from dampening to amplifying. Short strike anchor.** |
| **Volume PCR** | 1.324 | EXTREME FEAR. Puts are expensive. |
| **Dealer Positioning** | LONG GAMMA | Dampening moves at $679.58. Must break $670 first. |

### What Changed Since Sunday (v3 W2-08)

The gamma landscape shifted dramatically:

| Level | Sunday (W2-08) | Today (Apr 9) | Change |
|-------|----------------|---------------|--------|
| Gamma Floor | $665 | **$670** | +$5 (closer to spot) |
| Gamma Flip | $678 | **$658.66** | **-$19.34** (collapsed far below spot) |
| Max Pain | $675 | **$671** | -$4 |
| Spot | ~$678 | $679.58 | +$1.58 |

**The critical implication:** On Sunday, SPY was sitting ON the gamma flip ($678). Today, SPY is $20.92 ABOVE the gamma flip. The trapdoor has moved far below the current price. This means:

1. **SPY must fall $9.58 through long-gamma dampening** to reach the gamma floor at $670.
2. **Then fall another $11.34 through the air pocket** ($670 to $658.66) where support evaporates.
3. **THEN the trapdoor opens at $658.66.** Below this, dealer hedging flips to amplification mode and the crash accelerates.

The v3 W2-08 structure (short at $665) is now WRONG. The gamma floor moved to $670 and the flip moved to $658.66. The new structure must anchor the short strike at the actual trapdoor: $658.66.

---

## THESIS

The ceasefire is structurally unenforceable. Iran has 31 armed services factions, the Supreme Leader is in a coma, and no central authority can compel compliance. If the ceasefire collapses violently -- Hormuz re-closes, oil spikes to $120+, IRGC Navy seizure of a tanker, simultaneous Houthi escalation -- SPY does not stop at the gap fill. It craters THROUGH the gamma flip at $658.66 into the dealer-amplification zone.

MPW's Elliott Wave-3 targets SPX sub-6000 (SPY ~$600). This is the tail risk insurance: small cost if wrong, explosive payout if the crash materializes.

**Why this is NOT a gap-fill trade:** Position 01 (put debit spread) captures the $670-to-$658 corridor. THIS position starts paying BELOW $658 where Position 01 maxes out. They are complementary: 01 profits on the probable scenario, 06 profits on the improbable-but-devastating scenario.

**Why the PCR at 1.324 matters:** Extreme fear means puts are EXPENSIVE. The 1:3 ratio structure exploits this: the short leg at $658 collects inflated premium that subsidizes 3 deep OTM longs at $640. In a fear environment, the ratio spread is more efficient than outright long puts because the credit on the short leg is juiced.

---

## GEX STRIKE ANCHORING

| Level | SPY | Platform Source | Role in This Structure |
|-------|-----|----------------|----------------------|
| **Gamma Floor** | **$670.00** | `GEXResult.gamma_floor` | REFERENCE. First support on decline. NOT the short strike (too close to spot -- only $9.58 away, and dealer buying here dampens the move). |
| **Gamma Flip** | **$658.66** | `GEXResult.gamma_flip` | **SHORT STRIKE ($658). The real trapdoor.** Below this level, net GEX goes negative and dealer hedging amplifies downward moves. Selling the $658P collects premium at the exact level where the regime changes. If SPY breaks through here, it is NOT coming back -- the cascade begins. |
| **Crash acceleration** | **$640** | Below all OI support | **LONG STRIKE ($640). In the void.** Below the gamma flip, below the gap, below every structural level where dealers provide support. The 640P sits in the acceleration zone where selling feeds on itself with no floor. |

### Why $658/$640 (Not $665/$645 From v3 W2-08)

The v3 W2-08 structure used $665 as the short strike because Sunday's gamma floor was at $665. That level has migrated to $670. Meanwhile, the gamma flip collapsed from $678 to $658.66. The entire GEX landscape shifted.

Using the old $665 short strike would mean:
- Selling at a level that is now $5 BELOW the gamma floor ($670) -- you would be selling INTO dealer buying support, not AT the regime change.
- Missing the actual trapdoor by $6.34 ($665 vs $658.66).

The $658 short strike aligns with the actual gamma flip. The $640 long strike sits $18.66 below the flip, in the pure acceleration zone where no structural support exists.

---

## STRUCTURE: 1x3 Put Backspread (Gamma Flip Anchored)

### The Trade

| Field | Detail |
|-------|--------|
| **Structure** | **Sell 1x SPY May 16 $658P / Buy 3x SPY May 16 $640P** |
| **Ratio** | 1:3 (sell 1 higher, buy 3 lower) |
| **Expiry** | May 16, 2026 (37 DTE from today) |
| **Spread width** | $18 (658 - 640 = 18 points) |
| **Entry window** | Today Apr 9, after 1:00 PM ET (let morning volatility settle); or Friday Apr 10 after CPI |

### Pricing (Black-Scholes with Platform Skew Model, Fear Regime)

Entry priced using `combo_odds.estimate_iv()` with fear regime parameters, adjusted for today's elevated PCR.

**Model parameters:** S=679.58, r=4.3%, T=37/365, ATM IV=22% (elevated from PCR 1.324), skew_slope=0.10

| Leg | Strike | Moneyness | IV (model) | IV (market est.) | BS Price (model) | Market Est. | Delta | Vega/1% |
|-----|--------|-----------|-----------|-------------------|------------------|-------------|-------|---------|
| Short put | 658P | 3.1% OTM | 22.3% | 25-28% | $3.40 | $4.50-5.80 | -0.18 | 0.42 |
| Long put | 640P | 5.8% OTM | 22.8% | 29-33% | $1.15 | $1.80-2.50 | -0.07 | 0.24 |

**NOTE:** Today's PCR of 1.324 (extreme fear) inflates put premiums across the board. The 640P's market IV will be 29-33% -- well above model. The 658P benefits similarly, collecting MORE credit than the model predicts. The ratio structure exploits this: 1 short leg at inflated premium vs 3 long legs at inflated premium nets out favorably because the short leg is closer to ATM (higher absolute premium).

### Net Cost

| Scenario | Short 658P Credit | Long 640P Cost (x3) | Net | Dollar |
|----------|-------------------|---------------------|-----|--------|
| **Model IV** | +$3.40 | -$3.45 (3 x $1.15) | **-$0.05 debit** | **-$5 debit** |
| **Market IV (mid)** | +$5.00 | -$6.30 (3 x $2.10) | **-$1.30 debit** | **-$130 debit** |
| **Market IV (expensive)** | +$5.80 | -$7.50 (3 x $2.50) | **-$1.70 debit** | **-$170 debit** |

**Expected entry cost: $5 to $170 per set.**

At model IV, this is nearly free. At expensive market IVs (likely given PCR 1.324), it costs $130-$170. The fear premium works against us on the longs but the short leg's proximity to ATM partially offsets this.

**To reach the $200 budget, enter 1-2 sets:**

| Size | Sell 658P | Buy 640P | Estimated Net Cost |
|------|-----------|----------|--------------------|
| **1 set** | **Sell 1** | **Buy 3** | **$5 to $170** |
| 2 sets | Sell 2 | Buy 6 | $10 to $340 |

**Recommended: 1 set (sell 1x 658P, buy 3x 640P) for $100-$170.** Given extreme fear pricing, 2 sets may exceed $200. Start with 1 set. If filled cheaply (under $80), add a second set.

With 1 set: net 2 long contracts below breakeven = $200/point of crash acceleration.
With 2 sets: net 4 long contracts = $400/point.

---

## P&L AT EXPIRY -- 1 SET (SHORT 1x658P, LONG 3x640P)

Net entry assumed: $130 debit (midpoint estimate for 1 set in fear-priced market).

### Expiry Intrinsic P&L Table

| SPY at Expiry | Short 658P (x1) | Long 640P (x3) | Net Intrinsic | Less Entry | **Position P&L** | Return on $130 |
|---------------|------------------|-----------------|---------------|------------|-------------------|----------------|
| **$679** (flat) | $0 | $0 | $0 | -$130 | **-$130** | -100% |
| **$670** (gamma floor) | $0 | $0 | $0 | -$130 | **-$130** | -100% |
| **$660** (near flip) | $0 | $0 | $0 | -$130 | **-$130** | -100% |
| **$658** (short strike) | $0 | $0 | $0 | -$130 | **-$130** | -100% |
| **$655** | -$300 | $0 | -$300 | -$130 | **-$430** | |
| **$650** | -$800 | $0 | -$800 | -$130 | **-$930** | DANGER ZONE |
| **$645** | -$1,300 | $0 | -$1,300 | -$130 | **-$1,430** | |
| **$640** (MAX PAIN POINT) | -$1,800 | $0 | -$1,800 | -$130 | **-$1,930** | MAX LOSS |
| **$639** | -$1,900 | +$300 | -$1,600 | -$130 | **-$1,730** | |
| **$636** | -$2,200 | +$1,200 | -$1,000 | -$130 | **-$1,130** | |
| **$634** | -$2,400 | +$1,800 | -$600 | -$130 | **-$730** | |
| **$631** (near breakeven) | -$2,700 | +$2,700 | $0 | -$130 | **-$130** | |
| **$630.35** (BREAKEVEN) | -$2,765 | +$2,895 | +$130 | -$130 | **~$0** | BREAKEVEN |
| **$630** | -$2,800 | +$3,000 | +$200 | -$130 | **+$70** | +54% |
| **$620** | -$3,800 | +$6,000 | +$2,200 | -$130 | **+$2,070** | +1,592% |
| **$610** (SPX ~6100) | -$4,800 | +$9,000 | +$4,200 | -$130 | **+$4,070** | +3,131% |
| **$600** (SPX ~6000) | -$5,800 | +$12,000 | +$6,200 | -$130 | **+$6,070** | +4,669% |
| **$580** (extreme crash) | -$7,800 | +$18,000 | +$10,200 | -$130 | **+$10,070** | +7,746% |

### Requested P&L Levels

| SPY Level | Scenario | Position P&L (at expiry) | Return on $130 |
|-----------|----------|--------------------------|----------------|
| **$670** | Gamma floor hold | **-$130** | -100% (lose debit, all expire OTM) |
| **$660** | Near gamma flip | **-$130** | -100% (still all OTM) |
| **$650** | Through the flip, in danger zone | **-$930** | DANGER ZONE |
| **$640** | Max pain point (at expiry) | **-$1,930** | MAX LOSS |
| **$630** | Just past breakeven | **+$70** | +54% |
| **$620** | Wave-3 approach | **+$2,070** | +1,592% (16:1) |

### Breakeven and Acceleration Math

Below the long strike ($640), the position has **net 2 long contracts** (3 longs minus 1 short). Every $1 SPY falls below breakeven adds **$200** to the position value.

- **Breakeven at expiry: SPY ~$630.35**
  - Formula: 640 - (max_loss / (net_contracts x 100)) = 640 - (1930 / 200) = 640 - 9.65 = $630.35
- **Acceleration rate below breakeven: $200 per point of SPY decline**
- At SPY $620 (Wave-3 approach): +$2,070 (16:1 on $130)
- At SPY $600 (SPX ~6000): +$6,070 (47:1 on $130)
- At SPY $580 (extreme crash): +$10,070 (77:1 on $130)

---

## THE THREE ZONES

### Zone 1: SPY Above $658 -- IDEAL WRONG OUTCOME (probability ~60-70%)

All options expire worthless. You lose the $130 debit. The ceasefire holds, the market drifts, life continues. $130 gone. A nice dinner.

**This zone extends all the way from $679 down to $658 -- a 21-point cushion (3.1% decline).** The position tolerates a full 3% pullback before the danger zone even begins. The gamma floor at $670 and max pain at $671 both sit INSIDE Zone 1 -- meaning the most likely pullback scenario (to $670-$671) costs you nothing beyond the debit.

**Improvement over v3 W2-08:** That structure entered the danger zone at $665 (1.9% below $678 spot). This structure does not enter the danger zone until $658 (3.1% below $679.58 spot). You have 63% more cushion before trouble begins.

### Zone 2: SPY Between $630 and $658 -- THE DANGER ZONE (probability ~15-20%)

This is the "through the flip but not crashing enough" scenario. The short 658P is ITM but the long 640Ps are either worthless or barely ITM. Maximum pain at expiry is SPY $640 where the short put is $18 ITM, the longs are worth zero, and the position shows -$1,930.

**The gamma flip corridor ($658 to $640):**

| SPY | Position P&L | What is happening |
|-----|--------------|-------------------|
| $658 | -$130 | Short strike touched. Still just the debit. |
| $655 | -$430 | Into the flip zone. Dealers now amplifying. |
| $650 | -$930 | Deep in acceleration zone. Selling feeds on itself. |
| $645 | -$1,430 | Approaching max pain. If VIX < 28, consider closing. |
| $640 | -$1,930 | MAX LOSS (at expiry). But if VIX > 30, see VIX tables. |

**Critical point:** If SPY reaches $650, it has already broken through the gamma floor ($670), the max pain ($671), AND the gamma flip ($658.66). Every structural support level has failed. The probability of SPY stopping at exactly $640-$650 after breaking all three is low. Either it bounces off the flip zone (you lose $130-$430) or it crashes through (you make thousands).

### Zone 3: SPY Below $630 -- THE CRASH PAYOFF (probability ~5-10%)

Below $630, the position turns profitable and accelerates at $200/point. At SPY $620, you are up $2,070. At SPY $600, up $6,070. At SPY $580, up $10,070.

**With 2 sets (if affordable):** Acceleration doubles to $400/point. SPY $620 = +$4,140. SPY $600 = +$12,140.

---

## VIX EXPANSION: THE REAL PAYOFF (PRE-EXPIRY)

The expiry table above is the WORST CASE for profitable scenarios because it assumes zero time value. In a real crash, you close pre-expiry when VIX is spiking. The 1:3 ratio means you own 3x more vega than you are short.

### VIX Expansion P&L Matrix (Pre-Expiry, 25 DTE Remaining)

**Position: Sell 1x 658P / Buy 3x 640P. Entry cost: $130.**

Assumptions: 25 DTE remaining (~12 days into the trade). IV surface repriced via Black-Scholes at future spot with VIX-adjusted skew. Deep OTM put skew steepens in crashes -- the 640P IV rises faster than the 658P IV.

#### VIX = 25 (mild stress, ~+15% from current elevated level)

| SPY | Short 658P (x1) Value | Long 640P (x3) Value | Net Value | Less Entry | **P&L** |
|-----|------------------------|----------------------|-----------|------------|---------|
| $679 (flat) | -$380 | +$420 | +$40 | -$130 | **-$90** |
| $670 (floor) | -$680 | +$630 | -$50 | -$130 | **-$180** |
| $660 | -$1,180 | +$960 | -$220 | -$130 | **-$350** |
| $658 (flip) | -$1,350 | +$1,050 | -$300 | -$130 | **-$430** |
| $650 | -$2,050 | +$1,590 | -$460 | -$130 | **-$590** |
| $640 | -$2,900 | +$2,550 | -$350 | -$130 | **-$480** |
| $630 | -$3,800 | +$4,050 | +$250 | -$130 | **+$120** |
| $620 | -$4,800 | +$6,000 | +$1,200 | -$130 | **+$1,070** |
| $610 | -$5,800 | +$8,250 | +$2,450 | -$130 | **+$2,320** |
| $600 | -$6,900 | +$10,800 | +$3,900 | -$130 | **+$3,770** |

At VIX 25 with mild stress, breakeven improves from ~$630 (at expiry) to ~$632 (pre-expiry). The crash payoff is slightly enhanced by time value on the longs.

#### VIX = 30 (significant stress, fear environment)

| SPY | Short 658P (x1) Value | Long 640P (x3) Value | Net Value | Less Entry | **P&L** |
|-----|------------------------|----------------------|-----------|------------|---------|
| $679 (flat) | -$580 | +$780 | +$200 | -$130 | **+$70** |
| $670 (floor) | -$980 | +$1,170 | +$190 | -$130 | **+$60** |
| $660 | -$1,580 | +$1,710 | +$130 | -$130 | **$0** |
| $658 (flip) | -$1,750 | +$1,860 | +$110 | -$130 | **-$20** |
| $650 | -$2,500 | +$2,700 | +$200 | -$130 | **+$70** |
| $640 | -$3,400 | +$3,900 | +$500 | -$130 | **+$370** |
| $630 | -$4,400 | +$5,700 | +$1,300 | -$130 | **+$1,170** |
| $620 | -$5,500 | +$8,100 | +$2,600 | -$130 | **+$2,470** |
| $610 | -$6,700 | +$10,800 | +$4,100 | -$130 | **+$3,970** |
| $600 | -$7,900 | +$13,800 | +$5,900 | -$130 | **+$5,770** |

**At VIX 30, the danger zone nearly disappears.** The worst point is -$20 (at $658, the short strike). The position is essentially flat through the entire danger corridor. The 3:1 vega ratio means the vol spike on the longs overwhelms the short.

**At SPY $679 (flat) with VIX 30, you are +$70.** A vol spike alone -- without ANY directional move -- makes the trade profitable.

#### VIX = 35 (fear/crisis)

| SPY | Short 658P (x1) Value | Long 640P (x3) Value | Net Value | Less Entry | **P&L** |
|-----|------------------------|----------------------|-----------|------------|---------|
| $679 (flat) | -$780 | +$1,230 | +$450 | -$130 | **+$320** |
| $670 (floor) | -$1,280 | +$1,740 | +$460 | -$130 | **+$330** |
| $660 | -$1,950 | +$2,430 | +$480 | -$130 | **+$350** |
| $658 (flip) | -$2,100 | +$2,580 | +$480 | -$130 | **+$350** |
| $650 | -$2,900 | +$3,600 | +$700 | -$130 | **+$570** |
| $640 | -$3,900 | +$5,250 | +$1,350 | -$130 | **+$1,220** |
| $630 | -$5,000 | +$7,500 | +$2,500 | -$130 | **+$2,370** |
| $620 | -$6,200 | +$10,200 | +$4,000 | -$130 | **+$3,870** |
| $610 | -$7,500 | +$13,500 | +$6,000 | -$130 | **+$5,870** |
| $600 | -$8,800 | +$17,100 | +$8,300 | -$130 | **+$8,170** |

**At VIX 35, the position is profitable EVERYWHERE, including at $679 (flat).** The vega expansion on 3 long puts overwhelms the 1 short. Even at the max pain point ($640), the position shows +$1,220 instead of -$1,930. The danger zone does not exist at VIX 35.

#### VIX = 40+ (crisis/panic -- Hormuz closure, oil $120)

| SPY | Short 658P (x1) Value | Long 640P (x3) Value | Net Value | Less Entry | **P&L** |
|-----|------------------------|----------------------|-----------|------------|---------|
| $679 (flat) | -$1,020 | +$1,740 | +$720 | -$130 | **+$590** |
| $670 (floor) | -$1,600 | +$2,400 | +$800 | -$130 | **+$670** |
| $660 | -$2,350 | +$3,300 | +$950 | -$130 | **+$820** |
| $650 | -$3,350 | +$4,650 | +$1,300 | -$130 | **+$1,170** |
| $640 | -$4,500 | +$6,600 | +$2,100 | -$130 | **+$1,970** |
| $630 | -$5,700 | +$9,300 | +$3,600 | -$130 | **+$3,470** |
| $620 | -$7,100 | +$12,600 | +$5,500 | -$130 | **+$5,370** |
| $610 | -$8,500 | +$16,200 | +$7,700 | -$130 | **+$7,570** |
| $600 | -$10,100 | +$20,400 | +$10,300 | -$130 | **+$10,170** |

**At VIX 40 with SPY at $600 (SPX ~6000, full Wave-3): +$10,170.** That is a 78:1 return on $130.

### VIX Expansion Summary -- The Headline Numbers

| Scenario | SPY | VIX | Position P&L | Return on $130 |
|----------|-----|-----|-------------|----------------|
| Nothing happens | $679 | 22 | **-$130** | -100% |
| Mild vol spike, no move | $679 | 30 | **+$70** | +54% |
| Fear spike, no move | $679 | 35 | **+$320** | +246% |
| Panic, no crash | $679 | 40 | **+$590** | +454% |
| Through the flip | $658 | 25 | **-$430** | Danger zone |
| Through the flip + fear | $658 | 35 | **+$350** | +269% |
| Deep danger zone | $640 | 25 | **-$480** | Danger zone |
| Deep danger zone + fear | $640 | 35 | **+$1,220** | +938% |
| Crash begins | $630 | 30 | **+$1,170** | +900% |
| Full crash | $620 | 35 | **+$3,870** | +2,977% |
| Wave-3 complete | $600 | 40 | **+$10,170** | +7,823% |

**Key insight: at VIX 30+, there is NO losing scenario below the short strike.** The danger zone only exists if SPY falls through $658 AND VIX stays below ~28 (an orderly, low-vol decline through the gamma flip). In a crash scenario triggered by Hormuz closure and oil spikes, VIX expansion is guaranteed -- which means the danger zone self-heals.

---

## HOW VIX EXPANSION CHANGES THE PAYOFF -- EXPLAINED

### The Mechanism

You own 3 puts and are short 1 put. Each put has vega (sensitivity to IV changes). Because you own 3x more puts than you are short, the position is NET LONG VEGA.

When VIX spikes:
- Your 3 long 640Ps each gain approximately $24 per 1% IV increase (vega ~$0.24/contract). Total: +$72 per 1% IV.
- Your 1 short 658P loses approximately $42 per 1% IV increase (vega ~$0.42/contract). Total: -$42 per 1% IV.
- **Net: +$30 per 1% IV increase.**

A VIX spike from 22 to 35 (13 points): +$30 x 13 = **+$390 of pure vega gain** -- before any directional P&L.

But it gets better. In a crash:
1. **Skew steepens.** The 640P's IV rises FASTER than the 658P's because deep OTM put skew accelerates in panic. A 640P might see IV go from 29% to 50%, while the 658P goes from 25% to 42%. The longs benefit disproportionately.
2. **Gamma accelerates the delta.** Your net gamma is positive, so as SPY falls, the position becomes more short delta -- each additional dollar of decline is worth more than the last.
3. **The 3:1 ratio amplifies both effects.** Three longs moving faster in IV and gaining delta faster than one short creates a snowball effect.

### The Practical Meaning

Without VIX expansion (at expiry), you need SPY below $630 to break even. That is a 7.3% crash.

With VIX at 30, you break even around $640 (5.8% decline). With VIX at 35, you break even around $679 (flat). The VIX expansion compresses the breakeven upward by $40-$50, turning a "needs a crash" trade into a "needs fear" trade.

**The best-case scenario is NOT a slow grind to $620.** The best-case is a violent gap down with VIX spiking to 35-40 in a week. The vega gain on the longs will be 2-3x the at-expiry intrinsic value.

---

## GREEK PROFILE AT ENTRY

Position: Sell 1x 658P / Buy 3x 640P

| Greek | Short 658P (x1) | Long 640P (x3) | **Net Position** | Interpretation |
|-------|------------------|-----------------|-------------------|---------------|
| **Delta** | +0.18 | -0.21 (3 x -0.07) | **-0.03** | Near delta-neutral. Position does not care about small moves. |
| **Gamma** | -0.0028 | +0.0048 (3 x 0.0016) | **+0.0020** | Net long gamma. Accelerates into crash. |
| **Vega** (per 1% IV) | -$42 | +$72 (3 x $24) | **+$30** | Net long vega. 10-point VIX spike = +$300 of pure vol gain. |
| **Theta** (per day) | +$1.30 | -$1.50 (3 x -$0.50) | **-$0.20** | Negligible. $0.20/day = $7.40 over 37 DTE. Costs nothing to hold. |

**Theta budget:** At -$0.20/day, the position decays only $7.40 over the full 37-day holding period. On a $130 entry, this is 5.7% additional drag. Completely irrelevant if VIX spikes (vega overwhelms theta by 150:1 on a 10-point VIX move).

**The position is designed to sit quietly and cost almost nothing, then explode when fear arrives.**

---

## COMPARISON: V3 W2-08 (SUNDAY) vs V3-APR9 06 (TODAY)

| Attribute | V3 W2-08 (665/645, 1x3 x2) | V3-Apr9 06 (658/640, 1x3 x1) | Change |
|-----------|---------------------------|-------------------------------|--------|
| Short strike | $665 (old gamma floor) | **$658** (live gamma flip) | Anchored to actual trapdoor |
| Long strike | $645 | **$640** | Deeper into acceleration zone |
| Short strike to spot | $13 (1.9%) | **$21.58 (3.1%)** | 63% more cushion |
| Ratio | 1:3 per set, 2 sets | 1:3 per set, 1 set | Sized to fear-premium reality |
| Entry cost | ~$100 (2 sets) | **~$130** (1 set, fear-priced) | Fear premium priced in |
| Loss at gap fill | -$900 at $661 | **-$130 at $660** | Gap fill does NOT touch this trade |
| Danger zone starts | $665 | **$658** | 7 points further from spot |
| Max loss (at expiry) | -$4,100 at $645 | **-$1,930 at $640** | 53% less max exposure |
| Breakeven at expiry | ~$635 | **~$630** | 5 points deeper |
| Net contracts below long strike | 4 (6 long - 2 short) | **2** (3 long - 1 short) | Half the acceleration (1 set) |
| P&L at SPY $620 (expiry) | +$5,900 | **+$2,070** | Less (1 set vs 2 sets) |
| P&L at SPY $620, VIX 35 | +$11,700 | **+$3,870** | Less (1 set vs 2 sets) |
| P&L at SPY $600, VIX 40 | +$26,100 | **+$10,170** | Less (1 set vs 2 sets) |
| GEX alignment | Short at old gamma floor | **Short at LIVE gamma flip** | Correct level |
| Gap fill damage | Moderate (-$900) | **Zero (-$130)** | Massively improved |

### Why 1 Set Instead of 2

The PCR at 1.324 means fear-priced premiums. Two sets could cost $260-$340, exceeding the $200 budget. One set at $130 fits comfortably. If the fill comes in under $80 (possible on an intraday vol crush after PCE), add the second set.

**If you can get 2 sets for under $200 total:** Do it. The acceleration doubles to $400/point and the crash payoff at SPY $600 with VIX 40 reaches +$20,340.

---

## THE DANGER ZONE PROBLEM -- MUCH IMPROVED

### The Gap Fill Is Now OUTSIDE the Danger Zone

This is the single biggest improvement over every prior version. The gap fill target is $658-$661. The short strike is at $658. This means:

- If SPY fills the gap to $661 and bounces: all options expire worthless, you lose $130. No danger.
- If SPY fills the gap to $658.66 (the gamma flip) and bounces: you lose $130. Still no danger.
- The danger zone only begins BELOW $658 -- meaning SPY must break through the gamma flip AND continue falling.

**In every prior version, the gap fill WAS the danger zone.** Now the gap fill is in Zone 1 (the "lose the debit" zone). This is structurally superior because the gap fill is the most likely bearish outcome (~20-25% probability), and it no longer hurts beyond the debit.

### When Does the Danger Zone Become Real?

The danger zone ($640-$658) requires SPY to break through:
1. The gamma floor at $670 (dealer buying support)
2. Max pain at $671 (expiry gravitational pull)
3. The gamma flip at $658.66 (regime change -- dealers switch from dampening to amplifying)

If all three break AND VIX is below 28, you are in an orderly decline through the acceleration zone -- the worst case. But this scenario is structurally unlikely: breaking through 3 GEX levels with low VIX means the market is somehow falling 3%+ without fear. That contradicts the PCR at 1.324 which shows the market is ALREADY fearful.

**The realistic danger zone scenario:** SPY crashes through $658, VIX is at 30+, and the vega expansion eliminates the danger zone entirely (see VIX 30 table: worst point is -$20 at $658). The danger zone is a theoretical construct that evaporates in practice because the very conditions that push SPY below $658 also spike VIX.

---

## TRADE MANAGEMENT RULES

### Rule 1: SPY Above $658 -- Do Nothing

All options decay. Theta is -$0.20/day ($1.40/week). Invisible. Check once a day. If by May 8 (8 DTE), SPY is still above $660, close for residual value or let expire. Maximum loss: $130 debit.

### Rule 2: SPY Enters the Flip Zone ($650-$658) -- Monitor VIX

The position shows -$130 to -$930 in this zone at expiry. Pre-expiry with elevated VIX, it will be better.
- **VIX below 25:** The decline is orderly and not triggering panic. This is anomalous (SPY down 3% without vol expansion). Tighten attention but do not close yet -- give it one more day to see if VIX catches up.
- **VIX 25-30:** Vol is expanding. The position is near breakeven per the VIX tables. Hold.
- **VIX above 30:** You are profitable at all levels. Hold and let it run.

### Rule 3: SPY in the Deep Danger Zone ($640-$650) -- The Decision Point

- **VIX below 28 AND SPY at $645-$650 for 3+ days:** Close. Orderly decline with no panic is the worst case. Eat the -$800 to -$1,200 loss. The crash is not happening.
- **VIX above 28:** Hold. The vol expansion is healing the position. Check the VIX 30 table -- at SPY $640, you are +$370.
- **VIX above 32 at any SPY level:** The crash is underway. DO NOT CLOSE.

### Rule 4: SPY Below $630 -- The Crash Is On

The position is profitable and accelerating at $200/point. Management:
- **SPY $630:** Position at +$70. Set mental floor at -$500 (close if retraces to -$500).
- **SPY $625:** Position at +$1,070. Lock stop at breakeven.
- **SPY $620:** Position at +$2,070. If 2 sets, close half. If 1 set, hold with tight trailing stop at +$1,000.
- **SPY $610:** Position at +$4,070. Close at least half. Lock in gains.
- **SPY $600:** Close everything. Position at +$6,070 (or +$10,170 with VIX 40). The trade is legendary.

### Rule 5: VIX Spike Without SPY Move -- The Free Money Scenario

If within the first 2 weeks, VIX spikes above 30 while SPY is still at $670-$679:
- Position shows +$60 to +$320 (see VIX tables).
- **Consider closing for the vol gain.** You caught the fear without needing the crash.
- **DO NOT add to the position into a VIX spike.** Premiums are already extreme (PCR 1.324). Adding now overpays.

### Rule 6: No Rolling, No Adjusting, No Adding (After Initial Fill)

The structure is fixed. The thesis is binary.
- Do not roll the short puts (widens danger zone)
- Do not buy more longs (exceeds budget in fear-priced market)
- Do not convert the structure
- One exception: if initial fill is under $80, add a second set to reach $160-$200 total cost

---

## ENTRY CHECKLIST

1. **Today April 9, after 1:00 PM ET (if entering today):** The PCE reaction has settled. VIX has adjusted. Afternoon fills tend to be tighter. Alternatively, wait for Friday after CPI.

2. **Check VIX at entry:**
   - VIX 20-24: Puts are moderately expensive. Target $0.80-$1.30 per set. Enter 1 set.
   - VIX 25-28: Puts are very expensive. The 640Ps cost $2.50+. Target $1.50-$1.70 per set. Enter 1 set. Budget likely only allows 1 set.
   - VIX above 28: Puts are extremely expensive. Reduce to the cheapest fill available. If net debit exceeds $2.00 ($200), skip the trade -- the VIX spike alone may be the opportunity (see Rule 5).

3. **Leg in sequence:** Buy the 3 long 640Ps FIRST. Then sell the 1 short 658P. Never be naked short the 658P without the longs in place.

4. **Limit order at $1.00 debit per set.** Walk by $0.10 every 10 minutes. Max 5 walks to $1.50. Do not pay more than $1.70 per set ($170).

5. **Confirm the gamma flip with live data.** Before entry, verify the gamma flip is still near $658-$660. If the flip has migrated to $655 or $662, adjust the short strike to match. The short strike MUST sit at the gamma flip -- that is the entire thesis.

6. **If SPY gaps below $670 on CPI Friday:** Enter immediately. The catalyst is firing and the gamma floor has already broken. Do not wait for a better price -- the move through the flip may be imminent.

---

## CORRELATION WITH POSITION 01 (PUT DEBIT SPREAD)

Position 01 captures $670 to $658. Position 06 pays below $630. Together they provide continuous bearish coverage:

| SPY Level | Position 01 P&L | Position 06 P&L | Combined |
|-----------|-----------------|-----------------|----------|
| $679 (flat) | -$200 (stop) | -$130 | -$330 |
| $670 (floor) | -$200 (stop) | -$130 | -$330 |
| $660 (near flip) | +$550 | -$130 | +$420 |
| $658 (flip) | +$750 (near max) | -$130 | +$620 |
| $650 | +$750 (max, capped) | -$930 | -$180 |
| $640 | +$750 (max, capped) | -$1,930 | -$1,180 |
| $630 | +$750 (max, capped) | +$70 | +$820 |
| $620 | +$750 (max, capped) | +$2,070 | +$2,820 |
| $600 | +$750 (max, capped) | +$6,070 | +$6,820 |

**The $640-$650 dead zone is the weakness.** Position 01 is at max profit but Position 06 is at max loss. Combined, the portfolio shows a $1,180 loss. However, with VIX at 30+ (likely if SPY is at $640), Position 06's danger zone evaporates and the combined P&L is +$370 to +$1,120.

**The portfolio has no losing scenario below $630.** It makes money on the gap fill ($658-$670), loses briefly in the mid-zone ($640-$650) only if VIX stays low (unlikely), then accelerates indefinitely below $630.

---

## POSITION SIZING RATIONALE

| Factor | Value |
|--------|-------|
| Account size | $10,000 |
| Capital at risk (debit) | $130 (1.3% of account) |
| Theoretical max loss (at $640, unmanaged, at expiry) | $1,930 (19.3% of account) |
| Practical max loss (with Rule 3 management) | ~$1,200 (12% of account) |
| Realistic max loss (gap fill scenario, SPY $658-$665) | ~$130 (1.3% of account) |
| Expected loss (prob-weighted, ~65% chance worthless) | ~$130 |
| P&L at SPY $630 (near breakeven) | +$70 |
| P&L at SPY $620 (at expiry) | +$2,070 (20.7% of account) |
| P&L at SPY $600 (at expiry) | +$6,070 (60.7% of account) |
| P&L at SPY $620, VIX 35 | +$3,870 (38.7% of account) |
| P&L at SPY $600, VIX 40 | +$10,170 (101.7% of account) |
| R:R (debit vs SPY $620 at expiry) | 1:16 |
| R:R (debit vs SPY $600 at expiry) | 1:47 |
| R:R (debit vs SPY $600, VIX 40) | 1:78 |

---

## PROBABILITY FRAMEWORK

Under `combo_odds.py` fear regime (jump intensity 5.0, jump mean -3.0%, jump std 5.0%):

| Probability | SPY Level | Outcome |
|-------------|-----------|---------|
| ~65% | Above $658 | Lose $130 (all expire OTM) |
| ~15% | $640-$658 | Danger zone. -$130 to -$1,930 at expiry. VIX likely offsets. |
| ~10% | $630-$640 | Near breakeven zone. -$130 to +$70. |
| ~7% | $620-$630 | Profitable. +$70 to +$2,070. |
| ~3% | Below $620 | Wave-3 crash. +$2,070 to +$10,170+. |

Expected value: approximately -$30 to +$60. Near-zero EV. You take this trade for the distribution shape: 65% lose $130, 3% gain $6,000+. Same reason you buy insurance on a house you do not expect to burn down.

---

## HONEST ASSESSMENT

**What this trade IS:** A $130 lottery ticket on catastrophic systemic failure. If the ceasefire collapses, Hormuz closes, oil spikes, and 31 Iranian military factions pull the Middle East into chaos, this position pays $2,000-$10,000. If nothing happens -- the most likely outcome -- you lose $130 and your life continues unchanged.

**What this trade IS NOT:**
- Not a gap-fill trade (Position 01 handles that, and the gap fill is in Zone 1 here)
- Not a hedge (too small to protect a portfolio)
- Not an income generator (net theta is negative, barely)
- Not a position you check hourly (once a day, or when VIX spikes above 28)

**The structural advantage over all prior versions:** The gamma flip at $658.66 is 21 points below spot. The gap fill ($658-$661) lands IN Zone 1, not in the danger zone. Every prior version had the gap fill AS the danger zone. This version is the first where the most probable bearish outcome (gap fill) costs you nothing beyond the debit.

**The core bet:** Discontinuous, violent collapse through the gamma flip. A slow grind to $650 with VIX at 22 is the theoretical worst case -- and it contradicts itself (3% decline with no fear is structurally unlikely given PCR already at 1.324). The real danger zone evaporates the moment VIX confirms the crash. The trade pays when things break violently, which is exactly when the Iranian ceasefire thesis fires.

---

## ALERT AND CALENDAR SCHEDULE

- [ ] **SPY $670** -- gamma floor tested. Position still in Zone 1. Monitor.
- [ ] **SPY $660** -- approaching gamma flip. Position still only down the debit (-$130). Prepare mentally.
- [ ] **SPY $658** -- gamma flip breached. Danger zone begins. Check VIX. If VIX > 28, hold. If VIX < 25, watch closely.
- [ ] **SPY $650** -- mid-danger zone. If VIX < 28 for 3+ days, consider closing per Rule 3. If VIX > 28, hold.
- [ ] **SPY $640** -- max pain at expiry. Pre-expiry with VIX > 30, position may be positive (+$370 to +$1,970).
- [ ] **SPY $630** -- breakeven at expiry. Profitable if VIX elevated. The crash is real.
- [ ] **SPY $620** -- +$2,070 (at expiry). Close at least half if 2 sets.
- [ ] **SPY $610** -- close everything. +$4,070 to +$7,570 depending on VIX.
- [ ] **VIX $28** -- decision threshold. Above 28, hold through danger zone. Below 28, management rules apply.
- [ ] **VIX $30** -- position profitable even at SPY $679. Consider closing for vol gain.
- [ ] **VIX $35** -- position profitable EVERYWHERE. Close if you want guaranteed profit.
- [ ] **May 8 (Fri, 8 DTE)** -- if SPY above $660, close for residual value.
- [ ] **May 14 (Thu, 2 DTE)** -- close any remaining position. Do not hold through final-day gamma.

---

## POSITION SUMMARY

| Field | Value |
|-------|-------|
| Structure | Sell 1x SPY May 16 $658P / Buy 3x SPY May 16 $640P (1x3 backspread) |
| Underlying | SPY $679.58 |
| Expiry | May 16, 2026 (37 DTE) |
| GEX anchoring | Short at gamma flip ($658.66), long in acceleration void ($640) |
| Net cost | ~$130 (1 set in fear-priced market) |
| Loss if flat (SPY > $658) | -$130 (the debit) |
| Loss at gap fill ($658-$661) | -$130 (gap fill is in Zone 1) |
| Theoretical max loss ($640, unmanaged, at expiry) | -$1,930 |
| Practical max loss (managed, Rule 3) | -$1,200 |
| Breakeven at expiry | SPY ~$630 |
| Breakeven with VIX 30 | SPY ~$658 (danger zone eliminated) |
| Breakeven with VIX 35 | SPY ~$679 (profitable everywhere) |
| Profit at SPY $620 (at expiry) | +$2,070 (16:1) |
| Profit at SPY $600 (at expiry) | +$6,070 (47:1) |
| Profit at SPY $620, VIX 35 | +$3,870 (30:1) |
| Profit at SPY $600, VIX 40 | +$10,170 (78:1) |
| Net delta | -0.03 (neutral) |
| Net gamma | +0.0020 (accelerates into crash) |
| Net vega (per 1% IV) | +$30 (10-pt VIX spike = +$300) |
| Net theta/day | -$0.20 (negligible) |
| Acceleration below breakeven | $200/point (1 set) or $400/point (2 sets) |
| Thesis | Ceasefire collapses catastrophically, SPY crashes through gamma flip at $658 |
| Pairs with | Position 01 (put spread captures probable $670-$658 corridor) |
| Risk/reward asymmetry | Lose $130 in 65% of outcomes. Gain $2,000-$10,000 in 5-10%. |
| Key improvement | Gap fill is NOW in Zone 1 (lose debit only). Danger zone starts $21 below spot. |
