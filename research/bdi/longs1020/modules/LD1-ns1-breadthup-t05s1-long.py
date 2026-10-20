"""LD1-ns1-breadthup-t05s1-long - BDI longs1020 (research/bdi/longs1020), NEAR-MISS, NOT A CANDIDATE.
Live NS1 (RSI(14) crosses down through 40 while RSI(5) >= 80 and the stock is > 2% above its open) taken only
when market breadth (share of the universe above its VWAP) is at least 5 points higher than two bars earlier.
Side long, exit t05s1 (target 0.5R, stop 1R, R = 0.25 x daily ATR, flat 15:55), 5-minute bars, bar close
09:50-11:30, min_adv 95000000, context: [breadth].
Open 2-year history (locked block never read), production costs: n 134 (0.32/day), +0.095R, day t 1.50;
train n 61 +0.081R (parent NS1 -0.008R), valid n 73 +0.108R t 1.52 (parent +0.054R); excess over same-minute
random long +0.06 / +0.17R; up +0.15 / down +0.02R. Fails the pre-declared n_train >= 150 and the multiple-
testing bar (study 3.26, lineage 4.91). Every trade is also an NS1 trade (a filtered copy).
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "t05s1"
WINDOW = (950, 1130)
LAYERS = ["rsi crosses below 40 on this bar", "rsi5 >= 80", "stock > 2% above its open",
          "breadth >= breadth two bars earlier + 0.05 [context: breadth]", "09:50-11:30 ET"]


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


def mask(df) -> np.ndarray:
    if "breadth" not in df:
        return np.zeros(len(df), dtype=bool)       # fail-safe: no context -> no trades
    key = _keys(df)
    rsi = df["rsi"].to_numpy(dtype=float)
    rsi5 = df["rsi5"].to_numpy(dtype=float)
    fo = df["fromOpen"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    brd = df["breadth"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        m = (rsi <= 40) & (_shift(rsi, key, 1) > 40) & (rsi5 >= 80) & (fo > 2)
        m &= brd >= _shift(brd, key, 2) + 0.05
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
