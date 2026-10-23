"""pod-unger-daydrop-orb-long - Day-Drop filter: 30-min opening-range break long after a weak prior close (LONG).

Source: Andrea Unger (Better System Trader ep 016 / 045) 'The Day Drop Pattern', Stocks & Commodities V.41:04,
Benzinga summary.
URL: https://benzinga.com/trading-ideas/23/11/35701496/trading-the-nasdaq-improving-a-strategy-with-the-day-drop-pattern-as-a-downtrend-filter

VARIANT of orb20_a (20-min ORB, both sides). Stated change: long only, gated by Unger's Day-Drop filter on D-1 (no
IBS / close-location feature has been used in MCF before).

Rules (plain English):
  1. Day Drop: D-1 close location (close - low) / (high - low) <= 0.25 (daily table, completed day D-1).
  2. D-1 close above the daily SMA50 (closes up to D-1).
  3. Gap (open - prior close) between -1.0 and +0.5 x atr_d.
  4. 10:05-11:30 bar close: the close crosses above the 09:30-10:00 high (the running HOD at the 10:00 bar, which
     includes the 09:30-09:45 bars) - previous close at or below it - with volumeRatio >= 1.2 and the close above
     session VWAP.
  Entry: that close. Stop (GEOM S): the tighter of the 09:30-10:00 midpoint and entry - 0.5 x atr_d. Target: 2R
  (entry + 2 x (entry - stop)), else flat 15:55. One trade per symbol-day (scorer).
Frame note: SMA50 needs 50 post-gap daily rows, so trades start around mid-May 2025.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1005, 1130)
LAYERS = ["D-1 IBS <= 0.25", "D-1 close > daily SMA50", "gap -1.0..+0.5 x ATR",
          "close crosses above the 09:30-10:00 high, volumeRatio >= 1.2, above VWAP",
          "stop tighter of OR mid / 0.5 ATR, target 2R, flat 15:55", "10:05-11:30"]

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


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    dd = _map_daily(df, k, ["ibs", "d_close", "sma50"])
    if dd is None:
        return z
    orh, orl = _at(b["hod"], k, tod, 1000), _at(b["lod"], k, tod, 1000)
    with np.errstate(invalid="ignore"):
        m = dd["ibs"] <= 0.25
        m &= dd["d_close"] > dd["sma50"]
        gp = b["opn"] - b["pc"]
        m &= (gp >= -1.0 * atr) & (gp <= 0.5 * atr)
        m &= (c > orh) & (_prev(c, k) <= orh)
        m &= (_f(df, "volumeRatio") >= 1.2) & (c > b["vwap"])
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = np.maximum((orh + orl) / 2, c - 0.5 * atr)
        tgt = c + 2 * (c - stop)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def target_price(f, i, stop):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[1][i]) if s is not None and s[1] is not None else float("nan")
