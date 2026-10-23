"""pod-lunch-effect-index-long - Lunch Effect: long index ETFs at 11:00 after a flat or weak morning (LONG).

Source: Quantpedia, Vojtko & Dujava 'Lunch Effect in the U.S. Stock Market Indices' (SSRN 4934614, 2024).
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4934614

VARIANT of wi-lunch-reversal (idea, same Quantpedia page: stocks, both sides, fade stretched RSI 12:00-13:30). Stated
change: index ETFs only, long only, a fixed 11:00 entry and a flat-morning gate instead of a stretch.

Rules (plain English), decision bar = the bar closing 11:00, SYMBOLS SPY, QQQ, IWM, DIA:
  1. Flat / weak morning: fromOpen on the 10:55 bar between -0.6% and +0.2%.
  2. 11:00 close above the prior-day low, and SPY's gap today >= -1.0% (SPY's own row).
  3. RSI(14) <= 55 on the 11:00 bar; 5-bar change (11:00 close vs the 10:35 close) not below -0.3%.
  Entry: the 11:00 close. Stop: 0.25 x atr_d = 1R (GEOM hold: stop 1R, no target). Exit: the paper's 14:00 time exit
  is not in the harness, so the scored trade holds to 15:55; the 14:00 mark-to-market is computed separately from the
  trades parquet and the frames (reported alongside, not a second configuration). No tweak used. Costs in (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "hold"
WINDOW = (1100, 1100)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = []
LAYERS = ["SPY/QQQ/IWM/DIA", "fromOpen at 10:55 in [-0.6, +0.2]%", "close > PDL, SPY gap >= -1.0%",
          "rsi <= 55, 5-bar change >= -0.3%", "entry 11:00 close, stop 1R, hold"]
import numpy as np
import pandas as pd

def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day (NaN across a day boundary)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each symbol-day."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _at(x, k, tod, T):
    """Value of x on the bar closing at T, broadcast to its symbol-day. Use only on rows with tod >= T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]



def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    sym = df["symbol"].astype(str).to_numpy()
    d = df["date"].astype(str).to_numpy()
    sel = sym == "SPY"
    if not sel.any():
        return z
    sg = pd.Series(_f(df, "gap")[sel], index=d[sel]).groupby(level=0).first()
    spy_gap = sg.reindex(d).to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        fo = _f(df, "fromOpen")
        m = (tod == 1100)
        pfo = _lag(fo, k, 1)
        m &= (_lag(tod.astype(float), k, 1) == 1055) & (pfo >= -0.6) & (pfo <= 0.2)
        m &= _f(df, "dist_pdl_atr") > 0
        m &= spy_gap >= -1.0
        m &= _f(df, "rsi") <= 55
        m &= (c / _lag(c, k, 5) - 1) * 100 >= -0.3
    return np.asarray(m, dtype=bool)
