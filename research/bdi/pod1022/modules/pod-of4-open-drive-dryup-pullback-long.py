"""pod-of4-open-drive-dryup-pullback-long - Opening drive up, first pullback <= 38% on dried-up volume, break of the
pullback high (LONG).

Source: Dalton open-drive (Mind Over Markets, The Open) as listed in the Axia Volume Profile course notes; the Open
Drive script (TradingView nyTw4KmR).
URL: https://it.tradingview.com/script/nyTw4KmR-Open-Drive/

VARIANT of pod-dalton-open-drive-pullback. Changes: an effort-vs-result filter on the pullback (volume must dry up),
a 38% retracement cap, and a trigger on the break of the pullback high.

Rules (plain English). Bars: full-session 5m bars 09:35..15:00 with real volume (_r37_util.vbars). The history keeps
no 5m bar open, so a bar is 'green' when its close is above the previous bar's close (the 09:35 bar: above the 09:30
open). ATR(5m) = mean of the 14 latest 5m true ranges.
  1. Open drive: of the first 6 5m bars (09:35..10:00), >= 5 are green; the 10:00 close is in the top 25% of the
     09:30-10:00 range; that range >= 0.6x the average 09:30-10:00 range of the 20 prior sessions; no bar closing
     09:45 or later (after 09:40) trades below the 09:30 open, through the pullback.
  2. The first pullback after 10:00 (the first bar closing after 10:00 that does not make a new high; until then new
     highs extend the drive) retraces <= 38% of the drive (09:30 open to the drive high), and the average volume of
     the pullback bars is <= 60% of the average volume of the drive bars (09:35 to the bar before the pullback).
     A new high without a trigger, a deeper retracement or a failed volume check ends the day.
  3. Entry: the first 5m close above the highest high of the pullback bars, bar close by 11:30.
  Stop (GEOM S+x): pullback low - 0.05 x ATR(5m). Target: a measured move equal to the drive height (drive high -
  09:30 open) added to the pullback low; 2R when that is not above the entry. Time stop 120 min (MAX_BARS 24).
  Flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r310_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 24
WINDOW = (1005, 1130)
LAYERS = [">= 5 of first 6 bars green, 10:00 close top 25%, range >= 0.6x 20d avg, no trade below open",
          "first pullback <= 38% of drive", "pullback avg vol <= 60% of drive avg vol",
          "close > pullback high by 11:30", "stop pullback low - 0.05 ATR5, measured-move target, 120 min stop"]
_ST = {}


@numba.njit(cache=False)
def _k(nd, tod, o, h, l, c, v, atr, w20, a5):
    n = len(c)
    m = np.zeros(n)
    st = np.full(n, np.nan)
    tg = np.full(n, np.nan)
    dead = True
    op = 0.0
    nb = 0
    ng = 0
    hi = 0.0
    lo = 0.0
    dvs = 0.0
    dvn = 0
    DH = 0.0
    inpb = False
    pbmax = 0.0
    pblow = 0.0
    pbv = 0.0
    pbn = 0
    for i in range(n):
        if nd[i] >= 1:
            dead = tod[i] != 935
            op = o[i]
            nb = 0
            ng = 0
            hi = -np.inf
            lo = np.inf
            dvs = 0.0
            dvn = 0
            inpb = False
        if dead:
            continue
        if tod[i] >= 945 and l[i] < op:
            dead = True
            continue
        if tod[i] <= 1000:
            nb += 1
            if c[i] > o[i]:
                ng += 1
            hi = max(hi, h[i])
            lo = min(lo, l[i])
            if v[i] == v[i]:
                dvs += v[i]
                dvn += 1
            if tod[i] == 1000:
                rg = hi - lo
                ok = nb == 6 and ng >= 5 and rg > 0 and c[i] >= lo + 0.75 * rg and w20[i] == w20[i] \
                    and rg >= 0.6 * w20[i]
                if not ok:
                    dead = True
                DH = hi
            continue
        if tod[i] > 1130:
            dead = True
            continue
        if not inpb:
            if h[i] > DH:
                DH = h[i]
                if v[i] == v[i]:
                    dvs += v[i]
                    dvn += 1
                continue
            inpb = True
            pbmax = h[i]
            pblow = l[i]
            pbv = v[i] if v[i] == v[i] else 0.0
            pbn = 1
            if DH - pblow > 0.38 * (DH - op):
                dead = True
            continue
        if c[i] > pbmax:
            A = a5[i]
            dead = True
            if dvn > 0 and pbn > 0 and pbv / pbn <= 0.6 * (dvs / dvn) and A == A and A > 0:
                e = c[i]
                s = pblow - 0.05 * A
                R = e - s
                t = pblow + (DH - op)
                if t <= e:
                    t = e + 2.0 * R
                if R > 0:
                    m[i] = 1.0
                    st[i] = s
                    tg[i] = t
            continue
        if h[i] > DH:
            dead = True
            continue
        pbmax = max(pbmax, h[i])
        pblow = min(pblow, l[i])
        if v[i] == v[i]:
            pbv += v[i]
        pbn += 1
        if DH - pblow > 0.38 * (DH - op):
            dead = True
    return m, st, tg


def compute(df):
    n = len(df)
    z = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    X = U.vbars(df)
    if X is None or not len(X):
        return z
    I = X[X["tod"] <= 1000].groupby(["symbol", "dn"], as_index=False).agg(hh=("h", "max"), ll=("l", "min"),
                                                                           nb=("h", "size"), o9=("o935", "first"))
    I["hh"] = np.maximum(I["hh"], I["o9"])
    I["ll"] = np.minimum(I["ll"], I["o9"])
    I = I.sort_values(["symbol", "dn"], kind="mergesort").reset_index(drop=True)
    w = (I["hh"] - I["ll"]).where(I["nb"] == 6).to_numpy(float)
    sym = I["symbol"].to_numpy()
    newg = np.r_[True, sym[1:] != sym[:-1]] if len(I) else np.zeros(0, bool)
    I["w20"] = U._prior_mean(newg, w, 20)
    K = X[["symbol", "dn"]].merge(I[["symbol", "dn", "w20"]], on=["symbol", "dn"], how="left")
    assert len(K) == len(X)
    r = U.run_kernel(df, _k, extra=(K["w20"].to_numpy(float), U.atr5))
    tod = df["tod"].to_numpy(np.int64)
    m = r["m"] & (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (r["s"] < U.f(df, "close"))
    return m, r["s"], r["t"]


def mask(df):
    m, s, t = compute(df)
    _ST.clear()
    _ST[id(df)] = (s, t)
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
