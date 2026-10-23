"""Balance day: touch of the first-hour (IB) edge that closes back inside, fade to VWAP (SIDEWORD, config H)
Source: Better System Trader ep 085 Gary Hart and ep 112 Stefano Serafini (time windows, worst time for breakouts);
J. Dalton 'Mind Over Markets' open types (open-auction) via LuxAlgo, NexusFi, MarketCalls.
URL: https://www.luxalgo.com/library/concept/open-types/

VARIANT of CWT14 failed break at the OR low (needs a break of OR20), CWT15 value-area rotation (untested) and
wi-lunch-reversal (idea). Stated change: the level is the 60-min IB, no prior break (touch and hold), an explicit
balance-day gate and a VWAP target. Different trigger from pod-cwt-unger-quietib-fade (stretch beyond the IB) and
pod-of-ib-mid-rotation (midpoint cross).
Rules (long at the IB low; short = mirror at the IB high), config H of the merged idea:
 Day gate at the 10:30 bar: IBH / IBL = high / low of day as of 10:30.
 (1) Open-auction: today's open is inside the prior-day range (PDL <= open <= PDH).
 (2) Two-sided IB: IBH - open >= 0.15 x atr_d and open - IBL >= 0.15 x atr_d; IB range <= 0.5 x atr_d.
 (3) No range extension by 11:30 (HOD / LOD at the 11:30 bar equal IBH / IBL); 5-minute Wilder ADX(14) <= 20 on the
     trigger bar (per symbol, spans previous days).
 (4) Trigger 11:35-13:45: bar low <= IBL + 0.04 x atr_d, close back above IBL, the day low so far is not more than
     0.05 x atr_d under IBL (touch and hold, no real break); volumeRatio <= 0.9; session VWAP inside the middle 60% of
     the IB; close below VWAP (room to the target).
 Entry at that close. Stop: IBL - 0.12 x atr_d (GEOM S). Target: session VWAP at entry (limit). Flat 15:55.
Pre-declared choices inside the source ranges: touch tolerance 0.04 (0.03-0.05), stop buffer 0.12 (0.10-0.15); config
D (IB-midpoint target, rsi5 / wick trigger) not scored. No tuning on valid. Costs per config/default.yaml.

Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1135, 1345)
CONTEXT = []

import numpy as np
import pandas as pd

LONG = SIDE == "long"
SG = 1.0 if LONG else -1.0
_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _prev(x, k):
    p = np.r_[np.nan, np.asarray(x, float)[:-1]]
    p[_start(k)] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each symbol-day."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _first(cond, k):
    """True only on the first True row of each symbol-day (no earlier row qualified)."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _at(x, k, tod, T):
    """Value of x on the bar that closes at T, broadcast to the whole symbol-day (NaN when that bar is missing).
    Callers only use it on rows with tod > T, so nothing later than the decision bar is used."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _base(df):
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=tod, c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vd"] = _f(df, "vwapDistPct")
    b["vwap"] = c / (1 + b["vd"] / 100)
    return b


def _lag(x, k, n):
    """x from n bars earlier in the same symbol-day (NaN when that bar is in another symbol-day)."""
    x = np.asarray(x, float)
    if n <= 0:
        return x.copy()
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _rmax(x, k, a, b):
    """nanmax of x over lags a..b (bars i-a .. i-b) in the same symbol-day."""
    st = np.vstack([_lag(x, k, j) for j in range(a, b + 1)])
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return np.nanmax(st, axis=0)


def _rmin(x, k, a, b):
    st = np.vstack([_lag(x, k, j) for j in range(a, b + 1)])
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return np.nanmin(st, axis=0)


def _symcode(df):
    return pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()))[0]


def _ewm_sym(x, sc, alpha=None, span=None, minp=1):
    """EMA per symbol over the frame (it spans previous days, like the frame's 5m indicators); causal."""
    s = pd.Series(np.asarray(x, float))
    kw = dict(alpha=alpha) if alpha is not None else dict(span=span)
    return s.groupby(sc).transform(lambda v: v.ewm(adjust=False, min_periods=minp, **kw).mean()).to_numpy(float)


def _adx5(df, n=14):
    """Wilder ADX(n), +DI, -DI on the 5-minute bars, per symbol (spans previous days); causal."""
    sc = _symcode(df)
    h, l, c = (df[x].to_numpy(float) for x in ("high", "low", "close"))
    first = np.r_[True, sc[1:] != sc[:-1]]
    pc = np.r_[np.nan, c[:-1]]
    ph = np.r_[np.nan, h[:-1]]
    pl = np.r_[np.nan, l[:-1]]
    pc[first] = ph[first] = pl[first] = np.nan
    with np.errstate(invalid="ignore"):
        tr = np.fmax(h - l, np.fmax(np.abs(h - pc), np.abs(l - pc)))
        upm, dnm = h - ph, pl - l
        pdm = np.where((upm > dnm) & (upm > 0), upm, 0.0)
        mdm = np.where((dnm > upm) & (dnm > 0), dnm, 0.0)
        pdm[first] = mdm[first] = np.nan
        tr[first] = np.nan
    a = 1.0 / n
    atr = _ewm_sym(tr, sc, alpha=a, minp=n)
    with np.errstate(invalid="ignore", divide="ignore"):
        pdi = 100 * _ewm_sym(pdm, sc, alpha=a, minp=n) / atr
        mdi = 100 * _ewm_sym(mdm, sc, alpha=a, minp=n) / atr
        dx = 100 * np.abs(pdi - mdi) / (pdi + mdi)
    adx = _ewm_sym(dx, sc, alpha=a, minp=n)
    return adx, pdi, mdi


def _lib():
    try:
        import lib
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
        import lib
    return lib

LONG = SIDE == "long"
SG = 1.0 if LONG else -1.0
_ST = {}


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    ibh, ibl = _at(b["hod"], k, tod, 1030), _at(b["lod"], k, tod, 1030)
    h1130, l1130 = _at(b["hod"], k, tod, 1130), _at(b["lod"], k, tod, 1130)
    opn, vwap = b["opn"], b["vwap"]
    ibr = ibh - ibl
    adx, _, _ = _adx5(df, 14)
    vr = _f(df, "volumeRatio")
    eps = 1e-6
    with np.errstate(invalid="ignore"):
        m = (opn >= b["pdl"]) & (opn <= b["pdh"])
        m &= (ibh - opn >= 0.15 * atr) & (opn - ibl >= 0.15 * atr) & (ibr <= 0.5 * atr)
        m &= (h1130 <= ibh + eps) & (l1130 >= ibl - eps) & (adx <= 20)
        m &= (tod >= 1135) & (tod <= 1345) & (vr <= 0.9)
        m &= (vwap >= ibl + 0.2 * ibr) & (vwap <= ibh - 0.2 * ibr)
        if LONG:
            m &= (l <= ibl + 0.04 * atr) & (c > ibl) & (b["lod"] >= ibl - 0.05 * atr) & (c < vwap)
            stop = ibl - 0.12 * atr
        else:
            m &= (h >= ibh - 0.04 * atr) & (c < ibh) & (b["hod"] <= ibh + 0.05 * atr) & (c > vwap)
            stop = ibh + 0.12 * atr
    _ST.clear()
    _ST[id(df)] = (stop, vwap)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")


def target_price(f, i, stop):
    s = _ST.get(id(f))
    return float(s[1][i]) if s is not None else float("nan")
