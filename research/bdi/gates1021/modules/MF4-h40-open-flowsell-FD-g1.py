"""MF4-h40-open-flowsell-FD-g1 - research/bdi/gates1021 check-gate variant of MF4-h40-open-flowsell-FD (parent module research/bdi/fullday/MF4-h40-open-flowsell-FD.py,
copied below with its logic unchanged) plus ONE layer: skip while SPY's prior session closed >= +0.5% above the session before AND SPY is >= +0.25% from today's open [context: spy_fo + spy_prev - spy_prev is NOT a LabStrategy context column yet: live code needed].
Status: FINALIST (gates1021, N 718, bar 3.63). Open 2-year history, production costs: train parent -0.1192R -> gated -0.1081R, valid parent -0.0506R -> gated -0.0385R; blocked 12.7% / 13.5% of trades (train/valid); pooled gate-delta day-clustered t 4.80. The gated setup is still NEGATIVE after costs; the gate only removes its worst market state. Run with the parent's YAML block (window, min_adv, refire) plus context: [spy_fo].
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "|heat| >= 40 (MarcoFlow heat-40)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (np.abs(heat) >= 40) & (buyPressure < -0.25)


# ---------------------------------------------------------------- gates1021 check-gate (one layer)
_parent_mask = mask
LAYERS = list(LAYERS) + ["skip while SPY's prior session closed >= +0.5% above the session before AND SPY is >= +0.25% from today's open [context: spy_fo + spy_prev - spy_prev is NOT a LabStrategy context column yet: live code needed]"]
CONTEXT = ['spy_fo', 'spy_prev']


def _g21_keys(df):
    import pandas as _pd
    if "symbol" in df and "date" in df:
        return _pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    if "date" in df:
        return _pd.factorize(df["date"].astype(str))[0]
    return np.zeros(len(df), dtype=np.int64)


def _g21_block(df):
    n = len(df)
    nan = np.full(n, np.nan)
    spy = df["spy_fo"].to_numpy(dtype=float) if "spy_fo" in df else nan
    qqq = df["qqq_fo"].to_numpy(dtype=float) if "qqq_fo" in df else nan
    brd = df["breadth"].to_numpy(dtype=float) if "breadth" in df else nan
    pv = df["spy_prev"].to_numpy(dtype=float) if "spy_prev" in df else nan   # prior-session SPY close-to-close %
    tod = df["tod"].to_numpy(dtype=float)
    key = _g21_keys(df)
    p2 = np.r_[np.full(2, np.nan), brd[:-2]] if n > 2 else np.full(n, np.nan)
    same = np.r_[np.zeros(min(2, n), bool), key[2:] == key[:-2]] if n > 2 else np.zeros(n, bool)
    d2 = np.where(same & (tod >= 1000), brd - p2, np.nan)   # breadth slope from the 10:00 bar (as scored)
    with np.errstate(invalid="ignore"):
        return np.asarray((pv >= 0.5) & (spy >= 0.25), dtype=bool)


def mask(df) -> np.ndarray:
    """Parent mask AND NOT the gate state. Missing context -> the gate never blocks (NaN compares False)."""
    return np.asarray(_parent_mask(df), dtype=bool) & ~_g21_block(df)
