# Scale-In Put Ladder — SPX Gap Fill to ~6610

**Date drafted:** 2026-04-06
**Market context:** SPX ~6783 after gap up from ~6610 on US-Iran ceasefire news. VIX ~20. PCE Thursday 4/9, CPI Friday 4/10. SPY ~678. Ceasefire is a 2-week pause, not a resolution. Gap fills to ~6610 (SPY ~661) expected within the week.
**Account:** $10,000
**Total risk budget:** 3% = $300 across ALL entries combined

---

## Why Scale-In (Not All-In)

The adversarial swarm identified **timing risk as the #1 problem** with directional trades. The 01-aggressive-puts plan deploys full risk on Monday morning — if the fade starts Tuesday instead of Monday, theta eats 20-25% of premium overnight for nothing. A gap fill thesis can be right on direction and wrong on timing by 48 hours and still lose money on 4 DTE puts.

Scaling in solves this:
- Entry 1 is a probe — small enough that being early costs little
- Entry 2 confirms with macro data (PCE) — adds only if the catalyst fires
- Entry 3 confirms with price action — adds only if the market is actually breaking down
- If the thesis is wrong, you lose $100 (1%), not $300 (3%)
- If the thesis is right but slow, you are not bleeding full theta while waiting

---

## Entry 1 — PROBE (1% risk = $100 max loss)

**When:** Monday 2026-04-07, between 9:50-10:00 ET, IF either condition is met:
- SPY opens flat or rallies toward 679-680 on residual ceasefire euphoria (fade the pop), OR
- SPY opens below 676 (gap already leaking — take the early signal)

**Skip Entry 1 if:** SPY gaps UP above 682 at open. That means the market is accepting the gap. Do not probe against momentum.

**What:** Buy 1x SPY Apr 11 672P (slightly OTM weekly put)
- Strike 672 is ~0.9% OTM at SPY 678, giving a bit more cushion against theta than ATM
- Apr 11 expiry (4 DTE) — enough runway for the thesis but decays fast if wrong

**Entry price estimate:** ~$3.50-4.00 per contract (672P at SPY ~678, VIX 20, 4 DTE)
- Using $3.75 midpoint for planning

**Size:** 1 contract = $375 total premium at risk

**Stop loss:** Exit if contract drops to $2.75, locking in $100 loss (1% of account). This corresponds roughly to SPY holding above 680 by Tuesday close with theta compression.

**Profit target:** Do NOT take profit on Entry 1 alone. This is a probe — it becomes part of the full ladder. See "Exit Plan" below.

**Edge at Entry 1:** You are buying cheap information. If the market fades Monday-Tuesday, you have a cost basis 24-48 hours ahead of the crowd. If it does not fade, you lose $100 and have saved $200 of risk budget for better setups.

---

## Entry 2 — ADD (1% risk = $100 max loss)

**When:** Thursday 2026-04-09, after 10:00 ET, IF either condition is met:
- PCE comes in hot (core PCE MoM > 0.3%) AND SPY drops below 674 on the print, OR
- PCE comes in cool/inline BUT SPY still breaks below 674 anyway (sell-the-news on a non-event — the gap fill is structural, not just macro-driven)

**Skip Entry 2 if:** PCE is cool AND SPY holds above 676. A dovish macro print + resilient price action means the gap fill is delayed or dead. Keep Entry 1 alive with its existing stop but do NOT add.

**What:** Buy 1x SPY Apr 11 668P (lower strike — cheaper premium, bigger move required, but higher reward if gap fill completes)
- Strike 668 is ~1.5% OTM from SPY 678, positioned at the midpoint of the gap (678 to 661)
- Same Apr 11 expiry — all entries expire together for clean management

**Entry price estimate:** ~$2.00-2.80 per contract (668P will be cheaper than the 672P because further OTM, and 2 DTE remaining means less time premium)
- Using $2.40 midpoint. After a move to 674, this reprices to ~$3.50-4.00 and you still get filled around $2.40 if IV doesn't spike much.
- If SPY is at 674, a 668P with 1 DTE (Thursday to Friday) prices ~$2.00-2.50

**Size:** 1 contract = ~$240 premium at risk

**Stop loss:** Exit if contract drops to $1.40, locking in $100 loss (1% of account).

**Why a lower strike:** Entry 2 shifts the ladder's center of gravity lower. You now own a 672P and a 668P — a synthetic put ladder that profits across a wider band (672-661). If the gap fill is partial (say SPY hits 668 but not 661), the 672P is deep ITM while the 668P is at the money — you capture profit from both.

---

## Entry 3 — FULL (1% risk = $100 max loss)

**When:** Friday 2026-04-10, 8:45-9:00 ET (pre-market or just after CPI release), IF either condition is met:
- CPI comes in hot (core CPI MoM > 0.3%) AND SPY futures are below 670 pre-market, OR
- CPI is inline but SPY has already broken below 670 by Thursday's close (momentum confirming the thesis without needing CPI to be the catalyst)

**Alternative trigger (Sunday/Monday):** If CPI does not fire the trade on Friday, Entry 3 can still trigger:
- Sunday 2026-04-12 night: ES futures gap down below 6700 (SPX equivalent) on weekend geopolitical news (ceasefire deterioration, Houthi activity, Iran statement)
- Monday 2026-04-13 open: SPY opens below 668

If using the Monday trigger, the instrument changes (see below) because Apr 11 will have expired.

**What (Friday trigger):** Buy 1x SPY Apr 11 665P (deepest OTM — this is the "gap fill completion" bet)
- Strike 665 is ~2% OTM from 678, targeting the final leg to SPY 661
- 0 DTE if bought Friday — this is intrinsic-value-only territory
- Entry price estimate: ~$1.50-2.50 if SPY is at 669-670 at the time (665P is $4-5 ITM at 669 but 0 DTE so nearly intrinsic)

**What (Monday trigger — if Friday does not fire):** Buy 1x SPY Apr 17 665P
- Roll to next week's expiry since Apr 11 has expired
- Entry price estimate: ~$4.00-5.00 (5 DTE, slightly OTM from wherever SPY opens Monday)
- Adjust stop to exit at $3.00 (still $100 max loss on 1 contract)

**Size:** 1 contract = ~$200-250 premium at risk

**Stop loss:** Exit if contract drops to breakeven minus $1.00, capping loss at $100. Exact level depends on fill price.

**Why the lowest strike:** Entry 3 is the "full gap fill" conviction bet. By this point, you have seen PCE data, CPI data, and 4 days of price action. If all three entries fire, your ladder is:
- 672P (Entry 1) — deep ITM if gap fills, captures the first $11 of downside from 678
- 668P (Entry 2) — ITM at gap fill, captures the middle band
- 665P (Entry 3) — ITM only if gap fill reaches ~665 or lower, the high-conviction tail

---

## Combined Position at Full Scale-In

| Entry | Strike | Est. Cost | Max Loss | Trigger |
|-------|--------|-----------|----------|---------|
| 1 (Probe) | 672P Apr 11 | $375 | $100 | Monday open fade |
| 2 (Add) | 668P Apr 11 | $240 | $100 | PCE hot or SPY < 674 |
| 3 (Full) | 665P Apr 11 | $200 | $100 | CPI hot or SPY < 670 |
| **Total** | — | **~$815** | **$300** | — |

Total premium deployed: ~$815 (8.15% of account)
Total max loss (sum of all stops): $300 (3.0% of account)
This is aggressive on premium-to-stop ratio but acceptable because each stop is independent and the thesis has confirmation at every step.

---

## Exit Plan (All Entries Managed Together)

**Full gap fill target (SPY 661 / SPX ~6610):**
- 672P intrinsic value at 661: $11.00 (from ~$3.75 entry = +$7.25 = +193%)
- 668P intrinsic value at 661: $7.00 (from ~$2.40 entry = +$4.60 = +192%)
- 665P intrinsic value at 661: $4.00 (from ~$2.00 entry = +$2.00 = +100%)
- Total proceeds: ~$2,200 on ~$815 deployed = **+$1,385 profit (+170%)**
- Exit all three contracts at SPY 661. Do not get greedy below the gap.

**Partial gap fill target (SPY 668 — halfway):**
- 672P at 668: ~$5.50 (from $3.75 = +$1.75)
- 668P at 668: ~$2.00 (at the money, mostly time value — roughly breakeven)
- 665P at 668: ~$0.80 (OTM, losing — but Entry 3 may not have fired at this level)
- At SPY 668 with only Entries 1 and 2 active: +$175 on 672P, flat on 668P = modest winner
- Decision: Sell the 672P to lock profit, let 668P ride with stop at $1.40

**Time stop — Thursday 3:00 PM ET (if gap fill has not started):**
- If SPY is still above 675 by Thursday 3:00 PM, sell everything remaining. Theta decay on 1 DTE puts is brutal. Do not hold through Friday expiration hoping for CPI unless the position is already profitable.

---

## Cancel Conditions (STOP Scaling In)

**Cancel the entire ladder and exit all positions if ANY of these occur:**

1. **SPY closes above 682 on Monday.** The gap is being accepted. The ceasefire euphoria is not fading. The thesis is dead. Exit Entry 1 at whatever it is worth (likely $50-80 loss).

2. **VIX collapses below 16.** The market is fully pricing in peace and stability. Put premium will bleed with no catalyst. Vol crush kills all three entries.

3. **Ceasefire upgraded to permanent deal.** If the US-Iran negotiations produce a real resolution (not a pause), the geopolitical catalyst evaporates. This would be headline-driven and immediate — exit on the headline.

4. **SPY rallies above 685 at any point (new high).** The gap fill thesis requires the market to fade, not extend. A new high means the gap is a launchpad, not a ceiling. Cut everything immediately.

5. **After Entry 1 stop hits, do NOT enter 2 or 3.** If the probe fails (672P stopped at $2.75), the thesis is not working in the expected timeframe. Do not throw good money after bad. The whole point of scaling in is that a failed probe saves you from the larger entries.

---

## Risk Accounting

| Scenario | Entries Fired | Max Loss | % of Account |
|----------|--------------|----------|--------------|
| Thesis fails immediately | 1 only | $100 | 1.0% |
| Probe works, PCE is dovish, market holds | 1 only (2 skipped) | $100 | 1.0% |
| PCE fires Entry 2, but CPI is cool and market bounces | 1 + 2 | $200 | 2.0% |
| Full ladder, all three fire, but gap fill stalls at 670 | 1 + 2 + 3 | $300 | 3.0% |
| Full ladder, gap fills to 661 | 1 + 2 + 3 | $0 (profit) | +13.8% |

The **expected case** is that 1-2 entries fire and the third is skipped because either the thesis plays out quickly (profit) or stalls (partial loss). Losing the full $300 requires three independent confirmations to all fail after triggering — the market would need to look weak on Monday, look weak after PCE, look weak after CPI, and then reverse hard. Possible but unlikely given three confirming data points.

---

## Comparison to 01-Aggressive-Puts Plan

| Dimension | 01-Aggressive (Single Entry) | 09-Scale-In Ladder |
|-----------|------------------------------|---------------------|
| Entries | 1 (Monday morning) | Up to 3 (Mon/Thu/Fri) |
| Total risk | $200 (2%) | $300 (3%) — but $100 incremental |
| Timing risk | HIGH — all-in before data | LOW — adds only on confirmation |
| Premium efficiency | 1 contract at $4.80 | 3 contracts at $3.75/$2.40/$2.00 |
| Strikes covered | 670P only | 672P / 668P / 665P (wider band) |
| If thesis is early by 1 day | Theta eats $0.80-1.00 on full position | Theta eats $0.80 on probe only |
| If thesis is wrong | Lose $200 | Lose $100 (probe only, never add) |
| If thesis is right | +$720 (150% on 1 contract) | +$1,385 (170% on 3 contracts) |

The scale-in ladder risks 50% more in total ($300 vs $200) but has a much better risk-adjusted profile because most of the risk is conditional on confirmation.

---

## Adversarial Notes (What Could Go Wrong)

1. **All three entries fire and then the market reverses hard on Monday.** You are now long 3 puts at different strikes, all expiring worthless if SPY rips back above 675. Max loss is $300 / 3%. This is the worst case and it is sized for.

2. **IV crush after CPI.** If CPI comes in cool, VIX could drop from 20 to 16-17. All three puts lose vol premium simultaneously. The stops protect against this but you might get stopped on all three in quick succession.

3. **Liquidity on 0 DTE SPY puts.** SPY weekly options are highly liquid — this is not a real concern. Bid-ask on 665P at 0 DTE should be $0.03-0.05 wide.

4. **Position sizing module is dead code (per adversarial review #23).** This plan uses manual sizing. The system's Kelly criterion pipeline would not have caught oversizing here because it is not wired into any execution path. Manual discipline is the only guardrail.

5. **Combo odds engine overstates P(profit) for credit spreads (per adversarial review #04).** This plan uses long puts, not credit spreads, so the VRP asymmetry bias does not apply directly. However, any probability estimates from the engine should be treated as directionally indicative, not precise.
