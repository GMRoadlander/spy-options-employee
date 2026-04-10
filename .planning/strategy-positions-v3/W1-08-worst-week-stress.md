WORST-WEEK STRESS TEST -- V3 Swarm
====================================
Date compiled: 2026-04-06 (Sunday)
Trading week: April 7-11 (through Monday April 13)
Account: $10,000
Trader: Gil (new, first real positions)
Bias: Bearish / gap fill thesis (SPY 678 -> 661)
VIX: ~20 | PCE Thursday | CPI Friday

ASSUMED POSITIONS (from V2 Final Consensus, #20):
  #1 Bear call spread: SELL SPY Apr 17 $683C / BUY $688C, ~$1.10 credit
  #2 Long put: BUY SPY Apr 17 $670P, ~$3.40 debit
  #3 0DTE strangle: BUY SPY Apr 9 $680C + $676P, ~$1.70 debit
  COMBINED MAX RISK: $480
  ENTRY: #3 Thursday 9:35 AM, #1 and #2 Thursday 10:00-10:30 AM

NOTE ON POSITION SET: Gil may instead run the Portfolio of Three
(A: $672/$662 put spread $220, B: $684/$689 bear call $95 credit,
C: $655/$640/$625 butterfly $85). Numbers below model BOTH sets
where they diverge. The worst case is similar either way because
total risk is capped at ~$480-$500.

-----------------------------------------------------------------

SCENARIO 1: CEASEFIRE HOLDS + SUSTAINED RALLY
=============================================

Timeline:
- Saturday April 11: Islamabad talks produce framework agreement
- Sunday April 12: Oil futures gap down to $85 (from $94)
- Sunday night: ES futures open +1.5%, VIX futures drop to 16
- Monday April 13: SPX gaps up 2% to ~6920 (SPY ~$692)
- VIX drops to 15 by Monday close
- Tuesday-Wednesday: SPY consolidates 688-694, no pullback
- Ceasefire narrative hardens: "peace is real this time"

Position-by-position damage:

  #3 0DTE strangle (already closed Thursday):
     This position is GONE by Monday. Closed Thursday by 10:30 AM per rules.
     Result: Depends on PCE day action. Assume PCE was inline, strangle
     lost the put leg, call leg made partial profit.
     NET: -$90 to +$60 (call it -$30 midpoint)

  #1 Bear call spread ($683/$688, Apr 17):
     Monday open: SPY gaps to $692. Short $683C is $9 ITM. Long $688C
     is $4 ITM. Spread is at max loss = $5.00 - $1.10 credit = $3.90.
     BUT: Gil's stop is at $2.20 (2x credit). That stop should have
     triggered BEFORE Monday -- probably Friday if SPY was trending up
     after CPI. If Gil honored the stop Friday: loss = $1.10 (credit
     received minus $2.20 buyback) = -$110.
     IF GIL FROZE AND DIDN'T HONOR THE STOP: loss = $3.90 x 100 = -$390.
     NET (disciplined): -$110
     NET (froze): -$390

  #2 Long $670P (Apr 17):
     Monday: SPY at $692. The $670P with 4 DTE is $22 OTM. Delta ~0.05.
     Value: ~$0.15-$0.25. Essentially dead.
     Gil's stop was at $1.40. That should have triggered Thursday or
     Friday as SPY held above $680 and VIX crushed.
     IF GIL HONORED THE STOP: loss = $3.40 - $1.40 = $2.00 = -$200.
     IF GIL FROZE: put decays to ~$0.15. Loss = $3.40 - $0.15 = -$325.
     NET (disciplined): -$200
     NET (froze): -$325

SCENARIO 1 TOTAL:
  Disciplined Gil:  -$30 + (-$110) + (-$200) = -$340 (3.4% of account)
  Undisciplined Gil: -$30 + (-$390) + (-$325) = -$745 (7.5% of account)

  Account remaining: $9,660 (disciplined) / $9,255 (undisciplined)

  WHY THIS MATTERS: The difference between honoring stops and freezing
  is $405. That is the cost of emotional failure. The positions were
  DESIGNED to lose only $480 max with stops. Without stops, they lose
  $745 -- and that is still not catastrophic because the structures
  have defined risk. The bear call spread's $5 width saves Gil from
  unlimited upside loss. The long put can only go to zero. The 0DTE
  is already closed.

  This is the scenario where Gil learns the most painful lesson of
  trading: being wrong on direction with proper risk management is
  survivable. Being wrong on direction without risk management is
  how accounts die.

-----------------------------------------------------------------

SCENARIO 2: WHIPSAW HELL
=========================

Timeline:
- Thursday April 9, 8:30 AM: PCE prints HOT (0.5% MoM vs 0.3% expected)
- 8:30-9:30 AM: ES futures drop 40 points. VIX spikes to 24.
- 9:30 AM: SPY opens at $674. Gil's bearish thesis feels confirmed.
- 9:35 AM: Gil enters #3 (0DTE strangle). Put leg immediately up 60%.
  Call leg drops 40%. Net strangle up ~$0.50 (from $1.70 to $2.20).
- 9:45 AM: Gil SHOULD kill the call leg per rules. But the put is
  ripping. He thinks "why sell the call at a loss when the put is
  about to double?" GREED. He holds both legs.
- 10:00 AM: Gil enters #1 and #2 while feeling euphoric.
  Bear call spread: fills at $1.40 credit (wider because IV spiked).
  Long $670P: fills at $4.50 (more expensive because IV spiked and
  SPY is closer to strike). Gil overpays but doesn't notice.
- 10:15 AM: HEADLINE -- "Iran extends ceasefire to 30 days, Islamabad
  talks moved up to Wednesday." SPY reverses. Violently.
- 10:15-11:00 AM: SPY rips from $674 to $682. VIX drops from 24 to 19.
- Gil's 0DTE strangle: Put leg crashes from +60% to -80% (delta
  collapsed, theta accelerated, SPY reversed). Call leg recovers
  but not enough. Strangle worth ~$0.40 (from $1.70 entry).
  Gil was supposed to close by 10:30. He's paralyzed.
  NET #3: -$130 (bought $1.70, sold $0.40 or expired near zero)

- Thursday afternoon: SPY consolidates at $681. Gil holds #1 and #2.
- Friday April 10, 8:30 AM: CPI prints INLINE (3.4% YoY as expected).
- Market reaction: flat. SPY opens at $680, drifts to $679 by noon.
- Gil holds all week into the following Monday.
- Monday April 13: Market chops. SPY closes at $678.

Position damage:

  #3 0DTE strangle: -$130 (closed Thursday, total loss minus scraps)

  #1 Bear call spread ($683/$688, Apr 17):
     Entered at $1.40 credit (overpaid entry -- IV spike made credit
     fatter but that helps Gil here). SPY at $678-681 range.
     By Monday Apr 13 (6 DTE), spread is worth ~$0.80-$1.00.
     Gil is up ~$40-$60 on this position. The theta engine works.
     If Gil closes at 50% profit ($0.70): NET +$70.
     If Gil holds: will likely profit as theta continues.
     NET #1: +$40 to +$70 (call it +$55 midpoint)

  #2 Long $670P (Apr 17):
     Entered at $4.50 (overpaid due to IV spike). SPY at $678 Monday.
     Put is $8 OTM with 4 DTE. IV has crushed from 24 back to 19.
     Value: ~$1.00-$1.50.
     Gil's stop was $1.40 (set based on $3.40 entry assumption).
     At $4.50 entry, stop at $1.40 means a $310 loss.
     The put is hovering RIGHT AT the stop level.
     IF GIL HONORED STOP: -$310 (stopped out Friday or Monday)
     IF GIL HOLDS hoping for a move: put worth ~$0.80 by Wednesday
     time stop. Loss = $4.50 - $0.80 = -$370.
     NET #2 (disciplined): -$310
     NET #2 (held): -$370

  THE OVERPAY PROBLEM: Gil entered #2 at $4.50 instead of $3.40
  because IV spiked on hot PCE. He entered INTO the spike instead
  of AFTER the crush. The entry plan said 10:00-10:30 AM "after PCE
  settles." But PCE was hot, the market was moving, and Gil thought
  "I need to get in NOW before it drops more." That $1.10 overpay
  is a hidden $110 of extra risk the plan didn't account for.

SCENARIO 2 TOTAL:
  Disciplined Gil:   -$130 + $55 + (-$310) = -$385 (3.9% of account)
  Undisciplined Gil:  -$130 + $55 + (-$370) = -$445 (4.5% of account)
  With overpay tax:   Add -$110 to both = -$495 / -$555

  Account remaining: $9,505 to $9,615 (depending on discipline)

  THE LESSON: Whipsaw scenarios punish TWO mistakes at once:
  (1) not taking profit on the 0DTE when it was there, and
  (2) entering the swing positions into an IV spike instead of
  after the crush. The plan explicitly said "after PCE settles."
  Gil ignored the plan because the hot PCE confirmed his bias.
  Confirmation bias + FOMO = overpaying for positions that then
  reverse. This is the #1 killer of new traders.

-----------------------------------------------------------------

SCENARIO 3: FLASH CRASH + RECOVERY ("I Was Right and Still Lost")
=================================================================

Timeline:
- Thursday April 9: PCE inline. Gil enters all 3 positions as planned.
  #3 strangle: -$40 (PCE non-event, both legs bleed, closed by 10:30)
  #1 bear call at $1.10 credit. #2 long put at $3.40.

- Friday April 10: CPI prints HOT. SPY drops to $672. Gil's positions:
  #1 bear call: spread worth ~$0.40. Gil is up $70. Per rules, should
  close at 50% profit ($0.55). Gil doesn't -- wants "the full credit."
  #2 long put: $670P worth ~$5.80. Gil is up $240 (71% gain).
  Gil thinks: "This is it. The gap fill is happening. Hold."

- Saturday-Sunday: Ceasefire violation. Iranian speedboat fires on a
  tanker in the Strait. Oil futures spike to $110 Sunday night. VIX
  futures open at 32.

- Monday April 13 open: SPY gaps down to $660. Gap fill COMPLETE.
  VIX at 33. Gil's positions are exploding:
  #1 bear call: spread worth ~$0.05. Gil is up $105 (nearly full credit).
  #2 long put: $670P is $10 ITM. With VIX at 33 and 4 DTE, worth ~$12.50.
  Gil is up $910 on the put alone. Total portfolio up ~$975.
  Gil's $10K account is showing $10,975.

  Gil thinks: "If it went to $660, it's going to $650. I want $2,000."

  HE DOES NOT SELL.

- Monday 11:00 AM: HEADLINE -- "US and Iran announce emergency ceasefire
  extension. All parties return to Islamabad immediately."
  SPY reverses. Hard.
- Monday 11:00 AM - 2:00 PM: SPY rallies from $660 to $671.
  VIX drops from 33 to 24 in 3 hours.

  #2 long put: $670P goes from $12.50 to ~$3.50.
  The put lost $9.00 in 3 hours. Gil watches $900 of profit evaporate.
  He is frozen. "It'll come back." It doesn't come back.

  #1 bear call: spread goes from $0.05 to ~$0.65. Still profitable
  but Gil doesn't notice -- he's staring at the put.

- Tuesday April 14: SPY opens at $673, drifts to $675 by noon.
  #2 long put: $670P with 3 DTE, SPY at $675, VIX at 22.
  Value: ~$1.80-$2.20.
  Gil's stop was $1.40 (original) or $3.40 (breakeven, if he moved it
  at $668 per rules). Either way, the put is ABOVE both stops.
  But Gil is so emotionally wrecked from watching +$910 become +$80
  that he sells at $2.00 out of disgust.
  NET #2: $2.00 - $3.40 = -$1.40 x 100 = -$140.

  Wait. He was UP $910 and ended DOWN $140. On a trade where his
  THESIS WAS COMPLETELY CORRECT.

  #1 bear call: Gil closes at $0.45 (55% of credit).
  NET #1: $1.10 - $0.45 = +$0.65 x 100 = +$65.

SCENARIO 3 TOTAL:
  #3 strangle: -$40
  #1 bear call: +$65
  #2 long put: -$140
  TOTAL: -$115 (1.2% of account)

  Account remaining: $9,885

  BUT THE REAL DAMAGE: Gil had $975 of unrealized profit at the peak.
  He ended at -$115. The swing from peak to trough was $1,090 in
  unrealized P&L on a $480 risk budget. That is a 227% swing relative
  to capital at risk.

  IF GIL HAD FOLLOWED THE RULES:
  - $670P profit target was $10.00. At SPY $660 with VIX 33, the put
    was at $12.50 -- ABOVE the profit target. He should have sold
    at $10.00 on the way up (or at $12.50 at the peak).
  - Bear call should have closed at 50% profit ($0.55) on Friday.
  - Disciplined outcome: +$65 (bear call) + $660 (put at $10.00)
    - $40 (strangle) = +$685 (6.9% of account).

  THE DELTA BETWEEN DISCIPLINE AND GREED: $685 - (-$115) = $800.
  Eight hundred dollars. On a $480 risk budget. Greed cost Gil more
  than his ENTIRE max loss would have been.

  EMOTIONAL DAMAGE: DEVASTATING. Gil was right about the gap fill.
  He was right about the ceasefire being fragile. He was right about
  everything except the one thing that matters: taking profit when
  the thesis is complete. He will replay this trade for months.
  Every future trade, he will either (a) take profit too early out
  of PTSD, or (b) hold too long trying to "get back" the $910 he
  once saw. Both reactions lead to more losses.

  This is the scenario that breaks new traders psychologically.

-----------------------------------------------------------------

SCENARIO 4: BROKER / EXECUTION FAILURES
========================================

These are not hypothetical. They happen regularly during macro data
releases. Gil's broker (assumed: Schwab/thinkorswim or similar retail
platform) has documented outage history during high-vol events.

Sub-scenario 4A: Platform Down During PCE (Thursday 8:30 AM)

  - PCE prints hot at 8:30 AM. ES futures drop 35 points.
  - Gil tries to log in to enter #3 (0DTE strangle) at 9:35 AM.
  - Platform is slow. Order page takes 45 seconds to load.
  - By 9:40 AM, SPY has already moved $3 from the open.
  - Gil's 0DTE strangle is now $2.40 instead of $1.70.
  - He enters anyway (FOMO). Overpay: $0.70 x 100 = $70 extra risk.
  - The strangle needs a BIGGER move to profit. PCE move was the move.
  - NET additional loss from execution delay: -$70 to -$120

Sub-scenario 4B: Stop Loss Doesn't Execute

  - Gil sets a GTC stop on #2 (long $670P) at $1.40.
  - SPY gaps up Monday morning after ceasefire news.
  - The put goes from $2.50 (Friday close) to $0.80 (Monday open).
  - The stop at $1.40 was GAPPED THROUGH. The stop becomes a market
    order at the next available price: $0.80, not $1.40.
  - Expected loss: $200 (stop at $1.40). Actual loss: $260 (filled at
    $0.80). Slippage: $60.

Sub-scenario 4C: Spread Fill Slippage

  - Gil enters the bear call spread (#1) as a single spread order.
  - During high-vol period, the spread fills at $0.95 instead of $1.10.
  - Gil received $15 less credit. His max loss is now $4.05 instead
    of $3.90. His stop at $2.20 now represents a $125 loss instead
    of $110.
  - Additional risk from slippage: $15 per contract.

Sub-scenario 4D: Can't Close During Whipsaw

  - Monday flash crash to $660 (Scenario 3). Gil wants to sell.
  - Broker queue: "Your order is in queue. Estimated wait: 3 minutes."
  - SPY moves from $660 to $663 in those 3 minutes.
  - Gil's $670P goes from $12.50 to $10.00.
  - He finally sells at $10.00 instead of $12.50.
  - Missed profit from execution delay: $250.

SCENARIO 4 COMBINED EXECUTION TAX:
  Worst case across all sub-scenarios: -$70 (overpay) + -$60
  (stop slippage) + -$15 (credit slippage) + -$250 (exit delay)
  = -$395 of additional loss beyond what the plan models.

  But these don't all happen in the same week. Realistic worst case
  for a single week: TWO of these co-occur.
  NET realistic execution failure: -$130 to -$310 additional loss.

  Applied to Scenario 1 (rally):
    Disciplined + execution failure: -$340 + (-$180) = -$520 (5.2%)
  Applied to Scenario 3 (flash crash):
    Had Gil tried to sell at $12.50 and got filled at $10.00:
    Outcome swings from +$685 (disciplined) to +$435.

  THE LESSON: Retail execution risk is real and always works AGAINST
  the trader. During the exact moments when getting in/out matters
  most (data releases, gap opens, flash moves), the platform is at
  its worst. Build in a -$100 to -$200 "execution tax" mentally
  when modeling any position's P&L.

-----------------------------------------------------------------

SCENARIO 5: EVERYTHING EXPIRES WORTHLESS (The Slow Bleed)
==========================================================

Timeline:
- Monday April 7: SPY opens at $679 on ceasefire optimism. Drifts to $678.
- Tuesday April 8: SPY $677. Down $1. No headlines. Nothing happens.
- Wednesday April 9: SPY $679. Back up $2. Still nothing.
- Thursday April 9: PCE prints INLINE (0.3% MoM, exactly as expected).
  Market yawns. SPY opens at $678, closes at $679.
  Gil enters all 3 positions. VIX drifts from 20 to 18.

  #3 0DTE strangle: Both legs bleed. SPY moves $1.50 total.
  The strangle needed a $4+ move. It gets $1.50.
  Put leg expires near zero. Call leg expires near zero.
  NET #3: -$170 (total premium lost)

  Gil enters #1 and #2 at 10:30 AM Thursday.
  #1 bear call ($683/$688): Credit $1.10. SPY at $679.
  #2 long $670P: Debit $3.40. SPY at $679.

- Friday April 10: CPI prints INLINE (3.4% YoY as expected).
  SPY opens at $680, closes at $679. VIX drops to 17.
  Nothing. Happens.

- Weekend: No ceasefire incidents. Oil stays at $92. Islamabad talks
  are "constructive but inconclusive." Market shrugs.

- Monday April 13: SPY opens at $680. Drifts to $681 by noon.
- Tuesday April 14: SPY $679. VIX at 17.
- Wednesday April 15 (time stop for #2):
  SPY at $680. The $670P with 2 DTE, VIX at 17, $10 OTM.
  Value: ~$0.15-$0.25.
  Gil closes per time stop rule.
  NET #2: $0.20 - $3.40 = -$3.20 x 100 = -$320

- Thursday April 17 (expiration for #1):
  SPY at $681. The $683/$688 bear call spread:
  Short $683C is $2 OTM. Spread is worth ~$0.30-$0.45.
  Gil should have closed at 50% profit ($0.55) earlier in the week
  when the spread was at $0.50-$0.60. Let's say he did:
  NET #1 (closed at 50%): $1.10 - $0.55 = +$0.55 x 100 = +$55
  NET #1 (held to near-expiry): $1.10 - $0.35 = +$0.75 x 100 = +$75

SCENARIO 5 TOTAL:
  #3 strangle: -$170
  #2 long put: -$320
  #1 bear call: +$55 to +$75 (call it +$65)
  TOTAL: -$425 (4.3% of account)

  Account remaining: $9,575

  BREAKDOWN: The bear call spread is the ONLY position that profits.
  It collected $110 in credit and SPY stayed below $683. Theta worked.
  The long put and strangle both died from theta decay and no movement.

  This is the most LIKELY bad scenario. Markets chop more often than
  they trend. The gap fill thesis might be correct on a 2-3 week
  timeframe but wrong on a 1-week timeframe. If SPY fills the gap
  April 21-25 instead of April 7-17, Gil loses $425 and then watches
  the move happen without him.

  THE LESSON: Theta is the silent killer. Every day SPY doesn't move,
  the long put loses ~$28 and the strangle (while alive) loses ~$40.
  The bear call spread earns ~$18/day. Net daily bleed on a quiet
  day: ~$50. Over 8 trading days (Thursday to Wednesday time stop):
  ~$400. That is almost exactly what this scenario produces.

  In options, TIME is the enemy of the buyer and the friend of the
  seller. Gil is net long premium ($340 put + $170 strangle = $510
  paid, minus $110 call credit = $400 net debit). He is paying $50/day
  for the privilege of being bearish. If the market doesn't move,
  that rent adds up fast.

-----------------------------------------------------------------

SCENARIO 6: THE COMPOUND NIGHTMARE (All Bad Things At Once)
=============================================================

This is the true worst case -- elements of multiple scenarios combine.

Timeline:
- Thursday: PCE hot. Gil enters #3 into the spike (overpays by $70).
  Strangle whipsaws. Gil freezes on the 0DTE. Loses $170 + $70 = -$240.
- Thursday 10:15 AM: Gil enters #1 and #2 into the IV spike.
  Long put costs $4.50 instead of $3.40 (overpay $110).
  Bear call credit is $1.40 (helps slightly, but higher IV = wider
  spread if he needs to stop out).
- Friday: CPI cool. SPY pops to $682. Gil's put drops to $2.80.
  Bear call spread tightens to $0.70.
- Weekend: Ceasefire extension announced.
- Monday: SPY gaps to $688. Gil's stop on the bear call ($2.20 from
  $1.10 credit, but he entered at $1.40 credit so stop is at $2.80)
  doesn't trigger in the gap. Spread opens at $3.50.
  Gil's broker auto-closes at $3.50 (margin call or manual panic).
  Bear call loss: $3.50 - $1.40 = -$210.
- Monday: Long $670P at SPY $688 with 2 DTE = $0.10.
  Gil's stop at $1.40 was gapped through Friday. Filled at $0.90
  (slippage). Actually wait -- if he entered at $4.50:
  Stop at $1.40 (original rule). Filled at $1.40 on Friday (not
  gapped, orderly decline). Loss: $4.50 - $1.40 = -$310.

SCENARIO 6 TOTAL:
  #3 strangle (overpay + whipsaw): -$240
  #1 bear call (gapped through stop): -$210
  #2 long put (IV overpay + stopped out): -$310
  Execution slippage across all: -$80
  TOTAL: -$840 (8.4% of account)

  Account remaining: $9,160

  THIS IS THE ABSOLUTE FLOOR. It requires Gil to make 3+ mistakes
  (enter into IV spike, freeze on 0DTE, get gapped on stops) while
  the market also moves against him. It is unlikely but not impossible
  for a new trader under stress during their first live week.

=================================================================

SURVIVAL CHECK
=================================================================

                         Disciplined    Undisciplined    Compound
                         Gil            Gil              Nightmare
Scenario 1 (rally):     -$340 (3.4%)   -$745 (7.5%)      --
Scenario 2 (whipsaw):   -$385 (3.9%)   -$555 (5.6%)      --
Scenario 3 (flash+rev): +$685 (6.9%)   -$115 (1.2%)      --
Scenario 4 (execution):  -$180 addon    -$310 addon       --
Scenario 5 (chop):      -$425 (4.3%)   -$425 (4.3%)      --
Scenario 6 (compound):     --              --          -$840 (8.4%)

ABSOLUTE WORST CASE: Scenario 6 = -$840

After the worst scenario, Gil has: $9,160 remaining.

Can he still trade next week?
  YES. $9,160 is more than enough to run 1-contract spreads.
  A bear put spread costs $130-$300. A bear call spread requires
  $500 margin on a $5-wide spread. He has 18-70x the capital needed
  for a single position. He is not locked out of trading.

Is this amount recoverable?
  YES. $840 is 8.4% of the original $10K. A single good week with
  the same strategy (bear put spread + bear call spread, $500 risk)
  targeting +$500-$800 profit recovers the entire loss. Historically,
  the portfolio-of-three structure's gap fill scenario produces +$875
  on $495 risked. One winning week erases the worst week.

  Recovery timeline: 1-3 weeks if thesis eventually plays out.
  If Gil switches to pure theta selling (credit spreads only, no
  directional bets), he can grind $50-$100/week at low risk.
  Recovery in 8-16 weeks even without a directional win.

Emotional damage assessment: HIGH (not devastating)

  - Scenarios 1, 2, 5: Financial loss is manageable ($340-$555).
    Emotional impact is frustration and self-doubt. "Was the thesis
    wrong?" and "Should I have listened to the bull case?" Gil will
    want to revenge trade or quit. NEITHER is the right response.
    The right response: review the trade journal, identify ONE process
    error, fix it, and re-enter with the same risk budget next week.

  - Scenario 3: DEVASTATING emotional damage despite small financial
    loss (-$115). Seeing +$910 become -$115 will haunt Gil. This is
    the "I was right and still lost" scenario. It breaks traders
    because it attacks their CONFIDENCE, not their capital. Gil will
    question every future exit: "Am I selling too early? Too late?"
    This second-guessing lasts months.
    ANTIDOTE: The profit target was $10.00. The put hit $12.50. If
    Gil had sold at $10.00 (per rules), he banks $660. The rules
    WORKED. He didn't follow them. The lesson is NOT "the market is
    unfair." The lesson is "the rules exist for a reason."

  - Scenario 6: High emotional damage. Losing $840 (8.4%) in your
    first week feels like the account is dying. It is not. But Gil
    will feel sick. He needs someone (Borey) to tell him: "$840 on
    your first week, with multiple execution mistakes, and you still
    have $9,160? That is GOOD. Most new traders blow 20-50% in their
    first month. You survived."

=================================================================

CRITICAL TAKEAWAYS FOR GIL
=================================================================

1. THE STOPS ARE THE TRADE.
   Every scenario shows the same pattern: disciplined stops cut losses
   by 30-50% vs. freezing. The $670P stop at $1.40 saves $125-$200
   in every bearish-thesis-fails scenario. The bear call stop at $2.20
   saves $280 in a gap-up. Stops are not optional. They are the
   mechanism that keeps $480 of max risk from becoming $840.

2. THE 0DTE IS THE RISKIEST PIECE.
   In every scenario, the 0DTE strangle contributes -$30 to -$240 of
   loss and +$60 to +$250 of profit. Its expected value is roughly
   breakeven. But its EXECUTION RISK is the highest: it requires
   real-time decisions during the most volatile 30 minutes of the
   week. A new trader's first 0DTE during a PCE release is a recipe
   for emotional mistakes. Consider SKIPPING #3 entirely and running
   only #1 and #2 for a total max risk of $310 and zero intraday
   management pressure.

3. OVERPAYING INTO IV SPIKES IS A HIDDEN $100-$200 TAX.
   Scenarios 2 and 6 show that entering positions during a data-driven
   IV spike adds $70-$110 of unplanned risk. The entry plan says
   "after PCE settles" for a reason. If PCE is hot and SPY is moving,
   WAIT. The hardest thing to do when your thesis is being confirmed
   is to NOT act. But acting into a spike means buying expensive
   options that need an even bigger move to profit.

4. THE BEAR CALL SPREAD IS THE ANCHOR.
   In EVERY scenario -- rally, whipsaw, chop, crash -- the bear call
   spread either profits or loses a small, defined amount. It is the
   only position that profits in the "nothing happens" scenario (5).
   If Gil could only enter ONE position, this is it. $110 credit,
   73-77% win rate, $12-16/day of theta working for him.

5. $480 MAX RISK ON A $10K ACCOUNT IS SURVIVABLE UNDER ALL SCENARIOS.
   The defined-risk structures (spreads, long options with stops) mean
   that even the compound nightmare only costs 8.4% of the account.
   Gil can trade next week. He can trade for months. The account
   survives every scenario modeled here. That is the point of position
   sizing: not to maximize profit, but to ensure the ability to
   CONTINUE TRADING after being wrong.

6. THE BIGGEST RISK IS NOT THE MARKET. IT IS GIL.
   Scenarios 2, 3, and 6 show that emotional errors (not honoring
   stops, entering into IV spikes, freezing during 0DTE management,
   not taking profit at target) cost $400-$800 more than the market
   itself. The positions are well-designed. The risk is that the
   operator overrides the system.

   Borey said it best: "The first trade is not about profit. The grade
   is: did you follow the rules?"

=================================================================

BOTTOM LINE
=================================================================

  Best realistic outcome (Scenario 3, disciplined):  +$685  (+6.9%)
  Worst realistic outcome (Scenario 5, chop):        -$425  (-4.3%)
  True worst case (Scenario 6, everything breaks):   -$840  (-8.4%)
  Most likely outcome (Scenarios 2/5 blend):         -$300  (-3.0%)

  After the worst week imaginable, Gil has $9,160.
  He can still trade. He can still recover. He is still in the game.
  That is the ONLY metric that matters for week one.
