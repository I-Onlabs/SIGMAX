"""Minimal pandas compatibility helpers for validation tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

__all__ = ["date_range"]


def date_range(start: str, end: str, freq: str) -> List[datetime]:
    """Return a list of datetimes between ``start`` and ``end`` inclusive."""
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    if freq.upper() == "1H":
        step = timedelta(hours=1)
    elif freq.upper() == "1D":
        step = timedelta(days=1)
    else:
        raise ValueError(f"Unsupported frequency: {freq}")

    results = []
    current = start_dt
    while current <= end_dt:
        results.append(current)
        current += step
    return results
