"""pod-grimes-keltner-thrust-first-ema20-pullback-long - Keltner thrust, then the first pullback to the 20 EMA (Grimes
channel) (LONG).

Source: Adam Grimes, 'The Art and Science of Technical Analysis' (Keltner channels 2.25 ATR around EMA20, as quoted in
a ProRealCode thread); Topstep 'Going deep on Adam Grimes' approach'.
URL: https://www.prorealcode.com/topic/keltner-channel-2

VARIANT of pod-raschke-holygrail-adx-ema20. What changes: momentum is proved by a 5m CLOSE above the upper Keltner
band (EMA20 + 2.25 x ATR20) instead of ADX > 30, and only the FIRST pullback after a fresh thrust is taken.
Rules (plain English, LONG; 5m bars 09:35..15:00 with volume; EMA20 / ATR20 (Wilder) carried across sessions):
  1. Thrust bar T (bar close 09:45-13:30 ET): close > EMA20 + 2.25 x ATR20 and close > session VWAP. A later
     upper-band close resets T to that bar (no second upper-band close between the thrust and the touch).
  2. Touch bar P, 3-15 bars after T: low <= EMA20 + 0.1 x ATR20 (the FIRST such bar after T), with no 5m close below
     EMA20 - 0.25 x ATR20 on bars T+1..P; the pullback (bars T+1..P, >= 2 bars) has a lower average volume than the
     thrust leg (bar T and the 2 bars before it - pre-declared definition of the leg).
  3. Entry: buy-stop above the touch-bar high, valid 2 bars (P+1, P+2); harness fill = the bar whose high reaches it
     and closes above it; entry bar close <= 14:45.
  Stop (GEOM S+x): the pullback low (lowest low T+1..entry-1) - 0.1 x ATR20. Target 1: the thrust high (highest high
  T..P). Trail: exit at the close of the first later 5m bar closing below EMA20; flat 15:55.
  Universe: SPY / QQQ plus in-play large caps = adv20 >= $200M and |gap| >= 1% (pre-declared in-play proxy).
No tweak used. No tuning on valid. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision
bar are used for the entry. Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r311_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
WINDOW = (950, 1445)
MIN_ADV = 200e6
LAYERS = ["5m close > EMA20 + 2.25 ATR20 and > VWAP, 09:45-13:30 (latest thrust)",
          "first touch of EMA20 (+0.1 ATR) 3-15 bars later, no close < EMA20 - 0.25 ATR",
          "pullback avg volume < thrust-leg avg volume", "buy-stop over touch high, 2 bars, to 14:45",
          "SPY/QQQ or adv20 >= $200M with |gap| >= 1%", "stop pullback low - 0.1 ATR, target thrust high, trail close < EMA20"]
_S = U.Stash()


@numba.njit(cache=False)
def _kern(nd, tod, o, h, l, c, v, atr):
    n = len(c)
    m = np.zeros(n)
    s = np.full(n, np.nan)
    t = np.full(n, np.nan)
    xt = np.full(n, np.nan)
    e20 = np.full(n, np.nan)
    a20 = np.full(n, np.nan)
    vw = np.full(n, np.nan)
    ce = np.nan
    ca = np.nan
    na = 0
    trs = 0.0
    pv = 0.0
    vv = 0.0
    for i in range(n):
        if nd[i] == 2:
            ce = np.nan
            ca = np.nan
            na = 0
            trs = 0.0
        if nd[i] >= 1:
            pv = 0.0
            vv = 0.0
        pc = c[i - 1] if (i > 0 and nd[i] != 2) else np.nan
        tr = h[i] - l[i]
        if pc == pc:
            tr = max(tr, abs(h[i] - pc), abs(l[i] - pc))
        if na < 20:
            trs += tr
            na += 1
            if na == 20:
                ca = trs / 20.0
        else:
            ca = (ca * 19.0 + tr) / 20.0
        a20[i] = ca
        ce = c[i] if ce != ce else ce + (c[i] - ce) * (2.0 / 21.0)
        e20[i] = ce
        pv += (h[i] + l[i] + c[i]) / 3.0 * v[i]
        vv += v[i]
        vw[i] = pv / vv if vv > 0 else np.nan
    # state machine per symbol-day
    T = -1
    P = -1
    done = False
    bad = False
    for i in range(n):
        if nd[i] >= 1:
            T = -1
            P = -1
            done = False
        if done or a20[i] != a20[i]:
            continue
        # entry check on an armed touch
        if P >= 0 and i > P:
            if i - P > 2:
                P = -1
                done = True          # first pullback only: the buy-stop expired
                continue
            if h[i] >= h[P] + 0.01 and c[i] > h[P] + 0.01 and tod[i] <= 1445:
                pl = l[T + 1]
                for q in range(T + 1, i):
                    pl = min(pl, l[q])
                stop = pl - 0.1 * a20[i]
                th = h[T]
                for q in range(T, P + 1):
                    th = max(th, h[q])
                if stop < c[i] and th > c[i]:
                    m[i] = 1.0
                    s[i] = stop
                    t[i] = th
                    j = i + 1
                    while j < n and nd[j] == 0:
                        if c[j] < e20[j]:
                            xt[i] = tod[j]
                            break
                        j += 1
                done = True
                continue
            continue
        up = c[i] > e20[i] + 2.25 * a20[i]
        if up:
            if tod[i] >= 945 and tod[i] <= 1330 and c[i] > vw[i] and i >= 2 and nd[i] == 0 and nd[i - 1] == 0:
                T = i
                bad = False
            else:
                T = -1
            continue
        if T < 0:
            continue
        k = i - T
        if c[i] < e20[i] - 0.25 * a20[i]:
            bad = True
        if bad or k > 15:
            T = -1
            continue
        if l[i] <= e20[i] + 0.1 * a20[i]:
            if k < 3:
                T = -1               # touched too early: not the 3-15 bar pullback
                continue
            lv = (v[T] + v[T - 1] + v[T - 2]) / 3.0
            pvv = 0.0
            for q in range(T + 1, i + 1):
                pvv += v[q]
            pvv /= k
            if pvv < lv:
                P = i
            else:
                T = -1
                done = True          # the first pullback failed the volume test
    return m, s, t, xt


def mask(df) -> np.ndarray:
    n = len(df)
    r = U.run_kernel(df, _kern, cols=("m", "s", "t", "xt"))
    _S.put(df, s=r["s"], t=r["t"], xt=r["xt"])
    if not n:
        return np.zeros(0, bool)
    sym = df["symbol"].astype(str).to_numpy()
    inplay = np.isin(sym, ["SPY", "QQQ"]) | (np.abs(U.f(df, "gap")) >= 1.0)
    tod = df["tod"].to_numpy(np.int64)
    return np.asarray(r["m"] & inplay & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)


def stop_price(f, i):
    return float(_S.get(f, "s", mask)[i])


def target_price(f, i, stop):
    return float(_S.get(f, "t", mask)[i])


def exit_index(f, i, stop, target):
    return U.exit_from_tod(f, i, float(_S.get(f, "xt", mask)[i]))
