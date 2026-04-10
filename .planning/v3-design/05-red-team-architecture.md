# V3 Red Team Architecture: BUILD -> BREAK -> REBUILD

**Date:** 2026-04-06
**Purpose:** 30-agent swarm with adversarial red team layer. No position reaches Gil without surviving destruction testing.

**Problem solved:** V1 and V2 agents proposed positions without stress-testing their own work. The put spread agent always thinks put spreads are great. The butterfly agent always loves butterflies. The 20-agent adversarial swarm reviewed the CODEBASE but never reviewed V2's POSITIONS. V3 fixes this: every position gets a dedicated attacker.

**Architecture:** BUILD (10) -> BREAK (10) -> REBUILD (5) -> SYNTHESIZE (5)

---

## WAVE 1: BLUE TEAM -- Draft 10 Positions (Agents 1-10)

Every blue team agent receives the same shared input packet and produces a single position proposal. Each agent has a DIFFERENT structural mandate to ensure diversity -- no two agents propose the same structure type.

### Shared Input (all Wave 1 agents receive this)

- Current market snapshot (SPX level, VIX, key levels, dealer positioning)
- Thesis summary (ceasefire gap fill, timing uncertainty, catalyst calendar)
- Account constraints ($10K, 2% per-position risk cap, 5% total portfolio cap)
- V1/V2 adversarial findings (what Borey's review flagged, what the code auditors found)
- V2 consensus positions (so agents know what was already tried and what was criticized)
- Borey's actual feedback from V1 review (the C grade, the "lead with your stop-loss" mandate)

### Agent Definitions

---

**Agent 1 -- Directional Put Specialist**
- Wave: 1 (Blue Team)
- Role: Design the best single-leg or put debit spread to express the gap fill thesis
- Input: Shared packet + V2 Agent 01 (aggressive puts) + V2 Agent 02 (conservative spread) + Borey's critique that the V1 put spread had "lazy strikes"
- Output: One position with full trade ticket, strike justification anchored to GEX/volume profile (not round numbers), entry timing, stop-loss, time stop, invalidation criteria, and dollar-denominated max loss
- Constraint: Must address the V1 failure mode -- "direction right, timing wrong by 48 hours kills you." Must justify strike selection with data, not convenience
- Relationship: Wave 2 Agent 11 attacks this position

---

**Agent 2 -- Credit Spread Specialist (Bear Call)**
- Wave: 1 (Blue Team)
- Role: Design the best short premium position that profits from the thesis WITHOUT requiring the gap to fill -- SPY just needs to not rally
- Input: Shared packet + V2 Agent 03 (bear call spread) + Borey's note that premium selling on an overextended rally is "textbook institutional"
- Output: One credit spread position with full ticket, probability of profit estimate, theta decay per day, 50% profit-take rule, stop at 2x credit received
- Constraint: Must explain why selling this specific strike is better than alternatives. Must calculate probability of profit using the system's combo_odds engine, not hand-waving
- Relationship: Wave 2 Agent 12 attacks this position

---

**Agent 3 -- Butterfly/Condor Specialist**
- Wave: 1 (Blue Team)
- Role: Design a multi-leg defined-risk position that targets a specific price zone (the gap fill zone) with minimal cost if wrong on direction
- Input: Shared packet + V2 Agent 05 (broken wing butterfly) + V2 Agent 15 (iron condor) + adversarial finding that BWB and IC were "too complex for a new trader"
- Output: One butterfly or condor variant with full ticket, P&L diagram description, pin risk analysis, and an honest assessment of whether Borey can manage this without confusion
- Constraint: Must confront the complexity objection head-on. If the structure requires active adjustment, say so and quantify the adjustment rules. If it is genuinely too complex, propose a simpler variant and explain the tradeoff
- Relationship: Wave 2 Agent 13 attacks this position

---

**Agent 4 -- Volatility Event Specialist (0DTE/1DTE)**
- Wave: 1 (Blue Team)
- Role: Design the best short-duration catalyst scalp for PCE Thursday and/or CPI Friday
- Input: Shared packet + V2 Agent 10 (0DTE PCE strangle) + adversarial finding that "buying ATM premium Friday close on a weekly is writing a check to market makers"
- Output: One 0DTE or 1DTE position with full ticket, exact entry window (to the minute), exact exit rules (time stop, profit target, loss cap), gamma/theta tradeoff analysis
- Constraint: Must justify why 0DTE is the right expiry for this catalyst (not 7 DTE entered on the same day). Must have a hard time stop -- no holding past the entry session. Must cap risk at 1.5% of account ($150) because this is a scalp, not a core position
- Relationship: Wave 2 Agent 14 attacks this position

---

**Agent 5 -- Scale-In/Ladder Specialist**
- Wave: 1 (Blue Team)
- Role: Design a multi-entry position that solves the timing problem through conditional entries rather than a single all-in bet
- Input: Shared packet + V2 Agent 06 (scale-in ladder) + Borey's insight: "Wait for the squeeze MPW says comes first. THAT is when you buy puts."
- Output: A 2-3 entry ladder with specific triggers for each entry, descending strikes, and a kill switch (failed Entry 1 cancels everything). Total risk across all entries capped at 3%
- Constraint: Each entry trigger must be objectively verifiable (price level, VIX level, technical breakdown) -- no subjective calls like "if momentum confirms." Must specify what happens if Entry 1 triggers but Entry 2's trigger never fires (you are stuck with a partial position)
- Relationship: Wave 2 Agent 15 attacks this position

---

**Agent 6 -- Premium Seller (Put Side)**
- Wave: 1 (Blue Team)
- Role: Design a position that SELLS put premium -- the contrarian play. What if the ceasefire holds longer than expected and put buyers get crushed?
- Input: Shared packet + V2 Agent 13 (jade lizard) + Borey's own words: "If you and everyone on FinTwit see the same setup, the people selling you those puts see it too"
- Output: One put credit spread, cash-secured put, or jade lizard variant with full ticket, margin/collateral requirements, probability of profit, and an explicit "this is the anti-thesis trade" framing
- Constraint: Must explain the bull case honestly (ceasefire extends, VIX collapses, put sellers win). Must quantify what happens if the gap fill thesis is RIGHT and this trade loses. Must be sized so that the loss on gap fill does not exceed 2% of account
- Relationship: Wave 2 Agent 16 attacks this position

---

**Agent 7 -- Hedged Combo Specialist (Fence/Collar)**
- Wave: 1 (Blue Team)
- Role: Design a position with both bearish and bullish components -- the "I don't know which way but I'm not getting killed" trade
- Input: Shared packet + V2 Agent 07 (hedged fence with call kicker) + the finding that 15-20% bull probability is "not zero"
- Output: One combo position (fence, collar, risk reversal, or split-strike synthetic) with full ticket, net cost, P&L across 3 scenarios (gap fill, sideways chop, rally), and a clear explanation of what the hedge costs you in directional profit
- Constraint: The hedge must be meaningful -- not a $0.10 OTM call that expires worthless 99% of the time. Must pass the test: "If SPY rallies $10, does the hedge actually help?"
- Relationship: Wave 2 Agent 17 attacks this position

---

**Agent 8 -- Calendar/Diagonal Specialist**
- Wave: 1 (Blue Team)
- Role: Design a position that exploits the TERM STRUCTURE of volatility -- different expiries, different IV levels, different theta decay curves
- Input: Shared packet + V2 elimination note that "calendar spread mechanics confuse new traders" + the adversarial finding that entry timing is the biggest risk
- Output: One calendar spread, diagonal spread, or double calendar with full ticket, explanation of which expiry is overpriced vs underpriced and why, vega exposure analysis, and a "this is confusing, here is why it is worth the complexity" section
- Constraint: Must honestly assess whether the term structure edge is large enough to justify the additional complexity for a new trader. If it is not, must say so and propose a simpler alternative. Must include exact adjustment rules for when the short leg moves against you
- Relationship: Wave 2 Agent 18 attacks this position

---

**Agent 9 -- Contrarian/Mean Reversion Specialist**
- Wave: 1 (Blue Team)
- Role: Design the "everyone is wrong" trade. What if the gap does NOT fill? What if the ceasefire is real and SPX goes to 7000?
- Input: Shared packet + V2 bear call spread (which gets killed if rally extends) + Borey's note about waiting for the squeeze THEN buying puts + historical analogs where ceasefire rallies lasted 2-4 weeks before reversing
- Output: One bullish or mean-reversion position that profits if the consensus gap-fill thesis fails. Full ticket, scenario analysis, and an explicit statement of what market conditions would make this the RIGHT trade (not just a hedge)
- Constraint: This is NOT just a hedge. This is a full-conviction position for the scenario where the bear thesis is dead wrong. Must be sized and structured to profit meaningfully in the bull case, not just limit losses. 2% risk cap still applies
- Relationship: Wave 2 Agent 19 attacks this position

---

**Agent 10 -- "What Borey Would Actually Trade" Specialist**
- Wave: 1 (Blue Team)
- Role: Design the position that an experienced trader (Borey's persona) would actually put on, given everything the swarm has learned. Not the flashiest, not the most creative -- the most DISCIPLINED
- Input: Shared packet + Borey's V1 review (especially "wait for the squeeze, buy puts after everyone else has given up") + the full V2 consensus + every adversarial finding
- Output: One position that prioritizes: (a) correct position sizing as % of account, (b) explicit stop-loss in dollars, (c) entry trigger that is patient not impulsive, (d) simplicity -- 1-2 legs maximum, (e) the trade Borey described: "6800/6700 put spread two weeks out, entered after the squeeze, sized at 1% with a 50% stop"
- Constraint: Must resist the urge to improve on Borey's suggestion. The whole point is to draft what Borey said he would trade and see if it survives adversarial review. If the agent thinks Borey's trade has a flaw, note it but propose Borey's version anyway -- the red team will test it
- Relationship: Wave 2 Agent 20 attacks this position

---

## WAVE 2: RED TEAM -- Destroy 10 Positions (Agents 11-20)

Every red team agent receives ONE specific position from Wave 1 and tries to break it. The red team agent does NOT know what other positions exist -- they focus entirely on the single position assigned to them. Their job is to find the flaw, the hidden risk, the scenario where it blows up.

### Red Team Mandate (all Wave 2 agents follow this)

1. **Find the kill scenario.** What specific market event, price action, or timing failure causes this position to hit max loss?
2. **Quantify the damage.** Not "this could lose money" -- how much, under what conditions, with what probability?
3. **Check the math.** Does the P&L analysis hold? Are the Greeks correct? Is the probability of profit estimate honest or hand-waved?
4. **Test the thesis dependency.** If the underlying thesis is 60% correct (gap fill happens) but the timing is off by 3 days, does this position still work?
5. **Find the crowded trade problem.** Is this the same position every retail trader on FinTwit is putting on? If so, who is the counterparty and why are they happy to take the other side?
6. **Verdict: SURVIVE, FIX, or KILL.** Every red team agent must deliver one of three verdicts with justification.

---

**Agent 11 -- Red Team: Directional Put Attacker**
- Wave: 2 (Red Team)
- Role: Destroy Agent 1's directional put position
- Input: Agent 1's full position proposal + market data + V1 Borey review (specifically "put skew is bid, weekend premium is inflated, the Monday flush is the most crowded retail trade")
- Output: Kill scenario analysis, timing risk quantification (what happens if thesis is right but 3 days late), theta bleed calculation day by day, crowded trade analysis (who is selling you this put and why they are smiling), verdict (SURVIVE/FIX/KILL) with specific fix if applicable
- Relationship: Feeds to Wave 3 Agent 21 (if verdict is SURVIVE or FIX)

---

**Agent 12 -- Red Team: Credit Spread Attacker**
- Wave: 2 (Red Team)
- Role: Destroy Agent 2's bear call credit spread
- Input: Agent 2's full position proposal + market data
- Output: Rally scenario stress test (what if SPY gaps to 690 on ceasefire extension headlines Monday morning -- can you close the spread? What is the slippage? What is the gap risk?), assignment risk analysis if short call goes ITM, probability of profit audit (is the agent's estimate honest or does it ignore gap risk and correlation with VIX), verdict
- Relationship: Feeds to Wave 3 Agent 22 (if verdict is SURVIVE or FIX)

---

**Agent 13 -- Red Team: Butterfly/Condor Attacker**
- Wave: 2 (Red Team)
- Role: Destroy Agent 3's butterfly or condor position
- Input: Agent 3's full position proposal + market data
- Output: Pin risk analysis (what is the probability of expiring between the short strikes where the position is worst?), complexity audit (can Borey realistically manage this? What happens if one leg gets assigned early?), gamma risk into expiration quantification, max loss scenario that is NOT the theoretical max but the REALISTIC worst case including slippage and wide markets, verdict
- Relationship: Feeds to Wave 3 Agent 23 (if verdict is SURVIVE or FIX)

---

**Agent 14 -- Red Team: 0DTE Attacker**
- Wave: 2 (Red Team)
- Role: Destroy Agent 4's volatility event scalp
- Input: Agent 4's full position proposal + market data + historical PCE/CPI reaction data
- Output: "Nothing happens" scenario (PCE is inline, market shrugs, both legs of the strangle bleed to zero in 4 hours -- what is the realized loss?), execution risk analysis (0DTE spreads are WIDE at 9:35 AM, what is the realistic fill vs the theoretical midpoint?), speed-of-exit analysis (if the time stop is 10:30 AM but the market is whipsawing, can you actually close at a reasonable price?), verdict
- Relationship: Feeds to Wave 3 Agent 24 (if verdict is SURVIVE or FIX)

---

**Agent 15 -- Red Team: Scale-In Ladder Attacker**
- Wave: 2 (Red Team)
- Role: Destroy Agent 5's multi-entry ladder
- Input: Agent 5's full position proposal + market data
- Output: "Trigger cascade" scenario (what if Entry 1 triggers, market bounces, Entry 2 never fires -- you are stuck with a single undersized position that bleeds theta), "all triggers fire on the same day" scenario (you suddenly have 3x the intended position on a gap down -- is that actually what you want?), psychological audit (will Borey actually follow the kill switch or will he move the goalposts?), verdict
- Relationship: Feeds to Wave 3 Agent 21 (if verdict is SURVIVE or FIX -- shares rebuild slot with directional put since both are directional)

---

**Agent 16 -- Red Team: Premium Seller Attacker**
- Wave: 2 (Red Team)
- Role: Destroy Agent 6's put premium selling position
- Input: Agent 6's full position proposal + market data
- Output: "Gap fill happens fast" scenario (SPY drops $17 in 2 days -- what is the mark-to-market loss? Can you even close the short put at a reasonable price when VIX spikes to 35?), margin call analysis (does the account have enough buying power to hold this through a vol spike?), "selling puts into a falling knife" historical analogs, verdict
- Relationship: Feeds to Wave 3 Agent 22 (if verdict is SURVIVE or FIX -- shares rebuild slot with credit spread since both are short premium)

---

**Agent 17 -- Red Team: Hedged Combo Attacker**
- Wave: 2 (Red Team)
- Role: Destroy Agent 7's fence/collar/combo position
- Input: Agent 7's full position proposal + market data
- Output: "Hedge cost exceeds hedge value" analysis (does the call kicker actually offset enough loss to justify its cost, or is it a feel-good token?), "worst of both worlds" scenario (SPY chops sideways -- the put loses theta, the call loses theta, you pay double theta for no payoff), correlation analysis (in the scenario where you need the hedge, does it actually work or does correlation break down?), verdict
- Relationship: Feeds to Wave 3 Agent 23 (if verdict is SURVIVE or FIX -- shares rebuild slot with butterfly since both are multi-leg)

---

**Agent 18 -- Red Team: Calendar/Diagonal Attacker**
- Wave: 2 (Red Team)
- Role: Destroy Agent 8's calendar or diagonal spread
- Input: Agent 8's full position proposal + market data
- Output: "Vol crush kills both legs" scenario (VIX drops from 20 to 15 -- what happens to the term structure edge?), "early assignment on short leg" analysis, complexity-vs-edge audit (is the term structure edge large enough in dollar terms to justify the management overhead for a $10K account?), "new trader execution risk" assessment (can Borey reliably manage different expiry legs?), verdict
- Relationship: Feeds to Wave 3 Agent 24 (if verdict is SURVIVE or FIX -- shares rebuild slot with 0DTE since both are time-sensitive)

---

**Agent 19 -- Red Team: Contrarian Attacker**
- Wave: 2 (Red Team)
- Role: Destroy Agent 9's bullish/contrarian position
- Input: Agent 9's full position proposal + market data
- Output: "Gap fill happens and you are on the wrong side" scenario (the contrarian bet loses while every other position in the portfolio wins -- is the portfolio net P&L still acceptable?), "conviction without catalyst" analysis (what specific event would cause the ceasefire to actually hold? Is there a plausible mechanism or is this just hedging for the sake of hedging?), opportunity cost quantification (the capital locked in this position could be in a directional trade -- what is the expected value comparison?), verdict
- Relationship: Feeds to Wave 3 Agent 25 (if verdict is SURVIVE or FIX)

---

**Agent 20 -- Red Team: "Borey's Trade" Attacker**
- Wave: 2 (Red Team)
- Role: The most important red team agent. Try to destroy the trade that Borey himself said he would make
- Input: Agent 10's full position proposal + Borey's original description + market data
- Output: "Wait for the squeeze" timing risk (what if the squeeze never comes and the ceasefire just slowly becomes accepted -- your entry trigger never fires and you sit in cash while the market moves?), "1% sizing is too small" analysis (is a 1% position even worth the mental energy and commission cost?), "this is a DIFFERENT market than what Borey described" test (Borey said to wait for VIX 16-17, but what if VIX stays at 20-22 for weeks?), honest assessment of whether Borey's caution is wisdom or excessive patience that misses the trade entirely, verdict
- Relationship: Feeds to Wave 3 Agent 25 (if verdict is SURVIVE or FIX -- shares rebuild slot with contrarian since both challenge the consensus)

---

## WAVE 3: REBUILD -- Strengthen Survivors (Agents 21-25)

Wave 3 agents receive the ORIGINAL position from Wave 1 AND the red team attack from Wave 2. Their job is to rebuild the position incorporating the adversarial feedback. If the red team killed a position, the rebuild agent may resurrect it with fundamental changes or declare it dead and explain why.

Each rebuild agent handles 2 related positions to enable cross-pollination -- if the directional put was killed but the ladder survived, maybe the rebuild combines elements of both.

---

**Agent 21 -- Rebuild: Best Directional Expression**
- Wave: 3 (Rebuild)
- Role: Rebuild the best directional bearish position from Agents 1 and 5 (put + ladder), incorporating red team feedback from Agents 11 and 15
- Input: Agent 1 position + Agent 11 attack + Agent 5 position + Agent 15 attack
- Output: One rebuilt directional position (could be a modified put, a modified ladder, or a hybrid) that specifically addresses every red team finding. Must include: "Red team said X. I addressed it by Y." for each finding. If both positions were killed and cannot be saved, output a "DEAD -- here is why directional longs do not work in this environment" analysis
- Relationship: Feeds to Wave 4 Agent 26 (portfolio construction)

---

**Agent 22 -- Rebuild: Best Short Premium Expression**
- Wave: 3 (Rebuild)
- Role: Rebuild the best short premium position from Agents 2 and 6 (bear call + premium seller), incorporating red team feedback from Agents 12 and 16
- Input: Agent 2 position + Agent 12 attack + Agent 6 position + Agent 16 attack
- Output: One rebuilt short premium position that addresses every red team finding. If the bear call survived but the put selling was killed, explain why one premium-selling structure works and the other does not in this regime. If both were killed, explain why selling premium is wrong here
- Relationship: Feeds to Wave 4 Agent 26 (portfolio construction)

---

**Agent 23 -- Rebuild: Best Multi-Leg Defined Risk Expression**
- Wave: 3 (Rebuild)
- Role: Rebuild the best multi-leg position from Agents 3 and 7 (butterfly/condor + hedged combo), incorporating red team feedback from Agents 13 and 17
- Input: Agent 3 position + Agent 13 attack + Agent 7 position + Agent 17 attack
- Output: One rebuilt multi-leg position that addresses every red team finding. Must specifically address the "too complex for a new trader" objection with a concrete plan: exact order sequence, exact adjustment triggers, and a "if confused, do this" bailout instruction. If complexity cannot be tamed, kill both and explain why simple structures dominate here
- Relationship: Feeds to Wave 4 Agent 26 (portfolio construction)

---

**Agent 24 -- Rebuild: Best Time-Sensitive/Catalyst Expression**
- Wave: 3 (Rebuild)
- Role: Rebuild the best catalyst-driven position from Agents 4 and 8 (0DTE + calendar), incorporating red team feedback from Agents 14 and 18
- Input: Agent 4 position + Agent 14 attack + Agent 8 position + Agent 18 attack
- Output: One rebuilt time-sensitive position that addresses every red team finding. Must confront the fundamental question: is exploiting the PCE/CPI catalyst worth the execution risk and complexity, or should the portfolio simply avoid the event and enter after? If the 0DTE was killed but the calendar survived (or vice versa), explain the structural reason why
- Relationship: Feeds to Wave 4 Agent 26 (portfolio construction)

---

**Agent 25 -- Rebuild: Best Non-Consensus Expression**
- Wave: 3 (Rebuild)
- Role: Rebuild the best position that challenges the gap-fill consensus, from Agents 9 and 10 (contrarian + Borey's trade), incorporating red team feedback from Agents 19 and 20
- Input: Agent 9 position + Agent 19 attack + Agent 10 position + Agent 20 attack
- Output: One rebuilt position that represents the strongest challenge to the prevailing thesis. If the contrarian (bullish) was killed but Borey's patient trade survived, the output is Borey's trade. If both survived, pick the stronger one and explain why. Must answer: "What does this position teach Borey that the directional trades do not?"
- Relationship: Feeds to Wave 4 Agent 26 (portfolio construction)

---

## WAVE 4: SYNTHESIZE -- Portfolio + Presentation (Agents 26-30)

Wave 4 receives all 5 rebuilt positions (or fewer, if some were killed) and constructs the final portfolio, stress tests it, and formats the presentation.

---

**Agent 26 -- Portfolio Constructor**
- Wave: 4 (Synthesize)
- Role: Select 3 positions from the 5 rebuilt candidates and construct a portfolio with diversified failure modes
- Input: All 5 rebuilt positions from Agents 21-25 + account constraints ($10K, 5% total risk cap)
- Output: A 3-position portfolio with:
  - Combined risk table (total max loss, per-position max loss, risk as % of account)
  - Correlation analysis (when Position A loses, does Position B also lose or does it offset?)
  - 4 scenario P&L table: (1) gap fill fast, (2) gap fill slow, (3) sideways chop, (4) rally extends
  - Explanation of why these 3 and not the other 2 -- what failure mode diversity does this combination provide?
  - Combined Greeks (delta, theta, vega) for the portfolio as a whole
- Constraint: Total portfolio risk must not exceed $500 (5% of $10K). No single position may exceed $200 risk (2%). If a rebuilt position exceeds these limits, the portfolio constructor must resize it and note the impact
- Relationship: Feeds to Agent 28 (worst-case) and Agent 29 (Borey review) and Agent 30 (presentation)

---

**Agent 27 -- Borey Simulation**
- Wave: 4 (Synthesize)
- Role: Grade the V3 portfolio the way Borey graded V1 -- as a skeptical experienced trader who values discipline over cleverness
- Input: Agent 26's portfolio + V1 Borey review (for grading criteria calibration) + V2 final consensus (for comparison)
- Output: A grade (A through F) for each of:
  - Thesis quality (is the directional read defensible?)
  - Strategy selection (do the structures match the thesis?)
  - Risk management (position sizing, stops, max loss, exit plans)
  - Presentation (does the trader show discipline or flash?)
  - Overall grade with Borey's voice: "Here is what I would actually say to Gil about this portfolio"
- Constraint: Must grade HARDER than the V1 review. V1 got a C -- if V3 is not meaningfully better, this agent must say so. Must specifically note whether V3 addressed every V1 criticism (lazy strikes, no position sizing, no stops, timing dressed up as analysis)
- Relationship: Feeds to Agent 30 (presentation)

---

**Agent 28 -- Worst-Case Analyst**
- Wave: 4 (Synthesize)
- Role: Define the absolute worst day for this portfolio and quantify the damage
- Input: Agent 26's portfolio + historical analogs for worst-case scenarios
- Output:
  - **Black Monday scenario:** SPY gaps down 5% on Monday open (ceasefire collapses over weekend). What is the portfolio P&L? Can you close positions or are you trapped?
  - **Melt-up scenario:** Ceasefire extends, peace talks progress, SPY rallies 3% over the week. What is the portfolio P&L?
  - **Chop scenario:** SPY stays between 675-680 all week. Theta eats everything. What is the portfolio P&L?
  - **Whipsaw scenario:** SPY drops 2% Monday (you think the thesis is working), rallies 3% Tuesday (stops you out), then drops 4% Wednesday (the real move happens without you). Can the portfolio survive this?
  - **Max drawdown before recovery:** If the thesis is ultimately right but the path is painful, what is the worst mark-to-market loss BEFORE the portfolio recovers?
- Constraint: Use actual dollar figures, not percentages. Gil needs to see "$347 loss" not "3.47% drawdown"
- Relationship: Feeds to Agent 30 (presentation)

---

**Agent 29 -- Execution Playbook Writer**
- Wave: 4 (Synthesize)
- Role: Convert the portfolio into a minute-by-minute execution plan that Gil can follow without thinking
- Input: Agent 26's portfolio + Agent 28's worst-case scenarios
- Output: A day-by-day, time-stamped playbook:
  - **Sunday night:** Review this plan. Set alerts at these prices. Pre-enter these limit orders.
  - **Monday 9:30-10:00 AM:** Do X. If Y happens instead, do Z. If neither, wait.
  - **Monday 10:00-10:30 AM:** Check A. If A > threshold, enter Position 1. If not, stand down.
  - (Continue for each day through Friday)
  - **For each position:** Exact order type (limit, stop-limit, market), exact price levels, exact conditions for entry/exit/adjustment
  - **"If confused" bailout:** At any point, if Gil does not know what to do, the default action is: close everything at market, accept the loss, reassess tomorrow
- Constraint: Must be executable by someone who has never placed a multi-leg options order before. Every instruction must be unambiguous. No "use your judgment" -- only "if X then Y, else Z"
- Relationship: Feeds to Agent 30 (presentation)

---

**Agent 30 -- Final Presentation (Gil's Deliverable)**
- Wave: 4 (Synthesize)
- Role: Combine everything into the document Gil shows to Borey
- Input: Agent 26 (portfolio), Agent 27 (Borey grade), Agent 28 (worst-case), Agent 29 (execution playbook)
- Output: A single document structured as:
  1. **One-paragraph executive summary** (thesis, portfolio, total risk, best/worst case)
  2. **The 3 positions** (trade tickets, one paragraph each on why)
  3. **Combined risk table** (from Agent 26)
  4. **What could go wrong** (from Agent 28, condensed to top 3 scenarios)
  5. **Borey's grade** (from Agent 27)
  6. **Execution playbook** (from Agent 29, condensed to the critical decision points)
  7. **Red team survival record** (which positions survived, which were killed, which were rebuilt -- showing Borey that every position was stress-tested)
  8. **"What we learned from V1 and V2"** (explicit list of V1/V2 failures and how V3 addressed each one)
- Constraint: The document must be readable in 5 minutes. Borey spends ~5 min/day on this. Every paragraph must earn its space. No padding, no hedging language, no "on the other hand" -- clear statements with clear numbers
- Relationship: This is the terminal output. The document Gil presents.

---

## DEPENDENCY GRAPH

```
WAVE 1 (parallel)          WAVE 2 (parallel)         WAVE 3 (parallel)      WAVE 4 (sequential)
==================         ==================        ==================     ====================

Agent 01 (Put)       -->   Agent 11 (Attack) --+
                                               +--> Agent 21 (Rebuild) --+
Agent 05 (Ladder)    -->   Agent 15 (Attack) --+                         |
                                                                         |
Agent 02 (Bear Call) -->   Agent 12 (Attack) --+                         |
                                               +--> Agent 22 (Rebuild) --+
Agent 06 (Put Sell)  -->   Agent 16 (Attack) --+                         |
                                                                         |
Agent 03 (Butterfly) -->   Agent 13 (Attack) --+                         |
                                               +--> Agent 23 (Rebuild) --+-> Agent 26 (Portfolio)
Agent 07 (Fence)     -->   Agent 17 (Attack) --+                         |        |
                                                                         |        v
Agent 04 (0DTE)      -->   Agent 14 (Attack) --+                         |   Agent 27 (Borey)
                                               +--> Agent 24 (Rebuild) --+   Agent 28 (Worst Case)
Agent 08 (Calendar)  -->   Agent 18 (Attack) --+                         |   Agent 29 (Playbook)
                                                                         |        |
Agent 09 (Contrarian)-->   Agent 19 (Attack) --+                         |        v
                                               +--> Agent 25 (Rebuild) --+   Agent 30 (Present)
Agent 10 (Borey's)   -->   Agent 20 (Attack) --+
```

## EXECUTION TIMING

| Wave | Agents | Parallelism | Depends On | Estimated Duration |
|------|--------|-------------|------------|-------------------|
| 1 | 01-10 | All 10 in parallel | Input packet only | 3-5 min |
| 2 | 11-20 | All 10 in parallel | Wave 1 complete | 3-5 min |
| 3 | 21-25 | All 5 in parallel | Wave 2 complete | 3-5 min |
| 4a | 26 | Sequential | Wave 3 complete | 2-3 min |
| 4b | 27, 28, 29 | 3 in parallel | Agent 26 complete | 3-5 min |
| 4c | 30 | Sequential | 27, 28, 29 complete | 2-3 min |
| **Total** | **30 agents** | **4 waves + 3 sub-steps** | | **~16-26 min** |

## KILL CRITERIA -- WHAT MAKES V3 DIFFERENT FROM V1/V2

| V1/V2 Failure | V3 Fix | Enforced By |
|---------------|--------|-------------|
| Position agents biased toward their own structure | Every position gets a dedicated attacker who WANTS to kill it | Wave 2 red team |
| No adversarial review of the positions themselves | Red team agents produce SURVIVE/FIX/KILL verdicts with quantified evidence | Wave 2 output format |
| Lazy strike selection (round numbers) | Blue team agents must justify strikes with data (GEX, volume profile, dealer positioning) | Wave 1 constraints |
| No position sizing | Every position must state max loss in dollars and as % of account | Wave 1 + Wave 4 Agent 26 |
| No stop-losses | Every position must have a stop-loss level and a time stop | Wave 1 constraints |
| No exit plan if right OR wrong | Execution playbook agent (29) writes minute-by-minute instructions for every scenario | Wave 4 |
| "Thesis correct, timing off by 2 days" kills positions | Red team agents must specifically test the timing-mismatch scenario | Wave 2 mandate item 4 |
| Crowded trade risk ignored | Red team agents must assess whether the position is consensus retail and who the counterparty is | Wave 2 mandate item 5 |
| Complexity exceeds trader skill level | Red team and rebuild agents must honestly assess whether Borey can manage each structure | Wave 2 Agent 13, Wave 3 Agent 23 |
| No portfolio-level analysis | Portfolio constructor (26) analyzes correlation and diversification across failure modes | Wave 4 |
| V1 got a C from Borey, V2 was never graded | Borey simulation agent (27) grades V3 harder than V1 was graded | Wave 4 |
