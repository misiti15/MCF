"""pod-traderlion-dryup-ema21-pullback-long - Strong-day leader: volume dry-up pullback to the 5-min EMA21, buy the
volume re-expansion bar (LONG).

Source: TraderLion (podcast and entry-tactics material: buy pullbacks to a rising 21-EMA on volume dry-up, enter when
volume returns). Not re-fetched in round 2.
URL: https://traderlion.com

VARIANT of pod-smb-light-counter-move-long (emaDiff > 0.10 counter-move buy) and CWT11 VWAP trend pullback. Stated
change: the pullback must come on volume dry-up, and entry needs volume re-expansion at the EMA21 area, not VWAP.

Rules (plain English), only bars up to and including the decision bar i of the same symbol-day:
  1. fromOpen >= +1.5% and vwapDistPct >= 0.2 (above VWAP).
  2. emaDiff > 0.05 (EMA9 above EMA21) and emaDiff <= 0.6 x its max over the previous 12 bars of the same day
     (fallen >= 40% from that max: the pullback).
  3. sma20_dist_pct between -0.10 and +0.20 (near the 20/21 MA).
  4. Dry-up: volumeRatio <= 0.6 on each of the 3 bars before i.
  5. Trigger bar i: close > previous bar high, volumeRatio >= 1.2, flow3 > 0.3.
  Entry: trigger close, bar close 10:30-14:30. Stop (GEOM S): lowest low of the last 6 bars (i-5..i) - 0.05 x daily
  ATR; skip when the risk is > 0.5 x daily ATR. Target: the nearer of HOD + 0.25 x daily ATR and entry + 2R. Flat
  15:55. Costs in (scorer).
No tweak made.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
LAYERS = ["fromOpen >= 1.5, vwapDistPct >= 0.2", "emaDiff > 0.05 and <= 60% of its 12-bar max",
          "sma20_dist_pct -0.10..+0.20", "volumeRatio <= 0.6 on the 3 prior bars",
          "close > prev high, volumeRatio >= 1.2, flow3 > 0.3", "stop 6-bar low - 0.05 ATR (<= 0.5 ATR), target min(HOD+0.25ATR, 2R)",
          "10:30-14:30 ET"]


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, hod, fo, vd, ed, sd, vr, fl3, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 12, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            if not (fo[i] >= 1.5 and vd[i] >= 0.2 and ed[i] > 0.05 and -0.10 <= sd[i] <= 0.20):
                continue
            mx = -1e18
            for k in range(i - 12, i):
                mx = max(mx, ed[k])
            if not (ed[i] <= 0.6 * mx):
                continue
            if not (vr[i - 1] <= 0.6 and vr[i - 2] <= 0.6 and vr[i - 3] <= 0.6):
                continue
            if not (c[i] > h[i - 1] and vr[i] >= 1.2 and fl3[i] > 0.3):
                continue
            a = atr[i]
            lo = 1e18
            for k in range(i - 5, i + 1):
                lo = min(lo, l[k])
            sp = lo - 0.05 * a
            R = c[i] - sp
            if not (R > 0 and R <= 0.5 * a):
                continue
            t = min(hod[i] + 0.25 * a, c[i] + 2.0 * R)
            if not (t > c[i]):
                continue
            m[i] = True
            stop[i] = sp
            tgt[i] = t
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + f("dist_hod_atr") * atr
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), hod, f("fromOpen"), f("vwapDistPct"),
                   f("emaDiff"), f("sma20_dist_pct"), f("volumeRatio"), f("flow3"), atr, WINDOW[0], WINDOW[1])


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
