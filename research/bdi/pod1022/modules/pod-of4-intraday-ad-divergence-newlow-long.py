"""pod-of4-intraday-ad-divergence-newlow-long - Volume-weighted close-location (intraday A/D) higher low at a new
price low, quiet afternoon (LONG).

Source: Day One Traders / LuxAlgo absorption vs exhaustion (a shift in delta as confirmation); Chaikin A/D as a
bar-data delta proxy.
URL: https://www.luxalgo.com/library/concept/absorption-and-exhaustion/

VARIANT of pod-r3-hidden-bull-div-upday-long (RSI divergence) and bdi-art-ad-divergence (an untested filter idea).
Change: a delta proxy built from volume-weighted close location is used as a stand-alone trigger at a fresh session
low.

Rules (plain English). Bars: full-session 5m bars 09:35..15:00 with real volume (_r37_util.vbars). Intraday A/D =
cumulative sum from 09:30 of ((C - L) - (H - C)) / (H - L) x V (0 for a zero-range bar). ATR(5m) = mean of the 14
latest 5m true ranges. VWAP = session VWAP from 09:30 (typical price x volume).
  1. After 11:00 (bar close > 11:00), a bar prints a new session low that is >= 0.15% below the prior swing low. The
     prior swing low = the most recent pivot low (a bar whose low is <= the lows of the 2 bars on each side) at least
     6 bars before the new-low bar.
  2. Intraday A/D at the new-low bar is ABOVE its value at the prior swing-low bar (bullish delta divergence).
  3. At the new-low bar the close is below VWAP by >= 0.5 x ATR(5m); at the trigger bar SPY trades inside its
     09:30-10:30 range (SPY close between that range's low and high).
  4. Trigger: within 3 bars after the new-low bar, a 5m close above the prior bar's high. A further new low inside
     those 3 bars is re-evaluated as the new-low bar.
  Entry: the trigger bar close (= next bar open), bar close 11:05-15:00 (source says 15:30; the scorer clips at
  15:00).
  Stop (GEOM S+x): new low of day - 0.05 x ATR(5m). Target: VWAP or 2R, whichever is nearer (2R when VWAP is not
  above the entry) - declared before scoring. Time stop 75 min (MAX_BARS 15). Flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r310_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 15
WINDOW = (1105, 1500)
LAYERS = ["after 11:00 new LOD >= 0.15% below prior pivot low (>= 6 bars back)", "intraday A/D higher at the new low",
          "close <= VWAP - 0.5 ATR5 at the low", "SPY inside its first-hour range",
          "close > prior bar high within 3 bars", "stop LOD - 0.05 ATR5, target nearer of VWAP / 2R, 75 min stop"]
_ST = {}


@numba.njit(cache=False)
def _k(nd, tod, o, h, l, c, v, atr, a5, vw, spin):
    n = len(c)
    m = np.zeros(n)
    st = np.full(n, np.nan)
    tg = np.full(n, np.nan)
    ad = np.zeros(n)
    d0 = 0
    done = False
    lod = np.inf
    kk = -1
    for i in range(n):
        if nd[i] >= 1:
            d0 = i
            done = False
            lod = np.inf
            kk = -1
        rg = h[i] - l[i]
        x = 0.0
        if rg > 0 and v[i] == v[i]:
            x = ((c[i] - l[i]) - (h[i] - c[i])) / rg * v[i]
        ad[i] = x + (ad[i - 1] if i > d0 else 0.0)
        if done:
            lod = min(lod, l[i])
            continue
        newlow = l[i] < lod
        if kk >= 0 and not newlow and i - kk <= 3:
            if c[i] > h[i - 1] and spin[i] == 1.0 and tod[i] <= 1500:
                A = a5[i]
                e = c[i]
                s = l[kk] - 0.05 * A
                R = e - s
                if A == A and A > 0 and R > 0:
                    t = e + 2.0 * R
                    if vw[i] == vw[i] and vw[i] > e:
                        t = min(t, vw[i])
                    m[i] = 1.0
                    st[i] = s
                    tg[i] = t
                    done = True
                    lod = min(lod, l[i])
                    continue
        if kk >= 0 and i - kk >= 3:
            kk = -1
        if newlow and tod[i] > 1100:
            kk = -1
            # most recent pivot low j <= i-6
            j = i - 6
            piv = -1
            while j - 2 >= d0:
                if l[j] <= l[j - 1] and l[j] <= l[j - 2] and l[j] <= l[j + 1] and l[j] <= l[j + 2]:
                    piv = j
                    break
                j -= 1
            A = a5[i]
            if piv >= 0 and A == A and A > 0 and l[i] <= l[piv] * (1 - 0.0015) and ad[i] > ad[piv] \
                    and vw[i] == vw[i] and vw[i] - c[i] >= 0.5 * A:
                kk = i
        lod = min(lod, l[i])
    return m, st, tg


def compute(df):
    n = len(df)
    z = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    X = U.vbars(df)
    if X is None or not len(X):
        return z
    import _r24_bars as R24
    S = R24.spy_bars().copy()
    S["date"] = S["date"].astype(str)
    fh = S[S["tod"] <= 1030].groupby("date").agg(fh_h=("h", "max"), fh_l=("l", "min"), nfh=("h", "size"))
    S = S.merge(fh.reset_index(), on="date", how="left")
    S["tod"] = S["tod"].astype(np.int64)
    k = pd.DataFrame({"date": X["date"].astype(str).to_numpy(), "tod": X["tod"].to_numpy(np.int64)})
    q = k.merge(S[["date", "tod", "c", "fh_h", "fh_l", "nfh"]], on=["date", "tod"], how="left")
    assert len(q) == len(X)
    with np.errstate(invalid="ignore"):
        spin = ((q["nfh"] == 12) & (q["tod"] > 1030) & (q["c"] >= q["fh_l"]) & (q["c"] <= q["fh_h"])).to_numpy(float)
    r = U.run_kernel(df, _k, extra=(U.atr5, U.vwap, spin))
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
