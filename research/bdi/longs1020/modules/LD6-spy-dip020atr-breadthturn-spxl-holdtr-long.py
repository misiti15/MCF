"""LD6-spy-dip020atr-breadthturn-spxl-holdtr-long - BDI longs1020 Part A (A-SPY-rel020-brd-holdtr), NEAR-MISS, NOT A CANDIDATE.
"SPY Dip of 0.2 ATR, Breadth Turn (SPXL, trailing)".
SPY's running low of 5-minute closes since 09:35 is <= -0.20 x SPY's daily ATR% below its 09:30 open; then on a bar closing
09:50-10:30 market breadth (share above VWAP) is >= 10 points above its low since 09:50 and SPY closes
higher than the bar before; buy SPXL, first such bar of the day only. Exit holdtr (stop 1R, no target; once +1R
the stop trails 1R behind the best price; flat 15:55; R = 0.25 x SPXL daily ATR).
Use with symbols: [SPXL], pin_symbols: true, context: [spy_fo, breadth], window [950, 1030].
SPY's daily ATR is not in the SPXL frame live, so SPY ATR% is taken as SPXL ATR% (SPXL atr_d / SPXL close at the
09:50 bar) / 2.93, the median SPXL/SPY ATR% ratio on the open history (5%-95%: 2.84-3.31 x 1/3 scale, see verify_modules.json). Parity with the scan:
verify_modules.json.
Open history, production costs, 1-minute simulator (entry at the next 1-minute open; live enters at the bar close)
(research/bdi/longs1020/results_A.csv):
train n 54 +0.058R t 0.31 (random 09:50-10:30 SPXL long -0.047R; same dip days random bar +0.060R); valid n 50
+0.169R t 0.89 (random -0.041R; same days +0.201R); all n 104 (0.25/day), +0.111R t 0.84, without the best day
+0.065R; up +0.97 / flat -0.07 / down -0.29R (n 42). Does not beat the same-day random entry on valid.
Fails the pre-declared candidate rule (valid t >= 1.5 and beat the same-day random entry) and the multiple-testing bar
(study 3.26, index-dip lineage 5.00). NEAR-MISS, observation only, fails the multiple-testing bar; owner 2026-10-20: Testing 2.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "holdtr"
WINDOW = (950, 1030)
SYMBOLS = ["SPXL"]
SPXL_SPY_ATR = 2.93   # median SPXL ATR% / SPY ATR% on the open history (research/bdi/longs1020/verify_modules.json)
LAYERS = ['SPY running low of 5-min closes <= -0.20 x SPY daily ATR% from the open [context: spy_fo; SPY ATR% ~ SPXL ATR% / 2.93]', 'breadth >= its 09:50+ low + 0.10 [context: breadth]', "SPY close above the prior bar's close", 'first qualifying bar of the day', '09:50-10:30 ET']


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
    atrp = _col(df, "atr_d") / pd.Series(np.where(tod == 950, _col(df, "close"), np.nan)).groupby(k).transform("max").to_numpy() * 100 / SPXL_SPY_ATR
    lim = -0.20 * atrp
    with np.errstate(invalid="ignore"):
        m = (smin <= lim) & (b.to_numpy() >= bmin + 0.10) & (s.to_numpy() > sprev)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    first = pd.Series(m).groupby(k).cumsum().to_numpy() == 1
    return np.asarray(m & first, dtype=bool)
