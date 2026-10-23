"""pod-traderlion-open-low-pm-continuation-long - Gap-up that never traded below its open by noon: buy the afternoon
VWAP-side pullback (LONG).

Source: TraderLion (podcast and entry-tactics material: 'open equals low' strength, holding the opening print as the
line in the sand). Not re-fetched in round 2.
URL: https://traderlion.com

VARIANT of pod-dalton-open-drive-pullback-D/OF-long (LOD >= open, entries 10:00-11:30) and
pod-edgeful-green-first15-open-hold-long. Stated change: the open-hold must last until 12:00 (and to entry), the
stock must gap up, entry is in the afternoon and the exit is a hold (sibling file -holdtr scores the 1R trail).

Rules (plain English), only bars up to and including the decision bar i of the same symbol-day:
  1. gap >= +1.0%.
  2. Running low of day >= open - 0.03 x daily ATR at entry (the running low only falls, so this also covers every
     bar up to 12:00). open = close / (1 + fromOpen/100).
  3. fromOpen >= +0.8% at the 12:00 bar.
  4. Pullback: vwapDistPct between 0 and 0.35 on the bar before the trigger.
  5. Trigger bar: close > previous bar high and flow3 > 0.
  6. spy_fo > -0.2.
  Entry: trigger close, bar close 12:00-14:30, first qualifying bar per symbol-day. Stop (GEOM S): max(open, VWAP)
  - 0.10 x daily ATR; skip when the risk is > 0.6 x daily ATR. No target: hold to 15:55. Costs in (scorer).
No tweak made.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1200, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["gap >= 1%", "LOD >= open - 0.03 ATR through entry", "fromOpen >= 0.8 at 12:00",
          "prev bar vwapDistPct 0..0.35", "close > prev high, flow3 > 0", "spy_fo > -0.2",
          "stop max(open, VWAP) - 0.10 ATR (<= 0.6 ATR), hold to 15:55", "12:00-14:30 ET"]


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, lod, op, vw, gap, fo, vd, fl3, spy, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if tod[i0] != 950 or not (gap[i0] >= 1.0):
            continue
        noon_ok = False
        for i in range(i0, i1):
            if tod[i] == 1200:
                noon_ok = fo[i] >= 0.8
            if not noon_ok or i == i0 or tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (lod[i] >= op[i] - 0.03 * a):
                break
            if not (0.0 <= vd[i - 1] <= 0.35 and c[i] > h[i - 1] and fl3[i] > 0 and spy[i] > -0.2):
                continue
            sp = max(op[i], vw[i]) - 0.10 * a
            R = c[i] - sp
            if not (R > 0 and R <= 0.6 * a):
                continue
            m[i] = True
            stop[i] = sp
            break
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - f("dist_lod_atr") * atr
        op = c / (1 + f("fromOpen") / 100)
        vw = c / (1 + f("vwapDistPct") / 100)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), lod, op, vw, f("gap"), f("fromOpen"),
                   f("vwapDistPct"), f("flow3"), f("spy_fo"), atr, WINDOW[0], WINDOW[1])


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


