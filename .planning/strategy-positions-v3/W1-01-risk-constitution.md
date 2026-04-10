# RISK CONSTITUTION — V3 Swarm

**Effective:** Week of April 7-11, 2026
**Account:** $10,000
**Trader:** Gil (new, first live presentation to Borey)
**Market:** SPX ~6783 (SPY ~678), VIX ~20, Iran ceasefire structurally unenforceable
**Authority:** This document is law. No agent, trade proposal, or portfolio constructor may violate any rule below. A trade that requires an exception to any rule is a trade that does not get placed.

---

## V2 POST-MORTEM BINDING PRECEDENT

V2 produced 17 positions where every single one exceeded the stated 2% risk budget and then invented a justification. Borey's critique: "You set a rule. Then you find reasons the rule does not apply to THIS trade." This constitution exists to make that structurally impossible. There are no exception mechanisms. There is no "high conviction" override. The rule applies hardest when conviction is highest, because that is when you are most dangerous to yourself.

---

## 1. POSITION SIZE RULES

| Rule | Limit | Rationale |
|---|---|---|
| Max risk per position | **$200** (2.0% of $10K) | Borey's V2 critique: every position broke 2% and rationalized it. $200 is the hard ceiling. Not $201. Not "2.1% because the setup is great." |
| Max total portfolio risk | **$500** (5.0% of $10K) | A new trader's first week should not risk more than one bad restaurant dinner. $500 means surviving 20 consecutive max-loss weeks before ruin. |
| Max positions open simultaneously | **3** | More than 3 positions for a new trader creates management overload. V2 proposed 17. The correct number is 3. |
| Max correlated positions (same direction, same thesis) | **2** | If 2 of 3 positions are bearish, the third MUST be neutral or bullish-leaning. No "3 bearish positions that are really 1 bet sized 3x." |
| Min cash reserve (uninvested) | **$9,000** (90%) | Only $1,000 of buying power may be committed at any time, including margin held for credit spreads. This is a learning week, not a performance week. |
| Max single position as % of total risk budget | **50%** | No single position may consume more than $250 of the $500 risk budget. Forces diversification even within 3 positions. |

### Position Sizing Decision Tree

```
Proposed trade max loss > $200?  → REJECT. No exceptions.
Total portfolio risk with this trade > $500?  → REJECT. No exceptions.
This trade + existing trades = 3+ same-direction?  → REJECT.
Remaining cash after this trade < $9,000?  → REJECT.
This trade is > 50% of total risk budget ($250)?  → REJECT.
All checks pass?  → Proceed to entry rules.
```

---

## 2. STOP LOSS RULES

| Rule | Detail |
|---|---|
| Every position MUST have a hard dollar stop | Defined at entry. Written down. Non-negotiable. For debit positions: the stop is the debit paid (max loss = premium, no stop order needed if max loss < $200). For credit positions: stop at 2x credit received, executed as a limit buy order placed at entry. |
| Time stops | Every position must have a calendar exit date defined at entry. No position may be held past its time stop regardless of P&L. Time stop must be set at minimum 2 trading days before expiration (no holding into final 48 hours). |
| The stop is MECHANICAL | If the stop price is hit, the position is closed within 5 minutes. There is no "I'll wait and see." There is no "it's about to turn around." There is no "let me check Twitter first." The stop was set by a calm, rational version of Gil. The panicking version of Gil does not get to override it. |
| Stop-loss modification | Stops may only be moved in the profitable direction (trailing stop tighter). Stops may NEVER be moved further from current price. Moving a stop wider is equivalent to adding risk, which requires re-running the position sizing decision tree with the new risk amount. |
| Broker execution | For credit spreads: place the stop as a GTC limit order at the time of entry. Do not rely on mental stops for credit spreads. A mental stop on a new trader's first week is a suggestion, not a stop. |

---

## 3. ENTRY RULES

| Rule | Detail |
|---|---|
| No entries before 10:00 AM ET | The first 30 minutes of any session are dominated by overnight order flow, gap adjustments, and retail FOMO. Spreads are widest at open. A new trader entering at 9:31 AM is paying the maximum premium for the minimum information. Wait for price discovery. |
| No entries on Monday before 10:30 AM ET | Monday April 7 follows a weekend of ceasefire news. The opening will be chaotic. Iran headlines will hit pre-market. The first 60 minutes of Monday are noise, not signal. |
| No entries within 90 minutes after PCE/CPI release | PCE is Thursday April 9 at 8:30 AM ET. CPI is Friday April 10 at 8:30 AM ET. No entries until 10:00 AM ET on data days. The initial reaction reverses more than 50% of the time. Let the market digest. |
| No chasing | If the entry price exceeds $0.15 over the target limit price, skip the trade. Walk the limit by $0.05 increments, max 3 times, over 30 minutes. If unfilled after 3 walks, the market is telling you the price is wrong. Walk away. |
| No re-entry after a stop-out | If a position is stopped out, that thesis is dead for the week. No re-entering a modified version of the same trade. No "same spread but different strikes." No "same direction but different expiry." The stop-out is tuition. The lesson is not "try again immediately." |
| Scale-in rules | Not permitted this week. A new trader managing scale-in timing on top of position management on top of emotional regulation is three cognitive loads too many. Each position is entered as a single order at a single price. |
| Max entries per day | **2** | No more than 2 new positions opened in a single trading day. Prevents impulsive rapid-fire entries. |

---

## 4. EXIT RULES

| Rule | Detail |
|---|---|
| Take profit target | Close at **50% of max profit**. A put spread with $600 max profit closes when it shows $300 profit. A credit spread with $95 max profit closes when the spread can be bought back for $0.48. Do not hold for the last 50%. The last 50% of profit requires the last 90% of the risk. |
| Partial exits | Not applicable at 1-contract size. If any position is 2+ contracts: take half off at 50% max profit, let the remainder ride to 75% max profit or time stop, whichever comes first. |
| Time stop enforcement | Every position has a hard calendar exit. Debit spreads: close by 3:00 PM ET, 2 trading days before expiration. Credit spreads: close by 3:00 PM ET, 1 trading day before expiration. Never hold a short option position into expiration day. |
| CPI/PCE profit lock | If any position is showing 40%+ of max profit before a data release (PCE Thursday 8:30 AM, CPI Friday 8:30 AM), close it before the release. Do not gamble an unrealized gain on a binary event. A bird in the hand. |
| End-of-week rule | All positions expiring within the current week (Apr 7-11) must be closed by Thursday 3:00 PM ET. No Friday expiration holds for a new trader. Pin risk, gamma spikes, and assignment risk on Friday are for experienced traders. |
| Catastrophic exit | If the broker platform goes down during a data release: do not panic. Options positions have defined max loss. When the platform returns, execute your management rules. If max loss on any position exceeds $200 (it should not, per Rule 1), this is a constitution violation at entry, not an exit problem. |

---

## 5. CORRELATION LIMITS

| Rule | Limit |
|---|---|
| Max bearish positions | **2** |
| Max bullish positions | **2** |
| Min non-directional or opposing position | **1** of every 3 positions must be neutral (theta collection, iron condor) OR opposite direction from the other two. |
| Portfolio delta constraint | Net portfolio delta must stay between **-150 and +150** (SPY-equivalent). Two 1-lot bearish spreads typically produce -40 to -80 delta combined. This limit prevents stealth over-concentration. |
| Scenario correlation test | Before adding any position: answer this question — "In what scenario do ALL current positions lose money simultaneously?" If the new position also loses in that same scenario, it may only be added if total portfolio loss in that scenario stays under $400 (80% of risk budget). |
| All-positions-losing circuit breaker | If all open positions are simultaneously showing losses totaling more than $300 (60% of risk budget), close the worst-performing position immediately. Do not wait for the stop. The portfolio is telling you the thesis is wrong. |

---

## 6. EMOTIONAL RULES

| Rule | Detail |
|---|---|
| Check positions max **3 times per day** | 10:00 AM ET (market context), 1:00 PM ET (midday check), 3:30 PM ET (pre-close). Set these as phone alarms. Do not open the broker app outside these windows. Checking every 10 minutes does not make SPY move faster. It makes Gil move faster — toward a bad decision. |
| If down 3% on the portfolio ($300): | Stop opening new positions for the remainder of the week. Manage existing positions to their stops/time stops only. Do not try to "make it back." The week is a learning exercise, not a P&L exercise. |
| If down 4% on the portfolio ($400): | Close all positions. The week is over. Write down what happened. Walk away for 48 hours. Come back Wednesday of next week. The $400 loss is tuition, and the lesson is "I survived my first drawdown without blowing up." That is a passing grade. |
| If thesis changes (ceasefire becomes credible): | Close all bearish positions at market price within 30 minutes of the thesis change. A "credible" ceasefire means: (1) both Iran Supreme National Security Council AND IRGC Quds Force issue public statements confirming, AND (2) Houthi attacks cease for 48+ hours, AND (3) oil drops below $85. All three conditions. Not just a headline. |
| News blackout during market hours | No Twitter/X, no Reddit r/wallstreetbets, no FinTwit, no Discord trading channels (except Borey's channel) between 9:30 AM and 4:00 PM ET. Other people's opinions are noise. Your thesis and your risk rules are the only inputs that matter. |
| Post-trade journal | After every exit (win or lose), write 3 sentences: (1) What did I plan? (2) What did I actually do? (3) What will I do differently? This takes 60 seconds. It is the most valuable 60 seconds of the trading day. |
| Permission to do nothing | Doing nothing is always a valid action. If no setup meets the constitution, the correct trade count for the week is zero. Zero trades at zero risk is a better outcome than three trades that each required a rule exception. Borey respects discipline more than activity. |

---

## 7. INVALIDATION — HARD EXITS

These are non-negotiable. If any condition is met, close everything. Do not wait for confirmation. Do not check if it's a "false signal." Close first, analyze second.

| Trigger | Action | Rationale |
|---|---|---|
| SPX closes above **6850** (SPY above **$685**) | Close ALL positions within 30 minutes of close confirmation. | The gap-up rally is extending, not fading. The bear thesis is dead. SPX 6850 is 1% above current (6783) — a level the market should not reach if the gap is going to fill. If it gets there, the buyers are real and the ceasefire is being priced as durable. |
| SPX trades above **6900** (SPY above **$690**) intraday | Close ALL positions immediately, at market. | Do not wait for the close. This is a 1.7% rally from current levels. The gap-fill thesis is not just wrong — it is catastrophically wrong. Every bearish position is deep underwater and deteriorating. |
| VIX closes below **16** | Close ALL positions within 60 minutes. | VIX 16 means the market has decided there is no risk. The Iran situation is priced as resolved. The gap-fill catalyst (fear of ceasefire collapse) is gone. Vol compression kills both long premium (puts decay faster) and short premium strategies that rely on elevated vol for credit. |
| VIX spikes above **35** intraday | Close ALL credit spread positions immediately. Hold long debit positions (they benefit from vol expansion) but tighten time stops to next trading day close. | VIX 35 means a regime change. Credit spreads face unlimited gamma risk. Debit spreads benefit but should be monetized quickly before mean reversion. |
| Ceasefire upgraded to permanent (see criteria in Section 6) | Close ALL positions at market. | The entire geopolitical thesis is invalidated. Do not try to find a new thesis. Close and reassess next week. |
| Islamabad talks Saturday produce formal treaty | Close ALL positions at Monday open (10:00 AM ET after price discovery). | A formal treaty — not a "framework" or "extension" but an actual signed document with enforcement mechanisms — removes the structural instability that justifies the bear case. |
| Gil has lost $400 cumulative across all closed + open positions | Close ALL remaining positions. Trading is done for the week. | This is the portfolio circuit breaker. $400 = 4% of account = the maximum acceptable tuition for Week 1. Beyond this, the risk of emotional decision-making (revenge trading, doubling down) exceeds the risk of any individual position. |

---

## 8. STRATEGY STRUCTURE CONSTRAINTS

These rules govern WHAT TYPES of trades are permitted, not just their size.

| Rule | Detail |
|---|---|
| Max legs per position | **2** (vertical spreads only). No butterflies, condors, diagonals, ratios, or any structure with 3+ legs. Borey's V2 critique: "You have never managed a multi-leg position through a volatile session." Two legs. That's it. |
| No naked short options | Every short option must be paired with a long option of the same type (put or call) at a wider strike. No naked puts. No naked calls. No ratio spreads with uncovered legs. The account is $10K. Naked exposure is not permitted at any size. |
| No 0DTE trades | No positions with 0 days to expiration at entry. Minimum DTE at entry is **3 trading days** (approximately 4-5 calendar days). 0DTE requires millisecond execution discipline that Gil does not have. |
| Min DTE at entry | **4 calendar days**. This ensures at least 2 full trading days of time stop buffer before the "no holding into final 48 hours" exit rule kicks in. |
| American vs European style | SPY options are American style (early assignment risk on short legs). If any short leg goes more than $2 ITM, close the spread. Do not wait for assignment. Assignment on a $10K account can create a margin call that forces liquidation at the worst prices. |
| Commission check | If total round-trip commissions (entry + exit) exceed 3% of the position's max profit, the trade is too small to be worth the friction. At ~$0.65/contract/leg, a 2-leg spread costs $2.60 round trip. Max profit must exceed $87 for the trade to pass this test. |

---

## 9. CATALYST CALENDAR — BLACKOUT ZONES

No entries during these windows. Existing positions follow their management rules.

| Date | Event | Time (ET) | Blackout Window | Notes |
|---|---|---|---|---|
| Thu Apr 9 | PCE Price Index | 8:30 AM | 8:00 AM - 10:00 AM | No new entries. Manage existing per exit rules. |
| Fri Apr 10 | CPI Report | 8:30 AM | 8:00 AM - 10:00 AM | No new entries. Manage existing per exit rules. |
| Sat Apr 11 | Islamabad Talks | All day | N/A (market closed) | Review Sunday evening. If formal treaty: close Monday at 10:00 AM. |
| Mon Apr 7 | Post-ceasefire open | 9:30 AM | 9:30 AM - 10:30 AM | Extended blackout. Let 60 min of price discovery occur. |

---

## 10. ENFORCEMENT — HOW THIS CONSTITUTION IS APPLIED

1. **Every trade proposal from any Tier 3 agent MUST include a "Constitution Compliance" section** that maps the proposed trade against every rule in Sections 1-8. Missing or incomplete compliance sections result in automatic rejection.

2. **The Tier 4 adversarial agents will specifically test for constitution violations.** Their first check is not "is this a good trade?" but "does this trade violate any constitutional rule?" If yes, the trade is dead regardless of its merit.

3. **The Tier 5 portfolio constructor may NOT approve a portfolio that violates any rule.** If the best portfolio still violates a rule, the correct output is fewer positions or no positions.

4. **No agent may grant an exception.** There is no "override" mechanism. There is no "Agent 7 approves a waiver." The constitution is amended only by rerunning the Risk Framework tier with new market conditions, which requires Gil and Borey to agree on changed circumstances.

5. **If a trade looks amazing but violates the constitution, the correct action is: do not place the trade.** Write it down. Paper trade it. Learn from it. Place it next week with a constitution that accommodates it — if, after reflection, it still looks amazing.

---

## SUMMARY — THE FIVE NUMBERS THAT MATTER

```
Max risk per trade:          $200  (2% of account)
Max total portfolio risk:    $500  (5% of account)
Max concurrent positions:       3
Weekly loss circuit breaker: $400  (4% of account — close everything)
Thesis invalidation:         SPX 6850 close / SPX 6900 intraday / VIX < 16
```

**This document is the first output of the V3 swarm. Every agent that follows inherits these constraints. Every trade that follows must survive these rules. The constitution does not care about conviction, edge, or how good a setup looks. It cares about survival.**

*"The goal of Week 1 is not to make money. The goal is to prove to Borey that Gil can follow rules under pressure. The P&L is a side effect of discipline."*
