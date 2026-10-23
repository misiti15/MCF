"""pod-bespoke-friday-gapdown-index-orh-long - Friday 1%+ gap-down index ETF opening-range reclaim (gap-fill LONG).

Source: Bespoke Premium 'SPY Gaps Down by Weekday' (Friday 1%+ gap-downs had the largest open-to-close bounces since
1993), cross-checked with the CXO Advisory 'Gap reversal or continuation' SPY study.
URL: https://www.bespokepremium.com/author/ekop105seb21/page/85

VARIANT of pod-axia-inventory-correction-gapdown-etf-long. Stated change: Friday only (the Bespoke weekday stat), a
larger gap threshold, and a 15-minute opening-range reclaim trigger. The same mask on Mon-Thu is scored as a control
(pod-bespoke-friday-gapdown-index-orh-long-ctrl-monthu) so the Friday condition has to earn its place.

Rules (plain English, LONG), SYMBOLS SPY, QQQ, IWM, DIA:
  1. Weekday = Friday, or a session followed by a non-trading day (next listed session > 1 calendar day later and
     <= 4; the exchange calendar is known in advance).
  2. Gap: open / D-1 close - 1 <= -1.0% AND |gap| >= 0.6 x atr_d% (atr_d = daily ATR14 from completed days to D-1).
  3. Bar close 09:50-11:00: the first 5-min close above the 09:30-09:45 high AND above session VWAP.
  4. The 09:30-09:45 low is not more than 0.5 x atr_d below the open (no runaway flush).
  Entry: that bar's close. Stop (GEOM S): session LOD - 0.05 x atr_d. Target: D-1 close (full gap fill); otherwise
  flat 15:55. One trade per symbol per day (scorer: first bar).
Data: the 09:30-09:45 range and 09:30 open from _r24_bars (1-minute vendor bars; locked block never read).
No tweak made. Costs per config/default.yaml (applied by the scorer; entries before 10:30 carry the x1.4 cost).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (950, 1100)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
LAYERS = ["Friday / pre-holiday", "gap <= -1% and >= 0.6 atr_d%", "first close > 09:30-09:45 high and > VWAP",
          "09:30-09:45 low >= open - 0.5 atr_d", "stop LOD - 0.05 atr_d, target D-1 close"]
FRIDAY = True

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
    dv = R.daymap(df, ["or_h", "or_l", "o935"])
    dd = R.daymap(df, ["next_gap_days"], R.daily_feats())
    wd = pd.to_datetime(pd.Series(df["date"].to_numpy()).astype(str)).dt.weekday.to_numpy()
    ng = dd["next_gap_days"]
    fri = (wd == 4) | ((ng > 1) & (ng <= 4))
    day_ok = fri if FRIDAY else ~fri
    gap = C.f(df, "gap")
    with np.errstate(invalid="ignore", divide="ignore"):
        atrp = b["atr"] / b["pc"] * 100
        m = day_ok & (gap <= -1.0) & (np.abs(gap) >= 0.6 * atrp)                            # (1) (2)
        m &= (dv["o935"] - dv["or_l"]) <= 0.5 * b["atr"]                                    # (4)
        trig = (c > dv["or_h"]) & (c > b["vwap"]) & (tod >= 950) & (tod <= 1100)
        first = trig & ((pd.Series(trig.astype(float)).groupby(k).cumsum().to_numpy() - trig) == 0)
        m &= first                                                                          # (3)
        sp = b["lod"] - 0.05 * b["atr"]
        tg = b["pc"]
        m &= (sp < c) & (tg > c)
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
