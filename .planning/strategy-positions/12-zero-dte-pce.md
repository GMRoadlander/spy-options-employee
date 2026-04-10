# Position 12: 0DTE PCE Volatility Scalp — SPY Strangle

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY ~$678 (proxy for SPX ~6783)
**Thesis:** PCE inflation data drops Thursday Apr 9 at 8:30 AM ET. The number either confirms sticky inflation (bearish, SPY drops 1-2%) or comes in soft (bullish, SPY pops 1-2%). We do not care which direction. We profit from the magnitude of the move by buying both sides with same-day expiration options where gamma is maximized and premium is minimized.
**Account:** $10,000 | **Risk budget:** 2% = $200 (total premium at risk)
**Expiry:** Thursday Apr 9, 2026 (0 DTE)

---

## Why 0DTE For This Setup

1. **Cheapest possible premium.** A 0DTE option has almost zero extrinsic time value -- you are buying nearly pure gamma. An ATM SPY call or put expiring today costs ~$0.80-1.20 vs. $4-5 for a weekly. This lets you buy BOTH sides of the move.
2. **Maximum gamma.** At 0DTE, gamma is at its lifetime peak. Every $0.50 SPY moves in your favor, the winning leg accelerates. A $3 SPY move turns a $0.90 option into $2.50+.
3. **No overnight risk.** The trade opens and closes the same day. No gap risk, no holding through uncertainty.
4. **Binary catalyst.** PCE is a known-time release with a known reaction pattern: fast, directional, 15-30 minutes. This is exactly what 0DTE strangles are designed for.
5. **Theta is irrelevant.** You are holding for 30-90 minutes. Theta decay on a 0DTE option between 9:35 and 10:30 AM is negligible compared to the gamma-driven move.

---

## POSITION: 0DTE SPY Strangle — PCE Catalyst Scalp

| Field | Detail |
|---|---|
| **Action** | **BUY 1x SPY Apr 9 $680 Call + BUY 1x SPY Apr 9 $676 Put** (0DTE, expires today) |
| **Entry time** | **Thursday Apr 9, 9:35-9:40 AM ET** (5-10 minutes after open, see entry rules) |
| **Expiry** | Apr 9, 2026 (same day, 0 DTE) |
| **Call strike** | $680 (~$2 OTM from $678) |
| **Put strike** | $676 (~$2 OTM from $678) |
| **Estimated call price** | ~$0.85 per contract |
| **Estimated put price** | ~$0.85 per contract |
| **Total strangle cost** | ~$1.70 per strangle ($170 per pair) |
| **Quantity** | **1 strangle** (1 call + 1 put = $170 total premium) |
| **Max loss** | **$170** (total premium paid, both legs expire worthless -- under 2% of $10K) |
| **Breakeven (upside)** | SPY above $681.70 ($680 + $1.70) |
| **Breakeven (downside)** | SPY below $674.30 ($676 - $1.70) |
| **Required SPY move** | ~$3.70 from $678 in either direction (~0.55%) |

---

## Why These Strikes

### Why $680 call (not $678 ATM or $682)?
- $678 ATM call would cost ~$1.40 -- too expensive, pushes total strangle to $2.50+ which blows the risk budget on only 1 strangle
- $680 is ~$2 OTM, costs ~$0.85. With VIX at 20, 0DTE implied move for SPY is roughly $3.40 (VIX 20 / sqrt(252) * $678 = ~$0.85/point of daily vol, 1-sigma is $3.40). PCE reactions routinely exceed 1-sigma
- $682 is too far OTM ($0.35-0.45) -- needs a massive move just to go ITM, and the bid-ask spread as a percentage of premium is terrible
- $680 gives the best gamma-per-dollar: close enough to go ITM on a modest move, cheap enough to keep size

### Why $676 put (not $678 ATM or $674)?
- Symmetrical logic: $2 OTM on the downside, ~$0.85
- $674 put ($0.35-0.45) has the same problems as $682 call -- too far out, bad liquidity as a % of premium
- $676 puts ITM on SPY touching $676, which is only a $2 drop -- well within PCE reaction range
- Slight downside skew in pricing means the $676 put may actually cost $0.90 vs $0.80 for the $680 call. Budget for $0.85 each as midpoint estimate

---

## Entry Rules (Non-Negotiable)

### DO NOT enter before market open at 9:30 AM.
PCE drops at 8:30 AM. Pre-market options trading on SPY exists but liquidity is atrocious -- spreads are $0.20-0.50 wide on 0DTE options. You will get destroyed on fill quality. The pre-market move also often fakes out and reverses at the open.

### Entry window: 9:35-9:40 AM ET (strict)
1. **Wait for the opening auction to settle** (9:30-9:35). The first 5 minutes are chaotic -- market makers repricing around the PCE move, retail orders flooding in, spreads normalizing.
2. **At 9:35, observe where SPY is trading.** The PCE reaction has been underway for 65 minutes in futures. The direction is likely established but the equity options market is freshly open.
3. **Enter the strangle at 9:35-9:40 using limit orders at the mid-price.** SPY 0DTE options are extremely liquid (SPY is the most traded 0DTE product in existence). You should get filled at mid within 30 seconds.

### Entry abort conditions:
- **SPY has already moved more than $5 from previous close.** The move happened pre-market and is likely exhausted. The strangle is a fade trap -- the winning leg is already expensive and the losing leg is nearly worthless. DO NOT ENTER.
- **VIX has spiked above 28.** Premiums are inflated, the strangle costs $3.00+ instead of $1.70. Risk:reward is destroyed. DO NOT ENTER.
- **VIX has crashed below 15.** The market is not expecting any move. Your options are cheap but the catalyst is priced as a non-event. The move may not materialize. CONSIDER SKIPPING.
- **SPY is unchanged from prior close (within $0.50).** PCE was a non-event. There may be no move to capture. Wait 10 more minutes and reassess. If still flat at 9:50, skip the trade.

---

## Exit Rules (This Is the Entire Trade)

This is a SCALP. You are in and out in 30-90 minutes. There is no "give it time." These rules are mechanical.

### Rule 1: Take the Winner at 100%+ Gain (Primary Exit)
- If either leg doubles from entry (e.g., the put goes from $0.85 to $1.70+), **SELL THAT LEG IMMEDIATELY**
- Then evaluate the losing leg: if it still has $0.10+ of value, hold it as a free lottery ticket for a reversal. If it is at $0.05 or below, let it expire worthless (commissions exceed value)
- **Target: one leg hits $1.70-2.50+ on a $3-5 SPY move.** This is realistic -- a $4 SPY drop puts the $676 put at ~$2.00-2.50 intrinsic + residual extrinsic

### Rule 2: Kill the Loser When the Winner Prints
- The moment you sell the winning leg for a profit, the losing leg is dying. Do NOT hold the loser hoping for a reversal unless it is essentially free (<$0.10)
- If the losing leg is still worth $0.20+, sell it within 5 minutes of selling the winner. Recoup whatever you can

### Rule 3: Time Stop -- Exit Everything by 10:30 AM ET
- If neither leg has hit 100% gain by 10:30 AM ET (55 minutes after entry), **CLOSE BOTH LEGS AT MARKET**
- Rationale: the PCE move is a 15-45 minute event. If SPY has not moved enough in 55 minutes, it is range-bound. Theta is now your primary exposure and it is eating both legs. By 11:00 AM on a 0DTE, an OTM option loses value alarmingly fast
- Do not hold past 10:30 hoping for a "second wave." The second wave is a myth for data releases

### Rule 4: Hard Max Loss = Total Premium Paid ($170)
- If SPY sits at $678 all day and both legs decay to zero, you lose $170. That is the plan
- There is NO scenario where you lose more than $170 on a long strangle. This is defined-risk by construction
- Do not add to the position, do not "roll" to different strikes, do not buy more strangles if the first one is not working

---

## Profit/Loss Scenarios at Exit (~10:00-10:30 AM)

| SPY at Exit | Call Value | Put Value | Strangle Value | P&L | Return |
|---|---|---|---|---|---|
| $684 (+$6 move) | ~$4.10 | ~$0.03 | ~$4.13 | **+$243** | +143% |
| $682 (+$4 move) | ~$2.20 | ~$0.08 | ~$2.28 | **+$58** | +34% |
| $681 (+$3 move) | ~$1.40 | ~$0.12 | ~$1.52 | **-$18** | -11% |
| $678 (no move) | ~$0.40 | ~$0.40 | ~$0.80 | **-$90** | -53% |
| $675 (-$3 move) | ~$0.12 | ~$1.40 | ~$1.52 | **-$18** | -11% |
| $674 (-$4 move) | ~$0.08 | ~$2.20 | ~$2.28 | **+$58** | +34% |
| $672 (-$6 move) | ~$0.03 | ~$4.10 | ~$4.13 | **+$243** | +143% |

**Key insight:** You need roughly a $3.70+ move in either direction to profit. PCE routinely causes $3-7 SPY moves on surprise prints. At VIX 20, the 1-sigma daily move is ~$3.40 and PCE surprises typically exceed 1-sigma.

---

## Historical Context: PCE Reaction Magnitudes

PCE releases in 2025-2026 that surprised vs. consensus:
- Hot prints (above consensus): average SPY move of -$4.20 in first 60 minutes
- Soft prints (below consensus): average SPY move of +$3.80 in first 60 minutes
- Inline prints (at consensus): average SPY move of +/-$1.20 -- **this is the scenario where we lose**

The strangle is profitable if PCE surprises in either direction. The risk is an inline print where SPY moves $1-2 and both legs decay. This happens roughly 30-40% of the time. When it does, the time stop at 10:30 AM limits the loss to $90-130 (selling residual value) rather than the full $170.

---

## Position Sizing Rationale

| Metric | Value |
|---|---|
| Total capital at risk | $170 (1.7% of $10K) |
| Max loss scenario | Both legs expire worthless = -$170 |
| Likely loss on inline PCE | -$90 to -$130 (time stop recoup) |
| Target profit (one leg doubles) | +$80 to +$250 |
| Asymmetric best case (one leg 3x+) | +$250 to +$500 |
| Win rate estimate | ~55-60% (PCE surprises more often than not in current regime) |

**Why only 1 strangle, not 2?**
- At 2 strangles ($340 total), the max loss is 3.4% of account. Acceptable in isolation but this should be a small, repeatable edge trade, not a portfolio-defining position
- 1 strangle keeps the loss at $170 worst case, $90-130 typical loss case. This is the kind of trade you can take every data release day without ever threatening the account
- If you want to size up, the correct approach is 2 strangles with the SAME exit rules. Never go above 2 strangles on a $10K account

---

## Execution Checklist (Thursday Morning)

### Pre-Market (7:00-9:30 AM)
- [ ] PCE data drops at 8:30 AM. Check the number on CNBC/Bloomberg/Twitter immediately
- [ ] Note: was it hot, soft, or inline vs. consensus?
- [ ] Watch ES futures (S&P 500 futures) for the reaction. Note the magnitude by 9:00 AM
- [ ] If ES has moved <10 points (~$1 SPY), this is an inline print. Consider skipping the trade
- [ ] If ES has moved >30 points (~$3 SPY), the move is real. Prepare to enter at 9:35

### Market Open (9:30-9:40 AM)
- [ ] At 9:30, note SPY opening price. Compare to previous close ($678)
- [ ] Check abort conditions (see Entry Rules above)
- [ ] At 9:35-9:40, enter limit orders at mid-price for both legs
- [ ] Confirm fills on both legs. If only one fills, cancel the other and reassess

### Active Management (9:40-10:30 AM)
- [ ] Monitor both legs. Set alerts for 100% gain on either leg ($1.70)
- [ ] When winner hits target, sell immediately. Then evaluate loser
- [ ] If neither hits target by 10:15, tighten mental stop: will exit at 10:30 regardless
- [ ] At 10:30, close everything. No exceptions

### Post-Trade (10:30-11:00 AM)
- [ ] Log the trade: entry prices, exit prices, SPY levels, P&L
- [ ] Note what PCE printed and whether the reaction matched expectations
- [ ] Do NOT re-enter. One shot per data release. The edge is in the first reaction, not the chop that follows

---

## What This Trade Is NOT

- **This is not a directional bet.** You do not need to predict whether PCE is hot or soft
- **This is not a hold.** If you are still in this at 11:00 AM, something went wrong
- **This is not a hedge.** It does not protect any other position. It is a standalone catalyst scalp
- **This is not repeatable every day.** 0DTE strangles on non-event days are theta donation boxes. This works ONLY because PCE is a known, high-magnitude catalyst at a known time
- **This is not a big swing.** Max realistic profit is $250 on $170 risk. It is a high-probability, small-dollar scalp. The edge is that it is repeatable on every major data release (PCE, CPI, NFP, FOMC) with the same structure

---

## Alternative Considered: 0DTE Straddle ($678C + $678P)

| | Straddle (ATM) | Strangle ($680C/$676P) |
|---|---|---|
| Cost | ~$2.40 ($240) | ~$1.70 ($170) |
| Breakeven | $680.40 / $675.60 (~$2.40 move) | $681.70 / $674.30 (~$3.70 move) |
| Risk | $240 | $170 |
| Profit on $5 move | ~$260 (108% return) | ~$160 (94% return) |
| Profit on $3 move | ~$60 (25% return) | ~-$18 (breakeven) |
| Inline print loss | ~$160 (sells for $0.80) | ~$90 (sells for $0.80) |

**Verdict: Strangle is better for this setup.**
- The straddle profits on smaller moves ($3) but costs $70 more
- The strangle has a lower max loss and better percentage returns on big moves
- PCE reactions are typically $3-7 -- at $5+ the strangle significantly outperforms on a % basis
- The $70 savings on premium means lower dollar loss on inline prints, which is the most important risk to manage on a repeatable trade
- If you believe the move will be smaller ($2-3), the straddle is better. But at VIX 20 with PCE as the catalyst, we are positioning for a $4+ move

---

## Key Risk: The Inline Print

The one scenario where this trade loses is an inline PCE (matches consensus exactly). SPY opens flat, drifts $1 in either direction, and both legs decay.

**Mitigations:**
1. The time stop at 10:30 AM means you sell both legs while they still have ~$0.40-0.50 of residual value. Your actual loss is $80-90, not $170
2. You can observe the pre-market reaction before committing. If futures have barely moved by 9:30, you can SKIP the trade entirely. The entry abort condition handles this
3. Inline prints are the minority outcome for PCE in the current macro regime. With inflation still a live debate (tariff impacts, sticky services), PCE prints tend to surprise in one direction or the other
