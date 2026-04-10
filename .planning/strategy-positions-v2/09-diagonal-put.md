# Position 09: Diagonal Put Spread — Gap Fill on Your Schedule

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783)
**Spot:** SPY ~$678
**VIX:** ~20
**Thesis:** US-Iran ceasefire is unenforceable (31 armed services, Supreme Leader in coma). The gap from ~$661 to ~$678 fills — but it could be this week, next week, or three weeks from now as the ceasefire slowly unravels. Timing is the unknown. The direction is not.
**Account:** $10,000 | **Max risk:** 3% = $300

---

## Why a Diagonal, Not a Vertical

The problem statement is simple: if you buy an Apr 11 $673/$663 put spread and the gap fills on April 21, you lose $320 and miss the entire move. You were right on direction and wrong on timing, which is the most frustrating way to lose money in options.

A diagonal decouples direction from timing. You buy a long-dated put that survives for 3-4 weeks. You sell a short-dated put against it every week to generate income. If the gap fills in week 1, you profit. If it fills in week 3, you still profit — and you collected 2 weeks of income along the way. If it never fills, the income from selling weekly puts can partially or fully offset the cost of the long put.

The tradeoff: you are giving up simplicity and a fixed max-profit structure in exchange for patience and cash flow. This is a trade that rewards active weekly management.

---

## POSITION: Diagonal Put Spread

| Field | Detail |
|---|---|
| **Long leg** | **BUY 1x SPY May 2 $674 Put** |
| **Short leg (week 1)** | **SELL 1x SPY Apr 11 $670 Put** |
| **Entry** | Monday Apr 7, 10:00-10:30 AM ET |
| **Long leg expiry** | May 2, 2026 (25 DTE at entry) |
| **Short leg expiry** | Apr 11, 2026 (4 DTE at entry) |
| **Estimated long put cost** | ~$6.40 per contract |
| **Estimated short put credit** | ~$2.70 per contract |
| **Net debit** | ~$3.70 per diagonal ($370 for 1x) |
| **Max loss** | ~$370 (net debit if SPY stays above $674 through May 2 and all short legs expire worthless or are rolled for less than total debit) |
| **Account risk** | 3.7% — slightly above 3% target, but realistic max loss is lower after rolling (see below) |

---

## Strike Selection: Why $674 Long / $670 Short

### Long Leg: May 2 $674 Put

**Why $674 and not $672, $676, or $678?**

- **$678 (ATM):** Costs ~$8.80. Net debit after selling the short = ~$6.10. That is $610 on a $10K account — 6.1% risk, double the budget. No.
- **$676 (2 OTM):** Costs ~$7.50. Net debit = ~$4.80. Still $480 risk (4.8%). Tight.
- **$674 (4 OTM):** Costs ~$6.40. Net debit = ~$3.70. Risk is $370 (3.7%). Close to budget, and the rolling income will pull effective risk below $300 after 1-2 weeks.
- **$672 (6 OTM):** Costs ~$5.50. Net debit = ~$2.80. Cheaper, but delta drops to ~0.33. You need SPY to drop $6 before this put starts moving with real conviction. That eats into the gap-fill profit.
- **$670 (8 OTM):** Costs ~$4.70. Delta ~0.28. Too sluggish. By the time SPY reaches 665, this put has gained maybe $6.50 in value — versus $9+ for the $674 put.

**$674 is the best balance of cost, delta (~0.40), and gap-fill profit.** At 4 points OTM, it starts responding meaningfully as soon as SPY drops below 676. Delta of ~0.40 means for every $1 SPY falls, this put gains ~$0.40 — and that accelerates as SPY moves through 674 and the put goes ITM.

### Short Leg: Apr 11 $670 Put

**Why $670 and not $668, $672, or $674?**

- **$674 (same strike as long = calendar spread):** Tempting because you collect maximum premium (~$3.80 for 4 DTE). But if SPY drops to 672, the short is $2 ITM and your long is $2 ITM — you gain nothing from the move. The short put completely neutralizes the long put's directional profit until after the short expires. A calendar spread profits from time decay in a narrow range, not from a directional gap fill. Wrong tool for this thesis.
- **$672 (2 below long):** Credits ~$3.20. Good premium but only a $2 buffer. If SPY dips to 673 on Tuesday (a normal 0.7% down day), the short is already $1 from ATM and gaining delta fast. You are too close to getting whipsawed.
- **$670 (4 below long):** Credits ~$2.70. A $4 buffer between long and short strikes. SPY can drop 1.2% to 670 before the short put is at-the-money. That is one standard day's move at VIX 20 — meaning you can absorb normal volatility without the short leg becoming a problem. And $2.70 in 4-day premium is still substantial (~$0.55/day of decay).
- **$668 (6 below long):** Credits ~$2.10. Safer but you are leaving $0.60/contract on the table per week. Over 3-4 rolls, that is $180-$240 less income. The $670 strike is not materially riskier than $668 given that SPY would need to fall $8 (1.2%) in 4 days to threaten it — and if SPY does that, the gap fill is happening and your long put is printing.

**$670 gives a $4 spread between strikes — enough buffer for normal chop, enough premium to make the roll plan work.**

### Why Not Same-Strike (Calendar)?

This deserves emphasis. A $674/$674 calendar (same strike, different expiry) is a neutral trade. It profits when SPY stays near $674 and time decay difference between the long and short legs works in your favor. But the thesis here is directional — SPY drops $15-17 to fill the gap. A calendar's max profit zone is a narrow band around the strike. A diagonal's profit zone extends downward because the long put gains value while the lower-strike short put gains less value. For a directional thesis with uncertain timing, the diagonal is structurally correct.

---

## Why May 2 for the Long Leg

| Expiry | DTE | Approx Cost | Rolls Possible | Assessment |
|---|---|---|---|---|
| Apr 17 | 10 | ~$4.20 | 1 (just Apr 11) | Barely a diagonal — only one roll before the long is 6 DTE and bleeding theta |
| Apr 25 | 18 | ~$5.30 | 2-3 | Workable but tight. If gap fill takes 3 weeks, you expire too soon |
| **May 2** | **25** | **~$6.40** | **3-4** | **Optimal. Enough runway for 3-4 rolls. Extra week costs ~$1.10 but generates one more roll (~$1.50-2.70 credit)** |
| May 16 | 39 | ~$8.00 | 5-6 | Overpaying. Theta is flat at 39 DTE — first 2 weeks you own this put, it barely decays, which is nice for the long but you are paying $1.60 for time you probably will not need |

**May 2 wins the cost-benefit analysis.** The $1.10 extra over Apr 25 buys you one additional roll cycle that should produce $1.50-2.70 in credit — a net gain of $0.40-1.60 for extending one week.

---

## The Rolling Plan

This is the engine that makes the diagonal work. After each short put expires (or is closed), you sell the next week's put to collect more premium. Each roll reduces the effective cost of the long put.

### Week 1: Apr 7-11

| | |
|---|---|
| **Short leg** | 1x SPY Apr 11 $670P |
| **Credit** | ~$2.70 |
| **DTE** | 4 days |
| **Daily theta** | ~$0.55/day |
| **If SPY > $670 Friday** | Short expires worthless. Keep $270. Cumulative credit: **$270** |
| **If SPY < $670 Friday** | See "Managing an ITM Short" below |
| **Long put status** | 21 DTE remaining, decaying ~$0.10/day. Net theta (short decay minus long decay) = +$0.45/day in your favor |

### Week 2: Apr 14-17 (first roll)

| | |
|---|---|
| **Action** | Monday Apr 14: SELL 1x SPY Apr 17 put |
| **Strike selection** | Sell the put that is 8-10 points below current SPY price, AND at least $2 below the long $674 strike (so $672 or lower). Use the lower of these two constraints |
| **If SPY at ~678 (unchanged)** | Sell Apr 17 $670P again for ~$2.00-2.50 |
| **If SPY at ~674 (thesis starting)** | Sell Apr 17 $666P for ~$2.20-2.80 (IV likely elevated) |
| **If SPY at ~682 (rallied)** | Sell Apr 17 $672P for ~$1.50-2.00 (can move short strike up since SPY moved up) |
| **Expected credit** | $1.50-2.80 depending on SPY and VIX |
| **Cumulative credit target** | **$420-$550** |

### Week 3: Apr 21-25 (second roll)

| | |
|---|---|
| **Action** | Monday Apr 21: SELL 1x SPY Apr 25 put |
| **Strike selection** | Same rules: 8-10 OTM from SPY, minimum $2 below $674 |
| **If SPY at ~678** | Sell Apr 25 $668P for ~$1.50-2.00 |
| **If SPY at ~670 (drifting down)** | Sell Apr 25 $662P for ~$1.80-2.50 (closer to gap target) |
| **Expected credit** | $1.20-2.50 |
| **Cumulative credit target** | **$600-$800** |

### Week 4: Apr 28 - May 1 (final roll, if needed)

| | |
|---|---|
| **Action** | Monday Apr 28: SELL 1x SPY May 1 put |
| **Caution** | Long put expires May 2 — this is the LAST roll. Short expires 1 day before the long |
| **Strike selection** | Sell conservatively — 10-12 OTM. You do not want the short put ITM on May 1 with only 1 day of long put remaining to cover it |
| **If SPY at ~678** | Sell May 1 $666P for ~$1.00-1.50 |
| **If SPY at ~668** | Sell May 1 $658P for ~$1.00-1.80 |
| **Expected credit** | $0.80-1.80 |
| **Cumulative credit target** | **$700-$1,050** |

### Rolling Income Projection Summary

| Rolls Completed | Cumulative Credit (1x) | Net Cost of Position | Effective Risk |
|---|---|---|---|
| 1 (Apr 11 only) | ~$270 | $370 - $270 = $100 | $100 (1.0% of account) |
| 2 (+ Apr 17) | ~$470 | $370 - $470 = -$100 (credit) | $0 — you are playing with house money |
| 3 (+ Apr 25) | ~$650 | $370 - $650 = -$280 | $0 — net credit position |
| 4 (+ May 1) | ~$800 | $370 - $800 = -$430 | $0 — significant net credit |

**After just 2 rolls (by April 17), the cumulative short put credits likely exceed the original net debit.** From that point forward, the long May 2 $674 put is a free asset — every dollar it is worth at any future date is pure profit.

---

## Profit Scenarios

### Scenario A: Gap fills slowly — SPY drifts to $665 by April 22 (IDEAL)

This is the scenario the diagonal is designed for.

- Week 1 short $670P expires worthless (SPY still above 670): +$270
- Week 2 short $668P expires worthless (SPY at ~672): +$220
- Cumulative credits: +$490
- Long May 2 $674P is now $9 ITM (SPY at 665) with 10 DTE: worth ~$10.80
- Close the long put for $1,080
- **Total P&L:** $1,080 - $640 (long cost) + $490 (credits) = **+$930 profit (251% return on initial $370 debit)**

A vertical spread expiring Apr 11 would have been worth $0 at this point because the gap filled 11 days too late.

### Scenario B: Gap fills fast — SPY drops to $663 by April 10 (Thursday)

- Week 1 short $670P is $7 ITM — close for ~$7.50, losing ~$4.80 on this leg ($480 loss)
- Long May 2 $674P is $11 ITM with 22 DTE — worth ~$13.50
- Close everything: $1,350 - $640 (long cost) - $480 (short loss) = **+$230 profit**
- Alternatively: close only the short at -$480, keep the long, and sell a new short at $658P for the following week. This recovers some of the short loss through continued rolling

An Apr 11 vertical would have done better here — maybe +$500-600. This is the one scenario where simplicity wins. You pay for timing flexibility by giving up max profit on the fastest moves.

### Scenario C: No gap fill — SPY chops $675-$682 for 4 weeks

- All 4 short puts expire worthless: ~$800 cumulative credit
- Long May 2 $674P expires May 2, SPY at $678, still $4 OTM — worth ~$0.60 (all time value)
- Close long for $60
- **Total P&L:** $60 - $640 + $800 = **+$220 profit**

You profited from a trade where the thesis was completely wrong. The short put income exceeded the cost of the long put. A vertical spread would have lost its entire debit.

### Scenario D: SPY rallies hard to $695+ (thesis dead wrong)

- Short puts expire worthless each week: ~$800 cumulative credit
- Long May 2 $674P expires worthless: -$640
- **Total P&L with 4 rolls:** -$640 + $800 = **+$160 profit**
- **Total P&L with 3 rolls:** -$640 + $650 = **+$10 (break-even)**
- **Total P&L with only 1 roll (spike in week 1):** -$640 + $270 = **-$370 loss (max loss)**

The diagonal only loses its max debit if SPY rockets higher immediately in week 1 before you collect more than one cycle of short premium. This is the worst case.

### Scenario E: SPY crashes to $640 (overshoot below gap)

- Long $674P is $34 ITM: worth ~$34.20
- Short $670P (wherever the current short strike is) is ~$30 ITM: worth ~$30.30
- Net value of the diagonal at this moment: ~$3.90
- After credits collected: $390 - $370 debit + credits from prior rolls
- **With 2 prior rolls (+$490):** $390 - $370 + $490 = **+$510 profit**
- **With 0 prior rolls (crash in week 1):** $390 - $370 + $270 = **+$290 profit**

On a massive crash, both legs go deep ITM and the spread converges to the $4 width between strikes. You still profit because the short put credits cover the net debit, but you have given up the unlimited downside that a naked long put would capture. This is the cost of the income stream.

---

## Scenario Summary Table

| Scenario | SPY at Close | Timing | Diagonal P&L | Vertical (Apr 11) P&L | Winner |
|---|---|---|---|---|---|
| A: Slow gap fill | $665 by Apr 22 | 3 weeks | **+$930** | -$320 (expired) | Diagonal |
| B: Fast gap fill | $663 by Apr 10 | 3 days | +$230 | **+$520** | Vertical |
| C: No gap fill | $678 through May | Never | **+$220** | -$320 | Diagonal |
| D: Strong rally | $695 by May | Never | **+$160** | -$320 | Diagonal |
| E: Crash | $640 by Apr 10 | 3 days | +$290 | **+$680** | Vertical |

**The diagonal wins in 3 of 5 scenarios and breaks even or profits in 4 of 5.** The vertical only wins in the 2 scenarios where the gap fills within its expiry window. If you believe the timing is uncertain (which is the entire premise), the diagonal is the structurally superior trade.

---

## Managing an ITM Short Leg

If SPY drops through the short strike during any week, you have three options. Ranked in order of preference:

### Option 1: Close the Short, Sell a Lower One (PREFERRED)

- Example: SPY drops to $667, short $670P is $3 ITM
- Buy back the short for ~$3.70 (losing ~$1.00 on 1x = $100)
- Immediately sell next week's put at $662P for ~$2.50
- Net: -$100 from closing + $250 new credit = +$150 net from the roll
- Your long $674P has gained ~$3.00+ from the SPY drop, more than covering the short loss

### Option 2: Roll Down and Out

- Buy back the Apr 11 $670P and simultaneously sell the Apr 17 $664P
- This can often be done for a small net credit ($0.20-0.50) or small net debit ($0.20-0.50)
- Best when SPY has dropped modestly (to 669-671) and you expect stabilization before continuation

### Option 3: Close Everything and Take Profit

- If the gap fill is happening (SPY at 665 or below), both legs are deep ITM
- Close the diagonal for approximately the strike width ($4) minus whatever time value remains
- Add the cumulative short credits collected
- This is the right move when the thesis has played out — do not try to squeeze more from the structure

**NEVER let a short put go to assignment.** Buying 100 shares of SPY at $670 costs $67,000. On a $10K account, your broker will forcibly liquidate at a terrible price. Always close ITM short puts by 3:30 PM ET on expiry day.

---

## Entry Rules

1. **Wait until 10:00 AM ET Monday.** The opening 30 minutes has wide spreads and erratic pricing. Let the auction settle.
2. **Confirm SPY is below $681.** If SPY gaps above 681 on Monday (further from gap), the $674 put becomes more expensive relative to its delta. Consider waiting a day or using the $672 long strike instead.
3. **Confirm VIX is above 17.** The entire rolling plan depends on selling weekly premium that is fat enough to offset the long put's cost. At VIX 15, weekly OTM puts pay $1.20-1.50 instead of $2.50-2.70. The math gets tight.
4. **Enter as a diagonal spread order, not separate legs.** Your broker should allow a "diagonal" or "custom spread" order type. Limit order at $3.70 net debit or better.
5. **If you cannot fill at $3.90 or better, walk away.** The edge degrades above $3.90 net debit because the rolling income has less room to cover the cost.
6. **Size: 1 contract.** On a $10K account with a 3% risk budget ($300), 1 contract at $370 is slightly over budget. This is acceptable because the effective risk drops to ~$100 after just one roll. Do NOT size to 2 contracts ($740 risk = 7.4%) — that blows the risk budget and leaves no room for managing the short leg if it goes ITM.

---

## Exit Rules

### Take Profit

- **If SPY reaches $663-$665 and the long put is $9+ ITM:** close the entire position (all legs). The gap has filled. Do not get greedy rolling more short puts — you are now holding a short-dated ITM put, and any bounce will eat your gains fast.
- **If cumulative short credits exceed $6.40 (the long put cost):** the long put is now a free asset. Let it ride as a lottery ticket for a crash. Set a GTC sell order at $2.00 on the long put as a floor.

### Stop Loss

- **Max loss is structurally defined:** $370 (net debit). This only occurs if SPY rallies immediately in week 1 and you close the long put at $0.
- **Practical stop after 2 rolls (April 17):** If you have collected ~$470 in credits and SPY is at $684+, your long $674P is worth maybe $1.80. Close it. Total: $180 - $640 + $470 = **+$10 (break-even)**. Walk away. The thesis is not working.
- **No stop on the spread value itself.** The diagonal's "value" fluctuates as short legs are opened and closed. Track the long put's value plus cumulative credits as your true position value.

### Time Stop

- **May 1 (1 day before long expiry):** Close everything. Do not hold a 1 DTE put overnight — gamma risk is extreme and theta will destroy any remaining value. Close the last short put if open, sell the long put for whatever it is worth, and book the final P&L.

---

## Weekly Management Checklist

Set a calendar alert: **Every Thursday at 3:00 PM ET**.

- [ ] Is the current short put OTM (SPY above the short strike)? If yes, let it expire Friday. If ITM, close it NOW.
- [ ] What is SPY's current price? Choose next week's short strike: 8-10 points below current SPY, and at least $2 below $674.
- [ ] What is VIX? If VIX > 25, you can sell a strike that is only 6-8 OTM for fatter premium. If VIX < 16, sell 10-12 OTM to avoid getting run over on a normal down day.
- [ ] What is the cumulative credit collected so far? If it exceeds $640 (the long put cost), you are on house money.
- [ ] Is the gap fill thesis still alive? Check ceasefire headlines. If the ceasefire is genuinely holding and SPY is at 690+, consider closing everything and taking whatever profit the credits provide.

---

## Risk Factors

| Risk | Impact | Mitigation |
|---|---|---|
| SPY rallies 3%+ in week 1 | Max loss $370 — only 1 week of credit ($270) offsets | Sized for total loss at 3.7% of account. Painful but survivable. |
| VIX crashes below 15 | Weekly short put credits shrink to $1.00-1.50 | Rolling income still covers ~60-70% of long put cost. Reduce profit expectations, not the position. |
| Gap fills Monday (flash crash) | Short put goes deep ITM immediately | Close the short at a loss, keep the long. Long put profits exceed short put losses because of the $4 strike differential. |
| Short put assignment | Catastrophic margin failure ($67K obligation on $10K account) | ALWAYS close ITM short puts by 3:30 PM on expiry day. This is non-negotiable. |
| Bid-ask spread erosion | Lose $0.05-0.15 per roll entry and exit | SPY options are the most liquid in the world. Use limit orders at mid. Budget $0.10/roll x 4 rolls = $40 total friction. |
| Forgetting to roll on Thursday/Friday | Miss a week of income ($150-270 lost) | Calendar alerts. If you miss, just sell Monday — you lose 1 day of theta, not the entire concept. |
| Ceasefire actually holds | Gap never fills, SPY continues higher | Scenario D above: +$160 profit from rolling income even if thesis is completely wrong. |

---

## Diagonal vs. Vertical: The Honest Comparison

When the diagonal is BETTER:
- Timing uncertain (the whole point of this trade)
- VIX elevated (fatter weekly premiums to sell)
- You are disciplined about weekly management
- You want to profit even if the thesis fails

When a vertical is BETTER:
- You are confident the gap fills THIS WEEK (fast move)
- You want set-and-forget simplicity
- You want maximum profit on a fast crash ($680 on a vertical vs. $290 on the diagonal if SPY hits 640 in week 1)
- You do not want to manage anything

When a NAKED PUT is BETTER:
- You expect an extreme overshoot (SPY below 650)
- You want unlimited downside profit
- You can stomach the full premium risk if SPY goes sideways

The diagonal is the right tool specifically because the thesis statement includes the words "timing uncertain." If you knew the gap fills by Friday, you would buy a vertical. You do not know that, so you buy patience.

---

## Position Summary

| Field | Value |
|---|---|
| **Structure** | Long $674P (May 2) / Short $670P (Apr 11, rolled weekly) |
| **Underlying** | SPY |
| **Contracts** | 1x |
| **Long expiry** | May 2, 2026 (25 DTE) |
| **Short expiry (initial)** | Apr 11, 2026 (4 DTE) — rolled to Apr 17, Apr 25, May 1 |
| **Net debit** | ~$3.70 ($370) |
| **Max loss** | $370 (3.7% of account, only if SPY rallies immediately with no rolling income) |
| **Effective risk after 2 rolls** | ~$0 (credits exceed debit) |
| **Expected rolling income (3-4 rolls)** | ~$700-1,050 |
| **Max profit** | ~$930 (slow gap fill to $665 by April 22) |
| **Profit if thesis wrong** | +$160 to +$220 (rolling income covers the long put) |
| **Wins in** | 4 of 5 scenarios |
| **Loses only when** | SPY spikes higher in week 1 before collecting more than 1 cycle of short premium |
| **R:R (worst case)** | 1:2.5 ($370 risk / $930 best case) |
| **R:R (realistic, after 2 rolls)** | Near-infinite (risk approaches $0, any profit is a win) |
| **Active management** | Required — weekly roll every Thursday/Friday |
| **Thesis** | Ceasefire gap fills, timing unknown. Diagonal buys patience through income. |
| **Conviction** | High — structure profits in most scenarios, thesis only needs to be directionally correct |
