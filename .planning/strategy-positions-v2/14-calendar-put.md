# 14 — Calendar Put Spread: Theta Differential on Slow Gap Fill

**Date drafted:** 2026-04-06
**Drafter role:** Calendar spread specialist, theta-harvesting bias
**Market snapshot:** SPX ~6783 (SPY ~678). Gap up from ~6610 on US-Iran ceasefire. VIX ~20. PCE Thu Apr 9, CPI Fri Apr 10. $10K account.

---

```
POSITION: SPY $670 Put Calendar — Sell Apr 11 / Buy May 2
Action: Sell 2x SPY Apr 11 $670P / Buy 2x SPY May 2 $670P
Entry: Monday Apr 7, 10:00-10:30 AM ET (after opening range settles)
Type: Put calendar spread (horizontal spread), same strike, different expirations
Cost/Credit: ~$2.40 net debit per calendar ($480 total for 2x)
Quantity: 2 calendars
Max loss: $480 (net debit paid — occurs if SPY rallies hard or crashes through strike)
Max profit: ~$350-550 per calendar ($700-1,100 total) if SPY pins near 670 at Apr 11 expiry
Breakeven zone: Approximately SPY $664-676 at near-term expiry (tent-shaped P&L)
Take profit: Close when spread value reaches $4.80-5.50 (~2x debit). Do not hold through Apr 11 afternoon.
Stop loss: Close both legs if spread value drops below $1.20 (50% of debit = $240 loss)
Time stop: If not profitable by Wednesday Apr 9, 2:00 PM ET (pre-PCE), close. The short leg has only 2 days left and gamma is now dominant over theta.
Bail trigger: If SPY drops below $666 at any point, close immediately. The fast-crash scenario is killing the calendar. Do not wait for recovery.
```

---

## Why a Calendar Put Spread for This Thesis

The gap fill thesis has a timing problem. Ceasefire collapse is likely but the *when* is unknowable. Could be Monday on a Houthi drone strike. Could be April 18 when the 2-week pause expires and Iran's 31 military branches resume independent operations. Could be May.

A calendar put spread is built for "right direction, uncertain timing." You sell near-term theta (fast decay) and buy far-term theta (slow decay). The differential is your edge. While SPY consolidates above the gap, the short Apr 11 put decays rapidly toward zero. The long May 2 put decays slowly. The widening gap between their values is your profit.

But this structure has a specific and dangerous failure mode that the ceasefire thesis directly threatens.

---

## The Position: Component Breakdown

### Short leg: 2x SPY Apr 11 $670P (SELL)

| Field | Value |
|---|---|
| Expiry | Friday Apr 11, 2026 |
| DTE at entry | 4 days |
| Estimated price | ~$3.20-3.60 |
| Delta | ~-0.28 |
| Theta | ~-$0.55/day (violent decay — this is what you are selling) |
| Gamma | ~0.06 (high — this is the danger) |
| Role | Income generator. Decays ~$0.55/day. If SPY stays above 670, this leg approaches $0 by Friday. You keep the premium. |

### Long leg: 2x SPY May 2 $670P (BUY)

| Field | Value |
|---|---|
| Expiry | Friday May 2, 2026 |
| DTE at entry | 25 days |
| Estimated price | ~$5.60-6.00 |
| Delta | ~-0.33 |
| Theta | ~-$0.12/day (slow, manageable decay) |
| Gamma | ~0.02 (low — stable) |
| Role | Anchor. Retains time value while the short leg evaporates. After Apr 11, you own a 21-DTE put with real optionality for the gap fill. |

### Net position:

| Field | Value |
|---|---|
| Net debit | ~$2.40 per calendar ($5.80 long - $3.40 short) |
| Total cost | ~$480 for 2 calendars |
| Net theta | +$0.43/day per calendar (+$0.86/day total). The spread GAINS ~$0.86/day in a flat market. |
| Net delta | ~-0.05 per calendar. Nearly delta-neutral at entry. Slight bearish lean. |
| Net vega | Positive. You are long far-term vega, short near-term vega. A slow vol rise helps. A vol explosion hurts (see below). |
| Net gamma | Negative. The short near-term leg has more gamma. Fast moves in either direction hurt you. |

---

## Strike Selection: Why $670 Again

The v1 calendar (position 07) established $670 and the reasoning has not changed:

1. **$670 is 1.2% OTM.** Both legs carry significant extrinsic value. A calendar spread exploits theta differential in extrinsic value — if both legs are deep OTM, there is almost no extrinsic to harvest.

2. **Not ATM ($678).** If the thesis is a drift lower, an ATM strike means max profit only if SPY goes nowhere. That contradicts the directional lean. Placing the strike below current price converts the calendar into a mildly bearish play.

3. **Not at the gap fill target ($661).** Both legs would be 2.5% OTM with ~$1.00 extrinsic each. The theta differential between a 4-DTE $1.00 put and a 25-DTE $1.50 put is negligible. You are paying $0.50 net for almost no theta edge.

4. **$670 is a round-number magnet.** High open interest attracts pinning behavior near expiry, which is ideal for a calendar — you want SPY near the strike when the short leg expires.

5. **$670 matches the other v2 positions.** The aggressive put (position 01) uses the same strike. If SPY moves toward 670, both positions work. Portfolio coherence.

---

## Expiry Selection: Why Apr 11 / May 2 (Not Apr 17 / May 2)

### Near-term: Apr 11 (4 DTE) — aggressive theta, aggressive gamma

The v1 calendar chose Apr 17 (11 DTE) for the short leg, explicitly warning that Apr 11's 5 DTE was "too short" because gamma is violent. That was conservative and correct for a first draft. Here is why Apr 11 is right for v2:

**The point of Apr 11 is to MAXIMIZE the theta differential.** At 4 DTE, the short $670P decays at ~$0.55/day. At 11 DTE (Apr 17), it decays at ~$0.30/day. The net theta with Apr 11 is +$0.43/day; with Apr 17 it is +$0.18/day. The Apr 11 version earns theta 2.4x faster.

**The tradeoff is gamma risk.** At 4 DTE, the short put has gamma of ~0.06 vs. ~0.03 at 11 DTE. A $1 move in SPY changes the short put's delta by $0.06 instead of $0.03. This makes the calendar's P&L more sensitive to intraday swings.

**Why accept this tradeoff now:** The ceasefire just happened. Monday-Wednesday (Apr 7-9) is the "digestion period" — the market processes the gap, institutions adjust, and SPY likely consolidates between 674-682 while the market decides if the ceasefire is real. This consolidation zone is a calendar's dream. Four days of $678 +/- $4 chop with the short leg decaying at $0.55/day prints money.

**PCE on Thursday Apr 10 is irrelevant to this leg.** The short leg expires Friday Apr 11. By Thursday, it has 1 DTE left. If SPY is anywhere above 672, the short put is worth pennies regardless of what PCE says. PCE would need to tank SPY below 670 in a single session for the short leg to matter — and if that happens, you have bigger problems (see bail trigger).

### Far-term: May 2 (25 DTE) — the anchor that survives timing errors

After the short leg expires (or is closed), you own a 21-DTE $670 put. This is the real position. If the gap fill takes until April 18 (ceasefire expiry) or April 25 (earnings chaos), you still own a put with substantial time value.

May 2 also sets up the roll plan: after Apr 11, you sell the Apr 17 put against your May 2, then Apr 25, then May 1. Each roll is a new short-term income cycle (see rolling plan below).

---

## How This Makes Money

### The Theta Math (Flat Market)

Assume SPY stays at $678 for all 4 days (best case for theta harvesting):

| Day | Short $670P (Apr 11) | Long $670P (May 2) | Spread Value | Daily P&L |
|---|---|---|---|---|
| **Mon entry** | $3.40 | $5.80 | $2.40 (debit) | -- |
| **Tue close** | $2.85 | $5.68 | $2.83 | +$0.43 |
| **Wed close** | $2.20 | $5.56 | $3.36 | +$0.53 |
| **Thu close (post-PCE)** | $1.40 | $5.44 | $4.04 | +$0.68 |
| **Fri AM (Apr 11)** | $0.50 | $5.33 | $4.83 | +$0.79 |

**Spread goes from $2.40 to ~$4.83 in 4 days.** That is +$2.43 per calendar, or +$486 on 2 contracts. A ~100% return on the $480 debit.

This is the maximum. Reality will be worse because SPY will not sit at $678 for 4 days. But the point stands: the theta math is powerful when the near-term leg is in terminal decay.

### Scenario A: SPY drifts to 672-675 by Apr 11 (ideal)

- Short $670P Apr 11: expires slightly OTM or ATM, worth $0-2.00 depending on exact pin
- Long $670P May 2: now ATM with 21 DTE, worth ~$6.50-7.50 (full extrinsic)
- Spread value: ~$5.00-7.50
- **P&L: +$2.60 to +$5.10 per calendar. Total: +$520 to +$1,020 on 2x.**
- After closing the short, you also own a put that is perfectly positioned for the gap fill. Roll into the next short leg (see rolling plan).

### Scenario B: SPY holds 676-680 (consolidation)

- Short $670P Apr 11: expires worthless
- Long $670P May 2: still OTM, worth ~$4.80-5.40 (lost ~$0.40-1.00 of time value)
- Spread value: ~$4.80-5.40
- **P&L: +$2.40 to +$3.00 per calendar. Total: +$480 to +$600 on 2x.**
- Then sell the next short leg (Apr 17 $670P) for additional income.

### Scenario C: SPY rallies to 685+ (thesis wrong)

- Short $670P Apr 11: expires worthless (good)
- Long $670P May 2: now deeper OTM, worth ~$3.50-4.20 (lost significant extrinsic)
- Spread value: ~$3.50-4.20
- **P&L: +$1.10 to +$1.80 per calendar. Total: +$220 to +$360 on 2x.**
- The calendar still profits on a rally because the short leg decayed faster than the long. But profit is modest. Consider closing the long leg rather than rolling — the bearish thesis is weakened.

### Scenario D: SPY drops to 665-668 quickly (DANGER)

- Both legs approach ATM or ITM. Extrinsic value in the short leg STOPS decaying because it now has intrinsic value to defend.
- Short $670P Apr 11: worth $3.00-5.00 (intrinsic growing)
- Long $670P May 2: worth $5.50-8.00 (intrinsic + time value)
- Spread value: ~$2.00-3.00 (COMPRESSED — possibly below your debit)
- **P&L: -$0.00 to -$0.80 per calendar. Small loss or breakeven.**
- This is manageable. The calendar has not blown up, but the theta thesis is broken. Close and reassess, or let the short expire and keep the long for the gap fill.

### Scenario E: SPY crashes below 660 (gap fills immediately)

**THIS IS THE KILLER.** This is why the bail trigger exists.

- Both legs go deep ITM. At $660, both are $10 ITM.
- Deep ITM options lose almost all extrinsic value. The time spread between 4-DTE and 25-DTE becomes irrelevant when both legs are priced at intrinsic.
- Short $670P Apr 11: worth ~$10.20 (almost pure intrinsic)
- Long $670P May 2: worth ~$11.00 (intrinsic + minimal time premium)
- Spread value: ~$0.80
- **P&L: -$1.60 per calendar. Total: -$320 on 2x. (67% of max loss.)**
- At SPY $655: spread value ~$0.40. P&L: -$2.00 per calendar. Total: -$400.
- At SPY $650: spread value ~$0.20. P&L: -$2.20 per calendar. Total: -$440. Approaching max loss.

**The calendar put spread LOSES when the underlying moves fast through the strike, even though the directional thesis is correct.** This is the fundamental tension with this structure given the ceasefire collapse risk. A violent move through 670 kills both legs' extrinsic value and collapses the spread.

---

## The Bail Trigger: When to Abandon Ship

This is the most important section in the document.

### Hard bail: SPY drops below $666 at any point

Close both legs immediately. Do not wait. Do not hope for a bounce.

**Reasoning:** At $666, both puts are $4 ITM. The short leg's gamma is now working against you aggressively — every additional dollar of downside shrinks the spread value because the short put is gaining intrinsic faster than the time premium differential can compensate. Below $666, the calendar is a guaranteed loser on a continued decline and only breaks even on a reversal back above $670. You do not want a position whose only profitable path is "hope the thesis is wrong."

**Expected loss at $666 bail:** Spread value ~$1.80-2.20. Loss: ~$0.20-0.60 per calendar. Total: $40-$120. This is a small, controlled loss. The bail trigger exists to prevent this from becoming a $400+ loss at $655.

### Soft bail: Spread value drops to $1.20 (50% of debit)

This catches scenarios the hard bail misses — a VIX spike that inflates the short leg, or a multi-day chop that erodes the time premium differential without a large directional move.

**Expected scenarios triggering soft bail:**
- VIX spikes to 28+ on geopolitical headline. Near-term vega inflates the short leg disproportionately. Spread compresses.
- SPY whipsaws between 672-682 for 3 days. Both legs experience realized vol, but the short leg's gamma exposure means it reprices more aggressively. Spread value oscillates and trends down.

### Time bail: Wednesday Apr 9, 2:00 PM ET

If the spread is not profitable by Wednesday afternoon, close before PCE. Rationale:

1. The short leg has 2 DTE. Theta is still working but gamma now dominates. A $3 move in SPY post-PCE could swing the spread value by $1.00+. You are no longer in a theta trade — you are in a gamma gamble.

2. PCE hits Thursday 8:30 AM. If it triggers a selloff, the crash scenario (E) activates and the calendar gets killed. If it triggers a rally, the short leg is helped but you already have only 1.5 days of theta left — diminishing returns.

3. The purpose of the time bail is to protect against holding a 1-DTE short leg through a macro catalyst. That is not what calendar spreads are for.

---

## The Rolling Plan: Converting One Calendar Into a Campaign

If the Apr 11 short leg expires worthless or near-worthless (scenarios A-C), you are left with a naked long May 2 $670P. At this point, the calendar becomes a rolling income engine:

### Roll 1: Sell Apr 17 $670P against the May 2 long

| Field | Value |
|---|---|
| When | Friday Apr 11 close OR Monday Apr 14 open |
| What | Sell 2x SPY Apr 17 $670P |
| DTE | 5-6 days |
| Expected credit | ~$2.20-3.00 (depending on where SPY is and VIX level) |
| Strike selection | Same $670 if SPY is between 672-684. Drop to $668 if SPY has drifted to 670-672. Raise to $672 if SPY has rallied to 684+. |
| Risk | Same as original calendar: fast crash through strike kills the spread |

**Cumulative position after Roll 1:**
- Original debit: $2.40/calendar
- Apr 11 short expired worthless: recovered ~$3.40 (the original short put's full value)
- New short credit: ~$2.20-3.00
- **Effective cost basis of May 2 long:** $5.80 - $3.40 - $2.60 = **-$0.20 (FREE or better)**

If you collected $6.00+ in total short put credits against a $5.80 long put, you own the long put at a negative cost basis. Every subsequent roll is pure income.

### Roll 2: Sell Apr 25 $670P against the May 2 long

| Field | Value |
|---|---|
| When | Friday Apr 17 close OR Monday Apr 21 open |
| What | Sell 2x SPY Apr 25 $670P (or adjusted strike) |
| DTE | 4-7 days |
| Expected credit | ~$1.80-2.80 |
| Strike selection | Maintain $670 if SPY is 672-684. Adjust down 2 points for every $3 SPY has fallen below 672. |

### Roll 3 (final): Sell May 1 $670P against the May 2 long

| Field | Value |
|---|---|
| When | Friday Apr 25 close OR Monday Apr 28 open |
| What | Sell 2x SPY May 1 $670P |
| DTE | 3-5 days |
| Expected credit | ~$1.50-2.50 |
| WARNING | Your long expires May 2, one day after this short. On May 1 close, close both legs. Do NOT hold the short through expiry uncovered. |

### Rolling Arithmetic (cumulative, 2 calendars)

| Leg | Credit/Debit | Running Total |
|---|---|---|
| Buy May 2 $670P | -$5.80 x 2 = -$1,160 | -$1,160 |
| Sell Apr 11 $670P | +$3.40 x 2 = +$680 | -$480 (net debit at entry) |
| Apr 11 short expires worthless | +$0 additional (credit already captured) | -$480 |
| Sell Apr 17 $670P (Roll 1) | +$2.60 x 2 = +$520 | +$40 |
| Apr 17 short expires worthless | +$0 | +$40 |
| Sell Apr 25 $670P (Roll 2) | +$2.30 x 2 = +$460 | +$500 |
| Apr 25 short expires worthless | +$0 | +$500 |
| Sell May 1 $670P (Roll 3) | +$2.00 x 2 = +$400 | +$900 |
| Close May 2 $670P (residual value) | +$4.50 x 2 = +$900 (if SPY ~672) | +$1,800 |

**Total income from rolling (if SPY cooperates):** ~$1,800 on $480 initial debit. That is a 275% return.

**Reality check:** SPY will NOT stay at $678 for 4 weeks. Some rolls will collect less. Some short legs may need to be closed at a loss. The gap fill may happen mid-roll and you will close everything for the directional gain instead. This arithmetic shows the ceiling, not the floor.

---

## When the Calendar Loses to the Ceasefire

This is the honest section.

The calendar put spread is the WRONG trade if:

1. **The ceasefire collapses Monday.** SPY gaps down $10+ on Monday morning. Both legs go ITM. Extrinsic collapses. Spread value goes to near-zero. You lose ~$480 while a straight long put would have made $1,000+. The calendar's "timing flexibility" is worthless when the timing is NOW.

2. **SPY crashes gradually but relentlessly.** If SPY drops $2/day for 5 days (678 to 668), the calendar bleeds as the short leg accumulates intrinsic value that offsets its theta decay. By Wednesday, the short put is $2 ITM and worth more than when you sold it. You are paying for the crash with your short leg.

3. **VIX explodes to 30+ in the first two days.** Near-term put vega spikes. The short leg gains value faster than it decays. Your positive theta is overwhelmed by short vega losses. The spread compresses even without a directional move.

**All three scenarios are plausible given the ceasefire thesis.** The calendar is not wrong — it is a bet on TIMING. It says: "the gap fill will take at least a week to start, and when it starts it will be gradual, not violent." If that is not your read, this is the wrong structure. Use the aggressive put (position 01) or the diagonal (position 14) instead.

---

## Position Sizing

| Field | Value |
|---|---|
| Account | $10,000 |
| Net debit | ~$480 (2 calendars at $2.40) |
| % of account at risk | 4.8% |
| Max loss | $480 (both legs expire with spread at zero — SPY at $650 or $700) |
| Practical max loss (with bail at $666) | ~$120-$240 |
| Expected daily P&L (flat market) | +$86/day (net theta on 2 calendars) |
| Target profit (single cycle, Apr 11 expiry) | +$500-$1,000 |
| Target profit (full rolling campaign to May 2) | +$800-$1,800 |

**2 calendars, not 3:** At $2.40 each, 3 calendars cost $720 (7.2% of account). The rolling campaign requires management bandwidth and each roll carries re-entry risk. 2 calendars at 4.8% keeps risk controlled and leaves capital for the other v2 positions.

---

## Entry Execution

1. **Monday Apr 7, 9:45 AM ET:** Check SPY pre-market.
   - If SPY is below $672: DO NOT ENTER. The strike is already being tested. The calendar thesis (decay while SPY consolidates ABOVE the strike) is compromised. Consider the aggressive put (position 01) instead.
   - If SPY is above $684: Consider entry but at reduced size (1 calendar). The strike is further OTM, extrinsic is lower, theta differential narrows.
   - If SPY is at $675-682: Ideal entry zone. Proceed.

2. **Monday Apr 7, 10:00-10:30 AM ET:** Place limit order.
   - Order: Sell 2x SPY Apr 11 $670P / Buy 2x SPY May 2 $670P as a calendar spread.
   - Limit: $2.30 net debit. Walk up to $2.40 at 10:15, $2.50 at 10:30.
   - Do NOT pay more than $2.60. Above that, the theta math does not compensate for the gamma risk.

3. **Immediately after fill:** Set alerts.
   - SPY $670 (approaching strike — monitor closely)
   - SPY $666 (BAIL — close immediately)
   - SPY $685 (rally — calendar is winning on theta but directional thesis weakening)
   - Spread value $1.20 (soft bail)
   - Spread value $4.80 (take profit)

---

## Post-Entry Daily Management

### Monday close (Day 1):
Spread should be $2.60-2.80. You are up ~$0.20-0.40 per calendar from theta. If the spread is below $2.20, something is wrong (SPY moved too fast or VIX spiked). Evaluate Tuesday open.

### Tuesday close (Day 2):
Spread should be $3.00-3.40. Net theta is accelerating as the short leg enters the steepest part of its decay curve. If profitable by $0.80+ per calendar, consider taking half off (sell 1 of 2 calendars).

### Wednesday close (Day 3 — pre-PCE decision point):
- **If spread is $3.60+:** You are up 50%+. Take profit on at least 1 calendar. Hold 1 into Thursday if you want PCE exposure, but know you are now gambling, not theta-trading.
- **If spread is $2.20-3.60:** Neutral. The time bail says close by 2 PM Wed. Follow it unless SPY is pinning at 674-678 and you are confident the last 1.5 days of theta will push you over.
- **If spread is below $2.00:** Close. The calendar is failing. Either SPY moved too much or VIX moved against you.

### Thursday (Day 4 — PCE day):
If you still hold a position, this is the last day. The short leg expires tomorrow with ~$0.30-0.50 of value left (if OTM). PCE at 8:30 AM will spike or crush vol. If SPY is near $670 at 10 AM post-PCE, you are at max profit zone — CLOSE. Do not hold the short leg through Friday's final hours. Gamma is uncontrollable.

### Friday Apr 11 (near-term expiry):
If you are still holding: close the short leg by 2:00 PM ET regardless. Let the long May 2 leg ride, and begin planning Roll 1 to Apr 17.

---

## Comparison to v1 Calendar (Position 07)

| Factor | v1 (Position 07) | v2 (This Position) |
|---|---|---|
| Short leg expiry | Apr 17 (11 DTE) | Apr 11 (4 DTE) |
| Long leg expiry | May 1 (25 DTE) | May 2 (25 DTE) |
| Net debit | ~$1.60 | ~$2.40 |
| Daily theta | +$0.36/day (2x) | +$0.86/day (2x) |
| Gamma risk | Moderate | High |
| Max profit horizon | 11 days to near-term expiry | 4 days to near-term expiry |
| Rolling plan | None (single cycle) | 3 additional rolls planned |
| Bail trigger | 50% debit loss only | $666 price level + 50% debit + time stop |
| PCE/CPI exposure | Holds through both | Short leg expires AFTER PCE, avoids CPI risk on short leg |
| Philosophy | Conservative theta, single cycle | Aggressive theta, rolling campaign |

**v2 is higher theta, higher gamma, shorter cycle, with explicit bail rules.** v1 was designed as a standalone trade. v2 is designed as the first cycle of a rolling campaign that can generate income for 4 weeks while waiting for the gap to fill.

---

## Execution Checklist

- [ ] Monday Apr 7, 9:45 AM: Check SPY pre-market. Abort if below $672.
- [ ] Monday Apr 7, 10:00-10:30 AM: Place limit order for 2x SPY $670P calendar (sell Apr 11 / buy May 2) at $2.30-$2.50.
- [ ] If not filled by 10:30, walk to $2.60 max. Abandon above $2.60.
- [ ] Set alert: SPY $666 (BAIL — close everything immediately).
- [ ] Set alert: SPY $670 (approaching strike — watch closely).
- [ ] Set alert: Spread value $1.20 (soft bail — 50% loss).
- [ ] Set alert: Spread value $4.80 (take profit zone).
- [ ] Wednesday Apr 9, 2:00 PM: Time stop decision. Close if not profitable.
- [ ] Thursday Apr 10, 10:00 AM: Post-PCE assessment. Close if at max profit zone (SPY near 670).
- [ ] Friday Apr 11, 2:00 PM: Close short leg by this time regardless. Do not hold through final hour.
- [ ] Friday Apr 11 close / Monday Apr 14 open: Evaluate Roll 1 — sell Apr 17 $670P against May 2 long.
- [ ] Repeat roll cycle weekly. Final roll: sell May 1 $670P. Close everything by May 1 close.
- [ ] Post-trade: Log entry/exit on each cycle. Track cumulative credits vs. debit. Compare rolling income to a simple long put.

---

## Position Summary

| Field | Value |
|---|---|
| Structure | Sell 2x SPY Apr 11 $670P / Buy 2x SPY May 2 $670P (put calendar) |
| Underlying | SPY (~678, SPX ~6783) |
| Short expiry | April 11, 2026 (4 DTE) |
| Long expiry | May 2, 2026 (25 DTE) |
| Net debit | ~$2.40/calendar (~$480 for 2x) |
| Net theta | +$0.43/calendar/day (+$0.86/day total) |
| Max loss | $480 (net debit) |
| Practical max loss (with bail) | ~$120-$240 |
| Max profit (single cycle) | ~$700-$1,100 (SPY pins $670 at Apr 11 expiry) |
| Target profit (rolling campaign) | ~$800-$1,800 (3-4 roll cycles to May 2) |
| Bail trigger | SPY $666 (immediate close) |
| Soft bail | Spread value $1.20 (50% loss) |
| Time bail | Wednesday Apr 9, 2:00 PM (pre-PCE) |
| Roll plan | Apr 11 -> Apr 17 -> Apr 25 -> May 1, selling weekly $670P against May 2 long |
| Key risk | Fast crash through $670 collapses both legs' extrinsic. Calendar LOSES when directional thesis is correct but violent. |
| R:R (single cycle) | ~1:1.5 to 1:2.3 |
| R:R (rolling campaign) | ~1:1.7 to 1:3.8 |
| Thesis | Gap fill is coming but slowly — theta differential profits from consolidation before the move |
| Conviction | Moderate. This structure bets on TIMING more than DIRECTION. If you believe the crash is imminent, use position 01 instead. |
