# V3 Swarm Design: 30-Agent Strategy Diversity Blueprint

**Date:** 2026-04-06
**Design philosophy:** MAXIMUM STRATEGY DIVERSITY. No two agents propose the same structure type.
**Market context:** SPY ~678 (SPX ~6783), gap from ~661. Ceasefire unenforceable. VIX ~20. PCE Thu 4/10, CPI Fri 4/11. $10K account.
**V1-V2 gap analysis:** Too many similar put spreads and butterflies. V1 had 3 variants of put debit spreads and 2 butterflies. V2 repeated the same. Creative structures (condors with skewed wings, ratio backspreads, synthetics, multi-week campaigns, VIX products, sector proxies, risk reversals, collars, zebras) were entirely absent.

---

## CATEGORY A: DIRECTIONAL BEARISH (5 agents)

### Agent 01 -- Straight Long Put
- **Role:** Pure directional bear, maximum simplicity
- **Structure:** Long ATM put (single leg)
- **Unique angle:** The simplest possible expression of the gap fill thesis. No spread, no ratio, no complexity. Buy 1x SPY Apr 17 ~$676P. Let delta and vega do the work. This is the baseline that every other trade must justify being better than.
- **Output format:** Single trade ticket with Greeks at entry, P&L table at $5 SPY intervals, stop loss at 50% of premium, profit target at SPY $665.
- **Why this is different from V1/V2:** V1/V2 used puts as part of spreads. This agent proposes the naked long put as a standalone, forces honest comparison of spread overhead vs. simplicity.

### Agent 02 -- Bear Put Debit Spread (Narrow OTM)
- **Role:** Defined-risk directional, capital efficient
- **Structure:** Bear put debit spread, $5 wide, both strikes OTM
- **Unique angle:** Strikes 100% OTM -- buy SPY $672P / sell SPY $667P. Lower cost (~$1.00-1.20 debit) than V1/V2 spreads that straddled ATM. Trades probability for leverage. Requires a real move to profit but costs 75% less than V1's $676/$663 spread.
- **Output format:** Debit, max profit, breakeven, probability of profit at expiry, comparison to Agent 01's straight put on a per-dollar-risked basis.
- **Why this is different from V1/V2:** V1/V2 used wider (13-point) ATM-to-OTM spreads. This is narrow, cheap, highly leveraged -- a lottery ticket version.

### Agent 03 -- Synthetic Short Stock
- **Role:** Maximum bearish delta, no net premium
- **Structure:** Sell ATM call + Buy ATM put (same strike, same expiry)
- **Unique angle:** Behaves exactly like short 100 shares of SPY but with zero margin requirement beyond the spread risk. Sell SPY Apr 17 $678C / Buy SPY Apr 17 $678P for near-zero net debit. Delta approaches -100. This is the trade for someone who is CERTAIN the gap fills. Defined risk only if paired with a protective call wing (Agent 03 must note this and propose the unhedged version for maximum clarity, flagging the risk).
- **Output format:** Net debit/credit, delta/gamma/vega at entry, margin requirement, P&L chart, explicit risk warning about uncapped upside loss. Must include a "hedged variant" addendum with a $690C protective wing.
- **Why this is different from V1/V2:** No V1/V2 agent proposed a synthetic. This is the most aggressive defined-delta structure possible.

### Agent 04 -- Risk Reversal (Bearish)
- **Role:** Funded put via sold call premium
- **Structure:** Buy OTM put + Sell OTM call (different strikes, same expiry)
- **Unique angle:** Buy SPY Apr 17 $670P / Sell SPY Apr 17 $688C for near-zero cost. The sold call funds the put. If ceasefire holds and SPY rallies above $688, you lose -- but Agent 04 sizes this so max loss on the call side is bounded by a $693C protective wing (making it a risk reversal with a call spread cap). Net cost near zero. Gap fills = put prints. Rally = lose $500 max.
- **Output format:** Net premium, Greeks, P&L at SPY 650/660/670/678/688/693, breakeven both directions, probability analysis.
- **Why this is different from V1/V2:** No risk reversal was proposed. This structure has zero cost basis and profits from the thesis with no premium at risk.

### Agent 05 -- Deep ITM Put Spread (Bear Vertical)
- **Role:** High probability, low reward directional
- **Structure:** Bear put spread with ITM long strike
- **Unique angle:** Buy SPY Apr 17 $685P (deep ITM) / Sell SPY Apr 17 $680P. Costs ~$3.50 debit on a $5 spread. Max profit only $1.50, but probability of profit is 70%+. This is the "boring" trade that wins most of the time. Borey will recognize this as the institutional approach: sacrifice reward-to-risk for probability.
- **Output format:** Debit, max profit, probability of profit, comparison to Agent 02's leveraged approach. Include a table showing how this spread beats Agent 02 in 7 of 10 scenarios.
- **Why this is different from V1/V2:** V1/V2 spreads were all OTM-to-ATM. No agent explored the high-probability ITM debit spread.

---

## CATEGORY B: VOLATILITY PLAYS (5 agents)

### Agent 06 -- Long Straddle (PCE/CPI Catalyst)
- **Role:** Pure volatility buyer, direction-agnostic
- **Structure:** Long ATM straddle
- **Unique angle:** Buy SPY Apr 11 $678P + Buy SPY Apr 11 $678C. Expiry Friday after both PCE and CPI. Thesis: VIX at 20 is mispricing the binary risk of back-to-back macro data with a geopolitical powder keg. If either catalyst triggers a 2%+ move in either direction, the straddle prints. Entry Wednesday before PCE to capture the full vol expansion.
- **Output format:** Total debit, breakeven both directions, vega exposure, historical PCE/CPI move analysis (average SPY move on PCE day, CPI day), implied vs. realized vol comparison.
- **Why this is different from V1/V2:** V1 had a "PCE strangle" but placed it as a bearish-leaning play. This is pure non-directional vol, ATM, and honestly sized.

### Agent 07 -- Long Strangle (Wide Wings)
- **Role:** Cheap volatility lottery ticket
- **Structure:** Long OTM strangle
- **Unique angle:** Buy SPY Apr 11 $670P + Buy SPY Apr 11 $686C. Both legs well OTM. Total cost ~$2.50. This loses money in a boring week but pays 3-5x if either the gap fills violently OR the ceasefire rally extends on real deal progress. The wide strikes mean lower cost and higher leverage than the straddle.
- **Output format:** Total debit, breakevens, max loss (100% of premium), payout at SPY 660/665/670 and 686/690/695, comparison to Agent 06 straddle on a per-dollar basis.
- **Why this is different from V1/V2:** V1's strangle was conflated with a directional view. This is purely a volatility bet priced for maximum asymmetry.

### Agent 08 -- VIX Call Spread
- **Role:** Direct volatility product play
- **Structure:** VIX call debit spread
- **Unique angle:** Buy VIX Apr 16 $22C / Sell VIX Apr 16 $30C for ~$2.00 debit. VIX at 20 with two macro catalysts and a fragile geopolitical ceasefire. If fear spikes (ceasefire collapses, hot CPI, PCE miss), VIX easily hits 25-30. This is NOT a SPY trade -- it is a pure fear trade. Note: VIX options settle on VIX futures, not spot. Agent 08 must explain the basis between VIX spot, VIX futures, and the settlement mechanics.
- **Output format:** Debit, max profit at VIX 30+, breakeven VIX level, explanation of VIX settlement vs. spot, comparison to buying SPY puts on a vol-adjusted basis.
- **Why this is different from V1/V2:** Zero V1/V2 agents used VIX products. This is an entirely different instrument with different settlement mechanics.

### Agent 09 -- Put Calendar Spread
- **Role:** Sell near-term theta, own longer-term vega
- **Structure:** Put calendar (horizontal) spread
- **Unique angle:** Sell SPY Apr 11 $672P / Buy SPY Apr 25 $672P. Sell the weekly (rapid decay), own the monthly (slower decay, more vega). If SPY drifts toward $672 slowly over the next 2 weeks, the near put decays faster than the far put, generating profit. If VIX spikes, the long-dated put gains more than the short-dated put. The calendar profits from TIME and VOL simultaneously.
- **Output format:** Net debit, max profit zone, Greeks (especially vega differential between legs), P&L surface across price and time, optimal management (close when short leg expires, roll, or hold).
- **Why this is different from V1/V2:** V1 had a calendar but it was described poorly and not sized. Agent 09 provides a full P&L surface and explicit management rules.

### Agent 10 -- Double Calendar (Tent)
- **Role:** Non-directional theta + vega play with two profit zones
- **Structure:** Two calendar spreads at different strikes, creating a tent-shaped profit zone
- **Unique angle:** Sell SPY Apr 11 $672P / Buy SPY Apr 25 $672P AND Sell SPY Apr 11 $684C / Buy SPY Apr 25 $684C. Two profit peaks: one at $672 (gap fill zone), one at $684 (rally continuation). If SPY is anywhere between 670 and 686 when the short legs expire, the position profits. This is the "I don't know which way, but I know it won't stay exactly here" trade.
- **Output format:** Combined debit, profit tent visualization (P&L at each $2 increment from 660-695), vega exposure, theta decay schedule, management triggers.
- **Why this is different from V1/V2:** No double calendar was proposed. This is a sophisticated structure that profits from time + vol in a range.

---

## CATEGORY C: PREMIUM SELLING (4 agents)

### Agent 11 -- Bear Call Credit Spread
- **Role:** Neutral-to-bearish premium seller
- **Structure:** Call credit spread (bear call)
- **Unique angle:** Sell SPY Apr 17 $685C / Buy SPY Apr 17 $690C for ~$1.20 credit. SPY just needs to stay below $685 -- it does NOT need to drop. This wins if the gap fills, if SPY chops sideways, or even if SPY rallies modestly but fails to exceed $685. 70%+ probability of profit. The anti-thesis hedge: even if the ceasefire holds, $685 is unlikely to break in 11 days.
- **Output format:** Credit received, max loss, probability of profit, breakeven, theta per day, management rule (close at 50% of max profit).
- **Why this is different from V1/V2:** V1/V2 had a bear call but Agent 11 places strikes specifically above the ceasefire gap high, making it a "gap doesn't extend" bet rather than a "gap fills" bet. Subtle but important distinction.

### Agent 12 -- Iron Condor (Skewed Bearish)
- **Role:** Range-bound premium collector with bearish lean
- **Structure:** Iron condor with asymmetric wings
- **Unique angle:** Put side: Sell SPY Apr 11 $664P / Buy SPY Apr 11 $659P. Call side: Sell SPY Apr 11 $683C / Buy SPY Apr 11 $688C. The call wing is CLOSER to current price than the put wing, reflecting the bearish thesis. Call credit > put credit, so the net credit is larger. If SPY stays between 664 and 683, full profit. The asymmetry means the position earns MORE if SPY drifts lower (toward the gap) than if it rallies.
- **Output format:** Total credit, max loss each side, profit range, probability of profit, Greeks, P&L at $5 intervals, comparison to a symmetric condor.
- **Why this is different from V1/V2:** V1's condor was symmetric. Skewing the wings toward the thesis is a professional technique that V1/V2 missed.

### Agent 13 -- Jade Lizard
- **Role:** Premium seller with zero upside risk
- **Structure:** Short put + bear call spread
- **Unique angle:** Sell SPY Apr 17 $668P (naked short put) + Sell SPY Apr 17 $686C / Buy SPY Apr 17 $691C. The combined credit from the put and call spread exceeds the $5 call spread width, meaning ZERO risk if SPY rallies. All risk is to the downside -- but you WANT SPY to drop (gap fill thesis), so the short put assignment at $668 means you'd own SPY at $668 minus the credit, which is well below current price. Note: requires margin for the naked put. Agent 13 must calculate the margin requirement and confirm it fits a $10K account.
- **Output format:** Total credit, upside risk (should be zero), downside risk/breakeven, margin requirement, scenario analysis, explicit margin check against $10K.
- **Why this is different from V1/V2:** V1 had a jade lizard but it was poorly structured. Agent 13 recalculates with correct strikes and verifies the zero-upside-risk condition mathematically.

### Agent 14 -- Iron Butterfly
- **Role:** Maximum premium collection, defined risk
- **Structure:** Iron butterfly (ATM short straddle + OTM wings)
- **Unique angle:** Sell SPY Apr 11 $678P + Sell SPY Apr 11 $678C / Buy SPY Apr 11 $670P / Buy SPY Apr 11 $686C. Collects maximum premium by selling ATM. If SPY parks near $678 all week, massive profit. This is the ANTI-gap-fill trade -- the adversarial position. Agent 14 must explicitly argue the case: "What if the market is right? What if the ceasefire holds and SPY just sits here?" This forces the swarm to confront the base case null hypothesis.
- **Output format:** Credit received, max loss, breakevens, profit zone, explicit argument for why the gap might NOT fill (contrarian case), P&L at $2 intervals.
- **Why this is different from V1/V2:** No iron butterfly was proposed. This is the maximum-premium defined-risk structure and serves as the swarm's devil's advocate.

---

## CATEGORY D: EXOTIC / ASYMMETRIC (4 agents)

### Agent 15 -- Put Ratio Backspread
- **Role:** Asymmetric crash play, unlimited downside profit
- **Structure:** 1x2 put ratio backspread (sell 1 higher put, buy 2 lower puts)
- **Unique angle:** Sell 1x SPY Apr 17 $676P / Buy 2x SPY Apr 17 $668P for near-zero debit or small credit. If SPY drops modestly to $668-$676, you lose (the "valley of death"). But if SPY crashes through $660 (full gap fill + panic), the two long puts explode in value with no cap. This is the "ceasefire collapse" trade -- if Iran resumes hostilities, oil spikes, and SPY gaps down 3-4%, this pays 5-10x.
- **Output format:** Net debit/credit, P&L at every $5 from 640-680, "valley of death" zone clearly marked, max loss, unlimited profit potential below breakeven, probability analysis of scenarios.
- **Why this is different from V1/V2:** V1 had a ratio spread but it was a 1x2 ratio (short more strikes), which has uncapped risk. The backspread inverts this -- uncapped PROFIT, not risk.

### Agent 16 -- Broken Wing Butterfly (Skip Strike)
- **Role:** Directional butterfly with credit/zero-cost entry
- **Structure:** Broken wing put butterfly (uneven wing widths)
- **Unique angle:** Buy 1x SPY Apr 17 $674P / Sell 2x SPY Apr 17 $666P / Buy 1x SPY Apr 17 $654P. The lower wing is 12 points below the body while the upper wing is only 8 points above. This skip creates a net credit at entry. If SPY drops to $666 (near gap fill), max profit ~$800. If SPY stays above $674, you keep the small credit. The only losing zone is below $654, which requires a crash well beyond the gap fill.
- **Output format:** Net credit/debit, max profit at body strike, risk below lower wing, P&L diagram, comparison to standard (balanced) butterfly.
- **Why this is different from V1/V2:** V1 had a broken wing but used narrower skip. Agent 16 uses a wider skip for credit entry and higher max profit at the target.

### Agent 17 -- Christmas Tree (Ladder) Spread
- **Role:** Bearish spread with multiple short strikes targeting a zone, not a pin
- **Structure:** 1-1-1 put Christmas tree (buy 1 ATM, sell 1 OTM, sell 1 further OTM)
- **Unique angle:** Buy 1x SPY Apr 17 $678P / Sell 1x SPY Apr 17 $670P / Sell 1x SPY Apr 17 $662P. This profits across the ENTIRE gap fill zone ($662-$678) rather than requiring a precise pin like a butterfly. Max profit at $670. Below $662, the extra naked short put creates risk -- but $662 IS the gap fill level, so the thesis protects the structure. Agent 17 must clearly articulate why the risk below $662 is acceptable given the thesis.
- **Output format:** Debit, max profit, profitable range, risk below lower strike, margin requirement, P&L at $2 intervals, explicit risk acceptance argument.
- **Why this is different from V1/V2:** No Christmas tree was proposed. This is a wider profit zone than any butterfly with similar cost.

### Agent 18 -- Zebra (Zero Extrinsic Back Ratio)
- **Role:** Synthetic long put equivalent with minimal extrinsic value at risk
- **Structure:** ZEBRA -- Buy 2x deep ITM puts, sell 1x ATM put
- **Unique angle:** Buy 2x SPY Apr 17 $690P (deep ITM, ~$12.50 each) / Sell 1x SPY Apr 17 $678P (~$4.50). Net debit ~$20.50. Net delta ~ -100 (like short stock). The deep ITM puts have almost zero extrinsic value, so theta decay is minimal. The sold ATM put offsets ~40% of the cost. Behaves like short stock but with a defined-risk floor (max loss is the net debit if SPY rockets above $690).
- **Output format:** Net debit, delta, theta (should be near zero), P&L comparison to 100 shares short SPY, max loss, breakeven, capital requirement.
- **Why this is different from V1/V2:** No ZEBRA was proposed anywhere in V1/V2. This is a professional institutional structure that most retail traders have never seen. Borey will be impressed.

---

## CATEGORY E: MULTI-DAY CAMPAIGNS (3 agents)

### Agent 19 -- Scale-In Put Spread Ladder
- **Role:** Dollar-cost-average into the thesis across 3 entry points
- **Structure:** 3 separate put debit spreads entered on Mon, Wed, Fri of the same week
- **Unique angle:** Instead of one big bet on Monday, deploy 1/3 of risk each day:
  - **Monday:** Buy SPY Apr 17 $674P / Sell $669P at whatever the market gives
  - **Wednesday (pre-PCE):** Buy SPY Apr 17 $672P / Sell $667P, adjusting strikes to where SPY is
  - **Friday (post-CPI):** Buy SPY Apr 17 $670P / Sell $665P, adjusting to post-data reality
  - Each tranche risks ~$100 (1% of account). Total risk $300 (3%). If Monday's entry is bad (SPY rallies), Wednesday and Friday entries get better strikes. If Monday's entry is great (SPY already dropping), you scale in at even better levels.
- **Output format:** Entry schedule, conditional strike adjustments for each tranche, total risk budget, scenario table (SPY flat/up/down each day), comparison to single-entry approach.
- **Why this is different from V1/V2:** V1 had a "scale-in ladder" but it was a single-entry position with rolling, not a true multi-day campaign with conditional entries.

### Agent 20 -- Diagonal Put Spread Campaign (Poor Man's Put)
- **Role:** Long-term bearish position with near-term income
- **Structure:** Diagonal put spread rolled weekly
- **Unique angle:** Buy 1x SPY May 15 $678P (45 DTE, high delta ~0.55) / Sell 1x SPY Apr 11 $672P (4 DTE, rapid decay). Each week, sell a new weekly against the long put, collecting $0.50-$1.50 per roll. The long put captures the gap fill over 5 weeks. The short weeklies reduce cost basis by $2-6 over the campaign. If the gap fills fast, close the whole thing. If it takes 3-4 weeks, the weekly income subsidizes the wait.
- **Output format:** Initial debit, weekly roll schedule (4 potential rolls), cost basis reduction per roll, P&L scenarios at weeks 1/2/3/4, breakeven progression, max campaign risk.
- **Why this is different from V1/V2:** V1 had a diagonal but as a single snapshot. Agent 20 maps the entire 4-week campaign with explicit roll decisions and cost tracking.

### Agent 21 -- Rolling Iron Condor (Weekly Reset)
- **Role:** Weekly premium collection with strike adjustment
- **Structure:** Weekly iron condor, adjusted each Friday
- **Unique angle:** Week 1: Iron condor expiring Apr 11 with strikes based on current levels. Week 2: Roll to Apr 18, adjust strikes based on where SPY is. Week 3: Roll to Apr 25, tighten or widen based on realized vol. Each week collects $1.00-$1.80 in premium. Over 3 weeks, total collected could be $3-$5 against $5 max width. This is a BUSINESS, not a trade. Agent 21 frames it as "income generation during a volatile period" rather than a directional bet.
- **Output format:** Week 1/2/3 strike templates, adjustment rules (if SPY moves X, shift strikes by Y), total projected income, worst case per week, cumulative P&L tracker.
- **Why this is different from V1/V2:** No rolling multi-week premium strategy was proposed. This introduces the concept of options as a recurring business.

---

## CATEGORY F: HEDGED / PORTFOLIO (3 agents)

### Agent 22 -- Collar (Protective)
- **Role:** Protect existing SPY long exposure (or hypothetical allocation)
- **Structure:** Own 100 shares SPY + Buy OTM put + Sell OTM call
- **Unique angle:** Premise -- what if the $10K account already has some SPY exposure (or wants some)? Buy 100 SPY at $678 ($67,800 -- obviously hypothetical for a $10K account, so scale to 10 shares or use SPY options as proxy). Buy $670P for protection, sell $686C to fund it. Net cost of collar near zero. This caps upside at $686 but floors downside at $670. Agent 22 must acknowledge the capital constraint and propose a "mini collar" variant using 1x contracts or a spread-based synthetic equivalent.
- **Output format:** Collar cost (net of call premium vs. put premium), max profit, max loss, breakevens, mini-collar variant for $10K account, comparison to just buying puts.
- **Why this is different from V1/V2:** No collar was proposed. This introduces portfolio protection thinking rather than speculative positioning.

### Agent 23 -- Paired Trade: SPY Put + QQQ Call
- **Role:** Relative value / sector rotation hedge
- **Structure:** Long SPY put + Long QQQ call (paired)
- **Unique angle:** The ceasefire primarily affects energy/oil/geopolitics -- if it collapses, SPY drops (energy weight) but tech (QQQ) might be relatively unaffected or even benefit from flight to quality/growth. Buy SPY Apr 17 $672P + Buy QQQ Apr 17 $500C. If ceasefire collapses: SPY drops (put profits), QQQ holds or rises (call profits or limits loss). If ceasefire holds: SPY rallies (put loses), QQQ also rallies (call profits, partially offsetting). This is a hedged position that wins in 3 of 4 quadrants.
- **Output format:** Combined debit, scenario matrix (SPY up/down x QQQ up/down), correlation analysis, net P&L in each scenario, portfolio beta.
- **Why this is different from V1/V2:** No cross-asset paired trade was proposed. This introduces relative value thinking.

### Agent 24 -- Fence (Put Spread + Call Kicker)
- **Role:** Bearish with asymmetric upside protection
- **Structure:** Bear put spread + long OTM call
- **Unique angle:** Buy SPY Apr 17 $674P / Sell SPY Apr 17 $666P (bear put spread for the gap fill) + Buy 1x SPY Apr 17 $692C (cheap call for ceasefire extension). The put spread profits if gap fills. The $692C is a $0.30-$0.50 lottery ticket: if the ceasefire turns real and SPY blasts to $695+, the call kicker prevents disaster. Total cost: ~$1.80 spread + $0.40 call = $2.20. The call costs almost nothing but provides psychological comfort and actual tail protection.
- **Output format:** Total debit, P&L in gap-fill scenario, P&L in rally scenario, breakevens, cost of the call kicker as % of total position, argument for why the kicker is worth the drag.
- **Why this is different from V1/V2:** V2 had a "hedged fence" but Agent 24 uses a cheaper call kicker further OTM and explicitly quantifies the cost/benefit of the insurance.

---

## CATEGORY G: OIL / PROXY PLAYS (2 agents)

### Agent 25 -- USO Put Spread (Oil Spike Reversal)
- **Role:** Sector proxy for ceasefire collapse
- **Structure:** USO (United States Oil Fund) bear put spread
- **Unique angle:** Oil crashed 16% to ~$94 on ceasefire news. If the ceasefire collapses (31 militias, Supreme Leader in coma, Hormuz still mostly blocked), oil spikes back toward $100-$110. BUT -- Agent 25 takes the contrarian view: even if ceasefire collapses, oil might NOT recover to pre-ceasefire levels because demand destruction has already occurred. So USO puts (or put spreads if USO is elevated) target the scenario where oil stays low AND equity markets still sell off. Alternatively, this agent can propose USO CALL spreads as a hedge against the gap fill thesis being WRONG -- if ceasefire collapses, oil surges, and Agent 25's USO calls profit to offset SPY put losses.
- **Output format:** USO current price, put or call spread structure, debit, max profit, correlation analysis to SPY, scenario matrix (ceasefire holds/collapses x oil up/down), explicit logic for which direction to trade.
- **Why this is different from V1/V2:** Zero oil/commodity plays were proposed.

### Agent 26 -- XLE Put Spread (Energy Sector Short)
- **Role:** Energy sector proxy for ceasefire collapse
- **Structure:** XLE (Energy Select Sector SPDR) put debit spread
- **Unique angle:** If ceasefire collapses, oil spikes, but energy STOCKS might still sell off because the broader market panic overwhelms the oil price benefit. Alternatively, energy stocks that rallied on "peace dividend" (lower input costs for non-energy) reverse. Agent 26 targets XLE specifically because it isolates the energy component of SPY. Buy XLE Apr 17 put spread targeting a 3-5% decline. This is a SECTOR bet, not a broad market bet -- it has different correlation and timing properties than SPY puts.
- **Output format:** XLE current price, spread structure, debit, max profit, XLE vs. SPY correlation, scenario analysis, why XLE might move differently from SPY.
- **Why this is different from V1/V2:** No sector ETF trades were proposed. This adds a completely different risk factor to the portfolio.

---

## CATEGORY H: META AGENTS (4 agents)

### Agent 27 -- Portfolio Constructor
- **Role:** Select 3-5 positions from Agents 01-26 that maximize diversification
- **Structure:** N/A -- this agent does not propose trades. It SELECTS from other agents' output.
- **Unique angle:** Agent 27 receives all 26 position proposals and constructs an optimal portfolio of 3-5 positions. Selection criteria:
  1. **Correlation:** No two positions should have >0.7 correlation (e.g., don't pick both the put spread and the straight put)
  2. **Scenario coverage:** Portfolio must have positive expected P&L in at least 3 of 4 scenarios (gap fills fast, gap fills slow, range-bound, rally)
  3. **Risk budget:** Total max loss <= 5% of account ($500)
  4. **Structural diversity:** At least one directional, one vol play, one premium seller
  5. **Simplicity bonus:** Prefer simpler structures when P&L profiles are similar
- **Output format:** Selected positions table, correlation matrix, scenario coverage heatmap, total risk/reward, combined Greeks, execution priority (which to enter first).

### Agent 28 -- Adversarial Reviewer
- **Role:** Destroy every position. Find the fatal flaw.
- **Structure:** N/A -- pure critique.
- **Unique angle:** Agent 28 reads all 26 proposals and writes a "red team" report. For each position, it must find:
  1. The scenario where it loses maximum money
  2. The hidden assumption that could be wrong
  3. The execution risk (bid-ask spread, liquidity, fill quality)
  4. The sizing error (if any -- does the max loss actually fit the account?)
  5. The theta clock: how many days until this position starts actively losing money
  Agent 28 is ADVERSARIAL. It is not constructive. Its job is to kill bad trades before they enter the portfolio.
- **Output format:** For each of the 26 positions: 2-3 sentence kill shot. Then a ranked "survival list" of the 10 positions that withstood scrutiny, with justification.

### Agent 29 -- Borey's Pick
- **Role:** Simulate an experienced trader's reaction
- **Structure:** N/A -- selection and commentary.
- **Unique angle:** Agent 29 roleplays as Borey -- an experienced options trader who sees hundreds of trade ideas per week. Borey is NOT impressed by complexity. Borey is NOT impressed by clever names. Borey cares about: is the thesis clear? Is the risk defined? Is the sizing correct? Is the entry timing realistic? Would this trade make money? Agent 29 picks the 1-2 trades that Borey would actually put on, explains WHY in Borey's voice (direct, blunt, no BS), and explains what he'd change about the rest ("Too wide, too narrow, wrong expiry, overthinking it").
- **Output format:** "Borey's pick" with 2-3 sentence justification, "Borey's reject pile" with 1-sentence dismissals, "What Borey would tweak" for the close-but-not-quite trades.

### Agent 30 -- Final Synthesizer
- **Role:** Produce the final deliverable for the user
- **Structure:** N/A -- synthesis.
- **Unique angle:** Agent 30 takes input from Agents 27 (portfolio constructor), 28 (adversarial reviewer), and 29 (Borey's pick). It resolves conflicts between them, produces a single final portfolio recommendation of 2-4 positions, and writes the presentation-ready output. This is the ONLY output the user sees. It must include:
  1. The recommended portfolio with exact trade tickets
  2. Total risk, total max profit, scenario table
  3. Entry timing and order for Monday morning
  4. Management rules (when to adjust, when to close, when to add)
  5. A "if Borey says no to everything, just do this one trade" fallback
- **Output format:** Presentation-ready markdown with trade tickets, Greeks, P&L table, management playbook, and the single-trade fallback.

---

## EXECUTION ARCHITECTURE

### Wave 1: Position Generators (Agents 01-26)
- **Parallelism:** All 26 agents run simultaneously
- **Input:** Shared market context block (SPY $678, SPX 6783, VIX 20, PCE/CPI dates, ceasefire analysis, $10K account, gap fill thesis)
- **Output:** Each agent writes one markdown file to `.planning/strategy-positions-v3/`
- **Constraint:** Each agent MUST output a different structure type. The dispatcher prompt explicitly lists which structure each agent is assigned and prohibits deviation.
- **Estimated time:** 3-5 minutes for all 26 in parallel

### Wave 2: Meta Agents (Agents 27-30)
- **Parallelism:** Agents 27, 28, 29 run in parallel (they read Wave 1 output independently)
- **Input:** All 26 position files from Wave 1
- **Output:** Agent 27 writes portfolio-construction.md, Agent 28 writes adversarial-review.md, Agent 29 writes boreys-pick.md
- **Estimated time:** 2-3 minutes for all 3 in parallel

### Wave 3: Final Synthesis (Agent 30 only)
- **Parallelism:** None -- Agent 30 runs alone after Wave 2 completes
- **Input:** Outputs from Agents 27, 28, 29 plus original 26 positions
- **Output:** `final-recommendation.md` -- the single deliverable
- **Estimated time:** 1-2 minutes

### Total estimated time: 6-10 minutes

---

## DIVERSITY VERIFICATION CHECKLIST

Every structure below must appear exactly ONCE across the 30 agents:

| # | Structure | Agent | Category |
|---|-----------|-------|----------|
| 1 | Long put (single leg) | 01 | Directional |
| 2 | Bear put debit spread (narrow OTM) | 02 | Directional |
| 3 | Synthetic short (ATM call/put combo) | 03 | Directional |
| 4 | Risk reversal (bearish) | 04 | Directional |
| 5 | Deep ITM put spread | 05 | Directional |
| 6 | Long straddle | 06 | Volatility |
| 7 | Long strangle (wide) | 07 | Volatility |
| 8 | VIX call spread | 08 | Volatility |
| 9 | Put calendar spread | 09 | Volatility |
| 10 | Double calendar (tent) | 10 | Volatility |
| 11 | Bear call credit spread | 11 | Premium |
| 12 | Iron condor (skewed) | 12 | Premium |
| 13 | Jade lizard | 13 | Premium |
| 14 | Iron butterfly | 14 | Premium |
| 15 | Put ratio backspread (1x2) | 15 | Exotic |
| 16 | Broken wing butterfly (skip strike) | 16 | Exotic |
| 17 | Christmas tree (ladder) | 17 | Exotic |
| 18 | ZEBRA (zero extrinsic back ratio) | 18 | Exotic |
| 19 | Scale-in put spread ladder (3 entries) | 19 | Campaign |
| 20 | Diagonal put spread (rolling weekly) | 20 | Campaign |
| 21 | Rolling iron condor (weekly reset) | 21 | Campaign |
| 22 | Collar (protective) | 22 | Hedged |
| 23 | Paired trade (SPY put + QQQ call) | 23 | Hedged |
| 24 | Fence (put spread + call kicker) | 24 | Hedged |
| 25 | USO oil proxy play | 25 | Proxy |
| 26 | XLE energy sector short | 26 | Proxy |
| 27 | Portfolio constructor (meta) | 27 | Meta |
| 28 | Adversarial reviewer (meta) | 28 | Meta |
| 29 | Borey's pick (meta) | 29 | Meta |
| 30 | Final synthesizer (meta) | 30 | Meta |

**Zero overlap. 26 unique structures + 4 meta roles = 30 agents.**

---

## V1/V2 MISTAKES THIS DESIGN CORRECTS

1. **Duplicate structures eliminated.** V1 had Agent 01 (long put), Agent 02 (put spread), Agent 05 (butterfly), Agent 11 (broken wing butterfly), Agent 17 (wide butterfly) -- three butterflies. V3 has exactly ONE butterfly variant (Agent 16, broken wing with skip strike).
2. **Missing asset classes added.** V1/V2 had zero VIX, zero oil, zero sector, zero cross-asset trades. V3 has VIX (Agent 08), USO (Agent 25), XLE (Agent 26), and QQQ (Agent 23).
3. **Missing structures added.** V1/V2 had no synthetic, no risk reversal, no collar, no ZEBRA, no Christmas tree, no double calendar. V3 has all of these.
4. **Multi-week campaigns formalized.** V1's "scale-in ladder" was a single entry. V3 has three true campaigns (Agents 19-21) with explicit day-by-day or week-by-week execution schedules.
5. **Meta agents have clear dependencies.** V1's Agent 19 (portfolio) and Agent 20 (consensus) had overlapping mandates. V3 separates: Agent 27 constructs, Agent 28 destroys, Agent 29 selects, Agent 30 synthesizes. No overlap.
6. **Iron butterfly added as contrarian.** V1/V2 never proposed a position that profits from the gap NOT filling. Agent 14 explicitly argues the null hypothesis.
7. **Adversarial review is a dedicated agent, not an afterthought.** V1 buried critique in the portfolio agent. V3's Agent 28 exists solely to kill bad trades.
