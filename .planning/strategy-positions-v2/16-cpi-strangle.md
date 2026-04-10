# 16 — CPI Event Strangle (Long Strangle)

**Date drafted:** 2026-04-06
**Drafter role:** Event trader, agnostic on direction, pricing a move larger than implied
**Market snapshot:** SPX ~6783 (SPY ~678). VIX ~20. CPI (March data) releases Friday April 10, 8:30 AM ET. PCE (February data) releases Thursday April 9, 8:30 AM ET.

---

```
POSITION: SPY Apr 16 $682C / $674P — CPI Event Strangle
Action: Buy to open 1x SPY $682 Call, Apr 16 expiry
        Buy to open 1x SPY $674 Put, Apr 16 expiry
Entry: Thursday April 9, 2:00-3:00 PM ET (post-PCE afternoon, IV crushed)
Cost/Credit: ~$5.80 total debit ($2.80 call + $3.00 put, estimated)
Quantity: 1x each leg (2 contracts total)
Max loss: $200 (managed — see stop loss rules below; raw max loss is $580)
Max profit: Uncapped on upside; ~$1,400+ on downside gap fill to SPX 6610
Breakeven: SPY below ~$668.20 or above ~$687.80 by expiry
Take profit: Sell full strangle at $12.00+ total value ($1,200+ proceeds) on any CPI move
Stop loss: Exit both legs if combined value drops to $3.80 ($200 loss = 2% of $10K)
Time stop: Exit by Wednesday April 15 at 3:00 PM ET regardless of P&L
Invalidation: VIX drops below 16 before entry (market pricing no event risk, strangle will bleed). Also invalid if SPY moves more than $10 from $678 before entry (the event already happened without you).
Why THIS trade: CPI catches the tail of the Hormuz oil spike in the March data — PCE on Thursday is February data and will not. A hot CPI print is the higher-probability surprise, but a cool print could ignite a relief rally. The strangle does not need to guess direction; it needs a move larger than $10 in either direction. With ceasefire fragility adding a second catalyst over the weekend, the Apr 16 expiry captures both the CPI reaction AND any weekend ceasefire deterioration news for Monday's open.
```

---

## Why CPI Friday Over PCE Thursday

This is the core thesis. They are not interchangeable events.

**PCE (Thursday April 9) — February data:**
- Measured period: February 2026.
- The Hormuz oil spike began in the final days of March. February PCE data does not capture it.
- The market already knows this. PCE is priced as a "stale" print.
- Expected outcome: benign, consistent with recent trend. Unlikely to move markets more than $3-4.
- Our use for PCE: **IV crush after release.** This is when we enter.

**CPI (Friday April 10) — March data:**
- Measured period: March 2026.
- March CPI DOES capture the beginning of the Hormuz oil spike. Energy prices spiked. Transport costs rose. Food supply chains were disrupted.
- The market has not priced the full magnitude because the spike was late-month and the pass-through to consumer prices is debated.
- Hot surprise probability: **elevated.** Oil going from ~$80 to $112 in the back half of March flows into gasoline, airfare, shipping, food. Even if core CPI strips energy directly, the second-order effects (transport, logistics) bleed into core services.
- Cool surprise probability: **lower but real.** If the ceasefire calmed markets enough that March shelter costs decelerated (unlikely given the timing, but the BLS seasonal adjustments are unpredictable).

**The asymmetry:** CPI has a fatter tail than PCE this month. The strangle profits from fat tails.

## Expiry Selection: Why Apr 16 (Not 0DTE Friday, Not Apr 17)

This was the key decision. Three options were on the table:

### 0DTE Friday (April 10 expiry) — REJECTED

The cheapest option. A 0DTE strangle at $682C/$674P would cost roughly $2.50-3.50 total depending on Friday morning IV. Tempting for raw leverage.

**Why it loses:**

1. **Theta is your enemy on 0DTE.** At 8:30 AM the CPI drops. If the market moves immediately and violently, 0DTE works beautifully. But CPI reactions frequently take 30-90 minutes to develop their full range as algorithmic trading, institutional rebalancing, and the bond market feed back into equities. A 0DTE strangle that is +$2.00 at 9:00 AM can be +$0.50 by 10:30 AM if the move stalls and theta devours the remaining 6 hours of extrinsic value.

2. **You lose the weekend catalyst.** The ceasefire is the second leg of this trade. If CPI is hot on Friday but the move is only $5 (not enough to clear the strangle breakevens), and then Saturday morning a Houthi commander fires on a tanker, Monday opens with a $15 gap down. The 0DTE expired worthless Friday afternoon. You captured nothing.

3. **No risk management flexibility.** With 0DTE, there is no "move stop to breakeven" — the position lives or dies in one session. If CPI is a non-event (flat), you lose 100% of premium by 4:00 PM. With Apr 16, you lose ~15% of premium on a flat CPI day and still have 6 days for the ceasefire catalyst.

4. **Liquidity and spreads are worst at open.** 0DTE SPY options at 8:30 AM on a data release have the widest bid-ask spreads of any session. You pay an extra $0.10-0.20 per leg on the fill, which is 5-8% of your total position cost on a cheap strangle.

### Apr 17 (Wednesday expiry) — ACCEPTABLE BUT SUBOPTIMAL

Apr 17 weeklies would work. One extra day of theta cushion. But Apr 16 is the standard monthly expiry cycle, meaning:

- **Higher open interest and tighter spreads.** Monthly expiry options carry more institutional flow than weeklies. The $682C and $674P on the Apr 16 cycle will have 2-5x the open interest of the Apr 17 weeklies, resulting in $0.02-0.05 tighter bid-ask per leg.
- **Apr 16 gives 6 DTE at entry (Thursday PM) and survives through Monday.** That is enough. You do not need Apr 17's extra day.

### Apr 16 (Monthly expiry) — SELECTED

- 6 DTE at entry: Theta is ~$0.20/day per leg (~$0.40/day total), not the $0.80+/day of 0DTE.
- Survives CPI Friday AND the weekend. If ceasefire news breaks Saturday, Monday's open is captured.
- Monthly cycle = better liquidity = better fills.
- 6 days is enough runway for the thesis without paying for time you do not need (Apr 22+ would cost more for no added catalyst).

## Strike Selection: Why $682/$674 (4-Point Wings From ATM)

SPY at $678. The strangle wings are placed ~$4 out on each side (~0.6% OTM each).

**Why not ATM ($678C/$678P — a straddle):**
- ATM straddle costs ~$9.00-10.00 at VIX 18-19 with 6 DTE. That exceeds the $200 max loss target when the stop is factored in. You would need to set the stop at $8.00 (losing only $1.00-2.00), which is inside normal intraday noise for a straddle. You would get stopped out on Thursday afternoon chop before CPI even prints.

**Why not wider ($686/$670 — 8-point wings):**
- Wider wings are cheaper (~$3.50-4.00 total) but require a $14+ move in either direction to profit. That is a 2%+ move — plausible on a genuine CPI shock, but the breakevens are harsh and theta punishes you faster on OTM options. You need a bigger event just to break even.

**Why $682/$674 (4-point wings):**
- Total cost: ~$5.80. Breakevens at ~$668.20 and ~$687.80 require a ~$10 move (1.5%). That is achievable on a hot CPI + VIX spike combination.
- The put side ($674P) is slightly more OTM than the call side ($682C) — this is intentional. In a selloff, VIX spikes and vega inflates the put. In a rally, VIX compresses and the call gets less vega help. The asymmetry compensates: the put needs less intrinsic move because it gets more vega tailwind.
- Delta at entry: Call ~+0.38, Put ~-0.37. Near-symmetrical directional exposure. The strangle is genuinely direction-agnostic at entry.

## Entry Timing: Why Thursday Afternoon Post-PCE (Not Thursday Morning, Not Friday Pre-CPI)

**Thursday morning (pre-PCE):** IV is inflated for the PCE event. You are paying for two events' worth of implied volatility but only want to trade one (CPI). After PCE releases at 8:30 AM and the reaction settles by 10:30 AM, the PCE event premium evaporates. Options reprice 5-10% cheaper purely on the removal of the known Thursday catalyst.

**Thursday 2:00-3:00 PM:** This is the IV trough window.
- PCE volatility has been fully absorbed (4-5 hours post-release).
- CPI is 17-18 hours away. Friday morning's CPI IV bid-up has not yet begun — most of the CPI event premium gets priced in between 3:30 PM Thursday and 9:00 AM Friday as overnight positioning builds.
- The Apr 16 options are pricing "residual vol" — the baseline level between the two events. This is the cheapest the strangle will be until after CPI.

**Friday pre-CPI (7:00-8:25 AM):** IV has been bid up overnight. The strangle now costs $7.00-8.00 instead of $5.80. You are paying the full CPI event premium. If CPI is in-line and the move is only $3-4, IV crushes immediately and your $7.00 strangle drops to $4.50 in minutes. You need a larger move just to break even compared to the Thursday afternoon entry.

**Specific entry protocol:**
1. PCE drops at 8:30 AM Thursday. Do not enter.
2. Monitor reaction through 12:00 PM. Confirm PCE is a non-event (SPY stays within $3 of $678).
3. Between 2:00-3:00 PM ET, place limit orders:
   - Buy 1x SPY Apr 16 $682 Call: Limit $2.80, walk up to $3.20 max.
   - Buy 1x SPY Apr 16 $674 Put: Limit $3.00, walk up to $3.40 max.
   - Combined max entry: $6.60. If both legs fill above $6.60, do not enter — the IV crush did not happen and the risk/reward is degraded.
4. If PCE IS a hot surprise and SPY moves $8+ on Thursday: **do not enter the strangle.** The move already happened. The strangle becomes a directional chase. Stand down.
5. If SPY is below $670 or above $686 at entry time: **do not enter.** The market has already moved beyond your strikes. Stand down.

## Pricing Math

With SPY at $678, VIX at ~18-19 (post-PCE Thursday afternoon), 6 DTE remaining on Apr 16:

### Call Leg ($682C)

| Input | Value |
|-------|-------|
| Spot | $678 |
| Strike | $682 |
| IV | ~18% (post-PCE trough) |
| DTE | 6 |
| Delta | ~+0.38 |
| Theta | ~-$0.22/day |
| Vega | ~$0.10 per 1pt IV |
| Estimated price | $2.60-3.00 (using $2.80) |

### Put Leg ($674P)

| Input | Value |
|-------|-------|
| Spot | $678 |
| Strike | $674 |
| IV | ~19% (puts carry slight skew premium) |
| DTE | 6 |
| Delta | ~-0.37 |
| Theta | ~-$0.23/day |
| Vega | ~$0.11 per 1pt IV |
| Estimated price | $2.80-3.20 (using $3.00) |

### Combined Strangle

| Metric | Value |
|--------|-------|
| Total debit | ~$5.80 ($580 total) |
| Combined theta | ~-$0.45/day ($45/day bleed) |
| Combined vega | ~$0.21 per 1pt IV |
| Upside breakeven | ~$687.80 (SPY needs to rise $9.80) |
| Downside breakeven | ~$668.20 (SPY needs to fall $9.80) |

### Scenario Analysis

**Scenario 1 — Hot CPI, selloff to SPY $665 (SPX ~6650), VIX spikes to 28:**
- Put leg: Intrinsic $674-$665 = $9.00 + extrinsic ~$1.50 + vega boost ~$1.00 = ~$11.50
- Call leg: Deep OTM, but vega partially offsets theta. Worth ~$0.40-0.60.
- Total value: ~$12.00
- Profit: $12.00 - $5.80 = **$6.20 ($620 profit, 107% return)**

**Scenario 2 — Hot CPI + ceasefire collapse by Monday, SPY gaps to $656 (gap fill to SPX ~6560), VIX 32+:**
- Put leg: Intrinsic $674-$656 = $18.00 + extrinsic ~$1.00 + vega = ~$20.00
- Call leg: Nearly worthless. ~$0.10.
- Total value: ~$20.10
- Profit: $20.10 - $5.80 = **$14.30 ($1,430 profit, 247% return)**

**Scenario 3 — Cool CPI surprise, relief rally to SPY $690, VIX drops to 16:**
- Call leg: Intrinsic $690-$682 = $8.00 + extrinsic ~$0.80 = ~$8.80. But VIX crush from 18 to 16 reduces vega by ~$0.40. Net ~$8.40.
- Put leg: Deep OTM, VIX crush hurts. Worth ~$0.20.
- Total value: ~$8.60
- Profit: $8.60 - $5.80 = **$2.80 ($280 profit, 48% return)**
- Note: Rally scenarios produce less profit because VIX compresses on rallies, hurting vega. This is the inherent asymmetry of strangles in a skew environment. The downside payoff is larger because VIX expands on selloffs.

**Scenario 4 — In-line CPI, SPY stays at $675-681, VIX drops to 17:**
- Both legs lose: Combined theta burn (~$0.45/day) + IV crush post-CPI (~15-20% reduction in both legs).
- Friday close value: ~$3.50-4.00 (combined).
- Loss: $5.80 - $3.80 = **$2.00 ($200 loss) — this is where the stop triggers.**

**Scenario 5 — In-line CPI Friday, ceasefire deteriorates over weekend, Monday gap down $10:**
- Friday close: Both legs bled, combined ~$4.20. You DID NOT stop out (above $3.80 threshold).
- Monday open with SPY at $668: Put leg jumps to ~$7.50. Call leg dies to ~$0.15.
- Total: ~$7.65
- Profit: $7.65 - $5.80 = **$1.85 ($185 profit, 32% return)**
- This is the scenario that 0DTE misses entirely. The strangle survived CPI, held through the weekend, and captured Monday's gap.

## Why the Apr 16 Expiry Is the Correct Choice (Decision Summary)

| Factor | 0DTE (Apr 10) | Apr 16 (Monthly) |
|--------|---------------|------------------|
| Cost | ~$3.00 | ~$5.80 |
| Survives CPI non-event | No — total loss | Yes — still has 5 DTE |
| Captures weekend ceasefire risk | No — expired Friday | Yes — lives to Monday |
| Theta drag Thursday-Friday | Extreme ($1.50+/day) | Moderate ($0.45/day) |
| Liquidity | Lower (weekly) | Higher (monthly cycle) |
| Risk management flexibility | None (binary) | Can move stops, scale out |
| Max loss with stop | $300 (full premium) | $200 (stop at $3.80) |

The Apr 16 is more expensive, but you can manage it. The 0DTE is cheaper, but it is a coin flip with no recourse. For a $10K account risking 2%, risk management wins over raw leverage.

## Risk Management Rules

1. **Hard stop at $3.80 combined value.** If the strangle drops from $5.80 to $3.80, sell both legs. Loss = $2.00 per strangle = $200 = exactly 2% of $10K. Set this as a conditional order: if (call bid + put bid) <= $3.80, market sell both.

2. **Do not leg out.** If the put is winning and the call is worthless, do not sell the call and hold the put. The strangle is one position. Exit both legs together, always. Legging out turns a defined-risk event trade into an undefined directional bet.

3. **CPI reaction window: Hold through 10:30 AM Friday.** CPI drops at 8:30 AM. The initial reaction often reverses or extends over 90-120 minutes. Do not panic-sell at 8:35 AM if the strangle is down. Do not take profits at 8:35 AM if it is up. Wait for the full reaction. By 10:30 AM, the CPI move is established.

4. **Take profit at $12.00 combined.** If the strangle hits $12.00 at any point (107% return), sell. You do not need to capture the absolute peak. The thesis was "move larger than implied" — at $12.00, it has been captured. Do not hold for $20.00 hoping for a crash.

5. **Partial profit at $9.00 combined.** If the strangle reaches $9.00 (55% return), sell one leg (the winning leg) and let the other ride. This locks in $3.20 of profit on one leg while giving the remaining leg a free look at further movement. Adjust the stop on the remaining leg to $1.80 (original cost of that leg minus $1.00, ensuring you cannot lose more than $1.00 on the remaining position).

6. **Time stop: Wednesday April 15, 3:00 PM ET.** If neither CPI nor weekend news produced a move by Wednesday, the thesis failed. Exit for whatever the strangle is worth. Do not hold into the final 24 hours of an Apr 16 expiry — theta accelerates to ~$1.00+/day and the position will bleed to zero.

7. **VIX collapse invalidation.** If VIX drops below 16 at any point while holding, exit immediately. VIX below 16 means the market sees no event risk. Your strangle is long vega — it needs volatility to expand, not contract. A VIX at 16 compresses both legs simultaneously.

8. **Max position size: 1 strangle.** At ~$5.80, one strangle risks $200 at the stop. Do not buy 2 strangles ($400 risk = 4% of account) because "CPI is a big deal." The 2% rule is non-negotiable.

## Why a Strangle Over Other Event Structures

### vs. Straddle ($678C/$678P)
- Straddle costs ~$9.50. Stop at $7.50 = $200 loss, but $7.50 is inside normal afternoon theta noise. You would get stopped out before CPI prints.
- Strangle is cheaper, giving wider stop-loss room relative to position cost.

### vs. Iron Condor (Short Strangle + Long Protective Wings)
- Iron condor profits from CPI being a NON-event. That is the opposite thesis. If you think CPI will be boring, sell the condor. If you think it moves, buy the strangle. Picking both is incoherent.

### vs. Single Direction (Just a Put or Just a Call)
- This IS the alternative. Strategy #01 in this folder is the directional put for ceasefire collapse.
- The strangle adds the upside scenario: cool CPI surprise (shelter decelerating, goods deflation from pre-Hormuz supply chains) triggers a relief rally + dovish Fed re-pricing. A put misses that entirely.
- The strangle costs more than a single put (~$5.80 vs ~$3.40 for the $674P alone). The extra $2.40 buys the upside optionality.
- If you have HIGH conviction on direction (ceasefire collapse = down), the put alone is better. If you are trading the EVENT (CPI = big number in either direction), the strangle is correct.

### vs. Calendar Spread (Short Apr 10 / Long Apr 16)
- A calendar spread profits from CPI crushing short-dated IV while preserving long-dated value. Elegant, but it profits most when the market does NOT move (the short Apr 10 expires worthless, the long Apr 16 retains value). That is a vol structure trade, not an event trade. If CPI produces a $15 move, the short leg loses more than the long leg gains and the calendar blows up.

## Correlation With Strategy #01 (Aggressive Put)

If you are running BOTH positions:
- Strategy #01: $670P Apr 17 at $3.40, max loss $200.
- Strategy #16 (this): $682C/$674P Apr 16 strangle at $5.80, max loss $200.
- Combined risk: $400 = 4% of $10K. Above the 2% per-trade rule but acceptable for correlated event trades IF you acknowledge the correlation.

**The overlap:** Both positions profit on a selloff. The strangle's $674P and the directional $670P are $4 apart — a big SPY drop wins on both. This means your downside exposure is effectively 2x leveraged, while your upside exposure is only 1x (just the strangle's call).

**If running both, consider:**
- Reduce the strangle put strike to $670P to avoid doubling up on the same zone, OR
- Accept the 4% combined risk as a deliberate overweight on the ceasefire-collapse thesis with a CPI kicker.

This is a portfolio decision, not a strangle design issue. The strangle in isolation is correctly structured.

## What Could Go Wrong

1. **CPI is perfectly in-line.** March CPI prints +0.3% m/m, exactly as expected. No surprise. VIX drops from 18 to 16.5 immediately. The strangle drops from $5.80 to $3.80-4.00 within 30 minutes of the print. Your stop triggers. Loss: $200. This is the most likely loss scenario — CPI is in-line roughly 50% of the time historically.

2. **CPI is mildly hot (+0.4% vs +0.3% expected).** SPY drops $4 to $674. Your put goes from $3.00 to $3.80. Your call goes from $2.80 to $1.20. Combined: $5.00. You are DOWN $0.80 on a hot print because the move was not large enough to overcome the IV crush on the non-winning leg. This is the "dead zone" — the move exists but is too small. Frustrating. You exit at the time stop for a ~$80-100 loss.

3. **PCE on Thursday IS the surprise.** February PCE comes in hot (pre-Hormuz doesn't mean zero inflation risk — shelter was already elevated). SPY drops $8 on Thursday. You cannot enter the strangle at your planned prices — the put is now $5.50, not $3.00. DO NOT CHASE. The entry protocol says stand down if SPY moves $10+ before entry. Let it go.

4. **Overnight gap Friday morning before CPI.** Futures trade overnight. If geopolitical news breaks Thursday night and SPY futures gap to $670, Friday's CPI is secondary. Your strangle (if entered Thursday PM) is now deep in-the-money on the put side. This is actually a win — you entered at $5.80, and the strangle is worth $8.00+ at Friday's open. Take profit.

5. **Weekend risk cuts both ways.** You hold through the weekend hoping for ceasefire news. Instead, a surprise peace deal is announced Saturday. Monday opens with SPY at $695 and VIX at 15. Your call at $682 is worth $13.00+ intrinsic, but you could not sell Friday when the strangle was worth $4.50 (below your stop but above zero). Net result: you actually profit on the call side. But this is luck, not thesis — the original position was a CPI trade, and the weekend outcome was unrelated to CPI. Process-wise, you should have exited at the time stop if CPI was a non-event.

---

## Summary for Borey

Buy a strangle Thursday afternoon after PCE crushes IV. Apr 16 expiry, not 0DTE — the extra 5 days capture both CPI Friday AND any weekend ceasefire blowup. The strangle costs $5.80, risks $200 at the stop, and profits if SPY moves more than $10 in either direction. The downside payoff is larger (~$620-1,430) because VIX spikes help the put; the upside payoff is smaller (~$280) because VIX compresses on rallies.

This is a volatility trade, not a direction trade. You are betting that March CPI — the first print that captures Hormuz oil price pass-through — will surprise the market. If it does, direction does not matter. If it does not, the $200 stop gets you out clean, and the weekend still offers a second chance via ceasefire headlines.

One strangle. Two catalysts. $200 max risk. Enter Thursday, manage Friday, survive the weekend, exit by Wednesday.
