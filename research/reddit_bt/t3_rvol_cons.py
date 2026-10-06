"""t3_rvol_cons - relative-volume breakout from a 5-minute consolidation (tradingsim; low credibility).

Hypothesis from a web sweep (Reddit bodies unreadable from this server) - a hypothesis, not evidence.
Educational only - not financial advice.

Decision on a completed 5-min bar (labelled by start time; it closes at the 1-min bar starting at start+4,
which is the Signal bar_index; entry = next 1-min bar open = start+5). Decision close time must be inside the window.
  consolidation = prior N completed 5-min bars, range <= k x daily ATR
  long : close > consolidation high, volume >= m x mean volume of up to 20 prior 5-min bars of today (min 6),
         close in top 40% of the bar's range, close > session VWAP (as of that bar's close). Short = mirror.
  stop : tighter of opposite consolidation side and 0.25 ATR from the signal close.
Exits: the posted exit (first counter-trend 5-min bar with above-average volume) is path dependent and is NOT
implemented; it is approximated with fixed exits: "1R" (+1R/-1R), "2R", "ts30" (2R target + exit after 30 min if
MFE < 0.3R), "hold45" (no target, time exit 45 min after the signal).
One signal per symbol per day (first qualifying bar).
"""
from __future__ import annotations

from datetime import datetime, time, timedelta

import numpy as np

from mcf import features as F
from mcf.strategies.base import Signal

NAME = "t3_rvol_cons"
UNIVERSE = "top300"
WINDOWS = {"am": (time(10, 0), time(11, 30)), "pm": (time(13, 0), time(15, 0))}


def _variant(m, N, k, side, win, exit_="1R"):
    return {"m": m, "N": N, "k": k, "side": side, "win": win, "exit": exit_}


# Stage 1 (pre-declared): m x N x k x window x side with the 1R exit = 32 configs.
VARIANTS = {}
for _m in (2, 3):
    for _N in (6, 12):
        for _k in (0.25, 0.5):
            for _w in ("am", "pm"):
                for _s in ("long", "short"):
                    VARIANTS[f"m{_m}_N{_N}_k{_k}_{_w}_{_s}_1R"] = _variant(_m, _N, _k, _s, _w)
# Stage 2 (pre-declared rule): the 2 best stage-1 configs on TRAIN exp_r (n >= 30) get the other 3 exits = 6 configs.
# Chosen after the stage-1 train run only (valid not looked at).
STAGE2_BASES = ["m2_N12_k0.25_am_short_1R", "m3_N6_k0.25_am_short_1R"]  # chosen on train: top-2 exp_r with n >= 30
for _b in STAGE2_BASES:
    for _e in ("2R", "ts30", "hold45"):
        VARIANTS[_b.replace("_1R", f"_{_e}")] = dict(VARIANTS[_b], exit=_e)

FINALISTS: list[str] = []  # none: 37/38 configs negative on valid; the one positive (hold45, n=17) is one-day driven
_CACHE: dict = {}
BASELINE = {"stop_atr": 0.25, "target_atr": 0.25}


def signals(day, v) -> list[Signal]:
    bars = day.bars
    if len(bars) < 60 or not np.isfinite(day.atr) or day.atr <= 0:
        return []
    b5 = day.b5
    N, k, m = v["N"], v["k"], v["m"]
    w0, w1 = WINDOWS[v["win"]]
    side = 1 if v["side"] == "long" else -1
    key = (day.symbol, day.date)
    if _CACHE.get("key") != key:  # per-day precompute shared across variants (pure speed-up)
        _CACHE.clear()
        _CACHE.update(key=key, vw=F.vwap(bars).to_numpy(), pos={ts: i for i, ts in enumerate(bars.index)},
                      arr=tuple(b5[x].to_numpy(float) for x in ("open", "high", "low", "close", "volume")))
    vw, pos = _CACHE["vw"], _CACHE["pos"]
    idx = bars.index
    o, h, l, c, vol = _CACHE["arr"]
    starts = b5.index
    for j in range(max(N, 6), len(b5)):
        st = starts[j]
        close_t = (st + timedelta(minutes=5)).time()
        if close_t < w0 or close_t > w1:
            continue
        last1 = st + timedelta(minutes=4)
        bi = pos.get(last1)
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
            if not (px > ch and pct >= 0.6 and px > vw[bi]):
                continue
            stop = max(cl, px - 0.25 * day.atr)
        else:
            if not (px < cl and pct <= 0.4 and px < vw[bi]):
                continue
            stop = min(ch, px + 0.25 * day.atr)
        risk = abs(px - stop)
        if risk <= 0:
            continue
        sig = Signal(day.symbol, NAME, side, bi, stop)
        e = v["exit"]
        if e == "1R":
            sig.target = px + side * risk
        elif e == "2R":
            sig.target = px + side * 2 * risk
        elif e == "ts30":
            sig.target = px + side * 2 * risk
            sig.time_stop_min, sig.time_stop_min_r = 30, 0.3
        elif e == "hold45":
            sig.exit_by = (datetime.combine(day.date, close_t) + timedelta(minutes=45)).time()
        return [sig]
    return []
