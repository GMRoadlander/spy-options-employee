#!/usr/bin/env python3
"""Architectural lint — enforces structural invariants from the adversarial audit.

Run: python scripts/lint_architecture.py
Exit code 0 = all checks pass, 1 = violations found.

Three invariants:
1. Cogs never access _db directly (repository pattern)
2. No naive datetime.now() in src/ (timezone-aware everywhere)
3. Cogs never use getattr(self.bot, ...) (ServiceRegistry)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SRC = Path("src")
COGS = SRC / "discord_bot"

CHECKS: list[tuple[str, Path, str, re.Pattern, str]] = [
    # (name, search_path, glob, pattern, message)
    (
        "no _db access from cogs",
        COGS,
        "cog_*.py",
        re.compile(r"\._db\.|\._ensure_connected"),
        "Cog accesses _db directly. Use Store/Engine public query methods instead.",
    ),
    (
        "no naive datetime.now()",
        SRC,
        "**/*.py",
        re.compile(r"datetime\.now\(\)"),
        "Use now_et() from src.utils instead of datetime.now().",
    ),
    (
        "no getattr(self.bot, ...) in cogs",
        COGS,
        "cog_*.py",
        re.compile(r"getattr\(self\.bot,"),
        "Use self.services.x instead of getattr(self.bot, 'x', None).",
    ),
]

def main() -> int:
    violations = 0

    for name, search_path, glob_pattern, pattern, message in CHECKS:
        for filepath in search_path.rglob(glob_pattern):
            for i, line in enumerate(filepath.read_text(encoding="utf-8").splitlines(), 1):
                # Skip comments and docstrings
                stripped = line.lstrip()
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                if pattern.search(line):
                    print(f"FAIL [{name}] {filepath}:{i}: {line.strip()}")
                    print(f"     {message}")
                    violations += 1

    if violations:
        print(f"\n{violations} architectural violation(s) found.")
        return 1

    print("All architectural checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
