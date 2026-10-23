"""pod-bespoke-hotcpi-gapdown-first-hour-bounce-long - CPI-day gap-down first-hour relief bounce (LONG).

Source: Bespoke Premium 'Market Reaction to CPI' (hot-CPI intraday pattern: the S&P gaps lower, generally rises until
about 10:45, then weakens); thetrading.tools CPI economic-calendar stats.
URL: https://www.bespokepremium.com/tag/intraday/

VARIANT of pod-axia-inventory-correction-gapdown-etf-long and the gap-down long family. Stated change: a new regime
use - only US CPI release days (BLS calendar, published in advance; list in _r24_bars.CPI_DATES) - and the source's
10:45 time exit.

Rules (plain English, LONG), SYMBOLS SPY, QQQ, IWM:
  1. Today is a CPI release day.
  2. Gap: open / D-1 close - 1 between -2.0% and -0.4% (2%+ CPI gap-downs mostly continued lower; excluded).
  3. Bar close 09:40-10:15: a 5-min close above the prior bar's high while rsi5 was <= 30 on one of the previous 3
     bars.
  4. The close is still below today's open (buying the dip, not the breakout).
  Entry: that bar's close. Stop (GEOM S): session LOD - 0.05 x atr_d. Target: the session open or VWAP, whichever is
  nearer above the entry (none when neither is above).
Harness deviations (stated): (a) the frame starts at the 09:50 bar and the prior-bar high / rsi5 history exist only
for frame bars, so signals are possible from the 09:55 bar to 10:15 (the 09:40-09:50 part of the window is lost);
(b) the source's hard 10:45 exit is not available in the scorer - trades without a stop / target fill are held to
15:55 here, which is exactly the documented post-10:45 fade the source avoids. The scorer numbers below therefore
test the entry, not the source's exit.
Low frequency (about 12 CPI days a year x 3 symbols): n is reported as is.
No tweak made. Costs per config/default.yaml (applied by the scorer; entries before 10:30 carry the x1.4 cost).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (950, 1015)
SYMBOLS = ["SPY", "QQQ", "IWM"]
LAYERS = ["CPI release day", "gap -2.0..-0.4%", "close > prior bar high, rsi5 <= 30 in prior 3 bars",
          "close < open", "stop LOD - 0.05 atr_d, target nearer of open / VWAP"]

import numpy as np
import pandas as pd

import _cwt3_bars as C
import _r24_bars as R

_ST = {}


def _compute(df):
    n = len(df)
    if not n:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    b = C.base(df)
    k = C.key(df)
    tod, c = b["tod"], b["c"]
    ds = pd.Series(df["date"].to_numpy()).astype(str).to_numpy()
    cpi = np.isin(ds, R.CPI_DATES)
    gap = C.f(df, "gap")
    r5 = C.f(df, "rsi5")
    with np.errstate(invalid="ignore"):
        m = cpi & (gap >= -2.0) & (gap <= -0.4)                                             # (1) (2)
        m &= (tod >= 950) & (tod <= 1015)
        m &= c > C.lag(b["h"], k, 1)                                                        # (3)
        low_rsi = np.zeros(n, bool)
        for j in (1, 2, 3):
            low_rsi |= C.lag(r5, k, j) <= 30
        m &= low_rsi
        m &= c < b["opn"]                                                                   # (4)
        sp = b["lod"] - 0.05 * b["atr"]
        t1, t2 = b["opn"], b["vwap"]
        tg = np.where((t1 > c) & (t2 > c), np.minimum(t1, t2), np.where(t1 > c, t1, np.where(t2 > c, t2, np.nan)))
        m &= sp < c
    return np.asarray(m, bool), sp, tg


def mask(df) -> np.ndarray:
    try:
        m, stop, tgt = _compute(df)
    except (KeyError, FileNotFoundError):
        m, stop, tgt = np.zeros(len(df), bool), np.full(len(df), np.nan), np.full(len(df), np.nan)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
