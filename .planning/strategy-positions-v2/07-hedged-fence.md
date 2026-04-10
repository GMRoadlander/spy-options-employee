# Position 07: Hedged Fence — Bear Put Spread + OTM Call Kicker

**Date drafted:** 2026-04-06
**Market context:** SPX ~6783 (SPY ~678). Gap up from ~6610 on ceasefire headlines. VIX ~20. PCE Thursday 4/9, CPI Friday 4/10.
**Thesis update:** Swarm analysis revised bull case probability DOWN from 40% to 15-20%. Iran's fractured command structure (31 militia groups, Supreme Leader health crisis) makes ceasefire structurally unenforceable. Gap fill to SPY ~661 remains base case at ~55-60%. But 15-20% is not zero — a cheap call kicker keeps the rally scenario survivable.
**Account:** $10,000. Max total risk: 3% = $300.

---

## The Structure

Bearish core with a small upside insurance policy. The put spread captures the gap fill. The call kicker means a surprise rally to 690 costs you $100 instead of $300. You are paying $45 for that protection. At 15-20% rally probability, this is marginally positive expected value insurance — and more importantly, it lets you hold the bearish position through Monday/Tuesday headlines without flinching.

---

## POSITION: SPY Apr 11 675/668 Bear Put Spread + SPY Apr 11 688 Call

### Leg 1 — Bearish Core: SPY Apr 11 675/668 Bear Put Spread

| Field | Value |
|---|---|
| **Buy** | SPY Apr 11 675 Put |
| **Sell** | SPY Apr 11 668 Put |
| **Width** | $7.00 |
| **Net debit** | ~$2.55 per spread |
| **Contracts** | 1 |
| **Cost** | $255 |

**Why 675 long leg:** $3 OTM from SPY 678. Delta ~0.37. Close enough to participate immediately in any dip, far enough out that you are not overpaying for a put that is already near the money. If SPY drops $3 on Monday morning, this put is ATM and accelerating.

**Why 668 short leg:** $3 above the gap fill target of SPY 661 (SPX 6610). The short leg caps your profit just above the target zone — but you capture 100% of the move from 675 down to 668. You do NOT need SPY to overshoot the gap fill. If SPY hits 668, the spread is at max value. Every dollar below 668 is someone else's profit, and that is fine.

**Why $7 width:** Wide enough for meaningful reward ($4.45 max profit per spread) but narrow enough that the debit stays under $3.00, leaving room for the call hedge within the $300 budget. A $5-wide (675/670) only pays $2.45 max and does not reach full value unless SPY drops $8. A $10-wide (675/665) costs $3.40+ and blows the budget with no room for the hedge.

### Leg 2 — Upside Hedge: SPY Apr 11 688 Call

| Field | Value |
|---|---|
| **Buy** | SPY Apr 11 688 Call |
| **Contracts** | 1 |
| **Cost** | ~$0.45 per contract = $45 |

**Why 688 strike:** $10 OTM from SPY 678. Delta ~0.10. This call only matters if the ceasefire somehow gains credibility and SPX rips through 6880 (SPY 688). At that point, something fundamental has changed — Iran is cooperating, Houthis are standing down, oil is dropping — and you need the hedge. Below 688, this call expires worthless and you accept the $45 as insurance premium.

**Why a naked call, not a call spread:** At $0.45, this is already dirt cheap. Selling a further OTM call (say 695C at $0.15) saves $15 and caps your upside recovery. Not worth it. If SPY is at 695, you WANT the uncapped call to be recovering as much of the put spread loss as possible. The whole point is making the rally scenario survivable.

---

## Combined Position Summary

| Metric | Value |
|---|---|
| **Total cost (max risk)** | $255 + $45 = **$300** |
| **Account risk** | **3.0%** of $10,000 — exactly at the stated limit |
| **Put spread max profit** | $7.00 - $2.55 = $4.45 x 1 = $445 |
| **Downside breakeven** | SPY 672.45 at expiry (675 - $2.55 debit) |
| **Upside breakeven on hedge** | SPY 688.45 at expiry (688 + $0.45 premium) |
| **Reward:Risk (max)** | $445 / $300 = 1.48:1 on gap fill |
| **Reward:Risk (realistic)** | ~$355 / $150 = 2.4:1 (managed loss vs partial fill) |

---

## Scenario Analysis — P&L at Expiry

### Scenario 1: Gap Fill — SPY 661 (SPX ~6610) — 55-60% probability

The base case. Ceasefire fractures, Houthi activity resumes, gap fills by Wednesday/Thursday.

| Leg | Calculation | Value |
|---|---|---|
| 675/668 put spread | Fully ITM. Worth $7.00 (max width). | +$7.00 |
| Spread P&L | $7.00 - $2.55 debit | **+$4.45** |
| 688 call | Expires worthless. | -$0.45 |
| **Net P&L** | | **+$4.00 (+$400)** |

**Return on capital: +133%.** The put spread is fully in the money. The call kicker is a $45 cost of doing business. You collected $4.00 net on $3.00 risk.

### Scenario 2: Rally — SPY 690 (SPX ~6900) — 15-20% probability

The ceasefire holds. Iran falls in line. Market extends to 6900. This is the scenario the hedge exists for.

| Leg | Calculation | Value |
|---|---|---|
| 675/668 put spread | Both legs expire worthless. | -$2.55 |
| 688 call | SPY 690 - 688 strike = $2.00 intrinsic | +$2.00 |
| Call P&L | $2.00 - $0.45 premium | **+$1.55** |
| **Net P&L** | -$2.55 + $1.55 | **-$1.00 (-$100)** |

**Loss: $100 (1.0% of account).** This is the entire point of the hedge. Without the call kicker, this scenario costs you the full $255 put spread debit. With it, you lose $100. The rally scenario is survivable — not profitable, not breakeven, but a small controlled loss that does not damage the account or your psychology. You can immediately re-enter a bearish position if the rally stalls at 690.

If SPY reaches 695 instead of 690, the call is worth $7.00, netting +$6.55 on the call vs -$2.55 on the spread = **+$4.00 net profit**. The further the rally extends, the better the hedge works. Above 693.45, the position actually makes money in the bull scenario.

### Scenario 3: Chop — SPY 678 (SPX ~6780) — 15-20% probability

The worst case. Market does nothing. Ceasefire narrative lingers, no clear catalyst, SPY oscillates 675-682 all week.

| Leg | Calculation | Value |
|---|---|---|
| 675/668 put spread | 675P expires ~$0.20 residual (just OTM). 668P worthless. Spread ~$0.20. | -$2.35 |
| 688 call | Expires worthless. | -$0.45 |
| **Net P&L** | | **-$2.80 (-$280)** |

**Loss: $280 (2.8% of account).** Near max loss. This is the scenario where you are simply wrong about the catalyst timeline. Nothing happened. Theta ate both sides. This is why you manage the position (see Management Rules below) — if chop is developing by Wednesday, you close for $150-180 loss instead of riding to $280.

### Scenario 4: Crash — SPY 640 (SPX ~6400) — 5-10% probability

Black swan. Iran conflict escalates, ceasefire collapses violently, broader market selloff.

| Leg | Calculation | Value |
|---|---|---|
| 675/668 put spread | Fully ITM. Worth $7.00 (max width). Capped by short 668P. | +$7.00 |
| Spread P&L | $7.00 - $2.55 debit | **+$4.45** |
| 688 call | Expires worthless. | -$0.45 |
| **Net P&L** | | **+$4.00 (+$400)** |

**Return on capital: +133%.** Identical to the gap fill scenario. The short 668P caps your profit — you do not benefit from a crash below 668. This is the tradeoff for the spread structure. A naked 675P would be worth $35.00 at SPY 640. Your spread is worth $7.00. You gave up the tail. That is correct — you are trading a gap fill thesis, not a crash thesis. The $400 profit is the right outcome for the right thesis.

---

## P&L Summary Table

| Scenario | SPY Level | SPX Level | Put Spread | Call Hedge | Net P&L | % of Account |
|---|---|---|---|---|---|---|
| Gap fill | 661 | ~6610 | +$445 | -$45 | **+$400** | +4.0% |
| Rally | 690 | ~6900 | -$255 | +$155 | **-$100** | -1.0% |
| Chop | 678 | ~6780 | -$235 | -$45 | **-$280** | -2.8% |
| Crash | 640 | ~6400 | +$445 | -$45 | **+$400** | +4.0% |

**Expected value (probability-weighted):**
- Gap fill (57.5% x $400) = +$230
- Rally (17.5% x -$100) = -$17.50
- Chop (17.5% x -$280) = -$49
- Crash (7.5% x $400) = +$30
- **EV = +$193.50 per occurrence**

---

## Entry Plan

- **Day:** Monday 2026-04-07
- **Time:** 9:50-10:15 AM ET. Let opening volatility settle. SPY weekly options have wide bid-ask spreads in the first 10 minutes.
- **Order type:** Enter the bear put spread as a single spread order (limit at $2.55 or better). Enter the 688 call separately as a limit at $0.45. If your broker supports 3-leg custom orders, enter all at once for $3.00 total debit.
- **Ideal entry:** SPY trading 677-682. The put spread is slightly OTM and reasonably priced. The call is cheap.

**Skip conditions:**
- SPY opens above 685: Ceasefire rally is already extending. Call kicker is expensive ($1.00+), put spread is too cheap. Skip or wait for a pullback.
- SPY opens below 672: Gap fill is in motion. The 675P is already ITM and the spread costs $4.00+. You missed the entry. Do not chase.
- VIX drops below 16: Complacency. Options are cheap but the catalyst has evaporated. No trade.

---

## Management Rules

This is a $300 position. The management is proportionally simple.

### Monday after entry

Set alerts at SPY 682 (above = bearish thesis weakening) and SPY 673 (below = thesis activating). Check at noon, 2 PM, and 3:45 PM. Otherwise close the screen.

- SPY above 680: Fine. Day 1. The thesis does not require a Monday move.
- SPY 674-680: Exactly where expected. No action.
- SPY below 674: 675P is going ITM. Position is already profitable. Hold.

### Tuesday — Key Day

Gap fills historically accelerate on Tuesdays as institutional flows shift from headline-chasing to fundamental repricing.

- SPY breaks below 673: Position is solidly profitable. Hold for gap fill target.
- SPY 676-680: Thesis alive but not confirmed. Hold. Theta is mild on the spread.
- SPY pushes above 683: Thesis is in trouble. Tighten mental stop. If SPY closes above 683, close the put spread Wednesday morning for ~$1.20-1.50 (loss of ~$105-135). Keep the call as a free lottery ticket.

### Wednesday — Decision Day

By Wednesday close, you need conviction. Thursday is PCE, Friday is CPI. You do not want to hold an ambiguous position through two binary events at 1-2 DTE.

- SPY below 670: The spread is worth $5.00+. Take profit. Close everything. Net ~+$200-250. Do not hold for the last $2.00 through PCE.
- SPY 670-675: Spread is worth $2.80-4.00. You are roughly breakeven to slightly profitable. Decision: if SPY is trending down, hold one more day. If chopping, close for small gain/small loss.
- SPY above 676: Close the put spread. Accept the loss (~$100-180). Keep the call if VIX is rising (it has optionality into PCE/CPI). Sell the call if VIX is falling.

### Thursday (PCE, 8:30 AM ET)

Only in this position if Wednesday was below 675 (thesis is working).

- Hot PCE (above consensus): Accelerates the gap fill. SPY drops. Hold for gap fill target. Close by 2 PM.
- Cool PCE: SPY bounces. Close everything in the bounce. Take whatever profit exists.
- In-line PCE: Market does nothing. Close by noon. Do not hold into Friday with 1 DTE.

### Friday — Hard Stop

Do NOT hold any leg into Friday close. If somehow still in the trade, close between 10:00-10:30 AM after the CPI print settles. No exceptions. Pin risk and gamma risk at expiry are not worth the last few cents.

---

## Why This Structure Over Position 10 (v1 Hedged Bearish)

Position 10 was designed when the bull case was 40%. It used a $1,000 total risk budget (10% of account) and 2 contracts of a $15-wide spread. That was appropriate at the time.

The situation has changed:

| Factor | Position 10 (v1) | Position 07 (v2, this) |
|---|---|---|
| Bull case probability | 40% | 15-20% |
| Total risk | $1,000 (10%) | $300 (3%) |
| Contracts | 2 | 1 |
| Put spread width | $15 | $7 |
| Call hedge cost | $160 (2 contracts) | $45 (1 contract) |
| Rally (690) P&L | ~$0 (breakeven) | -$100 (small loss) |
| Gap fill (661) P&L | +$1,800 | +$400 |
| Chop (678) P&L | -$1,000 | -$280 |

**Key differences:**
1. **Risk is right-sized.** 3% max risk vs 10%. With a reduced bull case, you do not need heavy hedge spending, so the total position can be smaller.
2. **The hedge is cheaper and proportional.** $45 for one call vs $160 for two. The bull case dropped by half — the insurance should drop too.
3. **Rally scenario is a small loss, not breakeven.** This is intentional. At 15-20% probability, paying enough to reach full breakeven on the rally is over-insuring. A $100 loss on a $300 position in a 15% probability scenario is the correct amount of pain.
4. **Simpler execution.** 3 legs, 1 contract each. One spread order, one call order. No multi-contract scaling in and out.

---

## What Can Go Wrong

**VIX expansion before entry.** If VIX spikes to 25+ Monday morning on weekend headlines, the 675P costs $6.50 instead of $4.80 and the spread costs $3.40+. The structure no longer fits the $300 budget. Solution: narrow the spread to $5 wide (675/670) at ~$2.20, or wait for VIX to settle.

**Ceasefire narrative strengthens over the weekend.** If Sunday news shows concrete Houthi compliance (ships moving, drones grounded), SPY may gap up to 683+ Monday and the put spread is deeply OTM. Solution: skip the trade. The thesis depends on ceasefire fragility. If that assumption is invalidated, the trade is invalidated.

**Gap fill overshoots.** SPY drops to 655, you are capped at $7.00 on the spread. You watch $20 of additional put profit walk away. This is the cost of defined risk and it is the correct cost. You are not trading a crash thesis.

**SPY pins at 675 on expiry.** The worst micro-scenario: 675P expires ATM with maximum uncertainty. Solution: the Wednesday management rule prevents this. You are out by Thursday at the latest.

---

## The Bottom Line

$300 at risk. $400 max gain. Rally costs you $100 instead of $255. The structure fits the thesis, the budget, and the updated probabilities. It is not exciting. It does not need to be.
