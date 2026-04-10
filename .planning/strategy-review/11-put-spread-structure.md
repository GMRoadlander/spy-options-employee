# Adversarial Review: 6700/6600 Put Debit Spread Structure

**Claim:** Buy SPX 6700P / Sell SPX 6600P, April 16 expiry, Friday afternoon entry.

**Verdict:** The vehicle choice is defensible but every parameter -- strikes, width, expiry, timing -- appears chosen by round-number convenience rather than analysis.

---

## 1. Strike Selection -- WHERE IS THE ANCHOR?

6700 is a round number, not a level. A long put strike needs a reason to be there: a GEX flip zone where dealer hedging accelerates the move, a high-volume node where supply sits, or a technical support level whose breach triggers stops. Without any of these, 6700 is arbitrary. If the current GEX flip sits at 6720, the 6700 strike is 20 points below the acceleration zone -- you pay for delta you will not use on a dealer-driven flush. If support is at 6680, you are buying a strike above the level that actually matters. Check the GEX profile, the put wall, and Friday's volume-weighted settlement zone. 6750/6650 captures a shallower move with better probability; 6650/6550 targets a deeper flush at lower cost. Neither is obviously wrong -- but 6700/6600 is not obviously right.

## 2. Width -- 100 Points Is a Default, Not a Decision

A 100-point SPX spread risks roughly $3,000-4,500 in premium depending on IV. Wider spreads (150pt) buy more profit potential but the short leg captures less premium offset, inflating cost. Narrower spreads (50pt) are cheaper but cap gains quickly. The right width follows from expected move magnitude. If the thesis is a 2-3% selloff (~130-200 SPX points), a 100pt spread captures only the first 100 of that move. A 150pt spread captures more. If the thesis is a shallow 1% dip, even 100 points is too wide -- a 50pt spread risks less for a move that barely reaches the long strike. State the expected move, then size the width to it.

## 3. Expiry -- April 16 Is a Wednesday Orphan

April 16 is mid-week with no major scheduled catalyst. April 11 (Friday) saves premium but offers only 5 calendar days -- theta bleeds are violent sub-7 DTE. April 17 (Thursday) captures one more day. April 18 (Friday PM-settled) aligns with weekly gamma effects and OpEx dynamics. Wednesday expiry avoids OpEx pin risk, which is a feature if you fear a pinning rally, but it also misses the gamma amplification that makes bearish moves overshoot into Friday. The gamma/theta tradeoff: April 11 has high gamma but extreme theta -- you need the move fast. April 16 or 18 gives more runway at the cost of higher premium and lower gamma sensitivity per day. If the thesis depends on "early next week," April 11 is correct. If it is a slow grind, April 18 is better. April 16 splits the difference and optimizes neither.

## 4. Entry Timing -- "Friday Afternoon" Spans Two Regimes

2:00 PM is pre-power-hour: spreads are wider, IV is mid-range, and institutions are still adjusting. 3:30-3:50 PM is power hour: volume spikes, market makers reprice gamma aggressively, and SPX often makes its intraday directional move. If Friday rallies into the close (common after a selloff week), 3:45 PM entry buys puts at lower IV and a higher spot -- strictly better for a put spread. If Friday sells off into the close, waiting until 3:45 costs more delta. The actionable rule: set a limit order at the close price you want; do not market-order at an arbitrary time.

## 5. Max Loss Scenario -- Death by Flatness

If Monday opens flat and VIX drops, the spread loses both theta and vega simultaneously. At 10 DTE with IV declining, a 100pt OTM put spread might lose 15-20% of its value per day in a flat/rising market. By Wednesday (7 DTE), roughly half the extrinsic value is gone. By the following Monday (2 DTE), the spread is worth pennies unless SPX is near 6700. Realistic survival window: 3-4 trading days of flat tape before the spread is effectively dead. Set a stop-loss at 50% of premium paid, not at expiry.

## 6. Vehicle Choice -- Would an Experienced Trader Do This?

A put debit spread is a directional bet with defined risk -- appropriate for a new trader. An experienced trader with the same bearish thesis would likely sell a put credit spread above the money (e.g., sell 5750/5700 puts for premium income, profiting if SPX stays above), or sell call credit spreads at resistance, or structure an iron condor if conviction is moderate. The reason: selling premium has positive expected value in elevated-IV environments because implied vol consistently overprices realized vol. Buying premium fights this structural headwind. A put debit spread is not wrong, but it requires the move to happen fast enough to overcome the vol premium you paid. If showing this to an experienced trader, expect the question: "Why are you buying vol instead of selling it?"

---

**Bottom line:** Every parameter defaults to the nearest round number or calendar convenience. An adversarial-proof version names the GEX level that anchors the long strike, sizes width to expected move magnitude, picks expiry based on catalyst timing, enters on a limit order at close, and includes a 50%-of-premium stop. Without those, this is a thesis in search of a structure.
