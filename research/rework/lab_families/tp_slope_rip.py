"""tp_slope_rip -- rule-18 rework of trend_pullback_1/2/3 (lab_families).

Educational only -- not financial advice.
Sell the rip in a stock down from the open, only when the 5-min SMA20 is still falling (sma20_slope_pct < 0).
Side short, exit geometry t05s1 (R = 0.25 x daily ATR, exit by 15:55), entry at the close of the first qualifying bar per symbol-day.
Rework label: add:+slope20<0
Train: n=268 days=39 win=0.7388 exp_r=0.0867 t_dc=1.54 PF=1.333 halves 0.023/0.1584 ex-best-day 0.0638
Valid: n=89 days=12 win=0.8764 exp_r=0.2993 t_dc=5.56 PF=3.91 halves 0.1475/0.362 ex-best-day 0.2555
       window baseline -0.0023, same-time control 0.0133
Plateau (valid, 12 one-step neighbours): mean exp_r 0.2386, 100% positive.
Locked holdouts NOT scored here (lead scores once). Parent lineage already used look 1 on the Sep16-Oct5 test.
"""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
CONDS = [('fromOpen', 'fromOpen', '<'), ('vwap', 'vwapDistPct', '<'), ('sma50', 'sma50_dist_pct', '<'), ('sma20', 'sma20_dist_pct', '>'), ('tod_hi', 'tod', '<='), ('+slope20<0', 'sma20_slope_pct', '<')]  # (name, column, op); thresholds per variant below
VARIANTS = {
 "base": {
  "fromOpen": -0.5,
  "vwap": 0,
  "sma50": 0,
  "sma20": 0,
  "tod_hi": 1030,
  "+slope20<0": 0
 },
 "fromOpen=-0.75": {
  "fromOpen": -0.75,
  "vwap": 0,
  "sma50": 0,
  "sma20": 0,
  "tod_hi": 1030,
  "+slope20<0": 0
 },
 "fromOpen=-0.25": {
  "fromOpen": -0.25,
  "vwap": 0,
  "sma50": 0,
  "sma20": 0,
  "tod_hi": 1030,
  "+slope20<0": 0
 },
 "vwap=-0.2": {
  "fromOpen": -0.5,
  "vwap": -0.2,
  "sma50": 0,
  "sma20": 0,
  "tod_hi": 1030,
  "+slope20<0": 0
 },
 "vwap=0.2": {
  "fromOpen": -0.5,
  "vwap": 0.2,
  "sma50": 0,
  "sma20": 0,
  "tod_hi": 1030,
  "+slope20<0": 0
 },
 "sma50=-0.2": {
  "fromOpen": -0.5,
  "vwap": 0,
  "sma50": -0.2,
  "sma20": 0,
  "tod_hi": 1030,
  "+slope20<0": 0
 },
 "sma50=0.2": {
  "fromOpen": -0.5,
  "vwap": 0,
  "sma50": 0.2,
  "sma20": 0,
  "tod_hi": 1030,
  "+slope20<0": 0
 },
 "sma20=-0.1": {
  "fromOpen": -0.5,
  "vwap": 0,
  "sma50": 0,
  "sma20": -0.1,
  "tod_hi": 1030,
  "+slope20<0": 0
 },
 "sma20=0.1": {
  "fromOpen": -0.5,
  "vwap": 0,
  "sma50": 0,
  "sma20": 0.1,
  "tod_hi": 1030,
  "+slope20<0": 0
 },
 "tod_hi=1015": {
  "fromOpen": -0.5,
  "vwap": 0,
  "sma50": 0,
  "sma20": 0,
  "tod_hi": 1015,
  "+slope20<0": 0
 },
 "tod_hi=1100": {
  "fromOpen": -0.5,
  "vwap": 0,
  "sma50": 0,
  "sma20": 0,
  "tod_hi": 1100,
  "+slope20<0": 0
 },
 "+slope20<0=-0.1": {
  "fromOpen": -0.5,
  "vwap": 0,
  "sma50": 0,
  "sma20": 0,
  "tod_hi": 1030,
  "+slope20<0": -0.1
 },
 "+slope20<0=0.1": {
  "fromOpen": -0.5,
  "vwap": 0,
  "sma50": 0,
  "sma20": 0,
  "tod_hi": 1030,
  "+slope20<0": 0.1
 }
}
NEIGHBORS = {"base": ['fromOpen=-0.75', 'fromOpen=-0.25', 'vwap=-0.2', 'vwap=0.2', 'sma50=-0.2', 'sma50=0.2', 'sma20=-0.1', 'sma20=0.1', 'tod_hi=1015', 'tod_hi=1100', '+slope20<0=-0.1', '+slope20<0=0.1']}


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
