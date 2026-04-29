"""SpotGamma Day-1 network reconnaissance.

Opens a real (headed) Chromium browser, attempts auto-login with the
placeholder selectors from src/data/spotgamma_auth.py, and captures every
JSON XHR/Fetch response made by the SpotGamma dashboard SPA.

Outputs:
  - docs/spotgamma_endpoints.md   structured endpoint inventory
  - data/spotgamma_recon/<safe>.json   raw response samples (git-ignored)

Usage::

    .venv/Scripts/python.exe scripts/spotgamma_recon.py

Requires SPOTGAMMA_EMAIL + SPOTGAMMA_PASSWORD in .env. Credentials are read
inside this process via python-dotenv and are never logged or printed.

Workflow:
  1. Script opens browser, navigates to spotgamma.com/login.
  2. Tries to fill email/password using placeholder selectors.
  3. If auto-fill fails (selectors don't match), you log in MANUALLY in the
     visible browser window.
  4. Once you reach the dashboard, navigate around: Key Levels, HIRO,
     Equity Hub, TRACE, Founder's Notes. The script silently captures
     every JSON response in the background.
  5. Press Ctrl+C in the terminal (or close the browser) when done.
  6. Script writes the inventory + samples and exits.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import signal
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

OUT_DIR = REPO_ROOT / "data" / "spotgamma_recon"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR = REPO_ROOT / "docs"
DOCS_DIR.mkdir(exist_ok=True)
REPORT_PATH = DOCS_DIR / "spotgamma_endpoints.md"

LOGIN_URL = "https://spotgamma.com/login/"
DASHBOARD_HINT = "/dashboard"

EMAIL_SELECTOR = 'input[name="email"], input[type="email"], #email'
PASSWORD_SELECTOR = 'input[name="password"], input[type="password"], #password'
SUBMIT_SELECTOR = 'button[type="submit"], input[type="submit"], #login-submit'

MAX_BODY_SAMPLE_BYTES = 4096

captured: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
shutdown_event: asyncio.Event | None = None


def _safe_name(url: str) -> str:
    parts = urlsplit(url)
    base = (parts.path or "_root").strip("/").replace("/", "_") or "_root"
    if parts.query:
        base += "__" + re.sub(r"[^A-Za-z0-9_.-]", "_", parts.query)[:40]
    base = re.sub(r"[^A-Za-z0-9_.-]", "_", base)
    return base[:120] or "endpoint"


def _is_jsonish(content_type: str | None) -> bool:
    if not content_type:
        return False
    ct = content_type.lower()
    return "json" in ct or "javascript" in ct


async def _on_response(response: Any) -> None:
    url = response.url
    parts = urlsplit(url)
    if "spotgamma" not in (parts.netloc or "").lower():
        return

    headers = await response.all_headers()
    content_type = headers.get("content-type", "")
    if not _is_jsonish(content_type):
        return

    try:
        body = await response.body()
    except Exception:
        body = b""

    sample = body[:MAX_BODY_SAMPLE_BYTES]
    try:
        parsed = json.loads(sample.decode("utf-8", errors="replace"))
        sample_for_disk: Any = parsed
    except Exception:
        sample_for_disk = sample.decode("utf-8", errors="replace")

    key = f"{response.request.method} {parts.scheme}://{parts.netloc}{parts.path}"
    if key in captured:
        captured[key]["count"] += 1
        return

    safe = _safe_name(url)
    sample_path: Path | None = OUT_DIR / f"{safe}.json"
    try:
        with open(sample_path, "w", encoding="utf-8") as f:
            json.dump(sample_for_disk, f, indent=2, default=str)
    except Exception as exc:
        sample_path = None
        print(f"  ! could not write sample for {key}: {exc}", file=sys.stderr)

    sanitized_req_headers: dict[str, str] = {}
    try:
        req_headers = await response.request.all_headers()
    except Exception:
        req_headers = {}
    for k, v in req_headers.items():
        if k.lower() in {"authorization", "cookie", "x-auth-token"}:
            sanitized_req_headers[k] = "<redacted>"
        else:
            sanitized_req_headers[k] = v

    captured[key] = {
        "method": response.request.method,
        "url": url,
        "status": response.status,
        "content_type": content_type,
        "request_headers": sanitized_req_headers,
        "response_size_bytes": len(body),
        "sample_path": str(sample_path.relative_to(REPO_ROOT)) if sample_path else None,
        "count": 1,
        "first_seen": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    print(f"  [{response.status}] {key}")


def _write_report() -> None:
    if not captured:
        print("\nNo SpotGamma JSON responses captured. Did you log in and navigate the dashboard?")
        return

    lines: list[str] = []
    lines.append("# SpotGamma -- Captured Endpoints (Day-1 Recon)\n")
    lines.append(f"_Captured: {datetime.now(timezone.utc).isoformat(timespec='seconds')}_  ")
    lines.append(f"_Total unique endpoints: {len(captured)}_\n")
    lines.append("Sensitive headers (Authorization / Cookie / X-Auth-Token) are redacted.\n")
    lines.append("Raw response samples (truncated to 4KB) live in `data/spotgamma_recon/`.\n")

    for key, meta in captured.items():
        lines.append(f"## `{key}`\n")
        lines.append(f"- **status:** {meta['status']}")
        lines.append(f"- **content-type:** `{meta['content_type']}`")
        lines.append(f"- **size:** {meta['response_size_bytes']} bytes")
        lines.append(f"- **seen:** {meta['count']} time(s), first at {meta['first_seen']}")
        if meta["sample_path"]:
            lines.append(f"- **sample:** `{meta['sample_path']}`")
        lines.append("")
        lines.append("**Request headers (sanitized):**\n")
        lines.append("```")
        for k, v in meta["request_headers"].items():
            lines.append(f"{k}: {v}")
        lines.append("```\n")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n=> wrote {REPORT_PATH.relative_to(REPO_ROOT)} ({len(captured)} endpoints)")
    print(f"=> raw samples in {OUT_DIR.relative_to(REPO_ROOT)}/")


async def _try_auto_login(page: Any, email: str, password: str) -> bool:
    """Best-effort auto-login. Returns True on success."""
    try:
        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
    except Exception as exc:
        print(f"  ! navigation to {LOGIN_URL} failed: {exc}")
        return False

    try:
        await page.fill(EMAIL_SELECTOR, email, timeout=5_000)
        await page.fill(PASSWORD_SELECTOR, password, timeout=5_000)
        await page.click(SUBMIT_SELECTOR, timeout=5_000)
    except Exception as exc:
        print(f"  ! placeholder selectors did not match the live login form: {type(exc).__name__}")
        print("    -> please complete the login MANUALLY in the open browser window.")
        return False

    try:
        await page.wait_for_url(f"**{DASHBOARD_HINT}*", timeout=20_000)
        return True
    except Exception:
        print("  ! login submitted but did not redirect to /dashboard.")
        print("    -> if a 2FA / captcha appeared, complete it manually.")
        return False


async def main() -> int:
    global shutdown_event
    shutdown_event = asyncio.Event()

    email = os.getenv("SPOTGAMMA_EMAIL", "")
    password = os.getenv("SPOTGAMMA_PASSWORD", "")
    if not email or not password:
        print("ERROR: SPOTGAMMA_EMAIL or SPOTGAMMA_PASSWORD missing from .env", file=sys.stderr)
        print("Add these to .env (file is git-ignored) and re-run.", file=sys.stderr)
        return 2

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print(
            "ERROR: playwright not installed. "
            "Run: pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        return 2

    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, lambda: shutdown_event.set())  # type: ignore[union-attr]

    print("Launching Chromium (headed)...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(REPO_ROOT / "data" / "spotgamma_recon_browser"),
            headless=False,
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        page.on("response", lambda r: asyncio.create_task(_on_response(r)))

        print(f"\nAttempting auto-login to {LOGIN_URL} ...")
        ok = await _try_auto_login(page, email, password)
        if ok:
            print("  + auto-login succeeded; you're on the dashboard.")
        else:
            print("\n>>> Please log in MANUALLY in the browser window now.")

        print("\n>>> Now click around the dashboard:")
        print("    Key Levels, HIRO, Equity Hub, TRACE, Founder's Notes.")
        print(">>> Each panel triggers XHR calls that this script captures silently.")
        print(">>> When done, close the browser window OR press Ctrl+C in this terminal.")
        print()

        async def _wait_for_close() -> None:
            try:
                await page.wait_for_event("close", timeout=0)
            except Exception:
                pass
            shutdown_event.set()  # type: ignore[union-attr]

        watcher = asyncio.create_task(_wait_for_close())
        try:
            await shutdown_event.wait()  # type: ignore[union-attr]
        except KeyboardInterrupt:
            pass
        finally:
            watcher.cancel()
            try:
                await context.close()
            except Exception:
                pass

    _write_report()
    return 0


if __name__ == "__main__":
    try:
        rc = asyncio.run(main())
    except KeyboardInterrupt:
        rc = 0
        _write_report()
    sys.exit(rc)
