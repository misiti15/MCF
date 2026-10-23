"""pod-smb-day2-drive-pullback-long - Day-2 opening drive, buy the first VWAP/SMA20 pullback (LONG).

Source: SMB Training blog 'The PlayBook Checkup: $P 2nd Day Opening Drive and Pullback' (Mike Bellafiore).
URL: https://www.smbtraining.com/blog/the-playbook-checkup-p-2nd-day-opening-drive-and-pullback-power-point-edition

VARIANT of the SMB Second-Day Play tested as CWT10 (cwt-a-a3, failed: PDH breakout). Stated change: the entry is a
PULLBACK after the day-2 opening drive, not a range / PDH break.

Prior-day values (completed days only): D-1 close = today's open / (1 + gap%); D-1 high / low from dist_pdh_atr /
dist_pdl_atr; D-2 close = D-1's open / (1 + D-1 gap%) from the same symbol's rows on the previous trading day of the
frame (previous date in the frame's own date list). When that day is missing (first day of a scored month, or a
blackout day) the row cannot qualify. Today's open = close / (1 + fromOpen%). SMA20 = close / (1 + sma20_dist_pct%),
VWAP = close / (1 + vwapDistPct%). "Green bar": the frame has no bar open, so close > previous close is used (implied by
close > high_{i-1}). No tweak used; values are the source's.

Rules (plain English), decision bar i:
  1. Day 2: D-1 change >= +5% (or D-1 close - D-2 close >= 2 x daily ATR), and the D-1 close is in the top 25% of the
     D-1 range.
  2. Opening drive: high of day >= today's open + 0.5 x daily ATR, and the HOD was made by a bar closing 09:50 or later
     (after 09:45).
  3. Pullback: 0.3 <= dist_hod_atr <= 0.7 at bar i; some bar after the HOD bar up to i has low <= max(VWAP, SMA20) +
     0.05 x daily ATR; no close since the HOD bar more than 0.1 x daily ATR below VWAP.
  4. Trigger: close_i > high_{i-1} (green), rsiSlope > 0; spy_fo > -0.5%.
  Entry: close_i, bar close 10:15-12:30, one per symbol-day. Stop (GEOM S): pullback low (lowest low after the HOD bar
  up to i) - 0.05 x daily ATR. Target: HOD retest (the high of day at bar i). Flat 15:55. Costs in (scorer).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1015, 1230)
CONTEXT = ["spy_fo"]
LAYERS = ["D-1 change >= +5% (or >= 2 ATR), D-1 close in top 25% of its range",
          "HOD >= open + 0.5 ATR, made after 09:45",
          "0.3 <= dist_hod_atr <= 0.7, pullback low tags max(VWAP, SMA20) + 0.05 ATR, no close 0.1 ATR below VWAP",
          "close > high[i-1], rsiSlope > 0, spy_fo > -0.5%", "stop pullback low - 0.05 ATR, target HOD",
          "10:15-12:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _prior_close2(df, b):
    """Per segment: the D-2 close (D-1's open / (1 + D-1 gap)), NaN when D-1 is not in the frame."""
    sym = df["symbol"].astype(str).to_numpy()[b]
    dts = pd.to_datetime(pd.Series(df["date"].to_numpy()[b]).astype(str)).to_numpy()
    c = df["close"].to_numpy(float)[b]
    fo = df["fromOpen"].to_numpy(float)[b]
    gp = df["gap"].to_numpy(float)[b]
    with np.errstate(invalid="ignore", divide="ignore"):
        op = c / (1 + fo / 100)
        pc = op / (1 + gp / 100)                       # this segment's prior close
    days = np.unique(dts)
    di = np.searchsorted(days, dts)
    seg = pd.DataFrame({"s": sym, "di": di, "pc": pc})
    look = seg.set_index(["s", "di"])["pc"]
    look = look[~look.index.duplicated()]
    key = pd.MultiIndex.from_arrays([sym, di - 1])
    return look.reindex(key).to_numpy(float)          # D-1 segment's prior close = D-2 close


@numba.njit(cache=False)
def _kernel(b, e, pc2, tod, c, h, l, fo, gp, dhod, dpdh, dpdl, vd, sd, rs, spy, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        p2 = pc2[s]
        if not (p2 > 0):
            continue
        for i in range(i0 + 2, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0 and spy[i] > -0.5 and rs[i] > 0 and c[i] > h[i - 1] and c[i] > c[i - 1]):
                continue
            if not (dhod[i] >= 0.3 and dhod[i] <= 0.7):
                continue
            op = c[i] / (1.0 + fo[i] / 100.0)
            pc = op / (1.0 + gp[i] / 100.0)
            pdh = c[i] + dpdh[i] * a
            pdl = c[i] - dpdl[i] * a
            if not (pdh > pdl):
                continue
            if not ((pc / p2 - 1.0 >= 0.05 or pc - p2 >= 2.0 * a) and (pc - pdl) / (pdh - pdl) >= 0.75):
                continue
            hod = c[i] + dhod[i] * a
            if not (hod >= op + 0.5 * a):
                continue
            H = -1
            for k in range(i, i0 - 1, -1):
                if h[k] >= hod - 1e-4 * a:
                    H = k
                    break
            if H < 0 or H >= i:
                continue
            pl = 1e18
            tag = False
            bad = False
            for k in range(H, i + 1):
                vw = c[k] / (1.0 + vd[k] / 100.0)
                if c[k] < vw - 0.1 * a:
                    bad = True
                    break
                if k > H:
                    pl = min(pl, l[k])
                    sm = c[k] / (1.0 + sd[k] / 100.0)
                    if l[k] <= max(vw, sm) + 0.05 * a:
                        tag = True
            if bad or not tag:
                continue
            sp = pl - 0.05 * a
            if sp < c[i] and hod > c[i]:
                m[i] = True
                stop[i] = sp
                tgt[i] = hod
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    b, e = _segments(df)
    pc2 = _prior_close2(df, b)
    return _kernel(b, e, pc2, df["tod"].to_numpy(np.int64), f("close"), f("high"), f("low"), f("fromOpen"), f("gap"),
                   f("dist_hod_atr"), f("dist_pdh_atr"), f("dist_pdl_atr"), f("vwapDistPct"), f("sma20_dist_pct"),
                   f("rsiSlope"), f("spy_fo"), f("atr_d"), WINDOW[0], WINDOW[1])


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
