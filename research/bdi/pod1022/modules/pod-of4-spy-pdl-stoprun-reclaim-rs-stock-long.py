"""pod-of4-spy-pdl-stoprun-reclaim-rs-stock-long - Index stop run of the prior-day low reclaimed: buy the stocks that
held their own low (LONG).

Source: Bookmap 'Stop runs & liquidity traps' (a premarket / PDL break then a quick recovery = stop run +
absorption); NinjaTrader trap zones (prior-day high / low).
URL: https://bookmap.com/blog/stop-runs-liquidity-traps-how-the-market-flushes-out-weak-hands

VARIANT of pod-cwt-mcdermitt-rs-hold-at-index-newlow-long (enters AT the index new low). Change: the trigger is the
confirmed index stop-run RECLAIM, and the stock filter is that it held its own pre-sweep low of day.

Rules (plain English). Bars: SPY 5m bars (_r24_bars.spy_bars) and the stock's full-session 5m bars 09:35..15:00
(_r37_util.vbars). SPY prior-day low from lib.daily (D-1, completed day). ATR(5m) = mean of the 14 latest 5m true
ranges.
  1. SPY stop run, 09:45-11:30 (bar closes): a SPY bar trades >= 0.05% below the SPY prior-day low (sweep start),
     then a SPY 5m bar closes back above the PDL within 3 bars (the sweep bar itself or one of the next 3). The first
     such reclaim of the day is the event; a failed sweep lets a later sweep qualify.
  2. On the SPY reclaim bar, the stock: made no new session low during the SPY sweep bars (the lowest low of the
     sweep-start..reclaim bars is not below the stock's low of day before the sweep start), closes above its session
     VWAP (vwapDistPct > 0), and its fromOpen return exceeds SPY's (spy_fo) by >= 0.5 percentage points.
  3. ADV: adv20 >= $20M (the scorer default; config/default.yaml has no threshold for this idea). Max 5 names per
     event: the 5 with the largest fromOpen - spy_fo.
  Entry: the reclaim bar close (= next bar open), bar close 09:50-11:30 (the frames start at 09:50).
  Stop (GEOM S+x): the stock's low of day - 0.05 x ATR(5m). Target 1.5R. Time stop 90 min (MAX_BARS 18). Flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r310_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 18
WINDOW = (950, 1130)
TOPN = 5
MIN_ADV = 20e6
LAYERS = ["SPY trades >= 0.05% below its PDL 09:45-11:30, closes back above within 3 bars",
          "stock made no new LOD during the sweep", "stock above VWAP, fromOpen - SPY fromOpen >= 0.5",
          "top 5 by relative strength", "stop LOD - 0.05 ATR5, target 1.5R, 90 min time stop"]
_ST = {}
_MEM = {}


def spy_events():
    """Per date str: tod of the sweep-start bar and of the reclaim bar (first qualifying event)."""
    if "ev" in _MEM:
        return _MEM["ev"]
    import _r24_bars as R24
    S = R24.spy_bars().copy()
    S["date"] = S["date"].astype(str)
    S = S.merge(U.spy_day()[["date", "spy_low1"]], on="date", how="left")
    rows = []
    for d, g in S.groupby("date", sort=True):
        g = g[(g["tod"] >= 945) & (g["tod"] <= 1130)]
        pdl = g["spy_low1"].iloc[0] if len(g) else np.nan
        if not np.isfinite(pdl):
            continue
        tod, lo, cl = g["tod"].to_numpy(int), g["l"].to_numpy(float), g["c"].to_numpy(float)
        i = 0
        while i < len(g):
            if lo[i] <= pdl * (1 - 0.0005):
                hit = -1
                for r in range(i, min(i + 4, len(g))):
                    if cl[r] > pdl:
                        hit = r
                        break
                if hit >= 0:
                    rows.append((d, tod[i], tod[hit]))
                    break
                i += 4
                continue
            i += 1
    E = pd.DataFrame(rows, columns=["date", "s_tod", "r_tod"])
    _MEM["ev"] = E
    return E


@numba.njit(cache=False)
def _k(nd, tod, o, h, l, c, v, atr, stod, rtod, a5):
    n = len(c)
    m = np.zeros(n)
    st = np.full(n, np.nan)
    tg = np.full(n, np.nan)
    lod = np.inf
    lodb = np.inf
    mn = np.inf
    insw = False
    for i in range(n):
        if nd[i] >= 1:
            lod = np.inf
            insw = False
        if stod[i] == stod[i]:
            if tod[i] == stod[i]:
                insw = True
                lodb = lod
                mn = np.inf
            if insw:
                mn = min(mn, l[i])
                if tod[i] == rtod[i]:
                    insw = False
                    A = a5[i]
                    if lodb < np.inf and mn >= lodb and A == A and A > 0:
                        e = c[i]
                        s = lodb - 0.05 * A
                        if e > s:
                            m[i] = 1.0
                            st[i] = s
                            tg[i] = e + 1.5 * (e - s)
        lod = min(lod, l[i])
    return m, st, tg


def compute(df):
    n = len(df)
    z = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    X = U.vbars(df)
    if X is None or not len(X) or "spy_fo" not in df.columns:
        return z
    K = X[["date"]].merge(spy_events(), on="date", how="left")
    assert len(K) == len(X)
    r = U.run_kernel(df, _k, extra=(K["s_tod"].to_numpy(float), K["r_tod"].to_numpy(float), U.atr5))
    tod = df["tod"].to_numpy(np.int64)
    with np.errstate(invalid="ignore"):
        rs = U.f(df, "fromOpen") - U.f(df, "spy_fo")
        m = r["m"] & (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (r["s"] < U.f(df, "close"))
        m &= (U.f(df, "vwapDistPct") > 0) & (rs >= 0.5)
        m &= df["symbol"].astype(str).to_numpy() != "SPY"
        m &= U.f(df, "adv20") >= MIN_ADV
    if m.any():
        T = pd.DataFrame({"date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy()[m], "rs": rs[m],
                          "i": np.nonzero(m)[0]})
        T["rk"] = T.groupby("date")["rs"].rank(ascending=False, method="first")
        keep = np.zeros(n, bool)
        keep[T.loc[T["rk"] <= TOPN, "i"].to_numpy()] = True
        m &= keep
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
