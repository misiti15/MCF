"""pod-of-dante-insideday-fail-pm-short - Inside-day failure: poke through the inside day's high, reclaim, target the other side (SHORT, 13:00-15:00 try).

Source: Trader Dante (Tom Dante) X post on the 'Inside Day Failure'; Dante SFP material.
URL: https://twitter.com/Trader_Dante/status/1045012059627442176

VARIANT of CWT14-failbrk-pdl / -pdh. Stated change: D-1 must be an INSIDE day and the target is the OPPOSITE side of
the inside day (structural), not a fixed R. Opposite trigger of pod-traderlion-insideday-pdh-long.
Rules (plain English, LONG; SHORT mirrors at PDH):
  1. D-1 inside D-2: PDH < D-2 high and PDL > D-2 low (lib.daily(), completed days).
  2. Today's open between PDL and PDH and |open - prior close| <= 0.5 x atr_d.
  3. The LOD (so far) undercuts PDL by 0.05-0.50 x atr_d.
  4. A close back above PDL within 3 bars of the bar that set the LOD (a LOD set before 09:50 counts as the 09:45 bar).
  5. SPY not printing a new session low on that bar (spy_fo above its running min of the earlier bars since 09:50 -
     a close-based proxy).
  Entry: close. Stop (GEOM S): LOD - 0.05 x atr_d. Target: PDH - 0.02 x atr_d, else flat 15:55.
  Bar close 13:00-15:00 (the separate afternoon try the idea named).
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; daily values come
from completed days only.
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1300, 1500)
CONTEXT = ["spy_fo"]
LAYERS = ["D-1 inside day", "open inside D-1 range, small gap", "HOD overshoots PDH by 0.05-0.5 ATR",
          "close back below PDH within 3 bars", "SPY not at a new session high",
          "stop beyond the extreme + 0.05 ATR, target the other side of the inside day"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ST = {}
_DC = {}
ETFS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day k (NaN when that bar is in another group)."""
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


def _gcummin(x, k):
    return pd.Series(np.asarray(x, float)).groupby(k).cummin().to_numpy(float)


def _gcummax(x, k):
    return pd.Series(np.asarray(x, float)).groupby(k).cummax().to_numpy(float)


def _rowpos(k):
    """0-based bar index within the symbol-day."""
    return _gcum(np.ones(len(k)), k) - 1


def _at(x, k, tod, T):
    """Value of x on the bar that closes at T, broadcast to its symbol-day. Used only on rows with tod >= T."""
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
    b["sma20"] = c / (1 + _f(df, "sma20_dist_pct") / 100)
    return b


def _lib():
    try:
        import lib
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
        import lib
    return lib


def _daily_feats():
    """Per (symbol, date D): daily values as of D-1's close (completed days only). Series restart after a calendar
    gap > 7 days (the locked block is absent from lib.daily())."""
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
    pcl = gc.shift(1)
    tr = pd.concat([h - l, (h - pcl).abs(), (l - pcl).abs()], axis=1).max(axis=1)
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "d_close": c, "d_high": h, "d_low": l,
        "d_high_p": h.groupby(g).shift(1), "d_low_p": l.groupby(g).shift(1),
        "sma200": gc.transform(lambda x: x.rolling(200, min_periods=100).mean()),
        "atr14": tr.groupby(g).transform(lambda x: x.rolling(14).mean()),
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


def _map_spy_atr_pct(df, k):
    """SPY daily ATR(14) as of D-1, in % of SPY's D-1 close, per row."""
    f = _daily_feats()
    if f is None:
        return None
    s = f[f["symbol"] == "SPY"][["date", "atr14", "d_close"]]
    st = _start(k)
    u = pd.DataFrame({"date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(s, on="date", how="left")
    v = (m["atr14"] / m["d_close"] * 100).to_numpy(float)
    return v[np.cumsum(st) - 1]


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
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    dd = _map_daily(df, k, ["d_high", "d_low", "d_high_p", "d_low_p"])
    if dd is None:
        return z
    pdh, pdl, opn, pc = dd["d_high"], dd["d_low"], b["opn"], b["pc"]
    pos = _rowpos(k)
    spy = _f(df, "spy_fo")
    with np.errstate(invalid="ignore", divide="ignore"):
        g = (dd["d_high"] < dd["d_high_p"]) & (dd["d_low"] > dd["d_low_p"])      # (1) D-1 inside D-2
        g &= (opn > pdl) & (opn < pdh) & (np.abs(opn - pc) <= 0.5 * atr)          # (2)
        if SIDE == "long":
            ext = b["lod"]
            newx = np.r_[True, ext[1:] < ext[:-1] - 1e-6 * c[1:]] | _start(k)
            first_new = _start(k) & (np.abs(l - ext) > 1e-6 * c)       # LOD set before 09:50 -> treat as 1 bar before
            setpos = np.where(newx & ~first_new, pos, np.where(first_new, -1.0, np.nan))
            setpos = pd.Series(setpos).groupby(k).ffill().to_numpy(float)
            und = pdl - ext
            m = (und >= 0.05 * atr) & (und <= 0.50 * atr)                         # (3) undercut of PDL
            m &= (c > pdl) & (pos - setpos <= 3)                                   # (4) close back above within 3 bars
            m &= spy > _lag(_gcummin(spy, k), k)                                   # (5) SPY not at a new session low
            stop = ext - 0.05 * atr
            tgt = pdh - 0.02 * atr
        else:
            ext = b["hod"]
            newx = np.r_[True, ext[1:] > ext[:-1] + 1e-6 * c[1:]] | _start(k)
            first_new = _start(k) & (np.abs(h - ext) > 1e-6 * c)
            setpos = np.where(newx & ~first_new, pos, np.where(first_new, -1.0, np.nan))
            setpos = pd.Series(setpos).groupby(k).ffill().to_numpy(float)
            ov = ext - pdh
            m = (ov >= 0.05 * atr) & (ov <= 0.50 * atr)
            m &= (c < pdh) & (pos - setpos <= 3)
            m &= spy < _lag(_gcummax(spy, k), k)
            stop = ext + 0.05 * atr
            tgt = pdl + 0.02 * atr
        m &= g & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
