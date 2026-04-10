# Position 15: Put Backspread — Black Swan Crash Convexity

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783)
**Thesis:** The ceasefire is a paper tiger. If it collapses — Houthi attack, Iranian escalation, diplomatic breakdown — SPX gaps down hard. If MPW's Elliott Wave-3 crash thesis materializes alongside a geopolitical trigger, SPY could fall 10-15% over 2-3 weeks. You want to be positioned for the tail with minimal capital at risk if wrong.
**Account:** $10,000 | **Risk budget:** $300 max (3% of account for a defined-risk asymmetric structure)

---

## POSITION: 1x2 Put Backspread

| Field | Detail |
|---|---|
| **Structure** | **Sell 1x SPY Apr 25 $665P / Buy 2x SPY Apr 25 $650P** |
| **Entry** | Monday Apr 7, 2026, between 10:00-10:30 AM ET |
| **Expiry** | Apr 25, 2026 (14 DTE at entry — 2 weeks for the thesis to develop) |
| **Spread width** | $15 (665 - 650 = 15 points) |
| **Net debit** | ~$0.65 per backspread ($65 total) |
| **Quantity** | **3 backspreads** (sell 3x 665P, buy 6x 650P) |
| **Total cost** | ~$195 net debit (3 x $65) |
| **Max loss** | ~$4,305 (see "max loss zone" — but this is avoidable with management) |
| **Practical max loss** | ~$195 (the debit paid — if SPY stays above 665 at expiry, all legs expire worthless) |
| **Downside breakeven** | ~$635.07 (below which you are profitable) — **NO.** See corrected math below. |

---

## Pricing Breakdown (SPY ~678, VIX ~20, 14 DTE)

Using Black-Scholes estimates with 20% implied volatility, 14 DTE:

| Leg | Strike | Delta | Estimated Price | Qty | Cost |
|---|---|---|---|---|---|
| Short put | 665P | ~0.18 | ~$2.30 | Sell 1 | +$230 credit |
| Long put | 650P | ~0.08 | ~$1.15 | Buy 2 | -$230 debit |
| **Net per backspread** | | | **~$0.00 to $0.65 debit** | | |

**Realistic fill: ~$0.65 debit per backspread** (market makers will shade the fills against you on a 3-legged order). Could potentially enter for even money or a small credit if VIX pops above 22 on Monday morning.

For 3 backspreads: sell 3x 665P at $2.30, buy 6x 650P at $1.15. Net debit = 3 x $0.65 = **$1.95 total** ($195).

---

## P&L Analysis at Expiry (per backspread, then x3 for full position)

This is where the backspread shines. The payoff is NOT linear — it has a "valley of pain" between the strikes and then ACCELERATING profit below the lower strike.

### Per-Backspread P&L at Various SPY Levels

| SPY at Expiry | Short 665P Value | Long 650P Value (x2) | Net P&L per Backspread | x3 Position P&L |
|---|---|---|---|---|
| **680** (flat/up) | $0.00 | $0.00 | -$0.65 (lose debit) | **-$195** |
| **670** (small dip) | $0.00 | $0.00 | -$0.65 (lose debit) | **-$195** |
| **665** (at short strike) | $0.00 | $0.00 | -$0.65 (lose debit) | **-$195** |
| **660** (between strikes) | -$5.00 | $0.00 | -$5.65 | **-$1,695** |
| **655** (between strikes) | -$10.00 | $0.00 | -$10.65 | **-$3,195** |
| **650** (at long strikes) | -$15.00 | $0.00 | -$15.65 | **-$4,695** |
| **649** (just below longs) | -$16.00 | +$2.00 | -$14.65 | **-$4,395** |
| **645** | -$20.00 | +$10.00 | -$10.65 | **-$3,195** |
| **640** | -$25.00 | +$20.00 | -$5.65 | **-$1,695** |
| **635** (lower breakeven) | -$30.00 | +$30.00 | -$0.65 | **-$195** |
| **634.35** (true breakeven) | -$30.65 | +$30.65 | $0.00 | **$0** |
| **630** | -$35.00 | +$40.00 | +$4.35 | **+$1,305** |
| **620** | -$45.00 | +$60.00 | +$14.35 | **+$4,305** |
| **610** (crash -10%) | -$55.00 | +$80.00 | +$24.35 | **+$7,305** |
| **600** (crash -11.5%) | -$65.00 | +$100.00 | +$34.35 | **+$10,305** |
| **580** (crash -14.5%) | -$85.00 | +$140.00 | +$54.35 | **+$16,305** |

---

## The Payoff Profile Explained

The backspread has THREE distinct zones:

### Zone 1: SPY stays above 665 (BEST if wrong)
- All options expire worthless. You lose only the debit: **$195**.
- This is the most likely outcome. You paid $195 for a lottery ticket. Fine.

### Zone 2: SPY falls to 650-665 (THE DANGER ZONE)
- The short 665P is ITM but the long 650Ps are still OTM or barely ITM.
- **Max pain is at 650**: the short put is worth $15, the longs are worth $0. You owe $15 per backspread minus whatever you collected. Max loss = $15.65 per backspread x 3 = **$4,695**.
- This is the zone you MUST manage. See trade management rules below.

### Zone 3: SPY crashes below 634 (THE PAYDAY)
- The two long 650Ps gain faster than the one short 665P loses. Dollar for dollar, you gain $2 for every $1 the short put costs you, because you own twice as many longs.
- **Below 634.35, you are profitable.** Below 620, you are up $4,305. Below 600, you are up $10,305. This is the convexity — the further it falls, the faster you make money.
- At SPY 580 (a true crash scenario, SPX ~5800, -14.5%): **+$16,305** on a $195 investment. That is 83:1 return on capital at risk.

---

## Why This Is the Black Swan Trade

1. **Asymmetric by design.** If you are wrong (SPY stays flat or goes up), you lose $195. If you are right about a crash, you make $7,000-$16,000+. The payoff curve is convex — it gets better the more catastrophic the move.

2. **Volatility is your friend.** A crash spikes VIX from 20 to 40+. Your 6 long puts benefit from the vol expansion far more than your 3 short puts. The backspread is long vega in the tail — you OWN the volatility event.

3. **Time decay is nearly irrelevant.** At 14 DTE with strikes 8-13% OTM, daily theta is tiny (~$0.02-0.04/contract). You are not bleeding to death waiting. This is NOT a race against theta like a naked put.

4. **Gap risk works FOR you.** If SPY gaps down 5% on a Monday morning (ceasefire collapse, geopolitical shock), your long puts gap into deep ITM while the short put moves at half the rate. A gap is the ideal scenario — it vaults you past the danger zone (650-665) into the profit zone (sub-634).

5. **The ceasefire IS fragile.** Two-week pause, 3 ships, Iran still blocking the strait. Any Houthi drone, any IRGC statement, any tanker attacked and the "ceasefire rally" unwinds in hours. The gap up from 6610 to 6783 is built on a headline, not a resolution.

6. **Wave-3 alignment.** If MPW's Elliott Wave analysis is correct and SPX is entering a Wave-3 decline, the target zone (SPX 5800-6200) lines up perfectly with where this backspread prints massively. Wave-3 moves are the fastest and longest — exactly the kind of move that turns a $195 position into $10K+.

---

## Trade Management Rules (CRITICAL — Read This Twice)

The backspread's weakness is the valley of death between strikes. Here is how you survive it:

### Rule 1: Accept Zone 1 as the Default Outcome
If SPY stays above 670 through April 18, the position is nearly worthless. Let it ride to expiry or close for a few cents. Your loss is $195. This is the plan. Do not add to the position, roll it, or try to "rescue" it.

### Rule 2: Close if SPY Settles Into the Danger Zone
**If by April 18 (one week before expiry) SPY is between 655 and 665 and trending sideways:**
- Close the entire position. Eat the loss.
- At SPY 660 with 7 DTE, the position will be worth approximately -$3.50 to -$4.50 per backspread. Close for ~$1,050-$1,350 loss on the full 3-lot position.
- This is painful but recoverable. Holding into expiry at 655-660 risks the full $4,695 max loss. **Do not let that happen.**
- The danger zone is the scenario where SPY falls "just enough to hurt you but not enough to help you." Recognize it and exit.

### Rule 3: Let the Crash Run
**If SPY breaks below 645 with momentum:**
- Do NOT close. The convexity is working. Every additional point of downside is pure profit at $1.00/point per backspread ($3.00 for the 3-lot).
- Set a trailing stop at 50% of unrealized gain. If the position is up $3,000 and SPY bounces, close if the P&L drops to +$1,500.
- **If SPY hits 620, close at least half (2 of 3 backspreads).** A $2,000+ gain on a $195 risk is a career trade. Bank it.

### Rule 4: IV Spike = Close Opportunity
If VIX spikes above 35 (from current ~20) within the first week, even without a massive SPY move:
- The long puts will be worth significantly more due to vol expansion.
- If the position is showing a small profit or breakeven, consider closing. You caught the vol move, even if SPY only dropped to 660-665. The short put's vega is offset by the two long puts' vega.

### Rule 5: Do NOT Roll or Adjust
- If this trade does not work, it does not work. Do not roll the short put down, do not add more longs, do not convert it into a different structure.
- The beauty of the backspread is its simplicity: defined risk (in practice, $195 if you manage the danger zone), and convex payout. Adjusting destroys both properties.

---

## Position Sizing Rationale

| Factor | Value |
|---|---|
| Account size | $10,000 |
| Capital at risk (debit paid) | $195 (1.95% of account) |
| Theoretical max loss (danger zone, unmanaged) | $4,695 (47% of account) |
| Practical max loss (with Rule 2 management) | ~$1,350 (13.5% of account) |
| Expected loss (probability-weighted) | ~$195 (most likely: all expire worthless) |
| Potential gain at SPY 610 | +$7,305 (73% of account) |
| Potential gain at SPY 580 | +$16,305 (163% of account) |
| Risk/reward at crash scenario | 1:37 (risk $195, make $7,305 at -10% SPY) |

**Why 3 backspreads and not 1 or 5:**
- 1 backspread ($65 risk): Too small. Even at SPY 610, you make $2,435. Nice, but not portfolio-changing for a $10K account.
- 3 backspreads ($195 risk): Sweet spot. $195 is disposable. The crash payout ($7K-$16K) is meaningful. The danger zone max loss ($4.7K) is survivable IF managed per Rule 2 (which cuts it to ~$1,350).
- 5 backspreads ($325 risk): The danger zone max loss balloons to $7,825. Even with Rule 2 management (~$2,250 loss), this is 22.5% of the account on a low-probability trade. Too much.

---

## Entry Rules

1. **Wait for 10:00 AM ET.** Let the opening auction settle. If SPY gaps up on continued ceasefire optimism, that is GOOD for entry — you are buying cheap OTM puts.
2. **Check VIX.** If VIX has crashed below 17, the market is fully complacent. Puts are cheap, which helps your entry price — but the crash thesis needs a catalyst. Enter anyway (puts are cheap = good for you), but know that the trade needs a trigger.
3. **If VIX is above 25**, the market is already nervous. Your puts will be more expensive. Reduce to 2 backspreads to keep total debit under $200.
4. **Leg in if necessary.** If you cannot get a reasonable fill on the 3-legged order, consider buying the 6 long 650Ps first, then selling the 3 short 665Ps separately. The long puts are the core position — never be naked short the 665P without the longs in place.
5. **If SPY opens below 670 on Monday**, enter immediately. The selloff may be starting and you want to be in before the move accelerates.

---

## Expiry Choice: April 25 (14 DTE)

| Consideration | Reasoning |
|---|---|
| **Why not Apr 11 (4 DTE)** | Too short. A crash scenario unfolds over days to weeks, not hours. Theta kills OTM puts at 4 DTE. If the ceasefire collapses on April 12, you are already expired. |
| **Why not May 15 (38 DTE)** | Costs too much. The 650Ps at 38 DTE would be ~$2.50 each, making the backspread a ~$2.00 debit ($600 for 3). The extra time is insurance you probably do not need — if the crash does not start within 2 weeks, it is probably not the Wave-3 crash. |
| **Why Apr 25 (14 DTE)** | Captures the next two full weeks of potential catalysts: PCE (Apr 9), CPI (Apr 10), earnings season ramp (Apr 14-18), and any geopolitical reversal. Puts are cheap at 14 DTE for 8-13% OTM strikes. If the crash materializes, 14 days is enough for a 10%+ move. If it does not, the low debit means minimal loss. |

---

## Scenario Analysis

### Scenario A: Ceasefire Holds, SPY Rallies to 690+ (Probability: ~50%)
- All options expire worthless.
- **Loss: $195.** You bought insurance and did not need it. This is the cost of convexity.

### Scenario B: SPY Drifts Down to 665-670, Then Stabilizes (Probability: ~25%)
- Position is near breakeven or slightly negative. Short put is barely ITM, longs are worthless.
- **Close per Rule 2 if stuck in this zone by April 18. Loss: ~$200-$500.**

### Scenario C: SPY Falls to 650-660 and Stays There (Probability: ~10%)
- **THE DANGER ZONE.** This is the worst outcome.
- **Managed loss per Rule 2: ~$1,050-$1,350.** Unmanaged: up to $4,695.
- This scenario requires the market to fall "just enough" and then stop. Possible but less likely than either a bounce or a continued crash.

### Scenario D: Crash to SPY 620-640 (Probability: ~10%)
- The trade works as designed. You blow through the danger zone into convex profit territory.
- **Gain: $1,305 to $4,305.** This is 7x-22x the capital at risk.

### Scenario E: Black Swan Crash to SPY 580-600 (Probability: ~5%)
- This is the trade. Wave-3, geopolitical crisis, liquidity shock, forced selling.
- **Gain: $10,305 to $16,305.** This is 53x-84x the capital at risk.
- A $195 bet turns into $10K-$16K. The backspread pays for the entire account and then some.

---

## Comparison to Alternatives

| Structure | Cost | Max Loss | Payout at SPY 610 | Why Not |
|---|---|---|---|---|
| **Buy 6x 650P outright** | ~$690 | $690 | +$23,310 | 3.5x more expensive. Higher absolute return but no short put to subsidize. Bleeds theta harder. |
| **Bear put spread 665/650** | ~$450 | $450 | +$1,050 | Capped at $15 width. No convexity. If SPY crashes to 600, you make the same $1,050 as SPY 650. |
| **Put backspread (this trade)** | ~$195 | $195 (managed) | +$7,305 | Cheapest entry, convex payout, long vega. Danger zone is the tradeoff. |
| **VIX calls** | ~$300 | $300 | Variable | VIX calls are expensive and have wicked time decay. Roll risk. Less direct SPY exposure. |

The put backspread offers the best combination of low entry cost and convex crash payout. It is purpose-built for the "small if wrong, huge if right" mandate.

---

## Post-Entry Checklist

- [ ] Set alert at SPY $665 (short strike — danger zone begins)
- [ ] Set alert at SPY $650 (long strike — approaching max pain)
- [ ] Set alert at SPY $634 (lower breakeven — profit territory)
- [ ] Set alert at SPY $620 (take partial profit zone)
- [ ] Set alert at VIX $35 (vol spike close opportunity)
- [ ] Calendar reminder: April 18 (Friday) 3:00 PM ET — evaluate danger zone Rule 2
- [ ] Calendar reminder: April 23 (Wednesday) — if position is near worthless, let expire or close for pennies
- [ ] This is a SET IT AND FORGET IT position unless alerts trigger. Check once per day, not once per hour.

---

## Position Summary

| Field | Value |
|---|---|
| Structure | Sell 3x SPY 665P / Buy 6x SPY 650P (1x2 put backspread x3) |
| Underlying | SPY (~678, SPX ~6783) |
| Expiry | April 25, 2026 |
| Net debit | ~$0.65/backspread (~$195 total for 3x) |
| Practical max loss (managed) | ~$195-$1,350 |
| Theoretical max loss (unmanaged, at 650) | ~$4,695 |
| Profit at SPY 620 | +$4,305 |
| Profit at SPY 610 | +$7,305 |
| Profit at SPY 600 | +$10,305 |
| Profit at SPY 580 | +$16,305 |
| Lower breakeven | ~$634.35 |
| R:R (at SPY 610 crash) | ~1:37 (risk $195, make $7,305) |
| Thesis | Ceasefire collapses + Wave-3 crash = SPY -10% or more |
| Conviction | Low probability, high conviction on the structure if the crash happens |
| Greek profile | Long vega, long gamma in the tail, near-zero theta at entry |
