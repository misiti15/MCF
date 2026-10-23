"""pod-shannon-maxvol-bar-avwap-first-touch-long - First pullback to an AVWAP anchored at today's highest-volume
breakout bar (LONG).

Source: Brian Shannon, 'Maximum Trading Gains With Anchored VWAP' (anchor where volume or news changed sentiment; the
regular VWAP is distorted by the whole day's volume, so anchor at the start of the move - Friendly Bear podcast
'Everything AVWAP'); Benzinga 'My favorite ways to use the Anchored VWAP' (buy strength after the dip, stop under the
recent low).
URL: https://alphatrends.net/archives/podcast/the-friendly-bear-podcast-w-brian-shannon-cmt-everything-avwap/

NEW anchor. The backlog has only a PRIOR-day high-volume-bar AVWAP fade (a short at +2SD), which is different.

Rules (plain English). Bars: full-session 5m bars 09:35..15:00 with real volume (_r37_util.vbars: h / l / c from the
history frames + head table, volume from the 1-minute vendor bars). A bar's open is not stored: open = the previous
bar's close (09:35 bar: the 09:30 open) - stated proxy for 'green bar'.
  1. Anchor: at each bar, the session's highest-volume bar so far among bars closing <= 11:00. It must be green
     (close > open), close in the top 30% of its range, have volume >= 3x the average of the 20 PRIOR 5m bars (the
     bar series runs across days) and make a new high of day. When a later bar (<= 11:00) takes over as the
     highest-volume bar, the anchor moves there (or is dropped if that bar fails the checks) and the state resets.
     AVWAP = sum(typical x volume) / sum(volume) from the anchor bar (included) on.
  2. Run: a later bar's high reaches >= AVWAP + 0.5 x daily ATR.
  3. First touch: the first bar after the run whose low comes within 0.05 ATR of the AVWAP (low <= AVWAP + 0.05 ATR).
     It qualifies only if its low is not more than 0.1 ATR under the AVWAP, it closes above the AVWAP and above the
     session VWAP (own VWAP from the same bars). First touch only: a failed touch ends the day.
  4. Entry: the very next bar closes above the touch bar's high; entry bar close 10:00-14:30.
  5. Stop (GEOM S): touch-bar low - 0.05 ATR. Target: the high of day at entry, capped at entry + 2R; no trade when
     the HOD is not above the entry. Flat 15:55. First touch only, one trade per symbol-day.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r37_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
LAYERS = ["max-volume bar <= 11:00: green, top 30% close, vol >= 3x 20-bar avg, new HOD -> AVWAP anchor",
          "run >= 0.5 ATR above AVWAP", "first touch within 0.05 ATR (<= 0.1 ATR under), close > AVWAP and VWAP",
          "next bar closes > touch high, 10:00-14:30", "stop touch low - 0.05 ATR, target HOD capped 2R, flat 15:55"]
_ST = {}


@numba.njit(cache=False)
def _k(newday, tod, o, h, l, c, v, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    # 20 prior bars average volume (continuous per symbol; newday only resets the session state)
    i = 0
    a = -1
    maxv = -1.0
    spv = sv = 0.0
    sp = svv = 0.0
    hod = -np.inf
    ran = False
    done = False
    tch = -1
    for i in range(n):
        if newday[i]:
            a = -1
            maxv = -1.0
            sp = 0.0
            svv = 0.0
            hod = -np.inf
            ran = False
            done = False
            tch = -1
        tp = (h[i] + l[i] + c[i]) / 3.0
        vi = v[i] if v[i] == v[i] else 0.0
        sp += tp * vi
        svv += vi
        vwap = sp / svv if svv > 0 else np.nan
        prevhod = hod
        hod = max(hod, h[i])
        A = atr[i]
        if tod[i] <= 1100 and v[i] == v[i] and v[i] > maxv:
            maxv = v[i]
            a = -1
            ran = False
            done = False
            tch = -1
            # 20 prior bars of the same symbol (the caller marks a symbol change with newday = 2)
            cnt = 0
            s = 0.0
            j = i - 1
            while j >= 0 and cnt < 20 and newday[j + 1] != 2:
                if v[j] == v[j]:
                    s += v[j]
                    cnt += 1
                j -= 1
            rng = h[i] - l[i]
            if cnt == 20 and rng > 0 and c[i] > o[i] and (c[i] - l[i]) >= 0.7 * rng and v[i] >= 3.0 * s / 20.0 \
                    and h[i] >= prevhod:
                a = i
                spv = tp * v[i]
                sv = v[i]
            continue
        if a < 0:
            continue
        spv += tp * vi
        sv += vi
        if done or not (A > 0):
            continue
        av = spv / sv
        if tch >= 0:
            if i == tch + 1 and c[i] > h[tch] and tod[i] >= w0 and tod[i] <= w1:
                sp_ = l[tch] - 0.05 * A
                R = c[i] - sp_
                if R > 0 and hod > c[i]:
                    m[i] = True
                    stop[i] = sp_
                    tgt[i] = min(hod, c[i] + 2.0 * R)
            done = True
            continue
        if not ran:
            if h[i] >= av + 0.5 * A:
                ran = True
            continue
        if l[i] <= av + 0.05 * A:
            if l[i] >= av - 0.1 * A and c[i] > av and c[i] > vwap:
                tch = i
            else:
                done = True
    return m, stop, tgt


def compute(df):
    n = len(df)
    z = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if not n:
        return z
    X = U.vbars(df)
    if X is None or not len(X):
        return z
    sym = X["symbol"].to_numpy()
    dn = X["dn"].to_numpy(np.int64)
    nd = np.zeros(len(X), np.int64)
    nd[0] = 2
    chs = sym[1:] != sym[:-1]
    chd = dn[1:] != dn[:-1]
    nd[1:] = np.where(chs, 2, np.where(chd, 1, 0))
    g = lambda c: X[c].to_numpy(float)
    mm, ss, tt = _k(nd, X["tod"].to_numpy(np.int64), g("o"), g("h"), g("l"), g("c"), g("v"), g("atr"),
                    WINDOW[0], WINDOW[1])
    T = X[["symbol", "dn", "tod"]].copy()
    T["m"], T["s"], T["t"] = mm.astype(float), ss, tt
    r = U.to_frame(df, T, ["m", "s", "t"])
    tod = df["tod"].to_numpy(np.int64)
    m = (r["m"] == 1.0) & (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (r["s"] < U.f(df, "close"))
    return m, r["s"], r["t"]


def mask(df):
    m, s, t = compute(df)
    _ST.clear()
    _ST[id(df)] = (s, t)
    return np.asarray(m, bool)


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
