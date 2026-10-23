"""_cwt3_bars - shared helpers for the pod-cwt3-* lab modules (not a setup; no SIDE / mask).

Builds point-in-time inputs the scorer frame does not carry:
  * full-session continuous 5-minute bars (09:35..15:55) per symbol: the history frames (09:50-15:00, ALL symbol-days,
    not only the scorer's post-blackout rows) + the head/tail table (09:35-09:45, 15:05-15:55), for the frame's month
    and the previous OPEN month (warm-up). The rule-19 locked block (2024-11..2025-02) is never read: a locked or
    missing previous month is simply skipped (the first weeks after it are warm-up NaN).
  * raw 5-minute open / volume from frames_tf/5min (160 liquid symbols, 09:50-15:00).
  * daily values as of D-1's close (lib.daily(), completed days only).
Every feature that callers derive from these is causal: rolling windows end at the decision bar, daily values end at
D-1. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[4]
_HIST = _ROOT / "research" / "history2y"
_HEADTAIL = _ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
_TF5 = _HIST / "data" / "frames_tf" / "5min"
_LOCKED = ("2024-11-01", "2025-02-28")
_LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
_CACHE = {}
_FULL = {}

ETFS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
LARGE30 = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX", "JPM", "V", "MA", "COST",
           "LLY", "UNH", "WMT", "XOM", "ORCL", "CRM", "MU", "INTC", "PLTR", "TSM", "BAC", "GS", "CAT", "CVX", "JNJ",
           "AMAT"]


def lib():
    try:
        import lib as L
    except ImportError:
        sys.path.insert(0, str(_HIST))
        import lib as L
    return L


def f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def lag(x, k, n=1):
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def at_tod(x, k, tod, T):
    """x on the bar closing at T, broadcast to its symbol-day (use only on rows with tod >= T)."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def base(df):
    c, atr = f(df, "close"), f(df, "atr_d")
    b = dict(c=c, h=f(df, "high"), l=f(df, "low"), atr=atr, tod=df["tod"].to_numpy(np.int64))
    with np.errstate(invalid="ignore", divide="ignore"):
        b["hod"] = c + f(df, "dist_hod_atr") * atr
        b["lod"] = c - f(df, "dist_lod_atr") * atr
        b["pdh"] = c + f(df, "dist_pdh_atr") * atr
        b["pdl"] = c - f(df, "dist_pdl_atr") * atr
        b["opn"] = c / (1 + f(df, "fromOpen") / 100)
        b["pc"] = b["opn"] / (1 + f(df, "gap") / 100)
        b["vwap"] = c / (1 + f(df, "vwapDistPct") / 100)
        b["sma20"] = c / (1 + f(df, "sma20_dist_pct") / 100)
        b["atr5"] = f(df, "atrPct") / 100 * c
    return b


def rt_cost(px, tod):
    """Round-trip cost per share, RESEARCH_RULES rule 1 (1c + 1 bps per side, entry x1.4 before 10:30)."""
    side = 0.01 + 1e-4 * px
    return side * np.where(tod < 1030, 1.4, 1.0) + side


def month_of(df):
    d = pd.Timestamp(min(df["date"]))
    return f"{d.year:04d}-{d.month:02d}"


def prev_month(m):
    y, mo = int(m[:4]), int(m[5:7])
    y, mo = (y - 1, 12) if mo == 1 else (y, mo - 1)
    return f"{y:04d}-{mo:02d}"


def _open_months(df, warm=True):
    m = month_of(df)
    L = lib()
    ok = set(L.months()) - _LOCKED_MONTHS
    out = []
    if warm and prev_month(m) in ok:
        out.append(prev_month(m))
    if m in ok:
        out.append(m)
    d1 = pd.Timestamp(max(df["date"]))
    m1 = f"{d1.year:04d}-{d1.month:02d}"
    if m1 != m and m1 in ok:
        out.append(m1)
    return out


def full_bars(df, symbols=None, warm=True):
    """Continuous full-session 5m bars (symbol, date, tod, h, l, c) for the frame's symbols, previous open month
    included as warm-up. Never reads a locked month."""
    syms = sorted(set(df["symbol"].astype(str))) if symbols is None else sorted(set(symbols))
    months = _open_months(df, warm)
    ck = ("full", tuple(months), tuple(syms))
    if ck in _FULL:
        return _FULL[ck]
    _FULL.clear()
    L = lib()
    parts = []
    for mo in months:
        if mo in _LOCKED_MONTHS or mo in L.LOCKED_MONTHS:
            continue
        import pyarrow.dataset as ds
        x = ds.dataset(str(L.DATA / "frames" / f"month={mo}"), format="parquet").to_table(
            columns=["symbol", "date", "tod", "high", "low", "close"],
            filter=ds.field("symbol").isin(syms)).to_pandas()
        x["symbol"] = x["symbol"].astype(str)
        x["date"] = pd.to_datetime(x["date"]).dt.date
        parts.append(pd.DataFrame({"symbol": x["symbol"].to_numpy(object), "date": x["date"].to_numpy(),
                                   "tod": x["tod"].to_numpy(np.int64), "h": x["high"].to_numpy(float),
                                   "l": x["low"].to_numpy(float), "c": x["close"].to_numpy(float)}))
    if not parts:
        return None
    a = pd.Timestamp(months[0] + "-01")
    b = pd.Timestamp(months[-1] + "-01") + pd.offsets.MonthBegin(1)
    assert not (str(a.date()) <= _LOCKED[1] and str((b - pd.Timedelta(days=1)).date()) >= _LOCKED[0]), "locked"
    try:
        ht = pd.read_parquet(_HEADTAIL, columns=["symbol", "date", "tod", "h", "l", "c"],
                             filters=[("date", ">=", a), ("date", "<", b)])
        ht["symbol"] = ht["symbol"].astype(str)
        ht = ht[ht["symbol"].isin(syms) & ((ht["tod"] < 950) | (ht["tod"] > 1500))]
        ht["date"] = pd.to_datetime(ht["date"]).dt.date
        parts.append(pd.DataFrame({"symbol": ht["symbol"].to_numpy(object), "date": ht["date"].to_numpy(),
                                   "tod": ht["tod"].to_numpy(np.int64), "h": ht["h"].to_numpy(float),
                                   "l": ht["l"].to_numpy(float), "c": ht["c"].to_numpy(float)}))
    except Exception:
        pass
    p = pd.concat(parts, ignore_index=True).drop_duplicates(["symbol", "date", "tod"])
    p = p.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    _FULL[ck] = p
    return p


def tf5(df, symbols=None):
    """Raw 5m open / volume (frames_tf/5min) for the frame's months; NaN where a symbol is not covered."""
    syms = sorted(set(df["symbol"].astype(str))) if symbols is None else sorted(set(symbols))
    months = _open_months(df, warm=False)
    import pyarrow.dataset as ds
    parts = []
    for mo in months:
        p = _TF5 / f"month={mo}"
        if mo in _LOCKED_MONTHS or not p.exists():
            continue
        t = ds.dataset(str(p), format="parquet").to_table(
            columns=["symbol", "date", "tod", "open", "volume"], filter=ds.field("symbol").isin(syms)).to_pandas()
        t["symbol"] = t["symbol"].astype(str)
        t["date"] = pd.to_datetime(t["date"]).dt.date
        t["tod"] = t["tod"].astype(np.int64)
        parts.append(t)
    if not parts:
        return None
    return pd.concat(parts, ignore_index=True).drop_duplicates(["symbol", "date", "tod"])


def map_rows(df, tab, cols):
    """Left-join tab (symbol, date, tod, cols...) onto df's rows, in df order."""
    k = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(object), "date": df["date"].to_numpy(),
                      "tod": df["tod"].to_numpy(np.int64)})
    m = k.merge(tab[["symbol", "date", "tod"] + list(cols)], on=["symbol", "date", "tod"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}


def daily_feats():
    """Per (symbol, date D) daily values as of D-1's close (completed days). Series restart after a > 7-day gap."""
    if "daily" in _CACHE:
        return _CACHE["daily"]
    d = lib().daily()[["symbol", "date", "open", "high", "low", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    o, c, h, l = d["open"], d["close"], d["high"], d["low"]
    pcl = c.groupby(g).shift(1)
    tr = pd.concat([h - l, (h - pcl).abs(), (l - pcl).abs()], axis=1).max(axis=1)
    rng = (h - l).where(h > l)
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"].astype(str)})
    cur = {
        "d_open": o, "d_high": h, "d_low": l, "d_close": c,
        "d_openpos": (o - l) / rng, "d_closepos": (c - l) / rng,
        "sma50": c.groupby(g).transform(lambda x: x.rolling(50, min_periods=50).mean()),
        "atr14": tr.groupby(g).transform(lambda x: x.rolling(14, min_periods=14).mean()),
        "hi20_prev": h.groupby(g).transform(lambda x: x.shift(1).rolling(20, min_periods=20).max()),
        "lo20_prev": l.groupby(g).transform(lambda x: x.shift(1).rolling(20, min_periods=20).min()),
    }
    for nm, s in cur.items():
        out[nm + "_1"] = s.groupby(g).shift(1)          # value as of D-1 (row D)
    for nm in ("d_high", "d_openpos", "d_closepos"):
        out[nm + "_2"] = cur[nm].groupby(g).shift(2)     # value as of D-2
    _CACHE["daily"] = out
    return out


def map_daily(df, k, cols):
    t = daily_feats()
    st = start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(t, on=["symbol", "date"], how="left")
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}
