"""pod-bbt-lightning-bolt-vwap-cross-continuation-long - Lightning Bolt: VWAP up-cross, shallow pullback, continuation
break (LONG). Main config: bar close 09:50-11:30. The declared second config (09:50-15:00) is
pod-bbt-lightning-bolt-vwap-cross-continuation-long-allday.py, which reuses this file with a wider WINDOW.

Source: Bear Bull Traders - Peter Donnelly, 'Strategy 6: Lightning Bolt' / TradeBook: Lightning Bolt Pattern (2023
deck, BBT handbook cheat sheet).
URL: https://bearbulltraders.com/wp-content/uploads/2023/06/2023-05-Lightning-Bolt-Pattern-vfinal.pdf

VARIANT of the backlog 'VWAP reclaim after >= 15-30 min below, entry on the first pullback that holds' and Reddit R02
VWAP reclaim (failed). Stated changes: a minimum leg into VWAP, a pullback of at most 50% of the leg, volume must not
dry up, entry on a continuation break of the cross bar's high, a tight stop at the last below-VWAP bar, target 2R
(the source takes no partials before 2R).

Rules (plain English, LONG), decision bar i on the 5-minute frame, bars of the same symbol-day up to i only:
  (1) Leg: L = the lowest low of bars i-12..i-3 (its bar at or before the cross bar), with VWAP(cross bar) - L
      >= 0.30 x atr_d.
  (2) Cross: bar c in i-4..i-2 is the first close above session VWAP after >= 4 consecutive closes below it;
      H = high of c; the leg H - L >= 0.6 x atr_d.
  (3) Pullback: the bars between c and i (>= 1) do not close above H; their lowest low >= L + 0.5 x (H - L) (no more
      than a 50% retrace); their mean volumeRatio >= 0.8 x the mean volumeRatio of the bars from the L bar to c.
  (4) Trigger: close_i > H and close_i > VWAP_i.
  Entry: close_i. Stop (GEOM S): min(close of bar c-1, pullback low) - 0.02 x atr_d (stand-in for 'the open of the
  candle on the opposite side of VWAP'; the frame has no bar open). Target: entry + 2R. Flat 15:55. Costs in.
No tweak used (the two windows are the source's two declared configs). Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1130)
CONTEXT = []
LAYERS = ["leg: 10-bar low L, VWAP - L >= 0.3 ATR, H - L >= 0.6 ATR",
          "cross bar 2-4 bars back: first close above VWAP after >= 4 closes below",
          "pullback <= 50% of the leg, volume >= 0.8x the leg's", "close above the cross-bar high and VWAP",
          "stop min(close c-1, pullback low) - 0.02 ATR, target 2R, flat 15:55"]

_STASH = {}


def _segments(df):
    k = pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kern(b, e, c, h, l, vd, vw, vr, atr):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 8, i1):
            if not (vd[i] > 0) or not np.isfinite(atr[i]) or atr[i] <= 0:
                continue
            for cc in range(i - 2, i - 5, -1):
                if cc - 4 < i0:
                    continue
                if not (vd[cc] > 0):
                    continue
                ok = True
                for q in range(cc - 4, cc):
                    if not (vd[q] <= 0):
                        ok = False
                if not ok:
                    continue
                H = h[cc]
                if not (c[i] > H):
                    continue
                lo0 = max(i0, i - 12)
                L = 1e18
                lb = -1
                for q in range(lo0, i - 2):
                    if l[q] < L:
                        L = l[q]
                        lb = q
                if lb < 0 or lb > cc:
                    continue
                if vw[cc] - L < 0.30 * atr[i] or H - L < 0.6 * atr[i]:
                    continue
                pl = 1e18
                vs = 0.0
                ok = True
                for q in range(cc + 1, i):
                    if c[q] > H:
                        ok = False
                    pl = min(pl, l[q])
                    vs += vr[q]
                if not ok or pl < L + 0.5 * (H - L):
                    continue
                vmean = vs / (i - cc - 1)
                ls = 0.0
                for q in range(lb, cc + 1):
                    ls += vr[q]
                lmean = ls / (cc - lb + 1)
                if not (vmean >= 0.8 * lmean):
                    continue
                st = min(c[cc - 1], pl) - 0.02 * atr[i]
                if st < c[i]:
                    m[i] = True
                    stop[i] = st
                    break
    return m, stop


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, vd, vr, atr = f("close"), f("high"), f("low"), f("vwapDistPct"), f("volumeRatio"), f("atr_d")
    vr = np.nan_to_num(vr, nan=0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + vd / 100)
    b, e = _segments(df)
    m, stop = _kern(b, e, c, h, l, vd, vw, vr, atr)
    tod = df["tod"].to_numpy(np.int64)
    m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    tgt = c + 2 * (c - stop)
    return m, stop, tgt


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
