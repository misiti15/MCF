"""MFR1-h40-flowsell-fri-sma50dn-long - rework of MF4-h40-open-flowsell (swarm1017/rework-mf, 2026-10-17).
Opposite side of MF4 (LONG the MarcoFlow flow-sell signal), Fridays only, price below its 5-min SMA50, 09:50-11:00.
Open history, production cost (prod_r, tod entry costs), first signal per symbol-day, min_adv 95M:
  train 2024-10..2025-12 (locked 2024-11..2025-02 excluded): n 151, exp +0.076R, day-t 0.86
  valid 2026-01..2026-10-07: n 171, exp +0.203R, day-t 2.11; all n 322 (68 sessions), exp +0.144R, day-t 2.16
  regime up/flat/down +0.215/+0.094/+0.076R (pass), walk-forward share 0.70, ex-best-day +0.102R,
  excess vs same-minute random +0.156R (t 2.59).
STATUS: FAILS the try-count bar (t 2.16 < 4.86, lineage N ~133,904) - a day-of-week x filter pair chosen out of
47,820 configurations; likely noise. Not for live funds. Research record only.
Live note: needs the bar timestamps (DatetimeIndex) or a `date` column for the day-of-week layer.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "t1s1"
LAYERS = [
    "heat <= -40 (MarcoFlow bearish heat 40)",
    "buyPressure < -0.25 (flow-sell)",
    "Friday session",
    "sma50_dist_pct < 0 (close below 5-min SMA50)",
    "window: bar close 09:50-11:00 ET (YAML window [950, 1100])",
]


def _dow(df) -> np.ndarray:
    if "date" in df.columns:
        return pd.to_datetime(df["date"]).dt.dayofweek.to_numpy()
    return pd.DatetimeIndex(df.index).dayofweek.to_numpy()


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    bp = df["buyPressure"].to_numpy(dtype=float)
    s50 = df["sma50_dist_pct"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -40) & (bp < -0.25) & (_dow(df) == 4) & (s50 < 0) & (tod >= 950) & (tod <= 1100)
