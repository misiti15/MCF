"""pod-bbt-hod-break-rising-volume-1bar-trail-long - High-of-Day break with rising volume into the break, exit on the
first new 1-bar low (LONG). Config TRAIL (the control config is the -ctrl2r file).

Source: Bear Bull Traders - John Hiltz, 'Strategy 4: High of Day Breakout' (webinar Apr 2023) + Mike Baehr
'Leveraging Scanners for High of Day Break' (Sep 2024).
URL: https://bearbulltraders.com/wp-content/uploads/2023/05/High-of-Day-Break-Strategy-Webinar-Apr23-1.pdf

VARIANT of Reddit R07 'HOD break after consolidation' (failed) and pod-smb-second-chance-hod-retest. Stated changes:
a rising-volume-into-the-break condition (Baehr: 'key confirmation is rising volume into break'), and new EXIT LOGIC
from Hiltz / Baehr: get to break-even fast and exit on the first new low ('exiting on a new 1-minute low is the key
risk step', applied on 5-min bars - the frame has no 1-minute bars).

Rules (plain English), decision bar i (only bars up to i):
  1. In play: |gap| >= 1% or mean volumeRatio of today's frame bars up to i >= 1.5; close_i > session VWAP.
  2. Coil under the high: bars i-4..i-1 made no new HOD (running HOD at i-1 equals the one at i-5) and all their lows
     are >= HOD - 0.30 x daily ATR.
  3. Rising volume: volumeRatio_{i-2} < volumeRatio_{i-1} < volumeRatio_i and volumeRatio_i >= 1.5.
  4. Trigger: close_i > the running HOD as of bar i-1.
  Entry: close_i, bar close 10:00-12:00. Initial stop: min low of bars i-4..i - 0.02 x daily ATR.
  Exit TRAIL (GEOM 'S+bar1', added to score_batch.py for this idea): at the close of the first bar after entry whose
  low < the previous bar's low; the stop moves to break-even once the trade has been +0.5R (BE_AT_R = 0.5); no
  target; flat 15:55. Control config (-ctrl2r file): the same trigger with GEOM S and an entry + 2R target.
  Costs in (scorer). 2 configs (trail, control), no tweak.
Educational only - not financial advice."""
import numba
import numpy as np

from _bbtr22_util import base

SIDE = "long"
GEOM = "S+bar1"
BE_AT_R = 0.5
CONFIG = "TRAIL"
WINDOW = (1000, 1200)
CONTEXT = []
LAYERS = ["|gap| >= 1% or mean volumeRatio >= 1.5, above VWAP", "4-bar coil under HOD within 0.30 ATR",
          "rising volumeRatio x3, last >= 1.5", "close > prior HOD", "stop min low(i-4..i) - 0.02 ATR",
          "exit first lower low bar, BE at +0.5R (TRAIL) / 2R target (CTRL)", "10:00-12:00 ET"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, hod, vw, gap, vr, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        vsum = 0.0
        vn = 0
        for i in range(i0, i1):
            if vr[i] == vr[i]:
                vsum += vr[i]
                vn += 1
            if tod[i] < w0 or tod[i] > w1 or i - 5 < i0:
                continue
            a = atr[i]
            if not (a > 0):
                continue
            inplay = abs(gap[i]) >= 1.0 or (vn > 0 and vsum / vn >= 1.5)
            if not (inplay and c[i] > vw[i]):
                continue
            H = hod[i - 1]
            if hod[i - 1] > hod[i - 5] + 1e-5 * c[i]:
                continue
            ok = True
            for k in range(i - 4, i):
                if l[k] < H - 0.30 * a:
                    ok = False
                    break
            if not ok:
                continue
            if not (vr[i - 2] < vr[i - 1] and vr[i - 1] < vr[i] and vr[i] >= 1.5):
                continue
            if not (c[i] > H):
                continue
            ll = l[i]
            for k in range(i - 4, i):
                ll = min(ll, l[k])
            sp = ll - 0.02 * a
            if sp < c[i]:
                m[i] = True
                stop[i] = sp
    return m, stop


def mask(df) -> np.ndarray:
    _ST.clear()
    if len(df) == 0:
        return np.zeros(0, bool)
    d = base(df)
    m, sp = _kern(d["b"], d["e"], d["tod"], d["c"], d["h"], d["l"], d["hod"], d["vw"], d["gap"], d["vr"], d["atr"],
                  WINDOW[0], WINDOW[1])
    tp = d["c"] + 2.0 * (d["c"] - sp)
    _ST[id(df)] = (sp, tp)
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


if CONFIG == "CTRL":
    def target_price(f, i, stop):
        return float(_get(f)[1][i])
