# Position 19: Coordinated Portfolio of Three -- Gap Fill Week

**Date drafted:** 2026-04-06 (Sunday)
**Market context:** SPX ~6783 after ceasefire gap from ~6610. SPY ~$678. VIX ~20. PCE Thursday 4/9, CPI Friday 4/10. Gap fill target: SPX ~6610 (SPY ~$661).
**Account:** $10,000
**Combined risk budget:** 3% = $300 maximum total portfolio loss
**Trader level:** New -- all positions must be defined-risk, no naked legs, no margin requirements beyond the debit paid

---

## Portfolio Design Philosophy

Most of the prior positions in this series are standalone trades. Each one makes a single bet. The problem: if you pick wrong, you lose. If you pick right but the timing is off, you still lose.

This portfolio takes a different approach. Three positions, each with a different job, different expiry, and different market condition where it pays off. No single scenario wipes out all three. At least one position is working in every plausible outcome.

The three roles:

| # | Role | Structure | Expiry | What It Needs |
|---|------|-----------|--------|---------------|
| A | Gap fill profit | Put debit spread | Apr 17 | SPY drops to 665-661 |
| B | Volatility expansion | Long strangle | Apr 10 | Big move in either direction |
| C | Income / cost reduction | Call credit spread | Apr 25 | SPY stays below 686 |

Different expiries (Apr 10, Apr 17, Apr 25) means you are never "all in" on one date. Different structures mean you are never "all in" on one thesis.

---

## POSITION A: "Gap Filler" -- Bear Put Debit Spread

**Role:** Directional bearish -- profits from the gap fill to ~661.

| Field | Detail |
|---|---|
| **Action** | BUY 1x SPY Apr 17 $674 Put / SELL 1x SPY Apr 17 $668 Put |
| **Entry** | Monday Apr 7, 10:00-10:30 AM ET |
| **Expiry** | Apr 17, 2026 (11 DTE) |
| **Width** | $6.00 |
| **Estimated debit** | ~$1.30 per spread ($130 per contract) |
| **Quantity** | 1 contract |
| **Max loss** | **$130** (debit paid, if SPY closes above $674 at expiry) |
| **Max profit** | **$470** ($600 width - $130 debit) if SPY at or below $668 at expiry |
| **Breakeven** | SPY at **$672.70** (674 - 1.30) |
| **Reward:Risk** | 3.6:1 |
| **Account risk** | 1.3% |

### Strike Logic

- **$674 long put:** 4 points OTM from ~$678. Close enough to gain value quickly on any weakness, but OTM enough to keep the debit under $1.50. The $674 level corresponds to last week's pre-gap consolidation zone.
- **$668 short put:** This is the halfway point between current price ($678) and the full gap fill ($661). Selling here means you collect max profit if SPY drops just 10 points -- you do not need the full gap fill to win. A partial retrace to $668 is much higher probability than a full fill to $661.
- **$6 width:** Wide enough for a meaningful payout ($470), narrow enough to keep the debit small ($130). This is a 3.6:1 reward-to-risk on a move that has strong historical precedent (70%+ gap fill rate for moves >2%).

### Why Apr 17

- Survives both PCE (Thu 4/9) and CPI (Fri 4/10), which are the most likely catalysts
- 11 DTE gives theta room to breathe -- you are not fighting 0DTE decay
- If the gap starts filling Monday-Wednesday, you can close early for 50-70% of max profit
- If the data releases trigger the move Thursday-Friday, you still have 5 more trading days as buffer

### Management

- **Take profit:** Close at $4.00 spread value (~$270 profit, ~60% of max) if SPY reaches $669-668 before Apr 15
- **Stop loss:** Close if spread drops to $0.65 (50% of entry), locking in a $65 loss instead of the full $130. This triggers if SPY rallies above $680 and holds for 2+ days
- **Time stop:** If SPY has not broken below $674 by Wednesday Apr 9 close, reduce to mental stop only and let PCE/CPI play out. If still above $674 after both data releases (Friday close), exit Monday Apr 13 at market

---

## POSITION B: "Catalyst Straddle Lite" -- Long Put + Long Call (Narrow Strangle)

**Role:** Volatility expansion -- profits from a big move in EITHER direction. This is the hedge that saves you if the gap fill thesis is wrong and SPY rips higher instead.

| Field | Detail |
|---|---|
| **Action** | BUY 1x SPY Apr 10 $680 Call + BUY 1x SPY Apr 10 $676 Put |
| **Entry** | Wednesday Apr 8, 3:00-3:45 PM ET (day before PCE) |
| **Expiry** | Apr 10, 2026 (Friday weekly, 2 DTE at entry) |
| **Strike separation** | $4 ($676 to $680) |
| **Estimated cost** | ~$1.60 for the call + ~$1.40 for the put = **$3.00 total ($300/contract)** |
| **Quantity** | HALF SIZE: see sizing note below |
| **Max loss** | **$100** (see sizing) |
| **Upside breakeven** | SPY > **$683.00** (+0.74%) |
| **Downside breakeven** | SPY < **$673.00** (-0.74%) |
| **Account risk** | 1.0% |

### Sizing Note -- Keeping Within $100 Risk

A full strangle at $3.00 costs $300 per contract, which alone would consume the entire $300 portfolio risk budget. The solution:

**Do NOT buy a full strangle.** Instead, choose ONE of these two approaches based on your Wednesday assessment:

- **Option 1 (preferred if you lean bearish):** Buy only the $676 Put for ~$1.40 ($140 cost). Set a stop-loss at $0.40 to cap loss at $100. If PCE is hot, the put prints. If PCE is cold and SPY rallies, you lose $100 max with the stop.
- **Option 2 (if you are genuinely uncertain):** Buy 1x mini-strangle by purchasing 1x $681 Call (~$1.20) + 1x $675 Put (~$1.10) = $2.30 total ($230). Set a stop-loss at $1.30 total value to cap loss at $100. Wider strikes, cheaper, but harder breakevens.

**Recommendation: Option 1. Buy the $676 Put for $140, stop at $0.40, max loss $100.** Here is why: Position A is already bearish. If the gap fill happens, you do not need a call. If SPY rallies instead, Position C (the credit spread) will be working in your favor. The portfolio already has upside defense through Position C. What the portfolio needs in Position B is a short-dated, high-gamma bearish kicker that amplifies the gap fill if PCE/CPI triggers it. A 2DTE put with high gamma is that kicker.

| Refined Position B | Detail |
|---|---|
| **Action** | BUY 1x SPY Apr 10 $676 Put |
| **Entry** | Wednesday Apr 8, 3:00-3:45 PM ET |
| **Expiry** | Apr 10, 2026 (2 DTE at entry) |
| **Cost** | ~$1.40 ($140 per contract) |
| **Quantity** | 1 contract |
| **Stop loss** | $0.40 (max realized loss = $100) |
| **Max profit** | Uncapped on downside. At SPY $668: put worth ~$8.00 = +$660. At SPY $661: put worth ~$15.00 = +$1,360. |
| **Breakeven** | SPY < $674.60 |

### Why Apr 10 (Not Apr 17)

- This is a GAMMA trade, not a direction trade. You want maximum convexity around the PCE/CPI releases
- 2 DTE options have the highest gamma per dollar of any expiry -- a $5 SPY move on PCE Thursday is worth $3-4 on this put, compared to $1.50-2.00 on the Apr 17 put
- The whole point is to capture a 1-2 day explosive move. If PCE/CPI are non-events, the put dies -- and that is fine because you capped the loss at $100 via the stop
- The Apr 10 expiry is different from Position A (Apr 17) and Position C (Apr 25), achieving the time diversification requirement

### Management

- **Pre-PCE (Thursday AM):** If SPY gaps down on overnight news before PCE, consider taking the put off at $3.00+ (120% gain). Do not hold into data if already profitable
- **Post-PCE (Thursday after 8:30 AM):** If PCE is hot and SPY drops below $674, hold the put into Friday for CPI. Trail the stop to breakeven ($1.40). You now have a free look at CPI
- **Post-PCE flat:** If SPY is between $675-$681 after PCE, the put is decaying fast. Close for whatever residual value exists. Do not hold a 1DTE put into CPI hoping for a miracle -- the theta is brutal
- **Stop loss:** If put value drops to $0.40 at any point, close. No exceptions. This is a $100 cap on a high-risk, high-reward kicker

---

## POSITION C: "Patience Premium" -- Bear Call Credit Spread

**Role:** Income generation and time decay -- collects premium while you wait for the gap fill thesis to develop. Also serves as the upside hedge: if SPY rallies, this is the only position that loses, but it is small and partially offset by theta already collected.

| Field | Detail |
|---|---|
| **Action** | SELL 1x SPY Apr 25 $686 Call / BUY 1x SPY Apr 25 $689 Call |
| **Entry** | Tuesday Apr 7, 10:00-10:30 AM ET (let Monday opening settle) |
| **Expiry** | Apr 25, 2026 (18 DTE) |
| **Width** | $3.00 |
| **Credit received** | ~$0.70 per spread ($70 per contract) |
| **Quantity** | 1 contract |
| **Max loss** | **$230** ($300 width - $70 credit) if SPY closes above $689 at Apr 25 expiry |
| **Max profit** | **$70** (full credit retained) if SPY closes below $686 at Apr 25 expiry |
| **Breakeven** | SPY at **$686.70** (short strike + credit) |
| **Prob of profit** | ~73-77% (based on $686 short call delta ~0.22-0.27 at 18 DTE) |
| **Account risk** | 2.3% gross, but actual realized risk is $70 with stop-loss discipline (see below) |

### Strike Logic

- **$686 short call:** SPY would need to rally 1.2% from $678 AND hold there for 18 days. With a VIX of 20, the implied move over 18 days is about +/- 4.5%, but the short strike only needs to hold for the credit to be yours. $686 is above the post-gap high, above round-number resistance at $685, and above the zone where ceasefire euphoria should exhaust.
- **$689 long call:** Caps risk at $3 width. The $689 level is 1.6% above current price -- deep into "ceasefire is permanently real" territory. This is the hedge that prevents unlimited loss.
- **$3 wide, $0.70 credit:** Risk/reward is 3.3:1 against you on paper ($230 risk for $70 reward), but the probability compensates. A 75% win rate on this structure yields positive expected value: (0.75 x $70) - (0.25 x $230) = $52.50 - $57.50 = roughly breakeven in theory. The real edge is portfolio-level: this position collects income while the bearish thesis develops.

### Why Apr 25

- **Furthest expiry in the portfolio:** Provides time diversification. If the gap fill happens fast (this week), Position C has 2+ weeks of additional theta decay to collect
- **Higher credit than Apr 17:** 18 DTE collects more premium than 11 DTE for the same strikes. The extra week of time value is worth ~$0.15-0.20 more credit
- **Survives a false rally:** If SPY pops to $683-684 mid-week on ceasefire momentum, the Apr 25 spread has time to recover. An Apr 11 credit spread at the same strikes would be under immediate pressure
- **Theta curve sweet spot:** 14-21 DTE is where theta acceleration begins on OTM options. Your short $686 call is decaying at ~$0.04-0.06/day at entry, accelerating to $0.08-0.12/day by Apr 18

### Management

- **Take profit at 50%:** If spread can be bought back for $0.35 or less, close it. Expected timeline: 5-8 days if SPY stays flat or drifts down. Do not hold for the last 50% -- gamma risk increases
- **Stop loss at 2x credit:** If spread rises to $1.40 (unrealized loss = $70), close immediately. Actual realized loss = $1.40 - $0.70 = $0.70 per contract = $70 loss. This hard stop keeps the realized loss at $70, well under the $230 max
- **If SPY breaks $685:** The short strike is threatened. Close the spread regardless of P&L. Do not wait for $686 -- close early to preserve capital
- **Time stop:** If still open at Apr 21 (Monday of expiry week) and SPY is between $683-$686, close for whatever is available. Do not hold a threatened credit spread into expiry week

---

## PORTFOLIO SUMMARY

| Position | Role | Structure | Expiry | Max Loss | Max Profit |
|----------|------|-----------|--------|----------|------------|
| A | Gap fill (bearish) | Put debit spread 674/668 | Apr 17 | $130 | $470 |
| B | Vol kicker (gamma) | Long 676 put | Apr 10 | $100 | Uncapped |
| C | Income (theta) | Call credit spread 686/689 | Apr 25 | $70* | $70 |
| **TOTAL** | | | | **$300** | |

*Position C max loss is $70 with the 2x credit stop-loss rule. Theoretical max without the stop is $230, but the stop is non-negotiable.

### Combined Risk: $300 = 3.0% of $10,000

- Position A: $130 (1.3%)
- Position B: $100 (1.0%) with stop
- Position C: $70 (0.7%) with stop
- **Total: $300 (3.0%)** -- exactly at the budget

---

## SCENARIO ANALYSIS: Combined P&L

### Scenario 1: Gap Fill to SPY ~$665-661 (Thesis Plays Out)

SPY drops 2-2.5% over the week, filling the gap. PCE or CPI is the catalyst.

| Position | Outcome | P&L |
|----------|---------|-----|
| A (put spread 674/668) | SPY below $668, spread at max value | **+$470** |
| B (676 put, Apr 10) | If triggered by PCE/CPI, put worth $11-15 | **+$960 to +$1,360** |
| C (call credit 686/689) | SPY well below $686, full credit retained | **+$70** |
| **COMBINED** | | **+$1,500 to +$1,900** |

This is the best case. All three positions win. The gamma kicker (B) amplifies returns because 2DTE puts explode in value on a sharp move. Position C's $70 is the cherry on top.

### Scenario 2: Rally Continues to SPY ~$690 (Thesis Fails -- Bull Case)

Ceasefire holds, PCE/CPI are soft, market rips to new highs. SPY rallies 1.8% to $690.

| Position | Outcome | P&L |
|----------|---------|-----|
| A (put spread 674/668) | Both puts expire worthless | **-$130** |
| B (676 put, Apr 10) | Stop triggers at $0.40 | **-$100** |
| C (call credit 686/689) | SPY above $689, spread at max loss WITH stop | **-$70** |
| **COMBINED** | | **-$300** |

This is the worst case. All three positions lose. But the combined loss is exactly $300 -- 3% of account. This is by design. Even the absolute worst scenario does not blow the budget because every position has a defined stop or defined max loss.

**Critical observation:** Without Position C's stop-loss discipline, the credit spread max loss would be $230 instead of $70, pushing total to $460 (4.6%). The stops are what make this portfolio work within the risk budget.

### Scenario 3: Chop at SPY ~$675-681 (Nothing Happens)

SPY goes nowhere. PCE inline, CPI inline. Market digests the gap and consolidates.

| Position | Outcome | P&L |
|----------|---------|-----|
| A (put spread 674/668) | SPY above $674 at Apr 17, spread expires worthless | **-$130** |
| B (676 put, Apr 10) | SPY above $676 at Apr 10, stop triggers or expires worthless | **-$100** |
| C (call credit 686/689) | SPY below $686, full credit retained | **+$70** |
| **COMBINED** | | **-$160** |

The chop scenario is a moderate loss. Positions A and B lose (no directional move), but Position C earns its full $70 credit because SPY never threatened $686. The income position partially offsets the directional losses. Total damage: $160, which is only 1.6% of the account. Very survivable.

### Scenario 4: Crash to SPY ~$640 (Black Swan / Ceasefire Collapses)

Ceasefire collapses entirely. Iran escalates. SPY crashes 5.6% in a panic selloff.

| Position | Outcome | P&L |
|----------|---------|-----|
| A (put spread 674/668) | SPY well below $668, spread at max value | **+$470** |
| B (676 put, Apr 10) | Put worth ~$36 ($676 - $640) | **+$3,460** |
| C (call credit 686/689) | SPY far below $686, full credit retained | **+$70** |
| **COMBINED** | | **+$4,000** |

The crash scenario is a windfall. Position B (the gamma kicker) becomes enormously valuable because a 2DTE put that is $36 in-the-money with VIX spiking to 35+ is worth a fortune. Position A reaches max profit. Position C collects its credit. This is the convexity payoff -- the portfolio has embedded crash protection that pays 13:1 on the $300 risk.

---

## SCENARIO MATRIX

| Scenario | SPY Level | Pos A | Pos B | Pos C | **Net P&L** | **% of Account** |
|----------|-----------|-------|-------|-------|-------------|-------------------|
| Gap fill | ~$665 | +$470 | +$960 | +$70 | **+$1,500** | +15.0% |
| Full gap fill | ~$661 | +$470 | +$1,360 | +$70 | **+$1,900** | +19.0% |
| Rally to $690 | ~$690 | -$130 | -$100 | -$70 | **-$300** | -3.0% |
| Chop at $678 | ~$678 | -$130 | -$100 | +$70 | **-$160** | -1.6% |
| Mild pullback | ~$672 | -$50 | +$260 | +$70 | **+$280** | +2.8% |
| Crash to $640 | ~$640 | +$470 | +$3,460 | +$70 | **+$4,000** | +40.0% |

---

## WHY THESE THREE WORK TOGETHER

### 1. No single scenario wipes all three

In a rally (worst case), all three lose -- but only to their defined stops/max losses. Total damage is exactly $300. In every other scenario, at least one position is positive.

### 2. Time diversification prevents a single expiry from ruining you

- Position B expires Friday Apr 10 (short-dated gamma)
- Position A expires Thursday Apr 17 (medium-term direction)
- Position C expires Friday Apr 25 (long-dated theta)

If the market is quiet this week, Position B dies but Positions A and C still have time. If the market explodes this week, Position B captures it with maximum gamma efficiency.

### 3. Greek diversification

| Greek | Pos A | Pos B | Pos C | Portfolio |
|-------|-------|-------|-------|-----------|
| Delta | -12 | -45 | -8 | -65 (net bearish) |
| Gamma | +1 | +8 | -1 | +8 (long gamma) |
| Theta | -$2/day | -$15/day | +$4/day | -$13/day |
| Vega | +$3 | +$2 | -$4 | +$1 (roughly neutral) |

The portfolio is net bearish (delta -65), which aligns with the gap fill thesis. But it is also long gamma (+8), meaning a sudden move in EITHER direction helps. Theta is negative (-$13/day), which is the cost of holding the positions -- but this is small relative to the gamma payoff if a catalyst hits. Vega is roughly neutral, so an IV spike or crush does not dramatically help or hurt.

### 4. Position C funds the waiting

The $70 credit from Position C offsets roughly 5 days of theta decay from the portfolio ($13/day x 5 = $65). In other words, the credit spread "pays" for the first week of holding Positions A and B. If nothing happens for a week, Position C has covered most of the time decay cost.

### 5. Embedded convexity via Position B

Position B is the "lottery ticket" of the portfolio. It costs $140 (capped at $100 loss with stop), but in a crash scenario it pays $3,000+. This gives the portfolio a convex payoff profile: small losses in mild scenarios, enormous gains in extreme scenarios. The risk/reward is asymmetric in your favor.

---

## EXECUTION TIMELINE

### Monday Apr 7 (Day 1)

**10:00-10:30 AM ET:**
- [ ] Enter Position A: BUY 1x SPY Apr 17 $674P / SELL 1x SPY Apr 17 $668P for $1.30 debit (limit order at mid)
- [ ] Enter Position C: SELL 1x SPY Apr 25 $686C / BUY 1x SPY Apr 25 $689C for $0.70 credit (limit order at mid)
- [ ] Set alerts: SPY at $674 (A confirmation), $680 (A danger), $685 (C danger)
- [ ] Set stop on Position A: close if spread value drops to $0.65

**Do NOT enter Position B on Monday.** It is a Wednesday entry timed for the PCE catalyst.

### Tuesday Apr 8 (Day 2)

- [ ] Monitor SPY action. No trades today.
- [ ] If SPY breaks above $685 and holds, close Position C at the stop ($1.40 spread value, $70 loss)
- [ ] If SPY drops below $675, Position A is working -- do not take profit yet

### Wednesday Apr 8 (Day 3) -- POSITION B ENTRY DAY

**3:00-3:45 PM ET:**
- [ ] Enter Position B: BUY 1x SPY Apr 10 $676P for $1.40 (limit order)
- [ ] Set stop: close if put drops to $0.40 ($100 max loss)
- [ ] Review portfolio: all three positions now open

### Thursday Apr 9 (Day 4) -- PCE DAY

**8:30 AM ET: PCE Release**
- [ ] If PCE hot / SPY drops: Position B put is running. Trail stop to breakeven ($1.40). Hold for CPI Friday
- [ ] If PCE cold / SPY rallies: Position B stop may trigger. Accept the $100 loss. Position C benefits from SPY rally failing to reach $686
- [ ] If PCE inline / SPY flat: Position B decays. If put is worth $0.60-0.80, consider closing to salvage $40-60 (instead of riding to $0.40 stop)

### Friday Apr 10 (Day 5) -- CPI DAY / POSITION B EXPIRY

**8:30 AM ET: CPI Release**
- [ ] Position B expires today. If in the money, close by 3:00 PM ET to avoid exercise complications
- [ ] If SPY has dropped to $668-665, Position A is now deep in profit. Consider closing at 60% of max ($280 profit)
- [ ] If SPY is flat or up, Position B expires worthless. Portfolio loss so far: -$100 (B) and theta on A and C

### Apr 11-17 (Week 2) -- POSITION A WINDOW

- [ ] Position A has until Apr 17. If the gap fill thesis develops slowly, this is where it pays
- [ ] Position C continues collecting theta. Close at 50% profit ($0.35 buyback) if available
- [ ] If SPY breaks above $686 during this window, close Position C at the stop

### Apr 17 (Day 11) -- POSITION A EXPIRY

- [ ] Position A expires. Close by 3:00 PM ET regardless of P&L
- [ ] Position C still open with 8 days remaining

### Apr 18-25 (Week 3) -- POSITION C SOLO

- [ ] Position C is the last one standing. It should be deep in profit (SPY well below $686) or already closed at the stop
- [ ] If still open, close at 50% profit target or by Apr 23 (2 days before expiry)
- [ ] Do NOT hold Position C into Apr 25 expiry. Close by Thursday Apr 24 latest

---

## WHAT A NEW TRADER NEEDS TO KNOW

### This portfolio requires 3 trades to open and 3 trades to close.

That is 6 total transactions across 3 weeks. This is manageable. You are not day-trading. You are setting up positions with defined exits and walking away.

### The stops are non-negotiable.

The entire portfolio is designed around the assumption that stops are honored. If you remove the stops, the risk profile changes dramatically:
- Position B without a stop: $140 risk instead of $100
- Position C without a stop: $230 risk instead of $70
- Total without stops: $500 risk (5% of account) instead of $300 (3%)

The stops are not optional guardrails. They are load-bearing walls.

### You will probably lose on at least one position.

That is by design. A portfolio with three winning positions every time does not exist. The goal is for the winners to outpay the losers. In the gap fill scenario, one winner (+$1,500) more than covers two losers (if any lose). In the chop scenario, you lose on two positions but only $160 total. That is the power of diversification.

### Position B is the one you are most likely to lose on.

Short-dated puts have a high probability of expiring worthless. You are paying $100 for a high-gamma option that needs a catalyst to pay off. Think of it as insurance: you pay for it hoping you never need it, but if you do need it, it saves the portfolio.

### Total commissions estimate

At $0.65/contract (standard broker fee for options):
- Position A: 2 legs x $0.65 = $1.30 to open, $1.30 to close = $2.60
- Position B: 1 leg x $0.65 = $0.65 to open, $0.65 to close = $1.30
- Position C: 2 legs x $0.65 = $1.30 to open, $1.30 to close = $2.60
- **Total commissions: ~$6.50**

Commissions are negligible relative to the $300 risk budget.

---

## COMPARISON TO STANDALONE POSITIONS

| Metric | This Portfolio (19) | Aggressive Put (01) | Butterfly (05) | Iron Condor (08) |
|--------|--------------------|--------------------|----------------|-------------------|
| Max loss | $300 | $200 | $1,650 | $335 |
| Best-case profit | +$4,000 | +$720 | +$13,350 | +$165 |
| Worst-case loss | -$300 | -$200 | -$1,650 | -$335 |
| Chop scenario | -$160 | -$200 | -$1,650 | +$165 |
| Rally scenario | -$300 | -$200 | -$1,650 | -$335 |
| # of losing scenarios | 1 of 4 full loss | 2 of 4 | 3 of 4 | 1 of 4 |
| Requires crash for big win | No (gap fill enough) | No | Yes (exact pin) | N/A |
| New trader friendly | Yes | Yes | No (30 contracts) | Moderate |

The portfolio trades raw upside (the butterfly's $13K potential) for consistency: smaller max loss, fewer losing scenarios, and a payoff that does not require a pinpoint price target. It is the tortoise, not the hare.

---

*"A portfolio is not three trades. It is one position with three expressions. If they do not talk to each other, you just have three ways to lose."*
