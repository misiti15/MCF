"""pod-smb-gapdown-opening-print-reclaim-B-long - Gap-down opening-print reclaim (SMB 'reclaim the open'), Version B
(late day, 14:00-15:00) (LONG).

Source: SMB Capital YouTube / SMB Training opening-print tape lessons (Bellafiore / Bernstein: the opening print as
the day's first level). Taken from SMB material already known; the web was unavailable this round.
URL: https://www.youtube.com/@smbcapital

VARIANT of Reddit R05 gap-fill and of wi-red-to-green. Stated change: the trigger level is the OPENING PRINT, not the
prior close or VWAP, used at two pre-declared times (Version B here; Version A is the -A- file, scored separately).

Values: today's open = close / (1 + fromOpen%); prior close PDC = open / (1 + gap%); VWAP = close / (1 + vwapDistPct%);
low of day = close - dist_lod_atr x atr_d (includes 09:30-09:50); daily ATR = atr_d (as of the prior close).

Rules (plain English), decision bar i:
  1. Gap down: open - PDC <= -0.5 x daily ATR.
  2. Before the trigger (low of day as of bar i-1) the stock traded >= 0.3 ATR below the open.
  3. Bar i closes above the opening price AND above VWAP; bar i-1 closed at or below max(open, VWAP) (a reclaim).
  4. volumeRatio_i >= 1.3.
  Version B: bar close 14:00-15:00 ET (the source says 14:00-15:15; the scorer clips windows at 15:00), and
  condition 2 must have held since 10:30: no close above the open from 10:30 to bar i-1. Entry: the scorer enters at close_i (= next bar
  open), one per symbol-day.
  Stop (GEOM S): max(low of day, open - 0.3 ATR). Target: PDC (gap fill). Flat 15:55. Costs in (scorer).
No tweak used; thresholds are the idea's.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
VERSION = "B"
WINDOW = (1400, 1500)
LAYERS = ["gap <= -0.5 ATR", "LOD (before trigger) <= open - 0.3 ATR", "close crosses above max(open, VWAP)",
          "volumeRatio >= 1.3", "no close above the open since 10:30",
          "stop max(LOD, open - 0.3 ATR), target PDC", "14:00-15:00 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, fo, gp, dlod, vr, vd, atr, w0, w1, late):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        a = atr[i0]
        if not (a > 0):
            continue
        op = c[i0] / (1.0 + fo[i0] / 100.0)
        pdc = op / (1.0 + gp[i0] / 100.0)
        if not (op - pdc <= -0.5 * a):
            continue
        for i in range(i0 + 1, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            lod_prev = c[i - 1] - dlod[i - 1] * a
            if not (lod_prev <= op - 0.3 * a):
                continue
            if late:
                # Version B: below the open since 10:30 (no close above the open from 10:30 to bar i-1)
                ok = False
                bad = False
                for k in range(i0, i):
                    if tod[k] >= 1030:
                        ok = True
                        if c[k] > op:
                            bad = True
                            break
                if bad or not ok:
                    continue
            vw = c[i] / (1.0 + vd[i] / 100.0)
            vwp = c[i - 1] / (1.0 + vd[i - 1] / 100.0)
            if not (c[i] > op and c[i] > vw and c[i - 1] <= max(op, vwp)):
                continue
            if not (vr[i] >= 1.3):
                continue
            lod = c[i] - dlod[i] * a
            sp = max(lod, op - 0.3 * a)
            if sp < c[i] and pdc > c[i]:
                m[i] = True
                stop[i] = sp
                tgt[i] = pdc
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("fromOpen"), f("gap"), f("dist_lod_atr"),
                   f("volumeRatio"), f("vwapDistPct"), f("atr_d"), WINDOW[0], WINDOW[1], VERSION == "B")


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
