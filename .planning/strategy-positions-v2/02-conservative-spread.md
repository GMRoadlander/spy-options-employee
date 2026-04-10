# Position 02 v2: Conservative Gap-Fill Put Debit Spread

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783)
**Thesis:** US-Iran ceasefire gap from ~661 to ~678 fills within 7-10 trading days. Ceasefire is structurally unenforceable -- Iran has 31 separate armed services answering only to a Supreme Leader who is in a coma. Some commanders will honor the pause, others will not. Only 3 ships have transited Hormuz out of 800+ trapped. This is not a peace deal; it is a headline with no enforcement mechanism.
**Account:** $10,000 | **Risk budget:** 2% = $200
**v2 changes from v1:** Entry moved to AFTER PCE Thursday IV crush. Strikes justified by gap levels, not round numbers or Fibonacci. Expiry extended to give thesis room. "Monday flush" timing assumption removed -- the move could come any day.

---

## POSITION: Gap-Fill Put Debit Spread (Post-PCE Entry)

| Field | Detail |
|---|---|
| **Action** | **BUY 1x SPY Apr 25 $674 Put / SELL 1x SPY Apr 25 $662 Put** |
| **Entry** | **Thursday Apr 10, between 10:00-10:30 AM ET** (after PCE data release at 8:30 AM, let the reaction settle, buy into the IV crush) |
| **Expiry** | Apr 25, 2026 (15 DTE at entry -- 11 trading days) |
| **Width** | $12.00 (674 - 662 = 12 points) |
| **Estimated debit** | ~$3.80 per spread ($380 per contract) -- cheaper than v1 because post-PCE IV crush deflates put premiums by 10-15% |
| **Spreads** | **1 contract** |
| **Max loss** | **$380** (debit paid if SPY closes above $674 at expiry) |
| **Max profit** | **$820** ($1,200 width - $380 debit) if SPY at or below $662 at expiry |
| **Breakeven** | SPY at **$670.20** (674 - 3.80) |
| **Reward:Risk** | 2.16:1 (max) | 4.1:1 (against $200 realized risk with stop) |

---

## Why Enter AFTER PCE, Not Monday

This is the single biggest change from v1 and it comes directly from swarm review. The reasoning:

1. **IV crush is free money you leave on the table by entering early.** PCE drops Thursday 8:30 AM. Regardless of the number, the known-event premium bleeds out of options within the first hour. SPY put premiums will be 10-15% cheaper Thursday morning than Monday morning, all else equal. You are buying the same thesis for less.

2. **Monday is NOT a reliable catalyst day.** v1 assumed a "Monday flush" where the gap fill begins immediately. The swarm correctly flagged this as anchoring bias. The ceasefire could hold for 2-3 days before a Houthi commander defects. CPI Friday could be the trigger. An Iranian military statement could come Wednesday night. By waiting until Thursday, you observe 3 full sessions of price action and enter with more information, not less.

3. **You still catch CPI Friday.** Entering Thursday morning means you hold through CPI (Friday Apr 11). If March CPI is hot, that is the most likely single-day catalyst for a gap fill. Core CPI strips energy (oil at $94 does not flow through to core), so a hot print reflects sticky services inflation -- dovish hopes die and the rally fades.

4. **15 DTE at entry gives you the full next week.** If CPI is a non-event and SPY chops, you still have 8 trading days (Apr 14-25) for the structural ceasefire cracks to appear. v1's Apr 17 expiry would leave only 5 trading days after CPI. This extra time is cheap insurance against the thesis being right but slow.

**The tradeoff:** You sacrifice 3 days of potential movement (Mon-Wed). If the gap fill begins Monday morning, you miss the easy entry. That is acceptable. Conservative means accepting lower upside for higher probability. If SPY is already at 670 by Thursday, you skip the trade -- the easy money moved without you. There is always another trade.

---

## Entry Rules

1. **Wait for PCE release (8:30 AM ET Thursday Apr 10).** Do not enter before the number.
2. **Enter between 10:00-10:30 AM ET.** The PCE reaction takes 60-90 minutes to fully price in. The first 30 minutes after data are erratic. By 10:00 AM, IV has crushed, directional flow has stabilized, and spreads are tight.
3. **Confirm SPY is between $670 and $682.** 
   - If SPY has already broken below $670, skip the trade -- the move is in progress and you are chasing.
   - If SPY is above $682, the ceasefire rally is extending and your thesis is weakened -- stand aside.
4. **Confirm VIX is above 17.** If VIX has collapsed below 17, the market is saying "risk off is over" and put premiums are so cheap the spread has poor reward:risk. Your thesis needs vol to work.
5. **Use a limit order at the mid-price.** SPY options are among the most liquid in the world. You should get filled at or near mid within 5 minutes. If the market is moving fast and the mid is above $4.20, walk away -- the spread is too expensive.
6. **Maximum debit: $4.20.** Do not overpay. If PCE causes a spike in vol (hot number) and puts are temporarily inflated, wait until 11:00 AM or skip to Friday morning post-CPI entry (backup plan below).

### Backup Entry: Friday Apr 11, 10:00-10:30 AM ET (Post-CPI)

If Thursday entry is skipped (SPY outside range, VIX too low, spread too expensive), you have one more shot Friday morning after CPI. Same rules apply: wait 90 minutes after data, confirm SPY 670-682, confirm VIX > 17. The spread will be on a 14 DTE expiry at that point. If Friday also fails entry criteria, the trade is dead for this cycle. Do not force it.

---

## Strike Justification

### Why $674 long put (not $676 or $670)?

- **$674 is the pre-gap consolidation high.** Before the ceasefire gap, SPY traded in a range with the upper boundary near $674-675 (SPX ~6740-6750). This is the level SPY broke away from on the gap up. It is the first meaningful resistance-turned-support level below current price.
- **$676 (v1 strike) was too close to spot.** At SPY ~678, buying a $676 put is nearly ATM -- expensive, and paying for the first $2 of move that might just be noise. Moving to $674 saves ~$0.80 in premium while still having a ~0.38-0.40 delta (moves meaningfully with SPY).
- **$674 avoids the $675 round number.** Market makers cluster at $675. Placing the strike $1 below avoids pin risk and gets slightly better fills.
- **NOT $670** -- too far OTM. At $670 the delta drops to ~0.28 and the spread requires a $8 move just to get the long leg ATM. That is asking too much before the thesis even starts paying.

### Why $662 short put (not $660 or $665)?

- **$662 is the gap-fill zone.** SPY gapped from ~$661 on the ceasefire announcement. The pre-gap close was $661.XX. The first support above the gap origin is $662 -- the last price where sellers and buyers exchanged hands before the news.
- **Selling the $662 put means you collect max profit when SPY returns to the gap origin.** You do not need a fill to $659 or $655. The thesis is "gap fills" -- $662 IS the fill.
- **$665 would narrow the spread to $9 wide.** Worse reward:risk ($880 max profit vs $820 at similar debit). More importantly, $665 is above the gap origin -- you are capping yourself short of the thesis target.
- **$660 would widen the spread to $14.** The debit rises to ~$4.60+, pushing max loss uncomfortably high. And the last $2 of a gap fill (from 662 to 660) is the hardest part -- gaps fill 90-95%, not 100%. You would be paying for $2 of width that has low probability of being reached.
- **$663 (v1 short strike) was fine but $662 better aligns with the actual pre-gap close level.** The extra $1 of width costs ~$0.20 more in debit but adds $0.80 of max profit. Positive expected value trade.

### Why $12 wide?

- The gap is $17 (from SPY ~661 to ~678). The spread covers $12 of it -- the middle portion where probability of the move reaching is highest. You are not paying for the first $4 (spot to long strike) or the last $1 (short strike to gap origin). You are capturing the meat of the move.
- A $12-wide spread at ~$3.80 debit gives 2.16:1 reward:risk. This is the sweet spot between width and cost for a $10K account.

---

## Expiry Justification

### Why Apr 25 (15 DTE at entry) -- not weeklies or the Apr 17 monthly?

| Expiry | DTE at Entry (Thu) | Pro | Con | Verdict |
|---|---|---|---|---|
| Apr 11 (weekly) | 1 DTE | Cheapest debit (~$1.80). Expires same day as CPI -- pure binary bet. | You are entering Thursday and expiring Friday. This is not a trade, it is a lottery ticket. Zero room for error. One sideways day and you lose 100%. | **Gambling, not trading** |
| Apr 17 (semi-monthly) | 7 DTE | Moderate cost. Gives next week for thesis to develop. | Only 5 trading days after CPI for the ceasefire cracks to show. If the move takes 8-10 days, you expire before it happens. v1 used this expiry when entering Monday (11 DTE), but entering Thursday means only 7 DTE -- too tight. | **Adequate but thin margin** |
| Apr 25 (next weekly) | 15 DTE | Survives CPI catalyst AND gives a full second week for the structural ceasefire failure to manifest. Theta is gentle -- you lose ~$0.15-0.20/day on the spread, not $0.40+. | Costs ~$0.60 more than Apr 17 ($3.80 vs ~$3.20). | **Best balance of time and cost** |
| May 15 (monthly) | 35 DTE | Maximum time for thesis. | Debit ~$5.50+, max loss too high. Paying for 3 extra weeks you do not believe you need. Theta is lower but you are tying up capital for a month. | **Overpaying for insurance** |

The Apr 25 expiry is the critical upgrade from v1. By entering Thursday instead of Monday, you need a later expiry to maintain adequate DTE. 15 DTE at entry means:
- You survive CPI Friday (the most important single catalyst)
- You have 5 full trading days the following week (Apr 14-18) for the structural ceasefire failure thesis
- You still have Apr 21-25 as a buffer if the move is slow
- Theta decay is moderate, not punishing -- the spread loses ~$0.15-0.20/day, giving you genuine staying power

---

## Exit Rules

### Take Profit (Scaled)

| SPY Level | Spread Value | Action | Reasoning |
|---|---|---|---|
| **$668** | ~$5.50-6.00 | **Close 100% of position** | This is ~60-65% of max profit. You have captured the bulk of the move. Do not hold for the last $2-3 of profit -- that requires SPY to travel through the heaviest support zone ($665-662). Take the money. |
| **$662 or below** | ~$10.00-12.00 | Let expire or close for max profit | Full gap fill achieved. If reached before expiry, close immediately -- do not hold to expiry for the last $0.50. Assignment risk is not worth it. |

### Stop Loss (Hard Rule -- Non-Negotiable)

- **Close the entire position if the spread value drops to $1.80 or below** (from $3.80 entry).
- This is a **$200 loss** per spread, which hits the 2% account risk target exactly.
- **The $1.80 level corresponds to SPY sustaining above ~$681-682** while time passes. If SPY is at 682 and holding, the ceasefire rally is real and your thesis is wrong. Accept it.
- **Do not "give it more room."** You are a new trader. The stop exists to protect you from yourself. If the thesis is right, SPY will not be at 682 when your stop triggers. If the stop triggers, the thesis was wrong. That is not a failure -- it is risk management working as designed.
- **Execution:** Set a GTC limit sell at $1.80 on the spread immediately after entry. Do not rely on mental stops. Mental stops do not exist when SPY is moving against you and you are staring at the screen.

### Time Stop

- **If by Wednesday Apr 15 close SPY has not broken below $674** (the long strike), close the position regardless of P&L.
- At this point you have held for 3 trading days post-entry and 7 DTE remain. The spread will still have ~$2.00-2.80 of value from time premium. You will lose $100-180, well within the risk budget.
- **Rationale:** The thesis says the gap fills within 7-10 days of the gap (Apr 7-17). If by day 7 (Apr 15) SPY has not even breached $674, the structural ceasefire failure is taking longer than expected or is not happening. You are not positioned for a 3-week grind lower -- you are positioned for a catalyst-driven fill. Exit and reassess.

---

## Iran Structural Analysis: Why the Ceasefire Cracks

This is not geopolitical speculation. It is structural observation.

Iran's military is not a unified command. It consists of 31 separate armed services:
- **IRGC (Islamic Revolutionary Guard Corps)** -- multiple branches including the IRGC Navy, which controls Hormuz directly
- **Artesh (regular military)** -- separate chain of command from IRGC
- **Basij** -- militia forces with independent operational capacity
- **Quds Force** -- external operations, funds Houthis directly
- **Various provincial and specialized commands**

All 31 services take orders from the Supreme Leader. The Supreme Leader is in a coma. There is no functioning central command authority that can enforce a ceasefire across all 31 services.

What this means in practice: the ceasefire "agreement" was signed by political leadership (the president's office), which does not have operational control over IRGC Navy commanders in the Strait of Hormuz or Quds Force handlers managing Houthi operations. A regional IRGC Navy commander who has been blockading ships for months is not going to stand down because a politician in Tehran said so -- especially when the politician has no enforcement mechanism.

**The market is pricing a ceasefire as if Iran were France.** A country with unified civilian control of a single military. It is not. It is 31 separate militaries with a comatose commander-in-chief. The gap-up is built on a structural misunderstanding that the market will correct as ships continue to be turned away, Houthi attacks resume, or an IRGC commander makes a public statement contradicting the ceasefire.

**The only question is when, not if.** This trade gives you 15 days to be right about the "when."

---

## Risk Factors

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Ceasefire holds + market rallies to SPX 6900+ | 20% | Spread goes to zero | Hard stop at $1.80 caps loss at $200. You exit long before zero. |
| New ceasefire developments strengthen the deal (hostage release, ship transit acceleration) | 15% | SPY pushes to $685+, stop triggers | Stop loss. Accept the $200 loss. The thesis was wrong and you survived. |
| VIX crush below 17 kills put premiums | 10% | Spread value erodes even without SPY moving up | Entry rule: do not enter if VIX < 17. If VIX crashes after entry, the time stop on Wednesday catches this. |
| PCE/CPI both come in cool (dovish) | 25% | Market rallies on rate cut hopes, SPY pushes toward $683-685 | This is the most likely path to the stop loss. The time stop and hard stop both protect you. Note: cool CPI could also mean "nothing changes" and SPY drifts -- not necessarily a rally. |
| Gap fills partially to $668 then bounces hard | 15% | You miss the take-profit window and give back gains | Take-profit at $668 is aggressive -- you close at first touch, not on a retest. If SPY hits $668 and you have not closed, you have violated the exit rules. |
| Ceasefire actually works -- Supreme Leader's successor emerges, unifies command | 5% | Full thesis invalidation, prolonged rally | Lowest probability. Would require weeks of institutional transition. Your 15 DTE expiry means you are out long before this develops. |
| SPY gaps down Monday before your Thursday entry | 10% | You miss the move; spread is too expensive by Thursday | Accept it. There is always another trade. Do NOT chase by entering Thursday at inflated prices. The max debit rule ($4.20) enforces this discipline. |

---

## Position Sizing Rationale

With a $10,000 account and a $380 max loss (3.8%):
- This exceeds the 2% target but is the minimum executable unit for a meaningful spread
- The hard stop at $200 loss (spread at $1.80) makes the **realized** risk 2% of the account
- v2 is cheaper than v1 ($380 vs $480) because post-PCE IV crush reduces the debit
- The better reward:risk (2.16:1 vs 1.71:1) and longer DTE (15 vs 11) both compensate for the higher nominal risk
- **You must honor the stop.** If you cannot commit to closing at $1.80, do not take this trade. Write it on a sticky note. Put it on your monitor. The stop is the trade.

---

## Post-Entry Checklist

- [ ] Set GTC limit sell at $1.80 on the spread immediately after fill (hard stop = $200 loss)
- [ ] Set alert at SPY $674 (long strike -- thesis confirmation, your put is going ITM)
- [ ] Set alert at SPY $668 (take profit zone -- close position)
- [ ] Set alert at SPY $662 (full gap fill -- max profit zone)
- [ ] Set alert at SPY $682 (danger zone -- stop likely to trigger soon)
- [ ] Calendar reminder: Wednesday Apr 15, 3:45 PM ET -- evaluate time stop
- [ ] Calendar reminder: Friday Apr 25, 10:00 AM ET -- mandatory close if still holding
- [ ] Do NOT check the position more than 3 times per day: 10:00 AM, 1:00 PM, 3:45 PM
- [ ] Do NOT discuss the position in trading forums or Discord chats seeking validation. The trade is placed. External opinions do not change the math.

---

## What Changed from v1 and Why

| Element | v1 | v2 | Reason |
|---|---|---|---|
| **Entry day** | Monday Apr 7 | Thursday Apr 10 (post-PCE) | Buy into IV crush. 10-15% cheaper premiums. More information. |
| **Long strike** | $676 | $674 | Justified by pre-gap consolidation high, not proximity to spot. Saves ~$0.80 in premium. |
| **Short strike** | $663 | $662 | Aligned to actual pre-gap close level, not rounded. Extra $1 width for $0.20 cost. |
| **Expiry** | Apr 17 (11 DTE) | Apr 25 (15 DTE) | Later entry requires later expiry. 15 DTE gives a full second week for thesis. |
| **Estimated debit** | $4.80 | $3.80 | IV crush + slightly more OTM long strike. |
| **R:R** | 1.71:1 | 2.16:1 | Cheaper entry on similar width. |
| **Stop level** | $2.80 | $1.80 | Same $200 realized loss, but calculated from lower entry cost. |
| **Time stop** | Wed Apr 8 | Wed Apr 15 | Adjusted for later entry. Same logic: 3 trading days post-entry. |
| **"Monday flush" assumption** | Implicit | Removed | Swarm review: the move could come any day. Do not anchor to a specific day. |
| **Fibonacci references** | None explicit, but $676 was near a fib level | Removed entirely | Swarm review: justify with gap levels, not technical overlays. |
