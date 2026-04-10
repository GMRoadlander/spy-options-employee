# Position 16: Jade Lizard — Bearish Premium Collection

**Date:** 2026-04-06
**Thesis:** The ceasefire gap-up (SPY ~661 to ~678) is overextended and vulnerable to a fill back toward ~661. But instead of making an outright directional bet, we want to collect premium from both sides: sell an OTM put below the gap fill target and sell a call credit spread above current price. The jade lizard structure eliminates upside risk entirely (the call spread credit exceeds the put's strike width above breakeven) while profiting from any outcome between a moderate pullback and sideways churn. We get paid to express a bearish lean without the binary risk of a directional trade.

**Philosophy:** A jade lizard is a premium seller's bear trade. You sell an OTM put for income and hedge the "what if I'm wrong and it rallies" scenario by selling a call credit spread whose credit covers the put obligation above the call short strike. The result: zero risk to the upside, defined risk to the downside, and you collect premium from both sides of the market.

---

## POSITION: "Ceasefire Fade" Jade Lizard

### Leg 1: Short OTM Put (bearish income)

| Field | Detail |
|---|---|
| **Action** | **Sell** 1x SPY Apr 25 $654 Put |
| **Credit** | ~$1.05-1.25 per contract |
| **Delta** | ~-0.12 to -0.15 |
| **Rationale** | 3.5% OTM from current SPY ~678. Below the gap fill target of 661 by $7. Even if the gap fills, this put expires worthless. Only loses if SPY crashes through the gap fill level and keeps falling. |

### Leg 2: Bear Call Credit Spread (upside hedge + income)

| Field | Detail |
|---|---|
| **Action** | **Sell** 1x SPY Apr 25 $684 Call / **Buy** 1x SPY Apr 25 $688 Call |
| **Spread width** | $4.00 |
| **Credit** | ~$1.10-1.30 per contract |
| **Short call delta** | ~0.25-0.28 |
| **Rationale** | $684 is 0.9% above current price — just beyond the ceasefire high. SPY would need to sustain a continued rally through macro data to threaten this strike. The $688 long call caps max loss on the upside. |

### Combined Position

| Field | Detail |
|---|---|
| **Total credit** | ~$2.15-2.55 per jade lizard ($215-$255 per set) |
| **Target fill** | $2.35 total credit ($235 per set) |
| **Quantity** | **3 sets** (3x short put, 3x call spread) |
| **Total credit collected** | ~$705 (3 x $235) |
| **Expiry** | April 25, 2026 (19 DTE) |
| **Entry** | **Tuesday Apr 7, 10:00-10:30 AM ET** |
| **Margin requirement** | ~$654 per short put (cash-secured) or ~$2,500-3,000 total across 3 sets (portfolio margin will be lower) |

---

## The Jade Lizard Math: Why Zero Upside Risk

This is the critical feature. A jade lizard has **no risk to the upside** if the total credit received exceeds the call spread width minus the call spread credit. Let's verify:

- **Call spread width:** $4.00
- **Total credit received:** $2.35 (put credit ~$1.15 + call spread credit ~$1.20)
- **If SPY goes to infinity:** The call spread loses its max ($4.00 - $1.20 = $2.80 net), but the put expires worthless. Your P&L = total credit ($2.35) - call spread max loss ($2.80) = -$0.45... 

Wait -- that's NOT zero upside risk. Let me recalculate. For a true jade lizard (zero upside risk), we need:

**Total credit received >= call spread width**

$2.35 total credit vs. $4.00 spread width. That does NOT eliminate upside risk. We need to adjust.

### Corrected Position: Tighter Call Spread

| Field | Detail |
|---|---|
| **Short put:** | **Sell** 1x SPY Apr 25 $654 Put @ ~$1.15 credit |
| **Call spread:** | **Sell** 1x SPY Apr 25 $683 Call / **Buy** 1x SPY Apr 25 $685 Call @ ~$0.65 credit |
| **Spread width** | $2.00 |
| **Total credit** | ~$1.80 per set ($180 per jade lizard) |

Now check: total credit $1.80 vs. call spread width $2.00. Still short by $0.20. The upside risk is capped at $0.20 per set ($20 per contract) — nearly eliminated but not zero.

### Final Position: Optimal Structure

To achieve true zero upside risk with liquid SPY strikes, we use a **$1-wide call spread** and a richer short put:

| Leg | Strike | Action | Credit |
|---|---|---|---|
| **Short put** | SPY Apr 25 **$655 Put** | Sell | ~$1.20 |
| **Short call** | SPY Apr 25 **$684 Call** | Sell | ~$0.95 |
| **Long call** | SPY Apr 25 **$685 Call** | Buy | ~$0.80 |
| | | **Call spread credit** | ~$0.15 |
| | | **Total credit** | **~$1.35** |

**Upside risk check:** Total credit ($1.35) vs. call spread width ($1.00). **$1.35 > $1.00. Zero upside risk confirmed.** If SPY rallies to 700, 800, infinity — the call spread max loss is $1.00, and we keep the remaining $0.35 from the put credit. We literally cannot lose money to the upside.

---

## FINAL POSITION: Jade Lizard

| Field | Detail |
|---|---|
| **Sell** | 5x SPY Apr 25 $655 Put @ ~$1.20 credit |
| **Sell** | 5x SPY Apr 25 $684 Call @ ~$0.95 credit |
| **Buy** | 5x SPY Apr 25 $685 Call @ ~$0.80 credit |
| **Call spread credit** | ~$0.15 per set |
| **Put credit** | ~$1.20 per set |
| **Total credit per set** | **$1.35** ($135 per jade lizard) |
| **Quantity** | **5 sets** |
| **Total credit collected** | **$675** (5 x $135) |
| **Entry** | **Tuesday Apr 7, 10:00-10:30 AM ET** |
| **Expiry** | April 25, 2026 (19 DTE) |
| **Margin/buying power** | ~$3,275 per short put (cash-secured) = ~$16,375 total; with portfolio margin ~$4,000-5,000 for all 5 sets |

---

## Profit and Loss Scenarios

### Upside (SPY finishes above $685)
| SPY at expiry | Put P&L | Call spread P&L | Net P&L per set |
|---|---|---|---|
| $690 | +$1.20 (expires worthless) | -$1.00 + $0.15 = -$0.85 | **+$0.35** ($35 profit) |
| $700 | +$1.20 | -$0.85 | **+$0.35** ($35 profit) |
| $750 | +$1.20 | -$0.85 | **+$0.35** ($35 profit) |

**You profit on the upside no matter how high SPY goes.** This is the jade lizard's defining feature.

### Sideways (SPY finishes between $655 and $684)
| SPY at expiry | Put P&L | Call spread P&L | Net P&L per set |
|---|---|---|---|
| $678 (unchanged) | +$1.20 | +$0.15 | **+$1.35** ($135 profit — MAX) |
| $670 | +$1.20 | +$0.15 | **+$1.35** ($135 profit — MAX) |
| $661 (gap fill) | +$1.20 | +$0.15 | **+$1.35** ($135 profit — MAX) |
| $658 | +$1.20 | +$0.15 | **+$1.35** ($135 profit — MAX) |

**The entire range from 655 to 684 is max profit territory.** All options expire worthless, you keep the full $1.35 credit.

### Downside (SPY finishes below $655)
| SPY at expiry | Put P&L | Call spread P&L | Net P&L per set |
|---|---|---|---|
| $654 | +$0.20 | +$0.15 | **+$0.35** ($35 profit) |
| $653.65 | $0.00 | +$0.15 | **$0.00** (breakeven) |
| $650 | -$3.80 | +$0.15 | **-$3.65** ($365 loss) |
| $645 | -$8.80 | +$0.15 | **-$8.65** ($865 loss) |
| $640 | -$13.80 | +$0.15 | **-$13.65** ($1,365 loss) |

**Downside breakeven:** $655 - $1.35 = **$653.65** (SPX ~6536)

---

## Profitable Range

**SPY $653.65 to infinity.**

That is not a typo. The jade lizard profits at ANY price above $653.65. There is literally no upper limit.

- From $653.65 to $655: partial profit (put is slightly ITM but credit covers it)
- From $655 to $684: **full max profit** — $1.35 per set, $675 total for 5 sets
- From $684 to $685: reduced profit as call spread goes ITM, but put credit covers it
- Above $685: call spread at max loss ($1.00), but put credit ($1.20) exceeds it — still profit

The ONLY way to lose money is if SPY drops below $653.65 — that's a **3.6% decline** from current levels, well below the gap fill target of $661.

---

## Why This Structure Works for a Bearish Premium Seller

### 1. Bearish lean without binary risk
You believe the gap fills to ~661. A naked put or put spread requires you to be RIGHT about direction. The jade lizard lets you be right, wrong, or completely wrong about direction and still profit. The only losing scenario is a crash THROUGH the gap fill level and BELOW your short put.

### 2. You get paid from both sides
The call spread credit is small ($0.15), but it serves a critical structural purpose: it creates the zero-upside-risk guarantee. And the put credit ($1.20) is the real income engine. Combined, you're collecting $1.35 per set for taking on risk only below $653.65.

### 3. Elevated IV inflates your credits
VIX at ~20 means put premiums are fat. The $655 put at 19 DTE with VIX 20 commands $1.20 — that same put at VIX 14 would be $0.60. You're selling expensive insurance to a scared market.

### 4. Theta decay on two sides
You are short 3 options (1 put + 1 call) and long only 1 (the hedge call). Net theta is strongly positive. Every day that passes with SPY between 655 and 684, all three short options bleed toward zero.

### 5. Gap fill helps but isn't required
If SPY drops to 661 (gap fill), all three options expire worthless and you keep max credit. But if SPY stays at 678, or rallies to 690, you STILL profit. The gap fill thesis adds conviction but the trade doesn't depend on it.

---

## Entry Timing: Why Tuesday 10:00-10:30 AM

1. **Monday absorbs the weekend gap.** Let ceasefire headline momentum play out for one full session. If the rally extends Monday, call premiums inflate further — which means a richer call spread credit on Tuesday.
2. **Tuesday morning IV is still elevated** from the headline event but starting to settle. This is the sweet spot for selling premium: high enough IV to get rich credits, stable enough market to get clean fills.
3. **10:00-10:30 AM ET** is after the opening volatility crush but before institutional flows fully normalize. Put premiums are still fat from overnight fear.
4. **If SPY is above $688 by Tuesday open, do not enter.** The call spread would be too close to ATM. If SPY is below $660, the put is threatened — do not enter.
5. **Valid entry range: SPY between $665 and $685 at time of entry.**

---

## Strike Selection Rationale

### Short put at $655
- **$23 below current SPY** (~3.4% OTM). This is a significant cushion.
- **$6 below the gap fill target of $661.** Even if your bearish thesis plays out perfectly and SPY fills the gap to 661, the put still expires worthless. You need a CRASH, not a pullback, to be threatened.
- **Delta ~0.12-0.15** = roughly 85-88% probability of expiring OTM.
- **Why not $650?** The credit drops to ~$0.80, reducing total credit to ~$0.95. Not enough to cover the $1.00 call spread and eliminate upside risk. $655 is the optimal strike.
- **Why not $660?** Too close to the gap fill target. If SPY fills to 661 and overshoots to 658-659 intraday, you'd be managing a near-ITM put under stress. The extra $5 of cushion at $655 is worth the ~$0.40 reduction in premium.

### Short call at $684
- **$6 above current SPY** (~0.9% OTM). Just above the ceasefire intraday high.
- **Delta ~0.25-0.28** = 72-75% probability of expiring OTM.
- SPY would need to make new highs — continue rallying beyond the already-overextended gap-up — to threaten this strike. The macro calendar (PCE, CPI, earnings) creates headwinds.

### Long call at $685
- **$1 above short call.** The tightest possible spread width on SPY ($1 strikes are available).
- This minimizes the call spread width, which is the key to the zero-upside-risk math. A $1-wide spread costs only $1.00 max if fully ITM, and the $1.20 put credit covers that entirely.

---

## Trade Management

### Take profit: 50% of max credit
- When the combined position value drops to ~$0.67 (from $1.35 entry), **close all three legs.**
- This locks in ~$0.68 profit per set = $340 total for 5 sets.
- **Likely timeline:** 7-10 days if SPY drifts sideways or pulls back modestly.
- Use a single order to close all three legs as a package (most brokers support multi-leg close orders).

### Aggressive take profit: 75%
- If SPY pulls back sharply toward 661-665 in the first week, the position value may drop to ~$0.34 quickly.
- Close at that point for ~$1.01 profit per set = $505 total.

### Stop loss: Put leg management
- **If SPY drops below $658** (short put within $3), begin actively managing:
  - Roll the $655 put down and out (to May expiry, $650 strike) for a small credit or scratch.
  - Or close the put leg at ~$2.50-3.00 loss, keeping the call spread credit ($0.15) as a small offset.
- **Hard stop: if the put reaches $3.50 in value** (loss of $2.30 per set = $1,150 total for 5 sets), close the entire position. This limits the realized loss to ~$1,150 on a $10K account (11.5%).
- The call spread will be near worthless at this point (SPY falling = calls dying), so it costs almost nothing to close.

### Time stop
- If by April 21 (Monday of expiry week) the position is not at 50% profit and SPY is below 660, **close everything.** Gamma risk on the short put becomes unmanageable in the final 4 days.
- If SPY is between 665-680 on April 21, hold through expiry week — theta accelerates and all options should decay rapidly.

### Do NOT adjust the call spread
- The call spread is a hedge, not a profit center. Its $0.15 credit is structural (creates the zero-upside guarantee). Do not roll it, widen it, or close it independently. It lives and dies with the position.

---

## Risk Assessment

| Scenario | SPY Price | Impact | Response |
|---|---|---|---|
| Rally continues — ceasefire euphoria extends | $690+ | **No loss.** Call spread max loss ($1.00) covered by put credit ($1.20). Net profit: $0.35/set ($175 total). | Do nothing. This is the jade lizard's superpower. |
| Sideways churn | $670-680 | **Max profit.** All options decay to zero. Credit kept: $1.35/set ($675 total). | Take profit at 50% or hold to expiry. |
| Gap fills to 661 | $661 | **Max profit.** Everything OTM. Credit kept: $1.35/set ($675 total). | Take profit aggressively — don't wait to see if it bounces. |
| Gap fills and overshoots to 655 | $655 | **Near max profit.** Put is ATM but not ITM. Slight risk of assignment. | Close the put leg. Keep call spread credit. Net profit: ~$1.15/set. |
| Market crashes through gap to 645 | $645 | **Significant loss.** Put is $10 ITM. Loss: ~$8.65/set ($4,325 total). | Stop loss should have triggered at $658. If it didn't, close immediately. |
| VIX spike to 30+ on geopolitical shock | Varies | Short-term mark-to-market loss on the put (IV expansion). | Hold if SPY is above $658. Elevated VIX = richer roll credits if you need to adjust. |
| Flash crash / black swan to 620 | $620 | **Max pain.** Put is $35 ITM. Loss: ~$33.65/set ($16,825 — more than account). | This is the tail risk. Position sizing (5 sets, not 10) and stop losses are the only defense. |

---

## Sizing for a $10K Account

### Cash-secured (no margin)
Cash-secured short puts require full collateral: $655 x 100 = $65,500 per put. On a $10K account, you **cannot** trade this cash-secured. You need margin.

### With standard margin
Typical margin requirement for a short put + call spread combo:
- Short put margin: ~$3,000-4,000 per contract (20% of underlying minus OTM amount)
- Call spread margin: $100 per contract (spread width $1.00 x 100)
- **Total per set: ~$3,100-4,100**
- **5 sets: ~$15,500-20,500** — too much for $10K.

### Recommended sizing: 2 sets

| Field | 2 Sets | 3 Sets (aggressive) |
|---|---|---|
| Total credit | $270 | $405 |
| Max profit | $270 | $405 |
| Margin required | ~$6,200-8,200 | ~$9,300-12,300 |
| Max loss at stop ($658 trigger) | ~$460 | ~$690 |
| Max loss if no stop (SPY $645) | ~$1,730 | ~$2,595 |
| Account risk (at stop) | 4.6% | 6.9% |
| Account risk (no stop) | 17.3% | 26.0% |

**Go with 2 sets.** The $270 max profit is modest but the risk profile is clean. If you have portfolio margin or a larger margin allowance, 3 sets is acceptable but aggressive.

### Revised Final Position (2 Sets)

| Leg | Detail |
|---|---|
| **Sell** | 2x SPY Apr 25 $655 Put @ ~$1.20 |
| **Sell** | 2x SPY Apr 25 $684 Call @ ~$0.95 |
| **Buy** | 2x SPY Apr 25 $685 Call @ ~$0.80 |
| **Total credit** | **$270** (2 x $135) |
| **Max profit** | **$270** (SPY between $655-$684 at expiry) |
| **Max profit on upside** | **$70** (SPY above $685 — still positive) |
| **Downside breakeven** | **$653.65** |
| **Account risk at stop** | ~4.6% ($460 if stopped at $658) |

---

## Execution Checklist

- [ ] **Monday Apr 7:** Watch SPY's price action. Note the intraday high (potential resistance for call spread) and whether 678 holds as support.
- [ ] **Tuesday Apr 7 pre-market:** Check SPY price. Valid entry only if SPY is between $665-$685.
- [ ] **10:00 AM ET:** Place limit order for the jade lizard as a 3-leg combo order. Target $1.35 total credit.
- [ ] If not filled in 15 min, adjust to $1.25. Do not go below $1.15 (the call spread width must be covered).
- [ ] **Confirm zero-upside-risk math:** Total credit received must be > $1.00 (call spread width). If fills come in light and total credit is below $1.00, the jade lizard structure is broken — do not enter.
- [ ] Set alert: SPY at $658 (put defense trigger).
- [ ] Set alert: SPY at $684 (call spread proximity — informational, no action needed).
- [ ] Set alert: Position value at $0.67 (50% profit target).
- [ ] **Apr 9 (PCE):** Monitor. If SPY gaps down below 660, consider closing the put leg.
- [ ] **Apr 10 (CPI):** Same. Back-to-back macro data is the highest-risk window.
- [ ] **Apr 15-17 (earnings wave):** Theta accelerating. If position is profitable, consider closing.
- [ ] **Apr 21 (expiry week Monday):** If not at 50% profit and SPY < 660, close everything.
- [ ] **Apr 25 (expiry):** Should not be holding. Close by 3:00 PM ET at the latest.

---

## Comparison: Jade Lizard vs. Alternatives

| Strategy | Max Profit | Max Loss | Upside Risk | Downside Break-even | Complexity |
|---|---|---|---|---|---|
| **Jade Lizard (this trade)** | $270 | Unlimited below $653.65 | **None** | $653.65 | 3 legs |
| Bear call spread only (Position 03) | $180 | $420 | $420 | N/A (no downside risk) | 2 legs |
| Short put only | $240 | Unlimited below $653.80 | **None** | $653.80 | 1 leg |
| Put butterfly (Position 05) | $13,350 | $1,650 | $1,650 | $656.55 | 3 legs |
| Short strangle | $450+ | Unlimited both sides | **Unlimited** | ~$652 | 2 legs |

The jade lizard sits between a pure put sale and a short strangle. You sacrifice some downside premium (vs. strangle) but gain complete upside immunity. You collect more than a call spread alone. And unlike the butterfly, you profit across a $30+ range instead of needing a precise pin.

---

## Position Summary

| Field | Value |
|---|---|
| Structure | Short $655 Put / Short $684 Call / Long $685 Call |
| Underlying | SPY |
| Expiry | April 25, 2026 |
| Quantity | 2 sets |
| Total credit | $270 ($1.35 per set) |
| Max profit | $270 (SPY 655-684) |
| Upside profit | $70 (SPY above 685) |
| Max loss | Unlimited below $653.65 (managed with stop at $658) |
| Downside breakeven | $653.65 |
| Profitable range | $653.65 to infinity |
| Upside risk | **Zero** (credit exceeds call spread width) |
| R:R | $270 max profit vs. ~$460 managed loss = 1:1.7 (with stops) |
| Theta/day | ~$0.08-0.12 per set (~$16-24/day total) |
| Thesis | Bearish gap fill to 661, but positioned to win even if wrong |
| Conviction | High — the structure profits in 4 out of 5 scenarios |

---

*"A jade lizard is the premium seller's answer to 'What if I'm wrong?' You sell a put because you think the market drops. You sell a call spread because you know you might be wrong. The combined credit means you literally cannot lose if you're wrong. The only losing scenario is being MORE right than you expected — and even then, a stop loss keeps you alive."*
