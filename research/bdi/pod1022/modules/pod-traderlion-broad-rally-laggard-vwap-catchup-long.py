"""pod-traderlion-broad-rally-laggard-vwap-catchup-long - Broad afternoon rally: buy the red laggard turning up toward
VWAP (LONG).

Source: TraderLion podcast (money rotates into laggards late in strong-breadth sessions) and Raschke's use of breadth
context. Not re-fetched in round 2.
URL: https://traderlion.com

VARIANT of pod-smb-backside-long-into-vwap (a higher-low base under VWAP, VWAP target, no market gate). Stated change:
a market-wide rally gate, a red-on-day laggard filter, an afternoon window and a momentum turn instead of a base.

Rules (plain English), only bars up to and including the decision bar i of the same symbol-day:
  1. Market rally: spy_fo >= +0.5 and breadth_open >= 0.70.
  2. Laggard: fromOpen between -1.5% and -0.3%, vwapDistPct between -1.2 and -0.3.
  3. dist_pdl_atr > 0.2 (still above the prior-day low).
  4. Trigger: rsi5 crosses up through 50 (previous bar < 50, this bar >= 50), rsiSlope >= 8, flow3 > 0.
  Entry: trigger close, bar close 12:30-14:30. Stop (GEOM S): low of day - 0.05 x daily ATR; skip when the risk is
  > 0.6 x daily ATR. Target: session VWAP at entry; skip when VWAP is less than 1R away. Flat 15:55. Costs in (scorer).
No tweak made.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1230, 1430)
CONTEXT = ["spy_fo", "breadth_open"]
LAYERS = ["spy_fo >= 0.5, breadth_open >= 0.70", "fromOpen -1.5..-0.3, vwapDistPct -1.2..-0.3",
          "dist_pdl_atr > 0.2", "rsi5 crosses up 50, rsiSlope >= 8, flow3 > 0",
          "stop LOD - 0.05 ATR (<= 0.6 ATR), target VWAP (>= 1R away)", "12:30-14:30 ET"]


@numba.njit(cache=False)
def _kernel(b, e, tod, c, lod, vw, spy, bo, fo, vd, dpl, r5, rs, fl3, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 1, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            if not (spy[i] >= 0.5 and bo[i] >= 0.70 and -1.5 <= fo[i] <= -0.3 and -1.2 <= vd[i] <= -0.3
                    and dpl[i] > 0.2):
                continue
            if not (r5[i] >= 50 and r5[i - 1] < 50 and rs[i] >= 8 and fl3[i] > 0):
                continue
            a = atr[i]
            sp = lod[i] - 0.05 * a
            R = c[i] - sp
            if not (R > 0 and R <= 0.6 * a and vw[i] - c[i] >= R):
                continue
            m[i] = True
            stop[i] = sp
            tgt[i] = vw[i]
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df or "breadth_open" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - f("dist_lod_atr") * atr
        vw = c / (1 + f("vwapDistPct") / 100)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, lod, vw, f("spy_fo"), f("breadth_open"), f("fromOpen"),
                   f("vwapDistPct"), f("dist_pdl_atr"), f("rsi5"), f("rsiSlope"), f("flow3"), atr, WINDOW[0], WINDOW[1])


_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
