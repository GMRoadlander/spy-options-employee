# FINAL CONSENSUS: Top 3 Positions for Borey Review

**Date:** 2026-04-06 (Sunday)
**Synthesized from:** 19 position proposals (aggressive puts, conservative put spread, bear call credit spread, PCE strangle, broken wing butterfly, scale-in ladder, hedged fence, put backspread, diagonal put, 0DTE PCE, wide butterfly, Borey's simple trade, jade lizard, calendar put, iron condor, CPI strangle, MPW straddle, portfolio of 3, Borey's critique)
**Account:** $10,000 | **Combined risk budget:** $500 max (5% of account across all 3)
**Market:** SPX ~6783 (SPY ~678). Gap fill target ~6610 (SPY ~661). VIX ~20.

---

```
#1 BEST: Bear Call Credit Spread (Ceasefire Exhaustion Fade)
   Trade: SELL 1x SPY Apr 17 $683C / BUY 1x SPY Apr 17 $688C for ~$1.10 credit.
          Enter Thursday Apr 9, 10:00-10:30 AM ET after PCE settles.
          Stop: close if spread hits $2.20. Profit: close at $0.55 (50% of credit).
   Why: Defined risk ($110 max managed loss), 74% probability of profit, and
        theta pays you $12-16/day to wait. You don't need SPY to drop — you
        just need it to NOT rally above $683, which is above the MPW exhaustion
        zone and the $680 psychological ceiling. This is the trade Borey respects:
        sell overpriced optimism, let time do the work.

#2 SECOND: Aggressive Directional Put (Gap Fill Conviction)
   Trade: BUY 1x SPY Apr 17 $670P for ~$3.40 debit.
          Enter Thursday Apr 9, 10:00-10:30 AM ET after PCE IV crush.
          Stop: sell if contract drops to $1.40 ($200 loss). Profit: sell at $10.00
          if SPY hits $661 (gap fill). Move stop to breakeven if SPY hits $668.
   Why: This is the purest expression of the gap-fill thesis. If the ceasefire
        cracks, a $17 SPY drop produces ~$660 profit on $340 risked. Apr 17
        gives the thesis the full week. The stop caps loss at $200 (2% of account).
        One order in, one order out — no spread legs to manage.

#3 HEDGE: 0DTE PCE Strangle (Catalyst Scalp)
   Trade: BUY 1x SPY Apr 9 $680C + BUY 1x SPY Apr 9 $676P for ~$1.70 total.
          Enter Thursday Apr 9, 9:35-9:40 AM ET (after PCE prints, after open).
          Kill the losing leg after 15 min of directional commitment. Close winner
          at 2x ($1.70). Hard time stop: close everything by 10:30 AM.
   Why: This is insurance against being wrong on direction. If PCE surprises
        hot and SPY rallies (invalidating the bear thesis), the call leg pays.
        If PCE accelerates the selloff, the put leg pays. Either way, you are
        flat by 10:30 AM Thursday with zero weekend risk. It also teaches Gil
        the MPW exit method before deploying larger positions.
```

---

## COMBINED RISK ANALYSIS

```
COMBINED MAX RISK: $480
  #1 Bear call spread managed stop:  $110  (1.1% of account)
  #2 Long put hard stop:             $200  (2.0% of account)
  #3 0DTE strangle total premium:    $170  (1.7% of account)

COMBINED PROFIT ON GAP FILL (SPY ~661 by Apr 14-15):
  #1 Bear call spread:  +$110  (full credit, calls expire worthless)
  #2 Long $670 put:     +$660  (put worth ~$10.00)
  #3 0DTE strangle:     +$60 to +$250  (put leg on PCE day, already closed)
  TOTAL:                +$830 to +$1,020  (8-10% of account)

COMBINED LOSS IF WRONG (SPY rallies to 685+ and holds):
  #1 Bear call spread stop:  -$110
  #2 Long put stop:          -$200
  #3 0DTE strangle:          -$90 to -$170  (depends on PCE reaction)
  TOTAL:                     -$400 to -$480  (4-5% of account)
```

---

## WHY THESE 3 AND NOT OTHERS

**Eliminated — too complex for a new trader:**
- Broken wing butterfly: 3 legs, pin risk, requires precise strike selection and adjustment
- Jade lizard: naked short put component, undefined risk on downside
- Iron condor: 4 legs to manage, requires active adjustment, whipsaw kills you
- Diagonal put: calendar spread mechanics (different expiries) confuse new traders
- Put backspread: ratio spread, margin implications, non-linear P&L curve

**Eliminated — redundant with the top 3:**
- Conservative put spread ($676/$663): same thesis as #2 but capped profit, costs more. If you are going directional, the straight put is cheaper and uncapped
- Borey's simple trade: likely the $670 put or similar — already captured in #2
- CPI strangle: same structure as #3 but on Friday, carries weekend risk
- MPW straddle: more expensive version of #3, exceeds 2% risk budget

**Eliminated — wrong risk profile:**
- Scale-in ladder: "average down" mentality is dangerous for a new trader
- Hedged fence: collar-like structure assumes you hold SPY shares (you don't)
- Calendar put: benefits from IV expansion at back month, but ceasefire collapse means REALIZED vol, not implied vol — calendar underperforms straight puts
- Wide butterfly: max profit only at a pin — requires SPY to land exactly at the gap fill, not overshoot

**The portfolio of 3 concept was the right idea.** These 3 positions achieve it with proper diversification.

---

## WHY THESE 3 WORK TOGETHER

| Scenario | #1 Bear Call | #2 Long Put | #3 0DTE Strangle | Net |
|---|---|---|---|---|
| Gap fill next week (SPY 661) | +$110 | +$660 | +$60 to +$250 | **+$830 to +$1,020** |
| Slow grind to 670 | +$110 | +$200 | -$90 | **+$220** |
| Chop sideways 675-680 | +$55 | -$200 | -$90 | **-$235** |
| Rally to 685 (ceasefire holds) | -$110 | -$200 | +$60 | **-$250** |
| Crash to 650 (war resumes) | +$110 | +$1,600 | +$400 | **+$2,110** |
| PCE hot, CPI hot, SPY whipsaws | +$55 | -$100 | +$60 | **+$15** |

**Key insight: they don't all fail in the same scenario.** The 0DTE strangle (#3) is direction-agnostic — it profits on a rally that kills the other two. The bear call (#1) profits on sideways chop that bleeds the long put (#2). The long put (#2) captures the tail event that the credit spread's capped profit misses.

---

## ENTRY PLAN

```
Thursday April 9:
  - 8:30 AM: PCE prints. WATCH, do not trade.
  - 8:30-9:30 AM: Monitor ES futures. Note direction and magnitude.
    * If ES moved <15 pts: PCE non-event. Proceed with caution on #3.
    * If ES moved 15-50 pts: Good. Enter #3 at 9:35.
    * If ES moved >50 pts: Skip #3. The move happened. Enter #1 and #2 only.
  - 9:35-9:40 AM: ENTER #3 (0DTE strangle). Limit orders at mid on both legs.
  - 9:40-10:30 AM: MANAGE #3. Kill loser, take winner at 2x, hard close at 10:30.
  - 10:00-10:30 AM: ENTER #1 (bear call spread) and #2 (long put).
    * Confirm SPY is between 672-682. If outside this range, reassess.
    * Bear call: sell $683/$688 for $1.05+ credit.
    * Long put: buy $670P for $3.40 or less.
  - 10:30 AM: #3 is CLOSED. You are holding #1 and #2 only.
  - Rest of day: Set all stops and alerts. Walk away.

Friday April 10:
  - 8:30 AM: CPI prints. DO NOT ADD POSITIONS.
  - If bear call (#1) is at 30%+ profit pre-CPI, close it. Bank the $33+.
  - If long put (#2) surges on hot CPI, hold — this is the thesis working.
  - If SPY gaps above $683 on cold CPI, close #1 at stop. Hold #2 (different thesis).
  - End of day: Note where SPY closes. You should hold only #1 and #2 into weekend.

Weekend April 11-12:
  - Watch: Hormuz shipping reports (any ship attacked = thesis accelerating)
  - Watch: Iran Supreme Leader health updates (death = command chaos)
  - Watch: Oil futures Sunday night open (spike above $100 = Monday gap down)
  - Watch: VIX futures (if VIX Sunday open >25, Monday will be violent)
  - DO NOT: change your stops, add positions, or panic-sell via limit orders

Monday April 13:
  - If gap fill happened or is in progress: manage exits per the rules.
  - If SPY is above $680: #1 still has time, #2 may be bleeding. Check stops.
  - If SPY is 670-678: thesis intact, be patient. You have until Apr 15 (time stop).
  - If SPY hit $668 (halfway to gap fill): move #2 stop to breakeven ($3.40).
  - #1 at 50% profit ($0.55): CLOSE. Do not hold for the last $0.55.
```

---

## THE ONE THING GIL MUST SAY TO BOREY

**"I sized all three positions so that even if every single one hits max loss on the same day, I lose $480 — less than 5% of my account — and I still have $9,520 to trade next week."**

This shows Borey that Gil understands the game is survival first, profit second. Any new trader who leads with "here's how much I'll make" gets dismissed. A trader who leads with "here's exactly how much I can lose and why I'm comfortable with it" earns respect. The gap fill thesis might be right. The ceasefire might hold. It doesn't matter — the sizing ensures Gil is still in the game either way.
