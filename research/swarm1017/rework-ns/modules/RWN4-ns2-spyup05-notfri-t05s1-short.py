"""RWN4-ns2-spyup05-notfri-t05s1-short - swarm1017 rework of NS2 (research/swarm1017/rework-ns, Stage C).
Side short, exit t05s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars. Run with min_adv 95000000 and
window [950, 1130] (bar close ET).
Open 2-year history (locked block excluded), production costs: n 899 (2.11/day), exp +0.115R, day-clustered t
2.29 - BELOW the lineage bar 4.903 (N_lineage 165764); train n 604 +0.101R, valid n 295 +0.144R; up
+0.099 / down +0.428; walk-forward share 1.0; excess over same-minute random +0.082R (t 4.02);
deflated Sharpe 0.0. NOT scored on the locked block. A near-miss for the Testing account at most, not primary.
NS2 only while SPY is > 0.5% above its open, not Fridays; exit t05s1. Needs SPY fromOpen (live code needed).
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "t05s1"
LAYERS = ['close crosses above the 5-min SMA50 on this bar', 'RSI(14) >= 60', 'stock up > 2% from the open', 'SPY > 0.5% above its open (same bar) [live code needed]', 'not Friday', '09:50-11:30 ET']


def _keys(df):
    if "symbol" in df and "date" in df:     # offline frames hold many symbol-days
        return pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    return np.zeros(len(df), dtype=np.int64)  # live: one symbol, today's bars


def _prev(df, k, key):
    x = df[k].to_numpy(dtype=float)
    p = np.r_[np.nan, x[:-1]]
    p[np.r_[True, key[1:] != key[:-1]]] = np.nan
    return p


def _dow(df):
    if "date" in df:
        return pd.to_datetime(df["date"]).dt.dayofweek.to_numpy()
    return pd.DatetimeIndex(df.index).dayofweek.to_numpy()


def _spy_fo(df):
    # SPY % from its open at the same bar. NOT in the live lab frame today (live code needed); without it -> no trades.
    if "spy_fo" not in df:
        return np.full(len(df), np.nan)
    return df["spy_fo"].to_numpy(dtype=float)


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    key = _keys(df)
    rsi, fo, tod = col("rsi"), col("fromOpen"), col("tod")
    sma50, vwap = col("sma50_dist_pct"), col("vwapDistPct")
    p_sma50, p_vwap = _prev(df, "sma50_dist_pct", key), _prev(df, "vwapDistPct", key)
    dow, spy = _dow(df), _spy_fo(df)
    with np.errstate(invalid="ignore"):
        m = (sma50 > 0) & (p_sma50 <= 0) & (rsi >= 60) & (fo > 2) & (spy > 0.5) & (dow != 4) & (tod >= 950) & (tod <= 1130)
    return m
