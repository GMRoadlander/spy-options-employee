# 18 — Portfolio of Three: Coordinated Bearish Portfolio

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783)
**Market:** SPX ~6783 (SPY ~678). Gap-up from ~6610 on US-Iran ceasefire Apr 7. VIX ~20. Oil $94. MPW sees exhaustion at SPX 6775-6800.
**Account:** $10,000 | **Total risk budget:** 5% = $500
**Catalysts ahead:** PCE Thursday Apr 9, CPI Friday Apr 10

---

## Why Three Positions, Not One

A single bearish trade is a coin flip with structure. Three positions that cover different failure modes, different timelines, and different volatility regimes create a portfolio where:

1. **Not all three lose in the same scenario.** Position B (premium collection) profits in flat/slow markets where A and C bleed. Position C (convexity) profits in crashes where A hits max profit and stops gaining.
2. **Time diversification.** Different expiries mean you are not fully exposed to a single week's theta curve or a single expiration-day pin risk.
3. **Convexity for free.** The premium collected from B partially finances the lottery ticket in C, making the overall portfolio's risk profile asymmetric: defined loss, outsized gain on a tail event.

The three positions are designed so that a new trader can manage them by checking SPY price once per day and following explicit if/then rules. No real-time hedging. No delta balancing. Just entry, alerts, and exits.

---

## Position A: Core Bearish — Put Debit Spread (Gap Fill Bet)

### SPY Apr 17 $672 / $662 Put Debit Spread

| Field | Detail |
|---|---|
| **Action** | **BUY** 1x SPY Apr 17 $672 Put / **SELL** 1x SPY Apr 17 $662 Put |
| **Spread width** | $10.00 |
| **Entry** | **Thursday Apr 9, 10:00-10:30 AM ET** (after PCE settles) |
| **Estimated debit** | ~$2.20 per spread ($220 total) |
| **Quantity** | 1 contract |
| **Max loss** | **$220** = net debit paid |
| **Max profit** | **$780** = ($10.00 - $2.20) x 100 at SPY at or below $662 |
| **Breakeven** | SPY at **$669.80** (long strike minus debit) |
| **Prob of profit** | ~32-36% (need SPY below $669.80) |
| **DTE at entry** | 8 calendar days |
| **Reward:Risk** | **3.5:1** |

### Why This Structure

A put debit spread instead of a straight put because this is the *core* position in a 3-position portfolio. You need defined risk, and you need it cheap enough to leave room for B and C.

**Strike selection:**
- **Long $672 put (delta ~-0.30):** Slightly further OTM than the standalone $670P from Position 01. The $2 higher strike costs ~$0.50 more but starts gaining sooner on a pullback. In a coordinated portfolio, you want the core position to activate first.
- **Short $662 put:** Just above the gap-fill target of $661. This is intentional. If SPY fills the gap to $661, your spread is at full value ($10 intrinsic). You do not need to capture the overshoot because that is Position C's job. Selling the $662 put funds 40% of the long put's cost.

**Expiry: Apr 17 (8 DTE at entry).** Same logic as Position 01: survives both PCE and CPI, gives the thesis the full week, avoids holding 1-2 DTE when theta acceleration makes management impossible.

### Management Rules

1. **No stop loss on this position.** Max loss is the $220 debit. The spread cannot lose more than that. This is the advantage of debit spreads for new traders: the risk is defined at entry.
2. **Take profit at 60% of max profit ($468).** When the spread is worth $6.88 or more, close it. That is ~$468 profit on $220 risk. Do not hold for the last $3 of intrinsic hoping SPY falls from $664 to $662.
3. **Time stop: Tuesday Apr 15, 3:00 PM ET (2 DTE).** Close for whatever it is worth. Even if SPY is at $670 and the spread has some value, take it. Gamma risk on short-dated spreads is real.
4. **If SPY hits $668 (halfway to gap fill):** The spread should be worth ~$4.50-5.50. Sell half -- oh wait, you only have 1 contract. Instead: set a mental floor at $4.00. If the spread hits $5.50 and drops back below $4.00, close. The partial fill has given you a profit; do not let it become a loss.
5. **CPI rule (Fri Apr 10):** If the spread is worth $4.00+ before CPI, close. Do not gamble a $180 unrealized gain on a binary event.

---

## Position B: Premium Collection — Bear Call Credit Spread (Theta Engine)

### SPY Apr 11 $684 / $689 Bear Call Credit Spread

| Field | Detail |
|---|---|
| **Action** | **SELL** 1x SPY Apr 11 $684 Call / **BUY** 1x SPY Apr 11 $689 Call |
| **Spread width** | $5.00 |
| **Entry** | **Monday Apr 7, 10:30 AM ET** (after opening volatility settles) |
| **Estimated credit** | ~$0.95 per spread ($95 total) |
| **Quantity** | 1 contract |
| **Total credit** | $95 |
| **Max loss** | **$405** = ($5.00 - $0.95) x 100 |
| **Managed max loss** | **$190** = stop at 2x credit ($1.90) |
| **Max profit** | **$95** = full credit retained |
| **Breakeven** | SPY at **$684.95** (short strike + credit) |
| **Prob of profit** | ~73-77% (short strike delta ~0.23-0.27) |
| **DTE at entry** | 4 calendar days / 4 trading days |
| **Theta per day** | ~$0.18-0.24 per spread (~$18-24/day on a 4 DTE short spread) |

### Why Different Expiry and Different Entry Than A

This is the critical portfolio design decision. Position B uses **Apr 11 expiry (Friday of entry week)** and enters **Monday**, not Thursday.

1. **Time diversification.** Position A expires Apr 17. Position B expires Apr 11. If the ceasefire holds through Friday and SPY stays below $684, Position B profits and closes before Position A even has its main catalyst (PCE Thursday). You bank $95 before the big events.
2. **Monday entry captures maximum theta.** A 4 DTE at-the-money credit spread has the steepest theta decay curve. By entering Monday, you get 4 full days of accelerating decay. The spread loses ~25% of its value per day if SPY stays flat.
3. **If the ceasefire holds through Friday (the "chop" scenario):** Position A is bleeding theta on its 8 DTE puts, but Position B is actively profiting. This is the portfolio's hedge against "right direction, wrong timing."
4. **Short strike at $684 (not $683).** One dollar higher than Position 03's standalone bear call because the Monday entry is before PCE crush. IV is slightly higher Monday, so you can afford to sell a strike further OTM and still collect ~$0.95. The extra dollar of cushion matters when you are entering earlier.

### Why NOT the Same Apr 17 Expiry as Position A

If both A and B expire Apr 17, you have correlated expiry risk. A single whipsaw on Apr 16-17 hurts both. With Apr 11, Position B resolves before Position A faces its highest-risk days. You know by Friday whether B worked, and you can adjust your mental state for managing A and C the following week.

### Management Rules

1. **Stop loss: 2x credit = $1.90.** If the spread reaches $1.90, close immediately. Realized loss: $95. This happens if SPY hits ~$685-686.
2. **Take profit at 50% = $0.475.** Close when the spread can be bought for $0.48 or less. Expected by Wednesday if SPY stays below $682.
3. **Thursday PCE rule:** If the spread is still open Thursday morning (1 DTE), close it before 8:30 AM PCE release regardless of P&L. Do not hold a 1 DTE credit spread into a macro catalyst. The gamma risk is extreme.
4. **Never hold to expiration.** Close by Thursday at the latest. Friday expiration pin risk on a short spread is how new traders learn expensive lessons.

---

## Position C: Cheap Convexity — Put Butterfly (Crash Lottery Ticket)

### SPY Apr 22 $655 / $640 / $625 Put Butterfly

| Field | Detail |
|---|---|
| **Action** | **BUY** 1x SPY Apr 22 $655 Put / **SELL** 2x SPY Apr 22 $640 Put / **BUY** 1x SPY Apr 22 $625 Put |
| **Spread structure** | Long put butterfly, body at $640, wings $15 wide |
| **Entry** | **Monday Apr 7, 10:30 AM ET** (with Position B) |
| **Estimated debit** | ~$0.85 per butterfly ($85 total) |
| **Quantity** | 1 butterfly |
| **Max loss** | **$85** = net debit paid |
| **Max profit** | **$1,415** = ($15.00 - $0.85) x 100 at SPY exactly $640 |
| **Profitable zone** | SPY between **$654.15** and **$625.85** at expiry |
| **Breakeven (upper)** | SPY at **$654.15** (upper wing minus debit) |
| **Breakeven (lower)** | SPY at **$625.85** (lower wing plus debit) |
| **DTE at entry** | 15 calendar days |
| **Reward:Risk** | **16.6:1** |

### Why a Butterfly, Not a Backspread or Straight OTM Put

1. **Cost.** A $640 straight put at 15 DTE costs ~$1.50-2.00. A backspread (sell 1x $660P, buy 2x $645P) costs ~$1.60-2.00. The butterfly costs ~$0.85. For a lottery ticket, cheaper is better because you expect to lose this money 70%+ of the time.
2. **Defined risk.** The butterfly cannot lose more than $85. A backspread can lose more if SPY drops just to $660 (short leg in-the-money, long legs still OTM).
3. **The body at $640 is the crash target.** If the ceasefire collapses violently -- not just a gap fill to $661 but a full-blown Strait of Hormuz blockade, oil to $130, risk-off panic -- SPY $640 is approximately a 5.6% drawdown from $678. That is the 2022-style "war is real" level. The butterfly's max profit zone centers exactly there.
4. **The wide wings ($15) create a $29 profitable zone.** You do not need SPY to land precisely at $640. Anywhere from $625 to $655 at expiry produces a profit. That is a generous target for a crash scenario.

### Why Apr 22 Expiry (Not Apr 11 or Apr 17)

1. **A crash does not happen overnight.** If the ceasefire collapses, the first leg down might hit $661 (gap fill) by mid-week. The second leg -- the panic -- takes another 3-7 days as oil spikes, shipping routes close, and the market reprices actual war risk. Apr 22 gives this second leg time to develop.
2. **Apr 17 is Position A's expiry.** If you put the butterfly on Apr 17 too, you have three positions all expiring the same week. Apr 22 means Position A has already closed (win or lose) before the butterfly reaches peak gamma.
3. **15 DTE at entry means low theta.** A deep OTM butterfly at 15 DTE decays very slowly (~$0.03-0.05/day). You can hold it for 10 days without losing half the premium. This is a "set and forget" position that stays alive while A and B do the heavy lifting.

### Management Rules

1. **No stop loss.** Max loss is $85. Let it ride or expire worthless. Do not waste mental energy on a lottery ticket.
2. **If SPY hits $655 (upper wing), the butterfly starts gaining value fast.** At that point it might be worth $3.00-5.00. **Do not sell yet.** The thesis says the crash goes to $640. Let it run.
3. **If SPY hits $645-640 and the butterfly is worth $8.00+, take the money.** Close the entire butterfly. An $800+ return on $85 is a generational trade on a $10K account. Do not hold for max profit ($1,415) -- the last few dollars of a butterfly require SPY to pin exactly at the body strike. That never happens cleanly.
4. **If SPY hits $655 and bounces back to $665: close for whatever it is worth** ($1.50-2.50 likely). The crash scenario played partially. Take the partial win.
5. **Time stop: Thursday Apr 17, 3:00 PM ET (3 DTE).** If the crash has not happened by then, the butterfly is worth ~$0.10-0.30. Close it. The last 3 days of a butterfly are pure pin risk -- the value swings wildly on small moves and you will not be able to manage it rationally.

---

## Portfolio Summary

| Position | Direction | Expiry | Max Risk | Max Profit | Entry |
|---|---|---|---|---|---|
| A: Put debit spread $672/$662 | Bearish (gap fill) | Apr 17 | $220 | $780 | Thu Apr 9 |
| B: Bear call spread $684/$689 | Neutral-bearish (theta) | Apr 11 | $190 (managed) | $95 | Mon Apr 7 |
| C: Put butterfly $655/$640/$625 | Crash convexity | Apr 22 | $85 | $1,415 | Mon Apr 7 |
| **TOTAL** | | **3 expiries** | **$495** | **$2,290** | |

**Total max risk: $495 (4.95% of $10K).** Under the $500 / 5% cap.

**Combined debit/credit at entry:** $220 (A) - $95 (B) + $85 (C) = **$210 net cash outlay.** The $95 credit from B partially funds C. You have $285 of margin held for the short call spread (B) but that is returned when B closes.

---

## Expiry Timeline

```
Mon Apr 7   Tue Apr 8   Wed Apr 9   Thu Apr 9   Fri Apr 11   ...   Thu Apr 17   ...   Tue Apr 22
                                      PCE         CPI
  B+C enter                           A enters    B expires          A expires          C expires
  |                                   |           |                  |                  |
  |--- B: 4 DTE theta engine --------|---------->|                  |                  |
  |                                   |--- A: 8 DTE core bet ------>|                  |
  |--- C: 15 DTE crash lottery ----------------------------------------->|------------>|
```

**Key insight:** By Friday Apr 11, Position B has already resolved. You know if you banked $95 or lost $95. That frees mental bandwidth to manage A (which has 6 DTE left) and ignore C (which has 11 DTE left and requires no attention unless SPY is below $660).

---

## Combined P&L in 5 Scenarios

All P&L estimates assume positions are held to their respective management exit points, not expiration. Real results depend on exact entry fills, exit timing, and IV changes.

### Scenario 1: Gap Fill -- SPY $661 by Apr 14

The core thesis plays out. SPY drops from $678 to $661 over 5-7 trading days.

| Position | Value at exit | P&L | Notes |
|---|---|---|---|
| A: Put spread $672/$662 | ~$9.50 (near max, SPY just below short put) | **+$730** | Close at $9.50; $662 short put barely ITM but spread near full width |
| B: Bear call spread | Expired worthless (Fri Apr 11) | **+$95** | SPY well below $684 by Friday. Full credit retained. |
| C: Put butterfly | Worth ~$1.50-2.50 (SPY at $661, upper wing $655 not yet breached) | **-$50 to +$165** | Close for ~$0.35-1.50 depending on timing; butterfly gaining but not in sweet spot yet. Call it **+$50 midpoint.** |
| **TOTAL** | | **+$875** | **175% return on $495 risked** |

### Scenario 2: Partial Fill -- SPY $668 by Apr 15

SPY pulls back but stalls at $668. The gap does not fully fill. Ceasefire wobbles but holds.

| Position | Value at exit | P&L | Notes |
|---|---|---|---|
| A: Put spread $672/$662 | ~$4.50-5.00 (long put $4 ITM, short put still OTM) | **+$260** | Close at time stop Tue Apr 15. Solid partial win. |
| B: Bear call spread | Expired worthless (Fri Apr 11) | **+$95** | SPY at $668-675 range during B's life. Full credit. |
| C: Put butterfly | Worth ~$0.40-0.60 (SPY still above $655 upper breakeven) | **-$45** | Close at time stop. Small loss on the lottery ticket. |
| **TOTAL** | | **+$310** | **63% return on $495 risked** |

### Scenario 3: Chop -- SPY $678 (No Move) Through Apr 17

Market goes nowhere. Ceasefire holds, data is in-line, SPY oscillates $674-682.

| Position | Value at exit | P&L | Notes |
|---|---|---|---|
| A: Put spread $672/$662 | ~$0.80-1.20 at time stop (OTM, mostly theta-decayed) | **-$110** | Close at Tue Apr 15 for ~$1.00. Lost ~half the debit. |
| B: Bear call spread | Expired worthless or closed at 50% | **+$50 to +$95** | SPY stayed below $684. Theta did the work. Call it **+$70 midpoint.** |
| C: Put butterfly | Worth ~$0.15-0.25 (deep OTM, no crash) | **-$65** | Close at time stop. Near-total loss. Expected. |
| **TOTAL** | | **-$105** | **-21% (loss of $105 on $495 risked)** |

**This is the key portfolio property.** In the worst "nothing happens" scenario, you lose $105 -- not $495. Position B's theta income offsets a large portion of A and C's losses. A single-position bearish trade would lose the full debit here. The portfolio bleeds slowly instead of dying.

### Scenario 4: Rally -- SPY $690 by Apr 14

Ceasefire holds. Market rallies further. Everything the thesis said was wrong.

| Position | Value at exit | P&L | Notes |
|---|---|---|---|
| A: Put spread $672/$662 | ~$0.20-0.40 (deep OTM) | **-$185** | Close at time stop. Nearly full loss. |
| B: Bear call spread | Stopped out at 2x credit ($1.90) | **-$95** | SPY blew through $684. Stop triggered Wed/Thu. |
| C: Put butterfly | Worth ~$0.05-0.10 (worthless) | **-$80** | Close at time stop or let expire. Nearly full loss. |
| **TOTAL** | | **-$360** | **-73% (loss of $360 on $495 risked)** |

**Even in the worst scenario, you lose $360, not $495.** The managed stop on B ($190 managed max) saved $215 vs. unmanaged max loss. And $360 is 3.6% of the account -- painful but survivable. You still have $9,640 and full capacity to trade next week.

### Scenario 5: Crash -- SPY $640 by Apr 18-20

Ceasefire collapses violently. Strait of Hormuz blockade. Oil spikes to $130. VIX hits 35+. SPY crashes 5.6% in 7-10 days.

| Position | Value at exit | P&L | Notes |
|---|---|---|---|
| A: Put spread $672/$662 | $10.00 (max value, both legs deep ITM) | **+$780** | Full max profit. Close immediately once spread is at $9.50+. |
| B: Bear call spread | Expired worthless (Fri Apr 11) | **+$95** | SPY was already falling by Fri. Full credit retained. |
| C: Put butterfly | Worth ~$10.00-13.00 (SPY near body at $640) | **+$915 to +$1,215** | This is the lottery ticket paying off. Call it **+$1,000 midpoint.** |
| **TOTAL** | | **+$1,875** | **379% return on $495 risked** |

**This is convexity at work.** The $85 butterfly produces $1,000 in the crash scenario. It is sized to lose the full $85 most of the time, but when it pays, it pays 12x. That is the entire purpose of Position C -- it turns a $780 max profit (A alone) into a $1,875 portfolio gain.

---

## Scenario Summary Table

| Scenario | SPY Level | Pos A | Pos B | Pos C | **Total P&L** | **% of Account** |
|---|---|---|---|---|---|---|
| **Crash** | $640 | +$780 | +$95 | +$1,000 | **+$1,875** | **+18.8%** |
| **Gap fill** | $661 | +$730 | +$95 | +$50 | **+$875** | **+8.8%** |
| **Partial fill** | $668 | +$260 | +$95 | -$45 | **+$310** | **+3.1%** |
| **Chop** | $678 | -$110 | +$70 | -$65 | **-$105** | **-1.1%** |
| **Rally** | $690 | -$185 | -$95 | -$80 | **-$360** | **-3.6%** |

**Reading the table:**
- You profit in 3 of 5 scenarios (crash, gap fill, partial fill).
- You lose in 2 of 5 scenarios (chop, rally).
- The worst loss ($360) is 3.6% of the account.
- The best gain ($1,875) is 18.8% of the account.
- The chop scenario (most likely if you have no edge) loses only $105 (1.1%).

**Expected value calculation (rough, equal-weight scenarios):**
($1,875 + $875 + $310 - $105 - $360) / 5 = **+$519 average.**
In reality the scenarios are not equally likely, but even weighting the rally at 30% probability and the crash at 10%, the expected value remains positive because the crash payout is so large relative to its cost.

---

## Correlation Matrix: What Loses Together, What Does Not

|  | A loses | B loses | C loses |
|---|---|---|---|
| **Rally to $690** | Yes (OTM puts) | Yes (calls breached) | Yes (deep OTM) |
| **Chop at $678** | Yes (theta burn) | **No (theta profit)** | Yes (OTM decay) |
| **Slow grind to $668** | **No (partial win)** | **No (calls safe)** | Yes (not deep enough) |
| **Gap fill to $661** | **No (near max win)** | **No (calls safe)** | Marginal (upper wing nearby) |
| **Crash to $640** | **No (max win)** | **No (calls safe)** | **No (max profit zone)** |

**All three only lose together in the rally scenario.** In every other scenario, at least one position is profitable. That is the point of portfolio construction.

---

## Entry Sequence: Day-by-Day Execution

### Monday Apr 7 (Market Open After Ceasefire Weekend)

**10:00 AM:** Let the opening 30 minutes of chaos resolve. Watch SPY level.

**10:30 AM -- Enter Position B (Bear Call Spread):**
1. Place limit order: SELL SPY Apr 11 $684/$689 call spread for $0.90 credit (start conservative).
2. If not filled in 10 minutes, walk up to $0.95. Do not accept less than $0.85.
3. After fill: set alert at SPY $684 (short strike). Set alert at spread value $1.90 (stop).

**10:35 AM -- Enter Position C (Put Butterfly):**
1. Place limit order: BUY SPY Apr 22 $655/$640/$625 put butterfly for $0.90 debit (start generous).
2. If not filled in 10 minutes, walk down to $0.85. Do not pay more than $1.00.
3. After fill: set alert at SPY $655 (upper breakeven). No stop needed.

**End of Monday:** Two positions on. $95 collected from B, $85 spent on C. Net: $10 credit in pocket. Position A waits for Thursday.

### Tuesday Apr 8 - Wednesday Apr 9

**Monitor only.** Check SPY once at 3:00 PM each day.
- If Position B is at 30%+ profit ($0.665 or less), close it early. Do not get greedy on a 4 DTE spread.
- If SPY closes above $683 on either day, assess whether Position B's stop ($1.90) is in danger. If the spread is at $1.50+, consider closing early.

### Thursday Apr 9 (PCE Day)

**8:30 AM:** PCE data drops. Note the reaction. Do NOT trade for 90 minutes.

**10:00-10:30 AM -- Enter Position A (Put Debit Spread):**
1. Check SPY level:
   - **SPY $674-682:** Proceed. Place limit order: BUY SPY Apr 17 $672/$662 put spread for $2.30 debit (start generous). Walk down to $2.20. Do not pay more than $2.50.
   - **SPY below $672:** Position A's long strike is already ATM or ITM. The put spread costs $4.00+. **Do not enter.** The easy money already moved. Positions B and C are your only plays this week.
   - **SPY above $685:** Ceasefire momentum is strong. **Do not enter.** Positions B and C are still on; let them work.
2. After fill: set alerts per management rules above.

**Also Thursday -- check Position B:**
- If Position B has 1 DTE and is still open, close it before the 8:30 AM PCE number. Do not hold overnight into Friday expiration.

### Friday Apr 11 (CPI Day + Position B Expiry)

**Before 8:30 AM:** Position B should already be closed (Thursday rule). If somehow still open, close at market open.

**CPI drops at 8:30 AM.**
- Check Position A: apply CPI management rule from Position A section.
- Position C: ignore. It has 11 DTE and does not need attention.

### Monday Apr 14 - Tuesday Apr 15

- **Position A management phase.** Follow the management rules. Close by Tue Apr 15 at 3:00 PM.
- **Position C:** Check once daily. Only act if SPY is below $660.

### Wednesday Apr 16 - Thursday Apr 17

- Position A has expired or been closed.
- Position C is the only remaining position. 5 DTE. Check daily.
- Close C at time stop (Thu Apr 17, 3:00 PM) if the crash has not materialized.

### Friday Apr 18 - Tuesday Apr 22

- If Position C is still alive (you did not close at the Apr 17 time stop because SPY was in the $640-660 zone and the butterfly had value), manage it through expiry week. Close by Monday Apr 20 at the latest. Do not hold butterflies into the final 2 days.

---

## What This Portfolio Is NOT

1. **It is not hedged to be delta-neutral.** This is a directional bearish portfolio. It loses money if the market rallies. The portfolio design reduces *how much* it loses (via B's theta income) but it does not eliminate directional risk.

2. **It is not a "set and forget" portfolio.** There are 3 positions with 3 different expiries and 5 management rules. It requires checking SPY once daily and acting on alerts. A new trader CAN manage this, but they need to commit to the checklist.

3. **It is not a hedge against a long equity portfolio.** If Borey also holds long SPY/SPX positions elsewhere, this portfolio provides some offset, but it was not designed for that. It was designed as a standalone $500-risk bearish thesis expression.

4. **It is not scalable to 10 contracts.** The $500 risk cap with $10K account means 1 contract each. Do not scale up before successfully managing the full lifecycle of all three positions at least once.

---

## Final Checklist for Borey

- [ ] **Sunday night:** Review this document. Understand all three positions and their management rules. If anything is unclear, ask before market open.
- [ ] **Monday 10:30 AM:** Enter B (bear call spread) and C (butterfly). Two orders. Should take 5 minutes.
- [ ] **Monday after fill:** Set 3 alerts: SPY $684, B spread at $1.90, SPY $655.
- [ ] **Tue-Wed:** Check SPY at 3 PM. Close B early if at 30%+ profit.
- [ ] **Thursday pre-8:30 AM:** Close B if still open. Then wait for PCE.
- [ ] **Thursday 10:00 AM:** Enter A (put spread) if SPY is $674-682.
- [ ] **Thursday after A fill:** Set alerts per A management rules.
- [ ] **Friday (CPI):** Apply CPI rules for A. B should be closed. C needs no action.
- [ ] **Mon-Tue next week:** Manage A to time stop. Check C daily.
- [ ] **Thu Apr 17:** Close C if crash has not happened. Portfolio complete.

Total time commitment: ~10 minutes per day for 8 trading days. That is the cost of a 3-position portfolio. If that sounds like too much, run Position B alone -- it is the simplest of the three and profits in the widest range of scenarios.
