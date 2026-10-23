"""pod-smb-ipr-inplay-or-ratio-first-pullback-long - SMB Radar 'IPR' in-play stock (opening-range ratio >= 3): first
pullback above VWAP, long (LONG).

Source: SMB Capital / SMB Training blog - SMB Radar Opening Range filter (IPR) posts + 'Buying Pullbacks on the Open'
lesson (Bellafiore).
URL: https://www.smbtraining.com/blog/smb-radar-update-2

VARIANT of the backlog 'ORB on stocks in play' and CWT07 money trade. What changes: the in-play gate is SMB's Radar
IPR (opening-range ratio), not a gap or catalyst, and entry is on the first pullback, not the breakout.

Data: the 09:30-09:45 opening range (high / low) per symbol-day and the 09:35-09:45 5m closes / volumes come from the
1-minute vendor bars (helper _r24_bars cache; the locked block is never read). IPR = OR width / mean OR width of the
20 prior sessions (min 10). The 09:45 VWAP is a close-weighted VWAP of the 09:35-09:45 bars (the cache holds closes and
volumes, not highs / lows, for those bars); from 09:50 on, VWAP is the frame's session VWAP.

Rules (plain English):
  1. At 09:45: IPR >= 3.0, the 09:45 close > the 09:45 VWAP, and the 09:45 close is in the upper half of the
     09:30-09:45 range.
  2. Between 09:50 and 10:45 a pullback from the high of day retraces 30-60% of the OR width; no 5m close below VWAP
     from 09:50 through entry, and the pullback low stays above the OR midpoint. The pullback low bar closes by 10:45.
  3. Entry: the first 5m close above the prior bar's high after the pullback low (the entry bar does not undercut the
     pullback low), by 11:00. First pullback only: the first pullback that reaches 30% is the only one traded; if it
     goes deeper than 60% or under the OR midpoint, or a new high comes without an entry, the day is done.
  Stop: the lower of the pullback low and VWAP, minus 0.05 daily ATR. Target: OR high + 1x OR width or entry + 2R,
  whichever is nearer (only levels above the entry count). Time stop: flat at the 11:30 bar close if neither is hit
  (EXIT_TOD, GEOM S+x); hard flat 15:55. One trade per symbol per day (scorer: first signal).
Tweak: none. The 11:00 entry cut-off is a pre-declared reading of 'pullback between 09:50 and 10:45, then the first
close above the prior high'. 1 configuration. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import numba
import numpy as np

import _r33_util as U

SIDE = "long"
GEOM = "S+x"
EXIT_TOD = 1130
WINDOW = (955, 1100)
LAYERS = ["IPR >= 3 at 09:45", "09:45 close > VWAP and in the upper half of the OR",
          "pullback 30-60% of OR by 10:45, low above OR mid, all closes >= VWAP",
          "close above prior bar high", "stop min(pb low, VWAP) - 0.05 ATR, target min(ORH + ORW, 2R), flat 11:30"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, hod, vw, atr, ok, orh, orl):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not ok[i0]:
            continue
        w = orh[i0] - orl[i0]
        mid = 0.5 * (orh[i0] + orl[i0])
        if not (w > 0):
            continue
        H = hod[i0]
        lo = np.inf
        lotod = 0
        if h[i0] >= H - 1e-9:
            H = h[i0]
        else:
            lo = l[i0]
            lotod = tod[i0]
        if c[i0] < vw[i0]:
            continue
        for i in range(i0 + 1, i1):
            if c[i] < vw[i]:
                break                                      # a 5m close below VWAP kills the setup for the day
            if tod[i] > 1100:
                break
            if lo < np.inf and lotod <= 1045 and c[i] > h[i - 1] and l[i] >= lo:
                d = (H - lo) / w
                if d >= 0.3 and d <= 0.6 and lo > mid:
                    a = atr[i]
                    sp = min(lo, vw[i]) - 0.05 * a
                    R = c[i] - sp
                    t1 = orh[i0] + w
                    t2 = c[i] + 2.0 * R
                    tp = t2
                    if t1 > c[i] and t1 < t2:
                        tp = t1
                    if R > 0:
                        m[i] = True
                        stop[i] = sp
                        tgt[i] = tp
                        break
            # update pullback state with bar i
            if h[i] > H:
                if lo < np.inf and (H - lo) >= 0.3 * w:
                    break                                  # the first 30%+ pullback ended without an entry
                H = h[i]
                lo = np.inf
                lotod = 0
            elif l[i] < lo:
                lo = l[i]
                lotod = tod[i]
                if (H - lo) > 0.6 * w or lo <= mid:
                    break                                  # first pullback too deep / under the OR midpoint
    return m, stop, tgt


def mask(df):
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    if not n:
        return z
    T = U.c945_tab(df)
    if T is None:
        return z
    bb = U.base(df)
    I = U.map_day(df, U.ipr_tab(), ["ipr", "or_h", "or_l"])
    C = U.map_day(df, T, ["c945", "vw945"])
    with np.errstate(invalid="ignore"):
        ok = (I["ipr"] >= 3.0) & (C["c945"] > C["vw945"]) & (C["c945"] >= 0.5 * (I["or_h"] + I["or_l"]))
    m, stop, tgt = _kern(bb["b"], bb["e"], bb["tod"], bb["c"], bb["h"], bb["l"], bb["hod"], bb["vwap"], bb["atr"],
                         np.asarray(ok, np.bool_), I["or_h"], I["or_l"])
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
