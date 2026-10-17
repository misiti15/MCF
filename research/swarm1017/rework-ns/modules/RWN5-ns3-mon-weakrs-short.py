"""RWN5-ns3-mon-weakrs-short - swarm1017 rework of NS3 (research/swarm1017/rework-ns, Stage C).
Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars. Run with min_adv 95000000 and
window [950, 1130] (bar close ET).
Open 2-year history (locked block excluded), production costs: n 295 (0.69/day), exp +0.202R, day-clustered t
2.17 - BELOW the lineage bar 4.903 (N_lineage 165764); train n 173 +0.164R, valid n 122 +0.257R; up
+0.148 / down +0.407; walk-forward share 0.625; excess over same-minute random +0.247R (t 3.00);
deflated Sharpe 0.0. NOT scored on the locked block. A near-miss for the Testing account at most, not primary.
NS3 on Mondays when the stock is weaker than SPY from the open. Day-of-week filter: no known mechanism - likely selection noise. Needs SPY fromOpen (live code needed).
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "t1s1"
LAYERS = ['close crosses above VWAP on this bar', 'close above the 5-min SMA50', 'stock down > 2% from the open', 'Monday', 'stock fromOpen below SPY fromOpen [live code needed]', '09:50-11:30 ET']


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
        m = (vwap > 0) & (p_vwap <= 0) & (sma50 > 0) & (fo < -2) & (dow == 0) & (fo - spy < 0) & (tod >= 950) & (tod <= 1130)
    return m
