# 01 — Aggressive Directional Put (Straight Long Put)

**Date drafted:** 2026-04-06
**Drafter role:** Aggressive directional trader, high conviction ceasefire collapse
**Market snapshot:** SPX ~6783 (SPY ~678). Gap up from ~6610 on US-Iran ceasefire Apr 7. VIX ~20. Oil crashed 16% to $94.

---

```
POSITION: SPY Apr 17 $670P — Ceasefire Collapse Put
Action: Buy to open 1x SPY $670 Put, Apr 17 expiry
Entry: Thursday April 9, 10:00-10:30 AM ET (immediately after PCE release settles)
Cost/Credit: $3.40 per contract ($340 total debit)
Quantity: 1 contract
Max loss: $200 (stop loss enforced — see below)
Max profit: $1,360 at SPY $656 (gap overshoot); $960 at SPY $660 (gap fill)
Breakeven: SPY at $666.60
Take profit: Sell full position at $10.00 ($1,000 proceeds) if SPY hits $661 (gap fill to SPX ~6610)
Stop loss: Sell if contract value drops to $1.40 ($200 loss = exactly 2% of $10,000)
Time stop: Exit by Wednesday April 15 at 3:00 PM ET regardless of P&L — do not hold into final 2 days of theta burn
Invalidation: SPY closes above $685 on any day (ceasefire rally extending, not fading). Also invalid if VIX drops below 15 (market fully pricing in peace, puts will bleed to zero).
Why THIS trade: The ceasefire is structurally unenforceable — 31 separate Iranian military branches, Supreme Leader in a coma, no single chain of command to stand down. The 2022 Ukraine false ceasefire rallies reversed within days. A straight put (no spread) captures the full downside if the collapse is violent rather than gradual, which is the more likely failure mode when 800+ ships are still trapped and any single rogue commander can restart hostilities.
```

---

## Strike Selection: Why $670 (Not ATM, Not Deep OTM)

**$670 is 1.2% out-of-the-money** with SPY at ~$678. This is the sweet spot:

- **Not ATM ($678-680):** ATM puts cost ~$6.50-7.00 at VIX 20 with 10 DTE. That prices in the full implied move. You are paying fair value and need a move just to break even. The 2% stop ($200 max loss) would force a stop at a 30% premium loss — normal intraday noise at that delta. You would get stopped out before the thesis plays out.

- **Not deep OTM ($660-665):** Deep OTM puts cost ~$1.50-2.00 but have 15-20 delta. You need a 2%+ move just to approach breakeven, and theta eats 8-10% of premium per day. These are lottery tickets, not trades.

- **$670 sits in the zone where:** Delta is ~35, meaning the put gains roughly $0.35 for every $1 SPY drops. A move from $678 to $661 (gap fill) is $17, producing ~$6.00-7.00 of intrinsic gain plus whatever extrinsic remains. The put moves meaningfully on the thesis playing out, and the stop loss at $1.40 gives enough room that normal daily chop (SPY moving +/- $7 at VIX 20) does not automatically trigger it.

## Expiry Selection: Why Apr 17 (Not Apr 11)

The v1 draft used Apr 11 (4 DTE). That was wrong. Here is why:

1. **PCE is Thursday Apr 9, CPI is Friday Apr 10.** With Apr 11 expiry, you are holding 1 DTE through CPI — pure gamma roulette. You lose control of the position.

2. **The adversarial swarm found the best entry is AFTER PCE.** If you enter Monday and hold through PCE with Apr 11 expiry, theta eats ~$0.80-1.00/day for 3 days before the catalyst ($2.40-3.00 in decay). That is 50-70% of a $4.80 ATM put — you are already losing before the event.

3. **Apr 17 gives 10 DTE at entry (Thursday Apr 9).** Theta decay is ~$0.25-0.30/day, not $0.80-1.00/day. You can survive a 2-3 day wait for the ceasefire to crack without bleeding out.

4. **Apr 17 survives both PCE AND CPI.** If PCE is a non-event (likely — February data, pre-Hormuz) and CPI on Friday is the real mover, you still have 7 DTE and reasonable theta.

5. **The gap fill does not need to happen Monday.** Borey says "next week" — that means any day Mon-Fri. Apr 17 gives the thesis the full week plus a buffer.

## Entry Timing: Why Thursday After PCE (Not Monday Open)

The adversarial swarm's strongest finding: **enter AFTER the IV crush, not before.**

- **Monday morning:** VIX is 20 but weekly options carry extra premium from the ceasefire gap. Market makers are wide, fills are bad, and you are buying inflated vol. If the market chops Mon-Wed, your $670P bleeds from ~$4.80 to ~$3.00 on theta alone. When PCE hits Thursday, IV crush compresses it further. You could be stopped out at $2.80 (below the $1.40 stop in v2) without the thesis being wrong.

- **Thursday 10:00 AM (post-PCE):** The February PCE is likely a non-event (pre-Hormuz data). After the number drops, IV on Apr 17 puts compresses as the known event passes. You buy the $670P at ~$3.40 instead of ~$4.80 — same strike, cheaper entry, because you let 3 days of theta and 1 catalyst of IV crush work FOR you instead of AGAINST you.

- **If ceasefire collapses Monday-Wednesday (before your entry):** You miss the trade. That is acceptable. The 2% risk cap exists precisely to prevent FOMO entries. If SPY is already at $670 by Thursday, this trade is over — find a different setup. Discipline is the point.

**Specific entry protocol:**
1. PCE drops at 8:30 AM ET Thursday.
2. Wait 90 minutes for the reaction to settle (no chasing).
3. At 10:00-10:30 AM, place a limit buy for SPY Apr 17 $670P.
4. If SPY is at $678-682 (ceasefire still holding), the put should price at ~$3.00-3.80. Target fill at $3.40, walk up to $3.80 max.
5. If SPY is already below $672 (gap fill already starting), **do not chase**. The easy money moved. Stand down.
6. If SPY is above $685, **do not enter**. Thesis is weakened. Stand down.

## Pricing Math

With SPY at $678, VIX at ~18-19 (post-PCE crush from 20), 8 DTE remaining on Apr 17:

| Input | Value |
|-------|-------|
| Spot | $678 |
| Strike | $670 |
| IV | ~19% (post-PCE crush) |
| DTE | 8 (Apr 17 expiry, entering Apr 9) |
| Delta | ~-0.33 |
| Theta | ~-$0.28/day |
| Vega | ~$0.12 per 1pt IV |
| Estimated price | $3.20-3.60 (using $3.40 as working estimate) |

**At gap fill (SPY $661):**
- Intrinsic: $670 - $661 = $9.00
- Extrinsic remaining (assume ~3 DTE left): ~$0.50-1.00
- Total value: ~$9.50-10.00
- Profit: $10.00 - $3.40 = $6.60 per contract = **$660 profit (194% return)**

**At gap overshoot (SPY $656, ceasefire collapse panic):**
- Intrinsic: $670 - $656 = $14.00
- Extrinsic remaining: ~$0.30-0.60
- Total value: ~$14.30-14.60
- Profit: $14.00 - $3.40 = $10.60+ per contract = **$1,060+ profit (312% return)**

**At stop loss ($1.40 contract value):**
- Loss: $3.40 - $1.40 = $2.00 per contract = **$200 loss (exactly 2% of $10K)**

## Risk Management Rules

1. **Hard stop at $1.40 contract value.** No exceptions. Set a GTC contingent sell order at entry. This is not a mental stop — it is a resting order in the broker.

2. **Do not average down.** If the put drops to $2.00, you do not buy a second contract. The stop exists for a reason. If the thesis needs "more time," that is what the Apr 17 expiry provides. Adding to a loser is how $200 losses become $600 losses.

3. **Exit early if VIX collapses.** If VIX drops below 16 at any point while you hold this position, exit immediately regardless of SPY price. A VIX below 16 means the market has fully digested the ceasefire as real. Your put will bleed on vega compression even if SPY drifts lower.

4. **Time stop: Wednesday Apr 15, 3:00 PM ET.** If the trade has not worked by then, you have 2 DTE left and theta is accelerating from ~$0.28/day to ~$0.60+/day. Exit for whatever the put is worth. Do not become a gambler hoping for a Thursday miracle.

5. **Profit target: $10.00 per contract.** If SPY hits $661 and the put reaches $10.00, sell. Do not hold for "more downside." The gap fill is the thesis. Once it fills, the thesis is complete. Take the money.

6. **If SPY hits $668 (halfway to gap fill):** Move your stop from $1.40 to $3.40 (breakeven). You have locked in a free trade. Let the rest ride to $10.00.

## Why Straight Puts Over Spreads

The v1 consensus recommended a put debit spread ($676/$663) as the safer version. That is a valid trade. But you asked for the **aggressive directional** position, so here is the case:

| Factor | Long Put ($670P) | Put Spread ($676/$663P) |
|--------|------------------|------------------------|
| Cost | $3.40 | ~$4.80 |
| Max profit | Uncapped below $670 | Capped at $8.20 |
| At gap fill ($661) | ~$10.00 (194% return) | ~$8.20 (71% return) |
| At ceasefire panic ($650) | ~$20.00 (488% return) | $8.20 (71% return, capped) |
| Theta/day | -$0.28 (all yours) | -$0.15 (net, partially offset) |
| Vega sensitivity | Higher (helps if VIX spikes) | Lower (short leg offsets) |

The straight put costs LESS than the spread ($3.40 vs $4.80) because it uses a lower strike, meaning less intrinsic exposure but more leverage on a big move. If the ceasefire collapses — which is the thesis — the move will be violent, not gradual. Ships will be attacked. Oil will spike. VIX will jump from 20 to 30+. In that scenario:

- The long put gains on delta (SPY falling) AND vega (VIX spiking). Double tailwind.
- The put spread has the vega gain partially canceled by the short leg.
- The long put has no cap. The spread maxes at $13 width ($676-663).

For a trader with HIGH CONVICTION on a binary event (ceasefire holds or collapses), the straight put is the sharper weapon.

## What Could Go Wrong

1. **Ceasefire actually holds.** Some commanders honor it. Oil stays down. Market rallies to 6900+. Your put expires worthless, but the stop limits damage to $200.

2. **Gap fill happens before Thursday.** You miss the trade entirely. Acceptable — discipline over FOMO.

3. **PCE comes in hot.** February data surprises with high inflation. VIX spikes, which HELPS your put if you already hold it, but you are entering POST-PCE. If the spike happens before entry, the put is more expensive. Adjust: if VIX jumps above 25 pre-entry, reduce position to limit-buy at $2.80 (smaller position, same dollar risk).

4. **Slow grind down instead of collapse.** SPY drifts from $678 to $672 over 5 days. Your put goes from $3.40 to $3.00 (theta eating the delta gain). Time stop at Wed Apr 15 saves you from holding a decaying position.

5. **Whipsaw.** SPY drops to $670, your put surges to $6.00, then SPY reverses to $680 and your put drops back to $2.50. **This is why the breakeven stop-move at $668 matters.** Once SPY hits $668, your stop moves to $3.40. You can't lose money on the trade even if it reverses.

---

## Summary for Borey

This is the purest expression of the ceasefire-collapse thesis: one contract, defined risk, no complications. The entry waits for PCE to crush IV so you buy cheap. The expiry gives the thesis 8 days to play out. The stop caps loss at exactly $200 (2%). If the ceasefire cracks, a $17 move in SPY produces ~$660 profit on $340 risked. If it holds, you lose $200 and move on.

No spread legs to manage. No Greeks to hedge. One order in, one order out. The thesis is binary — the ceasefire is enforceable or it is not — and this trade matches that simplicity.
