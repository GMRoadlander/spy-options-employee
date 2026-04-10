# W2-04 -- Scale-In Put Ladder (2 Entries, GEX-Anchored)

**Date drafted:** 2026-04-06
**Market snapshot:** SPX ~6783 (SPY ~678). AT the gamma flip. Gap fill target 661. Timing uncertain.
**Conviction:** Direction 8/10, Timing 5/10, Magnitude 4/10. Overall: 6/10 (MEDIUM).
**Correlation budget slot:** Category 1 (Core Bearish). This is 1 of max 2 bearish positions. The third portfolio slot MUST be non-bearish per W1-06-correlation-budget.md.

---

## CONSTITUTIONAL COMPLIANCE CHECK

### Rules Satisfied

| Rule | Limit | This Position | Status |
|------|-------|---------------|--------|
| Max risk per position | $200 | $200 total ($100 + $100) | PASS |
| Max total portfolio risk | $500 | $200 (leaves $300 for 2 other positions) | PASS |
| Max positions open simultaneously | 3 | This ladder counts as 1 position (same thesis, same direction) | PASS |
| Max correlated positions (same direction) | 2 | 1 of 2 bearish slots used | PASS |
| Min cash reserve (90%) | $9,000 uninvested | Max $200 committed | PASS |
| Max single position as % of risk budget | 50% ($250) | $200 = 40% of $500 budget | PASS |
| Hard dollar stop per entry | Required | $100 stop on each entry | PASS |
| Time stop | Required | Defined per entry below | PASS |
| No entries before 10:00 AM ET | Required | Entry 1: 10:30+ AM Mon. Entry 2: 10:00+ AM Thu. | PASS |
| No Monday entries before 10:30 AM ET | Required | Entry 1: 10:30-11:00 AM Mon | PASS |
| No entries within 90 min of PCE/CPI | Required | Entry 2: 10:00 AM+ Thu (90 min after 8:30 PCE) | PASS |
| No chasing ($0.15 walk limit, 3 walks max) | Required | Enforced per entry below | PASS |
| Min 4 calendar DTE at entry | Required | Entry 1: 7 DTE (Mon -> Apr 14). Entry 2: 5 DTE (Thu -> Apr 14). | PASS |
| Max 2 legs per position | Required | 1 leg each (straight puts) | PASS |
| No naked short options | Required | Long puts only, no short legs | PASS |
| No 0DTE | Required | Min 5 DTE at entry | PASS |
| Max entries per day | 2 | 1 entry per day (Mon, Thu) | PASS |
| Independent confirmation trigger per entry | Required | Different triggers per entry (see below) | PASS |
| GEX strike compliance | $678, $675 only (long puts) | Entry 1: $678P, Entry 2: $675P | PASS |
| Take profit at 50% max profit | Required | Defined in exit plan | PASS |
| End-of-week rule (close by Thu 3:00 PM) | Required | Time stop: Wed Apr 13 3:00 PM ET | PASS |

### Rule in Tension

| Rule | Constitution Text | This Proposal | Resolution |
|------|-------------------|---------------|------------|
| Scale-in rules | "Not permitted this week." (Section 3) | Two sequential entries on different days with independent triggers | **FLAGGED. See below.** |
| No re-entry after stop-out | "That thesis is dead for the week." | Entry 2 cancelled if Entry 1 stops out. No re-entry. | PASS -- Entry 2 is a NEW entry at a different strike with an independent trigger, not a re-entry of a stopped position. But only if Entry 1 is still alive. |

### Scale-In Constitutional Conflict -- Requires Amendment

The Risk Constitution Section 3 states: *"Scale-in rules: Not permitted this week. A new trader managing scale-in timing on top of position management on top of emotional regulation is three cognitive loads too many."*

This ladder IS a scale-in by definition. It proposes two sequential entries into the same directional thesis on different days.

**Why this specific ladder mitigates the constitutional concern:**

1. Only 2 entries (not 3). Cognitive load is "manage 1 put, then maybe 1 more put." Not 3 legs with 3 triggers.
2. Each entry is a single contract of a single put. No spread management. No short legs. The simplest possible option position.
3. The cancel rule is hard-wired: if Entry 1 stops out, Entry 2 is cancelled permanently. There is no "try again" path. The ladder fails safe.
4. Total risk across both entries ($200) equals one normal position's budget. The scaling is within the single-position limit, not above it.
5. The entries are separated by 3 trading days (Monday and Thursday), not hours. This is not rapid-fire adding; it is a deliberate, pre-planned conditional entry.

**Decision required:** Gil must explicitly amend the constitution to permit this specific scale-in structure before execution. The amendment should be narrow: "Two-entry scale-in is permitted ONLY when (a) total combined risk is within a single position's $200 limit, (b) each entry is a single-leg long option, (c) second entry is cancelled if first entry stops out, (d) entries are on different trading days." No broader scale-in permission is granted.

If the amendment is not approved, this document serves as a paper-trade reference only.

---

## Rationale: Why Scale In, Why Not All-In

SPY is AT the gamma flip ($678). The thesis (gap fill to 661) has 70% probability but the TIMING conviction is only 5/10. A single all-in entry Monday morning bets $200 that the move starts this week. If the move starts Thursday after PCE, Monday's put has bled 3 days of theta. If the move starts next week, both entries expire.

The scale-in solves the timing problem:
- **Entry 1 (Probe):** $100 of information. Buys exposure at the gamma flip while it is still relevant. If SPY fades below the flip into negative GEX territory, you have a position ahead of the crowd.
- **Entry 2 (Confirm):** $100 of conviction. Fires ONLY if Entry 1 is working AND an independent catalyst confirms the thesis. Adds at a lower strike (max pain magnet) where premium is cheaper post-PCE IV crush.
- **If the probe fails:** You lose $100, not $200. Entry 2 never fires. You preserved half the budget.

The descending strikes ($678 then $675) mean you scale DOWN as conviction grows -- paying less per contract at a strike closer to the max pain magnet. You are not throwing more money at a losing trade; you are adding to a winning position at a better price.

---

## ENTRY 1 -- PROBE ($100 max loss)

```
POSITION: Buy 1x SPY Apr 14 $678P -- Gamma Flip Probe
Action: Buy to open 1x SPY $678 Put, Apr 14 expiry (Monday weekly)
Entry: Monday April 7, 10:30-11:00 AM ET (after extended Monday blackout)
Cost/Credit: ~$4.50 per contract ($450 total debit) [ATM put, 7 DTE, VIX ~20]
Quantity: 1 contract
Max loss: $100 (stop loss enforced)
Max profit: ~$1,250 at SPY $661 (gap fill: $678 - $661 = $17 intrinsic, minus ~$4.50 cost = ~$12.50 x 100)
Breakeven: SPY ~$673.50
Take profit: See combined exit plan below
Stop loss: Sell if contract value drops to $3.50. Loss = $4.50 - $3.50 = $1.00 x 100 = $100 (1% of account)
Time stop: Exit by Wednesday April 13, 3:00 PM ET (2 trading days before expiry, per constitution)
Invalidation: SPY closes above $685 on any day. VIX drops below 16. Entry 2 cancelled.
```

### Strike Logic: $678 (Gamma Flip)

- $678 is the gamma flip level per W1-02-gex-strike-map.md (significance 1.0, highest on the map).
- ATM at entry. Delta ~-0.50. Maximum participation in any initial fade.
- If SPY breaks below $678, it enters negative GEX territory where dealer hedging AMPLIFIES the move. The put is positioned exactly at the regime change boundary.
- GEX alignment: platform classifies puts at the flip as "marginally aligned" -- if spot drops below 6780, puts become firmly "aligned."

### Expiry Logic: Apr 14 (7 DTE at entry)

- Satisfies min 4 DTE constitutional requirement with margin.
- Apr 11 would leave only 4 calendar DTE, but the end-of-week rule requires closing by Thursday 3:00 PM -- that is only 3 trading days of exposure. Apr 14 gives a full 5 trading days (Mon-Fri) plus the weekend if still alive.
- Apr 17 would give more time but costs more premium, pushing the stop further and making $100 max loss harder to achieve with an ATM put.
- Apr 14 balances theta cost against time for the thesis to develop.

### Entry Trigger (Independent Confirmation Required)

**Trigger A (preferred):** SPY breaks below $677 (below gamma flip) by 10:30 AM Monday. The market is rejecting the ceasefire gap. Negative GEX territory confirmed. Buy the $678P as SPY moves into the amplification zone.

**Trigger B (fade the pop):** SPY opens Monday at $679-681 (small pop on residual ceasefire optimism) and reverses back to $678 by 10:30-11:00 AM. The failed rally IS the signal. Market tried to extend the gap and failed. Buy the put on the rejection.

### Skip Entry 1 If

- SPY is above $682 at 10:30 AM Monday. The gap is extending, not fading. Do not probe against momentum.
- VIX is below 17 pre-market Monday. Market is too complacent for the bear thesis.
- SPY is already below $674 at 10:30 AM Monday. The move already happened without you. Do not chase. Discipline over FOMO.

### Stop Loss Mechanics

- **Hard stop: sell $678P at $3.50 GTC.** Set immediately after fill.
- $4.50 entry - $3.50 stop = $1.00 loss x 100 shares = **$100 loss (1% of account).**
- This corresponds to SPY holding above ~$679-680 with theta compression. If SPY is UP on Monday afternoon and the put has lost $1.00, the thesis is failing in the expected timeframe.
- **Stop may only be moved in the profitable direction** (constitution Section 2). If SPY drops to $674, move stop to $4.50 (breakeven). Never widen the stop.

### No-Chase Rule

- Limit buy at $4.50. Walk by $0.05 increments, max 3 times, over 30 minutes (per constitution).
- Max entry price: $4.65.
- If unfilled at $4.65 after 30 minutes, skip Entry 1. The market is telling you the price is wrong.
- If Entry 1 is skipped, Entry 2 is also cancelled. No probe = no ladder.

---

## ENTRY 2 -- CONFIRM ($100 max loss)

```
POSITION: Buy 1x SPY Apr 14 $675P -- Max Pain Confirmation
Action: Buy to open 1x SPY $675 Put, Apr 14 expiry
Entry: Thursday April 9, 10:00-10:30 AM ET (after PCE settles, 90-min blackout respected)
Cost/Credit: ~$2.20 per contract ($220 total debit) [~3pt OTM post-PCE, 5 DTE, IV crushed]
Quantity: 1 contract
Max loss: $100 (stop loss enforced)
Max profit: ~$1,180 at SPY $661 ($675 - $661 = $14 intrinsic, minus ~$2.20 cost = ~$11.80 x 100)
Breakeven: SPY ~$672.80
Take profit: See combined exit plan below
Stop loss: Sell if contract value drops to $1.20. Loss = $2.20 - $1.20 = $1.00 x 100 = $100 (1% of account)
Time stop: Exit by Wednesday April 13, 3:00 PM ET (same as Entry 1)
Invalidation: SPY closes above $685 on any day. VIX drops below 16. Entry 1 already stopped out.
```

### Strike Logic: $675 (Max Pain Magnet)

- $675 is the max pain level per W1-02-gex-strike-map.md (significance 0.8).
- By Thursday, if the thesis is working, SPY should be at $674-676 (drifting toward max pain). The $675P is approximately ATM at the time of entry -- not 3 points OTM as it appears from Monday's spot.
- Max pain acts as a gravitational magnet into expiration. A put struck at max pain benefits from the pull-down effect when spot is above max pain.
- Scaling DOWN from $678 to $675 means paying less premium per contract. Entry 2 is cheaper than Entry 1 -- you are adding at a better price, not throwing more money at the same level.

### Expiry Logic: Apr 14 (5 DTE at entry)

- Same expiry as Entry 1. Both puts expire together -- simplifies management.
- 5 DTE at Thursday entry satisfies the min 4 DTE requirement.
- The end-of-week rule (close by Thu 3:00 PM, 2 trading days before expiry) gives until Wednesday Apr 13 -- 4 trading days of exposure from Thursday entry.

### Entry Trigger (Independent Confirmation -- DIFFERENT from Entry 1)

Entry 2 requires ALL of the following:

1. **Entry 1 is still alive.** Not stopped out. If Entry 1 was stopped, Entry 2 is cancelled permanently. No exceptions. The probe failed; the ladder is dead.

2. **Entry 1 is at breakeven or profitable.** The probe is WORKING. SPY has moved in the thesis direction. Do not add to a losing position.

3. **Independent catalyst confirmation (at least one):**

   - **Trigger A (PCE hot):** Core PCE MoM > +0.3%. Hot inflation data accelerates the sell-off thesis. The market re-prices rate cut expectations lower, which pressures equities. This is independent of the ceasefire thesis -- it is a macro catalyst.

   - **Trigger B (Technical breakdown):** SPY is below $675 at 10:00 AM Thursday, regardless of PCE outcome. The gap fill is structural, not macro-driven. The market is selling even without a catalyst. This is the stronger signal because it confirms the thesis does not depend on a single data point.

   - **Trigger C (Ceasefire deterioration):** Headline ceasefire violation between Monday and Thursday (Houthi attack, IRGC statement, ship seizure). SPY has sold off on the news. The structural analysis is being validated in real time.

### Skip Entry 2 If

- **Entry 1 has been stopped out.** This is the CORE rule of the ladder. If the probe failed, the thesis is not working in the expected timeframe. The $100 probe loss is tuition. Do not throw $100 more after it.
- **Entry 1 is showing a loss** (put value below $4.50 entry). Do not add to a losing position. The probe needs to be at least at breakeven before you add.
- **PCE is soft (core < +0.2%) AND SPY is above $676.** Dovish macro + resilient price = gap fill is delayed or dead. Keep Entry 1 alive with its existing stop but do not add.
- **SPY is already below $670 at 10:00 AM Thursday.** The gap fill is accelerating without you. Entry 2's $675P would be 5 points ITM and expensive. Do not chase deep ITM premium. Let Entry 1 ride.

### Stop Loss Mechanics

- **Hard stop: sell $675P at $1.20 GTC.** Set immediately after fill.
- $2.20 entry - $1.20 stop = $1.00 loss x 100 shares = **$100 loss (1% of account).**
- This corresponds to SPY bouncing back above $676-677 after PCE, with theta accelerating on 4-5 DTE. The PCE catalyst fired but the market absorbed it. The thesis is not dead but the timing is wrong for this expiry.
- **Stop may only be moved in the profitable direction.** If SPY drops to $672, move stop to $2.20 (breakeven).

### No-Chase Rule

- Limit buy at $2.20. Walk by $0.05 increments, max 3 times, over 30 minutes.
- Max entry price: $2.35.
- If unfilled at $2.35 after 30 minutes, skip Entry 2. Entry 1 continues with its own management rules.

---

## Combined Position at Full Scale-In

| Entry | Strike | Expiry | Est. Cost | Max Loss | Trigger | Day |
|-------|--------|--------|-----------|----------|---------|-----|
| 1 (Probe) | $678P | Apr 14 | $450 | $100 | Mon fade below gamma flip | Mon |
| 2 (Confirm) | $675P | Apr 14 | $220 | $100 | PCE hot or SPY < $675 + Entry 1 profitable | Thu |
| **Total** | -- | -- | **~$670** | **$200** | -- | -- |

- Total premium deployed: ~$670 (6.7% of account buying power, but only $200 at risk)
- Total max loss (sum of all stops): **$200 (2.0% of account) = 1 position's budget**
- Each stop is independent
- This consumes 1 of the 2 allowed bearish slots per correlation budget
- Remaining portfolio capacity: 2 positions, $300 risk budget, at least 1 must be non-bearish

### Portfolio-Level Greeks (This Position Only)

| Greek | Entry 1 Only | Both Entries On | Budget Target |
|-------|-------------|-----------------|---------------|
| Delta | ~-50 | ~-85 | Portfolio: -10 to -25 (need hedge) |
| Gamma | ~+0.08 | ~+0.14 | Near zero to +0.5 |
| Theta | ~-$0.65/day | ~-$1.10/day | Portfolio: -$5 to +$10/day |
| Vega | ~+$0.12 | ~+$0.20 | Portfolio: +$20 to +$80 |

**Note:** Delta of -85 (both entries on) significantly exceeds the portfolio delta target of -10 to -25. The non-bearish position (Category 3 hedge) MUST provide at least +60 to +75 delta to bring the portfolio into compliance. This is a binding constraint on the hedge position design.

---

## P&L Scenarios

### Scenario A: Both fire, gap fills to SPY $661 (BEST CASE)

| Entry | Strike | Cost | Value at $661 | P&L |
|-------|--------|------|---------------|-----|
| 1 | $678P | $4.50 | ~$17.00 (intrinsic) | +$12.50 |
| 2 | $675P | $2.20 | ~$14.00 (intrinsic) | +$11.80 |
| **Total** | -- | **$6.70** | **~$31.00** | **+$24.30/share = +$2,430 profit** |

- Return on capital deployed: +363%
- Return on account: +24.3%
- Risk taken: $200 max. Reward: $2,430. **R:R = 12.2:1**
- Note: Take profit at 50% max profit per constitution = close at ~$1,200 combined profit. Do not hold for the full $2,430.

### Scenario B: Both fire, partial gap fill to SPY $670 (gap stalls midway)

| Entry | Strike | Cost | Value at $670 | P&L |
|-------|--------|------|---------------|-----|
| 1 | $678P | $4.50 | ~$9.00 ($8 intrinsic + ~$1 extrinsic) | +$4.50 |
| 2 | $675P | $2.20 | ~$6.00 ($5 intrinsic + ~$1 extrinsic) | +$3.80 |
| **Total** | -- | **$6.70** | **~$15.00** | **+$8.30/share = +$830 profit** |

- Solid profit even on partial fill. Take profit rule likely triggers here.

### Scenario C: Only probe fires, thesis fails (MOST LIKELY LOSS SCENARIO)

| Entry | Strike | Cost | Outcome | P&L |
|-------|--------|------|---------|-----|
| 1 | $678P | $4.50 | Stopped at $3.50 | -$1.00 = **-$100** |
| 2 | -- | -- | Cancelled (probe failed) | $0 |
| **Total** | -- | **$4.50** | -- | **-$100 loss (1% of account)** |

This is the critical advantage: a failed thesis costs $100, not $200. The cancel rule saves $100.

### Scenario D: Probe works, PCE adds, then violent reversal (WORST REALISTIC CASE)

| Entry | Strike | Cost | Outcome | P&L |
|-------|--------|------|---------|-----|
| 1 | $678P | $4.50 | Stopped at $3.50 (reversal Fri) | -$100 |
| 2 | $675P | $2.20 | Stopped at $1.20 | -$100 |
| **Total** | -- | **$6.70** | -- | **-$200 loss (2% of account)** |

This requires: (1) thesis looked right Monday, (2) PCE confirmed Thursday, (3) violent reversal Friday (e.g., credible peace deal announced). Three independent signals confirmed and then a fourth event reversed all three. Low probability.

### Scenario E: Both fire, chop at $678 (SPY pins at gamma flip)

| Entry | Strike | Cost | Outcome | P&L |
|-------|--------|------|---------|-----|
| 1 | $678P | $4.50 | ATM at expiry, ~$1.00 extrinsic | -$3.50 (time stop triggers) |
| 2 | $675P | $2.20 | 3pt OTM, ~$0.40 extrinsic | -$1.80 (time stop triggers) |
| **Total** | -- | **$6.70** | -- | **-$530 premium lost, but stops cap at -$200** |

Stops fire before this scenario plays out fully. Actual loss: -$200 max.

---

## Exit Plan (Both Entries Managed Together)

### Full gap fill -- SPY $661:
- Exit all contracts at SPY $661-663. Do not get greedy below the gap.
- Per constitution: take profit at 50% of max profit. If combined max profit potential is ~$2,400, close at ~$1,200 combined profit (SPY ~$668-669).
- Practically: when combined position shows +$1,000-$1,200 profit, close everything.

### Partial gap fill -- SPY $670 (halfway):
- Combined position is profitable. Entry 1 has $8 intrinsic, Entry 2 has $5 intrinsic.
- Close both. +$830 profit. Do not hold for the last $9 of the gap.
- This IS the 50% max profit threshold. Take it.

### Time stop -- Wednesday April 13, 3:00 PM ET:
- Constitution requires closing 2 trading days before expiration.
- Apr 14 expiry: Wednesday is 1 trading day before, but the constitution says close by **Thursday** 3:00 PM for positions expiring "within the current week." Apr 14 is Monday of the following week, so technically the time stop is more flexible.
- Conservative application: close by Wednesday April 13, 3:00 PM ET. Do NOT hold over the weekend. Weekend gap risk on 1 DTE puts is unacceptable for a new trader.
- If SPY is at $674-676 at time stop: close for modest profit or small loss. Do not hold hoping for Monday continuation.

### CPI profit lock (Friday April 10, pre-8:30 AM):
- If the combined position is showing 40%+ of max profit before CPI release, close it Thursday afternoon per constitution Section 4. Do not gamble a winning position on a binary event.
- If showing < 40% of max profit, hold through CPI with existing stops.

---

## Cancel Conditions (KILL THE LADDER)

**Cancel the entire ladder and exit all open positions if ANY of these occur:**

1. **Entry 1 is stopped out.** Entry 2 is permanently cancelled. This is the core rule. No exceptions.

2. **SPY closes above $685 on any day.** The gamma ceiling ($685 per GEX map) has been breached. The ceasefire rally is extending, not fading. Exit Entry 1 at market.

3. **VIX drops below 16.** Market has fully priced in peace. Vol crush kills both puts. Exit everything.

4. **SPX trades above 6900 (SPY above $690) intraday.** Per constitution Section 7, close ALL positions immediately. The thesis is catastrophically wrong.

5. **Ceasefire upgraded to permanent deal** (per constitution criteria: IRGC + Supreme National Security Council both confirm, Houthi attacks cease 48+ hours, oil below $85).

6. **Gil has lost $400 cumulative across all closed + open positions.** Per constitution Section 7, close ALL remaining positions. Trading is done for the week.

7. **All open positions simultaneously showing losses totaling > $300.** Per correlation budget circuit breaker, close the worst-performing position immediately.

---

## Execution Checklist

### Sunday Night (April 6):
- [ ] Check ES futures. If gap UP above SPX 6830, prepare to skip Monday entry.
- [ ] Review Iran/Houthi headlines for overnight developments.
- [ ] Set alerts: SPY $677 (Trigger A), SPY $682 (danger), SPY $685 (cancel ladder).
- [ ] Confirm: has the constitution been amended to permit this 2-entry scale-in? If no, this is paper-trade only.

### Monday (April 7):
- [ ] 9:30 AM: Watch open. Do NOT trade in first 60 minutes (extended Monday blackout).
- [ ] 10:30-11:00 AM: Check triggers. Is SPY below $677 (Trigger A) or rejecting a pop at $678 (Trigger B)?
- [ ] If triggers met: place limit buy for 1x SPY Apr 14 $678P at $4.50. Walk $0.05 x 3 max.
- [ ] If filled: immediately set GTC stop-loss sell at $3.50.
- [ ] Set alert: SPY $685 close (cancel entire ladder).
- [ ] 3:45 PM: If SPY closed above $685, cancel everything.

### Tuesday (April 8):
- [ ] Monitor. No action.
- [ ] If Entry 1 is still above $4.50: thesis is alive. Prepare for Thursday.
- [ ] If Entry 1 is below $4.00: thesis is weakening. The stop at $3.50 is the backstop.
- [ ] Check Iran headlines for ceasefire violations.

### Wednesday (April 9):
- [ ] No action unless stop is hit.
- [ ] Review Entry 2 triggers. PCE releases 8:30 AM Thursday.
- [ ] Pre-commit: if PCE is hot AND Entry 1 is profitable, Entry 2 fires Thursday.

### Thursday (April 9, PCE):
- [ ] 8:30 AM: PCE prints. Note core MoM. Do NOT trade until 10:00 AM.
- [ ] 10:00 AM: Check ALL Entry 2 conditions:
  - [ ] Entry 1 still alive (not stopped)?
  - [ ] Entry 1 at breakeven or profitable ($678P value >= $4.50)?
  - [ ] Independent catalyst confirmed (PCE hot, OR SPY < $675, OR ceasefire violation)?
- [ ] If ALL conditions met: place limit buy for 1x SPY Apr 14 $675P at $2.20. Walk $0.05 x 3 max.
- [ ] If filled: immediately set GTC stop-loss sell at $1.20.
- [ ] If ANY condition not met: skip Entry 2. Entry 1 continues on its own.
- [ ] **CPI profit lock check:** if combined position showing 40%+ of max profit by 3:00 PM, close before Friday CPI.

### Friday (April 10, CPI):
- [ ] 8:30 AM: CPI prints. Do NOT trade until 10:00 AM.
- [ ] 10:00-10:30 AM: Re-evaluate. Is the position profitable? Has the thesis played out?
- [ ] If gap fill is complete or 50% profit achieved: close everything.
- [ ] If position is losing: stops are already set. Let them work.
- [ ] 3:00 PM: position check. If still holding over weekend, assess: is the risk worth 1 more trading day?

### Wednesday April 13 (Time Stop):
- [ ] 3:00 PM ET: **HARD CLOSE. Exit everything.** No exceptions. Do not hold 1 DTE puts over Thursday and into expiration.

---

## Adversarial Notes

1. **ATM puts are expensive.** Entry 1 at $678 (ATM) costs ~$4.50. The $100 stop loss requires a tight stop at $3.50 -- only $1.00 of room. Normal intraday noise at VIX 20 can produce $0.50-0.80 put swings. There is a real risk of being stopped out by noise, not by the thesis being wrong. **Mitigation:** the Monday blackout (10:30 AM entry) lets initial volatility settle. The $1.00 stop represents a ~22% decline in put value, which at delta -0.50 corresponds to SPY rallying ~$2. If SPY rallies from $678 to $680 and holds, the thesis IS weakened -- the stop is correct.

2. **IV crush on PCE could hurt Entry 1 before Entry 2 fires.** If PCE is a non-event and VIX drops from 20 to 18, the $678P loses ~$0.24 on vega alone (2 x $0.12). Combined with 3 days of theta (~$0.65/day x 3 = $1.95), Entry 1 could be at ~$2.30 by Thursday -- below the $3.50 stop. **This means Entry 1 may get stopped out by theta/vega before the thesis plays out.** This is the fundamental tension of the ladder: the probe needs to survive long enough for the confirmation to fire. The Apr 14 expiry (7 DTE) gives more room than Apr 11 (4 DTE) but does not eliminate the risk.

3. **Both puts expire on the same day.** If the thesis needs until Apr 15-16 to play out, both are dead. The conviction calibrator rated timing at 5/10. There is a 50% chance the timing is wrong for this expiry. **Mitigation:** the time stop on Wednesday Apr 13 prevents holding into worthless expiration. If the thesis is right but early, you take the loss and revisit with Apr 21 puts next week.

4. **$200 total risk is 40% of the single-position budget, not 100%.** This leaves room to add a third position (the non-bearish hedge) but also means the bearish bet is sized smaller than it could be. If the thesis is right and the gap fills, you make $2,400 on a position that could have been $500. The expected value is lower. **This is correct.** The timing uncertainty justifies the smaller size. The ladder structure compensates with better entry timing.

5. **Liquidity on Apr 14 SPY puts.** SPY Monday-expiry weeklies may have slightly wider spreads than the standard Friday weeklies. Check the bid-ask at entry. If spread is wider than $0.10, consider Apr 11 (Friday expiry, 4 DTE -- still constitutional) or Apr 17 (10 DTE, more liquid). Adjust stop proportionally.

---

## Summary for Borey

Two puts, one thesis, two different confirmation triggers. Entry 1 probes at the gamma flip ($678) on Monday -- if the gap fades, we are positioned. Entry 2 adds at max pain ($675) on Thursday -- only if the probe is working AND PCE or price action confirms. Total risk: $200 hard cap. If the probe fails, we lose $100 and walk away. If both fire and the gap fills, the payout is 12:1 on the risk.

This is the simplest expression of a scale-in: two single-leg puts at GEX-approved strikes, entered on different days with different triggers, managed to a combined budget of one position's worth. No spreads to manage. No short legs. Just two puts with hard stops and a kill switch.

The third portfolio slot is reserved for something non-bearish. This ladder is the Core Bearish (Category 1) component of a balanced portfolio per the correlation budget.
