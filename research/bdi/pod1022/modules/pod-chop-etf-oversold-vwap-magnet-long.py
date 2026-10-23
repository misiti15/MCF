"""pod-chop-etf-oversold-vwap-magnet-long - Choppy-day ETF oversold snap back to VWAP (LONG).

Source: Connors / Alvarez-style short-term ETF mean reversion (a Better System Trader guest topic), recast for 5-minute
bars. NOT verified against a specific episode (web blocked this run).
URL: https://alvarezquanttrading.com (no specific episode verified)

VARIANT of Reddit R03-vwap-fade (VWAP rubber band) and R11-rsi-os, which ran across all stocks and all days with a fixed
R geometry. Stated changes: ETFs only, a choppy-day gate, and a VWAP structural target.

Rules (plain English, LONG). SYMBOLS: SPY, QQQ, IWM, DIA, XLF, XLK, XLE, XLV, XLI, XLY, XLP, XLU, SMH, XBI, KRE.
  1. Bar close 10:30-14:30.
  2. Choppy, balanced tape: |spy_fo| <= 0.40 and breadth between 0.35 and 0.65.
  3. rsi5 <= 15.
  4. vwapDistPct <= -0.35 (stretched below VWAP).
  5. sma20_slope_pct >= -0.10 (not in a strong 5-minute downtrend).
  Entry: that bar's close. Stop (GEOM S): entry - 0.25 x atr_d. Target: session VWAP = close / (1 + vwapDistPct/100)
  as of the entry bar; else flat 15:55.
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "SMH", "XBI", "KRE"]
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["index / sector ETFs", "|spy_fo| <= 0.40", "breadth 0.35-0.65", "rsi5 <= 15", "vwapDistPct <= -0.35",
          "sma20_slope_pct >= -0.10", "stop entry - 0.25 ATR, target VWAP", "10:30-14:30 ET"]

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


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day (NaN across a day boundary)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each symbol-day."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _first(cond, k):
    """True only on the first True row of each symbol-day."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _date_table(df, col):
    """One row per (date, tod) with the market-wide column `col` (same value for every symbol), sorted."""
    t = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "tod": df["tod"].to_numpy(np.int64),
                      "v": _f(df, col)})
    t = t.dropna(subset=["v"]).drop_duplicates(["date", "tod"]).sort_values(["date", "tod"]).reset_index(drop=True)
    return t


def _map_back(df, t, cols):
    """Map (date, tod) table columns back to the rows of df."""
    idx = pd.MultiIndex.from_arrays([t["date"].to_numpy(), t["tod"].to_numpy()])
    q = pd.MultiIndex.from_arrays([df["date"].astype(str).to_numpy(), df["tod"].to_numpy(np.int64)])
    return {c: pd.Series(t[c].to_numpy(float), index=idx).reindex(q).to_numpy(float) for c in cols}


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "spy_fo" not in df or "breadth" not in df:
        return z
    tod = df["tod"].to_numpy(np.int64)
    c, atr, vd = _f(df, "close"), _f(df, "atr_d"), _f(df, "vwapDistPct")
    br = _f(df, "breadth")
    with np.errstate(invalid="ignore", divide="ignore"):
        m = np.isin(df["symbol"].astype(str).to_numpy(), SYMBOLS)
        m &= np.abs(_f(df, "spy_fo")) <= 0.40
        m &= (br >= 0.35) & (br <= 0.65)
        m &= _f(df, "rsi5") <= 15
        m &= vd <= -0.35
        m &= _f(df, "sma20_slope_pct") >= -0.10
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = c - 0.25 * atr
        tgt = c / (1 + vd / 100)
        m &= (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
