# Position 06: 1x2 Put Ratio Spread — Gap Fill Play

**Date drafted:** 2026-04-06
**Underlying:** SPY (proxy for SPX ~6783)
**SPY spot:** ~$678
**VIX:** ~20
**Thesis:** Gap fill to ~$661 (SPX ~6610) within 1 week. Moderate pullback, not a crash.

---

## POSITION: "Gap Filler" 1x2 Put Ratio Spread

### Structure

| Leg | Action | Qty | Strike | Expiry | Est. Price |
|-----|--------|-----|--------|--------|------------|
| Long put | BUY | 1x | SPY 670P | Apr 11, 2026 | $3.10 |
| Short put | SELL | 2x | SPY 661P | Apr 11, 2026 | $1.10 ea |

- **Net debit:** $0.90 per spread ($90 per 1-lot)
- **Position size:** 3x ratio spreads = $270 total risk on entry
- **Capital at risk:** $270 debit + margin on naked short put (see Danger Zone)

### Why These Strikes

- **670 long strike:** ~1.2% below spot. Close enough to gain delta quickly on a selloff, but OTM enough to keep the entry cheap. This is your "funded" leg.
- **661 short strike:** Pinned exactly to the gap fill target at ~$661 (SPX ~6610). If SPY lands here at expiration, both short puts expire worthless-ish while the long put is $9 ITM. Maximum extraction.
- **Spread width:** 9 points ($900 per spread intrinsic at max profit).

---

## Payoff Profile (per 1-lot, x3 for full position)

### Max Profit: $810 per spread / $2,430 total

- **Occurs at:** SPY = $661.00 at expiration (the gap fill target)
- **Math:** Long 670P worth $9.00 intrinsic, both short 661P expire at $0.00, minus $0.90 debit = $8.10 net profit x 100 = $810

### Breakeven Points

- **Upper breakeven:** SPY = $669.10 (670 - 0.90 debit)
- **Lower breakeven:** SPY = $652.90 (661 - 8.10 net credit width)

### Profit Zone

- **SPY between $669.10 and $652.90** = profitable at expiration
- **Sweet spot:** $661 exactly = max profit ($2,430 on 3 spreads)
- **Good enough zone:** $665 to $657 = still capturing $500+ per spread

### Max Loss

- **Upside (SPY stays above $669.10):** Limited to net debit of $270 total. All options expire worthless. This is the "it didn't drop enough" scenario.
- **Downside (SPY crashes below $652.90):** One short put is covered by the long put. The OTHER short put is naked. Below $652.90, you lose $100 per point per spread, times 3 spreads = $300/point. If SPY hits $640 (a -5.6% crash): loss = ($652.90 - $640) x 100 x 3 = $3,870. If SPY hits $620 (a -8.5% crash): loss = ($652.90 - $620) x 100 x 3 = $9,870. Practically, the downside is a large but finite loss if SPY crashes through your short strikes. SPY going to zero = theoretical max loss of ~$195,870 (3 x $652.90 x 100), but that is a planet-ending scenario.

---

## Risk/Reward Summary

| Scenario | SPY at Expiry | P&L (3-lot) |
|----------|--------------|-------------|
| No move | $678 | -$270 (max upside loss) |
| Small dip | $670 | -$270 |
| Moderate dip | $665 | +$1,230 |
| **Gap fill (target)** | **$661** | **+$2,430** |
| Overshoot | $655 | +$1,530 |
| Danger starts | $652.90 | $0 (breakeven) |
| Sharp selloff | $645 | -$2,370 |
| Crash | $635 | -$5,370 |

**Risk/reward on the thesis:** Risk $270 to make $2,430 = **9:1 reward-to-risk** if the gap fills.

---

## Why a Ratio Spread (Not a Straight Vertical)

| Feature | 1x2 Ratio | Straight 670/661 Put Spread |
|---------|-----------|---------------------------|
| Entry cost | $0.90 debit | ~$2.00 debit |
| Max profit | $810/spread | $700/spread |
| Profit if SPY = $661 | $810 | $700 |
| Downside tail risk | YES (naked leg) | NO (capped) |
| Break-even range | Wider on upside | Narrower |

The ratio spread is **cheaper to enter** and has **higher max profit** because you collect premium from the extra short put. The tradeoff is the naked downside leg. This is a trade that says: "I think SPY pulls back to $661, not $630."

---

## Who This Is For

A trader who:
- Has a **specific downside target** (gap fill at ~$661) and conviction it holds as support
- Is comfortable with **defined upside risk** (max $270 loss if wrong direction)
- Is willing to accept **tail risk** below $652.90 in exchange for a 9:1 setup
- Understands margin requirements for naked short puts
- Will actively manage the position (this is NOT set-and-forget)

---

## Trade Management Rules

### Entry
- Enter when SPY is at or near $678. If SPY has already dropped to $670, the ratio is less attractive (long leg already ITM, short legs gaining delta).
- Target net debit of $1.00 or less. If the spread costs more than $1.50, skip it.

### Profit Taking
- **Close at 50-60% of max profit** ($400-$500 per spread, $1,200-$1,500 total). Do not hold to expiration hoping for perfection.
- If SPY hits $663-$659 with 2+ days remaining, the spread will be near max value with time premium still inflating the shorts. Take the money.

### Stop Loss / Defense
- **If SPY drops below $656 with 3+ days left:** The naked leg is picking up serious delta. Close the entire position or buy back the extra short puts.
- **If SPY drops below $652 at any point:** Close immediately. You are past breakeven and every point lower costs $300.
- **Rolling defense:** If SPY is at $655 with 2 days left and you still believe support holds, buy 1x SPY 650P for ~$0.50-$1.00 to convert the naked put into a covered put spread. This caps your downside at ~$650 and converts the 1x2 into a butterfly-like structure.

### If SPY Doesn't Drop
- If SPY stays above $674 by Wednesday (Apr 8), the puts will have decayed significantly. Close for a smaller loss than the full $270 — likely $100-$150 recoverable.
- Do NOT hold losing ratio spreads into expiration Friday hoping for a last-day miracle.

### The Nuclear Scenario
- If VIX spikes above 30 and SPY is crashing through $655 with momentum, do not wait. Close everything. A gap fill thesis does not survive a regime change into crisis selling. The naked short put will expand in value rapidly as vol explodes.

---

## Margin Requirement Estimate

Your broker will margin the naked short put (1 of the 2 short puts is uncovered). Typical requirement:
- ~20% of underlying x 100 shares = ~$13,200 per naked put
- With 3 spreads, that is 3 naked puts = ~$39,600 margin requirement
- **This exceeds a $10K account.** Realistically, a $10K account can support **1 ratio spread** ($13,200 margin for the naked leg, reduced by the premium collected and the long put coverage). Check with your broker for exact requirements.
- **Adjusted position size for $10K account: 1x ratio spread.** Net debit $90, max profit $810, breakeven at $652.90.

> **Important:** If your broker does not allow naked short puts (e.g., Robinhood, some basic accounts), this trade is not available. You need at minimum a Level 4 options approval (naked puts) or a portfolio margin account.

---

## Alternative: Credit Entry Variant

If you widen the spread or move the long strike closer to ATM:

- Buy 1x SPY 673P / Sell 2x SPY 661P
- Est. cost: $4.80 - 2($1.10) = $2.60 debit (more expensive, but more room)
- Or adjust to slightly different strikes to achieve a net credit entry

A **net credit** version (rare but possible in high-IV environments):
- Buy 1x SPY 667P / Sell 2x SPY 661P
- If 667P costs $1.80 and 661P pays $1.10 each: net credit = $0.40
- Narrower profit zone but you get PAID to enter the trade

---

## Key Greeks at Entry (approximate, per spread)

| Greek | Value | Meaning |
|-------|-------|---------|
| Delta | -8 to -12 | Slightly short delta — profits on down move |
| Gamma | Near zero (at entry) | Gamma risk builds as SPY approaches short strikes |
| Theta | +$5 to +$8/day | Net positive theta — time decay helps you (short 2 > long 1) |
| Vega | -$10 to -$15 | Net short vega — a vol spike hurts, vol crush helps |

The Greeks shift dramatically as SPY moves. Near $661, gamma becomes your enemy if it keeps falling, and your friend if it stalls there.

---

## Summary

This is a **precision trade** built around a specific gap fill thesis. You risk $90 (1-lot) to make $810 if SPY pulls back to exactly $661 by April 11. The danger is a crash below $653 where the naked short put creates accelerating losses. Active management is non-negotiable. Take profits at 50-60% of max, and cut the position immediately if SPY blows through the gap fill level with momentum.

**The ratio spread is the right tool when you have a target, not just a direction.**
