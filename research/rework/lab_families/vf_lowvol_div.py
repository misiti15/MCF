"""vf_lowvol_div -- rule-18 rework of volume_flip_2 (mask shared with volume_flip_1) (lab_families).

Educational only -- not financial advice.
Afternoon bearish RSI divergence on a stretched stock, on a bar with BELOW-average volume (vol_climax < 1).
Side short, exit geometry t1s1 (R = 0.25 x daily ATR, exit by 15:55), entry at the close of the first qualifying bar per symbol-day.
Rework label: add:+climax<1
Train: n=368 days=40 win=0.4158 exp_r=0.251 t_dc=1.92 PF=2.062 halves 0.294/0.2061 ex-best-day 0.1312
Valid: n=51 days=13 win=0.451 exp_r=0.354 t_dc=5.63 PF=3.033 halves 0.2227/0.4257 ex-best-day 0.3104
       window baseline 0.0316, same-time control 0.0936
Plateau (valid, 8 one-step neighbours): mean exp_r 0.2621, 100% positive.
Locked holdouts NOT scored here (lead scores once). Parent lineage already used look 1 on the Sep16-Oct5 test.
"""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
CONDS = [('rsi5', 'rsi5', '>'), ('sma20', 'sma20_dist_pct', '>'), ('bear_div', 'bear_div', '=='), ('tod_lo', 'tod', '>='), ('tod_hi', 'tod', '<='), ('+climax<1', 'vol_climax', '<')]  # (name, column, op); thresholds per variant below
VARIANTS = {
 "base": {
  "rsi5": 90,
  "sma20": 1,
  "bear_div": 1.0,
  "tod_lo": 1300,
  "tod_hi": 1500,
  "+climax<1": 1
 },
 "rsi5=85": {
  "rsi5": 85,
  "sma20": 1,
  "bear_div": 1.0,
  "tod_lo": 1300,
  "tod_hi": 1500,
  "+climax<1": 1
 },
 "rsi5=93": {
  "rsi5": 93,
  "sma20": 1,
  "bear_div": 1.0,
  "tod_lo": 1300,
  "tod_hi": 1500,
  "+climax<1": 1
 },
 "sma20=0.75": {
  "rsi5": 90,
  "sma20": 0.75,
  "bear_div": 1.0,
  "tod_lo": 1300,
  "tod_hi": 1500,
  "+climax<1": 1
 },
 "sma20=1.25": {
  "rsi5": 90,
  "sma20": 1.25,
  "bear_div": 1.0,
  "tod_lo": 1300,
  "tod_hi": 1500,
  "+climax<1": 1
 },
 "tod_lo=1230": {
  "rsi5": 90,
  "sma20": 1,
  "bear_div": 1.0,
  "tod_lo": 1230,
  "tod_hi": 1500,
  "+climax<1": 1
 },
 "tod_lo=1330": {
  "rsi5": 90,
  "sma20": 1,
  "bear_div": 1.0,
  "tod_lo": 1330,
  "tod_hi": 1500,
  "+climax<1": 1
 },
 "+climax<1=0.8": {
  "rsi5": 90,
  "sma20": 1,
  "bear_div": 1.0,
  "tod_lo": 1300,
  "tod_hi": 1500,
  "+climax<1": 0.8
 },
 "+climax<1=1.2": {
  "rsi5": 90,
  "sma20": 1,
  "bear_div": 1.0,
  "tod_lo": 1300,
  "tod_hi": 1500,
  "+climax<1": 1.2
 }
}
NEIGHBORS = {"base": ['rsi5=85', 'rsi5=93', 'sma20=0.75', 'sma20=1.25', 'tod_lo=1230', 'tod_lo=1330', '+climax<1=0.8', '+climax<1=1.2']}


def _col(df, col):
    if col in df:
        return df[col].to_numpy(np.float64)
    raise KeyError(col)


def mask(df, variant: str = "base") -> np.ndarray:
    th = VARIANTS[variant]
    m = np.ones(len(df), bool)
    with np.errstate(invalid="ignore"):
        for name, col, op in CONDS:
            x, v = _col(df, col), th[name]
            if op == "<":
                m &= x < v
            elif op == ">":
                m &= x > v
            elif op == "<=":
                m &= x <= v + 1e-9
            elif op == ">=":
                m &= x >= v - 1e-9
            elif op == "==":
                m &= x == v
    return m
