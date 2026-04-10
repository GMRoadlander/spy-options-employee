# Position 05: Broken Wing Put Butterfly -- Gap Fill to SPY 661-668

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783, SPY ~678)
**Thesis:** Ceasefire gap from ~661 to ~678 is structurally unenforceable (31 Iranian armed services, Supreme Leader in coma). Gap fill to SPY ~661 expected. Timing uncertain -- could come any day next week.
**Account:** $10,000 | **Risk budget:** $125 (1.25% of account on upside)
**VIX:** ~20

---

## STRUCTURE: What Is a Broken Wing Put Butterfly?

A standard put butterfly buys equal-width wings around a center strike. A **broken wing** put butterfly makes the lower wing wider than the upper wing. This creates three properties:

1. **Small debit entry** -- the wider lower wing collects more premium from the short puts, reducing net cost
2. **Zero upside risk** -- if SPY stays flat or rallies, you lose only the small debit ($125)
3. **Downside risk zone** -- if SPY crashes *through* the lower wing, losses grow (capped at the wing width difference)
4. **Max profit at the body** -- if SPY sits at the short strike at expiration, you collect the full upper wing width minus your debit

The broken wing butterfly is ideal for targeting a **specific price zone** (the gap fill) with minimal cost if the thesis is wrong on direction.

---

## TRADE TICKET

| Field | Detail |
|---|---|
| **Leg 1 (upper wing)** | **BUY 1x SPY Apr 25 $675 Put** |
| **Leg 2 (body)** | **SELL 2x SPY Apr 25 $665 Put** |
| **Leg 3 (lower wing)** | **BUY 1x SPY Apr 25 $650 Put** |
| **Entry** | **Monday Apr 7, 10:00-10:30 AM ET** (after opening volatility settles) |
| **Expiry** | April 25, 2026 (19 calendar days / 14 trading days at entry) |
| **Upper wing width** | $10 (675 - 665) |
| **Lower wing width** | $15 (665 - 650) -- this is the "broken" part, 5 points wider |
| **Estimated debit** | **~$1.25 per butterfly** ($125 per contract) |
| **Contracts** | **1 butterfly** |
| **Total risk (upside)** | **$125** |

---

## PRICING ESTIMATE (VIX ~20, 19 DTE, SPY ~678)

| Leg | Strike | Est. Delta | Est. Price | Action | Net |
|---|---|---|---|---|---|
| Upper wing | $675 Put | ~0.40 | $4.90 | Buy 1 | -$4.90 |
| Body | $665 Put | ~0.25 | $2.55 | Sell 2 | +$5.10 |
| Lower wing | $650 Put | ~0.10 | $0.75 | Buy 1 | -$0.75 |
| **Net** | | | | | **-$0.55** |

**Skew adjustment:** At VIX 20 with SPY put skew, the OTM puts carry elevated implied vol. The $675 put (ATM-ish) trades at ~19-20 IV, while the $650 put (4.1% OTM) trades at ~22-24 IV due to skew. This steepening makes the lower wing relatively more expensive than a flat-vol model suggests, pushing the net debit from ~$0.55 to approximately **$1.00-1.50**. The $1.25 midpoint is the working estimate.

**If actual debit is lower (~$0.75-1.00):** Even better -- upside risk drops and reward:risk improves.
**If actual debit is higher (~$1.50-1.75):** Still acceptable. Max loss on upside is $175. Consider reducing to the tightest fill you can get.

---

## P&L AT EXPIRATION (per 1 butterfly)

| SPY at Expiry | Leg 1 (675P) | Leg 2 (2x 665P) | Leg 3 (650P) | Net P&L |
|---|---|---|---|---|
| **$680** (flat/rally) | $0 | $0 | $0 | **-$1.25** (lose debit) |
| **$678** (unchanged) | $0 | $0 | $0 | **-$1.25** |
| **$675** (at upper wing) | $0 | $0 | $0 | **-$1.25** |
| **$673** | +$2.00 | $0 | $0 | **+$0.75** |
| **$670** | +$5.00 | $0 | $0 | **+$3.75** |
| **$668** (top of gap) | +$7.00 | $0 | $0 | **+$5.75** |
| **$665** (MAX PROFIT) | +$10.00 | $0 | $0 | **+$8.75** |
| **$663** | +$12.00 | -$4.00 | $0 | **+$6.75** |
| **$661** (full gap fill) | +$14.00 | -$8.00 | $0 | **+$4.75** |
| **$658** | +$17.00 | -$14.00 | $0 | **+$1.75** |
| **$656.25** (lower breakeven) | +$18.75 | -$17.50 | $0 | **-$0.00** |
| **$655** | +$20.00 | -$20.00 | $0 | **-$1.25** |
| **$653** | +$22.00 | -$24.00 | $0 | **-$3.25** |
| **$650** (at lower wing) | +$25.00 | -$30.00 | $0 | **-$6.25** |
| **$645** (below lower wing) | +$30.00 | -$40.00 | +$5.00 | **-$6.25** (capped) |

---

## RISK & REWARD SUMMARY

| Metric | Value |
|---|---|
| **Max loss (upside / flat)** | **$125** (debit paid) -- SPY at $675 or above |
| **Max profit** | **$875** (SPY at exactly $665 at expiry) |
| **Max loss (downside)** | **$625** (SPY at $650 or below) |
| **Reward:Risk (upside)** | **7:1** |
| **Reward:Risk (downside)** | **1.4:1** |
| **Upper breakeven** | **$673.75** ($675 - $1.25) |
| **Lower breakeven** | **$656.25** ($650 + $6.25 - $1.25) |
| **Profitable range** | **$673.75 to $656.25** (~17.5 points of SPY) |

### Why the 7:1 Upside R:R Matters

On a $10K account with uncertain timing, the broken wing butterfly lets you bet on the gap fill for $125. If SPY rallies 5%, rallies 2%, or goes nowhere -- you lose $125. That is a scratch. The 40-50% probability of the thesis being wrong costs you 1.25% of the account. The 50-60% probability of the gap filling pays up to $875.

---

## STRIKE JUSTIFICATION

### Why $675 (upper wing)?

- **3 points below current price ($678).** SPY needs to drop only $4.25 (0.6%) before the trade is profitable at the upper breakeven ($673.75).
- Avoids ATM ($678) which would be more expensive and reduce the favorable debit.
- $675 is a round, liquid strike with tight bid-ask spreads.
- If SPY gaps down Monday, $675 may already be ATM or ITM, immediately putting the butterfly in play.

### Why $665 (body / short strikes)?

- **Dead center of the gap fill zone (661-668).** Max profit occurs at $665, which means:
  - A move to $668 (top of gap): **+$575** (66% of max profit)
  - A move to $661 (bottom of gap): **+$475** (54% of max profit)
  - A move to $665 (mid-gap): **+$875** (max profit)
- The pre-gap consolidation zone was SPY ~660-668. The body sits at the midpoint of that zone.
- SPX 6650 is a psychologically significant level where institutional support/resistance clusters.

### Why $650 (lower wing)?

- **15 points below the body** (vs 10 above). The 5-point asymmetry generates the small debit / zero upside risk structure.
- $650 represents SPY down 4.1% from current -- a genuine fear scenario (VIX 28+, ceasefire collapse + economic shock).
- Below $650, the long put caps your losses. A true crash beyond $650 cannot hurt you further.
- $650 is far enough below the gap fill target ($661) that a normal gap fill does not threaten the downside loss zone. SPY would need to overshoot the gap fill by $11 to reach max loss.

### Why 10/15 Asymmetry (Not 10/20 or 8/13)?

- **5 points of skew is the sweet spot.** It generates ~$1.25 debit -- small enough to make upside risk trivial ($125) but not so aggressive that downside max loss becomes catastrophic.
- A 10/20 split (e.g., 675/665/645) would reduce the debit further but push downside max loss to $10 - debit = ~$875+. Not worth it for a new trader.
- An 8/13 split (e.g., 673/665/652) narrows the upper wing too much, reducing max profit to ~$675. The 10-wide upper wing is the standard that delivers the 7:1 ratio.

---

## ENTRY RULES

1. **Wait until 10:00 AM ET.** Let the opening auction and any continuation moves settle. The first 30 minutes are noisy and spreads are wide on multi-leg orders.

2. **Confirm SPY is $675-681.** This is the ideal entry zone:
   - Below $675: The butterfly is already partially ITM. It will cost more as a debit (likely $2.00+). The 7:1 ratio degrades. Consider reducing to the 673/663/648 structure instead, or skip.
   - Above $681: The ceasefire rally has extended. The upper breakeven ($673.75) is too far below. Stand aside.

3. **Check VIX is 18-24.**
   - Below 18: Puts are cheap, butterfly debit may be even smaller (good), but low VIX suggests complacency that may delay the gap fill.
   - Above 24: Something is already breaking. You may be entering mid-move. The butterfly will be more expensive and the body may be too close.

4. **Enter as a single 3-leg butterfly order.** SPY options at $5 strikes are extremely liquid. Place a limit order at the butterfly midpoint. If not filled within 20 minutes, widen your limit by $0.10.

5. **If the platform does not support 3-leg butterflies:** Enter as two vertical spreads:
   - First: Buy the $675/$665 put debit spread (upper half)
   - Second: Sell the $665/$650 put credit spread (lower half)
   - Aim to enter both within the same minute to avoid leg risk.

6. **Do NOT enter if SPY gaps below $672 at the open.** A large gap down means the thesis is already in motion and the butterfly will be expensive. Wait for a bounce toward $675-678 and reassess.

---

## EXIT RULES

### Profit Targets

| Condition | Action | Expected P&L |
|---|---|---|
| **SPY drops to $665-667 with 5+ DTE remaining** | Close entire butterfly for ~$5.00-6.50 | **+$375 to +$525** |
| **SPY at $665 with 3-4 DTE** | Close for ~$7.00-8.00 | **+$575 to +$675** |
| **SPY at $665 with 1-2 DTE** | Close for ~$8.00-8.50 | **+$675 to +$725** |
| **Butterfly value reaches $5.00** (any time) | **Take profit -- 4:1 return achieved** | **+$375** |
| **Butterfly value reaches $6.50** (any time) | Take profit -- 5.2:1 return achieved | **+$525** |

**Primary rule: Take 50-75% of max profit when offered. Do NOT hold to expiry chasing the pin at $665.** Butterflies are extremely gamma-sensitive in the final 2 days. A $2 move off the body can erase most of your profit overnight.

### Stop Losses

| Condition | Action | Expected Loss |
|---|---|---|
| **SPY rallies above $681 and holds a full session** | Close butterfly for residual value (~$0.30-0.60) | **-$65 to -$95** |
| **SPY crashes below $656 intraday** | **HARD STOP -- close immediately** | **-$100 to -$300** |
| **SPY closes below $655** | Close next morning at market open | **-$200 to -$400** |
| **By Wednesday Apr 16 close, SPY still above $675** | Close for residual time value | **-$50 to -$100** |

### THE DOWNSIDE STOP IS NON-NEGOTIABLE

The downside max loss ($625) is the real danger in this trade. Here is why the hard stop at $656 exists:

- At $665 (body), you have max profit: +$875
- At $660, profit has eroded to: +$350
- At $656, you are near breakeven: ~$0
- At $653, you are losing: -$325
- At $650, you hit max loss: -$625

The loss accelerates in the $660-$650 zone. **If SPY breaks $656 convincingly (closes below, or trades below $654 intraday), exit the trade.** Do not hold hoping for a bounce. The gap fill thesis called for a controlled decline to 661-668, not a crash through 650. If SPY is at 655, the thesis has been blown through and the trade is now a pure gamble on a bounce.

---

## TIME DECAY (THETA) PROFILE

| Period | DTE | Theta Behavior | Notes |
|---|---|---|---|
| Week 1 (Apr 7-11) | 19-14 | Minimal theta impact | Trade driven by delta (SPY direction) and vega (VIX moves). Theta is ~$3-5/day on the butterfly. |
| Week 2 (Apr 14-18) | 13-7 | Theta starts mattering | If SPY is near $665: theta *helps* (short puts decay faster). If SPY is near $675 or $656: theta *hurts* (your long puts decay). |
| Final week (Apr 21-25) | 6-0 | Theta dominates | Near $665: butterfly accelerates toward $8.75 max. Away from $665: butterfly collapses toward zero. This is where you must be decisive. |

**Key insight:** Unlike a long put where theta is always your enemy, the butterfly's theta works **for** you when SPY is in the profit zone ($656-$674). The two short $665 puts decay faster than your one long $675 put and one long $650 put combined. Time passing near the body is your friend.

---

## GREEKS SNAPSHOT AT ENTRY (approximate, per 1 BWB)

| Greek | Value | Meaning |
|---|---|---|
| **Delta** | ~ -8 to -12 | Slightly bearish. You profit as SPY drops (initially). |
| **Gamma** | ~ +0.5 to +1.0 | Low at entry. Increases dramatically as SPY approaches $665 near expiry. |
| **Theta** | ~ -$3 to -$5/day | Small daily decay at entry. Flips positive when SPY enters the profit zone. |
| **Vega** | ~ +$0.10 to +$0.20 | Nearly vega-neutral. A VIX spike or crush barely affects the butterfly because the shorts and longs partially offset. |

**Vega neutrality is a feature.** If VIX spikes from 20 to 28 because the ceasefire collapses, your long puts gain vega but so do your short puts. The butterfly's value changes primarily from delta (SPY moving), not from IV expansion. This means you are not paying for a VIX bet -- you are paying purely for a move to a specific price.

---

## WHY THIS STRUCTURE vs ALTERNATIVES

| Factor | Long Put | Put Spread (Bear) | BWB (This Trade) |
|---|---|---|---|
| **Cost if wrong (SPY flat/up)** | $400-600 | $300-500 | **$125** |
| **Max profit** | Unlimited | $500-800 | **$875** |
| **Profitable range** | Below breakeven | Below breakeven | **$673.75 to $656.25** (widest) |
| **Theta** | Always hurts | Always hurts | **Helps when in zone** |
| **Vega sensitivity** | High | Moderate | **Low (near neutral)** |
| **Crash (SPY to $640)** | Big profit | Capped profit | **-$625 loss** |
| **Best when** | High conviction, timing certain | Moderate conviction | **Specific target, timing uncertain** |

**The BWB is the correct structure for this thesis** because:
1. Timing is uncertain ("could come any day next week") -- the BWB's low upside cost means you can afford to be early
2. The target is specific (gap fill to 661-668) -- the BWB's max profit sits at $665, dead center
3. A crash through the gap is not the base case -- the BWB's downside risk is the acceptable tradeoff for the 7:1 upside ratio

**The one scenario where the BWB is wrong:** If you believe SPY could crash to $640+ (full panic), a long put or put backspread is better. The BWB loses money on a crash. But the thesis is "gap fill," not "market crash."

---

## RISK FACTORS

| Risk | Impact | Mitigation |
|---|---|---|
| SPY stays flat at $678 all month | Lose $125 debit | Smallest possible loss. 1.25% of account. |
| SPY rallies to $690+ (ceasefire holds) | Lose $125 debit | Same. Zero additional risk on the upside. |
| VIX crush (drops to 14-15) | Butterfly may cheapen slightly but structure is self-hedging | Vega-neutral design means IV crush is a non-issue. |
| VIX spike to 30+ (panic event) | Butterfly gets more expensive to close but the underlying move matters more | If VIX spikes because SPY is dropping, you are profiting on delta. Close at profit target. |
| SPY crashes to $645 (overshoot) | Lose up to $625 | **HARD STOP at $656.** Accept $100-300 loss, do not hold into the $650 max-loss zone. |
| Gap fills early (Apr 8-10) but bounces back by Apr 25 | Butterfly was profitable but you missed the window | Profit targets at $5.00-6.50 catch this. Take profit when offered, do not wait for expiry. |
| Liquidity / fill quality on 3-leg combo | May get wide bid-ask | SPY $5-strike options are the most liquid in the world. Leg in as two spreads if needed. |
| Pin risk at expiry | Short puts exercised, long puts expire worthless | Close position by 3:00 PM ET on Apr 25. Never hold a butterfly to literal expiration. |
| Monday gap down (SPY opens at $672) | Butterfly is expensive to enter, body is close | **Do not enter if SPY opens below $672.** Wait for a bounce. |

---

## POST-ENTRY CHECKLIST

- [ ] Confirmed fill price: debit of $______ (target ~$1.25)
- [ ] Set price alert: SPY $674 (entering profit zone)
- [ ] Set price alert: SPY $668 (strong profit -- consider taking 50%+)
- [ ] Set price alert: SPY $665 (max profit zone -- close most or all)
- [ ] Set price alert: SPY $656 (HARD STOP -- close immediately)
- [ ] Set price alert: SPY $681 (thesis dead -- close)
- [ ] Calendar: Wednesday Apr 16 3:45 PM ET -- evaluate time stop (close if SPY above $675)
- [ ] Calendar: Friday Apr 18 -- one week to expiry. If not in profit zone, reassess thesis.
- [ ] Calendar: Thursday Apr 24 3:00 PM ET -- must close position before final day if still open
- [ ] **Platform confirmation:** Can enter a 3-leg butterfly order? If not, enter as two vertical spreads.
- [ ] **Do NOT adjust mid-trade.** No rolling, no adding legs, no converting to a different structure. This is a set-and-manage position.

---

## SCENARIO WALKTHROUGH

### Scenario A: Thesis works perfectly (50% probability estimate)
SPY drifts down from $678, reaches $668 by April 14, continues to $664-666 by April 18-22. Butterfly is worth $6.00-8.00. You close at $6.50 for **+$525 profit** (4.2:1 return on $125 risked). Total time in trade: 7-15 days.

### Scenario B: Partial gap fill (20% probability)
SPY drops to $670-672 but stalls. Never reaches the body at $665. Butterfly is worth $2.50-4.00 with 5+ DTE. You close at $3.00 for **+$175 profit** (1.4:1 return). Acceptable outcome.

### Scenario C: Rally continues / flat (20% probability)
SPY holds $676-682 all week. Butterfly decays toward zero. You close at the time stop (April 16) for ~$0.40. **-$85 loss.** Less than the max debit because you exited early. Non-event for the account.

### Scenario D: Crash through the gap (10% probability)
SPY drops hard -- $660 by April 10, $652 by April 14. The hard stop at $656 triggers on the way down. You close for **-$200 to -$350 loss.** Painful but contained. Without the stop, max loss would be $625.

---

## POSITION SUMMARY

| Field | Value |
|---|---|
| **Structure** | Broken Wing Put Butterfly |
| **Legs** | Long 1x 675P / Short 2x 665P / Long 1x 650P |
| **Underlying** | SPY |
| **Expiry** | April 25, 2026 |
| **Upper wing width** | $10 |
| **Lower wing width** | $15 (broken -- 5 points wider) |
| **Entry debit** | ~$1.25/contract ($125 total for 1x) |
| **Max profit** | $8.75/contract ($875 total) at SPY $665 |
| **Max loss (upside)** | $1.25/contract ($125 total) -- SPY at $675+ |
| **Max loss (downside)** | $6.25/contract ($625 total) -- SPY at $650 or below |
| **Upper breakeven** | ~$673.75 |
| **Lower breakeven** | ~$656.25 |
| **Profitable range** | ~17.5 points ($656.25 to $673.75) |
| **Reward:Risk (upside)** | 7:1 |
| **Hard stop** | SPY $656 intraday (non-negotiable) |
| **Profit target** | Close at $5.00-6.50 butterfly value (50-75% of max) |
| **Time stop** | Close by Apr 16 if SPY above $675 |
| **Thesis** | Ceasefire gap (SPY 661-678) fills back to 665 zone by April 25 |
| **Conviction** | Moderate-high -- gap fills are probabilistic, geopolitical catalyst is real |

---

## BOREY SUMMARY

**What you are doing:** Buying a broken wing butterfly for $125 that pays $875 if SPY drops from $678 to around $665 by April 25. That is 7-to-1 on the upside risk.

**If you are wrong:** SPY rallies or stays flat -- you lose $125. That is one coffee-and-lunch on a $10K account. You do not care.

**If you are right:** SPY fills the gap to the $661-668 zone. You make $375-$875 depending on exactly where it lands. The sweet spot is $665 (mid-gap) for the full $875.

**The danger:** SPY does not just fill the gap -- it crashes through it to $650 or lower. Then you lose up to $625. This is why the hard stop at $656 exists. If SPY blows through the gap fill zone, you are out. No hoping, no praying, no "it will bounce."

**Why this and not a straight put:** A put costs $400-600 and you lose all of it if SPY stays flat. The butterfly costs $125. Same upside profit potential ($875 vs similar on a put), but $125 at risk vs $500. On a $10K account where you are learning, the $375 difference in risk matters.

**Action:** Enter Monday April 7 between 10:00-10:30 AM ET. Set the four price alerts. Manage with the exit rules above. Do not overthink it -- the structure does the work.
