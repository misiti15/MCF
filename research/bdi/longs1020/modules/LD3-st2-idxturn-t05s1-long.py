"""LD3-st2-idxturn-t05s1-long - BDI longs1020 Part B5 (B5-ST2-IDXTURN-t05s1), NEAR-MISS, NOT A CANDIDATE.
"Oversold Slope Turn after an SPY Dip-Turn".
Live ST2 (5-min SMA20 slope turns up, stock > 3% below its open, buy pressure > 0, close within 0.5 daily ATR of
VWAP) taken only after SPY has dipped and turned: SPY's running low of 5-minute closes since 09:35 is <= -0.15% from
its open and SPY's current bar close is >= that low + 0.10 points.
Side long, exit t05s1 (target 0.5R, stop 1R, R = 0.25 x daily ATR, flat 15:55), 5-minute bars, bar close
09:50-11:30, first qualifying bar per symbol-day, min_adv 95000000, context: [spy_fo].
Open 2-year history (locked block never read), production costs (research/bdi/longs1020/results_B.csv):
train n 23 +0.035R t 0.27 (parent ST2 +0.035R: on train it equals the parent); valid n 50 +0.268R t 3.44 (parent
+0.168R); excess over same-minute random long +0.07 / +0.44R; all n 73 (0.18/day; train 0.10/day, valid 0.26/day),
+0.194R t 2.68, without the best day +0.162R; up +0.21 / flat +0.35 / down -0.04R. Valid concentrated in 2026Q2
(30 of 50 valid trades in 2026-05/06).
Fails the pre-declared candidate rule (n_train >= 150) and the multiple-testing bar
(study 3.26, live-long lineage 4.91). NEAR-MISS, observation only, fails the multiple-testing bar; owner 2026-10-20: Testing 2.
Educational only - not financial advice.
Every trade is also an ST2 trade (a filtered copy of the live parent)."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "t05s1"
WINDOW = (950, 1130)
LAYERS = ['5-min SMA20 slope crosses above 0', 'stock > 3% below its open', '19-bar buy pressure > 0', 'close within 0.5 daily ATR of VWAP', 'SPY running low since 09:35 <= -0.15% [context: spy_fo]', 'SPY close >= that low + 0.10 [context: spy_fo]', '09:50-11:30 ET']


def _keys(df):
    if "symbol" in df and "date" in df:
        return pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    if "date" in df:
        return pd.factorize(df["date"].astype(str))[0]
    return np.zeros(len(df), dtype=np.int64)


def _shift(x, key, k):
    p = np.r_[np.full(k, np.nan), x[:-k]]
    same = np.r_[np.zeros(k, bool), key[k:] == key[:-k]]
    return np.where(same, p, np.nan)


def _col(df, k):
    return df[k].to_numpy(dtype=float)


def _st2(df, key):
    """Live ST2 (research/bdi/fullday/ST2-slope20up-long-am-t05s1-FD.py, = swarm1017 stcore PARENT ST2): the 5-min
    SMA20 slope crosses above 0, the stock is > 3% below its open, 19-bar buy pressure > 0, close within 0.5 daily ATR
    of VWAP."""
    c, atr = _col(df, "close"), _col(df, "atr_d")
    vw = c / (1 + _col(df, "vwapDistPct") / 100)
    z = (c - vw) / atr
    sl = _col(df, "sma20_slope_pct")
    return (sl > 0) & (_shift(sl, key, 1) <= 0) & (_col(df, "fromOpen") < -3.0) & (_col(df, "buyPressure") > 0) \
        & (np.abs(z) < 0.5)


def mask(df) -> np.ndarray:
    if "spy_fo" not in df:
        return np.zeros(len(df), dtype=bool)       # fail-safe: no context -> no trades
    key = _keys(df)
    tod = _col(df, "tod")
    with np.errstate(invalid="ignore"):
        spy = _col(df, "spy_fo")
        spymin = pd.Series(spy).groupby(key).cummin().to_numpy()     # running low of SPY 5-min closes since 09:35
        filt = (spymin <= -0.15) & (spy >= spymin + 0.10)
        m = _st2(df, key) & filt
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
