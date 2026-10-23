"""pod-raschke-breadth-thrust-vwap-reclaim-long-B - Breadth thrust (internals swing from washed out to strong): buy
the laggard's VWAP reclaim (LONG). Config B (holdtr).

Source: Linda Raschke - interviews and 'Trading Sardines' (2019) on reading TICK / breadth swings from one extreme to
the other as the intraday turn signal. Not re-fetched in round 2 (search budget used up, WebFetch DNS failure).
URL: https://lbrgroup.com

VARIANT of pod-raschke-blindfold-breadth-div (breadth LEVEL divergence at a new 20-bar low) and harness example EX1
(static breadth >= 0.5 gate, fromOpen > 0.3). Stated change: the trigger is a breadth SWING, not a breadth level, and
the stock may be red on the day.

Rules (plain English, LONG). breadth = share of the universe above its own VWAP, on the (date, tod) series.
  1. Thrust bar T: breadth >= 0.60 now and the minimum breadth over the previous 12 bars of the same date is <= 0.30
     (frames start at 09:50; early in the day the earlier bars that exist are used). Only the first T per date counts.
  2. Within 6 bars after T (bars T+1 .. T+6 of the date's bar sequence; pre-declared reading of 'after'), the stock's
     bar has vwapReclaim == 1 (close above VWAP, at or below it 3 bars ago).
  3. fromOpen between -1.5% and +0.5%: a laggard that took part in the flush.
  4. sma20_slope_pct > -0.05.
  5. dist_pdl_atr > 0 (still above the prior-day low).
  Bar close 10:30-14:30. Entry: the reclaim bar's close (first per symbol-day).
  Exits: config A = t05s1 (target 0.5R, stop 1R); config B = holdtr (1R stop, 1R trail once +1R). Flat 15:55.
Both configs are stated in the idea up front (2 configurations tried); no other tweak. No tuning on valid.
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
SIDE = "long"
GEOM = "holdtr"
WINDOW = (1030, 1430)
CONTEXT = ["breadth"]
LAYERS = ["first breadth thrust of the date: breadth >= 0.60 after min <= 0.30 in previous 12 bars",
          "vwapReclaim == 1 within 1-6 bars after T", "fromOpen -1.5..+0.5", "sma20_slope_pct > -0.05",
          "dist_pdl_atr > 0", "holdtr", "10:30-14:30 ET"]

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


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "breadth" not in df:
        return z
    t = _date_table(df, "breadth")
    if not len(t):
        return z
    g = t.groupby("date")
    t["ord"] = g.cumcount().astype(float)
    bmin = g["v"].transform(lambda x: x.shift(1).rolling(12, min_periods=1).min())
    thr = ((t["v"] >= 0.60) & (bmin <= 0.30)).astype(float)
    prior = thr.groupby(t["date"]).cumsum() - thr
    t["tord"] = np.where((thr > 0) & (prior == 0), t["ord"], np.nan)
    t["tord"] = t.groupby("date")["tord"].transform(lambda x: x.ffill())   # T's ordinal, known only from T onward
    mb = _map_back(df, t, ["ord", "tord"])
    since = mb["ord"] - mb["tord"]
    tod = df["tod"].to_numpy(np.int64)
    fo = _f(df, "fromOpen")
    with np.errstate(invalid="ignore"):
        m = (since >= 1) & (since <= 6)
        m &= _f(df, "vwapReclaim") == 1
        m &= (fo >= -1.5) & (fo <= 0.5)
        m &= _f(df, "sma20_slope_pct") > -0.05
        m &= _f(df, "dist_pdl_atr") > 0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
