"""pod-bbt-mountain-pass-failed-2nd-low-sma50-long - Mountain Pass (low mirror): new low of day, failed second low,
5-minute SMA50 cross, target VWAP (LONG).

Source: Bear Bull Traders - Peter Donnelly, 'TradeBook: Mountain Pass' (Strategy 2 deck, 2023); BBT handbook cheat
sheet.
URL: https://bearbulltraders.com/wp-content/uploads/2023/02/Strategy-2-Mountain-Pass-Peter.pdf

VARIANT of pod-bbt-extreme-rev-mtf-long and bdi-reddit-vwap-double-bottom (W at VWAP). Stated changes: the trigger is
a close back above the 5-minute SMA50 (not an EMA9/20 cross, not a neckline break), it needs a FAILED second push to a
new low (a higher low) rather than an equal-low W, no VWAP-stretch or RSI gate, window 10:30-14:00.

Rules (plain English, LONG), decision bar i on the 5-minute frame (bars of the same symbol-day up to i only; the
frame starts at 09:50, so 'today's bars' are the frame bars from 09:50; the running low of day includes 09:30-09:45):
  (1) Existing trend: the close is below session VWAP on >= 70% of today's frame bars up to the LOD bar; fromOpen at
      the LOD bar <= -1.0%.
  (2) First low: the running low of day (as of bar i) was set on frame bar k in i-18..i-4 (a low of day set before
      09:50 does not qualify).
  (3) Failed second low: after k, a bar's high reached >= LOD + 0.25 x atr_d (the bounce); then a later bar j
      (k+2..i-1) came back with low_j <= LOD + 0.15 x atr_d but low_j > LOD + 0.02 x atr_d (no new low). The latest
      such j is used.
  (4) Trigger: sma50_dist_pct crosses from <= 0 at i-1 to > 0 at i (close back above the 5-minute SMA50), and
      close_i < VWAP_i - 0.20 x atr_d (room to the target).
  (5) Mean volumeRatio of today's frame bars up to i >= 1.0 (in play; source: relative volume > 100%).
  Entry: close_i, bar close 10:30-14:00. Stop (GEOM S): low_j - 0.03 x atr_d. Target: session VWAP at entry; skip if
  (target - entry) < 1.0 x (entry - stop). Flat 15:55. Costs in.
No tweak used. Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1400)
CONTEXT = []
LAYERS = [">= 70% of closes below VWAP up to the LOD bar, fromOpen <= -1% at the LOD",
          "LOD set 4-18 bars ago", "bounce >= 0.25 ATR, then a higher low within 0.02-0.15 ATR of the LOD",
          "close crosses above the 5m SMA50, >= 0.2 ATR below VWAP", "mean volumeRatio today >= 1.0",
          "10:30-14:00", "stop second low - 0.03 ATR, target VWAP (>= 1R), flat 15:55"]

_STASH = {}


def _segments(df):
    k = pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, vd, vw, vr, fo, s50, lodv, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        vsum = 0.0
        for i in range(i0, i1):
            vsum += vr[i]
            if i == i0 or tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0):
                continue
            if not (s50[i - 1] <= 0 and s50[i] > 0):
                continue
            if not (c[i] < vw[i] - 0.20 * a):
                continue
            if vsum / (i - i0 + 1) < 1.0:
                continue
            lod = lodv[i]
            k = -1
            for q in range(i0, i + 1):
                if l[q] <= lod + 0.001 * a:                 # float tolerance
                    k = q
            if k < 0 or k < i - 18 or k > i - 4:
                continue
            nb = 0
            for q in range(i0, k + 1):
                if vd[q] < 0:
                    nb += 1
            if nb < 0.7 * (k - i0 + 1) or not (fo[k] <= -1.0):
                continue
            j = -1
            bounced = False
            for q in range(k + 1, i):
                if bounced and q >= k + 2 and l[q] <= lod + 0.15 * a and l[q] > lod + 0.02 * a:
                    j = q
                if h[q] >= lod + 0.25 * a:
                    bounced = True
            if j < 0:
                continue
            st = l[j] - 0.03 * a
            if st < c[i] and (vw[i] - c[i]) >= 1.0 * (c[i] - st):
                m[i] = True
                stop[i] = st
    return m, stop


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, vd, atr = f("close"), f("high"), f("low"), f("vwapDistPct"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + vd / 100)
        lodv = c - f("dist_lod_atr") * atr
    vr = np.nan_to_num(f("volumeRatio"), nan=0.0)
    s50 = f("sma50_dist_pct")
    b, e = _segments(df)
    m, stop = _kern(b, e, df["tod"].to_numpy(np.int64), c, h, l, vd, vw, vr, f("fromOpen"), s50, lodv, atr,
                    WINDOW[0], WINDOW[1])
    return m, stop, vw


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
