"""pod-raschke-5sma-7bar-run-first-dip-long - 7-bar one-sided run over the 5-bar SMA on a trend-up day, buy the first
close below the SMA5 (trend-day pullback), target a retest of the run's HOD (LONG).

Source: Linda Raschke 5-SMA extension idea as coded in TradingView 'Linda Raschke 5 SMA Reversal [LuciTech]' (7+
closes on one side = one-sided market; the first close back across is the signal; in uptrends buy dips to the SMA);
Raschke rule 'buy the first pullback after a new high' (Steve Burns / Scribd rule list).
URL: https://it.tradingview.com/script/dyiN5wv3-Linda-Raschke-5-SMA-Reversal-LuciTech

NEW, not a copy: the trigger is a bar-count run measured against the SMA5, not a 20d-high break
(pod-raschke-first-pullback-after-20d-high-long) or a 9/20 EMA cross.

Rules (plain English). SMA5 = mean of the last 5 session 5m closes from 09:35 (_r24 cache via _r31_util.sess_ind).
  1. At the pullback bar p: the stock is up >= 0.5 x daily ATR from the open and closes above session VWAP.
  2. The >= 7 bars just before p all closed above their SMA5 (counted on frame bars from 09:55, the first bar with a
     valid SMA5 in the frame), and one of those run bars set a new high of day (its high = the running HOD).
  3. p is the first close below SMA5 after the run (by construction) and still closes above VWAP.
  4. Entry: the 'buy stop 1 tick above the pullback bar's high, valid for the next 2 bars' is scored at bar close:
     the first of bars p+1 / p+2 that closes above pullback high + $0.01 (stated bar-close proxy). Entry bar close
     10:00-14:30.
  5. Stop: pullback bar low - 0.05 x ATR. Target: retest of the run HOD (the running HOD at p; skip when the entry is
     already at / above it). Companions: -t1r (1R) and -t15r (1.5R) targets, as the idea asked. Flat 15:55.
No tweak made. 3 configurations (HOD / 1R / 1.5R targets). Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r36_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
TMODE = 0            # 0 = run HOD, 1 = 1R, 2 = 1.5R
RUN = 7
LAYERS = ["up >= 0.5 ATR from open, above VWAP", ">= 7 closes above SMA5 with a new HOD in the run",
          "first close below SMA5 still above VWAP", "close > pullback high + 1c within 2 bars, 10:00-14:30",
          "stop pullback low - 0.05 ATR, target run HOD (1R / 1.5R companions)"]
_ST = {}


@numba.njit(cache=False)
def _k(b, e, tod, c, h, l, s5, hod, vw, opn, atr, nrun, tmode, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for p in range(i0 + 1, i1 - 1):
            a = atr[p]
            if not (a > 0) or not (c[p] < s5[p]) or not (c[p] > vw[p]):
                continue
            if not (c[p] - opn[p] >= 0.5 * a):
                continue
            cnt = 0
            newhi = False
            j = p - 1
            while j >= i0 and c[j] > s5[j]:
                cnt += 1
                if h[j] >= hod[j] - 1e-9:
                    newhi = True
                j -= 1
            if cnt < nrun or not newhi:
                continue
            for q in range(p + 1, min(p + 3, i1)):
                if c[q] > h[p] + 0.01:
                    if tod[q] >= w0 and tod[q] <= w1:
                        sp = l[p] - 0.05 * a
                        R = c[q] - sp
                        if tmode == 0:
                            t = hod[p]
                        elif tmode == 1:
                            t = c[q] + R
                        else:
                            t = c[q] + 1.5 * R
                        if R > 0 and t > c[q] and not m[q]:
                            m[q] = True
                            stop[q] = sp
                            tgt[q] = t
                    break
    return m, stop, tgt


def compute(df, tmode):
    k = U.key(df)
    b = U.base(df)
    si = U.U31.sess_ind(df)
    bb, ee = U.segments(k)
    return _k(bb, ee, b["tod"], b["c"], b["h"], b["l"], si["s5"], b["hod"], b["vwap"], b["opn"], b["atr"], RUN,
              tmode, WINDOW[0], WINDOW[1])


def mask(df):
    m, s, t = compute(df, TMODE)
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
