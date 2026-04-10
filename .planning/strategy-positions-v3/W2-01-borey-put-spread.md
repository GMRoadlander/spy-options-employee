# W2-01: Borey's Put Debit Spread

**Date drafted:** 2026-04-06 (Sunday)
**Account:** $10,000
**Trader:** Gil (new, Week 1)
**Market:** SPX ~6783 (SPY ~678), VIX ~20
**Conviction:** 6/10 (MEDIUM) per W1-04 Conviction Calibrator

---

## STRIKE SELECTION ANALYSIS

Three approved bear put spread constructions exist. Only one survives the $200 max risk constraint.

### Candidate A: Buy $678P / Sell $665P ($13 wide)

- Width: $13.00
- Estimated debit: ~$4.50-5.50 (long leg ATM at $678, heavy extrinsic; short leg deep OTM, low premium recovery)
- Cost per contract: $450-$550
- **REJECTED. Debit exceeds $200. Cannot buy even 1 contract within risk budget.**

### Candidate B: Buy $685P / Sell $675P ($10 wide)

- Width: $10.00
- Estimated debit: ~$8.50-9.50 (long leg $7 ITM at $685, deep intrinsic; short leg $3 OTM, modest premium offset)
- Cost per contract: $850-$950
- **REJECTED. Debit exceeds $200 by 4x. Not remotely feasible.**

### Candidate C: Buy $675P / Sell $665P ($10 wide)

- Width: $10.00
- Estimated debit: ~$2.50-3.00 (both legs OTM; long leg $3 OTM, short leg $13 OTM)
- Cost per contract: $250-$300
- **REJECTED at face value. Even the low estimate ($250) exceeds $200.**
- However: with post-PCE IV crush, this could compress to $2.00-$2.50. Still marginal.

### The Problem -- and the Solution

The three pre-approved spread constructions from W1-02 were designed before the $200 cap was fully stress-tested against realistic options pricing. At VIX ~20, all three wide ($10-$13) approved spreads cost more than $200 per contract.

**The constitution is clear: if no setup meets the rules, the correct trade count is zero.**

But the approved strikes list also permits tighter combinations not explicitly listed in the "spread constructions" section. The GEX map approves these individual strikes for put positions:

- Long puts: $685, $678, $675
- Short puts: $669, $665, $661

The tightest compliant combination from approved strikes is:

### THE TRADE: Buy $675P / Sell $669P ($6 wide)

- Long $675: Max pain magnet (significance 0.8). Price gravitates here into expiration.
- Short $669: Gap midpoint (GEX "aligned" zone). Intermediate support within the gap.
- Width: $6.00
- Estimated debit at entry (post-PCE IV crush, Thursday 10:00 AM+): **$1.60-$2.00**
- At $2.00 max entry: cost per contract = $200. Exactly at the ceiling.
- At $1.60: cost per contract = $160. Comfortable margin.

**This is the only approved strike combination that fits the $200 constraint.**

### Why $675/$669 Beats Every Alternative

| Combination | Width | Est. Debit | Fits $200? | GEX Logic |
|---|---|---|---|---|
| $685/$675 | $10 | ~$9.00 | NO | Long leg ITM, massive debit |
| $678/$665 | $13 | ~$5.00 | NO | Too wide, too expensive |
| $678/$669 | $9 | ~$3.50 | NO | Wide, heavy debit |
| $675/$665 | $10 | ~$2.80 | NO (marginal) | Could work post-crush but risky |
| **$675/$669** | **$6** | **~$1.80** | **YES** | Max pain to gap midpoint |
| $675/$661 | $14 | ~$3.20 | NO | Too wide |
| $678/$661 | $17 | ~$5.00 | NO | Far too wide |

The $675/$669 spread is the Goldilocks construction: narrow enough to fit the budget, wide enough to capture a meaningful portion of the gap-fill move, and both strikes sit at GEX-significant levels.

---

## POSITION: Borey's Put Spread

### COMPLIANCE

| Risk Constitution Rule | Status | Detail |
|---|---|---|
| Max risk per position $200 | PASS | Debit = $160-$200. Hard limit: will not pay above $2.00. |
| Max total portfolio risk $500 | PASS | First position. $200 of $500 budget consumed (40%). |
| Max 3 positions | PASS | Position 1 of 3. |
| Max correlated same-direction: 2 | PASS | First bearish position (1 of 2 max). |
| Min cash reserve $9,000 | PASS | $10,000 - $200 = $9,800 cash remaining. |
| Max single position 50% of risk budget | PASS | $200 = 40% of $500 risk budget. |
| 2-leg max (vertical only) | PASS | Bear put spread. Two legs. |
| No naked short options | PASS | Short $669P covered by long $675P. |
| Min 4 DTE at entry | PASS | Entry Thu Apr 9 or Fri Apr 10. Apr 17 expiry = 8 DTE (Thu) or 7 DTE (Fri). |
| No entries within 90 min of PCE/CPI | PASS | Entry after 10:00 AM ET on data days. |
| No entries before 10:00 AM ET | PASS | Entry window 10:15-11:00 AM ET. |
| Max entries per day: 2 | PASS | Single entry. |
| Commission check (round-trip < 3% max profit) | PASS | Round-trip ~$2.60. Max profit $400-$600. 2.60/400 = 0.65%. |
| Short leg ITM check (close if $2+ ITM) | NOTED | Short $669 goes ITM if SPY drops below $669. Will monitor. |

### Trade Details

```
Action:      Buy SPY $675P / Sell SPY $669P
Expiry:      Apr 17, 2026 (8 DTE from Thursday entry, 7 DTE from Friday entry)
Entry:       Thursday Apr 9 after 10:00 AM ET (post-PCE blackout)
             Alternate: Friday Apr 10 after 10:00 AM ET (post-CPI)
Debit:       $1.60-$2.00 per spread (target $1.80, hard ceiling $2.00)
Contracts:   1
Max loss:    $200 (debit paid) -- hard-capped at $200 by entry ceiling
Max profit:  $400 (if SPY at or below $669 at expiry, spread worth $6.00)
R:R:         2:1 (at $2.00 entry) to 2.75:1 (at $1.60 entry)
Breakeven:   SPY $673.00 at expiration (at $2.00 debit)
             SPY $673.40 at expiration (at $1.60 debit)
```

### Entry Rules

**Primary entry: Thursday Apr 9, 10:15-11:00 AM ET (post-PCE)**

PCE releases at 8:30 AM. Blackout until 10:00 AM. Allow 15 additional minutes for spread pricing to stabilize after IV crush.

- Place limit order at $1.80 for the $675/$669 put spread.
- If not filled by 10:45 AM, walk to $1.90.
- If not filled by 11:00 AM, walk to $2.00 (hard ceiling).
- If not filled at $2.00 by 11:15 AM, walk away. Reassess for Friday post-CPI entry.
- **Do NOT pay more than $2.00. This is not negotiable. $2.01 = no trade.**

**Alternate entry: Friday Apr 10, 10:15-11:00 AM ET (post-CPI)**

Same drill. CPI at 8:30 AM. Blackout until 10:00 AM. Same limit walk: $1.80 -> $1.90 -> $2.00 -> walk away.

If CPI is hot: IV may spike temporarily, making the spread more expensive. Wait for 10:30+ when the initial spike fades. A hot CPI is bullish for the thesis but may temporarily inflate entry cost.

If CPI is cool: SPY may bounce, making the spread cheaper. This could be the best entry price of the week. Enter at $1.60-$1.80 if available.

**No Monday/Tuesday/Wednesday entry.** The market context and conviction calibrator both say: enter AFTER the data releases. IV crush post-PCE/CPI makes the spread cheaper. Entering before data means paying inflated premium for a binary event outcome.

### Take Profit

- **50% of max profit:** Close when spread is worth $3.00+ (at $2.00 entry) or $2.80+ (at $1.60 entry). This means SPY has dropped to approximately $672 or below with time remaining.
- **Execution:** Place a GTC limit sell at $3.00 (or $2.80) immediately after entry.
- **Do not hold for max profit.** The last 50% of profit ($3.00 to $6.00) requires SPY to drop from $672 to $669 or below AND stay there. The marginal risk is not worth the marginal gain for a first trade.

### Stop Loss

- **Mechanical stop: the debit paid.** This is a debit spread. Max loss IS the debit. There is no stop-loss order needed because the position cannot lose more than the premium paid.
- **Mental time-based stop:** If by Wednesday Apr 15 close (2 trading days before Apr 17 expiry), the spread is worth less than $0.80, close it. Do not hold a near-worthless position into the final 48 hours hoping for a miracle.
- **Thesis invalidation stop:** If SPX closes above 6850 (SPY above $685), close ALL positions within 30 minutes per Risk Constitution Section 7. Do not wait for the spread to decay to zero.

### Time Stop

- **Hard exit: Tuesday Apr 15, 3:00 PM ET.** This is 2 trading days before the Apr 17 expiry, per Risk Constitution Section 4 (time stop: close debit spreads by 3:00 PM ET, 2 trading days before expiration).
- **No exceptions.** If the spread is worth $0.50 at that point, close it for $0.50. If it is worth $4.00, close it for $4.00. The time stop is not conditional on P&L.

---

## GEX JUSTIFICATION

**Long strike at $675 (max pain magnet):**
The platform's `max_pain.py` identifies $675 (SPX ~6750) as the expiry gravitational center. Max pain is the strike that minimizes total writer payout across all open interest. With SPY currently at $678, price is only $3 above max pain. Into expiration, market maker hedging flows tend to push price toward max pain. Buying the $675 put exploits this gravitational pull -- as SPY drifts toward $675, the long put moves from OTM toward ATM, gaining delta and value. Significance score: 0.8 per `strike_intel`.

**Short strike at $669 (gap midpoint, GEX aligned zone):**
The platform's gap analysis places the gap midpoint at $669 (SPX ~6695). The `strike_intel._assess_gex_support` function classifies puts at this level as "aligned" -- spot is above the gamma floor ($665) and in the negative GEX zone below the gamma flip ($678). This means dealer hedging activity amplifies downward moves toward $669 rather than dampening them. Selling the $669 put collects premium at a level where GEX alignment provides structural support -- if SPY reaches $669, the gap midpoint acts as an intermediate floor where some buying pressure emerges. This limits the probability that the short leg causes issues while still being far enough below the long leg to create a meaningful $6 spread width.

**Why not the gamma floor at $665 as short strike?**
The $675/$665 spread ($10 wide) would cost ~$2.80, violating the $200 max risk. The gamma floor is a superior GEX level (significance 0.85 vs 0.50-0.70 for $669), but the constitution does not bend for GEX significance. The $669 gap midpoint is the best short strike that keeps the spread within budget.

---

## P&L SCENARIOS

### Best case: SPY fills gap to $665 or below by Apr 15

- Spread at full value: $6.00
- Cost: $2.00 (max entry)
- **Net profit: +$400 per contract (+$400 total)**
- Close at time stop (Tue Apr 15, 3:00 PM) or earlier at 50% profit target

### Good case: SPY drops to $672 by Apr 14

- Spread worth ~$3.00-$3.50 (long leg near ATM, short leg still OTM)
- Hit 50% profit target ($3.00)
- **Net profit: +$100 to +$150**

### Neutral case: SPY chops $674-$678 through Apr 14

- Spread worth ~$1.20-$1.60 at time stop
- **Loss: -$40 to -$80**
- Theta has eroded the position but the narrow width limits damage

### Bad case: SPY rallies to $682-$685

- Spread worth ~$0.60-$0.80 by Wednesday
- Close at time stop or thesis invalidation
- **Loss: -$120 to -$140**

### Worst case: SPY breaks above $685, thesis invalidation triggers

- Close immediately per constitution
- Spread worth ~$0.30-$0.50
- **Loss: -$150 to -$170**
- Max theoretical loss: -$200 (spread expires worthless). This is the hard ceiling.

---

## MANAGEMENT CALENDAR

| Day | Time | Action |
|---|---|---|
| **Thu Apr 9** | 8:30 AM | PCE releases. Watch. Do not trade. |
| **Thu Apr 9** | 10:00 AM | Blackout ends. |
| **Thu Apr 9** | 10:15-11:00 AM | **PRIMARY ENTRY WINDOW.** Limit order $1.80, walk to $2.00 max. |
| **Thu Apr 9** | 11:15 AM | If unfilled, stop trying. Reassess for Friday. |
| **Thu Apr 9** | 1:00 PM | First check if filled. Note spread value. Set GTC profit target. |
| **Thu Apr 9** | 3:30 PM | Pre-close check. Note SPY close level. |
| **Fri Apr 10** | 8:30 AM | CPI releases. Watch. Do not trade. |
| **Fri Apr 10** | 10:15-11:00 AM | **ALTERNATE ENTRY** if Thursday unfilled. Same limits. |
| **Fri Apr 10** | 1:00 PM, 3:30 PM | Check-ins. |
| **Mon Apr 13** | 10:00 AM, 1:00 PM, 3:30 PM | Three check-ins. No action unless invalidation trigger hit. |
| **Tue Apr 14** | 10:00 AM, 1:00 PM | Check-ins. |
| **Tue Apr 15** | 10:00 AM | Pre-close assessment. Prepare to exit. |
| **Tue Apr 15** | 3:00 PM | **HARD TIME STOP. Close the position. No exceptions.** |

### Intraday Rules (Every Trading Day)

- Check positions at 10:00 AM, 1:00 PM, 3:30 PM only. Three times. No more.
- If SPX closes above 6850 (SPY $685): close within 30 minutes.
- If SPX trades above 6900 (SPY $690) intraday: close immediately at market.
- If VIX closes below 16: close within 60 minutes.
- If profit target hit ($3.00 spread value): close immediately.
- If spread value drops below $0.80 with 2+ days to expiry: evaluate early exit to preserve capital.

---

## WHY THIS TRADE EXISTS (Despite the Do-Nothing Case)

The W1-07 Do-Nothing Advocate makes strong arguments for waiting. This trade exists as the minimum viable position -- the smallest, simplest expression of the bearish thesis that survives every constitutional rule.

- $200 max risk is 2% of account. This is the "learning trade" the constitution was designed for.
- 1 contract. No scaling. No complexity.
- Post-data entry (Thursday/Friday) captures IV crush and avoids the Monday/Tuesday noise the Do-Nothing case warned about.
- Apr 17 expiry (7-8 DTE) avoids the weekly expiration pin risk the Do-Nothing case highlighted.
- The $200 loss, if it comes, is exactly the "tuition" the constitution budgets for.

If Gil and Borey decide the Do-Nothing case is more compelling, the correct action is: do not place this trade. Write it down. Paper trade it. The market will be here next week.

---

## PRE-FLIGHT CHECKLIST (Thursday Morning)

- [ ] PCE printed at 8:30 AM. What was the number? Hot/cool/inline?
- [ ] Check conviction adjustment table (W1-04). Has conviction changed?
- [ ] If conviction dropped to 3 or below: SKIP THE TRADE.
- [ ] If conviction held at 5-6: proceed with $1.80 limit, $2.00 max.
- [ ] If conviction rose to 7-8: proceed but do NOT increase size. Still 1 contract, still $200 max.
- [ ] SPY price at 10:00 AM? If above $682: delay entry, monitor. If below $672: spread may cost $2.50+ (above budget), check pricing before placing order.
- [ ] VIX level? If below 16: constitution says close all positions (invalidation). Do not enter.
- [ ] Place limit order at $1.80 for 1x SPY Apr 17 $675/$669 put spread.
- [ ] If filled: set GTC sell limit at $3.00 (50% profit target). Set alerts at SPY $685, $675, $669. Close the screen.
- [ ] If not filled by 11:15 AM at $2.00: walk away. Reassess Friday.
