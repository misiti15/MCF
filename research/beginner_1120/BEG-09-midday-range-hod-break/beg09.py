# BEGINNER SETUP BEG-09-midday-range-hod-break (research only, not enabled in any account)
# research/beginner_1120/DESIGN.md "B09"; backtest research/beginner_1120/BEG-09-midday-range-hod-break/RESULTS.md
# Educational only - not financial advice.
"""BEG-09 Midday range -> high/low-of-day break (long and short), on 1-minute RTH bars.

Spec (DESIGN.md B09, implemented as written; plainest readings marked [R]):
  universe  U0 (prior close >= $5, ADV20 >= $20M) + price >= $10 [R: prior close] + rank_rvol20 <= 30
  setup     long: day return >= +3% at 11:30 [R: close of the 11:29 bar vs prev_close; fixes the side];
            consolidation = the FIRST run of 30 consecutive 1-minute bars [R: contiguous minutes; "at least 30" is met
            by the first 30-bar window, not extended], all starting in 11:30..14:29, with max(high)-min(low) <=
            0.35 x ATR (daily ATR14 at prior close) and every close > session VWAP. Short = mirror (<= -3%, closes
            < VWAP; easy to borrow only, enforced by the book)
  trigger   buy-stop at the day's high so far + $0.01 (short: day's low - $0.01), armed from the bar after the window
            completes, working through the 14:59 bar (valid until 15:00) [R: not cancelled if price leaves the
            range]. Fill = max(open, trigger) (short: min). One trade per symbol-day.
  stop      consolidation low - $0.02 (short: consolidation high + $0.02)
  exit      target = trigger + 2 x (trigger - stop) [R: 2R on the order price]; otherwise flat at the 15:55 open.
            Stop checked first, including on the fill bar [R: conservative, as BEG-03].
Tweak knobs (PLAN.md "Tweaks"): see P.
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

try:
    from mcf.strategies.base import Signal, Strategy
except Exception:          # research use without the package on the path
    Signal = Strategy = object

NAME = "BEG-09-midday-range-hod-break"
SIDE = "both"
P = dict(move_pct=3.0, move_hhmm=1129, win_lo=1130, win_hi=1429, win_len=30, range_atr=0.35, trig_off=0.01,
         order_until=1459, stop_off=0.02, tgt_r=2.0, exit_hhmm=1555, min_price=10.0, min_adv=20e6, rank_max=30,
         stop_mult=1.0, max_risk_atr=None)


def vwap(h, l, c, v):
    tp = (h + l + c) / 3.0
    cv = np.cumsum(v)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cv > 0, np.cumsum(tp * v) / np.where(cv > 0, cv, 1), np.nan)


def tmin(hhmm):
    return (np.asarray(hhmm) // 100) * 60 + np.asarray(hhmm) % 100


def day_side(hhmm, c, prev_close, p=P):
    """+1 / -1 / 0 from the 11:29 close vs prev_close; also the move %."""
    k = np.flatnonzero(hhmm == p["move_hhmm"])
    if not len(k) or not prev_close > 0:
        return 0, np.nan
    mv = (c[k[0]] / prev_close - 1) * 100
    return (1 if mv >= p["move_pct"] else -1 if mv <= -p["move_pct"] else 0), mv


def find_window(h, l, c, vw, hhmm, side, atr, p=P):
    """First 30-bar consolidation -> (k_end, lo, hi) or None. Uses bars <= k_end only."""
    n = p["win_len"]
    idx = np.flatnonzero((hhmm >= p["win_lo"]) & (hhmm <= p["win_hi"]))
    if len(idx) < n:
        return None
    tm = tmin(hhmm)
    ok = (c > vw) if side == 1 else (c < vw)
    lim = p["range_atr"] * atr
    for e in range(n - 1, len(idx)):
        a, b = idx[e - n + 1], idx[e]
        if b - a != n - 1 or tm[b] - tm[a] != n - 1:
            continue
        if not ok[a:b + 1].all():
            continue
        hi, lo = h[a:b + 1].max(), l[a:b + 1].min()
        if hi - lo <= lim:
            return int(b), float(lo), float(hi)
    return None


def plan(o, h, l, c, v, hhmm, prev_close, atr, p=P):
    """-> dict(k_arm, side, trig, stop, tgt, lo, hi) (order works from bar k_arm+1) or None."""
    side, _ = day_side(hhmm, c, prev_close, p)
    if side == 0 or not atr > 0:
        return None
    vw = vwap(h, l, c, v)
    w = find_window(h, l, c, vw, hhmm, side, atr, p)
    if w is None:
        return None
    k, lo, hi = w
    if side == 1:
        trig = float(h[: k + 1].max()) + p["trig_off"]
        stop = lo - p["stop_off"]
    else:
        trig = float(l[: k + 1].min()) - p["trig_off"]
        stop = hi + p["stop_off"]
    dist = side * (trig - stop) * p.get("stop_mult", 1.0)
    if dist <= 0:
        return None
    if p.get("max_risk_atr") is not None and dist > p["max_risk_atr"] * atr:
        return None
    stop = trig - side * dist
    return dict(k_arm=k, side=side, trig=trig, stop=float(stop), tgt=float(trig + side * p["tgt_r"] * dist),
                lo=lo, hi=hi)


def find_entry(o, h, l, c, v, hhmm, prev_close, atr, p=P):
    """First fill of the stop order -> dict(j, fill, ...) or None."""
    pl = plan(o, h, l, c, v, hhmm, prev_close, atr, p)
    if pl is None:
        return None
    s, trig = pl["side"], pl["trig"]
    for j in range(pl["k_arm"] + 1, len(o)):
        if hhmm[j] > p["order_until"]:
            break
        if (s == 1 and h[j] >= trig) or (s == -1 and l[j] <= trig):
            fill = max(o[j], trig) if s == 1 else min(o[j], trig)
            return dict(j=int(j), fill=float(fill), **pl)
    return None


def walk(o, h, l, c, hhmm, j, fill, side, stop, tgt, p=P):
    """From the fill bar j. -> (px, kind, xt); kind 0 time, 1 stop, 2 target."""
    s = side
    if s * (fill - stop) <= 0 or s * (tgt - fill) <= 0:
        return None
    for k in range(j, len(o)):
        if hhmm[k] >= p["exit_hhmm"]:
            return float(o[k]), 0, int(hhmm[k])
        if (s == 1 and l[k] <= stop) or (s == -1 and h[k] >= stop):
            if k == j:
                return float(stop), 1, int(hhmm[k]) + 1
            return float(min(o[k], stop) if s == 1 else max(o[k], stop)), 1, int(hhmm[k]) + 1
        if (s == 1 and h[k] >= tgt + 0.01) or (s == -1 and l[k] <= tgt - 0.01):
            return float(tgt), 2, int(hhmm[k]) + 1
    return float(c[-1]), 0, int(hhmm[-1]) + 1


class Beg09MiddayRangeBreak(Strategy):
    """Live class (mcf.strategies.base). Called on each bar close with the session's 1-minute bars so far. Once the
    first 30-bar consolidation completes it emits one stop order at HOD + $0.01 (LOD - $0.01) that works until 15:00."""
    name = NAME
    max_signals_per_day = 1

    def eligible(self, ctx) -> bool:
        return (ctx.prev_close >= P["min_price"] and (ctx.avg_dollar_volume or 0) >= P["min_adv"]
                and ctx.rank_rvol20 is not None and ctx.rank_rvol20 <= P["rank_max"])

    def generate(self, ctx):
        p = dict(P, **getattr(self, "params", {}))
        b = ctx.bars
        if not len(b):
            return []
        hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        a = [b[x].to_numpy(float) for x in ("open", "high", "low", "close", "volume")]
        pl = plan(*a, hhmm, ctx.prev_close, ctx.atr, p)
        if pl is None or pl["k_arm"] != len(b) - 1:      # emit once, on the bar that completes the window
            return []
        valid = int(tmin(p["order_until"]) - tmin(hhmm[-1]))
        if valid <= 0:
            return []
        eh = p["exit_hhmm"]
        return [Signal(symbol=ctx.symbol, strategy=self.name, side=pl["side"], bar_index=len(b) - 1,
                       stop=pl["stop"], target=pl["tgt"], entry_type="stop", entry_price=pl["trig"],
                       entry_valid_bars=valid, exit_by=time(eh // 100, eh % 100),
                       meta={"cons_lo": pl["lo"], "cons_hi": pl["hi"]})]
