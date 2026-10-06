"""Re-weighted MarcoFlow heat score (short-only; round-1 search (2-half robust objective), busiest). Label: reweight. Educational only - not financial advice.

score = sum_k W[k] * component_k  +  W_BONUS * alignment_bonus  +  W_TOD * hours_since_09:50
Components are MarcoFlow's piecewise heat components (mcf/research/heat.py); alignment_bonus is MarcoFlow's
+/-5 agreement bonus; hours_since_09:50 uses the 5-minute bar close time (tod, HHMM). Fitted on train only.
Short when score <= -33.6816.
"""
import numpy as np

W = {'volumeHeat': 0.5641447305679321, 'rsiHeat': 1.1421927213668823, 'momentumHeat': 1.3842382431030273, 'priceActionHeat': 0.6644748449325562, 'trendHeat': 0.3988378942012787, 'macdHeat': -0.07370142638683319, 'vwapHeat': 0.0}
W_BONUS = -0.38313931226730347
W_TOD = 2.8691444396972656
LONG_AT = None
SHORT_AT = -33.681649689394035


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
