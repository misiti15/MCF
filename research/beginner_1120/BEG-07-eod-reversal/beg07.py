# BEGINNER SETUP BEG-07-eod-reversal (research only, not enabled in any account)
# research/beginner_1120/DESIGN.md "B07"; backtest research/beginner_1120/BEG-07-eod-reversal/RESULTS.md
# Educational only - not financial advice.
"""BEG-07 End-of-day reversal of intraday extremes (long and short), on 1-minute RTH bars.

Spec (DESIGN.md B07, implemented as written; plainest readings marked [R]):
  universe  U0 (price >= $5, ADV20 >= $20M) + price >= $10, ADV20 >= $30M, stocks only (no ETFs).
            [R] price = the 15:24 close; ADV20 = 20-day average dollar volume as of the prior close.
  signal    one universe-level pass on the 15:24 bar close: r = close(15:24) / prev_close - 1.
            Long  : the 10 lowest r with r <= -3% that are NOT pinned at the day's low  (close > day low  + 0.1 ATR).
            Short : the 10 highest r with r >= +3% that are NOT pinned at the day's high (close < day high - 0.1 ATR),
                    easy-to-borrow only.
            [R] the pin and ETB filters are applied BEFORE the top-10 ranking ("the 10 lowest r ... that are not
            pinned"); day high/low = RTH 09:30..15:24 inclusive. ATR = daily ATR(14) as of the prior close.
  entry     at 15:25: market fill at the 15:25 bar open (DESIGN global convention: signal on a bar close, fill at
            the next bar's open).
  stop      0.20 x ATR from the entry [R: from the actual fill in the backtest; the live Signal carries the 15:24
            close as the reference price].
  exit      time exit at 15:55 (the 15:55 bar open, the engine's flat time), no target; max hold 30 min.
  one trade per symbol per day; at most 10 longs + 10 shorts per day.
Tweak parameters (pre-registered in PLAN.md, default = base): see P.
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

try:
    from mcf.strategies.base import Signal, Strategy
except Exception:          # research use without the package on the path
    Signal = Strategy = object

SIDE = "both"
P = dict(sig_hhmm=1524, exit_hhmm=1555, stop_atr=0.20, r_thr=3.0, n_side=10, pin_atr=0.10, min_px=10.0,
         min_adv=30e6, etb_min=0.9, side_only=0, max_r=None, min_atr_pct=0.0)


def pick(snap: pd.DataFrame, p=P) -> pd.DataFrame:
    """Universe pass for ONE session at the signal bar close.
    snap columns: symbol, c (signal-bar close), pc (prev close), dh, dl (RTH high/low so far), atr, adv, is_etf,
    etb (easy-to-borrow rate/flag, 1 = ETB). -> rows picked, with side (+1 long / -1 short) and r (%)."""
    s = snap[(~snap.is_etf.astype(bool)) & (snap.c >= max(5.0, p["min_px"])) & (snap.adv >= max(20e6, p["min_adv"]))
             & (snap.atr > 0) & (snap.pc > 0)].copy()
    s["r"] = (s.c / s.pc - 1) * 100
    if p.get("min_atr_pct", 0) > 0:
        s = s[s.atr / s.pc * 100 >= p["min_atr_pct"]]
    lo = s[(s.r <= -p["r_thr"]) & (s.c > s.dl + p["pin_atr"] * s.atr)]
    hi = s[(s.r >= p["r_thr"]) & (s.c < s.dh - p["pin_atr"] * s.atr) & (s.etb >= p["etb_min"])]
    if p.get("max_r"):
        lo, hi = lo[lo.r >= -p["max_r"]], hi[hi.r <= p["max_r"]]
    lo = lo.sort_values(["r", "symbol"]).head(p["n_side"]).assign(side=1)
    hi = hi.sort_values(["r", "symbol"], ascending=[False, True]).head(p["n_side"]).assign(side=-1)
    out = pd.concat([lo, hi])
    if p.get("side_only", 0):
        out = out[out.side == p["side_only"]]
    return out


def walk(o, h, l, side, dist, p=P, hhmm=None):
    """Path arrays from the entry bar (15:25) through the exit bar (15:55) inclusive. Entry at o[0]; stop = fill -/+ dist;
    stop first (gap-through fills at the worse of open/stop); time exit at the open of the exit bar.
    -> (fill, stop, px, kind, xt)  kind 0 = time exit, 1 = stop."""
    fill = o[0]
    stop = fill - side * dist
    n = len(o)
    for k in range(n - 1):
        if not np.isfinite(o[k]):
            continue
        if (side == 1 and l[k] <= stop) or (side == -1 and h[k] >= stop):
            px = min(o[k], stop) if side == 1 else max(o[k], stop)
            return fill, stop, px, 1, int(hhmm[k]) + 1 if hhmm is not None else k
    return fill, stop, o[n - 1], 0, int(hhmm[n - 1]) if hhmm is not None else n - 1


class BEG07(Strategy):
    """Live interface (mcf.strategies.base). The live runner must call universe_pass(date, snap) once at the 15:24 bar
    close with a snapshot of the whole universe (DayContext is per symbol, so the ranking cannot happen inside
    generate()); generate(ctx) then emits the picked symbol's signal."""
    name = "BEG-07-eod-reversal"
    max_signals_per_day = 1
    _picks: dict = {}

    @classmethod
    def universe_pass(cls, day, snap: pd.DataFrame):
        pk = pick(snap)
        cls._picks = {"date": day, "rows": {r.symbol: (int(r.side), float(r.r)) for r in pk.itertuples()}}
        return pk

    def generate(self, ctx):
        pk = self._picks
        if pk.get("date") != ctx.date or ctx.symbol not in pk.get("rows", {}):
            return []
        b = ctx.bars
        hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        if not len(hhmm) or hhmm[-1] < P["sig_hhmm"]:
            return []
        k = int(np.flatnonzero(hhmm <= P["sig_hhmm"])[-1])
        side, r = pk["rows"][ctx.symbol]
        ref = float(b.close.iloc[k])
        eh = P["exit_hhmm"]
        return [Signal(symbol=ctx.symbol, strategy=self.name, side=side, bar_index=k,
                       stop=ref - side * P["stop_atr"] * ctx.atr, target=None,
                       exit_by=time(eh // 100, eh % 100), meta={"r": r})]
