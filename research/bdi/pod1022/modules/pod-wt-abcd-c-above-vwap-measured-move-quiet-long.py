"""pod-wt-abcd-c-above-vwap-measured-move-quiet-long - ABCD with C held above VWAP on a quiet tape; exit at the
AB=CD measured move instead of HOD (LONG).

Source: Warrior Trading ABCD pattern (Ross Cameron; listed in the Warrior Trading-methodology replication) and Bear
Bull Traders ABCD (Andrew Aziz, How to Day Trade for a Living).
URL: https://vn.tradingview.com/script/RuvGSExs-Warrior-Trading-Momentum-Strategy

VARIANT of bdi-reddit-abcd (buy the break of B) and pod-wt-abcd-buy-at-c-long (buy at C). Stated changes: C must hold
above VWAP, a quiet-index regime gate, the measured-move target D = C + (B - A) and (in the source) a time stop.

Rules (plain English), 5-minute bars, values from bars up to and including the decision bar i:
  1. A = the lowest low since 09:50 (frame bars); B = the highest high after A, with B - A >= 1 x ATR14_5m (at B).
     A new low re-anchors A (B and C reset); a new high above B re-anchors B (C resets).
  2. C = the lowest low after B (>= 1 bar after B), retracing 38.2-61.8% of AB, with C > session VWAP (at the C bar)
     and the total volume of bars B+1..C <= 0.7 x the total volume of bars A..B.
  3. Trigger: bar i closes above B (the classic ABCD entry), with i - C <= 12 bars.
  4. Room: D - entry >= 1.5 x (entry - C), with D = C + (B - A).
  5. SPY's 5-minute ATR14 at this bar is at or below the 40th percentile of the same time slot over the 20 prior
     sessions (quiet).
  Entry: bar i's close. Window: bar close 10:00-14:00.
  Stop (GEOM S): C - 0.05 x ATR14_5m. Target: D, else flat 15:55. Modelling note: the 60-minute time stop is not
  modelled (one stop / target per trade in the scorer). No tweak used.
Costs per config/default.yaml (applied by the scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r32_util as Z  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1400)
CONTEXT = []
LAYERS = ["A = low since 09:50, B - A >= 1 ATR5m", "C retrace 38.2-61.8%, C > VWAP, BC vol <= 0.7 x AB vol",
          "close > B within 12 bars of C", "D - entry >= 1.5 x (entry - C)", "SPY ATR5m pct <= 40 at time of day",
          "stop C - 0.05 ATR5m, target D", "10:00-14:00"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, vw, a5, v, sp, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        ja = -1
        jb = -1
        jc = -1
        for i in range(i0, i1):
            if ja >= 0 and jb > ja and jc > jb and tod[i] >= w0 and tod[i] <= w1 and c[i] > h[jb] and i - jc <= 12:
                A = l[ja]
                Bv = h[jb]
                C = l[jc]
                ab = Bv - A
                ok = a5[jb] > 0 and ab >= a5[jb]
                if ok:
                    rt = (Bv - C) / ab
                    ok = rt >= 0.382 and rt <= 0.618 and C > vw[jc]
                if ok:
                    v1 = 0.0
                    for t in range(ja, jb + 1):
                        v1 += v[t]
                    v2 = 0.0
                    for t in range(jb + 1, jc + 1):
                        v2 += v[t]
                    ok = v1 > 0 and v2 <= 0.7 * v1
                if ok:
                    D = C + ab
                    ok = D - c[i] >= 1.5 * (c[i] - C) and sp[i] <= 40.0
                    if ok and a5[i] > 0:
                        m[i] = True
                        stop[i] = C - 0.05 * a5[i]
                        tgt[i] = D
            if ja < 0 or l[i] < l[ja]:
                ja = i
                jb = -1
                jc = -1
                continue
            if jb < 0 or h[i] > h[jb]:
                jb = i
                jc = -1
                continue
            if jc < 0 or l[i] < l[jc]:
                jc = i
    return m, stop, tgt


def mask(df) -> np.ndarray:
    n = len(df)
    _ST.clear()
    if not n:
        return np.zeros(0, bool)
    B = Z.base(df)
    bb = Z.bars(df)
    b, e = Z.segments(Z.key(df))
    c = B["c"]
    with np.errstate(invalid="ignore"):
        a5 = Z.f(df, "atrPct") / 100 * c
    sp = Z.map_spy_pct(df)
    m, stop, tgt = _kern(b, e, B["tod"], c, B["h"], B["l"], B["vwap"], a5, bb["v"], sp, WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _g(f, i, j):
    if id(f) not in _ST:
        mask(f)
    return float(_ST[id(f)][j][i])


def stop_price(f, i):
    return _g(f, i, 0)


def target_price(f, i, stop):
    return _g(f, i, 1)
