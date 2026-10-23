"""pod-smb-market-flush-holder-long - Buy the stock that held its low while SPY flushed, on SPY's first up bar
(LONG).

Source: SMB Radar 'Strong/Weak Today' + SMB Training 'Recognizing A Strong Stock'.
URL: https://www.smbtraining.com/blog/tag/strong-stocks

VARIANT of t4 relative strength (failed) and rw-t4_long_vwapmf (failed). Stated change: a MARKET EVENT triggers it
(SPY flush to a new session low, then SPY's first up bar), and the stock must have held its own LOD through the flush.

Rules (plain English):
  1. SPY event: on one of the 3 bars before this bar, SPY closed at a new session low (spy_fo below every earlier
     spy_fo of the day), with spy_fo <= -0.4% and breadth <= 0.35 on that bar.
  2. The stock's LOD is >= 6 bars old (the last bar at the running LOD is >= 6 bars back; an LOD from 09:30-09:45
     counts as old), and the close is above VWAP or at most 0.1 x atr_d below it.
  3. Relative strength: fromOpen - spy_fo >= +0.8 percentage points.
  4. This bar: SPY closes up (spy_fo above the previous bar's) and the stock closes up (close above the previous
     close; the frame has no bar open).
  Entry: that close; only the top 3 symbols per event (same date and bar) by rule 3 (adv20 >= $20M universe).
  Stop (GEOM S): max(LOD, entry - 0.5 x atr_d). Target: HOD (needs HOD above the entry). Flat 15:55.
  Bar close 10:00-14:30. The '-t1s1' file is the idea's baseline config (same mask, GEOM t1s1).
Frame note: SPY's 'session low' is tracked on spy_fo from the 09:50 bar on (09:30-09:45 SPY bars are not in the
context); the top-3 ranking is cross-sectional, so live it needs a scanner-level rank.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = ["spy_fo", "breadth"]
TOPN = 3
LAYERS = ["SPY new session low in the last 3 bars with spy_fo <= -0.4 and breadth <= 0.35",
          "stock LOD >= 6 bars old, close >= VWAP - 0.1 ATR", "fromOpen - spy_fo >= 0.8",
          "SPY bar up and stock bar up", "top 3 per event by RS", "stop max(LOD, entry - 0.5 ATR), target HOD",
          "10:00-14:30"]

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
def _kern(b, e, l, lod, c, spy, br):
    n = len(l)
    age = np.full(n, np.nan)
    ev = np.zeros(n, np.bool_)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        j = -1
        mn = 1e18
        for i in range(i0, i1):
            if l[i] <= lod[i] + 1e-6 * c[i]:
                j = i
            age[i] = (i - j) if j >= 0 else (i - i0 + 1)
            if i > i0 and spy[i] < mn and spy[i] <= -0.4 and br[i] <= 0.35:
                ev[i] = True
            if spy[i] == spy[i]:
                mn = min(mn, spy[i])
    return age, ev


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df or "breadth" not in df:
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    spy, br = _f(df, "spy_fo"), _f(df, "breadth")
    bb, ee = _segments(k)
    age, ev = _kern(bb, ee, b["l"], b["lod"], c, spy, br)
    evf = ev.astype(float)
    rs = _f(df, "fromOpen") - spy
    with np.errstate(invalid="ignore"):
        m = (_prev(evf, k, 1) == 1) | (_prev(evf, k, 2) == 1) | (_prev(evf, k, 3) == 1)
        m &= age >= 6
        m &= c > b["vwap"] - 0.1 * atr
        m &= rs >= 0.8
        m &= (spy > _prev(spy, k)) & (c > _prev(c, k))
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        if "adv20" in df:
            m &= _f(df, "adv20") >= 20e6
        stop = np.maximum(b["lod"], c - 0.5 * atr)
        tgt = np.where(b["hod"] > c, b["hod"], np.nan)
        m &= np.isfinite(tgt) & (stop < c)
    idx = np.flatnonzero(m)
    if len(idx):
        t = pd.DataFrame({"i": idx, "d": df["date"].astype(str).to_numpy()[idx], "tod": tod[idx], "rs": rs[idx]})
        t["rk"] = t.groupby(["d", "tod"])["rs"].rank(ascending=False, method="first")
        m = np.zeros(len(df), bool)
        m[t.loc[t["rk"] <= TOPN, "i"].to_numpy()] = True
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def target_price(f, i, stop):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[1][i]) if s is not None and s[1] is not None else float("nan")
