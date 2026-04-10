# V3 Swarm Design: The Borey Perspective

**Author**: Borey (experienced SPY options trader, modeled from V1/V2 reviews)
**Date**: 2026-04-06
**Context**: Redesigning the 30-agent swarm that generates trade ideas for a gap fill thesis (SPY 678 to 661). Previous swarms (V1: 10 position agents, V2: 20 position + consensus agents) produced too many structures and not enough operational guidance.

---

## What Was Wrong With V1 and V2

I got handed 18 positions from V1/V2. Fifteen of them were different structures for the same thesis. I do not need 15 ways to be bearish. I need ONE way to be bearish with a complete operating manual for the week.

Here is what was missing:

1. **Nobody told Gil what to do at 9:31 AM Monday.** The positions had "entry windows" but no minute-by-minute playbook. A new trader staring at a screen at market open with $10K is not reading a 3-page entry section. He needs: "If SPY is at X, do Y. If SPY is at Z, wait."
2. **The exit plans were afterthoughts.** Every position had a "management" section that was really "here is how I hope it works out." Nobody modeled what happens on Tuesday when SPY is at 679 and the position is down 15% and Gil is panicking.
3. **No agent modeled the emotional reality.** Gil is going to wake up Wednesday with the trade down $200 and PCE in 24 hours. What does he DO? Not what does the math say -- what does he physically do with his hands on the keyboard?
4. **The conviction calibration was binary.** Every position assumed high conviction on the gap fill. Nobody asked: "What if you are only 60% sure? Does that change the structure, the size, or the entry timing?"
5. **No agent modeled the week as a SEQUENCE of decisions.** Each position was a snapshot. The real trade is a sequence: Monday entry, Tuesday assessment, Wednesday decision, Thursday catalyst, Friday cleanup. Five decisions, not one.

---

## V3 Swarm: 30 Agents, Organized by What Actually Matters

### SECTION A: RISK ARCHITECTURE (Agents 1-5)
*Before you decide what to trade, decide what you can lose.*

**Agent 1: Weekly Risk Budget**
- Input: $10K account, Borey's risk tolerance profile, current open positions (none)
- Output: Maximum dollars at risk this week ($300, $500, $1000?), maximum per-trade risk, maximum number of concurrent positions
- Key question: "If every single trade this week goes to max loss, what is the total damage? Can Gil sleep?"
- Borey's standard: A new trader should not risk more than 3% of account in a single week. That is $300. Period. If the swarm proposes $960 in total risk (like Position 18 did), the risk agent rejects it or flags it with a warning.

**Agent 2: Worst Week Stress Test**
- Input: All proposed positions from the other agents
- Output: A single table showing what happens if EVERYTHING goes wrong. Monday gaps up $10. Tuesday gaps up $5 more. Wednesday PCE is cold. Thursday CPI is cold. Friday SPY is at $695. What is the dollar damage?
- Also models: Broker margin calls (does Gil have margin? If not, does any proposed position require it?), assignment risk on short legs, what happens if Gil cannot access his account for 24 hours (internet outage, broker outage, medical emergency)
- Format: One page, one table. Total dollar loss in the worst realistic scenario. If that number is more than 5% of the account, the swarm failed.

**Agent 3: Correlation Auditor**
- Input: All proposed positions
- Output: Which positions fail at the same time? If Agent X proposes a put spread and Agent Y proposes a long put, those are correlated -- both lose if SPY rallies. The auditor must identify: "In a SPY rally to 690, Positions A, B, and D all lose. Combined loss: $X. Is that within the risk budget?"
- Borey's rule: If more than 2 positions share the same failure mode, you have 1 position and 2 duplicates. Cut the duplicates.

**Agent 4: New Trader Guardrails**
- Input: Every proposed position
- Output: Pass/fail on each position against these hard rules:
  - No naked options (short puts/calls without a spread)
  - No positions requiring Level 3+ approval
  - No positions with margin requirements exceeding available cash
  - No positions with more than 4 legs
  - No positions requiring intraday adjustment to stay within risk limits
  - No positions where the trader MUST act within a specific 5-minute window or face outsized loss
- If a position fails any rule, it is cut. No exceptions, no "well, if the trader is careful..." A new trader is not careful. That is what makes them new.

**Agent 5: The "Cancel the Trade" Agent**
- Input: The macro thesis (gap fill), current market conditions
- Output: A clear list of conditions under which Gil should NOT trade this week at all. Examples:
  - SPY gaps up above 685 Monday pre-market (thesis is dead)
  - VIX drops below 15 (market is not pricing any risk)
  - A second ceasefire agreement is announced (the geopolitical catalyst evaporated)
  - Gil slept 3 hours and feels anxious (emotional state matters)
- This agent's job is to give Gil PERMISSION TO DO NOTHING. The hardest thing for a new trader is sitting on their hands. This agent validates that decision.

---

### SECTION B: THESIS CALIBRATION (Agents 6-9)
*How sure are you? And what does that mean for the trade?*

**Agent 6: Base Case Thesis (High Conviction, 70%+)**
- Input: Gap fill statistics, ceasefire fragility, macro catalysts
- Output: The single best expression of "I believe SPY fills the gap to 661 this week"
- Structure: Bear put spread. Nothing else. Borey said it in Position 18: "complexity does not equal edge." The high-conviction trade is a vertical. Period.
- Must include: Exact strikes, exact debit, exact contracts, exact entry time, exact stop loss in dollars

**Agent 7: Moderate Conviction Variant (55-70%)**
- Input: Same thesis, but modeled with more uncertainty
- Output: A SMALLER version of the same trade. Not a different structure -- a smaller size. If high conviction is 3 spreads, moderate conviction is 1 spread. If high conviction risks $960, moderate conviction risks $320.
- Key insight from Borey: "If you are 60% sure instead of 80% sure, you do not buy a butterfly instead of a spread. You buy a SMALLER spread." Conviction calibration is about SIZE, not structure.

**Agent 8: Low Conviction Variant (50-55%)**
- Input: Same thesis, but "this could easily not work"
- Output: Either (a) do not trade, or (b) a single-contract, narrow spread with a tight stop that risks no more than $100. This is the "toe in the water" trade.
- Must explicitly say: "If you are below 50% conviction, DO NOT TRADE. Go watch. There is no shame in cash."

**Agent 9: Contrarian Case**
- Input: What if the gap does NOT fill? What if the ceasefire holds?
- Output: The one trade Gil should consider if he thinks the bulls are right. A simple bull call spread, sized at 1% of account, as a hedge or an alternative.
- Purpose: This agent exists so Gil knows what the OTHER side of the trade looks like. If the contrarian case is compelling, it should make him reduce the size of his bear trade, not add a bull trade on top. Diversification between bull and bear is usually just paying for both sides of a coin flip.

---

### SECTION C: ENTRY TIMING (Agents 10-15)
*The difference between a good trade and a loss is often 15 minutes.*

**Agent 10: Monday Morning Playbook**
- Input: SPY pre-market price at 8:00 AM, VIX futures, overnight headlines
- Output: A literal decision tree. Not a paragraph -- a flowchart:
  ```
  SPY pre-market > 684 --> DO NOT TRADE TODAY. Thesis weakened. Reassess Tuesday.
  SPY pre-market 679-684 --> Wait for 9:45 AM. Watch for pop toward 681. Enter on the first red 5-min candle after 9:45.
  SPY pre-market 674-679 --> Thesis may already be in motion. Enter at 9:45 AM. Do not wait for a pop.
  SPY pre-market < 674 --> You missed the entry. The spread costs too much now. DO NOT CHASE. Wait for a bounce to 675-676 to enter. If no bounce by 10:30, skip today.
  ```
- This is the most important agent in the swarm. Gil will read this at 8:30 AM Monday with coffee. It needs to be a decision tree, not an essay.

**Agent 11: Optimal Entry Price Calculator**
- Input: Current SPY price, VIX, target spread (e.g., 673/663 bear put spread)
- Output: Fair value for the spread at various SPY levels. "If SPY is at 678, the spread should cost $3.20. If SPY is at 680, it should cost $2.90. If SPY is at 675, it should cost $3.80."
- Also: Maximum price Gil should pay ("I will not pay more than $3.40. If the spread is at $3.60, I missed it.")
- Limit order walking rules: Start at mid. Wait 5 minutes. Walk up $0.05. Wait 5 more. Walk up $0.05 more. Stop at the max price. Walk away.

**Agent 12: Opening Range Behavior Model**
- Input: Historical Monday opens after large Friday gap-ups, VIX regime
- Output: What typically happens in the first 30 minutes after a gap-up weekend?
  - 60% of the time: one more push up in the first 10-15 minutes, then fade begins
  - 25% of the time: flat open, drift lower starting ~10:00 AM
  - 15% of the time: gap up continues all day (thesis is wrong, do not trade)
- Purpose: Gil needs to know that the first 15 minutes are NOISE, not signal. This agent quantifies that and gives him the patience to wait.

**Agent 13: Scale-In Decision Logic**
- Input: Risk budget, conviction level, number of contracts
- Output: Should Gil enter all at once or scale in? And if scaling in, what are the triggers for each tranche?
  - Tranche 1 (Monday 9:45 AM): 1 of 3 contracts. This is the probe.
  - Tranche 2 (Tuesday 10:00 AM, IF SPY closed Monday below 677): Second contract. Thesis is alive.
  - Tranche 3 (Wednesday 10:00 AM, IF SPY closed Tuesday below 675): Third contract. Thesis is confirming.
  - If SPY does not hit the trigger, that tranche is NEVER entered. You risk 1/3 instead of 3/3.
- Borey's take: "Scaling in is for when you are 60% sure and want to let the market prove the thesis before you commit full size. If you are 80% sure, just enter full size. Do not overthink it."

**Agent 14: Pre-Data Entry Timing (PCE/CPI)**
- Input: PCE release Thursday 8:30 AM, CPI release Friday 8:30 AM
- Output: If Gil does NOT have a position by Wednesday, should he enter fresh for PCE? The answer is almost always no for a new trader -- 0DTE and 1DTE positions around data releases are advanced plays. But if yes:
  - Structure: Buy a single ATM put 30 minutes after PCE drops, ONLY if the number is hot and SPY is selling off. Do not try to front-run the data.
  - Size: $100 max risk (1% of account). This is a kicker, not a core position.
  - Stop: 50% of premium. If the put drops from $2.00 to $1.00, you are out.

**Agent 15: "The Market Changed" Re-Entry Agent**
- Input: A position that was stopped out or skipped
- Output: Under what conditions should Gil re-enter? And critically, under what conditions should he NOT re-enter?
  - Re-entry is valid if: The thesis is still intact, the stop was triggered by normal volatility (not a trend change), and the new entry price is BETTER than the original
  - Re-entry is NOT valid if: The stop was triggered because SPY broke above 682 (thesis is dead), or if Gil is re-entering because he is frustrated about the loss (revenge trading)
  - Hard rule: Maximum 1 re-entry per week. If the second entry also stops out, the thesis is wrong. Accept it.

---

### SECTION D: EXIT MANAGEMENT (Agents 16-21)
*Entries are easy. Exits are where money is made or lost.*

**Agent 16: Partial Profit Taker**
- Input: Current position, current P&L, days remaining
- Output: When to take partial profits and how much.
  - Rule 1: When the position is up 50% of max profit and there are 2+ days to expiry, sell 1/3 of contracts. Lock in gains. The remaining 2/3 are now a free roll on top of the locked-in profit.
  - Rule 2: When the position is up 75% of max profit, sell another 1/3. You now have 1 contract riding for the full target.
  - Rule 3: NEVER hold for the last 10% of max profit. If the spread is worth $6.50 and max is $6.80, close it. Those 30 cents are not worth 2 more days of risk.
- Borey: "I have never regretted taking profit too early. I have regretted holding for more dozens of times."

**Agent 17: Stop Loss Enforcer**
- Input: Entry price, current position value, account risk budget
- Output: Exact stop loss levels -- not "if the thesis is invalidated" but "if the spread drops to $X.XX, sell. No discretion. No hoping."
  - Time-based stop: If the position is not profitable by Wednesday close, exit Thursday morning pre-PCE. Do not hold a losing directional bet through a data release.
  - Price-based stop: If SPY breaks above the invalidation level (e.g., 682) and holds for 2 hours, exit regardless of position value.
  - Dollar-based stop: If the position has lost more than the pre-defined max loss (e.g., $300), exit. Even if the thesis "might still work." The dollar stop is not negotiable.
- Format: Three numbers. Price stop: $X. Time stop: [day/time]. Dollar stop: -$X. Print them on a sticky note.

**Agent 18: Trailing Stop Logic**
- Input: A position that is currently profitable
- Output: How to trail the stop as the position moves in your favor.
  - Once profitable: Move stop to breakeven (entry price). You now cannot lose money on this position.
  - Once up 30%: Move stop to lock in 15% of profit.
  - Once up 50%: Move stop to lock in 30% of profit.
  - The trail is always 50% of current profit. You give back half to stay in the trade for more, but you NEVER give back all of it.
- Critical: Trailing stops on spreads are different from trailing stops on single legs. The agent must calculate spread value, not individual leg value.

**Agent 19: Expiration Day Protocol**
- Input: Positions expiring this week (Friday Apr 11)
- Output: Exact instructions for Friday:
  - Close ALL positions by 10:30 AM ET. No exceptions.
  - If a spread is partially ITM, close the whole spread as a unit. Do NOT close one leg and leave the other.
  - If a short leg is ITM and likely to be assigned, close it. Do not let assignment happen on a $10K account -- the capital impact is outsized for the account.
  - If the spread is worth less than $0.10, let it expire. The commission to close is not worth it.
  - NEVER hold into the 3:00-4:00 PM gamma ramp. Pin risk and gamma exposure in the last hour of expiration day have blown up accounts far larger than $10K.

**Agent 20: "I'm Down 30%" Emotional Protocol**
- Input: Gil is staring at a position that is down 30% and it is Tuesday.
- Output: A script. Literally a set of sentences Gil reads to himself:
  1. "The position is down $X. My pre-defined max loss is $Y. Am I at my max loss? No? Then the plan is still working."
  2. "Has the thesis changed? Is SPY above 682? Is VIX below 16? Has there been a ceasefire extension? If no, the thesis is intact. Hold."
  3. "Am I panicking because of the P&L or because of new information? If it is just the P&L, close the screen and come back in 2 hours."
  4. "If I close now, will I regret it tomorrow when the gap fill starts? If yes, hold. If no, close and accept the loss."
  5. "The worst outcome is not a losing trade. The worst outcome is turning a planned $300 loss into a $900 loss by removing my stop."
- This agent is not about math. It is about behavioral finance. The best exit plan in the world fails if the trader panics and deviates.

**Agent 21: Thursday/Friday Catalyst Exit Matrix**
- Input: Positions still open going into PCE Thursday / CPI Friday
- Output: A decision matrix based on data outcomes:
  ```
  PCE HOT + SPY drops:    Hold bearish positions, trail stops. Take partial profit if >50% max.
  PCE HOT + SPY flat:     Market already priced it. Your position does not benefit. Tighten stop.
  PCE COLD + SPY rallies: Close bearish positions immediately. The macro thesis flipped.
  PCE COLD + SPY flat:    Hold. The gap fill thesis is structural, not data-dependent.
  PCE INLINE:             No change. The real move comes from CPI Friday. Hold to your plan.
  ```
  Same matrix for CPI Friday, but with the added constraint: "Close everything by 10:30 AM regardless."

---

### SECTION E: SCENARIO MODELING (Agents 22-26)
*What specifically happens in the real world, not in theory?*

**Agent 22: Gap Fills on Monday -- What If It Happens Fast?**
- Input: SPY gaps down Monday morning to 672
- Output: The gap fill is already 35% complete before Gil has even entered. What does he do?
  - Do NOT enter the originally planned spread at these prices -- it now costs $4.80 instead of $3.20
  - Consider a narrower spread (672/667) for less debit
  - Or: wait for a bounce to 675-676 and enter the original spread at a better price
  - Or: accept you missed it and move to the next setup
  - The key question: "Is the remaining move (672 to 661) big enough to justify a new entry?" Run the R:R at current prices.

**Agent 23: Ceasefire Headline Hits Mid-Session**
- Input: Tuesday at 1:00 PM, a headline drops: "Iran resumes uranium enrichment" or "Houthi drone strikes tanker in Red Sea"
- Output: What happens to Gil's position and what does he do?
  - SPY will spike down $3-5 in minutes. VIX will spike to 25+.
  - If Gil has a bear put spread, it is suddenly deep in the money. The temptation is to hold for more. The correct move: sell 50% of the position into the panic. Panic selling creates the best fills for profit-taking.
  - If Gil does NOT have a position: Do NOT enter during the spike. Spreads will be $0.30-0.50 wide. Fills will be terrible. Wait 30-60 minutes for the dust to settle. Then assess if the remaining move justifies entry.
  - If the headline is POSITIVE (ceasefire extended, Iran makes concessions): Close all bearish positions immediately. Do not wait. A positive headline when you are short is not "temporary" -- it reprices the entire thesis.

**Agent 24: The Chop Week**
- Input: SPY goes sideways between 675-680 all week. No catalysts land.
- Output: What is the P&L trajectory day by day?
  - Monday: Position entered at $3.20. SPY at 678. Spread worth ~$3.10. Down $30 (theta).
  - Tuesday: SPY at 677. Spread worth ~$3.00. Down $60.
  - Wednesday: SPY at 679. Spread worth ~$2.70. Down $150. THIS IS WHERE GIL PANICS.
  - Thursday (pre-PCE): SPY at 678. Spread worth ~$2.40. Down $240.
  - The message: In a chop week, a 4DTE spread loses 25% of its value to theta even if SPY barely moves. Gil needs to understand this BEFORE he enters. The chop week is the most likely scenario (40% probability) and the most psychologically difficult.

**Agent 25: VIX Spike / Crush Scenarios**
- Input: Current position, VIX moves from 20 to 25 (spike) or 20 to 16 (crush)
- Output: Impact on the spread:
  - VIX spike to 25: Both legs gain extrinsic value, but the long leg gains more (higher vega on ATM vs OTM). Net effect: spread widens slightly. Helpful but small -- maybe $0.15-0.25 per spread.
  - VIX crush to 16: Both legs lose extrinsic value. The long leg loses more. Net effect: spread narrows. Harmful -- maybe -$0.30-0.50 per spread. This is the silent killer: the market does not move but your spread loses value because volatility collapsed.
  - Key insight: A bear put spread is slightly long vega. A vol crush hurts you even if SPY drops. This is why Borey prefers 11 DTE over 4 DTE -- more time means less sensitivity to short-term vol moves.

**Agent 26: The Black Swan Agent**
- Input: SPY crashes 5%+ in a single day (flash crash, major geopolitical escalation, liquidity crisis)
- Output: What happens to each proposed position?
  - Bear put spread: Hits max profit. You cannot make more than the width minus the debit. Close immediately -- do not hold hoping for more.
  - Long put: Uncapped downside profit. But SPY halts trigger. Gil might not be able to exit during the halt.
  - Credit spreads (short call side): These are fine, they profit on down moves.
  - Credit spreads (short put side): These blow up. If Gil has a short put spread that is now deep ITM, close it immediately and accept the loss.
  - The message: In a crash, defined-risk positions protect you. Undefined-risk positions destroy you. This is why every position in the portfolio must be defined-risk.

---

### SECTION F: SYNTHESIS AND DELIVERY (Agents 27-30)
*Turn 26 agents of analysis into one page Gil can print and tape to his monitor.*

**Agent 27: The One-Pager**
- Input: All outputs from Agents 1-26
- Output: A single page with:
  - THE TRADE: Structure, strikes, debit, contracts (one line)
  - THE NUMBERS: Max loss in dollars, target profit in dollars, breakeven price (three numbers)
  - THE PLAN: Monday-Friday, one line per day (five lines)
  - THE STOPS: Price stop, time stop, dollar stop (three numbers)
  - THE KILL SWITCH: Conditions under which you close everything and walk away (three bullets)
- This page should fit on a sticky note. If it does not fit on a sticky note, the trade is too complicated for a new trader.

**Agent 28: Borey's Review Simulator**
- Input: The one-pager from Agent 27 and all supporting analysis
- Output: What Borey will ask when Gil presents this, and the answers:
  - "What is your max loss?" --> "$X" (one number, no hedging)
  - "What happens if you are wrong?" --> "I lose $X and I am out by [day]. No further damage."
  - "Why this structure and not a [simpler/cheaper] one?" --> One sentence.
  - "What if I told you the ceasefire was going to hold?" --> "I would [reduce size / not trade / hedge]. Here is how."
  - "Show me your worst day this week." --> "Wednesday, down $X, thesis intact, I hold because [specific reason]."
- Any question Borey asks that Gil cannot answer in one sentence means the trade is not understood well enough to execute.

**Agent 29: Monday Morning Email**
- Input: Final trade plan
- Output: The literal message Gil sends himself (or gets from the bot) Sunday night:
  ```
  MONDAY APR 7 TRADING PLAN
  
  Pre-market check (8:00 AM):
  - SPY futures: ___  (fill in live)
  - VIX futures: ___  (fill in live)
  - Kill if: SPY > 684 or VIX < 15
  
  9:30 AM: WATCH ONLY. Do not touch anything.
  9:45 AM: Check SPY price.
    - If 679-681: Wait for first red 5-min candle. Enter spread.
    - If 674-679: Enter spread now.
    - If > 681: Wait until 10:15. If still > 681, no trade today.
    - If < 674: Do NOT chase. Wait for bounce to 675-676.
  
  10:00-10:30 AM: If entered, set alerts:
    - SPY 682 = EXIT EVERYTHING (thesis dead)
    - SPY 675 = thesis confirming, do nothing
    - SPY 670 = consider partial profit
  
  10:30 AM - 4:00 PM: Close the screen. Check at 12, 2, 3:45. No trades.
  
  Worst case today: Spread down $0.20-0.40. Normal. Ignore.
  ```

**Agent 30: Portfolio Heat Map**
- Input: All proposed positions, scenarios from Section E
- Output: A simple grid showing how the combined portfolio performs across 6 scenarios:
  
  | Scenario | SPY End-of-Week | Portfolio P&L | Verdict |
  |----------|----------------|---------------|---------|
  | Gap fills fast (Mon-Tue) | 665 | +$X | Best case |
  | Gap fills slow (Thu-Fri) | 668 | +$X | Good |
  | Chop | 676-680 | -$X | Tolerable |
  | Rally to 685 | 685 | -$X | Stop triggered |
  | Rally to 695 | 695 | -$X | Max loss, defined |
  | Crash to 640 | 640 | +$X | Windfall |
  
  Six rows. Six dollar amounts. Gil sees exactly where he makes money and where he loses. No surprises.

---

## What This Swarm Does Differently Than V1/V2

### V1/V2 asked: "What structures can we build?"
### V3 asks: "What decisions does Gil face this week, and what should he do at each one?"

| V1/V2 Swarm | V3 Swarm |
|-------------|----------|
| 15 different structures | 1-3 structures, fully specified |
| Entry "windows" | Minute-by-minute decision trees |
| Management "if it works" | Management for EVERY scenario including loss |
| Risk as a section in each position | Risk as the FIRST 5 agents, before any position exists |
| No emotional modeling | Agent 20 is entirely about what to do when scared |
| Consensus by voting | Synthesis by compression to one page |
| "Present 3 options to Borey" | "Be ready to answer the 5 questions Borey will ask" |

### The philosophical shift

V1/V2 treated the swarm as a **research team generating options**. That is fine for a trader with 10 years of experience who wants to see the full possibility space.

V3 treats the swarm as a **coaching staff preparing a player for game day**. Gil does not need 15 plays. He needs 3 plays practiced to perfection, with a fallback for every scenario, and a coach whispering "stay calm, the plan is working" when things get ugly.

---

## Agent Dependency Map

```
[RISK: 1-5] --> feeds constraints to --> [THESIS: 6-9]
    |                                         |
    v                                         v
[ENTRY: 10-15] <-- uses thesis + risk limits
    |
    v
[EXIT: 16-21] <-- uses entry prices + risk limits
    |
    v
[SCENARIOS: 22-26] <-- models all positions against real-world events
    |
    v
[SYNTHESIS: 27-30] <-- compresses everything to deliverables
```

Risk agents run FIRST. They set the constraints. Everything downstream respects those constraints. If the risk budget says $300, no agent downstream proposes a position costing $500.

---

## Execution Order for the Swarm

**Wave 1 (parallel):** Agents 1-5 (risk architecture) + Agent 6-9 (thesis calibration)
These are independent. Risk agents do not need to know the thesis. Thesis agents do not need to know the risk budget. Run them simultaneously.

**Wave 2 (parallel, after Wave 1):** Agents 10-15 (entry timing) + Agents 22-26 (scenario modeling)
Entry timing uses the thesis from Wave 1. Scenario modeling uses the positions implied by the thesis. These two groups are independent of each other.

**Wave 3 (sequential, after Wave 2):** Agents 16-21 (exit management)
Exit management needs the entry prices from Wave 2 and the scenarios from Wave 2. Must wait.

**Wave 4 (sequential, after Wave 3):** Agents 27-30 (synthesis)
Synthesis needs everything. Runs last.

**Total waves:** 4
**Total agents:** 30
**Parallelism:** Waves 1 and 2 each run ~10 agents in parallel. Waves 3 and 4 are sequential but smaller (6 and 4 agents).

---

## What Borey Will See When This Is Done

A single document with:

1. **One trade.** A bear put spread. Specific strikes, specific debit, specific number of contracts.
2. **Five numbers.** Position size %, max loss in dollars, entry trigger price, stop price, target price.
3. **A Monday morning playbook.** A decision tree that fits on an index card.
4. **A day-by-day plan.** Monday through Friday, one line per day. What to do, what to watch, what to ignore.
5. **Three stops.** Price stop, time stop, dollar stop. On a sticky note.
6. **A "when it goes wrong" protocol.** Not theory -- a script.
7. **A heat map.** Six scenarios, six dollar amounts, no surprises.

That is what a profitable experienced trader wants to see from someone presenting a trade idea. Not 15 butterflies. Not 3 pages of Greek sensitivities. Not a clever multi-leg structure with a whiteboard-worthy payoff diagram.

One trade. Fully specified. Every decision pre-made. Every failure mode pre-modeled. Every emotional trap pre-addressed.

That earns trust.
