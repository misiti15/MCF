"""t5_inside_bar — 5-minute inside-bar breakout with a VWAP / EMA trend filter.

Source: r/algotrading search snippet (post body unreadable; low credibility) — a mechanised hypothesis, not evidence.

Rules (5-min bars labelled by start time; a bar labelled HH:MM closes at the close of the 1-min bar HH:MM+4):
  mother bar M closes >= 09:50 (label >= 09:45); inside bar I = the next 5-min bar with
  high <= M.high, low >= M.low and range <= 0.5 x M.range. Decision at I's close, which must be <= 14:30.
  Signal bar_index = the last 1-min bar of I, so the earliest stop order works from 09:55 (>= 09:50 rule).
  Long: buy stop at I.high + $0.01, stop I.low; short: sell stop at I.low - $0.01, stop I.high.
  Order valid 2 five-min bars (10 one-min bars). Skip if R (entry - stop) < 0.05 x daily ATR.
  Target k x R from the entry price (k in 1, 1.5, 2). Optional time stop: 30 min if MFE < 0.5R.
  Trend filter on: long only if I.close > session VWAP and EMA9 > EMA21 of 5-min closes; short mirror.
  Trend filter off: both orders work as an OCO bracket — the signal function emits only the side whose
  level trades first within the 10 bars (an OCO is placeable live; if both trigger in the same 1-min bar the
  setup is skipped as ambiguous). EMAs use today's 5-min bars only (pandas ewm adjust=True; no prior-day warm-up),
  so before ~11:15 EMA21 is effectively a shorter average — say so if ported.
  Several setups per symbol-day allowed; the harness skips a signal while a trade on that symbol is open.

Grid (pre-declared, full factorial = 24): target {1, 1.5, 2}R x trend filter {on, off} x universe {top300, index
ETFs} x time stop {off, on}. Educational only — not financial advice.
"""
from __future__ import annotations

from itertools import product

import numpy as np

from mcf import features as F
from mcf.strategies.base import Signal

NAME = "t5_inside_bar"
ETFS = {"SPY", "QQQ", "IWM", "DIA"}
UNIVERSE = "top300"


def signals(day, variant: dict) -> list[Signal]:
    if variant.get("etf_only") and day.symbol not in ETFS:
        return []
    b = day.bars
    if len(b) < 60:
        return []
    mins = b.index.hour.to_numpy() * 60 + b.index.minute.to_numpy()
    o, h, l, c = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    vw = F.vwap(b).to_numpy(float)
    b5 = day.b5
    m5 = b5.index.hour.to_numpy() * 60 + b5.index.minute.to_numpy()
    h5, l5, c5 = b5["high"].to_numpy(float), b5["low"].to_numpy(float), b5["close"].to_numpy(float)
    e9 = b5["close"].ewm(span=9, adjust=True).mean().to_numpy(float)
    e21 = b5["close"].ewm(span=21, adjust=True).mean().to_numpy(float)
    out = []
    for i in range(1, len(b5)):
        mom, ins = i - 1, i
        if m5[mom] < 585 or m5[ins] != m5[mom] + 5:        # mother closes >= 09:50; consecutive bars
            continue
        if m5[ins] + 5 > 870:                               # inside bar closes <= 14:30
            break
        mr = h5[mom] - l5[mom]
        if mr <= 0 or not (h5[ins] <= h5[mom] and l5[ins] >= l5[mom] and (h5[ins] - l5[ins]) <= 0.5 * mr):
            continue
        idx = np.nonzero(mins == m5[ins] + 4)[0]            # last 1-min bar of the inside bar
        if not len(idx):
            continue
        k = int(idx[0])
        if mins[k] < 589:
            continue
        hi, lo = h5[ins], l5[ins]
        r = hi - lo + 0.01
        if r < 0.05 * day.atr:
            continue
        if variant["trend"]:
            if c[k] > vw[k] and e9[ins] > e21[ins]:
                side = 1
            elif c[k] < vw[k] and e9[ins] < e21[ins]:
                side = -1
            else:
                continue
        else:                                               # OCO bracket: first side to trade
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
        stop = lo if side > 0 else hi
        sig = Signal(day.symbol, NAME, side, k, stop, entry + side * variant["target_r"] * r,
                     entry_type="stop", entry_price=entry, entry_valid_bars=10)
        if variant.get("time_stop"):
            sig.time_stop_min, sig.time_stop_min_r = 30, 0.5
        out.append(sig)
    return out


VARIANTS = {}
for tr, trend, etf, ts in product((1.0, 1.5, 2.0), (True, False), (False, True), (False, True)):
    name = f"t{tr}" + ("_trend" if trend else "_oco") + ("_etf" if etf else "") + ("_ts30" if ts else "")
    VARIANTS[name] = {"target_r": tr, "trend": trend, "etf_only": etf, "time_stop": ts}

FINALISTS: list[str] = []
BASELINE = {"stop_atr": 0.08, "target_atr": 0.12}
