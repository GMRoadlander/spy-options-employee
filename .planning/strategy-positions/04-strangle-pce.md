# POSITION: PCE Strangle — "Ceasefire Catalyst"

**Date drafted:** 2026-04-06
**Playbook:** MPW Strangle (direction-agnostic, catalyst-driven)
**Thesis:** Ceasefire rally is fragile. PCE Thursday 8:30 AM is the trigger. If hot, the rally unwinds hard. If soft, the rally extends into CPI Friday. Either way the move exceeds what VIX 20 is pricing. Two macro catalysts in 48 hours with geopolitical tail risk = realized vol > implied vol.

---

## Setup Context

| Metric        | Value                  |
|---------------|------------------------|
| SPX           | ~6783                  |
| SPY           | ~$678                  |
| VIX           | ~20                    |
| Implied daily | ~1.26% ($8.55 on SPY) |
| Catalysts     | PCE Thu 8:30 AM, CPI Fri 8:30 AM |
| Regime        | Ceasefire rally, extended, vulnerable to reversal OR continuation |

---

## Position

**Action:** Buy 1 SPY $683 Call + Buy 1 SPY $673 Put

**Expiry:** Friday April 10 (weekly 0DTE for Friday, 1DTE at Thursday entry)

**Entry:** Wednesday April 8, between 3:00-3:45 PM ET (close before PCE)

### Entry Timing Rationale

Enter Wednesday afternoon, NOT Thursday morning. Reasons:

1. **IV crush risk if you enter Thursday pre-market** — options will already be bid up for the event. Wednesday close gives you the position before the crowd piles in Thursday AM.
2. **Theta is your enemy** — but with 1.5 trading days to expiry and TWO catalysts (PCE Thu + CPI Fri), the gamma payoff overwhelms theta. You are buying gamma cheaply relative to what these events historically deliver.
3. **Do NOT enter after PCE** — if you wait, the winning side is already expensive and the losing side is worthless. The strangle only works if you own both legs before the move.

---

## Cost Estimate

With SPY at $678, VIX ~20, and Friday expiry:

| Leg            | Strike | OTM by  | Est. Premium |
|----------------|--------|---------|-------------|
| $683 Call      | $683   | ~$5 (~0.74%) | ~$1.80     |
| $673 Put       | $673   | ~$5 (~0.74%) | ~$1.60     |
| **Total per strangle** | | | **~$3.40 ($340/contract)** |

*Note: These are estimates based on VIX 20, 1.5 DTE, ~0.74% OTM. Actual premiums depend on Wed close IV. If VIX spikes above 22 pre-entry, widen strikes to $684/$672 to keep cost under $3.50.*

---

## Sizing (2% Risk on $10K)

| Parameter       | Value         |
|-----------------|---------------|
| Account size    | $10,000       |
| Max risk (2%)   | $200          |
| Cost per strangle | ~$340       |
| **Quantity**    | **1 strangle** (risk = $340, which is 3.4%) |

**Sizing note:** One strangle at $340 exceeds 2% ($200) slightly. Two options to stay within 2%:

- **Option A (preferred):** Buy 1 strangle, accept 3.4% risk. MPW's playbook uses 2-5% for high-conviction catalyst trades. Back-to-back PCE+CPI with geopolitical fragility qualifies.
- **Option B (strict 2%):** Widen strikes to $685/$671 (~$7 OTM each). Cost drops to ~$2.00/strangle ($200 total). Breakevens get harder but still reachable on a 2 SD move. Less ideal.

**Recommendation: Option A. One contract. $340 risk.**

---

## Max Loss

**$340** — total premium paid. This happens ONLY if SPY closes between $673 and $683 at Friday expiry with both legs expiring worthless. In practice, you exit the loser before expiry (see exit rules), so realized loss is less than max.

---

## Breakeven at Expiry

| Direction | Breakeven       | Move Required |
|-----------|-----------------|---------------|
| Upside    | SPY > **$686.40** | +$8.40 (+1.24%) |
| Downside  | SPY < **$669.60** | -$8.40 (-1.24%) |

**Key insight:** VIX 20 implies 1.26% daily moves. The breakeven requires roughly a 1 SD move. With a macro catalyst like PCE, 1.5-2 SD moves are common. This is a fair-odds bet — you need the catalyst to deliver, which is the whole thesis.

---

## Profit Scenarios

### Scenario 1: PCE Hot (above consensus) — SPY Drops

PCE comes in hot (e.g., core PCE 0.4% vs 0.3% expected). Stagflation fear. Ceasefire rally reverses.

| Item         | Value                                    |
|--------------|------------------------------------------|
| SPY move     | -2.0% to ~$664.50 (13.5 pts)            |
| $673 Put     | Now $8.50 ITM, worth ~$8.70 (w/ residual TV) |
| $683 Call    | Worthless or ~$0.05                      |
| Gross P&L    | +$870 - $340 cost = **+$530 net**       |
| Return       | **+156% on risk**                        |

*If you follow exit rules and cut the call at $0.15 while the put is running, you recover ~$15 more.*

### Scenario 2: PCE Soft (below consensus) — SPY Rallies

PCE comes in cool (e.g., core PCE 0.2%). Goldilocks. Ceasefire rally accelerates into CPI.

| Item         | Value                                    |
|--------------|------------------------------------------|
| SPY move     | +1.5% to ~$688.15 (10.15 pts)           |
| $683 Call    | Now $5.15 ITM, worth ~$5.40             |
| $673 Put     | Worthless or ~$0.05                      |
| Gross P&L    | +$540 - $340 cost = **+$200 net**       |
| Return       | **+59% on risk**                         |

*Rally scenario pays less because upside grinds are slower than selloffs. But CPI Friday provides a second catalyst for the call to keep running.*

### Scenario 3: PCE Inline — Lose Scenario

PCE matches consensus exactly. No surprise. SPY drifts +/- 0.3%.

| Item         | Value                                    |
|--------------|------------------------------------------|
| SPY move     | ~$676-$680, stays in the dead zone       |
| $683 Call    | Decays to ~$0.40                         |
| $673 Put     | Decays to ~$0.30                         |
| Residual     | ~$70 recoverable                         |
| **Net loss** | **-$270** (not full -$340)               |

*This is the worst case. If PCE is a non-event, you still have CPI Friday as a second shot, but theta is brutal on 0DTE. Consider holding into Friday only if IV stays bid.*

---

## Exit Rules

These are NON-NEGOTIABLE. MPW's edge comes from disciplined exits, not from picking direction.

### Rule 1: Take Profit on Winner at 2x Premium
- If either leg hits $6.80 (2x the $3.40 strangle cost), **sell it immediately**.
- Do not wait for more. A 2x on the strangle is a great trade.

### Rule 2: Kill the Loser When Underlying Crosses Mid-Strike
- Mid-strike = $678 (midpoint of $673 and $683).
- If SPY breaks below $678 decisively (30-min candle close), the put is working — **kill the $683 call** at market. Don't hope for a reversal.
- If SPY breaks above $678 decisively, the call is working — **kill the $673 put** at market.
- "Decisively" = sustained move, not a wick.

### Rule 3: Time Stop — Do NOT Hold Both Legs Into Weekend
- If both legs are still open at **Friday 2:00 PM ET**, close the entire position.
- Weekend theta + gap risk on a political situation (ceasefire) is NOT compensated.
- If one leg is profitable and the other is near-zero, close both. Take the net.

### Rule 4: If PCE Is a Non-Event, Reassess for CPI
- If after PCE, SPY is flat and both legs are worth ~$0.30-$0.50 each, you have a decision:
  - **Hold for CPI** if total residual value > $0.50 (you're playing CPI for ~$50 of remaining risk).
  - **Close everything** if residual < $0.50. Don't burn the last $50 on a coin flip.

---

## Why Strangle, Not Straddle

| Factor           | Straddle (ATM)       | Strangle (OTM)        |
|------------------|----------------------|-----------------------|
| Strikes          | $678 Call + $678 Put | $683 Call + $673 Put  |
| Est. cost        | ~$6.80 ($680)        | ~$3.40 ($340)         |
| Max risk         | $680                 | $340                  |
| Breakeven range  | $671.20 - $684.80    | $669.60 - $686.40     |
| BE width         | $13.60               | $16.80                |
| Upside BE        | +1.0%                | +1.24%                |
| Downside BE      | -1.0%                | -1.24%                |

**The strangle costs half as much with only ~0.24% wider breakevens.** On a $10K account, the straddle would consume 6.8% of capital — unacceptable. The strangle keeps risk at 3.4% while maintaining a realistic payoff window. You give up a tiny edge on breakeven in exchange for cutting your dollar risk in half. For a 2% risk framework, the strangle is the only viable structure.

Additionally: straddles have higher vega exposure. If IV crushes after PCE (common for data releases), the straddle loses more on the non-moving leg. The strangle's OTM legs have less vega to give back.

---

## Risk Flags

- **IV expansion pre-event**: If VIX jumps to 23+ before Wednesday close, the strangle will be more expensive. Reassess cost. May need to widen strikes or reduce to half-size.
- **Ceasefire collapse before entry**: If geopolitical headlines blow up Monday/Tuesday, SPY may already be moving. The strangle thesis relies on pre-catalyst entry. If SPY moves 2%+ before Wednesday, the trade is stale — skip it.
- **Pin risk on Friday**: SPY weekly options have enormous OI at round strikes ($675, $680, $685). If SPY pins near $678-$680, both legs die. This is the dead zone.
- **Liquidity**: SPY weekly options are extremely liquid. No fill concerns. Use limit orders, mid-price. Do not market order.

---

## Summary

| Field              | Value                           |
|--------------------|---------------------------------|
| Position           | Long 1x SPY Apr 10 $683C / $673P strangle |
| Entry              | Wed Apr 8, 3:00-3:45 PM ET     |
| Cost               | ~$3.40/strangle ($340 total)    |
| Max loss           | $340 (3.4% of $10K)            |
| Upside breakeven   | $686.40 (+1.24%)                |
| Downside breakeven | $669.60 (-1.24%)                |
| Target             | 2x premium ($680 gross, +$340 net) |
| Worst case         | Both legs expire, -$340         |
| Edge               | Realized vol > implied vol on dual catalysts + geopolitical fragility |
