"""t2_orb15 — 15-minute opening-range breakout with a 5-minute close trigger.

Source: tradethatswing blog (futures; low credibility), mechanised from a snippet — a hypothesis, not evidence.
OR = high/low of the 09:30-09:44 1-min bars (09:30-09:45). Trigger: the first 5-min bar that closes at or after
09:50 with close > OR_high (long) or < OR_low (short); market entry at the next 1-min bar open. One trade per
symbol per day; no trigger bar closing after 12:00. Stop = opposite OR side (or OR midpoint); target = breakout
side +/- k x OR width (from the OR edge, not the fill); otherwise flat 15:55.

Timing: 5-min bars are labelled by start time; the bar labelled 09:45 covers 09:45-09:49 and closes at the close of
the 1-min bar starting 09:49, so its signal bar_index is that 1-min bar and the fill is the 09:50 open (rule:
entries >= 09:50). Live: evaluate at each 5-min boundary using only completed bars.

Grid (pre-declared, full factorial = 32): target {0.5, 1.0} x OR width; stop {opposite side, midpoint};
OR-width filter {none, 0.25..1.0 x daily ATR}; time stop {none, 60 min if MFE < 0.25R}; universe {top300, index ETFs}.
Index-ETF variants return no signals for other symbols, so they run correctly on any universe.
Educational only — not financial advice.
"""
from __future__ import annotations

from itertools import product

import numpy as np

from mcf.strategies.base import Signal

NAME = "t2_orb15"
ETFS = {"SPY", "QQQ", "IWM", "DIA"}
UNIVERSE = "top300"


def signals(day, variant: dict) -> list[Signal]:
    if variant.get("etf_only") and day.symbol not in ETFS:
        return []
    b = day.bars
    if len(b) < 30:
        return []
    mins = b.index.hour.to_numpy() * 60 + b.index.minute.to_numpy()
    orm = (mins >= 570) & (mins < 585)            # 09:30..09:44 bars
    if orm.sum() < 10:
        return []
    hi = float(b["high"].to_numpy()[orm].max())
    lo = float(b["low"].to_numpy()[orm].min())
    w = hi - lo
    if w <= 0:
        return []
    f = variant.get("width_filter")
    if f and not (f[0] * day.atr <= w <= f[1] * day.atr):
        return []
    close = b["close"].to_numpy()
    # last 1-min bar of each 5-min bucket that closes in [09:50, 12:00]: bucket start 09:45..11:55
    bucket = mins // 5 * 5
    for bs in range(585, 720, 5):
        idx = np.nonzero(bucket == bs)[0]
        if not len(idx):
            continue
        k = int(idx[-1])
        if mins[k] < 589:                         # partial bucket: never signal before the 09:49 bar
            continue
        c = close[k]
        side = 1 if c > hi else -1 if c < lo else 0
        if side == 0:
            continue
        if k + 1 >= len(b):
            return []
        edge = hi if side > 0 else lo
        stop = (lo if side > 0 else hi) if variant.get("stop", "opp") == "opp" else (hi + lo) / 2
        target = edge + side * variant["target_k"] * w
        sig = Signal(day.symbol, NAME, side, k, stop, target)
        if variant.get("time_stop"):
            sig.time_stop_min, sig.time_stop_min_r = 60, 0.25
        return [sig]
    return []


VARIANTS = {}
for tk, st, wf, ts, etf in product((0.5, 1.0), ("opp", "mid"), (None, (0.25, 1.0)), (False, True), (False, True)):
    name = (f"t{tk}_{st}" + ("_wf" if wf else "") + ("_ts60" if ts else "") + ("_etf" if etf else ""))
    VARIANTS[name] = {"target_k": tk, "stop": st, "width_filter": wf, "time_stop": ts, "etf_only": etf}

FINALISTS: list[str] = []
# geometry: OR width on liquid names ~0.4 x daily ATR -> stop ~0.4 ATR, target ~0.2 ATR beyond the edge (~0.3 from fill)
BASELINE = {"stop_atr": 0.4, "target_atr": 0.3}
