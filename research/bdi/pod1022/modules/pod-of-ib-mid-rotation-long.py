"""pod-of-ib-mid-rotation-long - Initial-balance midpoint rotation on balance days (IB-50) (LONG).

Source: edgeful 'IB 50' playbook with futures trader Zinc; Axia Volume Profile course notes ('normal day: wide IB,
rest of session inside').
URL: https://help.edgeful.com/en/articles/15326958-how-to-access-the-ib-50-mr-zinc-playbook

VARIANT, opposite logic of wi-ib-narrow-extension (trade the IB break). Different trigger from
pod-hart-serafini-midday-range-edge-fade (touch of the edge): here the entry is a close back across the IB midpoint
after a visit to the far quarter.
Rules (plain English, LONG; SHORT mirrors):
  IB = the day's high / low at 10:30 (09:30-10:30), carried forward.
  1. Bar close 10:35-14:30 and HOD / LOD still equal the IB high / low (no extension yet).
  2. IB width 0.35-0.8 x atr_d.
  3. |spy_fo| < 0.4% and breadth 0.35-0.65.
  4. Price touched the lower 25% of the IB within the last 6 bars (this bar included).
  5. This bar closes back above the IB midpoint (prior close at or below it) with RSI(14) 40-60.
  Entry: close. Stop (GEOM S): IB low - 0.05 x atr_d. Target: IB high - 0.02 x atr_d. Flat 15:55.
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; daily values come
from completed days only.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1035, 1430)
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["no IB extension yet", "IB width 0.35-0.8 ATR", "|spy_fo| < 0.4%, breadth 0.35-0.65",
          "visited the lower IB quarter in 6 bars", "close crosses back above the IB mid, RSI 40-60",
          "stop beyond the IB + 0.05 ATR, target the other IB edge"]

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
    if not len(df) or "spy_fo" not in df or "breadth" not in df:
        return z
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    ibh = _at(b["hod"], k, tod, 1030)
    ibl = _at(b["lod"], k, tod, 1030)
    w = ibh - ibl
    mid = (ibh + ibl) / 2
    rsi = _f(df, "rsi")
    br = _f(df, "breadth")
    with np.errstate(invalid="ignore", divide="ignore"):
        eps = 1e-6 * c
        m = (tod >= 1035) & (np.abs(b["hod"] - ibh) <= eps) & (np.abs(b["lod"] - ibl) <= eps)   # (1) no extension
        m &= (w >= 0.35 * atr) & (w <= 0.8 * atr)                                               # (2)
        m &= (np.abs(_f(df, "spy_fo")) < 0.4) & (br >= 0.35) & (br <= 0.65)                     # (3)
        m &= (rsi >= 40) & (rsi <= 60)
        c1 = _lag(c, k)
        if SIDE == "long":
            lo6 = np.nanmin(np.vstack([_lag(l, k, j) if j else l for j in range(6)]), axis=0)
            m &= lo6 <= ibl + 0.25 * w                                                          # (4) visit lower quarter
            m &= (c > mid) & (c1 <= mid)                                                        # (5) close back above mid
            stop = ibl - 0.05 * atr
            tgt = ibh - 0.02 * atr
        else:
            hi6 = np.nanmax(np.vstack([_lag(h, k, j) if j else h for j in range(6)]), axis=0)
            m &= hi6 >= ibh - 0.25 * w
            m &= (c < mid) & (c1 >= mid)
            stop = ibh + 0.05 * atr
            tgt = ibl + 0.02 * atr
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
