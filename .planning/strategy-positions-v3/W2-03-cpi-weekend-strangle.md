# W2-03 -- CPI + Weekend Ceasefire Strangle (Long Strangle, MPW Method)

**Date drafted:** 2026-04-06
**Playbook:** MPW Strangle -- equal dollar amounts both sides, cut loser fast, let winner run
**Catalyst window:** CPI Friday Apr 10 8:30 AM + Islamabad talks Saturday Apr 11 + Monday open
**Expiry logic:** Apr 16 captures all three catalysts; Apr 17 acceptable alternate

---

```
POSITION: SPY Apr 16 $675P / $692C -- CPI + Weekend Ceasefire Strangle (MPW Method)

Action:     Buy to open 1x SPY Apr 16 $675 Put
            Buy to open 1x SPY Apr 16 $692 Call
Entry:      Friday April 10, 10:00-10:30 AM ET (post-CPI IV crush window)
            ALTERNATE: Thursday April 9 afternoon (2:00-3:00 PM, post-PCE IV crush)
Cost:       ~$1.80 total debit (~$1.20 put + ~$0.60 call, estimated at post-CPI IV trough)
Quantity:   1x each leg (2 contracts total)
Max loss:   $180 (full premium -- both legs expire worthless)
Max profit: Uncapped on upside; ~$850+ on downside gap fill to SPY $661
Breakeven:  SPY below ~$673.20 or above ~$693.80 by expiry
Take profit: Sell full strangle at $4.00+ total value ($220+ profit, ~120% return)
Stop loss:  None needed -- max loss is $180 < $200 constitutional limit
Time stop:  Exit by Wednesday April 15, 3:00 PM ET regardless of P&L
Invalidation: VIX drops below 16 (no event risk priced). SPY moves more than $12
              from $678 before entry (the event already happened without you).
Why THIS trade: CPI Friday catches the tail of the Hormuz oil spike in March data.
              Islamabad talks Saturday with Iran's 31 uncoordinated militaries makes
              any ceasefire outcome binary -- either credible enforcement framework
              (bullish, call wins) or structural collapse confirmation (bearish, put
              wins). The strangle does not need to guess direction. Apr 16 expiry
              captures CPI reaction + full weekend + Monday open repricing. MPW
              equal-dollar method: ~$1.20 put, ~$0.60 call -- if fills diverge,
              adjust quantity or walk limits to equalize dollar exposure per side.
```

---

## CONSTITUTION COMPLIANCE

| Rule | Limit | This Trade | Pass/Fail |
|---|---|---|---|
| Max risk per position | $200 | $180 (full premium loss) | PASS |
| Max total portfolio risk | $500 | $180 (assumes no other open positions) | PASS |
| Max positions open simultaneously | 3 | 1 (this position only) | PASS |
| Max correlated (same direction) | 2 | N/A -- strangle is non-directional | PASS |
| Min cash reserve (90%) | $9,000 | $10,000 - $180 = $9,820 | PASS |
| Max single position as % of risk budget | 50% ($250) | $180 = 36% of $500 budget | PASS |
| Max legs per position | 2 | 2 (one put, one call) | PASS |
| No naked short options | -- | Long options only, no short legs | PASS |
| No 0DTE | Min 4 calendar DTE | Apr 16 = 6 DTE at Friday entry (10 DTE at Thu entry) | PASS |
| Commission check (round-trip < 3% of max profit) | $2.60 RT | Max profit $850+; $2.60/$850 = 0.3% | PASS |
| No entries before 10:00 AM ET | -- | Entry 10:00-10:30 AM (or Thu 2-3 PM) | PASS |
| No entries within 90 min of CPI | CPI 8:30 AM | 10:00 AM = 90 min after CPI | PASS |
| Max entries per day | 2 | 1 entry (both legs are one position) | PASS |
| No chasing | $0.15 max walk | Limit orders, 3 walks max | PASS |

**All 14 constitutional rules: PASS. No exceptions required.**

---

## GEX STRIKE COMPLIANCE

| Leg | Strike | Approved Strike? | GEX Source |
|---|---|---|---|
| Long Put | $675 | YES | Max pain magnet, significance 0.8 |
| Long Call | $692 | YES | Hedge wing above call wall, "against" = cheap |

Both strikes are on the approved strike list from W1-02 GEX Strike Map.

**Alternate call strike:** $695 (far hedge wing, deep OTM) is also approved. Using $692 provides slightly better delta and lower breakeven. If $692 premium exceeds budget at entry, substitute $695 to reduce total debit.

---

## THESIS

### Why a Strangle, Why Now

Three catalysts converge in a 72-hour window:

1. **CPI Friday 8:30 AM (March data)** -- This is the first CPI print that captures the Hormuz oil spike. Oil went from ~$80 to $112 in the back half of March. Even if core CPI strips direct energy, second-order effects (transport, logistics, food supply chains) bleed into core services. A hot print accelerates the bearish gap-fill thesis. A cool print (shelter deceleration, pre-Hormuz goods deflation) ignites a relief rally.

2. **Islamabad talks Saturday April 11** -- Iran has 31 separate armed services. Supreme Leader Khamenei reportedly in a coma. No single authority can order all branches to stand down. Outcomes are binary:
   - "Framework" without IRGC participation = ceasefire collapse confirmation = bearish
   - IRGC participation + enforcement mechanism = genuine deescalation = bullish
   - Talks collapse = status quo = mildly bearish (market had priced some hope)

3. **Monday open repricing** -- Whatever happens Saturday reprices into SPY at Monday 9:30 AM. The strangle lives through this with 2 DTE remaining on Apr 16.

The strangle does not require a directional call. It requires the combination of CPI + geopolitics to produce a move larger than ~$5 in either direction. Given that the ceasefire is structurally unenforceable (31 militaries, no chain of command) and CPI catches an oil spike, the probability of a >$5 move in the CPI-to-Monday window is materially higher than what VIX ~20 is pricing.

### Why Post-CPI Entry (Not Pre-CPI)

The Risk Constitution bans entries within 90 minutes of CPI (Section 3: No entries within 90 minutes after PCE/CPI release). The earliest legal entry on Friday is 10:00 AM ET.

This is also the tactically optimal entry:

- **CPI prints at 8:30 AM.** The initial reaction takes 30-90 minutes to fully develop. By 10:00 AM, the direction and magnitude of the CPI reaction are established.
- **IV crushes post-CPI.** The CPI event premium (which inflated overnight Thursday into Friday morning) evaporates after the number is known. Options reprice 10-20% cheaper purely on catalyst removal.
- **You enter the strangle at the IV trough** -- paying for the weekend/Monday catalyst only, not the CPI catalyst that has already resolved. This is the cheapest the strangle will be before Monday.
- **If CPI is a non-event (SPY moves <$2):** The strangle is cheap (~$1.50-1.80) because IV has crushed. You hold through the weekend for the Islamabad catalyst at minimal cost.
- **If CPI is a big event (SPY moves $5+):** You assess whether the move has exhausted itself. If SPY has already moved to $670 or $685, the strangle strikes are now very asymmetric -- skip entry per invalidation rule.

### Alternate Entry: Thursday Post-PCE

If CPI timing feels too compressed, the Thursday 2:00-3:00 PM window works:
- PCE (February data, likely non-event) has crushed Thursday IV
- CPI event premium has not yet been bid into Friday morning options
- Apr 16 gives 7 DTE -- more theta cushion
- **Downside:** You pay for one extra day of theta and hold through CPI as well as the weekend. If CPI is a non-event, you bleed ~$0.20 in theta before the weekend catalyst.

---

## STRIKE SELECTION

### Put Leg: $675 (Max Pain Magnet)

| Metric | Value |
|---|---|
| Strike | $675 |
| SPX equivalent | ~6750 |
| GEX classification | Max pain magnet (significance 0.8) |
| Distance from spot | $3 OTM (0.44%) |
| Estimated price at entry | ~$1.00-1.40 (post-CPI IV trough, 6 DTE) |
| Using | $1.20 midpoint estimate |
| Delta at entry | ~-0.30 |

**Why $675 and not $678 (gamma flip):** The gamma flip at $678 is essentially ATM. An ATM put costs ~$2.50-3.00 at 6 DTE, pushing the strangle total to $3.10-3.60. Max loss would be $310-360, which still passes the $200 constitutional test but reduces the asymmetry of the payoff. The $675 put is cheaper, keeps total debit under $2.00, and still captures the gap-fill thesis because max pain at $675 acts as a gravitational magnet pulling price down toward it.

**Why not $665 (gamma floor):** Too far OTM ($13 below spot). At 6 DTE, the $665P costs ~$0.20-0.30. It requires a crash to $660 to have meaningful intrinsic value. The put side of a strangle should have realistic probability of going ITM, not just crash insurance.

### Call Leg: $692 (Hedge Wing)

| Metric | Value |
|---|---|
| Strike | $692 |
| SPX equivalent | ~6920 |
| GEX classification | Hedge wing above call wall, "against" = cheap |
| Distance from spot | $14 OTM (2.06%) |
| Estimated price at entry | ~$0.40-0.80 (post-CPI IV trough, 6 DTE) |
| Using | $0.60 midpoint estimate |
| Delta at entry | ~+0.12 |

**Why $692 and not $685 (gamma ceiling):** $685 is only $7 OTM. At 6 DTE, the $685C costs ~$1.50-2.00. A $675P/$685C strangle totals $2.70-3.20 -- too expensive for the $200 risk budget to maintain good asymmetry. More importantly, $685 is the gamma ceiling where dealer resistance is strongest. Buying a call AT the resistance level means you need SPY to break through the hardest level on the GEX map just to reach your strike. $692 is above all resistance -- if SPY gets there, the rally is genuine and the call is deep ITM.

**Why $692 over $695:** $692 is $3 closer to spot, giving slightly higher delta (~0.12 vs ~0.08) and better probability of reaching profitability. The price difference is ~$0.20. Both are approved strikes. If $692 premium is too high at entry (>$0.80), substitute $695.

### MPW Equal-Dollar Method

MPW's strangle method specifies equal dollar amounts on both sides. With the $675P at ~$1.20 and $692C at ~$0.60, the put costs 2x the call. To equalize:

**Option A (recommended): Accept the asymmetry.**
- 1x $675P ($120) + 1x $692C ($60) = $180 total.
- The put is intentionally larger because the bearish thesis has higher conviction (8/10 direction per Conviction Calibrator) and VIX expansion on selloffs inflates put value further.
- This is a "bearish-leaning strangle" which is honest about the directional bias while maintaining upside optionality.

**Option B (strict MPW): Equalize with quantity.**
- 1x $675P ($120) + 2x $692C ($120) = $240 total.
- Exceeds the desirable range. Two call contracts also create directional exposure that contradicts the strangle's non-directional premise at a higher cost.
- NOT recommended.

**Option C: Walk the put strike down to equalize.**
- Use $669P (~$0.60) + $692C (~$0.60) = $120 total.
- $669 is the gap midpoint, an approved strike. But $0.60 on the put gives it very low probability of profitability -- you need SPY at $668 just to break even on the put side. This defeats the purpose.
- NOT recommended unless budget is constrained below $150.

**Decision: Option A.** The bearish lean is justified by the thesis. MPW's equal-dollar principle is a guideline for direction-agnostic event trades; this trade has a known directional bias (ceasefire fragility) with an acknowledged upside tail (Islamabad breakthrough). The put should be the larger leg.

---

## PRICING MATH

### Entry Assumptions
- SPY at ~$678 (may have moved $2-4 on CPI by 10:00 AM)
- VIX at ~18-19 (post-CPI IV crush from ~20)
- DTE: 6 (Apr 16 expiry, entered Friday Apr 10)

### Put Leg ($675P)

| Input | Value |
|---|---|
| Spot | $678 |
| Strike | $675 |
| IV | ~19% (put skew premium over post-CPI trough) |
| DTE | 6 |
| Delta | ~-0.30 |
| Theta | ~-$0.18/day |
| Vega | ~$0.09 per 1pt IV |
| Estimated price | $1.00-1.40 (using $1.20) |

### Call Leg ($692C)

| Input | Value |
|---|---|
| Spot | $678 |
| Strike | $692 |
| IV | ~17% (call at "against" GEX zone, cheap) |
| DTE | 6 |
| Delta | ~+0.12 |
| Theta | ~-$0.08/day |
| Vega | ~$0.05 per 1pt IV |
| Estimated price | $0.40-0.80 (using $0.60) |

### Combined Strangle

| Metric | Value |
|---|---|
| Total debit | ~$1.80 ($180 total) |
| Combined theta | ~-$0.26/day ($26/day bleed) |
| Combined vega | ~$0.14 per 1pt IV |
| Downside breakeven | ~$673.20 (SPY needs to fall $4.80) |
| Upside breakeven | ~$693.80 (SPY needs to rise $15.80) |

Note: The breakevens are asymmetric by design. The put is much closer to ITM ($3 OTM) than the call ($14 OTM). The bearish scenario is the primary thesis; the call is tail optionality for a geopolitical surprise.

---

## SCENARIO ANALYSIS

### Scenario 1 -- Hot CPI + ceasefire deterioration over weekend, SPY gaps to $665 Monday, VIX 28

- Put: Intrinsic $675-$665 = $10.00 + extrinsic ~$0.80 + vega boost ~$0.70 = ~$11.50
- Call: Deep OTM, near-zero. ~$0.02
- Total value: ~$11.52
- **Profit: $11.52 - $1.80 = $9.72 ($972 profit, 540% return)**

### Scenario 2 -- Hot CPI, moderate selloff to SPY $670, VIX 24

- Put: Intrinsic $675-$670 = $5.00 + extrinsic ~$0.60 = ~$5.60
- Call: OTM, minimal. ~$0.08
- Total value: ~$5.68
- **Profit: $5.68 - $1.80 = $3.88 ($388 profit, 216% return)**

### Scenario 3 -- CPI non-event, ceasefire collapse Monday, SPY gaps to $668, VIX 26

- Friday close: Both legs bled. Combined ~$1.40 (below entry but above zero).
- Monday open with SPY at $668: Put jumps to ~$7.50 (intrinsic $7 + extrinsic). Call dies.
- Total: ~$7.55
- **Profit: $7.55 - $1.80 = $5.75 ($575 profit, 319% return)**
- This is the scenario that justifies Apr 16 over 0DTE: surviving a quiet Friday to capture Monday's gap.

### Scenario 4 -- Islamabad breakthrough, SPY rallies to $695 Monday, VIX 15

- Call: Intrinsic $695-$692 = $3.00 + extrinsic ~$0.30 = ~$3.30. VIX crush hurts vega.
- Put: Worthless. ~$0.01.
- Total: ~$3.31
- **Profit: $3.31 - $1.80 = $1.51 ($151 profit, 84% return)**
- The call wing works even in the bullish tail scenario, albeit with smaller profit due to VIX compression on rallies.

### Scenario 5 -- CPI inline, quiet weekend, SPY chops 675-681

- Friday: IV crush kills both legs. Combined value drops from $1.80 to ~$1.20.
- Weekend: No catalyst. Monday: Theta continues. Combined value ~$0.80.
- By Wednesday time stop: Combined value ~$0.30-0.50.
- **Loss: $1.80 - $0.40 = $1.40 ($140 loss, 78% of premium)**
- This is the worst realistic outcome. Note: still under $200 constitutional max.

### Scenario 6 -- CPI hot but SPY only drops $3 (to $675), then reverses

- Friday 10:30 AM: Put at $675 is ATM, worth ~$1.60. Call crushed to ~$0.15. Total ~$1.75.
- This is breakeven territory. The CPI move was real but not large enough.
- Hold through weekend for second catalyst. If Monday is quiet, exit at time stop.
- **Likely outcome: -$0.30 to +$1.00 ($30 loss to $100 profit)**

---

## ENTRY RULES (Non-Negotiable)

### Primary Entry: Friday April 10, 10:00-10:30 AM ET

1. CPI prints at 8:30 AM Friday. **Do not enter before 10:00 AM.** (Constitution Section 3: 90-minute blackout after CPI.)
2. By 10:00 AM, the CPI reaction is established. Assess:
   - **SPY moved >$5 from Thursday close:** Directional move is large. Check if entry strikes are still reasonable. If SPY is below $670, the $675P is already ITM -- the strangle is no longer a strangle, it is a directional bet. **Skip entry.**
   - **SPY moved $2-5:** CPI moved the market. IV has partially crushed. **Enter the strangle.** This is the sweet spot.
   - **SPY moved <$2:** CPI was a non-event. IV crushed hard. **Enter the strangle cheap.** You are now primarily trading the weekend catalyst, and the strangle is at its lowest cost.
   - **SPY moved >$8:** The CPI reaction was extreme. Premiums are repriced. **Do not enter.** The move already happened.

3. Place limit orders at mid-price:
   - Buy 1x SPY Apr 16 $675P: Limit $1.20, walk up in $0.05 increments, max 3 walks, ceiling $1.35.
   - Buy 1x SPY Apr 16 $692C: Limit $0.60, walk up in $0.05 increments, max 3 walks, ceiling $0.75.
   - Combined max entry: $2.10. If total fill exceeds $2.10, do not enter.

4. Both legs must fill within 15 minutes. If one fills and the other does not after 15 minutes and 3 walks, close the filled leg and stand down.

### Alternate Entry: Thursday April 9, 2:00-3:00 PM ET

Use this if:
- You want more DTE (7 instead of 6)
- You want to hold through CPI as an additional catalyst
- PCE Thursday was a non-event and IV has crushed

Same limit order protocol. Thursday prices may be slightly higher (~$2.00-2.20 total) because CPI event premium is partially priced in.

### Abort Conditions

- SPY has moved >$8 from prior close by entry time
- VIX has dropped below 16 (no event risk priced, strangle will bleed)
- VIX has spiked above 30 (premiums too inflated, strangle costs $3.00+)
- SPY is already below $670 or above $686 at entry time (strikes are misaligned)
- Combined strangle cost exceeds $2.10 at best available fill

---

## EXIT RULES -- MPW METHOD

### Rule 1: Take Profit at $4.00 Combined (120%+ Return)

If the strangle reaches $4.00 total value at any point, sell both legs. Profit: $2.20+ ($220+).

On a big move (SPY to $668 or $693+), one leg will be worth $5.00+ and the other near-zero. Sell both. Do not hold the winning leg hoping for $10.00. The 120% return on a $180 position is $220 profit. That is the win.

### Rule 2: Kill the Loser When Direction Commits

Once SPY commits to a direction (sustained move for 30+ minutes, confirmed by volume):

- **SPY below $674 and falling:** The put is working. **Sell the $692 call.** Recover whatever it is worth ($0.05-0.20). Let the put ride with a trailing stop at 50% of its current value.
- **SPY above $685 and rising:** The call is working. **Sell the $675 put.** Same logic.

"Committed direction" means: SPY has moved $4+ from entry-time price AND held the move for 30 minutes without retracing more than $1.

### Rule 3: Weekend Hold Decision -- Friday 3:30 PM ET

At Friday 3:30 PM, assess:

- **Strangle value > $2.50 (profitable):** Hold through weekend. Islamabad talks provide additional catalyst. Set Monday exit plan.
- **Strangle value $1.20-2.50 (modest loss to small gain):** Hold through weekend. The strangle still has 3 DTE and a weekend catalyst. Theta cost to hold is ~$0.26. The weekend binary is worth more than $0.26.
- **Strangle value < $1.20 (>$0.60 loss, >33% drawdown):** Evaluate. If CPI moved SPY $3+ in a direction and the strangle is still losing (stuck in the dead zone), consider closing one leg (the losing one) and holding the other as a directional punt through the weekend. If CPI was a total non-event and VIX is at 17, close everything -- the weekend catalyst alone may not be enough.
- **Strangle value < $0.50:** Close everything. The position is dying. Weekend miracle is not a strategy.

### Rule 4: Monday Morning Management (If Held Through Weekend)

- **Monday opens with SPY gapped >$5 from Friday close:** One leg is deep ITM. Sell the winning leg in the first 30 minutes (after 10:00 AM per constitution -- Monday has extended blackout to 10:30 AM). Sell the losing leg for whatever is left.
- **Monday opens flat:** Hold. You have 2 DTE remaining. The Islamabad talks outcome may take 24-48 hours to fully reprice. Set a tighter time stop: exit Tuesday 3:00 PM if no movement.
- **Monday opens with SPY gapped against your bigger leg (rally >$5):** If call is ITM, take profit. If neither leg is ITM and the strangle has decayed below $0.50, close.

### Rule 5: Time Stop -- Wednesday April 15, 3:00 PM ET

Absolute hard exit. No exceptions. Do not hold into the final 24 hours of Apr 16 expiry. Theta accelerates to ~$0.50+/day in the final day and the position bleeds to zero.

### Rule 6: VIX Collapse Invalidation

If VIX drops below 16 at any point while holding, exit both legs within 60 minutes. The strangle is long vega. VIX below 16 compresses both legs simultaneously.

---

## RISK FLAGS

1. **CPI inline (30-40% probability).** Both legs bleed on IV crush. Mitigated by: entering AFTER the crush (10:00 AM), so you buy the post-crush price, not the pre-crush price. Your risk is the weekend/Monday catalyst, not CPI itself.

2. **Asymmetric breakevens.** The call needs a $15.80 move ($692 - $678 + $1.80 debit) vs the put's $4.80 move. The call is tail optionality, not a primary thesis. If this asymmetry bothers you, accept it -- the call is insurance for the 15% scenario where Islamabad talks produce a real breakthrough.

3. **Weekend theta bleed.** Holding from Friday to Monday costs ~$0.52 in theta (2 days x $0.26/day). This is the price of capturing the weekend catalyst. If the weekend catalyst does not fire, you lose an extra $0.52 beyond the CPI-day loss.

4. **Liquidity at $692C.** Deep OTM calls may have wider bid-ask spreads. Apr 16 monthly cycle helps. Expect $0.05-0.10 spread at the $692 strike. Fill at mid.

5. **CPI moves SPY into the dead zone ($673-677).** Put is near-ATM but not ITM enough to overcome the call's total loss. Strangle value is ~$1.50-1.80 (breakeven-ish). This is the frustrating non-result. Manage via weekend hold decision at Friday 3:30 PM.

---

## WHAT THIS TRADE IS

- A **multi-catalyst event strangle** spanning CPI + weekend geopolitics + Monday open
- **Bearish-leaning** (put is 2x the dollar exposure of the call) with upside tail protection
- A **post-event entry** that buys cheap after CPI IV crush, then holds for the weekend binary
- A **defined-risk position** where max loss ($180) is structurally below the $200 constitutional limit with no stop order needed
- **GEX-compliant** using only approved strikes from W1-02

## WHAT THIS TRADE IS NOT

- A 0DTE scalp (constitution bans 0DTE; this is 6 DTE)
- A directional bet (it is directionally biased but profits on a large move in either direction)
- A position to double down on ("I'll buy another strangle if Monday gaps the wrong way" -- no)
- A hedge for any other portfolio position (this stands alone)

---

## EXECUTION CHECKLIST -- Friday April 10

### Pre-CPI (7:00-8:25 AM ET)
- [ ] Review CPI consensus: Core MoM expected ~+0.3%, YoY expected ~3.5%
- [ ] Have broker platform open with SPY Apr 16 $675P and $692C quotes staged
- [ ] Note Thursday close price for SPY and VIX
- [ ] Set alerts: SPY at $670, $674, $682, $686 (abort boundaries)

### CPI Release + Blackout (8:30-10:00 AM ET)
- [ ] CPI prints at 8:30 AM. Record actual print vs consensus
- [ ] **DO NOT ENTER.** Constitution blackout until 10:00 AM
- [ ] Monitor SPY magnitude and direction through 10:00 AM
- [ ] Record: SPY moved ___ from Thursday close, direction is ___, VIX is ___

### Entry Decision (10:00-10:30 AM ET)
- [ ] Check abort conditions (SPY moved >$8? VIX <16? VIX >30? SPY below $670 or above $686?)
- [ ] If no abort: at 10:00-10:15 AM, enter limit orders at mid-price
- [ ] Buy 1x SPY Apr 16 $675P: Limit $1.20, walk to $1.35 max
- [ ] Buy 1x SPY Apr 16 $692C: Limit $0.60, walk to $0.75 max
- [ ] Confirm fills within 15 minutes. If one leg stuck after 3 walks, close filled leg
- [ ] Record entry prices: Put @ $___, Call @ $___, Total strangle = $___

### Friday Afternoon (3:30 PM ET)
- [ ] Evaluate strangle value per Weekend Hold Decision rules
- [ ] If holding: no further action until Monday
- [ ] If closing: exit both legs before 3:50 PM

### Monday Management (10:30 AM ET -- extended blackout per constitution)
- [ ] Check Sunday evening futures for weekend gap direction
- [ ] At 10:30 AM Monday: evaluate per Rule 4
- [ ] If gap >$5 in either direction: sell winning leg, close loser

### Time Stop
- [ ] **Wednesday April 15, 3:00 PM ET: CLOSE EVERYTHING REMAINING. No exceptions.**

---

## SUMMARY FOR BOREY

Buy a $675 put and $692 call on SPY, April 16 expiry. Enter Friday morning after CPI crushes IV (10:00-10:30 AM window). Total cost: ~$1.80 ($180). Max loss is $180 -- under the $200 constitutional limit with no stop order needed because both legs are long options.

The put captures the gap-fill thesis at the GEX max-pain magnet strike. The call captures the tail scenario where Islamabad talks produce a genuine ceasefire breakthrough. Both strikes are GEX-approved.

The Apr 16 expiry is the key decision: it survives CPI Friday, the full weekend of Islamabad talks, AND Monday's repricing. A 0DTE would miss the weekend. A weekly would expire before the ceasefire catalyst fully reprices.

Three catalysts, two legs, $180 risk, 6 days of runway. Enter after the CPI crush. Let the weekend do the work.
