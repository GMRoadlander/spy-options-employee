"""Probe what auth mechanism the SpotGamma dashboard SPA actually uses.

Re-opens the persistent Playwright context, navigates to dashboard, dumps:
  - All localStorage keys + value lengths (no values printed)
  - First N XHR requests with full URL + sanitized headers
  - The actual Authorization header (just type/format, not the token)

Output:
  - prints summary to stdout
  - writes docs/spotgamma_endpoints.md  (URL inventory + sanitized headers)
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
USER_DATA_DIR = REPO_ROOT / "data" / "spotgamma_recon_browser"
DOCS = REPO_ROOT / "docs"
DOCS.mkdir(exist_ok=True)
REPORT = DOCS / "spotgamma_endpoints.md"

DASHBOARD = "https://dashboard.spotgamma.com/"
WAIT_AFTER_LOAD_SECONDS = 12

xhrs: "OrderedDict[str, dict[str, Any]]" = OrderedDict()


def _sanitize(headers: dict[str, str]) -> dict[str, str]:
    SENS = {"authorization", "cookie", "x-auth-token", "x-csrf-token"}
    out: dict[str, str] = {}
    for k, v in headers.items():
        kl = k.lower()
        if kl in SENS:
            if kl == "authorization" and v:
                scheme = v.split(" ", 1)[0]
                out[k] = f"<{scheme} ... ({len(v)} chars)>"
            else:
                out[k] = f"<redacted ({len(v)} chars)>"
        else:
            out[k] = v
    return out


def _on_request(req: Any) -> None:
    if req.resource_type not in {"xhr", "fetch"}:
        return
    parts = urlsplit(req.url)
    if "spotgamma" not in (parts.netloc or "").lower():
        return
    key = f"{req.method} {parts.scheme}://{parts.netloc}{parts.path}"
    if key in xhrs:
        xhrs[key]["count"] += 1
        return
    xhrs[key] = {
        "method": req.method,
        "url": req.url,
        "host": parts.netloc,
        "path": parts.path,
        "query": parts.query,
        "request_headers": _sanitize(dict(req.headers)),
        "count": 1,
    }


async def main() -> int:
    if not USER_DATA_DIR.exists():
        print(f"ERROR: persistent context not found at {USER_DATA_DIR}", file=sys.stderr)
        return 2

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: playwright not installed", file=sys.stderr)
        return 2

    print("Launching Chromium against persistent context (headless)...")
    async with async_playwright() as p:
        try:
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=str(USER_DATA_DIR),
                headless=True,
                viewport={"width": 1440, "height": 900},
                args=["--disable-blink-features=AutomationControlled"],
            )
        except Exception as exc:
            print(f"ERROR: could not launch persistent context: {exc}", file=sys.stderr)
            print("(Is the previous browser still running? Close it.)", file=sys.stderr)
            return 2

        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        page.on("request", _on_request)

        print(f"Navigating to {DASHBOARD} ...")
        try:
            await page.goto(DASHBOARD, wait_until="networkidle", timeout=30_000)
        except Exception as exc:
            print(f"  ! navigation timed out ({exc}). Continuing -- may have partial data.")

        print(f"Final URL: {page.url}")
        print(f"Waiting {WAIT_AFTER_LOAD_SECONDS}s for dashboard XHRs to fire ...")
        await asyncio.sleep(WAIT_AFTER_LOAD_SECONDS)

        try:
            ls = await page.evaluate(
                "Object.fromEntries(Object.entries(localStorage).map(([k,v]) => [k, v?.length || 0]))"
            )
            print(f"\nlocalStorage keys ({len(ls)}):")
            for k, v in sorted(ls.items()):
                print(f"  {k:30s} -> {v} chars")
        except Exception as exc:
            print(f"  ! localStorage read failed: {exc}")
            ls = {}

        likely_token_keys = [k for k in ls.keys() if any(
            tok in k.lower() for tok in ("token", "jwt", "auth", "session", "bearer", "id")
        )]
        token_preview: dict[str, str] = {}
        for k in likely_token_keys:
            try:
                v = await page.evaluate(f"localStorage.getItem({json.dumps(k)})")
                if v:
                    token_preview[k] = f"len={len(v)} starts={v[:8]!r}"
            except Exception:
                pass
        if token_preview:
            print("\nLikely token-bearing localStorage keys:")
            for k, prev in token_preview.items():
                print(f"  {k:30s} {prev}")

        await ctx.close()

    print(f"\nCaptured {len(xhrs)} unique XHR/fetch requests.")
    if xhrs:
        print("\nFirst 10 endpoints:")
        for key, meta in list(xhrs.items())[:10]:
            print(f"  {key}")
            for hk, hv in meta["request_headers"].items():
                if hk.lower() in {"authorization", "cookie"}:
                    print(f"    {hk}: {hv}")

        lines = [
            "# SpotGamma -- Endpoint Inventory (auth probe)\n",
            f"_Captured: {datetime.now(timezone.utc).isoformat(timespec='seconds')}_  ",
            f"_Total: {len(xhrs)} unique endpoints_\n",
        ]
        for key, meta in xhrs.items():
            lines.append(f"## `{key}`\n")
            lines.append(f"- **count:** {meta['count']}")
            if meta["query"]:
                lines.append(f"- **query:** `{meta['query']}`")
            lines.append("")
            lines.append("```")
            for hk, hv in meta["request_headers"].items():
                lines.append(f"{hk}: {hv}")
            lines.append("```\n")
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n=> wrote {REPORT.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
