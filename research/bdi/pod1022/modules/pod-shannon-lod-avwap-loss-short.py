"""pod-shannon-lod-avwap-loss-short - Loss of the VWAP anchored at today's low after a failed bounce below session
VWAP (SHORT).

Source: Alpha Trends / Brian Shannon - anchored VWAP, 'guilty until proven innocent' below a declining AVWAP / 5-day MA;
Benzinga interview 'My favorite ways to use the Anchored VWAP'.
URL: https://www.benzinga.com/general/education/22/05/27200039/my-favorite-ways-to-use-the-anchored-vwap-brian-shannon

VARIANT of NS3 failed VWAP reclaim short (Testing) and AVR (failed). Opposite side and anchor of
pod-shannon-hod-avwap-reclaim-long. Stated change: the level is the AVWAP of the buyers since today's LOD (not
session VWAP), after a bounce that stayed under session VWAP.

Rules (plain English):
  AVWAP_L: VWAP anchored at the bar that set the current low of day; that bar must close after 09:50 (frame bar
  09:50-09:55 or later; when the day's low is still a 09:30-09:50 low there is no anchor). Bar volumes are recovered
  (up to one scale per symbol-day) from successive session-VWAP values (the frame has no raw volume). A new low of
  day moves the anchor and resets the bounce.
  1. Downtrend: the price is below the daily 5-day SMA (closes up to D-1) and that SMA is falling (SMA5 at D-1 <
  SMA5 at D-2); fromOpen < 0.
  2. Since the LOD bar a bounce of >= 0.5 x daily ATR (highest high since the LOD - LOD), and every close since
  (and including) the LOD bar is below session VWAP.
  3. Trigger: the close crosses below AVWAP_L (previous close at or above the previous AVWAP_L).
  4. Market: SPY below its own session VWAP (SPY rows of the same frame, same date and bar) or breadth < 0.45;
  RSI(14) < 50.
  Entry: that close, 10:30-14:45. Stop (GEOM S): the bounce high + 0.05 x daily ATR, capped at 1.5R (1.5 x 0.25 x
  daily ATR above the entry). Target: a retest of the LOD. Flat 15:55. Costs per config/default.yaml (scorer).
No tweak made; the 5-day MA is the daily-table option the idea allows.
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1030, 1445)
CONTEXT = ["breadth"]
LAYERS = ["close < falling daily SMA5, fromOpen < 0", "AVWAP anchored at the in-frame LOD bar",
          "bounce >= 0.5 ATR from the LOD, all closes since the LOD below session VWAP",
          "close crosses below AVWAP_L", "SPY below VWAP or breadth < 0.45; rsi < 50",
          "stop bounce high + 0.05 ATR (cap 1.5R), target LOD, flat 15:55"]

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
def _kernel(b, e, c, h, l, lod, vw, v, atr, ok):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        rl = l[i0]
        a = -1
        spv = 0.0
        sv = 0.0
        av_prev = np.nan
        bh = np.nan
        below = False
        for i in range(i0, i1):
            rl = min(rl, l[i])
            L = min(lod[i], rl)
            tp = (h[i] + l[i] + c[i]) / 3.0
            if l[i] <= L + 1e-9 * c[i]:
                a = i if (i > i0 and v[i] == v[i]) else -1
                spv = tp * v[i] if a >= 0 else 0.0
                sv = v[i] if a >= 0 else 0.0
                av_prev = tp if a >= 0 else np.nan
                bh = h[i]
                below = c[i] < vw[i]
                continue
            if a < 0:
                continue
            if v[i] == v[i]:
                spv += tp * v[i]
                sv += v[i]
            av = spv / sv if sv > 0 else np.nan
            bh = max(bh, h[i])
            below = below and (c[i] < vw[i])
            if ok[i] and below and bh - L >= 0.5 * atr[i] and av == av and av_prev == av_prev:
                if c[i] < av and c[i - 1] >= av_prev:
                    m[i] = True
                    stop[i] = min(bh + 0.05 * atr[i], c[i] + 1.5 * 0.25 * atr[i])
                    tgt[i] = L
            av_prev = av
    return m, stop, tgt


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "breadth" not in df:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    dd = _map_daily(df, k, ["sma5", "sma5_p"])
    if dd is None:
        return z
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - _f(df, "dist_lod_atr") * atr
        vw = c / (1 + _f(df, "vwapDistPct") / 100)
        # SPY vs its own session VWAP at the same (date, bar), from the SPY rows of this frame
        sym = df["symbol"].astype(str).to_numpy()
        key = df["date"].astype(str).to_numpy().astype(object) + "|" + tod.astype(str).astype(object)
        spy = pd.Series(_f(df, "vwapDistPct")[sym == "SPY"], index=key[sym == "SPY"])
        spy = spy[~spy.index.duplicated()]
        spyv = pd.Series(key).map(spy).to_numpy(float)
        mkt = (spyv < 0) | (_f(df, "breadth") < 0.45)
        ok = (c < dd["sma5"]) & (dd["sma5"] < dd["sma5_p"]) & (_f(df, "fromOpen") < 0)
        ok &= mkt & (_f(df, "rsi") < 50) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        b, e = _segments(k)
        v = _relvol(b, e, c, h, l, vw, _f(df, "volumeRatio"))
    m, stop, tgt = _kernel(b, e, c, h, l, lod, vw, v, atr, np.asarray(ok, np.bool_))
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
