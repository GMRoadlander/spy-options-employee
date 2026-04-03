"""Shared utility functions used across the codebase."""

from __future__ import annotations

import zoneinfo
from datetime import datetime

from src.config import config

ET = zoneinfo.ZoneInfo(config.timezone)


def now_et() -> datetime:
    """Get the current time in Eastern Time (from config.timezone)."""
    return datetime.now(ET)
