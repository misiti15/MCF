"""pod-smb-day3-extended-belowvwap-coil-break-short - Day 3 extended stock: coil below VWAP breaks down (SHORT).

Source: SMB Capital junior trader deck 'Day 3 in Extended Stock: Consolidation below VWAP' (SUNE 12/17/15).
URL: https://www.slideshare.net/slideshow/how-to-use-vwap-as-an-important-technical-indicator/61960798

Opposite side of pod-smb-day3-extended-belowvwap-coil-pm-reclaim-long (both are run and reported). Not a copy of the
failed cwt 'day-3 failed push' short: that one is a failed new high near the open; this one is a midday coil below
VWAP that breaks down.

Data: as the long module (completed daily bars; day 1 of the run = D-2; pre-10:30 LOD incl. 09:30-09:45 from the
1-minute vendor bars via _smbv5_bars, locked block never read; VWAP / ATR14(5m) / volumeRatio from the frame).

Rules (plain English), decision bar i (bar close 11:00-15:00 ET):
  Context: D-2 and D-1 both closed up, combined return >= +8%, and D-2 (day 1) daily rvol >= 2.
  1. Of the 5m bars closing 10:35-13:00 that are complete before i (at least 5), >= 70% closed below VWAP (point in
     time: before 13:00 only the bars so far are counted).
  2. Coil: the 8 bars before i span <= 0.6 x ATR14(5m) x sqrt(8), coil low above the day's low made before 10:30.
  3. Bar i closes below the coil low with volumeRatio >= 1.3, and VWAP now <= VWAP 12 bars ago (slope <= 0).
  Entry: next bar open (scorer: close_i). Stop (GEOM S): coil high + 0.1 x ATR14(5m). Target: 2R or the prior-day
  close, whichever comes first (the PDC only when it is below entry); time exit 15:55. Borrow assumed available;
  costs in (scorer). 1 config, no tweak.
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1100, 1500)
LAYERS = ["D-2 and D-1 up, combined >= +8%, D-2 rvol >= 2", "below VWAP on >= 70% of 10:35-13:00 bars so far",
          "8-bar coil <= 0.6 ATR5 x sqrt(8), coil low above the pre-10:30 LOD",
          "close below coil low, volumeRatio >= 1.3, VWAP slope(12) <= 0",
          "stop coil high + 0.1 ATR5, target nearer of 2R / PDC", "11:00-15:00 ET"]
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
