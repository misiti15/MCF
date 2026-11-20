# BEGINNER SETUP BEG-05-mkt-intraday-momentum (research only, not enabled in any account)
# research/beginner_1120/DESIGN.md "B05"; backtest research/beginner_1120/BEG-05-mkt-intraday-momentum/RESULTS.md
# Educational only - not financial advice.
"""BEG-05 Market intraday momentum, last 25 minutes (long and short), on 1-minute RTH bars.

Spec (DESIGN.md B05, implemented as written; plainest readings marked [R]):
  universe  SPY, QQQ, IWM, DIA only (never inverse ETFs)
  signal    r1 = price at 10:00 / prev_close - 1 [R: price at 10:00 = close of the 09:59 bar, i.e. the end of the first
            half hour, as Gao et al.]; long if r1 >= +0.25% and the 15:29 close > session VWAP (typical-price VWAP from
            09:30, as mcf.features.vwap); short if r1 <= -0.25% and the 15:29 close < VWAP
  entry     signal on the 15:29 bar close, market fill at the 15:30 bar open (global convention: next bar open)
  stop      0.15 x ATR (daily ATR(14) as of the prior close) from the entry [R: from the actual fill in the backtest;
            the live Signal must carry a price at decision time, so it uses the 15:29 close as the reference]
  exit      time exit at 15:55 (the 15:55 bar open, the engine's flat time), no target; max hold 25 min
  one trade per symbol per day.
Tweak parameters (pre-registered in PLAN.md, default = base): stop_atr, r1_thr, sig_hhmm/exit (window), filters.
"""
from __future__ import annotations

from datetime import time

import numpy as np

try:
    from mcf.strategies.base import Signal, Strategy
except Exception:          # research use without the package on the path
    Signal = Strategy = object

SYMBOLS = ("SPY", "QQQ", "IWM", "DIA")
SIDE = "both"
P = dict(r1_hhmm=959, r1_thr=0.25, sig_hhmm=1529, exit_hhmm=1555, stop_atr=0.15, vwap_filter=True,
         min_r2_abs=0.0, side_only=0)


def vwap(h, l, c, v):
    tp = (h + l + c) / 3.0
    cv = np.cumsum(v)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cv > 0, np.cumsum(tp * v) / np.where(cv > 0, cv, 1), np.nan)


def find_signal(o, h, l, c, v, hhmm, prev_close, atr, p=P):
    """One session's bars (09:30..). -> dict(k, side, r1, ref, dist) for the signal bar k, or None. Uses bars <= k only."""
    if not (prev_close > 0 and atr > 0):
        return None
    k1 = np.flatnonzero(hhmm == p["r1_hhmm"])
    ks = np.flatnonzero(hhmm == p["sig_hhmm"])
    if not len(k1) or not len(ks):
        return None
    k1, k = int(k1[0]), int(ks[0])
    r1 = (c[k1] / prev_close - 1) * 100
    vw = vwap(h[: k + 1], l[: k + 1], c[: k + 1], v[: k + 1])[k]
    thr = p["r1_thr"]
    side = 0
    if r1 >= thr and (not p["vwap_filter"] or c[k] > vw):
        side = 1
    elif r1 <= -thr and (not p["vwap_filter"] or c[k] < vw):
        side = -1
    if side == 0 or (p.get("side_only", 0) and side != p["side_only"]):
        return None
    # optional one-part filter (tweak): the mid-day move (10:00 -> signal bar) must agree in sign by >= min_r2_abs %
    if p.get("min_r2_abs", 0) > 0:
        r2 = (c[k] / c[k1] - 1) * 100
        if side * r2 < p["min_r2_abs"]:
            return None
    return dict(k=k, side=side, r1=float(r1), ref=float(c[k]), dist=float(p["stop_atr"] * atr))


def walk(o, h, l, c, hhmm, sig, p=P):
    """Entry at the open of bar k+1, stop = fill -/+ dist; stop first (gap-through: worse of open/stop); time exit at
    the exit_hhmm bar open. -> (j, fill, stop, px, kind, xt) or None. kind 0 = time exit, 1 = stop."""
    j = sig["k"] + 1
    if j >= len(o) or hhmm[j] >= p["exit_hhmm"]:
        return None
    s, fill = sig["side"], o[j]
    stop = fill - s * sig["dist"]
    for k in range(j, len(o)):
        if hhmm[k] >= p["exit_hhmm"]:
            return j, fill, stop, o[k], 0, int(hhmm[k])
        if (s == 1 and l[k] <= stop) or (s == -1 and h[k] >= stop):
            return j, fill, stop, (min(o[k], stop) if s == 1 else max(o[k], stop)), 1, int(hhmm[k]) + 1
    return j, fill, stop, c[-1], 0, int(hhmm[-1]) + 1


class BEG05(Strategy):
    """Live interface (mcf.strategies.base): generate(ctx) on the session's 1-minute bars so far."""
    name = "BEG-05-mkt-intraday-momentum"
    max_signals_per_day = 1

    def eligible(self, ctx) -> bool:
        return ctx.symbol in SYMBOLS

    def generate(self, ctx):
        if ctx.symbol not in SYMBOLS:
            return []
        b = ctx.bars
        hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        if not len(hhmm) or hhmm[-1] < P["sig_hhmm"]:       # nothing before the 15:29 bar close (uses bars <= 15:29)
            return []
        a = [b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")]
        sig = find_signal(*a, hhmm, ctx.prev_close, ctx.atr)
        if sig is None:
            return []
        stop = sig["ref"] - sig["side"] * sig["dist"]
        eh = P["exit_hhmm"]
        return [Signal(symbol=ctx.symbol, strategy=self.name, side=sig["side"], bar_index=sig["k"], stop=stop,
                       target=None, exit_by=time(eh // 100, eh % 100), meta={"r1": sig["r1"]})]
