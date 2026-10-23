"""pod-traderlion-insideday-pdh-long - Inside day in an uptrend: break of the inside-day high after 10:00 (LONG).

Source: TraderLion / Trading Engineered Substack ('Inside Day' posts) and TraderLion entry tactics.
URL: https://tradingengineered.substack.com/sitemap/2023

VARIANT of CWT10 PDH breakout day-two (cwt-a-a3, failed) and nr7-orb (idea). Stated change: the compression filter is
a true inside day and the trigger is the inside-day high (PDH) after 10:00, not the opening range.

Rules (plain English):
  1. Inside day (lib.daily(), completed days): D-1 high < D-2 high and D-1 low > D-2 low.
  2. D-1 close > daily SMA20 and SMA20 rising (SMA20 at D-1 > SMA20 at D-2).
  3. |gap| < 1%.
  4. After 10:00 the FIRST 5-minute close above PDH (bars closing 10:00 or later) is the trigger, and that bar has
     volumeRatio >= 1.5.
  5. close > session VWAP and spy_fo > 0.
  Entry: the trigger close. Stop (GEOM S): max(inside-day midpoint (PDH + PDL) / 2, LOD), capped so entry - stop
  <= 1.5 x 0.25 x atr_d. Target: PDH + 0.5 x atr_d; else flat 15:55. Bar close 10:00-14:00.
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1400)
CONTEXT = ["spy_fo"]
LAYERS = ["D-1 inside D-2", "D-1 close > rising SMA20", "|gap| < 1%", "first close > PDH after 10:00, volumeRatio >= 1.5",
          "close > VWAP, spy_fo > 0", "stop max(ID mid, LOD) capped 0.375 ATR, target PDH + 0.5 ATR"]

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


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    dd = _map_daily(df, k, ["d_close", "d_high", "d_low", "d_high_p", "d_low_p", "sma20", "sma20_p"])
    if dd is None:
        return z
    with np.errstate(invalid="ignore", divide="ignore"):
        g = (dd["d_high"] < dd["d_high_p"]) & (dd["d_low"] > dd["d_low_p"])
        g &= (dd["d_close"] > dd["sma20"]) & (dd["sma20"] > dd["sma20_p"])
        g &= np.abs(_f(df, "gap")) < 1.0
        brk = _first((tod >= 1000) & (c > b["pdh"]), k)
        m = g & brk & (_f(df, "volumeRatio") >= 1.5) & (b["vd"] > 0) & (_f(df, "spy_fo") > 0)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = np.maximum((b["pdh"] + b["pdl"]) / 2, b["lod"])
        stop = np.maximum(stop, c - 0.375 * atr)
        tgt = b["pdh"] + 0.5 * atr
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
