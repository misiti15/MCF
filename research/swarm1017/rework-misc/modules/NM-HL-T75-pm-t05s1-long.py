"""NEAR-MISS (swarm1017 rework-misc, 2026-10-17) - does NOT pass the research bar; Testing-account forward test only.
Educational only - not financial advice.
Rework of heat_fade_long: the same long heat score (rsiHeat + priceActionHeat - momentumHeat - vwapHeat
- 5 x clip(fromOpen, -3, 3) - 4 x 8 / atr_d) at a STRICTER threshold (>= 75 instead of 57.5), stock below its open,
afternoon only (bar close 13:00-15:00), high win-rate geometry t05s1 (target +0.5R, stop -1R).
Open history (train 2024-10 + 2025-03..12 / valid 2026-01..10-07, production costs): n 893 / 967, exp +0.052 / +0.038R,
day-clustered t 1.93 vs bar 4.57 (heat lineage ~34k configs) - FAILS the bar. Regime up +0.042 / down +0.039, walk-forward
0.75, beats same-minute random (excess t 4.39). Threshold neighbour T65 also positive in both halves (plateau).
Run as type lab, min_adv 125000000, window [1300, 1500]. Live frame features only (heat components, fromOpen, atr_d)."""
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
LAYERS = ["hl_score>=75", "fromOpen<0", "tod 1300-1500"]


def mask(df):
    s = _base(df) - 5.0 * np.clip(_g(df, "fromOpen"), -3, 3) - 4.0 * 8.0 / df["atr_d"].to_numpy(dtype=np.float64)
    tod = df["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        return (s >= 75) & (df["fromOpen"].to_numpy(float) < 0) & (tod >= 1300) & (tod <= 1500)
