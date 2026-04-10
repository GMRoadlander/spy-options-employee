# Position: SPY Put Calendar Spread -- "Gap Fill Theta Exploit"

**Date:** 2026-04-06
**Setup:** SPX ~6783, SPY ~678. Gap fill target ~6610 SPX / ~661 SPY. VIX ~20 and softening. $10K account.
**Thesis:** Near-term puts decay rapidly while SPY consolidates above the gap; longer-term put retains value for the eventual fill.

---

## The Position

**Action:** Sell SPY 670P Apr 17 (11 DTE) / Buy SPY 670P May 1 (25 DTE)
**Contracts:** 2 calendars
**Estimated net debit:** ~$1.40-1.80 per spread ($280-360 total for 2 contracts)
**Max loss:** Net debit paid ($280-360)
**Max profit:** ~$300-500 per spread at near-term expiry if SPY pins near 670 (estimated ~2.5x-3x on debit)

---

## Strike Selection: 670, Not 678 or 661

The strike is the single most important decision in a calendar spread. Here is why 670 and not the alternatives:

**Why not ATM at 678?** A calendar spread's max profit zone is centered on the strike. If the thesis is correct -- SPY drifts lower toward the gap fill -- an ATM strike means max profit only if SPY goes nowhere. That contradicts the directional thesis. Placing the strike below current price turns the calendar into a mildly directional play: you profit if SPY drifts toward the strike over the near-term expiry window, then continues lower through the far-term window.

**Why not at the gap fill target 661?** A strike at 661 is ~2.5% below current price. Both legs would be deep OTM with minimal extrinsic value, which defeats the purpose. Calendar spreads exploit the differential in extrinsic (theta) decay between two expirations. Deep OTM options have almost no extrinsic to harvest. The near-term 661P would cost almost nothing, the far-term 661P would cost slightly more than nothing, and the spread would be so cheap it offers no meaningful profit on a theta play.

**Why 670?** It sits ~1.2% below current price -- close enough that both legs carry significant extrinsic value, but far enough OTM that the near-term put decays rapidly while the far-term retains time premium. 670 is also a round number that tends to attract option open interest, which helps pin behavior near expiry. If SPY grinds toward 670 over the next 11 days, the near-term put accelerates into peak theta decay territory while the far-term still has 14 days of life and resists collapse.

---

## Expiry Selection: Apr 17 / May 1

**Near-term (sold): Apr 17 -- 11 DTE at entry.** This is a Friday expiry in the peak theta decay zone (7-14 DTE is where daily theta accelerates non-linearly). By Apr 13-14, this leg enters terminal decay -- losing value rapidly even if SPY is near the strike. That is what you want to sell.

**Far-term (bought): May 1 -- 25 DTE at entry.** After the near-term expires, this leg retains ~14 DTE of time value. That is still in the gradual decay zone, not the cliff. The 14-day gap between expirations is the minimum necessary to generate meaningful theta differential. Wider gaps (e.g., Apr 17 / May 15) cost more but retain more value post-near-term-expiry; narrower gaps (e.g., Apr 17 / Apr 24) collapse the theta advantage into noise.

**Why not Apr 11 for the short leg?** Only 5 DTE at entry. The theta is violent, but so is the gamma. If SPY makes a 1% move in either direction, the short leg's value swings wildly and the calendar spread's P&L becomes unstable. 11 DTE gives the short leg enough time to decay predictably while keeping gamma manageable.

---

## How This Makes Money (And How It Dies)

### Ideal Scenario (Max Profit)
1. SPY drifts from 678 toward 670-672 over the next 10 days.
2. VIX stays flat or drops slightly (no vol spike that inflates the near-term leg).
3. By Apr 17, SPY is near 670. The short 670P Apr 17 expires roughly ATM with near-zero extrinsic value.
4. The long 670P May 1 still has ~14 DTE and retains $2.50-3.50 of extrinsic value.
5. Close the long leg for $2.50-3.50. Net profit: $1.10-2.10 per spread after subtracting the ~$1.60 debit.
6. After closing, SPY continues lower to fill the 661 gap -- but that is no longer your position. You are already out.

### Good Scenario (Partial Profit)
SPY drifts to 673-675. Near-term put expires with minimal value, far-term retains some extrinsic. Close for a modest profit of $0.30-0.80 per spread.

### Break-Even Scenario
SPY holds 678 or bounces to 682. Near-term put expires worthless (good -- you sold it), but the far-term put also loses value because it is further OTM. The far-term leg is worth roughly the debit paid. Exit flat.

### Loss Scenarios

**SPY rallies to 685+:** Both puts lose most extrinsic value, but the far-term loses more in dollar terms because it had more to begin with. The spread collapses toward zero. Max loss = full debit ($280-360).

**SPY crashes to 660 quickly (gap fills immediately):** This is the counter-intuitive killer. Both puts go deep ITM. When both legs are deep ITM, extrinsic value in both approaches zero and the spread value converges to zero regardless of expiration difference. A fast, violent move through the strike destroys the calendar spread even though the directional thesis was correct. Calendar spreads need the move to happen on schedule, not early. A gap-down Monday to 665 could turn a max-profit setup into a loss.

**VIX spikes to 30+:** Higher IV inflates the near-term leg disproportionately (near-term vega increases in high-vol regimes). The short leg gains value faster than the long leg, compressing the spread. This is a vega risk unique to calendars -- you are short near-term vega and long far-term vega, but the ratio shifts against you in a vol explosion.

---

## Risk Management

**Position size:** 2 contracts at ~$1.60 = $320 max risk. That is 3.2% of a $10K account. Slightly above the 1-2% rule from review 15, but acceptable because the max loss is absolutely defined at the debit. No scenario exists where you lose more than $360.

**Stop-loss:** If the spread value drops to $0.80 (50% of debit), close both legs. Do not hold to zero hoping for a reversal. A 50% loss means SPY has moved decisively away from the strike and the theta thesis is broken.

**Profit target:** Close when the spread reaches $3.00-3.50 (roughly 2x the debit). Do not hold through near-term expiry hoping for the last 10% of profit. Gamma risk into expiry makes the last day unpredictable.

**Time stop:** If by Apr 14 (3 days before near-term expiry) the spread is not profitable, close it. Holding a losing calendar into the last 48 hours is negative expectancy -- gamma takes over and the position becomes a coin flip.

---

## Entry Timing

**When:** Monday Apr 7, 10:00-10:30 AM ET, after the opening range establishes.

**Why not Friday close?** Unlike the directional put spread in review 14, a calendar spread does not benefit from minimizing carry time. You want the near-term leg to start decaying immediately. Every day the near-term put decays faster than the far-term put is a day the spread gains value. Entering Monday morning gives you a full 10 trading days of theta differential working in your favor.

**Why not Monday open at 9:30?** The first 15-30 minutes have inflated spreads and erratic pricing as market makers adjust from weekend positions. The calendar spread's two legs may be mispriced relative to each other, resulting in an artificially wide debit. Wait for the opening range to settle, then enter on a limit order at or below the mid-price.

**Limit order:** Place the calendar at $1.50 or better. If the market does not fill at $1.50, walk up to $1.60 in $0.05 increments. Do not pay more than $1.80 -- the risk/reward degrades above that entry.

---

## Why a Calendar Spread vs. Other Structures

**vs. Put debit spread (review 11):** A vertical put spread needs the move to happen before expiry. If SPY takes 15 days to reach 661 instead of 10, the vertical expires worthless even though the thesis was correct. The calendar is more forgiving on timing -- the near-term leg expires, you keep the far-term, and you still own the thesis.

**vs. Long put:** A naked long put costs more and faces full theta decay every day. The calendar's short leg subsidizes the long leg's theta, reducing your daily carry cost. If SPY consolidates near the strike for a week, the long put bleeds; the calendar accumulates.

**vs. Short call spread (review 13):** The call spread bets SPY stays below a level -- it does not profit from SPY moving to a specific target. If the thesis is "SPY moves to 670, then 661," a bearish credit spread has max profit if SPY stays at 678 or above -- which contradicts the thesis.

**vs. Straddle (review 12):** A straddle costs $12+ and needs a massive move to break even. The calendar costs $1.60 and profits from controlled, moderate movement toward the strike. The straddle is a vol bet; the calendar is a time-decay bet with a directional lean.

**The calendar's unique edge in this setup:** VIX at ~20 and declining means implied vol is moderate but not cheap. Selling near-term premium captures the vol risk premium (implied > realized ~85% of the time, per review 12) while the long-term leg retains value in a stable vol environment. You are selling expensive time decay and buying cheaper time decay. If VIX drops further, the near-term leg deflates faster -- which is profit for you.

---

## The Adversarial Questions This Position Must Survive

**"What if the gap never fills?"** Then the far-term put expires worthless after the near-term already expired worthless, and you lose the debit. That is why max loss is $320-360, not $3,000. The position is sized for the thesis to be wrong.

**"What if gap fills Monday?"** The calendar gets crushed by the move happening too fast. Both legs go ITM, extrinsic collapses, spread value goes to near-zero. This is the scenario where you wish you had bought a vertical put spread instead. Accept this as a known weakness -- calendars are time-structure bets, not crash bets.

**"Why not wait for confirmation of the move before entering?"** Because if SPY is already at 670 when you enter, the near-term put is ATM and expensive. The calendar's debit doubles and the risk/reward inverts. The edge comes from entering while SPY is still above the strike and the near-term put is OTM with high theta decay rate relative to its price.

**"Is 2 contracts enough to matter?"** On a $10K account, yes. Max profit of $600-1,000 is a 6-10% account gain. Max loss of $320-360 is survivable. The goal is not to get rich on one trade -- it is to execute a structured thesis with defined risk and learn whether calendar spreads are a repeatable edge for this account.

---

## Execution Checklist

- [ ] Monday Apr 7, 9:45 AM: Check SPY pre-market. If gapping down below 672, DO NOT ENTER -- the strike is already breached and the calendar thesis is broken. Consider a vertical put spread instead.
- [ ] Monday Apr 7, 10:00-10:30 AM: Place limit order for 2x SPY 670P calendar (sell Apr 17 / buy May 1) at $1.50.
- [ ] If not filled by 10:30, walk to $1.55, then $1.60 at 10:45. Abandon above $1.80.
- [ ] Set alert: SPY touches 670 (near-term put going ATM -- approaching max profit zone).
- [ ] Set alert: SPY touches 685 (rally killing the thesis -- evaluate early exit).
- [ ] Daily check: Monitor spread value. If below $0.80, close.
- [ ] Apr 14 (Tuesday): Time stop. If not profitable, close both legs.
- [ ] Apr 16-17: If profitable, close long leg before 2:00 PM on Apr 17 to avoid gamma roulette into close.
- [ ] Post-trade: Log entry price, exit price, P&L, and whether SPY actually reached 661. This data matters more than the P&L.
