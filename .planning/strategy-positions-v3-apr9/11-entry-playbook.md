# 11: Minute-by-Minute Execution Playbook (Thursday Apr 9 -- Monday Apr 14)

**Date:** 2026-04-09
**Account:** $10,000 | Risk budget: $500 max | Per-position: $200 max
**SPY:** $679.58 | VIX: ~20 | PCR: 1.324 (extreme fear)
**GEX:** Floor $670 | Ceiling $685 | Flip $658.66 | Max pain $671
**Dealers:** LONG GAMMA at $679.58 (dampening moves)

---

## ASSUMED PORTFOLIO (3-4 positions from 8 candidates)

The portfolio constructor will likely pick from these. This playbook covers
all plausible combinations. The most probable portfolio:

| Slot | Position | Risk | Entry Window | Priority |
|------|----------|------|-------------|----------|
| **A** | Bear call credit spread $683/$688 (02) | $130 | **TODAY 10:00-10:30 AM ET** | URGENT -- time-sensitive, theta starts now |
| **B** | CPI strangle $670P/$685C (05) | $200 | **TODAY 2:00-3:30 PM ET** | Enter at IV trough before CPI premium builds |
| **C** | Put debit spread $670/$660 (01) OR Diagonal $670/$660 (08) | $185-200 | Today 1:15-2:00 PM ET or Friday post-CPI | Flexible -- can wait for CPI |
| **D** | USO oil $80C/$86C (04) OR Contrarian bull $680/$687C (07) | $135-160 | Today 10:00-11:30 AM ET | Independent of SPY |

**Max 3 positions open simultaneously.** Total risk must stay under $500.

### Portfolio Combinations That Fit the Constitution

```
Combo 1 (BEARISH + EVENT):   Bear call ($130) + Strangle ($200) + Put spread ($200) = $530 FAILS
Combo 2 (BALANCED):          Bear call ($130) + Strangle ($200) + Contrarian bull ($135) = $465 PASSES
Combo 3 (THESIS + HEDGE):    Bear call ($130) + Diagonal ($185) + Contrarian bull ($135) = $450 PASSES
Combo 4 (OIL + EVENT):       Bear call ($130) + Strangle ($200) + USO ($160) = $490 PASSES
Combo 5 (MINIMALIST):        Bear call ($130) + Strangle ($200) = $330 PASSES (2 positions, room for Friday add)
```

**Recommended: Combo 5 on Thursday. Add a 3rd position Friday after CPI clarity.**

This is the safest play because:
1. Bear call enters NOW and starts earning theta today ($14-18/day).
2. Strangle enters at the Thursday IV trough and captures CPI as a free catalyst.
3. Friday post-CPI, you pick the 3rd slot based on what CPI told you:
   - Hot CPI --> add put spread or diagonal (bearish thesis confirmed)
   - Cool CPI --> add contrarian bull (squeeze thesis confirmed)
   - Inline CPI --> add USO (independent thesis, unaffected by CPI)

---

## THURSDAY APRIL 9 (Today -- PCE done, market open)

### 7:00 AM PT / 10:00 AM ET: BEAR CALL ENTRY WINDOW OPENS

**This is the first and most time-sensitive action of the day.**

PCE blackout expired. The 90-minute post-data window is over. Bear call
credit spread premium is at its highest right now -- PCE non-event means
IV is crushing on the call side but not yet fully deflated.

**Actions (10:00-10:30 AM ET / 7:00-7:30 AM PT):**

1. Pull up SPY. Check the number.
   - SPY below $681: **PROCEED.** The $680 call wall is holding.
   - SPY $681-$682: Proceed with caution. Reduce starting limit to $1.20 credit.
   - SPY above $683: **DO NOT ENTER.** Short strike is ATM. Wait for pullback below $681.

2. Pull up SPY Apr 17 $683C/$688C spread. Look at the natural (mid) price.
   - Credit at mid >= $1.25: Place limit to SELL at $1.25.
   - Credit at mid $1.15-$1.24: Place limit at the mid.
   - Credit at mid < $1.05: **SKIP.** Premium too thin. R:R degraded.

3. Order placed. Set a timer for 10 minutes.
   - Filled? --> Go to step 4.
   - Not filled after 10 min? Walk to $1.20. Wait 10 min.
   - Not filled? Walk to $1.15. Wait 10 min.
   - Not filled at $1.10 after 30 min? Walk to $1.10. Final walk.
   - Not filled at $1.05 after 40 min total? **ABORT.** Cancel order. Move on.

4. **IMMEDIATELY after fill:** Place GTC limit buy at $2.60 (2x stop).
   This is not optional. This is the stop loss. It goes in before you
   close the order ticket. Before you check Twitter. Before you text Borey.
   The stop goes in NOW.

5. Set alerts:
   - Spread value at $0.65 (50% profit target -- CLOSE)
   - SPY at $683 (short strike -- elevated monitoring)
   - SPY at $685 (close for assignment risk + Constitution Section 7)

6. Record in your trade log:
   ```
   Position: Bear call $683/$688 Apr 17
   Fill credit: $____
   Stop: GTC buy at $2.60
   Profit target: Buy at $0.65
   Max loss: $130
   Max profit: credit received
   ```

**Time check: It should be ~10:30-10:45 AM ET / 7:30-7:45 AM PT.**

---

### 7:30-8:00 AM PT / 10:30-11:00 AM ET: OPTIONAL -- USO OR CONTRARIAN BULL

If Combo 4 or Combo 3 is your plan, this is the window for the 3rd position.
**If using Combo 5 (recommended), SKIP THIS. Wait for Friday.**

**USO entry (if selected):**
1. Check crude oil. Is it $92-$97? If yes, proceed.
   - Crude above $100: SKIP. Easy move is gone.
   - Crude below $90: SKIP. Ceasefire holding better than expected.
2. Pull up USO May 16 $80C/$86C spread. Target $1.60 debit.
3. Walk: $1.60 --> $1.65 --> $1.70 --> $1.75 max. Over 30 minutes.
4. Do NOT pay more than $1.75.
5. If filled: set alerts at crude $100, $103, $88. Set Apr 25 time stop calendar reminder.

**Contrarian bull entry (if selected):**
1. Check SPY. Still $677-$682? If yes, proceed.
   - SPY below $672: SKIP. Bear thesis winning, no hedge needed.
   - SPY above $685: SKIP. Ceiling broken, calls already expensive.
2. Pull up SPY Apr 25 $680C/$687C spread. Target $1.35 debit.
3. Walk: $1.35 --> $1.40 --> $1.45 --> $1.50 max. Over 30 minutes.
4. If filled: set alerts at SPY $683 (partial profit), $687 (full profit), $672 (invalidation).

---

### 8:00 AM PT / 11:00 AM ET: PAUSE

Nothing to do here. The bear call is working (or was skipped). The market
is in mid-morning chop. Do NOT watch the screen. Do NOT second-guess.

**Set an alarm for 9:45 AM PT / 12:45 PM ET.** Close the trading platform.
Go do something else.

---

### 9:45 AM PT / 12:45 PM ET: PRE-STRANGLE ASSESSMENT

Come back to the screen. Check three numbers:

1. **SPY price.** Write it down: $____
   - If SPY moved $8+ from $679.58 (below $671 or above $688): The event
     already happened. The strangle strikes may be misaligned. **ABORT STRANGLE.**
   - If SPY is between $673 and $686: Strangle strikes ($670P/$685C) are
     well-positioned. Proceed.

2. **VIX level.** Write it down: ____
   - VIX below 16: No event risk priced. Strangle will bleed. **ABORT.**
   - VIX above 30: Premiums inflated. Strangle will cost $3.50+. **ABORT.**
   - VIX 17-25: Goldilocks zone. Proceed.

3. **Bear call position value.** Write it down: Spread at $____
   - If bear call is already at 50% profit ($0.65): CLOSE IT. Take the win.
   - If bear call is at a loss (spread above $1.60): Monitor. Stop is in place.
   - If bear call is steady (~$1.10-$1.30): Normal. No action.

---

### 10:15 AM PT / 1:15 PM ET: PUT SPREAD ENTRY WINDOW (if using Combo 1 or entering today)

**Only enter the put spread today if you have risk budget room AND the
strangle is NOT your plan.** If Combo 5 (bear call + strangle), skip this
and go to the strangle entry at 11:00 AM PT.

If entering put spread $670/$660 today:
1. Place limit at $1.80 debit for 1x SPY Apr 17 $670P/$660P.
2. Walk: $1.80 --> $1.90 (at 1:30 PM ET) --> $2.00 max (at 1:45 PM ET).
3. Hard ceiling: $2.00. At $2.01, walk away.
4. If filled: place GTC sell at $6.00 (50% profit target).
5. Set alerts: SPY at $670, $665, $660, $685.

---

### 11:00 AM PT / 2:00 PM ET: CPI STRANGLE ENTRY WINDOW OPENS

**This is the second critical action of the day.**

The IV trough of the week is RIGHT NOW. PCE is 5.5 hours ago (fully
digested). CPI event premium has NOT yet been bid up -- most overnight
CPI positioning builds between 3:30 PM ET today and Friday pre-market.
You are buying the strangle at the cheapest point before CPI.

**Actions (2:00-3:30 PM ET / 11:00 AM - 12:30 PM PT):**

1. Confirm abort conditions are clear:
   - [ ] SPY has NOT moved $8+ from prior close
   - [ ] VIX is between 16 and 30
   - [ ] SPY is between $665 and $690
   - [ ] Total portfolio risk with strangle stays under $500
     (Bear call $130 + strangle $200 = $330. PASSES.)

2. Pull up SPY Apr 16 $670P quote. Write down bid/ask: ____/____
   - Mid price: $____
   - Place limit BUY at mid. Example: mid = $1.20, limit $1.20.

3. Pull up SPY Apr 16 $685C quote. Write down bid/ask: ____/____
   - Mid price: $____
   - Place limit BUY at mid. Example: mid = $0.80, limit $0.80.

4. Walk each leg independently:
   - Put: $1.20 --> $1.25 --> $1.30 --> $1.35 max (3 walks, $0.05 each)
   - Call: $0.80 --> $0.85 --> $0.90 --> $0.95 max (3 walks, $0.05 each)
   - Combined ceiling: $2.30 total. If both legs fill above $2.30 combined, you overpaid.

5. Both legs must fill within 20 minutes of each other.
   - One leg fills, other stuck after 20 min + 3 walks: **CLOSE the filled leg. Stand down.**

6. If both fill, record:
   ```
   Position: CPI Strangle $670P/$685C Apr 16
   Put fill: $____
   Call fill: $____
   Total cost: $____
   Max loss: $____ (the total cost)
   Profit target: $4.00 combined (sell both legs)
   Kill loser: When SPY commits $4+ in one direction for 30 min
   ```

---

### 12:30 PM PT / 3:30 PM ET: LAST CHECK BEFORE CLOSE

**Three things to verify:**

1. **All open positions are recorded** with entry prices, stops, and targets.
   Print or screenshot your position screen.

2. **Bear call GTC stop at $2.60 is active.** Check the order status. If it
   says "pending" or "working," it is live. If it disappeared, re-enter it NOW.

3. **Portfolio risk tally:**
   ```
   Bear call:  $130 risk
   Strangle:   $200 risk (or actual cost if less)
   3rd pos:    $____ (if entered)
   TOTAL:      $____ (must be <= $500)
   Remaining risk budget for Friday: $____ (= $500 - total)
   ```

4. **Set overnight alerts:**
   - SPY futures at $685 (if breaks overnight, bear call thesis weakening)
   - SPY futures at $670 (if breaks overnight, put thesis activating)
   - Crude oil at $100 (ceasefire stress)
   - Crude oil at $88 (ceasefire holding)

5. **Prep for tomorrow.** Write down on a physical notepad or sticky:
   ```
   CPI FRIDAY APR 10 -- 5:30 AM PT / 8:30 AM ET
   
   Consensus (look up tonight):
     Core CPI MoM: ____% expected
     Core CPI YoY: ____% expected
     Headline CPI MoM: ____% expected
   
   HOT = above consensus by 0.1%+ --> SPY down, put wins, call dies
   COOL = below consensus by 0.1%+ --> SPY up, call wins, put dies
   INLINE = within 0.05% --> IV crush, both legs bleed
   
   BLACKOUT: No trading until 7:00 AM PT / 10:00 AM ET
   ```

6. **Close the trading platform.** Do not check futures tonight. The positions
   are set. The stops are in. CPI is tomorrow. You cannot affect the outcome.
   Sleep.

---

## FRIDAY APRIL 10 (CPI at 5:30 AM PT / 8:30 AM ET)

### 5:00 AM PT / 8:00 AM ET: WAKE UP. DO NOT TRADE.

Turn on CNBC or pull up a news feed. CPI drops in 30 minutes.

**What to have ready:**
- Your notepad with consensus numbers
- Phone with SPY futures chart open (not your broker -- do NOT log into the broker yet)
- Coffee

### 5:30 AM PT / 8:30 AM ET: CPI DROPS

**Write down the actual numbers immediately:**
```
Core CPI MoM: ____% (consensus was ____%)  --> HOT / COOL / INLINE
Core CPI YoY: ____% (consensus was ____%)
Headline CPI MoM: ____% (consensus was ____%)
```

**Watch SPY futures for the next 30 minutes. Do not trade. Just observe.**

What to look for in the first 30 minutes (5:30-6:00 AM PT):

| SPY Futures Move | What It Means | Impact on Your Book |
|-----------------|---------------|---------------------|
| Gaps down $3-5 to $674-676 | Hot CPI, moderate selloff | Strangle put leg gaining. Bear call safe. Good. |
| Gaps down $8+ below $672 | Hot CPI, strong selloff | Strangle put leg printing. Bear call safe. Consider closing call leg of strangle pre-open. |
| Gaps up $3-5 to $683-685 | Cool CPI, relief rally | Strangle call leg gaining. Bear call under pressure but below $683. Monitor. |
| Gaps up $6+ above $685 | Cool CPI blowout | Strangle call leg printing. **Bear call stop ($2.60) may trigger at open.** Prepare mentally. |
| Flat (+/- $1.50) | Inline CPI | IV crush incoming. Both strangle legs bleed. Bear call benefits from IV crush. Mixed. |

### 6:00 AM PT / 9:00 AM ET: PRE-MARKET ASSESSMENT

Write down:
```
SPY pre-market: $____
Direction from CPI: UP / DOWN / FLAT
Magnitude: $____ move
VIX futures: ____
```

**Decision tree for the CPI STRANGLE (before market opens):**

```
Is the strangle showing 40%+ profit on the combined value
(worth $2.80+ if you paid $2.00)?
  YES --> Plan to close BOTH legs within 30 min of open (10:00 AM ET).
          Do not gamble profit on open volatility.
  NO  --> Hold through open. See 6:30 AM PT rules below.
```

**Decision tree for the BEAR CALL (before market opens):**

```
Is SPY futures above $683 (your short strike)?
  YES, and holding --> Your GTC stop at $2.60 will handle this at open.
                       Do nothing manually. Let the stop work.
  YES, but fading --> Market may pull back below $683 by 10:00 AM.
                      Wait. Do not panic-close before the stop triggers.
  NO (SPY below $683) --> Bear call is safe. No action needed.
```

### 6:30 AM PT / 9:30 AM ET: MARKET OPENS

**Do NOT trade in the first 30 minutes.** Constitution Rule: no entries
before 10:00 AM ET. This also means no reactive exits before 10:00 AM ET
unless a GTC stop triggers automatically.

Watch for:
- Does the CPI gap hold or reverse? Write down: SPY at 9:30 = $____, SPY at 9:45 = $____, SPY at 10:00 = $____
- Does your bear call GTC stop trigger? If the broker fills you at $2.60, you are out. Loss = $130. Record it. Move on.
- Is the strangle winning? Which leg? Note: "Put winning" or "Call winning" or "Both flat"

### 7:00 AM PT / 10:00 AM ET: FIRST ACTION WINDOW

**This is the first moment you are allowed to make discretionary trades.**

**STRANGLE MANAGEMENT:**

Check strangle value. Write down: Put @ $____, Call @ $____, Total = $____

| Total Strangle Value | Action |
|---------------------|--------|
| **$4.00+** | **CLOSE BOTH LEGS NOW.** Take the 100%+ return. Profit: $200+. Do not wait for more. |
| **$3.00-$3.99** | Hold. Strong but not at target. Reassess at 3:30 PM PT for weekend hold decision. |
| **$2.00-$2.99** (near entry cost) | Hold. CPI was inline or small move. Weekend catalyst (Islamabad) is still ahead. |
| **Below $1.50** | CPI crushed IV. Assess: is one leg dead and the other alive? If one leg is worth $0.05 or less, sell it (recover $5). Hold the surviving leg as a directional bet through the weekend. |

**Has SPY committed to a direction? ($4+ sustained move for 30+ minutes, confirmed by volume):**

- SPY below $674 and falling: The put is working. **SELL the $685 call.** Recover $0.05-$0.20. Let the put ride with a mental trailing stop at 50% of its current value.
- SPY above $682 and rising: The call is working. **SELL the $670 put.** Let the call ride.
- SPY between $674-$682: No commitment. Hold both legs.

**BEAR CALL MANAGEMENT:**

- Was it stopped out at open? If yes, record the loss and move on. You now have $130 more risk budget available.
- Is SPY below $681? Bear call is safe. No action. Theta is grinding for you.
- Is SPY $681-$683? Monitor. Set a 30-minute timer. If SPY holds above $683 for 2+ hours, consider closing early to cut the loss.

**3RD POSITION ENTRY (if you went with Combo 5 -- 2 positions Thursday):**

Now you have CPI data. Use it.

| CPI Outcome | What the Market Told You | 3rd Position to Add |
|------------|--------------------------|---------------------|
| **HOT** (Core MoM 0.4%+, YoY ticks up) | Inflation sticky, oil spike in the data, stagflation narrative | **Put spread $670/$660 (01)** or **Diagonal $670/$660 (08)**. Bearish thesis confirmed. Enter after 10:00 AM ET. Target $1.80 debit for put spread, $1.85 for diagonal. Wait for any post-CPI put IV spike to fade (could take until 11:00 AM-12:00 PM ET). |
| **COOL** (Core MoM 0.2% or below, YoY ticks down) | Disinflation, Fed can cut, risk-on | **Contrarian bull $680/$687C (07)**. SPY will push toward $685 ceiling. Enter at $1.35 debit. The strangle call leg is already winning -- the contrarian bull doubles down on the squeeze scenario. |
| **INLINE** (Core MoM 0.3%, as expected) | No new information. Weekend is the catalyst. | **USO oil $80C/$86C (04)**. Independent of CPI. The oil thesis is about Hormuz, not inflation prints. Enter at $1.60 debit. OR: skip the 3rd position entirely and hold 2 positions through the weekend. |

**Entry for 3rd position: 7:00-8:30 AM PT / 10:00 AM-11:30 AM ET.**

Use the same entry procedures from the individual position files:
- Put spread: limit $1.80, walk to $2.00 max. Hard ceiling $2.00.
- Diagonal: limit $1.85, walk to $2.00 max.
- Contrarian bull: limit $1.35, walk to $1.50 max.
- USO: limit $1.60, walk to $1.75 max.

After filling, record the trade and verify total portfolio risk stays under $500.

---

### 7:00 AM PT / 10:00 AM ET: MIDDAY CHECK

If no 3rd position to enter, this is a monitoring check only.

Check every open position. Write the values down:
```
Bear call spread: $____ (entry was $____)  --> profit/loss: $____
Strangle put: $____  Strangle call: $____  Total: $____ --> profit/loss: $____
3rd position (if any): $____ --> profit/loss: $____
Total unrealized P&L: $____
```

**Invalidation checks:**
- [ ] SPY above $685? --> Close bear call within 30 min (Constitution Section 7)
- [ ] SPY above $690 intraday? --> Close ALL positions immediately
- [ ] VIX below 16? --> Close ALL positions within 60 min
- [ ] VIX above 35? --> Close ALL credit spreads immediately
- [ ] Any single position loss exceeding its defined max? --> Should not be possible with stops in place

If all clear: **close the platform. Set alarm for 12:00 PM PT / 3:00 PM ET.**

---

### 12:00 PM PT / 3:00 PM ET: WEEKEND HOLD DECISION

This is the most important decision of the day. You are deciding what to
hold through a weekend that includes Islamabad talks on Saturday.

**For each position, run this decision tree:**

#### BEAR CALL SPREAD ($683/$688):

```
Spread buyable at $0.65 or less?
  YES --> CLOSE. Take 50% profit. Do not hold through weekend.

Spread between $0.66 and $1.30 (original credit)?
  --> HOLD. You are breakeven to profitable. Theta works over the weekend
      (~$0.04-0.06/day x 2 weekend calendar days = $0.08-0.12 of free decay).
      The $683 short strike is $3.42 above spot. Weekend gap through $683 is
      unlikely unless Islamabad produces a genuine breakthrough AND oil craters.

Spread above $1.30 (you are losing)?
  --> If spread at $2.00+: CLOSE. You are halfway to your $2.60 stop.
      Do not hold a losing credit spread through a binary weekend event.
  --> If spread at $1.31-$1.99: judgment call.
      SPY below $682? Hold. The wall held. Weekend likely helps.
      SPY above $682? Close. The wall is cracking.
```

#### CPI STRANGLE ($670P/$685C):

```
Total strangle value > $3.00 (profitable)?
  --> HOLD through weekend. This is the whole point -- CPI + Islamabad.

Total strangle value $1.20-$3.00 (small loss to small gain)?
  --> HOLD. Weekend theta cost is ~$0.48 ($0.24/day x 2 days). The Islamabad
      binary event is worth more than $0.48 of theta.

Total strangle value $0.50-$1.20 (significant loss)?
  --> CLOSE THE LOSING LEG. Keep the surviving leg as a directional punt.
      If put is worth more: sell the call, hold the put through the weekend.
      If call is worth more: sell the put, hold the call.
      This reduces weekend exposure and salvages the winning direction.

Total strangle value below $0.50?
  --> CLOSE EVERYTHING. Do not hold $50 of options through a weekend
      hoping for a miracle. The theta will eat the remaining value even
      if the catalyst fires.
```

#### 3RD POSITION (if held):

Apply the same logic from the individual position file (01, 04, 07, or 08).
Key question: is it profitable or losing? If profitable, hold. If losing
AND the thesis is weakened by what CPI told you, close.

**After making all decisions, final Friday tally:**
```
HOLDING THROUGH WEEKEND:
  Position 1: _____________ Current value: $____ Risk: $____
  Position 2: _____________ Current value: $____ Risk: $____
  Position 3: _____________ Current value: $____ Risk: $____
  
CLOSED FRIDAY:
  Position: _____________ P&L: $____
  Position: _____________ P&L: $____

Weekend risk exposure: $____
```

---

### 12:30 PM PT / 3:30 PM ET: SET WEEKEND ALERTS AND WALK AWAY

**Alerts to set (phone push notifications, not email):**

1. SPY futures at $670 (gamma floor -- put thesis activating)
2. SPY futures at $685 (gamma ceiling -- bear call stress)
3. SPY futures at $660 (gamma flip zone -- major move)
4. SPY futures at $690 (Constitution invalidation -- close everything Monday)
5. Crude oil at $100 (ceasefire cracking)
6. Crude oil at $88 (ceasefire firming)
7. "Islamabad" or "Iran" Google News alert (set up now if not already)

**Log off. Close everything. Do not check again until Saturday news.**

---

## SATURDAY APRIL 12 -- ISLAMABAD TALKS

### What Is Happening

Iran ceasefire negotiation talks in Islamabad. Multiple parties involved.
Key question: does the IRGC (Islamic Revolutionary Guard Corps) participate?

### What Headlines to Watch (check news 2-3 times Saturday, not continuously)

| Headline Pattern | What It Means | Impact on Your Book |
|-----------------|---------------|---------------------|
| "Framework agreement reached" | Positive headline. Market will gap up Monday. **BUT:** Verify if IRGC is included. Without IRGC, the framework is paper. | Bear call: stressed. Strangle call leg: up. Put positions: down. **Do not panic.** Wait for details. |
| "IRGC participates in talks" | Genuine deescalation signal. This is rare and meaningful. Oil drops. SPY rallies. | This is the one scenario where all bearish positions lose. **Contrarian bull (if held) saves you.** If you don't hold the bull, accept the loss -- the stops protect you. |
| "Talks collapse" / "parties fail to agree" | Status quo. No ceasefire progress. Mildly bearish. | Bearish positions: slightly better. Strangle put leg: small gain. Oil: stable to up. |
| "IRGC absent from talks" / "military factions boycott" | Ceasefire structurally failing. This confirms the thesis. | Bearish positions WIN. Oil: UP (bullish for USO if held). SPY: DOWN Monday. |
| "Houthi attack during talks" / "Hormuz incident" | Ceasefire collapsing in real-time. Extreme bearish. | ALL bearish positions WIN BIG. Oil spikes. SPY gaps down Monday. Best case for the book. |
| "Supreme Leader health update" | Power vacuum news. Destabilizing. Bearish. | Adds uncertainty. SPY down. Bearish thesis strengthened. |

### Saturday Action Items

1. Check headlines 3 times: morning, midday, evening. Not more.
2. Write down: "Islamabad outcome: ____________"
3. Classify: BULLISH / BEARISH / NEUTRAL for Monday.
4. **Do not try to trade Sunday night futures.** You are not set up for that.
   Your positions are already placed. Let them work.

---

## SUNDAY APRIL 13

### 3:00 PM PT / 6:00 PM ET: FUTURES OPEN

CME equity futures open at 6:00 PM ET Sunday. This is the first market
reaction to Islamabad.

**What to do:**

1. Check SPY futures 30 minutes after open (6:30 PM ET). Write down: $____
2. Check the gap from Friday close. Write down: Gap = $____ (up/down)

| Sunday Futures Gap | What It Tells You | Monday Plan |
|-------------------|-------------------|-------------|
| SPY futures down $3-5 (around $674-676) | Islamabad failed or was inconclusive. Bearish. | Hold all bearish positions. Strangle put may be at target. Plan to close strangle put Monday morning at $4.00+ total. |
| SPY futures down $8+ (below $672) | Islamabad failed badly. Oil spiking. | This is the thesis playing out. DO NOT close anything tonight. Wait for Monday open to capture the full gap. Bear call at max profit. Strangle put printing. |
| SPY futures up $3-5 (around $683-685) | Islamabad produced a framework. Market optimistic. | Bear call approaching stop. **Do not pre-empt the stop.** Your GTC at $2.60 handles this. Strangle call leg gaining. Check if strangle total is at $4.00+ target. |
| SPY futures up $6+ (above $685) | Genuine breakthrough. IRGC participated. Oil crashing. | Bear call will stop out Monday. Loss = $130 (already defined). Strangle call should be printing. Contrarian bull (if held) is winning big. **Accept the bear losses -- they are sized for this.** |
| Flat (+/- $2) | Islamabad was a non-event. Weekend was noise. | All positions survive. Monday is a normal trading day. Theta continues working. |

3. Set your Monday morning alarm for 6:00 AM PT / 9:00 AM ET.
4. Write down your Monday plan based on what futures showed you.
   Do NOT trade Sunday night. Just observe and plan.

---

## MONDAY APRIL 14

### 6:00 AM PT / 9:00 AM ET: PRE-MARKET PREPARATION

**Before the bell, write down:**
```
SPY pre-market: $____
Change from Friday close: $____
VIX futures: ____
Crude oil: $____
Islamabad outcome (your classification): BULLISH / BEARISH / NEUTRAL
```

**Review your positions:**
```
Bear call $683/$688: Entry credit $____, current spread value (est): $____
Strangle $670P/$685C: Entry cost $____, current est value: $____
3rd position: Entry $____, current est: $____
```

### 6:30 AM PT / 9:30 AM ET: MARKET OPENS

**Do NOT trade.** Wait for 10:00 AM ET. First 30 minutes are noise,
especially after a weekend with a major catalyst.

Watch:
- Does the gap from Sunday night hold? Or is it fading?
- Write down: SPY at 9:30 = $____, 9:45 = $____, 10:00 = $____

### 7:00 AM PT / 10:00 AM ET: MONDAY MANAGEMENT -- POSITION BY POSITION

#### BEAR CALL $683/$688:

| SPY Level | Spread Est. Value | Action |
|-----------|-------------------|--------|
| Below $678 | $0.30-$0.50 | **CLOSE for 65-80% profit.** You are deep in profit and 3 DTE remaining. Take it. |
| $678-$681 | $0.65-$0.90 | Close at $0.65 (50% profit target). If not quite there, hold -- theta is aggressively decaying now (5 DTE). |
| $681-$683 | $0.90-$1.50 | Hold. Short strike not breached. But set a tighter mental alert: if SPY holds above $683 for 2 hours, close for a small loss. |
| $683-$685 | $1.50-$2.60 | **GTC stop at $2.60 handles this.** If it triggers, loss = $130. Recorded. Done. |
| Above $685 | $2.60+ (stopped) | Already stopped out. If stop missed (platform outage), close IMMEDIATELY at market. Constitution Section 7: close ALL positions within 30 min of SPY $685 close. |

#### STRANGLE $670P/$685C:

**If you already closed one leg Friday, you are holding a directional position. Manage accordingly:**

Holding the PUT only ($670P):
| SPY Level | Put Value Est. | Action |
|-----------|---------------|--------|
| Below $665 | $5.00+ | **SELL at market.** Profit: $380+. Outstanding result. |
| $665-$670 | $2.00-$5.00 | Hold with trailing stop at 50% of current value. The put is ATM to ITM. Let it work but protect gains. |
| $670-$675 | $0.80-$2.00 | Hold. Gamma floor at $670 is the thesis level. One more push needed. |
| Above $678 | $0.30-$0.80 | If value has decayed to $0.30 or below, close. Weekend catalyst failed to deliver for the put side. Recover what you can. |

Holding the CALL only ($685C):
| SPY Level | Call Value Est. | Action |
|-----------|---------------|--------|
| Above $688 | $3.00+ | **SELL at market.** Gamma ceiling broken. Take the win. |
| $685-$688 | $1.50-$3.00 | Hold with trailing stop at 50%. The ceiling is testing. |
| $682-$685 | $0.50-$1.50 | Hold. Close to the ceiling. One push needed. |
| Below $680 | $0.10-$0.50 | Close. Bull thesis dead. Recover pennies. |

Holding BOTH legs:
- Combined value at $4.00+: **CLOSE BOTH. Target hit.** Profit: $200+.
- Combined value $2.50-$3.99: Hold. Set Tuesday 10:00 AM as next check.
- Combined value $1.50-$2.49: If Monday is flat (no gap reaction), close the weaker leg. Hold the stronger.
- Combined value below $1.50: Close everything. Three catalysts (PCE, CPI, Islamabad) have passed. If none moved the needle, the strangle is dead.

#### 3RD POSITION (if held):

Run the management rules from the relevant position file:
- **Put spread (01):** Check-ins at 10:00 AM, 1:00 PM, 3:30 PM ET. If SPY below $665, spread is approaching 50% target ($6.00). Close.
- **Diagonal (08):** Long leg has 11 DTE. Short leg has 3 DTE. Position is aging well if SPY dropped. If SPY rallied, short leg decays for you. No urgent action unless SPY > $685.
- **USO (04):** Check crude oil. If above $100, approaching profit zone. If $103+, close at 50% target. If below $90, thesis weakening (but time stop is Apr 25 -- patience).
- **Contrarian bull (07):** If SPY above $683, consider taking partial profit (sell half at $2.70 if 100% return). If SPY below $672, close (invalidation).

---

### 10:00 AM PT / 1:00 PM ET: MIDDAY CHECK

Write down all position values. Quick scan:
- Any position at its profit target? Close it.
- Any position at its stop? Should have triggered. If not, close manually.
- Total portfolio unrealized P&L: $____

If everything is stable: **close the platform. Next check at 12:30 PM PT / 3:30 PM ET.**

---

### 12:30 PM PT / 3:30 PM ET: END OF DAY CHECK

Final check of the day. Write down closing values.

**Forward calendar:**
```
REMAINING SCHEDULE:
  Tue Apr 15: Bear call 2 DTE (close by 3:00 PM ET per constitution)
              Strangle 1 DTE on Apr 16 expiry (close by 3:00 PM ET)
  Wed Apr 15: Hard time stop for Apr 17 positions
  Wed Apr 23: Hard time stop for Apr 25 positions (diagonal, contrarian bull)
```

Set Tuesday alarms:
- 7:00 AM PT / 10:00 AM ET: Position check
- 10:00 AM PT / 1:00 PM ET: Position check
- 12:00 PM PT / 3:00 PM ET: **HARD CLOSE any Apr 17 credit spreads**
- 12:30 PM PT / 3:30 PM ET: **HARD CLOSE any Apr 16 strangle legs**

---

## CRITICAL RULES THAT APPLY EVERY DAY

These override everything above. If any trigger fires, act immediately.

| Trigger | Action | No Exceptions |
|---------|--------|---------------|
| SPY closes above $685 | Close ALL positions within 30 min | Constitution Section 7 |
| SPY trades above $690 intraday | Close ALL positions immediately at market | Constitution Section 7 |
| VIX closes below 16 | Close ALL positions within 60 min | Constitution Section 7 |
| VIX spikes above 35 | Close ALL credit spreads immediately | Constitution Section 7 |
| Any single position hits stop | Close that position within 5 min | Constitution Section 2 |
| Cumulative realized losses > $400 | Close ALL remaining positions. Week is over. | Risk budget protection |
| Platform outage during data release | Do not panic. Max loss is defined. Wait for platform. | Constitution Section 4 |

---

## WHAT "MONITOR" ACTUALLY MEANS (Anti-Vagueness Guide)

Throughout this playbook, "check" or "monitor" means these specific steps:

1. **Open your broker.** Look at the positions tab, not the chart.
2. **Write down three numbers:** SPY price, VIX level, each position's current value.
3. **Compare to your targets:** Is any position at its profit target? Its stop? Its invalidation level?
4. **If YES to any:** Execute the action described in this playbook. Not "think about it." Execute it.
5. **If NO to all:** Close the broker. You are done until the next scheduled check.
6. **Do not scroll Twitter.** Do not read options Reddit. Do not watch CNBC between check times. Information between scheduled checks is noise that creates anxiety and impulse trades.

**Check times (all times ET):**
- Thursday: 10:00 AM, 1:00 PM (pre-strangle), 2:00 PM (strangle entry), 3:30 PM (close)
- Friday: 8:30 AM (CPI -- watch only), 10:00 AM (first action), 3:00 PM (weekend decision), 3:30 PM (final)
- Saturday: 3x headline checks (morning, noon, evening)
- Sunday: 6:30 PM (futures open + 30 min)
- Monday: 10:00 AM, 1:00 PM, 3:30 PM

**That is 13 total check-ins over 4 days.** Not 130. Not "constantly." Thirteen.

---

## SUMMARY: THE FOUR DAYS IN ONE TABLE

| Day | Time (PT) | Action | Position |
|-----|-----------|--------|----------|
| **THU** | 7:00 AM | Enter bear call $683/$688 at $1.25 credit | Bear call |
| **THU** | 7:00 AM | Place GTC stop at $2.60 IMMEDIATELY after fill | Bear call |
| **THU** | 11:00 AM | Enter strangle $670P/$685C at ~$2.00 total | Strangle |
| **THU** | 12:30 PM | Verify all stops/alerts. Log positions. Close platform. | All |
| **FRI** | 5:30 AM | CPI drops. WATCH ONLY. Write down numbers. | -- |
| **FRI** | 7:00 AM | First action window. Manage strangle. Enter 3rd position based on CPI. | All |
| **FRI** | 12:00 PM | Weekend hold decision. Close losers, hold winners. | All |
| **FRI** | 12:30 PM | Set alerts. Log weekend exposure. Close platform. | All |
| **SAT** | 3x | Check Islamabad headlines. Classify: BULLISH/BEARISH/NEUTRAL. | -- |
| **SUN** | 3:30 PM | Futures open. Check gap. Write Monday plan. Do NOT trade. | -- |
| **MON** | 7:00 AM | Manage every position per decision trees above. | All |
| **MON** | 10:00 AM | Midday check. Close at targets. | All |
| **MON** | 12:30 PM | EOD. Set Tuesday hard-close alarms. | All |

---

*"A playbook is not a prediction. It is a set of if-then statements that make
the decision before the emotion arrives. Every 'what should I do?' is answered
before the market opens. You are not making decisions under pressure. You are
executing decisions made by a calm version of yourself, in advance."*
