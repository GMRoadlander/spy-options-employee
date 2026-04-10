# POSITION: PCE Strangle v2 — MPW Method, Revised

**Date drafted:** 2026-04-06
**Playbook:** MPW Strangle (direction-agnostic, catalyst-driven, cut loser fast)
**Version:** v2 — incorporates swarm findings on IV crush timing, 0DTE vs 1DTE analysis, and MPW's $15K strangle case study

---

## Thesis

Two macro catalysts in 48 hours (PCE Thursday 8:30 AM, CPI Friday 8:30 AM) on top of a structurally fragile ceasefire rally. VIX at 20 is pricing ~1.26% daily moves, but PCE surprises in the current regime (tariff uncertainty, sticky services inflation, geopolitical tail risk from an unenforceable ceasefire with Iran's Supreme Leader incapacitated) historically deliver 1.5-2.5 SD moves. Realized vol will exceed implied vol. We do not need to pick a direction. We need the move to exceed what the market is pricing.

---

## Decision: 0DTE (Thursday Expiry), NOT 1-2 DTE

The 0DTE strangle is the correct structure here. This is the core decision and it needs to be right, so here is the full reasoning.

### Why 0DTE Wins

1. **Cost.** A 0DTE strangle at ~$2 OTM per side costs ~$1.70. A 1DTE strangle (Friday expiry, entered Thursday) costs ~$3.40. The 0DTE version risks half the capital for a comparable payoff on a 4+ point SPY move. On a $10K account with 2% risk, the 0DTE version is the only one that fits the budget without compromise.

2. **Gamma maximization.** At 0DTE, gamma is at its lifetime peak. Every $0.50 SPY moves in your favor, the winning leg accelerates faster than at any other DTE. This is exactly what you want for a known-time binary catalyst.

3. **No theta bleed.** You hold for 30-90 minutes. Theta decay during that window is negligible compared to the gamma payoff. A 1DTE strangle entered Wednesday afternoon bleeds overnight theta before PCE even prints.

4. **No weekend risk.** The 0DTE opens and closes Thursday. You are flat before CPI Friday, flat before the weekend, and flat before any ceasefire headline can gap you. This satisfies the hard rule: do not hold both legs into the weekend.

5. **Swarm finding alignment.** The swarm concluded that entering BEFORE the event captures IV expansion, but entering IMMEDIATELY AFTER captures the directional move post-crush. The 0DTE entered at 9:35 AM Thursday (65 minutes after the 8:30 AM PCE print) is the "immediately after" approach -- you enter after the number is known, after the futures reaction is established, and you ride the equity market's catch-up move. This avoids paying for pre-event IV inflation.

### Why 1-2 DTE Loses

- A Wednesday afternoon entry (pre-PCE) buys inflated IV. If PCE is inline, the IV crush alone kills both legs even if SPY moves modestly. The swarm specifically flagged that straddles/strangles are "overpriced at Friday close" pre-event.
- A 1DTE strangle costs ~$3.40 ($340), which is 3.4% of the account -- exceeds 2% risk.
- Holding a 1DTE strangle through Thursday into Friday means you carry CPI risk AND weekend gap risk with decaying options. MPW's method is explicit: cut the loser immediately. Holding a 1DTE strangle into CPI is not cutting the loser -- it is hoping for a second catalyst to bail out a trade that should already be resolved.

### The Exception

If VIX spikes above 25 pre-PCE (geopolitical shock, ceasefire collapse), 0DTE premiums inflate and the strangle costs $2.50+. In that scenario, skip the 0DTE entirely. The move may have already happened.

---

## Setup Context

| Metric        | Value                  |
|---------------|------------------------|
| SPX           | ~6783                  |
| SPY           | ~$678                  |
| VIX           | ~20                    |
| Implied daily | ~1.26% ($8.55 on SPY) |
| 0DTE implied move | ~$3.40 (1-sigma)  |
| Catalyst      | PCE Thursday Apr 9, 8:30 AM ET |
| Regime        | Fragile ceasefire rally, extended, vulnerable |

---

## POSITION: 0DTE SPY Strangle — PCE Thursday

| Field | Detail |
|---|---|
| **Action** | **BUY 1x SPY Apr 9 $680 Call + BUY 1x SPY Apr 9 $676 Put** |
| **Expiry** | Thursday April 9, 2026 (0DTE, expires same day) |
| **Entry** | **Thursday Apr 9, 9:35-9:40 AM ET** |
| **Call strike** | $680 (~$2 OTM) |
| **Put strike** | $676 (~$2 OTM) |
| **Est. call price** | ~$0.85 |
| **Est. put price** | ~$0.85 |
| **Total strangle cost** | **~$1.70 ($170 per strangle)** |
| **Quantity** | **1 strangle** |
| **Max loss** | **$170 (1.7% of $10K — within 2% budget)** |
| **Breakeven up** | SPY > $681.70 (+$3.70, +0.55%) |
| **Breakeven down** | SPY < $674.30 (-$3.70, -0.55%) |

---

## Strike Selection

**$680 Call (~$2 OTM):** Close enough to go ITM on a modest bullish PCE reaction. At $2 OTM, delta is ~0.30 at entry but gamma is extreme on 0DTE -- a $3 SPY move puts it ITM and delta ramps toward 0.70. The $682-$683 call is too far out ($0.35-$0.45) with terrible bid-ask as a percentage of premium. The $678 ATM call is too expensive (~$1.40) and pushes the strangle above the risk budget.

**$676 Put (~$2 OTM):** Symmetric construction. $2 below current price. If PCE prints hot and SPY drops $4-5 (the Borey scenario -- gap fill acceleration), the put goes from $0.85 to $2.50+. Slight put skew may price this at $0.90 vs $0.80 for the call. Budget $0.85 each as the midpoint.

**Why not wider ($4-5 OTM)?** At $673P/$683C the strangle costs ~$0.60 ($60 total). Cheap, but needs a $5+ SPY move just to break even. That is 1.5 sigma on 0DTE. PCE reactions average $3.80-$4.20 on surprises. The $2 OTM strangle captures the fat part of the distribution; the $4-5 OTM strangle only captures the tail.

---

## Entry Rules (Non-Negotiable)

### Timing: 9:35-9:40 AM ET Thursday (NOT pre-market, NOT at open)

PCE prints at 8:30 AM. By 9:35 you know:
- What the number was (hot, soft, or inline)
- How ES futures reacted (direction and magnitude established over 65 minutes)
- Whether the equity market is confirming or fading the futures move

You enter AFTER the data is known. This is MPW's approach -- he entered strangles around ceasefire rumors when the catalyst was live, not before. The equity options market at 9:35 has repriced for PCE but the full directional move often takes 30-60 more minutes to play out as institutional order flow arrives.

### Pre-Entry Observation (8:30-9:30 AM)

Watch ES futures from 8:30-9:30. Note:
- **ES moved > 30 points (~$3 SPY):** Strong PCE reaction. Direction is established. The strangle is live -- enter at 9:35.
- **ES moved 15-30 points (~$1.50-$3 SPY):** Moderate reaction. Enter the strangle. There is likely more to come as equity flows amplify.
- **ES moved < 15 points (~$1.50 SPY):** Weak reaction. PCE was inline or the surprise was small. **Proceed with caution.** Enter at 9:35 but tighten the time stop to 10:15 instead of 10:30.
- **ES moved > 50 points (~$5 SPY):** The move has already happened. The winning leg is expensive, the losing leg is near-zero. **DO NOT ENTER.** The risk/reward is destroyed. You missed it.

### Abort Conditions (Do Not Enter If)

- SPY has moved > $5 from Wednesday close by 9:35 AM
- VIX has spiked above 28 (premiums inflated, strangle costs $2.50+)
- VIX has crashed below 15 (market expects nothing -- no catalyst energy)
- SPY is unchanged from prior close (within $0.50) at 9:50 AM -- PCE was a non-event, skip entirely

### Execution

- Limit orders at mid-price on both legs
- SPY 0DTE options are the most liquid options on Earth. Fill at mid within 30 seconds
- If one leg fills and the other does not within 60 seconds, cancel the unfilled leg and close the filled leg. Do not hold a single leg hoping for the other to fill

---

## Exit Rules — MPW Method (This Is the Entire Edge)

MPW's $15K strangle profit did not come from picking direction. It came from disciplined exits: let the winner run, kill the loser immediately. These rules are mechanical and non-negotiable.

### Rule 1: Take the Winner at 2x Entry ($1.70+)

If either leg doubles from its entry price (~$0.85 to $1.70+), **sell it immediately.**

- On a $4 SPY move: the winning leg is worth ~$2.20-$2.50. Sell.
- On a $6 SPY move: the winning leg is worth ~$4.00+. Sell.
- Do not hold for more. The 0DTE gamma that helped you also works in reverse -- a $2 snapback erases gains in minutes.

After selling the winner, evaluate the loser:
- If worth > $0.10: sell it. Recoup whatever is left.
- If worth $0.05 or less: let it expire. Commission exceeds salvage value.

### Rule 2: Kill the Loser the Moment Direction Is Clear

This is the MPW rule. Once SPY has committed to a direction (sustained move for 15+ minutes post-open, not a wick), the losing leg is dying. Do not hope for reversal.

- **SPY breaks above $679 on volume and holds for 15 minutes:** The call is working. **Kill the $676 put.** Sell at whatever it is worth ($0.20-$0.40). Do not wait for zero.
- **SPY breaks below $677 on volume and holds for 15 minutes:** The put is working. **Kill the $680 call.** Same logic.
- "On volume" = the move is confirmed by SPY volume exceeding 5-min average. Not a pre-market drift that reverses at 9:45.

### Rule 3: Time Stop — Close Everything by 10:30 AM ET

If neither leg has hit 2x and no clear direction has emerged by 10:30 AM (55 minutes after entry):

- **Close both legs at market. No exceptions.**
- PCE reactions are 15-45 minute events. If SPY has not moved enough in 55 minutes, it is range-bound and both legs are decaying into dust.
- Residual value at 10:30 is typically $0.30-$0.50 per side if SPY is near $678. You recover ~$60-$80 of the $170 premium. Realized loss: ~$90-$110.
- Do NOT hold past 10:30 hoping for a "second wave." Second waves on data releases are a myth.

### Rule 4: Hard Max Loss = $170 (Total Premium)

This is the absolute floor. You cannot lose more than $170 on a long strangle. This is defined risk by construction. No scenario -- gap, halt, flash crash -- can increase your loss.

- Do not add to the position
- Do not roll to different strikes
- Do not buy a second strangle if the first is not working

---

## Profit/Loss Scenarios at Exit (~10:00-10:30 AM)

| SPY at Exit | Call Value | Put Value | Strangle Value | P&L | Return |
|---|---|---|---|---|---|
| $684 (+$6) | ~$4.10 | ~$0.03 | ~$4.13 | **+$243** | +143% |
| $682 (+$4) | ~$2.20 | ~$0.08 | ~$2.28 | **+$58** | +34% |
| $681 (+$3) | ~$1.40 | ~$0.12 | ~$1.52 | **-$18** | -11% |
| $678 (flat) | ~$0.40 | ~$0.40 | ~$0.80 | **-$90** | -53% |
| $675 (-$3) | ~$0.12 | ~$1.40 | ~$1.52 | **-$18** | -11% |
| $674 (-$4) | ~$0.08 | ~$2.20 | ~$2.28 | **+$58** | +34% |
| $672 (-$6) | ~$0.03 | ~$4.10 | ~$4.13 | **+$243** | +143% |
| $668 (-$10, gap fill accelerates) | ~$0.00 | ~$8.00 | ~$8.00 | **+$630** | +371% |

**Key number:** You need ~$3.70 SPY move in either direction to profit. PCE surprise reactions average $3.80-$4.20. This is a slightly better than even-money bet with asymmetric upside on big moves.

**Borey's scenario (hot PCE + ceasefire collapse):** If PCE is hot AND a geopolitical headline hits Thursday morning, SPY could drop $8-12. The $676 put goes to $6-10. That is $430-$830 profit on $170 risk. This is the tail event that MPW's $15K trade captured.

---

## Why Strangle, Not Straddle (0DTE Version)

| | Straddle ($678C + $678P) | Strangle ($680C / $676P) |
|---|---|---|
| Cost | ~$2.40 ($240) | ~$1.70 ($170) |
| Breakeven | $680.40 / $675.60 ($2.40 move) | $681.70 / $674.30 ($3.70 move) |
| Max risk | $240 (2.4% of $10K) | $170 (1.7% of $10K) |
| Profit on $5 SPY move | ~$260 (+108%) | ~$160 (+94%) |
| Profit on $3 SPY move | ~$60 (+25%) | ~-$18 (breakeven) |
| Loss on inline PCE | ~$160 (sell residual $0.80) | ~$90 (sell residual $0.80) |

**Verdict: strangle.** The straddle profits on smaller $3 moves but costs $70 more. In the inline scenario (the one that kills you), the straddle loses $160 vs the strangle's $90. Over multiple data-release trades, the lower inline-print loss is the edge. The swarm confirmed strangles cost 40-60% less than straddles with similar breakevens. On a $10K account, the $70 savings is material.

---

## Risk Flags

1. **Inline PCE (30-40% probability).** The one scenario where both legs decay. Mitigated by: time stop at 10:30 (recovers ~$60-80 residual), and the pre-market observation abort condition (if futures barely move, you can skip entirely).

2. **Pre-market exhaustion.** If SPY has already moved $5+ in futures before 9:30, the directional move is largely done. The winning leg is expensive at entry and the losing leg is worthless. The abort condition handles this, but the temptation to enter anyway is real. Do not.

3. **VIX spike pre-entry.** If VIX jumps to 25+ on overnight geopolitical headlines, 0DTE premiums inflate. The strangle costs $2.50+ instead of $1.70. Risk/reward degrades. Skip if strangle cost exceeds $2.20 at entry.

4. **Reversal after entry.** SPY drops $3 on PCE, you sell the losing call, then SPY reverses and rallies $4. You are now flat on a move that would have paid. This is the cost of the MPW method -- you accept that cutting the loser sometimes means cutting a winner-in-waiting. The alternative (holding both legs) loses more often than it wins. Trust the method.

5. **Liquidity illusion.** SPY 0DTE options are liquid in aggregate but individual strikes can have wide spreads in the first 60 seconds after open. Use limit orders at mid. Do not market order.

---

## What This Trade Is

- A **catalyst scalp** timed to a known binary event
- A **volatility bet** that realized movement will exceed implied pricing
- A **30-90 minute hold**, not a day trade, not an overnight position
- A **repeatable structure** usable on every major data release (PCE, CPI, NFP, FOMC)
- MPW's strangle method applied to the cheapest possible expression (0DTE)

## What This Trade Is NOT

- A directional bet on PCE hot or soft
- A position to hold into CPI Friday or the weekend
- A hedge for any other position
- A trade to double down on if it is not working
- Something to attempt on a non-catalyst day (0DTE strangles without a catalyst are theta donation)

---

## Execution Checklist — Thursday April 9

### Pre-Market (7:00-8:30 AM ET)
- [ ] Review PCE consensus estimate (Bloomberg, CNBC, Econoday)
- [ ] Note core PCE MoM consensus (~0.3% expected) and YoY
- [ ] Have broker platform open with SPY Apr 9 $680C and $676P quotes ready
- [ ] Set alerts: ES futures at +/- 15 points, +/- 30 points, +/- 50 points from prior close

### PCE Release (8:30 AM ET)
- [ ] Check the actual PCE print immediately (CNBC, Bloomberg, Twitter/X)
- [ ] Compare to consensus: hot (above), soft (below), or inline
- [ ] Monitor ES futures reaction magnitude through 9:30 AM
- [ ] Record: ES moved ___ points, direction is ___, SPY pre-market at ___

### Entry Decision (9:30-9:40 AM ET)
- [ ] Check abort conditions (SPY moved >$5? VIX >28? VIX <15? SPY flat?)
- [ ] If no abort: at 9:35-9:40, enter limit orders at mid-price for both legs
- [ ] Confirm fills on both legs within 60 seconds
- [ ] If only one fills, cancel unfilled and close filled leg immediately
- [ ] Record entry prices: Call @ $___, Put @ $___, Total strangle = $___

### Active Management (9:40-10:30 AM ET)
- [ ] Set alert: either leg at $1.70 (2x entry = take profit trigger)
- [ ] Monitor SPY direction commitment (15-min sustained move = kill the loser)
- [ ] When winner hits 2x: SELL. Then sell loser if >$0.10
- [ ] If direction clear but winner hasn't hit 2x by 10:15: tighten to 10:20 close
- [ ] **10:30 AM: CLOSE EVERYTHING REMAINING. No exceptions.**

### Post-Trade (10:30-11:00 AM ET)
- [ ] Record: exit prices, SPY level at exit, total P&L
- [ ] Log PCE print vs consensus, reaction magnitude, whether the trade worked
- [ ] Do NOT re-enter. One shot per data release. The edge is in the first reaction
- [ ] You are now FLAT. No positions into CPI Friday. No weekend risk.

---

## Summary

| Field | Value |
|---|---|
| Position | Long 1x SPY Apr 9 0DTE $680C / $676P strangle |
| Entry | Thu Apr 9, 9:35-9:40 AM ET (post-PCE, post-open) |
| Cost | ~$1.70/strangle ($170 total) |
| Max loss | $170 (1.7% of $10K) |
| Realistic loss (inline PCE) | $90-$110 after time stop salvage |
| Breakeven up | $681.70 (+0.55%) |
| Breakeven down | $674.30 (-0.55%) |
| Target | 2x premium on winning leg (+$80-$250) |
| Tail case (big move) | +$250-$630 |
| Time stop | 10:30 AM ET — close everything |
| Weekend exposure | Zero — flat by Thursday 10:30 AM |
| Edge | 0DTE gamma on a known catalyst, MPW exit discipline |
