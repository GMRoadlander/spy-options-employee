# Scale-In Put Ladder v2 — SPX Gap Fill to ~6610

**Date drafted:** 2026-04-06
**Market context:** SPX ~6783 (SPY ~678). Gap from ~6610 on US-Iran ceasefire. VIX ~20. PCE Thu 4/9, CPI Fri 4/10. Ceasefire structurally unenforceable — Iran has 31 armed services, Supreme Leader reportedly in coma. Borey expects gap fill to SPY ~661. Timing uncertain (could be Thu through next Mon).
**Account:** $10,000
**Total risk budget:** 3% = $300 across ALL entries combined ($100 per entry)

---

## Rationale: Why Three Entries, Not One

The swarm identified **timing risk as the #1 killer** of directional trades. The gap fill thesis can be right on direction and wrong on timing by 48 hours and still lose money on 4 DTE puts. Theta at VIX 20 eats $0.80-1.00/day on an ATM weekly put.

Scale-in fixes this:
- **Entry 1 (Probe):** Cheap information. If the market fades Monday-Tuesday, you have a cost basis ahead of the crowd. If not, you lose $100 and preserve $200.
- **Entry 2 (Confirmation):** Fires only on macro catalyst (PCE) or technical breakdown. Adds at a lower strike where premium is cheaper and the move is confirmed.
- **Entry 3 (Conviction):** Fires only after two independent signals have confirmed. Cheapest entry, furthest OTM, highest leverage if gap completes.
- **If probe fails, cancel everything.** The entire ladder is designed so that a failed Entry 1 kills Entries 2 and 3. You never throw good money after bad.

Descending strikes (672 -> 668 -> 665) mean each successive entry is cheaper and further OTM — you are paying less per contract as the thesis requires more confirmation to justify adding.

---

## ENTRY 1 — PROBE ($100 max loss)

**POSITION: Buy 1x SPY Apr 11 672P**

- **Action:** Buy to open 1x SPY 672 Put, Apr 11 expiry (Friday weekly)
- **Strike logic:** 672 is ~0.9% OTM at SPY 678. Close enough to participate in early fade, far enough OTM to keep premium reasonable. Delta ~0.35.
- **Entry price estimate:** ~$3.50-4.00 (using $3.75 midpoint for planning)
- **Contracts:** 1
- **Total premium at risk:** $375

**When to enter:**
- Monday 2026-04-07, between 9:50-10:00 ET
- **Trigger A:** SPY opens flat or pops toward 679-680 on residual ceasefire euphoria (fade the pop — this is the ideal entry, buying into strength)
- **Trigger B:** SPY opens below 676 (gap already leaking — take the early signal before it accelerates)

**Skip Entry 1 if:**
- SPY gaps UP above 682 at open. The market is accepting the gap, not fading it. Do not probe against momentum.
- VIX drops below 16 pre-market. Market is too complacent for the thesis.

**Stop loss:** Exit if contract value drops to $2.75. Loss = $3.75 - $2.75 = $1.00 x 100 = **$100 loss (1% of account)**. This corresponds to SPY holding above 680 into Tuesday with theta compression — the thesis is failing.

**Profit target:** Do NOT take profit on Entry 1 alone. This is a probe. It becomes part of the full ladder. See Exit Plan below.

**Time stop:** If SPY is still above 677 at Tuesday 3:30 PM close, exit the probe for whatever it is worth. Do not hold a losing probe into the data events hoping for rescue. Likely value: $2.00-2.50, meaning $125-175 loss — but this is better than holding into zero.

---

## ENTRY 2 — CONFIRMATION ($100 max loss)

**POSITION: Buy 1x SPY Apr 11 668P**

- **Action:** Buy to open 1x SPY 668 Put, Apr 11 expiry
- **Strike logic:** 668 is ~1.5% OTM from 678, positioned at the midpoint of the gap (678 to 661). By the time Entry 2 fires, SPY should be around 673-674, making this strike only 0.6-0.9% OTM — reasonable premium for 1-2 DTE.
- **Entry price estimate:** ~$2.00-2.80 (using $2.40 midpoint). If SPY has moved to 674 when this triggers, the 668P reprices based on being closer to ATM but with less time value remaining.
- **Contracts:** 1
- **Total premium at risk:** $240

**When to enter:**
- Thursday 2026-04-09, after 10:00 ET (after PCE data settles)
- **Trigger A:** PCE comes in hot (core PCE MoM > 0.3%) AND SPY drops below 674 on the print. Hot inflation + falling price = thesis accelerating.
- **Trigger B:** PCE comes in cool/inline BUT SPY still breaks below 674 anyway. This is the stronger signal — the gap fill is structural, not just macro-driven. The market is selling even without a catalyst.

**Skip Entry 2 if:**
- PCE is cool AND SPY holds above 676. Dovish macro + resilient price = gap fill delayed or dead. Keep Entry 1 alive with its existing stop, but do not add.
- Entry 1 has already been stopped out. If the probe failed, the ladder is cancelled. Period.

**Stop loss:** Exit if contract value drops to $1.40. Loss = $2.40 - $1.40 = $1.00 x 100 = **$100 loss (1% of account)**.

**Why a lower strike:** Entry 2 shifts the ladder's center of gravity lower. You now own a 672P and a 668P. If the gap fill is partial (SPY hits 668 but not 661), the 672P is $4 ITM while the 668P is at the money — you capture profit from both across a wider band.

---

## ENTRY 3 — CONVICTION ($100 max loss)

**POSITION: Buy 1x SPY Apr 11 665P (Friday trigger) OR 1x SPY Apr 17 665P (Monday trigger)**

- **Action:** Buy to open 1x SPY 665 Put
- **Strike logic:** 665 is the "gap fill completion" strike. At SPY 661 (full gap fill), this put is $4 ITM. This is the highest-leverage, lowest-cost entry — it only makes sense if you have two confirming signals already.
- **Contracts:** 1

### Friday Trigger (preferred):
- **When:** Friday 2026-04-10, 8:45-9:15 ET (after CPI release settles)
- **Trigger A:** CPI comes in hot (core CPI MoM > 0.3%) AND SPY futures are below 670 pre-market. Double catalyst (hot inflation + already weak price).
- **Trigger B:** CPI inline but SPY has already closed below 670 on Thursday. Momentum is confirming without needing CPI as the catalyst.
- **Expiry:** Apr 11 (0 DTE). This is intrinsic-value-only territory.
- **Entry price estimate:** ~$1.50-2.50 if SPY is at 669-670 (665P is $4-5 ITM, but 0 DTE so nearly all intrinsic)
- **Using $2.00 midpoint for planning**
- **Stop loss:** Exit if value drops to $1.00. Loss = $2.00 - $1.00 = $1.00 x 100 = **$100 loss (1% of account)**

### Monday Trigger (alternative — if Friday does not fire):
- **When:** Monday 2026-04-13 open, if either:
  - ES futures gap down below SPX 6700 on Sunday night (ceasefire deterioration, Houthi activity, Iran statement)
  - SPY opens below 668 on Monday
- **Expiry:** Apr 17 (5 DTE — since Apr 11 has expired)
- **Entry price estimate:** ~$4.00-5.00 (more time premium on the weekly)
- **Stop loss:** Exit at $3.00. Loss = ~$1.00-2.00 x 100 = cap at **$100 loss**

**Skip Entry 3 if:**
- Entry 1 OR Entry 2 has been stopped out. Two fails = thesis is dead.
- SPY is above 673 on Friday morning. Not enough downside momentum to justify the final add.
- VIX has dropped below 17. Vol crush environment kills all three puts.

---

## Combined Position at Full Scale-In

| Entry | Strike | Expiry | Est. Cost | Max Loss | Trigger | Day |
|-------|--------|--------|-----------|----------|---------|-----|
| 1 (Probe) | 672P | Apr 11 | $375 | $100 | Monday open fade | Mon |
| 2 (Confirm) | 668P | Apr 11 | $240 | $100 | PCE hot or SPY < 674 | Thu |
| 3 (Convict) | 665P | Apr 11 | $200 | $100 | CPI hot or SPY < 670 | Fri |
| **Total** | — | — | **~$815** | **$300** | — | — |

- Total premium deployed: ~$815 (8.15% of account)
- Total max loss (sum of all stops): **$300 (3.0% of account)**
- Each stop is independent — no scenario requires all three to hit max loss simultaneously unless the market reverses violently after three confirming signals

---

## P&L Scenarios

### Scenario A: All 3 fire, gap fills to SPY 661 (BEST CASE)

| Entry | Strike | Cost | Value at 661 | P&L |
|-------|--------|------|--------------|-----|
| 1 | 672P | $3.75 | $11.00 (intrinsic) | +$7.25 (+193%) |
| 2 | 668P | $2.40 | $7.00 (intrinsic) | +$4.60 (+192%) |
| 3 | 665P | $2.00 | $4.00 (intrinsic) | +$2.00 (+100%) |
| **Total** | — | **$8.15** | **$22.00** | **+$13.85 per share = +$1,385 profit** |

- Return on capital deployed: **+170%**
- Return on account: **+13.85%**
- Risk taken: $300 max. Reward: $1,385. **R:R = 4.6:1**

### Scenario B: All 3 fire, partial gap fill to SPY 668 (gap stalls midway)

| Entry | Strike | Cost | Value at 668 | P&L |
|-------|--------|------|--------------|-----|
| 1 | 672P | $3.75 | ~$5.50 (ITM + small time value) | +$1.75 |
| 2 | 668P | $2.40 | ~$2.00 (ATM, mostly time) | -$0.40 |
| 3 | 665P | $2.00 | ~$0.80 (OTM) | -$1.20 |
| **Total** | — | **$8.15** | **~$8.30** | **+$0.15 per share = +$15 (breakeven)** |

- Entry 3 may not have fired at this level (SPY needs to be below 670 to trigger). If only Entries 1+2: cost $6.15, value $7.50 = **+$135 profit**.

### Scenario C: Only probe fires, fails (MOST LIKELY LOSS SCENARIO)

| Entry | Strike | Cost | Outcome | P&L |
|-------|--------|------|---------|-----|
| 1 | 672P | $3.75 | Stopped at $2.75 | -$1.00 = **-$100** |
| 2 | — | — | Skipped (probe failed) | $0 |
| 3 | — | — | Skipped (probe failed) | $0 |
| **Total** | — | **$3.75** | — | **-$100 loss (1% of account)** |

This is the key advantage of the ladder: a failed thesis costs $100, not $300.

### Scenario D: Probe works, PCE adds, but gap stalls and reverses (WORST REALISTIC CASE)

| Entry | Strike | Cost | Outcome | P&L |
|-------|--------|------|---------|-----|
| 1 | 672P | $3.75 | Stopped at $2.75 (reversal after PCE) | -$100 |
| 2 | 668P | $2.40 | Stopped at $1.40 | -$100 |
| 3 | — | — | Skipped (Entry 2 stop hit) | $0 |
| **Total** | — | **$6.15** | — | **-$200 loss (2% of account)** |

### Scenario E: All three fire, all three stopped (TRUE WORST CASE)

All three confirmations triggered, then a violent reversal (e.g., actual peace deal announced Friday afternoon).

| Entry | Strike | Cost | Outcome | P&L |
|-------|--------|------|---------|-----|
| 1 | 672P | $3.75 | Stopped at $2.75 | -$100 |
| 2 | 668P | $2.40 | Stopped at $1.40 | -$100 |
| 3 | 665P | $2.00 | Stopped at $1.00 | -$100 |
| **Total** | — | **$8.15** | — | **-$300 loss (3% of account)** |

This requires three independent confirmations to all fail after triggering — the market looked weak Monday, looked weak after PCE, looked weak after CPI, and then reversed hard. Possible but requires an extraordinary reversal.

---

## Exit Plan (All Entries Managed Together)

### Full gap fill — SPY 661 / SPX ~6610:
- Exit all open contracts at SPY 661
- Do not get greedy below the gap — SPY 661 is the target, not 655
- If SPY hits 663 and stalls, take it. Close enough. The last $2 of a gap fill is the hardest and least reliable.
- **Total proceeds: ~$2,200 on ~$815 deployed = +$1,385 profit**

### Partial gap fill — SPY 668 (halfway):
- Sell the 672P to lock profit (+$175)
- Hold the 668P with its existing stop at $1.40
- Entry 3 likely did not fire at this level
- Net position: profitable on Entry 1, near-breakeven on Entry 2

### Time stop — Thursday 3:00 PM ET:
- If SPY is still above 675 by Thursday 3:00 PM, sell everything remaining
- Theta decay on 1 DTE puts is brutal
- Do NOT hold through Friday expiration hoping for CPI unless the position is already profitable

### Friday 10:30 AM ET — hard close:
- Whatever is left, close it between 10:00-10:30 AM after CPI reaction settles
- Do not hold into the 3:00 PM gamma circus
- Do not hold through expiration for the last 30 cents of intrinsic

---

## Cancel Conditions (KILL THE LADDER)

**Cancel the entire ladder and exit all open positions if ANY of these occur:**

1. **SPY closes above 682 on Monday.** The gap is being accepted. Ceasefire euphoria is not fading. Exit Entry 1 at market (~$50-80 loss).

2. **VIX collapses below 16.** Market is fully pricing in peace and stability. Vol crush kills all put entries. Exit everything.

3. **Ceasefire upgraded to permanent deal.** If US-Iran negotiations produce a real resolution (not a pause), the geopolitical catalyst evaporates. Exit on the headline — do not wait for confirmation.

4. **SPY rallies above 685 at any point (new high).** A new high means the gap is a launchpad, not a ceiling. Cut immediately.

5. **Entry 1 stopped out -> Cancel Entries 2 and 3.** This is the core rule of the ladder. If the probe fails, the thesis is not working in the expected timeframe. Do not throw good money after bad. A failed probe saves you $200.

6. **Entry 2 stopped out -> Cancel Entry 3.** Two failed signals = thesis is dead. Even if CPI comes in hot on Friday, do not enter the third leg.

---

## Risk Accounting Summary

| Scenario | Entries Fired | Total Cost | Max Loss | % of Account | Outcome |
|----------|--------------|------------|----------|--------------|---------|
| Thesis fails immediately | 1 only | $375 | $100 | 1.0% | Small loss, $200 saved |
| Probe works, PCE dovish, market holds | 1 only | $375 | $100 | 1.0% | Entry 2 skipped wisely |
| PCE confirms, CPI is cool, bounce | 1 + 2 | $615 | $200 | 2.0% | Two signals, still wrong |
| All fire, gap stalls at 670 | 1 + 2 + 3 | $815 | $300 | 3.0% | Full loss, max budget |
| All fire, partial fill to 668 | 1 + 2 | $615 | $0 | +1.35% | Modest win |
| All fire, gap fills to 661 | 1 + 2 + 3 | $815 | $0 | **+13.85%** | Full thesis pays |

**Expected case:** 1-2 entries fire. The third is usually skipped because either the thesis plays out quickly (profit) or stalls (partial loss). The full $300 loss requires three independent confirmations to all fail — lowest probability outcome.

---

## Why This Structure Over Borey's Single Spread (Position 18)

| Dimension | Borey's Trade (18) | This Ladder (06-v2) |
|-----------|---------------------|---------------------|
| Structure | 3x 673/663 put spread | 3 individual puts at descending strikes |
| Total risk | $960 (realistic ~$400) | $300 hard cap |
| Entries | 1 (Monday morning) | Up to 3 (Mon/Thu/Fri) |
| Timing risk | HIGH — all-in before data | LOW — adds only on confirmation |
| If thesis is early by 1 day | Theta eats all 3 spreads | Theta eats probe only |
| If thesis is wrong | ~$400 loss (4% of account) | $100 loss (1% of account) |
| If thesis is right | +$2,040 (20.4% of account) | +$1,385 (13.85% of account) |
| R:R on realistic loss | ~5:1 | ~4.6:1 on full, ~13.9:1 on probe-only |

The ladder sacrifices $655 of upside profit to reduce worst-case loss by $660. For a $10K account where survival matters more than home runs, that is the right trade.

---

## Execution Checklist

### Sunday Night (April 6):
- [ ] Check ES futures. If gap UP above 6830, prepare to skip Monday entry.
- [ ] Review Iran/Houthi headlines for overnight developments.
- [ ] Set alerts: SPY 676 (trigger B), SPY 680 (danger), SPY 682 (cancel).

### Monday (April 7):
- [ ] 9:30 AM: Watch open. Do NOT trade in first 15 minutes.
- [ ] 9:50-10:00 AM: If triggers met, enter Entry 1 (672P). Limit at $3.75, walk to $4.00 max.
- [ ] Immediately set stop: sell 672P at $2.75 GTC.
- [ ] Set alert: SPY 682 close (cancel entire ladder).
- [ ] 3:45 PM: If SPY closed above 682, cancel everything.

### Tuesday (April 8):
- [ ] Monitor. If SPY breaks below 675, thesis is alive. No action needed.
- [ ] 3:30 PM: If SPY still above 677, consider early exit of probe (time stop).

### Wednesday (April 9, pre-PCE):
- [ ] No action. Position the mind for Thursday data.
- [ ] Review Entry 2 triggers. PCE releases 8:30 AM Thursday.

### Thursday (April 9, PCE):
- [ ] 8:30 AM: PCE prints. Watch core MoM.
- [ ] 10:00 AM+: If triggers met, enter Entry 2 (668P). Limit at $2.40, walk to $2.80 max.
- [ ] Set stop: sell 668P at $1.40 GTC.
- [ ] 3:00 PM: Time stop. If SPY above 675, close everything remaining.

### Friday (April 10, CPI + Expiration):
- [ ] 8:30 AM: CPI prints. Watch core MoM.
- [ ] 8:45-9:15 AM: If triggers met, enter Entry 3 (665P). Limit at $2.00, walk to $2.50 max.
- [ ] Set stop: sell 665P at $1.00 GTC.
- [ ] 10:00-10:30 AM: **HARD CLOSE. Exit everything.** No exceptions. Do not hold through expiration.

---

## Adversarial Notes

1. **All three fire and then a peace deal is announced.** Violent reversal, all stops hit. Max loss: $300 / 3%. This is sized for survivability.

2. **IV crush after cool CPI.** VIX drops from 20 to 16-17. All puts lose vol premium simultaneously. Stops protect, but you might get stopped on all three in quick succession. The descending strikes mean Entry 3 (most OTM) gets crushed hardest, but it is also the cheapest.

3. **Liquidity on 0 DTE SPY puts.** SPY weekly options are among the most liquid instruments on Earth. Bid-ask on 665P at 0 DTE should be $0.03-0.05 wide. Not a concern.

4. **Entry 2 and Entry 3 fire on the same day.** If PCE is Thursday morning and SPY crashes through 670, both triggers could theoretically fire Thursday. This is fine — enter both. The confirmation logic is met.

5. **Theta between entries.** Entry 1 loses ~$0.80/day while waiting for Entry 2 to trigger. Over 3 days (Mon-Thu), that is $2.40 of the $3.75 premium gone. The time stop on Tuesday protects against holding a fully decayed probe. If the probe is still alive Thursday, it has likely moved ITM.

6. **Position sizing module is dead code (per adversarial review #23).** Manual sizing only. Kelly criterion pipeline is not wired to execution.
