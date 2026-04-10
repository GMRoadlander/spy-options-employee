# 19 — Borey's Critique: The Swarm Got Out of Hand

**Date:** 2026-04-06
**Reviewer:** Borey (domain expert, 15+ years options trading)
**Context:** Gil generated 17 positions for a single gap-fill thesis (SPY 678 to 661). $10K account. New trader. I'm reviewing the collective output, not individual positions.

---

## The Blunt Version

Gil, you asked an AI to draft 17 different ways to bet on the same thing. That is not research. That is procrastination dressed up as due diligence. You have analysis paralysis. You could have spent this time learning to read a real order book, and instead you have a 200-page options textbook organized by position number.

Let me tell you what I see.

---

## 1. Positions That Are TOO COMPLEX for You

You are a new trader. You have never managed a multi-leg position through a volatile session. Here is what you should not touch.

### Position 05: Put Butterfly (30 contracts)

Thirty contracts. On a $10K account. The position costs $1,650 and requires SPY to land inside a 9-point window at expiry. You have never managed a 3-leg position through a CPI release, and you want to do it with 30 lots? The bid-ask spread on a 3-leg butterfly combo order will eat you alive on entry and exit. Market makers see a 30-lot butterfly from a retail account and they widen spreads because they know you will panic-exit at the worst time. The profitable range is $656.55 to $665.45 — SPY moves $8/day at VIX 20. Your entire profit zone is ONE NORMAL DAY of noise.

**Verdict: Absolutely not.**

### Position 17: Wide Butterfly (10 contracts)

Same problem as 05, just slightly less insane. 10 contracts on a 3-leg structure with a $12 profit window. You know what happens to butterflies in the last 2 days before expiry? Gamma turns them into slot machines. The position swings from +$3,000 to -$500 in an hour. You will not be able to sit still and watch that.

**Verdict: No. Maybe in 6 months when you have managed 20+ spread cycles.**

### Position 11: Broken Wing Butterfly

Three legs. Asymmetric wing widths. A downside max loss of $625 that occurs in a specific SPY zone ($653-$658) but not above or below. Try explaining that payoff diagram to yourself at 3:47 PM on a Thursday when SPY is at $657 and dropping. You will not remember which direction hurts you. I have seen experienced traders get confused by broken wings in live markets.

**Verdict: Too complex. The structure is smart but you are not ready for it.**

### Position 14: Diagonal Put Spread with Weekly Rolling

This position requires you to actively manage a roll every Thursday for 4 consecutive weeks. You will need to close the expiring short put, select a new strike based on current SPY level and VIX, calculate whether the cumulative credit covers your long put cost, and decide if the gap fill thesis is still alive. That is 4 separate trade management decisions, each with different strike selection logic, on a position whose P&L depends on the path SPY takes, not just the endpoint. You will forget to roll one week. Or you will roll to the wrong strike. Or SPY will be at $665 on expiry day and your short $668P will go ITM and you will panic because assignment on 2 short puts means $133,600 of SPY shares on a $10K account.

**Verdict: Excellent trade for someone with 50+ diagonal cycles under their belt. Not you. Not yet.**

### Position 16: Jade Lizard

The original draft could not even get the zero-upside-risk math right on the first try — it took three recalculations in the document itself. If the person DESIGNING the trade cannot get the structure correct without revisions, what chance does the person EXECUTING it have? The jade lizard requires a naked short put ($655 strike, needing $3,000-4,000 in margin per contract), a short call, and a long call. Three legs with a naked component. The margin requirements alone exceed what a $10K account can support at the proposed size. The document went from 5 sets ($16,375 margin) to 3 sets to 2 sets because the author kept realizing the account cannot support it.

**Verdict: This is a trade for a $50K+ account with Level 4 approval. Not yours.**

---

## 2. Positions with HIDDEN RISKS You Might Not Understand

### Position 06: 1x2 Put Ratio Spread — NAKED SHORT PUT

This is the most dangerous trade in the swarm. The document itself says the margin requirement is $39,600 for 3 spreads on a $10K account. It then says "adjusted to 1 spread" but even 1 spread requires $13,200 in margin. **You cannot trade this.** Your broker will reject the order.

But here is the hidden risk that the document buries in a table: if SPY crashes to $635, you lose $5,370. On a $10K account. That is 54% of your capital on a single trade that was supposed to have a $90 entry cost. The $90 debit makes it look cheap. It is not cheap. It is a naked short put with a long put stapled on top. The "9:1 reward-to-risk" headline only counts the debit as "risk." The REAL risk is the naked leg, and it is theoretically unlimited.

**Hidden risk: Account-destroying downside if your thesis overshoots.**

### Position 15: Put Backspread — THE VALLEY OF DEATH

Another trade that looks cheap ($195 debit for 3 backspreads) but has a max loss of $4,695 in the danger zone. The document acknowledges this and says "manage with Rule 2." Rule 2 says close if SPY is between $655-665 by April 18. But what if SPY is at $658 on April 15 and you think it is going lower? You will hold. You will tell yourself "it is about to break through." And then it does not, and you are staring at a $3,000 loss on what was supposed to be a $195 lottery ticket.

The backspread's danger zone ($650-$665) overlaps almost perfectly with the gap-fill target zone ($661). Think about that: the price range where your THESIS says SPY is going is the EXACT price range where this trade LOSES THE MOST MONEY. You are paying $195 to bet that SPY will skip past the gap-fill level and crash to $620+. That is not a gap-fill trade. That is a black swan trade disguised as a gap-fill trade.

**Hidden risk: Max loss zone overlaps with thesis target.**

### Position 10: Hedged Bearish — $1,000 at Risk (10% of Account)

The write-up says "10% of account — elevated but justified." No. On a new trader's first real trade, 10% of capital on a 3-leg structure is not justified by anything. The call kicker hedge is clever, but it costs $160 that only pays off if SPY rallies to $690+. In the chop scenario (SPY stays at $678), you lose the full $1,000. The document says chop is "the LEAST likely scenario" at 10-15%. I disagree. Chop is what happens most weeks. The market does not fill gaps on command. You could easily lose $1,000 on your first trade while the thesis remains technically alive — SPY just hasn't moved yet.

**Hidden risk: Worst case is the most common outcome (sideways), not the headline scenarios.**

### Position 04 and Position 12: Strangles / 0DTE Scalps

Both require you to make real-time decisions during the most volatile 30-60 minutes of the trading week (PCE and CPI releases). Position 12 explicitly says "exit everything by 10:30 AM." Do you know what happens to a new trader at 10:15 AM when one leg is up 80% and the other is dying? You freeze. You second-guess. You hold for "just 5 more minutes." By 10:45 the winning leg has reversed 40% and the losing leg is at zero. 0DTE options are for traders who have mechanical execution down to muscle memory. You do not.

**Hidden risk: Execution speed and emotional control requirements exceed new trader capability.**

---

## 3. The ONE Most Common Error Across All 17 Positions

**Every single position exceeds the stated 2% risk budget, and then rationalizes it.**

Let me list the excuses:

- Position 01: "1 contract at $480... strict 2% rule means stop at $2.80 for $200 loss." (Relies on a mental stop being honored. It won't be your first time.)
- Position 02: "The strict 2% rule ($200) would allow only a fractional contract. Option A: accept 4.8% risk."
- Position 04: "One strangle at $340... accept 3.4% risk. MPW's playbook uses 2-5%."
- Position 05: "30 contracts... ~15-20% of capital." (This is insane.)
- Position 06: "Margin requirement exceeds $10K account." (You literally cannot do this trade.)
- Position 08: "Adjusted: 1 contract at $335 max risk = 3.35% of account."
- Position 10: "$1,000 total risk... 10% of account."
- Position 11: "Max loss (downside) $625 = 6.25% of account."
- Position 14: "$720 total risk... 7.2% of account."
- Position 15: "Practical max loss $1,350... 13.5% of account."
- Position 16: "Margin required ~$6,200-8,200" on a $10K account.
- Position 17: "$900-1,200... 10% of capital."
- Position 18: "$960 on a $10K account is 9.6%."

You set a 2% risk rule. Not a single position respects it without either (a) relying on a stop loss that a new trader will not honor under stress, or (b) openly declaring the rule does not apply here because the setup is "high conviction."

This is the most common mistake in all of trading. You set a rule. Then you find reasons the rule does not apply to THIS trade. Then you do it again. And again. And after 5 trades at "just 5%, high conviction," you have lost 25% of your account and you are tilted.

**The rule exists for when you have conviction. That is when you need it most.**

---

## 4. If Gil Could Enter ONE Trade Tomorrow — What Structure?

**A bear put debit spread. 2 legs. Defined risk. No naked exposure. No rolling. No weekly management.**

Here is why, and this is not negotiable:

1. **It matches the thesis.** You think SPY fills the gap to ~661. A put spread profits from that move. End of story.

2. **Max loss is the debit.** There is no scenario — no flash crash, no VIX spike, no gap, no assignment — where you lose more than what you paid. You cannot blow up.

3. **You can calculate your P&L in your head.** At SPY 665, a 674/668 put spread is worth $6. You paid $1.30. Profit is $4.70. Done. No Greeks to track, no gamma flips, no vega exposure to worry about.

4. **It survives timing errors.** With Apr 17 expiry (11 DTE), the trade has time. If the gap fills Monday, great. If it fills Thursday after PCE, fine. If it fills next Wednesday, you still have time value.

5. **Exiting is one order.** Sell the spread. One ticket. Not "close leg 1, then leg 2, then leg 3, check if I need to roll, calculate my net credit." One order.

**Specific recommendation:**

```
BUY 1x SPY Apr 17 $674P / SELL 1x SPY Apr 17 $668P
Debit: ~$1.30 ($130 total)
Max profit: $470
Max loss: $130 (1.3% of account — ACTUALLY under 2%)
Breakeven: SPY $672.70
Entry: Monday Apr 7, 10:00-10:30 AM ET
Stop: Close if spread drops to $0.65 (50% loss = $65 realized loss)
Profit target: Close at $4.00 ($270 profit)
Time stop: Exit by Wednesday Apr 15 at 3:00 PM ET
```

This is the trade from Position 19-A. It is boring. It costs $130. The max profit is $470, which is not going to change your life. But it is a trade you can ACTUALLY MANAGE without panicking, without needing Level 4 options approval, without a margin account, and without watching the screen for 6 hours on PCE Thursday.

If you want to add a second position, add the bear call credit spread (Position 03-v2, $683/$688, 1 contract) on Thursday after PCE. It collects ~$110 in premium and wins if SPY stays below $683 — which it probably will regardless of whether the gap fills. Together, the two positions risk $240 and can make $580. That is the portfolio.

That is it. Two positions. Four legs total. Under 2.5% of account at risk.

---

## 5. Emotional Management — The Talk

Gil. Listen to me.

You are going to enter this trade and within 2 hours SPY is going to do something you did not expect. Maybe it rallies $3 on a headline about Iran "extending the ceasefire window." Maybe it drops $2 on a Houthi drone report and then reverses completely. Your position will be red. Maybe -30%. Maybe -50%.

Here is what you are going to feel: panic. Your chest will tighten. You will check the price every 90 seconds. You will open Twitter to see if anyone is talking about the ceasefire. You will start doing math in your head — "if I close now I only lose $60, but if I hold and it works I make $470." Then SPY drops $1 and you feel relief. Then it bounces $2 and the panic comes back worse.

**This is normal. Every trader feels this. The difference between a trader who survives and one who blows up is what you DO with that feeling.**

Here are the rules:

### Rule 1: The stop loss is not a suggestion.

You set $0.65 as the stop. If the spread hits $0.65, you close. You do not move the stop. You do not say "I'll give it one more day." You do not go on Reddit to find someone who agrees with you. You close. The $65 loss is the COST OF DOING BUSINESS. It is tuition. You are paying $65 to learn how the market moves. That is cheap.

### Rule 2: Being down 30% does NOT mean the trade is wrong.

A $1.30 spread that drops to $0.90 is not a failed trade. It is a trade that has not worked YET. SPY moving from $678 to $679 on Monday afternoon does not invalidate a gap-fill thesis that needs a week to play out. Check these things before you panic:

- Is SPY above $685? No? Then the thesis is alive.
- Has VIX dropped below 15? No? Then the market is not complacent.
- Is it past your time stop (Wednesday Apr 15)? No? Then you have time.

If the answer to all three is "no," then the THESIS HAS NOT CHANGED. Your P&L changed. Your thesis did not. Trade the thesis, not the P&L.

### Rule 3: Do NOT check the position more than 3 times per day.

Set alerts at your stop loss ($0.65), your profit target ($4.00), and at SPY $685 (thesis invalidation). Let the alerts do the watching. If no alert fires, the trade is working as designed and does not need your supervision.

Checking every 10 minutes does not make SPY move faster. It makes YOU move faster — toward a bad decision.

### Rule 4: When the trade is over, it is OVER.

Win or lose, when you close this position, close the chart, close the broker app, and do not re-enter. Do not "revenge trade" the same thesis if it stopped you out. Do not double down on the next trade because you are angry. Write down what happened, what you felt, and what you learned. Then walk away for 24 hours before even LOOKING at the market.

The biggest risk to your $10K account is not SPY rallying to $700. It is you, at 10:47 AM on a Thursday, with a losing position and a Twitter thread convincing you to "add to the winner" or "cut the loser and flip to calls." That moment is where accounts die. The stop loss saves you from the market. These rules save you from yourself.

### Rule 5: The first trade is not about profit.

Your first real trade is an exam in emotional regulation. The grade is not your P&L. The grade is:

- Did you honor the stop? Pass/fail.
- Did you follow the entry rules? Pass/fail.
- Did you avoid impulse decisions? Pass/fail.
- Did you close before the time stop? Pass/fail.

If you lose $65 but followed every rule, that is an A+. If you make $470 but held through a blown stop and got lucky, that is an F. Luck is not repeatable. Process is.

---

## Summary

| Question | Answer |
|---|---|
| Too complex for Gil? | 05 (30-lot butterfly), 06 (ratio w/ naked leg), 11 (broken wing), 14 (diagonal w/ rolls), 16 (jade lizard), 17 (10-lot butterfly) |
| Hidden risks? | 06 (unlimited downside), 10 ($1K in chop), 12 (execution speed), 15 (danger zone = thesis zone), 16 (margin exceeds account) |
| Most common error? | **Every position breaks the 2% rule and rationalizes it** |
| One trade for Gil? | Bear put spread $674/$668 Apr 17, $130 debit, 1.3% risk |
| Emotional management? | Honor the stop. Trade the thesis not the P&L. Check 3x/day max. First trade grades process, not profit. |

---

*"You don't need 17 positions. You need one position you understand completely and the discipline to manage it. Everything else is noise."*
