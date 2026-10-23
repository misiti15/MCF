"""pod-of3-single-print-zone-pm-defense-long - Morning single-print zone (non-overlapping 30-min brackets) defended on
the afternoon retest (LONG).

Source: Market Profile single prints / unfinished business (LuxAlgo auction-failure and responsive-vs-initiative
pages; Dalton, Mind Over Markets) and Jigsaw / Peter Davies order-flow webinar topics ('liquidity vacuums occurrence
and opportunity', 'second entries', futures.io thread).
URL: https://futures.io/trading_member/27102-veritech6.html

VARIANT of pod-of-defended-origin-retest (zone = one impulse bar's low) and the opposite logic of
pod-of-liquidity-vacuum-fill (fills the gap). Stated change: the zone is a TPO single-print gap between two
consecutive 30-min brackets (bracket N+1 low > bracket N high), formed 10:00-12:30 on an up move, and the trade is its
defence on the first afternoon retest.

Brackets: bracket 0 = 09:30-10:00 (its high / low = the running HOD / LOD on the 10:00 bar, which include the
09:30-09:45 bars the frame does not carry); bracket j >= 1 = bars closing in (10:00 + 30(j-1), 10:00 + 30j], so
bracket 5 = 12:00-12:30. A bracket counts only once its last bar has closed.
Rules (plain English, LONG):
  1. Zone SP = [bracket N high, bracket N+1 low] for consecutive brackets N = 0..4 (N+1 ends by 12:30) with bracket
     N+1 low > bracket N high and width >= 0.08 x atr_d. If several exist, the most recent (highest N) is used.
  2. No 5-min close inside (or below) SP from the end of bracket N+1 up to the bar before the decision bar.
  3. Decision bar closes 12:30-14:45 and is the FIRST bar at or after 12:30 whose low reaches SP top (+1c); its low
     is in the upper half of SP or touches the top (low >= SP midpoint), it closes above SP top, lower_wick >= 0.3,
     volumeRatio <= 1.1.
  4. Close > session VWAP or VWAP <= SP top (VWAP inside / below the zone); breadth >= 0.45.
  Entry: that bar's close. Stop (GEOM S): SP bottom - 0.05 x atr_d. Target: the running high of day; it must be
  >= 0.25 x atr_d above the entry, else skip. Flat 15:55.
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1230, 1445)
CONTEXT = ["breadth"]
LAYERS = ["single-print gap between 30-min brackets N, N+1 (ends by 12:30), width >= 0.08 ATR",
          "no close inside SP since formation", "first touch of SP top at/after 12:30, low >= SP mid, close > SP top",
          "lower_wick >= 0.3, volumeRatio <= 1.1", "close > VWAP or VWAP <= SP top; breadth >= 0.45",
          "stop SP bottom - 0.05 ATR, target HOD (>= 0.25 ATR away)"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt3_bars as CB  # noqa: E402

_ST = {}


def _stash(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash(f, i, 0)


def target_price(f, i, stop):
    return _stash(f, i, 1)


def _minutes(tod):
    tod = np.asarray(tod, np.int64)
    return (tod // 100) * 60 + tod % 100 - 570


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n or "breadth" not in df:
        return z
    b = CB.base(df)
    k = CB.key(df)
    tod, c, h, l, atr = b["tod"], b["c"], b["h"], b["l"], b["atr"]
    mn = _minutes(tod)
    bidx = (mn - 1) // 30                                    # bracket of the bar
    ng = int(k.max()) + 1
    NB = 6
    BH = np.full((ng, NB), np.nan)
    BL = np.full((ng, NB), np.nan)
    hod0 = CB.at_tod(b["hod"], k, tod, 1000)
    lod0 = CB.at_tod(b["lod"], k, tod, 1000)
    st = CB.start(k)
    BH[k[st], 0] = hod0[st]
    BL[k[st], 0] = lod0[st]
    sel = (bidx >= 1) & (bidx < NB)
    t = pd.DataFrame({"k": k[sel], "j": bidx[sel], "h": h[sel], "l": l[sel]})
    cnt = t.groupby(["k", "j"]).size().reset_index(name="n")
    a = t.groupby(["k", "j"]).agg(h=("h", "max"), l=("l", "min")).reset_index()
    a = a[cnt["n"].to_numpy() == 6]                          # only full brackets (6 bars)
    BH[a["k"].to_numpy(), a["j"].to_numpy()] = a["h"].to_numpy()
    BL[a["k"].to_numpy(), a["j"].to_numpy()] = a["l"].to_numpy()
    atr_day = np.full(ng, np.nan)
    atr_day[k[st]] = atr[st]
    top = np.full(ng, np.nan)
    bot = np.full(ng, np.nan)
    tend = np.full(ng, np.nan)
    with np.errstate(invalid="ignore"):
        for N in range(0, NB - 1):                           # (1) later N overwrites -> most recent
            ok = (BL[:, N + 1] > BH[:, N]) & ((BL[:, N + 1] - BH[:, N]) >= 0.08 * atr_day)
            top = np.where(ok, BL[:, N + 1], top)
            bot = np.where(ok, BH[:, N], bot)
            e = 600 + 30 * (N + 1)                           # minutes since 00:00 at bracket N+1 end
            tend = np.where(ok, (e // 60) * 100 + e % 60, tend)
    T, B, TE = top[k], bot[k], tend[k]
    seg = np.cumsum(st) - 1
    with np.errstate(invalid="ignore"):
        after = tod > TE
        bad = (after & (c <= T)).astype(float)               # (2) close inside / below SP
        badprev = CB.lag(pd.Series(bad).groupby(seg).cummax().to_numpy(float), k, 1)
        badprev = np.where(np.isnan(badprev), 0.0, badprev)
        touch = after & (tod >= 1230) & (l <= T + 0.01)
        ntouch = pd.Series(touch.astype(float)).groupby(seg).cumsum().to_numpy(float)
        mid = 0.5 * (T + B)
        m = np.isfinite(T) & (badprev == 0) & touch & (ntouch == 1)                  # (3) first PM retest
        m &= (l >= mid) & (c > T)
        m &= (CB.f(df, "lower_wick") >= 0.3) & (CB.f(df, "volumeRatio") <= 1.1)
        m &= (c > b["vwap"]) | (b["vwap"] <= T)                                     # (4)
        m &= CB.f(df, "breadth") >= 0.45
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop[:] = B - 0.05 * atr
        tgt[:] = b["hod"]
        m &= (tgt >= c + 0.25 * atr) & (stop < c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
