"""pod-smb-day3-extended-belowvwap-coil-pm-reclaim-long - Day 3 of an extended stock: midday coil below VWAP,
afternoon reclaim (LONG).

Source: SMB Capital junior trader deck 'Day 3 in Extended Stock: Consolidation below VWAP' (SUNE 12/17/15, SlideShare).
URL: https://www.slideshare.net/slideshow/how-to-use-vwap-as-an-important-technical-indicator/61960798

New setup. The deck shows a coil below VWAP on day 3 of a run; this tests the long resolution in the afternoon.

Data: daily bars of COMPLETED days (lib.daily()). "Day 1" of the run = D-2, "day 2" = D-1, today = day 3. Daily rvol =
volume / mean of the 20 sessions before. The day's low before 10:30 includes the 09:30-09:45 bars (1-minute vendor
bars, helper _smbv5_bars; the locked block is never read). VWAP = close / (1 + vwapDistPct%), ATR14(5m) = atrPct x
close, "volume >= 1.3x its 20-bar average" = volumeRatio >= 1.3 (frame).

Rules (plain English), decision bar i (bar close 13:00-15:00 ET):
  Context: D-2 and D-1 both closed up, combined return >= +8%, and D-2 (day 1) daily rvol >= 2.
  1. The 5m bars closing 10:35-13:00 closed below VWAP on >= 70% of them.
  2. Coil: the 8 bars before i span <= 0.6 x ATR14(5m) x sqrt(8) (high - low), and the coil low stays above the
     day's low made before 10:30.
  3. Bar i closes above VWAP and above the coil high, with volumeRatio >= 1.3.
  Entry: next bar open (scorer: close_i). Stop (GEOM S): coil low - 0.1 x ATR14(5m). Target: the higher of entry + 1.5R
  and the day-3 opening price; time exit 15:55. Costs in (scorer). The source's control (same signal on names without
  a multi-day run) is stood in for by the scorer's same-minute random control. 1 config, no tweak.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1300, 1500)
LAYERS = ["D-2 and D-1 up, combined >= +8%, D-2 rvol >= 2", "below VWAP on >= 70% of 10:35-13:00 bars",
          "8-bar coil <= 0.6 ATR5 x sqrt(8), coil low above the pre-10:30 LOD",
          "close above VWAP and coil high, volumeRatio >= 1.3", "stop coil low - 0.1 ATR5, target max(1.5R, open)",
          "13:00-15:00 ET"]
import numba
import numpy as np
import pandas as pd

import _smbv5_bars as V

_STASH = {}
_C = {}


def _ctx():
    """Per (symbol, date D): day-3 context from completed days, and the low of day before 10:30 (incl. 09:30-09:45)."""
    if "c" in _C:
        return _C["c"]
    dc = V.daily_ctx()
    run = (dc["ret1"] > 0) & (dc["ret2"] > 0) & ((1 + dc["ret1"]) * (1 + dc["ret2"]) - 1 >= 0.08) & (dc["rvol2"] >= 2)
    c = dc.loc[run, ["symbol", "date"]].merge(V.dayagg()[["symbol", "date", "lo_pre1030"]], on=["symbol", "date"],
                                              how="inner")
    _C["c"] = c
    return c


@numba.njit(cache=False)
def _kernel(b, e, lo1030, tod, c, h, l, fo, gp, vd, vr, ap, side, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        L0 = lo1030[s]
        if not (L0 == L0):
            continue
        for i in range(i0 + 8, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            # (1) below VWAP on >= 70% of the 10:35-13:00 bars available before i
            nb = 0
            nbelow = 0
            for k in range(i0, i):
                if tod[k] >= 1035 and tod[k] <= 1300:
                    nb += 1
                    if vd[k] < 0:
                        nbelow += 1
            if nb < 5 or nbelow < 0.7 * nb:
                continue
            # (2) coil: the 8 bars before i
            ch = -1e18
            cl = 1e18
            for k in range(i - 8, i):
                ch = max(ch, h[k])
                cl = min(cl, l[k])
            a5p = ap[i - 1] / 100.0 * c[i - 1]
            if not (a5p > 0 and ch - cl <= 0.6 * a5p * np.sqrt(8.0) and cl > L0):
                continue
            a5 = ap[i] / 100.0 * c[i]
            if not (vr[i] >= 1.3):
                continue
            vw = c[i] / (1.0 + vd[i] / 100.0)
            op = c[i] / (1.0 + fo[i] / 100.0)
            if side > 0:
                if not (c[i] > vw and c[i] > ch):
                    continue
                sp = cl - 0.1 * a5
                risk = c[i] - sp
                if not (risk > 0):
                    continue
                m[i] = True
                stop[i] = sp
                tgt[i] = max(c[i] + 1.5 * risk, op)
            else:
                if i - 12 < i0:
                    continue
                vw12 = c[i - 12] / (1.0 + vd[i - 12] / 100.0)
                if not (c[i] < cl and vw - vw12 <= 0):
                    continue
                sp = ch + 0.1 * a5
                risk = sp - c[i]
                if not (risk > 0):
                    continue
                pdc = op / (1.0 + gp[i] / 100.0)
                t2 = c[i] - 2.0 * risk
                m[i] = True
                stop[i] = sp
                tgt[i] = max(t2, pdc) if pdc < c[i] else t2
            break
    return m, stop, tgt


def compute(df):
    n = len(df)
    z = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if n == 0:
        return z
    try:
        C = _ctx()
    except Exception:  # noqa: BLE001 - no cache -> no trades
        return z
    sym, dat, b, e = V.keys(df)
    lo = V.segmap(sym, dat, b, C, ["lo_pre1030"])["lo_pre1030"]
    f = lambda k: df[k].to_numpy(float)
    return _kernel(b, e, lo, df["tod"].to_numpy(np.int64), f("close"), f("high"), f("low"), f("fromOpen"), f("gap"),
                   f("vwapDistPct"), f("volumeRatio"), f("atrPct"), 1 if SIDE == "long" else -1, WINDOW[0], WINDOW[1])


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
