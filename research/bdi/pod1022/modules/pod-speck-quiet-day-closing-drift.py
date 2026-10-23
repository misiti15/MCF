"""Quiet-day closing drift long in index ETFs (the days intraday_momentum skips) (LONG)
Source: Dimitri Speck, Better System Trader ep 137 (hours with significant S&P returns); Seasonax intraday seasonality.
URL: https://www.seasonax.com/?p=12639

VARIANT / complement of intraday_momentum (Testing; trades 15:30-close only when |first 30 min| >= 0.25%) and
close_momentum. Stated change: trades exactly the quiet days it skips, long only, earlier entry, with trend + VWAP +
breadth gates.
Rules (long), SYMBOLS = SPY, QQQ, IWM, DIA:
 (1) |fromOpen| at the 10:00 bar (09:55-10:00 close vs today's open) < 0.25%.
 (2) SPY's D-1 close is above its daily SMA50 (50 completed daily closes up to D-1).
 (3) At the 14:55 bar: close > session VWAP and the day range (HOD - LOD) <= 0.8 x atr_d.
 (4) breadth_open >= 0.45 (share of the universe above its own open, at the 15:00 entry bar).
 Entry: the 15:00 bar close. Stop: entry - 0.35 x atr_d or the 13:00-15:00 low (bars closing 13:05..15:00) - whichever
 is closer to the entry (GEOM S). Exit flat 15:55 (no target).
No tweak made. Daily series restart after a calendar gap > 7 days. Costs per config/default.yaml (applied by the scorer).

Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1500, 1500)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = ["breadth_open"]

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

_ST = {}
_DC = {}


def _spy_trend():
    """date (str) -> SPY close(D-1) > SMA50(D-1), from completed days only."""
    if "f" in _DC:
        return _DC["f"]
    try:
        d = _lib().daily()
    except Exception:
        _DC["f"] = None
        return None
    d = d[d["symbol"].astype(str) == "SPY"][["date", "close"]].sort_values("date").reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((dt - dt.shift()).dt.days > 7).cumsum()
    sma = d["close"].groupby(g).transform(lambda x: x.rolling(50, min_periods=50).mean())
    up = (d["close"] > sma).astype(float).where(sma.notna())
    f = pd.DataFrame({"date": d["date"].astype(str), "spy_up": up.groupby(g).shift(1)})
    _DC["f"] = f
    return f


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    f = _spy_trend()
    if f is None:
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    mp = dict(zip(f["date"], f["spy_up"]))
    spy_up = np.array([mp.get(x, np.nan) for x in df["date"].astype(str).to_numpy()], float)
    fo10 = _at(_f(df, "fromOpen"), k, tod, 1000)
    vwap_ok = _at((c > b["vwap"]).astype(float), k, tod, 1455)
    rng = _at(b["hod"] - b["lod"], k, tod, 1455)
    low_pm = np.where((tod >= 1305) & (tod <= 1500), b["l"], np.nan)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lpm = pd.Series(low_pm).groupby(k).cummin().to_numpy(float)
    with np.errstate(invalid="ignore"):
        m = (tod == 1500) & (np.abs(fo10) < 0.25) & (spy_up == 1)
        m &= (vwap_ok == 1) & (rng <= 0.8 * atr)
        m &= _f(df, "breadth_open") >= 0.45
        stop = np.fmax(c - 0.35 * atr, lpm)
    _ST.clear()
    _ST[id(df)] = (stop,)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")
