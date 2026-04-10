# 10: PORTFOLIO CONSTRUCTION + STRESS TEST

**Date:** 2026-04-09 (Thursday, post-PCE)
**Account:** $10,000
**SPY:** $679.58 | VIX: ~20 | PCR: 1.324 (EXTREME FEAR)
**Risk Constitution:** $500 max portfolio risk, $200 max per position, 3 max positions, $400 weekly circuit breaker

---

## CANDIDATE ELIMINATION: FROM 8 TO 4

### Eliminated Candidates

| # | Candidate | Risk | Why Eliminated |
|---|-----------|------|----------------|
| 3 | Bull put $659/$657 Apr 11 | $180 | Risk/reward is catastrophic: $180 risk for $23 max profit (1:8 R:R). The EV is marginally positive but one bad week wipes 8 winning weeks. It contributes almost nothing to portfolio profit while consuming a full position slot and significant risk budget. The $23 max credit is noise, not edge. |
| 6 | Crash backspread sell $658P/buy 3x $640P May 16 | $130 entry, $1,930 max loss | **VIOLATES Risk Constitution Section 1.** Max loss at expiry is $1,930 -- nearly 10x the $200 per-position ceiling. The "managed stop" argument does not hold: if SPY gaps to $645 overnight (through the gamma flip), there is no opportunity to stop out. The danger zone ($640-$658) is exactly where a ceasefire-collapse scenario pins SPY. The 3-leg structure also violates Section 8 (max 2 legs per position). Brilliant as a standalone concept, but unconstitutional. |
| 5 | CPI strangle $670P/$685C Apr 16 | $200 | Uses the full $200 risk budget on a non-directional position that requires a large move ($668 or $687) just to break even. Combined theta of -$24/day bleeds 12% of premium daily. The "chop at $676-$680" scenario (40% probability per the strangle's own analysis) produces a $160 loss. In a portfolio context, this is dead weight -- it doesn't complement directional positions, it competes with them for risk budget while needing a different catalyst (magnitude) than the core thesis (direction). |
| 8 | Diagonal $670P/$660P Apr25/Apr17 | $185 | **Violates Risk Constitution Section 8** ("vertical spreads only -- no diagonals"). The document itself acknowledges this conflict. Beyond the constitutional issue: the diagonal is functionally a more complex version of Candidate 1 (same strikes, same thesis) that adds rolling management overhead a first-week trader should not manage. Two roll decisions, assignment monitoring on American-style puts, and weekly short-leg management create cognitive overload that the constitution explicitly warns against (Section 8: "You have never managed a multi-leg position through a volatile session"). |

### Advancing Candidates

| # | Candidate | Risk | Direction | Expiry | Role |
|---|-----------|------|-----------|--------|------|
| 1 | Put spread $670/$660 Apr 17 | $200 | Bearish | Apr 17 | Core directional thesis |
| 2 | Bear call $683/$688 Apr 17 | $130 | Bearish | Apr 17 | Premium collection + theta |
| 4 | USO $80/$86C May 16 | $160 | Bullish (oil) | May 16 | Decorrelated catalyst play |
| 7 | Bull call $680/$687 Apr 25 | $135 | Bullish (SPY) | Apr 25 | Anti-correlation hedge |

---

## PORTFOLIO SELECTION: PICK 3

### Why 3 and Not 4

The Risk Constitution caps simultaneous positions at 3 (Section 1). Even if it allowed 4, the combined risk of all 4 candidates is $200 + $130 + $160 + $135 = $625, which exceeds the $500 portfolio risk cap. We must cut one.

### The Cut: Candidate 2 (Bear Call $683/$688)

The bear call is the weakest link for three reasons:

1. **Correlation with Candidate 1.** Both are bearish SPY with Apr 17 expiry. In a rally, BOTH lose simultaneously. The constitution requires max 2 same-direction bearish positions. With Candidate 1 already occupying one bearish slot, the bear call fills the second -- but then the portfolio has 2 bearish SPY bets on the same expiry. A single gap-up Monday invalidates both.

2. **Thin edge, asymmetric downside.** The bear call's own analysis admits "raw EV: -$13.00" at the mechanical stop. The adjusted EV is +$7. Seven dollars. On a trade that can lose $130 in a single morning if the $680 wall cracks. The 1:1 managed R:R is honest but uninspiring.

3. **Portfolio construction logic.** With Candidate 1 (bearish SPY), Candidate 4 (bullish oil), and Candidate 7 (bullish SPY), the portfolio has: 1 bearish, 1 oil-independent, 1 bullish hedge. This is the most diversified possible configuration. Adding the bear call makes it 2 bearish + 1 oil + 1 bullish, which over-weights the bear thesis that we only hold at 4/10 conviction on SPY direction.

### THE FINAL 3

| Position | Candidate | Structure | Risk | Direction | Expiry | Why Selected |
|----------|-----------|-----------|------|-----------|--------|--------------|
| **Pos 1** | #1 Put spread | Buy $670P / Sell $660P, Apr 17 | **$200** | Bearish SPY | Apr 17 (8 DTE) | **Core thesis.** The gamma floor break trade. Long strike at the exact $670 gamma floor, short at the $660 high-OI level. 4:1 R:R at $2.00 entry. Captures the $670-to-$660 air pocket if CPI/Islamabad pushes SPY through dealer support. Best risk/reward of all 8 candidates. |
| **Pos 2** | #4 USO oil | Buy $80C / Sell $86C, May 16 | **$160** | Bullish oil | May 16 (37 DTE) | **Decorrelation.** Independent of SPY GEX, dealer flow, and gamma levels. The only candidate that trades the PRIMARY catalyst (Hormuz/ceasefire) directly through oil, not through equity proxies. 2.75:1 R:R. 37 DTE survives multiple news cycles. Wins when ceasefire collapses even if SPY is flat -- the critical scenario where Pos 1 underperforms. |
| **Pos 3** | #7 Bull call | Buy $680C / Sell $687C, Apr 25 | **$135** | Bullish SPY | Apr 25 (16 DTE) | **Anti-correlation hedge.** Insurance against the scenario where every bearish/oil thesis is wrong: ceasefire holds, Islamabad framework succeeds, SPY squeezes through $685 ceiling. $135 buys up to $565 of catastrophic-scenario protection. PCR at 1.324 historically precedes rallies 61% of the time at 5 days. Without this hedge, a rally to $690 is an unmitigated portfolio loss. |

### Portfolio Risk Budget

```
Position 1 (put spread):   $200  (40% of $500 budget)
Position 2 (USO oil):      $160  (32% of $500 budget)
Position 3 (bull call):    $135  (27% of $500 budget)
                           -----
TOTAL PORTFOLIO RISK:      $495  (99% of $500 budget)  PASSES $500 cap.
Cash remaining:          $9,505  PASSES $9,000 minimum.
Max single position:       $200  = 40% of budget. PASSES 50% cap ($250).
Bearish count:                1  (Pos 1). PASSES max 2.
Bullish count:                2  (Pos 2 oil-bullish, Pos 3 SPY-bullish). PASSES max 2.
Non-bearish positions:        2  (Pos 2 + Pos 3). PASSES min 1 non-bearish.
Different expiry dates:       3  (Apr 17, May 16, Apr 25). PASSES min 2.
Positions:                    3  PASSES max 3.
```

---

## WHAT EACH POSITION ADDS

### Pos 1: The Core Thesis ($200 risk)

This IS the gap-fill trade. It profits specifically when SPY breaks the $670 gamma floor and falls toward the $660 high-OI put level. The GEX air pocket between $670 and $658.66 is the structural corridor where dealer support evaporates. The long strike sits AT the floor; the short strike sits AT the next structural level. This is the most GEX-aligned trade in the portfolio.

**Adds:** Directional exposure to the primary bearish thesis (ceasefire collapse, CPI miss, Islamabad failure). 4:1 R:R if thesis hits.

### Pos 2: The Decorrelator ($160 risk)

Oil is the PRIMARY catalyst. The ceasefire is about Hormuz, not about SPY gamma levels. If the ceasefire collapses, oil moves first and fastest ($94 to $110-120 in days). If the ceasefire holds but SPY chops (the scenario where Pos 1 bleeds), oil holds flat or drifts -- USO does not crash on SPY chop. This is the only position in the portfolio that is truly independent of SPY microstructure.

**Adds:** Catalyst independence. Wins in the "ceasefire collapses but SPY is flat" scenario that no other position captures. Different underlying, different expiry, different thesis mechanism.

### Pos 3: The Fire Extinguisher ($135 risk)

Every analysis in this project says the ceasefire is unenforceable and SPY should pull back. But PCR at 1.324 has historically preceded rallies 61% of the time. If the ceasefire holds, if Islamabad produces a framework, if the 40% squeeze probability materializes -- Pos 1 loses $200 and Pos 2 loses $160 (oil drifts lower). That is $360 of loss with nothing to offset it. Pos 3 catches the squeeze. At SPY $687, this position pays $565, offsetting the entire combined loss of Pos 1 + Pos 2.

**Adds:** Portfolio survival in the "we are wrong about everything" scenario. Converts a $360 loss into a $200+ gain.

---

## PORTFOLIO GREEKS (ESTIMATED)

| Greek | Pos 1 (put spread) | Pos 2 (USO call) | Pos 3 (bull call) | **Net Portfolio** |
|-------|-------------------|-------------------|-------------------|-------------------|
| **Delta** (SPY-equiv) | -30 to -40 | 0 (different underlying) | +19 | **-11 to -21** |
| **Gamma** | +0.02 | N/A (USO) | +0.01 | **+0.03** (SPY) |
| **Theta** (/day) | -$10 to -$14 | -$3 to -$5 | -$3 | **-$16 to -$22** |
| **Vega** (per 1% IV) | +$10 | +$8 (USO IV) | +$5 | **+$15** (SPY) + $8 (USO) |

**Net portfolio delta: -11 to -21 SPY-equivalent.** Well within the -150 to +150 constitutional limit. The portfolio leans slightly bearish but is not a concentrated directional bet.

**Net theta: -$16 to -$22/day.** This is the daily cost of holding the portfolio. At $20/day, the portfolio bleeds ~$100 over a full trading week if nothing moves. Acceptable given the $495 risk budget and the catalyst-dense calendar (CPI Friday, Islamabad Saturday, Monday open).

---

## STRESS TEST: 6 SCENARIOS

### Methodology

P&L estimates use the position details from each candidate's analysis, adjusted for the specific SPY levels in each scenario. For Pos 2 (USO), SPY level is translated to crude oil impact based on the correlation framework in the USO analysis: ceasefire collapse = oil $110+, chop = oil flat at $94, rally = oil drifts to $88-90.

All P&L figures are per-contract for 1 contract of each position.

---

### Scenario 1: GAP FILL ($661)

SPY drops $18.58 from $679.58 to $661. This is through the gamma floor ($670), through the air pocket, and near the gamma flip ($658.66). VIX likely ~25-28.

| Position | P&L | Reasoning |
|----------|-----|-----------|
| **Pos 1** (put spread $670/$660) | **+$350 to +$400** | Long $670P is $9 ITM, short $660P is $1 ITM. Spread worth ~$7.50-8.00 with time remaining. Minus $2.00 debit. Close at 50% target ($6.00) or hold for more. |
| **Pos 2** (USO $80/$86C) | **+$50 to +$150** | Gap fill likely triggered by ceasefire stress. Oil moves from $94 to $97-100 on Hormuz concerns. USO from $78 to $80-82. Spread worth $50-250 intrinsic. Net after $160 debit. |
| **Pos 3** (bull call $680/$687) | **-$120 to -$135** | SPY at $661 destroys call value. Spread worth $0-$0.15. Near total loss of $135 debit. |
| **TOTAL** | **+$265 to +$415** | |

**Verdict:** Strong win. The core thesis hits. Oil provides a modest kicker. The bull hedge dies as designed -- it was insurance you did not need. Well within all risk limits.

---

### Scenario 2: CHOP ($676-$680)

SPY grinds sideways in the $676-$680 range for the week. No CPI surprise. Islamabad talks produce vague "progress." VIX drifts to 18-19.

| Position | P&L | Reasoning |
|----------|-----|-----------|
| **Pos 1** (put spread $670/$660) | **-$60 to -$120** | Both legs OTM. Theta decay erodes the spread to $0.80-$1.40 by Wed Apr 15 time stop. Loss = $200 - ($80 to $140) = -$60 to -$120. |
| **Pos 2** (USO $80/$86C) | **-$20 to -$40** | Oil flat at $94. USO drifts. Theta bleeds ~$4/day for a week. Spread loses $20-40 in value. Still has 30+ DTE -- manageable decay. Position not closed yet. |
| **Pos 3** (bull call $680/$687) | **-$20 to -$40** | SPY flat at $679. Spread decays from $1.35 to $1.00-$1.15 over a week (16 DTE, slow theta). Not alarming. Position not closed yet. |
| **TOTAL** | **-$100 to -$200** | |

**Verdict:** Manageable loss. The worst chop scenario is -$200, well below the $400 circuit breaker. Pos 2 and Pos 3 survive with most of their value due to longer-dated expiries. Only Pos 1 takes meaningful damage from theta. This is the "paying tuition" week -- no thesis hit, no disaster.

---

### Scenario 3: RALLY ($690)

SPY rallies $10.42 from $679.58 to $690. Ceasefire holds. Islamabad produces a framework. VIX drops to 16-17. Oil drifts to $88-90.

| Position | P&L | Reasoning |
|----------|-----|-----------|
| **Pos 1** (put spread $670/$660) | **-$170 to -$200** | Puts crushed. Spread worth $0-$0.30 by time stop. Near total loss. Constitution Section 7: SPX 6900 (SPY $690) intraday = close ALL immediately. |
| **Pos 2** (USO $80/$86C) | **-$80 to -$120** | Oil drops to $88-90 on ceasefire. USO drops to $73-74. Spread deep OTM. With 30+ DTE, extrinsic value survives at ~$40-80. Loss: $160 - ($40 to $80) = -$80 to -$120. |
| **Pos 3** (bull call $680/$687) | **+$400 to +$500** | SPY at $690 blows through $687 short strike. Spread near max value ($7.00) with time remaining. Call at expiry/near: $565. Pre-expiry with DTE: $500-$600 minus $135 debit. The hedge pays off. |
| **TOTAL** | **+$100 to +$200** | |

**Verdict:** THE HEDGE WORKS. Without Pos 3, this scenario produces -$250 to -$320 loss. WITH Pos 3, the portfolio is net positive. The bull call converts a rally disaster into a small win. This is exactly why the position exists.

---

### Scenario 4: CRASH ($640)

SPY crashes $39.58 from $679.58 to $640. Ceasefire collapses violently. Hormuz re-closes. Oil spikes to $115-120. VIX to 35+. Full panic.

| Position | P&L | Reasoning |
|----------|-----|-----------|
| **Pos 1** (put spread $670/$660) | **+$800** | Both legs deep ITM. Spread at max value ($10.00). Full $800 profit. Close at any time -- this is the max. |
| **Pos 2** (USO $80/$86C) | **+$440** | Oil at $115-120. USO at $88-93. Spread at max value ($6.00). Full $440 profit. The oil thesis hits perfectly. |
| **Pos 3** (bull call $680/$687) | **-$135** | Total loss. SPY at $640 means calls are dust. Fire extinguisher not needed. |
| **TOTAL** | **+$1,105** | |

**Verdict:** Home run. Pos 1 and Pos 2 both max out. The combined $1,240 in profits dwarfs the $135 hedge loss. This is the scenario where decorrelation is irrelevant -- everything moves in the same direction. The portfolio captures it from two independent angles (SPY + oil).

---

### Scenario 5: CPI SHOCK DOWN ($665, Friday)

Hot March CPI (captures oil spike). SPY gaps down $14.58 to $665 by Friday close. VIX spikes to 24-26. Oil holds at $94-96 (CPI is backward-looking, not a live oil catalyst).

| Position | P&L | Reasoning |
|----------|-----|-----------|
| **Pos 1** (put spread $670/$660) | **+$200 to +$300** | Long $670P is $5 ITM. Short $660P still OTM. Spread worth ~$4.00-$5.00 with 5 DTE remaining (Apr 17 expiry). Close at 50% target ($6.00 if continues to fall) or hold for Mon. Profit: $200-$300 after $200 debit. |
| **Pos 2** (USO $80/$86C) | **-$10 to +$20** | Oil flat. CPI does not move crude directly. USO unchanged. Minimal theta impact over 1 day. Essentially flat. |
| **Pos 3** (bull call $680/$687) | **-$90 to -$110** | SPY at $665 kills calls. Spread worth $0.25-$0.45 (16 DTE saves some extrinsic). Loss: $90-$110. |
| **TOTAL** | **+$80 to +$210** | |

**Verdict:** Solid. The core thesis trade does its job. Oil is a non-event (CPI is backward-looking). The hedge bleeds but retains some value due to 16 DTE. Net positive across the portfolio.

---

### Scenario 6: CEASEFIRE COLLAPSE MONDAY ($655)

Islamabad talks fail Saturday. Sunday futures gap down. Monday open: SPY at $655 after price discovery. VIX spikes to 26-30. Oil jumps to $100-105 on Hormuz re-closure fears.

| Position | P&L | Reasoning |
|----------|-----|-----------|
| **Pos 1** (put spread $670/$660) | **+$500 to +$600** | Long $670P is $15 ITM. Short $660P is $5 ITM at $655. Spread worth $8.00-$9.50 with 4 DTE. Close: $600-$750 proceeds minus $200 debit. Close at or near the 50% target. |
| **Pos 2** (USO $80/$86C) | **+$100 to +$240** | Oil at $100-105. USO at $82-84. Spread worth $200-$400. Net: $40-$240 after $160 debit. Approaching 50% profit target. |
| **Pos 3** (bull call $680/$687) | **-$120 to -$135** | SPY at $655 obliterates calls. Near total loss. |
| **TOTAL** | **+$465 to +$705** | |

**Verdict:** Strong win. Both thesis legs (SPY bearish + oil bullish) fire simultaneously. This is the decorrelation payoff -- the ceasefire collapse moves both SPY and oil in the portfolio's favor. The hedge dies, which is correct: you do not need fire insurance when the house is not on fire.

---

## STRESS TEST SUMMARY TABLE

| Scenario | SPY | Pos 1 (put) | Pos 2 (USO) | Pos 3 (bull) | **TOTAL** | Circuit Breaker? |
|----------|-----|-------------|-------------|--------------|-----------|-------------------|
| Gap fill | $661 | +$375 | +$100 | -$128 | **+$347** | NO (profitable) |
| Chop | $676-680 | -$90 | -$30 | -$30 | **-$150** | NO (-$150 < $400) |
| Rally | $690 | -$185 | -$100 | +$450 | **+$165** | NO (profitable) |
| Crash | $640 | +$800 | +$440 | -$135 | **+$1,105** | NO (profitable) |
| CPI shock | $665 Fri | +$250 | +$5 | -$100 | **+$155** | NO (profitable) |
| Ceasefire collapse | $655 Mon | +$550 | +$170 | -$128 | **+$592** | NO (profitable) |

### Worst Case Analysis

**Single worst scenario: Chop ($676-$680) = -$150.** This is well below the $400 weekly circuit breaker and well below the $300 "close worst performer" threshold (Section 5).

**Worst single-position loss in any scenario: -$200 (Pos 1 in rally).** This is AT the constitutional maximum, not above it. The position was sized to this limit.

**No scenario produces combined losses exceeding $300.** The chop scenario at -$150 is the worst. Even in that case, Pos 2 and Pos 3 retain most of their value due to longer expiries (37 DTE and 16 DTE respectively).

---

## "ALL POSITIONS LOSE" CORRELATION TEST (CONSTITUTION SECTION 5)

**Question: "In what scenario do ALL current positions lose money simultaneously?"**

**Answer: SPY chops at $676-$680 with oil flat.** This is the only scenario where all three positions bleed simultaneously (Pos 1 theta decay, Pos 2 flat theta, Pos 3 flat theta). Combined loss: ~$150.

**$150 < $400 limit.** PASSES the correlation test.

No other scenario produces simultaneous losses across all three positions:
- Gap fill: Pos 1 wins, Pos 2 wins or flat, Pos 3 loses. NOT all-lose.
- Rally: Pos 1 loses, Pos 2 loses, Pos 3 WINS. NOT all-lose.
- Crash: Pos 1 wins, Pos 2 wins, Pos 3 loses. NOT all-lose.
- CPI shock: Pos 1 wins, Pos 2 flat, Pos 3 loses. NOT all-lose.
- Ceasefire collapse: Pos 1 wins, Pos 2 wins, Pos 3 loses. NOT all-lose.

The portfolio is structurally resistant to correlated loss. The "all-lose" scenario is the lowest-magnitude scenario ($150), not the highest.

---

## RISK CONSTITUTION FINAL AUDIT

| Rule | Limit | Portfolio | Status |
|------|-------|-----------|--------|
| Max risk per position | $200 | $200 / $160 / $135 | **PASS** |
| Max total portfolio risk | $500 | $495 | **PASS** |
| Max simultaneous positions | 3 | 3 | **PASS** |
| Max correlated same-direction | 2 | 1 bearish (Pos 1), 2 bullish-ish (Pos 2+3) | **PASS** |
| Min cash reserve $9,000 | $9,000 | $9,505 | **PASS** |
| Max single position 50% of budget | $250 | $200 (40%) | **PASS** |
| 2-leg max per position | 2 | All 2-leg verticals | **PASS** |
| No naked short options | -- | All short legs covered | **PASS** |
| Min 4 DTE at entry | 4 | 8 / 37 / 16 | **PASS** |
| Net delta within -150/+150 | -150 to +150 | ~-15 (SPY-equiv) | **PASS** |
| All-positions-losing < $400 | $400 | $150 (chop scenario) | **PASS** |
| Max loss in any single scenario | $300 (user rule) | $200 (rally, Pos 1 max loss) | **PASS** |
| At least 1 non-bearish position | 1 | 2 (Pos 2 + Pos 3) | **PASS** |
| At least 2 different expiry dates | 2 | 3 (Apr 17, May 16, Apr 25) | **PASS** |
| Weekly circuit breaker | $400 | Worst scenario: -$150 | **PASS** |

**All 15 checks: PASS. Zero exceptions. Zero waivers.**

---

## ENTRY PRIORITY ORDER

| Priority | Position | Entry Window | Why First |
|----------|----------|-------------|-----------|
| 1st | **Pos 2: USO oil** | Thu Apr 9, 10:00-11:30 AM ET | Oil does not depend on CPI. Enter before CPI (hot CPI is a tailwind -- you want to be positioned before it). Longest DTE means earliest entry preserves the most time value. |
| 2nd | **Pos 3: Bull call** | Thu Apr 9, 10:30-11:00 AM ET | Enter same day. Post-PCE IV crush makes calls cheaper. 16 DTE -- theta is slow, no urgency, but entering before CPI captures the CPI event as free optionality. |
| 3rd | **Pos 1: Put spread** | Thu Apr 9, 1:15-2:00 PM ET OR Fri Apr 10 post-CPI | Wait for post-PCE IV crush to compress put premiums. The $2.00 entry target is more achievable in the afternoon IV trough. If too expensive today, CPI Friday may crush IV further (if inline) or validate the thesis (if hot). |

---

## PORTFOLIO SUMMARY

```
=====================================================================
PORTFOLIO: 3 POSITIONS, $495 TOTAL RISK
=====================================================================

Pos 1: BUY 1x SPY Apr 17 $670P / SELL 1x SPY Apr 17 $660P
       Cost: $200 | Max profit: $800 | R:R 4:1 | Bearish SPY
       Thesis: Gamma floor break -> $670-$660 air pocket

Pos 2: BUY 1x USO May 16 $80C / SELL 1x USO May 16 $86C
       Cost: $160 | Max profit: $440 | R:R 2.75:1 | Bullish oil
       Thesis: Ceasefire collapse -> Hormuz -> oil $110+

Pos 3: BUY 1x SPY Apr 25 $680C / SELL 1x SPY Apr 25 $687C
       Cost: $135 | Max profit: $565 | R:R 4.2:1 | Bullish SPY
       Thesis: Portfolio hedge. Ceasefire holds -> squeeze -> $687

TOTAL RISK:       $495 ($500 cap)
CASH REMAINING:   $9,505 ($9,000 min)
WORST SCENARIO:   -$150 (chop)
BEST SCENARIO:    +$1,105 (crash)
CIRCUIT BREAKER:  CLEAR (worst -$150 vs $400 limit)
=====================================================================
```

**The portfolio survives every tested scenario.** It profits in 5 of 6 scenarios. The single loss scenario (chop, -$150) is 37.5% of the weekly circuit breaker, leaving $250 of headroom before the $400 trigger. No single position in any scenario exceeds $200 loss. The three-expiry, two-underlying structure provides genuine diversification, not the illusion of diversification that V2's 17 correlated positions created.

---

*"Three positions. Three expiries. Two underlyings. One thesis with a hedge against being wrong. The portfolio does not need SPY to crash, oil to spike, AND the squeeze to fail. It needs any ONE of those to happen. And if none of them happen, it loses $150 and walks away having followed every rule."*
