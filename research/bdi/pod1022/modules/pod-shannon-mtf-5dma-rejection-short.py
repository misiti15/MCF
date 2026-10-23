"""pod-shannon-mtf-5dma-rejection-short - Rejection at a falling 5-day MA with the 60-minute trend down (SHORT).

Source: Brian Shannon 'Technical Analysis Using Multiple Timeframes' (stage 4); Alpha Trends video summary.
URL: https://videohighlight.com/v/Wu57GWTm1_U

VARIANT of rw-tp_slope_rip (trend-pullback short + falling 5m SMA20, failed); opposite side of
pod-shannon-5dma-mtf-pullback-long. Stated change: the rejection level is the multi-day 5-day MA and a 60-minute
alignment gate replaces the 5m slope.

Rules (plain English):
  5-day MA (intraday): SMA of the 5-minute closes over the last 5 sessions of frame bars (5 x 63 = 315 bars, per
  symbol across the frame's days, as in the long sibling); 'falling' = below its value 63 bars (one session) earlier.
  60-minute bars: the closes of the 5-minute bars at 10:30, 11:30, 12:30, 13:30, 14:30 and 15:00 (the frame ends at
  15:00, so the last 'hour' is the 14:30-15:00 half hour; pre-declared). 60-min SMA20 = mean of the last 20 such
  closes per symbol; it is used from the bar that completes it onward.
  1. Daily (lib.daily(), completed days up to D-1): close < SMA50 and SMA10 < SMA20.
  2. 60-min SMA20 falling (latest value < the one before) and the entry close below it.
  3. Signal bar (the previous bar, same day): its high reaches the falling 5-day MA (high >= MA - 0.1 x atr_d) and it
     closes below the MA.
  4. RSI(14) 45-65 on the signal bar.
  5. Entry bar: the next bar closes below EMA9 (5-minute closes). Entry at that close, bar close 10:00-14:30.
  Stop (GEOM S): the 5-day MA at the signal bar + 0.25 x atr_d. Target: LOD or 1R, whichever is nearer (1R when the
  LOD is not below the entry). Flat 15:55.
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = []
NBAR = 63
HOURS = (1030, 1130, 1230, 1330, 1430, 1500)
LAYERS = ["D-1 close < SMA50, SMA10 < SMA20", "60-min SMA20 falling, close below it",
          "signal bar high reaches the falling 5-day MA (0.1 ATR) and closes below", "signal rsi 45-65",
          "next bar closes below EMA9", "stop MA5 + 0.25 ATR, target max(LOD, 1R)"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_ST = {}
_DC = {}


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


def _lag(x, k, n=1):
    """x from n bars earlier in the same group k (NaN when that bar is in another group)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each group k."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _first(cond, k):
    """True only on the first True row of each group (no earlier row qualified)."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _at(x, k, tod, T):
    """Value of x on the bar that closes at T, broadcast to its symbol-day. Callers use it only on rows with tod >= T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(_start(k))
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _ema_sym(x, sc, n):
    """Causal EMA(n) of 5-minute closes per symbol across the frame's days."""
    s = pd.Series(np.asarray(x, float))
    return s.groupby(sc).transform(lambda v: v.ewm(span=n, adjust=False).mean()).to_numpy(float)


def _sma_sym(x, sc, n):
    s = pd.Series(np.asarray(x, float))
    return s.groupby(sc).transform(lambda v: v.rolling(n, min_periods=n).mean()).to_numpy(float)


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


def _daily_feats():
    """Per (symbol, date D): daily values as of D-1's close (completed days only). Series restart after a calendar
    gap > 7 days (the locked block is absent from lib.daily())."""
    if "f" in _DC:
        return _DC["f"]
    try:
        try:
            import lib
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
            import lib
        d = lib.daily()[["symbol", "date", "high", "low", "close", "adv20"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c, h, l = d["close"], d["high"], d["low"]
    gc = c.groupby(g)
    sma10 = gc.transform(lambda x: x.rolling(10).mean())
    sma20 = gc.transform(lambda x: x.rolling(20).mean())
    ret21 = c / gc.shift(21) - 1
    elig = (d["adv20"] >= 20e6) & ret21.notna()
    rk = ret21.where(elig).groupby(d["date"]).rank(pct=True)
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "d_close": c, "d_high": h, "d_low": l,
        "d_high_p": h.groupby(g).shift(1), "d_low_p": l.groupby(g).shift(1),
        "sma10": sma10, "sma10_p": sma10.groupby(g).shift(1),
        "sma20": sma20, "sma20_p": sma20.groupby(g).shift(1),
        "sma50": gc.transform(lambda x: x.rolling(50).mean()),
        "hi20": h.groupby(g).transform(lambda x: x.rolling(20).max()),
        "hi10": h.groupby(g).transform(lambda x: x.rolling(10).max()),
        "lo10": l.groupby(g).transform(lambda x: x.rolling(10).min()),
        "ret21_rank": rk,
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


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    if s is None or s[j] is None:
        return float("nan")
    return float(s[j][i])


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


def _hourly_sma(c, sc, tod, n=20):
    """60-min SMA20 (and its previous value) forward-filled per symbol from the completing 5-minute bar."""
    hr = np.isin(tod, HOURS)
    idx = np.flatnonzero(hr)
    s = pd.Series(c[idx])
    g = sc[idx]
    sma = s.groupby(g).transform(lambda v: v.rolling(n, min_periods=n).mean()).to_numpy(float)
    prv = pd.Series(sma).groupby(g).shift(1).to_numpy(float)
    a = np.full(len(c), np.nan)
    p = np.full(len(c), np.nan)
    a[idx], p[idx] = sma, prv
    a = pd.Series(a).groupby(sc).ffill().to_numpy(float)
    p = pd.Series(p).groupby(sc).ffill().to_numpy(float)
    return a, p


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, h, atr = b["k"], b["tod"], b["c"], b["h"], b["atr"]
    sc = _symcode(df)
    dd = _map_daily(df, k, ["d_close", "sma10", "sma20", "sma50"])
    if dd is None:
        return z
    ma = _sma_sym(c, sc, 5 * NBAR)
    e9 = _ema_sym(c, sc, 9)
    h60, h60p = _hourly_sma(c, sc, tod)
    with np.errstate(invalid="ignore", divide="ignore"):
        rsi = _f(df, "rsi")
        sig = (h >= ma - 0.1 * atr) & (c < ma) & (ma < _lag(ma, sc, NBAR)) & (rsi >= 45) & (rsi <= 65)
        ps = _lag(np.asarray(sig, float), k, 1) == 1.0
        pma = _lag(ma, k, 1)
        m = (dd["d_close"] < dd["sma50"]) & (dd["sma10"] < dd["sma20"])
        m &= (h60 < h60p) & (c < h60)
        m &= ps & (c < e9)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = pma + 0.25 * atr
        r1 = c - (stop - c)
        tgt = np.where(b["lod"] < c, np.maximum(b["lod"], r1), r1)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
