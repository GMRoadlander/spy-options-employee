# 01: Put Debit Spread -- Gamma Floor Break to Gamma Flip

**Date drafted:** 2026-04-09 (Thursday, 10:07 AM PT / 1:07 PM ET)
**Account:** $10,000
**Trader:** Gil
**Market:** SPY $679.58 spot, VIX elevated, Volume PCR 1.324 (EXTREME FEAR)
**Source:** Live CBOE data, April 9, 10:07 AM PT

---

## LIVE GEX LEVELS (CBOE, April 9)

| Level | Price | Change from Sunday | Significance |
|-------|-------|--------------------|-------------|
| **SPY Spot** | $679.58 | +$3.57 from $676.01 | -- |
| **Gamma Flip** | $658.66 (multi-expiry) | +$2.47 from $656.19 | 1.0 |
| **Gamma Ceiling** | $685.00 | +$5.00 from $680.00 | 0.9 |
| **Gamma Floor** | $670.00 | **+$20.00 from $650.00** | 0.85 |
| **Max Pain (today)** | $671.00 | +$15.00 from $656.00 | 0.8 |
| **Volume PCR** | 1.324 | -- | EXTREME FEAR |
| **Dealer Positioning** | LONG GAMMA at $679.58 | -- | Dampening moves |
| **Squeeze Probability** | 40% | -- | High |

### Critical Change: Gamma Floor Jumped $20 (from $650 to $670)

This is the single most important development. On Sunday, the gamma floor was $650 -- dealer buying support was far below spot. Today, dealer support has risen to $670, only $9.58 below spot. This means:

1. **The "easy" selloff is only $9.58** ($679.58 to $670), dampened by long-gamma dealer hedging the entire way.
2. **Below $670, support falls away.** The next structural level is the gamma flip at $658.66. This is the corridor the trade targets.
3. **Max pain at $671 and gamma floor at $670 form a tight support band.** If SPY breaks below both, the next stop is $658.66 -- a $12 air pocket.

### Key OI Levels

- **Call side:** $670, $671, $675, $680, $683, $684, $685
- **Put side:** $650, $655, $659, $660, $670

---

## THESIS

SPY is pinned at $679.58 by long-gamma dealer dampening. If a catalyst (CPI miss Friday, Islamabad talks Saturday, Iran ceasefire collapse) pushes SPY through the $670 gamma floor, dealer support evaporates. The next structural support is the gamma flip at $658.66, with max pain confluence at $671 providing a weak deceleration zone just above $670. Below $670, the market enters a $12 air pocket toward $658.66.

This trade captures that specific corridor: the break below dealer support ($670) toward the gamma flip ($658.66).

**Why not target above $670?** Because dealers are LONG GAMMA above $670. Any drop from $679.58 to $670 is dampened, orderly, and likely to bounce. The profitable move is the one that happens AFTER support breaks.

**Why is this trade viable despite extreme fear / expensive puts?** Because we are buying at $670 (the exact gamma floor where put OI is concentrated) and selling at $660 (a high OI put level). Both legs benefit from OI concentration, and the short leg collects inflated premium that partially offsets the expensive long leg.

---

## STRIKE SELECTION ANALYSIS

### Target Corridor: $670 (gamma floor) to $658.66 (gamma flip)

The ideal spread buys the gamma floor break and sells near the gamma flip. Constraints: must fit $200 max risk.

### Candidate A: Buy $670P / Sell $658P ($12 wide)

- Width: $12.00
- Estimated debit: ~$3.50-$4.50 (long leg $9.58 OTM at $670; short leg $21.58 OTM at $658)
- Cost per contract: $350-$450
- **REJECTED. Debit exceeds $200. Cannot buy 1 contract within risk budget.**

### Candidate B: Buy $670P / Sell $660P ($10 wide)

- Width: $10.00
- Long leg at $670: gamma floor, high OI put level (significance 0.85). Exactly $9.58 OTM.
- Short leg at $660: high OI put level from CBOE data. $19.58 OTM. Close to gamma flip zone.
- Estimated debit: ~$2.00-$2.80 (both OTM; long leg ~$3.00-$3.50 with elevated IV; short leg ~$1.00-$1.30 credit from extreme fear put skew)
- Cost per contract: $200-$280
- **VIABLE at the low end.** At $2.00 entry = exactly $200 max risk. Need IV crush post-PCE (already released this morning, market held) to compress toward $2.00.

### Candidate C: Buy $670P / Sell $662P ($8 wide)

- Width: $8.00
- Estimated debit: ~$1.70-$2.20
- Cost per contract: $170-$220
- **VIABLE.** Tighter, but short leg misses the $660 OI level. Less structural significance.

### Candidate D: Buy $668P / Sell $660P ($8 wide)

- Width: $8.00
- Long leg at $668: $11.58 OTM. No OI significance. Just cheap.
- **REJECTED. Long leg has no GEX significance. Buying into empty space.**

### THE TRADE: Buy $670P / Sell $660P ($10 wide)

This is the best risk/reward construction because:

1. **Long strike $670** = gamma floor (significance 0.85). The exact level where dealer support lives today. Buying here means the put gains value precisely when dealer support breaks.
2. **Short strike $660** = high OI put level. Close to gamma flip ($658.66) but $1.34 above it, staying within the dampened zone. Selling here collects elevated premium from extreme fear.
3. **$10 width** captures most of the $670-to-$658.66 air pocket ($11.34 corridor, captured $10 of it).
4. **Entry target $2.00** = exactly $200 max risk. Hard ceiling at $2.00 per the constitution.

| Combination | Width | Est. Debit | Fits $200? | GEX Logic |
|---|---|---|---|---|
| $670/$658 | $12 | ~$4.00 | NO | Perfect corridor but too expensive |
| **$670/$660** | **$10** | **~$2.00** | **YES (at target)** | Gamma floor to high OI put level |
| $670/$662 | $8 | ~$1.90 | YES | Misses OI level at $660 |
| $668/$660 | $8 | ~$1.50 | YES | Long leg has no significance |
| $670/$655 | $15 | ~$3.20 | NO | Too wide, exceeds budget |

---

## POSITION: Put Debit Spread

### COMPLIANCE

| Risk Constitution Rule | Status | Detail |
|---|---|---|
| Max risk per position $200 | PASS | Debit = $200 max. Hard ceiling: will not pay above $2.00. |
| Max total portfolio risk $500 | PASS | First position. $200 of $500 budget consumed (40%). |
| Max 3 positions | PASS | Position 1 of 3. |
| Max correlated same-direction: 2 | PASS | First bearish position (1 of 2 max). |
| Min cash reserve $9,000 | PASS | $10,000 - $200 = $9,800 cash remaining. |
| Max single position 50% of risk budget | PASS | $200 = 40% of $500 risk budget. Under $250 ceiling. |
| 2-leg max (vertical only) | PASS | Bear put spread. Two legs. |
| No naked short options | PASS | Short $660P covered by long $670P. |
| Min 4 DTE at entry | PASS | Apr 17 expiry. Entry today Apr 9 = 8 DTE. |
| No entries within 90 min of PCE/CPI | PASS | PCE released 8:30 AM ET. Currently 1:07 PM ET. Blackout long passed. |
| No entries before 10:00 AM ET | PASS | Entry window begins 1:15 PM ET (now). |
| Max entries per day: 2 | PASS | Single entry. |
| Commission check (round-trip < 3% max profit) | PASS | Round-trip ~$2.60. Max profit $800. $2.60/$800 = 0.33%. |
| Short leg ITM check (close if $2+ ITM) | NOTED | Short $660 goes ITM if SPY drops below $660. Monitor. |

### Trade Details

```
Action:      Buy 1x SPY Apr 17 $670P / Sell 1x SPY Apr 17 $660P
Type:        Bear put debit spread (vertical)
Expiry:      Apr 17, 2026 (8 DTE from today)
Entry:       TODAY -- Thursday Apr 9, 1:15-2:00 PM ET
Debit:       Target $1.80, walk to $2.00 max (hard ceiling)
Contracts:   1
Max loss:    $200 (debit paid, capped by refusing to pay above $2.00)
Max profit:  $800 (SPY at or below $660 at expiry: spread worth $10.00, minus $2.00 debit)
R:R:         4:1 (at $2.00 entry) to 4.6:1 (at $1.80 entry)
Breakeven:   SPY $668.00 at expiration (at $2.00 debit)
             SPY $668.20 at expiration (at $1.80 debit)
```

---

## ENTRY RULES

**Entry window: TODAY, Thursday April 9, 1:15-2:00 PM ET**

PCE already released this morning at 8:30 AM ET. Market held -- non-event confirmed. The 90-minute blackout expired at 10:00 AM ET. IV crush from the PCE non-event should already be compressing put premiums.

1. Place limit order at **$1.80** for 1x SPY Apr 17 $670/$660 put spread.
2. If not filled by 1:30 PM ET, walk to **$1.90**.
3. If not filled by 1:45 PM ET, walk to **$2.00** (hard ceiling).
4. If not filled at $2.00 by 2:00 PM ET, **walk away**. Reassess for Friday post-CPI entry.
5. **Do NOT pay more than $2.00. $2.01 = no trade.**

**Alternate entry: Friday April 10, 10:15-11:00 AM ET (post-CPI)**

CPI releases 8:30 AM ET Friday (tomorrow). Same blackout, same limit walk: $1.80 -> $1.90 -> $2.00 -> walk away.

- If CPI is hot (March catches oil spike tail): bearish thesis strengthened, but put IV may spike. Wait until 10:30+ for spike to fade. May need to target Friday afternoon entry.
- If CPI is cool: SPY bounces, puts get cheaper. Best possible entry. Enter at $1.60-$1.80 if available.
- If CPI is inline: status quo. Proceed with $1.80 target.

**Why enter today (Thursday) instead of waiting for CPI (Friday)?**
Because the gamma floor jumped to $670 TODAY. This level is fresh. The market has not had time to fully price the new dealer support structure. If SPY drifts toward $670 into the close or tomorrow, the $670P long leg gains value. Waiting for CPI means the market has another full session to reprice around $670.

However, if the spread is too expensive today (PCR 1.324 = puts still inflated), the Friday post-CPI entry is a valid backup. Do not force the entry.

---

## TAKE PROFIT

- **50% of max profit:** Close when spread is worth **$6.00** (at $2.00 entry: $400 profit on $800 max = 50%) or **$5.90** (at $1.80 entry).
- **This means SPY has dropped to approximately $664-$665** with time remaining. SPY would need to break the gamma floor ($670), fall through the air pocket, and reach $664-$665.
- **Execution:** Place a GTC limit sell at $6.00 immediately after fill.
- **Alternative 30% profit exit:** If more conservative, close at $4.60 (at $2.00 entry = $260 profit). This requires SPY to reach only ~$667, which is in the air pocket but above the gamma flip.

---

## STOP LOSS

- **Mechanical stop: the debit paid.** This is a debit spread. Max loss IS the debit ($200). No stop-loss order needed because the position cannot lose more than $200.
- **Mental time-based stop:** If by Wednesday Apr 15 close (2 trading days before expiry), the spread is worth less than $0.80, close it. Do not hold a near-worthless position into the final 48 hours.
- **Thesis invalidation stop:** If SPY closes above $685 (gamma ceiling), close within 30 minutes per Risk Constitution Section 7.
- **Gamma floor invalidation:** If the gamma floor moves UP from $670 to $675+ in tomorrow's GEX data, the thesis weakens. The air pocket shrinks. Consider closing for whatever value remains if the floor rises above $675.

---

## TIME STOP

- **Hard exit: Wednesday April 15, 3:00 PM ET.** This is 2 trading days before the Apr 17 (Friday) expiry, per Risk Constitution Section 4.
- **No exceptions.** Close at whatever the spread is worth at that time.
- **Rationale:** A $10-wide debit spread 2 days from expiry becomes a gamma bomb. Pin risk at $660 or $670 creates unpredictable P&L swings. Exit cleanly.

---

## P&L SCENARIOS

### Best case: SPY breaks $670 floor, fills to $660 or below by Apr 15

- Spread at full value: $10.00
- Cost: $2.00 (max entry)
- **Net profit: +$800 per contract**
- More likely: close at 50% target ($6.00) for **+$400**

### Good case: SPY drops to $664-$666 by Apr 14

- Spread worth ~$5.00-$6.00 (long leg near ATM, short leg still OTM)
- Hit 50% profit target
- **Net profit: +$300 to +$400**

### Moderate case: SPY breaks $670 but bounces at $667-$668

- Spread worth ~$3.00-$4.00
- Close for partial profit at time stop or earlier
- **Net profit: +$100 to +$200**

### Neutral case: SPY chops $672-$679 through Apr 14

- Spread worth ~$0.80-$1.40 at time stop
- Theta decay erodes position. Gamma floor at $670 holds.
- **Loss: -$60 to -$120**

### Bad case: SPY rallies to $682-$685

- Spread worth ~$0.30-$0.60 by Tuesday
- Close at time stop
- **Loss: -$140 to -$170**

### Worst case: SPY breaks above $685, thesis invalidation triggers

- Close immediately per constitution
- Spread worth ~$0.10-$0.30
- **Loss: -$170 to -$190**
- Absolute max loss: -$200 (spread expires worthless). Hard ceiling.

---

## GEX JUSTIFICATION

**Long strike at $670 (gamma floor):**
The CBOE live data shows $670 as today's gamma floor -- the level where dealer hedging buying is at maximum intensity on the put side. This level jumped $20 from $650 (Sunday) to $670 (today), meaning dealers have repositioned their support line dramatically higher. Buying the $670P means the long leg gains value precisely when SPY breaks through this support. Above $670, dealers dampen any selloff. Below $670, their support vanishes. The $670P is the "break the floor" trade.

**Short strike at $660 (high OI put level, near gamma flip):**
$660 is a high OI put level in the CBOE data, $1.34 above the gamma flip at $658.66. Selling here collects inflated premium (PCR 1.324 = extreme fear, puts overpriced) at a level with structural significance. If SPY reaches $660, it is within $1.34 of the gamma flip -- the point where dealer hedging flips from dampening to amplifying. Max pain ($671) and gamma flip ($658.66) bracket this short strike, providing a zone of gravitational support. The probability of SPY blowing through $660 and reaching $650 is lower because the gamma flip confluence at $658.66 would trigger massive dealer buying.

**Why this corridor specifically ($670 to $660)?**
The gamma floor at $670 is the "last line of defense" for the current range. Max pain at $671 sits right above it. Below $670, there is a $10 air pocket to the next structural level at $660. This is the gap that opens when dealer support breaks. The spread captures exactly this gap. It does not need SPY to crash -- it needs SPY to lose its floor.

---

## MANAGEMENT CALENDAR

| Day | Time (ET) | Action |
|-----|-----------|--------|
| **Thu Apr 9** | 1:15-2:00 PM | **PRIMARY ENTRY WINDOW.** Limit $1.80, walk to $2.00 max. |
| **Thu Apr 9** | 2:00 PM | If unfilled at $2.00, stop trying. Plan for Friday. |
| **Thu Apr 9** | 3:30 PM | If filled: note spread value. Set GTC sell at $6.00. Set alerts at $670, $665, $660, $685. |
| **Fri Apr 10** | 8:30 AM | CPI releases. Watch. Do not trade. |
| **Fri Apr 10** | 10:15-11:00 AM | **ALTERNATE ENTRY** if Thursday unfilled. Same limits. |
| **Fri Apr 10** | 1:00 PM, 3:30 PM | Check-ins. Weekend risk: Islamabad talks Saturday Apr 11. |
| **Mon Apr 13** | 10:00 AM, 1:00 PM, 3:30 PM | Three check-ins. Weekend catalyst reaction (Islamabad talks). |
| **Tue Apr 14** | 10:00 AM, 1:00 PM | Check-ins. |
| **Wed Apr 15** | 10:00 AM | Pre-close assessment. Prepare to exit. |
| **Wed Apr 15** | 3:00 PM | **HARD TIME STOP. Close the position. No exceptions.** |

### Intraday Rules (Every Trading Day)

- Check positions at 10:00 AM, 1:00 PM, 3:30 PM ET only. Three times. No more.
- If SPY closes above $685 (gamma ceiling): close within 30 minutes.
- If SPY trades above $690 intraday: close immediately at market.
- If VIX closes below 16: close within 60 minutes.
- If profit target hit ($6.00 spread value): close immediately.
- If spread value drops below $0.80 with 2+ days to expiry: evaluate early exit to preserve capital.

---

## CATALYST AWARENESS

| Catalyst | Date/Time | Impact on This Trade |
|----------|-----------|---------------------|
| **PCE (already released)** | Today 8:30 AM ET | Non-event. Market held. IV crush in progress. |
| **CPI (March data)** | Fri Apr 10, 8:30 AM ET | Hot CPI = bearish (good for trade), but may spike put IV temporarily. Cool CPI = bullish (bad for trade), SPY bounces away from $670. |
| **Islamabad talks** | Sat Apr 11 | Ceasefire progress = bullish (bad). Collapse = bearish risk-off (good). |
| **Iran ceasefire structure** | Ongoing | "Structurally unenforceable" per context. Any credible enforcement = bullish (bad). |
| **Gamma floor drift** | Daily GEX recalc | If $670 floor moves to $675+, thesis weakens. If it drops to $665, thesis strengthens (air pocket widens). |

---

## EDGE ASSESSMENT: WHY THE 4:1 R:R IS REAL

1. **Entry is post-PCE IV crush.** The spread costs less today than it would have Monday-Wednesday morning. Puts are still expensive (PCR 1.324) but the PCE non-event has begun deflating event premium.

2. **$670 is a FRESH gamma floor.** It jumped $20 today. The market has not fully priced the implications. If $670 breaks, participants positioned for $650 support will be caught offside.

3. **The air pocket is structural, not speculative.** Between $670 (gamma floor) and $658.66 (gamma flip), there is minimal OI concentration in the CBOE data ($659, $660 have some, but $661-$669 is thin). This is a real gap in dealer positioning.

4. **CPI is the catalyst.** A hot March CPI print (which catches the tail of the oil spike) could be the push that breaks $670. The trade is positioned for the post-CPI reaction.

5. **40% squeeze probability caps upside.** The squeeze risk means a rally to $685+ is not unlikely, but the max loss is $200 regardless. The 40% squeeze is already priced into the elevated PCR and the $200 risk budget.

---

## PRE-ENTRY CHECKLIST (Before Placing Order)

- [ ] SPY price check: Is SPY still between $675-$685? If below $672, the $670P is near ATM and will cost more -- recheck debit.
- [ ] Spread pricing: Pull real bid/ask on SPY Apr 17 $670P and $660P. Calculate net debit. Is it at or below $2.00?
- [ ] VIX check: Is VIX above 16? (If below 16, constitution says close all positions -- do not enter.)
- [ ] Gamma floor confirmation: Has intraday GEX data confirmed $670 still holds as gamma floor? (Check CBOE or platform if available.)
- [ ] No breaking headlines: Islamabad early developments? Iran escalation? Major headline that changes thesis?
- [ ] Emotional check: Am I entering because the analysis supports it, or because I want to "be in a trade"? If the latter, walk away.
- [ ] Place limit order: 1x SPY Apr 17 $670/$660 put spread at $1.80. GTC.
- [ ] If filled: immediately place GTC sell at $6.00. Set price alerts at SPY $670, $665, $660, $685.
- [ ] If not filled by 2:00 PM ET at $2.00: walk away. Reassess Friday.
