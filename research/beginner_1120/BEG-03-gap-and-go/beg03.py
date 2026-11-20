# BEGINNER SETUP BEG-03-gap-and-go (research only, not enabled in any account)
# research/beginner_1120/DESIGN.md "B03"; backtest research/beginner_1120/BEG-03-gap-and-go/RESULTS.md
# Educational only - not financial advice.
"""BEG-03 Gap-and-go continuation (long only), on 1-minute RTH bars.

Spec (DESIGN.md B03, implemented as written; plainest readings marked [R]):
  universe  U0 (price >= $5, ADV20 >= $20M) + price $5-$200 [R: prior close] + gap = 09:30 open / prev_close - 1
            >= +3.0% + RVOL20 >= 3.0 (09:30-09:49 volume / its 14-session average, as mcf.backtest.engine)
  R20       high/low of the bars 09:30..09:49
  trigger   buy-stop at R20 high + $0.01, working on the bars 09:50..10:59 (so every fill is before 11:00).
            [R] The order is "armed" for bar k only if the close of bar k-1 (the last close before the trigger) is
            above session VWAP at k-1; an unarmed bar cannot fill; the order keeps working until 11:00. A bar that
            opens above the trigger fills at its open (stop-order semantics, mcf.backtest.engine.simulate).
  stop      max(R20 low, VWAP at signal) - $0.02, [R] VWAP at signal = VWAP at the close of bar k-1. The stop distance
            is measured from the trigger price; skip the bar (not armed) unless 0.4% <= distance / trigger <= 3%.
  exit      target = trigger + 2R (R = trigger - stop); after the best price reaches +1R (R measured from the real fill)
            the stop trails 1R behind the best price (updated for the next bar, as engine.simulate trail_r=1,
            trail_after_r=1); time exit at the open of the 12:00 bar (exit_by 12:00). One trade per symbol-day.
  fills     stop first; a gap-through below the stop fills at the bar open (after the entry bar); the target fills only
            when traded through by >= $0.01 (the Workbench rule used by bench10).
Tweaks (PLAN.md) override P keys: stop_mult, win_lo, rvol_min, tgt_r, gap_min, ... (one part each).
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

try:
    from mcf.strategies.base import Signal, Strategy
except Exception:          # research use without the package on the path
    Signal, Strategy = None, object

NAME = "BEG-03-gap-and-go"
SIDE = "long"
P = dict(min_price=5.0, max_price=200.0, min_adv=20e6, gap_min=3.0, rvol_min=3.0, r20_hi=949, win_lo=950, win_hi=1059,
         stop_off=0.02, trig_off=0.01, min_stop_pct=0.4, max_stop_pct=3.0, tgt_r=2.0, trail_r=1.0, trail_after_r=1.0,
         exit_by=1200, stop_mult=1.0)


def vwap(h, l, c, v):
    tp = (h + l + c) / 3.0
    cv = np.cumsum(v)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cv > 0, np.cumsum(tp * v) / np.where(cv > 0, cv, 1), np.nan)


def universe_ok(prev_close, open930, adv20, rvol20, p=P):
    if not (prev_close > 0 and open930 > 0):
        return False
    gap = (open930 / prev_close - 1) * 100
    return bool(p["min_price"] <= prev_close <= p["max_price"] and (adv20 or 0) >= p["min_adv"]
                and gap >= p["gap_min"] and rvol20 is not None and rvol20 >= p["rvol_min"])


def arm(k, h, l, c, vw, hhmm, p=P):
    """Order parameters for bar k (decided at the close of bar k-1) or None. Uses bars < k only."""
    r20 = hhmm <= p["r20_hi"]
    if k < 1 or not r20.any() or hhmm[0] != 930:
        return None
    hi, lo = h[r20].max(), l[r20].min()
    trig = round(hi + p["trig_off"], 2)
    if not c[k - 1] > vw[k - 1]:
        return None
    stop = max(lo, vw[k - 1]) - p["stop_off"]
    dist = trig - stop
    if dist <= 0 or not (p["min_stop_pct"] <= dist / trig * 100 <= p["max_stop_pct"]):
        return None
    dist *= p.get("stop_mult", 1.0)          # tweak only (1.0 in the base): widen after the band test
    stop = trig - dist
    return dict(trig=float(trig), stop=float(stop), tgt=float(trig + p["tgt_r"] * dist))


def find_entry(o, h, l, c, v, hhmm, p=P):
    """First fill of the buy-stop -> dict(j, fill, trig, stop, tgt) or None."""
    vw = vwap(h, l, c, v)
    for k in np.flatnonzero((hhmm >= p["win_lo"]) & (hhmm <= p["win_hi"])):
        a = arm(k, h, l, c, vw, hhmm, p)
        if a is None or h[k] < a["trig"]:
            continue
        return dict(j=int(k), fill=float(max(o[k], a["trig"])), **a)
    return None


def walk(o, h, l, c, hhmm, j, fill, stop, tgt, p=P):
    """From the entry bar j (filled intrabar at `fill`). -> (px, kind, xt) ; kind 0 time, 1 stop/trail, 2 target."""
    risk = fill - stop
    if risk <= 0 or tgt - fill <= 0:
        return None
    best = 0.0
    for k in range(j, len(o)):
        if hhmm[k] >= p["exit_by"] or hhmm[k] >= 1555:
            return float(o[k]), 0, int(hhmm[k])
        if l[k] <= stop:
            return float(min(o[k], stop) if k > j else stop), 1, int(hhmm[k]) + 1
        if h[k] >= tgt + 0.01:
            return float(tgt), 2, int(hhmm[k]) + 1
        best = max(best, (h[k] - fill) / risk)
        if p["trail_r"] is not None and best >= p["trail_after_r"]:
            stop = max(stop, fill + (best - p["trail_r"]) * risk)
    return float(c[-1]), 0, int(hhmm[-1]) + 1


class Beg03GapAndGo(Strategy):
    """Live class (mcf.strategies.base). Called on each bar close with the session's 1-minute bars so far: when the
    order is armed for the NEXT bar it emits a one-bar buy-stop (entry_valid_bars=1); the runner re-arms bar by bar
    (that is how the VWAP condition and the VWAP-based stop stay current). Needs ctx.avg_cum_volume (14-day)."""
    name = NAME
    max_signals_per_day = 1

    def eligible(self, ctx) -> bool:
        return P["min_price"] <= ctx.prev_close <= P["max_price"] and (ctx.avg_dollar_volume or 0) >= P["min_adv"]

    def generate(self, ctx):
        p = dict(P, **getattr(self, "params", {}))
        b = ctx.bars
        if not len(b):
            return []
        hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        k = len(b)                           # the next bar
        nxt = (pd.Timestamp(b.index[-1]) + pd.Timedelta(minutes=1))
        nh = nxt.hour * 100 + nxt.minute
        if not (p["win_lo"] <= nh <= p["win_hi"]) or ctx.avg_cum_volume is None or len(ctx.avg_cum_volume) < 20:
            return []
        ref = float(ctx.avg_cum_volume[19])
        rvol = float(b["volume"].to_numpy()[hhmm <= p["r20_hi"]].sum()) / ref if ref > 0 else np.nan
        if not universe_ok(ctx.prev_close, float(b["open"].iloc[0]), ctx.avg_dollar_volume, rvol, p):
            return []
        h, l, c, v = (b[x].to_numpy(float) for x in ("high", "low", "close", "volume"))
        a = arm(k, np.r_[h, np.nan], np.r_[l, np.nan], np.r_[c, np.nan], np.r_[vwap(h, l, c, v), np.nan],
                np.r_[hhmm, nh], p)
        if a is None:
            return []
        eb = p["exit_by"]
        return [Signal(symbol=ctx.symbol, strategy=self.name, side=1, bar_index=k - 1, stop=a["stop"],
                       target=a["tgt"], entry_type="stop", entry_price=a["trig"], entry_valid_bars=1,
                       exit_by=time(eb // 100, eb % 100), trail_r=p["trail_r"], trail_after_r=p["trail_after_r"],
                       meta={"rvol20": rvol})]
