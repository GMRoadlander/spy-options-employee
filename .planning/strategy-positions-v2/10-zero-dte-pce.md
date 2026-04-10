# Position 10: 0DTE PCE Volatility Scalp — SPY Strangle (v2)

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY ~$678 (proxy for SPX ~6783)
**Thesis:** February PCE drops Thursday Apr 9 at 8:30 AM ET. Pre-Hormuz data -- likely inline or soft. But the DATA IS IRRELEVANT. What matters is the market reaction in an environment where VIX is 20, ceasefire is structurally unenforceable (31 armed services, Supreme Leader coma), and any headline about violations can drop mid-session. We buy both sides of the move at maximum gamma, minimum premium, and scalp the first 55 minutes of the equity session.
**Account:** $10,000 | **Risk budget:** 2% = $200 (hard cap)
**Expiry:** Thursday Apr 9, 2026 (0 DTE -- expires today)

---

## Why This Setup Exists

The v1 strangle (Position 04) targeted a 1DTE entry on Wednesday for the PCE catalyst. That was a different trade -- it accepted overnight theta in exchange for pre-positioning. This is a same-day scalp. No overnight risk, no theta bleed, no holding through anything. You enter after the open, you exit before lunch. The edge is gamma on a known catalyst, not direction.

Three things make Thursday Apr 9 specifically attractive for a 0DTE strangle:

1. **February PCE is pre-Hormuz.** The market knows this. If data is soft, the reaction is "old news, already priced." If hot, it contradicts the narrative that inflation was cooling before tariffs. Either print creates confusion, and confusion creates movement.
2. **Ceasefire fragility as an overlay.** The ceasefire is structurally unenforceable. Any headline about Houthi violations, Iranian statements, or ship incidents during Thursday's session amplifies whatever the PCE reaction is. This is not priced into 0DTE implied vol.
3. **VIX at 20 means 0DTE options are cheap relative to actual tail risk.** VIX 20 implies a daily move of ~$3.40 on SPY. In the current regime (geopolitical uncertainty + macro data), realized intraday moves on data days have been running $3-7. You are buying implied vol that underestimates realized vol.

---

## POSITION: 0DTE SPY Strangle -- PCE Catalyst Scalp

| Field | Detail |
|---|---|
| **Action** | **BUY 1x SPY Apr 9 $680 Call + BUY 1x SPY Apr 9 $676 Put** (0DTE, expires today) |
| **Entry time** | **Thursday Apr 9, 9:35-9:45 AM ET** (5-15 minutes after open) |
| **Expiry** | Apr 9, 2026 (same day, 0 DTE) |
| **Call strike** | $680 (~$2 OTM from $678) |
| **Put strike** | $676 (~$2 OTM from $678) |
| **Estimated call price** | ~$0.80-0.90 per contract |
| **Estimated put price** | ~$0.80-0.90 per contract |
| **Total strangle cost** | ~$1.70 per strangle ($170 per pair) |
| **Quantity** | **1 strangle** (1 call + 1 put = $170 total premium) |
| **Max loss** | **$170** (total premium paid, both legs expire worthless -- under 2% of $10K) |
| **Breakeven (upside)** | SPY above $681.70 ($680 + $1.70) |
| **Breakeven (downside)** | SPY below $674.30 ($676 - $1.70) |
| **Required SPY move** | ~$3.70 from $678 in either direction (~0.55%) |

---

## Why These Strikes

### $680 Call (~$2 OTM)
- ATM $678 call costs ~$1.40 at 0DTE with VIX 20. Too expensive -- pushes the strangle to $2.50+ and blows the $200 risk budget.
- $680 at ~$0.85 is the gamma sweet spot: close enough to go ITM on a $2 move, cheap enough to pair with the put.
- $682 is too far (~$0.35-0.45). Needs a massive move, terrible bid-ask as a percentage of premium.
- At 0DTE, delta on the $680 call is ~0.30. A $3 SPY move puts it at ~0.60 delta and the option doubles.

### $676 Put (~$2 OTM)
- Symmetrical positioning. $2 OTM on the downside.
- Slight put skew may make this $0.85-0.90 vs $0.80-0.85 for the call. Budget $0.85 each.
- $674 put is too far out for the same reasons as the $682 call.
- ITM on SPY at $676 -- a $2 drop that is well within PCE reaction range and trivial if a ceasefire headline drops.

### Strike Adjustment Rules (if SPY is NOT at $678 at entry)
- If SPY opens at $675 (already dropped on PCE), shift to: $677 Call / $673 Put (maintain ~$2 OTM each side).
- If SPY opens at $681 (popped on PCE), shift to: $683 Call / $679 Put.
- The structure is always: nearest $2 OTM strikes on both sides of wherever SPY is trading at 9:35 AM.
- Recalculate cost. If the strangle costs > $2.00 ($200), the premiums are too inflated (VIX spike) -- abort.

---

## Entry Rules (Non-Negotiable)

### Entry Window: 9:35-9:45 AM ET (strict)

1. **Do NOT enter before 9:35.** PCE drops at 8:30 AM. Pre-market SPY options have $0.20-0.50 wide spreads on 0DTE. You will get filled at terrible prices. The pre-market move also routinely fakes out at the open.
2. **9:30-9:35: Watch the open.** Let the opening auction settle. Market makers reprice, retail orders flood in, spreads normalize.
3. **9:35-9:45: Enter using limit orders at mid-price.** SPY 0DTE is the most liquid options product in existence. You should fill at mid within 30 seconds. If you do not fill within 2 minutes, walk the limit up by $0.05 once. If still no fill, the market is too chaotic -- wait until 9:45. If still no fill at 9:45, abort.
4. **Both legs must fill.** If only one leg fills and the other does not within 2 minutes, cancel the unfilled leg and immediately close the filled leg. Do not run a naked directional 0DTE position. That is a different trade.

### Abort Conditions (DO NOT ENTER if any are true)

| Condition | Why | Action |
|---|---|---|
| SPY already moved $5+ from prior close pre-market | The move happened. The winning leg is expensive, the losing leg is near zero. You are buying a strangle where one side is already dead. | SKIP. Do not enter. |
| VIX > 28 | Premiums are inflated 70%+. The strangle costs $2.80-3.50 instead of $1.70. Risk:reward is destroyed. | SKIP. Do not enter. |
| VIX < 15 | Market is pricing zero movement. The catalyst is considered a non-event. Your options are cheap but there may be no move to capture. | SKIP. Do not enter. |
| SPY unchanged from prior close (within $0.50) at 9:35 | PCE was a non-event. Futures barely reacted in 65 minutes. | WAIT. Reassess at 9:50. If still flat, skip. |
| 0DTE strangle costs > $2.00 total | Implied vol is too high relative to expected payoff. You are overpaying for gamma. | SKIP. Do not enter. |
| Ceasefire has already visibly collapsed (headline before open) | SPY likely gapped $5+ already. See condition 1. | SKIP -- or reassess as a directional trade, NOT a strangle. |

---

## Exit Rules -- THE ENTIRE TRADE

This is a SCALP. In by 9:45, out by 10:30. No exceptions. No "let it run." No "give it time." These rules are mechanical and override your feelings.

### Rule 1: Take Winner at 100%+ Gain (Primary Exit)

If either leg doubles from entry price (e.g., put goes from $0.85 to $1.70+):
- **SELL THAT LEG IMMEDIATELY.** Do not wait for 150%. Do not wait for 200%. A 100% gain on one leg of a strangle is a great scalp.
- Then evaluate the losing leg:
  - If it has $0.10+ value: hold as a free lottery ticket for reversal. Set a $0.05 trailing stop or let it expire.
  - If it is $0.05 or below: let it expire worthless. Commissions exceed value.
- Net result: ~$0.85 profit on winner, ~$0.85 loss on loser = breakeven on legs, but the winner's 100%+ gain means net profit of $80-170.

**What 100% gain looks like in practice:**
- A $4 SPY move in either direction puts the winning leg at ~$2.00-2.50. That is 135-195% gain.
- A $3 SPY move puts the winning leg at ~$1.30-1.50. Close to 100% but not there. Hold for a few more minutes but respect the time stop.

### Rule 2: Kill the Loser When Underlying Crosses Mid-Strike

- Mid-strike = $678 (midpoint of $676 put and $680 call).
- If SPY breaks below $678 and holds for 10 minutes (not a wick -- a sustained move on 5-minute candles):
  - The put is working. **Kill the $680 call.** Sell at market, recover whatever is left ($0.10-0.30).
  - Let the put run toward the 100% target.
- If SPY breaks above $678 and holds for 10 minutes:
  - The call is working. **Kill the $676 put.** Same logic.
- "Holds for 10 minutes" means at least two consecutive 5-minute candle closes on the same side of $678.

### Rule 3: HARD Time Stop -- Out by 10:30 AM ET. No Exceptions.

- At 10:30 AM ET, close BOTH legs at market. Whatever they are worth. Even if one leg is at 90% gain and you think it will hit 100% in 5 more minutes.
- Rationale: PCE is a 15-45 minute event measured from equity open. By 10:30 (55 minutes post-entry), the data reaction is over. What follows is range-bound chop where theta eats both legs. On 0DTE options after 10:30 AM, OTM options lose value at an accelerating rate -- by noon they are effectively worthless unless deep ITM.
- The "second wave" after a data release is a myth. Do not hold hoping for one.
- 10:30 AM is 10:30 AM. Not 10:35. Not 10:45. Not "just a few more minutes." Set an alarm.

### Rule 4: Max Loss = Total Premium ($170)

- If SPY sits at $678 all morning and both legs decay, you lose $170. That is the plan.
- There is no scenario where you lose more than $170 on a long strangle. Defined risk by construction.
- Do NOT add to the position. Do NOT "average down." Do NOT buy a second strangle because the first one is not working. One shot, one exit.

---

## Profit/Loss Scenarios at Exit (~10:00-10:30 AM)

| SPY at Exit | Call Value | Put Value | Strangle Value | P&L | Return |
|---|---|---|---|---|---|
| $685 (+$7) | ~$5.10 | ~$0.01 | ~$5.11 | **+$341** | +201% |
| $684 (+$6) | ~$4.10 | ~$0.03 | ~$4.13 | **+$243** | +143% |
| $682 (+$4) | ~$2.20 | ~$0.08 | ~$2.28 | **+$58** | +34% |
| $681 (+$3) | ~$1.40 | ~$0.12 | ~$1.52 | **-$18** | -11% |
| $678 (flat) | ~$0.40 | ~$0.40 | ~$0.80 | **-$90** | -53% |
| $675 (-$3) | ~$0.12 | ~$1.40 | ~$1.52 | **-$18** | -11% |
| $674 (-$4) | ~$0.08 | ~$2.20 | ~$2.28 | **+$58** | +34% |
| $672 (-$6) | ~$0.03 | ~$4.10 | ~$4.13 | **+$243** | +143% |
| $671 (-$7) | ~$0.01 | ~$5.10 | ~$5.11 | **+$341** | +201% |

**Breakeven requires ~$3.70 SPY move in either direction.** In the current regime:
- PCE surprises (hot or soft) historically move SPY $3.80-5.20 in first 60 minutes
- Inline prints move SPY $1-2 -- this is the loss scenario (~30-40% of the time)
- The ceasefire overlay adds tail risk that is not reflected in the inline print probability

---

## The Ceasefire Overlay -- Why This Is Not Just a PCE Trade

The v1 position treated this as a pure data play. The v2 position recognizes the ceasefire context:

**Structurally unenforceable ceasefire facts:**
- 31 separate armed services in the Houthi coalition. No unified command structure.
- Supreme Leader reportedly in coma. No single authority to enforce compliance.
- Ceasefire violations are not a matter of "if" but "when."
- Any headline about a ship being fired on, a drone launch, or an Iranian statement during Thursday's session is a $3-7 SPY move by itself.

**What this means for the strangle:**
- The PCE print is the primary catalyst (8:30 AM).
- Ceasefire headlines are the secondary catalyst (any time during the session).
- The strangle captures BOTH. If PCE is a non-event but a ceasefire headline drops at 10:15, the strangle is still live until the 10:30 time stop.
- If PCE moves SPY $4 AND a ceasefire headline amplifies it, the winning leg could be a 3-4x.

**What this does NOT mean:**
- Do not hold past 10:30 hoping for a ceasefire headline. The time stop is the time stop.
- If a ceasefire headline drops before 9:30 and SPY has already moved $5+, the abort conditions apply. Do not enter.

---

## Execution Checklist (Thursday Morning)

### Pre-Market (7:00-9:30 AM ET)

- [ ] PCE data drops at 8:30 AM. Check the number immediately (CNBC, Bloomberg, X/Twitter).
- [ ] Note: Hot (core PCE > 0.3% m/m), Soft (< 0.2% m/m), or Inline (0.2-0.3% m/m)?
- [ ] Watch ES futures for the reaction. Note magnitude by 9:00 AM.
- [ ] **ABORT CHECK:** Has ES moved > 50 points (~$5 SPY)? If yes, DO NOT ENTER.
- [ ] **ABORT CHECK:** Has VIX spiked above 28? If yes, DO NOT ENTER.
- [ ] **ABORT CHECK:** Has a ceasefire collapse headline already moved SPY $5+? If yes, DO NOT ENTER.
- [ ] If ES has moved 10-30 points ($1-3 SPY): the move is real but not exhausted. Prepare to enter at 9:35.
- [ ] If ES has moved < 10 points (< $1 SPY): inline print. Consider skipping. Wait until 9:50 to decide.

### Market Open (9:30-9:45 AM ET)

- [ ] Note SPY opening price. Compare to previous close (~$678).
- [ ] Determine adjusted strikes if SPY is not near $678 (see Strike Adjustment Rules).
- [ ] Verify strangle cost < $2.00 total. If higher, ABORT.
- [ ] At 9:35, place limit orders at mid-price for both legs.
- [ ] Confirm both legs fill. If only one fills within 2 minutes, cancel other and close filled leg.
- [ ] Record entry prices for both legs and total cost.

### Active Management (9:40-10:30 AM ET)

- [ ] Set price alert for 100% gain on each leg (2x entry price).
- [ ] Monitor SPY relative to $678 mid-strike.
- [ ] If SPY breaks one side of $678 and holds 10 minutes: kill the losing leg.
- [ ] When winning leg hits 100%+: SELL IMMEDIATELY. Evaluate losing leg per Rule 1.
- [ ] 10:15 AM check: if neither leg has hit target, prepare for 10:30 exit.
- [ ] **10:30 AM: CLOSE EVERYTHING. NO EXCEPTIONS.**

### Post-Trade (10:30-11:00 AM ET)

- [ ] Log: entry prices, exit prices, SPY levels at entry/exit, total P&L.
- [ ] Note PCE print, market reaction direction, and magnitude.
- [ ] Note whether any ceasefire headlines hit during the session.
- [ ] DO NOT RE-ENTER. One shot per data release. The edge is in the first reaction.

---

## Position Sizing Rationale

| Metric | Value |
|---|---|
| Total capital at risk | $170 (1.7% of $10K) |
| Under 2% hard cap | Yes -- $30 of buffer |
| Max loss (both expire worthless) | -$170 |
| Likely loss on inline PCE (time stop salvage) | -$80 to -$100 |
| Target profit (one leg 100%+) | +$80 to +$170 |
| Best case (one leg 200%+, $5-7 SPY move) | +$170 to +$350 |
| Win rate estimate | ~55-65% (PCE surprises + ceasefire overlay in current regime) |

**Why only 1 strangle?**
- 1 strangle at $170 fits cleanly under the 2% ($200) risk cap.
- 2 strangles at $340 exceeds the 2% budget by 70%. Not acceptable for a scalp.
- This is a repeatable trade on every major data release day (PCE, CPI, NFP, FOMC). The edge is consistency, not size. Risking $170 each time and winning 55-65% with 1:1 to 2:1 payoffs compounds. Sizing up and blowing the risk budget does not.

---

## What This Trade Is and Is Not

**IS:**
- A 55-minute gamma scalp on a known catalyst at a known time.
- Defined risk. Max loss $170. Zero scenarios where you lose more.
- Direction-agnostic. You do not need to predict PCE or market reaction.
- Repeatable on every major data release (PCE, CPI, NFP, FOMC).

**IS NOT:**
- A directional bet. You are not predicting hot or soft PCE.
- A hold. If you are in this at 11:00 AM, something went wrong.
- A hedge for any other position. Standalone catalyst scalp.
- An every-day trade. 0DTE strangles on non-event days are theta donation. This works ONLY because PCE is a high-magnitude catalyst at a known time, overlaid with ceasefire fragility.
- A big swing. Target is $80-170 profit on $170 risk. It is a high-probability, small-dollar scalp. The value is repeatability.

---

## Comparison: v1 vs v2

| Dimension | v1 (Position 12) | v2 (This Position) |
|---|---|---|
| Strikes | $680C / $676P | $680C / $676P (same, with adjustment rules) |
| Entry window | 9:35-9:40 AM | 9:35-9:45 AM (wider -- allows for volatile opens) |
| Time stop | 10:30 AM | 10:30 AM (unchanged -- this is correct) |
| Ceasefire context | Not addressed | Explicit overlay with abort conditions |
| Strike adjustment | Not addressed | Rules for if SPY is not at $678 at entry |
| Abort: SPY moved $5+ | Present | Present (unchanged) |
| Abort: VIX > 28 | Present | Present (unchanged) |
| Abort: ceasefire collapse | Not present | Added |
| Abort: strangle > $2.00 | Not present | Added (hard premium cap) |
| Mid-strike rule | Not present | $678, hold 10 minutes, kill loser |
| PCE thesis | "We profit from magnitude" | "Data is irrelevant, reaction matters" + ceasefire overlay |
| Risk budget | $170 (1.7%) | $170 (1.7%) -- unchanged, correct |

---

## Summary Table

| Field | Value |
|---|---|
| Structure | Long 0DTE SPY strangle ($680C / $676P) |
| Underlying | SPY (proxy for SPX) |
| Expiry | Thursday Apr 9, 2026 (0 DTE) |
| Entry | 9:35-9:45 AM ET, limit orders at mid |
| Total cost | ~$1.70/strangle ($170 total) |
| Max loss | $170 (1.7% of $10K) |
| Upside BE | $681.70 (+0.55%) |
| Downside BE | $674.30 (-0.55%) |
| Winner target | 100%+ gain on either leg |
| Loser management | Kill when underlying crosses $678 mid-strike and holds 10 min |
| Hard time stop | 10:30 AM ET -- no exceptions |
| Abort if | SPY moved $5+ pre-market, VIX > 28, strangle > $2.00, ceasefire already collapsed |
| Edge | Gamma on PCE catalyst + ceasefire tail risk. Realized vol > implied vol at VIX 20 in this regime. |
| Do NOT | Hold past 10:30. Re-enter. Add to position. Run a naked leg. |
