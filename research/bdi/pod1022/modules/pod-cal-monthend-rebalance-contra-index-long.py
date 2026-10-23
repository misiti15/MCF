"""pod-cal-monthend-rebalance-contra-index-long - Month-end rebalancing flow: in the last two sessions of the month,
an afternoon contrarian trade on index ETFs against the month-to-date move (LONG side, after a down month; the SHORT
side is pod-cal-monthend-rebalance-contra-index-short.py).

Source: pension / balanced-fund month-end rebalancing flow (e.g. Harvey, Mazzoleni, Melone et al., 'The Unintended
Consequences of Rebalancing', 2025), a recurring theme on Top Traders Unplugged / Systematic Investor. Not verified
against a specific episode (web blocked this run).
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5122748
New: the backlog 'rebalanc' hits are portfolio-rebalance housekeeping, not a flow setup.

Rules (plain English):
  Date gate: the last 2 trading days of the month (NYSE calendar hard-coded below).
  MTD = SPY's prior close vs the last close of the previous month, from the SPY daily closes (research/history2y
  lib.daily(), the same daily bars as data/cache_hist; point in time: prior close only). When the previous month-end
  close is not in the open table (the locked block), MTD is NaN and the day is skipped.
  Symbols: SPY, QQQ, IWM, DIA.
  LONG: (1) MTD <= -3.0%; (2) bar close 13:30-15:00; (3) spy_fo <= -0.20 (entering on today's weakness); (4) rsi5 <= 40.
  SHORT: (1) MTD >= +4.0%; (2) bar close 13:30-15:00; (3) spy_fo >= +0.20; (4) rsi5 >= 60.
  Entry: bar close. Stop 1R = 0.25 x atr_d, no target (GEOM hold), flat 15:55. Events are scarce; the event count
  is reported with the result. Costs per config/default.yaml (applied by the scorer). No tweak made.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "hold"
WINDOW = (1330, 1500)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = ["spy_fo"]
LAYERS = ["last 2 trading days of the month", "SPY MTD (prior close) <= -3% (long) / >= +4% (short)",
          "spy_fo <= -0.20 (long) / >= +0.20 (short)", "rsi5 <= 40 (long) / >= 60 (short)", "13:30-15:00",
          "hold 1R stop, flat 15:55"]

HOLIDAYS = ["2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27", "2024-06-19", "2024-07-04",
            "2024-09-02", "2024-11-28", "2024-12-25",
            "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26", "2025-06-19",
            "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
            "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
            "2026-09-07", "2026-11-26", "2026-12-25", "2027-01-01"]
_CACHE = {}


def _gate_mtd():
    """{date: MTD %} for the last 2 trading days of each month; MTD from SPY's prior completed close only."""
    if "g" in _CACHE:
        return _CACHE["g"]
    hol = set(pd.to_datetime(HOLIDAYS).date)
    days = pd.Series([d for d in pd.bdate_range("2024-01-01", "2027-01-31").date if d not in hol])
    ym = days.map(lambda d: (d.year, d.month))
    last2 = set(days[days.groupby(ym).cumcount(ascending=False) <= 1])
    p = str(Path(__file__).resolve().parents[3] / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    d = lib.daily()
    s = d[d["symbol"].astype(str) == "SPY"][["date", "close"]].copy()
    s["date"] = pd.to_datetime(s["date"]).dt.date
    s = s.sort_values("date").set_index("date")["close"]
    allday = list(days)
    pos = {x: i for i, x in enumerate(allday)}
    out = {}
    for x in last2:
        i = pos[x]
        prev = allday[i - 1]                                    # prior trading day (completed)
        pm_end = [y for y in allday[:i] if (y.year, y.month) < (x.year, x.month)]
        if not pm_end:
            continue
        pm = pm_end[-1]                                         # last trading day of the previous month
        if prev in s.index and pm in s.index:
            out[x] = (s[prev] / s[pm] - 1) * 100
    _CACHE["g"] = out
    return out


def mask(df) -> np.ndarray:
    if not len(df) or "spy_fo" not in df:
        return np.zeros(len(df), dtype=bool)
    g = _gate_mtd()
    f = lambda k: df[k].to_numpy(float)
    tod = f("tod")
    dt = pd.to_datetime(df["date"]).dt.date
    mtd = dt.map(g).astype(float).to_numpy()
    with np.errstate(invalid="ignore"):
        if SIDE == "long":
            m = (mtd <= -3.0) & (f("spy_fo") <= -0.20) & (f("rsi5") <= 40)
        else:
            m = (mtd >= 4.0) & (f("spy_fo") >= 0.20) & (f("rsi5") >= 60)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        m &= df["symbol"].astype(str).isin(SYMBOLS).to_numpy()
    return np.asarray(m, dtype=bool)
