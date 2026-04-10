# 15 --- Iron Condor (Contrarian Range-Bound Hedge)

**Date drafted:** 2026-04-06
**Drafter role:** Iron condor specialist, contrarian hedge against directional thesis
**Market snapshot:** SPX ~6783 (SPY ~678). Gap up from ~6610 on US-Iran ceasefire Apr 7. VIX ~20. Oil crashed 16% to $94.

---

```
POSITION: SPY Apr 17 $660/$665P --- $690/$695C Iron Condor
Action: Sell 1x SPY $665 Put / Buy 1x SPY $660 Put / Sell 1x SPY $690 Call / Buy 1x SPY $695 Call, Apr 17 expiry
Entry: Monday April 7, 10:00-10:30 AM ET (let opening 30 min establish direction)
Credit received: ~$1.85 total ($1.00 put spread + $0.85 call spread)
Quantity: 1 contract
Max loss: $315 per condor ($5.00 width minus $1.85 credit x 100)
Max profit: $185 per condor (full credit x 100), if SPY closes between $665 and $690 at expiry
Profitable range: SPY $663.15 to $691.85 (short strikes minus/plus credit)
              = SPX ~6631 to ~6918 --- a 287-point window
Probability of profit: ~72-76% (each short strike ~1.3-1.5 standard deviations OTM at 11 DTE)
Take profit: Buy back at $0.92 or less (50% of credit = $93 per condor)
Close if tested: Exit threatened side if SPY touches $666 or $689 intraday
Time stop: Close entire position by Thursday April 15, 2:00 PM ET --- do not hold into final 2 DTE
Invalidation: VIX spikes above 30 (regime shift --- the IC needs calm) or SPY gaps through either short strike overnight
Why THIS trade: The bear thesis is strong --- 31 uncontrollable military branches, Supreme Leader in a coma, no chain of command. But MPW's blue path is 40%. If the gap does NOT fill next week and SPY chops 665-690 while the market digests the ceasefire, this IC harvests theta from both directions. It is the explicit hedge against being wrong about timing.
```

---

## The Contrarian Case: Why the Gap Might NOT Fill This Week

The bear thesis (positions 01-14) assumes the ceasefire collapses quickly. But consider:

1. **Markets can stay irrational longer than you can stay solvent.** The ceasefire is unenforceable, but enforcement failures take time to surface. The 31 military branches do not all defect on day one. The first violation might be a minor skirmish that the media downplays.

2. **PCE and CPI could distract.** If Thursday's PCE comes in cool and Friday's CPI is benign, the market has two positive catalysts to focus on instead of geopolitical risk. Rate cut hopes could override ceasefire skepticism for the full week.

3. **Short covering rally.** The gap up may have triggered a short squeeze in SPX puts. Dealers who were short gamma pre-ceasefire are now long gamma. They pin the market. The path of maximum frustration for directional traders is sideways.

4. **Oil at $94 is a pressure relief valve.** The 16% crash in oil removes the inflation panic that would have forced SPY lower. Without oil-driven stagflation fear, the gap fill needs a new catalyst.

5. **Algos respect levels, humans respect narratives.** The 6610 gap fill level is a human construct. Systematic strategies see a new range forming at 6700-6900 and trade mean reversion within it.

If ANY of these play out, SPY chops 665-690 for the week. The IC profits from exactly this scenario.

---

## Why Apr 17 (Not Apr 11)

The v1 iron condor used Apr 11 (4 DTE). This was the right instinct at the wrong expiry.

1. **Apr 11 forces you to hold through CPI Friday.** CPI is a binary event. A hot CPI print sends SPY below 665 in a single candle. A cool print sends it above 690. With Apr 11 expiry, you are expiring INTO the event. That is not premium selling --- that is coin flipping.

2. **Apr 17 gives 11 DTE.** Theta is gentler (~$0.15-0.18/day net on the condor vs ~$0.30-0.40/day on the Apr 11 version), but you survive PCE, CPI, AND the full following week. The thesis is "range-bound digestion" --- that needs TIME to play out. Four days is not enough for the market to fully digest a ceasefire between the US and Iran.

3. **Apr 17 lets you close before gamma accelerates.** The management rule says exit by Thursday April 15. That leaves 2 full trading days of runway. With Apr 11, you would need to exit by Wednesday April 9 --- before PCE even happens --- making the trade nearly pointless.

4. **Higher credit.** 11 DTE collects more premium than 4 DTE at the same strikes. The extra time value goes into YOUR pocket as the seller.

5. **The 50% profit target is achievable.** With 11 DTE, you can realistically hit 50% profit by Wednesday April 9 if SPY sits in the 672-684 range and vol compresses post-PCE. With 4 DTE, 50% decay takes 3 of 4 days --- you almost never get to close early.

---

## Strike Selection: Why 665/690 (Not Tighter, Not Wider)

### Put Side: $665/$660 (Below the Gap Fill Level)

The gap fill target is SPY ~$661 (SPX ~6610). The short put at $665 sits $4 ABOVE the gap fill level. This is the key design choice:

- **Even if the gap fills, the put side survives.** SPY would need to drop through $661, overshoot the gap fill, and continue to $665 --- and that is just the short strike. Breakeven on the put side is $663.15. SPY would need to crash to $663 for this leg to lose money.
- **The gap fill is support.** If SPY drops to $661, that is where buyers stepped in before the ceasefire. It is a natural bounce zone. Puts at $665 are selling premium below the support shelf.
- **$660 long put caps downside.** If the ceasefire collapse is catastrophic (SPY to $640), the long $660P limits loss to $315 total. You do not care what happens below $660.

### Call Side: $690/$695 (Above the Exhaustion Zone)

SPY gapped from ~$661 to ~$678. The ceasefire rally has already produced an 18-point ($2.6%) move. Historical analogs (Ukraine false ceasefires, Iraq War rallies) show exhaustion at 2.5-3.5% above the pre-event close.

- **$690 is 1.8% above spot ($678).** That would require the rally to extend to a total move of ~4.4% from the pre-ceasefire close. In a market already priced for optimism with oil down 16%, that kind of extension requires a NEW positive catalyst (rate cut signal, trade deal, earnings beat).
- **The ceasefire IS the catalyst. There is no second act.** The market already knows about the ceasefire. There is no incremental surprise to push SPY from 678 to 690 unless CPI comes in dramatically cold. And if CPI is that cold, you close Thursday before the print.
- **Dealer gamma positioning caps the upside.** Market makers hedging the gap-up are long gamma above 680. They sell rallies. The natural ceiling for this week is 685-688 before dealer hedging pushes it back down.

### Why Not Tighter (670/685)?

Short strikes only $8 and $7 from spot. At VIX 20, SPY's implied daily move is ~$7.50. That means a single normal day can test either short strike. You would be closing and rolling constantly. The IC needs breathing room.

### Why Not Wider (660/695)?

Same short strikes but wider wings. The $10-wide version would collect ~$3.20 but risk $6.80 ($680 max loss). That is 6.8% of the account on a probability trade. Unacceptable. The $5-wide keeps max loss at $315.

---

## Pricing Math

With SPY at $678, VIX at ~20, 11 DTE to Apr 17 expiry:

| Leg | Estimated Price | Credit/Debit |
|-----|----------------|--------------|
| Sell SPY Apr 17 $665P | ~$2.15 | +$2.15 |
| Buy SPY Apr 17 $660P | ~$1.15 | -$1.15 |
| **Put spread credit** | | **$1.00** |
| Sell SPY Apr 17 $690C | ~$1.60 | +$1.60 |
| Buy SPY Apr 17 $695C | ~$0.75 | -$0.75 |
| **Call spread credit** | | **$0.85** |
| **Total net credit** | | **$1.85 ($185 per condor)** |

### Greeks at Entry (Net Position)

| Greek | Value | What It Means |
|-------|-------|---------------|
| Delta | ~+0.02 | Nearly neutral. IC does not care about direction. |
| Theta | ~+$0.15/day | You collect ~$15/day in time decay while SPY stays in range. |
| Vega | ~-$0.08/pt | Each 1-point VIX drop earns ~$8. Vol compression helps. Post-PCE crush is a tailwind. |
| Gamma | ~-$0.01 | Small and manageable at 11 DTE. Grows dangerous below 3 DTE. |

### P&L at Expiry by SPY Price

| SPY at Expiry | P&L per Condor | Notes |
|---------------|----------------|-------|
| Below $660 | -$315 (max loss) | Put side fully breached. Long $660P saves you. |
| $660.00 | -$315 | Short put max loss. |
| $663.15 | $0 (breakeven) | Put-side breakeven. |
| $665.00 | +$185 (max profit) | Put short strike. Premium fully decayed. |
| $670-685 | +$185 (max profit) | Sweet spot. Full credit retained. |
| $690.00 | +$185 (max profit) | Call short strike. Premium fully decayed. |
| $691.85 | $0 (breakeven) | Call-side breakeven. |
| $695.00 | -$315 (max loss) | Call side fully breached. |
| Above $695 | -$315 (max loss) | Long $695C saves you. |

**Profitable range: $663.15 to $691.85 = $28.70 wide.** SPY would need to move 2.2% in either direction from $678 to exit the profitable zone. At VIX 20, the 11-day implied move is approximately $678 x 0.20 x sqrt(11/365) = $23.50 (1 standard deviation). The profitable range is 1.22 standard deviations wide on each side. Probability of staying inside: ~72-76%.

---

## Management Rules

### Rule 1: Close at 50% Profit ($0.92 or Less)

If the iron condor can be bought back for $0.92 or less ($93 per contract), close the entire position. This is the PRIMARY exit. Do not get greedy chasing the last $0.93 of credit.

**When this typically happens:** If SPY stays in the 670-685 range and VIX drifts from 20 to 17-18 post-PCE, the condor could hit 50% by Wednesday April 9 or Thursday April 10. The combination of theta decay and vol compression accelerates the P&L in the favorable scenario.

**Why 50%:** Empirical data from tastytrade research shows that closing iron condors at 50% of max profit captures 80% of the expected value while eliminating 90% of the tail risk. The last 50% of profit takes 70% of the remaining time and carries all the gamma risk.

### Rule 2: Close if Tested (SPY Touches $666 or $689)

If SPY touches $666 intraday, close the put spread immediately (buy back the 665P/660P spread). Keep the call spread open --- it is now a standalone bear call credit spread.

If SPY touches $689 intraday, close the call spread immediately (buy back the 690C/695C spread). Keep the put spread open --- it is now a standalone bull put credit spread.

**Do not wait for a close at that level.** By the time SPY closes at $666, it may have already blown through to $662 intraday and your max loss on the put side is locked in.

**Why $666/$689 (not the short strikes themselves):** The short strikes are at $665/$690. But a $1 buffer gives you time to execute the closing order before the short leg goes in-the-money. Options prices move fast near ATM --- waiting until SPY hits exactly $665 means the spread is already deep in trouble.

### Rule 3: Time Stop --- Close by Thursday April 15, 2:00 PM ET

With Apr 17 expiry, Thursday April 15 leaves 2 DTE. Do not hold past this point. Reasons:

- Gamma explodes in the final 2 days. A $3 SPY move that cost $0.40 in P&L at 11 DTE costs $1.50+ at 2 DTE.
- Any surprise news (Iran escalation, emergency Fed action, earnings shock) on Thursday evening or Friday morning can gap SPY through a short strike with no time to react.
- The theta you collect in the final 2 days (~$0.30-0.40) is not worth the gamma risk you absorb.

If the position is profitable at Thursday 2 PM, close it. If it is at breakeven, close it. If it is slightly underwater, close it and take the small loss. The only exception: both short strikes are more than $10 away from spot (SPY below $680 and above $655). In that extremely favorable case, you can hold into Friday morning --- but close by 11 AM Friday regardless.

### Rule 4: Never Adjust by Widening or Rolling

If one side is tested and you close it (per Rule 2), do NOT:
- Sell additional premium on the other side to "make up" for the loss
- Roll the tested side to a further expiry
- Add a second iron condor to "average" the credit

These are ways traders turn small defined losses into large undefined losses. Accept the partial loss. The surviving side will offset some of it.

### Rule 5: VIX Regime Check

If VIX spikes above 28 at any point while you hold this position, close the entire condor immediately regardless of P&L. A VIX above 28 means implied daily moves of $10+ in SPY. Your profitable range of $28.70 can be breached in 2-3 trading days. The IC needs calm, digestion, range-bound action. A VIX spike means the market has shifted from digestion to panic. Exit.

Conversely, if VIX drops below 14, your position is likely already at 60-70% profit from vol compression alone. Close it and take the win.

---

## How This Hedges the Directional Trades

The IC is not a standalone alpha generator. Its expected value is modest: (0.74 x $185) - (0.26 x $315) = $136.90 - $81.90 = +$55 per trade. That is ~$55 profit on $315 risked --- a 17% return on risk with 74% probability. Respectable but not exciting.

The real value is PORTFOLIO LEVEL hedging:

| Scenario | Position 01 (Aggressive Put) | This IC (#15) | Combined |
|----------|-------------------------------|---------------|----------|
| Gap fills to $661 | +$660 | +$185 (inside range) | +$845 |
| Gap fills to $655 (overshoot) | +$1,060 | -$120 (put side stressed but not max loss) | +$940 |
| Ceasefire holds, SPY chops 670-685 | -$200 (stop) | +$185 (sweet spot) | -$15 |
| Ceasefire rally extends to $692 | -$200 (stop) | -$100 (call side tested, close early) | -$300 |
| Ceasefire rally to $700+ | -$200 (stop) | -$315 (max loss) | -$515 |
| Slow grind nowhere, SPY 675-680 | -$200 (stop/time stop) | +$185 (perfect outcome) | -$15 |

**The critical row is "ceasefire holds, SPY chops."** Without the IC, a failed bear thesis costs $200. With it, the net cost is $15. The IC turns a losing week into a scratch.

---

## What Could Go Wrong

1. **CPI blows through a short strike.** If Friday April 10 CPI prints hot, SPY could gap below $665 Monday morning. The put side hits max loss immediately. Mitigation: the time stop at Thursday April 15 means you close BEFORE any late-week CPI reaction fully materializes. But the Apr 10 CPI is only 3 DTE after entry --- you ARE holding through this event. If you cannot tolerate that, do not enter until AFTER CPI (Friday afternoon April 10) and accept the lower credit.

2. **Ceasefire collapse is immediate and violent.** A Houthi missile hits a carrier Monday morning. SPY gaps down 3% to $658. The put side hits max loss ($315). This is the defined risk --- the long $660P protects you. But $315 loss on a $10K account is 3.15%, which exceeds the 2% rule. Mitigation: accept 3.15% risk on this single trade because the probability of max loss is under 15%. Alternatively, see sizing note below.

3. **Whipsaw.** SPY drops to $666 (you close the put side at a loss per Rule 2), then reverses to $688 (you close the call side at a loss per Rule 2). You lose on both sides despite the final price being in range. This is the IC's worst failure mode. Mitigation: the closing triggers are at $666/$689, not $665/$690. The $1 buffer reduces false triggers. Also, closing one side and keeping the other means you recoup part of the loss on the surviving side.

4. **Low volatility entry.** If VIX drops to 16-17 before you enter Monday, the credit shrinks from ~$1.85 to ~$1.20. At $1.20 credit, max loss is $3.80 ($380) and the risk/reward is terrible. **Do not enter if total credit is below $1.50.** The trade needs VIX 18+ to justify the risk.

---

## Sizing for Strict 2% Risk

One $5-wide iron condor at $1.85 credit has $315 max loss (3.15% of $10K). To comply with 2% ($200 max loss):

**Option A: Accept 3.15%.** The probability of hitting max loss is ~13%. Expected loss from the max-loss scenario is 0.13 x $315 = $41. This is rational risk management even if it exceeds the nominal 2% rule. Use this if the IC is your ONLY open position.

**Option B: Narrow to $3 wide.** Trade $662/$665P --- $690/$693C. Estimated credit: ~$1.10. Max loss: $1.90 x 100 = $190. Fits under 2%. Downside: the narrower wings give less protection and worse fills (less liquid strikes). Not recommended.

**Option C: Close early.** Enter the $5-wide at $1.85, but set a hard stop-loss at $200 unrealized loss on the position. This means closing when the condor value reaches ~$3.85 ($1.85 credit + $2.00 loss). This is tighter than max loss but enforces the 2% rule. Risk: the stop could trigger on a temporary intraday move and you lose the position before it recovers.

**Recommendation: Option A.** One contract, $315 max risk, accept the 3.15%. The IC is a hedge, not a core position. Hedge sizing can be slightly larger than directional sizing because the probability of full loss is structurally lower.

---

## Entry Protocol

1. **Pre-market check (8:00-9:30 AM ET Monday April 7):**
   - SPY pre-market between $673 and $684: proceed.
   - SPY pre-market above $685: call side is threatened. Stand down or widen call strike to $695/$700.
   - SPY pre-market below $670: put side is threatened. Stand down or widen put strike to $658/$663.
   - VIX futures at 18-23: proceed. Below 16: do not enter (insufficient premium). Above 28: do not enter (regime too volatile for IC).

2. **Entry (10:00-10:30 AM ET):**
   - Place the 4-leg iron condor as a SINGLE order. Do not leg in.
   - Limit order at $1.85 credit (mid-price). Wait 5-10 minutes.
   - Walk down to $1.70 in $0.05 increments if not filled. Do not accept below $1.50.
   - SPY bid-ask spreads on each leg are ~$0.02-0.04. Total slippage: $0.08-0.16. Budget $0.15 slippage.

3. **Immediately after fill:**
   - Set GTC buy-to-close order at $0.92 (50% profit target).
   - Set price alerts: SPY $666 (put side danger) and SPY $689 (call side danger).
   - Set calendar reminder: Thursday April 15, 2:00 PM ET --- mandatory position review.

---

## Summary for Borey

This is the "what if I'm wrong?" trade. Every other position in the book bets that the ceasefire fails and the gap fills. This IC profits from the opposite: SPY goes nowhere for a week while the market argues about whether the ceasefire is real. You collect $185 in premium and keep it as long as SPY stays between $663 and $692 --- a 29-point range that encompasses the gap fill level on the downside and the rally exhaustion on the upside.

Risk is $315. Probability of keeping the full credit is ~74%. Expected value is +$55 per trade. The real payoff is portfolio-level: if the aggressive put (position 01) loses $200 because the gap fill takes longer than expected, this IC makes $185 back. Net loss: $15 instead of $200. That is the difference between a trader and a gambler --- the gambler goes all-in on one direction, the trader hedges the timing risk.

One contract. Four legs. Defined risk. Close at 50% or if tested. Do not hold past Thursday April 15. This is the boring trade that makes the exciting trades survivable.
