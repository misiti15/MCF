"""pod-bbt-inverse-hs-below-vwap-long - Inverse head-and-shoulders at the low of day, neckline break, on choppy days
(LONG).

Source: Bear Bull Traders chart-pattern lessons (head and shoulders / inverse H&S as an intraday reversal; Aziz's
reversal webinars). Not re-fetched this round.
URL: https://www.youtube.com/@BearBullTraders

VARIANT of bdi-reddit-vwap-double-bottom (W at VWAP). Stated changes: a three-low structure (lower middle low) at the
LOD below VWAP, not at VWAP; neckline = the higher of the two reaction highs; a measured-move target.

Rules (plain English):
  1. Three 5-bar pivot lows (low below the 2 bars on each side) L1, H, L2 in time order, with L1 9-30 bars before
     this bar. H is the running LOD (its low equals the LOD at this bar). L1 = the latest pivot before H inside that
     span, L2 = the latest pivot after H that is confirmed (2 bars after it closed) before this bar. L1 and L2 are each
     0.15-0.60 x atr_d above H and within 0.15 x atr_d of each other.
  2. Neckline N = the highest high between L1 and L2 (both reaction highs lie there; N is the higher one).
  3. This bar is the first close > N + 0.02 x atr_d after L2, with volumeRatio >= 1.2.
  4. close < session VWAP and VWAP - close >= 0.5 x (N - H).
  5. 0.35 <= breadth <= 0.65.
  Entry: that close, bar close 10:30-14:30. Stop (GEOM S): L2 - 0.03 x atr_d. Target: min(N + (N - H), session VWAP
  at entry); flat 15:55.
Frame note: pivots are on frame bars only (09:50 on); a head set in 09:30-09:45 cannot qualify. The 'trend-down day'
exclusion in the regime hint is expressed only through the breadth band. No tweak made. Costs per
config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ["breadth"]
LAYERS = ["3 pivot lows L1/H/L2 in the last 9-30 bars, H = LOD", "L1, L2 0.15-0.60 ATR above H, within 0.15 ATR",
          "first close > neckline + 0.02 ATR, volumeRatio >= 1.2", "below VWAP by >= 0.5 x (N - H)",
          "0.35 <= breadth <= 0.65", "stop L2 - 0.03 ATR, target min(N + (N - H), VWAP)", "10:30-14:30"]

import numba
import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _base(df):
    k = _key(df)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=df["tod"].to_numpy(np.int64), c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day (includes 09:30-09:45)
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    return b


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, lod, vw, atr, vr, br, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        piv = np.zeros(i1 - i0, np.bool_)
        for j in range(i0 + 2, i1 - 2):
            if l[j] < l[j - 1] and l[j] < l[j - 2] and l[j] < l[j + 1] and l[j] < l[j + 2]:
                piv[j - i0] = True
        for i in range(i0, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0) or not (br[i] >= 0.35 and br[i] <= 0.65) or not (vr[i] >= 1.2):
                continue
            # head: latest confirmed pivot (j + 2 <= i - 1) whose low is the LOD
            jh = -1
            for j in range(i - 3, max(i0, i - 30) - 1, -1):
                if piv[j - i0] and abs(l[j] - lod[i]) <= 1e-6 * c[i]:
                    jh = j
                    break
            if jh < 0:
                continue
            j2 = -1
            for j in range(i - 3, jh, -1):
                if piv[j - i0]:
                    j2 = j
                    break
            j1 = -1
            for j in range(jh - 1, max(i0, i - 30) - 1, -1):
                if piv[j - i0]:
                    j1 = j
                    break
            if j1 < 0 or j2 < 0 or i - j1 < 9:
                continue
            H = l[jh]
            d1 = l[j1] - H
            d2 = l[j2] - H
            if not (d1 >= 0.15 * a and d1 <= 0.60 * a and d2 >= 0.15 * a and d2 <= 0.60 * a):
                continue
            if abs(l[j1] - l[j2]) > 0.15 * a:
                continue
            N = -1e18
            for t in range(j1, j2 + 1):
                N = max(N, h[t])
            thr = N + 0.02 * a
            if not (c[i] > thr):
                continue
            first = True
            for t in range(j2 + 1, i):
                if c[t] > thr:
                    first = False
                    break
            if not first:
                continue
            if not (c[i] < vw[i] and vw[i] - c[i] >= 0.5 * (N - H)):
                continue
            m[i] = True
            stop[i] = l[j2] - 0.03 * a
            tgt[i] = min(N + (N - H), vw[i])
    return m, stop, tgt


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "breadth" not in df:
        return z
    b = _base(df)
    bb, ee = _segments(b["k"])
    m, stop, tgt = _kern(bb, ee, b["tod"], b["c"], b["h"], b["l"], b["lod"], b["vwap"], b["atr"],
                         _f(df, "volumeRatio"), _f(df, "breadth"), WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
