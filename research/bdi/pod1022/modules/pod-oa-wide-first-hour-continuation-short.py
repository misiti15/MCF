"""pod-oa-wide-first-hour-continuation-short - Wide first-hour range on index ETFs: enter at 10:30 in its direction,
hold to the close (SHORT side; the source idea is both sides, scored as two modules).

Source: Option Alpha research blog 'Trading the Opening Range: Mean Reversion vs Trend Following' (SPY).
URL: https://optionalpha.com/blog/opening-range-breakout

VARIANT of intraday_momentum / intraday-momentum-paper (09:30-10:00 sign -> late trade) and t7-noise-band (retired).
Stated change: a first-hour range-SIZE condition, entry at 10:30, hold for the rest of the session.

Rules (plain English), SYMBOLS SPY, QQQ, IWM, DIA (SHORT shown; LONG is the mirror):
  1. First-hour range = HOD - LOD as of the 10:30 bar (09:30-10:30). As % of price it is above the 75th percentile of
     the same symbol's first-hour ranges over its trailing 60 completed sessions (prior sessions only, at least 40
     required), AND it is >= 0.8 x atr_d. The trailing table is built from the open-history frames (research/history2y
     lib.load_month); the locked block is never read, the trailing window simply skips it.
  2. 10:30 close below the open and below VWAP (SHORT: below / LONG: above).
  3. The close is in the lower half of the first-hour range.
  Entry: the first qualifying bar close 10:30-10:40. Stop (GEOM S): first-hour midpoint, capped at entry + 0.5 x atr_d. Exit 15:55 (no target).
  This module: SHORT. No tweak used. Only bars up to the decision bar. Costs in (scorer).
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1030, 1040)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = []
LAYERS = ["SPY/QQQ/IWM/DIA", "first-hour range > trailing-60 P75 and >= 0.8 ATR", "10:30 close below the open and below VWAP",
          "close in the lower half of the first-hour range", "stop first-hour mid capped at 0.5 ATR, hold to 15:55",
          "10:30-10:40 ET"]

import sys
from pathlib import Path
import numpy as np
import pandas as pd

_ST = {}


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


def _at(x, k, tod, T):
    """Value of x on the bar closing at T, broadcast to its symbol-day. Use only on rows with tod >= T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


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

_DC = {}


def _fh_table(syms):
    """Per (symbol, date): first-hour range % and its trailing-60 P75 over PRIOR sessions (min 40)."""
    if "t" in _DC:
        return _DC["t"]
    t = None
    try:
        try:
            import lib
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
            import lib
        rows = []
        for mo in lib.months():
            x = lib.load_month(mo, columns=["symbol", "date", "tod", "close", "dist_hod_atr", "dist_lod_atr", "atr_d"])
            x = x[(x["symbol"].astype(str).isin(syms)) & (x["tod"] == 1030)]
            rows.append(x)
        x = pd.concat(rows, ignore_index=True)
        x["symbol"] = x["symbol"].astype(str)
        x["rng"] = (x["dist_hod_atr"] + x["dist_lod_atr"]) * x["atr_d"] / x["close"] * 100
        x = x.sort_values(["symbol", "date"]).reset_index(drop=True)
        x["p75"] = x.groupby("symbol")["rng"].transform(
            lambda v: v.shift(1).rolling(60, min_periods=40).quantile(0.75))
        x["date"] = x["date"].astype(str)
        t = x[["symbol", "date", "p75"]]
    except Exception:
        t = None
    _DC["t"] = t
    return t


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    t = _fh_table(SYMBOLS)
    if t is None:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].astype(str).to_numpy()})
    p75 = u.merge(t, on=["symbol", "date"], how="left")["p75"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        H = _at(hod, k, tod, 1030)
        L = _at(lod, k, tod, 1030)
        c30 = _at(c, k, tod, 1030)
        rng = H - L
        rpct = rng / c30 * 100
        mid = (H + L) / 2
        m = (tod >= 1030) & (rpct > p75) & (rng >= 0.8 * atr)
        fo, vd = _f(df, "fromOpen"), _f(df, "vwapDistPct")
        if SIDE == "short":
            m &= (fo < 0) & (vd < 0) & (c < mid)
            stop = np.minimum(mid, c + 0.5 * atr)
        else:
            m &= (fo > 0) & (vd > 0) & (c > mid)
            stop = np.maximum(mid, c - 0.5 * atr)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, None)
    return np.asarray(m, dtype=bool)
