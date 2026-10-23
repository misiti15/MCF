"""pod-shannon-gapdown-dual-vwap-reclaim-pullback-am-long - A gap-down stock reclaims both the session VWAP and the
prior-close AVWAP in the morning; buy the first pullback that holds both (LONG).

Source: Alpha Trends - Brian Shannon on NinjaTrader (05-18-25): anchor VWAP to the week's open, the prior session
close and the 09:30 open; on gap-downs the reclaim of those VWAPs is the long trigger, then 'once price is above,
look for pullbacks - never buy the dip blindly, wait for a signal'.
URL: https://alphatrends.net/archives/podcast/brian-on-ninjatrader-05-18-25/

VARIANT of pod-shannon-gapdown-stage1-first-vwap-cross-pm-long. What changes: the morning window, the requirement to
reclaim TWO anchors (session VWAP and the prior-close AVWAP), and entry on the first held pullback rather than the
first cross.

Rules (plain English). V = max(session VWAP, AVWAP anchored at the prior day's last RTH bar 15:55-16:00); the AVWAP
is (session VWAP x today's cumulative volume + that bar's typical x volume) / (cumulative volume + its volume), from
the 1-minute vendor bars (_r36_util.pc_avwap).
  1. Gap between -8% and -1.5%. adv20 >= $30M.
  2. Reclaim: a 5m bar closing 09:50-11:30 closes above V (the frame starts at the 09:50 bar; the source window opens
     09:45).
  3. Pullback: within the next 1-6 bars after a reclaim bar, a bar whose low comes within 0.1 x ATR of V (low <= V +
     0.1 ATR) but closes >= V; every close from the reclaim to the pullback is >= V.
  4. Entry: the next bar that closes above the pullback bar's high, by 12:00 (bar close), with no close below V in
     between.
  5. Stop: pullback low - 0.05 x ATR. Target: the prior close (gap fill), capped at entry + 2R (skip when the prior
     close is not above the entry). Time stop 13:30 (GEOM S+x, EXIT_TOD 1330). One trade per symbol per day
     (scorer). Flat 15:55.
No tweak made. 1 configuration. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r36_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
EXIT_TOD = 1330
WINDOW = (955, 1200)
MIN_ADV = 30e6
LAYERS = ["gap -8%..-1.5%, adv >= 30M", "09:50-11:30 close above session VWAP and prior-close AVWAP",
          "pullback within 6 bars: low within 0.1 ATR of V, close >= V",
          "close above pullback high by 12:00", "stop pullback low - 0.05 ATR, target prior close capped 2R, exit 13:30"]
_ST = {}


@numba.njit(cache=False)
def _k(b, e, tod, c, h, l, V, gap, atr, pc):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        g = gap[i0]
        if not (g <= -1.5 and g >= -8.0):
            continue
        found = False
        for r in range(i0, i1):
            if found or tod[r] > 1130:
                break
            a = atr[r]
            if not (a > 0) or not (c[r] > V[r]):
                continue
            for p in range(r + 1, min(r + 7, i1)):
                if not (c[p] >= V[p]):
                    break
                if not (l[p] <= V[p] + 0.1 * a):
                    continue
                # pullback bar p: find the entry
                for j in range(p + 1, i1):
                    if tod[j] > 1200 or not (c[j] >= V[j]):
                        break
                    if c[j] > h[p]:
                        sp = l[p] - 0.05 * a
                        R = c[j] - sp
                        if R > 0 and pc[j] > c[j]:
                            m[j] = True
                            stop[j] = sp
                            tgt[j] = min(pc[j], c[j] + 2.0 * R)
                            found = True
                        break
                break        # the first pullback after this reclaim decides it
    return m, stop, tgt


def compute(df):
    k = U.key(df)
    b = U.base(df)
    av = U.pc_avwap(df)
    with np.errstate(invalid="ignore"):
        V = np.maximum(b["vwap"], av)
    V[~np.isfinite(av)] = np.nan
    bb, ee = U.segments(k)
    return _k(bb, ee, b["tod"], b["c"], b["h"], b["l"], V, U.f(df, "gap"), b["atr"], b["pc"])


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
