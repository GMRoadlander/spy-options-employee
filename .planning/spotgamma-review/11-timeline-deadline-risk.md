# 11 -- Timeline & Deadline Risk: Will This Actually Ship?

**Reviewer:** Boris Cherney (adversarial PM)
**Date:** 2026-04-06
**Hard deadline:** Last week of April 2026 (~21 calendar days, ~15 business days)
**Verdict:** The proposed scope WILL NOT ship by Day 1. Not close. But a useful subset can.

---

## 1. The HIRO Blocker -- Unknown API Shape Is a Schedule Killer

### The Problem

You are proposing to spend 5-7 days building an integration against an API you have never seen. That is not engineering -- that is gambling. The estimate of "5-7 days" assumes:

- The API exists and is documented
- It returns structured JSON (not rendered HTML widgets)
- It has authentication you can automate (not browser-session-only)
- It supports historical queries (not just live dashboard state)
- It exposes the specific HIRO metrics you need (not aggregate-only views)
- Rate limits allow polling at the frequency you need

Every one of those assumptions could be wrong. If even two are wrong, you are looking at 10-15 days of reverse-engineering, not 5-7 days of integration.

### What Actually Happens

1. You subscribe last week of April
2. You spend Day 1-2 logging into the dashboard, opening browser DevTools, sniffing network requests
3. You discover HIRO data comes through a WebSocket that requires a browser session cookie that expires every 4 hours
4. You spend Day 3-5 building a Selenium/Playwright wrapper to maintain sessions
5. You discover the WebSocket pushes binary protobuf, not JSON
6. Day 6-8: decode the protobuf schema by hand
7. Day 9: you have something fragile that breaks when SpotGamma deploys a frontend update
8. Day 10-12: you realize this approach is unmaintainable

Total wasted time: 2+ weeks. Meanwhile the $299/mo clock is ticking and you're extracting zero value.

### De-Risk Strategy

**Before subscribing** (this week, April 6-10):
- Email SpotGamma support: "Do you offer a REST/WebSocket API for HIRO data? Is there programmatic access?" Get a yes/no in writing.
- Search their documentation, community forums, Discord for "API" mentions.
- Check if any third-party wrappers exist (GitHub search: "spotgamma api", "spotgamma hiro python").
- If the answer is "no API, dashboard only": KILL this work item entirely. Do not build a brittle scraper. Redirect effort to the manual-input fallback and email parser.

**If API exists:** Get docs before Day 1 so you can stub out the client and write tests against mock responses before the subscription starts.

**If no API:** Accept it. The Founder's Notes email + manual Borey input covers 80% of the value. HIRO is a nice-to-have, not a must-have.

---

## 2. Email Parsing Scope Creep -- This Is NOT 4-5 Days

### The Stated Estimate

"4-5 days to parse Founder's Notes email."

### The Actual Task List

| # | Task | Realistic Time |
|---|------|---------------|
| 1 | Set up Gmail API OAuth2 (client ID, consent screen, token storage, refresh logic) | 4-6 hours |
| 2 | Build email fetcher (search by sender, date, subject pattern) | 2-3 hours |
| 3 | Handle HTML vs plain text multipart | 2-3 hours |
| 4 | Parse the template: extract key levels (gamma flip, call wall, put wall, vol trigger, etc.) | 4-6 hours |
| 5 | Handle template variations (SpotGamma WILL change their format -- they always do) | 3-4 hours |
| 6 | Handle edge cases: no email (holidays, outages), duplicate emails, emails arriving late | 3-4 hours |
| 7 | Handle data validation (is 5800 a reasonable SPX level or did parsing break?) | 2-3 hours |
| 8 | Map parsed data to your existing feature store schema (new columns in daily_features) | 3-4 hours |
| 9 | DB schema migration (ALTER TABLE daily_features ADD COLUMN for each SpotGamma field) | 2-3 hours |
| 10 | Write the SpotGamma data client following existing patterns (PolygonClient, UnusualWhalesClient) | 3-4 hours |
| 11 | Wire into bot.py with graceful degradation (your existing pattern: try/except/ImportError) | 2-3 hours |
| 12 | Config additions (SPOTGAMMA_EMAIL_SENDER, etc. in config.py) | 1 hour |
| 13 | Unit tests for parser (20-30 tests minimum: happy path, edge cases, template variations) | 4-6 hours |
| 14 | Integration tests with mocked Gmail responses | 3-4 hours |
| 15 | Gmail API quirks you haven't thought of yet (encoding, threading, labels, pagination) | 3-4 hours |
| 16 | Discord cog for `/spotgamma` command | 3-4 hours |
| 17 | Embed formatting for SpotGamma levels in Discord | 2-3 hours |

**Subtotal: 42-62 hours of focused work = 6-8 business days for a senior developer working on nothing else.**

And that's assuming you understand the email template perfectly before you start. You won't. You'll need at least 3-5 sample emails to build a robust parser, and you can't get those until the subscription starts.

### The Gmail MCP Angle

You have `mcp__claude_ai_Gmail__gmail_*` tools available. This helps with prototyping -- you can read real emails interactively. But production code cannot depend on MCP tools. You still need a proper Gmail API client or IMAP integration in your Python service.

### Realistic Estimate

**7-10 business days** including tests, edge cases, and the inevitable "oh, their template has a different format on OPEX weeks" discovery.

---

## 3. The 1503 Test Constraint -- Testing Is a Tax on Every Feature

### Current State

- 1503 tests across 62 test files
- Average: ~24 tests per module
- Follows a strict pattern: every src module has a corresponding test module
- Pattern established: new data clients (polygon, unusual_whales) each have ~25-50 tests
- CheddarFlow parser alone has 23 tests

### What SpotGamma Integration Adds

| New Module | Estimated Tests | Rationale |
|------------|----------------|-----------|
| `test_spotgamma_client.py` (email parser) | 25-35 | Match polygon/unusual_whales pattern; cover template variations |
| `test_spotgamma_hiro.py` (HIRO client, if API exists) | 20-30 | Match existing API client test patterns |
| `test_cog_spotgamma.py` (Discord cog) | 15-25 | Match cog_ml (47 tests) / cog_paper (36 tests) pattern |
| Feature store additions | 5-10 | New columns, new feature paths |
| Integration/E2E tests | 10-15 | SpotGamma data flowing through full pipeline |
| **Total new tests** | **75-115** | |

### Time Cost of Tests

At the project's demonstrated pace (~12 min for 55 E2E tests in Phase 4-8), simple tests go fast. But these tests need:

- Mocked Gmail API responses (multi-part MIME messages with realistic HTML)
- Mocked HIRO API responses (whatever shape that turns out to be)
- Template variation fixtures (at least 5 different email formats)
- Feature store schema migration verification

**Testing alone: 2-3 business days.** This is not optional -- the project has a strict "all tests passing" gate.

### Regression Risk

Every new feature touches:
- `config.py` (new env vars)
- `bot.py` (new initialization)
- `src/db/store.py` (new schema)
- `src/ml/feature_store.py` (new columns)

These are the most-imported modules in the codebase. A bad change breaks everything. You must run the full 1503-test suite after every significant commit. On this codebase, that's probably 30-60 seconds per run, but the review/fix cycle adds up.

---

## 4. Borey's 5 Min/Day Constraint -- Training Is a Hidden Dependency

### The Problem

Borey spends ~5 min/day via Discord. The proposed integration adds:

- New `/spotgamma` slash command with subcommands
- New levels showing up in analysis output
- New terminology (gamma flip vs. your existing gamma flip -- are they the same calculation?)
- Manual input fallback (Borey types SpotGamma levels into Discord when email parsing fails)

### Training Timeline

| Phase | When | Borey's Time | Risk |
|-------|------|-------------|------|
| Explain new commands | Before launch | 10-15 min (one-time) | Low |
| First week of real data | Week 1 | 10-15 min/day (questions, "this doesn't look right") | **High** |
| Manual input fallback | Ongoing | 2-3 min/day when email parsing fails | Medium |
| "Why are SpotGamma levels different from our GEX?" | Week 1-2 | ??? | **High** |

The last point is critical: your system already computes GEX, gamma flip, call wall, put wall. SpotGamma computes their own versions of the same levels using proprietary methodology. **They WILL disagree.** Borey will ask "which one do I trust?" and you need an answer before launch, not after.

### Recommendation

- Write a one-page comparison document: "Our GEX vs SpotGamma GEX -- what's different and why"
- Pre-record a 3-minute screen share walkthrough of the new commands
- Do NOT plan on Borey being available for debugging during Week 1 -- he has his own trading to do

---

## 5. The REAL Timeline -- With Honest Buffers

### Optimistic Plan (What You're Telling Yourself)

| Item | Estimated Days |
|------|---------------|
| Email parser | 4-5 |
| TradingView webhook bridge | 2-3 |
| HIRO API integration | 5-7 |
| Manual input fallback | < 1 |
| DB + feature store | 1-2 |
| Discord cog | 1-2 |
| Testing | 2-3 |
| Borey training | 0.5 |
| **Total** | **16-23 days** |

You have 15 business days. This plan is already over budget on the optimistic end, and the optimistic end NEVER happens.

### Realistic Plan (What Will Actually Happen)

| Item | Realistic Days | Buffer Factor | Notes |
|------|---------------|--------------|-------|
| Email parser + Gmail integration | 7-10 | 1.5-2x | Template unknowns, Gmail quirks, encoding issues |
| TradingView webhook bridge | 3-4 | 1.5x | Existing FastAPI pattern helps, but new alert types need design |
| HIRO API integration | 0 OR 12-18 | Binary | Either API exists (12-18 days) or it doesn't (0 days, killed) |
| Manual input fallback | 1-2 | 2x | Seems simple but needs validation, storage, and "what if Borey makes a typo?" |
| DB schema migration | 1-2 | 1x | Idempotent pattern is established, low risk |
| Feature store updates | 1-2 | 1.5x | New columns, plumbing to reasoning engine |
| Discord cog + embeds | 2-3 | 1.5x | Match existing quality bar of cog_ml (47 tests) |
| Testing (all new tests) | 3-4 | 1.5x | Mock construction is the bottleneck |
| Integration testing with real data | 3-5 | N/A | CANNOT START until subscription is live |
| Code review + bug fixes | 2-3 | N/A | Always takes longer than you think |
| Borey training + feedback loop | 1-2 | N/A | Cannot parallelize with development |
| **Total (without HIRO)** | **24-37 business days** | | **6-9 weeks** |
| **Total (with HIRO)** | **36-55 business days** | | **9-14 weeks** |

**Without HIRO, this is a 6-9 week project. You have 3 weeks. Even the "without HIRO" scope doesn't ship on time.**

---

## 6. Phased Delivery Plan -- What Provably Ships When

### Day 1 (Subscription Starts, ~April 27)

**What ships:** Manual input only.

| Deliverable | Status | Confidence |
|-------------|--------|------------|
| `/spotgamma set` slash command (Borey manually types levels) | Buildable by April 27 | 95% |
| DB schema for SpotGamma levels | Buildable | 95% |
| Basic embed showing SpotGamma levels alongside existing GEX | Buildable | 90% |
| Config additions for SpotGamma env vars | Buildable | 99% |
| 15-20 unit tests | Buildable | 90% |

**Time to build:** 3-4 business days (April 7-10)
**Time to test:** 1-2 business days (April 11-14)
**Buffer:** April 15-25 for bugs, review, and Borey training

This is the MINIMUM VIABLE SpotGamma integration. Borey reads the Founder's Notes email himself (he's doing this already if he's subscribing), types the key levels into Discord, and the system stores and displays them. Not glamorous. But it ships.

**Critical advantage:** This approach lets you start collecting real SpotGamma data into your DB on Day 1. When the email parser ships later, you can backfill, but you're not losing data.

### Week 2-3 (May 4-15)

**What ships:** Email parser (semi-automated).

| Deliverable | Confidence |
|-------------|------------|
| Gmail API integration (fetch Founder's Notes) | 80% |
| HTML/text parser for known template format | 75% |
| Automated daily pull with fallback to manual input | 70% |
| 25-35 parser tests with real email fixtures | 70% |
| `/spotgamma auto` command to trigger/check email parsing | 75% |

**Why lower confidence:** You need 3-5 real emails to build a robust parser. If the first email arrives April 28, you're building against 2-3 samples in Week 2. Template variations you haven't seen will break things.

### Month 1 (May 15-31)

**What ships:** Stabilized email parser + TradingView bridge.

| Deliverable | Confidence |
|-------------|------------|
| Email parser handling template variations (OPEX weeks, holidays) | 65% |
| TradingView SpotGamma alert bridge | 70% |
| Feature store integration (SpotGamma levels feed into ML pipeline) | 60% |
| Full test suite (75+ new tests) | 70% |

### Month 2+ (June)

**What maybe ships:** HIRO integration, IF an API exists.

| Deliverable | Confidence |
|-------------|------------|
| HIRO client (if API exists and is documented) | 30% |
| Real-time SpotGamma level updates in Discord | 25% |
| Full integration with reasoning engine | 40% |

---

## 7. The "Test Without Subscription" Problem

### The Core Issue

You cannot integration-test with real SpotGamma data until the subscription starts. So the first few days of the subscription are TESTING, not production use. At $299/mo, that's ~$10/day wasted on testing.

### Mitigation Strategy

**Pre-subscription (April 7-25):**

1. **Build against mocks.** Create `tests/fixtures/spotgamma/` with:
   - `founder_notes_sample_1.html` (fabricated from public SpotGamma screenshots/marketing materials)
   - `founder_notes_sample_2.html` (different format for robustness)
   - `spotgamma_levels_sample.json` (expected parsed output)

2. **Build the manual input path first.** This needs ZERO SpotGamma data to test. It's a Discord slash command that stores numbers. You can test it today.

3. **Build the Gmail integration against your own test emails.** Send yourself emails that mimic the SpotGamma format. This tests the Gmail API plumbing without needing real SpotGamma emails.

4. **Stub the SpotGamma client with an ABC.** Following your existing pattern (TastytradeClient, PolygonClient), create `SpotGammaClient` as an abstract interface. Implement `MockSpotGammaClient` for tests, `EmailSpotGammaClient` for production. Later, `HiroSpotGammaClient` if the API exists.

**Day 1 of subscription (April 27):**

1. Forward the first Founder's Notes email to yourself
2. Save the raw HTML/text to `tests/fixtures/spotgamma/`
3. Run your parser against the real email -- see what breaks
4. Fix parser, add the real email as a test fixture, re-run full suite
5. By Day 2-3, the email parser should handle the real format

**Cost of this approach:** 1-2 days of subscription time spent on parser debugging. $20 vs $10/day for the "just wing it" approach that wastes a week.

### What You Cannot Pre-Test

- SpotGamma's email delivery timing (do they send at 8:00 AM ET? 9:00 AM? It varies?)
- Template changes (they will change the format at some point -- you need graceful degradation)
- Whether their levels match your own calculations (this is a Borey judgment call)

---

## Summary Table

| Risk | Severity | Mitigation | Owner |
|------|----------|------------|-------|
| HIRO API doesn't exist | **CRITICAL** | Email SpotGamma support THIS WEEK. Kill if no API. | Gil |
| Email parser takes 2x estimated time | HIGH | Ship manual input first. Email parser is Week 2-3. | Dev |
| Template variations break parser | HIGH | Graceful degradation + fallback to manual. Collect fixtures aggressively. | Dev |
| SpotGamma levels conflict with existing GEX | HIGH | Write comparison doc before launch. Borey decides which to trust. | Gil + Borey |
| Test suite regression | MEDIUM | Run full 1503 tests after every significant commit. CI/CD if not already. | Dev |
| Borey overwhelmed by new commands | MEDIUM | Pre-record walkthrough. One new command at a time, not all at once. | Gil |
| $299/mo wasted on testing | LOW | Build manual input + mocks before sub starts. Minimize real-data debugging. | Dev |

---

## Bottom Line

**Full scope by Day 1: NO. Not remotely.**

**What CAN ship by Day 1:**
1. `/spotgamma set <level> <value>` -- manual input (3-4 days to build)
2. DB schema for SpotGamma levels (comes with #1)
3. Basic embed showing levels (comes with #1)
4. 15-20 tests (comes with #1)

**What ships Week 2-3:** Semi-automated email parser (if you start building it April 7)

**What ships Month 1:** Stabilized parser + TradingView bridge

**What MIGHT ship Month 2:** HIRO integration (only if API exists, which you should determine THIS WEEK)

The single most important action item RIGHT NOW is: **email SpotGamma support and ask about API access.** Everything else is downstream of that answer. Do it today. Do not wait until the subscription starts.

---

*Reviewed against codebase: 1503 tests, 62 test files, 89 source files, 15 feature columns in feature store, 23+ DB tables, established patterns for data clients (Polygon, Unusual Whales, Tastytrade, CBOE, Tradier, ORATS) and Discord cogs (10 loaded). The codebase is mature and well-structured, which helps -- but maturity means every new integration must meet the existing quality bar, which takes time.*
