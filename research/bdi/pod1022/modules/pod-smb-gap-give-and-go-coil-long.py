"""pod-smb-gap-give-and-go-coil-long - SMB Gap Give-and-Go: a gap-up gives back part of the gap, coils above support,
buy the coil break (LONG).

Source: SMB Capital Scalp Radar 'Gap Give and Go' (SMB YouTube / SMB Training). Taken from SMB material already known;
web was unavailable this round.
URL: https://www.youtube.com/@smbcapital

VARIANT of cwt-a-a9-goodnews-gap-dip-buy (CWT08, failed 0/72, which bought the VWAP reclaim / prior-bar-high break
after a 25/40% gap pullback). What changes: the entry is a break out of a tight, low-volume consolidation that forms
AFTER the give, and the give must stay well above the prior close.

Rules (plain English):
  1. gap >= +2% and the gap in $ (open - prior close) >= 0.5 x atr_d; 'rvol of the first 15 min >= 2' is proxied by
     volumeRatio >= 2 on the 09:45-09:50 bar (the frame has no raw volume and no 09:30-09:45 bars).
  2. Give (09:30-09:50): the low of day as of the 09:50 bar has retraced 30-60% of the gap from the open, i.e. it lies
     between prior close + 40% and prior close + 70% of the gap; and the low of day at the decision bar is still
     >= prior close + 25% of the gap.
  3. Consolidation: the K bars before the trigger, all after the 09:50 bar (K = the longest of 6..3 that passes;
     pre-declared rule inside the source's 3-6), range <= 0.25 x atr_d, mean volumeRatio < 1.0, consolidation low >=
     session VWAP (at the last consolidation bar) - 0.05 x atr_d.
  4. Trigger: the first 5-minute close above the consolidation high, bar close 09:45-10:30 (effectively 10:10-10:30,
     since the consolidation starts at 09:55).
  5. Market gate 'SPY at or above its VWAP' is proxied by qqq_vwap >= 0 (the frame's point-in-time context has no
     SPY VWAP column).
  Entry: trigger close. Stop (GEOM S): consolidation low - 0.02 x atr_d. Target: the opening-drive high (HOD as of
  the 09:50 bar); if that is less than 1R above the entry, entry + 2R instead.
Deviation: the source's 11:30 time stop cannot be modelled by this scorer; open trades hold to 15:55.
No tweak made. Costs in (scorer). Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1030)
CONTEXT = ["qqq_vwap"]
LAYERS = ["gap >= 2% and >= 0.5 ATR, 09:50 bar volumeRatio >= 2", "give: 09:50 LOD retraced 30-60% of the gap",
          "LOD stays >= prior close + 25% of the gap", "3-6 bar coil: range <= 0.25 ATR, mean vr < 1, low >= VWAP - 0.05 ATR",
          "close > coil high", "qqq_vwap >= 0 (SPY VWAP proxy)", "stop coil low - 0.02 ATR, target opening HOD or 2R",
          "09:45-10:30"]

_ST = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, opn, pc, gap, hod, lod, vw, vr, qv, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if tod[i0] != 950:
            continue
        a = atr[i0]
        G = opn[i0] - pc[i0]
        if not (a > 0 and gap[i0] >= 2.0 and G >= 0.5 * a and vr[i0] >= 2.0):
            continue
        L0 = lod[i0]
        if not (L0 >= pc[i0] + 0.40 * G and L0 <= pc[i0] + 0.70 * G):
            continue
        H0 = hod[i0]
        done = False
        for i in range(i0 + 4, i1):
            if done or tod[i] > w1:
                break
            if tod[i] < w0:
                continue
            if lod[i] < pc[i0] + 0.25 * G:
                break
            if not (qv[i] >= 0):
                continue
            for K in range(6, 2, -1):
                if i - K <= i0:
                    continue
                ch = -1e18
                cl = 1e18
                mv = 0.0
                for t in range(i - K, i):
                    ch = max(ch, h[t])
                    cl = min(cl, l[t])
                    mv += vr[t]
                if ch - cl > 0.25 * a or mv / K >= 1.0 or cl < vw[i - 1] - 0.05 * a:
                    continue
                if c[i] > ch:
                    sp = cl - 0.02 * a
                    r = c[i] - sp
                    tp = H0 if H0 - c[i] >= r else c[i] + 2.0 * r
                    if r > 0:
                        m[i] = True
                        stop[i] = sp
                        tgt[i] = tp
                        done = True
                break
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if n == 0 or "qqq_vwap" not in df:
        return np.zeros(n, dtype=bool)
    f = lambda k: df[k].to_numpy(float)
    c = f("close")
    atr = f("atr_d")
    vw = c / (1 + f("vwapDistPct") / 100)
    opn = c / (1 + f("fromOpen") / 100)
    gap = f("gap")
    pc = opn / (1 + gap / 100)
    hod = c + f("dist_hod_atr") * atr
    lod = c - f("dist_lod_atr") * atr
    b, e = _segments(df)
    m, stop, tgt = _kern(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), opn, pc, gap, hod, lod, vw,
                         f("volumeRatio"), f("qqq_vwap"), atr, WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


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
