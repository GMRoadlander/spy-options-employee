# SpotGamma Integration: Security & Credential Review

**Reviewer:** Boris Cherney (adversarial)
**Date:** 2026-04-06
**Scope:** Credential management, webhook security, email parsing risks, data integrity
**Verdict:** The codebase has a surprisingly decent security posture for a personal project, but there are real gaps that become critical when you add SpotGamma -- especially email parsing and the webhook endpoint.

---

## 1. Email Access (Founder's Notes via IMAP)

### 1.1 Credential Storage Risk: HIGH

If you add IMAP credentials to parse Founder's Notes, you're adding **the most dangerous credential class in this codebase**. Every other credential here is an API key with limited scope (read market data, post to Discord). An email credential grants access to an entire inbox.

**Current credential pattern:** All secrets live in `.env`, loaded via `python-dotenv` in `src/config.py` (line 7). The `.gitignore` correctly excludes `.env` and `.env.*`. The `Config` dataclass reads `os.getenv()` with empty-string defaults. This is the correct pattern -- use it for SpotGamma.

**Gmail-specific concerns:**
- **App passwords** are the simplest path but they bypass 2FA, which defeats the purpose of having 2FA. If someone gets the `.env` file, they have full email access.
- **OAuth2** is better (scoped, revocable) but requires client_id/client_secret/refresh_token storage. That's 3 credentials instead of 1. The refresh token is effectively permanent access.
- **Recommendation:** Dedicated Gmail account used ONLY for SpotGamma Founder's Notes. Never use Borey's or Gil's personal email. If it gets compromised, the blast radius is one throwaway inbox.

### 1.2 HTML Parsing Injection Risk: MEDIUM-HIGH

Parsing arbitrary email HTML is a well-known attack surface. SpotGamma emails are presumably benign, but:

- **XSS via stored HTML:** If you store raw HTML in SQLite and later render it in Discord embeds, malicious content could leak. Discord's embed API strips HTML, but if you ever add a web dashboard, this becomes XSS.
- **SSRF via HTML parsing:** If you use `lxml` or `BeautifulSoup` with an XML parser that resolves external entities, a crafted email could trigger SSRF. Use `html.parser` or `lxml` with `resolve_entities=False`.
- **Email header injection:** If your IMAP query uses unsanitized input to construct search criteria, it's injectable. Always use the IMAP library's parameterized search, never string concatenation.
- **Image/attachment references:** SpotGamma emails may contain `<img src="...">` tags or attachments. Never follow these URLs server-side -- that's an SSRF vector.

**Recommendation:** Strip HTML to plain text immediately upon receipt using `bleach.clean()` or `html2text`. Parse numeric levels from the plain text. Never store or process the raw HTML.

### 1.3 Specific Guidance

```
# In .env (add these for email parsing)
SPOTGAMMA_EMAIL_IMAP_HOST=imap.gmail.com
SPOTGAMMA_EMAIL_ADDRESS=spotgamma-reader@gmail.com  # DEDICATED account
SPOTGAMMA_EMAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx        # App password
# OR for OAuth2:
SPOTGAMMA_EMAIL_CLIENT_ID=...
SPOTGAMMA_EMAIL_CLIENT_SECRET=...
SPOTGAMMA_EMAIL_REFRESH_TOKEN=...
```

---

## 2. API Key Storage Audit

### 2.1 Current Credential Inventory

| Credential | Config Field | Auth Method | Risk if Leaked |
|---|---|---|---|
| Discord bot token | `discord_token` | Bot token | Full bot control, channel access |
| Claude API key | `claude_api_key` | Bearer header | Cost exposure (API calls) |
| Tastytrade | `tastytrade_client_secret` + `refresh_token` | OAuth2 session | Read-only market data (no trading) |
| Tradier | `tradier_token` | Bearer header | Sandbox only -- no real risk |
| ORATS | `orats_api_key` | Query param | Read-only, rate-limited |
| Polygon.io | `polygon_api_key` | Query param `apiKey=` | Read-only market data |
| Unusual Whales | `unusual_whales_api_key` | Bearer header | Read-only flow data |
| Webhook secret | `webhook_secret` | HMAC comparison | Spoofed webhook alerts |

### 2.2 Findings

**GOOD:**
- All credentials in `.env`, loaded via `os.getenv()` with empty-string defaults
- `.gitignore` covers `.env` and `.env.*`
- No hardcoded secrets anywhere in source code
- Credential logging is properly suppressed (e.g., `polygon_client.py` line 163 filters `apiKey` from debug logs; `orats_client.py` line 145 filters `token`)
- Graceful degradation when keys are missing (all clients return empty data, not crashes)

**CONCERNING:**
- **Polygon API key in URL query params** (`polygon_client.py` lines 158, 254): API keys in URLs get logged by proxies, CDNs, and browser history. Less concerning here since this is server-to-server, but it's Polygon's design, not yours.
- **No credential rotation mechanism**: If any key is compromised, it's a manual `.env` edit. Consider adding a `/rotate-key` Discord command that invalidates and refreshes (for OAuth2 sources).
- **Docker `env_file: .env`** (`docker-compose.yml` line 6): The `.env` file is mounted into the container. If the container is compromised, all credentials are exposed. This is standard practice but worth noting.

### 2.3 SpotGamma Key Addition

Adding `SPOTGAMMA_API_KEY` or `SPOTGAMMA_HIRO_TOKEN` follows the existing pattern perfectly. No architectural changes needed. Add it to `Config` the same way:

```python
spotgamma_api_key: str = os.getenv("SPOTGAMMA_API_KEY", "")
```

---

## 3. Webhook Endpoint Security

### 3.1 Current Implementation: WEAK

The webhook at `src/webhook/tradingview.py` has a **critical architectural weakness**:

```python
# Line 55-56
if config.webhook_secret:
    if not hmac.compare_digest(x_webhook_secret or "", config.webhook_secret)
```

This is NOT HMAC authentication. This is **shared-secret comparison**. The client sends the secret verbatim in the `X-Webhook-Secret` header, and the server compares it. Real HMAC authentication would:

1. Client signs the request body with the secret: `HMAC-SHA256(body, secret)`
2. Client sends the signature in a header
3. Server recomputes the signature from the received body and compares

What you have is a **password in a header**. It's better than nothing, but:
- If TLS terminates at a proxy, the secret is visible in plaintext headers
- Replay attacks are trivial -- capture one request, replay it forever
- No request body integrity -- an attacker can modify the body if they have the secret

### 3.2 Blast Radius of Fake Webhook Data

If someone spoofs the webhook:

1. **Fake alert goes to Discord** via `cog_webhooks.py` -- the `alert_queue` has no validation of alert content beyond Pydantic model parsing (`extra="allow"` makes this very permissive)
2. **Signal gets logged** to `signal_log` table (line 62-73 of `cog_webhooks.py`) with `signal_type="webhook"` and `strength=0.6` hardcoded
3. **No direct path to paper trading** from webhooks currently -- the paper engine is driven by `ShadowModeManager` reading strategy templates, not webhook alerts. This is actually a good security boundary.
4. **But:** If you route SpotGamma levels through the webhook, and those levels feed into the ML feature store or strategy entry conditions, then fake levels DO cascade into paper trades.

### 3.3 Network Exposure: HIGH

```python
# src/main.py line 60
host="0.0.0.0",
port=config.webhook_port,
```

The FastAPI server binds to `0.0.0.0:8000`. On Gil's local PC, this means:
- Any device on the local network can hit the webhook
- If port 8000 is forwarded (for TradingView), it's internet-exposed
- The `/health` endpoint returns `{"status": "ok"}` -- a probe target

**docker-compose.yml line 8:** `ports: "8000:8000"` maps the container port to the host. Since this runs on Gil's PC now (not DigitalOcean), the exposure depends on his router/firewall config.

### 3.4 Recommendations

1. **Implement real HMAC-SHA256 body signing** for any SpotGamma webhook integration:
   ```python
   expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
   if not hmac.compare_digest(expected, received_signature):
       raise HTTPException(401)
   ```
2. **Add request timestamp validation** -- reject requests older than 5 minutes to prevent replay
3. **Bind to `127.0.0.1`** if the webhook only needs local access (TradingView alerts can go through a reverse proxy)
4. **Rate limit the webhook endpoint** -- FastAPI + slowapi or a simple counter. Currently unlimited.
5. **Add IP allowlisting** if SpotGamma provides known webhook source IPs

---

## 4. Dashboard Scraping

### 4.1 Credential Exposure: HIGH

If anyone proposes Selenium/Playwright scraping of the SpotGamma dashboard:

- **Session cookies stored in memory or on disk** -- these are equivalent to full account credentials. A crash dump, debug log, or temp file could expose them.
- **Browser profile persistence** -- Selenium/Playwright can persist profiles with cookies, localStorage, and credentials. These are unencrypted on disk.
- **Screenshots in logs** -- Debug screenshots (common in scraping code) may capture PII or account details
- **$299/mo subscription at risk** -- SpotGamma TOS almost certainly prohibit automated scraping. Account termination loses the subscription.

### 4.2 Technical Fragility

- DOM structure changes break scrapers without warning
- SpotGamma can add bot detection (Cloudflare, reCAPTCHA) at any time
- Session expiry and re-authentication logic is error-prone
- Headless browser memory usage (~200-500MB per Chrome instance) on Gil's PC

### 4.3 Verdict

**Do not scrape.** Every other integration path is superior:
- HIRO API: structured, authenticated, reliable
- Email parsing: semi-structured, automated delivery, no session management
- TradingView webhook: already proven in codebase

---

## 5. Data Integrity & Poisoning

### 5.1 Attack Surface Map

SpotGamma levels (key_levels, call_wall, put_wall, vol_trigger, etc.) would enter the system through one of:

```
Email/API/Webhook --> SpotGammaClient --> FeatureStore/DB --> ML Models --> Paper Trading
```

### 5.2 Feature Store Injection: LOW (if parameterized)

The `FeatureStore.save_features()` in `src/ml/feature_store.py` (lines 70-127) constructs SQL dynamically but uses parameterized queries (`?` placeholders). The column names are validated against `FEATURE_COLUMNS` whitelist (line 93-95):

```python
provided = {
    k: v for k, v in features.items()
    if k in FEATURE_COLUMNS and v is not None
}
```

This is correct -- column names are from a hardcoded whitelist, values use parameterized binding. Safe against SQL injection.

The `columns_str` and `update_clause` in the INSERT statement (line 119) are built from `FEATURE_COLUMNS` keys, not user input.

**SpotGamma concern:** If you add SpotGamma-derived features (e.g., `sg_call_wall`, `sg_put_wall`), you'd need to add them to `FEATURE_COLUMNS`. This is the correct pattern.

### 5.3 Poisoned Level Cascade: MEDIUM

If an attacker feeds fake SpotGamma levels:

1. **Anomaly detector** (`src/ml/anomaly.py`) could be trained on poisoned data. The IF/LOF models would learn corrupted distributions. The circuit breaker (`anomaly_halt_threshold = 0.8`) might not trigger if poisoned data is internally consistent.
2. **Regime model** (`src/ml/regime.py`) -- HMM state assignments could shift if vol_trigger or key levels distort the feature inputs. The model might misclassify the current regime (risk-on vs risk-off), leading to oversized or undersized positions.
3. **Paper trading impact** -- Risk limits (`src/risk/config.py`) provide a hard floor: max position size, max portfolio delta, max daily loss. Even with poisoned features, the risk manager would cap losses at 5% daily / 10% drawdown. **This is a meaningful defense.**
4. **VIX circuit breaker** -- Independent of SpotGamma data. Even if levels are poisoned, VIX > 35 halts everything. Good isolation.

### 5.4 ML Model Integrity

The serialization + HMAC pattern in `regime.py` and `anomaly.py` is well-implemented in structure, but:

**The HMAC keys are hardcoded in source code:**
- `regime.py` line 258: `_HMAC_KEY = b"regime-model-integrity-v1"`
- `anomaly.py` line 480: `_HMAC_KEY = b"flow-anomaly-model-integrity-v1"`

The comment says "not secret, but ensures integrity." This is incorrect security reasoning. If an attacker can read the source code (which is in the git repo), they can forge valid HMAC signatures for arbitrary serialized payloads. The HMAC key should come from `.env`, not source code. As-is, the HMAC provides protection against accidental corruption only, not adversarial tampering.

Also: the deserialization uses `# noqa: S301` suppression on both `regime.py` line 324 and `anomaly.py` line 540. Deserialization of untrusted data enables arbitrary code execution. The HMAC check is supposed to prevent loading tampered files, but with the key in source code, this is security theater against a determined attacker.

### 5.5 Recommendations for SpotGamma Data Integrity

1. **Validate SpotGamma levels on ingestion**: key levels should be within a reasonable range of current SPX price (e.g., +/-10%). A call wall at 0 or 99999 is obviously poisoned.
2. **Rate-of-change guards**: If the vol_trigger jumps by more than 5% between readings, flag it as suspicious and use the previous value.
3. **Cross-reference**: Compare SpotGamma call_wall with your own max-pain/GEX calculations. Large divergences should trigger warnings.
4. **Staleness detection**: If SpotGamma data is older than 30 minutes during market hours, mark features as stale. The system already has staleness detection patterns in `src/ai/reasoning.py`.
5. **Move HMAC keys to `.env`**: `REGIME_MODEL_HMAC_KEY` and `ANOMALY_MODEL_HMAC_KEY` should not be in source code.

---

## 6. Summary of Findings

| Finding | Severity | Status |
|---|---|---|
| Webhook uses shared-secret, not HMAC body signing | HIGH | Existing vulnerability |
| FastAPI binds to `0.0.0.0` on local PC | HIGH | Existing -- needs review of firewall/port forwarding |
| Model HMAC keys hardcoded in source | MEDIUM | Existing -- ineffective against adversarial tampering |
| No rate limiting on webhook endpoint | MEDIUM | Existing |
| Email parsing adds largest-scope credential | HIGH | New risk from SpotGamma |
| Email HTML parsing is SSRF/injection surface | MEDIUM-HIGH | New risk from SpotGamma |
| Poisoned SpotGamma levels cascade to paper trades | MEDIUM | New risk, mitigated by risk limits |
| Dashboard scraping credential exposure | HIGH | Theoretical -- do not implement |
| API keys in Polygon URL query params | LOW | Existing, Polygon's design |
| No credential rotation mechanism | LOW | Existing |

### Priority Actions Before SpotGamma Integration

1. **Fix webhook HMAC** -- implement real body signing, not shared-secret comparison
2. **Use dedicated email account** if going the email parsing route
3. **Strip HTML immediately** on email ingestion -- parse numbers from plain text only
4. **Add SpotGamma level validation** -- range checks, rate-of-change guards
5. **Consider binding to `127.0.0.1`** and using a reverse proxy with its own auth layer
6. **Move model HMAC keys to `.env`** -- or better, use a proper signing key derived from a secret

---

*This review covers code as of commit `48cd5f0`. Paths are relative to project root.*
