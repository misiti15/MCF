"""LD7-ns1-idxturn-holdtr-long - BDI longs1020 Part B5 (B5-NS1-IDXTURN-holdtr), NEAR-MISS, NOT A CANDIDATE.
"Oversold Pop after an SPY Dip-Turn (trailing)".
Live NS1 (RSI(14) crosses down through 40 while RSI(5) >= 80 and the stock is > 2% above its open) taken only after
SPY has dipped and turned: SPY's running low of 5-minute closes since 09:35 is <= -0.15% from its open and SPY's
current bar close is >= that low + 0.10 points.
Side long, exit holdtr (stop 1R, no target; once +1R the stop trails 1R behind the best price, R = 0.25 x daily ATR, flat 15:55), 5-minute bars, bar close
09:50-11:30, first qualifying bar per symbol-day, min_adv 95000000, context: [spy_fo].
Open 2-year history (locked block never read), production costs (research/bdi/longs1020/results_B.csv):
train n 78 +0.578R t 0.89 (parent NS1 holdtr +0.237R); valid n 99 +0.010R t 0.06 (parent -0.029R); excess over
same-minute random long +0.03 / +0.05R; all n 177 (0.42/day; train 0.33/day, valid 0.52/day), +0.260R t 0.80,
without the best day -0.073R (train carried by a few days); up +0.90 / flat -0.18 / down -0.29R (n 53).
Research exit from the 1-minute simulator (entry at the next 1-minute open); live enters at the bar close.
Fails the pre-declared candidate rule (n_train >= 150) and the multiple-testing bar
(study 3.26, live-long lineage 4.91). NEAR-MISS, observation only, fails the multiple-testing bar; owner 2026-10-20: Testing 2.
Educational only - not financial advice.
Every trade is also an NS1 trade (a filtered copy of the live parent)."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "holdtr"
WINDOW = (950, 1130)
LAYERS = ['rsi crosses below 40 on this bar', 'rsi5 >= 80', 'stock > 2% above its open', 'SPY running low since 09:35 <= -0.15% [context: spy_fo]', 'SPY close >= that low + 0.10 [context: spy_fo]', '09:50-11:30 ET']


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


def _ns1(df, key):
    """Live NS1: RSI(14) crosses down through 40 while RSI(5) >= 80 and the stock is > 2% above its open."""
    rsi = _col(df, "rsi")
    return (rsi <= 40) & (_shift(rsi, key, 1) > 40) & (_col(df, "rsi5") >= 80) & (_col(df, "fromOpen") > 2)


def mask(df) -> np.ndarray:
    if "spy_fo" not in df:
        return np.zeros(len(df), dtype=bool)       # fail-safe: no context -> no trades
    key = _keys(df)
    tod = _col(df, "tod")
    with np.errstate(invalid="ignore"):
        spy = _col(df, "spy_fo")
        spymin = pd.Series(spy).groupby(key).cummin().to_numpy()     # running low of SPY 5-min closes since 09:35
        filt = (spymin <= -0.15) & (spy >= spymin + 0.10)
        m = _ns1(df, key) & filt
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
