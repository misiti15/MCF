"""pod-wt-late-r2g-pdc-coil-break-long - Late red-to-green: a gap-down stock coils for an hour just under the prior
close, then breaks through it midday (LONG).

Source: Warrior Trading red-to-green move (Ross Cameron; the prior close is the trigger level) and the community R2G
tracker rules (cross above PDC, stop under the cross bar / PDC, first target PDH).
URL: https://kr.tradingview.com/script/wSvTh08f-Red-to-Green-Green-to-Red-Tracker

VARIANT of wi-red-to-green and 'Reddit R06-red-green' (any cross of the prior close) and CWT12 coil-under-resistance
(session resistance). Stated changes: the level is the prior close on a gap-down day, a >= 1-hour coil under it, a
midday window, the stop under the coil and the PDH target.

Rules (plain English), 5-minute bars, values from bars up to and including the decision bar i:
  1. gap <= -1.5% (opened red).
  2. Coil: the 12 bars i-12..i-1 all have high <= PDC + 0.05 x ATR14_daily and low >= PDC - 0.35 x ATR14_daily, and
     the coil range (highest high - lowest low) <= 0.4 x ATR14_daily.
  3. Bar i closes above PDC with volume >= 1.5 x its 20-bar mean (frame volumeRatio).
  4. Close > session VWAP.
  5. SPY |fromOpen| < 0.5% (quiet / choppy tape; context spy_fo).
  Entry: the next bar's open, filled at bar i's close by the scorer. Window: signal bar close 11:00-14:30.
  Stop (GEOM S): the coil low. Target: PDH (when PDH is not above entry the trade holds to 15:55).
  Modelling note: the source's first half at entry + 1R is not modelled (one exit per trade); the full position
  targets PDH. No tweak used. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r32_util as Z  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
COIL = 12
CONTEXT = ["spy_fo"]
LAYERS = ["gap <= -1.5", "12-bar coil within PDC - 0.35 ATR .. PDC + 0.05 ATR, range <= 0.4 ATR",
          "close > PDC with volumeRatio >= 1.5", "close > VWAP", "|spy_fo| < 0.5", "stop coil low, target PDH",
          "11:00-14:30"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, pdc, atr, nb, w0, w1):
    n = len(c)
    ok = np.zeros(n, np.bool_)
    cl = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + nb, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            p = pdc[i]
            if not (a > 0 and p == p):
                continue
            hh = -1e18
            lo = 1e18
            good = True
            for t in range(i - nb, i):
                if not (h[t] <= p + 0.05 * a and l[t] >= p - 0.35 * a):
                    good = False
                    break
                hh = max(hh, h[t])
                lo = min(lo, l[t])
            if good and hh - lo <= 0.4 * a:
                ok[i] = True
                cl[i] = lo
    return ok, cl


def mask(df) -> np.ndarray:
    n = len(df)
    _ST.clear()
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool)
    B = Z.base(df)
    b, e = Z.segments(Z.key(df))
    ok, cl = _kern(b, e, B["tod"], B["c"], B["h"], B["l"], B["pc"], B["atr"], COIL, WINDOW[0], WINDOW[1])
    c = B["c"]
    with np.errstate(invalid="ignore"):
        m = ok & (Z.f(df, "gap") <= -1.5)
        m &= c > B["pc"]
        m &= Z.f(df, "volumeRatio") >= 1.5
        m &= c > B["vwap"]
        m &= np.abs(Z.f(df, "spy_fo")) < 0.5
    tgt = np.where(B["pdh"] > c, B["pdh"], c * 10.0)       # PDH not above entry -> no reachable target (15:55)
    _ST[id(df)] = (cl, tgt)
    return np.asarray(m, bool)


def _g(f, i, j):
    if id(f) not in _ST:
        mask(f)
    return float(_ST[id(f)][j][i])


def stop_price(f, i):
    return _g(f, i, 0)


def target_price(f, i, stop):
    return _g(f, i, 1)
