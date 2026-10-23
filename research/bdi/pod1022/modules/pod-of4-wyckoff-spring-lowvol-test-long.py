"""pod-of4-wyckoff-spring-lowvol-test-long - Wyckoff spring on LOW volume plus a secondary test, intraday range low
(LONG).

Source: Wyckoff Method cheat sheet + Wyckoff Event Detection scripts (TradingView community); Trader Dante SFP (the
body must not close beyond the level).
URL: https://cn.tradingview.com/scripts/search/Wyckoff

VARIANT of the LIQ sweep-reversal family and pod-dante-poor-low-double-touch-sweep-quiet-long. Change: the sweep must
happen on LOW volume (no supply), the reverse of the high-volume stop-run condition, and a separate low-volume test is
required before entry.

Rules (plain English). Bars: full-session 5m bars 09:35..15:00 with real volume (_r37_util.vbars). ATR(5m) = simple
mean of the last 14 5m true ranges.
  1. Range: the 12 bars before the spring bar (same day, the first of them closing after 10:00); width (max high -
     min low) <= 0.4 x daily ATR. Range low RL, range high RH.
  2. Spring bar: low below RL by 0.02-0.25 x ATR(5m); volume <= 1.0x the average of the 20 bars before it; the bar
     closes back above RL, or one of the next 2 bars does (without trading below the spring low first).
  3. Test: within 12 bars of the spring, a later bar (after the reclaim) trades within 0.15% of RL (low <= RL x
     1.0015), makes no new low below the spring low, and has volume < the spring-bar volume. The latest such bar is
     the test bar.
  Entry: the first bar after a test bar that closes above the test bar's high (bar-close proxy for the stop-entry),
  still below RH, bar close 10:30-15:00 (source says 15:30; the scorer clips at 15:00). Any bar trading below the
  spring low, or 12 bars without a test (or 12 bars after the test without entry), cancels the setup and the search
  restarts.
  Stop (GEOM S+x): spring low - 0.05 x ATR(5m). Target: RH. Time stop 60 min (MAX_BARS 12). Flat 15:55.
The short mirror (low-volume upthrust) is not run here. No tweak used. 1 configuration. Costs per config/default.yaml
(scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r39_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 12
WINDOW = (1030, 1500)
LAYERS = ["12-bar range after 10:00, width <= 0.4 daily ATR",
          "spring 0.02-0.25 ATR5 below RL on vol <= 20-bar avg, reclaim within 2 bars",
          "test within 0.15% of RL, no new low, vol < spring vol", "close > test high, below RH",
          "stop spring low - 0.05 ATR5, target RH, 60 min time stop"]
_ST = {}


@numba.njit(cache=False)
def _k(nd, tod, o, h, l, c, v, atr):
    n = len(c)
    m = np.zeros(n)
    st = np.full(n, np.nan)
    tg = np.full(n, np.nan)
    tr = np.full(n, np.nan)
    s0 = 0
    d0 = 0
    state = 0          # 0 search, 1 spring waiting reclaim, 2 reclaimed waiting test, 3 test found
    sidx = -1
    sl = 0.0
    RL = 0.0
    RH = 0.0
    vs = 0.0
    a5s = 0.0
    tidx = -1
    for i in range(n):
        if nd[i] == 2:
            s0 = i
        if nd[i] >= 1:
            d0 = i
            state = 0
        tr[i] = h[i] - l[i] if i == s0 else max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        if state == 1:
            if l[i] < sl:
                state = 0
            elif c[i] > RL:
                state = 2
                continue
            elif i - sidx >= 2:
                state = 0
            else:
                continue
        elif state == 2 or state == 3:
            if l[i] < sl:
                state = 0
            else:
                if state == 3 and c[i] > h[tidx]:
                    if c[i] < RH:
                        m[i] = 1.0
                        st[i] = sl - 0.05 * a5s
                        tg[i] = RH
                    state = 0
                    continue
                if i - sidx <= 12 and l[i] <= RL * 1.0015 and v[i] == v[i] and v[i] < vs:
                    state = 3
                    tidx = i
                    continue
                if state == 2 and i - sidx >= 12:
                    state = 0
                elif state == 3 and i - tidx >= 12:
                    state = 0
                else:
                    continue
        # state 0: is bar i a spring?
        if i - 12 < d0 or tod[i - 12] <= 1000 or i - 20 < s0 or i - 13 < s0:
            continue
        A = atr[i]
        if not (A > 0) or not (v[i] == v[i]):
            continue
        hi = -np.inf
        lo = np.inf
        for j in range(i - 12, i):
            hi = max(hi, h[j])
            lo = min(lo, l[j])
        if hi - lo > 0.4 * A:
            continue
        a5 = 0.0
        for j in range(i - 13, i + 1):
            a5 += tr[j]
        a5 /= 14.0
        if not (a5 > 0):
            continue
        if not (l[i] < lo - 0.02 * a5 and l[i] >= lo - 0.25 * a5):
            continue
        sv = 0.0
        cnt = 0
        for j in range(i - 20, i):
            if v[j] == v[j]:
                sv += v[j]
                cnt += 1
        if cnt < 20 or v[i] > sv / 20.0:
            continue
        sidx = i
        sl = l[i]
        RL = lo
        RH = hi
        vs = v[i]
        a5s = a5
        state = 2 if c[i] > RL else 1
    return m, st, tg


def compute(df):
    r = U.run_kernel(df, _k)
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
