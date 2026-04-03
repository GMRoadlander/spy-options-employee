"""Shared utility functions used across the codebase."""

from __future__ import annotations

import zoneinfo
from datetime import datetime

from src.config import config

ET = zoneinfo.ZoneInfo(config.timezone)


def now_et() -> datetime:
    """Get the current time in Eastern Time (from config.timezone)."""
    return datetime.now(ET)


def parse_dt(iso_str: str) -> datetime:
    """Parse an ISO datetime string, making it timezone-aware (ET) if naive.

    Handles legacy naive timestamps stored before the timezone migration.
    """
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ET)
    return dt
