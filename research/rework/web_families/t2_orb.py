"""t2_orb - rule-18 rework of research/reddit_bt/t2_orb15 (opening-range breakout). Educational only - not
financial advice. A hypothesis under test, not evidence.

OR = high/low of the first `orl` minutes (bars 09:30 .. 09:30+orl-1). Trigger (first qualifying bar, one trade per
symbol per day, decision bar closing in [max(OR end, 09:50), 12:00]):
  c5     a completed 5-min bar (buckets from the OR end) closes beyond the OR (original rule)
  c1     a 1-min bar closes beyond the OR
  c1v / c5v  same, and the trigger bar volume >= 1.5 x the mean volume of up to 10 previous bars of the same size
         (min 3)
Market entry at the next 1-min open. Stop = opposite OR side ("opp") or OR midpoint ("mid"); target = breakout edge
+/- tk x OR width. Optional OR-width filter (wf: 0.25..1.0 x daily ATR) and 60-min time stop if MFE < 0.25R.
"""
from __future__ import annotations

from itertools import product

import numpy as np

from mcf.strategies.base import Signal

NAME = "t2_orb"
UNIVERSE = "top300"
BASE = {"orl": 15, "trig": "c5", "tk": 0.5, "stop": "opp", "wf": False, "ts": False}
STEPS = {"orl": [15, 20, 30], "tk": [0.5, 1.0, 1.5]}


def signals(day, v) -> list[Signal]:
    b = day.bars
    if len(b) < 40:
        return []
    mins = b.index.hour.to_numpy() * 60 + b.index.minute.to_numpy()
    end = 570 + v["orl"]
    orm = (mins >= 570) & (mins < end)
    if orm.sum() < 0.66 * v["orl"]:
        return []
    hi = float(b["high"].to_numpy()[orm].max())
    lo = float(b["low"].to_numpy()[orm].min())
    w = hi - lo
    if w <= 0:
        return []
    if v.get("wf") and not (0.25 * day.atr <= w <= 1.0 * day.atr):
        return []
    close = b["close"].to_numpy(float)
    vol = b["volume"].to_numpy(float)
    trig = v["trig"]
    cand = []   # (k, bar volume, prior same-size volumes)
    if trig.startswith("c5"):
        bucket = (mins - end) // 5
        vols5 = []
        for bs in range(0, (720 - end) // 5):
            idx = np.nonzero(bucket == bs)[0]
            if not len(idx):
                continue
            k = int(idx[-1])
            bv = float(vol[idx].sum())
            if mins[k] == end + bs * 5 + 4 and mins[k] >= 589:
                cand.append((k, bv, list(vols5[-10:])))
            vols5.append(bv)
        if not cand:
            return []
        # include OR 5-min buckets as prior volume for the first breakout buckets
        orb = [float(vol[(mins >= s) & (mins < s + 5)].sum()) for s in range(570, end, 5)]
        cand = [(k, bv, (orb + pv)[-10:]) for k, bv, pv in cand]
    else:
        for k in np.nonzero((mins >= max(end, 589)) & (mins <= 719))[0]:
            cand.append((int(k), float(vol[k]), list(vol[max(0, k - 10):k])))
    for k, bv, pv in cand:
        c = close[k]
        side = 1 if c > hi else -1 if c < lo else 0
        if side == 0:
            continue
        if trig.endswith("v"):
            if len(pv) < 3 or not bv >= 1.5 * float(np.mean(pv)):
                continue
        if k + 1 >= len(b):
            return []
        edge = hi if side > 0 else lo
        stop = (lo if side > 0 else hi) if v["stop"] == "opp" else (hi + lo) / 2
        sig = Signal(day.symbol, NAME, side, k, stop, edge + side * v["tk"] * w)
        if v.get("ts"):
            sig.time_stop_min, sig.time_stop_min_r = 60, 0.25
        return [sig]
    return []


def name(v):
    return f"t2[or{v['orl']}_{v['trig']}_t{v['tk']}_{v['stop']}" + ("_wf" if v["wf"] else "") + ("_ts60" if v["ts"] else "") + "]"


GRID = [dict(BASE, orl=o, trig=tg, tk=tk, stop=st) for o, tg, tk, st in
        product((15, 20, 30), ("c5", "c1", "c1v", "c5v"), (0.5, 1.0), ("opp", "mid"))]


def stage2(res, grid):
    top = sorted(grid, key=lambda v: -res[name(v)]["train"].get("exp_r", -9))[:3]
    return [dict(v, wf=True) for v in top] + [dict(v, ts=True) for v in top]
