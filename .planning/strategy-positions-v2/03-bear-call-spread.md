# Position 03: Bear Call Credit Spread — Ceasefire Exhaustion Fade

**Date drafted:** 2026-04-06 (Sunday)
**Underlying:** SPY (proxy for SPX ~6783)
**Market:** SPX ~6783 (SPY ~678). Gap-up from ~6610 on US-Iran ceasefire. VIX ~20. Oil $94.
**Account:** $10,000 | **Risk budget:** 2% = $200

---

## Thesis

The ceasefire is structurally unenforceable. Iran has 31 separate armed services answering only to the Supreme Leader, who is in a coma. No single authority exists to order all branches to stand down. The market gapped from SPY ~661 to ~678 on headline momentum alone.

This is not a peace deal. It is a press release. The gap will fill.

Even if the gap does NOT fill immediately, ceasefire hopium has inflated call premiums. VIX at 20 (vs. average ~16-17) means we are selling roughly 20% more premium than normal. Call skew is elevated because the market is pricing continued upside that the geopolitical reality cannot support. We sell that optimism and let time do the work.

**We don't need to predict direction. We need SPY to stay below our short strike.**

---

## POSITION: SPY Apr 17 $683 / $688 Bear Call Credit Spread

| Field | Detail |
|---|---|
| **Action** | **SELL** SPY Apr 17 $683 Call / **BUY** SPY Apr 17 $688 Call |
| **Spread width** | $5.00 |
| **Entry** | **Thursday Apr 9, 10:00-10:30 AM ET** (after PCE release settles — see Entry Timing) |
| **Estimated credit** | ~$1.10 per spread ($110 per contract) |
| **Quantity** | **1 contract** |
| **Total credit** | $110 |
| **Max loss** | **$390** = ($5.00 - $1.10) x 100 = $3.90 x 100 |
| **Max profit** | **$110** = full credit received |
| **Breakeven** | SPY at **$684.10** (short strike + credit) |
| **Prob of profit** | ~72-76% (short strike delta ~0.24-0.28) |
| **Days to expiry** | 8 calendar days / 6 trading days at entry |
| **Theta per day** | ~$0.12-0.16 per spread at entry (~$12-16/day) |
| **Reward:Risk** | 1:3.5 (compensated by ~74% probability of profit) |

---

## Entry Timing: Why Thursday After PCE, Not Monday

The swarm consensus and premium seller logic both point to the same conclusion: do NOT enter Monday.

1. **Monday is the worst day to sell calls after a gap-up weekend.** Opening imbalances, short-covering cascades, and FOMO buyers artificially inflate call premiums in the wrong direction — they push the underlying UP, not call IV up. You want elevated IV, not elevated SPY.
2. **Tuesday-Wednesday are still digesting.** The ceasefire narrative needs 2-3 sessions to get priced in. Early-week call buying from retail will keep SPY buoyant and your short strike uncomfortably close.
3. **PCE Thursday (Apr 9) is the catalyst.** Enter AFTER the PCE number drops at 8:30 AM ET. By 10:00-10:30 AM, the initial reaction has played out but residual IV from the data release is still in the chain. You are selling into post-catalyst elevated premium.
4. **Any PCE outcome helps us:**
   - Hot PCE = SPY sells off. Your short strike gets further OTM. Enter at even better credit.
   - Cool PCE = relief rally, but ceasefire premium was already priced in. IV settles. You still sell at a decent credit because CPI is still the next day.
   - In-line PCE = non-event. Market chops. Enter as planned.
5. **CPI Friday (Apr 10) is still ahead.** By entering Thursday, you have CPI as a free gamma event that is more likely to push SPY down (hot CPI) than up through $683.

**Abort conditions:**
- If SPY is above $682 at 10:00 AM Thursday, wait until it pulls back below $681 or stand aside entirely.
- If VIX has collapsed below 17, the premium is not worth the risk. Find a different trade.

---

## Strike Justification

### Short strike: $683 — The Exhaustion Ceiling

This is NOT a Fibonacci level. This is where the rally actually runs out of gas.

1. **MPW (Market Pressure Waves) identifies exhaustion at SPX 6775-6800.** SPY $678-$680 is the equivalent zone. The $683 strike sits $3-5 above the exhaustion zone — we are selling calls where the market has already shown it cannot sustain momentum.
2. **The gap-up intraday high.** When SPY gapped from ~661 to ~678, the intraday high of the gap session likely printed between $680-$683. That high becomes immediate resistance. Buyers who chased the gap are underwater if SPY revisits that level and will sell into it.
3. **Round-number psychology at $680.** SPY $680 (SPX 6800) is a massive psychological level. Sellers cluster at round numbers. The $683 short strike gives us $3 of cushion above $680 — SPY has to punch through the round number AND hold above it before we are even at our short strike.
4. **Delta ~0.24-0.28.** There is a 72-76% probability SPY closes below $683 at expiration. That is our statistical edge. We are selling a zone that SPY reaches less than 1 in 4 times.
5. **The gap itself is gravity.** Gaps of this magnitude (2.5%+) in SPX/SPY fill >70% of the time within 5-10 trading days. If the gap is pulling SPY DOWN toward $661, it is not simultaneously rallying to $683.

### Long strike: $688 — The Catastrophe Hedge

1. **$5 wide spread.** Wider than a $3 spread to collect more absolute credit ($1.10 vs. ~$0.65 on a $3-wide). The additional width costs ~$0.20 in long call premium but adds $0.45 in short call premium. Net improvement: ~$0.25 more credit.
2. **$688 is absurd territory.** SPY at $688 means SPX at ~6880 — a further 1.5% rally from already-overextended levels, THROUGH PCE data, CPI data, and into a structurally unenforceable ceasefire. The long call exists purely to cap max loss. We never expect to need it.
3. **Max loss of $390 is tolerable for 1 contract.** The stop-loss rule (below) limits realized loss to ~$220 — within the 2% budget.

### Why NOT wider?
- A $10 wide spread collects ~$1.40 but risks $860. One contract blows 8.6% of the account. Too much.

### Why NOT narrower ($3 wide)?
- A $3 wide (683/686) collects only ~$0.65. After commissions, the profit target is barely $30. Not worth the mental energy and monitoring cost. The $5 wide is the sweet spot: enough credit to justify the trade, tight enough to control risk.

---

## Management Rules

### Primary exit: Close at 50% of max profit

- When the spread can be bought back for **$0.55 or less**, close the position.
- This locks in ~$55 profit and eliminates all remaining risk.
- **Expected timeline:** 3-4 trading days if SPY stays below $680 or pulls back.
- **Why 50% and not more?** The last 50% of a credit spread's profit carries disproportionate gamma risk. You are earning pennies while risking dollars. Take the money and redeploy.

### Stop loss: 2x credit received (HARD RULE)

- If the spread value rises to **$2.20** (from $1.10 entry), close immediately.
- Realized loss = $2.20 - $1.10 = $1.10 per spread = **$110 loss**.
- Wait — that is only $110, not $200. Correct. The 2x-credit stop on a 1-contract position keeps you WELL under the 2% budget. This is intentional. You are a new trader. Tight stops build discipline.
- **No exceptions. No "it will come back." No averaging down.** Close and walk away.
- SPY would need to be around $684-685 for the spread to be at 2x. If SPY is at $685, the thesis is failing — the ceasefire rally has legs you did not expect. Respect the market.

### Time stop: Close at 2 DTE

- If the position is still open on **Tuesday Apr 15 (2 DTE)**, close for whatever you can get.
- Gamma accelerates violently in the final 48 hours. A $1 SPY move that costs $0.05 on Thursday costs $0.25 on Wednesday before expiry. Do not hold short options into expiration week's final days.
- If the spread is worth $0.20 or less at 2 DTE, you can let it ride to capture the last $20. But set a hard alert at $0.55 — if it moves back above your 50% target, close.

### CPI Friday (Apr 10) — special rule

- CPI releases at 8:30 AM ET, the day after your entry.
- **If the spread is at 30%+ profit before CPI** ($0.77 or less): close before the number. Do not gamble your profit on a binary event.
- **If the spread is breakeven or slightly underwater:** hold through CPI. A hot CPI is your best friend — it sends SPY down and your spread toward zero.
- **If SPY gaps above $683 on CPI:** your stop loss triggers. Close immediately at market open.

---

## Sizing: Why 1 Contract

| Scenario | Max loss | % of account |
|---|---|---|
| Stop loss triggers (2x credit) | $110 | 1.1% |
| Time stop at 2 DTE (partial loss) | ~$50-150 | 0.5-1.5% |
| Full max loss (did not manage) | $390 | 3.9% |

The stop loss keeps realized risk at 1.1% — comfortably under 2%. Max theoretical loss of 3.9% can only happen if you ignore the stop loss rule. **If you cannot commit to the stop, do not take this trade.**

2 contracts would risk $220 at the stop (2.2%) and $780 at max loss (7.8%). Not appropriate for a new trader on a $10K account. Start with 1. Add contracts after you have managed 2-3 credit spread cycles successfully.

---

## What Can Go Wrong

| Scenario | Impact | Response |
|---|---|---|
| SPY rallies to $685+ on continued ceasefire momentum | Spread moves against you, approaches 2x | Stop loss triggers at $2.20. Realized loss: $110. |
| VIX spikes (war resumes, ceasefire collapses) | IV expansion temporarily hurts short spread | Hold. If war resumes, SPY drops hard. Your spread goes to zero. VIX spike is short-term pain, thesis confirmation. |
| CPI comes in cold, market rips on rate-cut hopes | SPY could test $683 | If at $683+, stop loss. If below, hold — CPI rallies often fade by Monday. |
| SPY chops sideways 673-680 for a week | Best case | Theta grinds the spread to zero. Close at 50% profit. |
| Gap fills to $661 immediately | Best case | Spread goes near-zero within 1-2 days. Close at 75%+ profit. |
| PCE Thursday is a non-event, IV drops | Credit spread benefits from IV drop | This helps us. IV crush on the short call > IV crush on the long call (vega is higher on the closer-to-ATM short). |
| Another geopolitical shock (oil spike, Iran escalation) | SPY drops, VIX spikes | Both help us. The spread collapses in value (profit). |

---

## Execution Checklist

- [ ] Mon-Wed Apr 7-9: Monitor SPY price action. Note the weekly high. If SPY closes above $683 any day before entry, reassess.
- [ ] Thu Apr 9, 8:30 AM: PCE data drops. Note the reaction.
- [ ] Thu Apr 9, 10:00 AM: Check SPY level. If below $682, proceed. If above $682, wait for a pullback or stand aside.
- [ ] Thu Apr 9, 10:00-10:30 AM: Place limit order to SELL the $683/$688 call spread for $1.05 credit (start conservative).
- [ ] If not filled in 10 minutes, adjust to $1.00. Do not chase below $0.90 — the risk/reward deteriorates.
- [ ] Immediately after fill: Set alert at SPY $683 (short strike proximity).
- [ ] Set alert: spread value at $0.55 (50% profit target — close).
- [ ] Set alert: spread value at $2.20 (stop loss — close immediately).
- [ ] Fri Apr 10 (CPI): Follow the CPI special rule above. This is the highest-risk day.
- [ ] Mon Apr 13: If spread is at 40%+ profit, close. Don't hold for the last few cents.
- [ ] Tue Apr 15 (2 DTE): If still open and not at target, close for whatever you can get.
- [ ] Wed Apr 16 - Thu Apr 17: You should NOT be holding at this point.

---

## Why This Trade, In One Paragraph

The market gapped 2.5% on a ceasefire that cannot be enforced because the Iranian command structure is fragmented and leaderless. Call premiums are inflated by hopium. VIX at 20 gives us 20% more premium than normal to sell. We sell the $683 call — above the MPW exhaustion zone, above the gap-day intraday high, above the $680 psychological level — and buy the $688 call for protection. We enter after PCE to capture post-catalyst IV. Theta pays us $12-16/day to wait. If SPY stays below $683, we keep the $110 credit. If we are wrong, the stop loss caps our loss at $110 — 1.1% of the account. The math works: 74% win rate at $55 profit (50% take-profit) minus 26% loss rate at $110 loss = +$12 expected value per trade. It is not exciting. It is correct.

---

*"Premium selling is not predicting where the market goes. It is defining a zone where it probably won't go and getting paid for that opinion while time decay does the work."*
