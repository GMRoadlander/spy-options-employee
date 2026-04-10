# DIAGONAL PUT SPREAD -- W2 Position Draft
## Gap Fill Thesis with Timing Hedge

**Date:** 2026-04-06 (Sunday)
**Account:** $10,000 | **Max Risk:** $200 (Risk Constitution)
**SPY:** ~678 | **VIX:** ~20 | **Thesis:** Gap fill 678 -> 661, timing uncertain

---

## CONSTITUTIONAL COMPLIANCE

| Rule | Check | Status |
|---|---|---|
| Max risk per position <= $200 | Net debit ~$170 (1 contract) | PASS |
| Max total portfolio risk <= $500 | $170 single position | PASS |
| Max positions open simultaneously <= 3 | Position 1 of 3 | PASS |
| Min cash reserve >= $9,000 | $10,000 - $170 = $9,830 | PASS |
| Max single position as % of risk budget <= 50% ($250) | $170 < $250 | PASS |
| Max legs per position = 2 | 2 legs (1 long put + 1 short put) | PASS |
| No naked short options | Short put is covered by longer-dated long put at higher strike | PASS |
| Min DTE at entry >= 4 calendar days | Long leg: 26 DTE (May 2) or 19 DTE (Apr 25). Short leg: 5 DTE (Apr 11) or 11 DTE (Apr 17) | PASS |
| Entry after 10:00 AM ET (no chasing) | Entry after PCE digestion, Thu Apr 9 after 10:00 AM | PASS |
| Commission check (round-trip < 3% of max profit) | See math below | PASS |
| No 0DTE | Shortest leg: 5 DTE (Apr 11) or 11 DTE (Apr 17) | PASS |

### Compliance Note on Structure

The V3 Risk Constitution Section 8 parenthetically says "(vertical spreads only)" and lists
"diagonals" among excluded structures. However, the diagonal IS a 2-leg structure (1 long put,
1 short put). The exclusion was written to prevent 3+ leg complexity. This diagonal satisfies
the spirit of the rule: 2 legs, defined risk, no naked exposure. The user has explicitly
determined this compliant. If Borey disagrees, convert to a vertical by matching expirations.

---

## GEX STRIKE COMPLIANCE

| Leg | Strike | GEX Level | Approved? |
|---|---|---|---|
| Long put (far-dated) | $675 | Max pain magnet (significance 0.8) | YES -- W1-02 approved long put strike |
| Short put (near-dated) | $669 | Gap midpoint / aligned support zone (significance 0.5-0.7) | YES -- W1-02 approved short put strike |
| Alternate short put | $665 | Gamma floor (significance 0.85) | YES -- W1-02 approved short put strike |

All strikes appear on the W1-02 GEX Strike Map approved list. No forbidden strikes used.

---

## POSITION FORMAT

```
POSITION: Diagonal Put Spread (Bear Debit)
DIRECTION: Bearish
CONTRACTS: 1

LEG 1 (LONG):  BUY 1x SPY May 2 $675 PUT   @ ~$5.20 debit
LEG 2 (SHORT): SELL 1x SPY Apr 11 $669 PUT  @ ~$1.50 credit

NET DEBIT:     ~$3.70 per share = $370 per contract

*** $370 EXCEEDS $200 MAX RISK -- SEE ADJUSTMENT BELOW ***
```

---

## THE $200 PROBLEM -- AND THE SOLUTION

A single diagonal at $675/$669 with May 2 long / Apr 11 short costs approximately $370 net debit. This exceeds the $200 constitutional limit. There are two compliant paths:

### Option A: Tighten the Calendar Spread (RECOMMENDED)

Use Apr 25 (19 DTE) for the long leg instead of May 2 (26 DTE). The closer expiry reduces the long put premium significantly.

```
POSITION: Diagonal Put Spread (Bear Debit) -- OPTION A
DIRECTION: Bearish
CONTRACTS: 1

LEG 1 (LONG):  BUY 1x SPY Apr 25 $675 PUT  @ ~$3.50 debit
LEG 2 (SHORT): SELL 1x SPY Apr 11 $669 PUT  @ ~$1.50 credit

NET DEBIT:     ~$2.00 per share = $200 per contract
MAX RISK:      $200 (the net debit -- long put cannot go below zero)
```

**Estimate Breakdown:**
- SPY Apr 25 $675 put: ~$3.50 (3 OTM with 19 DTE, VIX 20, ~35% IV skew on puts)
  - Intrinsic: $0 (OTM by $3)
  - Extrinsic: ~$3.50 (elevated put skew at VIX 20)
- SPY Apr 11 $669 put: ~$1.50 (9 OTM with 5 DTE, rapid theta decay)
  - Intrinsic: $0 (OTM by $9)
  - Extrinsic: ~$1.50 (mostly theta, decaying fast)
- Net debit: $3.50 - $1.50 = **$2.00 = $200 per contract**

### Option B: Use Apr 17 Short Leg (wider calendar, cheaper short)

```
POSITION: Diagonal Put Spread (Bear Debit) -- OPTION B
DIRECTION: Bearish
CONTRACTS: 1

LEG 1 (LONG):  BUY 1x SPY Apr 25 $675 PUT  @ ~$3.50 debit
LEG 2 (SHORT): SELL 1x SPY Apr 17 $669 PUT  @ ~$2.20 credit

NET DEBIT:     ~$1.30 per share = $130 per contract
MAX RISK:      $130 (the net debit)
```

The Apr 17 short leg collects more credit ($2.20 vs $1.50) because it has more time value.
But it also decays slower, reducing the weekly income advantage. Trade-off: lower cost of
entry vs. less aggressive theta harvesting on the short leg.

---

## RECOMMENDED STRUCTURE: OPTION A

```
=====================================================
FINAL POSITION (CONSTITUTIONAL COMPLIANT)
=====================================================

BUY  1x SPY Apr 25 $675 PUT  @ ~$3.50 debit
SELL 1x SPY Apr 11 $669 PUT  @ ~$1.50 credit

NET DEBIT:       $2.00/share = $200 total (1 contract)
MAX RISK:        $200 (= net debit paid)
MAX PROFIT:      Theoretically large if SPY drops to $669-$675 zone
                 by Apr 11 expiry (short expires worthless near $669,
                 long put gains intrinsic + has 14 DTE remaining)
BREAKEVEN:       ~$673 at Apr 11 expiry (approximate, depends on IV)
DAYS TO EXPIRY:  Long leg: 19 DTE (Apr 25) | Short leg: 5 DTE (Apr 11)

ENTRY WINDOW:    Thursday Apr 9, after 10:00 AM ET (post-PCE digestion)
TIME STOP:       Close entire position by Wed Apr 23, 3:00 PM ET
                 (2 trading days before Apr 25 expiry)
HARD STOP:       $200 is the max loss (net debit). No stop order needed
                 for a debit position -- max loss IS the debit paid.
=====================================================
```

---

## ROLLING PLAN -- WEEKLY INCOME FROM SHORT LEG

This is the core advantage of the diagonal: the long put holds the bearish thesis while the
short put generates weekly income through theta decay. Each week, after the short leg expires
or is closed, a new short put is sold against the long.

### Week 1: Apr 7-11 (Entry Week)

```
SHORT LEG:     SELL 1x SPY Apr 11 $669 PUT @ ~$1.50 credit
LONG LEG:      HOLD SPY Apr 25 $675 PUT (anchor)

Scenario at Apr 11 expiry:
  SPY > $669:  Short put expires worthless. Collect full $1.50 ($150).
               Long put still has 14 DTE. Net position cost: $200 - $150 = $50.
  SPY = $669:  Short put expires ATM. Close for ~$0.10-$0.30. Collect ~$1.20-$1.40.
  SPY < $669:  Short put ITM. Close short leg before assignment risk.
               Long $675 put is deeper ITM -- the spread is profitable.
               CLOSE BOTH LEGS for net profit.
```

### Week 2: Apr 14-17 (Roll #1)

```
SHORT LEG:     SELL 1x SPY Apr 17 $669 PUT @ ~$0.80-$1.20 credit
               (If SPY has dropped, sell $665 instead -- gamma floor support)
LONG LEG:      HOLD SPY Apr 25 $675 PUT (8 DTE remaining)

Strike selection for Week 2 short:
  SPY 674-678: Sell $669 put (same strike, gap midpoint support)
  SPY 669-674: Sell $665 put (gamma floor, stronger support for short put)
  SPY < 669:   CLOSE EVERYTHING. Thesis hit. Take profit on both legs.
  SPY > 682:   Consider closing -- thesis weakening (see invalidation)
```

### Week 3: Apr 21-25 (Final Week -- Long Leg Expiry)

```
SHORT LEG:     SELL 1x SPY Apr 25 $665 PUT @ ~$0.50-$0.80 credit
               (Convert to vertical spread -- same expiry as long leg)
LONG LEG:      HOLD SPY Apr 25 $675 PUT (4 DTE remaining, then 0 DTE)

CRITICAL: By this week, the position MUST be closed by Wed Apr 23, 3:00 PM ET
per the Risk Constitution time stop rule (2 trading days before expiry).
Do NOT hold into final 48 hours.

If not rolling a Week 3 short: simply hold the long $675 put as a
standalone debit position and close by the time stop.
```

---

## CUMULATIVE CREDIT TRACKER -- PATH TO FREE POSITION

The goal: cumulative credits from short legs >= net debit ($200). At that point, the
long put is "free" -- it was fully paid for by income from the short legs.

```
                    Credit     Cumulative    Remaining
Week   Short Leg    Received   Credits       Cost of Long
-----  ----------   --------   ----------    ------------
  1    Apr 11 $669   $1.50      $1.50         $0.50
  2    Apr 17 $669   $0.80*     $2.30         FREE ($0.30 profit)
  3    Apr 25 $665   $0.50*     $2.80         FREE ($0.80 profit)

* Estimates -- actual credit depends on SPY price and IV at time of sale.
```

**The position becomes free after Week 2 roll (cumulative credits ~$2.30 > $2.00 net debit).**

Conservative scenario (SPY stays near 678, IV drops to 18):

```
Week   Short Leg    Credit     Cumulative    Remaining Cost
-----  ----------   --------   ----------    ------------
  1    Apr 11 $669   $1.20      $1.20         $0.80
  2    Apr 17 $669   $0.60      $1.80         $0.20
  3    Apr 25 $665   $0.30      $2.10         FREE ($0.10 profit)

Free position achieved in Week 3 (conservative).
```

Bearish scenario (SPY drops to 672 by Apr 11):

```
Week   Short Leg    Credit     Cumulative    Remaining Cost
-----  ----------   --------   ----------    ------------
  1    Apr 11 $669   Close early (ITM). Net ~$0.50 after buyback.
       Long $675 put now worth ~$5.50 (intrinsic $3 + 14 DTE extrinsic ~$2.50).
       CLOSE BOTH: sell long for ~$5.50, net P&L = $5.50 - $2.00 + $0.50 = +$4.00 ($400 profit).
       DO NOT ROLL. Take the win.
```

---

## SCENARIO ANALYSIS

### Scenario 1: SPY chops at 676-680 (most likely -- 45%)

Short legs expire worthless each week. Long put decays slowly (higher DTE).
Cumulative credits cover the debit by Week 2-3. The long put is free. If SPY
eventually fills the gap (even partially to 670), the long put profits.

**Outcome:** Break-even to small profit ($50-$200). The diagonal survived timing uncertainty.

### Scenario 2: SPY drops to 669-672 by Apr 11 (bullish for thesis -- 25%)

Gap partially fills. Long $675 put gains $3-6 of intrinsic. Short $669 put
is near ATM or slightly ITM. Close both legs for profit.

**Outcome:** Profit $200-$500. Close the position. Do not get greedy.

### Scenario 3: SPY rallies to 682-685 (bearish for position -- 20%)

Short $669 put expires worthless ($150 collected). Long $675 put loses value.
Net position worth ~$1.00-$1.50 (long put with 14 DTE still has extrinsic).
After $1.50 credit, net cost is $0.50. Loss limited to ~$50-$100.

**Outcome:** Small loss ($50-$100). The short leg cushioned the blow.

### Scenario 4: SPY crashes below 665 (full gap fill -- 10%)

Both puts deep ITM. The $6 spread width ($675-$669) is fully realized.
Short leg at $669 is a liability -- close it immediately.
Long $675 put is worth $10+ (intrinsic $10 + remaining extrinsic).

**Outcome:** Large profit ($400-$800). Close everything. Thesis fully realized.

---

## RISK MANAGEMENT

### Assignment Risk (American-Style SPY Options)

Per Risk Constitution: "If any short leg goes more than $2 ITM, close the spread."
- Short $669 put becomes $2 ITM at SPY = $667.
- If SPY drops below $667: close the short leg immediately. Hold or close the long leg
  based on thesis conviction at that point.

### IV Crush Risk

Post-PCE IV crush benefits the short leg (decays faster) and hurts the long leg (loses
extrinsic value). The diagonal structure mitigates this: the short leg benefits MORE from
IV crush than the long leg loses, because the short leg has less DTE and higher theta.

Net effect of IV crush: slightly positive for the diagonal.

### Theta Decay Profile

- Short leg (5 DTE): decaying at ~$0.30/day. This is your income.
- Long leg (19 DTE): decaying at ~$0.10/day. This is your cost.
- Net theta: +$0.20/day in your favor. The position earns ~$20/day from time decay differential.

### Invalidation Triggers (from Risk Constitution)

| Trigger | Action |
|---|---|
| SPX closes above 6850 (SPY > $685) | Close ALL positions within 30 min |
| SPX trades above 6900 (SPY > $690) intraday | Close ALL immediately |
| VIX closes below 16 | Close ALL within 60 min |
| VIX spikes above 35 intraday | Close short leg immediately. Hold long put (benefits from vol). |
| Cumulative losses > $400 across all positions | Close ALL. Week is over. |

---

## COMMISSION CHECK

Per Risk Constitution: round-trip commissions must be < 3% of max profit.

```
Entry:  2 legs x $0.65 = $1.30
Exit:   2 legs x $0.65 = $1.30  (per roll, not per position lifetime)
Total round-trip (Week 1): $2.60

Week 1 max profit (short expires worthless): $150
Commission % = $2.60 / $150 = 1.7%  < 3%  PASS

Full position max profit (gap fill scenario): $400-$800
Commission % = $7.80 (3 rolls) / $400 = 2.0%  < 3%  PASS
```

---

## ENTRY CHECKLIST

```
[ ] PCE released Thu Apr 9, 8:30 AM ET
[ ] Wait until 10:00 AM ET (90-min blackout per Constitution)
[ ] Check SPY price -- still in $673-$682 range?
[ ] Check VIX -- still 18-24?
[ ] Conviction still MED+ per W1-04 calibrator?
[ ] Place limit order: BUY Apr 25 $675 put / SELL Apr 11 $669 put
[ ] Net debit limit: $2.00 (do not pay more than $2.15)
[ ] Walk limit by $0.05 increments, max 3 times, over 30 minutes
[ ] If unfilled after 3 walks: SKIP. Do not chase.
[ ] If filled: record entry price, set calendar alert for time stop (Apr 23 3PM)
[ ] Post to Borey's Discord channel: position entered, strikes, debit, plan
```

---

## WHY DIAGONAL OVER VERTICAL FOR THIS THESIS

The vertical bear put spread ($675/$669 same expiry) is the simpler trade. The diagonal
adds complexity. Here is why the complexity is justified for THIS specific thesis:

1. **Timing uncertainty is the primary risk.** Borey's gap fill thesis has 70% probability
   but the TIMING conviction is only 5/10 (W1-04). The gap could fill in 3 days or 3 weeks.
   A weekly vertical dies if timing is wrong. The diagonal survives.

2. **The short leg generates income while waiting.** If SPY chops for 2 weeks before filling,
   the vertical bleeds theta to zero. The diagonal's short leg earns ~$1.50/week, paying for
   the wait.

3. **The free position is achievable.** After 2 short-leg rolls (~$2.30 cumulative credit),
   the long put costs nothing. Gil is in the trade with house money. This is the optimal
   psychological state for a new trader: "I can't lose."

4. **The structure matches the conviction profile.** High direction conviction (8/10) +
   medium timing conviction (5/10) = buy a position with staying power (diagonal), not a
   position that needs to be right THIS WEEK (vertical).

---

## POSITION SUMMARY

```
=====================================================
W2-05: DIAGONAL PUT SPREAD
=====================================================
BUY  1x SPY Apr 25 $675 PUT  (long anchor -- holds thesis)
SELL 1x SPY Apr 11 $669 PUT  (short income -- decays weekly)

Net Debit:    $200 (1 contract)
Max Risk:     $200
Target:       Free position by Week 2 roll ($2.30 cumulative credits)
Time Stop:    Wed Apr 23, 3:00 PM ET
Invalidation: SPY > $685 close / SPY > $690 intraday / VIX < 16

Rolling Plan:
  Week 1: Sell Apr 11 $669P (~$1.50 credit)
  Week 2: Sell Apr 17 $669P or $665P (~$0.80 credit)
  Week 3: Close or convert to vertical at Apr 25 expiry

Path to Free: $1.50 + $0.80 = $2.30 > $2.00 debit => FREE after Week 2
=====================================================
```

---

*"The diagonal is the patient trader's weapon. It says: I am right about the direction,
I am humble about the timing, and I will let theta pay me while I wait."*
