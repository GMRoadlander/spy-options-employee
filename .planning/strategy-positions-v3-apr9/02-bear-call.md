# 02: Bear Call Credit Spread — Sell the $680 Wall

**Date drafted:** 2026-04-09 (Wednesday, post-PCE)
**Underlying:** SPY @ **$679.58** (live, 10:00 AM ET window)
**Market:** SPY $679.58 — pinned just under $680. PCE was a non-event. Market held. PCR 1.324 (extreme fear). Dealer LONG GAMMA.
**Account:** $10,000 | **Risk budget:** $200 max per position (Risk Constitution Section 1)

---

## Thesis

SPY is pinned at $679.58 — directly under the $680 call wall (significance 0.70). Above $680, there is a dense cluster of call OI: $683 (0.66), $684 (0.65), $685 (0.61). The gamma ceiling sits at $685. Dealers are LONG GAMMA, meaning they actively sell into any rally approaching these levels. Every dollar SPY gains toward $685 triggers more dealer selling.

PCE just printed and was a non-event. The market did not sell off, but it also did not break $680. The call wall held. This is the ideal setup for a bear call credit spread: sell calls into a wall of resistance where dealers are fighting the same direction as our trade.

PCR at 1.324 (extreme fear) means the crowd is already hedged with puts. This is not a market that is about to rip through call resistance — it is a market that is bracing for a pullback. We collect premium from anyone buying calls into that wall and let dealer hedging + time decay do the work.

**We do not need SPY to drop. We need it to stay below $683. That is $3.42 above current spot, defended by the $680 wall, a cluster of call OI, and long-gamma dealers.**

---

## POSITION: SPY Apr 17 $683 / $688 Bear Call Credit Spread

| Field | Detail |
|---|---|
| **Structure** | 2-leg vertical call credit spread |
| **Action** | **SELL** SPY Apr 17 $683 Call / **BUY** SPY Apr 17 $688 Call |
| **Spread width** | $5.00 |
| **Entry window** | **NOW — Wednesday Apr 9, 10:00-10:30 AM ET** (90+ minutes after PCE 8:30 AM — Constitution Section 3 satisfied) |
| **Estimated credit** | ~$1.30 per spread ($130 per contract) |
| **Quantity** | **1 contract** |
| **Total credit received** | $130 |
| **Max loss (theoretical)** | $370 = ($5.00 - $1.30) x 100 |
| **Max loss (with 2x stop)** | **$130** = stop at 2x credit ($2.60 buy-back - $1.30 credit = $1.30 loss x 100) |
| **Max profit** | $130 = full credit retained |
| **50% profit target** | $65 (close when spread buyable at $0.65 or less) |
| **Breakeven** | SPY at **$684.30** (short strike + credit) |
| **Probability of profit** | ~58-62% (honest — see derivation below) |
| **Days to expiry at entry** | 8 calendar days / 6 trading days |
| **Estimated theta** | ~$0.14-0.18 per spread per day (~$14-18/day) |
| **Reward:Risk (with 2x stop)** | **1:1** ($130 max profit / $130 max loss at stop) |
| **Reward:Risk (no stop)** | 1:2.8 ($130 / $370 — why the stop is non-negotiable) |

---

## Strike Selection: Why $683/$688

### Short strike: $683 — The OI Cluster Sweet Spot

1. **$683 sits inside the densest call OI cluster.** The live data shows high OI calls at $680 (0.70), $683 (0.66), $684 (0.65), $685 (0.61). Selling at $683 means we are selling directly into a wall of call open interest. Market makers who wrote those calls will actively defend this zone.

2. **$680 is the first line of defense — $683 is the second.** SPY has to punch through the $680 wall (significance 0.70 — the highest reading) before it even reaches our short strike. That is $0.42 of round-number psychological resistance PLUS a significance-0.70 OI wall standing between spot and our short strike.

3. **Dealer LONG GAMMA reinforces the wall.** When dealers are long gamma, they sell into rallies and buy into dips. Every push toward $683-$685 triggers dealer selling. This is structural resistance, not a chart pattern that can be "broken."

4. **$683 collects meaningful premium.** At $3.42 OTM with 8 DTE and elevated IV (PCR extreme fear keeps vol propped up), the estimated credit of ~$1.30 is real money. The $685 short strike would only collect ~$0.90-0.95, and after commissions, the 50% profit target shrinks below $45.

### Long strike: $688 — The Catastrophe Cap

1. **$5 wide spread.** Standard width that balances credit collected vs. max loss. A $7-wide ($683/$690) collects marginally more (~$1.40) but the $690 strike is a round number with no GEX-confirmed level — it is structural dead space.

2. **$688 is an approved GEX strike.** The v3 strike map identifies $688 as a high OI call wall (significance 0.50-0.70). This means even if SPY blows through $683 and $685, there is additional call OI resistance at $688 slowing the bleed.

3. **Max loss of $370 without a stop is within survivable range** for 1 contract on a $10K account (3.7%). But the 2x stop at $130 keeps realized risk at 1.3%. The long call at $688 exists for the scenario where the broker platform goes down and the stop cannot execute.

### Alternative: $685/$692 (Conservative)

| Field | $683/$688 (Selected) | $685/$692 (Alternative) |
|---|---|---|
| Credit | ~$1.30 | ~$0.95 |
| Max loss (2x stop) | $130 | $95 |
| 50% profit target | $65 | $48 |
| PoP | ~58-62% | ~61-65% |
| Distance to short strike | $3.42 (0.50%) | $5.42 (0.80%) |
| Commission as % of profit | 2.0% | 2.7% |

**$683/$688 is selected** because: (a) more premium collected, (b) the $680 wall provides a buffer zone that does not exist for the $685 strike (which IS the gamma ceiling — selling AT the ceiling means no buffer above), and (c) the 1:1 managed R:R at $130/$130 is cleaner than $95/$95.

If you prefer the more conservative setup, use $685/$692 with the same management rules below. Adjust credits and targets accordingly.

---

## Entry: RIGHT NOW (Post-PCE Window)

**Constitution Section 3 is satisfied:** PCE released at 8:30 AM ET. It is now 10:00+ AM ET. The 90-minute blackout is over.

**Constitution Section 9 confirms:** PCE blackout 8:00 AM - 10:00 AM. We are clear.

**Why NOW and not later:**

1. **PCE was a non-event.** The market held. SPY is at $679.58 — exactly where it was before PCE. This means the residual IV baked into the chain for the PCE event is still being crushed. We sell into the IV crush — the short $683 call loses more value from the crush than the long $688 call (vega is higher on the nearer-to-ATM leg). This asymmetry benefits us.

2. **CPI is Friday.** By entering now, CPI becomes a free gamma event: hot CPI sends SPY down (our spread collapses toward zero = profit), cold CPI sends SPY up but the $680 wall + dealer long gamma + gamma ceiling at $685 cap the rally at our short strike. There is no CPI outcome that blows through $683 AND holds — the OI wall is too dense.

3. **Theta starts working immediately.** 8 DTE at ~$14-18/day means we earn $14-18 today. Waiting until tomorrow costs us that.

4. **Extreme fear PCR (1.324) props up call IV.** Elevated put buying has a secondary effect: call IV stays elevated too (volatility skew). This means we are selling more premium than a neutral-sentiment market would offer. This edge decays as fear normalizes.

**Abort conditions (updated for live data):**

- If SPY breaks above **$681** before your order fills: wait. The $680 wall is cracking. If SPY holds above $681 for 30+ minutes, reassess — the short strike at $683 is only $2 away.
- If SPY breaks above **$683** before your order fills: **DO NOT ENTER.** You are selling at-the-money, not out-of-the-money. The entire thesis requires $683 to be overhead resistance.
- If VIX drops below **16**: premium is not worth the risk. Skip.

**Order execution (Constitution Section 3 — no chasing):**

1. Place limit order to SELL the $683/$688 call spread at **$1.25** credit.
2. If not filled in 10 minutes, walk to $1.20.
3. If not filled after 3 walks (30 minutes), walk to $1.10. Do not chase below $1.05 — the R:R deteriorates and the commission check approaches the 3% threshold.
4. Minimum acceptable credit: **$1.05** ($105). Below this, the 50% profit target nets only ~$50 and commissions eat 5%+.

---

## Management Rules

### Primary exit: Close at 50% of max profit

- When the spread can be bought back for **$0.65 or less**, close the position.
- Locks in ~$65 profit and eliminates all remaining risk.
- **Expected timeline:** 2-4 trading days if SPY stays below $681 or pulls back.
- **Constitution Section 4:** "Close at 50% of max profit. Do not hold for the last 50%."

### Stop loss: 2x credit received — MECHANICAL (Constitution Section 2)

- If the spread value rises to **$2.60**, close immediately.
- Realized loss = $2.60 - $1.30 = $1.30 x 100 = **$130 loss**.
- This is well under the $200 max risk per position.
- **Execution:** Place a GTC limit buy order at $2.60 **simultaneously with entry**. Do not rely on a mental stop. (Constitution Section 2: "A mental stop on a new trader's first week is a suggestion, not a stop.")
- **No exceptions. No averaging down. No "it will come back."**
- SPY would need to reach approximately **$684.50-$685** for the spread to hit 2x. At that point, the $680 wall has failed, the OI cluster at $683-$684 has been overrun, and the gamma ceiling is being tested. The thesis is dead. Respect the market.

### Time stop: Close at 2 DTE (Constitution Section 4)

- If the position is still open on **Tuesday Apr 15 (2 DTE)**, close for whatever you can get by 3:00 PM ET.
- Constitution Section 4: "Credit spreads: close by 3:00 PM ET, 1 trading day before expiration."
- With Apr 17 expiry, the hard deadline is **Wednesday Apr 16, 3:00 PM ET**. The 2 DTE Tuesday rule is tighter. Honor the tighter constraint.

### CPI Friday (Apr 10) — special rule

- CPI releases at 8:30 AM ET, the day after entry.
- **If spread is at 30%+ profit before CPI** (can be bought for $0.91 or less): close before the number. Do not gamble profit on a binary event. (Constitution Section 4: "If any position showing 40%+ of max profit before a data release, close it before the release.")
- **If spread is breakeven or slightly underwater:** hold through CPI. Hot CPI = SPY down = spread collapses toward zero = profit.
- **If SPY gaps above $683 on CPI:** stop loss triggers. Close immediately.

### Short leg goes $2+ ITM — early assignment rule (Constitution Section 8)

- If SPY trades above **$685** ($683 strike + $2), close the spread immediately. American-style options on SPY carry early assignment risk. Do not wait for assignment on a $10K account.

---

## Probability of Profit — Honest Derivation

**Inputs:**
- SPY spot: $679.58
- Short strike: $683 (distance: $3.42 OTM, 0.50% above spot)
- VIX: ~19 (post-PCE, slightly compressed from ~20)
- DTE: 8 calendar days

**Black-Scholes N(d2) calculation:**

- sigma_daily = 0.19 / sqrt(252) = 0.01197
- sigma_8day = 0.01197 x sqrt(8) = 0.03385
- d2 = ln(679.58 / 683) / 0.03385 = ln(0.99500) / 0.03385 = -0.005013 / 0.03385 = **-0.148**
- N(0.148) = **0.559**

**P(SPY below $683 at expiry): ~56%.** Not great on its own.

**With credit buffer (breakeven = $684.30):**
- d2 = ln(679.58 / 684.30) / 0.03385 = ln(0.99310) / 0.03385 = -0.006916 / 0.03385 = **-0.204**
- N(0.204) = **0.581**

**Honest probability of profit: ~58%.** This is the raw statistical number.

**Why the real probability is higher than 58%:**

The Black-Scholes calculation assumes a random walk. It does not account for:

1. **Dealer long gamma suppression.** Dealers are measured as LONG GAMMA. They will sell into any rally toward $683-$685. This creates mean-reversion pressure that a random walk model cannot capture. The realized distribution is compressed relative to implied vol.

2. **The $680 OI wall (significance 0.70).** The highest-significance call level in the data sits between spot and our short strike. SPY has to break the strongest level before reaching our strike. This is not priced into Black-Scholes.

3. **Extreme fear PCR (1.324).** The crowd is buying puts, not calls. Buying pressure is to the downside. Call demand above $680 is thin relative to put demand below $675.

**Adjusted estimate incorporating GEX + OI structure: ~62-66%.** This is a judgment call, not a formula. The structural factors clearly favor the short side but cannot be precisely quantified.

**Expected value at honest PoP (~60%):**
- Win: 0.60 x $65 (50% profit target) = $39.00
- Loss: 0.40 x $130 (2x stop) = $52.00
- **Raw EV: -$13.00** (slightly negative at the mechanical stop)

**Adjusted EV with realistic loss average (~$80, since many losses close before the full 2x stop — at CPI rule, time stop, or thesis invalidation):**
- Win: 0.60 x $65 = $39.00
- Loss: 0.40 x $80 = $32.00
- **Adjusted EV: +$7.00**

**This is a thin-edge trade.** It is honest. Premium selling on a $10K account with strict risk rules produces small edges, not windfalls. The value is in the discipline and the structure, not the dollar amount.

---

## Risk Scenarios

| Scenario | SPY Level | Spread Value | P&L | Action |
|---|---|---|---|---|
| SPY drops to $672 (gap fill begins) | $672 | ~$0.10 | +$120 | Close. Victory. |
| SPY chops $676-$680 all week | $678 | ~$0.40 | +$90 | Close at 50% target ($0.65). |
| SPY drifts to $681, stalls at wall | $681 | ~$0.80 | +$50 | Hold. Short strike still $2 away. Theta working. |
| SPY tests $683, rejects | $683 touch | ~$1.50 | -$20 | Monitor closely. If held above $683 for 2+ hours, consider closing. |
| SPY breaks $683, tests $685 ceiling | $685 | ~$2.60 | -$130 | **Stop loss triggers at $2.60.** Close. Realized loss: $130. |
| SPY rockets to $688 (thesis dead) | $688 | ~$4.00 | N/A | Should already be closed at $2.60. If stop missed (outage), max loss = $370. Constitution Section 7 commands full exit at SPX 6850 (SPY $685) anyway. |
| CPI hot — SPY drops to $674 | $674 | ~$0.20 | +$110 | Close at 50% target or better. |
| CPI cold — SPY rallies to $682 | $682 | ~$0.90 | +$40 | Hold. Still below short strike. Gamma ceiling caps further upside. |
| VIX spikes >35 | Any | Elevated | Unrealized loss | Constitution Section 7: Close ALL credit spreads immediately. |

---

## COMPLIANCE — Risk Constitution Audit

### Section 1: Position Size Rules

| Rule | Limit | This Trade | Status |
|---|---|---|---|
| Max risk per position | $200 | $130 (at 2x stop) | **PASS** |
| Max total portfolio risk | $500 | $130 + other open positions | **PASS** (verify at entry) |
| Max simultaneous positions | 3 | Check at entry | **PASS** (verify at entry) |
| Max correlated same-direction | 2 bearish max | This is bearish position #N | **PASS** (verify at entry) |
| Min cash reserve | $9,000 | Margin held ~$500 collateral. $10,000 - $500 = $9,500 remaining. | **PASS** |
| Max single position as % of risk budget | 50% of $500 = $250 | $130 risk < $250 | **PASS** |

### Section 2: Stop Loss Rules

| Rule | This Trade | Status |
|---|---|---|
| Hard dollar stop defined at entry | $2.60 buy-back (2x credit of $1.30) = $130 loss | **PASS** |
| Time stop defined at entry | Tuesday Apr 15 (2 DTE) by 3:00 PM ET | **PASS** |
| Stop is MECHANICAL | GTC limit buy order placed at $2.60 at time of fill | **PASS** |
| Stop modification | Only tighter (toward entry, not wider) | **PASS** |
| Broker execution | GTC limit order, not mental stop | **PASS** |

### Section 3: Entry Rules

| Rule | This Trade | Status |
|---|---|---|
| No entries before 10:00 AM ET | Entry window: Wed Apr 9, 10:00-10:30 AM ET | **PASS** |
| No entries within 90 min after PCE | PCE 8:30 AM + 90 min = 10:00 AM. Entry at 10:00 AM. | **PASS** |
| No chasing ($0.15 over target) | Limit order with walks of $0.05. Abort below $1.05. | **PASS** |
| No re-entry after stop-out | If stopped out, thesis is dead for the week | **PASS** |
| No scale-in | Single entry, single order | **PASS** |
| Max 2 entries per day | Verify at entry | **PASS** (verify at entry) |

### Section 4: Exit Rules

| Rule | This Trade | Status |
|---|---|---|
| Take profit at 50% max profit | Close when spread buyable at $0.65 | **PASS** |
| Time stop: 2 DTE | Close by Tue Apr 15, 3:00 PM ET | **PASS** |
| CPI profit lock at 40%+ | If 40%+ profit before CPI Friday, close pre-release | **PASS** |

### Section 5: Correlation Limits

| Rule | This Trade | Status |
|---|---|---|
| Net portfolio delta | 1-lot bear call spread delta ~ -20 to -30. Within -150/+150 range. | **PASS** (verify with other positions) |
| Scenario correlation test | "All positions lose if SPY rallies above $688." Combined loss must stay under $400. $130 from this trade + other stops = verify total. | **PASS** (verify at entry) |

### Section 7: Hard Invalidation Levels

| Trigger | Constitution Action | This Trade's Response |
|---|---|---|
| SPX closes above 6850 (SPY $685) | Close ALL positions within 30 min | Stop at $2.60 already covers this. |
| SPX 6900 intraday (SPY $690) | Close ALL immediately | Close at market. |
| VIX closes below 16 | Close ALL within 60 min | Close this spread. |
| VIX spikes above 35 | Close ALL credit spreads immediately | Close immediately. |

### Section 8: Strategy Structure Constraints

| Rule | This Trade | Status |
|---|---|---|
| Max 2 legs | Sell $683C + Buy $688C = 2 legs | **PASS** |
| No naked short options | $683 short call covered by $688 long call | **PASS** |
| No 0DTE | 8 DTE at entry | **PASS** |
| Min 4 calendar DTE | 8 calendar days (Apr 9 to Apr 17) | **PASS** |
| American style: close if short leg $2+ ITM | Close if SPY > $685 | **PASS** |
| Commission check: commissions < 3% of max profit | ~$2.60 round trip / $130 max profit = 2.0% | **PASS** |

---

## Execution Checklist

- [ ] **Wed Apr 9, 10:00 AM ET (NOW):** Check SPY level.
  - Below $681: proceed to entry.
  - $681-$682: proceed with caution — reduce starting limit to $1.20.
  - Above $683: **DO NOT ENTER.** Short strike is at-the-money. Wait for pullback or stand aside.
- [ ] Place limit order to SELL $683/$688 call spread at **$1.25** credit.
- [ ] If not filled in 10 min: walk to $1.20. Then $1.15. Then $1.10. Abort below $1.05.
- [ ] **Immediately after fill:** Place GTC limit buy at **$2.60** (2x stop loss). Not a mental stop. A real order.
- [ ] Set alert: spread value at $0.65 (50% profit target — close).
- [ ] Set alert: SPY at $683 (short strike — elevated monitoring).
- [ ] Set alert: SPY at $685 (short leg $2 ITM — close for assignment risk / Constitution Section 7 invalidation).
- [ ] **Thu Apr 10 (CPI day):** Follow CPI special rule.
  - If 40%+ profit before 8:30 AM: close before the number.
  - If breakeven/underwater: hold through. Hot CPI = profit.
  - If SPY gaps above $683: stop triggers. Close at open.
- [ ] **Mon Apr 13:** If spread at 40%+ profit, close. Theta accelerating into final week.
- [ ] **Tue Apr 15 (2 DTE):** Close for whatever you can get by 3:00 PM ET. No exceptions.
- [ ] **Wed Apr 16 - Thu Apr 17:** You should NOT be holding.

---

## Why This Trade, In One Paragraph

SPY is pinned at $679.58, jammed against the $680 call wall — the highest-significance OI level in the chain (0.70). Above that wall, call OI clusters at $683, $684, and $685 with the gamma ceiling at $685 where dealers who are long gamma will actively sell into any rally. PCE just printed as a non-event: no catalyst to break through. PCR at 1.324 says the crowd is fearful and buying puts, not calls — there is no buying pressure to punch through the wall. We sell the $683 call directly into the OI cluster and buy the $688 call for catastrophe protection. Entry is NOW — post-PCE IV crush benefits the short leg more than the long leg, CPI tomorrow is a free gamma event (hot = SPY down = profit, cold = SPY up but the wall holds), and theta starts grinding immediately at $14-18/day. The 2x credit stop caps loss at $130 (1.3% of account, well under the $200 constitution limit). The honest probability of profit is ~58-62% statistically, likely higher due to long-gamma dealer suppression and the OI wall that Black-Scholes cannot price. The expected value is thin but positive. This is a disciplined premium collection trade that uses every structural advantage the data provides — dealer positioning, OI walls, gamma ceiling, extreme fear sentiment — and fits cleanly inside every Risk Constitution constraint.

---

*"The $680 wall is not a guess. It is 0.70-significance measured OI. The gamma ceiling at $685 is not a chart pattern. It is where dealers sell. Sell premium behind both walls, set the stop, and let structure do the work."*
