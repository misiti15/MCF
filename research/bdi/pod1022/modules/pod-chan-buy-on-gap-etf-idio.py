"""Buy-on-gap in sector ETFs when the market did not gap (LONG)
Source: Ernie Chan buy-on-gap model ('Algorithmic Trading', ch. 4), replications by financialnoob and futures.io.
URL: https://financialnoob.substack.com/p/buy-on-gap-strategy-and-its-performance

VARIANT of gap_sma20 mirror (stocks), swarm1017 AM gap-down capitulation and Chan's stock buy-on-gap (replications
decayed). Stated change: sector / industry ETFs only, only when the gap is idiosyncratic (SPY did not gap), plus an
intraday confirmation bar.
Rules (long), SYMBOLS = US sector / industry ETFs (XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC SMH SOXX XBI IBB KRE
KBE XRT XHB ITB XOP OIH GDX XME JETS IYR VNQ IGV ITA VGT):
 (1) Today's open <= prior-day low - 1.0 x sigma90, sigma90 = stdev of the last 90 completed daily close-to-close
     returns x the prior close (daily table, values as of D-1's close; today's open is known at 09:30).
 (2) Today's open > the daily SMA20 of closes as of D-1 (Chan's trend filter).
 (3) |SPY gap| (SPY open today vs SPY prior close) <= 0.3% - the gap is idiosyncratic to the sector.
 (4) 09:50-10:15 bar close: the FIRST bar that closes above the prior bar's high, with min RSI(5) over the prior 3
     bars <= 25 (fewer prior bars at 09:50-10:00 because the frame starts at 09:50).
 Entry at that close. Stop: low of day - 0.05 x atr_d (GEOM S). Target: the prior-day low (gap fill, limit) when it is
 above the entry, else flat 15:55.
No tweak made. Daily series restart after a calendar gap > 7 days (no return spans the locked block, which is never read).
Costs per config/default.yaml (applied by the scorer).

Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (950, 1015)
SYMBOLS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "SMH", "SOXX", "XBI", "IBB",
           "KRE", "KBE", "XRT", "XHB", "ITB", "XOP", "OIH", "GDX", "XME", "JETS", "IYR", "VNQ", "IGV", "ITA", "VGT"]
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

_ST = {}
_DC = {}


def _daily_feats():
    if "f" in _DC:
        return _DC["f"]
    try:
        d = _lib().daily()[["symbol", "date", "open", "low", "close"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    newseg = (d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)
    g = newseg.cumsum()
    c = d["close"]
    ret = c / c.groupby(g).shift(1) - 1                          # NaN at a segment start (never spans the gap)
    # stdev of the last 90 valid returns per symbol (count-based; returns from completed days only)
    rr = pd.DataFrame({"s": d["symbol"], "r": ret}).dropna()
    sig = rr.groupby("s")["r"].transform(lambda x: x.rolling(90, min_periods=90).std())
    d["sig"] = np.nan
    d.loc[rr.index, "sig"] = sig
    d["sig"] = d.groupby("symbol")["sig"].ffill()
    d["sma20"] = c.groupby(g).transform(lambda x: x.rolling(20, min_periods=20).mean())
    f = pd.DataFrame({"symbol": d["symbol"], "date": d["date"].astype(str), "open": d["open"]})
    f["pdl"] = d["low"].groupby(g).shift(1)
    f["pc"] = c.groupby(g).shift(1)
    f["sig"] = d["sig"].groupby(g).shift(1)                      # as of D-1's close
    f["sma20"] = d["sma20"].groupby(g).shift(1)
    spy = f[f["symbol"] == "SPY"][["date", "open", "pc"]]
    spy = spy.assign(spy_gap=(spy["open"] / spy["pc"] - 1) * 100)[["date", "spy_gap"]]
    f = f.merge(spy, on="date", how="left")
    _DC["f"] = f
    return f


def _map_daily(df, k, cols):
    f = _daily_feats()
    if f is None:
        return None
    st = _start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(f, on=["symbol", "date"], how="left")
    return {c: m[c].to_numpy(float)[k] for c in cols}


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    dd = _map_daily(df, k, ["open", "pdl", "pc", "sig", "sma20", "spy_gap"])
    if dd is None:
        return z
    opn = dd["open"]
    r5 = _f(df, "rsi5")
    r5min = _rmin(r5, k, 1, 3)
    with np.errstate(invalid="ignore"):
        m = opn <= dd["pdl"] - 1.0 * dd["sig"] * dd["pc"]
        m &= opn > dd["sma20"]
        m &= np.abs(dd["spy_gap"]) <= 0.3
        inwin = (tod >= 950) & (tod <= 1015)
        trig = inwin & (c > _prev(b["h"], k)) & (r5min <= 25)
        m &= _first(trig, k)
        stop = b["lod"] - 0.05 * atr
        tgt = np.where(dd["pdl"] > c, dd["pdl"], c * 1e6)       # no gap-fill level above -> effectively flat 15:55
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")


def target_price(f, i, stop):
    s = _ST.get(id(f))
    return float(s[1][i]) if s is not None else float("nan")
