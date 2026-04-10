# V3 Swarm Design: 30 Agents — Risk Management First

**Date:** 2026-04-06
**Design philosophy:** Risk management is more important than trade selection. A great trade with bad risk management loses money. A mediocre trade with great risk management survives.
**Market context:** SPX ~6783 (SPY ~678), gap from ~6610 on fake ceasefire, Iran 31 armed services + Supreme Leader in coma, VIX ~20, PCE Thu, CPI Fri, $10K account, new trader.

---

## V1/V2 Post-Mortem: What Was Missing

V1: No Iran context, Fibonacci anchoring, pre-PCE entries (wasted theta), no risk framework, all positions correlated bearish.

V2: Fixed context and timing. Still missing: portfolio-level position sizing, correlation risk across positions, worst-case scenario planning, emotional management rules for a new trader, real-time adjustment triggers, and adversarial stress-testing.

V3 fixes all of this by inverting the priority: **risk management agents outnumber and outrank trade-drafting agents.** Every trade proposal must survive adversarial review before reaching the portfolio constructor.

---

## Architecture: 5 Tiers

```
TIER 1: RISK FRAMEWORK (Agents 1-7)
  Runs FIRST. Defines the rules every trade must obey.
  Output: The Risk Constitution — hard constraints no trade can violate.

TIER 2: MARKET CONTEXT (Agents 8-12)
  Runs SECOND. Establishes what the market is actually doing.
  Output: Regime assessment, key levels, catalyst calendar, volatility surface.

TIER 3: TRADE PROPOSALS (Agents 13-22)
  Runs THIRD. Drafts specific positions — bearish, neutral, bullish, hedge.
  Each trade MUST include its own risk management or it is rejected.

TIER 4: ADVERSARIAL REVIEW (Agents 23-25)
  Runs FOURTH. Tries to BREAK every proposed trade.
  Output: Kill list (reject), Fix list (revise), Pass list (approved).

TIER 5: PORTFOLIO CONSTRUCTION (Agents 26-30)
  Runs LAST. Combines surviving trades into a portfolio.
  Output: Final 3-5 positions for Gil to present to Borey.
```

---

## TIER 1: RISK FRAMEWORK (Agents 1-7)

These agents run BEFORE any trade is proposed. They define the rules of engagement. Their output is the "Risk Constitution" that every subsequent agent must obey.

---

### Agent 1: Position Sizing Architect
**Role:** Defines maximum position sizes, per-trade and portfolio-level risk budgets
**Specialty:** Kelly criterion, fixed-fractional sizing, account preservation math for a $10K account with a new trader
**Output:** The Sizing Rules document:
- Max risk per trade (% of account and dollar amount)
- Max total portfolio risk (% of account and dollar amount)
- Max number of concurrent positions
- Minimum cash reserve requirement
- Rules for sizing up vs. sizing down based on conviction level
- Specific guidance: a new trader should risk LESS than an experienced trader, not more
**Context they need:** $10K account size, new trader (first presentation to Borey), no margin beyond debit paid, broker commission structure (~$0.65/contract)

---

### Agent 2: Correlation Risk Analyst
**Role:** Identifies hidden correlations between proposed positions and enforces diversification
**Specialty:** Understanding that "3 bearish positions" is really "1 bearish position sized 3x" — correlation math, Greeks aggregation, scenario overlap
**Output:** Correlation Rules document:
- Max net delta exposure (portfolio level)
- Max percentage of portfolio that fails in the same scenario
- Required diversification: at minimum 2 of these 4 categories must be represented: {directional bearish, directional bullish, volatility expansion, theta collection}
- Correlation matrix template that Tier 3 agents must fill in
- Rule: if ALL positions lose money in the same scenario, the portfolio is too correlated
**Context they need:** V1 failure (all 20 positions were bearish, total correlation = 1.0), V2 improvement (added neutral/hedges but did not formally measure correlation), Greek aggregation concepts (portfolio delta, gamma, vega, theta)

---

### Agent 3: Worst-Case Scenario Planner
**Role:** Defines the 5-7 scenarios the portfolio MUST survive, and the maximum acceptable loss in each
**Specialty:** Tail risk, black swan scenarios, multi-event chains (e.g., ceasefire holds AND hot CPI AND VIX crush simultaneously)
**Output:** Scenario Survival Matrix:
- Scenario 1: Gap fills to 661 (thesis works) — acceptable P&L range
- Scenario 2: Ceasefire holds, SPY rallies to 690-695 (thesis fails completely)
- Scenario 3: Chop at 675-682 for 2 weeks (thesis is right but timing is wrong)
- Scenario 4: Flash crash to 640 (thesis over-delivers, black swan)
- Scenario 5: Hot PCE + hot CPI, SPY drops 3% then reverses on Fed pivot talk
- Scenario 6: Iran escalation headlines mid-week (VIX spike to 30+)
- Scenario 7: SPY gaps up Monday pre-market above 685 on ceasefire details
- For EACH scenario: max acceptable portfolio loss, which positions survive, which die
- Hard rule: worst-case total portfolio loss must not exceed [X]% of account (Agent 1 defines X)
**Context they need:** Iran geopolitical detail (31 branches, Supreme Leader in coma, ceasefire structurally unenforceable), macro calendar (PCE Thu 8:30 AM, CPI Fri 8:30 AM), VIX at 20, gap fill historical rates (65-70% for >2% gaps)

---

### Agent 4: Stop-Loss and Exit Rules Engineer
**Role:** Designs the exit framework — not just "where" but "how" and "when" stops are executed
**Specialty:** Stop-loss psychology, slippage in options (wide bid-ask kills naive stops), time stops vs. price stops, the difference between "I should stop out" and "I actually will stop out"
**Output:** Exit Rules Playbook:
- Price stop methodology: percentage of debit vs. absolute dollar vs. spread value
- Time stops: when to exit regardless of P&L (e.g., Wednesday before PCE if thesis not confirmed)
- Profit-taking rules: 50% of max? Scale out in thirds? One-and-done?
- Slippage budget: how much wider can the actual exit be vs. the planned exit?
- The "stop override" problem: explicit rules for when a new trader will be tempted to move/remove stops, and why they must not
- GTC order vs. mental stop: which is appropriate for each position type
- Catastrophic exit: what happens if the broker platform goes down during a data release?
**Context they need:** New trader psychology (first real money on the line), options bid-ask spreads at VIX 20 (~$0.05-0.15 for ATM SPY weeklies, wider for OTM), the fact that SPY options are penny-increment (good liquidity), broker limitations

---

### Agent 5: Emotional Management Rules Designer
**Role:** Creates the behavioral guardrails a new trader needs to survive the week emotionally
**Specialty:** Trading psychology, decision fatigue, FOMO, revenge trading, the specific emotional pattern of "I was right about direction but wrong about timing and now I'm panicking"
**Output:** The Emotional Playbook:
- Pre-market routine: what to check, what NOT to check, screen time limits
- Intraday rules: how often to look at P&L (answer: not more than 3x/day for swing trades)
- The "do nothing" checklist: situations where the correct action is no action
- Post-loss protocol: what to do if stopped out on Day 1 (answer: DO NOT re-enter a modified version of the same trade)
- The "it's working" trap: rules for when the trade is profitable but not yet at target (don't move profit targets further out)
- Social media / news blackout recommendations during market hours
- Decision journal template: 3 sentences before each trade, 3 sentences after
- The "Borey is watching" factor: how awareness of being evaluated changes behavior (it makes you trade smaller, which is actually correct)
**Context they need:** This is a new trader making their first real presentation to an experienced mentor (Borey). The emotional stakes are high. The financial stakes ($300-960) are manageable but feel enormous to someone new. Borey expects discipline, not brilliance.

---

### Agent 6: Margin and Capital Requirements Validator
**Role:** Ensures every proposed trade is actually executable in a $10K account with standard options approval
**Specialty:** Broker requirements, options approval levels (Level 1-4), margin math, buying power reduction, the practical reality that some "defined risk" trades still require margin holds
**Output:** Capital Feasibility Report:
- Each proposed trade: buying power required, options level required, margin impact
- Hard reject list: any trade requiring Level 4 (naked), portfolio margin, or margin beyond debit
- Cash reservation: how much capital must remain uninvested for emergencies
- Assignment risk: which positions have early assignment exposure and what happens if assigned on a $10K account
- Commission impact on small positions (when commissions > 2% of the trade value, the trade is too small)
**Context they need:** $10K account, assumed Level 2-3 options approval (spreads allowed, naked not allowed), standard broker commissions (~$0.65/contract/leg), SPY options are American-style (early assignment possible on ITM short legs)

---

### Agent 7: Risk Constitution Compiler
**Role:** Synthesizes Agents 1-6 into a single "Risk Constitution" document that ALL subsequent agents must obey
**Specialty:** Integration, conflict resolution (when Agent 1 says "max 3% risk" but Agent 3's worst case requires 5% to diversify properly), final authority on constraints
**Output:** THE RISK CONSTITUTION — a one-page set of hard rules:
- Max risk per trade: $[X]
- Max total portfolio risk: $[X]
- Max concurrent positions: [N]
- Required diversification: [rule]
- Mandatory stop-loss methodology: [rule]
- Mandatory exit timeline: [rule]
- Emotional guardrails: [rule]
- Capital/margin constraints: [rule]
- Scenario survival requirements: [rule]
- ANY TRADE THAT VIOLATES ANY RULE IS AUTOMATICALLY REJECTED
**Context they need:** Full output of Agents 1-6

---

## TIER 2: MARKET CONTEXT (Agents 8-12)

These agents establish the factual ground truth about the market. Their output feeds into every Tier 3 trade proposal.

---

### Agent 8: Geopolitical Regime Analyst
**Role:** Assesses the Iran ceasefire durability and probability of collapse scenarios
**Specialty:** Military intelligence interpretation, precedent analysis (2022 Ukraine false ceasefire, 2024 Gaza ceasefire), chain-of-command analysis for non-unitary actors
**Output:** Ceasefire Durability Assessment:
- Probability of ceasefire holding 1 week / 2 weeks / 1 month
- Most likely collapse triggers (rogue commander, Houthi faction, Israeli response to violation)
- Timeline of likely escalation — is collapse front-loaded (first 48 hours) or gradual?
- Impact on SPY: how many points of the gap are priced into the ceasefire, and how fast do they unwind?
- Key headlines to watch and their meaning
- Probability distribution: 60% bear (MPW's number) — does the intel justify more or less?
**Context they need:** Full Iran briefing: 31 armed services, Supreme Leader in coma, ceasefire structurally unenforceable, Houthi independence from Iranian command, 800+ ships still rerouting, oil at $94 after 16% crash, historical parallels

---

### Agent 9: Macro Catalyst Analyst (PCE + CPI)
**Role:** Assesses likely PCE/CPI outcomes and their market impact
**Specialty:** Economic data analysis, consensus estimates vs. whisper numbers, historical SPY reaction to PCE/CPI surprises, the interaction between geopolitical risk and macro data
**Output:** Data Release Playbook:
- PCE (Thursday 8:30 AM): consensus, range of estimates, what "hot" vs "cold" means for SPY
- CPI (Friday 8:30 AM): consensus, range of estimates, impact scenarios
- Interaction effects: what happens if BOTH are hot? If PCE hot but CPI cold?
- Historical: SPY average move on PCE day, CPI day, and the 2-day combined move
- Timing: how fast does SPY react (first 15 min), and does it reverse by close?
- Recommendation: should trades be entered before or after each data release?
**Context they need:** Current Fed funds rate expectations, market pricing for rate cuts, recent inflation trends, consensus estimates for this specific PCE/CPI, VIX at 20 (implied daily move ~1.25%)

---

### Agent 10: Volatility Surface Analyst
**Role:** Maps the current implied volatility surface and identifies where options are cheap/expensive
**Specialty:** IV rank, IV percentile, term structure (front-month vs back-month), skew (puts vs calls), the specific dynamics of VIX ~20
**Output:** Volatility Intelligence Report:
- Current IV rank/percentile for SPY (is VIX 20 "high" or "normal" historically?)
- Term structure: are front-month options more expensive than back-month? (Inverted = fear)
- Skew: how much more expensive are OTM puts vs OTM calls? (Steep skew = market hedging)
- Practical impact: which strategies benefit from current vol conditions?
  - If IV is high: selling premium is favored, buying premium is expensive
  - If IV is low: buying premium is cheap, selling premium gives little credit
  - If skew is steep: put spreads are more expensive, call spreads are cheaper
- Expected IV change through PCE/CPI: will vol expand or contract after data?
- Recommendation: which expiry dates offer the best value for the thesis?
**Context they need:** VIX at 20, historical VIX range for 2025-2026, SPY current IV by expiry (Apr 10, Apr 11, Apr 17, Apr 25), skew data if available

---

### Agent 11: Technical Levels and Structure Analyst
**Role:** Maps key support/resistance levels, gap zones, and market structure without anchoring to any single framework
**Specialty:** Multiple technical approaches (not just Fibonacci — also volume profile, prior highs/lows, gap zones, VWAP, GEX/DEX levels), explicit about which levels are "real" (high-volume) vs "theoretical"
**Output:** Key Levels Map:
- Gap zone: SPX 6610 to 6783 (SPY 661 to 678) — this is the void
- Support levels within the gap: where are the "shelves" where buyers might step in?
- Resistance levels above: where does the rally stall?
- Volume profile: where was actual trading volume concentrated before the gap?
- GEX/DEX levels: where are options dealers positioned? (These create mechanical support/resistance)
- The "trapdoor" level: below what price does selling become self-reinforcing? (Borey's view: SPY 675)
- Honest assessment: which levels actually matter and which are decoration?
**Context they need:** SPX/SPY price history for the 2 weeks before the gap, the gap itself (6610 to 6783 in one day), current price, MPW's 60% bear assessment, Borey's 675 trapdoor level, options open interest by strike (if available)

---

### Agent 12: Market Context Synthesizer
**Role:** Combines Agents 8-11 into a single Market Briefing that all trade-proposing agents receive
**Specialty:** Integration, resolving conflicting signals (e.g., strong bearish thesis but high IV making puts expensive), weighting factors by importance
**Output:** MARKET BRIEFING — one document with:
- Directional bias: bearish/neutral/bullish with probability weights (e.g., 60% bear, 25% chop, 15% bull)
- Timing: when the move is most likely to happen (PCE? CPI? Monday? Friday?)
- Volatility regime: what it means for strategy selection
- Key levels: the 3-5 levels that actually matter
- Catalysts: ranked by impact and timing
- The one thing that could make the entire thesis wrong
- What Borey and MPW think (explicitly stated, not buried)
**Context they need:** Full output of Agents 8-11, Borey's view (gap fill to 661, conviction high), MPW's view (60% bear, exhaustion at 6800)

---

## TIER 3: TRADE PROPOSALS (Agents 13-22)

Each agent proposes ONE specific trade with FULL risk management baked in. Every proposal must reference the Risk Constitution (Agent 7 output) and demonstrate compliance. Any trade that violates the Constitution is dead on arrival.

---

### Agent 13: Borey's Trade — The Put Debit Spread
**Role:** Designs the trade Borey would actually put on — simple, directional, defined risk
**Specialty:** Experienced trader's perspective: simple structures, wide strikes, thesis conviction, the "boring is profitable" philosophy
**Output:** One put debit spread with:
- Strike selection rationale (not Fibonacci — logic-based)
- Expiry selection (survive PCE + CPI, not too much DTE for theta)
- Size that fits the Risk Constitution
- Entry timing and limit price discipline
- Management rules: day-by-day decision tree (Tuesday if flat, Wednesday if still above X, Thursday post-PCE, Friday cleanup)
- The "I close it and walk away" exit — no adjustments, no rolling
- Risk Constitution compliance checklist
**Context they need:** Risk Constitution (Agent 7), Market Briefing (Agent 12), Borey's actual trade from V1/V2 (the 673/663 put spread concept), Borey's philosophy: "Complexity does not equal edge. The edge is the thesis."

---

### Agent 14: Borey's Hedge — What Borey Would Add If Forced
**Role:** Designs the ONE additional position Borey would add if told "you must hedge the portfolio"
**Specialty:** Borey's voice — reluctant hedging, minimal complexity, the "insurance you hope you never need" philosophy
**Output:** One hedge position that:
- Protects against the scenario where the put spread fails (rally to 690+)
- Costs as little as possible (Borey hates paying for hedges)
- Does not complicate the portfolio (2 legs maximum)
- Can be ignored if the thesis is working (no active management required)
- Honest assessment: "I'm adding this because Gil asked, not because I think I need it"
- Risk Constitution compliance checklist
**Context they need:** Risk Constitution (Agent 7), Market Briefing (Agent 12), Borey's trade (Agent 13 output), Borey's stated view that selling premium when you have directional conviction is a "hedge-your-bets play"

---

### Agent 15: Conservative Bear — The "I Can't Lose More Than $150" Trade
**Role:** Designs the most capital-efficient bearish trade for a new trader who is terrified of losing money
**Specialty:** Ultra-conservative sizing, narrow spreads, the "first trade" mentality where surviving matters more than profiting
**Output:** One bearish position with:
- Maximum possible loss under $150 (including slippage and commissions)
- Clear, simple structure (no more than 2 legs)
- Wide margin of safety on entry (OTM enough that you're not paying for time value)
- Realistic profit target (not a 10:1 lottery ticket)
- Management rules a genuine beginner can follow without panic
- Explicit: "This is the trade you put on if you want to learn without getting hurt"
- Risk Constitution compliance checklist
**Context they need:** Risk Constitution (Agent 7), Market Briefing (Agent 12), new trader psychology (first real money), the fact that Borey values discipline over size

---

### Agent 16: Aggressive Bear — The "Gap Fill Conviction" Trade
**Role:** Designs the highest-conviction bearish trade for maximum directional participation
**Specialty:** Aggressive but not reckless, wider spreads, longer DTE, more contracts — the "I believe this and I'm sizing accordingly" approach
**Output:** One aggressively bearish position that:
- Has higher dollar risk than Agent 15's trade (but still within Risk Constitution limits)
- Maximizes participation in a gap fill move (higher delta, wider spread, more gamma)
- Includes the specific scenario where this trade makes 3:1 or better
- Includes the specific scenario where this trade loses max — and why that max is acceptable
- Aggressive entry plan: where to enter, where to add, where to cut
- Risk Constitution compliance checklist
**Context they need:** Risk Constitution (Agent 7), Market Briefing (Agent 12), gap fill statistics (65-70% for >2% gaps), Borey's conviction level, Iran geopolitical detail

---

### Agent 17: Gamma Kicker — The PCE/CPI Catalyst Trade
**Role:** Designs a short-dated, high-gamma trade specifically for the PCE/CPI data releases
**Specialty:** 0-2 DTE options, gamma trading, event-driven positioning, the specific dynamics of data releases (front-loaded move, potential reversal)
**Output:** One gamma trade that:
- Uses Apr 10 or Apr 11 expiry (2-4 DTE at entry)
- Enters Wednesday afternoon or Thursday morning (just before PCE)
- Has the highest gamma-per-dollar of any position in the portfolio
- Explicitly acknowledges this is the most likely position to lose money (short-dated options have low probability of profit)
- Size is small enough that total loss is emotionally manageable ($75-125)
- Profit potential on a 2%+ move is 5:1 or better
- Risk Constitution compliance checklist
**Context they need:** Risk Constitution (Agent 7), Market Briefing (Agent 12), PCE/CPI playbook (Agent 9), VIX at 20 (implied daily move ~1.25%), options Greeks for 2DTE SPY puts/calls

---

### Agent 18: Theta Collector — The "Get Paid to Wait" Trade
**Role:** Designs a credit spread or iron condor that collects premium while the thesis develops
**Specialty:** Premium selling, probability-based trading, the specific appeal for a new trader: "I got paid to enter this trade"
**Output:** One credit trade that:
- Collects premium on day 1 (psychologically important for a new trader)
- Has >70% probability of profit based on current IV
- Profits from the PASSAGE OF TIME, not from a specific price move
- Works even if SPY chops sideways for 2 weeks (the "nothing happens" scenario)
- Short strikes are placed above strong resistance (call side) or below strong support (put side)
- Has a clear 50% profit-take rule and a 2x credit stop-loss rule
- Risk Constitution compliance checklist
**Context they need:** Risk Constitution (Agent 7), Market Briefing (Agent 12), volatility surface (Agent 10), key levels (Agent 11), the $686 resistance level, IV rank/percentile

---

### Agent 19: Neutral/Range — The "Thesis Is Wrong" Trade
**Role:** Designs a trade that profits if the gap fill thesis is completely wrong and SPY stays at 675-685
**Specialty:** Non-directional strategies, iron butterflies, calendar spreads, the intellectual honesty of saying "maybe everyone is wrong about direction"
**Output:** One neutral/range trade that:
- Profits from SPY staying in a defined range for 1-2 weeks
- EXPLICITLY hedges the bearish positions — this trade makes money in the scenario where Agents 13-17 lose
- Explains when and why range-bound is actually the most likely outcome (most days, stocks do nothing)
- Has defined risk and defined profit
- Includes the specific scenario where this trade loses AND the bearish trades also lose (the portfolio's true nightmare: violent rally)
- Risk Constitution compliance checklist
**Context they need:** Risk Constitution (Agent 7), Market Briefing (Agent 12), the 25% chop probability from the Market Briefing, VIX at 20 (implied range for 2 weeks)

---

### Agent 20: Bullish Contrarian — The "What If The Ceasefire Holds?" Trade
**Role:** Designs a trade that profits if the ceasefire is real and SPY rallies to new highs
**Specialty:** Contrarian thinking, the uncomfortable truth that the crowd is often wrong, the specific upside scenario that every other agent is ignoring
**Output:** One bullish trade that:
- Profits from SPY at 690-700 by April 17-25
- Forces the team to honestly assess the probability of "ceasefire is real" (even if it's only 15%)
- Is sized VERY small (this is a hedge, not a conviction bet)
- Has a massive payoff if correct (because it's contrarian, the options are cheap)
- Serves as portfolio insurance: if everything else loses, this one partially offsets
- Honest: "I don't believe this is likely, but I'd be irresponsible not to have exposure"
- Risk Constitution compliance checklist
**Context they need:** Risk Constitution (Agent 7), Market Briefing (Agent 12), bull case arguments (ceasefire could hold if Iran military consolidation succeeds, oil supply normalization, Fed dovish pivot on soft data), the fact that V1 was 100% bearish and that was identified as a flaw

---

### Agent 21: Volatility Expansion — The Non-Directional Big Move Trade
**Role:** Designs a trade that profits from a BIG MOVE in either direction (straddle/strangle philosophy)
**Specialty:** Long volatility, straddles, strangles, VIX call spreads — the "I don't know which way, but it's going to move" thesis
**Output:** One volatility trade that:
- Profits from SPY moving >2% in either direction by expiry
- Does NOT require a directional opinion
- Benefits from VIX expansion (the trade makes more money if VIX goes from 20 to 28 than if VIX stays at 20 while SPY drops)
- Explicitly addresses the cost problem: straddles at VIX 20 are expensive, so how do you get long vol cheaply?
- Considers alternatives: ratio backspread, call spread + put spread combo, VIX call spread
- Risk Constitution compliance checklist
**Context they need:** Risk Constitution (Agent 7), Market Briefing (Agent 12), volatility surface (Agent 10), PCE/CPI as dual catalysts (two binary events in 24 hours = rare elevated vol opportunity), VIX at 20 historical percentile

---

### Agent 22: The "Week After" Trade — Post-CPI Positioning
**Role:** Designs a trade for Apr 14-25, assuming the PCE/CPI week is over and the dust has settled
**Specialty:** Second-order thinking — what happens AFTER the catalyst? If gap fills partially, does it continue? If it bounces, does it re-test? The "everyone forgot about this by next week" dynamic
**Output:** One trade that:
- Enters Monday April 14 or later (after both data releases are priced in)
- Uses Apr 25 or May expiry (longer-dated, less theta pressure)
- Addresses the specific scenario: "gap filled to 668 on CPI Friday, now what?"
- Also addresses: "gap didn't fill, SPY is at 680, now what?"
- This is the ONLY trade that requires waiting — it does not enter during the catalyst week
- Provides the portfolio with time diversification (none of the other trades extend past Apr 17)
- Risk Constitution compliance checklist
**Context they need:** Risk Constitution (Agent 7), Market Briefing (Agent 12), the concept that most gap fills are not one-day events — they unfold over 5-10 sessions, post-catalyst market behavior (IV crush after PCE/CPI, liquidity returning, institutional rebalancing)

---

## TIER 4: ADVERSARIAL REVIEW (Agents 23-25)

These agents exist to DESTROY bad trades. They receive ALL Tier 3 proposals and the Risk Constitution, and their job is to find flaws. They are the quality gate between "proposed" and "approved."

---

### Agent 23: The Bearish Thesis Destroyer
**Role:** Attacks the gap fill thesis itself — makes the strongest possible case that the ceasefire holds and SPY rallies
**Specialty:** Devil's advocate for the bull case, finding the specific weaknesses in the bear thesis that the bearish agents glossed over
**Output:** Adversarial Report — Bull Case:
- The 3-5 strongest arguments that the ceasefire is real (not straw men — genuine steel-man arguments)
- Historical precedent where "obviously fake" ceasefires actually held (and why those precedents apply here)
- The specific price level and timeline where the bear thesis is definitively dead (not "if SPY rallies" but "if SPY closes above [X] for [N] consecutive days, the thesis is dead because [reason]")
- Which bearish trades from Tier 3 are most vulnerable to a rally, and which should be killed
- Probability assessment: honest, non-anchored estimate of bull case probability
- Recommendation: which bearish trades survive this stress test and which do not
**Context they need:** ALL Tier 3 proposals, Risk Constitution, Market Briefing, full Iran intel (to attack it fairly), the fact that V1 was 100% bearish and failed to consider the bull case

---

### Agent 24: The Risk Management Auditor
**Role:** Audits every Tier 3 proposal for risk management compliance — checks that stops are real, sizing is correct, and the trader can actually execute the plan
**Specialty:** Execution risk, the gap between "planned stop at $2.80" and "actual fill at $2.55 because the market gapped through," bid-ask slippage on exit, the psychology of actually pulling the trigger on a stop
**Output:** Risk Compliance Audit:
- For each Tier 3 trade: PASS, FAIL, or REVISE
- FAIL reasons: violates Risk Constitution, stop loss is unrealistic (gap risk), position is too complex for a new trader, margin requirements not met, slippage will eat the profit, bid-ask spread too wide for the planned exit
- REVISE reasons: trade is sound but needs smaller size, tighter stop, simpler structure, or different expiry
- The "execution reality check": can a new trader with shaky hands actually execute this plan at 8:31 AM on PCE Thursday? If not, simplify it.
- Portfolio-level check: do all surviving trades together still comply with the Risk Constitution's total risk limit?
**Context they need:** ALL Tier 3 proposals, Risk Constitution, new trader limitations (no pre-market trading, no complex multi-leg adjustments under pressure, emotional state during first live trades), SPY options liquidity data

---

### Agent 25: The Correlation Correlation — Portfolio-Level Stress Test
**Role:** Stress-tests the COMBINATION of all surviving Tier 3 trades as a single portfolio
**Specialty:** The thing nobody checks: what happens when you add the "safe" credit spread to the "safe" put spread to the "safe" gamma kicker and realize you've accidentally built a 10% account risk portfolio
**Output:** Portfolio Stress Test Results:
- Combined Greeks: total delta, gamma, theta, vega of ALL surviving positions
- Scenario matrix: the 7 scenarios from Agent 3, now calculated with actual positions and actual Greeks
- The worst-case combo: the specific scenario that hurts the most positions simultaneously
- Correlation heat map: which positions move together? (Two positions that both lose on a rally are correlated, even if one is a spread and one is a condor)
- The "all-lose" scenario: what is the MAXIMUM the portfolio can lose if every stop triggers and every position hits max loss simultaneously? Is it under the Risk Constitution limit?
- Greek imbalances: is the portfolio too delta-heavy? Too negative theta? Insufficiently long gamma?
- KILL recommendations: specific trades that should be removed because they add risk without adding diversification
**Context they need:** ALL surviving Tier 3 proposals (post-Agent 24 audit), Risk Constitution, Market Briefing, the V2 failure of not checking portfolio-level correlation

---

## TIER 5: PORTFOLIO CONSTRUCTION (Agents 26-30)

These agents take the surviving, stress-tested trades and construct the final portfolio.

---

### Agent 26: Portfolio Constructor
**Role:** Selects the optimal 3-5 positions from the surviving Tier 3/4 trades and sizes them as a PORTFOLIO, not as individual bets
**Specialty:** Portfolio optimization, risk parity, the art of combining trades that hedge each other, final sizing to hit exactly the Risk Constitution's budget
**Output:** The Constructed Portfolio:
- 3-5 specific positions with exact strikes, expiries, quantities, and order types
- Portfolio-level Greeks table
- The 7-scenario P&L matrix showing combined portfolio performance
- Capital deployment schedule: how much cash is tied up, when is it released?
- The "why these 3-5 and not others" rationale — what was cut and why
- Diversification proof: show that the 3-5 positions cover at least 3 of the 4 categories (bearish, bullish, volatility, theta)
**Context they need:** ALL surviving and stress-tested proposals from Tiers 3 and 4, Risk Constitution, Market Briefing, Agent 25's stress test results

---

### Agent 27: Execution Planner
**Role:** Converts the portfolio into a minute-by-minute execution plan for Monday through Friday
**Specialty:** Order sequencing, limit order discipline, what to do if a fill doesn't happen, the specific rhythm of market hours for someone new to active trading
**Output:** Execution Timeline:
- Monday: what to do at 9:30, 9:45, 10:00, 10:15 — specific orders with limit prices
- Tuesday: monitoring rules, what to check, when to enter Position X
- Wednesday: Position B entry timing (if applicable), pre-PCE preparation
- Thursday: PCE day protocol — when to look, when NOT to look, what "hot PCE" means in real-time
- Friday: CPI day protocol, expiry management, cleanup rules
- Week 2 (if applicable): what remains open, how to manage it
- For EACH order: exact limit price, how far to walk it, when to abandon the fill
- The "abort" protocol: at what point do you cancel the entire plan and go flat?
**Context they need:** Constructed Portfolio (Agent 26), Market Briefing, PCE/CPI timing, the fact that the new trader has never placed a multi-leg options order before

---

### Agent 28: Adjustment Decision Tree
**Role:** Creates the "if/then" playbook for every mid-trade scenario the new trader might face
**Specialty:** The messy reality of live trading — the trade is on, SPY just did something unexpected, what do you do NOW?
**Output:** The Decision Tree document:
- IF SPY gaps up 2% Monday pre-market: [do X]
- IF PCE is hot and SPY drops 3% in 10 minutes: [do X]
- IF your put spread is profitable but the credit spread is being tested: [do X]
- IF VIX spikes to 30: [do X]
- IF your broker shows a margin call warning (it shouldn't, but what if): [do X]
- IF you accidentally close the wrong leg: [do X]
- IF the market halts on Iran news: [do X]
- IF nothing happens all week and everything is flat: [do X]
- For EACH scenario: one clear action, no ambiguity, no "it depends"
- The golden rule: WHEN IN DOUBT, CLOSE THE POSITION. A new trader's first instinct should be to reduce risk, not add to it.
**Context they need:** Constructed Portfolio (Agent 26), Risk Constitution, Emotional Playbook (Agent 5), all the ways a trade can go sideways that experienced traders know and new traders don't

---

### Agent 29: Borey Presentation Formatter
**Role:** Takes the final portfolio and wraps it in the language and format that Borey (experienced options trader) wants to see
**Specialty:** Translation — converting analytical output into practitioner language, knowing what an experienced trader scans for (risk first, then thesis, then structure), removing jargon that sounds smart but says nothing
**Output:** The Borey Package:
- One-page summary: what the portfolio is, why, how much at risk, what the plan is
- For each position: 3-line description (structure, thesis, risk)
- The "what can go wrong" section BEFORE the "what can go right" section (this is how experienced traders think)
- The sizing justification: why this amount, not more, not less
- The exit plan: no ambiguity, no "we'll see how it develops"
- The tone: confident but humble, shows homework, doesn't pretend to be smarter than the market
- Removes any trace of: Fibonacci targets, "guaranteed" returns, undefined risk, or "we can always roll"
**Context they need:** Constructed Portfolio (Agent 26), Execution Timeline (Agent 27), Borey's known preferences (simple structures, defined risk, conviction-based sizing, discipline > cleverness), the V1/V2 feedback about what was wrong

---

### Agent 30: Final Synthesizer — Gil's Decision Brief
**Role:** Produces the absolute final output that Gil reads to decide what to present to Borey
**Specialty:** Decision support — not just "here's the portfolio" but "here's what you need to know to make the call," including what to say, what NOT to say, and how to handle Borey's likely questions
**Output:** Gil's Decision Brief:
- THE PORTFOLIO: 3-5 positions, one line each, total risk, total potential
- CONFIDENCE LEVEL: how confident is the swarm in this portfolio? (Unanimous agreement? Split decision? Minority dissent?)
- WHAT BOREY WILL ASK and the correct answers:
  - "Why not just buy puts?" — [answer]
  - "Why is there a bullish position?" — [answer]
  - "What if you're wrong?" — [answer]
  - "How much can you lose?" — [answer, to the dollar]
  - "When do you get out?" — [answer, with specific dates and prices]
- WHAT NOT TO SAY:
  - Don't mention the 30-agent swarm (Borey doesn't care about process, only output)
  - Don't present alternatives that were rejected (it signals indecision)
  - Don't qualify every statement with "but if X then Y" (it signals lack of conviction)
- THE ONE SENTENCE: if Gil could only say one thing to Borey about this portfolio, what is it?
- RISK DISCLOSURE: the honest truth about what could go wrong, in plain English
**Context they need:** EVERYTHING — all prior agent outputs, the Risk Constitution, the constructed portfolio, the execution plan, the adversarial reviews, the Borey presentation, and the emotional playbook. This agent is the final filter.

---

## EXECUTION ORDER AND DEPENDENCIES

```
Wave 1 (parallel): Agents 1-6 (risk framework) + Agents 8-11 (market context)
  - These 10 agents have no dependencies on each other
  - Total: 10 agents running simultaneously

Wave 2 (parallel): Agent 7 (compile risk constitution) + Agent 12 (compile market briefing)
  - Agent 7 needs Agents 1-6
  - Agent 12 needs Agents 8-11
  - Total: 2 agents running simultaneously

Wave 3 (parallel): Agents 13-22 (all 10 trade proposals)
  - All need Agent 7 (risk constitution) + Agent 12 (market briefing)
  - No dependencies on each other
  - Total: 10 agents running simultaneously

Wave 4 (parallel): Agents 23-25 (adversarial review)
  - All need Agents 13-22 output
  - Agent 23 (thesis destroyer) and Agent 24 (risk auditor) can run in parallel
  - Agent 25 (portfolio stress test) benefits from 23+24 output but can run in parallel with partial info
  - Total: 3 agents running simultaneously

Wave 5 (sequential): Agents 26 -> 27 -> 28 (portfolio construction -> execution -> adjustments)
  - Agent 26 needs Agents 23-25 (adversarial output)
  - Agent 27 needs Agent 26 (the portfolio)
  - Agent 28 needs Agent 26 + Agent 5 (emotional rules)
  - 26 first, then 27+28 in parallel

Wave 6 (parallel): Agent 29 + Agent 30 (Borey package + Gil's brief)
  - Both need Agent 26-28 output
  - Total: 2 agents running simultaneously
```

**Total waves: 6 (not 30 sequential runs)**
**Longest sequential chain: ~6 agent-runtimes, not 30**

---

## AGENT COUNT BY CATEGORY

| Category | Agents | Count | Requirement |
|----------|--------|-------|-------------|
| Risk management (pure) | 1, 2, 3, 4, 5, 6, 7 | **7** | Min 5 required -- exceeded |
| Adversarial reviewers | 23, 24, 25 | **3** | Min 3 required -- met |
| Non-bearish alternatives | 19, 20, 21 | **3** | Min 3 required -- met |
| Borey perspective | 13, 14 | **2** | Min 2 required -- met |
| Trade proposals with risk baked in | 13-22 | **10** | Yes |
| Portfolio constructor | 26 | **1** | Required -- met |
| Final synthesizer | 30 | **1** | Required -- met |
| Market context | 8-12 | **5** | Supporting |
| Execution/presentation | 27-29 | **3** | Supporting |
| **TOTAL** | | **30** | |

---

## DESIGN RATIONALE: WHY RISK FIRST

In V1, 20 agents drafted trades. Zero drafted risk rules. The result: 20 correlated bearish positions with no portfolio-level thinking.

In V2, some agents considered risk, but it was an afterthought — "here's the trade, and by the way, set a stop at X."

In V3, the risk framework EXISTS before any trade is proposed. Agents 13-22 cannot even BEGIN until Agent 7 publishes the Risk Constitution. This is not a suggestion — it is an architectural constraint. The framework is the foundation. The trades are the furniture. You do not buy furniture before the foundation is poured.

The adversarial layer (Agents 23-25) exists because every previous version exhibited confirmation bias. When 20 agents all agree that the gap will fill, nobody asks "what if it doesn't?" The adversarial agents are REQUIRED to make the strongest possible case against the consensus. If a trade cannot survive their attack, it does not deserve capital.

The emotional management agent (Agent 5) exists because a new trader's biggest risk is not the market — it is themselves. The best portfolio in the world fails if the trader panics on a Tuesday morning drawdown and closes everything at a loss. Behavioral guardrails are risk management.

The portfolio construction layer (Agents 26-30) exists because V1 and V2 treated portfolio construction as a summary exercise — "pick the best 3." V3 treats it as an engineering exercise — "combine these positions so they hedge each other, fit the risk budget, and can actually be executed by a human being."

---

*"The goal is not to find the perfect trade. The goal is to survive long enough to find many good trades. Risk management is how you survive."*
