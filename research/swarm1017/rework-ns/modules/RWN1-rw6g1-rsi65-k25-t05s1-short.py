"""RWN1-rw6g1-rsi65-k25-t05s1-short - swarm1017 rework of RW6G1 (research/swarm1017/rework-ns, Stage A).
Side short, exit t05s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars. Run with min_adv 95000000 and
window [950, 1130] (bar close ET).
Open 2-year history (locked block excluded), production costs: n 372 (0.87/day), exp +0.221R, day-clustered t
2.93 - BELOW the lineage bar 4.903 (N_lineage 165764); train n 246 +0.239R, valid n 126 +0.184R; up
+0.285 / down +0.120; walk-forward share 0.778; excess over same-minute random +0.124R (t 3.83);
deflated Sharpe 0.0. NOT scored on the locked block. A near-miss for the Testing account at most, not primary.
RW6G1 thresholds RSI14 >= 65 (was 60), band guard k 2.5 (was 2), exit t05s1 (was t1s1).
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "t05s1"
LAYERS = ['close crosses above the 5-min SMA50 on this bar', 'stock up > 3% from the open', 'RSI(14) >= 65', 'no unresolved close above VWAP + 2.5 SD', '09:50-11:30 ET (bar close)']


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


def vwap_band_block(df, k: float) -> np.ndarray:
    """As research/bdi/live1009/RW6G1-ns2-up3-vwap2sd-short.py with band width k: True where a short is blocked
    (close above VWAP and a close above VWAP + k SD since the last close at or below VWAP, same day)."""
    if "volume" not in df:
        return np.ones(len(df), dtype=bool)  # fail safe
    key = _keys(df)
    h, l, c, v = (df[x].to_numpy(dtype=float) for x in ("high", "low", "close", "volume"))
    tp = (h + l + c) / 3
    g = pd.Series(key)
    cv = pd.Series(v).groupby(g).cumsum().to_numpy().copy()
    cv[cv == 0] = np.nan
    vw = pd.Series(tp * v).groupby(g).cumsum().to_numpy() / cv
    var = pd.Series(tp * tp * v).groupby(g).cumsum().to_numpy() / cv - vw * vw
    sd = np.sqrt(np.clip(var, 0, None))
    with np.errstate(invalid="ignore"):
        beyond = c - vw > 0
        seg = pd.Series((~beyond).astype(np.int64)).groupby(g).cumsum().to_numpy()
        band = c - (vw + k * sd) > 0
        flag = pd.Series(band).groupby(key.astype(np.int64) * 100_000 + seg).cummax().to_numpy()
    return beyond & flag


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    key = _keys(df)
    rsi, fo, tod = col("rsi"), col("fromOpen"), col("tod")
    sma50, vwap = col("sma50_dist_pct"), col("vwapDistPct")
    p_sma50, p_vwap = _prev(df, "sma50_dist_pct", key), _prev(df, "vwapDistPct", key)
    dow, spy = _dow(df), _spy_fo(df)
    with np.errstate(invalid="ignore"):
        m = (sma50 > 0) & (p_sma50 <= 0) & (fo > 3) & (rsi >= 65) & (tod >= 950) & (tod <= 1130)
    return m & ~vwap_band_block(df, 2.5)
