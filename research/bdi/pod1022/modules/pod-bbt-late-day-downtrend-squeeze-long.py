"""pod-bbt-late-day-downtrend-squeeze-long - Late-day short squeeze: an all-day downtrend that puts in a higher low
after the 13:00-14:30 LOD and breaks its 30-minute high (LONG).

Source: Bear Bull Traders YouTube (Aziz / BBT moderators on end-of-day short covering in stocks that trended down all
day). Not re-fetched this round.
URL: https://www.youtube.com/@BearBullTraders

VARIANT of pod-smb-backside-long-into-vwap (related to ST1-ordn-long-pm, which buys the OR-low breakdown). Stated
changes: late window (14:00-15:00 only); the stock was below VWAP on >= 85% of its bars all day (persistent downtrend,
not a single flush >= 0.75 ATR below VWAP); the trigger is a break of the 30-minute (6-bar) high after a higher low,
not a tight base; and a breadth-improving gate is added.

Rules (plain English), decision bar i:
  1. fromOpen <= -2.0% and >= 85% of today's frame bars up to i (09:50 onward) closed below session VWAP.
  2. The LOD was set on a frame bar closing 13:00-14:30 (the last bar whose low equals the running LOD), and the
     lowest low after it (through bar i) is >= LOD + 0.10 x atr_d (higher low); at least 2 bars after the LOD bar.
  3. Bar i: close > max(high of bars i-6..i-1), volumeRatio >= 1.3, rsi rising (rsi_i > rsi_{i-1}).
  4. breadth at i >= breadth on the bar 30 minutes earlier + 0.05, and spy_fo > -0.6%.
  5. Session VWAP - close_i >= 0.25 x atr_d.
  Entry: close_i, bar close 14:00-15:00. Stop (GEOM S): higher low - 0.03 x atr_d. Target: session VWAP at entry,
  else flat 15:55. Costs in (scorer).
Frame note: a LOD set 09:30-09:45 cannot be dated on frame bars; such days do not qualify (they fail rule 2 anyway).
No tweak made. Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1400, 1500)
CONTEXT = ["breadth", "spy_fo"]
LAYERS = ["fromOpen <= -2%, >= 85% of bars below VWAP", "LOD set 13:00-14:30, higher low >= LOD + 0.10 ATR",
          "close > 6-bar high, volumeRatio >= 1.3, rsi rising", "breadth up >= 0.05 over 30 min, spy_fo > -0.6%",
          "VWAP >= 0.25 ATR above close", "stop HL - 0.03 ATR, target VWAP", "14:00-15:00"]

_ST = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _mins(t):
    return (t // 100) * 60 + t % 100


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, lod, vw, vr, rsi, fo, br, spy, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        j = -1
        below = 0
        for i in range(i0, i1):
            if c[i] < vw[i]:
                below += 1
            if l[i] <= lod[i] + 1e-6 * c[i]:
                j = i
            if tod[i] < w0 or tod[i] > w1 or j < 0 or i - i0 < 6:
                continue
            a = atr[i]
            if not (a > 0 and fo[i] <= -2.0 and below >= 0.85 * (i - i0 + 1)):
                continue
            if tod[j] < 1300 or tod[j] > 1430 or i - j < 2:
                continue
            hl = 1e18
            for t in range(j + 1, i + 1):
                hl = min(hl, l[t])
            if hl < lod[i] + 0.10 * a:
                continue
            hh = -1e18
            for t in range(i - 6, i):
                hh = max(hh, h[t])
            if not (c[i] > hh and vr[i] >= 1.3 and rsi[i] > rsi[i - 1]):
                continue
            # breadth on the bar 30 minutes earlier (same symbol-day)
            tm = _mins(tod[i]) - 30
            b6 = np.nan
            for t in range(i - 1, i0 - 1, -1):
                if _mins(tod[t]) == tm:
                    b6 = br[t]
                    break
                if _mins(tod[t]) < tm:
                    break
            if not (br[i] >= b6 + 0.05 and spy[i] > -0.6):
                continue
            if vw[i] - c[i] < 0.25 * a:
                continue
            sp = hl - 0.03 * a
            if sp < c[i]:
                m[i] = True
                stop[i] = sp
                tgt[i] = vw[i]
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if n == 0 or "breadth" not in df or "spy_fo" not in df:
        return np.zeros(n, dtype=bool)
    f = lambda k: df[k].to_numpy(float)
    c = f("close")
    atr = f("atr_d")
    vw = c / (1 + f("vwapDistPct") / 100)
    lod = c - f("dist_lod_atr") * atr
    b, e = _segments(df)
    m, stop, tgt = _kern(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), lod, vw, f("volumeRatio"),
                         f("rsi"), f("fromOpen"), f("breadth"), f("spy_fo"), atr, WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


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
