"""pod-cal-preholiday-index-vwap-long - Pre-holiday session: buy the morning VWAP pullback in index / sector ETFs,
hold to the close (LONG).

Source: pre-holiday effect literature (Ariel 1990, 'High stock returns before holidays'; Lakonishok and Smidt 1988,
'Are seasonal anomalies real? A ninety-year perspective'), a calendar edge often cited by systematic-trading podcast
guests. NOT verified against a specific Better System Trader / Top Traders Unplugged episode (web blocked this run).
URL: https://doi.org/10.1111/j.1540-6261.1990.tb05110.x
New: no holiday entry in the backlog, config or bdi notes.

Rules (plain English, LONG):
  Date gate: the last full session before an NYSE full-day market holiday (hard-coded NYSE calendar 2024-2027 below,
  a schedule published in advance, so no lookahead). Skip a session that is itself a half day, and skip one whose next
  session (after the holiday) is a half day (e.g. the Wednesday before Thanksgiving).
  Symbols: SPY, QQQ, IWM, DIA, XLK, XLF, XLI, XLY, XLV, XLP, XLU, XLE, SMH.
  1. Bar close 10:00-12:30.
  2. vwapDistPct between -0.15 and +0.25 (at or just above VWAP).
  3. rsi5 <= 40 (a small pullback).
  4. spy_fo >= -0.30.
  Entry: close of the first qualifying bar. Stop 1R = 0.25 x atr_d, no target (GEOM hold), flat 15:55.
  Costs per config/default.yaml (applied by the scorer). No tweak made. Few events (about 9 holidays a year), judged
  pooled across the ETFs.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "hold"
WINDOW = (1000, 1230)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLI", "XLY", "XLV", "XLP", "XLU", "XLE", "SMH"]
CONTEXT = ["spy_fo"]
LAYERS = ["last full session before an NYSE full-day holiday (no half days either side)",
          "vwapDistPct in [-0.15, 0.25]", "rsi5 <= 40", "spy_fo >= -0.30", "10:00-12:30", "hold 1R stop, flat 15:55"]

HOLIDAYS = ["2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27", "2024-06-19", "2024-07-04",
            "2024-09-02", "2024-11-28", "2024-12-25",
            "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26", "2025-06-19",
            "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
            "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
            "2026-09-07", "2026-11-26", "2026-12-25", "2027-01-01"]
HALF_DAYS = ["2024-07-03", "2024-11-29", "2024-12-24", "2025-07-03", "2025-11-28", "2025-12-24",
             "2026-11-27", "2026-12-24"]


def _gate_dates():
    hol = set(pd.to_datetime(HOLIDAYS).date)
    half = set(pd.to_datetime(HALF_DAYS).date)
    days = [d for d in pd.bdate_range("2024-01-01", "2027-01-31").date if d not in hol]
    out = set()
    for i in range(len(days) - 1):
        d, nxt = days[i], days[i + 1]
        cal = pd.bdate_range(d, nxt).date[1:-1]          # weekdays strictly between this and the next session
        if not any(x in hol for x in cal):
            continue                                     # not followed by a full-day holiday
        if d in half or nxt in half:
            continue
        out.add(d)
    return out


GATE = _gate_dates()


def mask(df) -> np.ndarray:
    if not len(df) or "spy_fo" not in df:
        return np.zeros(len(df), dtype=bool)
    tod = df["tod"].to_numpy(float)
    dt = pd.to_datetime(df["date"]).dt.date.to_numpy()
    with np.errstate(invalid="ignore"):
        vd = df["vwapDistPct"].to_numpy(float)
        m = np.isin(dt, list(GATE))
        m &= (vd >= -0.15) & (vd <= 0.25)
        m &= df["rsi5"].to_numpy(float) <= 40
        m &= df["spy_fo"].to_numpy(float) >= -0.30
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        m &= df["symbol"].astype(str).isin(SYMBOLS).to_numpy()
    return np.asarray(m, dtype=bool)
