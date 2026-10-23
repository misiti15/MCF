"""pod-wt-first-new-high-after-base-pullback-macd-gate-long - Ross Cameron pullback: buy the first candle to make a
new high after a 2-4 bar low-volume pullback, MACD positive, first two pullbacks of the day only (LONG).

Source: Warrior Trading / Ross Cameron (ASNS recap: wait for the first red candle after greens, bounce off the 9 MA)
and a video-summary checklist (first candle making a new high, MACD filter, no dominant selling volume, first or second
pullback only).
URL: https://youtubesummary.com/summary/BUCPPCXOHbs

VARIANT of pod-wt-bull-flag-breakout-or-bailout-long and bdi-reddit-bull-flag-pole. Stated changes: a MACD-positive
gate, a pullback-volume ratio cap, a cap of two pullbacks per day, and a HOD-retest target.

Rules (plain English), 5-minute bars, values from bars up to and including the decision bar i:
  1. fromOpen >= +3%, rvol_day (cumulative volume / its 20-session same-time mean) >= 2, close > session VWAP.
  2. Impulse leg: >= 3 consecutive bars each printing a new high of day, ending at bar T; leg size (high of T - lowest
     low of the leg bars) >= 1 x ATR14 of 5m bars.
  3. Pullback: the 2-4 bars T+1..i-1 each make a lower high; their lowest low retraces <= 50% of the leg; their total
     volume <= 0.6 x the leg's total volume; that low is above both session VWAP and session EMA20 (at the low bar).
  4. MACD(12,26,9) line > 0 and >= its signal line at the pullback-low bar (line from the frame's macdPct; signal =
     EMA9 of the line over the symbol's consecutive frame bars).
  5. It is the 1st or 2nd pullback of the session: completed pullbacks (>= 2 lower highs after a new-HOD bar, then a
     bar breaking the prior bar's high) are counted from 09:50.
  Entry: bar i closes above the high of bar i-1 (the source's stop-entry at the prior high + 1 tick; the scorer fills
  at the close of the breaking bar). Window: bar close 10:00-11:30.
  Stop (GEOM S): the pullback low. Target: the HOD retest (the source's first half). Modelling note: the scorer has one
  exit per trade, so the 9-EMA trail on the second half is not modelled; the trade is taken only when the HOD is at
  least 1R above entry (the source's condition for the HOD half), full size exits at HOD, else stop or 15:55.
  No tweak used. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r32_util as Z  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1130)
CONTEXT = []
LAYERS = ["fromOpen >= 3, rvol_day >= 2, close > VWAP", ">= 3 new-HOD bars, leg >= 1 ATR5m",
          "2-4 lower-high pullback, retrace <= 50%, vol <= 0.6 x leg, low > VWAP and EMA20",
          "MACD > 0 and >= signal at the pullback low", "1st or 2nd pullback", "close > prior bar high",
          "stop pullback low, target HOD (>= 1R)", "10:00-11:30"]
_ST = {}


@numba.njit(cache=False)
def _sig(sym, x):
    out = np.full(len(x), np.nan)
    e = np.nan
    for i in range(len(x)):
        if i == 0 or sym[i] != sym[i - 1]:
            e = np.nan
        if x[i] == x[i]:
            e = x[i] if e != e else e + 0.2 * (x[i] - e)
        out[i] = e
    return out


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, hod, vw, e20, a5, v, mac, sg, fo, rvc, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        npb = 0
        for i in range(i0 + 3, i1):
            # find the pullback ending at i-1 (lower highs from T+1), with T a new-HOD bar
            T = -1
            P = 0
            for q in range(2, 5):
                t = i - 1 - q
                if t < i0:
                    break
                ok = True
                for j in range(t + 1, i):
                    if not (h[j] < h[j - 1]):
                        ok = False
                        break
                if not ok:
                    break
                if h[t] >= hod[t] - 1e-9 * c[t]:
                    T = t
                    P = q
                    break
            if T < 0 or not (c[i] > h[i - 1]):
                continue
            # a completed pullback (counted regardless of the other conditions)
            npb += 1
            if npb > 2 or tod[i] < w0 or tod[i] > w1:
                continue
            if not (fo[i] >= 3.0 and rvc[i] >= 2.0 and c[i] > vw[i]):
                continue
            k = 0
            t = T
            while t >= i0 and h[t] >= hod[t] - 1e-9 * c[t]:
                k += 1
                t -= 1
            if k < 3:
                continue
            ll = 1e18
            lv = 0.0
            for t in range(T - k + 1, T + 1):
                ll = min(ll, l[t])
                lv += v[t]
            leg = h[T] - ll
            if not (a5[T] > 0 and leg >= a5[T]):
                continue
            pl = 1e18
            jl = -1
            pv = 0.0
            for t in range(T + 1, i):
                pv += v[t]
                if l[t] < pl:
                    pl = l[t]
                    jl = t
            if not (h[T] - pl <= 0.5 * leg and lv > 0 and pv <= 0.6 * lv):
                continue
            if not (pl > vw[jl] and pl > e20[jl]):
                continue
            if not (mac[jl] > 0 and mac[jl] >= sg[jl]):
                continue
            H = hod[i - 1]
            r = c[i] - pl
            if not (r > 0 and H - c[i] >= r):
                continue
            m[i] = True
            stop[i] = pl
            tgt[i] = H
    return m, stop, tgt


def mask(df) -> np.ndarray:
    n = len(df)
    _ST.clear()
    if not n:
        return np.zeros(0, bool)
    B = Z.base(df)
    bb = Z.bars(df)
    k = Z.key(df)
    b, e = Z.segments(k)
    c = B["c"]
    with np.errstate(invalid="ignore"):
        a5 = Z.f(df, "atrPct") / 100 * c
        mac = Z.f(df, "macdPct") / 100 * c
    sym = np.asarray(pd.factorize(df["symbol"].astype(str))[0], np.int64)
    sg = _sig(sym, mac)
    m, stop, tgt = _kern(b, e, B["tod"], c, B["h"], B["l"], B["hod"], B["vwap"], bb["e20"], a5, bb["v"], mac, sg,
                         Z.f(df, "fromOpen"), bb["rvc"], WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _g(f, i, j):
    if id(f) not in _ST:
        mask(f)
    return float(_ST[id(f)][j][i])


def stop_price(f, i):
    return _g(f, i, 0)


def target_price(f, i, stop):
    return _g(f, i, 1)
