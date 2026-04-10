# W3-01: GEX CORRECTION -- Red Team Audit of All Wave 2 Positions
## Real CBOE Data vs Estimated Strike Map

**Date:** 2026-04-06
**Source:** Live pipeline run against CBOE data (13,356 contracts, 37 expirations)
**Author:** Red Team Agent #1
**Status:** CRITICAL -- All Wave 2 positions must be re-evaluated before entry

---

## THE PROBLEM

W1-02 (GEX Strike Map) was built from ESTIMATES because the platform could not run live at the time. The estimates assumed "typical post-gap OI distribution" and placed the gamma flip near spot ($678). The live pipeline just ran. The estimates were SIGNIFICANTLY wrong.

### Estimated vs Real GEX Levels

| Level | W1-02 ESTIMATE | REAL (CBOE live) | Error | Direction |
|-------|---------------|------------------|-------|-----------|
| **Gamma Flip** | $678 | **$656.19** | **-$21.81** | Estimated 22 points too HIGH |
| **Gamma Ceiling** | $685 | **$680** | -$5.00 | Estimated 5 points too high |
| **Gamma Floor** | $665 | **$650** | **-$15.00** | Estimated 15 points too LOW |
| **Max Pain** | $675 | **$656** | **-$19.00** | Estimated 19 points too high |
| **Squeeze Probability** | 5-15% | **40%** | +25-35% | Massively underestimated |

### Real PCR Data

| Metric | W1-02 Estimate | REAL (CBOE live) | Implication |
|--------|---------------|------------------|-------------|
| Volume PCR | ~0.8 (neutral) | **1.337 (EXTREME FEAR)** | Everyone is already hedged with puts |
| OI PCR | ~0.8-1.0 (neutral) | **1.374 (Dealer LONG GAMMA)** | Dealers DAMPEN moves at current price |

### Real Key OI Levels
- **Call side:** $656, $660, $665, $670, $675, $680
- **Put side:** $630, $638, $640, $645, $650

---

## WHAT THE REAL DATA CHANGES ABOUT THE MARKET THESIS

### 1. SPY at $676 is $20 ABOVE the real gamma flip ($656)

The entire Wave 2 swarm operated under the belief that SPY was sitting ON the gamma flip at $678. In reality, SPY is 20 points ABOVE the flip. This means:

- **Dealers are LONG gamma at current prices.** Their hedging DAMPENS moves, not amplifies them.
- A selloff from $676 to $665 occurs in the DAMPENED regime. It will be slow, orderly, and resisted by dealer buying.
- The "trapdoor" that W2-10 built its entire thesis around does not open until SPY reaches $656 -- a 3% decline from current levels.

### 2. The gap fill zone ($661) is ABOVE the gamma flip ($656)

Even a full gap fill to $661 keeps SPY in the long-gamma (dampened) regime. The acceleration zone only kicks in below $656. This means gap fills are ORDERLY, not violent.

### 3. Max pain and gamma flip converge at $656

Two independent signals -- max pain (writer payout minimization) and gamma flip (dealer hedging regime change) -- point to the SAME level. $656 is a powerful confluence. It is the real "line in the sand," not $678.

### 4. Extreme fear PCR (1.337) = crowded puts

Everyone already owns puts. New put buying is expensive (crowded trade). This makes SELLING puts at support levels more attractive, not buying them. The estimated "neutral" PCR was wrong by a full regime classification.

### 5. 40% squeeze probability vs 5-15% estimated

The real squeeze probability is nearly 3x the high end of the estimate. This significantly increases the probability of a short squeeze through the gamma ceiling ($680, not $685 as estimated).

---

## POSITION-BY-POSITION AUDIT

---

### W2-01: Borey's Put Spread -- Buy $675P / Sell $669P

**GEX Levels Used:** Long strike at $675 (est. max pain), short strike at $669 (est. gap midpoint)

**What Was Wrong:**
- $675 was justified as "max pain magnet" -- real max pain is $656 (19 points lower)
- $669 was justified as "gap midpoint, GEX aligned zone" -- in reality, $669 is deep in the long-gamma dampened zone, NOT aligned for puts
- The entire spread sits $13-$19 above the real action zone ($650-$656)
- At current prices, puts at $675 and $669 are in the DAMPENED regime where dealers resist the move

**What Should Change:**
- Real max pain magnet is $656, not $675
- Real gamma floor support is $650, not $665
- A GEX-correct bear put spread would be: Buy $656P / Sell $650P ($6 wide) -- gamma flip to gamma floor
- Alternatively: Buy $660P / Sell $650P ($10 wide) -- near gap bottom to real gamma floor

**Does It Still Work?**
The spread can still profit if SPY drops $7+ to reach the $669 short strike. But the thesis justification is wrong: dealers are NOT amplifying the move in this zone -- they are dampening it. The "gravitational pull to max pain" at $675 is fiction; real max pain is at $656. The spread profits only on directional conviction, NOT on GEX mechanics as claimed.

**Verdict: FIX**

The structure is not fatally flawed (defined risk, within budget), but the strike selection is wrong. If SPY drops to $669, you profit -- but the GEX tailwind the agent described does not exist at these strikes. The real tailwind starts at $656. For a $200 budget, the corrected spread Buy $656P / Sell $650P is the GEX-aligned trade.

---

### W2-02: Bear Call Credit Spread -- Sell $685C / Buy $692C

**GEX Levels Used:** Short strike at $685 (est. gamma ceiling), long strike at $692 (est. hedge wing)

**What Was Wrong:**
- $685 was justified as "gamma ceiling, strongest call resistance" -- real gamma ceiling is $680 (5 points lower)
- The short call at $685 is $5 ABOVE the real ceiling, meaning it has LESS dealer resistance backing it
- The agent calculated an honest 63% PoP based on $685 being $7 OTM -- but with real ceiling at $680, the short call should be there for maximum structural backing

**What Should Change:**
- Real gamma ceiling is $680, not $685
- Corrected spread: Sell $680C / Buy $687C ($7 wide)
- This places the short call AT the real resistance where dealers are actively selling into rallies
- BUT: $680 is only $4 OTM from SPY $676 -- PoP drops significantly
- The corrected PoP would be approximately 50-55% (essentially a coin flip)

**Does It Still Work?**
The original $685/$692 spread actually BENEFITS from the correction in one sense: $685 is FARTHER from the gamma ceiling at $680, which means SPY is even less likely to reach $685 (it has to push through $680 resistance first). The spread is safer than the agent thought, not more dangerous.

However, the credit collected will be lower than estimated because the $685 call is farther OTM than assumed (relative to the ceiling). And the structural resistance argument at $685 is weaker -- the real resistance is at $680.

**Verdict: SURVIVE**

The position is accidentally safer than designed. $685 is above the real ceiling ($680), so SPY has to push through dealer resistance at $680 before reaching the short strike. The thesis is wrong about WHY it works (not ceiling resistance at $685), but the outcome is favorable: extra buffer. Keep the $685/$692 construction. Alternatively, move to $680/$687 for a higher-credit, higher-risk, structurally-anchored version.

---

### W2-03: CPI Weekend Strangle -- Buy $675P / Buy $692C

**GEX Levels Used:** Put at $675 (est. max pain), call at $692 (est. hedge wing)

**What Was Wrong:**
- $675 was justified as "max pain magnet, significance 0.8" -- real max pain is $656
- The put leg is $19 above real max pain -- it has no gravitational pull benefit
- The put needs SPY to drop to $673 to breakeven -- that is still $17 above the real gamma flip ($656)
- Even at the put's breakeven, the move is entirely within the DAMPENED dealer-long-gamma regime

**What Should Change:**
- A GEX-correct put leg would be at $656 (real max pain / gamma flip confluence) or $660 (near gap bottom)
- The call leg at $692 is still reasonable -- it is above the real ceiling ($680) and profits on a genuine breakout
- Corrected strangle: Buy $656P / Buy $692C -- true extremes of the GEX map
- Problem: the $656P is deep OTM ($20 below spot), so it costs very little (~$0.30-0.50 at 6 DTE, VIX 20). The strangle becomes radically asymmetric in cost, which may be acceptable.

**Does It Still Work?**
The $675 put can still profit if SPY drops $5+. But the "max pain gravitational pull" justification is false. The real gravitational pull is toward $656, which actually SUPPORTS the put thesis (SPY has further to fall). However, the $675P captures only the first leg of the move -- it does not benefit from the gamma flip acceleration below $656.

The strangle structure is intact but sub-optimal. The put leg should be cheaper and deeper for the real GEX dynamics to be captured.

**Verdict: FIX**

Replace $675P with $660P or $656P. The strangle cost drops (the put is cheaper), but the downside breakeven moves lower. The call side is fine. The corrected strangle would be: Buy $660P / Buy $692C for approximately $0.80-1.20 total debit (cheaper and more GEX-aligned).

---

### W2-04: Scale-In Put Ladder -- Entry 1: $678P, Entry 2: $675P

**GEX Levels Used:** $678 (est. gamma flip for Entry 1), $675 (est. max pain for Entry 2)

**What Was Wrong:**
- $678 was the FOUNDATION of this trade -- "gamma flip probe." The agent wrote: "If SPY breaks below $678, it enters negative GEX territory where dealer hedging AMPLIFIES the drop."
- REAL gamma flip is $656. SPY breaking $678 does NOTHING to dealer hedging behavior. The regime change is 22 points lower.
- $675 was justified as "max pain magnet" -- real max pain is $656
- Both entries are buying puts in the DAMPENED regime where dealers resist the drop
- The "trapdoor" the agent described does not exist at $678. It exists at $656.

**What Should Change:**
- Entry 1 probe should be at or near $656 (real gamma flip), not $678
- Entry 2 confirm should be at $650 (real gamma floor) if Entry 1 is working
- Corrected ladder: Entry 1: Buy $660P (near flip), Entry 2: Buy $656P (at flip)
- Problem: both strikes are $16-20 OTM from current spot, making them very cheap (~$0.50-1.50) but with very low probability of reaching profitability in one week

**Does It Still Work?**
The ATM put at $678 will profit on any decline regardless of GEX dynamics -- it has delta ~0.50 and gains value purely directionally. But the THESIS is wrong: the "gamma amplification" justification is false at these strikes. The agent was paying ATM premium ($4.50/contract) for a GEX mechanic that does not exist at that price level.

The scale-in concept is sound, but the strikes are directional bets masquerading as GEX-informed trades. The agent would have been better served buying cheaper OTM puts at the REAL gamma flip.

**Verdict: KILL**

The entire thesis ("probe at the gamma flip, confirm with amplification") is built on the wrong gamma flip. At $678, there is no flip, no amplification, no trapdoor. You are paying $4.50 for an ATM put justified by a mechanic that operates 22 points lower. The directional bet may work, but the GEX edge does not exist. The $200 risk budget is better allocated to positions anchored at real GEX levels.

---

### W2-05: Diagonal Put Spread -- Buy Apr 25 $675P / Sell Apr 11 $669P

**GEX Levels Used:** $675 (est. max pain for long leg), $669 (est. gap midpoint for short leg)

**What Was Wrong:**
- $675 long leg justified as "max pain magnet" -- real max pain is $656
- $669 short leg justified as "gap midpoint, GEX aligned support" -- in reality, $669 has no GEX significance; it is in the dampened zone
- The rolling plan assumes selling puts at $669 and $665 as "GEX support" levels -- $665 is NOT the real gamma floor ($650 is)
- The "path to free position" through rolling depends on sufficient premium at the short strikes -- if markets recognize these are NOT support levels, premium may be lower than estimated

**What Should Change:**
- Corrected diagonal: Buy Apr 25 $660P / Sell Apr 11 $650P
- Long leg near gap bottom, short leg at real gamma floor ($650)
- $10 wide, capturing the zone where the real GEX dynamics operate
- Rolling plan would sell $650P each week (real gamma floor support = better premium anchor)

**Does It Still Work?**
The diagonal structure is sound -- the timing hedge concept is valid regardless of GEX levels. But both strikes are in the "wrong" zone. The $675 long leg is $19 above the real gravitational center ($656). The $669 short leg has no structural support backing its premium.

The trade can still profit on a directional move, but the "free position" math depends on selling sufficient premium at the short strikes. If the market does not respect $669 as support (it shouldn't -- real support is at $650), the short leg premiums may be lower, pushing the "free" point further out.

**Verdict: FIX**

Move both strikes $15-20 lower. The diagonal concept is correct; the execution zone is wrong. Corrected: Buy Apr 25 $660P / Sell Apr 11 $650P. This aligns with real GEX support and gravitational levels. Budget may change (deeper OTM = cheaper long leg, but also less premium on short leg).

---

### W2-06: Broken Wing Butterfly -- 675/665/652

**GEX Levels Used:** Upper wing $675 (est. max pain), body $665 (est. gamma floor), lower wing $652

**What Was Wrong:**
- Body at $665 was justified as "gamma floor -- dealer short-gamma accelerates pin." Real gamma floor is $650 (15 points lower).
- Upper wing at $675 was justified as "max pain, gravitational pull." Real max pain is $656.
- The ENTIRE profit zone ($656.42 to $673.58) is in the DAMPENED regime where dealers resist movement
- The "dealer mechanics at $665" section describing short-gamma acceleration is FALSE at $665 -- dealers are LONG gamma at $665 (it is above the real flip at $656)
- The Monte Carlo used estimated GEX parameters, not real ones
- Lower wing at $652 is close to the REAL gamma floor ($650), which means there IS real support near the lower wing -- but the agent didn't know this

**What Should Change:**
- Body should be at $650 (real gamma floor) or $656 (real gamma flip)
- Corrected BWB: Buy $660P / Sell 2x $650P / Buy $640P (body at real floor)
- Alternatively: Buy $660P / Sell 2x $656P / Buy $645P (body at gamma flip/max pain confluence)
- The profit zone shifts down ~15 points
- This is a fundamentally different trade targeting a different price zone

**Does It Still Work?**
The butterfly structure with body at $665 requires SPY to reach $665 for max profit. That is $11 below current spot. With dealers DAMPENING the move to $665, the probability of reaching the body is lower than the Monte Carlo estimated (which assumed dealers were SHORT gamma there, amplifying the pin).

The 27.9% probability of profit was computed under wrong dealer positioning assumptions. Real probability is likely lower because the dampened regime makes a $665 pin less likely.

The positive expected value (+$8.30/contract) may flip negative with corrected GEX dynamics.

**Verdict: KILL**

The body is at the wrong level. The gamma floor is NOT at $665 -- it is at $650. The entire "dealer short-gamma accelerates pin" thesis is wrong at $665. Moving the body to $650 creates a fundamentally different trade requiring a 3.8% decline instead of 1.9%. The original structure's probability profile, Greeks analysis, and P&L curves are all based on wrong GEX inputs. Rebuild from scratch with real levels.

---

### W2-07: Oil Proxy Trade -- USO $80C/$86C

**GEX Levels Used:** None directly. This trade is on USO, not SPY.

**What Was Wrong:**
- Nothing about the USO trade itself depends on SPY GEX levels
- The correlation argument (how it pairs with SPY positions) references estimated levels but the core thesis is about oil, not equity GEX

**What Should Change:**
- The pair trade P&L matrix references "SPY $678P/$665P bear put spread" -- those SPY strikes are wrong per the correction, but the USO trade does not depend on them
- The USO trade should be paired with CORRECTED SPY positions, not the estimated ones

**Does It Still Work?**
Yes. The oil proxy thesis is completely independent of SPY GEX levels. Oil goes up when Hormuz closes, regardless of where SPY's gamma flip sits. The correlation benefit is actually STRONGER now: if SPY stays above $656 (real gamma flip) and dealers dampen the equity selloff, the USO calls provide independent profit from oil spiking while the SPY puts underperform in the dampened regime.

**Verdict: SURVIVE**

This is the only position that is completely unaffected by the GEX correction. It was designed to be uncorrelated to SPY GEX dynamics, and it succeeds at that. The decorrelation argument is actually enhanced: dealer dampening above $656 means SPY may not sell off as much as the bears expect, making the USO call spread an even more valuable portfolio diversifier.

---

### W2-08: Crash Convexity -- Sell 2x $665P / Buy 6x $645P

**GEX Levels Used:** Short strike at $665 (est. gamma floor), long strikes at $645

**What Was Wrong:**
- $665 short strike justified as "gamma floor -- dealers hedge massive put OI creating support floor." Real gamma floor is $650 (15 points lower).
- The "support floor" at $665 does not exist. Real support is at $650.
- This means the short puts at $665 are NOT at a support level -- they are 9 points above real support
- The danger zone analysis assumed $665 was support-backed. Without real support at $665, the probability of SPY reaching $665 and continuing through to the danger zone is HIGHER than estimated
- The $645 long strikes are $5 BELOW the real gamma floor ($650) -- they sit in the acceleration zone where dealer hedging stops providing support. This is actually correct for a crash trade.

**What Should Change:**
- Short strike should move to $650 (real gamma floor) to benefit from real dealer support
- Corrected structure: Sell 2x $650P / Buy 6x $630P (or $635P)
- The short leg at $650 has real support; the long legs in the $630-$635 zone are in the true acceleration void
- This shifts the danger zone deeper and aligns the short leg with actual institutional flow

**Does It Still Work?**
Partially. The $645 long strikes accidentally sit in the correct zone -- below the real gamma floor ($650), in the acceleration void. The problem is the SHORT strike at $665, which has no real support. If SPY sells off orderly to $665, the short puts go ITM and the position enters the danger zone at $665 instead of having real support there.

However, the agent's own analysis noted that at VIX 30+, the danger zone disappears. The VIX expansion tables are based on structural ratios (3:1 vega) that do not depend on GEX levels. The vega protection mechanism still works.

**Verdict: FIX**

Move the short strike from $665 to $650 (real gamma floor). This gives the short leg actual dealer support, extends the "safe zone" from $665 down to $650, and pushes the danger zone $15 deeper. The long strikes could stay at $645 (only $5 below the new short) or move to $630 for a wider, more convex structure. Sell 2x $650P / Buy 6x $630P captures the full real acceleration zone.

---

### W2-09: Contrarian Bull -- Buy $685C / Sell $692C

**GEX Levels Used:** Long call at $685 (est. gamma ceiling), short call at $692

**What Was Wrong:**
- $685 was justified as "gamma ceiling -- if SPY breaks through, short squeeze mechanics kick in"
- Real gamma ceiling is $680. The breakout level is 5 points LOWER than assumed.
- This means the call spread needs SPY to go 5 points further than the real ceiling to be ITM
- The squeeze probability is 40% (not 5-15%), which SUPPORTS the bull thesis
- The "short squeeze through gamma ceiling" argument is actually stronger with the real data, but the ceiling is at $680, not $685

**What Should Change:**
- Corrected spread: Buy $680C / Sell $687C ($7 wide)
- Long call AT the real gamma ceiling -- the breakout trigger is right at the strike
- $680 is only $4 OTM from current SPY $676. More expensive but higher probability.
- The 40% squeeze probability significantly improves the thesis
- Alternatively: keep $685/$692 but understand it requires a move THROUGH the ceiling, not to it

**Does It Still Work?**
Actually better than before. The corrected data shows:
1. 40% squeeze probability (vs 5-15% estimated) -- dramatically improves the bull case
2. Gamma ceiling at $680 (vs $685) -- SPY only needs a $4 move to reach resistance, and a breakout through $680 with 40% squeeze probability could easily carry to $685+
3. Dealer long gamma dampening means a selloff is LESS likely, which preserves the call spread's value longer

The $685/$692 spread still works because it captures a move THROUGH the real ceiling. The real ceiling at $680 acts as a launch pad -- once SPY breaks $680, the next resistance is further up, and the $685 strike is in the "thin air" zone.

**Verdict: SURVIVE (with upgrade opportunity)**

The position accidentally benefits from the correction. The real squeeze probability (40%) is far higher than estimated. The lower ceiling ($680) means less distance to travel before breakout. Keep $685/$692 as a breakout play. Or UPGRADE to $680/$687 for a higher-probability, higher-cost version that sits right at the real ceiling.

---

### W2-10: Gamma Flip Play -- Buy $678P / Sell $665P

**GEX Levels Used:** Long put at $678 (est. gamma flip), short put at $665 (est. gamma floor)

**What Was Wrong:**
- THE ENTIRE THESIS IS BUILT ON $678 BEING THE GAMMA FLIP. It is not. Real gamma flip is $656.
- The agent wrote: "SPY $678 is the gamma flip... THE TRAPDOOR. Break below this and dealer hedging reverses from dampening to amplifying." FALSE. The trapdoor is at $656.
- The agent wrote: "Below $678, net GEX is negative." FALSE. Net GEX is POSITIVE from $678 all the way down to $656.
- The "GEX Mechanics: The Play-by-Play" section describing Phases 1-4 of dealer selling cascade is entirely fictional at these price levels. Dealers are LONG gamma from $678 to $656 and will BUY on dips, not sell.
- The "asymmetry" argument (downside amplified, upside dampened) is INVERTED at $678. At $678, the upside is dampened AND the downside is dampened. There is NO asymmetry until $656.
- The short strike at $665 was justified as "gamma floor, maximum dealer buying support." Real gamma floor is $650. There is no special support at $665.
- The "trapdoor zone" ($678-$665) does not exist. The real trapdoor zone is $656-$650.

**What Should Change:**
- Corrected spread: Buy $656P / Sell $650P ($6 wide) -- real gamma flip to real gamma floor
- This is the ACTUAL "trapdoor" trade: long put at the regime change boundary, short put at the support floor
- Problem: $656 is $20 OTM from current spot. The $656P costs very little (~$1.00-1.50 at 8 DTE) but has low probability of going ITM
- The corrected trade is fundamentally different: a cheap OTM lottery ticket instead of an ATM microstructure play

**Does It Still Work?**
NO. The thesis is dead. Every claim in the document about dealer mechanics, GEX amplification, and the "trapdoor" at $678 is wrong. The spread sits entirely in the long-gamma (dampened) regime where dealers are actively resisting the move that the trade needs.

The spread can still profit on pure direction -- SPY drops $5+ and the $678P gains value. But the GEX edge does not exist. You are paying ATM premium ($4.50-5.50) for a microstructure thesis that is invalidated by real data. The $200 risk on a $450-550 debit with a tight stop is burning capital for a directional bet with no structural edge.

**Verdict: KILL**

This is the most damaged position in the entire Wave 2 set. The entire thesis -- every word about the gamma flip, the trapdoor, the dealer cascade, the asymmetry -- is wrong by 22 points. Kill it. The agent should rebuild from scratch using the real gamma flip at $656 as the anchor. The corrected trade (Buy $656P / Sell $650P) is a completely different animal: cheap, deep OTM, low probability, but structurally correct.

---

## SUMMARY SCORECARD

| Position | Strikes Used | Key GEX Error | Impact | Verdict |
|----------|-------------|---------------|--------|---------|
| **W2-01** Borey's Put Spread | $675/$669 | Max pain off by $19 | Moderate -- still directional | **FIX** |
| **W2-02** Bear Call Spread | $685/$692 | Ceiling off by $5 | Low -- accidentally safer | **SURVIVE** |
| **W2-03** CPI Strangle | $675P/$692C | Max pain off by $19 | Moderate -- put leg misplaced | **FIX** |
| **W2-04** Scale-In Ladder | $678P, $675P | Gamma flip off by $22 | FATAL -- thesis premise wrong | **KILL** |
| **W2-05** Diagonal Put | $675/$669 | Max pain off by $19, floor off by $15 | Moderate -- zone mismatch | **FIX** |
| **W2-06** BWB | 675/665/652 | Floor off by $15, body wrong zone | FATAL -- probability model broken | **KILL** |
| **W2-07** Oil Proxy | USO $80C/$86C | None (different underlying) | Zero | **SURVIVE** |
| **W2-08** Crash Convexity | $665/$645 | Floor off by $15 | Moderate -- short leg unsupported | **FIX** |
| **W2-09** Contrarian Bull | $685/$692 | Ceiling off by $5, squeeze 40% not 15% | POSITIVE -- thesis improved | **SURVIVE** |
| **W2-10** Gamma Flip Play | $678/$665 | Flip off by $22, floor off by $15 | FATAL -- entire thesis invalidated | **KILL** |

### Final Count

| Verdict | Count | Positions |
|---------|-------|-----------|
| **SURVIVE** | 3 | W2-02, W2-07, W2-09 |
| **FIX** | 4 | W2-01, W2-03, W2-05, W2-08 |
| **KILL** | 3 | W2-04, W2-06, W2-10 |

---

## CORRECTED STRIKE MAP (For Wave 3 Position Rebuilds)

Based on real CBOE data:

### Approved PUT Strikes (Long)

| Strike | Real GEX Level | Significance |
|--------|---------------|-------------|
| $680 | Gamma ceiling (reversal zone for puts) | 0.9 |
| $660 | Near gap bottom / high OI zone | 0.7 |
| $656 | **Gamma flip + Max pain CONFLUENCE** | **1.0** |
| $650 | **Gamma floor** | 0.85 |

### Approved PUT Strikes (Short)

| Strike | Real GEX Level | Significance |
|--------|---------------|-------------|
| $650 | Gamma floor (real dealer support) | 0.85 |
| $645 | Below floor, acceleration zone | 0.5 |
| $640 | High OI put level | 0.6 |
| $638 | High OI put level | 0.5 |
| $630 | Deep put OI wall | 0.6 |

### Approved CALL Strikes (Short)

| Strike | Real GEX Level | Significance |
|--------|---------------|-------------|
| $680 | **Gamma ceiling (real resistance)** | 0.9 |
| $675 | High OI call level | 0.7 |

### Approved CALL Strikes (Long)

| Strike | Real GEX Level | Significance |
|--------|---------------|-------------|
| $685 | Above ceiling, breakout zone | 0.6 |
| $692 | Far hedge wing | 0.4 |

### Corrected Spread Constructions

| Type | Construction | Width | GEX Logic |
|------|-------------|-------|-----------|
| Bear Put (primary) | Buy $656P / Sell $650P | $6 | Gamma flip to gamma floor |
| Bear Put (wider) | Buy $660P / Sell $650P | $10 | Gap bottom to gamma floor |
| Bear Call (primary) | Sell $680C / Buy $687C | $7 | Real ceiling to hedge wing |
| Crash Convexity | Sell $650P / Buy $630P (ratio) | $20 | Real floor to deep acceleration |
| Bull Hedge | Buy $680C / Sell $687C | $7 | At real ceiling for breakout |
| BWB (corrected) | Buy $660P / Sell 2x $650P / Buy $640P | 10/10 | Body at real floor |

---

## CRITICAL IMPLICATIONS FOR PORTFOLIO CONSTRUCTION

### 1. The "Dampened Regime" Changes Everything

With SPY at $676 and the gamma flip at $656, the current market is in a **dealer-long-gamma regime**. This means:
- Selloffs from $676 to $660 are ORDERLY and RESISTED
- Rallies from $676 to $680 are also RESISTED (dampened both ways)
- The market is effectively "pinned" in the $656-$680 range by dealer hedging
- SELLING PREMIUM (credit spreads, butterflies) is favored over BUYING PREMIUM (debit spreads, straddles) in this regime

### 2. Extreme Fear PCR Means Puts Are Expensive

Volume PCR at 1.337 = extreme fear. Everyone owns puts. Put premiums are inflated by demand. This means:
- Buying puts (W2-01, W2-04, W2-05, W2-10) pays a "fear premium" for protection everyone else already has
- Selling puts at REAL support ($650) collects elevated premium against a level where dealers actually support price
- The bear put spread corrected to Buy $656P / Sell $650P may be cheaper than expected because the $650P premium is elevated by fear

### 3. The 40% Squeeze Probability Is Portfolio-Relevant

The contrarian bull case (W2-09) is MUCH stronger with 40% squeeze probability. The portfolio should potentially INCREASE the hedge allocation and DECREASE the bearish allocation compared to Wave 2 plans.

### 4. Real Max Pain at $656 = Different Expiry Dynamics

Max pain at $656 (not $675) means the "gravitational pull" for April options expiry is toward $656, not $675. This is 20 points below current spot. If max pain gravity is real and strong, SPY drifts DOWN over the next 10 days toward $656 -- but the move is dampened by long-gamma dealers the entire way. Expect a slow grind, not a crash.

---

## RECOMMENDATION

**Do not enter ANY Wave 2 position as-is.** The SURVIVE positions (W2-02, W2-07, W2-09) can proceed with awareness of corrected levels. The FIX positions need corrected strikes before entry. The KILL positions should be rebuilt from scratch using the corrected strike map.

**Priority rebuilds:**
1. W2-01 (Borey's core trade) -- Fix strikes to real GEX levels
2. W2-08 (crash convexity) -- Fix short strike to real gamma floor
3. W2-09 (contrarian bull) -- Already survives, but UPGRADE to real ceiling strike for better entry

**Kill replacements:**
1. W2-04 (scale-in ladder) -- Replace with real gamma flip probe at $656
2. W2-06 (BWB) -- Rebuild with body at $650 (real gamma floor)
3. W2-10 (gamma flip play) -- Rebuild with $656/$650 as the real trapdoor trade

---

*"The GEX engine does not care about your estimates. It cares about the gamma and open interest at each strike as observed in real option chains. When the estimates are wrong by 22 points on the gamma flip, every downstream position built on those estimates is structurally compromised. Run the live data. Trust the math. Rebuild."*
