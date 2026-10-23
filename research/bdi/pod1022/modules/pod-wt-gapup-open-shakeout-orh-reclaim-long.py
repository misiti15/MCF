"""pod-wt-gapup-open-shakeout-orh-reclaim-long - Ross Cameron 'let it shake out' ORB: a gap-up stock trades below its
open in the first 20 minutes, then breaks the opening-range high (LONG).

Source: Warrior Trading trade review 'opening range breakout' (ROKU: wait for the first 5-10 minutes to shake out, then
play the ORB with clear strength).
URL: https://www.warriortrading.com/trade-review-opening-range-breakout/

VARIANT of pod-smb-gapdown-opening-print-reclaim-long (gap DOWN, reclaim of the open print). Stated changes: gap-UP
names, and the trigger is the opening-range high after a shakeout under the open, not the open print. Distinct from
CWT07 gap-and-go (gap held with no shakeout).

Rules (plain English), 5-minute bars, values from bars up to and including the decision bar i:
  1. gap >= +2% and rvol_day (cumulative volume / its 20-session same-time mean) >= 2 at bar i.
  2. Shakeout: the session low 09:30-09:50 (09:30-09:45 low from the 1-minute bars, and the 09:50 bar's low) is
     <= open - 0.15 x ATR14_daily, and the gap is not fully filled (low of day so far > PDC).
  3. OR high = the 09:30-10:00 high; at bar i the close is > session VWAP.
  4. Bar i is the first 5-minute close above the OR high (bars from 10:05), with volume >= 1.3 x the mean volume of
     the 6 bars before it.
  5. The shakeout low is >= 0.5 x ATR14_daily below the OR high (enough range).
  Entry: the next bar's open, filled at bar i's close by the scorer. Window: signal bar close 10:05-11:00.
  Stop (GEOM S): max(shakeout low, OR midpoint) - the OR midpoint is the primary stop and is the max whenever the
  shakeout low is inside the OR (always here). Target: entry + 2R, else flat 15:55. Modelling note: the source's trail
  on a 5-minute close below VWAP is not modelled (one stop / target per trade). No tweak used.
Costs per config/default.yaml (applied by the scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r32_util as Z  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1005, 1100)
TARGET_R = 2.0
CONTEXT = []
LAYERS = ["gap >= 2, rvol_day >= 2", "09:30-09:50 low <= open - 0.15 ATR, LOD > PDC", "close > VWAP",
          "first close above the 09:30-10:00 high, vol >= 1.3 x prior 6 bars", "shakeout low <= ORH - 0.5 ATR",
          "stop max(shakeout low, OR mid), 2R", "10:05-11:00"]
_ST = {}


def mask(df) -> np.ndarray:
    n = len(df)
    _ST.clear()
    if not n:
        return np.zeros(0, bool)
    B = Z.base(df)
    bb = Z.bars(df)
    d = Z.map_day(df, ["or_l", "dr_h", "dr_l"])
    k = Z.key(df)
    c, tod, atr = B["c"], B["tod"], B["atr"]
    # low of the 09:50 bar broadcast to its symbol-day (used only on rows >= 10:05)
    g = np.full(int(k.max()) + 1, np.nan)
    sel = tod == 950
    g[k[sel]] = B["l"][sel]
    l950 = g[k]
    shk = np.fmin(d["or_l"], l950)
    shk = np.where(np.isfinite(d["or_l"]) & np.isfinite(l950), shk, np.nan)
    orh, orm = d["dr_h"], (d["dr_h"] + d["dr_l"]) / 2.0
    with np.errstate(invalid="ignore"):
        above = (c > orh) & (tod >= 1005)
        cnt = np.zeros(n, np.int64)
        run = 0
        st = Z.start(k)
        for i in range(n):
            if st[i]:
                run = 0
            cnt[i] = run
            if above[i]:
                run += 1
        m = above & (cnt == 0)
        m &= (Z.f(df, "gap") >= 2.0) & (bb["rvc"] >= 2.0)
        m &= shk <= B["opn"] - 0.15 * atr
        m &= B["lod"] > B["pc"]
        m &= c > B["vwap"]
        m &= bb["v"] >= 1.3 * bb["v6"]
        m &= shk <= orh - 0.5 * atr
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    stop = np.fmax(shk, orm)
    tgt = c + TARGET_R * (c - stop)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _g(f, i, j):
    if id(f) not in _ST:
        mask(f)
    return float(_ST[id(f)][j][i])


def stop_price(f, i):
    return _g(f, i, 0)


def target_price(f, i, stop):
    return _g(f, i, 1)
