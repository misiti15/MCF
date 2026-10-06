"""wg1_pdl_fade -- rule-18 rework of win_geometry_1 (lab_families).

Educational only -- not financial advice.
Afternoon fade of a gap-down stock stretched above its 5-min SMA50 while still at/below ~0.25 ATR above the prior-day low.
Side short, exit geometry t1s05 (R = 0.25 x daily ATR, exit by 15:55), entry at the close of the first qualifying bar per symbol-day.
Rework label: add:+pdl<.25
Train: n=328 days=33 win=0.3079 exp_r=0.1554 t_dc=1.83 PF=1.712 halves 0.2028/-0.0128 ex-best-day 0.0939
Valid: n=33 days=11 win=0.4242 exp_r=0.3561 t_dc=4.62 PF=3.279 halves 0.2189/0.4075 ex-best-day 0.2875
       window baseline 0.0025, same-time control 0.0002
Plateau (valid, 8 one-step neighbours): mean exp_r 0.3613, 100% positive.
Locked holdouts NOT scored here (lead scores once). Parent lineage already used look 1 on the Sep16-Oct5 test.
"""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
CONDS = [('gap', 'gap', '<'), ('sma50', 'sma50_dist_pct', '>'), ('tod_lo', 'tod', '>='), ('+pdl<.25', 'dist_pdl_atr', '<')]  # (name, column, op); thresholds per variant below
VARIANTS = {
 "base": {
  "gap": -0.445,
  "sma50": 2.19,
  "tod_lo": 1300,
  "+pdl<.25": 0.25
 },
 "gap=-0.7": {
  "gap": -0.7,
  "sma50": 2.19,
  "tod_lo": 1300,
  "+pdl<.25": 0.25
 },
 "gap=-0.2": {
  "gap": -0.2,
  "sma50": 2.19,
  "tod_lo": 1300,
  "+pdl<.25": 0.25
 },
 "sma50=1.85": {
  "gap": -0.445,
  "sma50": 1.85,
  "tod_lo": 1300,
  "+pdl<.25": 0.25
 },
 "sma50=2.5": {
  "gap": -0.445,
  "sma50": 2.5,
  "tod_lo": 1300,
  "+pdl<.25": 0.25
 },
 "tod_lo=1230": {
  "gap": -0.445,
  "sma50": 2.19,
  "tod_lo": 1230,
  "+pdl<.25": 0.25
 },
 "tod_lo=1330": {
  "gap": -0.445,
  "sma50": 2.19,
  "tod_lo": 1330,
  "+pdl<.25": 0.25
 },
 "+pdl<.25=0.175": {
  "gap": -0.445,
  "sma50": 2.19,
  "tod_lo": 1300,
  "+pdl<.25": 0.175
 },
 "+pdl<.25=0.375": {
  "gap": -0.445,
  "sma50": 2.19,
  "tod_lo": 1300,
  "+pdl<.25": 0.375
 }
}
NEIGHBORS = {"base": ['gap=-0.7', 'gap=-0.2', 'sma50=1.85', 'sma50=2.5', 'tod_lo=1230', 'tod_lo=1330', '+pdl<.25=0.175', '+pdl<.25=0.375']}


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
