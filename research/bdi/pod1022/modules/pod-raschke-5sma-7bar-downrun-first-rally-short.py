"""pod-raschke-5sma-7bar-downrun-first-rally-short - Trend-down day: 7-bar run under the 5-bar SMA, short the first
close back above it that fails (SHORT).

Source: Linda Raschke rule list ('sell the first rally after a new low') and the 5-SMA one-sided-run rule (TradingView
'Linda Raschke 5 SMA Reversal [LuciTech]').
URL: https://www.scribd.com/document/942776286/Trading-Rules-Linda-Raschke

VARIANT of pod-raschke-5sma-7bar-run-first-dip-long (side change, plus a trend-down gate that excludes quiet days).

Rules (plain English). SMA5 = mean of the last 5 session 5m closes from 09:35 (_r24 cache via _r31_util.sess_ind).
  1. At the rally bar p: the stock is down >= 0.5 x daily ATR from the open, closes below session VWAP, and SPY is
     below its open (spy_fo < 0).
  2. The >= 7 bars just before p all closed below their SMA5 (frame bars from 09:55, the first with a valid SMA5 in
     the frame), and one of those run bars set a new low of day (its low = the running LOD).
  3. p is the first close above SMA5 after the run (by construction) and still closes below VWAP.
  4. Entry: the 'sell stop 1 tick under the rally bar's low, valid 2 bars' is scored at bar close (as the long
     parent): the first of bars p+1 / p+2 that closes below rally low - $0.01 (stated bar-close proxy). Entry bar
     close 10:00-14:30.
  5. Stop (GEOM S): rally-bar high + 0.05 x ATR. Target: 'LOD retest or 1R' read as the nearer of the two (the LOD
     at p, when it is below the entry, else 1R) - pre-declared reading. Flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml incl. the short side (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r36_util as U  # noqa: E402

SIDE = "short"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = ["spy_fo"]
RUN = 7
LAYERS = ["down >= 0.5 ATR from open, below VWAP, spy_fo < 0", ">= 7 closes below SMA5 with a new LOD in the run",
          "first close above SMA5 still below VWAP", "close < rally low - 1c within 2 bars, 10:00-14:30",
          "stop rally high + 0.05 ATR, target nearer of LOD and 1R, flat 15:55"]
_ST = {}


@numba.njit(cache=False)
def _k(b, e, tod, c, h, l, s5, lod, vw, opn, spy, atr, nrun, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for p in range(i0 + 1, i1 - 1):
            a = atr[p]
            if not (a > 0) or not (c[p] > s5[p]) or not (c[p] < vw[p]):
                continue
            if not (opn[p] - c[p] >= 0.5 * a) or not (spy[p] < 0):
                continue
            cnt = 0
            newlo = False
            j = p - 1
            while j >= i0 and c[j] < s5[j]:
                cnt += 1
                if l[j] <= lod[j] + 1e-9:
                    newlo = True
                j -= 1
            if cnt < nrun or not newlo:
                continue
            for q in range(p + 1, min(p + 3, i1)):
                if c[q] < l[p] - 0.01:
                    if tod[q] >= w0 and tod[q] <= w1:
                        sp = h[p] + 0.05 * a
                        R = sp - c[q]
                        t = c[q] - R
                        if lod[p] < c[q]:
                            t = max(t, lod[p])
                        if R > 0 and t < c[q] and not m[q]:
                            m[q] = True
                            stop[q] = sp
                            tgt[q] = t
                    break
    return m, stop, tgt


def compute(df):
    n = len(df)
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    k = U.key(df)
    b = U.base(df)
    si = U.U31.sess_ind(df)
    bb, ee = U.segments(k)
    return _k(bb, ee, b["tod"], b["c"], b["h"], b["l"], si["s5"], b["lod"], b["vwap"], b["opn"], U.f(df, "spy_fo"),
              b["atr"], RUN, WINDOW[0], WINDOW[1])


def mask(df):
    m, s, t = compute(df)
    _ST.clear()
    _ST[id(df)] = (s, t)
    return m


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
