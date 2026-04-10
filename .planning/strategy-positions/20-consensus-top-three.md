# Consensus: Top 3 Positions for Borey Review

**Date:** 2026-04-06
**Synthesized from:** 9 position proposals (aggressive puts, conservative spread, premium seller, PCE strangle, butterfly, ratio spread, calendar, iron condor, hedged bearish)
**Selection criteria:** Defined risk, gap fill alignment, simplicity for a new trader, what an experienced trader respects, diversification across failure modes

---

## #1 BEST POSITION: Conservative Put Debit Spread (Position 02)

**BUY 1x SPY Apr 17 $676P / SELL 1x SPY Apr 17 $663P for ~$4.80 debit**

This is the best trade to present to Borey because it directly expresses the gap fill thesis with structurally capped risk and no ambiguity about what can go wrong. The 11 DTE expiry survives both PCE and CPI catalysts without the theta guillotine of a weekly, the strike selection is surgically aligned with the gap fill zone (short put at $663 captures 95% of the fill without requiring perfection), and the hard stop at $2.80 spread value enforces a $200 realized loss -- exactly 2% of the account. An experienced trader will respect that the strike justification, expiry choice, and exit rules are all internally consistent and that the new trader is not reaching for maximum leverage. This is the trade that says: "I have a thesis, I sized it correctly, and I know exactly when I am wrong."

- **Max risk:** $480 (debit), $200 realized with stop discipline
- **Max profit:** $820 at SPY $663 or below
- **Reward:Risk:** 1.71:1 (4.1:1 against realized risk with stop)
- **Breakeven:** SPY $671.20
- **Expiry:** Apr 17 (11 DTE -- survives PCE Thursday + CPI Friday)

---

## #2 SECOND BEST: Bear Call Credit Spread (Position 03)

**SELL 1x SPY Apr 17 $683C / BUY 1x SPY Apr 17 $686C for ~$0.90 credit**

This is the second-best because it profits from the gap fill thesis WITHOUT requiring the gap to actually fill -- SPY just needs to stay below $683, which it already is. The trade has a 72-75% probability of profit at entry, collects theta daily, and wins if the ceasefire fades, if macro data disappoints, OR if the market simply chops sideways. Critically, this position diversifies against Position #1: if the gap fill takes longer than expected and SPY drifts sideways at 675-680 for two weeks, the put spread from #1 bleeds theta while this credit spread quietly expires worthless for full profit. Borey will recognize premium selling on an overextended rally as a textbook institutional trade, and the 50% profit-take rule at $0.45 shows professional discipline rather than greed.

- **Max risk:** $210 per spread (2.1% of account -- fits the 2% rule)
- **Max profit:** $90 per spread
- **Reward:Risk:** 0.43:1 (but 72-75% probability of profit = positive expected value)
- **Breakeven:** SPY $683.90
- **Expiry:** Apr 17 (11 DTE)

**Size 1 spread for strict 2% compliance.** Add a second only after managing one full cycle.

---

## #3 HEDGE/ALTERNATIVE: Iron Condor (Position 08)

**SELL 1x SPY Apr 11 665P / BUY 1x SPY Apr 11 660P / SELL 1x SPY Apr 11 690C / BUY 1x SPY Apr 11 695C for ~$1.65 credit**

This is the hedge position because it profits from the scenario that kills both #1 and #2: a rangebound chop where SPY stays between 665 and 690 all week. If the gap fill thesis is dead wrong and the ceasefire rally is real but exhausts near current levels, the iron condor collects $165 while the put spread from #1 hits its stop for -$200. The net portfolio damage is only -$35 instead of -$200. The iron condor also introduces the new trader to premium selling and non-directional strategies -- showing Borey that the trader understands portfolio construction, not just directional bets. The 50% profit-take rule and the hard rule to close by Thursday before CPI demonstrate that the trader respects gamma risk into expiration.

- **Max risk:** $335 per condor (3.35% of account)
- **Max profit:** $165 per condor
- **Profitable range:** SPY $663.35 to $691.65 (286-point SPX window)
- **Probability of profit:** ~68-72%
- **Expiry:** Apr 11 (4 DTE -- close by Thursday before CPI)

---

## COMBINED PORTFOLIO: All 3 Positions

| Position | Cost/Credit | Max Risk | Max Profit | Wins When |
|----------|-------------|----------|------------|-----------|
| #1 Put Spread (02) | -$480 debit | $200 (with stop) | $820 | Gap fills to 663 |
| #2 Bear Call (03) | +$90 credit | $210 | $90 | SPY stays below 683 |
| #3 Iron Condor (08) | +$165 credit | $335 | $165 | SPY chops 665-690 |
| **TOTAL** | **-$225 net** | **$745 worst case** | **$1,075** | **Different scenarios** |

**Portfolio risk: $745 max = 7.45% of $10K account.** In practice, the iron condor and bear call cannot both hit max loss simultaneously (they would require SPY to be both above 686 AND outside 665-690, which is only the blow-up-higher scenario). Realistic worst case is $535-600.

**Correlation of failure:** These three positions do NOT all fail together. The put spread fails if SPY rallies hard. The bear call fails only if SPY breaks above 683.90. The iron condor fails only if SPY breaks below 663 or above 691. The only scenario that hurts all three is a sharp rally above 692 -- which requires the ceasefire to hold AND hot macro data to be shrugged off. That is the lowest-probability outcome.

---

## AVOID -- Positions Too Complex or Risky for a New Trader

**06 - Ratio Spread:** Has a naked short put leg that creates unlimited downside risk below $652.90. Requires Level 4 options approval, portfolio margin, and active management skills a new trader does not have. The margin requirement ($13,200+ per spread) exceeds the entire $10K account. A single gap-down Monday morning could wipe the account. Borey would question why a new trader is selling naked puts.

**05 - Butterfly (30 contracts):** The position itself is defined-risk and clever, but 30 contracts at $55 each is $1,650 at risk (16.5% of the account) on a lottery ticket that requires SPY to pin at exactly $661 at expiry. The profitable range is only $656.55 to $665.45 -- a 9-point window on a stock that moves 8+ points per day at VIX 20. Experienced traders use butterflies as kickers on top of core positions, not as the core itself. Present it to Borey as a concept for later, not a first trade.

**01 - Aggressive Naked Put:** Naked long puts with 4 DTE bleed theta at $0.80-1.00/day. The revised 1-contract version is defensible but the stop at $2.80 (a 42% premium loss) will likely trigger on normal intraday volatility before the thesis plays out. Position 02 (the put spread) expresses the same thesis with less theta exposure and a wider time window. Skip the naked put.

**04 - PCE Strangle:** Direction-agnostic, which contradicts the core gap-fill thesis. Costs $340 (3.4% of account) and needs a 1.24% move just to break even -- which is almost exactly the 1-day implied move at VIX 20, meaning you are paying fair value for a coin-flip. Strangles are an advanced volatility trade that requires precise entry timing (Wednesday afternoon) and active leg management. Not appropriate for a first trade presentation.

**07 - Calendar Spread:** Elegant theta structure but counter-intuitive failure mode: if the gap fills too fast (the bull thesis), the calendar LOSES money because both legs go deep ITM and the extrinsic differential collapses. A trade that loses when the thesis works too well is confusing for a new trader and hard to explain to Borey without sounding uncertain about the thesis.

**10 - Hedged Bearish (3-leg fence):** The analysis is excellent and the risk management is sophisticated, but $1,000 total risk (10% of account) on a 3-leg structure with a call kicker is too much complexity and too much capital for a new trader's first presentation. The insight about hedging the 40% bull case is valuable -- incorporate it mentally, but execute it through the simpler portfolio of #1 + #2 + #3 above, which achieves the same diversification with independent, manageable positions.

---

## ENTRY PLAN

### Monday, April 7, 2026

**Pre-market (8:00-9:30 AM ET):**
- Check SPY pre-market price. If above $684, stand down on all positions -- ceasefire rally is extending beyond expectations.
- Check VIX futures. If below 16, stand down -- market is too complacent for the gap fill thesis.
- If SPY pre-market is $673-682 and VIX is 18-23, proceed with entry plan.

**10:00-10:30 AM ET -- Enter Position #1 (Put Debit Spread):**
- After opening range settles, enter the SPY Apr 17 $676/$663 put debit spread.
- Limit order at $4.80 or better. Walk up to $5.00 maximum in $0.05 increments.
- Immediately set a GTC limit sell at $2.80 (stop loss = $200 realized loss).
- Set price alert at SPY $675 (thesis confirmation) and SPY $680 (danger zone).

**10:15-10:45 AM ET -- Enter Position #3 (Iron Condor):**
- Enter the SPY Apr 11 660/665P - 690/695C iron condor as a single 4-leg order.
- Limit order at $1.65 credit or better. Accept $1.50 minimum. Do not enter below $1.40 credit.
- Set alert: spread buyback at $0.82 (50% profit target).
- Set calendar reminder: Thursday Apr 10, 2:00 PM ET -- mandatory close before CPI Friday.

### Tuesday, April 8, 2026

**10:00-10:30 AM ET -- Enter Position #2 (Bear Call Credit Spread):**
- Wait one full session to let ceasefire enthusiasm normalize before selling calls.
- If SPY is still below $683, enter the SPY Apr 17 $683/$686 bear call spread.
- Limit order at $0.85 credit, walk to $0.80 minimum. Do not sell below $0.75.
- Set alert: spread value at $0.45 (50% profit -- close position).
- Set alert: spread value at $1.80 (stop loss -- close position).

**If SPY has broken above $685 by Tuesday open:** Do NOT enter the bear call. The thesis is weakened. Run only positions #1 and #3.

### Summary of Entry Sequence

| When | Position | Action |
|------|----------|--------|
| Mon 10:00 AM | #1 Put Spread | Buy $676/$663 put spread for ~$4.80 |
| Mon 10:15 AM | #3 Iron Condor | Sell 665/660P - 690/695C condor for ~$1.65 |
| Tue 10:00 AM | #2 Bear Call | Sell $683/$686 call spread for ~$0.90 |

**Total capital deployed:** ~$225 net debit (put spread cost minus credits received)
**Total max risk:** ~$745 (all three hit max loss simultaneously -- unlikely)
**Realistic worst case:** ~$535-600 (5.3-6.0% of account)

---

## What Borey Will See

A new trader who:
1. Has a clear thesis (gap fill) supported by statistical reasoning
2. Expressed it through three defined-risk positions that complement each other
3. Sized every position for survivability, not maximum profit
4. Has specific entry rules, exit rules, stop losses, and time stops for each position
5. Understands that the 40% bull case is real and has positioned the portfolio to limit damage if the thesis is wrong
6. Is presenting choices, not gambling on a single direction

That is what earns trust.
