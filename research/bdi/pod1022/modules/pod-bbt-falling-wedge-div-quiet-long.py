"""pod-bbt-falling-wedge-div-quiet-long - Falling wedge with RSI bullish divergence on a quiet day, upper-line break
(LONG).

Source: Bear Bull Traders chart-pattern / reversal lessons (wedges and divergence as reversal confirmation; Aziz
reversal webinar). Not re-fetched this round.
URL: https://www.youtube.com/@BearBullTraders

VARIANT of the F3 mirror (bullish exhaustion long: rsi5 < 15, below SMA20, bull_div, lower wick). Stated change: not a
single exhaustion bar - it needs a contracting decline (a wedge: the last 3 swing highs and lows both falling, bar
ranges shrinking), confirmed by bull_div, and the entry is the break of the wedge's upper boundary on a quiet day.

Rules (plain English), decision bar i; the wedge window is bars i-N..i-1, N scanned from 10 up to 20 (pre-declared:
the shortest window that passes is used; the source says 10-20 bars):
  1. The 3 most recent 3-bar pivot highs and the 3 most recent 3-bar pivot lows in the window are each strictly
     falling; the drop between the last two pivot lows is < 0.6 x the drop between the first two (converging); the
     mean bar range (high - low) of the window's last 5 bars is <= 0.7 x that of its first 5 bars.
  2. bull_div == 1 on one of bars i-3..i.
  3. Bar i: close > the most recent pivot high and close > EMA9 (EMA of the day's 5-minute closes, seeded 09:50).
  4. Quiet day: HOD - LOD so far <= 1.0 x atr_d and |spy_fo| <= 0.4%.
  5. close < session VWAP.
  Entry: close_i, bar close 10:30-14:30. Stop (GEOM S): wedge low (lowest low of the window and bar i) - 0.03 x atr_d.
  Target: the wedge's first pivot high, capped at session VWAP; flat 15:55. Costs in (scorer).
No tweak made. Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["wedge: 3 falling pivot highs + 3 falling pivot lows, converging, ranges shrinking (10-20 bars)",
          "bull_div in last 4 bars", "close > last pivot high and > EMA9", "day range <= 1 ATR, |spy_fo| <= 0.4%",
          "close < VWAP", "stop wedge low - 0.03 ATR, target first pivot high capped at VWAP", "10:30-14:30"]

_ST = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, hod, lod, vw, bd, spy, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        ev = c[i0]
        for i in range(i0, i1):
            ev = ev + 0.2 * (c[i] - ev)
            if tod[i] < w0 or tod[i] > w1 or i - i0 < 10:
                continue
            a = atr[i]
            if not (a > 0 and c[i] > ev and c[i] < vw[i] and hod[i] - lod[i] <= 1.0 * a and abs(spy[i]) <= 0.4):
                continue
            div = False
            for t in range(max(i0, i - 3), i + 1):
                if bd[t] == 1:
                    div = True
            if not div:
                continue
            for N in range(10, 21):
                st = i - N
                if st < i0:
                    break
                ph = np.full(3, -1)
                pl = np.full(3, -1)
                ch = 0
                cl = 0
                for k in range(i - 2, st, -1):
                    if ch < 3 and h[k] > h[k - 1] and h[k] > h[k + 1]:
                        ph[2 - ch] = k
                        ch += 1
                    if cl < 3 and l[k] < l[k - 1] and l[k] < l[k + 1]:
                        pl[2 - cl] = k
                        cl += 1
                if ch < 3 or cl < 3:
                    continue
                if not (h[ph[0]] > h[ph[1]] and h[ph[1]] > h[ph[2]]):
                    continue
                if not (l[pl[0]] > l[pl[1]] and l[pl[1]] > l[pl[2]]):
                    continue
                if not ((l[pl[1]] - l[pl[2]]) < 0.6 * (l[pl[0]] - l[pl[1]])):
                    continue
                r1 = 0.0
                r2 = 0.0
                for k in range(5):
                    r1 += h[st + k] - l[st + k]
                    r2 += h[i - 5 + k] - l[i - 5 + k]
                if not (r2 <= 0.7 * r1):
                    continue
                if not (c[i] > h[ph[2]]):
                    continue
                wl = 1e18
                for k in range(st, i + 1):
                    wl = min(wl, l[k])
                sp = wl - 0.03 * a
                tp = min(h[ph[0]], vw[i])
                if sp < c[i] and tp > c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = tp
                    break
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, dtype=bool)
    f = lambda k: df[k].to_numpy(float)
    c = f("close")
    atr = f("atr_d")
    vw = c / (1 + f("vwapDistPct") / 100)
    hod = c + f("dist_hod_atr") * atr
    lod = c - f("dist_lod_atr") * atr
    b, e = _segments(df)
    m, stop, tgt = _kern(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), hod, lod, vw,
                         np.nan_to_num(f("bull_div")), f("spy_fo"), atr, WINDOW[0], WINDOW[1])
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
