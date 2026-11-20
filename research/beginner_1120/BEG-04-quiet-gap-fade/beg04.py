# BEGINNER SETUP BEG-04-quiet-gap-fade (research only, not enabled in any account)
# research/beginner_1120/DESIGN.md "B04"; backtest research/beginner_1120/BEG-04-quiet-gap-fade/RESULTS.md
# Educational only - not financial advice.
"""BEG-04 Quiet gap fade toward the prior close (long and short), on 1-minute RTH bars.

Spec (DESIGN.md B04, implemented as written; plainest readings marked [R]):
  universe  U0 (prior close >= $5, ADV20 >= $20M) + ADV20 >= $50M + price >= $15 [R: prior close]
            + 1.5% <= |gap| <= 6% (gap = 09:30 open / prev_close - 1) + no unusual volume: rank_rvol20 > 100 AND
            RVOL20 < 1.5 (RVOL20 = 09:30-09:49 volume / its 14-session average; rank in the day's U0 universe).
            [R] a symbol without an RVOL20 (no 14-day history) is not traded. Shorts: ETB only (the book's E90
            proxy) and never an inverse / volatility fund.
  R20       high/low of the bars 09:30..09:49.
  trigger   gap up -> short when a 1-minute bar closes below the R20 low AND that close is below session VWAP.
            gap down -> long when a bar closes above the R20 high AND above VWAP.
            [R] decision bars 09:50..11:59, fill at the NEXT bar's open (DESIGN global convention), so every fill is
            in 09:51..12:00. [R] only the FIRST trigger of the symbol-day counts: if it fails the 1.2R test the
            symbol-day is skipped ("skip the trade"), there is no second look.
  stop      the other side of R20 +/- $0.02 (short: R20 high + 0.02; long: R20 low - 0.02), capped at 0.35 x ATR from
            entry. [R] "entry" = the decision-bar close (the price known when the order is sent); ATR = daily ATR(14)
            as of the prior close.
  target    prev_close (the gap fill). [R] the 1.2R test uses the decision-bar close: skip if
            |close - prev_close| < 1.2 x |close - stop| (also skips a target already passed).
  exit      stop first; the target fills only when traded through by >= $0.01 (bench10 / Workbench rule); otherwise
            flat at the 15:55 open. Booked R uses the real next-bar fill against the fixed stop; a fill at or beyond
            the stop is no trade.
Tweaks (PLAN.md) override P keys (one part each): stop_mode='atr', win_hi=1114, gap_lo=2.5.
"""
from __future__ import annotations

from datetime import time

import numpy as np

try:
    from mcf.strategies.base import Signal, Strategy
except Exception:          # research use without the package on the path
    Signal, Strategy = None, object

NAME = "BEG-04-quiet-gap-fade"
NO_SHORT = {"SQQQ", "SH", "SPXU", "SDS", "QID", "PSQ", "SPXS", "TZA", "SOXS", "UVXY", "VXX", "VIXY", "SVXY", "UVIX",
            "SVIX", "TECS", "FAZ", "LABD", "DOG", "RWM", "SRTY", "TWM", "YANG", "FNGD", "SDOW", "DXD", "TSLQ", "NVDQ"}
P = dict(min_price=15.0, min_adv=50e6, gap_lo=1.5, gap_hi=6.0, rank_min=100, rvol_max=1.5, r20_hi=949,
         win_lo=950, win_hi=1159, stop_off=0.02, atr_cap=0.35, min_tgt_r=1.2, exit_at=1555, stop_mult=1.0,
         tgt_frac=1.0, stop_mode="r20")


def vwap(h, l, c, v):
    tp = (h + l + c) / 3.0
    cv = np.cumsum(v)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cv > 0, np.cumsum(tp * v) / np.where(cv > 0, cv, 1), np.nan)


def universe_ok(prev_close, open930, adv20, rvol20, rank_rvol20, p=P):
    """-> side (+1 long after a gap down, -1 short after a gap up) or 0."""
    if not (prev_close and prev_close > 0 and open930 and open930 > 0):
        return 0
    if rvol20 is None or rank_rvol20 is None or not np.isfinite(rvol20) or not np.isfinite(rank_rvol20):
        return 0
    gap = (open930 / prev_close - 1) * 100
    ok = (prev_close >= p["min_price"] and (adv20 or 0) >= p["min_adv"] and p["gap_lo"] <= abs(gap) <= p["gap_hi"]
          and rank_rvol20 > p["rank_min"] and rvol20 < p["rvol_max"])
    return 0 if not ok else (-1 if gap > 0 else 1)


def decide(k, side, h, l, c, vw, hhmm, prev_close, atr, p=P):
    """Trigger test on the close of bar k (uses bars <= k only). -> None (no trigger), 'skip' (trigger fails the
    1.2R test) or dict(side, stop, tgt, ref)."""
    r20 = hhmm <= p["r20_hi"]
    if not r20.any() or hhmm[0] != 930:
        return None
    hi, lo = float(h[r20].max()), float(l[r20].min())
    ck = float(c[k])
    if side < 0:
        if not (ck < lo and ck < vw[k]):
            return None
        dist = min(hi + p["stop_off"] - ck, p["atr_cap"] * atr)
        if p.get("stop_mode") == "atr":                   # tweak only: a flat 0.35 x ATR stop, no R20 stop
            dist = p["atr_cap"] * atr
    else:
        if not (ck > hi and ck > vw[k]):
            return None
        dist = min(ck - (lo - p["stop_off"]), p["atr_cap"] * atr)
        if p.get("stop_mode") == "atr":
            dist = p["atr_cap"] * atr
    dist *= p.get("stop_mult", 1.0)                       # tweak only (1.0 in the base)
    if not dist > 0:
        return "skip"
    stop = ck - side * dist
    tgt = ck + p.get("tgt_frac", 1.0) * (prev_close - ck)  # tgt_frac 1.0 = prev_close (the base)
    if side * (tgt - ck) < p["min_tgt_r"] * dist:
        return "skip"
    return dict(side=side, stop=float(stop), tgt=float(tgt), ref=ck)


def find_entry(o, h, l, c, v, hhmm, side, prev_close, atr, p=P):
    """First trigger of the day -> dict(k, j, fill, side, stop, tgt, ref) or None (no trigger / skipped)."""
    vw = vwap(h, l, c, v)
    for k in np.flatnonzero((hhmm >= p["win_lo"]) & (hhmm <= p["win_hi"])):
        d = decide(k, side, h, l, c, vw, hhmm, prev_close, atr, p)
        if d is None:
            continue
        if d == "skip" or k + 1 >= len(o):
            return None
        j = k + 1
        fill = float(o[j])
        if side * (fill - d["stop"]) <= 0 or side * (d["tgt"] - fill) <= 0:
            return None
        return dict(k=int(k), j=int(j), fill=fill, **d)
    return None


def walk(o, h, l, c, hhmm, j, side, stop, tgt, p=P):
    """From the entry bar j (filled at its open). -> (px, kind, xt); kind 0 time, 1 stop, 2 target."""
    for k in range(j, len(o)):
        if hhmm[k] >= p["exit_at"]:
            return float(o[k]), 0, int(hhmm[k])
        if (side > 0 and l[k] <= stop) or (side < 0 and h[k] >= stop):
            return float(stop), 1, int(hhmm[k]) + 1          # fill at open == entry, so no gap-through on bar j
        if tgt is not None and ((side > 0 and h[k] >= tgt + 0.01) or (side < 0 and l[k] <= tgt - 0.01)):
            return float(tgt), 2, int(hhmm[k]) + 1
    return float(c[-1]), 0, int(hhmm[-1]) + 1


class Beg04QuietGapFade(Strategy):
    """Live class (mcf.strategies.base). Called on each bar close with the session's 1-minute bars so far; on the
    first trigger it emits a market signal (next bar open) with the structural stop, the prev_close target and
    exit_by 15:55. Needs ctx.avg_cum_volume (14-day) and ctx.rank_rvol20."""
    name = NAME
    max_signals_per_day = 1

    def eligible(self, ctx) -> bool:
        return ctx.prev_close >= P["min_price"] and (ctx.avg_dollar_volume or 0) >= P["min_adv"]

    def generate(self, ctx):
        p = dict(P, **getattr(self, "params", {}))
        b = ctx.bars
        if not len(b) or ctx.avg_cum_volume is None or len(ctx.avg_cum_volume) < 20:
            return []
        hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        k = len(b) - 1
        if not (p["win_lo"] <= hhmm[k] <= p["win_hi"]):
            return []
        ref = float(ctx.avg_cum_volume[19])
        rvol = float(b["volume"].to_numpy()[hhmm <= p["r20_hi"]].sum()) / ref if ref > 0 else np.nan
        side = universe_ok(ctx.prev_close, float(b["open"].iloc[0]), ctx.avg_dollar_volume, rvol,
                           ctx.rank_rvol20 if ctx.rank_rvol20 is not None else np.nan, p)
        if side == 0 or (side < 0 and ctx.symbol in NO_SHORT):
            return []
        o, h, l, c, v = (b[x].to_numpy(float) for x in ("open", "high", "low", "close", "volume"))
        vw = vwap(h, l, c, v)
        # only the first trigger of the day counts: if an earlier window bar already triggered, stay out
        for kk in np.flatnonzero((hhmm >= p["win_lo"]) & (hhmm < hhmm[k])):
            if decide(kk, side, h, l, c, vw, hhmm, ctx.prev_close, ctx.atr, p) is not None:
                return []
        d = decide(k, side, h, l, c, vw, hhmm, ctx.prev_close, ctx.atr, p)
        if not isinstance(d, dict):
            return []
        ea = p["exit_at"]
        return [Signal(symbol=ctx.symbol, strategy=self.name, side=side, bar_index=k, stop=d["stop"], target=d["tgt"],
                       entry_type="market", exit_by=time(ea // 100, ea % 100), meta={"rvol20": rvol})]
