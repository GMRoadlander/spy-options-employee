# 17 — MPW Strangle (Both Sides, Equal Dollar, Different Strikes)

**Date drafted:** 2026-04-06
**Drafter role:** Volatility event trader, agnostic on direction, high conviction a big move is imminent
**Market snapshot:** SPX ~6783 (SPY ~678). VIX ~20. US-Iran ceasefire unenforceable (31 militaries, coma). PCE Thursday Apr 9. CPI Friday Apr 10. Islamabad talks Saturday Apr 11.
**Method source:** MPW — Bamboo Scroll #218. Buy calls and puts simultaneously with equal dollar amounts at different strikes when a big move is coiled. Direction does not matter. Magnitude does.

---

```
POSITION: SPY Apr 17 Strangle — MPW Event Volatility Play
                                                            
CALL LEG:
  Action: Buy to open 2x SPY Apr 17 $682C
  Entry: Thursday April 10, 10:00-10:30 AM ET (30 min after CPI release settles)
  Cost/Credit: ~$1.80 per contract ($360 total debit)
  
PUT LEG:
  Action: Buy to open 2x SPY Apr 17 $674P
  Entry: Same time — both legs entered together
  Cost/Credit: ~$1.90 per contract ($380 total debit)

Total debit: ~$740 (3.7% of $10K account)
  Call side: $360
  Put side: $380
  Approximately equal dollar allocation per side

Max loss: $740 (both legs expire worthless — SPY sits between $674 and $682 through Apr 17)
Stop loss: EXIT BOTH LEGS if combined value drops to $370 (50% loss = 3.7% of account)
Time stop: Exit both legs Wednesday April 15, 2:00 PM ET
Invalidation: VIX drops below 15 (vol compression kills both legs). Also invalid if SPY is already outside $668-688 range before entry (move already happened, you are late).
```

---

## Why MPW's Method, Not a Straddle

MPW does NOT buy a straddle (same strike). He buys a strangle (different strikes, equal dollars). Here is why that matters:

**Straddle (ATM $678C + $678P):** Each leg costs ~$5.00-5.50 at VIX 20 with 7 DTE. Total cost: ~$1,050-1,100. That is 10%+ of the account for a setup where you need SPY to move $10+ just to break even. You are paying maximum theta and maximum extrinsic premium.

**MPW Strangle ($682C + $674P):** Each leg costs ~$1.80-1.90 (OTM). Total cost: ~$740. You need a bigger move to profit (SPY must breach $682 or $674), but the move you are betting on IS big — ceasefire collapse, CPI shock, or Islamabad failure. You are not paying for the middle of the distribution. You are paying for the tails, which is where the money is when catalysts cluster.

**MPW's example math (Scroll #218):**
- Bought $5,000 worth of SPY 645C at $1.40 + $5,000 worth of SPY 642P at $1.45
- Ceasefire rumor lifted SPX 70 points
- Calls went to $7.25 (5.2x). Puts dropped to $0.40.
- Net: ~$15K profit on ~$10K invested

The key insight: the winning leg does not need to cover the losing leg by a little. In a big move, the winning leg goes 4-7x while the losing leg goes to near zero. **The asymmetry is the edge.**

## Why These Strikes: $682C and $674P

**Call strike $682 (0.6% OTM):**
- Delta ~0.38. Gains ~$0.38 per $1 SPY rises.
- If SPY rallies to $695 (ceasefire extended + CPI cool): $682C goes from $1.80 to ~$13.50. That is a 7.5x return on the call leg.
- Why not deeper OTM ($690+): At VIX 20, $690C costs ~$0.60. Cheap, but delta is ~0.15. You need a $20+ move to get meaningful returns. MPW does not buy lottery tickets — he buys options that move FAST on a $10-15 move.

**Put strike $674 (0.6% OTM):**
- Delta ~-0.35. Gains ~$0.35 per $1 SPY falls.
- If SPY drops to $661 (gap fill on ceasefire collapse): $674P goes from $1.90 to ~$13.50. That is a 7.1x return on the put leg.
- Why not deeper OTM ($665-): Same logic as calls. $665P costs ~$0.70 but needs a $17+ move to become meaningful. The $674P starts working as soon as SPY drops below $674.

**Both strikes are roughly equidistant from spot ($4 above, $4 below).** This is not a straddle pretending to be a strangle — it is genuinely OTM on both sides, paying only for tail moves.

## Entry Timing: Why Friday After CPI (Not Thursday After PCE)

This is the critical decision. MPW's edge is picking the MOMENT when the move is coiled. Three catalysts stack up:

| Catalyst | Date | Likely Impact | Volatility Behavior |
|----------|------|---------------|---------------------|
| PCE (February) | Thu Apr 9, 8:30 AM | Low — stale pre-Hormuz data | Moderate IV crush after release |
| CPI (March) | Fri Apr 10, 8:30 AM | HIGH — first data capturing Hormuz disruption | Major IV crush after release |
| Islamabad talks | Sat Apr 11 | EXPLOSIVE — ceasefire enforcement test | No options market open to price it |

**The optimal entry is Friday April 10 at 10:00 AM, after CPI settles.** Here is the reasoning:

1. **CPI is the vol catalyst that sets the stage.** March CPI is the first data point that captures Hormuz Strait disruption — oil shipment delays, supply chain repricing, energy cost passthrough. If CPI is hot (>0.4% MoM core), the Fed narrative shifts. If CPI is cool, the "ceasefire = disinflation" trade gets confirmed. Either way, CPI is the data that moves. PCE (February, pre-Hormuz) is irrelevant noise.

2. **After CPI, IV crushes on the weekly/near-term options.** The Apr 17 $682C and $674P get cheaper. You are buying AFTER the known event reprices, not before. This is MPW's principle: buy cheap options when the market thinks the event is over, but you know another event is coming.

3. **The REAL catalyst is Saturday's Islamabad talks.** This is the explosive event that the options market CANNOT price efficiently on Friday afternoon. Think about it:
   - Friday after CPI, market makers collapse IV because the "known" event just passed.
   - Weekend theta is already priced in (market makers charge for 2 days of decay on Friday).
   - But they are NOT charging enough for the Islamabad talks because diplomatic events have no reliable pricing model.
   - You are buying Friday afternoon options that are priced for "nothing happens over the weekend" when something WILL happen.

4. **If Islamabad talks fail Saturday (most likely outcome given 31 competing militaries and a comatose Supreme Leader):**
   - Sunday night futures open down 2-3% (SPY equivalent drop from $678 to $658-664).
   - Monday morning, your $674P opens at $10-16 instead of $1.90.
   - Your $682C drops to $0.10-0.20 (total loss on call leg: ~$360).
   - Net position: ~$1,600-2,800 profit on $740 invested.

5. **If a commander violates the ceasefire before Saturday:**
   - This could happen Thursday night or Friday.
   - If it happens before your entry, SPY is already dropping — do not chase. Thesis is intact but the trade is gone.
   - If it happens after your Friday entry, same outcome as Islamabad failure — puts explode.

6. **If ceasefire holds AND CPI is cool:**
   - "Risk on" rally. SPY pushes to $690-695 on Monday.
   - Your $682C opens at $8-13 instead of $1.80.
   - Your $674P drops to $0.10-0.15 (total loss on put leg: ~$380).
   - Net position: ~$1,200-2,200 profit on $740 invested.

**The point: you profit on EITHER a big move up OR a big move down.** The only losing scenario is SPY sitting in the $674-682 range through April 17. Given the catalyst stack (CPI + Islamabad + ceasefire instability), a range-bound outcome for 7 straight days is the LEAST likely scenario.

## Pricing Math

With SPY at $678, VIX at ~18-19 (post-CPI crush from 20), 7 DTE remaining on Apr 17:

### Call Leg: 2x SPY Apr 17 $682C

| Input | Value |
|-------|-------|
| Spot | $678 |
| Strike | $682 |
| IV | ~18% (post-CPI crush) |
| DTE | 7 |
| Delta | ~0.38 |
| Theta | ~-$0.22/day |
| Vega | ~$0.10 per 1pt IV |
| Estimated price | $1.70-1.90 (using $1.80) |
| 2 contracts cost | $360 |

### Put Leg: 2x SPY Apr 17 $674P

| Input | Value |
|-------|-------|
| Spot | $678 |
| Strike | $674 |
| IV | ~19% (put skew adds ~1pt) |
| DTE | 7 |
| Delta | ~-0.35 |
| Theta | ~-$0.24/day |
| Vega | ~$0.10 per 1pt IV |
| Estimated price | $1.80-2.00 (using $1.90) |
| 2 contracts cost | $380 |

### Scenario: Islamabad Fails, Ceasefire Collapses (SPY to $661 Monday Open)

| Leg | Entry | Exit | Per Contract | 2 Contracts |
|-----|-------|------|-------------|-------------|
| $674P | $1.90 | ~$13.50 | +$11.60 | +$2,320 |
| $682C | $1.80 | ~$0.15 | -$1.65 | -$330 |
| **Net** | | | | **+$1,990 (269% return on $740)** |

VIX spike from 19 to 30+ adds another $1.00-2.00 to the put via vega. Realistic net: **+$2,200-2,600.**

### Scenario: Ceasefire Holds + Cool CPI (SPY to $693 Monday Open)

| Leg | Entry | Exit | Per Contract | 2 Contracts |
|-----|-------|------|-------------|-------------|
| $682C | $1.80 | ~$11.50 | +$9.70 | +$1,940 |
| $674P | $1.90 | ~$0.15 | -$1.75 | -$350 |
| **Net** | | | | **+$1,590 (215% return on $740)** |

### Scenario: SPY Chops in $674-682 Range (Worst Case)

| Leg | Entry | Exit (Wed Apr 15) | Per Contract | 2 Contracts |
|-----|-------|-------------------|-------------|-------------|
| $682C | $1.80 | ~$0.50 | -$1.30 | -$260 |
| $674P | $1.90 | ~$0.55 | -$1.35 | -$270 |
| **Net** | | | | **-$530 (72% loss on $740, 5.3% of account)** |

Note: the 50% stop at $370 combined value limits this to **-$370 (3.7% of account)** if you honor the stop. The time stop at Wednesday catches it if theta grinds both sides slowly.

## The Catalyst Ranking

From most to least likely to produce the explosive move MPW's method requires:

**1. Islamabad talks failure (Saturday Apr 11) — 65% probability**
31 separate military branches, no unified command, Supreme Leader in a coma. The talks are theater. A "framework agreement" means nothing when any single IRGC Quds Force commander, Basij militia leader, or Navy admiral can violate it independently. When the talks fail or produce a toothless communique, Sunday night futures will price in the collapse. This is the HIGHEST probability catalyst because it has a specific time (Saturday) and the structural dynamics make failure near-certain.

**2. Commander violates ceasefire (any time this week) — 50% probability**
Does not require Islamabad to fail first. With 31 competing military factions, the probability that ALL of them honor a ceasefire for 7+ days is extremely low. One drone, one mine, one missile at a tanker in the Strait. Oil spikes $10-15 in minutes. SPX drops 100+ points. This could happen before your Friday entry (in which case you do not enter) or after (in which case your puts explode).

**3. CPI shock (Friday Apr 10, 8:30 AM) — 30% probability**
March CPI captures Hormuz disruption. If core CPI prints 0.5%+ MoM, the "Fed is done hiking" narrative reverses instantly. SPX drops 50-80 points on a hot CPI. Your puts were entered after the number, so this only helps if the number is VERY hot and the selling continues into the afternoon. Alternatively, a very cool CPI (0.1% MoM) confirms the "ceasefire = disinflation" thesis and SPX rallies 40-60 points — your calls benefit.

**4. Oil supply disruption news (any time) — 25% probability**
800+ ships still in the Strait area. Insurance companies refusing to cover tankers. One incident — even a near-miss — sends oil up $5-10 and equity markets down. This is the "random" catalyst that is not random at all given the military dynamics.

## Risk Management Rules (MPW-Adapted)

1. **Enter both legs simultaneously.** This is not "buy calls now, add puts later." The whole point is equal dollar exposure to both directions at the same moment. If you stagger, you are making a directional bet, which is a different trade.

2. **50% combined stop: exit BOTH legs if combined value drops to $370.** This happens if SPY sits near $678 and theta grinds both sides. At $370 combined, you have lost $370 (3.7% of account). Do not hold and hope. The thesis was "big move soon" — if it has not happened in 3 days, the thesis is wrong for this expiry.

3. **Take profit on the WINNING leg when it hits 5x.** MPW's example: calls went to $7.25 (5.2x from $1.40). At 5x, the winning leg has $900 per contract in profit. Take it. Do not hold for 10x. The losing leg is already near zero — sell it for whatever you can get ($0.10-0.20).

4. **If the move happens Sunday night (futures gap):** Your entry price is locked from Friday. Monday morning at 9:30 AM, place a limit sell on the winning leg at 5x your entry. Place a market sell on the losing leg. Do not wait for "more." Gaps get bought/sold, and the winning leg will shed value fast after the initial gap.

5. **Time stop: Wednesday April 15, 2:00 PM ET.** With 2 DTE remaining, both legs are in theta death spiral. Whatever they are worth on Wednesday afternoon, take it. This is NOT a position to hold into expiration.

6. **Do NOT roll.** If the trade does not work by Wednesday, the catalyst thesis was wrong or the timing was off. Rolling to a later expiry is a new trade with new thesis requirements. Treat it as such. Close this one, reassess, and decide with fresh eyes.

7. **If one leg hits 3x before the weekend:** Consider selling HALF of that leg (1 contract) to lock in profit, let the other contract ride. This guarantees you recovered most of the losing side's cost even if the move reverses.

## Why This Is Different From Position #01 (Aggressive Put)

| Factor | #01 Aggressive Put | #17 MPW Strangle |
|--------|-------------------|------------------|
| Thesis | Ceasefire collapses (directional) | Something big happens (non-directional) |
| Risk if wrong direction | Full loss ($200 stop) | Partial loss (winning leg partially offsets losing leg) |
| Risk if nothing happens | $200 stop loss | $370 stop loss (higher because 2 legs) |
| Profit if ceasefire collapses | ~$660 (194%) | ~$1,990-2,600 (269-351%) on 2 contracts |
| Profit if ceasefire HOLDS and market rallies | $0 (total loss, puts worthless) | ~$1,590 (215%) — CALLS WIN |
| Capital deployed | $340 (3.4%) | $740 (7.4%) |
| Complexity | 1 order | 2 orders, manage both legs |

**The MPW strangle is the better trade if you believe a big move is coming but are not certain of direction.** The ceasefire Intel says collapse is more likely, but MPW's insight is that you do not NEED to be right on direction when the catalyst guarantees magnitude.

## Specific Entry Protocol

1. **Friday April 10, 8:30 AM ET:** CPI releases. Watch the number. Do not act.
2. **8:30-10:00 AM:** Let the CPI reaction play out. Market will whipsaw for 60-90 minutes.
3. **10:00-10:30 AM:** IV has settled post-CPI. Place limit buys for both legs simultaneously:
   - 2x SPY Apr 17 $682C — limit $1.80 (walk to $2.00 max)
   - 2x SPY Apr 17 $674P — limit $1.90 (walk to $2.10 max)
4. **If total fill cost exceeds $820:** Reduce to 1 contract per leg (max $410 total). The 7.4% account risk cap is a hard ceiling.
5. **If SPY is already outside $668-688:** Do not enter. The big move already happened. You are late.
6. **If VIX is above 25:** Options are expensive. Reduce to 1 contract per leg. If VIX is above 30, do not enter — you are buying after the vol spike, not before.
7. **If VIX is below 16:** Do not enter. Market is complacent and options are cheap for a reason — no one expects a move. Your thesis requires catalysts that the market is not pricing. A VIX below 16 means the market IS pricing them and has decided they do not matter.
8. **Both legs must fill.** If only one side fills after 30 minutes, cancel the unfilled leg and sell the filled leg. A one-legged strangle is a directional bet, which is not this trade.

## What MPW Would Say

From Bamboo Scroll #218: "When the move is coming but you do not know which way, buy both. Equal dollars. Let the market decide which side pays you. The losing side goes to near zero but you already know that going in — it is the cost of admission. The winning side pays for everything and then some."

The key MPW principle at work: **options are cheap before the market realizes a catalyst is real.** Friday afternoon, post-CPI, the market thinks the event calendar is clear until next week's data. It is not pricing Islamabad. It is not pricing commander defections. It is not pricing the 800 ships. You are buying vol that is cheap relative to what is actually about to happen.

---

## Summary for Borey

Two contracts each side, $740 total. You are betting that SPY does NOT stay between $674-682 for the next 7 days. Given CPI Friday, Islamabad Saturday, and an unenforceable ceasefire held together by a comatose Supreme Leader and 31 competing militaries — a range-bound market is the least likely outcome.

If SPY drops big: puts pay 7x, calls go to zero. Net ~$2,000+.
If SPY rallies big: calls pay 6x, puts go to zero. Net ~$1,600+.
If SPY chops: both legs bleed. Stop loss caps damage at $370 (3.7% of account).

MPW's edge: you do not need to guess direction. You just need to be right that something is about to happen. The catalyst stack says it will.
