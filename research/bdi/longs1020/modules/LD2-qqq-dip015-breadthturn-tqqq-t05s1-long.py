"""LD2-qqq-dip015-breadthturn-tqqq-t05s1-long - BDI longs1020 Part A, NEAR-MISS, NOT A CANDIDATE.
Shallow Nasdaq dip, then breadth turns: QQQ's running low of 5-minute closes is >= 0.15% below its 09:30 open, then
on a bar closing 09:50-10:30 market breadth (share above VWAP) is >= 10 points above its low since 09:50 and QQQ
closes higher than the bar before; buy TQQQ, first such bar of the day only. Exit t05s1 (R = 0.25 x TQQQ daily ATR).
Use with symbols: [TQQQ], context: [qqq_fo, breadth], window [950, 1030].
Open history, production costs, 1-minute simulator (next-minute entry): train n 92 +0.030R t 0.42 (random 09:50-10:30
TQQQ long -0.100R; same dip days random bar +0.020R); valid n 67 +0.079R t 0.96 (random -0.058R; same days +0.064R);
down sessions -0.06R. Fails valid t >= 1.5 and the multiple-testing bar (study 3.26, index-dip lineage 5.00).
Offline frames start at 09:50, so QQQ's 09:35-09:45 closes are missing offline; live frames include them.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "t05s1"
WINDOW = (950, 1030)
SYMBOLS = ["TQQQ"]
LAYERS = ["QQQ running low of 5-min closes <= -0.15% from the open [context: qqq_fo]",
          "breadth >= its 09:50+ low + 0.10 [context: breadth]", "QQQ close above the prior bar's close",
          "first qualifying bar of the day", "09:50-10:30 ET"]


def _day(df):
    if "symbol" in df and "date" in df:
        return pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    if "date" in df:
        return pd.factorize(df["date"].astype(str))[0]
    return np.zeros(len(df), dtype=np.int64)


def mask(df) -> np.ndarray:
    if "qqq_fo" not in df or "breadth" not in df:
        return np.zeros(len(df), dtype=bool)
    key = _day(df)
    tod = df["tod"].to_numpy(dtype=float)
    q = pd.Series(df["qqq_fo"].to_numpy(dtype=float))
    b = pd.Series(np.where(tod >= 950, df["breadth"].to_numpy(dtype=float), np.nan))
    k = pd.Series(key)
    qmin = q.groupby(k).cummin().to_numpy()
    bmin = b.groupby(k).cummin().to_numpy()
    qprev = q.groupby(k).shift(1).to_numpy()
    with np.errstate(invalid="ignore"):
        m = (qmin <= -0.15) & (b.to_numpy() >= bmin + 0.10) & (q.to_numpy() > qprev)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    first = pd.Series(m).groupby(k).cumsum().to_numpy() == 1
    return np.asarray(m & first, dtype=bool)
