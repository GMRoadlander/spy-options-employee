# W2-07: OIL PROXY TRADE -- The Uncorrelated Leg

**Date drafted:** 2026-04-06 (Sunday)
**Author:** Oil/Energy Divergence Analyst
**Inputs:** W1-03-market-context.md, W1-01-risk-constitution.md, W1-06-correlation-budget.md
**Status:** PROPOSAL -- requires Borey review before entry

---

## WHY NO PREVIOUS SWARM PROPOSED THIS

V1 through V3-W1 produced 40+ position proposals. Every single one was denominated in SPY or SPX. Every single one bet on equity direction. The entire swarm treated the Iran-Hormuz crisis as a stock market event.

It is not. It is an oil event that happens to affect stocks.

The primary transmission mechanism is: Hormuz closes -> oil spikes -> inflation expectations spike -> equities sell off. The swarm has been trading the LAST link in the chain (equities selling off) while ignoring the FIRST link (oil spiking). This is like betting on whether the house floods while ignoring the river level.

Oil is the primary asset. SPY is the derivative.

**The novel angle:** If the ceasefire collapses, oil recovers to $110-120 REGARDLESS of what SPY does. Oil doesn't need a gap fill thesis, doesn't need PCE to come hot, doesn't need VIX to spike. Oil just needs one Houthi drone, one IRGC Navy seizure, one headline that the ceasefire is dead. The catalyst space for oil is larger, simpler, and more direct than for equities.

More importantly: oil calls are UNCORRELATED to SPY puts in the chop/rally scenarios. If SPY rallies to 690 on renewed ceasefire confidence, the SPY puts die -- but oil should ALREADY be near $94 and the calls lose only their small premium. If SPY chops at 678, the SPY puts bleed theta -- but oil calls bleed independently and don't compound the directional loss. This is the diversification that W1-06 (Correlation Budget) demanded but no trade proposal delivered on a different underlying.

---

## THESIS

### The Setup

Oil crashed 16% from $112 to $94 on the ceasefire announcement. This priced in:
- Full Hormuz reopening (has NOT happened -- 3 ships transited, 800+ still trapped)
- Sustained global oil supply normalization (cannot happen with 31 uncoordinated armed services)
- Conflict de-escalation trajectory (Supreme Leader in a coma, no successor named)

Oil at $94 is pricing a ceasefire that is structurally unenforceable. The same thesis that drives the SPY gap fill -- but applied to the asset that moves FIRST.

### The Asymmetry

If ceasefire collapses:
- Oil snaps from $94 back toward $110-120 within days (the move is FAST because tanker insurance reprices immediately, physical traders scramble)
- USO (United States Oil Fund) tracks front-month WTI futures. USO moves roughly 1:1 with crude on percentage basis for short-term moves
- A $94 -> $112 crude move = ~19% USO gain
- A $94 -> $120 crude move = ~28% USO gain

If ceasefire holds:
- Oil drifts lower to $85-88 as Hormuz reopens for real
- USO drops ~6-10%
- Call premium is lost (max risk = debit paid)

The risk/reward is structurally favorable: the upside move is 2-3x the downside drift, and the upside is an event-driven snap while the downside is a slow grind.

### Why USO and Not /CL Options

/CL (crude oil futures) options require a futures account, margin, and contract specifications that add complexity for a new trader. One /CL contract controls 1,000 barrels (~$94,000 notional). The margin alone would consume most of the $10K account.

USO is an ETF. It trades in a standard equity account. Options are American-style, penny-increment pricing, high liquidity. It is the correct instrument for a $10K account making its first oil bet.

**Current USO price:** ~$78 (USO tracks CL futures but at a different absolute level due to fund NAV, contango roll costs, etc. The percentage moves are what matter.)

### Why NOT XLE (Energy Sector ETF)

The user suggested XLE puts as a "sell what rallied" play. I am deliberately NOT recommending this, and here's why:

XLE is a STOCK that happens to hold energy companies. In a ceasefire collapse:
1. Oil spikes (good for energy companies' revenue)
2. Broader market crashes (bad for all stocks including energy)
3. These forces PARTIALLY OFFSET each other

XLE's behavior in a Hormuz re-closure is ambiguous. Energy stocks could rally on oil or crash with SPY. You'd be paying for a directional bet where the direction is uncertain.

USO calls have NO ambiguity. Oil goes up, USO goes up. Period. No cross-currents, no sector rotation dynamics, no earnings surprises from individual companies diluting the thesis.

The cleaner the thesis, the better the trade. USO is the clean trade.

---

## POSITION: USO Call Debit Spread

### Structure

| Field | Detail |
|---|---|
| **Instrument** | USO (United States Oil Fund ETF) |
| **Structure** | Buy 2x USO May 16 $80C / Sell 2x USO May 16 $86C |
| **Type** | Bull call debit spread (vertical) |
| **Spread width** | $6 ($600 max value per spread at expiry) |
| **Entry** | Monday Apr 7, 10:30-11:00 AM ET (after extended Monday blackout per constitution) |
| **Expiry** | May 16, 2026 (39 DTE at entry) |
| **Estimated debit** | ~$1.60 per spread ($160 per contract) |
| **Quantity** | 2 spreads |
| **Total cost / max loss** | ~$320 (3.2% of account -- see Constitution Compliance) |
| **Max profit** | $600 per spread x 2 = $1,200 total (if USO >= $86 at expiry) |
| **Breakeven at expiry** | USO ~$81.60 (strike + debit = $80 + $1.60) |

### Why These Strikes

**$80 long call:** USO at ~$78 means this is $2 OTM (~2.5%). Not too far -- you need USO to move only 2.5% to be ATM, and the thesis calls for a 19-28% move in crude. Close enough to capture the move quickly once the catalyst fires.

**$86 short call:** This corresponds to crude oil at roughly $108-112. The thesis target is $110-120 crude. Selling the $86 caps your upside at approximately where crude was BEFORE the ceasefire crash -- you're not betting on new highs, just a reversion to the pre-ceasefire level. This is conservative and realistic.

**$6 width:** Wide enough for meaningful profit ($600/spread), narrow enough that the debit stays manageable ($160/spread). A $4-wide spread would cost ~$120 but cap profit at $400; a $8-wide would cost ~$190 but the extra $200 upside requires crude above $120, which is greedy.

**39 DTE (May 16):** The ceasefire is 2 weeks with Islamabad talks April 11. If the ceasefire collapses, it likely happens within 2-3 weeks of announcement (structural failures manifest quickly once operational stress tests begin). 39 DTE gives the thesis 5+ weeks to play out, surviving multiple news cycles, OPEC+ meetings, and the full Islamabad negotiation timeline.

### Pricing Estimates (USO ~$78, Crude ~$94, VIX ~20)

Crude oil implied volatility is typically 25-35% (higher than equity vol). USO options will reflect this.

| Leg | Strike | Delta | Est. Price | Qty | Cash Flow |
|---|---|---|---|---|---|
| Long call | $80C | ~0.38 | ~$3.20 | Buy 2 | -$640 |
| Short call | $86C | ~0.20 | ~$1.60 | Sell 2 | +$320 |
| **Net per spread** | | | | | **-$1.60 debit ($160)** |

Total debit: 2 x $160 = **$320**

**Fill notes:** USO options are liquid but not SPY-liquid. Bid-ask spreads on monthly expiry options are typically $0.05-0.10. Use a limit order at the mid. If no fill in 15 minutes, walk by $0.05. Do not pay more than $1.75/spread ($350 total). If VIX is spiking Monday morning (ceasefire headlines over weekend), crude IV will be elevated and the spread may cost $1.80-2.00 -- reduce to 1 spread to stay under $200.

---

## P&L TABLE

USO percentage moves mapped from crude oil price levels:

| Crude Oil | USO (est.) | Long $80C Value | Short $86C Value | Spread Value | Less Debit | **P&L (2 spreads)** |
|---|---|---|---|---|---|---|
| **$85** (ceasefire holds, drift lower) | ~$71 | $0 | $0 | $0 | -$320 | **-$320** |
| **$90** (slow bleed) | ~$74 | $0 | $0 | $0 | -$320 | **-$320** |
| **$94** (flat, no change) | ~$78 | $0 | $0 | $0 | -$320 | **-$320** |
| **$97** (minor uptick) | ~$80.50 | $0.50 | $0 | $0.50 | -$320 | **-$220** |
| **$100** | ~$82.50 | $2.50 | $0 | $2.50 | -$320 | **+$180** |
| **$105** | ~$85 | $5.00 | $0 | $5.00 | -$320 | **+$680** |
| **$108** (pre-ceasefire level) | ~$86 | $6.00 | $0 | $6.00 | -$320 | **+$880** |
| **$112** (war high) | ~$88 | $8.00 | $2.00 | $6.00 | -$320 | **+$880** |
| **$120** (thesis max) | ~$93 | $13.00 | $7.00 | $6.00 | -$320 | **+$880** |
| **$130** (overshoot) | ~$98 | $18.00 | $12.00 | $6.00 | -$320 | **+$880** |

### Key P&L Levels

| Crude Level | Scenario | Position P&L | Return on $320 |
|---|---|---|---|
| **$94** (flat) | Ceasefire chop | **-$320** | -100% |
| **$100** (mild bounce) | Hormuz tightens slightly | **+$180** | +56% |
| **$108** (pre-ceasefire reversion) | Ceasefire formally collapses | **+$880** | +275% |
| **$112+** (war high or above) | Full Hormuz re-closure | **+$880** | +275% (capped) |

**Max risk: $320. Max reward: $880. R:R = 1:2.75.**

This is not a lottery ticket (unlike the 1:51 crash convexity backspread). This is a workhorse trade with realistic, achievable upside and a capped, known downside.

---

## THE CORRELATION ARGUMENT -- WHY THIS CHANGES THE PORTFOLIO

This is the critical section. Read it alongside W1-06 (Correlation Budget).

### Scenario Matrix: SPY Puts + Oil Calls

| Scenario | SPY Bear Put Spread | USO Call Spread | Combined | Correlation |
|---|---|---|---|---|
| **Ceasefire collapses, market crashes** | WIN (+$300-600) | WIN (+$500-880) | **BIG WIN** | Positive (both win) |
| **Ceasefire collapses, market chops** | LOSE (-$130-200) | WIN (+$500-880) | **NET WIN** | Negative (oil wins, SPY flat) |
| **Ceasefire holds, market rallies** | LOSE (-$130-200) | LOSE (-$320) | **LOSE** | Positive (both lose) |
| **Chop everywhere, nothing happens** | LOSE (-$80-150) | LOSE (-$100-200*) | **SMALL LOSE** | Positive (both bleed) |
| **Surprise oil supply glut (non-Iran)** | NEUTRAL/WIN | LOSE (-$320) | **MIXED** | Negative |
| **Hot CPI, stagflation fears** | WIN (+$200-400) | WIN (+$200-400) | **WIN** | Positive |

*Theta decay on the USO spread is ~$3-5/day initially, so a 2-week hold with no movement loses roughly $40-70, not the full $320.

### The Key Insight

Look at row 2: **"Ceasefire collapses, market chops."** This is the scenario where:
- The ceasefire breaks (a Houthi drone hits a tanker)
- Oil spikes on the headlines
- But SPY doesn't sell off because the market has already "priced in" geopolitical risk, or because a simultaneous dovish Fed comment offsets the fear

In this scenario, the SPY puts lose money but the USO calls WIN INDEPENDENTLY. The oil move happens on the physical commodity market regardless of whether equity indices react. This is the decorrelation that V1/V2/V3-W1 never achieved because every trade was SPY-denominated.

### The Bad Scenario

Row 3: "Ceasefire holds, market rallies." Both positions lose. This is the one scenario where the oil trade adds to losses rather than hedging them. Combined max loss: $520-$520 (SPY puts $200 + USO calls $320).

This exceeds the $500 total portfolio risk limit in the constitution. **Resolution:** Either (a) reduce the USO spread to 1 contract ($160 max loss, combined $360), or (b) this trade REPLACES one of the three SPY positions rather than being added as a fourth. See Constitution Compliance section below.

---

## CONSTITUTION COMPLIANCE

### Position Sizing Decision Tree (Section 1)

```
Proposed trade max loss > $200?  --> $320 > $200. FAILS.
```

**This trade violates the $200 max risk per position rule at 2 contracts.**

### Resolution Options

**Option A: Reduce to 1 contract ($160 max loss)**

| Field | Value |
|---|---|
| Structure | Buy 1x USO May 16 $80C / Sell 1x USO May 16 $86C |
| Total debit | ~$160 |
| Max profit | $440 ($600 spread value - $160 debit) |
| R:R | 1:2.75 |

This passes all constitution checks. $160 < $200. But it limits the upside to $440.

**Option B: Tighter spread, 2 contracts ($80/$84, $4 wide)**

| Field | Value |
|---|---|
| Structure | Buy 2x USO May 16 $80C / Sell 2x USO May 16 $84C |
| Total debit | ~$220-240 |
| Max profit | ~$560-580 |

Still fails $200 limit. Need 1 contract: $110-120 debit, $280 max profit. Workable but thin.

**Option C: This trade IS the Category 3 hedge (replaces SPY call spread)**

The Correlation Budget (W1-06) mandates a Category 3 anti-correlation hedge. The current plan uses a SPY call debit spread ($682C/$692C) for ~$80-130. The USO call spread serves the same portfolio function -- it profits when the bearish thesis is wrong about TIMING (ceasefire holds a few more weeks but eventually collapses) while the SPY puts bleed.

But wait: the USO call spread does NOT profit if the ceasefire truly holds and SPY rallies. It profits when oil spikes regardless of equity direction. So it is not a pure hedge against "thesis wrong" -- it is a hedge against "thesis right on direction, wrong on transmission mechanism."

This is a subtler and arguably MORE VALUABLE hedge than the SPY call spread. The SPY call hedge says "maybe stocks go up." The USO call hedge says "even if stocks don't react to the ceasefire collapse, the oil market will."

**RECOMMENDATION: Option A (1 contract at $160 risk) as a supplementary position, OR replace the Category 3 SPY call spread with this.**

If replacing Category 3: the correlation budget allows $80-130 for the hedge. The USO spread at 1 contract ($160) is $30 over the upper bound. Either negotiate with the Risk Constitution (unlikely to be granted) or use the tighter $80/$84 spread at 1 contract (~$110-120 debit, within the $80-130 Category 3 budget).

---

## TRADE MANAGEMENT

### Rule 1: Entry Timing

Enter Monday April 7 between 10:30-11:00 AM ET. Crude oil trades nearly 24 hours (futures open Sunday 6 PM ET), so by Monday morning the weekend news is already priced into /CL. USO opens at 9:30 AM but tracks the already-moved /CL price. There is no "gap" to wait for in USO the way there is in SPY.

However: if oil has ALREADY spiked above $100 over the weekend (ceasefire violation headlines), do NOT chase. The easy 6% is gone. Wait for a pullback to $96-98 before entering, or reduce size to 1 contract on the $80/$86 spread (breakeven moves higher but you're buying an already-confirmed thesis).

### Rule 2: Stop Loss

This is a debit spread. Max loss = debit paid ($160 at 1 contract, $320 at 2). There is no danger zone like the backspread. The hard stop IS the debit.

However, a TIME stop applies: if by April 25 (20 DTE remaining) crude oil has not moved above $98, close the position for whatever residual value remains (likely $40-80). The thesis requires a catalyst within the first 2-3 weeks. If 18 days pass with oil flat at $94, the ceasefire is holding better than expected and your premium is decaying.

### Rule 3: Take Profit

**50% max profit rule (per constitution Section 4):** Max profit per spread is $440 (at 1 contract) or $880 (at 2). The 50% target:
- 1 contract: close at +$220 profit (spread trading at ~$3.80, crude at ~$103-105)
- 2 contracts: close at +$440 profit (same crude level)

Crude oil at $103-105 is a 10-12% bounce from $94. This is the MINIMUM move you'd expect from a credible ceasefire violation. If you hit this level, take the money. Don't hold for $112. The constitution says the last 50% of profit costs 90% of the risk.

**Exception:** If crude is at $105 AND accelerating (VIX spiking, Hormuz confirmed closed, tanker insurance rates doubling), hold to $108-110 but move the stop to breakeven ($80 on 1 contract, $160 on 2). Let the remaining profit run with house money.

### Rule 4: Ceasefire Confirmed = Close Immediately

If the Islamabad talks Saturday April 11 produce a genuine framework AND ships begin transiting Hormuz in volume (50+ in 48 hours), close the USO spread Monday April 14 at market open. The thesis is dead. Do not wait for oil to drift lower -- close into the first liquidity window.

### Rule 5: Correlation with SPY Positions

If you hold both SPY puts AND USO calls, and the ceasefire collapses:
- SPY puts will be printing
- USO calls will be printing
- You now have concentrated "ceasefire collapse" exposure across two assets

**Portfolio-level trailing stop:** If combined P&L across SPY puts + USO calls exceeds +$500, move a mental stop at +$250 on the combined position. Give back half, keep half. Do not let a winning portfolio trade turn into a scratch because you held too long on both sides.

### Rule 6: Contango Risk (USO-Specific)

USO holds front-month WTI futures and rolls monthly. In contango (front-month cheaper than back-month), USO loses value on each roll. For a 39-DTE hold, you'll experience at most one roll cycle. In the current backwardated crude market (near-term scarcity premium from Hormuz), contango drag is minimal. But if the curve flips to contango (ceasefire holds, supply normalizes), USO will underperform /CL by 0.5-1.5% per month.

This is a second-order effect. For a 39-DTE options trade, the contango drag on USO NAV is ~$0.50-1.00 on the shares -- immaterial compared to the $6 spread width. Ignore it unless you're holding through multiple roll cycles (you shouldn't be -- time stop at 20 DTE).

---

## THE PAIR TRADE THESIS (Advanced, For Borey's Consideration)

If Borey approves BOTH this and a SPY bear put spread, the combined position creates something the swarm hasn't built: a **ceasefire collapse portfolio** with two uncorrelated profit drivers.

### The Structure

| Position | Risk | Profits When | Loses When |
|---|---|---|---|
| SPY $678P/$665P bear put spread | $130 | SPY drops (gap fill) | SPY rallies or chops |
| USO $80C/$86C bull call spread | $160 | Oil spikes (Hormuz) | Oil flat or drops |
| **Combined** | **$290** | **Ceasefire collapses** | **Ceasefire holds** |

### Why This Is Better Than Two SPY Positions

Two SPY bearish positions have correlation ~0.95. If SPY rallies, BOTH lose. Your portfolio loss is concentrated.

SPY puts + USO calls have correlation ~0.40-0.60 in the ceasefire-collapse scenario (both win) but correlation ~0.10-0.30 in the neutral/chop scenario (oil can move independently of equities on OPEC news, inventory data, tanker insurance changes).

The lower correlation in the neutral scenario means your expected loss in "nothing happens" is smaller:
- Two SPY bearish trades in chop: both bleed theta, combined loss $150-300
- SPY bearish + USO calls in chop: SPY bleeds, but USO might catch an independent oil catalyst (Iran internal power struggle, OPEC production cut, refinery outage), partial offset

### Scenario P&L (The Pair)

| Scenario | SPY Put Spread | USO Call Spread | Combined | vs. Two SPY Bearish |
|---|---|---|---|---|
| Ceasefire collapses, crash | +$400-600 | +$440 | **+$840-1,040** | +$700-900 (similar) |
| Ceasefire collapses, chop | -$130 | +$300-440 | **+$170-310** | -$260 (BOTH lose) |
| Ceasefire holds, rally | -$130 | -$160 | **-$290** | -$260 (similar) |
| Chop, nothing happens | -$100 | -$80 | **-$180** | -$200 (slightly worse) |
| Hot CPI, oil up, SPY down | +$300 | +$200 | **+$500** | +$400 (similar) |

**Row 2 is the money row.** The scenario where the ceasefire collapses but equities don't react much (maybe the market was already pricing it in, maybe a Fed pivot offsets it). In this scenario, the pair trade makes +$170-310 while the pure SPY portfolio loses -$260. That's a $430-570 swing in your favor.

This is the entire argument for the oil proxy trade in one row.

---

## WHAT BOREY PROBABLY HASN'T CONSIDERED

### 1. Oil Moves First

When Hormuz last tightened (before the ceasefire), crude moved 2-3 days BEFORE SPY reacted. The transmission chain: tanker insurance -> shipping rates -> crude futures -> inflation expectations -> equity repricing. Oil is the canary. By the time SPY drops, oil has already moved 5-8%.

An oil position captures the FAST money. SPY captures the slow money. Both capture the SAME catalyst but on different timelines. You can ride the oil move while the SPY move is still building.

### 2. Oil Has Binary Optionality That Stocks Don't

SPY at 678 can go to 670 or 685. That's +-1%. The distribution is roughly normal.

Crude at $94 can ONLY go two ways from here:
- Ceasefire holds: slow drift to $85-88 (6-10% down, GRADUAL)
- Ceasefire collapses: snap to $110-120 (17-28% up, FAST)

The distribution is bimodal, not normal. Options on bimodal assets are structurally underpriced by Black-Scholes (which assumes normal distribution). The $80 call is priced assuming crude has a smooth probability distribution around $94. In reality, crude is far more likely to be at either $88 or $112 in 3 weeks than at $94. The tails are fat, and you're buying the right tail.

### 3. The "Sell The Ceasefire" Trade Is Crowded in Equities, NOT in Oil

Everyone on FinTwit is buying SPY puts. The put skew is bid (acknowledged in W1-03-market-context.md). You're paying extra for the crowded equity bet.

Far fewer retail traders are buying USO calls. Oil options are a different market: dominated by commercial hedgers (airlines, refiners, producers) and commodity CTAs. Retail is underrepresented. The put/call skew in USO is set by oil fundamentals, not by Twitter sentiment. You're likely getting a fairer price in USO than in SPY.

### 4. This Survives The "I Was Right But Lost Money" Scenario

The Do-Nothing Case (W1-07) warned about the specific nightmare: "Gil is right about direction, wrong about timing, options expire worthless."

USO calls partially escape this. Even if the ceasefire collapse is delayed 2 weeks beyond your SPY option expiry, oil will be the FIRST thing to react when it finally happens. The 39 DTE on the USO spread gives you 5+ weeks of runway. You can be right about direction and STILL make money even if the timing is 3-4 weeks off.

SPY weeklies can't do this. SPY weeklies die on Friday regardless of whether the ceasefire collapses on Saturday.

---

## RISKS AND HONEST WEAKNESSES

### 1. USO Is Not Pure Crude Oil

USO holds front-month futures. It suffers from contango roll costs, management fees (0.60%), and tracking error. For moves of 15%+ in crude, USO will capture 85-95% of the move. For small moves of 2-3%, USO might capture only 70-80%. This trade needs a BIG move to work, not a small one.

### 2. If Ceasefire Holds, This Loses Everything

Unlike the SPY call spread hedge that profits on a rally, the USO call spread ONLY profits if oil goes up. If the ceasefire holds AND oil drifts lower, you lose the full $160-320 debit. There is no "wrong but still make money" path with this trade. It is a directional bet on oil, full stop.

### 3. Crude Oil Can Be Irrational

Oil can stay at $94 even if the ceasefire is visibly failing, because:
- Strategic Petroleum Reserve (SPR) releases can cap price
- OPEC+ can increase production (though they've been reluctant)
- A global demand slowdown (China recession) can offset supply fear
- The US can waive Iran sanctions to prevent oil spikes in an election-adjacent year

These are all real risks. They don't invalidate the thesis but they can delay or dampen the move.

### 4. Liquidity Risk

USO options are liquid on monthly expiries but the bid-ask is wider than SPY. Expect to give up $0.05-0.10 on entry and exit each. On a $160 position, that's 3-6% slippage -- meaningful but not disqualifying. Use limit orders and be patient.

### 5. This Adds Account Risk

If this is a 4th position (added alongside 3 SPY trades), it violates the "max 3 positions" rule. If it replaces a position, you lose that position's edge. There is no free lunch. The oil trade adds value only if it replaces correlated SPY exposure, not if it's stacked on top.

---

## ENTRY CHECKLIST

1. [ ] **Check crude oil price at 10:00 AM ET Monday.** If oil is already above $100: do NOT enter. The move has started without you and you'd be chasing.
2. [ ] **If oil is $92-97 (near current):** Enter 1x USO $80C/$86C spread at the mid, limit $1.60. Walk to $1.70 after 15 minutes. Max $1.75.
3. [ ] **If oil has dropped below $90 (ceasefire strengthening):** Skip this trade entirely. The thesis is weakening.
4. [ ] **Confirm USO options chain:** Verify May 16 expiry exists and has open interest > 500 on both the $80C and $86C. If OI is thin, use the $79C/$85C instead (adjust debit estimate).
5. [ ] **Set alerts:**
   - [ ] Crude oil $100 (profit zone entry)
   - [ ] Crude oil $105 (50% max profit zone -- evaluate exit)
   - [ ] Crude oil $88 (thesis weakening -- evaluate time stop acceleration)
   - [ ] April 25 (time stop -- close if crude below $98)

---

## POSITION SUMMARY

| Field | Value (1 contract) | Value (2 contracts) |
|---|---|---|
| Structure | Buy 1x USO May 16 $80C / Sell 1x USO May 16 $86C | Buy 2x USO May 16 $80C / Sell 2x USO May 16 $86C |
| Underlying | USO (~$78), tracking WTI crude (~$94) |  |
| Expiry | May 16, 2026 (39 DTE) |  |
| Net debit | ~$160 | ~$320 |
| Max loss | $160 (1.6% of account) | $320 (3.2% -- VIOLATES constitution) |
| Max profit | $440 | $880 |
| Breakeven | USO ~$81.60 (crude ~$98) | Same |
| R:R | 1:2.75 | 1:2.75 |
| 50% profit target | Close at +$220 (crude ~$103) | Close at +$440 (crude ~$103) |
| Time stop | Close by Apr 25 if crude < $98 | Same |
| Thesis | Ceasefire collapse -> Hormuz re-closure -> oil snaps back to $110+ |  |
| Correlation to SPY puts | LOW in neutral/chop, HIGH in collapse | Same |
| Greek profile | Long delta (~+0.38), long vega (benefits from crude IV spike), slightly negative theta | Same |

---

## CONSTITUTION-COMPLIANT RECOMMENDATION

**1 contract of the USO $80C/$86C May 16 call spread at ~$1.60 ($160 debit).**

- $160 < $200 max risk per position. PASSES.
- If added as a 3rd position (alongside 1 SPY bear put spread + 1 SPY neutral/theta): total risk $290 + $160 = $450 < $500. PASSES.
- Provides genuine decorrelation from SPY positions (different underlying, different market, different catalyst timing).
- 39 DTE provides timing buffer that weekly SPY options cannot.
- R:R of 1:2.75 on a realistic thesis (oil to $103-108 = pre-ceasefire levels).

This is not the sexiest trade in the portfolio. It is not a 1:51 crash lottery ticket. It is a 1:2.75 workhorse that profits from the most direct expression of the thesis (oil goes up when Hormuz closes) on the asset that moves first, with lower correlation to everything else in the book.

**The novel contribution: this is the only position across all 40+ proposals in V1/V2/V3 that profits from the Iran thesis on a non-equity instrument.** It is the only position where "ceasefire collapses but SPY doesn't react" still makes money. It is the position the swarm should have proposed first and didn't.

---

*"When the thesis is about oil, trade oil. When the thesis is about stocks, trade stocks. When the thesis is about oil but you only trade stocks, you are one abstraction layer too far from the primary signal."*
