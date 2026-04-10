# W2-06: Broken Wing Put Butterfly

**Date:** 2026-04-06 (Sunday analysis, Monday entry)
**Underlying:** SPY @ $678.00
**Structure:** Put BWB 675/665/652
**Expiry:** Friday 2026-04-11 (5 DTE at entry)
**Regime:** Fear (VIX ~20, Iran Supreme Leader coma, 31 militaries mobilized, ceasefire structurally unenforceable)

---

## Thesis

Gap fill to ~$661 is the base case. Geopolitical tail risk (Iran escalation) creates asymmetric downside potential that a standard butterfly can't capture. The broken wing structure trades a wider max-loss corridor below $652 for reduced entry cost and higher reward:risk ratio. Body at $665 gamma floor exploits dealer hedging dynamics -- short gamma dealers accelerate selling into the pin zone, creating a magnet effect that increases the probability of touching max profit.

The skip wing at $652 (vs symmetric $655) accomplishes three things:
1. Reduces net debit from $167.66 to $141.90 (-15%)
2. Improves reward:risk from 5.0:1 to 6.0:1
3. Shifts the lower breakeven down only marginally ($656.68 to $656.42)
4. Accepts $441.90 max downside loss (vs $167.66 symmetric) below $652 -- a 4.2% move from spot that requires a genuine crash scenario

---

## Structure Comparison (all priced via BS with skew-adjusted IV, fear regime)

### Structure A: 675/665/655 (Symmetric 10/10)

| | Strike | IV | Premium | Action | Qty |
|---|--------|------|---------|--------|-----|
| Upper wing | 675P | 23.10% | $5.72 | Buy | 1 |
| Body | 665P | 23.13% | $2.44 | Sell | 2 |
| Lower wing | 655P | 23.16% | $0.83 | Buy | 1 |

- **Net debit:** $1.68/sh = **$167.66/contract**
- **Max profit:** $832.34 (at $665)
- **Max loss:** $167.66 (both directions -- defined risk)
- **Reward:risk:** 5.0:1
- **Breakevens:** $656.68 / $673.32

### Structure B: 675/665/652 (BWB +3 skip) -- RECOMMENDED

| | Strike | IV | Premium | Action | Qty |
|---|--------|------|---------|--------|-----|
| Upper wing | 675P | 23.10% | $5.72 | Buy | 1 |
| Body | 665P | 23.13% | $2.44 | Sell | 2 |
| Lower wing | 652P | 23.17% | $0.57 | Buy | 1 |

- **Net debit:** $1.42/sh = **$141.90/contract**
- **Max profit:** $858.10 (at $665)
- **Max loss upside:** $141.90 (above $675 -- just the debit)
- **Max loss downside:** $441.90 (at and below $652)
- **Reward:risk (vs debit):** 6.0:1
- **Breakevens:** $656.42 / $673.58
- **Profit zone:** $656.42 - $673.58 ($17.16 wide)

### Structure C: 675/665/650 (BWB +5 skip)

| | Strike | IV | Premium | Action | Qty |
|---|--------|------|---------|--------|-----|
| Upper wing | 675P | 23.10% | $5.72 | Buy | 1 |
| Body | 665P | 23.13% | $2.44 | Sell | 2 |
| Lower wing | 650P | 23.18% | $0.44 | Buy | 1 |

- **Net debit:** $1.29/sh = **$128.75/contract**
- **Max profit:** $871.25 (at $665)
- **Max loss upside:** $128.75
- **Max loss downside:** $628.75
- **Reward:risk (vs debit):** 6.8:1
- **Breakevens:** $656.29 / $673.71

**Why B over C:** Structure C saves only $13/contract but adds $187 of downside tail risk. In a fear regime with Iran escalation, the probability of a 4.2% crash (B's blow-through at $652) is already non-trivial at 3.2%. A 4.8% crash (C's blow-through at $650) is only marginally less likely at 2.8%. The extra $187 of exposure isn't worth $13 of savings when the geopolitical catalyst is specifically a tail-risk event.

---

## GEX Alignment

| GEX Level | Strike | Role in Structure |
|---|---|---|
| Gamma ceiling | $685 | Above position -- if SPY stays here, full loss (debit only) |
| Gamma flip | $678 | Current spot, entry point. Neutral GEX zone |
| Max pain | $675 | **Upper wing** -- gravitational pull from MM hedging |
| Gamma floor | $665 | **Body (2x short)** -- dealer short-gamma accelerates pin |
| Gap fill target | ~$661 | Deep in profit zone ($558/contract at expiry) |

**Dealer mechanics at $665:** Below the gamma flip, dealers are short gamma on puts. As SPY approaches $665, dealers must sell futures to hedge their put exposure, which accelerates the move toward the body. Once AT $665, gamma peaks -- dealers are maximally hedging, creating a sticky/pinning effect. This is exactly where our 2x short puts sit. The gamma floor acts as a volatility attractor that benefits the butterfly's peaked payoff.

---

## Greeks at Entry (per 1 contract, x100 multiplier applied)

### Per-Leg Greeks

| Leg | Delta | Gamma | Theta ($/day) | Vega ($/1% IV) |
|---|---|---|---|---|
| Buy 1x 675P | -42.10 | +2.133 | -$68.27 | +$31.04 |
| Sell 2x 665P | -22.65 ea | +1.640 ea | -$53.42 ea | +$23.89 ea |
| Buy 1x 652P | -6.98 | +0.729 | -$24.07 | +$10.63 |

### Net Position Greeks

| Greek | Value | Interpretation |
|---|---|---|
| **Delta** | **-3.78** | Slightly bearish. Equivalent to being short ~3.8 shares of SPY |
| **Gamma** | **-0.4181** | Short gamma -- position benefits from SPY NOT moving once near body |
| **Theta** | **+$14.50/day** | Positive theta. Collecting $14.50/day in time decay at current spot |
| **Vega** | **-$6.11** | Short vega. Position LOSES $6.11 for every 1% IV increase |

### Greek Interpretation

- **Negative delta (-3.78):** The position wants SPY to decline toward the body at $665. Delta is modest -- this isn't a directional bet so much as a zone bet.
- **Negative gamma (-0.42):** Once SPY is near the body, gamma works against you on further moves. This is the tradeoff for the peaked payoff structure. Gamma becomes increasingly negative as SPY approaches $665, peaking at -0.83 right at the body.
- **Positive theta (+$14.50):** Strong theta tailwind. With 5 DTE of short-dated puts, time decay is aggressive. This position earns ~$14.50/day just from the passage of time while SPY stays near current levels.
- **Negative vega (-$6.11):** Iran escalation = VIX spike = this position loses money from vega alone. A VIX spike to 30 at DTE=3 puts every spot level underwater. **This is the primary risk vector.** See IV sensitivity table below.

---

## Delta/Gamma Evolution as SPY Approaches Body

This table shows how the position's Greeks shift as SPY moves toward the body. Critical for understanding when to manage.

| SPY | Position Delta | Position Gamma | Regime |
|---|---|---|---|
| $690 | -5.30 | +0.11 | Far above -- small short delta, slightly long gamma |
| $685 | -5.44 | -0.07 | Gamma ceiling. Delta bearish, gamma flipping short |
| $680 | -4.51 | -0.31 | Approaching upper wing. Gamma accelerating negative |
| **$678** | **-3.78** | **-0.42** | **ENTRY. Moderate short delta, short gamma building** |
| $675 | -2.29 | -0.57 | Upper wing strike. Delta shrinking, gamma intensifying |
| $672 | -0.37 | -0.70 | Approaching profit zone. Near delta-neutral |
| $670 | +1.11 | -0.77 | **Delta flips positive.** Position now wants SPY to stop falling |
| $668 | +2.70 | -0.82 | Deep in profit zone. Strong short gamma = position resists further moves |
| **$665** | **+5.19** | **-0.83** | **BODY. Max short gamma. Delta now wants SPY to bounce.** |
| $662 | +7.64 | -0.79 | Through body. Delta positive and accelerating -- wants reversal |
| $660 | +9.16 | -0.72 | Gap fill zone. P&L still excellent but delta fighting you |
| $655 | +12.17 | -0.46 | Approaching lower breakeven. Delta very positive |
| $650 | +13.63 | -0.12 | Below lower wing. Gamma flattening -- P&L capped at max loss |

**Key insight:** At $665 (body), the position has +5.19 delta. It is now LONG delta -- the position wants SPY to stop falling or bounce. This is the natural management signal. If SPY pins at $665 into expiry, you collect maximum profit. If it crashes through, the +5 delta and -0.83 gamma mean your P&L deteriorates rapidly below the lower breakeven.

---

## Full P&L Curve at Expiry ($2 intervals)

| SPY at Expiry | P&L per Contract | Zone |
|---|---|---|
| $648 | **-$441.90** | Max loss (below lower wing) |
| $650 | -$441.90 | Max loss |
| $652 | -$441.90 | Lower wing strike -- max loss locks in |
| $654 | -$241.90 | Recovering |
| **$656** | **-$41.90** | Near lower breakeven ($656.42) |
| $658 | +$158.10 | Profit zone |
| $660 | +$358.10 | Gap fill area |
| $662 | +$558.10 | Strong profit |
| $664 | +$758.10 | Near max profit |
| **$665** | **+$858.10** | **MAX PROFIT (body)** |
| $666 | +$758.10 | Near max profit |
| $668 | +$558.10 | Profit zone |
| $670 | +$358.10 | Profit zone |
| $672 | +$158.10 | Near upper breakeven |
| **$674** | **-$41.90** | Near upper breakeven ($673.58) |
| $676 | -$141.90 | Max loss upside |
| $678 | -$141.90 | Current spot -- full loss if SPY doesn't move |
| $680 | -$141.90 | |
| $682 | -$141.90 | |
| $684 | -$141.90 | |
| $686 | -$141.90 | |
| $688 | -$141.90 | |
| $690 | -$141.90 | |

**Profit zone width:** $656.42 to $673.58 = **$17.16** (2.5% of spot)

---

## P&L Surface Across DTE (Mark-to-Market)

### DTE=5 (Entry Day)

Position is nearly flat at entry. Theta hasn't kicked in yet.

| SPY | P&L | | SPY | P&L |
|---|---|---|---|---|
| $650 | -$159 | | $666 | +$3 |
| $655 | -$93 | | $668 | +$10 |
| $660 | -$38 | | $670 | +$13 |
| $662 | -$21 | | $672 | +$14 |
| $664 | -$7 | | $675 | +$7 |
| $665 | -$2 | | $678 | $0 |

### DTE=3 (Wednesday -- Decision Point)

| SPY | P&L | Notes |
|---|---|---|
| $650 | -$160 | Approaching max downside loss |
| $655 | -$65 | |
| $660 | +$14 | Gap fill: profitable |
| $665 | +$62 | Body: $62 profit (7% of max) |
| $668 | +$72 | **Sweet spot at DTE=3** |
| $670 | +$72 | |
| $675 | +$50 | |
| $678 | +$27 | If SPY flat, theta earned ~$27 |

### DTE=2 (Thursday)

| SPY | P&L | Notes |
|---|---|---|
| $650 | -$171 | |
| $655 | -$70 | |
| $660 | +$62 | |
| $665 | +$127 | Body approaching par |
| $668 | +$129 | **Peak MTM at DTE=2** |
| $670 | +$123 | |
| $675 | +$64 | |
| $678 | +$38 | Solid theta capture even if flat |

### DTE=1 (Friday Morning)

| SPY | P&L | Notes |
|---|---|---|
| $650 | -$218 | |
| $655 | -$69 | |
| $658 | +$87 | |
| $660 | +$154 | Gap fill |
| $665 | +$247 | **Near max profit if holding to close** |
| $668 | +$238 | |
| $670 | +$211 | |
| $675 | +$73 | |
| $678 | +$26 | |

### Expiry (Friday Close)

Intrinsic only. See full P&L curve table above. Max profit $858 at $665, max loss $442 below $652.

---

## IV Sensitivity (P&L at DTE=3 for various VIX levels)

**This is the kill zone for the trade.** Negative vega means a VIX spike destroys P&L even if SPY moves to the body.

| SPY | VIX 18 | VIX 20 | VIX 22 | VIX 25 | VIX 30 | VIX 35 |
|---|---|---|---|---|---|---|
| $650 | -$163 | -$160 | -$159 | -$160 | -$167 | -$175 |
| $655 | -$54 | -$65 | -$76 | -$91 | -$113 | -$132 |
| $660 | +$37 | +$14 | -$7 | -$33 | -$68 | -$95 |
| **$665** | **+$90** | **+$62** | **+$37** | **+$6** | **-$36** | **-$67** |
| $670 | +$96 | +$72 | +$50 | +$21 | -$19 | -$50 |
| $675 | +$63 | +$50 | +$36 | +$15 | -$16 | -$43 |
| $678 | +$33 | +$27 | +$19 | +$5 | -$19 | -$43 |

**Critical observation:** At VIX 25 (only +25% from current), the position at the BODY ($665) earns only +$6. At VIX 30, it's -$36 even at max-profit spot. **If Iran escalation triggers a VIX spike above 25, this trade is underwater everywhere regardless of spot.** The play only works if SPY drops to the body on orderly selling/gap-fill mechanics, not on a panic VIX spike.

**This is the fundamental tension of the trade:** The thesis (Iran escalation, gap fill) implies rising volatility, but the structure (short vega butterfly) needs stable/declining vol to profit at DTE=3. Resolution: the butterfly works if SPY drops *slowly* over 3-4 days with VIX staying in the 20-22 range, then pins near $665 as theta accelerates into expiry. It does NOT work if SPY gaps down $15 overnight on an Iran headline with VIX spiking to 30+.

---

## Management Zones

### Zone 1: SPY $685-$690 (Above Gamma Ceiling)

**Position status:** Full loss (debit only, $142).
**Delta:** -5.3 to -6.1 (still bearish, position alive).
**Action:** Hold. The position is cheap enough to let it run. Theta is slightly positive. No reason to exit unless thesis is dead.
**Exit if:** Thesis invalidated (ceasefire announced, Iran de-escalation). Close for ~$80-100 loss.

### Zone 2: SPY $678-$685 (Current Level to Gamma Ceiling)

**Position status:** Flat to small loss (-$142 to $0).
**Delta:** -3.8 to -5.4 (moderately bearish).
**Action:** **Patient hold.** You entered for this to move lower. Theta is earning +$14.50/day. Every day SPY stays here or drifts lower, the position improves. Monitor VIX -- if VIX spikes above 25 while SPY stays flat, consider reducing.
**Exit if:** VIX > 28 with SPY above $680 (vega crush exceeds theta benefit).

### Zone 3: SPY $673-$678 (Upper Wing Approach)

**Position status:** Small profit at DTE=3+ ($14-$42).
**Delta:** -2.3 to -3.8 (bearish decreasing).
**Action:** **Tighten awareness.** You're approaching the profit zone. Set alerts at $675 and $670. If SPY hits $673 with 3+ DTE remaining, the MTM will be +$66 at DTE=3. Consider taking 25-35% of max profit if you want to lock in.
**Partial exit:** Close half at $670 for ~+$70/contract (50% of debit recovered + profit).

### Zone 4: SPY $665-$673 (Profit Zone -- Upper Half)

**Position status:** Profitable ($62-$858 depending on DTE and exact spot).
**Delta:** -0.37 to +5.19 (transitioning from bearish to bullish -- the position now wants SPY to STOP and PIN).
**Gamma:** -0.70 to -0.83 (deeply short gamma -- rapid P&L change on moves).
**Action:** **Active management required.**
- **DTE >= 3:** Consider closing 50% at +$60-80/contract. You've captured 40-55% of max profit with 3 days of gamma risk remaining. The vega risk from a sudden VIX spike is real.
- **DTE = 2:** If SPY is at $665-670, you're sitting on +$93-$129. This is the sweet spot -- theta is massively in your favor. Hold if VIX < 23. Close if VIX > 25.
- **DTE = 1:** If you held to here and SPY is 665-670, you're at +$204-$248. Take 75%+ off here. The last-day gamma risk is extreme.

### Zone 5: SPY $656-$665 (Profit Zone -- Lower Half, Through Body)

**Position status:** Profitable on the upper side, approaching lower breakeven.
**Delta:** +5.19 to +12.17 (strongly positive -- position wants reversal NOW).
**Action:** **Close or hedge.** At $665, you're at max profit ($858 at expiry). Every dollar below $665 costs you $100/contract. At $656.42 you're breakeven. This is NOT a zone to hold and hope.
- **At $665:** Close 75-100% of position. You've won.
- **At $660:** Still +$358 at expiry, but if it's DTE=3 you only have +$14 MTM. The theta runway is your friend but gamma is your enemy. Close at least half.
- **At $656:** Near breakeven. If DTE > 2, the MTM is still negative (BS time value). Close everything.

### Zone 6: SPY $652-$656 (Danger Zone)

**Position status:** Breakeven to significant loss.
**Delta:** +12.17 to +13.63 (position urgently wants bounce).
**Gamma:** Flattening (-0.46 to -0.12).
**Action:** **CLOSE IMMEDIATELY.** Below $656.42, you're in the broken wing loss corridor. Max loss of $441.90 locks in at $652 and below. Do not try to "ride it back." The thesis was a controlled gap fill, not a crash.

### Zone 7: SPY < $652 (Below Lower Wing -- Max Loss)

**Position status:** Locked at -$441.90 per contract.
**Action:** Nothing to do. P&L is frozen. The lower wing protects from further loss below $652 (unlike a naked short, the bought 652P caps it). Lesson: the skip wing accepted this risk in exchange for cheaper entry.

---

## Monte Carlo Probability Profile (200K paths, fear regime jump-diffusion)

| Metric | Value |
|---|---|
| **Prob profit** | **27.9%** |
| Expected P&L | +$8.30/contract |
| Median P&L | -$141.90 (most paths: SPY stays above $675, lose debit) |
| P01 (worst 1%) | -$441.90 |
| P05 | -$141.90 |
| P10 | -$141.90 |
| P25 | -$141.90 |
| P50 (median) | -$141.90 |
| P75 | +$86.88 |
| P90 | +$541.88 |
| P95 | +$697.59 |
| P99 | +$826.01 |

### Zone Probabilities

| Zone | Probability | Avg P&L | Description |
|---|---|---|---|
| Above $675 | 62.9% | -$141.90 | Lose debit. Most likely outcome. |
| $665-$675 | 23.9% | +$304.45 | **Profit zone upper half.** |
| ~$665 +/- 1 | 3.1% | +$808.30 | Near max profit |
| $652-$665 | 9.9% | +$393.00 | **Profit zone lower half** |
| Below $652 | 3.2% | -$441.90 | Max downside loss |

### Terminal Spot Distribution

| Probability | SPY Level |
|---|---|
| SPY < $665 | 13.1% |
| SPY < $661 (gap fill) | 8.1% |
| SPY < $655 | 4.2% |
| SPY < $652 (blow-through) | 3.2% |
| SPY in $655-$675 | 32.9% |
| SPY in $660-$670 (sweet spot) | 16.0% |

**Positive expected value:** +$8.30/contract. The trade has positive EV under fear-regime jump diffusion because the peaked payoff in the profit zone ($304-$808) more than compensates for the frequent small losses ($142 debit) when SPY stays above $675. The 3.2% crash probability that costs $442 is the drag, but it's not enough to make the trade negative EV.

---

## Risk Inventory

| Risk | Severity | Probability | Mitigation |
|---|---|---|---|
| **VIX spike to 25+** while SPY in transit | **HIGH** | Moderate | Close at DTE=3 if VIX > 25. Butterfly is short vega -- a 10-point VIX spike wipes out $60-100 of P&L even at the body. |
| **Iran overnight gap** through $652 | HIGH | Low (~3.2%) | Accept. The $441.90 max loss is the price of the skip wing. Size accordingly (see sizing below). |
| **SPY pins at $678** (no move) | MEDIUM | ~25% | Lose $141.90 debit. Acceptable. This is the "cost of being wrong" and it's small. |
| **SPY rallies above $685** | LOW | ~30% | Same $141.90 loss. Defined risk upside. |
| **Expiry pin risk** at $665 | LOW-MED | 3% | If SPY is at $665 on Friday, the 2x short 665P will be right at the money. Assignment risk on the short puts. Close before 3:30 PM ET if SPY is within $1 of $665. |
| **Wide bid-ask on entry** | MEDIUM | Certain | Butterfly orders on SPY typically have $0.10-0.20 wide markets per leg. Use a limit order on the net debit. Target $1.40-1.50 net. Don't pay more than $1.60 or the risk/reward degrades. |

---

## Entry Protocol

1. **Pre-market Monday:** Check VIX level. If VIX has spiked to 25+ over the weekend (Iran escalation), the butterfly is mispriced against you. Either wait for VIX to settle or switch to a put debit spread that benefits from continued vol expansion.

2. **First 15 minutes:** Do not enter. Let the opening auction settle. Watch for gap direction.

3. **Entry window:** 9:45 AM - 10:30 AM ET. Place the butterfly as a single order (not legging in). Target net debit of $1.40-1.50.

4. **Fill quality check:** If best fill is > $1.60 net debit, reduce to 1 contract or walk away. At $1.60, max profit drops to $840 and reward:risk falls to 5.25:1.

---

## Sizing Framework (Borey decides final size)

| Contracts | Max Risk Up | Max Risk Down | Max Profit | % of $10K Account at Risk |
|---|---|---|---|---|
| 1 | $142 | $442 | $858 | 4.4% downside |
| 2 | $284 | $884 | $1,716 | 8.8% downside |
| 3 | $426 | $1,326 | $2,574 | 13.3% downside |
| 5 | $710 | $2,210 | $4,290 | 22.1% downside |

**The relevant risk number is the downside max loss ($442/contract), not the debit.** The broken wing means you can lose more than you paid on a crash through $652. Size to the downside number.

---

## Key Levels Summary

| Level | Significance |
|---|---|
| **$690** | Above gamma ceiling. Full loss territory. |
| **$685** | Gamma ceiling. Position alive but losing. |
| **$678** | Current spot / gamma flip. Entry point. |
| **$675** | Max pain / upper wing. Start of profit zone approach. |
| **$673.58** | **Upper breakeven** |
| **$670** | Delta flips positive. Position now wants stability. |
| **$665** | **Gamma floor / body / MAX PROFIT** |
| **$661** | Gap fill target. +$558 at expiry. |
| **$656.42** | **Lower breakeven** |
| **$652** | Lower wing. Max downside loss locks in. |
| **$648** | Below wing. Loss capped at $441.90. |

---

## Model Notes

- All pricing via Black-Scholes with skew-adjusted IV per codebase (`src/analysis/combo_odds.py` skew model: log-moneyness slope = 0.10, fear regime near-term premium applied)
- Monte Carlo: 200K paths, Merton jump-diffusion, fear regime parameters (intensity=5.0, jump mean=-3%, jump std=5%, vol_ratio=0.78)
- Risk-free rate: 4.3% (10yr proxy)
- Greeks computed per-leg then netted. All per-contract values include x100 multiplier.
- P&L surfaces at DTE 1-5 use mark-to-market BS repricing with dynamic IV re-estimation at each spot level
- Terminal spot P05 = $656.74, P10 = $662.73 under fear regime -- gap fill to $661 is roughly a P10 event (10% probability)
