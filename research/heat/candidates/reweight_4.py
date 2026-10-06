"""Re-weighted MarcoFlow heat score (long-only; best long found - NOT viable on valid, kept for the record). Label: reweight. Educational only - not financial advice.

score = sum_k W[k] * component_k  +  W_BONUS * alignment_bonus  +  W_TOD * hours_since_09:50
Components are MarcoFlow's piecewise heat components (mcf/research/heat.py); alignment_bonus is MarcoFlow's
+/-5 agreement bonus; hours_since_09:50 uses the 5-minute bar close time (tod, HHMM). Fitted on train only.
Long when score >= 10.4536.
"""
import numpy as np

W = {'volumeHeat': -0.25, 'rsiHeat': -0.2785789668560028, 'momentumHeat': 0.0, 'priceActionHeat': 0.0, 'trendHeat': 0.8402960896492004, 'macdHeat': -0.353013813495636, 'vwapHeat': -0.5040194392204285}
W_BONUS = -0.10000000149011612
W_TOD = 0.0
LONG_AT = 10.453629458427427
SHORT_AT = None


def _bonus(df):
    vh, rh = df["volumeHeat"].to_numpy(np.float64), df["rsiHeat"].to_numpy(np.float64)
    mh, ph = df["momentumHeat"].to_numpy(np.float64), df["priceActionHeat"].to_numpy(np.float64)
    return (np.where((vh > 5) & (mh > 5), 5, 0) + np.where((rh > 10) & (ph > 5), 5, 0)
            + np.where((vh < -5) & (mh < -5), -5, 0) + np.where((rh < -10) & (ph < -5), -5, 0)).astype(np.float64)


def score(df):
    s = np.zeros(len(df))
    for k, w in W.items():
        if w:
            s += w * df[k].to_numpy(np.float64)
    if W_BONUS:
        s += W_BONUS * _bonus(df)
    if W_TOD:
        tod = df["tod"].to_numpy(np.int64)
        s += W_TOD * ((tod // 100) * 60 + tod % 100 - 590) / 60.0
    return s
