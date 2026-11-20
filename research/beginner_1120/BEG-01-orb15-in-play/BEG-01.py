# BEGINNER CANDIDATE BEG-01 ORB-15 on stocks in play (research only, not enabled in any account)
# research/beginner_1120/DESIGN.md B01; plan research/beginner_1120/BEG-01-orb15-in-play/PLAN.md.
# Educational only - not financial advice.
"""BEG-01 ORB-15 on stocks in play (long and short), written from the public rule (Zarattini, Barbon & Aziz 2024).

Live interface: `Beg01ORB15(Strategy)` (mcf.strategies.base) emits one stop-entry `Signal` per symbol-day at the 09:49
bar close: buy-stop OR15 high + $0.01 after an up 09:30-09:44 candle, sell-stop OR15 low - $0.01 after a down candle
(doji = none), working 09:50..11:29 (entry_valid_bars), stop trigger -/+ STOP_ATR x ATR capped at the far side of OR15,
target TARGET_R x R from the trigger, breakeven at +1R (be_at_r), flat 15:55 (exit_by).
Universe: U0 (price >= $5, ADV20 >= $20M) + price >= $10, RVOL20 >= 2.0, rank_rvol20 <= 20, ATR >= $0.50.
RVOL20 = 09:30-09:49 cumulative volume / its 14-session average (ctx.avg_cum_volume at minute 19).
The pure helpers `eligible_stats` / `plan_from_stats` are what the research backtest (beg01.py) calls, so the
backtest and the live class share one rule."""
from __future__ import annotations

from datetime import time

import numpy as np

try:
    from mcf.strategies.base import Signal, Strategy
except Exception:  # pragma: no cover - lets the helpers import without the package
    Signal, Strategy = None, object

NAME = "BEG-01-orb15-in-play"
SIDE = "both"
# ---- the rule as written (base). Tweaks override these through params.
PX_U0, ADV_U0 = 5.0, 20_000_000
PX_MIN, RVOL_MIN, RANK_MAX, ATR_MIN = 10.0, 2.0, 20, 0.50
STOP_ATR, TARGET_R, BE_R = 0.10, 2.0, 1.0
ORDER_FROM, ORDER_UNTIL = 950, 1130          # working on bars 09:50 .. 11:29 (fills before 11:30)
EXIT_BY = 1555
OR_END = 944                                 # OR15 = bars 09:30 .. 09:44
DECISION = 949                               # RVOL20 window 09:30 .. 09:49
NO_SHORT = {"SQQQ", "SH", "SPXU", "SDS", "SPXS", "QID", "PSQ", "UVXY", "VXX", "SVXY", "VIXY", "UVIX", "SVIX",
            "TZA", "SRTY", "RWM", "SOXS", "TECS", "FAZ", "LABD", "DOG", "DXD", "SDOW", "TWM", "YANG", "TSLQ", "NVDQ"}
LAYERS = [
    "U0: price >= $5, ADV20 >= $20M; then price >= $10, RVOL20 >= 2.0, rank_rvol20 <= 20, ATR >= $0.50",
    "09:30-09:44 candle up -> buy-stop OR15 high + 1c; down -> sell-stop OR15 low - 1c; doji -> no trade",
    "order works 09:50-11:29; one trade per symbol-day; shorts ETB only, never inverse/vol funds",
    "stop 0.10 x ATR from the trigger, never beyond the far side of OR15; target 2R; breakeven at +1R; flat 15:55",
]


def eligible_stats(px, adv20, rvol, rank, atr, p=None):
    """Universe test on the 09:49 statistics (vectorised). rank = rank of rvol inside the day's U0 (1 = highest)."""
    p = p or {}
    px, adv20, rvol, rank, atr = (np.asarray(x, float) for x in (px, adv20, rvol, rank, atr))
    with np.errstate(invalid="ignore"):
        return ((px >= PX_U0) & (adv20 >= ADV_U0) & (px >= p.get("px_min", PX_MIN)) & (rvol >= p.get("rvol_min", RVOL_MIN))
                & (rank <= p.get("rank_max", RANK_MAX)) & (atr >= p.get("atr_min", ATR_MIN)))


def plan_from_stats(o930, c944, or_hi, or_lo, atr, p=None):
    """-> side (+1/-1/0), trigger, stop, target (vectorised). side 0 = doji / no trade."""
    p = p or {}
    k, tr = p.get("stop_atr", STOP_ATR), p.get("target_r", TARGET_R)
    o930, c944, or_hi, or_lo, atr = (np.asarray(x, float) for x in (o930, c944, or_hi, or_lo, atr))
    side = np.where(c944 > o930, 1, np.where(c944 < o930, -1, 0))
    trig = np.where(side > 0, np.round(or_hi + 0.01, 2), np.round(or_lo - 0.01, 2))
    raw = trig - side * k * atr
    stop = np.where(side > 0, np.maximum(raw, or_lo), np.minimum(raw, or_hi))   # never beyond the far side of OR15
    tgt = trig + side * tr * np.abs(trig - stop)
    return side, trig, stop, tgt


class Beg01ORB15(Strategy):
    """Live class. Needs ctx.rank_rvol20 (rank inside the day's universe) and ctx.avg_cum_volume (14-day)."""
    name = NAME
    max_signals_per_day = 1

    def eligible(self, ctx):
        return ctx.atr is not None and ctx.atr >= self.params.get("atr_min", ATR_MIN) and \
            ctx.avg_dollar_volume >= ADV_U0

    def generate(self, ctx):
        b = ctx.bars
        hm = b.index.hour * 100 + b.index.minute
        if not len(b) or hm[-1] < DECISION or hm[0] != 930:
            return []
        d = int(np.flatnonzero(hm <= DECISION)[-1])
        if hm[d] != DECISION or ctx.avg_cum_volume is None or len(ctx.avg_cum_volume) < 20:
            return []
        ref = float(ctx.avg_cum_volume[19])
        rvol = float(b["volume"].iloc[: d + 1].sum()) / ref if ref > 0 else np.nan
        rank = ctx.rank_rvol20 if ctx.rank_rvol20 is not None else 10 ** 9
        px = float(b["close"].iloc[d])
        if not eligible_stats([px], [ctx.avg_dollar_volume], [rvol], [rank], [ctx.atr], self.params)[0]:
            return []
        orb = b[hm <= OR_END]
        side, trig, stop, tgt = (float(x[0]) for x in plan_from_stats(
            [b["open"].iloc[0]], [orb["close"].iloc[-1]], [orb["high"].max()], [orb["low"].min()], [ctx.atr], self.params))
        if side == 0 or (side < 0 and ctx.symbol.upper() in NO_SHORT):
            return []
        until = self.params.get("order_until", ORDER_UNTIL)
        valid = ((until // 100) * 60 + until % 100) - (9 * 60 + 50)
        return [Signal(symbol=ctx.symbol, strategy=self.name, side=int(side), bar_index=d, stop=stop, target=tgt,
                       entry_type="stop", entry_price=trig, entry_valid_bars=int(valid), exit_by=time(15, 55),
                       be_at_r=self.params.get("be_r", BE_R), meta={"rvol20": rvol, "rank": rank})]
