"""pod-of4-valentini-imbalance-lvn-pullback-long - Imbalance (trend) day pullback into today's LVN and hold (LONG,
trend model).

Source: Fabio Valentini trend model (out of balance, buy the pullback into the low-volume area) via the PickMyTrade
summary; NexusFi auction theory (favor pullbacks into prior acceptance on imbalance days).
URL: https://blog.pickmytrade.trade/fabio-valentini-pro-scalper-nasdaq-scalping-strategy/

VARIANT of 'Volume profile ... LVN air pocket' (backlog, failed: LVN breakouts) and pod-of-liquidity-vacuum-fill.
Change: a continuation pullback INTO today's LVN on imbalance days only, with a hold-and-reclaim trigger instead of a
break-through.

Rules (plain English). Bars: full-session 5m bars 09:35..15:00 with real volume (_r37_util.vbars). IB = high of the
12 bars 09:30-10:30 (all 12 required). ATR(5m) = mean of the 14 latest 5m true ranges. Profile = today's
volume-at-price built from the 5m bars, each bar's volume spread evenly over its high-low range, bins of 0.1% of the
09:30 open.
  1. Imbalance up: at the 11:00 bar close, the close is above the prior-day high (lib.daily D-1) and the high of day
     is above the IB high (range extension up).
  2. LVN = the lowest-volume 0.1% bin lying between the IB high and the HOD whose upper edge is at least 0.3 x
     ATR(5m) below the HOD, from the profile of the bars BEFORE the current bar (recomputed each bar until a touch).
  3. Pullback into the LVN: a bar after 11:00 trades at or below the LVN upper edge (the LVN is then frozen). Trigger:
     a later-or-same 5m bar closes back above the LVN upper edge with volume above the average volume of the
     pullback bars (the bars after the HOD bar, before the trigger bar). A trade below the stop level, or a new HOD,
     cancels the pullback (a new HOD re-arms the search).
  Entry: the trigger bar close (= next bar open), bar close 11:05-15:00.
  Stop (GEOM S+x): LVN lower edge - 0.1 x ATR(5m). Target: retest of the entry-time HOD, then trail on the prior bar
  low (exit_index: the close of the first bar after the HOD retest whose low is below the previous bar's low).
  Time stop 90 min (MAX_BARS 18). Flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r310_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 18
WINDOW = (1105, 1500)
LAYERS = ["11:00 close > PDH and HOD > IB high", "LVN between IBH and HOD, >= 0.3 ATR5 below HOD",
          "pullback into LVN, close back above LVN top on vol > pullback avg",
          "stop LVN low - 0.1 ATR5, HOD retest then prior-bar-low trail, 90 min time stop"]
_ST = {}
NB = 4001


@numba.njit(cache=False)
def _k(nd, tod, o, h, l, c, v, atr, ibh, pdh, a5):
    n = len(c)
    m = np.zeros(n)
    st = np.full(n, np.nan)
    hd = np.full(n, np.nan)
    hist = np.zeros(NB)
    anchor = 0.0
    bs = 0.0
    dead = True
    armed = False
    state = 0
    hod = 0.0
    hodi = -1
    lo = 0.0
    hi = 0.0
    for i in range(n):
        if nd[i] >= 1:
            for b in range(NB):
                hist[b] = 0.0
            anchor = o[i]
            bs = 0.001 * anchor
            dead = not (bs > 0 and ibh[i] == ibh[i] and pdh[i] == pdh[i])
            armed = False
            state = 0
            hod = -np.inf
            hodi = -1
        if dead:
            continue
        # ---- decision on bar i uses the profile of bars < i (LVN) and bar i itself (touch / trigger)
        if armed and tod[i] > 1100:
            A = a5[i]
            if h[i] > hod:
                state = 0           # new HOD: pullback over, re-arm
            elif A == A and A > 0:
                if state == 0:
                    top = hod - 0.3 * A
                    bm = -1
                    bmin = np.inf
                    for b in range(NB):
                        blo = anchor + (b - NB // 2) * bs
                        bhi = blo + bs
                        if blo >= ibh[i] and bhi <= top and hist[b] < bmin:
                            bmin = hist[b]
                            bm = b
                    if bm >= 0 and l[i] <= anchor + (bm - NB // 2 + 1) * bs:
                        lo = anchor + (bm - NB // 2) * bs
                        hi = lo + bs
                        state = 1
                if state == 1:
                    stp = lo - 0.1 * A
                    if l[i] <= stp:
                        state = 2   # broke the LVN: done for this pullback until a new HOD
                    elif c[i] > hi and i - hodi >= 2:
                        sv = 0.0
                        cnt = 0
                        for j in range(hodi + 1, i):
                            if v[j] == v[j]:
                                sv += v[j]
                                cnt += 1
                        if cnt >= 1 and v[i] == v[i] and v[i] > sv / cnt:
                            m[i] = 1.0
                            st[i] = stp
                            hd[i] = hod
                            dead = True
        # ---- update profile, HOD, arming with bar i
        if v[i] == v[i] and v[i] > 0:
            b0 = int(np.floor((l[i] - anchor) / bs)) + NB // 2
            b1 = int(np.floor((h[i] - anchor) / bs)) + NB // 2
            b0 = min(max(b0, 0), NB - 1)
            b1 = min(max(b1, 0), NB - 1)
            w = v[i] / (b1 - b0 + 1)
            for b in range(b0, b1 + 1):
                hist[b] += w
        if h[i] > hod:
            hod = h[i]
            hodi = i
        if tod[i] == 1100:
            armed = c[i] > pdh[i] and hod > ibh[i]
            if not armed:
                dead = True
    return m, st, hd


def compute(df):
    n = len(df)
    z = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    X = U.vbars(df)
    if X is None or not len(X):
        return z
    I = X[X["tod"] <= 1030].groupby(["symbol", "dn"], as_index=False).agg(ibh=("h", "max"), nib=("h", "size"))
    I = I[I["nib"] == 12]
    K = X[["symbol", "dn"]].merge(I[["symbol", "dn", "ibh"]], on=["symbol", "dn"], how="left")
    assert len(K) == len(X)
    d = U.daily_x(X, ["h1"])
    r = U.run_kernel(df, _k, extra=(K["ibh"].to_numpy(float), d["h1"], U.atr5), cols=("m", "s", "t"))
    tod = df["tod"].to_numpy(np.int64)
    m = r["m"] & (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (r["s"] < U.f(df, "close"))
    return m, r["s"], r["t"]


def mask(df):
    m, s, hd = compute(df)
    _ST.clear()
    k = (df["symbol"].astype(str) + "|" + df["date"].astype(str)).to_numpy()
    _ST[id(df)] = (s, hd, k, df["high"].to_numpy(float), df["low"].to_numpy(float))
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def exit_index(f, i, stop, target):
    """After a bar whose high reaches the entry-time HOD, exit at the close of the first later bar whose low is below
    the previous bar's low (prior-bar-low trail). -1 = none (time stop / flat)."""
    s, hd, k, hh, ll = _get(f)
    tgt = hd[i]
    j = i + 1
    touched = False
    while j < len(f) and k[j] == k[i]:
        if touched and ll[j] < ll[j - 1]:
            return j
        if hh[j] >= tgt:
            touched = True
        j += 1
    return -1
