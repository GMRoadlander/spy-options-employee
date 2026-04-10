# Position 18: Borey's Actual Trade — The One I'd Put On

**Date drafted:** 2026-04-06
**Market context:** SPX ~6783 after gap up from ~6610 on ceasefire headlines. VIX ~20. PCE Thursday 4/9, CPI Friday 4/10. Gap fill thesis to SPY ~661.

---

## The Honest Answer

I'm buying a put debit spread. That's it.

Not a butterfly, not a condor, not some multi-leg structure that looks impressive on a whiteboard. A simple bear put spread. Two legs. One debit. Defined risk. I know what I can lose before I enter.

I've been doing this long enough to know that complexity does not equal edge. The edge here is the thesis — the gap fills. The structure's job is to let me express that thesis with controlled risk and without overthinking it. A vertical spread does that.

Here's why I'm not just buying a naked put, even though that's what most people would expect: VIX is 20. That's not cheap. A naked put at 670 with 4-5 DTE is going to cost me roughly $4.80, and theta is going to eat $0.80-1.00 of that every single day SPY goes sideways. If the gap fills on Wednesday or Thursday instead of Monday, I've already bled 40-60% of my premium just waiting. With a spread, I'm selling some of that inflated premium back. My net theta exposure is cut in half. I can survive an extra day of waiting.

---

## POSITION: SPY Apr 11 673/663 Bear Put Spread

- **Buy:** SPY Apr 11 673 Put
- **Sell:** SPY Apr 11 663 Put
- **Width:** $10
- **Net debit:** ~$3.20 per spread ($320 per contract)
- **Contracts:** 3 ($960 total risk)
- **Max profit:** $6.80 per spread x 3 = $2,040 (SPY at or below 663 at expiry)
- **Max loss:** $960 (the debit — and I won't let it get there)
- **Breakeven:** SPY 669.80 at expiry

---

## Why These Strikes

**673 long leg.** Not ATM at 678. Not deep OTM at 665. I'm buying the 673 because it's ~$5 below current price, which means I'm not paying for the first 0.7% of the move. SPY has to actually start fading for this to matter, which is what I want — I'm not paying top dollar for a put that starts ITM. At 673, delta is around 0.35-0.38. That's the sweet spot. High enough delta that I participate in the move, low enough that I'm not overpaying.

**663 short leg.** This is $2 above the gap fill target of 661. I'm giving myself a $2 cushion below the target. If SPY fills the gap to 661, my spread is fully in the money. I don't need SPY to crash to 655 or 650 — I just need the gap to fill. The short leg at 663 captures nearly all of the expected move without requiring overshoot.

**$10 width.** Wider than the $5 spreads most people default to. Here's why: a $5 spread (673/668) costs maybe $2.00 and maxes at $3.00. That's 1.5:1. Not worth the commission and mental energy. A $10 spread costs $3.20 and maxes at $6.80. That's 2.1:1. Better risk/reward, and the extra $1.20 of premium I'm paying buys me $3.80 of extra profit potential. The math is just better on the wider spread when you have a specific downside target.

---

## Entry — Monday April 7

**When:** 9:45-10:15 AM ET. Not at the open. Never at the open.

Here's what happens Monday morning: the algos reprice everything in the first 10 minutes. Spreads are wide, fills are garbage, and whatever you think the fair price is, you're going to pay 20% more. I wait for the first 15 minutes of noise to settle.

Specifically, I'm watching for one of two things:

1. **SPY pops toward 679-681 on residual ceasefire optimism.** This is the ideal entry. The market gives me a gift — slightly higher SPY means slightly cheaper puts relative to the thesis. I buy into strength. This happens maybe 60% of Monday mornings after a big Friday gap up. Weekend longs want to take profits, but there's usually one more push up first.

2. **SPY opens flat or slightly red around 676-677.** The fade is already starting. I enter immediately because the gap fill move might be front-loaded. Waiting for a bounce that doesn't come means chasing.

**If SPY gaps down below 673 at open:** I do NOT chase. The spread is already partially in the money and will cost $4.50+. The risk/reward has shifted. I wait for a bounce, and if no bounce comes by 10:30, I skip the trade entirely. The move happened without me. That's fine. There's always another trade.

**Execution:** I place a limit order at $3.20. If I don't get filled in 15 minutes, I walk it up to $3.30. I will not pay more than $3.40. If SPY is moving fast and the spread is already at $3.60, I missed it. I walk away.

---

## Management — This Is Where It Actually Matters

Most people think trading is about entries. It's not. It's about what you do after you're in. Here's my actual process, minute by minute:

### Monday after entry (10:00 AM - 4:00 PM ET)

I set alerts and close the screen. Seriously. The trade has 4 DTE and needs a $17 move in SPX. That's not happening in one afternoon unless there's a headline. I check at 12:00 PM, 2:00 PM, and 3:45 PM. That's it.

- If SPY is above 679 by close: I'm annoyed but not worried. Day 1 of 4. The thesis is intact.
- If SPY is 675-679: Exactly where I'd expect. No action.
- If SPY is below 674: I'm already profitable. I note the spread value and do nothing.

### Tuesday — The Real Day

Tuesday is when gap fills typically start accelerating, for a mechanical reason: Monday is the re-pricing day. Tuesday is when institutional flows actually shift. Funds that were buying the ceasefire headline on Friday are now looking at the actual fundamentals — a 2-week pause, 3 ships, Iran still blocking. The smart money starts hedging.

- **If SPY breaks below 674:** I start watching more closely. The 673 put is going ITM. My spread is expanding. I do nothing except move my mental stop.
- **If SPY is 676-680:** The thesis is still alive but not confirmed. I hold. Theta is starting to eat the position but the spread mitigates this — my short leg is also decaying.
- **If SPY pushes above 682:** The gap is not filling this week. I close the position for whatever I can get. Probably $1.80-2.20. Loss of $300-420. I accept it and move on. I do NOT hold a losing position into PCE data hoping for a miracle.

### Wednesday — Decision Day

This is my line in the sand. By Wednesday close, SPY needs to be below 676 or I'm getting out. Here's why: Thursday is PCE and Friday is CPI. Two binary events back to back. If my trade isn't already working by Wednesday, I'm going to be holding through data events with 1-2 DTE, which is just gambling.

- **SPY below 672:** The trade is working beautifully. Spread is worth $4.50-5.00. I sell ONE of my 3 contracts here. That locks in $450-500 of proceeds, recovering roughly half my total risk. The remaining 2 contracts are now a free roll toward the gap fill.
- **SPY 672-676:** Hold. But I have Thursday morning as a hard exit if things don't improve.
- **SPY above 676:** Close everything on Thursday morning pre-PCE. Take the loss. It's probably $200-400 at this point. That's a bruise, not a wound.

### Thursday (PCE Day) — Only If Still In

If I'm still holding into Thursday, I have two contracts left and they're already profitable (because I only hold through here if Wednesday was below 672).

**Pre-PCE (8:30 AM ET data release):** I do NOT close before the print. This is where experience matters. The market prices in expected PCE. If I'm already bearish and short, a hot PCE is my friend — it accelerates the gap fill as the market reprices rate cuts. A cool PCE might bounce SPY temporarily but the gap fill thesis is structural, not data-dependent.

**Post-PCE, first 30 minutes:** This is where the day's direction is set. 
- If SPY drops hard (below 668): My spread is now worth $5.50-6.00. I sell the second contract. One left.
- If SPY bounces above 674: I close everything. Take the profit from the 3 contracts combined and go home.
- If SPY chops around 670-674: Hold the last 2 contracts into Friday, but I'm watching closely.

### Friday (CPI Day, Expiration) — Cleanup

I am NOT holding into expiration. Period. Full stop.

If I have any contracts left on Friday, I close them between 10:00-10:30 AM ET, after the CPI reaction settles but well before the 3:00 PM gamma circus. I don't care if the spread is worth $6.50 and I think it's going to $6.80. Those last 30 cents are not worth the assignment risk, the pin risk, or the stress.

---

## Why Not the Other Structures

I've traded all of these. Here's why I'm not using them here.

**Naked long put (Position 01).** I've lost money on more naked puts than I care to admit, and it's always the same story: I was right on direction but theta killed me before the move happened. A 670P costs $4.80 with 4 DTE. If SPY goes sideways for 2 days and then fills the gap on Thursday, that put has lost $1.60 to theta. My spread loses maybe $0.60 in the same period. I need the gap to fill — I don't need to be right about the exact day.

**Put butterfly centered at 661 (Position 05).** Beautiful on paper. 8:1 payoff if SPY pins 661. But SPY doesn't pin levels. It blows through them or reverses off them. A butterfly needs precision. A gap fill is a zone, not a number. SPY at 663 is a gap fill. SPY at 659 is a gap fill. The butterfly pays dramatically different amounts at those two levels. My spread pays the same.

**Selling premium (Position 03).** VIX at 20 is decent for selling, but I have a directional thesis. Selling a call spread or an iron condor is a bet that SPY stays in a range. I don't think it's going to stay in a range. I think it's going to 661. Premium selling is for when you don't have conviction. I have conviction.

**The strangle (Position 04).** A hedge-your-bets play. Buying a put and a call because "something's going to happen with PCE/CPI." I'm not paying for both sides. I have a thesis. If I'm wrong, I lose the debit and move on. I don't need a participation trophy on the upside.

---

## Position Sizing Logic

$960 on a $10K account is 9.6% of capital at risk. That's aggressive for most people. It's not aggressive for me, because:

1. **Max loss is truly max.** I can't lose more than $960. There's no scenario — not a flash crash, not a halt, not a gap — where I lose more. The spread is defined.
2. **I'm not going to lose the full $960.** My management rules above mean I'm closing for $1.80-2.20 if the thesis fails by Tuesday/Wednesday. Realistic max loss is more like $300-400.
3. **The thesis has an edge.** This isn't a coin flip. SPX gaps of this magnitude fill within 5 days roughly 65-70% of the time. I'm not betting randomly.
4. **One trade, one week.** This isn't a recurring weekly debit. It's a single thesis with a specific catalyst window. Size it accordingly.

If the account were $50K, I'd still put on 3 spreads. Maybe 5. The dollar amount changes; the structure doesn't. I size to the thesis, not the account.

---

## What I'm Really Watching

Not charts. Not indicators. I'm watching:

1. **Houthi/Iran headlines.** One ship turned back, one drone, one Iranian statement about "resuming operations" and SPY is at 668 by lunch. This is the primary catalyst for the gap fill and it's the one nobody can predict.
2. **Pre-market futures at 8:00 AM ET each morning.** If ES futures are red by more than 20 points, the gap fill is accelerating. If green by 20+, the market still believes the ceasefire. I adjust my aggressiveness accordingly.
3. **VIX direction, not level.** VIX at 20 is fine. VIX going from 20 to 23 in a morning means someone knows something. VIX dropping to 17 means the market is complacent and my thesis is losing oxygen.
4. **SPY 675 as the trapdoor.** Once SPY breaks and holds below 675, the gap fill becomes self-reinforcing — the people who bought the Friday gap up start panic-selling. 675 is the support that, once broken, becomes resistance. This is the level that turns my trade from "thesis" to "in progress."

---

## The Unsexy Truth

This trade is boring. Two legs. A debit. Close it when it works or when it doesn't. No adjustments, no rolling, no legging into a condor mid-week because "the setup changed."

That IS the edge. Every complex adjustment I've ever made in the middle of a trade has cost me money. The best trades I've ever had were simple structures with clear theses that I entered, managed with pre-set rules, and closed. This is one of those.

The gap fills or it doesn't. I risk $960 to make $2,040. If I'm wrong, I lose $300-400 after my management rules. If I'm right, I make $1,500-2,040. That's the trade.

---

## Summary Table

| Field | Value |
|---|---|
| Structure | Bear put spread (673P long / 663P short) |
| Underlying | SPY |
| Expiry | April 11, 2026 (Friday weekly) |
| Net debit | ~$3.20/spread (~$960 total for 3x) |
| Max profit | $6.80/spread ($2,040 total) |
| Max loss | $960 (debit), realistic ~$300-400 with management |
| Breakeven | 669.80 at expiry |
| R:R (max) | 2.1:1 |
| R:R (realistic) | ~4:1 to 5:1 (managed loss vs expected profit) |
| Thesis | Ceasefire gap (SPX 6610 to 6783) fills back to ~661 by April 11 |
| Conviction | High — gap fill + weak ceasefire + macro catalysts |
| Entry window | Monday April 7, 9:45-10:15 AM ET |
| Hard exit if wrong | Wednesday close if SPY > 676 |
| First profit take | Wednesday if SPY < 672 (sell 1 of 3) |
| Final exit | Friday 10:00-10:30 AM ET, no exceptions |
