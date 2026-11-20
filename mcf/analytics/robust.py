"""Robustness figures for promotion / demotion / review tables (owner WW-CLUSTER 2026-11-20, research/whatworks_1120).

Every review that shows "avg R w/o best day" also shows:
  - the day-clustered t (t of the per-day mean R: mean of the daily means over their standard error), so a record made
    of a few correlated sessions is not read as many independent trades;
  - "avg R w/o top 2 days": avg R per trade with the setup's two best sessions (by total R) left out.

Pure Python (no pandas) so the dashboard post, blueprint and footrace code can all share it.
Educational only - not financial advice.
"""
from __future__ import annotations

import math
from typing import Iterable


def day_t(day_means: Iterable[float]) -> float:
    """Day-clustered t: mean of the per-day mean R over its standard error (0 with <= 2 days or no spread)."""
    x = [float(v) for v in day_means]
    n = len(x)
    if n <= 2:
        return 0.0
    m = sum(x) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1))
    return 0.0 if not sd > 0 else m / (sd / math.sqrt(n))


def by_day(daily: Iterable) -> dict[str, list]:
    """daily rows [date, trades, total R, ...] (several accounts may repeat a date) -> {date: [trades, total R]}."""
    out: dict[str, list] = {}
    for row in daily or []:
        d, c, r = row[0], row[1], row[2]
        a = out.setdefault(str(d), [0, 0.0])
        a[0] += int(c or 0)
        a[1] += float(r or 0.0)
    return out


def wo_top_days(days: dict[str, list], k: int = 2) -> float | None:
    """Avg R per trade without the `k` best sessions by total R. None when fewer than k + 1 sessions or no trades left."""
    if len(days) <= k:
        return None
    top = sorted(days.items(), key=lambda kv: (-kv[1][1], kv[0]))[:k]
    n = sum(v[0] for v in days.values()) - sum(v[0] for _, v in top)
    tot = sum(v[1] for v in days.values()) - sum(v[1] for _, v in top)
    return tot / n if n > 0 else None


def day_t_daily(days: dict[str, list]) -> float | None:
    """Day-clustered t from {date: [trades, total R]} (sessions with 0 trades skipped); None with <= 2 sessions."""
    means = [v[1] / v[0] for v in days.values() if v[0]]
    return day_t(means) if len(means) > 2 else None
