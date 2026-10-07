"""t3_rvol - rule-18 rework of research/reddit_bt/t3_rvol_cons (relative-volume breakout from a 5-min
consolidation). Educational only - not financial advice. A hypothesis under test, not evidence.

Same rules as the original (decision on a completed 5-min bar, entry next 1-min open; consolidation = prior N 5-min
bars with range <= k x daily ATR; breakout bar volume >= m x mean of up to 20 prior 5-min bars; close in the top
(bottom) 40% of the bar; close beyond the session VWAP unless vwap=False; stop = tighter of the opposite
consolidation side and 0.25 ATR; 1R target). Windows (decision close time): am 10:00-11:30, mid 11:30-13:30,
pm 13:00-15:00. One signal per symbol per day.
"""
from __future__ import annotations

from datetime import time, timedelta
from itertools import product

import numpy as np

from mcf import features as F
from mcf.strategies.base import Signal

NAME = "t3_rvol"
UNIVERSE = "top300"
WINDOWS = {"am": (time(10, 0), time(11, 30)), "mid": (time(11, 30), time(13, 30)), "pm": (time(13, 0), time(15, 0))}
BASE = {"m": 2, "N": 12, "k": 0.25, "side": "short", "win": "am", "vwap": True}
STEPS = {"N": [3, 6, 9, 12, 15], "k": [0.15, 0.2, 0.25, 0.35, 0.5], "m": [1.5, 2, 3]}
_CACHE: dict = {}


def signals(day, v) -> list[Signal]:
    bars = day.bars
    if len(bars) < 60 or not np.isfinite(day.atr) or day.atr <= 0:
        return []
    N, k, m = v["N"], v["k"], v["m"]
    w0, w1 = WINDOWS[v["win"]]
    side = 1 if v["side"] == "long" else -1
    key = (day.symbol, day.date, day.atr)
    if _CACHE.get("key") != key:
        b5 = day.b5
        _CACHE.clear()
        _CACHE.update(key=key, vw=F.vwap(bars).to_numpy(), pos={ts: i for i, ts in enumerate(bars.index)},
                      arr=tuple(b5[x].to_numpy(float) for x in ("open", "high", "low", "close", "volume")),
                      starts=b5.index)
    vw, pos, starts = _CACHE["vw"], _CACHE["pos"], _CACHE["starts"]
    idx = bars.index
    o, h, l, c, vol = _CACHE["arr"]
    for j in range(max(N, 6), len(starts)):
        st = starts[j]
        close_t = (st + timedelta(minutes=5)).time()
        if close_t < w0:
            continue
        if close_t > w1:
            break
        bi = pos.get(st + timedelta(minutes=4))
        if bi is None or bi + 1 >= len(bars) or idx[bi].time() < time(9, 49):
            continue
        ch, cl = h[j - N:j].max(), l[j - N:j].min()
        if ch - cl > k * day.atr:
            continue
        avgv = vol[max(0, j - 20):j].mean()
        if not avgv > 0 or vol[j] < m * avgv:
            continue
        rng = h[j] - l[j]
        if rng <= 0:
            continue
        pct = (c[j] - l[j]) / rng
        px = c[j]
        if side > 0:
            if not (px > ch and pct >= 0.6 and (px > vw[bi] or not v["vwap"])):
                continue
            stop = max(cl, px - 0.25 * day.atr)
        else:
            if not (px < cl and pct <= 0.4 and (px < vw[bi] or not v["vwap"])):
                continue
            stop = min(ch, px + 0.25 * day.atr)
        risk = abs(px - stop)
        if risk <= 0:
            continue
        return [Signal(day.symbol, NAME, side, bi, stop, px + side * risk)]
    return []


def name(v):
    return f"t3[m{v['m']}_N{v['N']}_k{v['k']}_{v['win']}_{v['side']}" + ("" if v["vwap"] else "_novwap") + "]"


GRID = [dict(BASE, side=s, N=n, k=k, win=w) for s, n, k, w in
        product(("long", "short"), (6, 9, 12), (0.2, 0.25, 0.35), ("am", "mid", "pm"))]


def stage2(res, grid):
    ok = [v for v in grid if res[name(v)]["train"].get("n", 0) >= 30]
    top = sorted(ok, key=lambda v: -res[name(v)]["train"].get("exp_r", -9))[:6]
    return [dict(v, vwap=False) for v in top]
