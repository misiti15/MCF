"""pod-cwt4-raschke-sma5-7bar-streak-first-cross-long - Exhausted drift: first 5-min close back above SMA5 after 7+
closes below it, quick snap target (LONG).

Source: Linda Raschke (CWT guest), Street Smarts / LBR trade-sheet rule 'ExtSig': >= 7 consecutive closes on one side
of the 5-period SMA, then the first close back across is a mean-reversion / exit signal. Taken from a third-party
TradingView 'Raschke Trade Sheet scanner' description.
URL: https://www.tradingview.com/script/8MVLfKu4-Raschke-Trade-Sheet-scanner/

VARIANT of the backlog VWAP 'N closes below VWAP then reclaim' family. Stated change: the line is a fast SMA5 (not
VWAP), the streak is 7+ bars, the target is a small snap-back toward the start of the drift (not trend continuation),
and it runs only in a quiet tape.

Rules (plain English), decision bar i (5-minute bars; SMA5 = mean of the last 5 session closes from 09:35, r24 cache):
  1. Streak: the 7 or more closes before bar i are all below their SMA5 (grid 7/9: the 7 arm is coded, pre-declared;
     a 9 arm was not run). The streak must start inside the frame (the close before it, the 'streak-start close', is
     known).
  2. Orderly drift: streak-start close - last streak close between 0.4 and 1.2 x atr_d, and no streak bar's range is
     > 1.5 x the 5-minute ATR (the frame's ATR14 `atrPct` is used for the source's ATR20; stated proxy).
  3. Quiet tape: rvol_day (cumulative volume 09:30..bar / its 20-session same-time mean) <= 1.2 and SPY's last-60-min
     range (12 bars of SPY 5m high/low) <= 0.35 x SPY daily ATR14 (as of D-1).
  4. Bar i is the first close back above SMA5. Bar close 10:30-15:00 ET.
  Entry: bar i close (= next-bar open). Stop (GEOM S): streak low - 0.05 x atr_d. Target: the nearer (above entry) of
  the 50% retrace (streak-start close - drift / 2) and session VWAP. Skip when target - entry < 3 x the round-trip
  cost (1c + 1 bps per side, entry x1.4 before 10:30). The source's 8-bar time stop is NOT supported by the scorer
  (it holds to stop / target / 15:55) - a stated deviation.
No tweak used. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt3_bars as C3  # noqa: E402
import _r31_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1500)
STREAK = 7
LAYERS = [">= 7 closes below SMA5 then first close above", "drift 0.4-1.2 ATR, no bar range > 1.5 ATR5",
          "rvol_day <= 1.2, SPY 60-min range <= 0.35 SPY ATR", "stop streak low - 0.05 ATR",
          "target nearer of 50% retrace / VWAP, >= 3x cost", "10:30-15:00 ET"]
_ST = {}


@numba.njit(cache=False)
def _k(b, e, tod, c, c24, s5, h, l, atr, atr5, vw, rvc, spyok, cost, nst, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 1, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            if not (c24[i] > s5[i]) or not (atr[i] > 0):
                continue
            cnt = 0
            j = i - 1
            while j >= i0 and c24[j] < s5[j]:
                cnt += 1
                j -= 1
            if cnt < nst or j < i0 or not (c24[j] == c24[j] and s5[j] == s5[j]):
                continue
            cs = c[j]
            drift = cs - c[i - 1]
            if drift < 0.4 * atr[i] or drift > 1.2 * atr[i]:
                continue
            bad = False
            lo = np.inf
            for q in range(j + 1, i):
                if h[q] - l[q] > 1.5 * atr5[i]:
                    bad = True
                lo = min(lo, l[q])
            if bad:
                continue
            if not (rvc[i] <= 1.2 and spyok[i]):
                continue
            t50 = cs - drift / 2.0
            t = np.inf
            if t50 > c[i]:
                t = t50
            if vw[i] > c[i] and vw[i] < t:
                t = vw[i]
            if t == np.inf or t - c[i] < 3.0 * cost[i]:
                continue
            sp = lo - 0.05 * atr[i]
            if sp >= c[i]:
                continue
            m[i] = True
            stop[i] = sp
            tgt[i] = t
    return m, stop, tgt


def _spy_r60():
    S = U.U.spy_tab()
    if "r60" not in S:
        g = S.groupby("date")
        S["r60"] = g["h"].transform(lambda x: x.rolling(12, min_periods=12).max()) - \
            g["l"].transform(lambda x: x.rolling(12, min_periods=12).min())
    return S


def compute(df):
    n = len(df)
    b = U.base(df)
    k = U.key(df)
    si = U.sess_ind(df)
    _spy_r60()
    sp = U.U.map_spy(df, ["r60", "spy_atr"])
    with np.errstate(invalid="ignore"):
        spyok = sp["r60"] <= 0.35 * sp["spy_atr"]
    atr5 = U.f(df, "atrPct") / 100 * b["c"]
    cost = C3.rt_cost(b["c"], b["tod"])
    bb, ee = U.segments(k)
    return _k(bb, ee, b["tod"], b["c"], si["c24"], si["s5"], b["h"], b["l"], b["atr"], atr5, b["vwap"], si["rvc"],
              np.asarray(spyok, np.bool_), cost, STREAK, WINDOW[0], WINDOW[1])


def mask(df):
    m, s, t = compute(df)
    _ST.clear()
    _ST[id(df)] = (s, t)
    return m


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
