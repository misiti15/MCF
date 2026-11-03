"""TM3-gapup-drift-powerhour-short - ex30/time time / calendar setup (BDI 2026-11-03, research/bdi/ex30/time).
Overnight gap vs intraday drift, power hour: a name that gapped up >= 1% but has drifted >= 0.75 daily ATR
below its open, is under VWAP and within 0.15 ATR of its low of day at 14:30-15:00 - short into the close.
Exploratory account candidate; see research/bdi/ex30/time/NOTES.md. Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "t05s1"
WINDOW = (1430, 1500)
CONTEXT = []
LAYERS = ['gap >= +1.0%', 'move from open <= -0.75 daily ATR', 'dist above LOD <= 0.15 ATR', 'close < VWAP', 'bar close 14:30-15:00 ET']


def _features(df):
    """Per-bar features on a lab frame (one live symbol-day indexed by bar starts, or many offline symbol-days sorted by
    symbol, date, tod). Lags use only bars with tod >= 950 (history frames start at 09:50), so live = history."""
    n = len(df)

    def col(k):
        return df[k].to_numpy(dtype=float) if k in df else np.full(n, np.nan)

    if "date" in df:
        d = pd.to_datetime(pd.Series(np.asarray(df["date"]).astype(str)))
    elif isinstance(df.index, pd.DatetimeIndex):
        d = pd.Series(df.index.tz_localize(None).normalize() if df.index.tz is not None else df.index.normalize())
    elif "ts" in df:
        d = pd.to_datetime(pd.Series(np.asarray(df["ts"]))).dt.tz_localize(None).dt.normalize()
    else:
        d = pd.Series(pd.NaT, index=range(n))
    d = d.reset_index(drop=True)
    if "symbol" in df:
        key = pd.factorize(pd.Series(np.asarray(df["symbol"]).astype(str)) + "|" + d.astype(str))[0]
    else:
        key = np.zeros(n, dtype=int)
    tod = col("tod")
    early = tod < 950
    c, atr, fo = col("close"), col("atr_d"), col("fromOpen")
    hi = col("high")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + col("dist_hod_atr") * atr
        lod = c - col("dist_lod_atr") * atr
    s = pd.DataFrame({"k": key, "c": np.where(early, np.nan, c), "hi": np.where(early, np.nan, hi),
                       "hod": np.where(early, np.nan, hod), "lod": np.where(early, np.nan, lod)})
    g = s.groupby("k", sort=False)
    F = dict(tod=tod, c=c, atr=atr, hod=hod, lod=lod, spy=col("spy_fo"), prng=col("spy_prng"), gap=col("gap"),
             vwd=col("vwapDistPct"), dhod=col("dist_hod_atr"), dlod=col("dist_lod_atr"),
             dom=d.dt.day.to_numpy(dtype=float), dow=d.dt.weekday.to_numpy(dtype=float))
    F["prev_c"] = g["c"].shift(1).to_numpy()
    F["prev_hi"] = g["hi"].shift(1).to_numpy()
    F["hod6"] = g["hod"].shift(6).to_numpy()
    F["lod2"] = g["lod"].shift(2).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        F["move"] = (c - c / (1 + fo / 100)) / atr
        F["rng"] = F["dhod"] + F["dlod"]
        F["pos"] = F["dlod"] / F["rng"]
        F["vwa"] = F["vwd"] / 100 * c / atr
    return F


def mask(df) -> np.ndarray:
    F = _features(df)
    tod = F["tod"]
    with np.errstate(invalid="ignore"):
        m = (F["gap"] >= 1.0) & (F["move"] <= -0.75) & (F["dlod"] <= 0.15) & (F["vwd"] < 0)
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
