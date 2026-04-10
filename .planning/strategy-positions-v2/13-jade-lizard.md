# 13 — Jade Lizard (Short OTM Put + Bear Call Spread)

**Date drafted:** 2026-04-06
**Drafter role:** Advanced combo trader, premium seller with bearish lean
**Market snapshot:** SPX ~6783 (SPY ~678). Gap up from ~6610 on US-Iran ceasefire Apr 7. VIX ~20. Ceasefire structurally unenforceable (31 separate military branches, Supreme Leader in coma, no unified chain of command). $10K account.

---

```
POSITION: SPY Apr 25 $652P / $686C / $687C — "Ceasefire Hopium" Jade Lizard

Leg 1 — Short OTM Put (bearish income):
  Action: Sell to open 2x SPY Apr 25 $652 Put
  Credit: ~$0.95 per contract ($190 total)
  Delta: ~-0.10 to -0.12

Leg 2 — Short Call (bear call spread, short leg):
  Action: Sell to open 2x SPY Apr 25 $686 Call
  Credit: ~$0.85 per contract ($170 total)
  Delta: ~0.22 to 0.25

Leg 3 — Long Call (bear call spread, long leg):
  Action: Buy to open 2x SPY Apr 25 $687 Call
  Debit: ~$0.72 per contract ($144 total)

Call spread credit: $0.85 - $0.72 = $0.13 per set
Put credit: $0.95 per set
Total credit per jade lizard: $1.08 ($108 per set)
Quantity: 2 sets
Total credit collected: $216

Entry: Tuesday April 8, 10:00-10:30 AM ET
Expiry: April 25, 2026 (17 DTE at entry)
Valid entry range: SPY between $672 and $684 at time of entry

ZERO-UPSIDE-RISK CHECK:
  Total credit received: $1.08
  Call spread width: $1.00 ($687 - $686)
  $1.08 > $1.00 — CONFIRMED: zero upside risk.
  If SPY goes to infinity, call spread loses $1.00, put expires worthless.
  Net P&L = $1.08 - $1.00 = +$0.08 profit per set. You cannot lose money to the upside.

Margin requirement: ~$3,200-3,800 per short put (standard margin) = ~$6,400-7,600 total for 2 sets
  Call spread margin: $100 per set (spread width x 100), offset by credit received
  Total buying power reduction: ~$6,600-7,800 — fits within $10K account

Max profit: $216 (SPY between $652 and $686 at expiry — all options expire worthless)
Max profit on upside: $16 (SPY above $687 — call spread at max loss but put credit covers it)
Downside breakeven: $650.92 (short put strike $652 minus total credit $1.08)
Profitable range: $650.92 to infinity
Max loss: Theoretically unlimited below $650.92 (managed with stop — see below)

Take profit: Close all 3 legs when position value drops to $0.54 (50% of $1.08 credit)
Stop loss: If SPY drops below $655, begin defense. Hard stop if put reaches $3.00 in value.
Time stop: If by April 21 the position is not at 50% profit and SPY is below $658, close everything.
Invalidation: SPY closes below $660 before entry (gap already filling, put is too close).
  Also invalid if VIX drops below 15 (premiums too thin to construct a valid jade lizard).
```

---

## Why These Exact Strikes

### Short put at $652 — not $655, not $660

The gap fill target is SPY ~$661 (SPX ~6610). The short put MUST sit below the gap fill target with enough cushion that even if the thesis plays out perfectly, the put expires worthless.

- **$652 is $26 below current SPY** (~3.8% OTM). Delta ~0.10-0.12 means roughly 88-90% probability of expiring OTM.
- **$652 is $9 below the gap fill target of $661.** If SPY fills the gap to $661 and overshoots by $5 intraday to $656, you still have $4 of cushion. The put is safe through a full gap fill and a moderate overshoot.
- **Why not $655?** Only $6 below the gap fill. If the gap fills with momentum (as gaps often do — they overshoot), $655 gets tested. An intraday wick to $654 puts you in management mode during a high-stress moment. The extra $3 at $652 costs roughly $0.25 in credit but buys meaningful peace of mind.
- **Why not $660?** One dollar below the gap fill target. Insane. If your bearish thesis is correct and SPY fills to $661, your short put is $1 away from being ATM. You would be panicking right at the moment your thesis is working. This defeats the purpose of the jade lizard structure.
- **Why not $648?** Credit drops to ~$0.60. Total credit becomes $0.73 per set, which is BELOW the $1.00 call spread width. The zero-upside-risk condition breaks. The jade lizard structure is destroyed. $652 is the optimal balance.

### Short call at $686 — selling the ceasefire hopium

- **$686 is $8 above current SPY** (~1.2% OTM). Just above the likely ceasefire intraday resistance zone.
- The ceasefire gap-up has already priced in the "good news." For SPY to sustain above $686, you need follow-through buying — which requires the ceasefire to actually hold. Given 31 military branches and no chain of command, the probability of sustained follow-through is low.
- Delta ~0.22-0.25 means roughly 75-78% probability of expiring OTM.
- **Why not $684?** Too close. A normal 1% daily move (which VIX 20 implies) from $678 reaches $685 — your short call would be breached on a routine green day. You need room for normal noise.
- **Why not $690?** Credit drops to ~$0.55. The call spread credit becomes ~$0.07, which barely contributes to the structure. The higher you go, the more the jade lizard degenerates into just a naked put sale.

### Long call at $687 — the tightest possible hedge

- **$1 above the short call.** SPY has $1-wide strikes. This is the minimum spread width.
- A $1-wide call spread means you only need $1.00 of total credit to eliminate upside risk. With the $652 put generating $0.95 and the call spread generating $0.13, total credit of $1.08 clears the $1.00 threshold.
- The tighter the spread, the less credit the call spread generates — but the less you need to generate. The $1 width is structurally optimal for jade lizards on SPY.

---

## P&L at Expiration (Per Set)

### Upside — SPY finishes above $687

| SPY at Expiry | Put P&L | Call Spread P&L | Net P&L (per set) | Total (2 sets) |
|---|---|---|---|---|
| $690 | +$0.95 (expires worthless) | -$1.00 + $0.13 = -$0.87 | **+$0.08** | **+$16** |
| $700 | +$0.95 | -$0.87 | **+$0.08** | **+$16** |
| $750 | +$0.95 | -$0.87 | **+$0.08** | **+$16** |

The call spread is at max loss ($1.00) but the put credit ($0.95) plus call spread credit ($0.13) exceeds it. You profit $0.08 per set no matter how high SPY goes. This is the jade lizard's defining feature: **zero upside risk.**

### Sideways / moderate pullback — SPY finishes between $652 and $686

| SPY at Expiry | Put P&L | Call Spread P&L | Net P&L (per set) | Total (2 sets) |
|---|---|---|---|---|
| $686 (short call strike) | +$0.95 | +$0.13 | **+$1.08** (MAX) | **+$216** |
| $678 (unchanged) | +$0.95 | +$0.13 | **+$1.08** (MAX) | **+$216** |
| $670 | +$0.95 | +$0.13 | **+$1.08** (MAX) | **+$216** |
| $661 (gap fill) | +$0.95 | +$0.13 | **+$1.08** (MAX) | **+$216** |
| $655 | +$0.95 | +$0.13 | **+$1.08** (MAX) | **+$216** |
| $652 (short put strike) | +$0.95 | +$0.13 | **+$1.08** (MAX) | **+$216** |

**The entire $34 range from $652 to $686 is max profit territory.** Every option expires worthless. You keep the full $1.08 credit per set. This is a massive sweet spot.

### Downside — SPY finishes below $652

| SPY at Expiry | Put P&L | Call Spread P&L | Net P&L (per set) | Total (2 sets) |
|---|---|---|---|---|
| $651 | +$0.95 - $1.00 = -$0.05 | +$0.13 | **+$0.08** | **+$16** |
| $650.92 | -$0.13 | +$0.13 | **$0.00** (breakeven) | **$0** |
| $650 | -$1.05 | +$0.13 | **-$0.92** | **-$184** |
| $648 | -$3.05 | +$0.13 | **-$2.92** | **-$584** |
| $645 | -$6.05 | +$0.13 | **-$5.92** | **-$1,184** |
| $640 | -$11.05 | +$0.13 | **-$10.92** | **-$2,184** |
| $635 | -$16.05 | +$0.13 | **-$15.92** | **-$3,184** |

**Downside breakeven: $650.92** — SPY must drop 4.0% from current levels. That is well below the gap fill target ($661) and requires a genuine crash, not a pullback.

---

## Profitable Range

**$650.92 to infinity.**

This is the jade lizard's superpower. You profit at every single price from $650.92 upward — there is no upper limit. The ONLY losing scenario is a crash through $650.92, which requires SPY to fall 4.0% and blow through the gap fill by $10.

| SPY Zone | What Happens | P&L |
|---|---|---|
| Above $687 | Call spread at max loss, put worthless | +$0.08/set (+$16 total) — still profit |
| $686 to $687 | Call spread partially ITM, put worthless | +$0.08 to +$1.08/set — profit |
| $652 to $686 | All options expire worthless | +$1.08/set (+$216 total) — **MAX PROFIT** |
| $650.92 to $652 | Put slightly ITM, credit covers it | +$0.00 to +$1.08/set — profit |
| Below $650.92 | Put deeply ITM, credit insufficient | **LOSS** — managed with stop |

---

## Why This Structure for This Market

### 1. The gap fill thesis does not require a crash

You believe SPY fills the gap to ~$661. The jade lizard profits at $661. It also profits at $678 (no move), $670 (partial fill), $685 (rally), and $700 (big rally). You only lose if SPY crashes THROUGH the gap fill and keeps falling another $10 to $650.92. The jade lizard decouples your thesis from your risk: you have a bearish lean but you are positioned to profit in every scenario except a crash.

### 2. Elevated VIX inflates both sides of your credit

VIX at 20 is ~20% above the long-run average of ~16-17. This inflates both put premiums (your main income leg) and call premiums (your hedge leg). The $652 put at VIX 20 commands ~$0.95 — at VIX 14, it would be ~$0.45. You are selling expensive insurance to a frightened market.

### 3. The ceasefire is the perfect call spread catalyst

The call credit spread sells the thesis that the ceasefire rally has legs. It does not. Thirty-one separate military branches with no central command, a Supreme Leader in a coma, and 800+ ships still trapped in the Strait. The "good news" is already in the price. For SPY to sustain above $686, the ceasefire needs to hold for weeks — which requires something that does not exist (a unified chain of command to enforce it). You are selling lottery tickets to optimists.

### 4. Theta decay on three short exposures

You are short 2 options (the put and the short call) and long only 1 (the hedge call at $687). Net theta is positive. Every day SPY stays between $652 and $686, all short options bleed toward zero. At 17 DTE with VIX 20, theta on each short option is roughly $0.04-0.06/day. Combined net theta across 2 sets is approximately $12-18/day.

### 5. Two sets fits the $10K account

Margin on 2 naked short puts at $652 is approximately $6,400-7,600 (standard margin = ~20% of strike minus OTM amount). The call spread adds ~$200 of margin. Total buying power reduction is roughly $6,600-7,800, leaving $2,200-3,400 of free margin. This is tight but workable — you have enough cushion to not face a margin call unless SPY drops to the stop loss zone.

---

## Entry Rules

### Why Tuesday, not Monday

1. **Monday absorbs the ceasefire headline.** Let the gap-up play out for one full session. If the rally extends Monday, call premiums inflate further — richer call spread credit on Tuesday.
2. **Tuesday morning IV is still elevated** from the event but starting to settle. This is the premium seller's sweet spot: high enough IV for rich credits, stable enough for clean fills.
3. **If SPY runs to $688+ on Monday**, the call strikes need to be moved higher (reducing credit). Wait and reassess. If SPY drops to $665 on Monday, the put is closer than intended. Wait and reassess. Tuesday entry gives you one day of information.

### Entry checklist

- [ ] Confirm SPY is between $672 and $684 at 10:00 AM ET Tuesday.
- [ ] Confirm VIX is above 18. Below 18 means credits are too thin.
- [ ] Place the jade lizard as a **3-leg combo order** at a limit of $1.08 total credit.
- [ ] If not filled in 15 minutes, adjust limit to $1.00. **Do NOT go below $1.00** — that is the call spread width. Below $1.00 total credit, the zero-upside-risk condition breaks and the structure is invalid.
- [ ] Once filled, confirm: total credit > $1.00. If fills came in light and total credit is $0.98 or below, the jade lizard structure is broken. Close the call spread immediately and reassess.

### Conditions that cancel the trade

| Condition | Why | Action |
|---|---|---|
| SPY below $665 at entry time | Short put is only $13 away — too close | Do not enter |
| SPY above $688 at entry time | Short call at $686 is already ITM | Do not enter |
| VIX below 15 | Premiums collapse — cannot construct a valid jade lizard | Do not enter |
| VIX above 30 | Something has already broken — entering mid-crisis | Do not enter |
| Total credit below $1.00 | Zero-upside-risk condition fails | Do not enter |

---

## Management Rules

### Take profit: 50% of max credit

- When the combined 3-leg position can be bought back for $0.54 or less, **close all three legs.**
- This locks in ~$0.54 profit per set = **$108 total for 2 sets.**
- Likely timeline: 8-12 days if SPY drifts sideways or pulls back modestly toward 665-670.
- Use a single combo order to close all three legs. Do not leg out.

### Aggressive take profit: 70%

- If SPY pulls back sharply toward $661-665 in the first 5 days, the put remains OTM and all options decay rapidly.
- Close when the position value drops to ~$0.32 for ~$0.76 profit per set = **$152 total.**

### Put defense — the critical rule

The short $652 put is the only source of meaningful risk. The call spread is fully hedged. All management attention goes to the put.

| SPY Level | Threat Level | Action |
|---|---|---|
| Above $660 | None | Hold. Everything is working. |
| $658-$660 | Yellow — monitoring | Tighten alerts. Check daily. No action yet. |
| $655-$658 | Orange — active management | Prepare to roll or close the put leg. Place a GTC buy-to-close on the put at $3.00 (hard stop). |
| Below $655 | Red — close or roll | **Close the put immediately** if it reaches $3.00 in value (loss of ~$2.05 per put, $410 total for 2 sets). Or roll the put to May expiry $647 strike for a small credit. |
| Below $650 | Emergency | Close everything. The stop should have already triggered. Realized loss ~$410-500. |

**Hard stop on the put: if the $652 put reaches $3.00 in value, close it.** This limits the put leg loss to ~$2.05 per contract ($410 total for 2 sets). The call spread will be near worthless at this point (SPY falling means calls die), so it costs almost nothing to close. Net loss after the call spread credit: approximately $384.

### Time stop

- **April 21 (Monday of expiry week):** If the position is not at 50% profit AND SPY is below $658, close everything. Gamma risk on the short put becomes unmanageable in the final 4 days.
- If SPY is between $665 and $680 on April 21, hold through expiry week. Theta accelerates and all options should decay rapidly.
- **April 25 (expiry day):** Do not hold to literal expiration. Close by 3:00 PM ET at the latest. Pin risk and after-hours assignment risk are not worth the last $0.10 of decay.

### Do NOT adjust the call spread

The call spread is structural, not a profit center. Its $0.13 credit creates the zero-upside guarantee. Do not roll it, widen it, or close it independently. It lives and dies with the position. If you close the call spread while keeping the put, you have converted a jade lizard into a naked put — a fundamentally different risk profile.

---

## Risk Assessment

| Scenario | SPY Price | P&L (2 sets) | Response |
|---|---|---|---|
| Ceasefire rally extends, new highs | $690+ | **+$16** (profit) | Do nothing. Zero upside risk. |
| Sideways churn, market digests | $672-682 | **+$216** (max profit) | Take profit at 50% or hold. |
| Modest pullback, gap partially fills | $665-672 | **+$216** (max profit) | Take profit aggressively. |
| Full gap fill to $661 | $661 | **+$216** (max profit) | Close — thesis played out, bank the win. |
| Gap fill + overshoot to $655 | $655 | **+$216** (max profit) | Close immediately — approaching danger zone. |
| Crash through gap to $650 | $650 | **-$184** | Stop should have triggered at $655. Close now. |
| Black swan crash to $640 | $640 | **-$2,184** (if no stop) | Stop loss prevents this. With stop at $3.00 put value, max realized loss is ~$384. |
| VIX spike to 30+ on geopolitical shock | Varies | Mark-to-market loss on put (IV expansion) | Hold if SPY is above $658. Elevated VIX = richer roll credits if adjustment needed. |
| VIX crush to 14 on peace deal | $680+ | Accelerated profit on both sides | Close early — all options decay faster in low IV. |

---

## Sizing Analysis for $10K Account

| Field | 1 Set | 2 Sets (recommended) | 3 Sets (aggressive) |
|---|---|---|---|
| Total credit | $108 | **$216** | $324 |
| Max profit | $108 | **$216** | $324 |
| Margin required | ~$3,300-3,900 | **~$6,600-7,800** | ~$9,900-11,700 |
| Max loss at stop ($3.00 put value) | ~$192 | **~$384** | ~$576 |
| Max loss without stop (SPY $645) | ~$592 | ~$1,184 | ~$1,776 |
| Account risk (at stop) | 1.9% | **3.8%** | 5.8% |
| Account risk (no stop) | 5.9% | 11.8% | 17.8% |
| Remaining free margin | ~$6,100-6,700 | **~$2,200-3,400** | Margin call likely |

**2 sets is the right size.** The $216 max profit is modest but the structure is sound. The managed loss at the stop is $384 (3.8% of account) — slightly above the 2% strict threshold but acceptable for a trade with this probability profile. 3 sets would consume nearly all available margin and leave no room for error. 1 set works for extremely conservative accounts but the $108 max profit feels thin for 17 days of capital commitment.

---

## Calendar of Key Dates During the Trade

| Date | Event | Impact on Position | Action |
|---|---|---|---|
| **Tue Apr 8** | **ENTRY** | Place the jade lizard | Enter 10:00-10:30 AM ET |
| Wed Apr 9 | PCE (February) | Likely stale data, pre-Hormuz. Low impact expected. | Monitor. If SPY gaps below $660, evaluate put defense. |
| Thu Apr 10 | CPI (March) | Higher impact. Hot CPI = SPY drops (gap fill accelerates). Cool CPI = SPY rallies (call spread safe). | If SPY drops below $658, execute put defense. If SPY rallies above $686, no action needed (zero upside risk). |
| Fri Apr 11 | Weekly opex | Gamma effects on weekly options. Your Apr 25 options less affected. | Monitor only. |
| Apr 14-17 | Earnings wave begins | Increased single-stock vol but index-level impact moderate. Theta accelerating on your position. | If at 50% profit, consider closing. |
| **Mon Apr 21** | Expiry week begins | Gamma intensifies. Short put becomes highly sensitive. | **Time stop check:** if not at 50% profit AND SPY below $658, close everything. |
| **Fri Apr 25** | **EXPIRY** | All options expire. | **Must be closed by 3:00 PM ET.** Do not hold to expiration. |

---

## Comparison to Position 16 (v1 Jade Lizard)

The v1 jade lizard used a $655 put, $684/$685 call spread, and recommended 5 sets initially (revised to 2). Key improvements in this v2:

| Change | v1 (Position 16) | v2 (This Position) | Why |
|---|---|---|---|
| Short put strike | $655 | **$652** | 3 extra points of cushion below gap fill. $655 was only $6 below $661 — uncomfortably close during a gap fill overshoot. |
| Call spread strikes | $684/$685 | **$686/$687** | $684 was only 0.9% above spot — breached on a normal green day. $686 gives 1.2% cushion. |
| Total credit | $1.35 | **$1.08** | Lower credit is the cost of wider cushions on both sides. But the structure is more robust — less likely to need active management. |
| Upside excess | $0.35 over spread width | **$0.08 over spread width** | v1 had more excess, but both satisfy the zero-upside-risk condition. Any amount over $1.00 works. |
| Margin fit | 5 sets initially proposed (did not fit $10K) | **2 sets from the start** | Realistic sizing from the beginning. |
| Put stop trigger | SPY $658 | **SPY $655 / put value $3.00** | More specific — a price level AND a premium level. Whichever triggers first. |

The tradeoff is clear: v2 collects $0.27 less per set ($54 less on 2 sets) but has materially wider cushions on both sides. In a market with elevated VIX, gap risk, and headline-driven moves, the wider cushions are worth the reduced credit.

---

## Position Summary

| Field | Value |
|---|---|
| Structure | Short $652 Put / Short $686 Call / Long $687 Call |
| Underlying | SPY |
| Expiry | April 25, 2026 (17 DTE at entry) |
| Quantity | 2 sets |
| Total credit | $216 ($1.08 per set) |
| Max profit | $216 (SPY $652-$686 at expiry) |
| Upside profit | $16 (SPY above $687 — still positive) |
| Max loss (managed) | ~$384 (stop at $3.00 put value) |
| Max loss (unmanaged) | Unlimited below $650.92 |
| Downside breakeven | $650.92 |
| Profitable range | **$650.92 to infinity** |
| Upside risk | **Zero** (credit of $1.08 exceeds $1.00 call spread width) |
| R:R (managed) | $216 max profit vs. ~$384 managed loss = **1:1.8** |
| Theta/day (net) | ~$0.06-0.08 per set (~$12-18/day total for 2 sets) |
| Probability of profit | ~85-90% (put has ~10% chance of going ITM; upside is risk-free) |
| Thesis | Bearish gap fill to $661, but positioned to profit even if completely wrong |

---

*The jade lizard answers the question every premium seller asks: "What if I'm wrong about direction?" You sell a put because you believe the market drops. You sell a call spread because you know you might be wrong. The combined credit eliminates the upside entirely. The only way to lose is if the market drops more than you expected — and even then, a disciplined stop keeps you alive. In a market driven by an unenforceable ceasefire between 31 militaries with no chain of command, collecting $216 to bet that SPY does not crash below $651 is a probability trade worth taking.*
