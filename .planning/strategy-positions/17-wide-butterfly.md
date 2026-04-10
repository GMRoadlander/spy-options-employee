# Position 17: Wide (Skip-Strike) Put Butterfly — Gap Fill to 660-662

**Thesis:** SPX gapped from ~6610 to ~6783. The 6600-6620 zone (SPY 660-662) is an unfilled gap. A standard butterfly (Position 05) targets the exact center but has a narrow ~$9 profit window. This wide butterfly uses 7-wide wings instead of 5-wide, expanding the profitable range to ~$12 — better suited when the exact landing zone within the gap is uncertain. The tradeoff: higher debit, but you cover more of the gap fill zone and tolerate imprecision.

---

## TRADE TICKET

| Field | Value |
|---|---|
| **Structure** | Wide Put Butterfly (skip-strike) |
| **Legs** | Buy 1x SPY 668P / Sell 2x SPY 661P / Buy 1x SPY 654P |
| **Expiry** | April 18, 2026 (12 DTE from April 6) |
| **Wing width** | $7 (skip-strike: 7 points between each leg) |
| **Entry debit** | ~$0.90-1.20 per butterfly (~$1.05 midpoint estimate) |
| **Quantity** | 10 contracts |
| **Total risk** | ~$900-1,200 (10x debit, cannot lose more) |
| **Max profit** | $7.00 - $1.05 = ~$5.95 per butterfly x 10 = ~$5,950 |
| **Max profit at** | SPY closes exactly at 661 on April 18 |
| **Lower breakeven** | 654 + $1.05 = ~655.05 |
| **Upper breakeven** | 668 - $1.05 = ~666.95 |
| **Profitable range** | SPY between ~655 and ~667 at expiry (~$12 wide) |
| **R:R** | ~1:5.5 (risk ~$1,050 to make up to ~$5,950) |

---

## LEG DETAIL

| Leg | Strike | Type | Qty | Action | Role |
|---|---|---|---|---|---|
| 1 | 668 | Put | 1 | BUY | Upper wing (protection) |
| 2 | 661 | Put | 2 | SELL | Body (center, max profit strike) |
| 3 | 654 | Put | 1 | BUY | Lower wing (protection) |

**Net position:** Long 1x 668P, Short 2x 661P, Long 1x 654P. Debit spread.

---

## Why Wide Wings (7-Wide vs 5-Wide)

| Attribute | Standard 5-Wide (Pos 05) | This 7-Wide (Pos 17) |
|---|---|---|
| Wings | 666/661/656 | 668/661/654 |
| Debit | ~$0.55 | ~$1.05 |
| Max profit/contract | ~$4.45 | ~$5.95 |
| Profitable range | ~$9 (656.55-665.45) | ~$12 (655.05-666.95) |
| Breakeven width | 8.9 points | 11.9 points |
| R:R | ~1:8 | ~1:5.5 |

**The key tradeoff:** The wide butterfly costs roughly 2x the debit but delivers:

1. **33% wider profit zone.** The gap fill zone is 660-662 but the actual reversal could stall at 658 or overshoot to 665. A 5-wide butterfly needs SPY within a $9 window; the 7-wide gives you $12 of room. That is the difference between catching an imprecise gap fill and missing it by $1.

2. **Higher max profit per contract.** Max profit is wing width minus debit. At $5.95 vs $4.45, the wider butterfly pays more per contract at the pin, partially offsetting the higher cost.

3. **More forgiving on timing.** With 12 DTE (April 18), SPY needs to reach the zone quickly. The extra width means a partial fill (say SPY reaches 665, not 661) still produces meaningful profit instead of near-breakeven.

4. **Better for an uncertain landing.** You know the gap is at 6600-6620 (SPY 660-662). You do NOT know if the fill will be precise, overshoot, or stall short. The wider wings are specifically designed for "I know the neighborhood but not the exact address."

5. **Lower R:R is acceptable.** The ratio drops from ~1:8 to ~1:5.5. Still highly asymmetric. You are not buying a lottery ticket at 1:20; you are buying a higher-probability lottery ticket at 1:5.5 with a wider net.

---

## Payoff at Key Prices (per contract, at April 18 expiry)

| SPY at Expiry | P&L per Contract | Notes |
|---|---|---|
| 670+ | -$1.05 (max loss) | Above upper wing, all puts OTM |
| 668 | -$1.05 | At upper wing, butterfly worth $0 |
| 667 | -$0.05 | Near upper breakeven |
| 666 | +$0.95 | Entering profit zone |
| 664 | +$2.95 | Solid profit |
| 662 | +$4.95 | Top of gap fill zone |
| 661 | +$5.95 (max profit) | Exact center pin |
| 660 | +$4.95 | Bottom of gap fill zone |
| 658 | +$2.95 | Still profitable |
| 656 | +$0.95 | Profit fading |
| 655 | -$0.05 | Near lower breakeven |
| 654 | -$1.05 | At lower wing, butterfly worth $0 |
| 652 or below | -$1.05 (max loss) | Below lower wing, all puts deep ITM |

**Note:** SPY anywhere from 659-663 (the core gap fill zone) yields $3.95-$5.95 per contract. That is $3,950-$5,950 on 10 contracts vs $1,050 risked.

---

## Why April 18 (Not April 25)

Position 05 uses April 25. This position deliberately uses April 18 for differentiation and a specific tactical reason:

1. **Cheaper debit.** Less time value means the butterfly costs less. At 12 DTE vs 19 DTE, you save ~$0.10-0.20 per contract on the net debit.

2. **Faster gamma ramp.** If SPY approaches the gap fill zone during the week of April 14-18, gamma acceleration is more violent at 12 DTE. The butterfly's value expands faster in the final days.

3. **Pairs with Position 05.** Running both creates a time-staggered structure: if the gap fills during April 14-18, Position 17 captures it with high gamma. If it fills later (April 21-25), Position 05 captures it. This is a time spread on the same thesis.

4. **Lower total capital at risk.** 10 contracts at ~$1.05 = ~$1,050 risk. Combined with Position 05 (30x at $0.55 = $1,650), total gap-fill exposure is ~$2,700 across two expiries — still under 30% of a $10K account.

---

## Trade Management

- **Entry:** Monday April 7 during the first 30 minutes (9:30-10:00 AM ET). Place as a single butterfly order, limit at $1.05 or better. If not filled by 10:30 AM, raise limit to $1.15.
- **Profit target:** Close at 50-60% of max profit ($3.00-$3.60 per contract). Do not hold for the exact pin — take the win.
- **Time stop:** If by Wednesday April 16 SPY is above 673, the thesis is failing for this expiry. Close for residual value (~$0.05-0.20).
- **Early fill scenario:** If SPY hits 660-662 before April 14, the butterfly will be worth $2.00-3.50 (below max due to remaining time value on the short puts). Consider closing 50% of the position and letting the rest ride.
- **Do not roll.** If this expires worthless, Position 05 (April 25) is still alive. Accept the loss on this expiry.
- **Close before expiry.** Exit by 3:00 PM ET on April 18 to avoid pin risk.

---

## Position Summary

| Field | Value |
|---|---|
| Structure | Long 668P / Short 2x 661P / Long 654P |
| Underlying | SPY |
| Expiry | April 18, 2026 |
| Wing width | $7 (skip-strike) |
| Debit | ~$1.05/contract (~$1,050 total for 10x) |
| Max profit | ~$5.95/contract (~$5,950 total) |
| Max loss | ~$1,050 (debit paid) |
| Breakevens | ~655.05 / ~666.95 |
| Profitable range | ~$12 (vs ~$9 for standard 5-wide) |
| R:R | ~1:5.5 |
| Thesis | SPX 6600-6620 gap fills by April 18; wide wings cover imprecise landing |
| Conviction | Moderate — this is the cheaper, faster-expiring companion to Position 05 |
| Pairing | Time-staggered with Position 05 (April 25, 5-wide) |
