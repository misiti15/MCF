"""NEAR-MISS (swarm1017 rework-misc, 2026-10-17) - does NOT pass the research bar; Testing-account forward test only.
Educational only - not financial advice.
Rework of heat_fade_long: parent core (long heat score >= 57.5, gap > 0, bar close 11:05-13:30) plus two filters:
atrPct in the top train tercile (>= 0.3055) and Friday; geometry t05s1.
Open history: n_train 967 exp +0.092R / n_valid 895 exp +0.065R, day t 3.08 vs bar 4.57 - FAILS the bar.
Regime up +0.067 / down +0.078, walk-forward 0.88, excess vs same-minute random t 3.80, ex-best-day +0.068.
Caution: a day-of-week filter chosen from 37 filters x 666 pairs is the kind of split most likely to be luck.
Run as type lab, min_adv 125000000, window [1105, 1330]."""
import numpy as np
import pandas as pd


def _g(df, c):
    return np.nan_to_num(df[c].to_numpy(dtype=np.float64))


def _base(df):
    return _g(df, "rsiHeat") + _g(df, "priceActionHeat") - _g(df, "momentumHeat") - _g(df, "vwapHeat")


def _dow(df):
    if "date" in df.columns:
        return pd.to_datetime(df["date"]).dt.dayofweek.to_numpy()
    return np.asarray(df.index.dayofweek)

SIDE = "long"
GEOM = "t05s1"
LAYERS = ["hl_score>=57.5", "gap>0", "atrPct>=0.305473", "Friday", "tod 1105-1330"]
ATR_HI = 0.305473


def mask(df):
    s = _base(df) - 5.0 * np.clip(_g(df, "fromOpen"), -3, 3) - 4.0 * 8.0 / df["atr_d"].to_numpy(dtype=np.float64)
    tod = df["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        return ((s >= 57.5) & (df["gap"].to_numpy(float) > 0) & (df["atrPct"].to_numpy(float) >= ATR_HI)
                & (_dow(df) == 4) & (tod >= 1105) & (tod <= 1330))
