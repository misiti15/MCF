"""pod-qs-30m-lower-lows-etf-long-holdtr - Three lower-high/lower-low 30-min bars on an ETF in a daily uptrend: buy, hold to the close (LONG).

Source: Quantified Strategies 'Intraday strategies: a crude oil backtest' (three consecutive lower lows / lower
highs, buy, exit at the close), translated to equity ETFs.
URL: https://quantifiedstrategies.substack.com/p/intraday-strategies-a-crude-oil-backtest

VARIANT of the index dip-bounce family (IDX1-5, LD, idxdip1015: % drop thresholds). Stated change: the trigger is a
price-structure sequence (3 straight lower-high AND lower-low 30-min bars) at fixed checkpoints, held to the close.
Rules (plain English):
  Symbols: SPY, QQQ, IWM, DIA and the 11 sector SPDRs.
  30-min bars are built from the 5m bars; the first one (09:30-10:00) is the day's high/low at 10:00.
  1. At a checkpoint T in 11:00 / 11:30 / 12:00, the last three completed 30-min bars each have a high AND a low
     below the prior 30-min bar's (three comparisons, so four bars; at 11:00 only three bars exist, so in practice
     11:30 and 12:00 can fire - kept as written).
  2. D-1 close > daily SMA200 (completed days; data limit: lib.daily() starts 2024-10-01 and restarts after the locked
     gap, so the SMA uses at least 100 and up to 200 completed days - it is undefined, and the module silent, before
     ~mid-2025).
  3. fromOpen <= -0.3% at T.  4. RSI(14) (5m) <= 40.
  Entry: the T close (first qualifying checkpoint). Stop 0.25 x atr_d (1R). Exit holdtr: stop 1R, then a 1R trail once +1R, flat 15:55 (the alt exit the idea named).
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; daily values come
from completed days only.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "holdtr"
WINDOW = (1100, 1200)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
LAYERS = ["ETF universe", "3 straight lower-high/lower-low 30-min bars at 11:00/11:30/12:00", "D-1 close > daily SMA200",
          "fromOpen <= -0.3%", "RSI(14) <= 40", "holdtr exit"]

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
    dd = _map_daily(df, k, ["d_close", "sma200"])
    if dd is None:
        return z
    mins = (tod // 100) * 60 + tod % 100
    bk = np.where(mins <= 600, 0, np.ceil((mins - 600) / 30.0)).astype(np.int64)   # 30-min bucket; 0 = 09:30-10:00
    # bucket highs / lows per symbol-day (each bucket is fully completed by the checkpoint that reads it)
    g = pd.DataFrame({"k": k, "bk": bk, "h": h, "l": l})
    agg = g.groupby(["k", "bk"]).agg(H=("h", "max"), L=("l", "min"))
    H = {}
    L = {}
    for j in range(0, 6):
        H[j] = np.full(len(df), np.nan)
        L[j] = np.full(len(df), np.nan)
    hod10 = _at(b["hod"], k, tod, 1000)                       # first 30-min bar = the day's range at 10:00
    lod10 = _at(b["lod"], k, tod, 1000)
    H[0], L[0] = hod10, lod10
    idx = pd.MultiIndex.from_arrays([k, np.full(len(k), 0)])
    for j in range(1, 6):
        idx = pd.MultiIndex.from_arrays([k, np.full(len(k), j)])
        H[j] = agg["H"].reindex(idx).to_numpy(float)
        L[j] = agg["L"].reindex(idx).to_numpy(float)
    m = np.zeros(len(df), dtype=bool)
    with np.errstate(invalid="ignore"):
        for T, last in ((1100, 2), (1130, 3), (1200, 4)):
            ok = tod == T
            for j in range(last - 2, last + 1):               # the last three completed bars each lower than the prior
                if j - 1 < 0:
                    ok &= False
                    continue
                ok &= (H[j] < H[j - 1]) & (L[j] < L[j - 1])
            m |= ok
        m &= dd["d_close"] > dd["sma200"]
        m &= _f(df, "fromOpen") <= -0.3
        m &= _f(df, "rsi") <= 40
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
