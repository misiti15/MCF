"""NEAR-MISS (swarm1017 rework-misc, 2026-10-17) - does NOT pass the research bar; Testing-account forward test only.
Educational only - not financial advice.
Rework of heat_fade_short: parent core (short heat score -(rsiHeat + priceActionHeat - momentumHeat - vwapHeat)
- 8 x 8 / atr_d >= 11.3, fromOpen < 0, bar close 09:50-10:30) plus fromOpen < -1 and Monday; geometry t05s1.
Open history: n_train 277 exp +0.197R / n_valid 308 exp +0.079R, day t 2.83 vs bar 4.57 - FAILS the bar.
Regime up +0.055 / down +0.225 (still short-leaning), walk-forward 0.92, excess vs random t 4.58, ex-best-day +0.103.
Caution: Monday filter = likely luck among 666 pairs. Run as type lab, min_adv 125000000, window [950, 1030]."""
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

SIDE = "short"
GEOM = "t05s1"
LAYERS = ["hs_score>=11.3", "fromOpen<-1", "Monday", "tod 0950-1030"]


def mask(df):
    s = -_base(df) - 8.0 * 8.0 / df["atr_d"].to_numpy(dtype=np.float64)
    tod = df["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        return (s >= 11.3) & (df["fromOpen"].to_numpy(float) < -1) & (_dow(df) == 0) & (tod >= 950) & (tod <= 1030)
