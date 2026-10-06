"""Re-weighted MarcoFlow heat score (short-only; round-2 search (4-block robust objective)). Label: reweight. Educational only - not financial advice.

score = sum_k W[k] * component_k  +  W_BONUS * alignment_bonus  +  W_TOD * hours_since_09:50
Components are MarcoFlow's piecewise heat components (mcf/research/heat.py); alignment_bonus is MarcoFlow's
+/-5 agreement bonus; hours_since_09:50 uses the 5-minute bar close time (tod, HHMM). Fitted on train only.
Short when score <= -11.2745.
"""
import numpy as np

W = {'volumeHeat': 0.4850851595401764, 'rsiHeat': 0.5706528425216675, 'momentumHeat': 0.25, 'priceActionHeat': -0.25, 'trendHeat': 0.3499999940395355, 'macdHeat': 0.0, 'vwapHeat': 0.0}
W_BONUS = 0.10000000149011612
W_TOD = 5.301723480224609
LONG_AT = None
SHORT_AT = -11.274544553756767


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
