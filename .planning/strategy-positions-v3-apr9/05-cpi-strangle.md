# 05 -- CPI Strangle (Long Strangle, Thursday Afternoon Entry)

**Date drafted:** 2026-04-09
**Playbook:** Long strangle -- buy OTM put + OTM call, cut loser at mid-strike, let winner run
**Catalyst window:** CPI Friday Apr 10 8:30 AM ET + Islamabad talks Saturday Apr 11 + Monday open
**Expiry:** Apr 16 (monthly cycle, 7 DTE at entry) -- captures all three catalysts
**Market at drafting:** SPY $679.58 | Gamma ceiling $685 | Gamma floor $670 | Gamma flip $658.66 | PCR 1.324 (extreme fear)

---

```
POSITION: SPY Apr 16 $670P / $685C -- CPI + Weekend Strangle

Action:     Buy to open 1x SPY Apr 16 $670 Put
            Buy to open 1x SPY Apr 16 $685 Call
Entry:      Thursday April 9, 2:00-3:30 PM ET (post-PCE IV crush window)
Cost:       ~$2.00 total debit (~$1.20 put + ~$0.80 call, estimated at post-PCE IV trough)
Quantity:   1x each leg (2 contracts total)
Max loss:   $200 (full premium -- both legs expire worthless, no stop order needed)
Max profit: Uncapped on upside; ~$800+ on downside if SPY gaps to $661
Breakeven:  SPY below ~$668.00 or above ~$687.00 by expiry
Take profit: Sell full strangle at $4.00+ total value (~$200+ profit, ~100% return)
Kill loser:  When SPY commits to a direction, sell the losing leg at market
Hard time stop: Exit by Wednesday April 15, 3:00 PM ET -- no exceptions
Invalidation: VIX drops below 16 (no event risk priced). SPY moves more than
              $10 from $679 before entry (the event already happened without you).
Why THIS trade: CPI Friday is the first print capturing the Hormuz oil spike in
              March data. If hot, SPY drops toward $670 gamma floor. If soft, SPY
              pushes toward $685 gamma ceiling. The strangle profits on a large
              move in either direction. Apr 16 expiry captures CPI + full weekend
              of Islamabad talks + Monday's repricing. Enter Thursday afternoon
              after PCE crushes IV -- cheapest window before CPI event premium
              gets bid up Friday morning.
```

---

## CONSTITUTION COMPLIANCE

| Rule | Limit | This Trade | Pass/Fail |
|---|---|---|---|
| Max risk per position | $200 | $200 (full premium loss) | PASS |
| Max total portfolio risk | $500 | $200 (assumes no other open positions) | PASS |
| Max positions open simultaneously | 3 | 1 (this position only) | PASS |
| Max correlated (same direction) | 2 | N/A -- strangle is non-directional | PASS |
| Min cash reserve (90%) | $9,000 | $10,000 - $200 = $9,800 | PASS |
| Max single position as % of risk budget | 50% ($250) | $200 = 40% of $500 budget | PASS |
| Max legs per position | 2 | 2 (one put, one call) | PASS |
| No naked short options | -- | Long options only, no short legs | PASS |
| No 0DTE | Min 4 calendar DTE | Apr 16 = 7 DTE at Thursday entry | PASS |
| Commission check (RT < 3% of max profit) | $2.60 RT | Max profit $800+; $2.60/$800 = 0.3% | PASS |
| No entries before 10:00 AM ET | -- | Entry 2:00-3:30 PM ET | PASS |
| No entries within 90 min of CPI/PCE | PCE 8:30 AM | 2:00 PM = 5.5 hours after PCE | PASS |
| Max entries per day | 2 | 1 entry (both legs are one position) | PASS |
| No chasing | $0.15 max walk | Limit orders, 3 walks max | PASS |

**All 14 constitutional rules: PASS. No exceptions required.**

---

## GEX STRIKE SELECTION

### Why These Strikes Changed From W2-03

The W2-03 strangle used $675P/$692C based on estimated GEX levels (gamma floor $665, gamma ceiling $685, gamma flip $678). Live data as of April 9 corrected every level:

| Level | W2-03 Estimate | Apr 9 Live Data | Shift |
|---|---|---|---|
| Gamma Ceiling | $685 | $685 | Unchanged |
| Gamma Floor | $665 | $670 | +$5 |
| Gamma Flip | $678 | $658.66 | -$19 |
| Max Pain | $675 | ~$670 (near floor) | -$5 |

The gamma floor moved UP to $670, making it the natural put strike. The gamma ceiling held at $685, making it the natural call strike. Both strikes now sit exactly at the GEX boundary levels where dealer hedging creates the strongest directional commitment.

### Put Leg: $670 (Gamma Floor)

| Metric | Value |
|---|---|
| Strike | $670 |
| SPX equivalent | ~6700 |
| GEX classification | Gamma floor -- highest absolute put GEX strike |
| Distance from spot | $9.58 OTM (1.41%) |
| Estimated price at entry | ~$1.00-1.40 (post-PCE IV trough, 7 DTE) |
| Using | $1.20 midpoint estimate |
| Delta at entry | ~-0.25 |

**Why $670:** This is the live gamma floor. Massive put OI here creates a structural support level where dealers buy to hedge. If CPI is hot and SPY sells off, it accelerates INTO this strike because the gamma flip at $658.66 is far below -- there is no dealer dampening between $670 and $658.66. Once SPY breaks $670, the next support is $658.66 (gamma flip), 11 points lower. The put captures the floor break.

**Why not $675 (old max pain):** Live data shows max pain has migrated down to ~$670. The $675 strike no longer has structural significance -- it is in the dead zone between the ceiling and the floor. Paying for a $675P costs more ($1.60-1.80) and does not sit on a GEX level.

**Why not $665 or lower:** Too far OTM. At 7 DTE, the $665P costs ~$0.50-0.70. Requires a crash to $663 just to break even on the put side alone. The gamma floor at $670 provides a more realistic target.

### Call Leg: $685 (Gamma Ceiling)

| Metric | Value |
|---|---|
| Strike | $685 |
| SPX equivalent | ~6850 |
| GEX classification | Gamma ceiling -- highest call GEX strike |
| Distance from spot | $5.42 OTM (0.80%) |
| Estimated price at entry | ~$0.60-1.00 (post-PCE IV trough, 7 DTE) |
| Using | $0.80 midpoint estimate |
| Delta at entry | ~+0.20 |

**Why $685:** This is the live gamma ceiling. It is the hard resistance level where dealer hedging caps rallies. But here is the key insight: if CPI is soft and triggers a relief rally, the gamma ceiling is the level that must BREAK for the move to be real. A soft CPI print combined with dovish Fed commentary could push SPY through $685, and once through, there is no resistance above until $690+. The call captures the ceiling break.

**Why not $692 (old hedge wing):** W2-03 used $692 as a deep OTM hedge wing at $0.60. But the setup has changed. With SPY at $679.58 and the gamma ceiling confirmed at $685, the $685C is only $5.42 OTM and costs ~$0.80 -- still within budget. The $692C would cost ~$0.25-0.35, providing worse delta and requiring an $12+ move just to reach the strike. The ceiling strike gives better risk/reward.

**Why this is NOT "buying a call AT resistance":** The strangle is not a directional call bet expecting SPY to reach $685. It is a breakout play. The call pays off specifically in the scenario where the ceiling fails. If the ceiling holds, the call expires worthless -- and the put leg handles the alternative scenario. The strangle does not need $685 to hold OR break. It needs one of the two boundaries to fail.

---

## PRICING MATH

### Entry Assumptions
- SPY at ~$679.58 (may drift $1-2 Thursday afternoon)
- VIX at ~19-20 (post-PCE trough, before CPI event premium builds Friday morning)
- DTE: 7 (Apr 16 expiry, entered Thursday Apr 9)
- PCR: 1.324 (extreme fear -- put skew premium elevated)

### Put Leg ($670P)

| Input | Value |
|---|---|
| Spot | $679.58 |
| Strike | $670 |
| IV | ~22% (put skew premium, elevated by PCR 1.324 extreme fear) |
| DTE | 7 |
| Delta | ~-0.25 |
| Theta | ~-$0.14/day |
| Vega | ~$0.08 per 1pt IV |
| Estimated price | $1.00-1.40 (using $1.20) |

### Call Leg ($685C)

| Input | Value |
|---|---|
| Spot | $679.58 |
| Strike | $685 |
| IV | ~19% (call side, lower skew) |
| DTE | 7 |
| Delta | ~+0.20 |
| Theta | ~-$0.10/day |
| Vega | ~$0.07 per 1pt IV |
| Estimated price | $0.60-1.00 (using $0.80) |

### Combined Strangle

| Metric | Value |
|---|---|
| Total debit | ~$2.00 ($200 total) |
| Combined theta | ~-$0.24/day ($24/day bleed) |
| Combined vega | ~$0.15 per 1pt IV |
| Downside breakeven | ~$668.00 (SPY needs to fall $11.58) |
| Upside breakeven | ~$687.00 (SPY needs to rise $7.42) |

**Breakeven asymmetry note:** The upside breakeven is closer ($7.42 move) than the downside ($11.58 move). This is unusual for a strangle -- normally the put side is closer because of skew. Here, the call is only $5.42 OTM vs the put's $9.58 OTM. The strangle is slightly bullish-leaning on distance but slightly bearish-leaning on probability (put skew from PCR 1.324 means the put has higher implied probability of reaching its strike despite being farther away, and VIX expansion on selloffs inflates the put further).

---

## THESIS

### The CPI Setup

Three catalysts converge in a 72-hour window:

1. **CPI Friday 8:30 AM (March data)** -- This is the first CPI print capturing the Hormuz oil spike. Oil went from ~$80 to $112 in the back half of March. Even if core CPI strips direct energy, second-order effects (transport, logistics, food supply chains) bleed into core services. A hot print sends SPY toward the $670 gamma floor. A soft print ignites a relief rally toward the $685 gamma ceiling.

2. **Islamabad talks Saturday April 11** -- Iran has 31 separate armed services. No single authority can order all branches to stand down. Outcomes are binary:
   - Framework without IRGC participation = collapse confirmation = bearish
   - IRGC participation + enforcement mechanism = genuine deescalation = bullish
   - Talks collapse = status quo = mildly bearish

3. **Monday open repricing** -- Whatever happens Saturday reprices into SPY at Monday open. The strangle lives through this with 5 DTE remaining.

### Why Enter Thursday Afternoon (Not Friday Post-CPI)

W2-03 recommended a Friday 10:00 AM entry. This version enters Thursday afternoon instead. The reasoning:

**Thursday 2:00-3:30 PM is the IV trough of the week:**
- PCE (February data) released at 8:30 AM Thursday. By 2:00 PM, the PCE event premium is fully absorbed (5.5 hours post-release).
- CPI event premium has NOT yet been bid up. Most CPI overnight positioning builds between 3:30 PM Thursday and Friday morning pre-market.
- You buy the strangle at the cheapest point before CPI.

**Friday 10:00 AM is AFTER the CPI event:**
- If CPI is a big move ($5+), the winning leg has already moved -- you are chasing.
- If CPI is a non-event, IV has crushed and the strangle is cheap -- but you have lost the CPI catalyst and are now only trading the weekend.
- Thursday entry captures both CPI AND the weekend, paying for neither event's premium.

**The tradeoff:** Thursday entry costs one extra day of theta (~$0.24). That is the price of owning the CPI catalyst instead of watching it from the sidelines.

### Why $670/$685 (GEX Boundaries, Not Arbitrary Wings)

The strangle strikes sit at the two structural boundaries of the current GEX regime:

- **$670 (gamma floor):** Below this, dealer put hedging creates support. Above this, puts are in the "free zone" -- no structural buying to slow a decline. If CPI cracks $670, the next support is the gamma flip at $658.66, eleven points below. The put captures this cliff.

- **$685 (gamma ceiling):** Above this, dealer call hedging creates resistance. Below this, calls are dampened. If CPI pushes through $685, the resistance evaporates and the move extends. The call captures this breakout.

The strangle is not betting on direction. It is betting that CPI produces a move large enough to break one of these two structural boundaries. Given that March CPI catches an oil spike and the PCR at 1.324 signals extreme fear (meaning the market is already braced for bad news but could snap-back on good news), the probability of a boundary break is elevated.

---

## SCENARIO ANALYSIS

### Scenario 1 -- Hot CPI, selloff to SPY $665, VIX 26

- Put: Intrinsic $670-$665 = $5.00 + extrinsic ~$0.60 + vega boost ~$0.50 = ~$6.10
- Call: Deep OTM, near-zero. ~$0.05
- Total value: ~$6.15
- **Profit: $6.15 - $2.00 = $4.15 ($415 profit, 208% return)**

### Scenario 2 -- Hot CPI + ceasefire collapse Monday, SPY gaps to $656 (gamma flip), VIX 30

- Put: Intrinsic $670-$656 = $14.00 + extrinsic ~$0.80 + vega boost ~$1.00 = ~$15.80
- Call: Worthless. ~$0.02
- Total value: ~$15.82
- **Profit: $15.82 - $2.00 = $13.82 ($1,382 profit, 691% return)**

### Scenario 3 -- Soft CPI, relief rally to SPY $690, VIX 17

- Call: Intrinsic $690-$685 = $5.00 + extrinsic ~$0.50 = ~$5.50. VIX crush from 20 to 17 reduces vega by ~$0.45. Net ~$5.05.
- Put: Deep OTM. ~$0.05.
- Total value: ~$5.10
- **Profit: $5.10 - $2.00 = $3.10 ($310 profit, 155% return)**

### Scenario 4 -- CPI non-event, quiet weekend, SPY chops $675-683

- Friday: IV crush kills both legs. Combined value drops from $2.00 to ~$1.30.
- Weekend: No catalyst. Monday: Theta continues. Combined value ~$0.90.
- By Wednesday time stop: Combined value ~$0.30-0.50.
- **Loss: $2.00 - $0.40 = $1.60 ($160 loss, 80% of premium)**
- Worst realistic outcome. Still under $200 constitutional max.

### Scenario 5 -- CPI non-event Friday, ceasefire collapse Monday, SPY gaps to $662

- Friday close: Both legs bled. Combined ~$1.30.
- Monday open with SPY at $662: Put jumps to ~$8.80 (intrinsic $8 + extrinsic + vega). Call dies.
- Total: ~$8.85
- **Profit: $8.85 - $2.00 = $6.85 ($685 profit, 343% return)**
- This justifies Apr 16 over 0DTE: surviving a quiet Friday to capture Monday's gap.

### Scenario 6 -- Hot CPI, SPY drops to $670 (floor), then bounces

- Friday 10:00 AM: Put at $670 is ATM, worth ~$1.80. Call crushed to ~$0.20. Total ~$2.00.
- Breakeven territory. The CPI move reached the floor but did not break it.
- Hold through weekend for second catalyst. If Monday is quiet, exit at time stop.
- **Likely outcome: -$0.50 to +$1.50 ($50 loss to $150 profit)**

---

## ENTRY RULES

### Entry: Thursday April 9, 2:00-3:30 PM ET

1. Confirm PCE was a non-event (SPY within $4 of $679.58 by 2:00 PM). If PCE moved SPY $8+ in either direction, the market has already repriced and the strangle strikes may be misaligned. Reassess or stand down.

2. Place limit orders at mid-price:
   - Buy 1x SPY Apr 16 $670P: Limit $1.20, walk up in $0.05 increments, max 3 walks, ceiling $1.35.
   - Buy 1x SPY Apr 16 $685C: Limit $0.80, walk up in $0.05 increments, max 3 walks, ceiling $0.95.
   - **Combined max entry: $2.30.** If total fill exceeds $2.30, do not enter.

3. Both legs must fill within 20 minutes. If one fills and the other does not after 20 minutes and 3 walks, close the filled leg and stand down.

4. Record entry prices immediately: Put @ $____, Call @ $____, Total = $____.

### Abort Conditions

- SPY has moved $8+ from prior close by entry time (the event already happened)
- VIX has dropped below 16 (no event risk priced, strangle will bleed)
- VIX has spiked above 30 (premiums too inflated, strangle costs $3.50+)
- SPY is already below $665 or above $690 (strikes are misaligned with GEX boundaries)
- Combined strangle cost exceeds $2.30 at best available fill
- PCE was a hot surprise and SPY is trending hard in one direction at 2:00 PM

---

## EXIT RULES

### Rule 1: Take Winner at 2x ($4.00 Combined, ~100% Return)

If the strangle reaches $4.00 total value at any point, sell both legs. Profit: ~$2.00 ($200+). This is the target. Do not hold for $10.00. The 100% return on a $200 position is $200 profit. Take it.

### Rule 2: Kill the Loser at Mid-Strike ($677.50)

Once SPY commits to a direction (sustained $4+ move for 30+ minutes, confirmed by volume):

- **SPY below $674 and falling:** The put is working. **Sell the $685 call.** Recover whatever it is worth ($0.05-0.20). Let the put ride with a trailing stop at 50% of its current value.
- **SPY above $682 and rising:** The call is working. **Sell the $670 put.** Same logic. Let the call ride.

"Committed direction" means: SPY has moved $4+ from entry-time price AND held the move for 30 minutes without retracing more than $1.50.

### Rule 3: Weekend Hold Decision -- Friday 3:30 PM ET

At Friday 3:30 PM, assess:

- **Strangle value > $3.00 (profitable):** Hold through weekend. Set Monday exit plan.
- **Strangle value $1.20-3.00 (modest loss to small gain):** Hold through weekend. Theta cost to hold is ~$0.24/day ($0.48 for the weekend). The Islamabad binary is worth more than $0.48.
- **Strangle value $0.50-1.20 (>40% drawdown):** Close the losing leg. Hold the surviving leg as a directional punt through the weekend at reduced cost.
- **Strangle value < $0.50:** Close everything. Weekend miracle is not a strategy.

### Rule 4: Monday Morning Management (If Held Through Weekend)

- **Monday opens with SPY gapped $5+ from Friday close:** Sell the winning leg after 10:00 AM (let 30 minutes of price discovery settle). Sell the losing leg for whatever is left.
- **Monday opens flat:** Hold. Set tighter time stop: exit Tuesday 3:00 PM if no movement.
- **Monday opens against your remaining leg:** If strangle value has decayed below $0.50, close.

### Rule 5: Time Stop -- Wednesday April 15, 3:00 PM ET

Absolute hard exit. No exceptions. Do not hold into the final 24 hours of Apr 16 expiry. Theta accelerates to $0.50+/day in the final day.

### Rule 6: VIX Collapse Invalidation

If VIX drops below 16 at any point while holding, exit both legs within 60 minutes. The strangle is long vega. VIX 16 compresses both legs simultaneously.

---

## RISK FLAGS

1. **CPI inline (30-40% probability).** Both legs bleed on IV crush. Mitigated by entering AFTER PCE crush on Thursday -- you buy at the weekly IV trough, not the CPI-inflated premium. Your real risk is the weekend catalyst, and you hold CPI as a free look.

2. **Dead zone: SPY $673-$682.** The strangle is least profitable when SPY stays between the two strikes. A $3-4 CPI move in either direction leaves the strangle near breakeven. The position needs a BOUNDARY break, not a moderate move.

3. **Weekend theta bleed.** Holding from Friday close to Monday open costs ~$0.48 in theta (2 calendar days at $0.24/day). This is the price of the weekend catalyst.

4. **PCR at 1.324 inflates put premium.** Extreme fear means the $670P costs more than it would in a neutral environment. The put side of the strangle may be $0.20-0.30 more expensive than modeled. If the combined cost exceeds $2.30, abort per entry rules.

5. **Gamma flip at $658.66 is far below.** If SPY sells off and breaks $670, there is no structural support until $658.66. This is bullish for the put leg (the move accelerates) but means there is no natural exit signal between $670 and $658 -- the trailing stop at 50% of put value handles this.

6. **Islamabad talks could produce a ceasefire headline that reverses any CPI move.** A hot CPI dropping SPY to $670 on Friday, followed by a "breakthrough" headline Saturday, could gap SPY back to $680+ on Monday. The put leg profits on Friday, the call leg profits on Monday -- but you cannot capture both peaks. Manage via Rule 3 (Friday 3:30 PM assessment).

---

## WHAT THIS TRADE IS

- A **multi-catalyst event strangle** spanning CPI + weekend geopolitics + Monday open
- A **GEX-boundary breakout play** using the live gamma floor ($670) and gamma ceiling ($685) as strike selection
- A **pre-event entry** that buys at the Thursday IV trough before CPI event premium inflates Friday morning
- A **defined-risk position** where max loss ($200) equals the constitutional ceiling with no stop order needed
- **Budget-compliant**: $200 total outlay, fits the $200 max risk per position rule exactly

## WHAT THIS TRADE IS NOT

- A directional bet (it profits on a large move in either direction)
- A 0DTE scalp (7 DTE at entry, survives the weekend)
- A position to double down on (if CPI is a non-event, do not buy a second strangle)
- A hedge for any other portfolio position (this stands alone)

---

## EXECUTION CHECKLIST -- Thursday April 9

### Post-PCE Assessment (10:00 AM - 1:00 PM ET)
- [ ] PCE printed at 8:30 AM. Record actual vs consensus
- [ ] Confirm SPY stayed within $4 of $679.58 (non-event)
- [ ] Record: SPY at ____, VIX at ____, move from prior close: ____
- [ ] If SPY moved $8+: ABORT strangle entry

### Entry Window (2:00-3:30 PM ET)
- [ ] Check abort conditions (SPY $8+ move? VIX <16? VIX >30? SPY below $665 or above $690?)
- [ ] Pull up SPY Apr 16 $670P and $685C quotes
- [ ] Place limit: Buy 1x $670P at $1.20 mid, walk $0.05 x 3 max, ceiling $1.35
- [ ] Place limit: Buy 1x $685C at $0.80 mid, walk $0.05 x 3 max, ceiling $0.95
- [ ] Confirm both legs fill within 20 minutes. If one stuck after 3 walks, close filled leg
- [ ] Record entry prices: Put @ $____, Call @ $____, Total strangle = $____
- [ ] Confirm total <= $2.30. If exceeded, close and stand down

### CPI Morning -- Friday April 10
- [ ] CPI prints at 8:30 AM. Record actual: Core MoM ____, YoY ____
- [ ] **DO NOT TRADE.** Constitution blackout until 10:00 AM
- [ ] Monitor SPY direction and magnitude through 10:00 AM
- [ ] At 10:00 AM: Check strangle value. Record: Put @ ____, Call @ ____, Total = ____
- [ ] If total >= $4.00: TAKE PROFIT (Rule 1)
- [ ] If SPY committed directionally ($4+ sustained move): KILL LOSER (Rule 2)

### Friday Afternoon (3:30 PM ET)
- [ ] Evaluate strangle value per Weekend Hold Decision (Rule 3)
- [ ] Record decision: HOLD / CLOSE LOSER / CLOSE ALL
- [ ] If holding: Set Monday morning alarms

### Monday Management (10:00 AM ET+)
- [ ] Check Sunday evening futures gap direction
- [ ] At 10:00 AM: Evaluate per Rule 4
- [ ] Record Monday strangle value: Put @ ____, Call @ ____, Total = ____

### Time Stop
- [ ] **Wednesday April 15, 3:00 PM ET: CLOSE EVERYTHING REMAINING. No exceptions.**

---

## SUMMARY FOR BOREY

Buy a $670 put and $685 call on SPY, April 16 expiry. Enter Thursday afternoon after PCE crushes IV (2:00-3:30 PM window). Total cost: ~$2.00 ($200). Max loss is $200 -- exactly at the constitutional limit with no stop order needed because both legs are long options.

The strikes are the live GEX boundaries: gamma floor ($670) and gamma ceiling ($685). The strangle profits when CPI breaks one of these boundaries. A hot print drives SPY through the $670 floor into the $658 gamma flip zone (put wins). A soft print drives SPY through the $685 ceiling (call wins).

Three catalysts in 72 hours. $200 risk. Two boundary strikes. Enter at the Thursday IV trough. Let CPI and the weekend do the work.
