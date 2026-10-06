"""Shared code for the linear_model heat candidates (educational only - not financial advice).

Each model is a heat-style score: sum_i W_i * (clip(x_i, lo_i, hi_i) - mu_i) / sd_i, where x_i are live
5-minute-bar indicators (MarcoFlow's raw heat inputs, split into positive/negative parts or absolute
values), and W_i are ridge-regression weights fitted on the TRAIN split only (2026-07-08..08-27),
scaled so that 10 points = one standard deviation of the score. Gates (-100) remove bars outside a
time window or where the round-trip cost exceeds a cap (cost in R = 0.08 / prior daily ATR $).
"""
import numpy as np

MODELS = {
 "long_stretch": {
  "features": [
   "vwapDistPct_pos",
   "vwapDistPct_neg",
   "macdPct_pos",
   "macdPct_neg",
   "emaDiff_pos",
   "emaDiff_neg",
   "momentum_pos",
   "momentum_neg",
   "fromOpen_pos",
   "fromOpen_neg"
  ],
  "lo": [
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0
  ],
  "hi": [
   3.324224,
   3.175065,
   1.717331,
   1.812738,
   1.712254,
   1.694731,
   2.825738,
   2.641781,
   8.850332,
   7.961083
  ],
  "mu": [
   0.282467,
   0.286635,
   0.127834,
   0.122929,
   0.119601,
   0.112963,
   0.188843,
   0.182071,
   0.744748,
   0.705487
  ],
  "sd": [
   0.51474,
   0.501882,
   0.248305,
   0.252838,
   0.23996,
   0.234321,
   0.38813,
   0.365165,
   1.347659,
   1.269622
  ],
  "w": [
   0.31450000405311584,
   7.17110013961792,
   -2.96589994430542,
   5.27209997177124,
   1.4056999683380127,
   -0.885699987411499,
   2.8945000171661377,
   -1.132699966430664,
   2.524899959564209,
   -0.14419999718666077
  ]
 },
 "long_stretch_abs": {
  "features": [
   "vwapDistPct_pos",
   "vwapDistPct_neg",
   "macdPct_pos",
   "macdPct_neg",
   "emaDiff_pos",
   "emaDiff_neg",
   "momentum_pos",
   "momentum_neg",
   "fromOpen_pos",
   "fromOpen_neg",
   "abs_vwapDistPct",
   "abs_macdPct",
   "abs_emaDiff",
   "abs_momentum",
   "abs_fromOpen",
   "abs_gap",
   "atrPct",
   "dvolPct",
   "volumeRatio",
   "volumeSurge"
  ],
  "lo": [
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.003186,
   0.001155,
   0.001016,
   0.001618,
   0.006969,
   0.0,
   0.043497,
   0.787695,
   -2.383262,
   -1.786109
  ],
  "hi": [
   3.324224,
   3.175065,
   1.717331,
   1.812738,
   1.712254,
   1.694731,
   2.825738,
   2.641781,
   8.850332,
   7.961083,
   4.007146,
   2.281559,
   2.211568,
   3.63543,
   10.348566,
   12.178112,
   1.90078,
   18.187674,
   1.45266,
   1.483343
  ],
  "mu": [
   0.282467,
   0.286635,
   0.127834,
   0.122929,
   0.119601,
   0.112963,
   0.188843,
   0.182071,
   0.744748,
   0.705487,
   0.574522,
   0.254447,
   0.236193,
   0.377322,
   1.463696,
   1.246802,
   0.338947,
   4.070292,
   -0.347714,
   -0.233091
  ],
  "sd": [
   0.51474,
   0.501882,
   0.248305,
   0.252838,
   0.23996,
   0.234321,
   0.38813,
   0.365165,
   1.347659,
   1.269622,
   0.622484,
   0.327034,
   0.312655,
   0.500495,
   1.608046,
   1.618897,
   0.286378,
   2.602792,
   0.625064,
   0.54845
  ],
  "w": [
   -0.9240999817848206,
   5.1757001876831055,
   -2.387200117111206,
   4.475200176239014,
   0.507099986076355,
   -1.4101999998092651,
   2.7288999557495117,
   -0.9034000039100647,
   2.15120005607605,
   -0.04639999940991402,
   2.130199909210205,
   1.2740999460220337,
   -0.8389999866485596,
   -1.0140000581741333,
   0.26930001378059387,
   -3.330699920654297,
   3.0652999877929688,
   0.33059999346733093,
   0.059300001710653305,
   0.5867999792098999
  ]
 },
 "short_abs": {
  "features": [
   "abs_vwapDistPct",
   "abs_macdPct",
   "abs_emaDiff",
   "abs_momentum",
   "abs_fromOpen",
   "abs_gap",
   "atrPct",
   "dvolPct",
   "volumeRatio",
   "volumeSurge"
  ],
  "lo": [
   0.003186,
   0.001155,
   0.001016,
   0.001618,
   0.006969,
   0.0,
   0.043497,
   0.787695,
   -2.383262,
   -1.786109
  ],
  "hi": [
   4.007146,
   2.281559,
   2.211568,
   3.63543,
   10.348566,
   12.178112,
   1.90078,
   18.187674,
   1.45266,
   1.483343
  ],
  "mu": [
   0.574522,
   0.254447,
   0.236193,
   0.377322,
   1.463696,
   1.246802,
   0.338947,
   4.070292,
   -0.347714,
   -0.233091
  ],
  "sd": [
   0.622484,
   0.327034,
   0.312655,
   0.500495,
   1.608046,
   1.618897,
   0.286378,
   2.602792,
   0.625064,
   0.54845
  ],
  "w": [
   -6.480400085449219,
   -3.9084999561309814,
   1.6902999877929688,
   -0.08940000087022781,
   -1.444700002670288,
   5.389800071716309,
   -4.350900173187256,
   1.34660005569458,
   -0.38600000739097595,
   -0.8737999796867371
  ]
 },
 "short_stretch_abs": {
  "features": [
   "vwapDistPct_pos",
   "vwapDistPct_neg",
   "macdPct_pos",
   "macdPct_neg",
   "emaDiff_pos",
   "emaDiff_neg",
   "momentum_pos",
   "momentum_neg",
   "fromOpen_pos",
   "fromOpen_neg",
   "abs_vwapDistPct",
   "abs_macdPct",
   "abs_emaDiff",
   "abs_momentum",
   "abs_fromOpen",
   "abs_gap",
   "atrPct",
   "dvolPct",
   "volumeRatio",
   "volumeSurge"
  ],
  "lo": [
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.0,
   0.003186,
   0.001155,
   0.001016,
   0.001618,
   0.006969,
   0.0,
   0.043497,
   0.787695,
   -2.383262,
   -1.786109
  ],
  "hi": [
   3.324224,
   3.175065,
   1.717331,
   1.812738,
   1.712254,
   1.694731,
   2.825738,
   2.641781,
   8.850332,
   7.961083,
   4.007146,
   2.281559,
   2.211568,
   3.63543,
   10.348566,
   12.178112,
   1.90078,
   18.187674,
   1.45266,
   1.483343
  ],
  "mu": [
   0.282467,
   0.286635,
   0.127834,
   0.122929,
   0.119601,
   0.112963,
   0.188843,
   0.182071,
   0.744748,
   0.705487,
   0.574522,
   0.254447,
   0.236193,
   0.377322,
   1.463696,
   1.246802,
   0.338947,
   4.070292,
   -0.347714,
   -0.233091
  ],
  "sd": [
   0.51474,
   0.501882,
   0.248305,
   0.252838,
   0.23996,
   0.234321,
   0.38813,
   0.365165,
   1.347659,
   1.269622,
   0.622484,
   0.327034,
   0.312655,
   0.500495,
   1.608046,
   1.618897,
   0.286378,
   2.602792,
   0.625064,
   0.54845
  ],
  "w": [
   1.1448999643325806,
   -5.537399768829346,
   2.6972999572753906,
   -4.810699939727783,
   -0.4864000082015991,
   1.656999945640564,
   -2.8431999683380127,
   1.104599952697754,
   -2.108299970626831,
   0.5410000085830688,
   -2.6180999279022217,
   -1.625599980354309,
   0.7448999881744385,
   0.9125000238418579,
   -0.3709999918937683,
   3.4932000637054443,
   -3.0334999561309814,
   1.4672000408172607,
   -0.21040000021457672,
   -0.5558000206947327
  ]
 }
}


def _x(df, name):
    if name in ("costR",):
        return 0.08 / df["atr_d"].to_numpy(np.float64)
    if name == "dvolPct":
        return df["atr_d"].to_numpy(np.float64) / df["close"].to_numpy(np.float64) * 100
    if name.startswith("abs_"):
        return np.abs(np.nan_to_num(df[name[4:]].to_numpy(np.float64)))
    if name.endswith("_pos"):
        return np.maximum(np.nan_to_num(df[name[:-4]].to_numpy(np.float64)), 0)
    if name.endswith("_neg"):
        return np.maximum(-np.nan_to_num(df[name[:-4]].to_numpy(np.float64)), 0)
    v = df[name].to_numpy(np.float64)
    if name in ("volumeRatio", "volumeSurge"):
        return np.log(np.clip(np.nan_to_num(v, nan=1.0), 0.05, 20))
    return np.nan_to_num(v)


def raw_score(df, model):
    m = MODELS[model]
    s = np.zeros(len(df))
    for f, lo, hi, mu, sd, w in zip(m["features"], m["lo"], m["hi"], m["mu"], m["sd"], m["w"]):
        s += w * (np.clip(_x(df, f), lo, hi) - mu) / sd
    return s


def gates(df, t0=None, t1=None, cost_cap=None):
    g = np.zeros(len(df))
    tod = df["tod"].to_numpy()
    if t0 is not None:
        g[(tod < t0) | (tod > t1)] = -100.0
    if cost_cap is not None:
        g[~(0.08 / df["atr_d"].to_numpy(np.float64) <= cost_cap)] = -100.0
    return g
