"""pod-smb-midday-shock-flush-into-daily-support-long - Midday shock flush (breaking-news style volume spike) into daily
support that holds: fade long (LONG).

Source: SMB Capital - 'Name of the play: Resistance fade after breaking news' (SMB Foundation curriculum), mirrored to
support, with SMB's fade-trade cautions.
URL: https://smbpowerpoints.s3.amazonaws.com/SMB%20Foundation.pdf

VARIANT of pod-smb-lt-support-first-test-hold-long. What changes: the trigger is a sudden midday shock (an intraday
news-style flush) instead of an orderly first test, the level is the long-term support it runs into, and it is
mirrored from SMB's resistance fade after breaking news.

Data: frame columns (5m ATR14 = atrPct x close, volumeRatio = bar volume / its 20-bar average, VWAP) and daily support
levels as of D-1 (_r34_util: 20-day low of D-20..D-1 and the last confirmed daily swing low, completed days only).

Rules (plain English):
  1. Shock (bar close 11:00-14:30): the drop from the highest high of the last <= 3 bars (the shock bar and up to 2
     bars before it) to the shock bar's low is >= 3 x ATR14(5m), and one of those bars has volume >= 5x its 20-bar
     average.
  2. The flush low (lowest low since the shock window began) is within 0.3 daily ATR of a daily support level (the
     20-day low or the last daily swing low, whichever is nearer); no 5m close below that level - 0.1 daily ATR up to
     entry (a close below ends the day).
  3. Hold: two consecutive 5m bars after the flush-low bar that do not make a new low (a new low within the support
     band resets the hold count and the flush low).
  4. Entry: a 5m close above the second hold bar's high, within 3 bars of it and within 12 bars of the shock bar.
  Stop: flush low - 0.05 daily ATR. Target: 50% retrace of the shock leg (shock-window high to flush low), or VWAP if
  nearer (only levels above the entry). Time stop 45 minutes (9 bars, GEOM S+x MAX_BARS). Flat 15:55.
  Skips: price < $10; earnings days are already removed by the scorer's blackout (4 sessions either side); there is
  no float data, so low float is not filtered (declared gap; universe adv20 >= $20M).
Reading (pre-declared): 'shock bar range' = the shock leg of rule 1. Tweak: none. 1 configuration. Costs in (scorer).
Educational only - not financial advice."""
import numba
import numpy as np

import _r33_util as U
import _r34_util as D34

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 9
WINDOW = (1105, 1500)
LAYERS = ["11:00-14:30 drop >= 3 ATR5 in <= 3 bars with a >= 5x volume bar",
          "flush low within 0.3 ATR of 20d low / last daily swing low, no close below level - 0.1 ATR",
          "two bars without a new low", "close above 2nd hold bar high",
          "stop flush low - 0.05 ATR, target min(50% shock leg, VWAP), 45-min time stop", "price >= 10"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, atr5, vr, vw, atr, s1, s2):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        a = atr[i0]
        if not (a > 0) or not (c[i0] >= 10):
            continue
        state = 0            # 0 searching shock, 1 armed
        L = 0.0
        S = 0.0
        hi = 0.0
        tshock = 0
        hold = 0
        h2 = 0.0
        thold = 0
        for i in range(i0, i1):
            if state == 1:
                if c[i] < S - 0.1 * a or i - tshock > 12:
                    break
                if hold >= 2 and i - thold <= 3 and c[i] > h2:
                    sp = L - 0.05 * a
                    t1 = L + 0.5 * (hi - L)
                    tp = t1
                    if vw[i] > c[i] and vw[i] < t1:
                        tp = vw[i]
                    if tp > c[i] and sp < c[i]:
                        m[i] = True
                        stop[i] = sp
                        tgt[i] = tp
                    break
                if hold >= 2 and i - thold > 3:
                    break
                if l[i] < L:
                    L = l[i]
                    if abs(L - S) > 0.3 * a:
                        break
                    hold = 0
                else:
                    hold += 1
                    if hold == 2:
                        h2 = h[i]
                        thold = i
                continue
            if tod[i] < 1100 or tod[i] > 1430 or i - 2 < i0:
                continue
            hh = max(h[i], max(h[i - 1], h[i - 2]))
            vmax = max(vr[i], max(vr[i - 1], vr[i - 2]))
            if atr5[i] > 0 and hh - l[i] >= 3.0 * atr5[i] and vmax >= 5.0:
                lo = min(l[i], min(l[i - 1], l[i - 2]))
                best = np.inf
                S = np.nan
                for lev in (s1[i0], s2[i0]):
                    if lev == lev and abs(lo - lev) <= 0.3 * a and abs(lo - lev) < best:
                        best = abs(lo - lev)
                        S = lev
                if S == S and c[i] >= S - 0.1 * a:
                    state = 1
                    L = lo
                    hi = hh
                    tshock = i
                    hold = 0
    return m, stop, tgt


def mask(df):
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    if not n:
        return z
    bb = U.base(df)
    Dd = D34.map_daily(df, ["lo20_1", "swl_1"])
    m, stop, tgt = _kern(bb["b"], bb["e"], bb["tod"], bb["c"], bb["h"], bb["l"], bb["atr5"], U.f(df, "volumeRatio"),
                         bb["vwap"], bb["atr"], Dd["lo20_1"], Dd["swl_1"])
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
