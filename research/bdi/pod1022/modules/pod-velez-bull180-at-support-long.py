"""pod-velez-bull180-at-support-long - Velez Bull 180 at VWAP or SMA20 in an uptrend (LONG).

Source: Oliver Velez Bull/Bear 180 control-bar pattern (TradingView implementation).
URL: https://br.tradingview.com/script/HxrVWbV8

NEW trigger family as a gated pattern (unconditioned candle patterns failed before); gated by trend and location.
Rules (plain English, LONG; SHORT = Bear 180 mirror):
  1. Bar i-1 range >= 1.5 x the mean range of the 10 bars before it (same day; until 10 same-day bars exist, the
     frame's 5m ATR(14) at bar i-2 stands in), close in its lowest 30%, down vs its prior close.
  2. Bar i up (close > close_(i-1), the bar open ~ the prior close), closes above high_(i-1), close in its top 25%.
  3. Low of bar i-1 or bar i within 0.1 x atr_d of the session VWAP or the 5m SMA20 (at that bar).
  4. sma20_slope_pct > 0 and close > VWAP.
  Entry: close. Stop (GEOM S): min(low_(i-1), low_i) - 0.02 x atr_d. Target: 2 x stop distance or HOD, whichever is
  nearer (HOD used only when it is above the entry). Bar close 10:00-14:30. Flat 15:55.
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; daily values come
from completed days only.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
LAYERS = ["wide bar i-1 (>= 1.5x mean range) closing at its low 30%", "bar i reverses through bar i-1's high, close in its top 25%",
          "low of i-1 or i within 0.1 ATR of VWAP or SMA20", "sma20 slope and close vs VWAP agree with the side",
          "stop beyond the two-bar extreme + 0.02 ATR, target nearer of 2R / HOD", "10:00-14:30 ET"]

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
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    s = 1.0 if SIDE == "long" else -1.0
    with np.errstate(invalid="ignore", divide="ignore"):
        rng = h - l
        pos = (c - l) / rng                                   # close location in the bar, 0 = low, 1 = high
        # mean range of the 10 bars before bar i-1 (same day); before 10 exist, the 5m ATR(14) at bar i-2
        rl = np.vstack([_lag(rng, k, j) for j in range(2, 12)])
        cnt = np.sum(np.isfinite(rl), axis=0)
        mr = np.where(cnt >= 10, np.nanmean(np.where(np.isfinite(rl), rl, np.nan), axis=0),
                      _lag(_f(df, "atrPct") * c / 100, k, 2))
        rng1, pos1, c1, c2 = _lag(rng, k), _lag(pos, k), _lag(c, k), _lag(c, k, 2)
        h1, l1 = _lag(h, k), _lag(l, k)
        m = rng1 >= 1.5 * mr                                   # (1) wide bar i-1 ...
        if SIDE == "long":
            m &= (pos1 <= 0.30) & (c1 < c2)                     # ... closing in its lowest 30%, down vs its prior close
            m &= (c > c1) & (c > h1) & (pos >= 0.75)            # (2) up bar closing above high_{i-1}, top 25%
            ext1, ext = l1, l
        else:
            m &= (pos1 >= 0.70) & (c1 > c2)
            m &= (c < c1) & (c < l1) & (pos <= 0.25)
            ext1, ext = h1, h
        vw1, sm1 = _lag(b["vwap"], k), _lag(b["sma20"], k)
        tol = 0.1 * atr
        near = (np.abs(ext1 - vw1) <= tol) | (np.abs(ext1 - sm1) <= tol) | \
               (np.abs(ext - b["vwap"]) <= tol) | (np.abs(ext - b["sma20"]) <= tol)
        m &= near                                               # (3) at VWAP or SMA20
        m &= (s * _f(df, "sma20_slope_pct") > 0) & (s * b["vd"] > 0)   # (4) trend + side of VWAP
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        if SIDE == "long":
            stop = np.minimum(l1, l) - 0.02 * atr
            t2 = c + 2.0 * (c - stop)
            tgt = np.where(b["hod"] > c, np.minimum(t2, b["hod"]), t2)
        else:
            stop = np.maximum(h1, h) + 0.02 * atr
            t2 = c - 2.0 * (stop - c)
            tgt = np.where(b["lod"] < c, np.maximum(t2, b["lod"]), t2)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
