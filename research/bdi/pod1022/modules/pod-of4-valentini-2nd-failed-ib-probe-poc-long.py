"""pod-of4-valentini-2nd-failed-ib-probe-poc-long - Balance-day second failed probe below the IB low, target the
developing POC (LONG, mean-reversion model).

Source: Fabio Valentini order-flow models (balance vs imbalance; mean reversion after a second failed attempt) as
summarised by the Tradezella auction-market playbook / PickMyTrade.
URL: https://www.tradezella.com/playbooks/auction-market-playbook

VARIANT of pod-of3-barros-ib-failed-lookbelow-opposite-extension-long (a single failure, target the opposite
extension). Changes: two failures are required, a balance-day gate, and the target is the developing POC.

Rules (plain English). Bars: full-session 5m bars 09:35..15:00 with real volume (_r37_util.vbars).
  IB = high / low of the 12 bars 09:30-10:30 (all 12 required).
  1. Balance day: the IB is inside the prior-day range (IB high <= PDH and IB low >= PDL, lib.daily D-1) and the IB
     width <= 0.8x the mean IB width of the 20 prior sessions.
  2. After 10:30: probe 1 = a bar whose low < IB low; it must close back inside (close > IB low) on that bar or one of
     the next 2 bars, else the day is done (acceptance below). Probe 2 = a later bar whose low < IB low, starting >= 3
     bars after probe 1 started and after probe 1's reclaim (at or below the probe-1 low allowed); it must also close
     back inside within 2 bars.
  3. Entry: the 5m close back inside the IB after probe 2, bar close 10:35-15:00 (source says 15:15; the scorer clips
     at 15:00).
  Stop (GEOM S+x): the lower of the two probe lows - 0.05 x daily ATR. Target: today's developing POC at entry
  (volume-at-price from the session's 5m bars, each bar's volume spread evenly over its high-low range, bins of
  0.02 x daily ATR); skip if POC - entry < 1.2x risk. Time stop 90 min (MAX_BARS 18). Flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r39_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 18
WINDOW = (1035, 1500)
LAYERS = ["balance: IB inside prior range, IB width <= 0.8x 20d avg", "probe 1 below IBL, back inside within 2 bars",
          "probe 2 >= 3 bars later, back inside within 2 bars", "entry the probe-2 reclaim close",
          "stop lower probe low - 0.05 ATR, target developing POC >= 1.2R, 90 min time stop"]
_ST = {}
NB = 2001


@numba.njit(cache=False)
def _k(nd, tod, o, h, l, c, v, atr, ibh, ibl, bal):
    n = len(c)
    m = np.zeros(n)
    st = np.full(n, np.nan)
    tg = np.full(n, np.nan)
    hist = np.zeros(NB)
    anchor = 0.0
    bs = 0.0
    dead = False
    npr = 0          # completed (reclaimed) probes
    inpr = False
    pstart = -1
    p1start = -1
    plow = 0.0
    p1low = 0.0
    for i in range(n):
        if nd[i] >= 1:
            for b in range(NB):
                hist[b] = 0.0
            anchor = o[i]
            bs = 0.02 * atr[i]
            dead = not (bal[i] == 1.0 and bs > 0 and anchor == anchor)
            npr = 0
            inpr = False
        if not dead and v[i] == v[i] and v[i] > 0:
            b0 = int(np.floor((l[i] - anchor) / bs)) + NB // 2
            b1 = int(np.floor((h[i] - anchor) / bs)) + NB // 2
            b0 = min(max(b0, 0), NB - 1)
            b1 = min(max(b1, 0), NB - 1)
            w = v[i] / (b1 - b0 + 1)
            for b in range(b0, b1 + 1):
                hist[b] += w
        if dead or tod[i] <= 1030:
            continue
        L = ibl[i]
        if inpr:
            plow = min(plow, l[i])
            if c[i] > L:
                inpr = False
                npr += 1
                if npr == 1:
                    p1low = plow
                else:
                    e = c[i]
                    s = min(p1low, plow) - 0.05 * atr[i]
                    R = e - s
                    bm = 0
                    for b in range(NB):
                        if hist[b] > hist[bm]:
                            bm = b
                    poc = anchor + (bm - NB // 2 + 0.5) * bs
                    if R > 0 and poc - e >= 1.2 * R:
                        m[i] = 1.0
                        st[i] = s
                        tg[i] = poc
                    dead = True
            elif i - pstart >= 2:
                dead = True
            continue
        if l[i] < L and (npr == 0 or i - p1start >= 3):
            pstart = i
            if npr == 0:
                p1start = i
            plow = l[i]
            if c[i] > L:
                npr += 1
                if npr == 1:
                    p1low = plow
                else:
                    e = c[i]
                    s = min(p1low, plow) - 0.05 * atr[i]
                    R = e - s
                    bm = 0
                    for b in range(NB):
                        if hist[b] > hist[bm]:
                            bm = b
                    poc = anchor + (bm - NB // 2 + 0.5) * bs
                    if R > 0 and poc - e >= 1.2 * R:
                        m[i] = 1.0
                        st[i] = s
                        tg[i] = poc
                    dead = True
            else:
                inpr = True
    return m, st, tg


def _ib(X):
    I = X[X["tod"] <= 1030].groupby(["symbol", "dn"], as_index=False).agg(ibh=("h", "max"), ibl=("l", "min"),
                                                                           nib=("h", "size"))
    I = I[I["nib"] == 12].sort_values(["symbol", "dn"], kind="mergesort").reset_index(drop=True)
    I["w"] = I["ibh"] - I["ibl"]
    sym = I["symbol"].to_numpy()
    newg = np.r_[True, sym[1:] != sym[:-1]] if len(I) else np.zeros(0, bool)
    I["w20"] = U._prior_mean(newg, I["w"].to_numpy(float), 20)
    return I


def compute(df):
    n = len(df)
    z = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    X = U.vbars(df)
    if X is None or not len(X):
        return z
    I = _ib(X)
    K = X[["symbol", "dn", "date"]].merge(I[["symbol", "dn", "ibh", "ibl", "w", "w20"]], on=["symbol", "dn"],
                                         how="left")
    dt = U.daily_tab()[["symbol", "date", "high1", "low1"]]
    K = K.merge(dt, on=["symbol", "date"], how="left")
    assert len(K) == len(X)
    with np.errstate(invalid="ignore"):
        bal = ((K["ibh"] <= K["high1"]) & (K["ibl"] >= K["low1"]) & (K["w"] <= 0.8 * K["w20"])).to_numpy(float)
    r = U.run_kernel(df, _k, extra=(K["ibh"].to_numpy(float), K["ibl"].to_numpy(float), bal))
    tod = df["tod"].to_numpy(np.int64)
    m = r["m"] & (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (r["s"] < U.f(df, "close"))
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
