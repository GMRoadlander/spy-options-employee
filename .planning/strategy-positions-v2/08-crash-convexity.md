# Position 08: Crash Convexity -- Put Backspread

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783)
**Thesis:** The ceasefire is unenforceable. Iran has 31 armed services factions, the Supreme Leader is incapacitated, and no central authority can compel compliance. If the ceasefire collapses and Hormuz re-closes, oil spikes to $120+, the gap from ~6610 unwinds violently, and MPW's Elliott Wave-3 target of SPX sub-6000 comes into play. This is the tail risk position: small cost if wrong, enormous payout if the crash materializes.
**Account:** $10,000 | **Risk budget:** $200 max (2% of account)

---

## POSITION: 1x2 Put Backspread (x2)

| Field | Detail |
|---|---|
| **Structure** | **Sell 2x SPY May 16 $672P / Buy 4x SPY May 16 $662P** |
| **Ratio** | 1:2 per backspread (sell 1 higher, buy 2 lower) x 2 sets |
| **Entry** | Monday Apr 7, 2026, 10:00-10:30 AM ET |
| **Expiry** | May 16, 2026 (39 DTE at entry) |
| **Spread width** | $10 (672 - 662 = 10 points) |
| **Net debit** | ~$1.00 per backspread ($100 per set) |
| **Quantity** | 2 backspreads (sell 2x 672P, buy 4x 662P) |
| **Total cost** | ~$200 net debit (2 x $100) |
| **Theoretical max loss** | $2,200 at SPY $662 (see danger zone -- avoidable with management) |
| **Practical max loss** | $200 (the debit paid -- if SPY stays above 672 at expiry) |
| **Lower breakeven** | ~$651 at expiry |

---

## Pricing Estimates (SPY ~678, VIX ~20, 39 DTE)

Black-Scholes estimates at 20% implied volatility, 39 DTE to May 16:

| Leg | Strike | Delta | Est. Price | Qty | Cash Flow |
|---|---|---|---|---|---|
| Short put | 672P | ~0.24 | ~$6.00 | Sell 1 | +$600 credit |
| Long put | 662P | ~0.15 | ~$3.50 | Buy 2 | -$700 debit |
| **Net per backspread** | | | | | **-$1.00 debit ($100)** |

For 2 backspreads: sell 2x 672P at $6.00 (+$1,200), buy 4x 662P at $3.50 (-$1,400). **Net debit = $200.**

**Fill reality:** Market makers will widen the spread on a multi-leg order. Use a limit order at $1.00 per backspread. If you cannot fill at $1.00, walk up to $1.10 max (total $220). Do not pay more than $1.10 per set. If VIX opens above 22 Monday morning, fills improve -- you may get in at $0.80 ($160 total).

**Why May 16 (39 DTE):** A crash unfolds over days to weeks, not hours. May 16 gives the thesis 5+ weeks to develop. April expiries are too short -- if the ceasefire collapses April 15 and the selloff runs through late April, an April 25 expiry gives you no room. May 16 survives earnings season (AAPL Apr 30, AMZN May 1, jobs May 2), multiple geopolitical news cycles, and any delayed Wave-3 trigger. The extra DTE costs more per leg but the ratio structure keeps net debit low.

---

## P&L at Expiry -- Full Position (2 backspreads)

The payoff has three zones. The numbers below are at-expiry intrinsic values for the full 2-backspread position.

| SPY at Expiry | Short 672P (x2) | Long 662P (x4) | Net Intrinsic | Less Debit | **Position P&L** |
|---|---|---|---|---|---|
| **678** (flat) | $0 | $0 | $0 | -$200 | **-$200** |
| **672** (at short strike) | $0 | $0 | $0 | -$200 | **-$200** |
| **668** (gap fill begins) | -$800 | $0 | -$800 | -$200 | **-$1,000** |
| **665** (mid-danger) | -$1,400 | $0 | -$1,400 | -$200 | **-$1,600** |
| **662** (MAX PAIN) | -$2,000 | $0 | -$2,000 | -$200 | **-$2,200** |
| **661** (full gap SPX ~6610) | -$2,200 | +$400 | -$1,800 | -$200 | **-$2,000** |
| **658** | -$2,800 | +$1,600 | -$1,200 | -$200 | **-$1,400** |
| **655** | -$3,400 | +$2,800 | -$600 | -$200 | **-$800** |
| **651** (breakeven) | -$4,200 | +$4,400 | +$200 | -$200 | **~$0** |
| **650** (crash threshold) | -$4,400 | +$4,800 | +$400 | -$200 | **+$200** |
| **645** | -$5,400 | +$6,800 | +$1,400 | -$200 | **+$1,200** |
| **640** (crash) | -$6,400 | +$8,800 | +$2,400 | -$200 | **+$2,200** |
| **635** | -$7,400 | +$10,800 | +$3,400 | -$200 | **+$3,200** |
| **630** (deep crash) | -$8,400 | +$12,800 | +$4,400 | -$200 | **+$4,200** |
| **620** (Wave-3 territory) | -$10,400 | +$16,800 | +$6,400 | -$200 | **+$6,200** |
| **610** (SPX ~6100) | -$12,400 | +$20,800 | +$8,400 | -$200 | **+$8,200** |
| **600** (SPX ~6000) | -$14,400 | +$24,800 | +$10,400 | -$200 | **+$10,200** |

### Key P&L Levels the User Asked For

| SPY Level | Scenario | Position P&L | Return on $200 |
|---|---|---|---|
| **678** | Flat / rally | **-$200** | -100% (lose the debit) |
| **668** | Gap fill start | **-$1,000** | DANGER ZONE |
| **661** | Full gap fill | **-$2,000** | DANGER ZONE |
| **650** | Crash begins | **+$200** | +100% (breakeven zone) |
| **640** | Crash / Wave-3 approach | **+$2,200** | +1,100% (11:1) |

---

## The Three Zones Explained

### Zone 1: SPY Above 672 -- BEST IF WRONG (probability ~55-60%)

All options expire worthless. You lose the $200 debit. This is the most likely outcome. The ceasefire holds, the market drifts sideways or higher, and your $200 evaporates quietly. This is the plan when the thesis is wrong. Accept it.

### Zone 2: SPY Between 652 and 672 -- THE DANGER ZONE (probability ~20-25%)

This is where the backspread punishes you. The short 672Ps are in-the-money but the long 662Ps are either worthless or barely ITM. Maximum pain is at SPY 662 where the short puts are $10 ITM, the longs are worth zero, and you owe $2,200.

**This zone corresponds to the gap fill scenario (SPY 661-668).** If SPY drops "just enough" to fill the gap but then stabilizes, you are in the worst possible outcome. The gap fill is the enemy of this trade -- this is a CRASH trade, not a gap-fill trade.

**Max loss in the danger zone: $2,200 (22% of account) if unmanaged.**

### Zone 3: SPY Below 651 -- THE CRASH PAYOFF (probability ~10-15%)

Below $651, the 4 long puts gain $4 for every $1 the 2 short puts cost you (2:1 ratio on both sides). The position gains $200 per point of SPY decline. At SPY 640, you are up $2,200. At 620 (Wave-3 territory, SPX ~6200), you are up $6,200. At 600 (SPX ~6000, full Wave-3), you are up $10,200.

The convexity accelerates the further SPY falls. Every additional dollar of decline adds $200 to your profit. A VIX spike from 20 to 40+ amplifies this further because your 4 long puts gain more vega than your 2 short puts lose.

---

## The Danger Zone Problem -- Why This Trade Demands Management

The gap fill (SPY 661-668) is the MOST LIKELY bearish scenario, and it is exactly where this trade HURTS the most. This is the central tension of the crash convexity position: the moderate bearish outcome is worse than being flat.

**If you believe the gap fill is likely, DO NOT take this trade.** This trade is ONLY for the tail -- the low-probability, high-magnitude crash. It explicitly sacrifices the gap-fill payoff for crash leverage.

The danger zone exists because you sold 2 puts at 672 to fund 4 puts at 662. Between 662 and 672, those short puts are bleeding while the longs are worthless. The 2:1 long ratio only saves you once SPY is deep enough below 662 that the longs overpower the shorts.

---

## Trade Management Rules

### Rule 1: If SPY Stays Above 672 -- Do Nothing

The position decays slowly (theta on far-OTM options at 39 DTE is ~$0.02-0.05/contract/day). Let it sit. Check once a day. If by May 8 (8 DTE) SPY is still above 672, close for whatever pennies remain or let it expire worthless.

### Rule 2: THE CRITICAL RULE -- Close if SPY Enters and Stays in the Danger Zone

**If SPY drops to 665-668 and stabilizes there for 2+ trading days:**

Close the entire position immediately. Do not wait.

At SPY 666 with 20 DTE remaining, the position will be worth approximately -$800 to -$1,200 (the short puts have time value working against you, but not yet at max intrinsic loss). Eating a $1,000-$1,200 loss here prevents the $2,200 max loss at expiry.

**Trigger:** SPY below 670 for 2 consecutive closes AND VIX has NOT spiked above 30. If VIX is above 30, the market is panicking and may continue lower -- hold. If VIX is 22-25 and SPY is at 666, the market is "orderly" filling the gap. Close.

The distinction: a slow, orderly gap fill with low VIX = close (you are in the danger zone and the crash is not happening). A violent spike lower with VIX exploding = hold (the crash may be underway and you need to survive the danger zone to reach Zone 3).

### Rule 3: Let the Crash Run

**If SPY breaks below 655 with VIX above 30:**

The position is approaching breakeven and accelerating toward profit. DO NOT close. Every additional point lower adds $200.

- At SPY 645: position is +$1,200. Set a mental stop at +$600 (give back half).
- At SPY 640: position is +$2,200. Move stop to +$1,100.
- At SPY 630: position is +$4,200. Close at least half (1 backspread) to lock in $2,100. Let the other backspread ride.
- At SPY 620: close remaining backspread for ~$3,100. Total realized: ~$5,200.

### Rule 4: VIX Spike Early = Opportunity

If within the first 2 weeks, VIX spikes above 35 even without a large SPY move (e.g., geopolitical shock causes a vol event with SPY only at 672-668):

- The long puts will have gained significant vega value.
- The position may be near breakeven or slightly positive even though SPY is in the "danger zone" by strike terms.
- **Evaluate closing.** If you can exit for a small gain or breakeven during a vol spike, consider taking it. You caught the vol move without needing the full crash.

### Rule 5: No Rolling, No Adjusting, No Adding

This is a defined-risk position with a specific thesis. If the thesis is wrong, the $200 is gone. Do not:
- Roll the short puts down (this widens the danger zone)
- Add more long puts (increases debit beyond 2% budget)
- Convert to a different structure (destroys the convexity profile)
- Double down after a partial loss (revenge trading)

The position is binary: either the crash happens and you make thousands, or it does not and you lose $200. Managing the danger zone (Rule 2) is the only active decision.

---

## Why This Structure (Not Alternatives)

### Why Not Position 15 (665/650 backspread)?

Position 15 from the original series used 665/650 strikes with breakeven at $634.35. That requires SPY to fall 6.4% just to break even -- too far. By moving the strikes closer to ATM (672/662), the breakeven moves to $651, requiring only a 4% drop. The tradeoff: the danger zone is closer to current price (662-672 vs 650-665), meaning a gap fill puts you in more pain. But for a crash-specific trade, you want the breakeven as high as possible.

### Why Not Straight Long Puts?

Buying SPY May 16 650P outright costs ~$2.00-2.50 per contract. Two contracts = $400-500. Over budget. One contract = $200-250, and at SPY 650 at expiry it is worth $0 (strike = price, no intrinsic value). You need SPY below 648 just to break even. The backspread gets you 4 contracts of downside exposure for the same $200 by selling 2 higher puts to fund them.

### Why Not a Butterfly?

A 672/662/652 put butterfly costs ~$3.50 and max-profits at exactly 662. This trade is not about pinning a level -- it is about unlimited downside leverage. The butterfly caps out; the backspread accelerates.

### Why Not VIX Calls?

VIX calls are expensive, have vicious time decay, and their payout depends on the VIX futures term structure, not directly on SPY price. A VIX spike from 20 to 35 might only double a VIX call, while the backspread at SPY 640 returns 11:1. VIX calls are a volatility bet; this is a directional crash bet with volatility as a tailwind.

### Why 672/662 Specifically?

- **672 short strike:** SPY closed at ~678. The 672P is 6 points OTM (~0.9%). This is close enough to ATM that it collects meaningful premium ($6.00) to subsidize the longs, but far enough OTM that a normal 1-2 day pullback does not immediately put the short in-the-money.
- **662 long strike:** 16 points OTM (~2.4%). This is where the gap fill zone begins (SPX ~6620). If SPY drops to 662, the gap is partially filled and the question becomes: does it stop here (danger zone) or continue to crash (payday)?
- **10-point width:** Narrow enough to keep the debit small ($1.00/backspread), wide enough for the danger zone to be traversable in a genuine crash move. A 5-point width would have a tighter breakeven but produces less profit per point below breakeven.

---

## Pre-Expiry P&L (Crash in Progress, Not at Expiry)

The table above shows at-expiry values. In a real crash scenario, you would likely close BEFORE expiry while VIX is elevated. Here is what the position looks like mid-trade with a VIX spike:

**Scenario: April 14 (32 DTE remaining), SPY at 655, VIX at 35:**

| Leg | Intrinsic | Time Value (elevated IV) | Estimated Price | Position Value |
|---|---|---|---|---|
| Short 672P (x2) | $17 each | +$5.50 | ~$22.50 | -$4,500 |
| Long 662P (x4) | $7 each | +$6.00 | ~$13.00 | +$5,200 |
| **Net** | | | | **+$700** |
| Less debit paid | | | | -$200 |
| **Position P&L** | | | | **+$500** |

With VIX at 35, the longs gain MORE time value than the shorts because you own 4 vs selling 2, and far-OTM puts have higher vega sensitivity to vol spikes. Even at SPY 655 (which is -$800 at expiry), the mid-trade P&L with elevated vol shows +$500.

**Scenario: April 14, SPY at 645, VIX at 40:**

| Leg | Est. Price | Position Value |
|---|---|---|
| Short 672P (x2) | ~$30.00 | -$6,000 |
| Long 662P (x4) | ~$20.50 | +$8,200 |
| **Net less debit** | | **+$2,000** |

At SPY 645 mid-trade with VIX at 40, the position shows +$2,000 -- well above the +$1,200 at-expiry value. **The vol spike is the accelerant.** This is why you hold through the crash and close mid-move, not at expiry.

---

## Position Sizing Rationale

| Factor | Value |
|---|---|
| Account size | $10,000 |
| Capital at risk (debit paid) | $200 (2.0% of account) |
| Theoretical max loss (danger zone, unmanaged) | $2,200 (22% of account) |
| Practical max loss (with Rule 2 management) | ~$1,200 (12% of account) |
| Expected loss (prob-weighted, ~60% chance all expire worthless) | ~$200 |
| Gain at SPY 640 (at expiry) | +$2,200 (22% of account) |
| Gain at SPY 620 (Wave-3) | +$6,200 (62% of account) |
| Gain at SPY 600 (full Wave-3, SPX ~6000) | +$10,200 (102% of account) |
| Risk/reward: debit vs SPY 640 | 1:11 |
| Risk/reward: debit vs SPY 620 | 1:31 |
| Risk/reward: debit vs SPY 600 | 1:51 |

---

## Entry Checklist

1. **Wait until 10:00 AM ET.** Let the opening auction settle. A gap-up on continued ceasefire optimism is GOOD for this entry -- OTM puts cheapen.
2. **Check VIX:**
   - VIX below 18: Puts are very cheap. Enter at $0.80-0.90 per backspread. Excellent entry.
   - VIX 18-22: Normal. Target $1.00 per backspread.
   - VIX above 25: Puts are expensive. Reduce to 1 backspread ($100-120 risk) to stay under $200.
3. **Leg in if needed:** Buy the 4 long 662Ps first, then sell the 2 short 672Ps. Never be naked short the 672Ps without the longs in place. The longs are the core position.
4. **Use a limit order at $1.00 per backspread.** If the order does not fill in 15 minutes, walk to $1.10. If still no fill, wait until after lunch (1:00 PM) when market maker spreads tighten.
5. **If SPY opens below 675 Monday morning,** enter immediately -- the risk catalyst may already be firing and delay costs you delta.

---

## Alert and Calendar Schedule

- [ ] **SPY $672** -- short strike breached, danger zone begins. Monitor daily.
- [ ] **SPY $665** -- deep in danger zone. Evaluate Rule 2 (close if orderly decline, hold if VIX >30).
- [ ] **SPY $662** -- max pain level. If here with low VIX, close immediately per Rule 2.
- [ ] **SPY $655** -- approaching breakeven. If VIX >30, hold for crash continuation.
- [ ] **SPY $651** -- breakeven. Everything below here is profit.
- [ ] **SPY $640** -- +$2,200. Consider closing half (1 backspread).
- [ ] **SPY $620** -- +$6,200. Close remaining position. The trade worked.
- [ ] **VIX $30** -- evaluate whether the move is orderly or panicked. Panicked = hold. Orderly = close if in danger zone.
- [ ] **VIX $35** -- consider closing for vol gains even if SPY has not moved far.
- [ ] **May 8 (Fri, 8 DTE)** -- if SPY above 670, close for residual value or let expire.
- [ ] **May 14 (Thu, 2 DTE)** -- close any remaining position. Do not hold through final-day gamma.

---

## Honest Assessment

**What this trade IS:** A $200 lottery ticket on a tail-risk crash. If the ceasefire collapses, Hormuz closes, oil spikes, and the market enters a genuine panic selloff, this position pays $2,000+ at SPY 640 and scales to $10,000+ at SPY 600. The cost of being wrong is $200 -- two dinners out.

**What this trade IS NOT:** A gap-fill trade. If SPY drifts to 665 and stabilizes, this position loses MORE than the $200 debit (up to $1,200 with management, $2,200 without). The gap fill is the enemy. You must manage the danger zone or accept the larger loss.

**The core bet:** You are betting on a discontinuous move -- a gap, a crash, a panic -- that vaults SPY through the danger zone (672-651) and into the profit zone (below 651). A slow grind lower to 665 kills this trade. A fast crash to 640 makes it. That is the tradeoff for 11:1 to 51:1 upside leverage on a $200 position.

**Probability-weighted expectation:** ~60% chance all expire worthless (-$200). ~20% chance you close in the danger zone (-$800 to -$1,200 managed). ~15% chance of modest crash to 645-655 (+$0 to +$1,200). ~5% chance of full crash to 620-600 (+$6,200 to +$10,200). Expected value is roughly -$30 to +$50 depending on management discipline. This is a slightly negative to breakeven EV trade that you take for the convexity -- the same reason you buy homeowner's insurance.

---

## Position Summary

| Field | Value |
|---|---|
| Structure | Sell 2x SPY May 16 672P / Buy 4x SPY May 16 662P (1x2 backspread x2) |
| Underlying | SPY (~678, SPX ~6783) |
| Expiry | May 16, 2026 (39 DTE) |
| Net debit | ~$1.00/backspread (~$200 total for 2x) |
| Practical max loss (managed) | $200 (if flat) to $1,200 (if danger zone managed) |
| Theoretical max loss (unmanaged at 662) | $2,200 |
| Breakeven (at expiry) | SPY ~$651 |
| Profit at SPY 650 | +$200 |
| Profit at SPY 640 | +$2,200 |
| Profit at SPY 630 | +$4,200 |
| Profit at SPY 620 (Wave-3) | +$6,200 |
| Profit at SPY 600 (SPX ~6000) | +$10,200 |
| R:R (debit vs SPY 640) | 1:11 |
| R:R (debit vs SPY 600) | 1:51 |
| Thesis | Ceasefire collapse + Hormuz closure + Wave-3 = SPY crash |
| Greek profile | Long vega (4 longs vs 2 shorts), long gamma in the tail, minimal theta at entry |
| Danger zone | SPY 652-672 -- must manage per Rule 2 or accept larger loss |
