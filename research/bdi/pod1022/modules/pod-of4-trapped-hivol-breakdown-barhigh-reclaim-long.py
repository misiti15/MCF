"""pod-of4-trapped-hivol-breakdown-barhigh-reclaim-long - Trapped shorts: a high-volume breakdown of the morning low
reclaimed above the breakdown bar's HIGH, daily uptrend (LONG).

Source: Optimus Futures 'How to Spot Trapped Traders Desperate to Get Out'; NinjaTrader liquidity traps.
URL: https://optimusfutures.com/blog/how-to-spot-trapped-traders-desperate-to-get-out-of-a-position

VARIANT of the LIQ sweep-reversal family (level reclaim / impulse-bar open triggers). Changes: the breakdown bar must
carry heavy volume (committed shorts), the trigger is a reclaim of that bar's HIGH rather than of the level, and a
daily-uptrend gate is added.

Rules (plain English). Bars: full-session 5m bars 09:35..15:00 with real volume (_r37_util.vbars). Morning range =
high / low of the 12 bars 09:30-10:30 (all 12 required). ATR(5m) = mean of the 14 latest 5m true ranges.
  1. Daily uptrend (lib.daily, completed days): D-1 close > D-1 SMA20, and the SMA20 is rising (D-1 SMA20 > the SMA20
     five sessions earlier, D-6).
  2. Breakdown: a 5m bar closing at 10:50 or later (after 10:45) closes below the morning low with volume >= 2.0x the
     average volume of the 20 bars before it.
  3. Trigger: within the next 3 bars, a 5m close above that breakdown bar's high. A newer breakdown bar replaces the
     pending one.
  Entry: the trigger bar close (= next bar open), bar close 10:50-15:00.
  Stop (GEOM S+x): the lowest low from the breakdown bar to the trigger bar - 0.05 x ATR(5m).
  Target: the source scales out 50/50 at the range midpoint and the range high, or uses 2R. The scorer has one exit,
  so the target is the average of the two scale-out levels (75% of the morning range), capped at entry + 2R
  (declared before scoring, not tuned). Time stop 75 min (MAX_BARS 15). Flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r310_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 15
WINDOW = (1050, 1500)
LAYERS = ["daily close > SMA20, SMA20 rising", "after 10:45 close < 09:30-10:30 low on vol >= 2x 20-bar avg",
          "close > breakdown bar high within 3 bars", "stop post-breakdown low - 0.05 ATR5",
          "target 75% of morning range capped at 2R, 75 min time stop"]
_ST = {}


@numba.njit(cache=False)
def _k(nd, tod, o, h, l, c, v, atr, orh, orl, up, a5, va):
    n = len(c)
    m = np.zeros(n)
    st = np.full(n, np.nan)
    tg = np.full(n, np.nan)
    bi = -1
    done = False
    for i in range(n):
        if nd[i] >= 1:
            bi = -1
            done = not (up[i] == 1.0 and orl[i] == orl[i] and orh[i] == orh[i])
        if done or tod[i] < 1050:
            continue
        if bi >= 0 and i - bi <= 3 and c[i] > h[bi]:
            lo = l[bi]
            for j in range(bi, i + 1):
                lo = min(lo, l[j])
            A = a5[i]
            if A == A and A > 0:
                e = c[i]
                s = lo - 0.05 * A
                R = e - s
                t = min(orl[i] + 0.75 * (orh[i] - orl[i]), e + 2.0 * R)
                if R > 0 and t > e:
                    m[i] = 1.0
                    st[i] = s
                    tg[i] = t
                    done = True
                    continue
            bi = -1
        if bi >= 0 and i - bi >= 3:
            bi = -1
        if c[i] < orl[i] and va[i] == va[i] and v[i] == v[i] and v[i] >= 2.0 * va[i]:
            bi = i
    return m, st, tg


def compute(df):
    n = len(df)
    z = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    X = U.vbars(df)
    if X is None or not len(X):
        return z
    I = X[X["tod"] <= 1030].groupby(["symbol", "dn"], as_index=False).agg(orh=("h", "max"), orl=("l", "min"),
                                                                           nib=("h", "size"))
    I = I[I["nib"] == 12]
    K = X[["symbol", "dn"]].merge(I[["symbol", "dn", "orh", "orl"]], on=["symbol", "dn"], how="left")
    assert len(K) == len(X)
    d = U.daily_x(X, ["c1", "sma201", "sma206"])
    with np.errstate(invalid="ignore"):
        up = ((d["c1"] > d["sma201"]) & (d["sma201"] > d["sma206"])).astype(float)
    r = U.run_kernel(df, _k, extra=(K["orh"].to_numpy(float), K["orl"].to_numpy(float), up, U.atr5, U.vavg20))
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
