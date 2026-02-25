# SPX Day Trader — Roadmap

## Milestones

- SHIPPED **v1.0 MVP** — Phases 1-4 + 2.1 (shipped 2026-02-24)

## Completed Milestones

- [v1.0 SPX Day Trader MVP](milestones/v1.0-ROADMAP.md) (Phases 1-4 + 2.1) — SHIPPED 2026-02-24

<details>
<summary>v1.0 MVP (Phases 1-4 + 2.1) — SHIPPED 2026-02-24</summary>

- [x] Phase 1: MVP Data & Signals (2/2 plans) — completed 2026-02-21
- [x] Phase 2: Strategy Research Engine (3/3 plans) — completed 2026-02-22
- [x] Phase 2.1: Code Review Fixes (1/1 plans) — completed 2026-02-22
- [x] Phase 3: ML Intelligence Layer (9/9 plans) — completed 2026-02-23
- [x] Phase 4: Paper Trading & Validation (8/8 plans) — completed 2026-02-25

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|-----------|
| 1. MVP Data & Signals | v1.0 | 2/2 | Complete | 2026-02-21 |
| 2. Strategy Research Engine | v1.0 | 3/3 | Complete | 2026-02-22 |
| 2.1. Code Review Fixes | v1.0 | 1/1 | Complete | 2026-02-22 |
| 3. ML Intelligence Layer | v1.0 | 9/9 | Complete | 2026-02-23 |
| 4. Paper Trading & Validation | v1.0 | 8/8 | Complete | 2026-02-25 |

## Borey's Daily Workflow (Target State)

| Activity | Frequency | Time |
|----------|-----------|------|
| Read morning briefing | Daily | 1 min |
| Read/rate alerts during market | Real-time | 30 sec each |
| Read daily summary | Daily | 2 min |
| Weekly strategy review | Weekly | 10 min |
| Monthly deep review + new ideas | Monthly | 20 min |
| Define new strategy (NL or YAML) | As needed | 5 min |
| Review backtest results | As needed | 5 min |
| Review paper trading performance | As needed | 5 min |

**Total daily**: ~5 minutes. All via Discord — never touches code.

## Key Constraints

- **LLMs in research/signal layer, NOT execution path** — latency makes LLM-in-the-loop execution impossible for intraday
- **Anti-overfitting pipeline is NON-NEGOTIABLE** — 90%+ of backtested strategies fail in production; WFA + CPCV + DSR + Monte Carlo is the minimum
- **HMM regime detection is highest-ROI ML model** — prevents catastrophic strategy-regime mismatches
- **SPX European/cash-settled** — eliminates early exercise, assignment, pin risk complexity
- **Strategy templates in YAML** — Borey defines, not a custom DSL
- **Advisory + paper trading permanently** — no live order execution; the system researches and validates, Borey decides

## Cost Structure

| Phase | Monthly Cost | Key Adds |
|-------|-------------|----------|
| Phase 1 (MVP) | ~$18 | Tastytrade (free), Sonnet (~$6), DO droplet ($12) |
| Phase 2 (Research) | ~$150 | +ORATS ($99), scale droplet ($24), +Sonnet ($25) |
| Phase 3 (ML) | ~$400 | +Polygon ($199), +Unusual Whales ($99), scale droplet ($48), +AI ($50) |
| Phase 4 (Paper) — Steady State | ~$400 | +AI ($50) |

---

*Roadmap created: 2026-02-21*
*Restructured: 2026-02-21 — identity shift from alert bot to trading research platform*
*Restructured: 2026-02-23 — removed Phase 5 (autonomous trading), system is permanent research + paper trading platform*
*v1.0 archived: 2026-02-24 — milestone complete, archived to milestones/v1.0-ROADMAP.md*
