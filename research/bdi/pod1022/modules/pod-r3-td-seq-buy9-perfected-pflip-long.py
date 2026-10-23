"""pod-r3-td-seq-buy9-perfected-pflip-long - TD Sequential 5-minute Buy Setup 9 (perfected) with price-flip
confirmation (LONG).

Source: Tom DeMark, 'Applying TD Sequential to Intraday Charts' (PDF); ProRealCode forum note that waiting for the
first opposing bar improves the win/loss rate.
URL: https://c.mql5.com/forextsd/forum/114/thomas_demark_-_applying_td_sequential_to_intraday_charts.pdf

New family (no DeMark/TD count in the repo). Rules (plain English), per symbol-day on 5m closes:
  1. Buy setup: 9 consecutive bars each closing below the close 4 bars earlier (the 4-bar look-back stays inside the
     day; the frame starts at 09:50, so the earliest bar 9 is the 13th bar of the frame day).
  2. Perfection: low of setup bar 8 or bar 9 <= min(low of bar 6, low of bar 7).
  3. Price flip: within the next 3 bars, the FIRST bar whose close > the prior bar's close; entry at that bar's close.
  4. Filters on the entry bar: spy_fo > -0.6; stock fromOpen in [-4%, 0]; vwapDistPct <= -0.3; rsi <= 40.
  Window 10:30-14:30. Stop (GEOM S): lowest low of the 9 setup bars - 0.05 x atr_d. Target: the high of setup bar 1,
  capped at entry + 2R; otherwise flat 15:55. Scorer control: hold.
Harness notes (pre-declared): only the count==9 bar starts a setup (bars 10+ of a longer run do not re-fire); a
setup whose bar-1 high is not above the entry is skipped by the scorer (no valid target). No tweak used.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r28_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["TD buy setup 9 (close < close 4 bars earlier x9, within day)", "perfected (low 8 or 9 <= min low 6,7)",
          "price flip within 3 bars (first close > prior close)", "spy_fo > -0.6, fromOpen in [-4,0]",
          "vwapDistPct <= -0.3, rsi <= 40", "10:30-14:30", "stop setup low - 0.05 ATR, target bar-1 high capped 2R"]
_ST = {}


@numba.njit(cache=False)
def _td(c, h, l, st):
    n = len(c)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    cnt = 0
    pos = 0
    for i in range(n):
        if st[i]:
            pos = 0
            cnt = 0
        else:
            pos += 1
        if pos >= 4 and c[i] < c[i - 4]:
            cnt += 1
        else:
            cnt = 0
        if cnt == 9:
            j = i
            perf = min(l[j], l[j - 1]) <= min(l[j - 2], l[j - 3])
            if not perf:
                continue
            lo = l[j - 8]
            for q in range(j - 7, j + 1):
                if l[q] < lo:
                    lo = l[q]
            hi1 = h[j - 8]
            # price flip: first up-close bar within j+1..j+3 of the same day
            for e in range(j + 1, min(j + 4, n)):
                if st[e]:
                    break
                if c[e] > c[e - 1]:
                    stop[e] = lo
                    tgt[e] = hi1
                    break
    return stop, tgt


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i])


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not U.ctx_ok(df, ["spy_fo"]):
        _ST[id(df)] = (np.full(n, np.nan), np.full(n, np.nan))
        return np.zeros(n, bool)
    c, h, l, atr = U.f(df, "close"), U.f(df, "high"), U.f(df, "low"), U.f(df, "atr_d")
    st = U.start(U.daykey(df))
    lo, hi1 = _td(c, h, l, st)
    stop = lo - 0.05 * atr
    tgt = np.minimum(hi1, c + 2.0 * (c - stop))
    tod = df["tod"].to_numpy(float)
    fo = U.f(df, "fromOpen")
    with np.errstate(invalid="ignore"):
        m = np.isfinite(lo)
        m &= U.f(df, "spy_fo") > -0.6
        m &= (fo >= -4.0) & (fo <= 0.0)
        m &= U.f(df, "vwapDistPct") <= -0.3
        m &= U.f(df, "rsi") <= 40
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
