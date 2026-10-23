"""pod-r3-hidden-bull-div-upday-long - Hidden bullish divergence on an up day: a higher price low with a lower RSI
low, then an RSI5 cross up (LONG).

Source: YouTube-origin EMA/RSI hidden-divergence strategy ('tested hundreds of times manually' per the script
author), automated as a TradingView script; Trading Rush-style indicator test.
URL: https://in.tradingview.com/script/itKnLY6I

New: the repo has only REGULAR divergence (bull_div / bdi-rdt-r12-rsi-div); hidden divergence is the continuation form.
Rules (plain English):
  1. Trend: emaDiff > 0, sma50_dist_pct > 0 (stand-in for the source's EMA50 > EMA250), fromOpen > 0.5%.
  2. Swing low A = min low over bars t-20..t-8 with its RSI14 (the frame's `rsi`) value rsiA; current pullback low
     B = min low over t-4..t with its RSI14 value. Require B > A (higher low) AND rsi at B < rsiA - 3 (lower RSI low).
     The look-back is a continuous 5m chart per symbol (it spans the sessions in the frame).
  3. Trigger: rsi5 crosses up through 35 on the current bar (prior bar < 35, now >= 35, same session) and
     close > EMA9 (EMA9 of 5m closes, recomputed, carried across sessions).
  4. vwapDistPct >= -0.2 and spy_fo > 0.
  Window 10:15-14:45. Entry at close. Stop (GEOM S): B - 0.05 x atr_d. Target: the prior 20-bar high (max high of
  t-20..t-1), capped at entry + 2R; otherwise flat 15:55. Scorer control: hold (the stated control geometry).
Harness notes (pre-declared): a signal whose 20-bar high is not above the entry is skipped by the scorer. No tweak
used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r28_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1015, 1445)
CONTEXT = ["spy_fo"]
LAYERS = ["emaDiff > 0, sma50_dist_pct > 0, fromOpen > 0.5", "swing low A (t-20..t-8) < pullback low B (t-4..t)",
          "RSI14 at B < RSI14 at A - 3 (hidden bull div)", "rsi5 crosses up 35, close > EMA9",
          "vwapDistPct >= -0.2, spy_fo > 0", "10:15-14:45", "stop B - 0.05 ATR, target 20-bar high capped 2R"]
_ST = {}


@numba.njit(cache=False)
def _swing(l, h, rsi, st):
    n = len(l)
    A = np.full(n, np.nan)
    rA = np.full(n, np.nan)
    B = np.full(n, np.nan)
    rB = np.full(n, np.nan)
    H20 = np.full(n, np.nan)
    g0 = 0
    for t in range(n):
        if st[t]:
            g0 = t
        if t - g0 < 20:
            continue
        a = t - 20
        for q in range(t - 19, t - 7):
            if l[q] < l[a]:
                a = q
        b = t - 4
        for q in range(t - 3, t + 1):
            if l[q] < l[b]:
                b = q
        hh = h[t - 20]
        for q in range(t - 19, t):
            if h[q] > hh:
                hh = h[q]
        A[t], rA[t], B[t], rB[t], H20[t] = l[a], rsi[a], l[b], rsi[b], hh
    return A, rA, B, rB, H20


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i])


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not U.ctx_ok(df, ["spy_fo"]):
        _ST[id(df)] = (np.full(n, np.nan), np.full(n, np.nan))
        return np.zeros(n, bool)
    c, h, l, atr = U.f(df, "close"), U.f(df, "high"), U.f(df, "low"), U.f(df, "atr_d")
    sk = U.symkey(df)
    dk = U.daykey(df)
    st = U.start(sk)
    A, rA, B, rB, H20 = _swing(l, h, U.f(df, "rsi"), st)
    e9 = U.ema(c, st, 9)
    r5 = U.f(df, "rsi5")
    r5p = U.lag(r5, dk, 1)
    tod = df["tod"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        m = (U.f(df, "emaDiff") > 0) & (U.f(df, "sma50_dist_pct") > 0) & (U.f(df, "fromOpen") > 0.5)
        m &= (B > A) & (rB < rA - 3)
        m &= (r5p < 35) & (r5 >= 35) & (c > e9)
        m &= (U.f(df, "vwapDistPct") >= -0.2) & (U.f(df, "spy_fo") > 0)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    stop = B - 0.05 * atr
    _ST[id(df)] = (stop, np.minimum(H20, c + 2.0 * (c - stop)))
    return np.asarray(m, bool)
