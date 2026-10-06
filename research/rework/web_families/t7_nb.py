"""t7_nb - rule-18 rework of research/reddit_bt/t7_noise_band (Zarattini-Aziz-Barbon noise-area momentum),
pooled over SPY + QQQ + IWM. Educational only - not financial advice. A hypothesis under test, not evidence.

Bands and checks exactly as the original module (sigma = mean |close/open - 1| at the same minute over the N prior
sessions; upper = max(open, prev close) x (1 + sigma), lower = min(...) x (1 - sigma); checks every 30 or 60 min
from 10:00; entry at the next open; re-entries allowed). Exits:
  check        intrabar stop at the band/VWAP (floored at 0.05 ATR) + exit at the next open after the first later
               check whose close is beyond the then-current band/VWAP stop
  trail1       band/VWAP stop, then trail 1R behind the best price once +1R
  trail05      band/VWAP stop, then trail 0.5R once +0.5R
  faithfulX    band/VWAP stop evaluated ONLY at checks (exit next open), intrabar disaster stop X x daily ATR
               (X = 0.3, 0.5, 0.75); R unit = X ATR
side: both | long.
"""
from __future__ import annotations

from itertools import product

import numpy as np

from mcf import features as F
from mcf.strategies.base import Signal

from research.rework.web_families import lib as L

NAME = "t7_nb"
UNIVERSE = ["SPY", "QQQ", "IWM"]
BASE = {"interval": 30, "lookback": 14, "exit": "faithful0.5", "side": "both"}
STEPS = {"lookback": [7, 10, 14, 20, 30]}


def _prior(day, n):
    h = L.C._hist("data/cache", day.symbol)
    if h is None or day.date not in h[0]:
        return None
    prior = sorted(d for d in h[0] if d < day.date)[-n:]
    return [h[0][d] for d in prior] if len(prior) == n else None


def _move_at(g, minute):
    mins = g.index.hour * 60 + g.index.minute
    sel = np.nonzero(mins == minute - 1)[0]
    if not len(sel):
        return np.nan
    return abs(float(g["close"].iloc[sel[0]]) / float(g["open"].iloc[0]) - 1)


def signals(day, v) -> list[Signal]:
    b = day.bars
    if len(b) < 300:
        return []
    prior = _prior(day, v["lookback"])
    if prior is None:
        return []
    mins = b.index.hour.to_numpy() * 60 + b.index.minute.to_numpy()
    c = b["close"].to_numpy(float)
    vw = F.vwap(b).to_numpy(float)
    op = float(b["open"].iloc[0])
    hi_ref, lo_ref = max(op, day.prev_close), min(op, day.prev_close)
    step = v["interval"]
    checks = list(range(600, 930 + 1, step)) if step == 30 else list(range(600, 900 + 1, 60))
    lv = {}
    for m in checks:
        sel = np.nonzero(mins == m - 1)[0]
        if not len(sel):
            continue
        sig_m = np.nanmean([_move_at(g, m) for g in prior])
        if not np.isfinite(sig_m):
            continue
        k = int(sel[0])
        lv[m] = (k, c[k], hi_ref * (1 + sig_m), lo_ref * (1 - sig_m), vw[k])
    out = []
    floor = 0.05 * day.atr
    ex = v["exit"]
    for m, (k, px, up, lo, vv) in lv.items():
        side = 1 if px > up else -1 if px < lo else 0
        if side == 0 or k + 1 >= len(b) or (v["side"] == "long" and side < 0):
            continue
        stop = max(up, vv) if side > 0 else min(lo, vv)
        if side * (px - stop) <= 0:
            continue
        if side * (px - stop) < floor:
            stop = px - side * floor
        if ex.startswith("faithful"):
            stop = px - side * float(ex[8:]) * day.atr
        sig = Signal(day.symbol, NAME, side, k, stop, None)
        if ex == "check" or ex.startswith("faithful"):
            for m2, (k2, px2, up2, lo2, v2) in lv.items():
                if m2 <= m:
                    continue
                st2 = max(up2, v2) if side > 0 else min(lo2, v2)
                if side * (px2 - st2) <= 0:
                    sig.exit_by = b.index[k2 + 1].time() if k2 + 1 < len(b) else None
                    break
        elif ex == "trail1":
            sig.trail_r, sig.trail_after_r = 1.0, 1.0
        elif ex == "trail05":
            sig.trail_r, sig.trail_after_r = 0.5, 0.5
        out.append(sig)
    return out


def name(v):
    return f"t7[i{v['interval']}_n{v['lookback']}_{v['exit']}" + ("_long" if v["side"] == "long" else "") + "]"


EXITS = ("check", "trail1", "trail05", "faithful0.3", "faithful0.5", "faithful0.75")
GRID = [dict(BASE, interval=i, lookback=n, exit=e) for i, n, e in product((30, 60), (10, 14, 20), EXITS)]
GRID += [dict(BASE, interval=30, lookback=14, exit=e, side="long") for e in EXITS]


def stage2(res, grid):
    return []
