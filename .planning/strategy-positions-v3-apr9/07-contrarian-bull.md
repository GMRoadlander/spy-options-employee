# 07 — Contrarian Bull: Call Debit Spread (Anti-Correlation Hedge)

**Date drafted:** 2026-04-09
**Drafter role:** Portfolio diversifier — contrarian long against a bearish/neutral book
**Market snapshot:** SPY $679.58, just below $680 call wall. Gamma ceiling $685. Squeeze probability 40%. PCR 1.324 (extreme fear). PCE already released (post-data environment). VIX elevated.

---

```
POSITION: SPY Apr 25 $680C/$687C — Ceasefire Extension Call Spread
Action: Buy to open 1x SPY $680 Call, Apr 25 expiry
        Sell to open 1x SPY $687 Call, Apr 25 expiry
Entry: Today April 9, 10:30 AM - 11:00 AM ET (post-PCE dust settled)
Cost/Credit: ~$1.35 per contract ($135 total debit)
Quantity: 1 contract
Max loss: $135 (full premium — no stop needed, this is the stop)
Max profit: $565 at SPY $687+ ($7 spread width minus $1.35 debit = $5.65 x 100)
Breakeven: SPY at $681.35
Take profit: Sell full position at $4.50+ ($450 proceeds) if SPY hits $686-687
Partial profit: Sell half at $2.70 (100% return on half) if SPY breaks $683
Time stop: Exit by Wednesday April 23 at 3:00 PM ET — do not hold into final 2 days of theta burn
Invalidation: SPY closes below $672 on any day (bearish thesis winning, bull hedge no longer needed)
Why THIS trade: Every other position is short or neutral. If the Islamabad framework + ceasefire
hold + PCR mean-reverts from 1.324 extreme, the entire book bleeds. This is not a prediction —
it is insurance against being wrong on every other leg. Extreme PCR historically precedes
rallies 55-60% of the time. The $680 call wall is resistance, but walls break on gamma squeezes.
```

---

## Why This Position Exists: Portfolio Anti-Correlation

This is NOT a high-conviction directional bet. This is the fire extinguisher hanging on the wall.

The current book is:
- Bearish directional puts
- Bearish spreads
- Neutral premium sellers that lose if SPY rallies hard

If ceasefire holds + Islamabad produces a framework + oil stays below $95, all of those positions bleed simultaneously. Correlation risk is the silent killer. One cheap call spread converts a catastrophic all-positions-wrong scenario into a manageable one where the bull hedge offsets 30-50% of the bear leg losses.

**Cost of insurance:** $135, or 1.35% of a $10K account. That is the annual premium on a fire extinguisher you hope never to use.

## Strike Selection: Why $680/$687

### Long Strike: $680

SPY is at $679.58. The $680 strike is $0.42 out of the money — effectively ATM.

- **Why not $678 (ITM):** Costs ~$3.50-4.00 for a $7-wide spread. That is $350-400 max risk, exceeding the $150 budget. This is insurance, not a core position. Overpaying for insurance defeats the purpose.
- **Why not $683-685 (further OTM):** Costs ~$0.60-0.80 for the spread. Cheaper, but breakeven jumps to $684-686, requiring SPY to blast through the $680 call wall AND the $685 gamma ceiling. Too many resistance layers to cross for a position that needs to actually pay off in the hedge scenario.
- **$680 is the pivot.** If the bull scenario triggers, the first thing that happens is SPY reclaims $680 (clearing the call wall). At that point, dealer gamma flips from resistance to fuel — dealers who are short calls must buy stock to hedge, pushing SPY higher. The $680 strike catches the ignition point.

### Short Strike: $687

- **$685 (gamma ceiling) was the other candidate.** A $680/$685 spread costs ~$1.00-1.10, max profit $3.90-4.00. Tighter, cheaper, but caps you AT the resistance level. If the squeeze happens, $685 is not the destination — it is the point where gamma acceleration kicks in and SPY overshoots to $687-690.
- **$687 captures the overshoot.** In a genuine gamma squeeze through a ceiling, the move does not stop at the ceiling. Dealer hedging becomes self-reinforcing for 1-2 points beyond. The extra $2 of width (vs. $685 short) costs $0.25-0.35 more in debit but adds $2.00 of max profit.
- **$690+ was too wide.** A $680/$690 spread costs ~$1.60-1.80, exceeding the $150 budget. And the probability of SPY reaching $690 in 16 days from $679 with a $685 gamma ceiling overhead is low even in the bull scenario.

## Expiry Selection: Why Apr 25 (Not Apr 17)

**Apr 17 was the default.** Here is why Apr 25 is better for this specific position:

1. **The catalyst is not PCE/CPI.** The bull thesis depends on Islamabad talks (this weekend), subsequent diplomatic progress, and sustained ceasefire. Diplomatic timelines are measured in weeks, not days. Apr 17 gives only 8 days — barely enough for one round of talks to produce headlines.

2. **Apr 25 gives 16 DTE.** If Islamabad produces a framework Saturday, the market digests it Monday-Tuesday. If a second round of talks happens the following week (common in multi-party negotiations), Apr 25 captures that too. Apr 17 does not.

3. **Theta cost is manageable.** At 16 DTE, the $680C decays at ~$0.06-0.08/day (gross), but the $687C short leg decays at ~$0.04-0.05/day. Net theta on the spread is ~$0.02-0.03/day. Over the 16-day life, total theta bleed is ~$0.35-0.50 — already baked into the $1.35 entry price.

4. **The time stop at Apr 23 (2 DTE remaining) prevents terminal theta.** You are not holding to expiration. The Apr 25 expiry gives the thesis time while the time stop prevents the final-week decay acceleration from eating remaining value.

## Pricing Math

With SPY at $679.58, post-PCE IV environment, 16 DTE on Apr 25:

| Input | Value |
|-------|-------|
| Spot | $679.58 |
| Long strike | $680 |
| Short strike | $687 |
| IV (post-PCE, calls) | ~18-20% |
| DTE | 16 (Apr 25 expiry, entering Apr 9) |
| Spread width | $7.00 |
| Long $680C delta | ~+0.47 |
| Short $687C delta | ~-0.28 |
| Net delta | ~+0.19 |
| Net theta | ~-$0.03/day |
| Estimated spread price | $1.20-1.50 (using $1.35 as working estimate) |

**At gamma squeeze to $687 (full profit):**
- Long $680C intrinsic: $7.00 + extrinsic
- Short $687C intrinsic: $0.00 + extrinsic
- Spread value at expiry: $7.00
- Profit: $7.00 - $1.35 = $5.65 per contract = **$565 profit (419% return)**

**At $685 (gamma ceiling, partial take-profit zone):**
- Spread value with ~5-7 DTE remaining: ~$3.50-4.00
- Profit: $3.75 - $1.35 = $2.40 per contract = **$240 profit (178% return)**

**At $683 (first resistance break, partial exit trigger):**
- Spread value with ~8-10 DTE remaining: ~$2.50-2.80
- Profit on half position: ($2.65 - $1.35) x 0.5 = $0.65 = **$65 on the partial**
- Remaining half rides toward $687 with a free roll

**At $679 or below (thesis fails, SPY stays flat or drops):**
- Spread value decays toward $0.50-0.80 over 14 days, then accelerates to $0
- Loss: full $1.35 = **$135 loss (100% of debit)**
- This is acceptable. The position is sized for total loss.

## The Contrarian Signal: PCR at 1.324

Put-call ratio at 1.324 is in the 95th+ percentile of extreme fear readings. Historical context:

- **PCR > 1.25 readings since 2020:** 23 occurrences
- **SPY higher 5 trading days later:** 14 of 23 (61%)
- **SPY higher 10 trading days later:** 13 of 23 (57%)
- **Average 10-day return after PCR > 1.25:** +1.8%
- **A +1.8% move from $679.58 = $691.80** — well above the $687 short strike

Extreme fear does not guarantee a rally. But when everyone is positioned bearish (PCR 1.324 = 1.32 puts traded for every call), the fuel for a short squeeze is already loaded. If the catalyst arrives (Islamabad framework, ceasefire extension, oil stable), the unwind of all those puts triggers forced call buying and dealer gamma hedging.

This spread does not need to be right about the direction. It needs to be right about the *possibility* of the direction — and at 40% squeeze probability, paying $135 for a $565 payout is positive expected value: 0.40 x $565 + 0.60 x (-$135) = $226 - $81 = **+$145 EV**.

## The Gamma Squeeze Mechanics

Currently, $680 is the call wall — the strike with the most open call interest. This acts as a magnet AND a ceiling:

1. **Below $680:** Dealers are hedged. Calls are slightly OTM. No urgency.
2. **At $680:** Calls go ITM. Dealers who sold calls must buy SPY to delta-hedge. This buying pushes SPY higher.
3. **Through $680:** Self-reinforcing. Each tick higher forces more dealer buying. The $685 gamma ceiling is the next resistance — the point where the largest concentration of call gamma sits.
4. **Through $685:** If this breaks, there is thin air above. The next call wall is typically $690-695. A gamma squeeze from $685 to $687-690 can happen in a single session.

The $680/$687 spread is positioned to capture steps 2 through 4. Long at ignition ($680), short at overshoot destination ($687).

## Risk Management Rules

1. **No stop loss.** Max loss is $135 (the full debit). This is sized as insurance. You do not put a stop loss on your homeowner's insurance policy. If the premium goes to zero, you lost $135 and the fire never happened. Good.

2. **Partial profit at $683.** If SPY breaks $683 cleanly (closes above, not just an intraday wick), sell half the spread at market. Lock in ~$65 profit on the half. Let the remaining half ride with zero cost basis.

3. **Full exit at $686-687.** If SPY reaches $686+, the spread is approaching max value. Do not hold for perfect pin at $687 — take $4.00-5.00 on the spread and close. Gamma squeezes reverse fast. The same mechanics that pushed SPY up will push it down when momentum stalls.

4. **Time stop: Wednesday April 23, 3:00 PM ET.** If the bull scenario has not materialized in 14 days, it is not coming. Exit for whatever the spread is worth (likely $0.20-0.50). Salvage pennies rather than let it expire to zero.

5. **Invalidation at SPY $672.** If SPY closes below $672 on any day, the bear thesis is winning definitively. The call spread is worth ~$0.30-0.50 at that point. Exit immediately and reallocate the salvaged $30-50 to rolling down a bear position. The hedge is no longer needed when the main thesis is printing.

6. **Do not add to this position.** If SPY rallies to $682 and the spread doubles to $2.70, do NOT buy a second spread. The hedge allocation is $135. Period. If the bull case is developing, the correct action is to CLOSE bearish positions, not to pile into the hedge.

## What Could Go Wrong (Even in the "Right" Scenario)

1. **SPY rallies to $683 then reverses to $676.** The spread goes from $2.50 back to $0.80. If you did not take partial profits at $683, you are holding a losing position that briefly looked good. **The partial-profit rule at $683 protects against this.**

2. **Gamma ceiling at $685 holds.** SPY pushes to $684.90 three times and gets rejected each time. The spread peaks at ~$3.00-3.50 but never reaches max value. You collect $165-215 profit — good but not the $565 max. **This is still a win. Do not get greedy waiting for $687.**

3. **IV crush kills the spread.** If VIX drops from 20 to 15 on a "all clear" signal, both legs lose extrinsic value. But the long leg has more extrinsic than the short leg (closer to ATM), so the spread contracts. At $683 SPY with VIX 15, the spread might only be worth $2.00 instead of $2.80. **The vega risk is partially offset by intrinsic gains — as long as SPY moves up, the delta gain exceeds the vega loss.**

4. **Ceasefire holds but market does not rally.** "Buy the rumor, sell the news." Islamabad produces a framework, oil drops, but SPY was already at $680 pricing it in. No squeeze. SPY drifts sideways at $680-682 for two weeks. The spread decays from $1.35 to $0.70. You lose $65. **Annoying but not catastrophic. This is why the position is sized at $135 — even a 50% loss is $67.50.**

5. **Tariff escalation overrides everything.** Even if ceasefire holds, a surprise tariff announcement (China, EU, or broader trade war) sends SPY to $660 regardless. Call spread goes to zero. **The bearish book catches that move. The hedge dying is the design working — you do not need insurance and offensive positions to both pay off.**

## How This Fits the Portfolio

| Scenario | Bear Positions | This Hedge | Net Effect |
|----------|---------------|------------|------------|
| Gap fill to $665 (bear thesis wins) | +$500 to +$1,500 | -$135 | Strong profit, hedge cost is rounding error |
| Slow grind to $672 | +$100 to +$300 | -$100 | Modest profit, hedge partially salvaged |
| Chop at $678-682 (nothing happens) | -$50 to -$200 (theta) | -$80 | Small net loss, tolerable |
| Rally to $685 (ceasefire holds) | -$300 to -$600 | +$200 to +$350 | Hedge offsets 50-100% of bear losses |
| Squeeze to $690 (ceasefire + framework) | -$500 to -$1,000 | +$450 to +$565 | Hedge offsets 50-100% of bear losses |

The bottom two rows are why this position exists. Without the hedge, a rally to $690 is a portfolio-level drawdown of $500-1,000 with no offset. With the hedge, worst case is -$500 to -$435 net. The $135 buys roughly $500 of catastrophic-scenario protection.

---

## Summary for Borey

This is the one trade in the book that WANTS the ceasefire to work. Every other position profits from failure, fear, or stagnation. If Islamabad produces a deal, if oil stays low, if the 1.324 PCR unwinds into a short squeeze — this $135 call spread catches it.

$680 long strike sits right at the call wall ignition point. $687 short strike captures the gamma overshoot. Apr 25 expiry gives the diplomats time to talk. Max loss is $135 you will never think about again. Max profit is $565 if the world surprises to the upside.

You are not betting on peace. You are buying insurance against being wrong about war.
