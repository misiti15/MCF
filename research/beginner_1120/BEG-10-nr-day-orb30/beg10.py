# BEGINNER SETUP BEG-10-nr-day-orb30 (research only, not enabled in any account)
# research/beginner_1120/DESIGN.md "B10"; backtest research/beginner_1120/BEG-10-nr-day-orb30/RESULTS.md
# Educational only - not financial advice.
"""BEG-10 Narrow-range day -> first-30-minute breakout (long and short), on 1-minute RTH bars.

Spec (DESIGN.md B10, implemented as written; plainest readings marked [R]):
  universe  U0 (prior close >= $5, ADV20 >= $20M) + price >= $10 [R: prior close] + ADV20 >= $30M
  setup     yesterday's range (prev_high - prev_low, RTH session [R]) <= 0.6 x ATR (daily ATR14 at prior close);
            OR30 = high/low of the 09:30..09:59 bars; skip the day if OR30 range > 0.8 x ATR
  trigger   OCO stop entries placed at the 09:59 bar close: buy-stop at OR30 high + $0.01, sell-stop at OR30 low
            - $0.01, working on the 10:00..12:29 bars [R: "entries 10:00-12:30" = valid until 12:30]. First fill wins
            and cancels the other. Fill = max(open, trigger) (short: min). If one bar touches both triggers, the side
            whose trigger is nearer that bar's open fills [R]. Shorts only when easy to borrow: on a non-ETB name only
            the buy-stop is placed [R]. One trade per symbol-day.
  stop      midpoint of OR30 [R: (OR30 high + OR30 low) / 2, unrounded]
  exit      target = trigger + 2 x (trigger - stop) [R: 2R on the order price; the booked R uses the real fill];
            otherwise flat at the 15:55 open. Stop checked first, including on the fill bar [R: conservative].
Tweak knobs (PLAN.md "Tweaks"): see P.
"""
from __future__ import annotations

from datetime import time

import numpy as np

try:
    from mcf.strategies.base import Signal, Strategy
except Exception:          # research use without the package on the path
    Signal = Strategy = object

NAME = "BEG-10-nr-day-orb30"
SIDE = "both"
P = dict(nr_atr=0.6, or_end=959, or_max_atr=0.8, trig_off=0.01, win_lo=1000, win_hi=1229, stop_frac=0.5,
         stop_mult=1.0, tgt_r=2.0, exit_hhmm=1555, min_price=10.0, min_adv=30e6, sides=(1, -1), or_min_atr=None)


def tmin(hhmm):
    return (np.asarray(hhmm) // 100) * 60 + np.asarray(hhmm) % 100


def nr_day(prev_high, prev_low, atr, p=P):
    return bool(atr > 0 and prev_high >= prev_low and (prev_high - prev_low) <= p["nr_atr"] * atr)


def plan(h, l, hhmm, atr, p=P):
    """OR30 orders, known at the 09:59 bar close -> dict(k_or, hi, lo, legs={side: (trig, stop, tgt)}) or None."""
    m = (hhmm >= 930) & (hhmm <= p["or_end"])
    k = np.flatnonzero(m)
    if not len(k) or hhmm[k[-1]] != p["or_end"] or not atr > 0:
        return None
    hi, lo = float(h[m].max()), float(l[m].min())
    rng = hi - lo
    if rng <= 0 or rng > p["or_max_atr"] * atr:
        return None
    if p.get("or_min_atr") is not None and rng < p["or_min_atr"] * atr:
        return None
    mid = lo + p["stop_frac"] * rng
    legs = {}
    for s in p["sides"]:
        trig = hi + p["trig_off"] if s == 1 else lo - p["trig_off"]
        dist = s * (trig - (mid if s == 1 else hi - p["stop_frac"] * rng)) * p["stop_mult"]
        if dist <= 0:
            continue
        stop = trig - s * dist
        legs[s] = (trig, float(stop), float(trig + s * p["tgt_r"] * dist))
    return dict(k_or=int(k[-1]), hi=hi, lo=lo, legs=legs) if legs else None


def find_entry(o, h, l, hhmm, atr, p=P, etb=True):
    """First fill of the OCO pair -> dict(j, fill, side, trig, stop, tgt, hi, lo, k_or) or None."""
    pl = plan(h, l, hhmm, atr, p)
    if pl is None:
        return None
    legs = {s: v for s, v in pl["legs"].items() if s == 1 or etb}
    if not legs:
        return None
    for j in range(pl["k_or"] + 1, len(o)):
        if hhmm[j] < p["win_lo"]:
            continue
        if hhmm[j] > p["win_hi"]:
            break
        hit = [s for s, (trig, _, _) in legs.items() if (h[j] >= trig if s == 1 else l[j] <= trig)]
        if not hit:
            continue
        s = hit[0] if len(hit) == 1 else min(hit, key=lambda x: abs(o[j] - legs[x][0]))
        trig, stop, tgt = legs[s]
        fill = max(o[j], trig) if s == 1 else min(o[j], trig)
        return dict(j=int(j), fill=float(fill), side=s, trig=trig, stop=stop, tgt=tgt, hi=pl["hi"], lo=pl["lo"],
                    k_or=pl["k_or"])
    return None


def walk(o, h, l, c, hhmm, j, fill, side, stop, tgt, p=P):
    """From the fill bar j. -> (px, kind, xt); kind 0 time, 1 stop, 2 target."""
    s = side
    if s * (fill - stop) <= 0 or (tgt is not None and s * (tgt - fill) <= 0):
        return None
    for k in range(j, len(o)):
        if hhmm[k] >= p["exit_hhmm"]:
            return float(o[k]), 0, int(hhmm[k])
        if (s == 1 and l[k] <= stop) or (s == -1 and h[k] >= stop):
            if k == j:
                return float(stop), 1, int(hhmm[k]) + 1
            return float(min(o[k], stop) if s == 1 else max(o[k], stop)), 1, int(hhmm[k]) + 1
        if tgt is not None and ((s == 1 and h[k] >= tgt + 0.01) or (s == -1 and l[k] <= tgt - 0.01)):
            return float(tgt), 2, int(hhmm[k]) + 1
    return float(c[-1]), 0, int(hhmm[-1]) + 1


class Beg10NrDayOrb30(Strategy):
    """Live class (mcf.strategies.base). On the 09:59 bar close of a narrow-range day it emits two stop-order Signals
    (buy-stop above OR30, sell-stop below), valid through 12:29, tagged meta["oco"] so the runner cancels the sibling
    when one fills. NOTE: the live engine has no entry-OCO today; deploying this needs that support (or one leg only)."""
    name = NAME
    max_signals_per_day = 2

    def eligible(self, ctx) -> bool:
        p = dict(P, **getattr(self, "params", {}))
        return (ctx.prev_close >= p["min_price"] and (ctx.avg_dollar_volume or 0) >= p["min_adv"]
                and nr_day(ctx.prev_high, ctx.prev_low, ctx.atr, p))

    def generate(self, ctx):
        p = dict(P, **{k: v for k, v in getattr(self, "params", {}).items() if k in P})
        b = ctx.bars
        if not len(b):
            return []
        hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        if hhmm[-1] != p["or_end"] or not nr_day(ctx.prev_high, ctx.prev_low, ctx.atr, p):
            return []
        pl = plan(b["high"].to_numpy(float), b["low"].to_numpy(float), hhmm, ctx.atr, p)
        if pl is None:
            return []
        valid = int(tmin(p["win_hi"]) - tmin(p["or_end"]))
        eh = p["exit_hhmm"]
        oco = f"{NAME}:{ctx.symbol}:{ctx.date}"
        return [Signal(symbol=ctx.symbol, strategy=self.name, side=s, bar_index=len(b) - 1, stop=stop, target=tgt,
                       entry_type="stop", entry_price=trig, entry_valid_bars=valid,
                       exit_by=time(eh // 100, eh % 100), meta={"oco": oco, "or_hi": pl["hi"], "or_lo": pl["lo"]})
                for s, (trig, stop, tgt) in pl["legs"].items()]
