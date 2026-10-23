"""pod-traderlion-undercut-rally-long - Undercut of the 10-day base low, reclaim, then break of the 30-min high (LONG).

Source: TraderLion - Richard Moglen 'Trade Opportunity Case Study of the Week: W Range Breakout' (undercut-and-rally).
URL: https://traderlion.com/profile/richard-moglen/trade-opportunity-case-study-of-the-week-w-range-breakout-sep-6-2025/

VARIANT of CWT14 failed-PDL-break long (Primary/Testing) and LIQ / R15 sweep-reclaim. Stated change: the undercut
level is the 10-day base low (not PDL / OR), the stock must be in a daily base above SMA50, and the trigger is a later
break of the 30-minute high, not the reclaim bar.

Rules (plain English):
  1. Daily (lib.daily(), completed days up to D-1): D-1 close > SMA50 and the 10-day high-low range (D-10..D-1)
     <= 15% of the D-1 close. 10-day low = min low of D-10..D-1.
  2. Before 11:00 the low of day undercuts the 10-day low by 0.05-0.5 x atr_d (depth measured with the LOD as of the
     11:00 bar, or as of the current bar when earlier; LOD includes 09:30-09:45).
  3. After the undercut, a 5-minute close back above the 10-day low and above session VWAP (the reclaim; may be the
     trigger bar itself).
  4. Trigger: a close above the 09:30-10:00 high (HOD as of the 10:00 bar) with volumeRatio >= 1.3.
  Entry: the trigger close. Stop (GEOM S): LOD - 0.02 x atr_d. Target: PDH when it is above the entry, else none
  (flat 15:55). Bar close 10:00-13:00.
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1300)
CONTEXT = []
LAYERS = ["D-1 close > SMA50, 10d range <= 15%", "LOD undercuts the 10d low by 0.05-0.5 ATR before 11:00",
          "close back above the 10d low and VWAP", "close > 09:30-10:00 high with volumeRatio >= 1.3",
          "stop LOD - 0.02 ATR, target PDH else 15:55"]

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


@numba.njit(cache=False)
def _kern(bb, ee, tod, c, lod, vw, vr, h30, lo10, atr, gate, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    for s in range(len(bb)):
        i0, i1 = bb[s], ee[s]
        if not gate[i0]:
            continue
        under = False
        rec = False
        lod11 = np.nan
        for i in range(i0, i1):
            if tod[i] <= 1100:
                lod11 = lod[i]
                if lod[i] < lo10[i] - 0.05 * atr[i]:
                    under = True
            if not under:
                continue
            if c[i] > lo10[i] and c[i] > vw[i]:
                rec = True
            if not rec or tod[i] < w0 or tod[i] > w1:
                continue
            dep = (lo10[i] - lod11) / atr[i]
            if dep >= 0.05 and dep <= 0.5 and c[i] > h30[i] and vr[i] >= 1.3:
                m[i] = True
    return m


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    dd = _map_daily(df, k, ["d_close", "sma50", "hi10", "lo10"])
    if dd is None:
        return z
    with np.errstate(invalid="ignore", divide="ignore"):
        gate = (dd["d_close"] > dd["sma50"]) & ((dd["hi10"] - dd["lo10"]) / dd["d_close"] <= 0.15)
        h30 = _at(b["hod"], k, tod, 1000)
    bb, ee = _segments(k)
    m = _kern(bb, ee, tod, c, b["lod"], b["vwap"], np.nan_to_num(_f(df, "volumeRatio")), h30, dd["lo10"], atr,
              np.asarray(gate, np.bool_), WINDOW[0], WINDOW[1])
    with np.errstate(invalid="ignore"):
        stop = b["lod"] - 0.02 * atr
        tgt = np.where(b["pdh"] > c, b["pdh"], c + 100 * atr)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
