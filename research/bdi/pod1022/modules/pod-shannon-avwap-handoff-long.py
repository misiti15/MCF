"""pod-shannon-avwap-handoff-long - VWAP hand-off: second touch of an AVWAP anchored at the held VWAP-test bar (LONG).

Source: Brian Shannon anchored-VWAP method as coded in TradingView 'Anchored VWAP Hand-Off'; TraderLion / Moglen
interview with Brian Shannon.
URL: https://kr.tradingview.com/script/9wtLN3Mf-Anchored-VWAP-Hand-Off

VARIANT of CWT11 VWAP trend pullback (failed), vwap_pullback and ENVC VWAP continuation (videos, failed). Stated
change: the entry is NOT the first VWAP touch but the next pullback to a new AVWAP anchored at the held touch bar,
with a higher low.

Rules (plain English):
  1. Trend: fromOpen > +0.5% and sma20_slope_pct > 0 at the entry bar.
  2. Anchor A: a bar closing 10:00 or later whose low is at or below session VWAP and whose close is above it (the
  VWAP test held). AVWAP_A = VWAP anchored at bar A (bar volumes recovered up to one scale per symbol-day from
  successive session-VWAP values; the frame has no raw volume). While no rally has happened, a newer held test
  re-anchors A.
  3. Rally: a later bar's high is >= 0.3 x daily ATR above AVWAP_A.
  4. Hand-off: after the rally, a later bar's low is <= AVWAP_A + 0.02 x daily ATR, its low is above A's low, it
  closes above AVWAP_A, and buyPressure > 0. A close below AVWAP_A or a low at or below A's low cancels A (a new held
  VWAP test can then start a new anchor).
  Entry: that close, 10:15-14:30. Stop (GEOM S): A's low - 0.05 x daily ATR. Target: a retest of the high of day at
  entry. Flat 15:55. Costs per config/default.yaml (scorer).
No tweak made.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1015, 1430)
CONTEXT = []
LAYERS = ["fromOpen > 0.5%, sma20_slope_pct > 0", "anchor: held VWAP test bar after 10:00",
          "rally >= 0.3 ATR above AVWAP_A", "pullback low <= AVWAP_A + 0.02 ATR, higher low, close > AVWAP_A, buyPressure > 0",
          "stop A low - 0.05 ATR, target HOD, flat 15:55"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_DC = {}
_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _symcode(df):
    return pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()))[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _lag(x, k, n):
    """x from n bars earlier in the same group k (NaN when that bar is in another group)."""
    x = np.asarray(x, float)
    if n <= 0:
        return x.copy()
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _first(cond, k):
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(_start(k))
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _sma_sym(x, sc, n):
    """Causal SMA(n) per symbol over the frame (spans previous days, like the frame's 5m indicators)."""
    s = pd.Series(np.asarray(x, float))
    return s.groupby(sc).transform(lambda v: v.rolling(n, min_periods=n).mean()).to_numpy(float)


def _lib():
    try:
        import lib
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
        import lib
    return lib


def _daily_feats():
    """Per (symbol, date D): daily values as of D-1's close (completed days only). Series restart after a
    calendar gap > 7 days (the locked block is absent from lib.daily())."""
    if "f" in _DC:
        return _DC["f"]
    try:
        d = _lib().daily()[["symbol", "date", "high", "low", "close"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c, h, l = d["close"], d["high"], d["low"]
    gc = c.groupby(g)
    rng = (h - l).replace(0, np.nan)
    sma5 = gc.transform(lambda x: x.rolling(5).mean())
    sma50 = gc.transform(lambda x: x.rolling(50).mean())
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "d_close": c,
        "sma5": sma5, "sma5_p": sma5.groupby(g).shift(1),
        "sma10": gc.transform(lambda x: x.rolling(10).mean()),
        "sma20": gc.transform(lambda x: x.rolling(20).mean()),
        "sma50": sma50, "sma50_p5": sma50.groupby(g).shift(5),
        "ibs": (c - l) / rng,
    })
    for col in [x for x in f.columns if x not in ("symbol", "date")]:
        f[col] = f[col].groupby(g).shift(1)          # the row for D carries the values as of D-1's close
    _DC["f"] = f
    return f


def _map_daily(df, k, cols):
    f = _daily_feats()
    if f is None:
        return None
    st = _start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(f, on=["symbol", "date"], how="left")
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}


@numba.njit(cache=False)
def _relvol(b, e, c, h, l, vw, vr):
    """Bar volumes recovered (up to one scale per symbol-day) from successive session-VWAP values:
    v_t / cumV_t = (VWAP_t - VWAP_{t-1}) / (tp_t - VWAP_{t-1}); when that is not in (0,1) the bar's volume is
    scaled from the last valid bar by volumeRatio. First bar of the day: NaN."""
    n = len(c)
    out = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        cum = 1.0
        lastv = np.nan
        lastvr = np.nan
        for i in range(i0 + 1, i1):
            tp = (h[i] + l[i] + c[i]) / 3.0
            den = tp - vw[i - 1]
            w = (vw[i] - vw[i - 1]) / den if den != 0.0 else np.nan
            v = np.nan
            if w > 0.0 and w < 1.0:
                nc = cum / (1.0 - w)
                v = nc - cum
                cum = nc
            elif lastv == lastv and lastvr > 0 and vr[i] > 0:
                v = lastv * vr[i] / lastvr
                cum = cum + v
            if v == v:
                lastv = v
                lastvr = vr[i]
            out[i] = v
    return out


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, hod, vw, v, atr, ok):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        a = -1
        spv = 0.0
        sv = 0.0
        alow = np.nan
        rallied = False
        for i in range(i0, i1):
            tp = (h[i] + l[i] + c[i]) / 3.0
            if a >= 0:
                if v[i] == v[i]:
                    spv += tp * v[i]
                    sv += v[i]
                av = spv / sv if sv > 0 else np.nan
                if av != av:
                    a = -1
                elif c[i] < av or l[i] <= alow:
                    a = -1
                elif rallied:
                    if ok[i] and l[i] <= av + 0.02 * atr[i] and l[i] > alow and c[i] > av:
                        m[i] = True
                        stop[i] = alow - 0.05 * atr[i]
                        tgt[i] = hod[i]
                elif h[i] - av >= 0.3 * atr[i]:
                    rallied = True
            # a held VWAP test starts (or, before a rally, replaces) the anchor
            if (a < 0 or not rallied) and tod[i] >= 1000 and l[i] <= vw[i] and c[i] > vw[i] and v[i] == v[i] \
                    and i > i0 and not m[i]:
                a = i
                spv = tp * v[i]
                sv = v[i]
                alow = l[i]
                rallied = False
    return m, stop, tgt


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        vw = c / (1 + _f(df, "vwapDistPct") / 100)
        ok = (_f(df, "fromOpen") > 0.5) & (_f(df, "sma20_slope_pct") > 0) & (_f(df, "buyPressure") > 0)
        ok &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        b, e = _segments(k)
        v = _relvol(b, e, c, h, l, vw, _f(df, "volumeRatio"))
    m, stop, tgt = _kernel(b, e, tod, c, h, l, hod, vw, v, atr, np.asarray(ok, np.bool_))
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
