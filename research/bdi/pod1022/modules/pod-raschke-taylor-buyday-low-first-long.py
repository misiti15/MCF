"""pod-raschke-taylor-buyday-low-first-long - Taylor 'buy day' (Raschke): the low is made early after a sell-short
day, then a late open / VWAP reclaim is held to the close (LONG).

Source: Linda Raschke on George Douglass Taylor's Book Method three-day cycle (buy day / sell day / sell-short day);
SMB Training 'The Taylor Rhythm'; LBR 3-day cycle notes.
URL: https://www.smbtraining.com/blog/the-taylor-rhythm

VARIANT of CWT14 failed-PDL-break long and pod-smb-gapdown-opening-print-reclaim-long. Stated change: no gap or PDL
undercut is needed; the gate is Taylor's cycle (today is a 'buy day' after a sell-short day), entry comes late (11:00+)
after the low is set early, and the exit is the close.
Rules (plain English):
  1. Cycle: D-1 closed below its open and in the bottom 35% of its range, and C[D-1] - C[D-3] < 0.
  2. D-1 close > daily SMA50 (completed days; skip downtrend names).
  3. The low of day was printed before 10:30 (the LOD as of the 10:30 bar) and has not been broken since.
  4. Trigger: a 5-minute close above both today's open and the session VWAP at 11:00 or later, with the close in the
     upper half of the day's range so far.
  Entry: trigger close, 11:00-14:00 ET, one per symbol-day. Stop (GEOM S): LOD - 0.05 x atr_d; skip when risk >
  0.8 x atr_d. Exit: flat 15:55 (core; the optional D-1-high target is not used).
  Universe: adv20 >= $50M (index / sector ETFs pass it).
Harness notes (pre-declared): daily values from lib.daily() (completed days). No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r27_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1400)
MIN_ADV = 50e6
CONTEXT = []
LAYERS = ["D-1 red, close in bottom 35% of range, C1 < C3", "D-1 close > SMA50", "LOD set by 10:30 and unbroken",
          "close > open and VWAP, upper half of day range", "11:00-14:00", "stop LOD - 0.05 ATR (risk <= 0.8 ATR), hold to 15:55"]
_ST = {}


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n:
        return np.zeros(0, bool)
    k = U.key(df)
    b = U.base(df)
    D = U.map_daily(df, k, ["o1", "h1", "l1", "c1", "c3", "sma501"])
    c, atr, lod, hod, tod = b["c"], b["atr"], b["lod"], b["hod"], b["tod"]
    # LOD as of the 10:30 bar close, broadcast to the day (used only on rows with tod >= 1100)
    g = np.full(int(k.max()) + 1, np.nan)
    sel = tod == 1030
    g[k[sel]] = lod[sel]
    lod1030 = g[k]
    with np.errstate(invalid="ignore", divide="ignore"):
        rng1 = D["h1"] - D["l1"]
        m = (D["c1"] < D["o1"]) & (rng1 > 0) & ((D["c1"] - D["l1"]) / rng1 <= 0.35)
        m &= (D["c1"] - D["c3"]) < 0
        m &= D["c1"] > D["sma501"]
        m &= np.isfinite(lod1030) & (lod >= lod1030 - 1e-9) & (tod >= 1100)
        m &= (c > b["opn"]) & (c > b["vwap"])
        m &= (hod > lod) & ((c - lod) / (hod - lod) >= 0.5)
        stop = lod - 0.05 * atr
        risk = c - stop
        m &= (risk > 0) & (risk <= 0.8 * atr)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop,)
    return np.asarray(m & np.isfinite(stop), bool)
