# Hedged Bearish — SPX Gap Fill with Ceasefire Protection

**Date drafted:** 2026-04-06
**Market context:** SPX ~6783 after gap up from ~6610 on US-Iran ceasefire news. VIX ~20. PCE Thursday 4/9, CPI Friday 4/10. Swarm analysis shows 40% probability the ceasefire holds and rally extends to SPX 6900+. Gap fill to ~6610 (SPY ~661) remains the base case at 45-50% probability. Chop scenario (SPX 6750-6830) is 10-15%.

**Problem this solves:** Position 01 (aggressive puts) is naked directional — if ceasefire gains credibility over the weekend and SPX rips to 6900 Monday, you eat the full premium loss. That is a coin-flip mentality. This position says: "I am bearish, but I acknowledge the 40% bull case is real, and I refuse to blow up on it."

---

## POSITION: Bear Put Spread + OTM Call Kicker ("Bearish Fence")

### Leg 1 — Bearish: SPY Apr 11 675/660 Bear Put Spread

- **Action:** Buy SPY Apr 11 675P, Sell SPY Apr 11 660P
- **Why these strikes:** 675P is ~$0.50 OTM (SPY ~678), captures the move quickly on any dip. 660P short leg is just below the gap fill target (SPY 661) — you keep nearly all profit through the full gap fill and only give up the last dollar of overshoot. $15-wide spread gives excellent reward structure.
- **Entry price estimate:** $4.20 debit per spread (675P costs ~$6.50, 660P sells for ~$2.30 at VIX 20, 4 DTE)
- **Contracts:** 2 spreads (2 x $420 = $840 total debit)
- **Max profit:** $15.00 width - $4.20 debit = $10.80 per spread x 2 = $2,160 (if SPY at or below 660 at expiry)
- **Max loss on this leg:** $840 (total debit paid — occurs if SPY stays above 675 at expiry)

### Leg 2 — Hedge: SPY Apr 11 685C (OTM Call Kicker)

- **Action:** Buy SPY Apr 11 685C
- **Why this strike:** 685 is ~$7 OTM from current SPY ~678. It only activates if the ceasefire rally extends hard (SPX 6850+). This is not meant to profit — it is insurance. If SPX rips to 6900 (SPY ~690), this call goes from ~$0.80 to ~$6.00+, recovering a large chunk of the put spread loss.
- **Entry price estimate:** $0.80 per contract
- **Contracts:** 2 contracts (2 x $80 = $160 total debit)
- **Max loss on this leg:** $160 (premium paid — occurs if SPY stays below 685)

---

## Combined Position Summary

| Metric | Value |
|---|---|
| **Total cost (max risk)** | $840 + $160 = **$1,000** |
| **Account risk** | 10% of $10,000 — elevated but justified by the hedge structure. True catastrophic loss is limited to $1,000 in ALL scenarios. |
| **Breakeven on downside** | SPY ~670.80 (675 - 4.20 put spread cost) |

---

## Scenario Analysis

### Scenario 1: Gap fills to SPY 661 (SPX ~6610) — BASE CASE (45-50%)

- Bear put spread: Both puts deep ITM. Spread worth ~$14.00 at expiry (675-661=$14, capped at $15 width). Profit = ($14.00 - $4.20) x 2 = **+$1,960**
- Call kicker: Expires worthless. Loss = -$160
- **Net P&L: +$1,800**
- **Return on capital: +180%**

### Scenario 2: Ceasefire rally extends to SPY 690 (SPX ~6900) — BULL CASE (40%)

- Bear put spread: Both puts expire worthless. Loss = -$840
- Call kicker: 690 - 685 = $5.00 intrinsic. Value ~$5.00+. Proceeds = $5.00 x 2 = $1,000. Profit = $1,000 - $160 = **+$840**
- **Net P&L: -$840 + $840 = ~$0 (approximately breakeven)**
- **This is the magic of the hedge.** The 40% bull scenario does not hurt you. Compare to Position 01 which loses 100% of premium in this scenario.

### Scenario 3: Chops sideways at SPY 678 (SPX ~6780) — CHOP CASE (10-15%)

- Bear put spread: 675P expires ~$0 (SPY above strike), 660P expires worthless. Spread worth ~$0. Loss = -$840
- Call kicker: 685C expires worthless. Loss = -$160
- **Net P&L: -$1,000**
- **This is the worst case** — and it is defined and survivable. You lose exactly $1,000, which is 10% of the account. Painful but not fatal. And this is the LEAST likely scenario.

### Scenario 4: Partial gap fill to SPY 668 (SPX ~6680) — MODERATE BEAR (likely interim)

- Bear put spread: Spread worth ~$7.00 (675-668). Profit = ($7.00 - $4.20) x 2 = **+$560**
- Call kicker: Expires worthless. Loss = -$160
- **Net P&L: +$400**
- **Even a partial gap fill pays you.** You do not need the full $170-point move.

---

## Entry Plan

- **Day:** Monday 2026-04-07
- **Time:** 9:50-10:15 ET — let opening volatility settle. Enter all three legs as a single order if your broker supports multi-leg, otherwise enter the bear put spread first, then the call.
- **Trigger to enter:** SPY trading between 676-682. This is the sweet spot where puts are not yet too expensive and calls are still cheap.
- **Skip conditions:**
  - SPY opens above 684: Ceasefire rally is already extending. The call kicker is too expensive and the put spread is too cheap. Wait for a pullback or skip entirely.
  - SPY opens below 673: Gap fill is already in motion. You missed the best entry. Consider Position 01 (naked put) instead since downside momentum is confirmed.
  - VIX drops below 16: Market is too complacent. Options are cheap but the catalyst is gone. No trade.

---

## Management Rules

1. **At SPY 668 (partial gap fill):** Consider closing the bear put spread for ~$7.00/spread. You have +$400 net profit. Take it if it is Wednesday or later (theta will eat the remaining value). Let it ride if it is still Monday/Tuesday.
2. **At SPY 661 (full gap fill):** Close everything. Take the +$1,800 and walk away. Do not get greedy hoping for overshoot — the short 660P leg caps you anyway.
3. **If SPY breaks above 685 on Monday/Tuesday:** The call kicker is now working. Do NOT panic-sell the put spread at a loss. The hedge is doing its job. If SPY hits 690, the call kicker approximately offsets the put spread loss. Hold both sides.
4. **Thursday morning (1 DTE):** If the trade has not moved significantly in either direction, close all legs for whatever they are worth. Do not hold 1 DTE into CPI Friday with a spread position — gamma risk is extreme and you cannot manage it intraday.
5. **Hard stop:** If total position value drops below $300 (from $1,000 entry) AND the call kicker is not appreciating, exit everything. Do not watch $1,000 go to $0.

---

## Why Hedged — The New Trader's Edge

This position exists because you are a new trader and **surviving the learning curve is more important than maximizing any single trade.**

- Position 01 (aggressive puts) has a better payout in the bear case (~$720 profit on 1 contract vs ~$1,800 here on more capital). But Position 01 has ZERO protection in the bull case — you lose 100% of premium.
- This position costs more ($1,000 vs $480) but has a fundamentally different risk profile: **you cannot lose catastrophically in any scenario.** The worst case is -$1,000 and the most likely bad scenario (rally to 690) is approximately breakeven.
- Borey will respect the risk management. Showing discipline with a hedged structure builds trust. Blowing up on a naked directional bet because "the gap should fill" is how traders wash out.
- The swarm said 40% chance the ceasefire holds. That is not a number you ignore. That is a number you respect by paying $160 for insurance.

**Think of it this way:** The call kicker costs $160. If you run this trade 10 times, the 4 times the rally extends, the kicker saves you ~$840 each time ($3,360 total saved). The 6 times it does not rally, you lose $160 each ($960 total wasted on insurance). Net insurance value over 10 trades: +$2,400. The hedge has POSITIVE expected value at 40% rally probability.

---

## Comparison to Position 01

| Metric | Position 01 (Aggressive Put) | Position 10 (Hedged Bearish) |
|---|---|---|
| Total risk | $480 (1 contract) | $1,000 (spread + call) |
| Gap fill profit (SPY 661) | +$720 (150%) | +$1,800 (180%) |
| Rally loss (SPY 690) | -$480 (100% loss) | ~$0 (breakeven) |
| Chop loss (SPY 678) | -$200 (at stop) | -$1,000 (max) |
| Requires stop discipline | Yes (must exit at $2.80) | No (losses are structurally capped) |
| Complexity | Simple | Moderate (3 legs) |

**Recommendation:** If you run ONE position, run this one. Position 01 is fine as a learning trade with 1 contract, but this is how real traders structure risk. You pay more, but you sleep Monday night regardless of what the ceasefire headlines say.
