"""pod-wt-gap-full-fill-pdc-hold-long - Gap-up fully filled to the prior close, hammer hold at the PDC, long back
toward VWAP (LONG).

Source: Warrior Trading / Ross Cameron, prior-day close as support / 'red-to-green line' teaching; Bear Bull Traders
support-resistance lessons (prior-day close as an intraday level). Not re-fetched this round.
URL: https://www.youtube.com/@DaytradeWarrior

VARIANT of CWT08 good-news gap dip buy (cwt-a-a9) and the red-to-green line. Stated changes against CWT08: a FULL gap
fill to the prior-day close (CWT08 uses 25/40% of the gap), no news / rvol requirement, entry on a hammer hold AT the
PDC (not a VWAP reclaim), and a quiet-day gate. Against red-to-green: it buys the hold of the line from above and
never needs a cross from red to green.

Rules (plain English):
  1. gap between +1.0% and +4.0%.
  2. First touch of the prior close: close within +/- 0.05 x atr_d of the PDC (PDC = open / (1 + gap/100), open =
     close / (1 + fromOpen/100)), and this bar is in the FIRST touch episode: the first bar of the day whose running
     LOD reached PDC + 0.05 x atr_d is this bar or one of the 2 before it (a touch in 09:30-09:45 dates to 09:50).
     Reading note: requiring the touch bar itself to close up (rule 3) is nearly impossible (the first close at the
     level from above is a down close; 0 trades in a June-2025 smoke test), so 'first touch' is read as the first
     touch episode of up to 3 bars. This is an interpretation fixed before the full score, not a tuned parameter.
  3. This bar: lower_wick >= 0.45, close > prior close, rsi5 <= 30 on one of this bar and the 2 before.
  4. |spy_fo| <= 0.5%.
  5. Session VWAP - close >= 0.3 x atr_d.
  Entry: that close, bar close 10:00-14:00. Stop (GEOM S): PDC - 0.15 x atr_d. Target: session VWAP at entry, else
  flat 15:55.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1400)
CONTEXT = ["spy_fo"]
LAYERS = ["1 <= gap <= 4", "close within 0.05 ATR of the PDC, first touch episode (<= 3 bars)", "lower_wick >= 0.45, close up, rsi5 <= 30 in last 3 bars",
          "|spy_fo| <= 0.5", "VWAP >= 0.3 ATR above", "stop PDC - 0.15 ATR, target VWAP", "10:00-14:00"]

import numba
import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _base(df):
    k = _key(df)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=df["tod"].to_numpy(np.int64), c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day (includes 09:30-09:45)
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    return b


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


def _prev(x, k, n=1):
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        same = np.zeros(len(x), bool)
        same[n:] = k[n:] == k[:-n]
        p[~same] = np.nan
    return p


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    k, c, a, pc, tod = b["k"], b["c"], b["atr"], b["pc"], b["tod"]
    r5 = _f(df, "rsi5")
    with np.errstate(invalid="ignore"):
        gap = _f(df, "gap")
        m = (gap >= 1.0) & (gap <= 4.0)
        m &= np.abs(c - pc) <= 0.05 * a
        lod = b["lod"]
        tb = (lod <= pc + 0.05 * a) & ~(_prev(lod, k) <= pc + 0.05 * a)      # first-touch bar of the day
        tbf = tb.astype(float)
        m &= tb | (_prev(tbf, k) == 1) | (_prev(tbf, k, 2) == 1)
        m &= _f(df, "lower_wick") >= 0.45
        m &= c > _prev(c, k)
        rmin = np.fmin(r5, np.fmin(_prev(r5, k), _prev(r5, k, 2)))
        m &= rmin <= 30
        m &= np.abs(_f(df, "spy_fo")) <= 0.5
        m &= b["vwap"] - c >= 0.3 * a
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (pc - 0.15 * a, b["vwap"])
    return np.asarray(m, dtype=bool)
