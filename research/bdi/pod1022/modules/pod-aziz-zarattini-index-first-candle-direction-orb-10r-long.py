"""pod-aziz-zarattini-index-first-candle-direction-orb-10r-long - Aziz-Zarattini index ORB: trade only in the
direction of the first 30-minute candle on QQQ / SPY, stop at the OR low, 10R target or the close (LONG).

Source: Aziz & Zarattini, 'Can Day Trading Really Be Profitable?' (SSRN 4416622; QQQ / TQQQ 5-minute ORB, trade in the
direction of the first candle, 10R target, end-of-day exit).
URL: https://en.wikipedia.org/wiki/Andrew_Aziz

VARIANT of orb5 / t2-orb15 (single-stock ORBs). Stated changes: index ETFs only, a first-candle direction gate, a
10R-or-close exit, long only. The 30-minute OR is used because the scorer frames start at 09:50 (the paper uses 5 min).

Rules (plain English), values from bars up to and including the decision bar:
  1. Symbol QQQ or SPY (no TQQQ / SPXL mirror; not in the frame universe).
  2. The 09:30-10:00 candle (open = 09:30 print, close = the 10:00 close) is green and |close - open| >= 0.25 x the
     OR range (no doji).
  3. The OR range (09:30-10:00 high - low) <= 1.2 x its median over the 20 prior sessions.
  4. Entry: the FIRST 5-minute close above the OR high on bars closing 10:05-12:00; entry at that close.
  Skip FOMC statement days and CPI release days. One trade per day (the scorer's first bar per symbol-day).
  Stop (GEOM S): the OR low (the paper's rule). Target: entry + 10 x (entry - stop), else flat 15:55.
  The paper's ATR stop variant (entry - 0.10 x ATR14 daily) is NOT scored here. No tweak used.
Costs per config/default.yaml (applied by the scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r32_util as Z  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1005, 1200)
SYMBOLS = ["QQQ", "SPY"]
TARGET_R = 10.0
CONTEXT = []
LAYERS = ["QQQ / SPY", "09:30-10:00 candle green, body >= 0.25 OR range", "OR range <= 1.2 x 20-day median",
          "first close above OR high 10:05-12:00", "skip FOMC / CPI", "stop OR low, target 10R, else 15:55"]
_ST = {}


def mask(df) -> np.ndarray:
    n = len(df)
    _ST.clear()
    if not n:
        return np.zeros(0, bool)
    d = Z.map_day(df, ["o935", "dr_h", "dr_l", "c1000", "orw_med20"])
    c, tod = Z.f(df, "close"), df["tod"].to_numpy(np.int64)
    k = Z.key(df)
    o, hh, ll, cc, med = d["o935"], d["dr_h"], d["dr_l"], d["c1000"], d["orw_med20"]
    rng = hh - ll
    ds = df["date"].astype(str).to_numpy()
    with np.errstate(invalid="ignore"):
        m = np.isin(df["symbol"].astype(str).to_numpy(), SYMBOLS)
        m &= (cc > o) & (np.abs(cc - o) >= 0.25 * rng) & (rng > 0)
        m &= rng <= 1.2 * med
        m &= ~np.isin(ds, Z.FOMC + Z.CPI)
        above = (c > hh) & (tod >= 1005)
        # first close above the OR high: no earlier bar (>= 10:05) of the same day closed above it
        cnt = np.zeros(n, np.int64)
        run = 0
        st = Z.start(k)
        for i in range(n):
            if st[i]:
                run = 0
            cnt[i] = run
            if above[i]:
                run += 1
        m &= above & (cnt == 0)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = ll
    return np.asarray(m, bool)


def stop_price(f, i):
    if id(f) not in _ST:
        mask(f)
    return float(_ST[id(f)][i])


def target_price(f, i, stop):
    px = float(f["close"].iloc[i])
    return px + TARGET_R * (px - stop)
