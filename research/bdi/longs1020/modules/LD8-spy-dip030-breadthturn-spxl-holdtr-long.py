"""LD8-spy-dip030-breadthturn-spxl-holdtr-long - BDI longs1020 Part A (A-SPY-abs030-brd-holdtr), NEAR-MISS, NOT A CANDIDATE.
"SPY Dip of 0.30%, Breadth Turn (SPXL, trailing)".
SPY's running low of 5-minute closes since 09:35 is <= -0.30% below its 09:30 open; then on a bar closing
09:50-10:30 market breadth (share above VWAP) is >= 10 points above its low since 09:50 and SPY closes
higher than the bar before; buy SPXL, first such bar of the day only. Exit holdtr (stop 1R, no target; once +1R
the stop trails 1R behind the best price; flat 15:55; R = 0.25 x SPXL daily ATR).
Use with symbols: [SPXL], pin_symbols: true, context: [spy_fo, breadth], window [950, 1030].
Open history, production costs, 1-minute simulator (entry at the next 1-minute open; live enters at the bar close)
(research/bdi/longs1020/results_A.csv):
train n 39 +0.045R t 0.20 (random 09:50-10:30 SPXL long -0.047R; same dip days random bar +0.059R); valid n 31
+0.121R t 0.48 (random -0.041R; same days +0.237R); all n 70 (0.16/day), +0.078R t 0.47, without the best day
+0.009R; up +1.08 / flat -0.05 / down -0.43R (n 33). Does not beat the same-day random entry on either split.
Fails the pre-declared candidate rule (valid t >= 1.5 and beat the same-day random entry) and the multiple-testing bar
(study 3.26, index-dip lineage 5.00). NEAR-MISS, observation only, fails the multiple-testing bar; owner 2026-10-20: Testing 2.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "holdtr"
WINDOW = (950, 1030)
SYMBOLS = ["SPXL"]
LAYERS = ['SPY running low of 5-min closes <= -0.30% from the open [context: spy_fo]', 'breadth >= its 09:50+ low + 0.10 [context: breadth]', "SPY close above the prior bar's close", 'first qualifying bar of the day', '09:50-10:30 ET']


def _day(df):
    if "symbol" in df and "date" in df:
        return pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    if "date" in df:
        return pd.factorize(df["date"].astype(str))[0]
    return np.zeros(len(df), dtype=np.int64)


def _col(df, k):
    return df[k].to_numpy(dtype=float)


def mask(df) -> np.ndarray:
    if "spy_fo" not in df or "breadth" not in df:
        return np.zeros(len(df), dtype=bool)       # fail-safe: no context -> no trades
    key = _day(df)
    k = pd.Series(key)
    tod = _col(df, "tod")
    s = pd.Series(_col(df, "spy_fo"))
    b = pd.Series(np.where(tod >= 950, _col(df, "breadth"), np.nan))
    smin = s.groupby(k).cummin().to_numpy()            # running low of SPY 5-min closes since 09:35
    bmin = b.groupby(k).cummin().to_numpy()            # breadth low since 09:50
    sprev = s.groupby(k).shift(1).to_numpy()
    lim = -0.30
    with np.errstate(invalid="ignore"):
        m = (smin <= lim) & (b.to_numpy() >= bmin + 0.10) & (s.to_numpy() > sprev)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    first = pd.Series(m).groupby(k).cumsum().to_numpy() == 1
    return np.asarray(m & first, dtype=bool)
