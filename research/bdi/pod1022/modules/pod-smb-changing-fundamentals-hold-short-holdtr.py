"""pod-smb-changing-fundamentals-hold-short-holdtr - Changing Fundamentals / Trade2Hold: hold an all-morning trend in a
non-earnings news gapper (SHORT side; holdtr exit).

Source: SMB Training blog 'The Best Setup for New Traders: A Changing Fundamentals Trade ($M)' + PlayBook 'Trade2Hold'.
URL: https://www.smbtraining.com/blog/the-best-setup-for-new-traders-2

VARIANT of CWT07 catalyst gap-and-go (failed) and gap_continuation (stop-entry at the opening range, 2R). Stated
change: no breakout trigger and no R target; a fixed-time trend-quality check at 10:45 and a hold to the close with a
structural stop. The scorer's earnings blackout (4 trading days either side) leaves non-earnings catalysts only.

Pre-declared choice (no tuning): the frame has no true day-relative rvol (the arena 'rvol_day' is a mean-volumeRatio
proxy on a different scale), so the source's listed alternative is used: volumeSurge >= 1.3, taken as the MAX over
the 09:50-10:45 bars (the opening surge of an in-play name; at 10:45 alone volume normally decays on a gapper).

Rules (plain English), decision bar = the 10:45 bar close only:
  1. gap <= -3% and fromOpen <= 0.
  2. Volume: max volumeSurge over 09:50-10:45 >= 1.3.
  3. >= 85% of the 5-minute closes since 09:50 are below the session VWAP; pricePosition <= 0.3.
  4. The highest high since 10:00 (bars closing 10:05-10:45) is below today's open (open = close / (1 + fromOpen%)).
  Entry: the 10:45 close. Stop (GEOM S): max(high since 10:00, VWAP + 0.25 x daily ATR) + 1c. No target: exit at
  15:55. (Companion file -holdtr: the same entry with the scorer's holdtr geometry, as the idea pre-declares.)
  LONG mirror in pod-smb-changing-fundamentals-hold-long (gap >= +3%). Costs in (scorer).
THIS FILE: GEOM holdtr (R = 0.25 x daily ATR) instead of the structural stop.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "holdtr"   # the idea's pre-declared second exit: stop 1R (0.25 ATR), 1R trail once +1R
WINDOW = (1045, 1045)
LAYERS = ["gap <= -3%, fromOpen <= 0", "max volumeSurge 09:50-10:45 >= 1.3",
          ">= 85% of closes since 09:50 below VWAP, pricePosition <= 0.3", "high since 10:00 below the open",
          "stop max(high since 10:00, VWAP + 0.25 ATR), hold to 15:55", "10:45 bar only"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, vd, fo, gap, pp, vs, atr, d):
    # d = +1 long, -1 short
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0, i1):
            if tod[i] != 1045:
                continue
            a = atr[i]
            if not (a > 0):
                break
            if d < 0:
                if not (gap[i] <= -3.0 and fo[i] <= 0 and pp[i] <= 0.3):
                    break
            else:
                if not (gap[i] >= 3.0 and fo[i] >= 0 and pp[i] >= 0.7):
                    break
            cnt = 0
            good = 0
            mvs = -1e18
            ext = -1e18 if d < 0 else 1e18
            for k in range(i0, i + 1):
                if tod[k] < 950:
                    continue
                cnt += 1
                if (d < 0 and vd[k] < 0) or (d > 0 and vd[k] > 0):
                    good += 1
                if vs[k] > mvs:
                    mvs = vs[k]
                if tod[k] >= 1005:
                    if d < 0:
                        ext = max(ext, h[k])
                    else:
                        ext = min(ext, l[k])
            if cnt < 6 or good < 0.85 * cnt or not (mvs >= 1.3):
                break
            op = c[i] / (1.0 + fo[i] / 100.0)
            vw = c[i] / (1.0 + vd[i] / 100.0)
            if d < 0:
                if not (ext < op):
                    break
                sp = max(ext, vw + 0.25 * a) + 0.01
                if not (sp > c[i]):
                    break
            else:
                if not (ext > op):
                    break
                sp = min(ext, vw - 0.25 * a) - 0.01
                if not (sp < c[i]):
                    break
            m[i] = True
            stop[i] = sp
            break
    return m, stop


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("high"), f("low"), f("vwapDistPct"),
                   f("fromOpen"), f("gap"), f("pricePosition"), f("volumeSurge"), f("atr_d"),
                   1 if SIDE == "long" else -1)


def mask(df) -> np.ndarray:
    m, stop = compute(df)
    _STASH.clear()
    _STASH[id(df)] = stop
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[i])
