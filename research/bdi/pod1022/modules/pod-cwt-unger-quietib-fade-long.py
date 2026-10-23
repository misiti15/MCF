"""Quiet first hour: fade the first stretch beyond the first-hour range back to VWAP (LONG side)
Source: Andrea Unger (named CWT guest list); Unger Academy first-hour and bias material (patterns as filters, side chosen by regime).
URL: https://ungeracademy.com/blog/dax-first-hour-strategy-last-year-performance

Rules (long): Universe: SPY, QQQ, IWM, DIA and large caps (adv20 >= $200M; MIN_ADV = 200e6). (1) First-hour range (HOD - LOD at the 10:30 bar) < 0.35 x atr_d. (2) rvol_day = mean volumeRatio from 09:50 to the entry bar < 0.8 (proxy for cumulative volume < 0.8x its same-time average). (3) 11:00-14:30: a 5-min close >= 0.15 x atr_d below the first-hour low with RSI(5) < 25 (the first such bar). Entry at that close. Target: session VWAP at entry (limit). Stop: 0.35 x atr_d below the entry bar's low. Flat 15:55.
No tweak. Costs per config/default.yaml (applied by the scorer).


Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
CONTEXT = ["spy_fo", "breadth_open"]
MIN_ADV = 200000000

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


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    fh, fl = _at(b["hod"], k, tod, 1030), _at(b["lod"], k, tod, 1030)
    vr = _f(df, "volumeRatio")
    ok = np.isfinite(vr)
    rvol = _gcum(np.where(ok, vr, 0.0), k) / _gcum(ok.astype(float), k)
    r5 = _f(df, "rsi5")
    with np.errstate(invalid="ignore", divide="ignore"):
        m = ((fh - fl) < 0.35 * atr) & (rvol < 0.8) & (tod >= 1100) & (tod <= 1430)
        if LONG:
            m &= (c <= fl - 0.15 * atr) & (r5 < 25)
            stop = b["l"] - 0.35 * atr
        else:
            m &= (c >= fh + 0.15 * atr) & (r5 > 75)
            stop = b["h"] + 0.35 * atr
    _ST.clear()
    _ST[id(df)] = (stop, b["vwap"])
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")


def target_price(f, i, stop):
    s = _ST.get(id(f))
    return float(s[1][i]) if s is not None else float("nan")
