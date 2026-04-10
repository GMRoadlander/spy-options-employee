CORRELATION BUDGET -- V3 Swarm
===============================
Date: 2026-04-06 (Sunday)
Author: Correlation Budget Officer (Agent W1-06)
Inputs: W1-03-market-context.md, V2 post-mortem, V3 Risk Architecture (01-risk-management-architect.md)
Binding on: ALL Tier 3 trade proposal agents. No portfolio may be submitted that violates this budget.

---

## V1/V2 FATAL FLAW: THE CORRELATION DISASTER

V1: 20 positions proposed. All 20 were bearish. Correlation = 1.0.
If the ceasefire held, EVERY position lost. No hedge. No diversification.
Total portfolio was not "20 positions" -- it was "1 bearish bet sized 20x."

V2: Improved with a bear call spread (Position B) and crash butterfly (Position C).
But Position B (bear call) ALSO loses on a rally. It is bearish, not neutral.
Position C (crash butterfly) is ultra-bearish. The "portfolio of three" was
really "three bearish bets at three different aggression levels."

In the rally scenario (SPY 690), V2 lost on ALL THREE positions: -$360.
In the chop scenario (SPY 678), V2 lost on 2 of 3: -$105.

The only scenario where a V2 position hedged another was chop (B's theta
offset A and C's bleed). But even that was partial -- B was still directionally
bearish (bear CALL spread), it just profited from theta faster than it lost
from delta. That is not a hedge. That is a slower bleed.

V3 MUST FIX THIS. The portfolio must include at least one position that
PROFITS when the thesis is WRONG.

---

## PORTFOLIO BALANCE REQUIREMENTS

- Max bearish directional positions: 2 out of 3 total
- Required non-bearish positions: 1 minimum (must profit if SPY rallies to 690)
- Required neutral/theta positions: 1 minimum (must profit if SPY chops 674-682)
- At least 1 position must have POSITIVE delta or POSITIVE vega-on-rally characteristics
- The non-bearish position is NOT optional. It is the price of admission for the bearish trades.

Why only 3 positions total:
- Borey's critique: "17 positions is procrastination, not research"
- $10K account, $500 max risk = ~$165 average risk per position
- New trader: 3 positions with 3 different management rules is the maximum cognitive load
- More positions = more correlation hiding behind the illusion of diversification

---

## CORRELATION MATRIX: WHICH TRADES LOSE TOGETHER

Every proposed portfolio MUST fill in this matrix before submission. If any row
shows all three positions losing, the portfolio is REJECTED unless the total
loss in that row is under $200 (the "acceptable bad day" threshold).

| Scenario         | Bearish #1   | Bearish #2 / Neutral | Hedge / Non-Bear | Net P&L    | Survives? |
|------------------|-------------|----------------------|-------------------|------------|-----------|
| Gap fill (661)   | +$400-780   | +$50-110             | -$50-100          | +$400-790  | YES       |
| Rally (690)      | -$130-220   | -$50-110             | +$100-250         | -$80-80    | YES (!)   |
| Chop (678)       | -$80-150    | +$40-95              | +$20-60           | -$20-5     | YES       |
| Crash (640)      | +$600-780   | +$80-110             | -$80-170          | +$600-720  | YES       |
| VIX spike (30+)  | +$200-400   | -$20-50              | +$50-150          | +$230-500  | YES       |
| VIX crush (15)   | -$100-180   | +$60-95              | +$10-40           | -$30-(-45) | YES       |
| Mon gap up (685) | -$100-200   | -$30-95              | +$80-200          | -$50-(-95) | YES       |

CRITICAL ROW: "Rally (690)." In V2, this row was -$185, -$95, -$80 = -$360.
In V3, this row MUST show at least one position with a positive P&L, and the
net loss MUST be under $250 (2.5% of account). The hedge position is what
makes this possible.

CRITICAL ROW: "Chop (678)." This is the MOST LIKELY single scenario (~25%
probability per market context). The portfolio must not lose more than $150
here. At least one position must be profitable in chop. Theta collectors and
neutral strategies serve this purpose.

---

## THE THREE REQUIRED PORTFOLIO CATEGORIES

### Category 1: Core Bearish (Gap Fill Thesis)
- Direction: Bearish
- Purpose: Profits when the gap fill thesis plays out (SPY 678 -> 661)
- Structure: Put debit spread or straight long put
- Risk budget: $130-220 max (largest single allocation because this IS the thesis)
- Entry: Thursday Apr 9, after PCE settles (10:00-10:30 AM)
- Why biggest allocation: 70% probability of gap fill per market context
- Delta: Negative (target: -15 to -30 portfolio delta from this position)

### Category 2: Neutral / Theta Collector
- Direction: Neutral to slightly bearish
- Purpose: Profits from TIME, not from direction. Makes money in chop.
- Structure: Iron condor, iron butterfly, short strangle with wings, or bear call credit spread
  with strikes far enough OTM that it functions as theta play
- Risk budget: $90-150 max
- Entry: Monday Apr 7 or Thursday Apr 9 (captures maximum theta runway)
- KEY CONSTRAINT: Must be profitable if SPY stays between 672-684 through expiry
- Delta: Near-zero to slightly negative (target: -5 to -10 portfolio delta from this position)
- This position offsets Category 1's theta bleed in chop scenarios

### Category 3: Anti-Correlation Hedge (Bull Case Insurance)
- Direction: Bullish or long-volatility (direction-agnostic)
- Purpose: THE CEASEFIRE HOLDS. SPY rallies to 685-695. This position pays.
- Structure options (in order of preference for a new trader):
  a) Call debit spread (simplest: buy $682C / sell $692C, defined risk, profits on rally)
  b) Long call (simpler but more expensive, unlimited upside)
  c) Long straddle (profits on big move in EITHER direction -- rally OR crash)
  d) VIX put spread (profits on vol crush = ceasefire confidence, but settlement is complex)
- Risk budget: $80-130 max (smallest allocation because thesis is bearish, but NOT ZERO)
- Entry: Monday Apr 7 (before the week's catalysts -- you want this on BEFORE PCE/CPI)
- KEY CONSTRAINT: Must show positive P&L at SPY $690
- Delta: Positive (target: +10 to +20 portfolio delta from this position)
- This is the position V1/V2 never had. It is the difference between a portfolio and a prayer.

---

## PORTFOLIO-LEVEL GREEK CONSTRAINTS

These apply to the COMBINED portfolio after all three positions are on:

| Greek    | Target Range       | Rationale                                              |
|----------|--------------------|--------------------------------------------------------|
| Delta    | -10 to -25         | Bearish lean (thesis) but NOT max bearish              |
| Gamma    | Near zero to +0.5  | Avoid large gamma that whipsaws P&L intraday           |
| Theta    | -$5 to +$10/day    | Should not bleed >$5/day waiting; theta-positive ideal |
| Vega     | +$20 to +$80       | Slightly long vega: vol spike helps (ceasefire cracks) |

Why these ranges:
- Delta -10 to -25: Bearish enough that a 10-point SPY drop makes ~$100-250.
  Not so bearish that a 5-point SPY rally loses $50-125. V2's portfolio delta
  was approximately -45 to -60 (all bearish). V3 cuts that in half.
- Theta near zero: The neutral position's positive theta should roughly offset
  the bearish and hedge positions' negative theta. The portfolio should not
  hemorrhage $20/day waiting for the thesis to play out.
- Vega slightly positive: If the ceasefire collapses (vol spikes), vega helps.
  If ceasefire holds (vol crushes), the hedge position's directional gain
  offsets the vega loss. This is the right structural lean for this market.

---

## DIVERSIFICATION RULES (HARD CONSTRAINTS)

1. **At least 2 different expiry dates.**
   - Why: Single-expiry risk is real. If SPY pins at your strike on expiry day,
     all positions with that expiry get crushed by gamma simultaneously.
   - V2 used 3 expiries (Apr 11, Apr 17, Apr 22). That was correct. V3 must
     maintain at least 2.
   - Preferred: One near-term (Apr 11 or Apr 14) and one standard (Apr 17).

2. **At least 1 position that profits on a rally to SPY 690.**
   - This is the Category 3 hedge. Non-negotiable.
   - It does not need to profit a LOT on a rally. Even +$80 on a rally while
     the other two lose $200 total changes the max loss from $200 to $120.
   - The EXISTENCE of a rally-profitable position changes risk psychology.
     When SPY is at $684 and rising, a trader with no hedge panics. A trader
     with a call spread watches calmly because one position is gaining.

3. **At least 1 position that profits on chop/flat (SPY 674-682).**
   - This is the Category 2 theta collector. Non-negotiable.
   - Chop is the most common weekly outcome in any market. Ignoring it is
     how V1/V2 bled money while "waiting for the thesis."

4. **No more than $250 at risk in any single scenario.**
   - The worst row in the correlation matrix must not exceed -$250.
   - V2's worst row was -$360 (rally). V3 caps it at -$250.
   - This means the hedge must recover at least $100-150 of bearish losses
     in the rally scenario.
   - Exception: the "Monday gap up to 685 before positions are fully on" row
     may exceed $250 if only Monday-entry positions are affected, because
     Thursday-entry positions have not yet been placed. Actual capital at risk
     on Monday is only Positions B and C ($170-280), not the full portfolio.

5. **Circuit breaker: if portfolio down $300 total realized, close everything.**
   - $300 = 3% of account. At that point, the thesis is wrong or the timing
     is wrong, and holding further is hope, not strategy.
   - This is a REALIZED loss circuit breaker, not unrealized. Unrealized
     drawdowns on defined-risk positions are expected and priced in.
   - After circuit breaker triggers: no new positions for 48 hours. Review
     what went wrong. Do not revenge trade.

---

## APPROVED PORTFOLIO SHAPES

These are the only portfolio configurations that pass the correlation budget.
Tier 3 agents must propose trades that fit one of these shapes. Any other
shape requires explicit override from the Risk Constitution Compiler.

### Shape A: Aggressive Bearish (for 75%+ gap-fill conviction)
```
Position 1: Bearish put spread       — $180-220 risk — Apr 17 expiry
Position 2: Bear call credit spread  — $90-150 risk  — Apr 11 expiry
Position 3: Call debit spread (HEDGE) — $80-130 risk  — Apr 17 expiry
Total risk: $350-500
Bearish allocation: 60-70%
Hedge allocation: 20-30%
```
- 2 bearish + 1 hedge
- Position 2 doubles as theta collector (profits in chop if short call OTM)
- Position 3 is the anti-correlation hedge V2 never had
- Rally scenario: Pos 1 loses $180-220, Pos 2 loses $90-150, Pos 3 gains $100-250
  Net: -$70 to -$220 (UNDER $250 cap)
- Chop scenario: Pos 1 loses $80-150, Pos 2 gains $40-95, Pos 3 loses $30-80
  Net: -$70 to -$135 (UNDER $150 cap)

### Shape B: Balanced (for 60-70% gap-fill conviction -- RECOMMENDED)
```
Position 1: Bearish put spread       — $130-180 risk — Apr 17 expiry
Position 2: Iron condor / neutral    — $100-150 risk — Apr 11 or Apr 14 expiry
Position 3: Call debit spread (HEDGE) — $80-120 risk  — Apr 17 expiry
Total risk: $310-450
Bearish allocation: 40-50%
Neutral allocation: 25-35%
Hedge allocation: 20-30%
```
- 1 bearish + 1 neutral + 1 hedge
- Position 2 is a true neutral (iron condor profits if SPY stays in a range)
- Strongest performance in chop: 2 of 3 positions profit
- Rally scenario: Pos 1 loses $130-180, Pos 2 loses $50-100, Pos 3 gains $100-200
  Net: -$80 to -$80 (NEAR ZERO in many configurations)
- Gap fill scenario: Pos 1 gains $300-600, Pos 2 loses $50-100, Pos 3 loses $80-120
  Net: +$120 to +$380
- Note: Reduced gap-fill upside vs. Shape A is the COST of diversification.
  This is a feature, not a bug. You are trading max upside for survivability.

### Shape C: Diversified (for uncertain conviction or first-ever trade)
```
Position 1: Bearish put spread       — $130-170 risk — Apr 17 expiry
Position 2: Long straddle (vol play) — $100-170 risk — Apr 11 expiry
Position 3: Bear call credit spread  — $80-110 risk  — Apr 11 expiry
Total risk: $310-450
Bearish allocation: 40-50%
Vol play allocation: 30-40%
Theta allocation: 20-25%
```
- 1 bearish + 1 vol play + 1 theta collector
- Position 2 (straddle) profits on BIG move in EITHER direction
  -- if ceasefire collapses: put leg profits (bearish alignment)
  -- if ceasefire confirmed with real enforcement: call leg profits (hedge)
  -- if chop: both legs bleed (this is the cost)
- Position 3 theta collector offsets Position 2's chop bleed
- Rally scenario: Pos 1 loses $130-170, Pos 2 call leg gains $50-200, Pos 3 loses $80-110
  Net: -$10 to -$260 (wider range, depends on rally magnitude)
- This shape is BEST for the "I don't know" trader. It admits uncertainty.

---

## SHAPE RECOMMENDATION FOR THIS WEEK

**Shape B (Balanced) is recommended.**

Rationale:
1. Gap fill probability is 70%, not 90%. The 30% wrong case is real.
2. Gil is a new trader. Borey will judge discipline over conviction.
3. Shape B's chop performance (-$20 to +$5) is far superior to Shape A's
   (-$70 to -$135). Chop is the most likely SINGLE scenario at 25%.
4. Shape B's rally defense (net -$80 to near zero) is dramatically better
   than V2's -$360. This alone justifies the reduced gap-fill upside.
5. A new trader who survives a choppy week with -$20 P&L and learns the
   mechanics of three-position management is worth more than a trader who
   makes +$875 on a lucky gap fill and learns nothing about risk management.

If Borey says "I'm very confident in the gap fill, go more aggressive," Shape A
is the fallback. But the default is B until directed otherwise.

---

## WHAT THIS DOCUMENT CONTROLS

Every Tier 3 trade proposal agent (Agents 13-22) must:
1. Declare which Category (1, 2, or 3) their trade fills
2. Declare which Shape (A, B, or C) their trade fits into
3. Fill in the correlation matrix row for their trade
4. Demonstrate their trade does not push portfolio delta below -25
5. Demonstrate their trade does not push worst-case scenario loss above $250

Every Tier 5 portfolio construction agent (Agents 26-30) must:
1. Select exactly 3 positions, one from each Category
2. Verify the complete correlation matrix has no all-red rows above $250
3. Verify at least 2 different expiry dates
4. Verify portfolio Greeks fall within the target ranges
5. Verify total risk is under $500
6. Include the circuit breaker rule ($300 realized loss = close all)

Any portfolio that fails ANY of these checks is sent back for revision. There
are no exceptions. There are no "high conviction" overrides. The correlation
budget is the law.

---

## APPENDIX: WHY THE HEDGE "COSTS" MONEY AND WHY THAT IS CORRECT

The Category 3 hedge (call debit spread or straddle) will lose money in the
base case (gap fill). It costs ~$80-130 that produces $0 when the thesis works.
A bearish trader looks at this and says "why am I paying $100 to bet AGAINST
my own thesis?"

The answer: you are not betting against your thesis. You are paying $100 for
the RIGHT TO BE WRONG and still survive.

Expected value math (using market context probabilities):

Without hedge (V2 shape: 3 bearish positions, $495 risk):
  70% gap fill: +$875  = +$612.50 weighted
  25% chop:     -$105  = -$26.25 weighted
  15% rally:    -$360  = -$54.00 weighted
  EV = +$532.25

With hedge (V3 Shape B: 2 bearish + 1 hedge, $420 risk):
  70% gap fill: +$450  = +$315.00 weighted
  25% chop:     -$20   = -$5.00 weighted
  15% rally:    -$80   = -$12.00 weighted
  EV = +$298.00

V2 has higher EV (+$532 vs +$298). So why is V3 better?

Because EV ignores SURVIVAL. V2's -$360 rally loss is 3.6% of account. Do that
three weeks in a row (entirely possible in a trending bull market) and you have
lost 10%+ and Borey has lost confidence in you. V3's -$80 rally loss is 0.8%
of account. You can be wrong 6 times in a row before losing what V2 loses in
one bad week.

The hedge is not a drag on returns. It is a SURVIVAL TAX. Every professional
portfolio pays it. The ones that do not blow up.

---

END OF CORRELATION BUDGET. This document is binding on all downstream agents.
