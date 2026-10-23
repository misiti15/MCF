"""Raschke 'Anti': fast %K hook in the direction of a trending slow %D, scalp exit (LONG)
Source: Linda Raschke 'Street Smarts' The Anti (Better System Trader ep 049 guest); IG write-up, RoboForex summary,
NexusFi 'Anti strategy' thread, TradingView MACD 3-10-16 + Stoch 7-10 scripts.
URL: https://nexusfi.com/thinkorswim/23724-anti-strategy-linda-bradford-rasche-2.html

VARIANT of the articles indicator grid / stochx (%K/%D crosses at OB/OS, failed) and NS1 RSI dip + RSI5 pop. Stated
change: the trend is the SLOPE of the slow line, the trigger is a mid-range hook of the fast line back in that
direction, with a scalp exit.
Rules (long; short = exact mirror below VWAP with %D falling and <= 50, %K pulled up then hooking down, 40-70 band):
 Stochastic(7,10) on 5m bars per symbol (spans previous days): fast %K = 100 x (close - LL7) / (HH7 - LL7),
 slow %D = SMA10 of %K. (Config S of the source; the 3/10 oscillator config 310 is not scored.)
 (1) Slow %D has risen over the last 3 bars (%D_i > %D_{i-3}) and %D >= 50.
 (2) Pullback: the max of %K over bars i-2..i-6 minus %K_{i-1} >= 15 points; %K now 30-60.
 (3) Hook: %K_i > %K_{i-1} after >= 2 down bars (%K_{i-1} < %K_{i-2} < %K_{i-3}); close > high_{i-1}.
 (4) close > session VWAP.
 Entry: the hook bar close. Stop: the lowest low of bars i..i-4 - 0.03 x atr_d, capped at 0.25 x atr_d (1R) from the
 entry (GEOM S). Target: 0.5 x the entry-to-stop risk (t05s05-like scalp; the 4-bar time stop is not in the harness,
 so the trade is otherwise flat 15:55). WINDOW 10:00-14:30.
Pre-declared choices inside the source ranges: 3-bar slope, 15-point pullback, 0.03 atr_d stop buffer; the 'second
hook only' config is not scored. No tuning on valid. Costs per config/default.yaml (applied by the scorer).

Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
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


def _sym_roll(x, sc, n, fn):
    s = pd.Series(np.asarray(x, float))
    r = s.groupby(sc).rolling(n, min_periods=n)
    r = r.max() if fn == "max" else (r.min() if fn == "min" else r.mean())
    return r.reset_index(level=0, drop=True).sort_index().to_numpy(float)


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    sc = _symcode(df)
    hh, ll = _sym_roll(h, sc, 7, "max"), _sym_roll(l, sc, 7, "min")
    with np.errstate(invalid="ignore", divide="ignore"):
        K = 100 * (c - ll) / (hh - ll)
    K = np.where(np.isfinite(K), K, 50.0)
    D = _sym_roll(K, sc, 10, "mean")
    K1, K2, K3 = _lag(K, k, 1), _lag(K, k, 2), _lag(K, k, 3)
    with np.errstate(invalid="ignore"):
        if LONG:
            m = (D > _lag(D, k, 3)) & (D >= 50)
            m &= (_rmax(K, k, 2, 6) - K1 >= 15) & (K >= 30) & (K <= 60)
            m &= (K > K1) & (K1 < K2) & (K2 < K3) & (c > _prev(h, k))
            m &= c > b["vwap"]
            ext = _rmin(l, k, 0, 4)
            stop = np.maximum(ext - 0.03 * atr, c - 0.25 * atr)
        else:
            m = (D < _lag(D, k, 3)) & (D <= 50)
            m &= (K1 - _rmin(K, k, 2, 6) >= 15) & (K >= 40) & (K <= 70)
            m &= (K < K1) & (K1 > K2) & (K2 > K3) & (c < _prev(l, k))
            m &= c < b["vwap"]
            ext = _rmax(h, k, 0, 4)
            stop = np.minimum(ext + 0.03 * atr, c + 0.25 * atr)
        tgt = c + 0.5 * (c - stop)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")


def target_price(f, i, stop):
    s = _ST.get(id(f))
    return float(s[1][i]) if s is not None else float("nan")
