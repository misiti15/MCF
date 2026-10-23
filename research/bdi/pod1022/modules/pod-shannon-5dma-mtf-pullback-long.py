"""pod-shannon-5dma-mtf-pullback-long - Multiple-timeframe pullback to the 5-day moving average in a stage-2 stock
(LONG).

Source: Brian Shannon, 'Technical Analysis Using Multiple Timeframes'; Alpha Trends 5-day MA (TradingView 'Brian
Shannon 5-Day MA' / LevelUp scripts); Chat With Traders ep 029.
URL: https://it.tradingview.com/scripts/brianshannon

VARIANT of CWT25 daily MA pullback (daily bars) and R09 5m EMA20 pullback (failed). Stated change: the level is the
multi-day 5-day MA drawn on intraday bars, plus a daily stage-2 filter.

Rules (plain English):
  5-day MA (intraday): SMA of the 5-minute closes over the last 5 sessions of frame bars (5 x 63 = 315 bars,
  computed per symbol across the frame's days; the frame holds the 09:50-15:00 bars, so the first five sessions of
  each scored month are warm-up and give no trades).
  1. Stage 2 (daily table, completed days up to D-1): close > SMA50, SMA50 rising (SMA50 at D-1 > SMA50 five sessions
  earlier), SMA10 > SMA20 > SMA50.
  2. The 5-day MA slopes up over the last session (MA5 now > MA5 63 bars earlier).
  3. Signal bar (the previous bar): its low is within 0.1 x daily ATR of the 5-day MA or below it, and it closes
  above the 5-day MA; RSI(14) 35-55 on the signal bar; its close is within 0.5% of session VWAP or above it.
  4. Entry bar: the next bar (same day) closes above the signal bar's high. Entry at that close, 10:00-14:30.
  Stop (GEOM S): the 5-day MA at the signal bar - 0.25 x daily ATR. Target: the high of day at entry or 1R,
  whichever is nearer (1R when the HOD is not above the entry). Flat 15:55. Costs per config/default.yaml (scorer).
Pre-declared choices inside the idea: 'rising SMA50' = over 5 sessions; 'next close' = the very next bar only;
'last ~1 session' = 63 frame bars. No tuning on valid.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = []
NBAR = 63
LAYERS = ["daily stage 2: close > rising SMA50, SMA10 > SMA20 > SMA50", "intraday 5-day MA rising over 1 session",
          "signal bar low within 0.1 ATR of the 5-day MA, close above it, rsi 35-55, close >= VWAP - 0.5%",
          "next bar closes above the signal-bar high", "stop MA5 - 0.25 ATR, target min(HOD, 1R), flat 15:55"]

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
    sc = _symcode(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    dd = _map_daily(df, k, ["d_close", "sma10", "sma20", "sma50", "sma50_p5"])
    if dd is None:
        return z
    ma = _sma_sym(c, sc, 5 * NBAR)
    with np.errstate(invalid="ignore", divide="ignore"):
        vwd = _f(df, "vwapDistPct")
        hod = c + _f(df, "dist_hod_atr") * atr
        rsi = _f(df, "rsi")
        sig = (l <= ma + 0.1 * atr) & (c > ma) & (rsi >= 35) & (rsi <= 55) & (vwd >= -0.5)
        sig &= ma > _lag(ma, sc, NBAR)
        sig = np.asarray(sig, float)
        ps = _lag(sig, k, 1) == 1.0
        ph = _lag(h, k, 1)
        pma = _lag(ma, k, 1)
        m = (dd["d_close"] > dd["sma50"]) & (dd["sma50"] > dd["sma50_p5"])
        m &= (dd["sma10"] > dd["sma20"]) & (dd["sma20"] > dd["sma50"])
        m &= ps & (c > ph)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = pma - 0.25 * atr
        r1 = c + (c - stop)
        tgt = np.where(hod > c, np.minimum(hod, r1), r1)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
