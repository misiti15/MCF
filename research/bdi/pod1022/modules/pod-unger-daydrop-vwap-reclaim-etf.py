"""pod-unger-daydrop-vwap-reclaim-etf - Day-Drop ETF: morning dip below the open, then a VWAP reclaim long (LONG).

Source: Andrea Unger, 'The Day Drop Pattern', Stocks & Commodities V.41:04 (Better System Trader ep 016 / 045).
URL: https://store.traders.com/stcov413ddrp.html

VARIANT of pod-unger-daydrop-orb-long (same Day-Drop filter, different trigger: a morning dip and a VWAP reclaim
instead of an opening-range break) and of the index dip-bounce family (IDX/LD, % thresholds). Not the NS3/NS4 VWAP
reclaim SHORT fades (opposite side, ETFs only, prior-day filter).

Rules (plain English), SYMBOLS = index + sector / industry ETFs:
  1. Day Drop: D-1 close location (close - low) / (high - low) <= 0.20 (daily table, completed day D-1).
  2. The ETF is in an uptrend: D-1 close above its daily SMA50 (closes up to D-1).
  3. Before 11:00 the price trades at least 0.25 x daily ATR below today's open (the low of day as of the last bar
     closing at or before 11:00, which includes the 09:30-09:50 bars).
  4. 10:00-12:00: the first 5-minute close back above session VWAP (previous close at or below it) after the dip,
     with RSI(5) rising on that bar and RSI(5) <= 30 on at least one of the previous 6 bars.
  Entry: that close. Stop (GEOM S): the morning low (low of day at entry) - 0.05 x daily ATR. Target: 2R, else
  flat 15:55. One trade per symbol-day (scorer). Costs per config/default.yaml (applied by the scorer).
Frame note: the SMA50 needs 50 post-gap daily rows, so trades start around mid-May 2025.
No tweak made; every threshold is the idea's stated value.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1200)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC",
           "SMH", "SOXX", "XBI", "IBB", "KRE", "XRT", "XHB", "XOP", "ITB", "IYR", "XME"]
CONTEXT = []
LAYERS = ["D-1 close location <= 0.20", "D-1 close > daily SMA50", "pre-11:00 low <= open - 0.25 ATR",
          "10:00-12:00 first close back above VWAP after the dip, rsi5 rising from <= 30 within 6 bars",
          "stop morning low - 0.05 ATR, target 2R, flat 15:55"]

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


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    dd = _map_daily(df, k, ["ibs", "d_close", "sma50"])
    if dd is None:
        return z
    with np.errstate(invalid="ignore", divide="ignore"):
        opn = c / (1 + _f(df, "fromOpen") / 100)
        lod = c - _f(df, "dist_lod_atr") * atr
        vwap = c / (1 + _f(df, "vwapDistPct") / 100)
        # the low of day as of the last bar closing at or before 11:00 (lod is non-increasing inside the day)
        ml = pd.Series(np.where(tod <= 1100, lod, np.nan)).groupby(k).ffill().to_numpy(float)
        dip = ml <= opn - 0.25 * atr
        pc = _lag(c, k, 1)
        pv = _lag(vwap, k, 1)
        cross = (c > vwap) & (pc <= pv)
        inwin = (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        firstx = _first(cross & dip & inwin, k)
        r5 = _f(df, "rsi5")
        lo6 = np.fmin.reduce(np.vstack([_lag(r5, k, j) for j in range(1, 7)]), axis=0)
        m = (dd["ibs"] <= 0.20) & (dd["d_close"] > dd["sma50"])
        m &= firstx & (r5 > _lag(r5, k, 1)) & (lo6 <= 30)
        stop = lod - 0.05 * atr
        tgt = c + 2 * (c - stop)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
