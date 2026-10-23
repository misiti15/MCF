"""pod-traderlion-qqq-vwap-reclaim-rs-leader-long-holdtr - SIBLING of pod-traderlion-qqq-vwap-reclaim-rs-leader-long: same mask, exit holdtr (stop 1R, 1R trail once +1R, flat 15:55).
(holdtr sibling; rules below unchanged.)

Source: TraderLion podcast (relative strength during market pullbacks: buy leaders as the index turns). Related CWT
guests: McDermitt ep267, Bruzzese ep255/312. Not re-fetched in round 2.
URL: https://traderlion.com

VARIANT of CWT16 'Relative Strength vs SPY' (marked 'equivalent already failed'), which buys the stock's own
breakout. Stated change: entry is timed by the index turn (QQQ's VWAP reclaim), and the RS test is whether the stock
held its own VWAP while QQQ was under its VWAP.

Rules (plain English), only bars up to and including the decision bar i of the same symbol-day:
  1. Stretch: qqq_vwap < -0.05 on each of the >= 12 consecutive bars just before i (same day; the whole run counts).
  2. This bar: qqq_vwap > 0 (the first cross after the stretch).
  3. The stock had vwapDistPct > 0 on >= 80% of the stretch bars and has vwapDistPct > 0 now.
  4. fromOpen >= +0.5% and dist_hod_atr <= 0.5.
  Entry: close of the QQQ-reclaim bar, bar close 10:45-14:30. Exit: this file t1s1 (R = 0.25 x daily ATR, target 1R,
  stop 1R, flat 15:55). Siblings: -holdtr (same mask, 1R stop then 1R trail) and -S (stop = the stock's lowest low
  during the stretch - 0.05 x daily ATR, target entry + 1R of that structural risk, flat 15:55). Costs in (scorer).
No tweak made.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "holdtr"
WINDOW = (1045, 1430)
CONTEXT = ["qqq_vwap"]
LAYERS = ["qqq_vwap < -0.05 on >= 12 consecutive prior bars", "qqq_vwap > 0 now (first cross)",
          "stock above own VWAP on >= 80% of stretch bars and now", "fromOpen >= 0.5, dist_hod_atr <= 0.5",
          "10:45-14:30 ET"]


@numba.njit(cache=False)
def _kernel(b, e, tod, c, l, qv, vd, fo, dh, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        run = 0
        above = 0
        runlo = 1e18
        for i in range(i0, i1):
            if qv[i] < -0.05:
                run += 1
                if vd[i] > 0:
                    above += 1
                runlo = min(runlo, l[i])
                continue
            ok = run >= 12 and qv[i] > 0
            r0, a0, lo0 = run, above, runlo
            run = 0
            above = 0
            runlo = 1e18
            if not ok or tod[i] < w0 or tod[i] > w1:
                continue
            if not (a0 >= 0.8 * r0 and vd[i] > 0 and fo[i] >= 0.5 and dh[i] <= 0.5):
                continue
            a = atr[i]
            sp = lo0 - 0.05 * a
            R = c[i] - sp
            m[i] = True
            if R > 0:
                stop[i] = sp
                tgt[i] = c[i] + R
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "qqq_vwap" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("low"), f("qqq_vwap"), f("vwapDistPct"),
                   f("fromOpen"), f("dist_hod_atr"), f("atr_d"), WINDOW[0], WINDOW[1])


_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


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
