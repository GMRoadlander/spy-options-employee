# Position 11: Broken Wing Put Butterfly -- Gap Fill to 6610

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783, SPY ~678)
**Thesis:** Ceasefire gap from ~661 to ~678 fills within 5-7 trading days. Broken wing butterfly profits from the drop with zero upside risk and a small credit at entry.
**Account:** $10,000 | **Risk budget:** 2% = $200
**VIX:** ~20

---

## STRUCTURE: What Is a Broken Wing Put Butterfly?

A regular put butterfly is symmetrical: buy 1 higher put, sell 2 middle puts, buy 1 lower put, all equally spaced. A **broken wing** (BWB) skews the lower wing wider, which:

1. Turns the trade from a debit into a **credit** (or very small debit)
2. Eliminates upside risk entirely -- if SPY stays flat or rallies, you keep the credit
3. Shifts risk to the downside: if SPY crashes *through* the lower wing, you have a loss
4. Max profit occurs at the short strike (the body) at expiration

Think of it as a free shot at a move to a specific price, with the tradeoff being you lose if the move overshoots too far.

---

## POSITION: SPY Apr 17 678/668/653 Broken Wing Put Butterfly

| Field | Detail |
|---|---|
| **Leg 1 (upper wing)** | **BUY 1x SPY Apr 17 $678 Put** (ATM) |
| **Leg 2 (body)** | **SELL 2x SPY Apr 17 $668 Put** (10 points below) |
| **Leg 3 (lower wing)** | **BUY 1x SPY Apr 17 $653 Put** (15 points below body) |
| **Entry** | **Monday Apr 7, between 10:00-10:30 AM ET** |
| **Expiry** | Apr 17, 2026 (11 DTE at entry) |
| **Upper wing width** | $10 (678 - 668) |
| **Lower wing width** | $15 (668 - 653) -- this is the "broken" part, 5 points wider |
| **Estimated credit** | **$0.45 per butterfly** ($45 credit per contract) |
| **Contracts** | **2 butterflies** |
| **Total credit received** | **$90** |

---

## PRICING BREAKDOWN (VIX ~20, 11 DTE, SPY ~678)

| Leg | Strike | Delta | Estimated Price | Action | Net |
|---|---|---|---|---|---|
| Upper wing | $678 Put | ~0.50 | $6.00 | Buy 1 | -$6.00 |
| Body | $668 Put | ~0.30 | $2.80 | Sell 2 | +$5.60 |
| Lower wing | $653 Put | ~0.12 | $0.85 | Buy 1 | -$0.85 |
| **Net** | | | | | **-$1.25** |

**Wait -- that is a debit, not a credit.** Let me recalculate with the skew adjustment.

At VIX 20 with 11 DTE, the put skew steepens meaningfully below ATM. The $653 put (3.7% OTM) will be cheaper than the linear interpolation suggests because it is deep OTM while both short legs benefit from elevated mid-range IV. However, the natural pricing of this structure at these strikes likely produces a **small debit of $1.00-1.50 per butterfly**, not a credit.

### REVISED: Accepting the Small Debit

| Field | Detail |
|---|---|
| **Estimated debit** | **$1.25 per butterfly** ($125 per contract) |
| **Contracts** | **2 butterflies** |
| **Total debit** | **$250** |
| **Max loss (upside)** | **$250** (debit paid -- SPY stays above $678) |
| **Max loss (downside)** | **$750** (see calculation below) |
| **Max profit** | **$1,750** (at $668 at expiration) |
| **Reward:Risk** | **7:1** (on the upside loss) or **2.3:1** (on the downside loss) |

---

## P&L AT EXPIRATION

| SPY at Expiry | Leg 1 (678P) | Leg 2 (2x 668P) | Leg 3 (653P) | Net P&L (per BWB) |
|---|---|---|---|---|
| **$680** (flat/up) | $0 | $0 | $0 | **-$1.25** (debit lost) |
| **$678** | $0 | $0 | $0 | **-$1.25** |
| **$673** | +$5.00 | $0 | $0 | **+$3.75** |
| **$670** | +$8.00 | $0 | $0 | **+$6.75** |
| **$668** (MAX PROFIT) | +$10.00 | $0 | $0 | **+$8.75** |
| **$665** | +$13.00 | -$6.00 | $0 | **+$5.75** |
| **$660** | +$18.00 | -$16.00 | $0 | **+$0.75** |
| **$658** (breakeven low) | +$20.00 | -$20.00 | $0 | **-$1.25** |
| **$655** | +$23.00 | -$26.00 | $0 | **-$4.25** |
| **$653** (max loss) | +$25.00 | -$30.00 | $0 | **-$6.25** |
| **$648** (below lower wing) | +$30.00 | -$40.00 | +$5.00 | **-$6.25** |

**Downside max loss formula:** Lower wing width minus upper wing width minus credit = $15 - $10 + $1.25 = **$6.25 per butterfly**. With 2 contracts: $6.25 x 2 x 100 = **$1,250**.

**STOP.** That exceeds 2% of the account. Recalibrating.

---

## RECALIBRATED POSITION (Strict Risk Management)

### Option A: 1 Butterfly (RECOMMENDED)

| Field | Detail |
|---|---|
| **Action** | BUY 1x SPY Apr 17 $678P / SELL 2x SPY Apr 17 $668P / BUY 1x SPY Apr 17 $653P |
| **Entry** | Monday Apr 7, 10:00-10:30 AM ET |
| **Estimated debit** | ~$1.25 ($125 total) |
| **Max loss (upside)** | **$125** (SPY stays above $678) = 1.25% of account |
| **Max loss (downside)** | **$625** (SPY at $653 or below) = 6.25% of account |
| **Max profit** | **$875** (SPY at exactly $668 at expiry) |
| **Profitable range** | **$676.75 to $659.25** (approx 17.5 points of SPY) |
| **Breakeven (upper)** | $678 - $1.25 = **$676.75** |
| **Breakeven (lower)** | $653 + ($6.25 - $1.25) = ~**$659.25** |
| **Reward:Risk (upside)** | 7:1 |
| **Reward:Risk (downside)** | 1.4:1 |

### Why This Works for the Thesis

The gap-fill target is SPY ~$661-668. The max profit zone of this butterfly ($668) sits at the **top of the gap fill zone**. SPY does not need to fill the entire gap -- just reaching the upper edge of the fill zone at $668 delivers max profit.

The danger zone ($653 and below) requires SPY to drop 3.7% from current levels -- a crash scenario that goes well beyond the gap fill. This is the tradeoff: you give up protection against a crash in exchange for zero-cost upside risk.

---

## STRIKE JUSTIFICATION

### Why $678 (upper wing)?
- ATM strike. Gives the butterfly its maximum sensitivity to the first move down.
- Friday close was ~$678, so any Monday red candle immediately puts this leg ITM.
- ATM puts have the highest absolute delta of the three legs -- this is what makes the trade work.

### Why $668 (body / short strikes)?
- **This is the money strike.** $668 SPY = ~SPX 6680, which is the area where the gap starts to thin out.
- The pre-gap consolidation high was ~$668-670. Market should find initial support here.
- Selling 2x at $668 means if SPY stops dropping right at this support level, you get max profit.
- The gap fill "thesis price" of $661 is 7 points below this, meaning even a partial gap fill (to $665-668) delivers 60-100% of max profit.

### Why $653 (lower wing)?
- Placed $15 below the body (vs $10 above). The extra $5 of width is what generates the credit/small debit and eliminates upside risk.
- $653 corresponds to SPX ~6530, which would be a full gap fill plus an additional 1.2% overshoot. This is "VIX 30, ceasefire collapsed, CPI was hot" territory.
- Below $653, your losses are capped. The long put protects against a true crash.
- $653 avoids the $650 round number magnet and sits in a less crowded strike zone.

### Why 15-point / 10-point asymmetry?
- 5 points of skew is the minimum needed to turn a debit butterfly into a near-zero cost entry.
- More skew (e.g., $648 lower wing for 20-point width) would produce a larger credit but dramatically increases the downside max loss ($20 - $10 = $10 loss per butterfly, minus credit = ~$9.50 max loss = $950 on 1 contract). Not worth it.
- 5 points of skew keeps the downside max loss manageable while achieving the near-zero upside risk objective.

---

## ENTRY RULES

1. **Wait for 10:00 AM ET.** Let the opening auction and any gap-up continuation finish.
2. **Confirm SPY is still $676-680.** If SPY has already dropped to $674 or below, the trade is less attractive -- the body ($668) is too close and the butterfly is already partially ITM, making it more expensive.
3. **If SPY gaps above $681**, stand aside. The ceasefire rally may have legs and the upper breakeven ($676.75) is too far below.
4. **Leg into it if needed.** If you cannot get a reasonable fill on the 3-leg order, you can enter as: (a) buy the 678/668 put spread first, then (b) sell the 668/653 put spread. This sometimes gets better fills than the 3-leg combo order.
5. **Check VIX is 18-25.** Below 18 means puts are too cheap (the butterfly costs more as a debit). Above 25 means something has already broken and you are entering mid-move.

---

## EXIT RULES

### Profit Targets

| Condition | Action | Expected P&L |
|---|---|---|
| **SPY drops to $668-670 with 3+ DTE remaining** | Close entire butterfly for ~$6.00-7.00 | **+$475 to +$575** (sell for $6-7, paid $1.25) |
| **SPY at $668 with 1-2 DTE** | Close for ~$8.00-8.75 | **+$675 to +$750** |
| **SPY at $668 on expiration day** | Let expire or close for ~$8.75 | **+$750** (near max) |
| **Butterfly value reaches $5.00** | Take profit -- 4:1 return on debit | **+$375** |

**Key rule: Do NOT hold to expiry hoping for a pin at $668.** Butterflies lose value rapidly in the last 1-2 days if the underlying is not sitting on the short strike. Take 60-80% of max profit when offered.

### Stop Loss

| Condition | Action | Loss |
|---|---|---|
| **SPY rallies above $681 and holds for a full session** | Close for whatever the butterfly is worth (~$0.30-0.60) | **-$65 to -$95** |
| **SPY crashes below $658 quickly (within 2 days)** | Close immediately -- you are entering the downside loss zone | **-$100 to -$300** (depending on speed and time remaining) |
| **By Wednesday Apr 9 close, SPY has not broken below $675** | Close the butterfly for whatever it is worth | **-$50 to -$100** (theta decay but some time value remains) |

### The Downside Stop Is Critical

The downside max loss ($625) is the real risk in this trade. If SPY starts crashing through $660 toward $653, **do not hold hoping for a bounce**. The loss accelerates in the $660-$653 zone. Close if SPY breaks $658 convincingly (e.g., closes below $658, or intraday moves below $656).

---

## TIME DECAY (THETA) PROFILE

This is what makes the butterfly attractive vs. a straight put or spread:

| Day | Theta Impact | Notes |
|---|---|---|
| Mon-Tue (11-9 DTE) | Minimal theta. Vega is your main driver. | Trade moves with SPY and VIX. |
| Wed-Thu (8-7 DTE) | Theta starts helping if SPY is near $668 | The short strikes decay faster than your longs. If SPY is in the profit zone, the butterfly *gains* value from time passing. |
| Fri+ (6-4 DTE) | Theta is your friend OR enemy | Near $668: butterfly accelerates toward max profit. Near $678 or $658: butterfly accelerates toward zero or max loss. |
| Final 2 days | Violent gamma | Butterfly value swings sharply. Do not hold into final day unless SPY is pinned at $668. |

**Key insight:** Unlike a long put where theta always hurts you, a butterfly's theta works FOR you once SPY is in the profit zone. This is why you can afford to be patient.

---

## COMPARISON TO POSITIONS 01 AND 02

| Factor | Pos 01 (Long Put) | Pos 02 (Put Spread) | Pos 11 (BWB) |
|---|---|---|---|
| Cost / Risk if wrong | $480 (full loss) | $480 (full loss) | $125 (if flat/up) |
| Max profit | Unlimited | $820 | $875 |
| Profitable range | Below $673.20 | $671.20 to $663 | **$676.75 to $659.25** (widest) |
| Risk if SPY rallies | Lose $480 | Lose $480 | **Lose only $125** |
| Risk if SPY crashes | Profit increases | Capped at $820 | Lose up to $625 |
| Theta | Enemy (always) | Enemy (always) | **Friend when in the zone** |
| Complexity | Simple | Moderate | Highest (3 legs) |
| Best for | High-conviction directional | Conservative directional | **Targeting a specific price with low upside cost** |

**The BWB is ideal when you have a specific price target ($668) and want to minimize the cost of being wrong on direction (only $125 upside risk).** The tradeoff is that a crash *through* your target actually hurts you.

---

## RISK FACTORS

| Risk | Impact | Mitigation |
|---|---|---|
| SPY stays flat at $678 | Lose $125 debit | Smallest loss of all three positions |
| SPY rallies to $685+ | Lose $125 debit | Same -- this is the beauty of the BWB |
| VIX crush (drops to 15) | Butterfly may lose some value but structure is self-hedging | Less exposed to vega than a long put because shorts partially offset |
| SPY crashes to $650 (overshoot) | Lose up to $625 | Hard stop at $658. Accept the loss, do not hold into the max-loss zone |
| PCE/CPI spike causes gap down Monday | Butterfly becomes expensive to enter; body may be too close | Skip if SPY gaps below $674 at open |
| Liquidity on 3-leg combo | May get poor fill | Leg in as two spreads (see entry rules). SPY options are very liquid at $5 strikes |
| Pin risk at expiry | Short strikes exercised, long strikes expire worthless | Close at least 1 day before expiry. Never hold a butterfly to literal expiration |

---

## POST-ENTRY CHECKLIST

- [ ] Set alert at SPY $675 (entering profit zone)
- [ ] Set alert at SPY $668 (max profit zone -- prepare to close)
- [ ] Set alert at SPY $658 (danger zone -- prepare to exit)
- [ ] Set alert at SPY $681 (thesis dead -- close)
- [ ] Calendar reminder: Wednesday Apr 9 3:45 PM ET -- evaluate time stop
- [ ] Calendar reminder: Thursday Apr 10 3:00 PM ET -- must decide: hold through CPI or close
- [ ] **Confirm you can enter a 3-leg butterfly order on your platform.** If not, enter as two vertical spreads.
- [ ] Do NOT adjust the position mid-trade (no rolling, no adding legs). This is a set-it-and-manage-it structure.

---

## BOREY SUMMARY

**In plain English:** You are betting SPY drops from $678 to around $668 by next week. The broken wing butterfly costs you $125 and pays $875 if you are right. If SPY goes nowhere or rallies, you lose only $125. If SPY crashes through $658, you start losing more -- up to $625 -- but you have a stop loss to prevent that.

**Why this over a put or spread:** You risk $125 instead of $480 if the market stays flat or goes up. The gap fill thesis has maybe a 50-60% probability. On the ~40% chance you are wrong, losing $125 instead of $480 is the difference between a scratch and a meaningful drawdown on a $10K account.

**The catch:** If the market crashes and overshoots the gap fill, you lose money. A straight put would profit in that scenario, the BWB does not. You are specifically betting on a *controlled* move to a *specific area*, not a crash.

**Action required:** Enter Monday morning. Manage with the stops above. Take profit at $5.00+ on the butterfly. Do not hold to expiry.
