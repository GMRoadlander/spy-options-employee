# Position 14: Diagonal Put Spread — Gap Fill with Timing Flexibility

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783)
**Thesis:** US-Iran ceasefire gap from ~661 to ~678 fills within 1-3 weeks. Timing is uncertain — could be Monday, could be April 25. A diagonal put spread buys time cheaply while generating weekly income from short-dated puts.
**Account:** $10,000 | **Risk budget:** ~5% = $500

---

## POSITION: Diagonal Put Spread (Poor Man's Covered Put)

| Field | Detail |
|---|---|
| **Long leg** | **BUY 2x SPY May 2 $672 Put** |
| **Short leg (week 1)** | **SELL 2x SPY Apr 11 $668 Put** |
| **Entry** | Monday Apr 7, 10:00-10:30 AM ET (after opening range settles) |
| **Long leg expiry** | May 2, 2026 (25 DTE at entry) |
| **Short leg expiry** | Apr 11, 2026 (4 DTE at entry) |
| **Estimated long put cost** | ~$5.80 per contract ($1,160 for 2x) |
| **Estimated short put credit** | ~$2.20 per contract ($440 for 2x) |
| **Net debit** | ~$3.60 per diagonal ($720 for 2x) |
| **Max loss** | ~$720 (net debit, if SPY stays above 672 through May 2 and all short legs expire worthless or are rolled for less than total debit) |
| **Breakeven at first expiry** | ~$668.40 (short strike minus net credit after accounting for remaining long put value) |
| **Reward:Risk** | Variable — see scenarios below |

---

## How This Trade Works

**You own the right to be bearish for 25 days. You rent out that right 4-5 days at a time.**

The structure has two moving parts:

1. **Long May 2 $672 Put** — this is your anchor. It is 6 points OTM at entry (SPY ~678), has 25 DTE, and decays slowly (~$0.08/day initially). This leg survives timing errors. If the gap fill takes 2 weeks instead of 2 days, you still own a put with real value.

2. **Short Apr 11 $668 Put** — this generates income. It is 10 points OTM, expires in 4 days, and decays aggressively (~$0.40/day). If SPY stays above 668 through Friday, this leg expires worthless and you keep the $440 credit. Then you sell the next week's put.

The diagonal relationship: the short strike ($668) is BELOW the long strike ($672), creating a $4 buffer zone. This means if SPY drops moderately (to 670, say), your long put gains value faster than the short put because it is closer to the money. The short put provides a partial hedge against time decay on the long put.

---

## Strike Justification

### Why $672 Long Put (May 2)?

- **6 points OTM** at entry (SPY ~678). Close enough to have ~0.38 delta — moves meaningfully with SPY
- **Not ATM ($678)** — that would cost ~$8.50, making the net debit ~$6.30 per diagonal ($1,260 for 2x). Too expensive for a $10K account
- **Not deep OTM ($665)** — that would cost ~$3.20, cheaper but delta is only ~0.25. You need the move to happen AND be large before the put responds. Defeats the purpose of buying time
- **$672 is the sweet spot**: affordable enough for 2 contracts, high enough delta to profit from the first 50% of the gap fill move, and corresponds to the Friday close area where a retest is probable before any deeper move

### Why $668 Short Put (Apr 11)?

- **10 points OTM** at entry. Very high probability of expiring worthless if SPY merely chops sideways or dips modestly
- **Below the long strike by $4** — this is critical. If SPY drops to 670, your long $672 put is $2 ITM and gaining fast, while your short $668 put is still $2 OTM and losing value. You profit from the differential
- **$668 avoids the gap fill zone** ($661-663). You do NOT want the short put to be threatened by the actual thesis playing out. If SPY crashes to 662, having the short at 668 means it goes $6 ITM — but your long at 672 goes $10 ITM, so the spread still profits
- **4 DTE expiry** means aggressive theta decay. At $2.20 credit with 4 days to live, this put loses ~$0.40/day if SPY holds still. By Wednesday it is worth ~$1.00 even without any SPY move

### Why Not a Wider Diagonal (e.g., Long $675 / Short $660)?

- Long $675 costs ~$7.30. Short $660 (4 DTE, 18 OTM) credits only ~$0.80. Net debit = $6.50 per diagonal
- You are paying much more and collecting much less. The wider spacing looks "safer" but the economics are terrible
- The $672/$668 spacing keeps the short put close enough to collect real premium while maintaining the $4 buffer

---

## Why May 2 (Not April 25)?

| Expiry | DTE | Cost | Weekly rolls possible | Verdict |
|---|---|---|---|---|
| Apr 25 | 18 | ~$4.80 | 2-3 rolls | Adequate but tight — if gap fill takes 3 weeks, you run out of time |
| **May 2** | **25** | **~$5.80** | **3-4 rolls** | **Extra week costs ~$1.00 but adds an entire additional roll cycle** |
| May 16 | 39 | ~$7.50 | 5-6 rolls | Overpaying — theta is very slow at 39 DTE, first 2 weeks of time value are nearly wasted |

**May 2 is optimal.** The $1.00 premium for the extra week buys you one more short put sale (~$1.50-2.20 credit), which more than pays for itself. You net GAIN by choosing May 2 over April 25.

---

## The Rolling Plan (Week by Week)

This is where the diagonal shines. Each Friday after the short leg expires, you sell the next week's short put. The goal: collect enough total premium from short puts to reduce (or eliminate) the net cost of the long put.

### Week 1: Apr 7-11

| | |
|---|---|
| **Short leg** | 2x SPY Apr 11 $668P |
| **Credit collected** | ~$2.20/contract ($440 total) |
| **If SPY > 668 Friday** | Short expires worthless. You keep $440. Cumulative credit: $440 |
| **If SPY < 668 Friday** | Close the short for a loss, or let it assign and manage. See "What If the Short Goes ITM" below |

### Week 2: Apr 14-17 (roll)

| | |
|---|---|
| **Short leg** | SELL 2x SPY Apr 17 $666P (adjust strike down if SPY has fallen, up if SPY has risen) |
| **Expected credit** | ~$1.50-2.50/contract depending on where SPY is and IV level |
| **Strike selection rule** | Sell the put that is 8-12 points OTM from current SPY price, OR 2-4 points below your long strike, whichever is lower |
| **Cumulative credit target** | $800-$1,300 after 2 weeks |

### Week 3: Apr 20-25 (roll)

| | |
|---|---|
| **Short leg** | SELL 2x SPY Apr 25 $664P (or adjusted) |
| **Expected credit** | ~$1.20-2.00/contract |
| **Cumulative credit target** | $1,200-$1,800 after 3 weeks |

### Week 4 (if needed): Apr 28 - May 1

| | |
|---|---|
| **Short leg** | SELL 2x SPY May 1 $662P (or adjusted) |
| **This is the final roll** — long put expires May 2, one day after |
| **Expected credit** | ~$0.80-1.50/contract |
| **Cumulative credit target** | $1,500-$2,200 total |

### The Math That Matters

- **Total debit paid:** ~$1,160 (2x May 2 $672P)
- **Total short put credits (3-4 rolls):** ~$1,200-$2,200
- **Net cost of the long put after rolling:** $0 to NEGATIVE (you got paid to own it)
- **This means:** even if the gap fill never happens and SPY stays at 678 the entire month, you can break even or profit slightly from the short put income alone, as long as SPY does not crash through your short strikes

---

## Profit Scenarios

### Scenario A: Gap fills slowly (SPY drifts to 665 by April 22)

This is the ideal scenario for a diagonal.

- Short puts from weeks 1-2 expire worthless: +$800 cumulative credit
- Long May 2 $672P is now $7 ITM: worth ~$8.50 (intrinsic $7 + $1.50 time value)
- Week 3 short put ($664P) is $1 ITM — close for ~$1.50 loss
- **Total P&L:** ($8.50 x 200) - $1,160 debit + $800 credits - $300 short loss = **+$1,040 profit (~104% return on risk)**

### Scenario B: Gap fills fast (SPY drops to 663 by April 10)

- Week 1 short $668P goes $5 ITM — close for ~$5.30, losing ~$3.10/contract ($620 loss on 2x)
- Long May 2 $672P is $9 ITM with 22 DTE — worth ~$11.50
- Close the entire position: ($11.50 x 200) - $1,160 debit - $620 short loss = **+$520 profit**
- Alternatively, close the short, keep the long, sell a new short at a lower strike for more income

### Scenario C: No gap fill — SPY chops 675-682 for 4 weeks

- All 3-4 short puts expire worthless: +$1,500-$2,200 cumulative credit
- Long May 2 $672P expires with 1 DTE, SPY at 678 — worth ~$1.00 (all time value, still OTM)
- **Total P&L:** ($1.00 x 200) - $1,160 debit + $1,700 credits = **+$740 profit**
- You profited from a trade where your directional thesis was WRONG. This is the diagonal's superpower.

### Scenario D: SPY rallies hard to 695+ (thesis completely wrong)

- Short puts expire worthless each week: +$1,500-$2,200 cumulative
- Long May 2 $672P expires worthless: -$1,160
- **Total P&L:** -$1,160 + $1,700 = **+$540 profit** (you still made money)
- Note: this only works if SPY rallies gradually. A sudden spike to 695 in week 1 means you only collected one week of short premium ($440) and the long put is dead: -$1,160 + $440 = **-$720 loss** (max loss)

### Scenario E: SPY crashes to 640 (overshoot)

- Long $672P worth ~$32 (intrinsic $32, minimal time value)
- Short $668P (or wherever the current short is) worth ~$28
- Net spread value: ~$4 per contract = $800
- Minus debit: $800 - $720 net debit = **+$80 profit** (barely)
- **Key insight:** on a massive crash, the diagonal converges to the width between strikes ($4) minus the net debit. This is the tradeoff — you gave up unlimited downside profit in exchange for the rolling income. If you think a crash to 640 is likely, buy naked puts instead

---

## Why a Diagonal Beats a Vertical for This Thesis

| Factor | Vertical Put Spread (Position 02) | Diagonal Put Spread (This Position) |
|---|---|---|
| **Timing flexibility** | Must be right within 11 DTE | Has 25 DTE, can be wrong for 2 weeks and still win |
| **Cost of being early** | Theta eats you daily at ~$0.35/day | Short put income offsets theta — net decay is near zero or positive |
| **Cost of being wrong** | Lose entire debit ($480) | Can recover debit through rolling even if thesis fails |
| **Max profit on gap fill** | $820 (fixed) | $500-$1,040 depending on timing (variable but competitive) |
| **Profit if SPY stays flat** | Lose entire debit | **Can profit** from short put decay alone |
| **Complexity** | Set and forget | Must manage weekly rolls — active management required |
| **Worst case** | -$480 | -$720 (higher max loss) |

**The diagonal is superior when timing is uncertain.** The vertical is a coin flip — either the gap fills in 11 days or you lose. The diagonal is a process — you collect income every week while waiting for the gap to fill, and if it never fills, the income can still cover the cost.

---

## What If the Short Leg Goes ITM?

This is the risk that requires active management. Three options:

### Option 1: Close the Short for a Loss, Sell a New One (RECOMMENDED)

- If SPY drops to 665 and the short $668P goes $3 ITM, close it for ~$3.50 (losing ~$1.30/contract)
- Immediately sell the next week's put at a LOWER strike (e.g., $660P) to collect new premium
- Your long $672P has gained more value than the short lost, so the net position is still profitable

### Option 2: Let the Short Expire ITM and Get Assigned

- **Do NOT do this.** Assignment on a short put means you are obligated to buy 200 shares of SPY at $668 = $133,600. On a $10K account, this is catastrophic margin failure. Your broker will liquidate immediately.
- **Always close short puts before expiry if they are ITM.**

### Option 3: Roll the Short Down and Out

- Buy back the Apr 11 $668P (at a loss) and simultaneously sell the Apr 17 $663P (for credit)
- This "roll" extends the expiry and lowers the strike
- Often can be done for a small net credit or small net debit
- Best option when SPY has dropped modestly (to 667-670) and you expect it to stabilize before continuing lower

---

## Entry Rules

1. **Wait for 10:00 AM ET.** Monday opens are messy — let the opening auction settle
2. **Confirm SPY is below $680.** If it gaps up above 680, reassess — the move away from the gap is strengthening
3. **Confirm VIX is above 18.** Higher IV means fatter short put premiums, which is exactly what you want. If VIX has crashed to 15, the rolling income will be disappointing
4. **Enter both legs simultaneously as a diagonal spread order.** Do NOT leg in separately. Use a limit order at the net debit mid-price
5. **If you cannot get filled at $3.80 or better, do not enter.** Walk away. The edge disappears above that debit

---

## Exit Rules

### Take Profit
- **If SPY reaches 663-665 and your long put is $7+ ITM:** close the entire position (both legs). Do not get greedy trying to roll more short puts. The gap has filled, take the win
- **If cumulative short put credits exceed the long put cost (>$5.80/contract):** you are playing with house money. Let the long put ride as a free lottery ticket for a crash

### Stop Loss
- **Max loss is defined:** $720 (net debit for 2x diagonals). This occurs only if SPY rockets higher in week 1 before you collect any rolling income AND you close the long put at zero
- **Practical stop:** if by April 18 (after 2 roll cycles) SPY is above 682 and trending higher, close the long put for whatever residual value remains. You will have collected ~$800 in short credits, so even a $200 recovery on the long put means break-even
- **No hard stop on the spread value.** Unlike a vertical, a diagonal's value fluctuates with the short leg — the "value" of the position is the long put value minus any short put obligation. Monitor the LONG put's value instead

### Time Stop
- **May 1 (day before long expiry):** close everything. Do not hold a 1 DTE long put overnight. Close the last short put (if any) and sell the long put for remaining value

---

## Risk Factors

| Risk | Impact | Mitigation |
|---|---|---|
| SPY rallies 5%+ in week 1 | Max loss $720 — short put premium from week 1 ($440) only partially offsets | Position sized for total loss; $720 = 7.2% of account |
| VIX crashes below 15 | Short put premiums shrink, rolling income disappoints | Would still collect ~$1.00-1.50/week; reduce position to 1x if concerned |
| Gap fills too fast (Monday flash crash) | Short put goes deep ITM, must close at a loss | Close short immediately, keep long — net position still profits from the crash |
| Short put assignment risk | Catastrophic margin failure on $10K account | ALWAYS close ITM short puts before 3:30 PM on expiry day |
| Bid-ask spread on the diagonal | May lose $0.10-0.20 per entry and each roll | SPY options are extremely liquid; use limit orders at mid |
| Forgetting to roll | Short put expires, you lose a week of income | Set calendar alerts every Thursday at 3:00 PM ET: "Roll or close short put" |

---

## Position Sizing Rationale

- **2 contracts** at ~$3.60 net debit = $720 total risk (7.2% of account)
- This exceeds the 2% rule, but the effective risk is lower because:
  - You expect to recover $1,200-$2,200 from rolling short puts over 3-4 weeks
  - The long put retains time value even if the thesis fails
  - Realistic max loss after 2+ weeks of rolling is more like $200-400
- **1 contract** ($360 risk, 3.6%) is a valid conservative alternative. The rolling income will be halved ($600-$1,100 total) but still covers most of the debit
- **Do not size to 3+ contracts.** At $1,080+ risk and $668 short strikes, a fast gap fill could require $1,000+ to close the shorts — you need dry powder for management

---

## Weekly Management Checklist

Every Thursday at 3:00 PM ET:

- [ ] Is the current short put OTM? If yes, let it expire Friday. If ITM, close it now
- [ ] Where is SPY? Choose next week's short strike: 8-12 points OTM from current price, minimum 2 points below the long $672 strike
- [ ] What is VIX? If VIX > 25, sell a slightly closer strike for more premium. If VIX < 16, sell further OTM to avoid getting run over
- [ ] How much cumulative credit have you collected? If > $5.80/contract (the long put cost), you are playing with house money
- [ ] Is the gap fill thesis still valid? If SPY is at 700+ with strong momentum, consider closing everything

---

## Position Summary

| Field | Value |
|---|---|
| Structure | Long $672P (May 2) / Short $668P (Apr 11, rolled weekly) |
| Underlying | SPY |
| Long expiry | May 2, 2026 |
| Short expiry (initial) | Apr 11, 2026 (rolled weekly to Apr 17, Apr 25, May 1) |
| Net debit | ~$3.60/diagonal (~$720 for 2x) |
| Expected rolling income | ~$1,200-$2,200 over 3-4 weeks |
| Max loss | ~$720 (net debit, worst case with no rolling income) |
| Realistic max loss | ~$200-400 (after 2+ weeks of rolling income) |
| Max profit | ~$1,040 (gap fills slowly to 665 by April 22) |
| Profit if thesis is wrong | Possible +$540-740 from rolling income alone |
| R:R (worst case) | ~1:1.4 |
| R:R (realistic) | ~1:3 to 1:5 |
| Thesis | Ceasefire gap fills, but timing is uncertain — diagonal buys patience |
| Conviction | Moderate-high — the structure profits in 3 of 4 scenarios |
