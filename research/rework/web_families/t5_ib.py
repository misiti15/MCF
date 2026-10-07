"""t5_ib - rule-18 rework of research/reddit_bt/t5_inside_bar (5-min inside-bar breakout). Educational only - not
financial advice. A hypothesis under test, not evidence.

Original rules (mother bar closes >= 09:50, inside bar = next 5-min bar inside the mother with range <= 0.5 x mother,
decision at the inside-bar close <= 14:30, stop order at I.high + 1c / I.low - 1c valid 10 one-min bars, trend
filter VWAP + EMA9/21 of today's 5-min closes or OCO), with the rework knobs:
  mm    mother-bar range >= mm x daily ATR (larger mother bars only)
  f     ATR-floored stop: stop distance from the entry = max(inside range + 1c, f x daily ATR)
  tr    target in R from the entry
  trend True (VWAP + EMA filter) / False (OCO: first side to trade; both in one bar = skip)
  ema   EMA lengths of the trend filter (default 9/21)
"""
from __future__ import annotations

from itertools import product

import numpy as np

from mcf import features as F
from mcf.strategies.base import Signal

NAME = "t5_ib"
UNIVERSE = "top300"
BASE = {"mm": 0.25, "f": 0.15, "tr": 1.5, "trend": True, "ema": (9, 21)}
STEPS = {"mm": [0.1, 0.15, 0.25, 0.35, 0.5], "f": [0.05, 0.1, 0.15, 0.25, 0.35], "tr": [0.75, 1.0, 1.5, 2.0, 3.0]}


def signals(day, v) -> list[Signal]:
    b = day.bars
    if len(b) < 60:
        return []
    mins = b.index.hour.to_numpy() * 60 + b.index.minute.to_numpy()
    h, l, c = (b[k].to_numpy(float) for k in ("high", "low", "close"))
    vw = F.vwap(b).to_numpy(float)
    b5 = day.b5
    m5 = b5.index.hour.to_numpy() * 60 + b5.index.minute.to_numpy()
    h5, l5 = b5["high"].to_numpy(float), b5["low"].to_numpy(float)
    ef, es = v.get("ema", (9, 21))
    e9 = b5["close"].ewm(span=ef, adjust=True).mean().to_numpy(float)
    e21 = b5["close"].ewm(span=es, adjust=True).mean().to_numpy(float)
    out = []
    for i in range(1, len(b5)):
        mom, ins = i - 1, i
        if m5[mom] < 585 or m5[ins] != m5[mom] + 5:
            continue
        if m5[ins] + 5 > 870:
            break
        mr = h5[mom] - l5[mom]
        if mr <= 0 or mr < v["mm"] * day.atr:
            continue
        if not (h5[ins] <= h5[mom] and l5[ins] >= l5[mom] and (h5[ins] - l5[ins]) <= 0.5 * mr):
            continue
        idx = np.nonzero(mins == m5[ins] + 4)[0]
        if not len(idx):
            continue
        k = int(idx[0])
        if mins[k] < 589:
            continue
        hi, lo = h5[ins], l5[ins]
        r = max(hi - lo + 0.01, v["f"] * day.atr)
        if v["trend"]:
            if c[k] > vw[k] and e9[ins] > e21[ins]:
                side = 1
            elif c[k] < vw[k] and e9[ins] < e21[ins]:
                side = -1
            else:
                continue
        else:
            side = 0
            for j in range(k + 1, min(len(b), k + 11)):
                up, dn = h[j] >= hi + 0.01, l[j] <= lo - 0.01
                if up and dn:
                    break
                if up or dn:
                    side = 1 if up else -1
                    break
            if side == 0:
                continue
        entry = hi + 0.01 if side > 0 else lo - 0.01
        out.append(Signal(day.symbol, NAME, side, k, entry - side * r, entry + side * v["tr"] * r,
                          entry_type="stop", entry_price=entry, entry_valid_bars=10))
    return out


def name(v):
    e = "" if tuple(v.get("ema", (9, 21))) == (9, 21) else f"_ema{v['ema'][0]}-{v['ema'][1]}"
    return f"t5[mm{v['mm']}_f{v['f']}_t{v['tr']}_" + ("trend" if v["trend"] else "oco") + e + "]"


GRID = [dict(BASE, mm=a, f=f, tr=t, trend=tt) for a, f, t, tt in
        product((0.15, 0.25, 0.35), (0.1, 0.15, 0.25), (1.0, 1.5, 2.0), (True, False))]


def stage2(res, grid):
    return []
