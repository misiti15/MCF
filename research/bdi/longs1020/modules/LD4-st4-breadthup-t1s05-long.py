"""LD4-st4-breadthup-t1s05-long - BDI longs1020 Part B5 (B5-ST4-BRDUP-t1s05), NEAR-MISS, NOT A CANDIDATE.
"Oversold EMA Cross-Down with Breadth Turning Up".
Live ST4 (EMA9 crosses below EMA21, stock > 3% below its open, RSI(14) > 50, RSI(5) <= 20) taken only when market
breadth (share of the universe above its VWAP) is at least 5 points higher than two bars earlier.
Side long, exit t1s05 (target 1R, stop 0.5R, R = 0.25 x daily ATR, flat 15:55), 5-minute bars, bar close
09:50-11:30, first qualifying bar per symbol-day, min_adv 95000000, context: [breadth].
Open 2-year history (locked block never read), production costs (research/bdi/longs1020/results_B.csv):
train n 5 +0.345R t 1.02 (parent ST4 +0.078R); valid n 16 +0.403R t 2.09 (parent +0.192R); excess over same-
minute random long +0.42 / +0.42R; all n 21 (0.05/day; train 0.02/day, valid 0.08/day), +0.389R t 2.29, without
the best day +0.237R; up +0.66 / flat +0.45 / down -0.18R (n 4). n is tiny (5 train trades).
Fails the pre-declared candidate rule (n_train >= 150) and the multiple-testing bar
(study 3.26, live-long lineage 4.91). NEAR-MISS, observation only, fails the multiple-testing bar; owner 2026-10-20: Testing 2.
Educational only - not financial advice.
Every trade is also an ST4 trade (a filtered copy of the live parent)."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "t1s05"
WINDOW = (950, 1130)
LAYERS = ['EMA9 crosses below EMA21', 'stock > 3% below its open', 'RSI(14) > 50', 'RSI(5) <= 20', 'breadth >= breadth two bars earlier + 0.05 [context: breadth]', '09:50-11:30 ET']


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


def _st4(df, key):
    """Live ST4 (research/bdi/fullday/ST4-emadn-long-am-t1s05-FD.py, = swarm1017 stcore PARENT ST4): EMA9 crosses below
    EMA21 (emaDiff crosses below 0), the stock is > 3% below its open, RSI(14) > 50, RSI(5) <= 20."""
    e = _col(df, "emaDiff")
    return (e < 0) & (_shift(e, key, 1) >= 0) & (_col(df, "fromOpen") < -3.0) & (_col(df, "rsi") > 50) \
        & (_col(df, "rsi5") <= 20)


def mask(df) -> np.ndarray:
    if "breadth" not in df:
        return np.zeros(len(df), dtype=bool)       # fail-safe: no context -> no trades
    key = _keys(df)
    tod = _col(df, "tod")
    with np.errstate(invalid="ignore"):
        brd = _col(df, "breadth")
        filt = brd >= _shift(brd, key, 2) + 0.05
        m = _st4(df, key) & filt
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
