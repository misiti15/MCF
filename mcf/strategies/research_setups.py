"""Setups from the 2026-10-06 research sweep (research/setups_research.json, synthesis tiers A/B).

Each follows the synthesised spec with these MCF adaptations (stated so results are read correctly):
  * every entry is at or after 09:50 (owner's caution window)
  * cross-sectional specs (rank the whole universe) are run per symbol with the spec's fallback
    thresholds; "top 20 by 20-minute rvol" uses the shared rank_rvol20 from the engine/runner
  * where a spec needs a market-wide number we do not carry per symbol (SPY's gap, 20-day realised
    vol), a per-symbol proxy is used and named in the docstring
Status: research candidates. They trade in PAPER only after a screening backtest, and reach funds
only through the promotion gates.
"""

from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

from .. import features as F
from .base import DayContext, Signal, Strategy, t


def _idx_at(ctx: DayContext, hhmm: str) -> int | None:
    """Index of the 1-minute bar starting at hhmm, or None if not present yet."""
    want = t(hhmm)
    times = ctx.times()
    hit = np.flatnonzero(times == want)
    return int(hit[0]) if len(hit) else None


def _bars_until(ctx: DayContext, start_i: int, hhmm: str) -> int:
    """Number of bars after start_i that start before hhmm (validity window for stop entries)."""
    times = ctx.times()
    return int(((times > times[start_i]) & (times < t(hhmm))).sum())


def _liquid(ctx: DayContext, min_shares: float = 1e6, min_atr: float = 0.5) -> bool:
    shares = ctx.avg_dollar_volume / ctx.prev_close if ctx.prev_close else 0
    return ctx.prev_close >= 5 and ctx.atr >= min_atr and (np.isnan(shares) or shares >= min_shares)


class ORB20(Strategy):
    """20-minute opening range breakout on stocks in play (research id sip_orb_20m; 09:50-compliant
    sibling of the 5-minute ORB). Top `top_n` by 09:30-09:49 rvol with rvol >= min_rvol. Direction from
    the 09:30 open -> 09:49 close; optional VWAP agreement. Stop-entry at the range extreme +-1c,
    working until `entry_until`. variant 'A': stop 0.5 x range, target 0.75 x range (higher win rate);
    variant 'B': stop stop_atr x ATR, no target, held to the close (paper-style)."""

    name = "orb20"

    def eligible(self, ctx):
        return (ctx.rank_rvol20 is not None and ctx.rank_rvol20 <= self.params.get("top_n", 20)
                and _liquid(ctx))

    def generate(self, ctx: DayContext):
        i = _idx_at(ctx, "09:49")
        if i is None or i + 1 >= len(ctx.bars):
            return []
        rv = float(ctx.rvol().iloc[i])
        if not rv >= self.params.get("min_rvol", 1.5):
            return []
        rng = ctx.bars.iloc[: i + 1]
        hi, lo = float(rng["high"].max()), float(rng["low"].min())
        o, c = float(rng["open"].iloc[0]), float(rng["close"].iloc[-1])
        if c == o or hi <= lo:
            return []
        side = 1 if c > o else -1
        if self.params.get("vwap_filter", True):
            vw = float(ctx.vwap().iloc[i])
            if side * (c - vw) <= 0:
                return []
        entry = hi + 0.01 if side == 1 else lo - 0.01
        width = hi - lo
        if self.params.get("variant", "A") == "A":
            stop = entry - side * self.params.get("stop_or", 0.5) * width
            target = entry + side * self.params.get("target_or", 0.75) * width
            exit_by = t("15:50")
        else:
            stop = entry - side * self.params.get("stop_atr", 0.15) * ctx.atr
            target, exit_by = None, None
        return [Signal(ctx.symbol, self.name, side, i, stop, target, "stop", entry,
                       entry_valid_bars=_bars_until(ctx, i, self.params.get("entry_until", "11:30")),
                       exit_by=exit_by, meta={"rv20": rv, "or_width": width})]


class GapContinuation(Strategy):
    """Gap continuation on stocks in play (research id gap_continuation_in_play). |gap| >= max(3%, 1 ATR),
    09:30-09:49 rvol >= 3; at 09:50 price must hold above VWAP, the open and the range midpoint (gap-up
    long; mirror short). Stop-entry at the 09:30-09:49 extreme, working to 11:00. Stop = the closer of
    VWAP and the range's other side, at least 0.3 ATR away. Target 2R; time exit 15:55."""

    name = "gap_continuation"

    def eligible(self, ctx):
        return _liquid(ctx) and ctx.prev_close <= self.params.get("max_price", 250)

    def generate(self, ctx: DayContext):
        i = _idx_at(ctx, "09:49")
        if i is None or i + 1 >= len(ctx.bars):
            return []
        gap = ctx.gap_pct
        if abs(gap) < max(self.params.get("min_gap_pct", 3.0), 100 * ctx.atr / ctx.prev_close):
            return []
        rv = float(ctx.rvol().iloc[i])
        if not rv >= self.params.get("min_rvol", 3.0):
            return []
        side = 1 if gap > 0 else -1
        rng = ctx.bars.iloc[: i + 1]
        hi, lo = float(rng["high"].max()), float(rng["low"].min())
        o, c, vw = float(rng["open"].iloc[0]), float(rng["close"].iloc[-1]), float(ctx.vwap().iloc[i])
        mid = (hi + lo) / 2
        if side * (c - vw) <= 0 or side * (c - o) <= 0 or side * (c - mid) <= 0:
            return []
        if side == -1 and c <= ctx.prev_close * 0.90:
            return []  # short-sale restriction territory: paper would fill what a real book will not
        entry = hi + 0.01 if side == 1 else lo - 0.01
        near = max(vw, lo) if side == 1 else min(vw, hi)
        stop = min(near, entry - 0.3 * ctx.atr) if side == 1 else max(near, entry + 0.3 * ctx.atr)
        risk = abs(entry - stop)
        tr = self.params.get("target_r", 2.0)
        return [Signal(ctx.symbol, self.name, side, i, stop, entry + side * tr * risk if tr else None, "stop", entry,
                       entry_valid_bars=_bars_until(ctx, i, self.params.get("entry_until", "11:00")),
                       exit_by=t("15:55"), meta={"gap": gap, "rv20": rv})]


class GapBelowSMA20Short(Strategy):
    """Short a gap down through the 20-day SMA (research id gap_down_below_sma20_short; QuantRocket
    'sell-gap' idea). Prior close above SMA20, today's open below it and below the prior close; at the
    09:49 close price is still below the open and the SMA and not down 10% (SSR). Short at market,
    stop above the 09:30-09:49 high + 0.05 ATR, hold to the close. `mirror` adds the long version
    (gap up through SMA20 after closing below it)."""

    name = "gap_sma20"

    def eligible(self, ctx):
        return _liquid(ctx, min_atr=0.0) and np.isfinite(ctx.sma20)

    def generate(self, ctx: DayContext):
        i = _idx_at(ctx, "09:49")
        if i is None:
            return []
        rng = ctx.bars.iloc[: i + 1]
        o, c = float(rng["open"].iloc[0]), float(rng["close"].iloc[-1])
        sides = [-1] + ([1] if self.params.get("mirror", False) else [])
        out = []
        for side in sides:
            crossed = (ctx.prev_close > ctx.sma20 > o and o < ctx.prev_close) if side == -1 else (
                ctx.prev_close < ctx.sma20 < o and o > ctx.prev_close)
            if not crossed or abs(ctx.gap_pct) < self.params.get("min_gap_pct", 0.0):
                continue
            if side == -1 and not (c < o and c < ctx.sma20 and c > ctx.prev_close * 0.90):
                continue
            if side == 1 and not (c > o and c > ctx.sma20):
                continue
            ext = float(rng["high"].max()) if side == -1 else float(rng["low"].min())
            stop = ext - side * self.params.get("stop_atr", 0.05) * ctx.atr
            out.append(Signal(ctx.symbol, self.name, side, i, stop, None, "market", meta={"gap": ctx.gap_pct}))
        return out


class IndexGapFill(Strategy):
    """Fade small index-ETF gaps (research id index_small_gap_fill). 0.10% <= |gap| <= 0.40%, not filled by
    09:49 and not extended more than 1 x gap beyond the open. Enter against the gap at the 09:49 close;
    target the prior close; stop beyond the 09:30-09:49 extreme by max(stop_gap_mult x gap, 0.10%);
    exit at 12:00. Judged on expectancy and worst day, not fill rate."""

    name = "index_gap_fill"

    def eligible(self, ctx):
        return ctx.symbol in set(self.params.get("symbols", ["SPY", "QQQ", "IWM"]))

    def generate(self, ctx: DayContext):
        i = _idx_at(ctx, "09:49")
        if i is None:
            return []
        g = ctx.gap_pct / 100
        if not (self.params.get("min_gap", 0.001) <= abs(g) <= self.params.get("max_gap", 0.004)):
            return []
        rng = ctx.bars.iloc[: i + 1]
        o, c = float(rng["open"].iloc[0]), float(rng["close"].iloc[-1])
        pc = ctx.prev_close
        if g > 0 and (rng["low"].min() <= pc or c - o > abs(g) * pc):
            return []
        if g < 0 and (rng["high"].max() >= pc or o - c > abs(g) * pc):
            return []
        side = -1 if g > 0 else 1
        ext = float(rng["high"].max()) if side == -1 else float(rng["low"].min())
        buf = max(self.params.get("stop_gap_mult", 1.5) * abs(g) * pc, 0.001 * c)
        stop = ext - side * buf
        return [Signal(ctx.symbol, self.name, side, i, stop, pc, "market", exit_by=t("12:00"), meta={"gap": ctx.gap_pct})]


class CloseMomentumGated(Strategy):
    """Last-half-hour index momentum with the research gate (research id market_intraday_momentum_close).
    At the 15:29 close, r = close / prior close - 1; trade in its direction into 15:55 only when
    |r| >= gate_mult x the instrument's daily ATR% (proxy for '0.5 x its 20-day mean |r|') AND
    (|r| >= 1% OR daily ATR% >= vol_gate_pct, the proxy for 20%+ annualised volatility)."""

    name = "close_momentum"

    def eligible(self, ctx):
        return ctx.symbol in set(self.params.get("symbols", ["SPY", "QQQ", "IWM"]))

    def generate(self, ctx: DayContext):
        i = _idx_at(ctx, "15:29")
        if i is None or i + 1 >= len(ctx.bars):
            return []
        c = float(ctx.bars["close"].iloc[i])
        r = c / ctx.prev_close - 1
        atr_pct = ctx.atr / ctx.prev_close
        if abs(r) < self.params.get("gate_mult", 0.5) * atr_pct:
            return []
        if not (abs(r) >= 0.01 or atr_pct * 100 >= self.params.get("vol_gate_pct", 1.26)):
            return []
        side = 1 if r > 0 else -1
        stop = c - side * self.params.get("stop_atr", 0.5) * ctx.atr
        return [Signal(ctx.symbol, self.name, side, i, stop, None, "market", meta={"r_rod": r})]


class EODReversal(Strategy):
    """End-of-day reversal, long leg (research id eod_reversal_xs, per-symbol fallback of 'bottom 30 names
    with ROD <= -2%'). Liquid names ($20M+ ADV) down at least `min_drop_pct` from the prior close at the
    15:29 close, excluding gaps beyond 8% (news proxy): buy at 15:30, exit 15:55, catastrophic stop
    1 x ATR / sqrt(13)."""

    name = "eod_reversal"

    def eligible(self, ctx):
        return ctx.prev_close >= 5 and ctx.avg_dollar_volume >= self.params.get("min_adv", 20e6)

    def generate(self, ctx: DayContext):
        i = _idx_at(ctx, "15:29")
        if i is None or i + 1 >= len(ctx.bars) or abs(ctx.gap_pct) >= 8:
            return []
        c = float(ctx.bars["close"].iloc[i])
        rod = (c / ctx.prev_close - 1) * 100
        if rod > -self.params.get("min_drop_pct", 2.0):
            return []
        stop = c - ctx.atr / np.sqrt(13)
        return [Signal(ctx.symbol, self.name, 1, i, stop, None, "market", meta={"rod": rod})]


class VWAPPullbackInPlay(Strategy):
    """VWAP pullback in a trending stock in play (research id vwap_pullback_in_play). In play: rvol(09:30-09:49)
    >= 2 and (|gap| >= 2% or the 09:30-09:49 range >= 0.5 ATR), top 20 by that rvol. Trend: >= 15 of the
    last 20 closes on the trend side of VWAP and VWAP rising (falling for shorts). Trigger: a bar touches
    VWAP (within 0.05 ATR) without retracing > 50% of the open-to-extreme move, then a close back on the
    trend side within 3 bars. Stop-entry 1c beyond the reclaim bar, valid 3 bars, 09:50-12:00; stop at
    min(pullback low - 0.05 ATR, VWAP - 0.15 ATR); target 1.5R; exit 15:50."""

    name = "vwap_pullback"

    def eligible(self, ctx):
        return (ctx.rank_rvol20 is not None and ctx.rank_rvol20 <= self.params.get("top_n", 20) and _liquid(ctx))

    def generate(self, ctx: DayContext):
        i0 = _idx_at(ctx, "09:49")
        if i0 is None or len(ctx.bars) < i0 + 5:
            return []
        rng = ctx.bars.iloc[: i0 + 1]
        if not float(ctx.rvol().iloc[i0]) >= self.params.get("min_rvol", 2.0):
            return []
        if not (abs(ctx.gap_pct) >= 2 or (rng["high"].max() - rng["low"].min()) >= 0.5 * ctx.atr):
            return []
        b = ctx.bars
        c, h, l = b["close"].to_numpy(), b["high"].to_numpy(), b["low"].to_numpy()
        vw = ctx.vwap().to_numpy()
        times = ctx.times()
        o = float(b["open"].iloc[0])
        tol, end = 0.05 * ctx.atr, t(self.params.get("entry_until", "12:00"))
        for side in (1, -1):
            for j in range(max(i0 + 1, 20), len(b) - 1):
                if times[j] >= end:
                    break
                above = (c[j - 20:j] > vw[j - 20:j]) if side == 1 else (c[j - 20:j] < vw[j - 20:j])
                if above.sum() < 15 or side * (vw[j] - vw[j - 20]) <= 0:
                    continue
                touched = (l[j] <= vw[j] + tol) if side == 1 else (h[j] >= vw[j] - tol)
                if not touched:
                    continue
                ext = h[: j + 1].max() if side == 1 else l[: j + 1].min()
                move = side * (ext - o)
                if move <= 0 or side * (ext - (l[j] if side == 1 else h[j])) > 0.5 * move:
                    continue
                for k in range(j, min(j + 3, len(b) - 1)):
                    if side * (c[k] - vw[k]) > 0:
                        entry = h[k] + 0.01 if side == 1 else l[k] - 0.01
                        pull = l[j:k + 1].min() if side == 1 else h[j:k + 1].max()
                        stop = (min(pull - 0.05 * ctx.atr, vw[k] - 0.15 * ctx.atr) if side == 1
                                else max(pull + 0.05 * ctx.atr, vw[k] + 0.15 * ctx.atr))
                        risk = abs(entry - stop)
                        return [Signal(ctx.symbol, self.name, side, k, stop, entry + side * 1.5 * risk, "stop", entry,
                                       entry_valid_bars=3, exit_by=t("15:50"), meta={"vwap": float(vw[k])})]
        return []


RESEARCH_REGISTRY = {s.name: s for s in (ORB20, GapContinuation, GapBelowSMA20Short, IndexGapFill,
                                          CloseMomentumGated, EODReversal, VWAPPullbackInPlay)}
