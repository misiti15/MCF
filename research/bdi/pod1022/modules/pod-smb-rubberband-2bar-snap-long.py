"""pod-smb-rubberband-2bar-snap-long - SMB RubberBand scalp: accelerating morning flush, long on the 2-bar-high snap
(LONG).

Source: SMB Capital YouTube / SMB Training 'Scalp Radar' series: the RubberBand scalp (Bellafiore / SMB desk). Taken
from SMB material already known; web was unavailable this round, so the source was not re-checked.
URL: https://www.youtube.com/@smbcapital

VARIANT of cwt-b-b5-panic-flush-v-long (CWT05 panic flush V-reversal, failed 0/64). What changes: the flush has to
ACCELERATE, and the trigger is SMB's 2-bar-high 'snap' rather than a V on a volume climax; half-retrace target.
Also distinct from pod-cwt-breitstein-stock-multiday-flush (config R, which merged the 2-day RubberBand): no multi-day
daily gate here, and the acceleration (expanding ranges, weak closes) is required instead of a Bollinger close.

Rules (plain English, 5-minute bars, adv20 >= $95M), snap bar i:
  1. The stock is down >= 1.0 daily ATR from the open at bar i ((open - close_i) >= 1.0 x atr_d).
  2. Acceleration: bars i-3, i-2, i-1 each have a larger range (high - low) than the bar before, and each closes in
     the lower 30% of its range.
  3. Snap: bar i closes above max(high[i-1], high[i-2]) with volumeRatio >= 1.5 (volume / its 20-bar average).
  4. SPY did not print a new session low on bar i (proxy: spy_fo at i is not below every earlier spy_fo of the day
     from 09:50; the frame has SPY closes only, not SPY lows or 09:30-09:45 bars).
  Entry: the snap bar's close (the frame has no bar open; the source says next bar open), bar close 09:50-11:30.
  Stop (GEOM S): session LOD - 0.05 x atr_d. Target: the nearer (above entry) of the 50% retrace of the open-to-LOD
  move and session VWAP; if neither is above the entry there is no trade. One entry per symbol-day (scorer).
Deviation: the source's 45-minute time stop cannot be modelled by this scorer; trades not stopped or filled hold to
15:55. No tweak made. Costs in (scorer). Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1130)
MIN_ADV = 95e6
CONTEXT = ["spy_fo"]
LAYERS = ["down >= 1 ATR from open", "3 bars of expanding range closing in lower 30%",
          "close > 2-bar high, volumeRatio >= 1.5", "SPY not at a new session low (close proxy)",
          "stop LOD - 0.05 ATR, target nearer of 50% retrace / VWAP", "09:50-11:30, adv20 >= $95M"]

_ST = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, opn, lod, vw, vr, spy, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        smin = 1e18
        for i in range(i0, i1):
            newlow = spy[i] < smin
            if spy[i] < smin:
                smin = spy[i]
            if i == i0:
                newlow = False          # first frame bar: no earlier SPY close in the frame to compare with
            if tod[i] < w0 or tod[i] > w1 or i - i0 < 4:
                continue
            a = atr[i]
            if not (a > 0 and opn[i] - c[i] >= 1.0 * a and vr[i] >= 1.5 and not newlow):
                continue
            if not (c[i] > max(h[i - 1], h[i - 2])):
                continue
            ok = True
            for t in range(i - 3, i):
                r = h[t] - l[t]
                if not (r > h[t - 1] - l[t - 1] and r > 0 and (c[t] - l[t]) <= 0.3 * r):
                    ok = False
            if not ok:
                continue
            sp = lod[i] - 0.05 * a
            half = lod[i] + 0.5 * (opn[i] - lod[i])
            tp = 1e18
            if half > c[i]:
                tp = half
            if vw[i] > c[i] and vw[i] < tp:
                tp = vw[i]
            if tp < 1e17 and sp < c[i]:
                m[i] = True
                stop[i] = sp
                tgt[i] = tp
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
    opn = c / (1 + f("fromOpen") / 100)
    lod = c - f("dist_lod_atr") * atr
    b, e = _segments(df)
    m, stop, tgt = _kern(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), opn, lod, vw,
                         f("volumeRatio"), f("spy_fo"), atr, WINDOW[0], WINDOW[1])
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
