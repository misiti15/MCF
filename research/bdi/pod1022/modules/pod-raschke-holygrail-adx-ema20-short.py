"""Holy Grail: ADX(14) >= 30 trend, first pullback to the 5-min EMA20, stop-entry over the touch bar (SHORT)
Source: Linda Raschke & Larry Connors 'Street Smarts' Holy Grail (TradingSetupsReview, TradingView scripts,
antoinebuteau notes); Raschke on Better System Trader ep 049/124 and CWT ep 048.
URL: https://tradingsetupsreview.com/the-holy-grail-trading-setup

VARIANT of R09 first pullback to the 20 MA (failed), trend-pullback (holdout_failed), BK 9-EMA ride (failed) and
NM-ETF-late-dip-di-long (ADX7 ETF dip). Stated change: a classic ADX(14) >= 30 trend-strength gate, first EMA20 touch
only, a stop-entry above the touch bar and a swing-high target.
Rules (long; the short side is the exact mirror: -DI > +DI, rally up to EMA20, below VWAP, spy_fo < 0, stop above the
touch high, target the 20-bar swing low):
 (1) 5-minute Wilder ADX(14) >= 30 and +DI > -DI (computed per symbol on 5m bars, spanning previous days, causal).
 (2) Trend proof: in the 12 bars before the touch bar a close >= EMA20 + 0.5 x atr_d, or a new high of day.
 (3) Touch bar: low <= EMA20 + 0.03 x atr_d and close >= EMA20 - 0.05 x atr_d; it is the FIRST touch since the current
     ADX >= 30 / +DI > -DI run began (within the day); touch close > session VWAP; spy_fo > 0; (1) holds on it.
 (4) Entry: the first of the next 3 bars whose close > the touch-bar high (the harness enters at bar close, so this is
     the stop-entry filled at the close of the breakout bar).
 Stop: lowest low from the touch bar to the entry bar - 0.03 x atr_d (GEOM S). Target: the prior 20-bar swing high
 (bars before the entry bar) when it is above the entry, else 1R (entry + entry-to-stop risk). Flat 15:55.
 WINDOW 10:15-14:30 (entry bar close).
Pre-declared choices inside the source ranges: touch tolerance 0.03 atr_d (range 0.02-0.05), stop buffer 0.03 atr_d,
first touch only, 3 confirmation bars, ADX 'rising' config and second-touch config not scored. No tuning on valid.
Costs per config/default.yaml (applied by the scorer).

Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1015, 1430)
CONTEXT = ["spy_fo"]

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
    sc = _symcode(df)
    adx, pdi, mdi = _adx5(df, 14)
    ema = _ewm_sym(c, sc, span=20, minp=20)
    spy = _f(df, "spy_fo")
    with np.errstate(invalid="ignore"):
        if LONG:
            trend = (adx >= 30) & (pdi > mdi)
            ext = (c - ema) >= 0.5 * atr
            newx = h >= b["hod"] - 1e-9                       # this bar printed the high of day so far
            touch = (l <= ema + 0.03 * atr) & (c >= ema - 0.05 * atr) & (c > b["vwap"]) & (spy > 0)
        else:
            trend = (adx >= 30) & (mdi > pdi)
            ext = (ema - c) >= 0.5 * atr
            newx = l <= b["lod"] + 1e-9
            touch = (h >= ema - 0.03 * atr) & (c <= ema + 0.05 * atr) & (c < b["vwap"]) & (spy < 0)
    proof = np.zeros(len(df), bool)
    for j in range(1, 13):
        proof |= (_lag((ext | newx).astype(float), k, j) == 1)
    # run id: a new run starts on the first bar of a symbol-day or when the trend gate switches on
    tr_prev = _prev(trend.astype(float), k)
    run_start = trend & ~(tr_prev == 1)
    rid = np.cumsum(run_start | _start(k))
    t0 = trend & touch & proof
    # first touch within the run (only counted while the run is active)
    cnt = pd.Series(t0.astype(int)).groupby(rid).cumsum().to_numpy()
    first_touch = t0 & (cnt == 1)
    m = np.zeros(len(df), bool)
    stop = np.full(len(df), np.nan)
    tgt = np.full(len(df), np.nan)
    swing = _rmax(h, k, 1, 20) if LONG else _rmin(l, k, 1, 20)
    for j in (1, 2, 3):
        ft = _lag(first_touch.astype(float), k, j) == 1
        th = _lag(h, k, j) if LONG else _lag(l, k, j)
        ext_pb = _rmin(l, k, 0, j) if LONG else _rmax(h, k, 0, j)
        with np.errstate(invalid="ignore"):
            hit = ft & ((c > th) if LONG else (c < th))
            # require no earlier bar after the touch to have confirmed already
            for q in range(1, j):
                prev_c = _lag(c, k, q)
                hit &= ~((prev_c > th) if LONG else (prev_c < th))
        new = hit & ~m
        s = ext_pb - SG * 0.03 * atr
        r = SG * (c - s)
        tg = np.where(SG * (swing - c) > 0, swing, c + SG * r)
        stop = np.where(new, s, stop)
        tgt = np.where(new, tg, tgt)
        m |= new
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
