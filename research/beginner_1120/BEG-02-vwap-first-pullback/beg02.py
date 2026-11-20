# BEGINNER SETUP BEG-02-vwap-first-pullback (research only, not enabled in any account)
# research/beginner_1120/DESIGN.md "B02"; backtest research/beginner_1120/BEG-02-vwap-first-pullback/RESULTS.md
# Educational only - not financial advice.
"""BEG-02 VWAP first pullback in a trend (long and short), on 1-minute RTH bars.

Spec (DESIGN.md B02, implemented as written; plainest readings noted with [R]):
  universe  U0 (price >= $5, ADV20 >= $20M) + price >= $10 [R: prior close] + rank_rvol20 <= 50 (09:30-09:49
            relative volume rank among the day's U0 names, mcf.backtest.engine.rank_contexts)
  setup     long: price at 09:50 [R: close of the 09:49 bar] >= +2.0% vs prev_close AND every 1-minute close of the
            bars 09:35..09:49 is above session VWAP [R: every bar present; the 09:49 bar must exist]; short = mirror
  window    signal bars 09:50..12:59 (entry at the next bar's open, so the last entry is 13:00)
  trigger   the FIRST bar from 09:50 whose low <= VWAP x (1 + 0.10%) and whose close > VWAP (long) [R: one look per
            symbol-day; if that first pullback fails the target rule, no trade that day]; short: high >= VWAP x
            (1 - 0.10%) and close < VWAP (easy to borrow only; enforced by the book)
  stop      pullback bar low - $0.02 (short: high + $0.02); widened to 0.15 x ATR from the reference price when closer
            [R: reference = the trigger bar close, the price known at the decision]
  target    min(entry + 2R, day high so far) for a long (max(entry - 2R, day low so far) for a short), with R and the
            2R/1.5R tests measured from the reference price; skip if the day's high/low is < 1.5R away
  time stop after 60 min in the trade, exit at the next bar open if +0.5R was never reached
  max hold  120 min (exit at the open of the bar 120 min after the entry bar); flat by 15:55 in any case
"""
from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from mcf.strategies.base import Signal, Strategy
except Exception:          # research use without the package on the path
    Signal = Strategy = object

SIDE = "both"
P = dict(move_pct=2.0, trend_lo=935, trend_hi=949, win_lo=950, win_hi=1259, touch_pct=0.10, stop_off=0.02,
         min_stop_atr=0.15, tgt_r=2.0, min_tgt_r=1.5, time_stop_min=60, time_stop_r=0.5, max_hold=120,
         min_price=10.0, min_adv=20e6, rank_max=50, stop_mult=1.0)


def vwap(h, l, c, v):
    tp = (h + l + c) / 3.0
    cv = np.cumsum(v)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cv > 0, np.cumsum(tp * v) / np.where(cv > 0, cv, 1), np.nan)


def setup_side(hhmm, c, vw, prev_close, p=P):
    """+1 / -1 / 0 at 09:50 from the 09:49 close and the 09:35..09:49 closes vs VWAP; also returns the 09:50 move %."""
    k = np.flatnonzero(hhmm == p["trend_hi"])
    if not len(k) or not prev_close > 0:
        return 0, np.nan
    mv = (c[k[0]] / prev_close - 1) * 100
    sel = (hhmm >= p["trend_lo"]) & (hhmm <= p["trend_hi"])
    above, below = np.all(c[sel] > vw[sel]), np.all(c[sel] < vw[sel])
    if mv >= p["move_pct"] and above:
        return 1, mv
    if mv <= -p["move_pct"] and below:
        return -1, mv
    return 0, mv


def find_signal(o, h, l, c, v, hhmm, prev_close, atr, p=P):
    """-> dict(k, side, ref, stop, tgt, tgt_r) for the first pullback bar k, or None. Uses bars <= k only."""
    vw = vwap(h, l, c, v)
    side, _ = setup_side(hhmm, c, vw, prev_close, p)
    if side == 0 or not atr > 0:
        return None
    tp = p["touch_pct"] / 100.0
    for k in np.flatnonzero((hhmm >= p["win_lo"]) & (hhmm <= p["win_hi"])):
        if side == 1:
            hit = l[k] <= vw[k] * (1 + tp) and c[k] > vw[k]
        else:
            hit = h[k] >= vw[k] * (1 - tp) and c[k] < vw[k]
        if not hit:
            continue
        ref = c[k]
        stop = l[k] - p["stop_off"] if side == 1 else h[k] + p["stop_off"]
        dist = max(side * (ref - stop), p["min_stop_atr"] * atr) * p.get("stop_mult", 1.0)
        stop = ref - side * dist
        ext = h[: k + 1].max() if side == 1 else l[: k + 1].min()
        room = side * (ext - ref) / dist
        if room < p["min_tgt_r"]:
            return None                     # first pullback only: skipped, no second look
        tr = min(p["tgt_r"], room)
        return dict(k=int(k), side=side, ref=float(ref), stop=float(stop), tgt=float(ref + side * tr * dist),
                    tgt_r=float(tr))
    return None


def walk(o, h, l, c, hhmm, sig, p=P):
    """Entry at the open of bar k+1; stop first (gap-through: worse of open/stop), target only when traded through by
    >= $0.01 (Workbench rule), time stop, max hold, flat at the 15:55 open. -> (j, fill, px, kind, xt) or None.
    kind: 0 market/time exit, 1 stop, 2 target (limit)."""
    j = sig["k"] + 1
    if j >= len(o) or hhmm[j] >= 1555:
        return None
    s, stop, tgt, fill = sig["side"], sig["stop"], sig["tgt"], o[j]
    risk = s * (fill - stop)
    if risk <= 0 or s * (tgt - fill) <= 0:
        return None
    em = (hhmm[j] // 100) * 60 + hhmm[j] % 100
    xlim = em + p["max_hold"]
    mfe = 0.0
    for k in range(j, len(o)):
        km = (hhmm[k] // 100) * 60 + hhmm[k] % 100
        if km >= xlim or hhmm[k] >= 1555:
            return j, fill, o[k], 0, int(hhmm[k])
        if (s == 1 and l[k] <= stop) or (s == -1 and h[k] >= stop):
            return j, fill, (min(o[k], stop) if s == 1 else max(o[k], stop)), 1, int(hhmm[k]) + 1
        if (s == 1 and h[k] >= tgt + 0.01) or (s == -1 and l[k] <= tgt - 0.01):
            return j, fill, tgt, 2, int(hhmm[k]) + 1
        mfe = max(mfe, s * ((h[k] if s == 1 else l[k]) - fill) / risk)
        if km - em + 1 >= p["time_stop_min"] and mfe < p["time_stop_r"] and k + 1 < len(o):
            return j, fill, o[k + 1], 0, int(hhmm[k + 1])
    return j, fill, c[-1], 0, int(hhmm[-1]) + 1


class BEG02(Strategy):
    """Live interface (mcf.strategies.base): generate(ctx) on the session's 1-minute bars so far."""
    name = "BEG-02-vwap-first-pullback"
    max_signals_per_day = 1

    def eligible(self, ctx) -> bool:
        return (ctx.prev_close >= P["min_price"] and (ctx.avg_dollar_volume or 0) >= P["min_adv"]
                and ctx.rank_rvol20 is not None and ctx.rank_rvol20 <= P["rank_max"])

    def generate(self, ctx):
        b = ctx.bars
        hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        a = [b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")]
        sig = find_signal(*a, hhmm, ctx.prev_close, ctx.atr)
        if sig is None:
            return []
        ts = b.index[sig["k"]] + pd.Timedelta(minutes=1 + P["max_hold"])
        return [Signal(symbol=ctx.symbol, strategy=self.name, side=sig["side"], bar_index=sig["k"], stop=sig["stop"],
                       target=sig["tgt"], exit_by=ts.time(), time_stop_min=P["time_stop_min"],
                       time_stop_min_r=P["time_stop_r"], meta={"tgt_r": sig["tgt_r"]})]
