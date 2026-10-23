"""pod-of4-iceberg-floor-hivol-touches-long - Iceberg-bid proxy: 3+ high-volume touches of the same low that hold,
buy the break of the cluster high (LONG).

Source: Bookmap 'How to trade around iceberg orders' (repeated aggression at one price with minimal movement);
EnergyExch Jigsaw user on absorption at levels.
URL: https://bookmap.com/blog/how-to-trade-effectively-around-iceberg-orders-key-strategies-tips

VARIANT of pod-smb-held-floor-triple-bottom-long and pod-of-lowerwick-cluster-quiet-lod-long (both price-only).
Change: each touch must carry heavy volume (absorption / iceberg) and the touches must fall within 30 minutes.

Rules (plain English). Bars: full-session 5m bars 09:35..15:00 with real volume (_r37_util.vbars). ATR(5m) = mean of
the 14 latest 5m true ranges. 20-bar average volume = the 20 bars before the bar.
  1. Cluster: within the 6 bars before the trigger bar (30 minutes), >= 3 bars have lows within 0.03% of the same
     price P (P = the lowest of those lows; every touching low <= P x 1.0003), and no bar from the first touch to the
     trigger closes below P.
  2. Each touching bar has volume >= 1.3x its 20-bar average and closes in the upper half of its range.
  3. P is within 0.2% of the session low of day (as of the bar before the trigger) or of the prior-day low
     (lib.daily D-1).
  Quiet gate (the idea's regime hint, stated in the source summary): SPY's session range so far is < 0.7x SPY's mean
  daily range of the 20 prior sessions.
  Entry: the first 5m close above the highest high of the touching bars, bar close 10:15-15:00 (source says 15:15;
  the scorer clips at 15:00).
  Stop (GEOM S+x): P - 0.05 x ATR(5m). Target: 1.5R or VWAP - the nearer of the two when VWAP is above the entry,
  else 1.5R (declared before scoring). Time stop 60 min (MAX_BARS 12). Flat 15:55.
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
MAX_BARS = 12
WINDOW = (1015, 1500)
LAYERS = [">= 3 touches of P (0.03%) in 6 bars, no close below P", "each touch vol >= 1.3x 20-bar avg, close upper half",
          "P within 0.2% of LOD or PDL", "SPY range so far < 0.7x 20d avg", "close > cluster high",
          "stop P - 0.05 ATR5, target nearer of 1.5R / VWAP, 60 min time stop"]
_ST = {}


@numba.njit(cache=False)
def _k(nd, tod, o, h, l, c, v, atr, pdl, a5, va, vw, qt):
    n = len(c)
    m = np.zeros(n)
    st = np.full(n, np.nan)
    tg = np.full(n, np.nan)
    d0 = 0
    done = False
    for i in range(n):
        if nd[i] >= 1:
            d0 = i
            done = False
        if done or i - 6 < d0 or qt[i] != 1.0 or tod[i] < 1015:
            continue
        A = a5[i]
        if not (A == A and A > 0):
            continue
        lod = np.inf
        for j in range(d0, i):
            lod = min(lod, l[j])
        best = False
        bP = 0.0
        bmax = 0.0
        for k in range(i - 6, i):
            # candidate P = l[k] as the cluster's lowest touch
            P = l[k]
            cnt = 0
            mx = -np.inf
            first = -1
            for j in range(i - 6, i):
                if l[j] >= P and l[j] <= P * 1.0003:
                    rg = h[j] - l[j]
                    if not (va[j] == va[j] and v[j] == v[j] and v[j] >= 1.3 * va[j] and rg > 0
                            and c[j] >= l[j] + 0.5 * rg):
                        continue
                    cnt += 1
                    mx = max(mx, h[j])
                    if first < 0:
                        first = j
            if cnt < 3:
                continue
            ok = True
            for j in range(first, i + 1):
                if c[j] < P:
                    ok = False
                    break
            if not ok:
                continue
            near = abs(P - lod) <= 0.002 * P or (pdl[i] == pdl[i] and abs(P - pdl[i]) <= 0.002 * P)
            if not near:
                continue
            if c[i] > mx:
                best = True
                bP = P
                bmax = mx
                break
        if best:
            e = c[i]
            s = bP - 0.05 * A
            R = e - s
            if R > 0:
                t = e + 1.5 * R
                if vw[i] == vw[i] and vw[i] > e:
                    t = min(t, vw[i])
                m[i] = 1.0
                st[i] = s
                tg[i] = t
                done = True
    return m, st, tg


def compute(df):
    n = len(df)
    z = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    X = U.vbars(df)
    if X is None or not len(X):
        return z
    d = U.daily_x(X, ["l1"])
    import _r24_bars as R24
    S = R24.spy_bars()[["date", "tod", "run_h", "run_l"]].copy()
    S["date"] = S["date"].astype(str)
    S = S.merge(U.spy_day()[["date", "spy_rng20m1"]], on="date", how="left")
    S["tod"] = S["tod"].astype(np.int64)
    k = pd.DataFrame({"date": X["date"].astype(str).to_numpy(), "tod": X["tod"].to_numpy(np.int64)})
    q = k.merge(S, on=["date", "tod"], how="left")
    assert len(q) == len(X)
    with np.errstate(invalid="ignore"):
        quiet = ((q["run_h"] - q["run_l"]) < 0.7 * q["spy_rng20m1"]).to_numpy(float)
    r = U.run_kernel(df, _k, extra=(d["l1"], U.atr5, U.vavg20, U.vwap, quiet))
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
