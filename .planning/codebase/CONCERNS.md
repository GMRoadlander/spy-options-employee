# Concerns

## High Severity

### Unsafe env var conversion — `src/config.py:14-16`
`int(os.getenv(..., "0"))` without error handling. Non-numeric value crashes app at startup.

### Hardcoded channel ID defaults — `src/config.py:14-16`
Default "0" silently accepted. No validation that channel IDs are non-zero at config load time.

### Missing JSON parsing error handling — `src/data/cboe_client.py:126`
`await resp.json(content_type=None)` outside try/except. Malformed JSON from CBOE crashes mid-analysis.

### No API response structure validation — `src/data/tradier_client.py:147-148`
Response format changes would cause silent parsing failures. No schema validation.

### Hardcoded model version — `src/config.py:20`
`claude_model = "claude-haiku-4-5-20251001"` not configurable via env var.

### Hardcoded API URLs — `src/config.py:27-28`
CBOE and Tradier URLs hardcoded. Endpoint changes require code modification.

### Naive datetime usage — Multiple files
`datetime.now()` used in db/store.py and data clients instead of timezone-aware datetimes. Scheduler uses `_now_et()` correctly but persistence layer does not.

### Division by zero in PCR — `src/analysis/pcr.py:120-133`
Zero call volume produces infinity PCR. Downstream code treating infinity as normal ratio will misbehave.

## Medium Severity

### No graceful shutdown — `src/bot.py:93-113`
No SIGTERM handler. Container shutdown may leave database inconsistent.

### No health check endpoint — Project-wide
No `/health` or `/status` for container orchestration. Can't detect broken bot.

### Database optional without warning — `src/bot.py:47-57`
Store import failure silently sets `store=None`. Alerts lose cooldown enforcement without user knowing.

### matplotlib memory leak risk — `src/discord_bot/charts.py:66-80`
Figures not always closed on error path. Should use try/finally.

### Bare except clause — `src/ai/commentary.py:191`
`except Exception:` catches all exceptions including KeyboardInterrupt in async code.

### No connection pooling limits — `src/data/cboe_client.py:82-88`
aiohttp sessions created without explicit connection limits.

### Missing input validation — `src/analysis/gex.py:61-91`
No validation that strike prices > 0 before GEX processing.

### Spot price accepted when <= 0 — `src/data/cboe_client.py:158-160`
Only warns if spot_price <= 0, doesn't reject the chain. Analysis produces garbage results.

### Silent stale data fallback — `src/data/__init__.py:99-102`
If all expirations are past, uses most recent past expiry without alerting. GEX on expired contracts is meaningless.

### API token in logs — `src/data/tradier_client.py:40`
Bearer token in Authorization header could appear in debug/error logs.

### Missing .env documentation — `.env.template`
Template shows placeholders but doesn't document expected formats or what happens with invalid values.

## Low Severity

### No dependency lock file — Project root
`>=` pins without lock file. Builds not reproducible.

### No pytest in requirements — `requirements.txt`
Test framework not in any requirements file. Dev dependencies undocumented.

### No linting/formatting config — Project-wide
No .flake8, pyproject.toml [tool.black], or .isort.cfg. Style enforced by convention only.

### Magic numbers in config — `src/config.py`
Risk-free rate (0.05), squeeze threshold (0.3), OI shift threshold (0.10) undocumented.

### Type ignore comments — `src/bot.py:34`
`None  # type: ignore[assignment]` used instead of fixing type annotations.

### No startup connectivity check — `src/bot.py:37-78`
Bot doesn't validate API connectivity on startup. Fails silently if CBOE is down.

### Cache not persistent — `src/data/data_manager.py:43-45`
In-memory cache lost on restart. No cache warming.

---

## Summary

| Severity | Count |
|----------|-------|
| High | 8 |
| Medium | 11 |
| Low | 7 |
| **Total** | **26** |

## Recommended Immediate Actions

1. Add JSON error handling in CBOE client
2. Replace naive `datetime.now()` with timezone-aware alternatives
3. Add environment variable validation at startup
4. Add SIGTERM handler for graceful shutdown
5. Make Claude model configurable via env var

---
*Generated: 2026-02-21*
