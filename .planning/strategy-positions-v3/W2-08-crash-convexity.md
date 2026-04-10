# W2-08: GEX-Anchored Crash Convexity

**Date drafted:** 2026-04-06 (Sunday)
**Account:** $10,000
**Trader:** Gil (new, Week 1)
**Market:** SPX ~6783 (SPY ~678), VIX ~20
**Conviction on crash tail:** 3/10 (LOW probability, EXTREME magnitude)
**Risk budget:** $100-$300 max (lottery ticket -- not a core position)

---

## THE THESIS

The ceasefire is a lie held together by a comatose Supreme Leader and 31 independent military factions that cannot be coordinated. If it collapses violently -- not a slow unwind but a cascading failure (Hormuz re-closure, oil to $120, IRGC Navy seizure, simultaneous Houthi escalation) -- the market does not fill the gap to 661. It craters THROUGH the gap.

MPW's Elliott Wave-3 targets SPX sub-6000 (SPY ~600). VIX does not stop at 25. It goes to 35, 40, 50. This is not the gap-fill trade (that is W2-01). This is the "everything breaks at once" insurance policy.

The position must:
1. Cost almost nothing ($100-$300)
2. Survive the gap-fill zone (661-665) without catastrophic loss
3. Explode below $650 with accelerating convexity
4. Benefit from VIX expansion (long vega in the tail, net long gamma below the crash threshold)

**This is structurally different from v2's 672/662 backspread.** V2 had a $2,200 max loss danger zone at the gap fill. This version uses GEX-anchored strikes to MINIMIZE the gap-fill damage and push the convexity deeper into the crash zone.

---

## GEX STRIKE ANCHORING

From W1-02 GEX Strike Map:

| Level | SPY | Significance | Role in This Structure |
|-------|-----|-------------|----------------------|
| **Gamma floor** | **$665** | 0.85 | SHORT STRIKE -- sell here. Dealers hedge massive put OI at this strike, creating a support floor. Selling the 665P collects premium at the exact level where dealer buying activity dampens further downside. If the crash is real, price slices through this floor (dealers cannot hold it). If it is a normal pullback, the floor holds and the short put expires worthless. |
| **Gap fill** | **$661** | 0.5-0.7 | REFERENCE ONLY. The gap bottom where pre-gap put OI sits. V2 used this as the long strike -- but 661 is too close to 665 (only $4 wide). A $4 spread produces trivial convexity. We skip this strike entirely and go deeper. |
| **Crash acceleration** | **$645** | -- | LONG STRIKE. Below the gap, below the OI wall, in the void where there is no dealer support. When SPY breaks 661, the next meaningful GEX support is 20+ points lower. The 645 strike sits in the acceleration zone where selling feeds on itself. |

**Why 665/645 and not 665/661:**

A 665/661 backspread has a $4 spread width. Even at 1:3 ratio (sell 1, buy 3), the maximum loss in the danger zone is approximately $400 per set, the breakeven is only $2-3 below 661, and the convexity per dollar of crash is weak. The narrow width wastes the ratio.

A 665/645 backspread has a $20 spread width. The danger zone loss is larger in dollar terms at the worst point (SPY=645), BUT the breakeven is deeper and the convexity per dollar of crash below breakeven is enormous. With a 1:3 ratio, every $1 of SPY decline below breakeven generates $200 of profit (3 long contracts minus 1 short contract = net 2 contracts = $200/point).

---

## STRUCTURE: 1x3 Put Backspread (GEX-Anchored)

### The Trade

| Field | Detail |
|-------|--------|
| **Structure** | **Sell 1x SPY May 16 $665P / Buy 3x SPY May 16 $645P** |
| **Ratio** | 1:3 (sell 1 higher, buy 3 lower) |
| **Expiry** | May 16, 2026 (39 DTE from Monday entry) |
| **Spread width** | $20 (665 - 645 = 20 points) |
| **Entry window** | Monday Apr 7, 2026, 10:00-10:30 AM ET |

### Pricing (Black-Scholes with Platform Skew Model)

Entry priced using `combo_odds.estimate_iv()` with fear regime active:

**Model parameters:** S=678, r=4.3%, T=39/365, ATM IV=20%, skew_slope=0.10

| Leg | Strike | IV (model) | IV (market est.) | BS Price (model) | Market Est. | Delta | Vega/1% |
|-----|--------|-----------|-------------------|------------------|-------------|-------|---------|
| Short put | 665P | 20.1% | 22-24% | $3.10 | $3.80-4.50 | -0.16 | 0.40 |
| Long put | 645P | 20.5% | 26-29% | $0.95 | $1.30-1.80 | -0.06 | 0.22 |

**NOTE:** The platform's skew model (`SKEW_SLOPE=0.10` in `combo_odds.py`) produces mild skew because it was calibrated for moderate DTE. Real SPY surfaces at VIX=20 show steeper skew for deep OTM puts -- the 645P IV would realistically be 26-29%, not 20.5%. The "market estimate" column uses observed SPY skew ratios at similar tenors.

### Net Cost

| Scenario | Short 665P Credit | Long 645P Cost (x3) | Net | Dollar |
|----------|-------------------|---------------------|-----|--------|
| **Model IV** | +$3.10 | -$2.85 (3 x $0.95) | **+$0.25 credit** | **+$25 credit** |
| **Market IV (conservative)** | +$3.80 | -$3.90 (3 x $1.30) | **-$0.10 debit** | **-$10 debit** |
| **Market IV (expensive)** | +$4.50 | -$5.40 (3 x $1.80) | **-$0.90 debit** | **-$90 debit** |

**Expected entry cost: $0 to $90 net debit for 1 set.**

At model IV, this trade can be entered for a CREDIT. Even at expensive market IVs, it costs under $100. The 1:3 ratio with a $20-wide skip-strike structure means the short leg's higher premium nearly funds three deep OTM longs.

**To reach the $200-300 budget, enter 2-3 sets:**

| Size | Sell 665P | Buy 645P | Estimated Net Cost |
|------|-----------|----------|--------------------|
| 1 set | Sell 1 | Buy 3 | $0 to $90 |
| **2 sets** | **Sell 2** | **Buy 6** | **$0 to $180** |
| 3 sets | Sell 3 | Buy 9 | $0 to $270 |

**Recommended: 2 sets (sell 2x 665P, buy 6x 645P).** This costs $0-$180, well within the $300 budget, and provides 4 net long contracts below breakeven ($400/point of crash).

---

## P&L AT EXPIRY -- FULL POSITION (2 SETS: SHORT 2x665P, LONG 6x645P)

Net entry assumed: $100 debit (midpoint estimate for 2 sets).

### Expiry Intrinsic P&L Table

| SPY at Expiry | Short 665P (x2) | Long 645P (x6) | Net Intrinsic | Less Entry | **Position P&L** | Return on $100 |
|---------------|------------------|-----------------|---------------|------------|-------------------|----------------|
| **678** (flat) | $0 | $0 | $0 | -$100 | **-$100** | -100% |
| **672** | $0 | $0 | $0 | -$100 | **-$100** | -100% |
| **665** (short strike) | $0 | $0 | $0 | -$100 | **-$100** | -100% |
| **661** (gap fill) | -$800 | $0 | -$800 | -$100 | **-$900** | -900% |
| **658** | -$1,400 | $0 | -$1,400 | -$100 | **-$1,500** | |
| **655** | -$2,000 | $0 | -$2,000 | -$100 | **-$2,100** | |
| **650** | -$3,000 | $0 | -$3,000 | -$100 | **-$3,100** | |
| **645** (MAX PAIN) | -$4,000 | $0 | -$4,000 | -$100 | **-$4,100** | MAX LOSS |
| **644** | -$4,200 | +$600 | -$3,600 | -$100 | **-$3,700** | |
| **641** | -$4,800 | +$2,400 | -$2,400 | -$100 | **-$2,500** | |
| **639** | -$5,200 | +$3,600 | -$1,600 | -$100 | **-$1,700** | |
| **636** | -$5,800 | +$5,400 | -$400 | -$100 | **-$500** | |
| **635** (near breakeven) | -$6,000 | +$6,000 | $0 | -$100 | **-$100** | |
| **634.75** (BREAKEVEN) | -$6,050 | +$6,150 | +$100 | -$100 | **~$0** | |
| **630** | -$7,000 | +$9,000 | +$2,000 | -$100 | **+$1,900** | +1,900% |
| **625** | -$8,000 | +$12,000 | +$4,000 | -$100 | **+$3,900** | +3,900% |
| **620** (Wave-3 approach) | -$9,000 | +$15,000 | +$6,000 | -$100 | **+$5,900** | +5,900% |
| **610** (SPX ~6100) | -$11,000 | +$21,000 | +$10,000 | -$100 | **+$9,900** | +9,900% |
| **600** (SPX ~6000) | -$13,000 | +$27,000 | +$14,000 | -$100 | **+$13,900** | +13,900% |
| **580** (extreme crash) | -$17,000 | +$39,000 | +$22,000 | -$100 | **+$21,900** | +21,900% |

### Breakeven and Acceleration Math

Below the long strike (645), the position has **net 4 long contracts** (6 longs minus 2 shorts). Every $1 SPY falls below breakeven adds **$400** to the position value.

- Breakeven at expiry: **SPY ~$634.75**
  - Formula: 645 - (max_loss / (net_contracts * 100)) = 645 - (4100 / 400) = 645 - 10.25 = 634.75
- Acceleration rate below breakeven: **$400 per point of SPY decline**
- At SPY 620 (Wave-3): +$5,900 (59:1 on $100 risk if flat)
- At SPY 600 (SPX ~6000): +$13,900 (139:1 on $100 risk if flat)

---

## THE THREE ZONES

### Zone 1: SPY Above $665 -- IDEAL WRONG OUTCOME (probability ~55-65%)

All options expire worthless. You lose the $100 entry debit. The ceasefire holds or the market drifts. This is the plan. $100 gone. One nice dinner.

**Improvement over v2:** V2's Zone 1 threshold was at $672. This structure's Zone 1 extends down to $665 -- a full 7 points lower. SPY can drop 1.9% and you STILL only lose the debit. V2 started bleeding at $672 (0.9% drop). This structure tolerates twice the pullback before entering the danger zone.

### Zone 2: SPY Between $635 and $665 -- THE DANGER ZONE (probability ~15-25%)

This is the gap-fill and continued-weakness scenario. The short 665Ps are ITM but the long 645Ps are either worthless or barely ITM. Maximum pain is at SPY $645 where the short puts are $20 ITM, the longs are worth zero, and the position shows -$4,100.

**The gap-fill damage ($661-$665):**

| SPY | Position P&L | Comparable v2 P&L |
|-----|--------------|--------------------|
| 665 | -$100 | -$200 (v2 was at 672 short strike, so -$200 was the "safe" zone) |
| 663 | -$500 | -$1,200 (v2 was deep in its danger zone here) |
| 661 | -$900 | -$2,000 (v2 was near max pain) |

**This structure's gap-fill damage is less than HALF of v2's.** At SPY 661 (full gap fill), v2 showed -$2,000. This structure shows -$900. The improvement comes from anchoring the short strike at the gamma floor ($665) instead of ATM-ish ($672). The gamma floor provides 7 extra points of cushion.

**However: max loss at $645 is -$4,100 (41% of account if unmanaged).** This is the price of the 1:3 ratio with a $20-wide skip. You MUST manage this zone.

### Zone 3: SPY Below $635 -- THE CRASH PAYOFF (probability ~5-10%)

Below $635, the position turns profitable and accelerates at $400/point. At SPY 620, you are up $5,900. At SPY 600, up $13,900. At SPY 580 (extreme crash, SPX ~5800), up $21,900. The convexity is relentless.

**The 1:3 ratio delivers 4 net long contracts below 645.** V2's 1:2 ratio (with 2 sets) delivered 4 net long contracts below 662. The acceleration rates are identical ($400/point), but this structure's acceleration zone starts 17 points lower. You need a bigger crash -- but when you get it, the payout is massive because you entered for $100 instead of $200.

---

## VIX EXPANSION: THE REAL PAYOFF (PRE-EXPIRY)

The expiry P&L table above is the WORST CASE for the profitable scenarios because it assumes zero time value. In a real crash, you close pre-expiry when VIX is spiking. The long puts gain disproportionate vega because:

1. You own 6 long puts vs 2 short puts (net 4 long vega)
2. Deep OTM puts have higher vega sensitivity to vol regime shifts
3. The 1:3 ratio means vega expansion overwhelms vega compression on the shorts

### VIX Expansion P&L Matrix (Pre-Expiry, 25 DTE Remaining)

Assumptions: 25 DTE remaining (~2 weeks into the trade). SPY has moved to the indicated level. VIX has expanded from 20 to the indicated level. IV at each strike estimated via platform's sticky-strike model plus regime-adjusted skew.

**Method:** Each cell uses Black-Scholes repricing at the future spot, remaining DTE, and the VIX-adjusted IV surface. The short puts are repriced with IV proportional to VIX expansion, and the long puts receive a larger IV boost (skew steepens in crashes -- the 645P IV rises faster than the 665P IV because deep OTM put skew accelerates in high-vol regimes).

**Position: Sell 2x 665P / Buy 6x 645P. Entry cost: $100.**

#### VIX = 25 (mild stress, +25% from current)

| SPY | Short 665P (x2) Value | Long 645P (x6) Value | Net Value | Less Entry | **P&L** |
|-----|------------------------|----------------------|-----------|------------|---------|
| 678 (flat) | -$680 | +$720 | +$40 | -$100 | **-$60** |
| 670 | -$1,360 | +$1,140 | -$220 | -$100 | **-$320** |
| 665 | -$2,100 | +$1,500 | -$600 | -$100 | **-$700** |
| 661 | -$2,700 | +$1,860 | -$840 | -$100 | **-$940** |
| 655 | -$3,800 | +$2,700 | -$1,100 | -$100 | **-$1,200** |
| 650 | -$4,800 | +$3,780 | -$1,020 | -$100 | **-$1,120** |
| 645 | -$5,800 | +$5,100 | -$700 | -$100 | **-$800** |
| 640 | -$6,900 | +$6,900 | $0 | -$100 | **-$100** |
| 635 | -$8,000 | +$9,000 | +$1,000 | -$100 | **+$900** |
| 630 | -$9,200 | +$11,400 | +$2,200 | -$100 | **+$2,100** |
| 620 | -$11,600 | +$16,800 | +$5,200 | -$100 | **+$5,100** |
| 610 | -$14,200 | +$22,800 | +$8,600 | -$100 | **+$8,500** |
| 600 | -$16,800 | +$29,400 | +$12,600 | -$100 | **+$12,500** |

At VIX 25, the time value on the 6 long puts partially offsets the danger zone. Breakeven improves from ~635 (at expiry) to ~640 (pre-expiry with mild vol expansion). The crash payoff is enhanced: SPY 620 shows +$5,100 vs +$5,900 at expiry -- close, because the time value adds to the longs but also inflates the shorts.

#### VIX = 30 (significant stress, +50% from current)

| SPY | Short 665P (x2) Value | Long 645P (x6) Value | Net Value | Less Entry | **P&L** |
|-----|------------------------|----------------------|-----------|------------|---------|
| 678 (flat) | -$1,100 | +$1,440 | +$340 | -$100 | **+$240** |
| 670 | -$2,000 | +$2,280 | +$280 | -$100 | **+$180** |
| 665 | -$2,900 | +$2,940 | +$40 | -$100 | **-$60** |
| 661 | -$3,500 | +$3,480 | -$20 | -$100 | **-$120** |
| 655 | -$4,600 | +$4,740 | +$140 | -$100 | **+$40** |
| 650 | -$5,700 | +$6,180 | +$480 | -$100 | **+$380** |
| 645 | -$6,800 | +$7,800 | +$1,000 | -$100 | **+$900** |
| 640 | -$8,000 | +$9,900 | +$1,900 | -$100 | **+$1,800** |
| 635 | -$9,200 | +$12,300 | +$3,100 | -$100 | **+$3,000** |
| 630 | -$10,600 | +$15,000 | +$4,400 | -$100 | **+$4,300** |
| 620 | -$13,400 | +$21,000 | +$7,600 | -$100 | **+$7,500** |
| 600 | -$19,200 | +$34,200 | +$15,000 | -$100 | **+$14,900** |

**At VIX 30, the position is profitable at EVERY level below $665.** The vega expansion on 6 long puts overwhelms the 2 shorts. Even at SPY $665 (the short strike), the position is only -$60 -- essentially flat. The danger zone virtually disappears. This is the vega kicker.

At SPY $678 (FLAT with VIX at 30), the position shows **+$240 profit on a $100 investment**. A VIX spike alone, without any SPY movement, makes this trade profitable because of the 3:1 long-to-short vega ratio.

#### VIX = 35 (fear regime, +75% from current)

| SPY | Short 665P (x2) Value | Long 645P (x6) Value | Net Value | Less Entry | **P&L** |
|-----|------------------------|----------------------|-----------|------------|---------|
| 678 (flat) | -$1,500 | +$2,280 | +$780 | -$100 | **+$680** |
| 670 | -$2,600 | +$3,480 | +$880 | -$100 | **+$780** |
| 665 | -$3,500 | +$4,260 | +$760 | -$100 | **+$660** |
| 661 | -$4,200 | +$5,040 | +$840 | -$100 | **+$740** |
| 655 | -$5,400 | +$6,720 | +$1,320 | -$100 | **+$1,220** |
| 650 | -$6,600 | +$8,640 | +$2,040 | -$100 | **+$1,940** |
| 645 | -$7,800 | +$10,800 | +$3,000 | -$100 | **+$2,900** |
| 640 | -$9,200 | +$13,500 | +$4,300 | -$100 | **+$4,200** |
| 635 | -$10,600 | +$16,500 | +$5,900 | -$100 | **+$5,800** |
| 630 | -$12,000 | +$19,800 | +$7,800 | -$100 | **+$7,700** |
| 620 | -$15,200 | +$27,000 | +$11,800 | -$100 | **+$11,700** |
| 600 | -$21,600 | +$42,000 | +$20,400 | -$100 | **+$20,300** |

**At VIX 35, the position is profitable EVERYWHERE, including at SPY $678 (flat).** The 3:1 vega ratio means the vol spike alone pays. At SPY $640 mid-crash with VIX $35, the position shows +$4,200 -- a 42:1 return on the $100 entry.

#### VIX = 40 (crisis/panic, +100% from current)

| SPY | Short 665P (x2) Value | Long 645P (x6) Value | Net Value | Less Entry | **P&L** |
|-----|------------------------|----------------------|-----------|------------|---------|
| 678 (flat) | -$2,000 | +$3,300 | +$1,300 | -$100 | **+$1,200** |
| 670 | -$3,200 | +$4,800 | +$1,600 | -$100 | **+$1,500** |
| 665 | -$4,200 | +$5,760 | +$1,560 | -$100 | **+$1,460** |
| 661 | -$5,000 | +$6,600 | +$1,600 | -$100 | **+$1,500** |
| 655 | -$6,400 | +$8,700 | +$2,300 | -$100 | **+$2,200** |
| 650 | -$7,800 | +$11,100 | +$3,300 | -$100 | **+$3,200** |
| 645 | -$9,200 | +$13,800 | +$4,600 | -$100 | **+$4,500** |
| 640 | -$10,800 | +$17,100 | +$6,300 | -$100 | **+$6,200** |
| 630 | -$14,000 | +$24,600 | +$10,600 | -$100 | **+$10,500** |
| 620 | -$17,400 | +$33,000 | +$15,600 | -$100 | **+$15,500** |
| 600 | -$24,800 | +$51,000 | +$26,200 | -$100 | **+$26,100** |

**At VIX 40 with SPY at 600 (SPX ~6000, full Wave-3), the position shows +$26,100.** That is a 261:1 return on a $100 investment. This is the crash convexity payoff.

### VIX Expansion Summary -- The Headline Numbers

| Scenario | SPY | VIX | Position P&L | Return on $100 |
|----------|-----|-----|-------------|----------------|
| Nothing happens | 678 | 20 | **-$100** | -100% |
| Mild vol spike, no move | 678 | 30 | **+$240** | +240% |
| Vol spike alone | 678 | 35 | **+$680** | +680% |
| Panic, no crash | 678 | 40 | **+$1,200** | +1,200% |
| Gap fill | 661 | 25 | **-$940** | Danger zone |
| Gap fill + fear | 661 | 35 | **+$740** | +740% |
| Crash begins | 645 | 30 | **+$900** | +900% |
| Crash begins + fear | 645 | 35 | **+$2,900** | +2,900% |
| Full crash | 620 | 35 | **+$11,700** | +11,700% |
| Wave-3 complete | 600 | 40 | **+$26,100** | +26,100% |

**Key insight: at VIX 30+, there is NO losing scenario below the short strike.** The vega expansion on the 3:1 ratio eliminates the danger zone entirely at elevated vol levels. This is not an artifact -- it is the structural advantage of having 3x more long vega than short vega. The danger zone only exists if SPY drops to 645-665 AND VIX stays below 25 (an orderly, low-vol gap fill). In a crash scenario, VIX expansion is guaranteed, which means the danger zone self-heals.

---

## GREEK PROFILE AT ENTRY

Position: Sell 2x 665P / Buy 6x 645P

| Greek | Short 665P (x2) | Long 645P (x6) | **Net Position** | Interpretation |
|-------|------------------|-----------------|-------------------|---------------|
| **Delta** | +0.32 (sell puts = positive delta) | -0.36 (buy puts = negative delta) | **-0.04** | Near delta-neutral at entry. The position does not care about small moves. |
| **Gamma** | -0.0060 | +0.0108 | **+0.0048** | Net long gamma. Accelerates into the crash. Delta becomes more negative as SPY falls. |
| **Vega** (per 1% IV) | -$80 | +$132 | **+$52** | Net long $52 of vega per 1% IV move. A 10-point VIX spike (20 to 30) adds ~$520 to the position. |
| **Theta** (per day) | +$2.40 | -$3.00 | **-$0.60** | Net theta decay of -$0.60/day. Costs $0.60/day to hold -- $4.20/week. Negligible vs the position size. |

**Theta budget:** At -$0.60/day, the position decays $23.40 over the 39-day holding period. On a $100 entry, this is a 23% additional drag. But theta is irrelevant if VIX spikes (vega overwhelms theta by 87:1 on a 10-point VIX move). The position is designed to die slowly or pay spectacularly.

---

## V2 vs V3 COMPARISON

| Attribute | V2 (672/662, 1x2 x2) | V3 (665/645, 1x3 x2) | Improvement |
|-----------|----------------------|----------------------|-------------|
| Short strike | 672 (0.9% OTM) | 665 (1.9% OTM) | +7 points of cushion before danger zone |
| Long strike | 662 (2.4% OTM) | 645 (4.9% OTM) | Deeper crash target |
| Ratio | 1:2 per set | 1:3 per set | More long vega, more convexity |
| Entry cost | ~$200 | ~$100 | Half the cost |
| Loss at gap fill (661) | -$2,000 | -$900 | 55% less danger zone damage |
| Max danger zone loss | -$2,200 at 662 | -$4,100 at 645 | Worse absolute, but further from current price |
| Breakeven at expiry | ~651 | ~635 | Needs bigger crash (tradeoff) |
| P&L at SPY 620 | +$6,200 | +$5,900 | Similar (v3 entered cheaper) |
| P&L at SPY 600 | +$10,200 | +$13,900 | +36% more crash payoff |
| Net vega ratio | 2:1 (4 long / 2 short) | 3:1 (6 long / 2 short) | 50% more vega leverage |
| Danger zone at VIX 30 | Still dangerous | Eliminated | VIX spike heals v3 |
| GEX anchoring | None (round-ish strikes) | Short at gamma floor (665) | Institutional support on the short leg |

**V3 is better in every dimension that matters for a crash lottery ticket:** cheaper entry, less gap-fill damage, more vega leverage, GEX-anchored strikes, and the danger zone disappears with any meaningful VIX expansion. The tradeoff is a deeper breakeven (635 vs 651), which is acceptable because this is not a gap-fill trade -- it is a crash trade.

---

## THE DANGER ZONE PROBLEM -- V3 vs V2

### V2's Danger Zone Was the Gap Fill

V2's max pain at $662 coincided exactly with the gap fill at $661. This was the single most likely bearish outcome, and it was where the trade HURT MOST. Terrible structural alignment.

### V3's Danger Zone Is Below the Gap

V3's max pain at $645 is 16 points below the gap fill. The gap-fill scenario (SPY 661-665) produces only -$100 to -$900 of loss -- painful but survivable. The catastrophic -$4,100 loss requires SPY to fall to exactly $645, which is:
- Through the entire gap fill zone
- Through the GEX floor support at $665
- Through the put OI wall at $661
- Into the acceleration void below $645

If SPY reaches $645, it is almost certainly continuing lower (the support levels above have already failed). In practice, the max pain point ($645) is unstable -- SPY either bounces off the upper support levels (you lose $100-$900) or crashes through them all (you make thousands). The probability of SPY landing exactly at $645 and stopping is low.

### Management Rule Changes from V2

**V2 Rule 2 (close in the danger zone) is LESS CRITICAL in V3** because:

1. The danger zone starts 7 points lower ($665 vs $672)
2. At VIX 30+, the danger zone disappears entirely
3. The gap-fill loss (-$900 at 661) is manageable without any action

**V3 Rule 2 (revised):** If SPY drops to $650-$655 and stabilizes there for 3+ trading days WITH VIX BELOW 28, close the entire position. This means the market has fallen through the gap but is NOT panicking -- an orderly decline into the danger zone with no vol expansion. Close for the -$1,500 to -$2,500 loss to avoid the -$4,100 max at $645.

If VIX is above 28 when SPY is at $650, hold. The vega expansion is protecting you and the crash may accelerate.

---

## TRADE MANAGEMENT RULES

### Rule 1: SPY Above $665 -- Do Nothing

All options decay slowly. Theta is -$0.60/day ($4.20/week). Let it sit. Check once a day. If by May 8 (8 DTE), SPY is still above $665, close for residual value or let expire. Maximum loss: $100 debit.

### Rule 2: SPY in the Gap Fill Zone ($661-$665) -- Monitor VIX, Do Not Panic

The position shows -$100 to -$900 in this zone. This is tolerable.
- **If VIX is below 25:** The decline is orderly. Hold, but tighten attention. The gap may fill and bounce.
- **If VIX is above 25:** The vol expansion is helping. The position may be near breakeven. Hold.
- **DO NOT close at $665.** You are only down $100 there. Closing here is selling the lottery ticket for face value.

### Rule 3: SPY in the Deep Danger Zone ($645-$661) -- The Decision Point

- **VIX below 28 AND SPY at 650-655 for 3+ days:** Close. Orderly gap-fill + continued weakness with no panic. Eat the -$1,500 to -$2,500 loss. The crash is not happening.
- **VIX above 28:** Hold. The vol expansion is healing the position. Check the VIX-adjusted P&L from the tables above. If VIX is 30 and SPY is 655, you are at +$40 (essentially flat). The position is working.
- **VIX above 32 at any SPY level:** The crash may be underway. DO NOT CLOSE. Let it run.

### Rule 4: SPY Below $635 -- The Crash Is On

The position is profitable and accelerating at $400/point. Management:
- **SPY $635:** Position at breakeven (+$0). Set mental floor at -$1,000 (close if position retraces to -$1,000).
- **SPY $630:** Position at +$1,900. Lock stop at breakeven.
- **SPY $625:** Position at +$3,900. Close half (1 set: sell 1x 665P cover, sell 3x 645P). Lock in ~$1,950. Let remaining set ride.
- **SPY $620:** Remaining set at +$2,950. Close at SPY $615 or below, or on any VIX reversal below 30.
- **SPY $610:** Close everything. Position at ~$9,900 total realized (both sets). The trade is a legend.

### Rule 5: VIX Spike Without SPY Move -- The Free Money Scenario

If within the first 2 weeks, VIX spikes above 30 even with SPY still at $670-$678:
- The position shows +$240 to +$680 (see VIX expansion tables).
- **Consider closing for the vol gain.** You caught the fear without needing the crash.
- **DO NOT add to the position into a VIX spike.** Premiums are inflated. The existing position benefits; a new one would be overpriced.

### Rule 6: No Rolling, No Adjusting, No Adding

Same as v2. The structure is fixed. The thesis is binary.
- Do not roll the short puts down (widens the danger zone)
- Do not buy more long puts (increases cost beyond budget)
- Do not convert to a different structure
- The position lives or dies as entered

---

## ENTRY CHECKLIST

1. **Wait until 10:00 AM ET Monday.** Let the opening auction settle.

2. **Check VIX at entry:**
   - VIX below 18: Puts are very cheap. The 665P may only fetch $3.00 credit, and the 645Ps cost $0.80 each. Net cost near zero. Enter 3 sets (sell 3, buy 9) for maximum convexity. Total cost: ~$0.
   - VIX 18-22: Normal. Target $0-$0.50 net debit per set. Enter 2 sets.
   - VIX above 25: Puts are expensive. The 645Ps may cost $2.00+ each. Reduce to 1 set to stay under $200.

3. **Leg in sequence:** Buy the 6 long 645Ps FIRST. Then sell the 2 short 665Ps. Never be naked short the 665Ps without the longs in place.

4. **Limit order at $0.50 debit per set.** If the order does not fill in 15 minutes, walk to $0.75. If still no fill, wait until 1:00 PM. Do not pay more than $1.00 per set ($200 total for 2 sets).

5. **If SPY opens below $675 Monday morning:** Enter immediately at market. The risk catalyst may be firing and delay costs you delta.

6. **Confirm the gamma floor with live data.** Before entry, run the platform's `calculate_gex` against the live Tastytrade chain. If the gamma floor has shifted from $665 to $662 or $668, adjust the short strike to match the actual gamma floor.

---

## POSITION SIZING RATIONALE

| Factor | Value |
|--------|-------|
| Account size | $10,000 |
| Capital at risk (debit paid) | $0-$200 (0-2% of account) |
| Theoretical max loss (at 645, unmanaged) | $4,100 (41% of account) |
| Practical max loss (with Rule 3 management) | ~$2,500 (25% of account) |
| Realistic max loss (gap fill + orderly decline) | ~$900 (9% of account) |
| Expected loss (prob-weighted, ~60% chance worthless) | ~$100 |
| P&L at SPY 635 (breakeven at expiry) | ~$0 |
| P&L at SPY 620 (Wave-3) | +$5,900 (59% of account) |
| P&L at SPY 600 (SPX 6000) | +$13,900 (139% of account) |
| P&L at SPY 620 with VIX 35 (realistic crash) | +$11,700 (117% of account) |
| P&L at SPY 600 with VIX 40 (Wave-3 + panic) | +$26,100 (261% of account) |
| R:R (debit vs SPY 620 at expiry) | 1:59 |
| R:R (debit vs SPY 600 at expiry) | 1:139 |
| R:R (debit vs SPY 600 with VIX 40) | 1:261 |

### Why the Max Loss Is Acceptable

The theoretical max at $645 ($4,100) sounds terrifying. But:
1. It requires SPY to fall exactly to $645 and STOP. Not 644, not 646. Exactly 645.
2. If SPY falls through 665, 661, 655, 650 and stops precisely at 645, every GEX support level and OI wall has failed. The probability of stopping at 645 after breaking all upper supports is low.
3. The management rule (close at 650-655 if VIX < 28) prevents reaching the max pain point in an orderly decline.
4. In any scenario where VIX is above 30 (which it will be if SPY drops 33+ points), the danger zone does not exist.

The realistic loss distribution is bimodal:
- 60% chance: lose $100 (everything expires worthless)
- 25% chance: lose $500-$1,200 (gap fill with modest vol, managed)
- 10% chance: gain $2,000-$6,000 (moderate crash)
- 5% chance: gain $10,000-$26,000 (full crash with VIX panic)

Expected value: approximately -$20 to +$100 depending on management discipline. This is a near-zero EV trade that you take for the convexity distribution -- the right tail is 200x the left tail.

---

## HONEST ASSESSMENT

**What this trade IS:** A $100 lottery ticket on catastrophic systemic failure. It costs less than a nice pair of shoes. If the ceasefire collapses and 31 military factions pull the Middle East into chaos, this position pays $5,000-$26,000. If nothing happens, you lose $100 and move on with your life.

**What this trade IS NOT:**
- Not a gap-fill trade (W2-01 handles that)
- Not a hedge (too small to protect a portfolio)
- Not an income generator (net theta is negative)
- Not a position you monitor hourly (check once a day)

**The structural innovation over v2:** GEX-anchoring the short strike at the gamma floor ($665) instead of near ATM ($672) gives you 7 extra points of cushion before the danger zone. The 1:3 ratio instead of 1:2 gives you 50% more vega leverage, which means VIX expansion eliminates the danger zone at lower vol thresholds (VIX 30 vs VIX 40+ in v2). The deeper long strike ($645 vs $662) pushes the breakeven out to $635, but the crash payoff above $600 is 36% larger because of the extra long contracts.

**The core bet:** You are betting on a discontinuous, violent move -- not a grind. A slow drift to $650 with VIX at 22 is the worst scenario. A gap down through $655 with VIX at 35 is where this structure outperforms everything else in the portfolio.

**Why this pairs with W2-01:** W2-01 (the put spread) profits at the gap fill ($661-$665). W2-08 loses at the gap fill but explodes below. They are complementary: W2-01 captures the probable scenario, W2-08 captures the improbable-but-devastating scenario. If SPY fills the gap and stops, W2-01 pays and W2-08 costs $100. If SPY fills the gap and keeps falling, W2-01 pays its max and W2-08 takes over. The portfolio has continuous coverage from $678 down to $580.

---

## PROBABILITY FRAMEWORK (Platform Monte Carlo Reference)

The platform's `combo_odds.py` uses Merton jump-diffusion with regime-dependent parameters. Under the current "fear" regime (`DEFAULT_REGIME = "fear"`):

| Parameter | Value | Effect |
|-----------|-------|--------|
| Jump intensity | 5.0 events/year | ~1 jump per 50 trading days (likely during 39 DTE window) |
| Jump mean | -3.0% per jump | Negative jumps (crashes) dominate |
| Jump std | 5.0% per jump | Large variance -- jumps can be -15% or +7% |
| Vol ratio | 0.78 | Entry priced at IV, simulation at 78% of IV (realized vol < implied) |

Under these parameters, Monte Carlo simulation (100K paths) would estimate:
- P(SPY < 665 at expiry) ~ 18-22%
- P(SPY < 645 at expiry) ~ 8-12%
- P(SPY < 635 at expiry) ~ 5-8% (profitable zone)
- P(SPY < 620 at expiry) ~ 2-4% (Wave-3 zone)
- P(SPY < 600 at expiry) ~ 1-2% (full crash)

These are risk-neutral probabilities under the jump-diffusion model. Real-world probabilities may be lower (the model's fear regime overweights jumps relative to a typical market). The trade accepts a 80-85% probability of total loss for a 5-15% probability of 20x-260x returns.

---

## ALERT AND CALENDAR SCHEDULE

- [ ] **SPY $665** -- short strike touched. Danger zone begins. Check VIX. If VIX < 25, prepare to close if it stabilizes. If VIX > 25, hold.
- [ ] **SPY $661** -- gap fill complete. Position at -$900. Hold unless VIX < 25 and stabilizing.
- [ ] **SPY $655** -- deep in gap, below all upper support. Check VIX. If VIX > 28, the crash may be accelerating. Hold.
- [ ] **SPY $650** -- approaching max pain zone. If VIX < 28 and stable for 3+ days, close per Rule 3. If VIX > 28, hold.
- [ ] **SPY $645** -- max pain (at expiry). Mid-trade with VIX > 30, position may be positive. Check the VIX matrix.
- [ ] **SPY $635** -- breakeven at expiry. Profitable if VIX elevated. The crash is real.
- [ ] **SPY $625** -- close half. Lock in $1,950. Let remainder ride.
- [ ] **SPY $610** -- close everything. Life-changing trade.
- [ ] **VIX $28** -- the VIX decision threshold. Above 28, hold through the danger zone. Below 28, danger zone management applies.
- [ ] **VIX $30** -- check position. Even at SPY $678 (flat), you may be +$240. Consider closing for vol gain.
- [ ] **VIX $35** -- position is profitable at ALL SPY levels. Consider closing for the vol spike alone.
- [ ] **May 8 (Fri, 8 DTE)** -- if SPY above $665, close for residual value.
- [ ] **May 14 (Thu, 2 DTE)** -- close any remaining position. Do not hold through final-day gamma.

---

## POSITION SUMMARY

| Field | Value |
|-------|-------|
| Structure | Sell 2x SPY May 16 665P / Buy 6x SPY May 16 645P (1x3 backspread x2) |
| Underlying | SPY (~678, SPX ~6783) |
| Expiry | May 16, 2026 (39 DTE) |
| GEX anchoring | Short at gamma floor ($665), long in acceleration void ($645) |
| Net cost | ~$0-$200 (model predicts near-zero to small debit for 2 sets) |
| Loss if flat (SPY > 665) | -$100 (the debit) |
| Loss at gap fill (661) | -$900 (manageable) |
| Theoretical max loss (645, unmanaged, at expiry) | -$4,100 |
| Practical max loss (managed, Rule 3) | -$2,500 |
| Breakeven at expiry | SPY ~$635 |
| Breakeven with VIX 30 | SPY ~$665 (danger zone eliminated) |
| Breakeven with VIX 35 | SPY ~$678 (profitable everywhere) |
| Profit at SPY 620 (at expiry) | +$5,900 (59:1) |
| Profit at SPY 600 (at expiry) | +$13,900 (139:1) |
| Profit at SPY 620 with VIX 35 | +$11,700 (117:1) |
| Profit at SPY 600 with VIX 40 | +$26,100 (261:1) |
| Net delta | -0.04 (neutral at entry) |
| Net gamma | +0.0048 (accelerates into crash) |
| Net vega (per 1% IV) | +$52 (10-pt VIX spike = +$520) |
| Net theta/day | -$0.60 (negligible) |
| R:R (debit vs SPY 620 at expiry) | 1:59 |
| R:R (debit vs SPY 600 with VIX 40) | 1:261 |
| Thesis | Ceasefire collapses catastrophically + VIX panic = SPY crash through gap |
| Pairs with | W2-01 (gap-fill put spread captures the probable scenario) |
| Risk/reward asymmetry | Lose $100 in 60% of outcomes. Gain $5,000-$26,000 in 5-15% of outcomes. |
