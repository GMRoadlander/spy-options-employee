# Position 02: Conservative Gap-Fill Put Debit Spread

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783)
**Thesis:** US-Iran ceasefire gap from ~661 to ~678 fills within 5-7 trading days. Ceasefire is fragile, macro catalysts (PCE Thu, CPI Fri) provide downside triggers.
**Account:** $10,000 | **Risk budget:** 2% = $200

---

## POSITION: Gap-Fill Put Debit Spread

| Field | Detail |
|---|---|
| **Action** | **BUY 1x SPY Apr 17 $676 Put / SELL 1x SPY Apr 17 $663 Put** |
| **Entry** | **Monday Apr 7, between 10:00-10:30 AM ET** (after opening range settles, avoid first 30 min chop) |
| **Expiry** | Apr 17, 2026 (11 DTE at entry) |
| **Width** | $13.00 (676 - 663 = 13 points) |
| **Estimated debit** | ~$4.80 per spread ($480 per contract) |
| **Spreads** | **1 contract** |
| **Max loss** | **$480** (debit paid if SPY closes above $676 at expiry) |
| **Max profit** | **$820** ($1,300 width - $480 debit) if SPY at or below $663 at expiry |
| **Breakeven** | SPY at **$671.20** (676 - 4.80) |
| **Reward:Risk** | 1.71:1 |

---

## IMPORTANT: Account Risk Recalibration

The strict 2% rule ($200) would allow only a fractional contract, which is not executable. The two viable options:

### Option A -- Single Spread (RECOMMENDED)
- 1 spread at ~$4.80 = $480 max risk = **4.8% of account**
- This exceeds the 2% target but is the minimum executable unit
- Mitigated by the hard stop-loss rule below (cuts actual risk to ~$200)

### Option B -- Narrower Spread to Hit 2%
- BUY $674 Put / SELL $670 Put ($4 wide) for ~$1.80 debit
- 1 spread = $180 risk (under 2%)
- Problem: breakeven at $672.20, needs a bigger move just to profit, narrow width kills reward:risk, and you are paying more per dollar of width due to bid-ask on tighter strikes
- **Not recommended** -- worse probability of profit, worse reward:risk

**Recommendation: Use Option A with the stop-loss discipline below to keep realized risk near $200.**

---

## Entry Rules

1. **Wait for 10:00 AM ET.** Do not enter in the first 30 minutes. Monday opens after a gap-up weekend are messy -- let the opening auction and short-covering finish.
2. **Confirm SPY is below $679.** If it gaps up further on ceasefire enthusiasm above $679, the thesis is weakened -- stand aside.
3. **Check VIX is still above 18.** If VIX has crashed below 18, put premiums are cheaper but the market is saying "risk off is over" -- thesis is weakened.
4. **Use a limit order at the mid-price.** Do not pay the ask. SPY options are liquid -- you should get filled at or near mid within a few minutes.

## Exit Rules

### Take Profit (Scaled)
| SPY Level | Action | Reasoning |
|---|---|---|
| **$668** | Close 100% of position | ~70% of max profit captured, don't get greedy near the gap-fill target |
| **$663 or below** | Let expire or close for max profit | Full gap fill achieved |

### Stop Loss (Hard Rule -- Non-Negotiable)
- **Close the entire position if the spread value drops to $2.80 or below** (from $4.80 entry)
- This is a $200 loss per spread, which hits the 2% account risk target
- **Do not "give it more room."** You are a new trader. Discipline > conviction.
- Translate: if SPY rallies to ~$680+ and stays there by Tuesday close, the spread will likely be at or below $2.80. Exit.

### Time Stop
- **If by Wednesday Apr 8 close SPY has not broken below $675**, close the position regardless of P&L. The thesis required movement within the first half of the week, before PCE/CPI vol reprices the spread against you.
- Rationale: theta decay accelerates after day 3-4 on an 11 DTE spread. If the move hasn't started, you are paying rent on a thesis that isn't working.

---

## Strike Justification

### Why $676 long put (not $678 or $675)?
- SPY at ~$678. Buying the $678 ATM put costs more (~$6.50+) and pushes the debit too high for a $10K account
- $676 is 2 points OTM -- close enough to have ~0.42 delta (moves meaningfully with SPY), cheap enough to keep the debit under $5.00
- $676 sits just below Friday's close, meaning any red day immediately puts this leg ITM
- Avoids the $675 round number where market makers cluster, slightly better fill

### Why $663 short put (not $660 or $665)?
- $663 corresponds to the **gap-fill zone**: SPY gapped from ~$661 on the ceasefire announcement. The first support above $661 is the $662-664 area (pre-gap consolidation high)
- Selling the $663 put means you collect max profit when SPY reaches the gap-fill area -- you don't need a full fill to $661
- $665 would narrow the spread too much (only $11 wide, worse reward:risk)
- $660 would widen it to $16, pushing the debit to ~$6.50+ (too expensive)
- $663 avoids the $660 round number where significant open interest and pinning risk exists

### Why $13 wide?
- Wide enough to capture the bulk of the gap-fill move ($678 to $663 = $15, spread covers $13 of it)
- The last $2 of the move (663 to 661) is the hardest part -- gaps often fill to 90-95%, not 100%. The $663 short strike gives you credit for a "close enough" fill

---

## Expiry Justification

### Why Apr 17 (11 DTE) -- not weeklies or monthlies?

| Expiry | DTE | Pro | Con | Verdict |
|---|---|---|---|---|
| Apr 11 (weekly) | 4 DTE | Cheapest debit (~$3.50) | Theta destroys you if the move takes 3+ days. PCE is Thu, CPI Fri -- you expire the same day as CPI. No room for error. | **Too aggressive for a new trader** |
| Apr 17 (semi-monthly) | 11 DTE | Survives both PCE and CPI. Gives 7 full trading days for the gap to fill. Theta is moderate, not punishing. | Costs more than the weekly | **Best balance of cost and time** |
| May 15 (monthly) | 28 DTE | Maximum time for thesis to play out | Debit ~$7.00+, max loss too high for account size. Paying for time you don't believe you need. | **Overpaying for insurance** |

The Apr 17 expiry lets you hold through both data releases (PCE Thursday, CPI Friday) which are the most likely catalysts for the gap fill. If neither triggers the move, you still have 4 more trading days as a buffer.

---

## Risk Factors

| Risk | Impact | Mitigation |
|---|---|---|
| Ceasefire holds + market rallies further | Spread goes to zero | Hard stop at $2.80 caps loss at ~$200 |
| VIX crush after ceasefire stability | Puts lose value even without SPY move | Apr 17 expiry gives time for a catalyst (PCE/CPI) to re-inject vol |
| PCE/CPI come in cool (dovish) | Market rallies on rate cut hopes | Time stop: exit by Wed if no move. Don't hold into data hoping for a miss |
| Gap fills partially to $668 then bounces | You miss max profit | Take-profit at $668 captures ~70% of max -- don't hold for perfection |
| SPY opens Monday with another gap up | Entry is worse or thesis is dead | Entry rule: do not enter if SPY opens above $679 |

---

## Position Sizing Rationale

With a $10,000 account and a $480 max loss (4.8%):
- This is above the ideal 2% but is the minimum executable position
- The hard stop at $200 loss (2%) makes the **realized** risk 2%
- You must honor the stop. If you cannot commit to the stop, **do not take this trade**
- After this trade (win or lose), take no other positions until you review the outcome

---

## Post-Entry Checklist

- [ ] Set alert at SPY $675 (thesis confirmation)
- [ ] Set alert at SPY $668 (take profit zone)
- [ ] Set alert at SPY $680 (danger zone)
- [ ] Set GTC limit sell at $2.80 on the spread (stop loss)
- [ ] Calendar reminder: Wednesday 3:45 PM ET -- evaluate time stop
- [ ] Do NOT check the position more than 3 times per day. Overmonitoring leads to emotional exits.
