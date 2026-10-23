"""pod-smb-trend-trend-pm-consolidation-hold-holdtr - SECOND CONFIG (GEOM holdtr) of the Trend Trend Trade: daily and intraday trends aligned, afternoon box
break held to the close (LONG).

Source: SMB Capital PlayBook 'Trend Trend Trade' (SMB blog; ATAS PlayBook summary).
URL: https://www.smbtraining.com/blog/wp-json/wp/v2/posts/17322

VARIANT of CWT46 afternoon breakout (cwt-b-b6, failed: fromOpen >= 4/8% gate) and CWT12 coil. Stated change: the
big-mover gate is replaced by DAILY trend alignment and the trade is held to the close. Sibling of
pod-shannon-midday-vwap-base-quiet-long (that one uses a quiet-SPY gate).

Rules (plain English):
  1. Daily trend: D-1 close > daily SMA20 > daily SMA50 (closes up to D-1) and D-1 close within 1.0 x atr_d of the
     20-day high (highs D-20..D-1). Daily table: research/history2y lib.daily(), completed days only.
  2. Intraday trend: >= 75% of the 5-minute closes since 10:00 (up to and including this bar) are above session
     VWAP, and fromOpen >= +0.5%.
  3. Box: the N bars before this bar (N = the longest of 10, 9, 8, 7, 6 whose high-low range is <= 0.35 x atr_d;
     the source's 6-10 bar range, pre-declared rule for picking N, no tuning) and the box low is above VWAP (VWAP at
     the last box bar).
  4. Trigger: this bar closes above the box high with volumeRatio >= 1.2.
  Entry: that close. Stop (GEOM S): box low - 0.03 x atr_d. Exit: flat 15:55, no target. Bar close 12:30-14:45.
  The '-holdtr' file is the idea's second config (same mask, GEOM holdtr: stop 1R = 0.25 ATR, 1R trail after +1R).
Frame note: 'closes since 10:00' counts the frame's 5-minute bars that close at 10:00 or later. SMA50 needs 50
post-gap daily rows, so trades start around mid-May 2025.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "holdtr"
WINDOW = (1230, 1445)
LAYERS = ["D-1 close > SMA20 > SMA50, within 1 ATR of the 20-day high", ">= 75% of closes since 10:00 above VWAP",
          "fromOpen >= 0.5", "6-10 bar box range <= 0.35 ATR, box low above VWAP", "close > box high, volumeRatio >= 1.2",
          "stop box low - 0.03 ATR, flat 15:55", "12:30-14:45"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

LONG = SIDE == "long"
_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _prev(x, k, n=1):
    """x shifted n bars back inside the same symbol-day (NaN where that bar is in another symbol-day)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        same = np.zeros(len(x), bool)
        same[n:] = k[n:] == k[:-n]
        p[~same] = np.nan
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
    Callers only use it on rows with tod > T (or == T), so nothing later than the decision bar is used."""
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
    """Per (symbol, date D): daily values known at D's open, computed on completed days up to D-1 only.
    Series restart after a calendar gap > 7 days (the locked block is absent from lib.daily(), so the SMA50 / 20-day
    values are NaN until enough post-gap days exist)."""
    if "f" in _DC:
        return _DC["f"]
    try:
        try:
            import lib
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
            import lib
        d = lib.daily()[["symbol", "date", "high", "low", "close"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c, h, l = d["close"], d["high"], d["low"]
    gc = c.groupby(g)
    pc = gc.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1).where(pc.notna())
    rng = (h - l).replace(0, np.nan)
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "d_close": c, "d_high": h, "d_low": l,
        "sma20": gc.transform(lambda x: x.rolling(20).mean()),
        "sma50": gc.transform(lambda x: x.rolling(50).mean()),
        "hi20": h.groupby(g).transform(lambda x: x.rolling(20).max()),
        "atr5": tr.groupby(g).transform(lambda x: x.rolling(5).mean()),
        "dchg": c - pc,
        "ibs": (c - l) / rng,
    })
    cols = [x for x in f.columns if x not in ("symbol", "date")]
    for col in cols:                       # the row for D carries the values as of D-1's close
        f[col] = f[col].groupby(g).shift(1)
    _DC["f"] = f
    return f


def _map_daily(df, k, cols):
    """Daily features for every frame row (via its symbol-day), NaN when missing."""
    f = _daily_feats()
    if f is None:
        return None
    st = _start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(f, on=["symbol", "date"], how="left")
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, vw, vr, atr, fo, gate, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not gate[i0]:
            continue
        na = 0
        nt = 0
        for i in range(i0, i1):
            if tod[i] >= 1000:
                nt += 1
                if c[i] > vw[i]:
                    na += 1
            if tod[i] < w0 or tod[i] > w1:
                continue
            if nt == 0 or na < 0.75 * nt or not (fo[i] >= 0.5) or not (vr[i] >= 1.2):
                continue
            for N in range(10, 5, -1):
                if i - N < i0:
                    continue
                bh = -1e18
                bl = 1e18
                for t in range(i - N, i):
                    bh = max(bh, h[t])
                    bl = min(bl, l[t])
                if bh - bl <= 0.35 * atr[i]:
                    if bl > vw[i - 1] and c[i] > bh:
                        m[i] = True
                        stop[i] = bl - 0.03 * atr[i]
                    break
    return m, stop


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    b = _base(df)
    k, c, atr = b["k"], b["c"], b["atr"]
    dd = _map_daily(df, k, ["d_close", "sma20", "sma50", "hi20"])
    if dd is None:
        return z
    with np.errstate(invalid="ignore"):
        gate = (dd["d_close"] > dd["sma20"]) & (dd["sma20"] > dd["sma50"]) & ((dd["hi20"] - dd["d_close"]) <= 1.0 * atr)
    bb, ee = _segments(k)
    m, stop = _kern(bb, ee, b["tod"], c, b["h"], b["l"], b["vwap"], _f(df, "volumeRatio"), atr, _f(df, "fromOpen"),
                    np.asarray(gate, np.bool_), WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, None)
    return np.asarray(m, dtype=bool)
