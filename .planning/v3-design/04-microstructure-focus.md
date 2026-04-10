# V3 Swarm Design: Market Microstructure Focus

**Date**: 2026-04-06
**Context**: SPY gap fill thesis (678 to 661). Iran ceasefire unenforceable. VIX ~20. PCE/CPI this week.
**Problem Statement**: V1/V2 had ZERO reference to GEX, dealer positioning, put/call ratios, 0DTE flow, dark pool activity, or options market microstructure. Every position was based on directional thesis + MPW chart patterns. This platform computes all of these signals. V3 uses them.

---

## Design Philosophy

Market microstructure is not a "nice to have" overlay -- it is the PRIMARY input for strike selection, timing, and position sizing. Directional thesis tells you WHAT to trade. Microstructure tells you WHERE (which strikes), WHEN (entry/exit timing relative to flow dynamics), and HOW MUCH (sizing relative to dealer positioning risk).

The 30 agents are organized into 5 tiers:

| Tier | Role | Agent Count | Feeds Into |
|------|------|-------------|------------|
| 1 - Data Extraction | Pull live microstructure data from platform engines | 5 | Tier 2 |
| 2 - Microstructure Analysis | Interpret dealer positioning, flow dynamics, regime | 8 | Tier 3 |
| 3 - Strike Architecture | Anchor strikes/spreads to GEX levels, not round numbers | 8 | Tier 4 |
| 4 - Position Drafting | Draft full positions using microstructure justification | 6 | Tier 5 |
| 5 - Synthesis & Conflict Resolution | Merge, challenge, finalize | 3 | Output |

---

## TIER 1: Data Extraction Agents (5 agents)

These agents pull structured data from the platform's existing analysis engines. They do NOT interpret -- they extract and normalize. Every downstream agent receives data from Tier 1, never from raw APIs.

### Agent 01: GEX Profile Extractor

**Consumes**: `src/analysis/gex.py` -> `GEXResult`
**Produces**: Structured GEX snapshot

```
Output schema:
  net_gex: float               # Total net gamma exposure
  gamma_flip: float | null     # Zero-gamma crossing price
  gamma_ceiling: float | null  # Strike with max call GEX (call wall)
  gamma_floor: float | null    # Strike with max put GEX (put wall)
  squeeze_probability: float   # 0-1 score
  net_gex_by_strike: dict      # Per-strike net GEX profile
  gex_by_expiry: dict | null   # Per-expiry breakdown
  dealer_gamma_regime: str      # "long_gamma" | "short_gamma" | "transitional"
  gex_skew: float              # Call GEX sum / Put GEX sum (>1 = call-heavy)
```

**Critical extraction logic**:
- Classify `dealer_gamma_regime` from net_gex sign and magnitude: positive net GEX above a threshold = long_gamma (dealers suppress vol), negative = short_gamma (dealers amplify vol), near zero = transitional.
- Compute `gex_skew` as the ratio of total positive call GEX to total absolute put GEX. This tells downstream agents whether dealer exposure is tilted toward calls or puts.
- Flag if gamma_flip is within 0.5% of spot (regime boundary -- high sensitivity zone).

**Why this agent exists**: Raw `GEXResult` has 12 fields. Not every downstream agent needs all of them, and some need derived metrics (regime classification, skew ratio) that the raw engine does not produce. This agent normalizes the interface.

---

### Agent 02: Put/Call Ratio & Dealer Positioning Extractor

**Consumes**: `src/analysis/pcr.py` -> `PCRResult`
**Produces**: Structured PCR/dealer snapshot

```
Output schema:
  volume_pcr: float
  oi_pcr: float
  sentiment_signal: str         # "extreme_bullish" | "bullish" | "neutral" | "bearish" | "extreme_fear"
  dealer_positioning: str       # "short_gamma" | "long_gamma" | "neutral"
  pcr_percentile: float | null  # Where current PCR sits vs. 20-day range (from feature store)
  call_volume: int
  put_volume: int
  call_oi: int
  put_oi: int
  volume_oi_divergence: str     # "confirming" | "diverging" (volume PCR vs OI PCR agreement)
```

**Critical extraction logic**:
- `volume_oi_divergence`: When volume PCR and OI PCR disagree (e.g., volume says extreme_fear but OI says neutral), this is a signal that today's flow is an anomaly relative to existing positioning. "Diverging" is a high-information state.
- Pull `pcr_percentile` from feature store (`src/ml/feature_store.py`) if available -- this contextualizes whether a PCR of 1.1 is extreme for THIS market or normal.

---

### Agent 03: Flow & Dark Pool Extractor

**Consumes**: `src/data/unusual_whales_client.py` -> flow data, `src/data/polygon_client.py` -> OPRA stream, `src/ml/anomaly.py` -> `FlowAnalyzer`
**Produces**: Structured intraday flow snapshot

```
Output schema:
  sweep_count: int              # Today's sweep orders (aggressive fills)
  block_count: int              # Today's block trades (>100 lots)
  net_premium: float            # Net call premium - net put premium
  premium_skew: str             # "call_heavy" | "put_heavy" | "balanced"
  dark_pool_ratio: float        # % of volume off-exchange
  dark_pool_bias: str           # "buying" | "selling" | "neutral" (from print price vs. NBBO)
  largest_prints: list          # Top 5 trades by premium (strike, type, size, side)
  anomaly_flags: list           # Active anomaly detections from FlowAnalyzer
  zero_dte_flow: dict           # Separate flow stats for 0DTE contracts only
```

**Critical extraction logic**:
- Isolate 0DTE flow from multi-day flow. 0DTE call buying has an outsized market impact because 0DTE gamma is extreme -- a $1M 0DTE call sweep moves more delta than a $1M 30DTE call sweep.
- Flag when dark pool ratio exceeds 40% (institutional activity hiding from lit markets -- often precedes directional moves).
- The `anomaly_flags` come directly from the `FlowAnomalyDetector` IsolationForest in `src/ml/anomaly.py`.

---

### Agent 04: Key Levels & Strike Intel Extractor

**Consumes**: `src/analysis/strike_intel.py` -> `StrikeIntelResult`, `src/analysis/max_pain.py` -> `MaxPainResult`
**Produces**: Consolidated key levels map

```
Output schema:
  key_levels: list[KeyLevel]       # Sorted by significance
  max_pain: float                  # Expiry magnet price
  max_pain_distance_pct: float     # How far spot is from max pain
  high_oi_call_strikes: list       # Top 5 call OI concentrations
  high_oi_put_strikes: list        # Top 5 put OI concentrations
  optimal_call_strikes: list       # GEX-aligned call recommendations
  optimal_put_strikes: list        # GEX-aligned put recommendations
  oi_concentration_score: float    # How concentrated OI is at a few strikes vs. spread out
```

**Critical extraction logic**:
- Compute `oi_concentration_score`: Herfindahl index of OI across strikes. High concentration means a few strikes dominate dealer exposure (strong magnet effects). Low concentration means no clear dealer pressure points.
- Cross-reference key levels: If gamma_flip, max_pain, and a high-OI strike are all within $5 of each other, flag this as a "convergence zone" -- price is likely to be sticky there.

---

### Agent 05: Regime & Volatility Context Extractor

**Consumes**: `src/ml/regime.py` -> HMM state, `src/ml/volatility.py` -> LSTM forecast, `src/ml/features.py` -> feature set
**Produces**: Volatility regime context

```
Output schema:
  hmm_regime: str               # "risk_on" | "risk_off" | "crisis"
  regime_confidence: float      # HMM posterior probability
  regime_duration_days: int     # How long current regime has persisted
  iv_rank: float                # Current IV vs. 1-year range
  iv_percentile: float          # % of days IV was below current
  rv_iv_spread: float           # Realized vol - implied vol (variance risk premium)
  vol_forecast_1d: float        # LSTM 1-day ahead vol forecast
  vol_forecast_5d: float        # LSTM 5-day ahead vol forecast
  hurst_exponent: float         # <0.5 mean-reverting, >0.5 trending
  vix_term_structure: str       # "contango" | "backwardation" | "flat"
```

**Critical for microstructure**: When IV rank is high and RV/IV spread is positive (realized vol exceeding implied), options are cheap relative to actual movement -- this is when dealer hedging has the largest impact because gamma is mispriced.

---

## TIER 2: Microstructure Analysis Agents (8 agents)

These agents INTERPRET the extracted data. Each produces a directional or structural thesis grounded in microstructure, not chart patterns.

### Agent 06: Dealer Gamma Regime Analyst

**Consumes**: Agent 01 (GEX), Agent 02 (PCR)
**Produces**: Dealer regime assessment with trading implications

**Core question**: Are dealers long or short gamma, and what does that mean for the next 1-5 days?

**Analysis framework**:

1. **Long gamma regime** (net GEX positive, spot above gamma flip):
   - Dealers are hedging by selling into rallies and buying dips -> volatility is suppressed
   - Price action will be "sticky" and mean-reverting around the gamma ceiling
   - Implication: SELL premium, use credit spreads, expect narrow ranges
   - Strike anchor: sell strikes near gamma ceiling (call side) or gamma floor (put side)

2. **Short gamma regime** (net GEX negative, spot below gamma flip):
   - Dealers are hedging by buying into rallies and selling into dips -> volatility is amplified
   - Price action will be "slippery" with outsized moves in the direction of initial impulse
   - Implication: BUY premium, use debit spreads, expect expanded ranges
   - Strike anchor: the gamma floor becomes a target (not support), gamma ceiling becomes a magnet on reversal

3. **Transitional regime** (spot near gamma flip, net GEX near zero):
   - Most dangerous state -- small moves can flip dealer positioning
   - Implication: REDUCE position size, widen stops, avoid selling naked premium
   - Strike anchor: straddles/strangles around gamma flip

**Output**:
```
  regime: str                   # "long_gamma" | "short_gamma" | "transitional"
  regime_strength: float        # 0-1 (how far from the boundary)
  implied_strategy_bias: str    # "sell_premium" | "buy_premium" | "neutral"
  vol_expectation: str          # "compressed" | "amplified" | "uncertain"
  key_implication: str          # 1-2 sentence plain English summary for Borey
```

---

### Agent 07: 0DTE Flow Dynamics Analyst

**Consumes**: Agent 03 (Flow), Agent 01 (GEX)
**Produces**: 0DTE-specific microstructure assessment

**Core question**: Is 0DTE flow amplifying or dampening the current move, and when does it unwind?

**Analysis framework**:

SPX has daily expirations. 0DTE options have extreme gamma (highest gamma of any contract in the market). When retail or institutional players buy 0DTE calls en masse, dealers get short those calls and must delta-hedge by buying SPX futures. This creates a feedback loop:

1. **0DTE call buying surge**: Dealers buy futures to hedge -> SPX rises -> calls go further ITM -> dealers buy more futures -> "gamma squeeze" upward
2. **0DTE put buying surge**: Dealers sell futures to hedge -> SPX drops -> puts go further ITM -> dealers sell more -> "gamma squeeze" downward
3. **Unwind at 3:00-3:30 PM ET**: As 0DTE contracts expire, gamma collapses, dealer hedges unwind, and the squeeze reverses. This is the most dangerous 30 minutes for any position initiated during a 0DTE-driven move.
4. **VANNA flows**: As 0DTE options lose time value and IV changes, vanna (dS/dIV) creates additional hedging flows that can be directional.

**Output**:
```
  zero_dte_net_premium: float      # Net premium flow in 0DTE contracts
  zero_dte_direction: str          # "call_dominant" | "put_dominant" | "balanced"
  gamma_feedback_active: bool      # Is the 0DTE flow creating a self-reinforcing move?
  estimated_unwind_size: float     # Approximate notional of 0DTE dealer hedges that will unwind
  unwind_risk_window: str          # "3:00-3:30 PM ET" or "already unwinding"
  implications: str                # Plain English: "0DTE call buying is amplifying the rally. Expect reversal pressure after 3PM."
```

**Critical caveat for positions**: If a V3 position is entered because of a rally driven by 0DTE call buying, the agent MUST flag that the move may be temporary and will likely reverse in the last 30 minutes of the session. This is the single most common trap for directional traders.

---

### Agent 08: Options Market Maker Positioning Analyst

**Consumes**: Agent 01 (GEX), Agent 02 (PCR), Agent 04 (Key Levels)
**Produces**: Where are MMs hedged and what does their hedging do to the trade?

**Core question**: At the proposed entry price and strike, is MM hedging flow working FOR the trade or AGAINST it?

**Analysis framework**:

Market makers are net short options (they provide liquidity by selling to retail/institutional buyers). Their delta hedging creates mechanical flows:

1. **Call wall (gamma ceiling)**: MMs are heavily short calls at this strike. As spot approaches, they must sell stock/futures to stay delta-neutral. This creates resistance. Above the call wall, their hedging accelerates selling -- the wall "pushes back."

2. **Put wall (gamma floor)**: MMs are heavily short puts at this strike. As spot approaches from above, they must buy stock/futures. This creates support. Below the put wall, their hedging accelerates buying -- the floor "catches."

3. **Between walls**: Price tends to oscillate. MMs are "pinned" -- their hedging dampens both up and down moves.

4. **Outside walls**: When spot breaks through a wall, the MM hedging that was opposing the move suddenly reverses and AMPLIFIES it. A break above the call wall forces MMs to buy aggressively (they flip from selling into the rally to buying to cover). This is a "gamma squeeze breakout."

**Output**:
```
  spot_vs_call_wall: str           # "below" | "at" | "above" | "no_wall"
  spot_vs_put_wall: str            # "above" | "at" | "below" | "no_wall"
  mm_hedging_direction: str        # "buying" | "selling" | "neutral"
  mm_hedging_magnitude: str        # "light" | "moderate" | "heavy"
  wall_break_risk: str             # "call_wall_at_risk" | "put_wall_at_risk" | "both_intact" | "already_broken"
  pinning_probability: float       # 0-1: likelihood that price pins between walls into close
  breakout_amplification: str      # If a wall breaks, describe the expected acceleration
  implications: str
```

---

### Agent 09: Put/Call Ratio Signal Analyst

**Consumes**: Agent 02 (PCR), Agent 05 (Regime)
**Produces**: PCR-based entry/exit signal with regime context

**Core question**: Is the current put/call ratio at an extreme that signals a reversal or continuation?

**Analysis framework**:

PCR signals are CONTRARIAN at extremes and CONFIRMING in trends:

1. **PCR < 0.3 (extreme bullish / complacency)**: Everyone is buying calls. Historically this precedes pullbacks because:
   - Positioning is one-sided (crowded long)
   - Dealers are massively short calls -> short gamma -> amplification on any reversal
   - This is a SELL signal for calls, BUY signal for puts (contrarian)

2. **PCR > 1.15 (extreme fear)**: Everyone is buying puts. Historically this precedes bounces because:
   - Put buying has exhausted itself
   - Dealers are short puts -> their hedging (buying stock) provides mechanical support
   - Extreme put PCR often marks capitulation bottoms
   - This is a SELL signal for puts, BUY signal for calls (contrarian)

3. **PCR 0.7-1.0 (neutral)**: No signal. Don't use PCR for timing in this range.

4. **Regime modifier**: In the `crisis` regime (from HMM), extreme_fear PCR readings are NOT contrarian -- they confirm the trend. Only apply contrarian logic in `risk_on` and `risk_off` regimes.

**Output**:
```
  pcr_signal: str                  # "contrarian_bullish" | "contrarian_bearish" | "confirming" | "no_signal"
  signal_strength: float           # 0-1
  regime_adjusted: bool            # Did regime context modify the raw signal?
  entry_bias: str                  # "favor_calls" | "favor_puts" | "neutral"
  timing_implication: str          # "enter_now" | "wait_for_confirmation" | "avoid"
  rationale: str
```

---

### Agent 10: Dark Pool Divergence Analyst

**Consumes**: Agent 03 (Flow), Agent 05 (Regime)
**Produces**: Institutional flow signal from off-exchange activity

**Core question**: Is institutional (dark pool) flow diverging from retail (lit market) flow, and which one should we trust?

**Analysis framework**:

Dark pool prints represent institutional order flow that is deliberately hidden from lit exchanges. When dark pool flow diverges from lit market direction, institutions are positioning against the visible trend:

1. **SPX rallying + dark pool selling**: Institutions distributing into strength. Bearish signal. The rally may be retail-driven and unsustainable.
2. **SPX dropping + dark pool buying**: Institutions accumulating on weakness. Bullish signal. The selloff may be retail panic.
3. **Dark pool ratio > 40%**: Abnormally high off-exchange activity suggests large block positioning is happening -- a directional move may follow.

**Output**:
```
  dark_pool_divergence: bool       # Is DP flow opposite to lit market direction?
  divergence_direction: str        # "bullish_divergence" | "bearish_divergence" | "none"
  dp_ratio: float                  # Current dark pool ratio
  dp_ratio_percentile: float       # vs. 20-day range
  institutional_signal: str        # "accumulating" | "distributing" | "neutral"
  confidence: float                # 0-1
  rationale: str
```

---

### Agent 11: GEX-Anchored Strike Map Architect

**Consumes**: Agent 01 (GEX), Agent 04 (Key Levels), Agent 08 (MM Positioning)
**Produces**: The master strike map that ALL position-drafting agents must use

**Core question**: Given current GEX levels, which strikes are structurally sound and which are traps?

This is the CENTRAL agent that replaces V1/V2's "pick a round number or Fibonacci level" approach.

**Analysis framework**:

Every strike in a position must be justified by its relationship to a GEX level:

| Strike Role | Anchored To | Rationale |
|-------------|-------------|-----------|
| Short call strike | At or above gamma ceiling | MM hedging creates resistance -- selling premium here is selling against the wall |
| Short put strike | At or below gamma floor | MM hedging creates support -- selling premium here is selling with the floor |
| Long call strike | Between gamma flip and gamma ceiling | Positive gamma territory, room to run, MM hedging supports the move |
| Long put strike | Between gamma floor and gamma flip | Negative gamma territory, move gets amplified by dealer hedging |
| Debit spread short leg | At the next GEX wall beyond your target | The wall limits further movement, defining natural take-profit |
| Credit spread long leg | One wall beyond the short leg | If the short leg's wall breaks, the long leg's wall provides emergency support |
| Stop/adjustment trigger | At gamma flip | Regime change signal -- if spot crosses gamma flip, the entire hedging dynamic inverts |

**Output**:
```
  approved_call_strikes: list      # Strikes justified by GEX for bullish exposure
  approved_put_strikes: list       # Strikes justified by GEX for bearish exposure
  forbidden_strikes: list          # Strikes that sit in "no man's land" (between walls with no GEX support)
  anchor_rationale: dict           # For each approved strike: which GEX level anchors it and why
  convergence_zones: list          # Price ranges where multiple key levels cluster
  regime_boundary: float | null    # Gamma flip -- the line where everything changes
```

**Enforcement**: No Tier 3 or Tier 4 agent may propose a strike that is not in `approved_call_strikes` or `approved_put_strikes`. If a position needs a strike outside the approved set, it must be escalated to Agent 28 (Conflict Resolver) with a written justification.

---

### Agent 12: OI Shift & Positioning Change Detector

**Consumes**: Agent 04 (Key Levels), historical OI from previous cycle
**Produces**: Intraday OI change signals

**Core question**: Has positioning shifted since the last analysis cycle, and does that change the thesis?

**Analysis framework**:

OI changes reveal new positioning being built or existing positioning being unwound:
- OI increase + price up at a call strike = new bullish bets being opened (confirming)
- OI increase + price down at a put strike = new hedges being opened (confirming)
- OI decrease + price up = short covering on calls (potential exhaustion)
- OI decrease + price down = put profit-taking (potential bottom)

When a key GEX level's OI changes by >20%, the GEX profile shifts and all downstream strikes may need re-anchoring.

**Output**:
```
  significant_oi_changes: list     # Strikes where OI changed >20% from prior cycle
  positioning_shift: str           # "bullish_building" | "bearish_building" | "unwinding" | "stable"
  gex_invalidated: bool            # Has GEX profile shifted enough to re-run Agent 11?
  key_level_stability: str         # "stable" | "shifting" | "broken" (have the walls moved?)
  rationale: str
```

---

### Agent 13: Gamma Flip Proximity & Transition Analyst

**Consumes**: Agent 01 (GEX), Agent 06 (Dealer Regime)
**Produces**: Proximity analysis for the most important level in options microstructure

**Core question**: How close is spot to the gamma flip, and what happens if it crosses?

The gamma flip (Vol Trigger in SpotGamma terminology) is the single most important level for position management. Above it, the market is mechanically calm. Below it, the market is mechanically volatile. Crossing it changes everything.

**Analysis framework**:

```
Distance categories:
  >2% above gamma flip:   "Deep positive gamma" -- low urgency, mean-reversion favored
  0.5-2% above:           "Positive but close" -- monitor for breakdown
  Within 0.5%:            "At boundary" -- MAXIMUM CAUTION, any position must account for regime flip
  0.5-2% below:           "Negative but close" -- short gamma amplifying moves, could snap back
  >2% below:              "Deep negative gamma" -- directional moves accelerate, don't fight the flow
```

**Output**:
```
  distance_to_flip_pct: float      # Signed: positive = above, negative = below
  proximity_zone: str              # Category from above
  flip_cross_scenario: str         # What happens to existing positions if spot crosses
  recommended_position_adjustment: str  # "hold" | "reduce" | "hedge" | "exit"
  stop_level_suggestion: float     # Where to place stops relative to gamma flip
```

---

## TIER 3: Strike Architecture Agents (8 agents)

Each of these agents drafts a specific position type, using Tier 2 microstructure analysis to select strikes. They do NOT produce final positions -- they produce candidates for Tier 4 to evaluate.

### Agent 14: GEX-Anchored Bear Put Spread Architect

**Thesis**: SPY gap fill 678->661. Bearish directional.
**Microstructure requirements**:
- Short put strike anchored at or near gamma floor (MM hedging provides natural target)
- Long put strike at the next major put OI concentration below gamma floor (cost reduction with structural support)
- Entry: Only when dealer gamma regime is short_gamma or transitional (amplification regime)
- Avoid: If PCR is already extreme_fear (contrarian bounce risk)
- 0DTE check: If 0DTE put buying is already heavy, the move may be priced in

**Strike selection algorithm**:
1. Get `gamma_floor` from Agent 11's approved put strikes
2. Select short put 1-2 strikes above gamma floor (sell premium into the wall)
3. Select long put at the next high-OI put cluster below (from Agent 04)
4. Width: defined by distance between GEX walls, not arbitrary $5 or $10 widths
5. Expiry: match to the expiry with the steepest GEX profile (from Agent 01's gex_by_expiry)

---

### Agent 15: GEX-Anchored Bull Call Spread Architect

**Thesis**: Bounce play if gap fill completes and reverses.
**Microstructure requirements**:
- Short call strike at or near gamma ceiling (wall provides natural target and resistance)
- Long call strike near gamma flip or the nearest high-OI call concentration
- Entry: Only when PCR is extreme_fear (contrarian) AND dealer positioning is shifting
- 0DTE check: If 0DTE call buying is surging, this amplifies the bounce

**Strike selection algorithm**:
1. Get `gamma_ceiling` from Agent 11
2. Short call at gamma ceiling or one strike above (sell into the wall)
3. Long call at gamma flip or nearest approved call strike below ceiling
4. Width: defined by gamma ceiling - gamma flip distance

---

### Agent 16: Gamma Flip Straddle/Strangle Architect

**Thesis**: Price is near gamma flip -- direction is uncertain but magnitude will be large.
**Microstructure requirements**:
- ONLY enter when Agent 13 reports proximity_zone = "At boundary" (within 0.5% of gamma flip)
- Straddle strike at gamma flip itself
- Strangle: call leg at gamma ceiling, put leg at gamma floor (wings at the walls)
- This is a volatility play, not a directional play
- Dealer regime: must be "transitional" -- confirms the vol expansion thesis

**Strike selection algorithm**:
1. Center: gamma flip from Agent 11's regime_boundary
2. Call wing: gamma ceiling
3. Put wing: gamma floor
4. Expiry: shortest expiry that spans at least one catalyst (PCE/CPI dates)

---

### Agent 17: Dark Pool Divergence Fade Architect

**Thesis**: Institutional flow diverges from retail -- trade with institutions.
**Microstructure requirements**:
- ONLY enter when Agent 10 reports dark_pool_divergence = true with confidence > 0.7
- If bullish divergence (institutions buying while market drops): bull call spread
- If bearish divergence (institutions selling while market rallies): bear put spread
- Strikes: anchor to the nearest GEX level in the direction of the divergence

**Strike selection algorithm**:
1. Determine direction from Agent 10
2. For bullish: long call at nearest approved call strike below spot, short call at gamma ceiling
3. For bearish: long put at nearest approved put strike above spot, short put at gamma floor
4. This is a FADE trade -- expect mean reversion, not continuation

---

### Agent 18: 0DTE Gamma Squeeze Amplifier Architect

**Thesis**: 0DTE flow is creating a self-reinforcing directional move -- ride it but respect the unwind.
**Microstructure requirements**:
- ONLY enter when Agent 07 reports gamma_feedback_active = true
- Direction: follow the 0DTE flow (call dominant = bullish, put dominant = bearish)
- HARD EXIT RULE: position MUST close by 2:45 PM ET to avoid the 3:00 PM unwind
- Use debit spreads (defined risk) because 0DTE gamma works both ways

**Strike selection algorithm**:
1. Direction from Agent 07
2. If call dominant: debit call spread with long leg at nearest ATM approved strike, short leg at gamma ceiling
3. If put dominant: debit put spread with long leg at nearest ATM approved strike, short leg at gamma floor
4. Width: narrow (0DTE gamma makes even narrow spreads responsive)
5. MANDATORY: `exit_time: "14:45 ET"` in position metadata

---

### Agent 19: Max Pain Expiry Magnet Architect

**Thesis**: Price gravitates toward max pain as expiration approaches (dealer pinning effect).
**Microstructure requirements**:
- ONLY relevant within 2 days of expiration for the target expiry
- Strongest when gamma regime is long_gamma (dealers actively suppress moves toward max pain)
- Weakest when gamma regime is short_gamma (dealers amplify moves AWAY from max pain)
- Use butterfly or iron condor centered on max pain

**Strike selection algorithm**:
1. Center: max pain price from Agent 04
2. Wings: gamma ceiling (upper) and gamma floor (lower)
3. Width: asymmetric if max_pain is not centered between walls
4. Reject if max_pain_distance_pct > 2% AND gamma regime is short_gamma (too far to pin)

---

### Agent 20: PCR Extreme Contrarian Architect

**Thesis**: PCR at an extreme signals a reversal. Position for the snap-back.
**Microstructure requirements**:
- ONLY enter when Agent 09 reports pcr_signal = "contrarian_bullish" or "contrarian_bearish"
- For contrarian bullish (PCR was extreme_fear, expecting bounce): sell put credit spread at gamma floor
- For contrarian bearish (PCR was extreme_bullish, expecting pullback): sell call credit spread at gamma ceiling
- VETO: If HMM regime is "crisis", do NOT trade contrarian bullish -- fear is justified in crisis
- Credit spreads because we are selling the extreme -- collect premium from panic

**Strike selection algorithm**:
1. For contrarian bullish: short put at gamma floor, long put one approved strike below
2. For contrarian bearish: short call at gamma ceiling, long call one approved strike above
3. Premium target: collect at least 30% of spread width (theta advantage on reversal)

---

### Agent 21: Squeeze Probability Exploiter Architect

**Thesis**: Squeeze probability is elevated (>0.6) -- position for an explosive move.
**Microstructure requirements**:
- Consumes Agent 01 squeeze_probability AND Agent 06 regime assessment
- High squeeze probability + short gamma regime = expect large move in direction of flow
- Use long gamma positions (debit spreads, long straddles) to benefit from the expansion
- Direction hint: from Agent 07 (0DTE flow) and Agent 09 (PCR signal)

**Strike selection algorithm**:
1. If directional bias exists: debit spread in that direction, legs at GEX walls
2. If no directional bias: straddle at gamma flip (benefit from movement regardless of direction)
3. Expiry: 3-7 DTE (enough time for the squeeze to develop, short enough to capture gamma)

---

## TIER 4: Position Drafting Agents (6 agents)

These agents take Tier 3 candidates and produce fully specified positions with entry/exit criteria, position sizing, and risk parameters -- all anchored to microstructure.

### Agent 22: Microstructure-Justified Position Drafter (Bearish)

**Consumes**: Agents 14 (bear put), 17 (DP fade if bearish), 18 (0DTE if put dominant), 20 (PCR contrarian if bearish)
**Produces**: 1-2 fully specified bearish positions

For each candidate from Tier 3:
1. Verify ALL strikes are in Agent 11's approved set (reject if not)
2. Verify dealer regime supports the trade (Agent 06)
3. Verify no conflicting 0DTE dynamics (Agent 07)
4. Compute position size based on squeeze probability (higher squeeze = smaller size due to whipsaw risk)
5. Set stops relative to gamma flip (the regime change level)
6. Set profit targets at GEX walls (where MM hedging supports the target)

**Output per position**:
```
  strategy: str                    # e.g., "bear_put_spread"
  legs: list[Leg]                  # Each leg with strike, expiry, type, direction
  entry_condition: str             # "Enter when spot is below gamma flip" or similar
  stop_loss: float                 # Anchored to gamma flip or ceiling
  profit_target: float             # Anchored to gamma floor or max pain
  position_size: str               # % of paper portfolio, adjusted for squeeze probability
  max_loss: float                  # Defined by spread width
  microstructure_justification: str  # 3-5 sentences citing specific GEX levels, PCR signals, flow data
  risk_flags: list[str]            # e.g., ["0DTE_unwind_risk", "near_gamma_flip"]
  exit_triggers: list[str]         # e.g., ["gamma_flip_crossed_upward", "pcr_drops_below_0.8"]
```

---

### Agent 23: Microstructure-Justified Position Drafter (Bullish)

**Consumes**: Agents 15 (bull call), 17 (DP fade if bullish), 18 (0DTE if call dominant), 20 (PCR contrarian if bullish)
**Produces**: 1-2 fully specified bullish positions

Same framework as Agent 22 but for bullish candidates. Additional check: if the gap fill thesis (678->661) is active and bearish, any bullish position must be explicitly framed as a HEDGE or BOUNCE play, not a primary thesis. The microstructure data must show WHY the bounce is structurally supported (e.g., approaching gamma floor, extreme_fear PCR, dark pool buying divergence).

---

### Agent 24: Microstructure-Justified Position Drafter (Volatility)

**Consumes**: Agents 16 (gamma flip straddle), 21 (squeeze exploiter)
**Produces**: 1-2 fully specified volatility positions

These are non-directional plays that profit from movement magnitude, not direction. Microstructure justification must show:
- WHY vol expansion is expected (regime transition, squeeze probability, 0DTE feedback)
- WHERE the vol expansion will be bounded (GEX walls define the expected range)
- WHEN to exit (catalyst timing: PCE/CPI dates, 0DTE unwind windows)

---

### Agent 25: Position Risk Overlay Agent

**Consumes**: ALL Tier 4 positions (Agents 22-24)
**Produces**: Risk-adjusted position set with microstructure-based risk metrics

For each position:
1. **Gamma flip risk**: How close is spot to gamma flip? If <0.5%, halve position size.
2. **0DTE unwind risk**: Does the position overlap with a 0DTE-driven move? Add time-based exit.
3. **Catalyst risk**: PCE/CPI this week -- positions spanning the catalyst must account for the vol crush or expansion.
4. **Correlation risk**: If multiple positions are all bearish and all anchored to the same gamma floor, they are correlated. Flag and suggest reducing total exposure.
5. **Regime change risk**: If the HMM regime confidence is < 0.7, the regime could flip. Add contingency plan.
6. **Dealer regime sensitivity**: Compute how each position's P&L changes if net_gex flips sign (stress test the microstructure thesis).

**Output**: Same positions as input but with:
- `risk_score: float` (0-1, higher = more risk from microstructure)
- `risk_adjustments: list[str]` (specific changes made)
- `position_size_override: str | null` (if risk overlay reduced size)
- `contingency_plan: str` (what to do if the microstructure thesis breaks)

---

### Agent 26: Microstructure Summary Narrator

**Consumes**: ALL Tier 2 analyses (Agents 06-13)
**Produces**: 1-paragraph plain English microstructure summary for Borey

This is NOT position advice -- it is a market structure briefing that answers "what does the FLOW say?" before any positions are discussed.

**Template**:
```
MARKET MICROSTRUCTURE BRIEFING (as of {timestamp})

Dealers are currently {long/short/transitional} gamma with net GEX at {value}.
Gamma flip sits at {price} ({distance}% {above/below} spot) -- we are in
{positive/negative} gamma territory meaning dealer hedging {dampens/amplifies}
moves. Call wall (resistance): {gamma_ceiling}. Put wall (support): {gamma_floor}.

Put/call ratio is {volume_pcr} ({signal}) -- {interpretation based on Agent 09}.
{If PCR is extreme: "This is a {contrarian/confirming} signal because {reason}."}

0DTE flow: {summary from Agent 07}. {If feedback active: "0DTE {call/put} buying
is creating a self-reinforcing {rally/selloff}. Unwind risk at {time}."}

Dark pool: {summary from Agent 10}. {If divergence: "Institutional flow is
{diverging/confirming} -- {interpretation}."}

Regime: HMM reads {regime} with {confidence}% confidence, {duration} days running.
IV rank: {iv_rank}. Vol forecast: {vol_1d}/{vol_5d}.

Bottom line: The flow says {1 sentence synthesis of what all microstructure
signals agree on, or where they conflict}.
```

---

### Agent 27: Iran Ceasefire / Geopolitical Catalyst Overlay

**Consumes**: Directional thesis, Agent 05 (Regime), Agent 09 (PCR)
**Produces**: How geopolitical catalyst interacts with current microstructure

**Specific analysis**:
- Iran ceasefire "unenforceable" per thesis. This is a TAIL RISK catalyst, not a central scenario.
- If ceasefire collapses: risk-off shock -> VIX spike -> short gamma regime amplifies the drop -> gamma floor becomes a target, not support
- If ceasefire holds: risk-on relief -> VIX compression -> long gamma regime absorbs the rally -> gamma ceiling acts as resistance
- Current VIX ~20 is elevated but not panic. PCR and flow data tell us which scenario the market is pricing.

**Output**:
```
  catalyst: str                    # "iran_ceasefire"
  market_pricing: str              # "partially_priced" | "not_priced" | "fully_priced"
  microstructure_alignment: str    # Does current dealer positioning amplify or dampen the catalyst?
  scenario_if_collapse: str        # What happens to GEX levels and positions
  scenario_if_holds: str           # What happens to GEX levels and positions
  position_adjustment: str         # How to modify positions for the catalyst
```

---

## TIER 5: Synthesis & Conflict Resolution (3 agents)

### Agent 28: Microstructure Conflict Resolver

**Consumes**: ALL Tier 4 positions (Agents 22-25), ALL Tier 2 analyses
**Produces**: Resolved position set with no internal contradictions

**Conflict patterns to detect and resolve**:

1. **Directional contradiction**: A bearish put spread AND a bullish call spread at the same time. This is acceptable ONLY if they are explicitly framed as a straddle-like structure or if they have non-overlapping expiries/triggers.

2. **Strike violation**: Any position using a strike NOT in Agent 11's approved set. Must be rejected or escalated.

3. **Regime mismatch**: A credit spread (sell premium) recommended when the dealer regime is short_gamma (volatility amplified). Short gamma regimes PUNISH premium sellers. Flag and either veto the credit spread or require a regime change confirmation before entry.

4. **0DTE time bomb**: A position entered during 0DTE-driven flow without a pre-close exit plan. Add the exit plan or veto.

5. **Overcrowding**: All positions clustered at the same GEX level. Diversify across levels or reduce total count.

6. **Catalyst blindness**: A position that ignores the PCE/CPI dates or the Iran ceasefire dynamic. Add catalyst awareness.

**Output**: Final position set with conflicts documented and resolved.

---

### Agent 29: V1/V2 Gap Auditor

**Consumes**: Final position set from Agent 28
**Produces**: Audit confirming V1/V2 gaps are closed

This agent exists SOLELY to prevent regression to V1/V2 behavior. For each position, it checks:

| V1/V2 Gap | V3 Requirement | Check |
|-----------|----------------|-------|
| No GEX reference | Every strike anchored to a GEX level | Verify `anchor_rationale` is non-empty for every leg |
| No dealer positioning | Dealer regime cited in justification | Verify `microstructure_justification` mentions gamma regime |
| No PCR signals | PCR signal cited or explicitly noted as neutral | Verify Agent 09 output is referenced |
| No 0DTE flow | 0DTE dynamics considered | Verify Agent 07 output is referenced (even if "no 0DTE signal") |
| No dark pool data | Dark pool signal considered | Verify Agent 10 output is referenced |
| Round number strikes | Strikes justified by GEX, not round numbers | Verify no strike is selected solely because "it's a nice number" |
| Fibonacci strikes | Strikes justified by positioning, not chart patterns | Verify no strike rationale mentions "Fibonacci" or "retracement" |
| No MM positioning logic | MM hedging flow direction cited | Verify Agent 08 output is referenced |
| No exit triggers based on flow | At least one exit trigger is microstructure-based | Verify `exit_triggers` includes at least one GEX/flow condition |

**Output**:
```
  audit_passed: bool
  gaps_remaining: list[str]        # Any V1/V2 gaps still present
  positions_vetoed: list[str]      # Positions that failed audit (returned to Tier 4)
  audit_commentary: str            # Summary for Borey
```

If `audit_passed` is false, positions are returned to Agents 22-24 with specific instructions on what microstructure justification is missing.

---

### Agent 30: Final Synthesis & Borey Briefing

**Consumes**: Agent 28 (resolved positions), Agent 29 (audit), Agent 26 (microstructure briefing)
**Produces**: The final output that goes to Discord

**Output format for Borey**:

```
=== MICROSTRUCTURE BRIEFING ===
{Agent 26 output -- 1 paragraph market structure summary}

=== POSITIONS (V3 -- Microstructure-Anchored) ===

POSITION 1: {strategy name}
  Thesis: {1 sentence}
  Legs: {strike, type, expiry for each leg}
  Entry: {condition anchored to microstructure level}
  Stop: {level anchored to gamma flip or GEX wall}
  Target: {level anchored to gamma floor/ceiling/max pain}
  Size: {% of portfolio}
  Max loss: ${amount}

  WHY THESE STRIKES:
    - Short leg at {strike} = {GEX level} -- {MM hedging creates resistance/support here}
    - Long leg at {strike} = {GEX level} -- {structural protection from positioning}

  FLOW SAYS:
    - Dealer regime: {long/short gamma} -- {implication}
    - PCR: {value} ({signal}) -- {implication}
    - 0DTE: {summary}
    - Dark pool: {summary}

  RISK FLAGS:
    - {flag 1}
    - {flag 2}

  EXIT TRIGGERS (microstructure-based):
    - If gamma flip crosses {direction}: {action}
    - If PCR moves to {level}: {action}
    - If 0DTE flow reverses: {action}

{repeat for each position}

=== AUDIT ===
V1/V2 Gap Check: {PASSED/FAILED}
{If failed: specific gaps listed}

=== CATALYST AWARENESS ===
PCE/CPI: {date} -- {how positions are prepared}
Iran ceasefire: {assessment from Agent 27}
```

---

## Agent Dependency Graph

```
Tier 1 (Data):    01-GEX  02-PCR  03-Flow  04-Levels  05-Regime
                    |   \    |  \    |         |   \       |
                    v    \   v   \   v         v    \      v
Tier 2 (Analysis): 06   07   08   09   10    11    12    13
                    |    |    |    |    |     |     |     |
                    v    v    v    v    v     v     v     v
Tier 3 (Strikes): 14   15   16   17   18    19    20    21
                    |    |    |    |    |     |     |     |
                    +----+----+----+----+-----+-----+-----+
                    |              |                |
                    v              v                v
Tier 4 (Draft):   22(bear)    23(bull)         24(vol)
                    |              |                |
                    +---------+----+----------------+
                              |
                              v
                    25(Risk Overlay)  26(Narrative)  27(Catalyst)
                              |           |              |
                              +-----------+--------------+
                              |
                              v
Tier 5 (Synth):          28(Conflict)
                              |
                              v
                          29(Audit)
                              |
                              v
                          30(Output)
```

## Execution Plan

**Wave 1** (parallel): Agents 01-05 (all independent, all data extraction)
**Wave 2** (parallel): Agents 06-13 (all depend on Tier 1, independent of each other)
**Wave 3** (parallel): Agents 14-21 (all depend on Tier 2, independent of each other)
**Wave 4** (parallel): Agents 22-24, 26, 27 (position drafters + narrative + catalyst)
**Wave 5** (sequential): Agent 25 (risk overlay on all positions)
**Wave 6** (sequential): Agent 28 (conflict resolution)
**Wave 7** (sequential): Agent 29 (V1/V2 audit)
**Wave 8** (sequential): Agent 30 (final synthesis)

Total waves: 8
Max parallel agents per wave: 8 (Waves 2 and 3)
Estimated wall-clock time: ~4-6 minutes (vs. serial: ~20 minutes)

---

## Platform Data Integration Map

Every agent that produces analysis MUST cite which platform module it consumed:

| Platform Module | File | Agents That Consume It |
|---|---|---|
| GEX Engine | `src/analysis/gex.py` | 01, 06, 07, 08, 11, 13 |
| PCR Engine | `src/analysis/pcr.py` | 02, 09 |
| Max Pain | `src/analysis/max_pain.py` | 04, 19 |
| Strike Intel | `src/analysis/strike_intel.py` | 04, 11 |
| Unusual Whales Client | `src/data/unusual_whales_client.py` | 03 |
| Polygon Client | `src/data/polygon_client.py` | 03 |
| Flow Analyzer | `src/ml/anomaly.py` | 03 |
| HMM Regime | `src/ml/regime.py` | 05 |
| LSTM Vol Forecast | `src/ml/volatility.py` | 05 |
| Feature Store | `src/ml/feature_store.py` | 02, 05 |
| FinBERT Sentiment | `src/ml/sentiment.py` | 05 |
| Combo Odds (Monte Carlo) | `src/analysis/combo_odds.py` | 22, 23, 24 |
| Commentary Engine | `src/ai/commentary.py` | 26 |
| CheddarFlow Parser | `src/discord_bot/cog_cheddarflow.py` | 03 |

---

## Known Limitations and Honest Caveats

1. **OI is T+1 data**: Open interest updates once per day from OCC. Intraday GEX levels are computed from yesterday's OI + today's gamma. This is a universal limitation -- SpotGamma, Unusual Whales, and our system all face it. The 0DTE flow data from Polygon/UW partially compensates.

2. **Dealer positioning is assumed, not observed**: We ASSUME dealers are net short options (standard market maker model). In reality, some dealers carry directional books. Our GEX convention (calls positive, puts negative) is the industry standard assumption but it is an assumption.

3. **0DTE gamma calculation has a known bug**: The platform currently returns zero GEX for 0DTE contracts because `T=0` triggers a guard clause (`src/analysis/gex.py:65-69`). The adversarial review (Agent 02 auditor) flagged this. Until fixed, 0DTE GEX analysis will use flow data from Unusual Whales as a proxy, not the GEX engine directly.

4. **Squeeze probability normalization is fragile**: The adversarial review flagged that squeeze probability varies with the number of strikes analyzed. Agents should treat squeeze_probability as ordinal (high/medium/low), not as a calibrated probability.

5. **Multiple gamma flip points**: The platform only reports the first gamma flip crossing. In rare market conditions, there can be multiple flip points. Agent 13 should note this limitation and recommend caution when net_gex_by_strike shows multiple zero crossings.

6. **PCR thresholds are not calibrated**: The boundaries (0.3, 0.7, 1.0, 1.15) are reasonable defaults but have not been backtested against SPX-specific data. Agent 09 should use percentile-based extremes from the feature store when available.

---

## What Makes V3 Different From Every Other Options Newsletter

Most options analysis (including V1/V2 of this system) starts with a chart, draws some lines, picks strikes at round numbers, and then maybe mentions VIX as an afterthought. The microstructure is invisible.

V3 inverts this. The FIRST thing computed is where the dealers are positioned. The FIRST question answered is "where does MM hedging create structural support and resistance?" Strikes are selected because the options market STRUCTURE supports them -- because gamma exposure at that strike creates a mechanical flow that aids the trade -- not because a line on a chart looked appealing.

This is what the platform was built to do. The GEX engine, PCR engine, strike intelligence module, flow analyzer, Unusual Whales integration, Polygon OPRA stream, HMM regime detection, and anomaly scoring system exist for exactly this purpose. V1/V2 ignored all of it. V3 makes it the foundation.
