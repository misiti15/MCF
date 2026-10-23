"""pod-of3-barros-ib-failed-lookbelow-opposite-extension-long - Barros failed auction: failed IB-low extension, then
buy the opposite-side IB-high range extension (LONG). Fill-at-signal configuration.

Source: Ray Barros failed-auction definition (failure at one end after the IB followed by range extension at the
opposite end; failure to hold the IB break > 30 min) via marketcalls.in 'Market Profile Failed Auction' and the
NexusFi failed-auction concept page.
URL: https://www.marketcalls.in/market-profile/market-profile-failed-auction.html

VARIANT of CWT14 ORL failed-break long (entry at the reclaim) and pod-axia-or-buying-tail-late-break-long (OR30 excess
tail). Stated changes: the level is the 60-min IB, the failure must happen AFTER 10:30 and be resolved within 30 min
(Barros time rule), and the entry is the later opposite-side range extension, not the reclaim.
Rules (plain English, LONG):
  1. IB = running HOD / LOD on the 10:30 bar (09:30-10:30); width 0.3-0.8 x atr_d.
  2. Look-below: a bar closing after 10:30 trades >= 0.05 x atr_d below the IB low, and within 6 bars (that bar
     included) a close returns above the IB low; no close below the IB low after that reclaim. If no reclaim comes
     within 6 bars, the day is dead (an accepted breakdown, not a failed auction).
  3. Signal = the first close above the IB high after 10:30 (no earlier close above it), after the reclaim, bar close
     10:45-14:30, volumeRatio >= 1.2, breadth >= 0.45.
  4. The failed look-below low is still the LOD (running LOD unchanged since the reclaim bar).
  Entry: signal close. Stop (GEOM S): IB midpoint. Target: IB high + 1.0 x IB width; flat 15:55.
The idea asks for two separately counted configurations: this one (fill at the signal close) and
pod-of3-barros-ib-failed-lookbelow-opposite-extension-long-hold1 (wait one bar; enter at the next bar's close only if
it still closes above the IB high). No tweak made. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1045, 1430)
CONTEXT = ["breadth"]
WAIT_BAR = False
LAYERS = ["IB width 0.3-0.8 ATR", "look-below >= 0.05 ATR after 10:30 reclaimed within 6 bars, held",
          "first close above IB high, volumeRatio >= 1.2, breadth >= 0.45", "look-below low still the LOD",
          "stop IB mid, target IB high + 1 IB width"]

import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r29_util as U  # noqa: E402

_ST = {}


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i])


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


@numba.njit(cache=False)
def _scan(st, tod, h, l, c, lod, ibh, ibl, atr):
    """Per row: 1 if this bar is the signal bar (first close above IB high after a held, failed look-below)."""
    n = len(c)
    sig = np.zeros(n, np.bool_)
    lb = -1          # index of the look-below start
    rec = -1         # index of the reclaim bar
    dead = False
    above = False    # a close above the IB high already happened
    for i in range(n):
        if st[i]:
            lb = -1
            rec = -1
            dead = False
            above = False
        if tod[i] <= 1030 or dead or above or not np.isfinite(ibl[i]) or not np.isfinite(atr[i]):
            continue
        if lb < 0:
            if l[i] <= ibl[i] - 0.05 * atr[i]:
                lb = i
            else:
                if c[i] > ibh[i]:
                    above = True         # extension up without a prior failed look-below
                continue
        if rec < 0:
            if c[i] > ibl[i]:
                rec = i
            elif i - lb >= 5:
                dead = True              # no reclaim within 6 bars: accepted breakdown
            continue
        if i > rec and c[i] < ibl[i]:
            dead = True
            continue
        if c[i] > ibh[i]:
            above = True
            if lod[i] >= lod[rec] - 1e-9 * c[i]:
                sig[i] = True
    return sig


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n or "breadth" not in df:
        return np.zeros(n, bool)
    b = U.base(df)
    k = U.key(df)
    c, atr, tod = b["c"], b["atr"], b["tod"]
    ibh = U.at_tod(b["hod"], k, tod, 1030)
    ibl = U.at_tod(b["lod"], k, tod, 1030)
    st = U.start(k)
    sig = _scan(st, tod, b["h"], b["l"], c, b["lod"], ibh, ibl, atr)
    w = ibh - ibl
    with np.errstate(invalid="ignore"):
        ok = sig & (w >= 0.3 * atr) & (w <= 0.8 * atr)
        ok &= (U.f(df, "volumeRatio") >= 1.2) & (U.f(df, "breadth") >= 0.45)
        if WAIT_BAR:
            m = (U.lag(ok.astype(float), k) == 1) & (c > ibh)
        else:
            m = ok
        stop[:] = (ibh + ibl) / 2
        tgt[:] = ibh + w
        m &= (stop < c) & (tgt > c)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
