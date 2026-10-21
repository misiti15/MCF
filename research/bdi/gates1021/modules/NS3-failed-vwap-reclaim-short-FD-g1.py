"""NS3-failed-vwap-reclaim-short-FD-g1 - research/bdi/gates1021 check-gate variant of NS3-failed-vwap-reclaim-short-FD (parent module research/bdi/fullday/NS3-failed-vwap-reclaim-short-FD.py,
copied below with its logic unchanged) plus ONE layer: skip while SPY's prior session closed >= +0.5% above the session before AND SPY is >= +0.25% from today's open [context: spy_fo + spy_prev - spy_prev is NOT a LabStrategy context column yet: live code needed].
Status: NEAR-MISS (not a candidate; pooled t below the bar 3.63) (gates1021, N 718, bar 3.63). Open 2-year history, production costs: train parent -0.0044R -> gated +0.0244R, valid parent -0.0157R -> gated -0.0061R; blocked 13.7% / 16.2% of trades (train/valid); pooled gate-delta day-clustered t 2.98. The gated setup is still NEGATIVE after costs; the gate only removes its worst market state. Run with the parent's YAML block (window, min_adv, refire) plus context: [spy_fo].
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "price reclaims VWAP on this bar",
    "price above the 5-min 50-bar average",
    "stock down > 2% from the open",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    def prev(k):
        x = col(k)
        p = np.r_[np.nan, x[:-1]]
        if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
            key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
            p[np.r_[True, key[1:] != key[:-1]]] = np.nan
        return p

    rsi, rsi5, fromOpen = col("rsi"), col("rsi5"), col("fromOpen")
    sma50, vwap, tod = col("sma50_dist_pct"), col("vwapDistPct"), col("tod")
    with np.errstate(invalid="ignore"):
        return (vwap > 0) & (prev('vwapDistPct') <= 0) & (sma50 > 0) & (fromOpen < -2)


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
