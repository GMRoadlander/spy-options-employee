# Iron Condor — SPX Range-Bound Theta Harvest

**Date drafted:** 2026-04-06
**Market context:** SPX ~6783 after gap up from ~6610 on US-Iran ceasefire news. VIX ~20. PCE Thursday 4/9, CPI Friday 4/10. Competing theses: gap fill down to ~6610 (bearish) vs. ceasefire rally continuation (bullish). If NEITHER extreme plays out and SPY chops between 665-685 for the week, a premium-selling strategy captures theta from both sides.

---

## POSITION: SPY Apr 11 660/665P — 690/695C Iron Condor

- **Action:** Sell SPY 665 Put / Buy SPY 660 Put / Sell SPY 690 Call / Buy SPY 695 Call, all Apr 11 expiry (Friday weekly)
- **Entry:** Monday 2026-04-07, 10:00-10:30 ET. Let the opening 30 minutes establish direction. Ideally enter when IV is still elevated — if VIX is holding above 19, fill all four legs simultaneously as a single iron condor order. Do NOT leg in separately.
- **Credit received:** $1.65 total ($0.85 from the put spread + $0.80 from the call spread). SPY ~678, 4 DTE, VIX ~20. The 665P is ~1.9% OTM and the 690C is ~1.8% OTM — roughly symmetric wings. With 20 IV implying ~1.1% daily moves, these strikes sit just outside 1 standard deviation for the week.
- **Max loss:** $3.35 per spread ($5.00 width minus $1.65 credit) x 100 = $335 per iron condor
- **Max profit:** $1.65 x 100 = $165 per iron condor, if SPY closes between 665 and 690 at Apr 11 expiry
- **Profitable range:** SPY between $663.35 and $691.65 (short strikes minus/plus credit received). That is SPX ~6630 to ~6916 — a massive 286-point window.
- **Probability of profit:** ~68-72%. Each short strike is roughly 1.1-1.2 standard deviations OTM. The combined probability of SPY staying inside both short strikes is approximately 70%. The breakeven range is even wider.
- **Quantity:** 6 contracts. 6 x $335 max loss = $2,010 total risk. On a $10,000 account at 2% risk ($200), this is oversized. **Adjusted: 1 contract at $335 max risk = 3.35% of account. Acceptable only if this is the sole open position. For strict 2% risk, see note below.**
- **Strict 2% sizing:** There is no way to get max loss below $200 on a $5-wide iron condor collecting $1.65. One contract risks $335. To stay within 2%, either: (a) accept 3.35% risk on this single trade, (b) narrow to a $3-wide condor (660/663P, 690/693C) collecting ~$0.95 with $205 max loss, or (c) trade SPX micro options if available. **Recommendation: trade 1 contract of the $5-wide and accept $335 max risk (3.35%). The probability of hitting max loss is under 15%.**
- **Entry price estimate breakdown:**
  - Sell 665P: ~$1.55
  - Buy 660P: ~$0.70
  - Put spread credit: $0.85
  - Sell 690C: ~$1.40
  - Buy 695C: ~$0.60
  - Call spread credit: $0.80
  - **Total net credit: $1.65 ($165 per contract)**

---

## Management Rules

- **Close at 50% profit:** If the iron condor can be bought back for $0.82 or less ($83 per contract), close the entire position. This is the primary exit. On a 4 DTE trade, this could happen as early as Wednesday if SPY stays in the 670-682 range. Do NOT get greedy chasing the last 50%.
- **Close if tested:** If SPY touches 666 or 689 intraday, close the threatened side immediately. Do not wait for a close at that level. The risk/reward flips against you fast once a short strike is approached with 2-3 DTE remaining.
- **Roll or close by Thursday 2:00 PM ET:** Do not hold into CPI Friday (Apr 10) with full position. CPI is a binary event that can blow through either short strike. If the position is profitable by Thursday afternoon, close it. If it is at breakeven, close it. Only hold into Friday if you are already at 40%+ profit and both short strikes are more than $8 away from spot.
- **Never adjust by widening:** If one side is losing, do NOT sell more premium to "fix" it. Close the losing side and accept the partial loss. The winning side will partially offset.
- **Gamma risk warning:** On Thursday and Friday, gamma accelerates. A $3 SPY move that would have cost you $0.40 on Monday could cost $1.20 on Friday. Get small or get out by Thursday.

---

## Why an Iron Condor Here

1. **VIX at 20 means elevated premium.** Average VIX is ~16-17. At 20, you are selling roughly 20% more premium than normal. Iron condors are premium-selling strategies — they want fat IV. This is the right environment.
2. **Competing theses cancel out.** Gap fill thesis says down. Ceasefire thesis says up. When two credible narratives collide, the most likely outcome is chop. The market often resolves binary debates by going sideways and frustrating both sides. The iron condor profits from exactly this.
3. **Hedges directional uncertainty.** Position 01 (aggressive put) bets on the gap fill. This iron condor is the anti-thesis trade: "what if we are wrong about direction?" If SPY chops between 668-682 all week, the put from position 01 loses $200 but this iron condor makes $165. Combined, net loss is only $35. That is portfolio hedging through strategy diversification.
4. **Defined risk, defined reward.** Max loss is $335 and cannot exceed that under any scenario. Unlike selling naked strangles, the long wings at 660 and 695 cap your downside. You will never get a margin call or an overnight gap that blows up the account.
5. **Theta is your friend.** At 4 DTE, theta decay is aggressive. Each day that passes with SPY inside the range, the condor decays toward zero and your credit becomes profit. You earn roughly $0.30-0.40/day in theta if SPY stays near 678. By Wednesday, the position has already decayed 50-60% and you can close for the target.
6. **Probability is on your side.** A 70% probability of profit trade with a 1:2 risk/reward (risking $335 to make $165) has a positive expected value: (0.70 x $165) - (0.30 x $335) = $115.50 - $100.50 = +$15.00 per trade. Over many repetitions, this is an edge. It is not exciting money, but it is consistent, grindable income.

---

## Risk Notes for Borey

- **CPI Friday is the biggest threat.** A hot CPI print could send SPY below 665 in a single candle. A cool CPI could send it above 690 on rate-cut euphoria. This is why the management rules say to close or reduce by Thursday 2 PM. Do not hold a 4 DTE iron condor into a CPI release at 0 DTE.
- **Ceasefire collapse risk.** If Iran or Houthis escalate before Friday, VIX spikes to 25+ and SPY drops through 665. The iron condor max loss hits on the put side. The long 660P limits damage to $335, but it still stings. This is why you only trade 1 contract.
- **This is NOT a high-conviction trade.** The iron condor is a probability play, not a directional bet. Expected profit is small (~$15 per trade in theory). The real value is as a portfolio hedge against the aggressive put (position 01). Think of this as insurance that pays you if the put thesis is wrong.
- **Slippage on 4-leg orders.** Iron condors have 4 legs and the bid-ask spreads compound. On SPY options, each leg might have a $0.02-0.04 spread. Total slippage could be $0.08-0.16. Use a limit order at the mid-price ($1.65) and be willing to wait 5-10 minutes for a fill. Do not market-order an iron condor.
- **Pin risk at expiration.** If SPY closes near 665 or 690 on Friday, you face assignment risk on the short legs. SPY options are American-style and can be exercised early. Close any leg that is within $0.50 of being in-the-money by Friday morning. Do not let this go to expiration with a short leg near the money.

---

## Alternative Considered and Rejected

**Wider wings (655/665P — 690/700C):** $10-wide spreads collect more credit (~$2.80) but risk $7.20 per spread ($720). Too much risk for a $10k account on a probability play. The $5-wide keeps max loss manageable.

**Narrower short strikes (670/675P — 685/690C):** Closer to ATM, collecting ~$2.50. Higher credit but much higher probability of being breached. With VIX at 20, a $7 move in SPY (1%) is a normal day. Short strikes only $3-7 from spot would be tested constantly. The wider 665/690 shorts give breathing room for daily chop.

**Butterfly instead of condor:** A 665/678/690 iron butterfly collects ~$6.00 credit but requires SPY to pin near 678. Max loss on the wings is much larger (~$7.00 per side). The butterfly is higher reward but lower probability. For a "chop around in a range" thesis, the condor is superior because it profits across the entire range, not just at a single pin.

**Selling a strangle (naked 665P + 690C):** Higher credit (~$2.95) with no wing protection. If SPY gaps through either strike, losses are theoretically unlimited (put side) or very large (call side). On a $10k account, naked short options are irresponsible. The iron condor sacrifices $1.30 of credit for defined risk. That is the right trade-off.
