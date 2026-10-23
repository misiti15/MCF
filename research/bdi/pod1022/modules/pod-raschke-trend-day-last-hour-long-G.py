"""pod-raschke-trend-day-last-hour-long-G - Stock trend-day continuation into the close: structural trend-day check,
fixed late entry (LONG, config G).

Source: Linda Raschke rules ('the last hour tells the truth'; trend vs reversion day) - OptionsTradingIQ, FXStreet Prop
Trader Fest replay; Gao, Han, Li & Zhou 'Market Intraday Momentum' as coded in QuantRocket 'first-last' notebook
(Concretum/Zarattini write-ups). MERGED idea (pod-raschke-trend-day-last-hour-long + pod-gao-last-hour-stock-continuation).
URL: https://www.quantrocket.com/codeload/first-last/first_last/Introduction.ipynb.html

VARIANT of intraday_momentum / close_momentum (index ETFs, first-30-min or day return -> 15:30 entry), the backlog
intraday-momentum-paper idea and CWT46. Stated change: single stocks, the signal is a structural trend-day
classification with a still-trending second half, entry 14:30-15:00, held to the close.

Rules (plain English, LONG; SHORT is the exact mirror on bear trend days):
  1. At entry the close sits in the top 15% of the day range (day_pos = (close - LOD) / (HOD - LOD) >= 0.85) and
     dist_hod_atr <= 0.25.   [short: day_pos <= 0.15, dist_lod_atr <= 0.25]
  2. The open sits in the bottom 25% of the day range so far, OR the prior close -> 10:00 return is >= +1.0% and
     fromOpen at entry > fromOpen at the 10:00 bar.   [short: open in the top 25%, or <= -1.0% and fromOpen lower]
  3. At most 1 VWAP cross (sign change of close vs session VWAP between consecutive bars, both closing >= 10:30)
     since 10:30, and close above VWAP on every bar closing 12:00 or later ('all afternoon', pre-declared as 12:00).
  4. Day range so far (HOD - LOD) >= 0.8 x atr_d (the first branch of the source's 'or atrPct >= its 20-day
     median'; the second branch is not coded).
  5. spy_fo > +0.0% (config R: > +0.3%; config G: > 0).   [short: spy_fo < -0.0%]
  Entry: the 15:00 bar close (the last frame bar). Stop: 0.25 x atr_d (1R), no target, flat 15:55 (GEOM hold). Costs per config/default.yaml (scorer).
Frame note: HOD / LOD include 09:30-09:45 (dist_*_atr); EMAs are per symbol over the frame's 5-minute closes.
No tweak made (configs R and G are the source's two pre-declared configs). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "hold"
CONFIG = "G"
WINDOW = (1500, 1500)
CONTEXT = ["spy_fo"]
SPY_MIN = 0.0
LAYERS = ["day_pos >= 0.85 and within 0.25 ATR of HOD", "open in bottom 25% of range or pc->10:00 >= +1% and extending",
          "<= 1 VWAP cross since 10:30, above VWAP since 12:00", "day range >= 0.8 ATR", "spy_fo beyond threshold",
          "config G: 15:00 close; config R: first EMA9/EMA20 touch-and-hold 14:30-15:00", "stop 1R, hold to 15:55"]

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
    sg = 1.0 if SIDE == "long" else -1.0
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    hod, lod, vd, opn, pc = b["hod"], b["lod"], b["vd"], b["opn"], b["pc"]
    fo = _f(df, "fromOpen")
    spy = _f(df, "spy_fo")
    with np.errstate(invalid="ignore", divide="ignore"):
        rng = hod - lod
        dpos = (c - lod) / rng
        opos = (opn - lod) / rng
        c10 = _at(c, k, tod, 1000)
        fo10 = _at(fo, k, tod, 1000)
        ret10 = (c10 / pc - 1) * 100
        if sg > 0:
            m1 = (dpos >= 0.85) & (_f(df, "dist_hod_atr") <= 0.25)
            m2 = (opos <= 0.25) | ((ret10 >= 1.0) & (fo > fo10))
            badside = vd <= 0
            m5 = spy > SPY_MIN
        else:
            m1 = (dpos <= 0.15) & (_f(df, "dist_lod_atr") <= 0.25)
            m2 = (opos >= 0.75) | ((ret10 <= -1.0) & (fo < fo10))
            badside = vd >= 0
            m5 = spy < -SPY_MIN
        s = np.sign(vd)
        ps = _lag(s, k, 1)
        ptod = _lag(tod.astype(float), k, 1)
        cross = (tod >= 1030) & (ptod >= 1030) & (s != ps) & np.isfinite(ps)
        m3 = (_gcum(cross, k) <= 1) & (_gcum((tod >= 1200) & badside, k) == 0) & ~badside
        m4 = rng >= 0.8 * atr
        m = m1 & m2 & m3 & m4 & m5 & np.isfinite(c10)
        if CONFIG == "G":
            m &= tod == 1500
        else:
            sc = _symcode(df)
            e9, e20 = _ema_sym(c, sc, 9), _ema_sym(c, sc, 20)
            if sg > 0:
                t = ((l <= e9) & (c > e9)) | ((l <= e20) & (c > e20))
            else:
                t = ((h >= e9) & (c < e9)) | ((h >= e20) & (c < e20))
            m &= t
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
