# Position 11: $7-Wide Put Butterfly -- Gap Fill Lottery Ticket

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783, SPY ~678)
**Thesis:** Ceasefire gap from ~6610 (SPY ~661) to ~6783 (SPY ~678) is unenforceable and will fill. Iran has 31 armed services, no unified chain of command. Supreme Leader in coma. Ceasefire paper is worthless. Borey expects gap fill next week. A $7-wide put butterfly centered at the gap fill target is the cheapest way to bet on a precise landing zone.
**Account:** $10,000
**VIX:** ~20

---

## TRADE TICKET

| Field | Value |
|---|---|
| **Structure** | $7-Wide Put Butterfly |
| **Legs** | Buy 1x SPY 668P / Sell 2x SPY 661P / Buy 1x SPY 654P |
| **Expiry** | **April 25, 2026** (19 DTE from April 6) -- RECOMMENDED |
| **Wing width** | $7 (skip-strike: 7 points between each leg) |
| **Center strike** | 661 (gap fill target: SPX ~6610) |
| **Entry debit** | ~$0.95-1.25 per butterfly (~$1.10 midpoint estimate) |
| **Quantity** | **15 contracts** |
| **Total risk** | ~$1,425-$1,875 (~$1,650 midpoint) -- 14-19% of $10K account |
| **Max profit** | $7.00 - $1.10 = ~$5.90 per butterfly x 15 = **~$8,850** |
| **Max profit at** | SPY closes exactly at 661 on April 25 |
| **Lower breakeven** | 654 + $1.10 = **~655.10** |
| **Upper breakeven** | 668 - $1.10 = **~666.90** |
| **Profitable range** | SPY between **~655 and ~667** at expiry (~$12 wide) |
| **R:R** | **~1:5.4** (risk ~$1,650 to make up to ~$8,850) |

---

## LEG DETAIL

| Leg | Strike | Type | Qty | Action | Role |
|---|---|---|---|---|---|
| 1 | 668 | Put | 15 | BUY | Upper wing (protection + profit above center) |
| 2 | 661 | Put | 30 | SELL | Body (center strike, max profit pin) |
| 3 | 654 | Put | 15 | BUY | Lower wing (protection + defines max loss) |

**Net position:** Long 15x 668P, Short 30x 661P, Long 15x 654P. Net debit spread.

---

## WHY THIS STRUCTURE

### Cheap Lottery Ticket Math

You are paying ~$1.10 per contract for a shot at $5.90. That is a 5.4:1 payout. Fifteen contracts cost ~$1,650 total -- a loss you can stomach on a $10K account. If SPY lands anywhere from 655 to 667 at expiry, you profit. If SPY lands at 661 on the nose, you make ~$8,850. If the gap never fills, you lose $1,650 and move on.

### Why $7-Wide (Not $5-Wide)

| Attribute | $5-Wide (666/661/656) | This $7-Wide (668/661/654) |
|---|---|---|
| Debit | ~$0.55 | ~$1.10 |
| Max profit/contract | ~$4.45 | ~$5.90 |
| Profitable range | ~$9 (656.55-665.45) | **~$12 (655.10-666.90)** |
| Profitable range width | 8.9 points | **11.8 points** |
| R:R | ~1:8 | ~1:5.4 |

The $7-wide costs 2x the debit but gives you 33% more room. The gap fill zone is SPY 660-662 but the actual reversal could stall at 658, overshoot to 665, or pin anywhere in between. You are buying imprecision insurance. The R:R drops from 1:8 to 1:5.4 -- still massively asymmetric.

### Why the Butterfly Is Vol-Neutral

VIX at 20 means puts are expensive. But a butterfly is long 2 puts and short 2 puts -- the vega nearly cancels. You are immune to IV crush. If VIX drops from 20 to 15 post-ceasefire-collapse, it barely moves your P&L. This is the structural advantage over a naked long put or put spread in a high-IV environment.

---

## PAYOFF TABLE (Per Contract, at April 25 Expiry)

| SPY at Expiry | Butterfly Value | P&L per Contract | Notes |
|---|---|---|---|
| 670+ | $0.00 | **-$1.10** (max loss) | All puts OTM, debit lost |
| 668 | $0.00 | **-$1.10** | At upper wing, worth zero |
| 667 | $1.00 | **-$0.10** | Near upper breakeven |
| 666 | $2.00 | **+$0.90** | Entering profit zone |
| 665 | $3.00 | **+$1.90** | Solid profit |
| 664 | $4.00 | **+$2.90** | Strong profit |
| 663 | $5.00 | **+$3.90** | Upper gap zone |
| 662 | $6.00 | **+$4.90** | Top of gap fill |
| **661** | **$7.00** | **+$5.90 (MAX)** | **Exact gap fill pin** |
| 660 | $6.00 | **+$4.90** | Bottom of gap fill |
| 659 | $5.00 | **+$3.90** | Below gap, still strong |
| 658 | $4.00 | **+$2.90** | Overshoot, still profitable |
| 656 | $2.00 | **+$0.90** | Profit fading |
| 655 | $1.00 | **-$0.10** | Near lower breakeven |
| 654 | $0.00 | **-$1.10** (max loss) | At lower wing |
| 650 or below | $0.00 | **-$1.10** (max loss) | Below lower wing |

**Key zone:** SPY 659-663 (the core gap fill area) yields **$3.90-$5.90 per contract** = **$5,850-$8,850 total on 15 contracts** vs $1,650 risked.

---

## EXPIRY CHOICE: APRIL 25 RECOMMENDED

| Factor | April 18 (12 DTE) | April 25 (19 DTE) -- RECOMMENDED |
|---|---|---|
| Debit | ~$0.85-1.10 | ~$0.95-1.25 |
| Extra cost | -- | ~$0.10-0.15 more per contract |
| Gamma ramp | Faster (violent final days) | Moderate (still strong final week) |
| Time for thesis | Tight -- gap must fill in 8 trading days | **19 calendar days -- covers full earnings week** |
| Catalyst window | Misses April 21-25 earnings | **Captures Goldman, Tesla, Boeing, GOOG earnings week** |
| Ceasefire collapse time | May not be enough | **More time for Iran's 31 factions to fracture ceasefire** |

**Recommendation: April 25.** The ceasefire is held together with duct tape (no unified Iranian military command, Supreme Leader incapacitated). But duct tape can last a week. April 18 forces the thesis to play out in 8 trading days. April 25 gives you 13 trading days, captures the full Q1 earnings wave, and costs only ~$0.10-0.15 more per contract ($150-$225 total on 15 contracts). That is trivial insurance.

**Exception -- use April 18 if:** You believe the collapse is imminent (e.g., Monday-Tuesday escalation), want maximum gamma, and are willing to accept the narrower time window. In that case, reduce quantity to 20 contracts at ~$0.90 = ~$1,800 risk.

---

## SIZING: WHY 15 CONTRACTS

| Size | Total Risk | Max Profit | % of $10K | Verdict |
|---|---|---|---|---|
| 5 contracts | ~$550 | ~$2,950 | 5.5% | Too small -- lottery ticket needs enough notional to matter |
| 10 contracts | ~$1,100 | ~$5,900 | 11% | Conservative -- acceptable for risk-averse sizing |
| **15 contracts** | **~$1,650** | **~$8,850** | **16.5%** | **RECOMMENDED -- meaningful payout, survivable loss** |
| 20 contracts | ~$2,200 | ~$11,800 | 22% | Aggressive -- only if high conviction |
| 30 contracts | ~$3,300 | ~$17,700 | 33% | Reckless -- too much capital in a single lottery ticket |

**15 contracts at ~$1.10 = ~$1,650 total risk.** This is 16.5% of the $10K account. If the gap never fills, you lose $1,650 and the account is at $8,350 -- painful but not crippling. If the gap fills to 661, you make ~$8,850 and nearly double the account. The Kelly criterion for a ~20% probability event with a 5.4:1 payout would suggest ~13% of bankroll, so 15 contracts is right in the zone.

---

## ENTRY RULES

1. **When:** Monday April 7, 2026, between 9:45-10:15 AM ET. Let the opening auction settle.
2. **How:** Place as a single butterfly combo order (3-leg), limit at $1.10 or better. Most brokers support this as "butterfly" order type.
3. **If not filled by 10:30 AM:** Raise limit to $1.20. Do not chase above $1.25.
4. **If SPY gaps down below $674 at the open:** Stand aside. The gap is already partially filling and the butterfly will be more expensive (closer to ATM). Wait for a bounce back toward $676-678 to enter, or skip entirely.
5. **If SPY gaps above $681:** The ceasefire rally has legs. Enter a smaller position (10 contracts) as the probability of near-term gap fill decreases.
6. **If you cannot get a 3-leg fill:** Enter as two vertical spreads: (a) Buy the 668/661 put spread, then (b) Sell the 661/654 put spread. Aim to get both legs on within 5 minutes.
7. **VIX check:** Confirm VIX is 18-25. Below 18 means the market is complacent (less likely to sell off). Above 25 means something has already broken and the butterfly may be mispriced.

---

## TRADE MANAGEMENT

### Profit Targets

| Condition | Action | Approximate P&L |
|---|---|---|
| SPY reaches 660-662 with 5+ DTE remaining | Close 100% of position for ~$4.00-5.50/contract | **+$4,350-$6,600** |
| Butterfly value hits $3.50 (3.2:1 return on debit) | Close 50% (8 contracts), let 7 ride | **Lock in ~$1,680 profit on the closed portion** |
| SPY at 661 with 1-2 DTE remaining | Close 100% for ~$5.50-6.50/contract | **+$6,600-$8,100** |
| Butterfly value hits $2.50 at any time | Consider closing 30-50% to book partial profit | **Risk-off: guaranteed gain on a lottery ticket** |

**Core rule: Do NOT hold for the exact pin.** A butterfly at max profit requires SPY to close exactly at 661 on the final day. That is a low-probability event even if the gap fills. Take 50-70% of max profit when offered. A $4.00 butterfly (3.6:1 return) is an excellent outcome.

### Time Stop

| Condition | Action |
|---|---|
| By Monday April 21 (4 DTE), SPY is above 673 | Thesis is failing. Close for residual value (~$0.05-0.20/contract). Accept the ~$1,500 loss. |
| By Wednesday April 23, SPY is above 670 | Close for whatever remains. The gap fill is not happening this cycle. |
| By Thursday April 24, position is worth < $0.30 | Close. Do not hold worthless butterflies into expiry for a miracle. |

### Stop Loss

| Condition | Action |
|---|---|
| SPY rallies above $683 and holds for a full session | Close for residual (~$0.10-0.30/contract). Loss: ~$1,200-$1,500. |
| VIX drops below 15 (complacency) | The put butterfly loses theoretical value. Evaluate but do not panic -- vol-neutral structure limits the damage. |

### What NOT to Do

- **Do NOT add to the position.** This is a single-entry lottery ticket. If it isn't working, adding more contracts just increases the loss.
- **Do NOT roll to a later expiry.** If April 25 fails, the thesis may be wrong. Accept the loss and reassess.
- **Do NOT remove the lower wing to "make it cheaper."** Removing the 654P turns this into a naked short put spread with massive downside risk. Never.
- **Do NOT hold into the final 30 minutes of April 25.** Close by 3:30 PM ET to avoid pin risk and auto-exercise on the short 661 puts.

---

## RISK ASSESSMENT

| Risk Factor | Impact | Mitigation |
|---|---|---|
| Gap never fills -- ceasefire holds, rally continues | Max loss = ~$1,650 (debit) | 16.5% of account. Survivable. Position sized for total loss. |
| Gap fills to 665, not 661 | Profit reduced to ~$1.90/contract (~$2,850 total) | Still profitable -- 665 is well inside the profit zone (655-667). |
| Gap fills too fast -- SPY crashes to 645 | Butterfly expires worthless. Max loss = ~$1,650 | Cannot lose more than debit. Overshoot risk is inherent in butterflies. |
| Gap fills early (April 10-15) then SPY bounces back by April 25 | Butterfly expires OTM. Max loss = debit. | **Close early.** If butterfly hits $2.50-3.50 mid-trade, take the money. |
| Liquidity on $7-wide SPY butterflies | Wider bid-ask on the combo order | Use limit orders. SPY is the most liquid option market in the world. Leg in if needed. |
| Pin risk at expiry | Assignment on 30 short 661 puts if SPY closes near 661 | **Close position by 3:30 PM ET on April 25.** Never hold butterflies to literal expiration. |
| Iran ceasefire actually holds | Gap does not fill. Lose debit. | $1,650 is the cost of being wrong. It is defined and acceptable. |
| VIX spike to 30+ mid-trade | Butterfly is vol-neutral so limited impact. May actually help if SPY is moving toward 661. | Monitor but do not panic. Structure self-hedges vega. |

---

## THE GEOPOLITICAL CASE (WHY THE GAP FILLS)

This is not standard "gap filling" technical analysis. The thesis has a specific structural foundation:

1. **Iran has 31 separate armed services.** The IRGC, Artesh (regular army), Basij, Quds Force, IRGC Navy, IRGC Air Force -- each with independent command structures, budgets, and political agendas. A ceasefire requires all 31 to comply. One rogue Quds Force commander in Syria or one IRGC Navy provocation in the Strait of Hormuz unravels it.

2. **Supreme Leader in coma.** Khamenei cannot enforce compliance even if the ceasefire were genuine. The succession struggle between hardliners and IRGC factions means every faction is posturing for power, not for peace.

3. **Historical precedent.** Every Iran "ceasefire" or "deal" since 2015 has been followed by proxy escalation within 2-4 weeks. The JCPOA was violated within months. The market knows this pattern but prices it out during the initial euphoria.

4. **The gap itself is the tell.** A 2.5% gap up on ceasefire news (SPX 6610 to 6783) with no earnings catalyst, no Fed pivot, and no economic data to support it is pure sentiment. Sentiment gaps fill.

5. **Calendar risk is front-loaded.** The next 19 days include Q1 earnings season, potential Fed commentary, and the natural unwinding of ceasefire optimism as implementation details (or lack thereof) emerge.

---

## POSITION SUMMARY

| Field | Value |
|---|---|
| **Structure** | Long 15x 668P / Short 30x 661P / Long 15x 654P |
| **Underlying** | SPY |
| **Expiry** | April 25, 2026 |
| **Wing width** | $7 (skip-strike) |
| **Center** | 661 (SPX ~6610 gap fill level) |
| **Debit** | ~$1.10/contract (~$1,650 total for 15x) |
| **Max profit** | ~$5.90/contract (~$8,850 total) |
| **Max loss** | ~$1,650 (debit paid -- hard floor, cannot lose more) |
| **Breakevens** | ~655.10 / ~666.90 |
| **Profitable range** | ~$12 wide (655 to 667) |
| **R:R** | ~1:5.4 |
| **Thesis** | Iran ceasefire is unenforceable. 31 armed services, comatose Supreme Leader. Gap from 661 to 678 fills within 19 days. |
| **Conviction** | Moderate-to-high on gap fill thesis, moderate on timing |
| **Entry** | Monday April 7, 9:45-10:15 AM ET, limit $1.10 |
| **Profit target** | Close at 50-70% of max ($3.00-$4.00/contract) |
| **Time stop** | Close if SPY above 673 on April 21 |
| **Hard stop** | Close by 3:30 PM ET on April 25, no exceptions |
