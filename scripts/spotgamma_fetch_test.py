"""End-to-end SpotGamma API proof of life.

Extracts the sgToken JWT from the persistent Playwright context's localStorage,
then makes raw aiohttp calls to api.spotgamma.com with Authorization: Bearer.
Prints actual fetched values for SPX Key Levels, HIRO, and Synthetic OI.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import aiohttp

REPO_ROOT = Path(__file__).resolve().parent.parent
USER_DATA_DIR = REPO_ROOT / "data" / "spotgamma_recon_browser"

API_BASE = "https://api.spotgamma.com"

ENDPOINTS = [
    ("/home/keyLevels", "Key Levels (no params)"),
    ("/home/keyLevels?includeGammaCurve=0", "Key Levels (gammaCurve=0)"),
    ("/home/keyLevels?sym=SPX", "Key Levels (sym=SPX)"),
    ("/v6/running_hiro", "Running HIRO"),
    ("/synth_oi/v1/eh_symbols", "EH symbols (synth_oi)"),
    ("/v1/eh_symbols", "EH symbols (v1)"),
    ("/v1/me/user", "User profile"),
    ("/v1/futures/realtime", "Futures realtime"),
    ("/v3/equitiesBySyms?syms=SPX", "Equities by SPX"),
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


async def extract_jwt_and_cookies() -> tuple[str, dict[str, str]]:
    """Open persistent context, navigate to dashboard, read sgToken + all cookies for spotgamma.com."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        try:
            await page.goto("https://dashboard.spotgamma.com/", wait_until="domcontentloaded", timeout=20_000)
        except Exception:
            pass
        await asyncio.sleep(3)
        token = await page.evaluate("localStorage.getItem('sgToken')") or ""
        ck_objs = await ctx.cookies()
        cookies = {c["name"]: c["value"] for c in ck_objs if "spotgamma" in c.get("domain", "")}
        await ctx.close()
        return token, cookies


async def try_endpoint(session: aiohttp.ClientSession, url: str) -> tuple[int, int, str]:
    try:
        async with session.get(
            url, allow_redirects=False, timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            body = await resp.read()
            ct = resp.headers.get("content-type", "")
            return resp.status, len(body), ct
    except Exception as exc:
        return -1, 0, f"{type(exc).__name__}: {exc}"


async def main() -> int:
    print("Extracting sgToken JWT + cookies from persistent context...")
    try:
        token, cookies = await extract_jwt_and_cookies()
    except Exception as exc:
        print(f"ERROR: could not extract auth: {exc}", file=sys.stderr)
        return 2

    if not token:
        print("FAIL: sgToken not found in localStorage. Re-login required.", file=sys.stderr)
        return 2

    print(f"  + sgToken: {len(token)} chars, starts {token[:8]!r}")
    print(f"  + cookies: {len(cookies)} ({sorted(cookies)})\n")

    headers = {
        "User-Agent": UA,
        "Accept": "application/json, */*",
        "Authorization": f"Bearer {token}",
        "Referer": "https://dashboard.spotgamma.com/",
        "Origin": "https://dashboard.spotgamma.com",
    }
    if cookies:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())

    async with aiohttp.ClientSession(headers=headers) as session:
        print(f"Hitting {len(ENDPOINTS)} endpoints on {API_BASE} ...\n")
        results: list[tuple[str, int, int, str, str]] = []
        for path, label in ENDPOINTS:
            url = API_BASE + path
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    body = await resp.read()
                    ct = resp.headers.get("content-type", "")
                    status = resp.status
            except Exception as exc:
                status, body, ct = -1, b"", f"{type(exc).__name__}: {exc}"
            marker = "OK " if status == 200 else "   "
            print(f"  {marker}[{status:>3}] {len(body):>7}b {ct[:30]:<30}  {label} -> {path}")
            results.append((label, status, len(body), ct, body.decode("utf-8", errors="replace")))

        # Parse Key Levels for proof of life
        print("\n--- SPX Key Levels (live) ---\n")
        for label, status, size, ct, raw in results:
            if label != "Key Levels" or status != 200:
                continue
            try:
                data = json.loads(raw)
                if isinstance(data, str):
                    data = json.loads(data)
                rows = data.get("data", []) if isinstance(data, dict) else []
                if not rows:
                    print(f"  (no data rows; raw[:200]: {raw[:200]})")
                for row in rows[:3]:
                    if not isinstance(row, dict):
                        continue
                    print(f"  sym={row.get('sym')} trade_date={row.get('trade_date')}")
                    print(f"    spot (upx):           {row.get('upx')}")
                    print(f"    Call Wall:            {row.get('callwallstrike')}")
                    print(f"    Put Wall:             {row.get('putwallstrike')}")
                    print(f"    Vol Trigger (zero_g): {row.get('zero_g_strike')}")
                    print(f"    Abs Gamma:            {row.get('topabs_strike')}")
                    print(f"    SG 1d move (sig):     {row.get('sig')}")
                    print(f"    SG 5d move (sig5):    {row.get('sig5')}")
            except Exception as exc:
                print(f"  parse error: {exc}")
                print(f"  raw[:300]: {raw[:300]}")

        # Print 403 bodies (small, often diagnostic)
        print("\n--- 403 diagnostic bodies ---\n")
        for label, status, size, ct, raw in results:
            if status == 403:
                print(f"  {label}: {raw[:200]!r}")

        # Equities by SPX -- look for Key Levels fields
        print("\n--- /v3/equitiesBySyms?syms=SPX (looking for Call Wall, Put Wall, Vol Trigger) ---\n")
        for label, status, size, ct, raw in results:
            if "Equities by SPX" not in label or status != 200:
                continue
            try:
                data = json.loads(raw)
                if isinstance(data, str):
                    data = json.loads(data)
                # Look for SPX-relevant fields recursively
                def walk(obj, path=""):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            kl = k.lower()
                            if any(t in kl for t in ("wall", "trigger", "gamma", "abs_gam", "zero_g", "topabs", "upx", "sig")):
                                if not isinstance(v, (dict, list)):
                                    print(f"  {path}.{k} = {v}")
                            walk(v, f"{path}.{k}")
                    elif isinstance(obj, list) and obj:
                        if isinstance(obj[0], dict):
                            walk(obj[0], f"{path}[0]")
                walk(data)
            except Exception as exc:
                print(f"  parse error: {exc}; raw[:300]: {raw[:300]}")

        # Snapshot HIRO
        print("\n--- HIRO snapshot ---\n")
        for label, status, size, ct, raw in results:
            if label != "Running HIRO":
                continue
            if status != 200:
                print(f"  HIRO unavailable: status={status}, body[:200]={raw[:200]}")
                break
            try:
                data = json.loads(raw)
                if isinstance(data, str):
                    data = json.loads(data)
                # HIRO shape unknown; print summary
                if isinstance(data, dict):
                    keys = list(data.keys())[:8]
                    print(f"  keys: {keys}")
                    if "data" in data and isinstance(data["data"], list) and data["data"]:
                        print(f"  first data row: {json.dumps(data['data'][0], default=str)[:300]}")
                elif isinstance(data, list):
                    print(f"  list of {len(data)} items")
                    if data:
                        print(f"  first: {json.dumps(data[0], default=str)[:300]}")
            except Exception as exc:
                print(f"  parse error: {exc}; raw[:300]: {raw[:300]}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
