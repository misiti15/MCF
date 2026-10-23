"""pod-shannon-vwap-2d-pinch-lunch-break-long - Lunch pinch of the session VWAP and the 2-day VWAP, afternoon upside
break (quiet-day LONG).

Source: Brian Shannon 'pinch / hand-off' AVWAP concept (LuxAlgo 'VWAP pinch'; TradingView 'Anchored VWAP Pinch &
Handoff Intervals and Signals'); Multi-Day Rolling VWAP (Shannon book ideas).
URL: https://th.tradingview.com/script/VYu6A3GB-Anchored-VWAP-Pinch-Handoff-Intervals-and-Signals/

VARIANT of bdi-vid-pinch (quarter-open vs gap-day AVWAP pinch, failed). Stated change: the pinched lines are the
session VWAP and the 2-day VWAP, intraday-only and long-only, and the compression must form during lunch. Distinct
from pod-tosind-lunch-compression-index-break and pod-carter-pm-midrange-squeeze-long (price-range compression, not
VWAP-line convergence).
Rules (plain English):
  1. Pinch: for every 5-minute bar 11:30-13:30 (bar closes 11:35..13:30), |session VWAP - VWAP2D| <= 0.15 x atr_d.
  2. The 11:30-13:30 high-low box <= 0.5 x atr_d, and inside it price touched both sides of the pinched lines (some
     bar high >= max(VWAP, VWAP2D) and some bar low <= min(VWAP, VWAP2D), each at that bar).
  3. Close > VWAP5D and VWAP5D is rising (above its value as of D-1's close).
  4. SPY's 11:30-13:30 range <= 0.4 x SPY atr_d (quiet tape).
  5. Trigger: after 13:30, a 5-minute close above max(box high, session VWAP, VWAP2D) with volumeRatio >= 1.3.
  Entry: trigger close, 13:35-15:00 ET. Stop (GEOM S): max(box low, min(VWAP, VWAP2D) - 0.15 x atr_d).
  Target: box high + 1 x box height, else flat 15:55.
Harness approximations (pre-declared): VWAP2D is anchored at D-1's open (D-1's whole session + today so far) and
VWAP5D at D-4's open; prior sessions enter as daily typical price x daily volume (lib.daily(), completed days), today
as session VWAP x cumulative 5-minute volume (_r24_bars cache). 'VWAP5D rising over 63 bars' is read as today's
VWAP5D > the 5-session VWAP as of D-1's close (D-5..D-1), which is roughly 50-70 bars back at 13:35-15:00. No tweak
used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r27_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1335, 1500)
CONTEXT = []
LAYERS = ["|VWAP - VWAP2D| <= 0.15 ATR on every bar 11:30-13:30", "lunch box <= 0.5 ATR, both sides of the lines touched",
          "close > VWAP5D, VWAP5D rising", "SPY 11:30-13:30 range <= 0.4 SPY ATR",
          "close > max(box high, VWAP, VWAP2D), volumeRatio >= 1.3", "13:35-15:00",
          "stop max(box low, min line - 0.15 ATR), target box high + box height"]
_ST = {}


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


@numba.njit(cache=False)
def _scan(st, tod, h, l, c, vw, v2, atr, vr):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    i = 0
    while i < n:
        e = i + 1
        while e < n and not st[e]:
            e += 1
        cnt = 0
        ok = True
        bh = -1e300
        bl = 1e300
        tu = False
        td = False
        for t in range(i, e):
            if tod[t] >= 1135 and tod[t] <= 1330:
                cnt += 1
                if not (abs(vw[t] - v2[t]) <= 0.15 * atr[t]):
                    ok = False
                bh = max(bh, h[t])
                bl = min(bl, l[t])
                if h[t] >= max(vw[t], v2[t]):
                    tu = True
                if l[t] <= min(vw[t], v2[t]):
                    td = True
        if ok and cnt == 24 and tu and td:
            for t in range(i, e):
                if tod[t] < 1335:
                    continue
                a = atr[t]
                if not (bh - bl <= 0.5 * a):
                    break
                if c[t] > max(bh, max(vw[t], v2[t])) and vr[t] >= 1.3:
                    m[t] = True
                    stop[t] = max(bl, min(vw[t], v2[t]) - 0.15 * a)
                    tgt[t] = bh + (bh - bl)
        i = e
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n:
        return np.zeros(0, bool)
    k = U.key(df)
    st = U.start(k)
    b = U.base(df)
    B = U.vol_bars(df)
    if B is None:
        return np.zeros(n, bool)
    cv = U.map_bars(df, B, ["cv"])["cv"]
    D = U.map_daily(df, k, ["tpv1", "v1", "s41", "v41", "s51", "v51"])
    S = U.map_spy(df, ["h", "l", "spy_atr"])
    vw, c, tod, atr = b["vwap"], b["c"], b["tod"], b["atr"]
    with np.errstate(invalid="ignore", divide="ignore"):
        v2 = (D["tpv1"] + vw * cv) / (D["v1"] + cv)
        v5 = (D["s41"] + vw * cv) / (D["v41"] + cv)
        v5p = D["s51"] / D["v51"]
        # SPY 11:30-13:30 range (date-level, from bars 11:35..13:30; used only on rows >= 13:35)
        dkey = pd.factorize(pd.Series(df["date"].to_numpy()).astype(str))[0]
        sh = np.where((tod >= 1135) & (tod <= 1330), S["h"], np.nan)
        sl = np.where((tod >= 1135) & (tod <= 1330), S["l"], np.nan)
        gh = pd.Series(sh).groupby(dkey).transform("max").to_numpy(float)
        gl = pd.Series(sl).groupby(dkey).transform("min").to_numpy(float)
        quiet = (gh - gl) <= 0.4 * S["spy_atr"]
        m, stop, tgt = _scan(st, tod, b["h"], b["l"], c, vw, v2, atr, U.f(df, "volumeRatio"))
        m &= (c > v5) & (v5 > v5p) & quiet
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        m &= c > stop
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), bool)
