"""Event-driven intraday backtester.

Pipeline per session date:
  1. build a DayContext per symbol (prior-day stats only -> no lookahead)
  2. rank symbols by opening relative volume ("stocks in play")
  3. each enabled strategy emits Signals; each Signal is simulated bar-by-bar
  4. candidate trades pass through the portfolio/risk filter in entry-time order

Fill assumptions (deliberately conservative):
  * market entries fill at the NEXT bar's open; stop entries fill at max(open, trigger)
  * if stop and target are both inside one bar, the stop is assumed to hit first
  * gaps through the stop fill at the bar open, not the stop price
  * slippage is charged on both sides
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import time

import numpy as np
import pandas as pd

from .. import features as F
from ..data.bars import daily_from_intraday
from ..strategies.base import PRIOR5_BARS, DayContext, Signal, Strategy, t


@dataclass
class Trade:
    symbol: str
    strategy: str
    side: int
    date: object
    signal_time: pd.Timestamp
    entry_time: pd.Timestamp
    entry: float
    stop: float
    target: float | None
    exit_time: pd.Timestamp
    exit: float
    exit_reason: str
    r_multiple: float
    mae_r: float
    mfe_r: float
    success: int = 0      # signal quality: +1R reached before -1R (rest of session, independent of exits)
    shares: int = 0
    pnl: float = 0.0
    meta: str = ""


@dataclass
class Costs:
    """Adverse fill model. Limit-order (target) exits pay no slippage; everything else does.

    Published intraday edges are a few cents/share, so per-share slippage matters more than bps
    (e.g. QQQ ORB breaks even at ~2.2c/share). Defaults are deliberately pessimistic.
    """

    bps: float = 1.0
    per_share: float = 0.01
    stop_extra_per_share: float = 0.02

    @classmethod
    def from_cfg(cls, c: dict) -> "Costs":
        return cls(c.get("slippage_bps", 1.0), c.get("slippage_per_share", 0.01), c.get("stop_slippage_per_share", 0.02))

    def entry(self, px: float, side: int) -> float:
        return px * (1 + side * self.bps / 1e4) + side * self.per_share

    def exit(self, px: float, side: int, reason: str) -> float:
        if reason == "target":
            return px
        extra = self.stop_extra_per_share if reason == "stop" else 0.0
        return px * (1 - side * self.bps / 1e4) - side * (self.per_share + extra)


def first_touch(h, l, j, fill, risk, side, times, until: time, k: float = 1.0) -> int:
    """1 if price reaches +k*R before -k*R from the fill bar until `until`; 0 otherwise.
    Both inside one bar counts as a failure (order unknown). Neither touched counts as a failure.
    This is the owner's success/fail model: it measures whether the setup called direction,
    independent of how the exit was managed."""
    up, dn = fill + side * k * risk, fill - side * k * risk
    for i in range(j, len(h)):
        if times[i] >= until:
            break
        hit_up = h[i] >= up if side == 1 else l[i] <= up
        hit_dn = l[i] <= dn if side == 1 else h[i] >= dn
        if hit_dn:
            return 0
        if hit_up:
            return 1
    return 0


def simulate(sig: Signal, bars: pd.DataFrame, flatten: time, costs: "Costs | float") -> Trade | None:
    if not isinstance(costs, Costs):
        costs = Costs(bps=costs * 1e4, per_share=0.0, stop_extra_per_share=0.0)
    o, h, l, c = (bars[k].to_numpy() for k in ("open", "high", "low", "close"))
    times = np.array(bars.index.time)
    n = len(bars)
    side = sig.side
    exit_t = min(sig.exit_by or flatten, flatten)

    j, fill = None, None
    if sig.entry_type == "market":
        j = sig.bar_index + 1
        if j >= n or times[j] >= exit_t:
            return None
        fill = o[j]
    else:
        px = sig.entry_price
        for k in range(sig.bar_index + 1, min(n, sig.bar_index + 1 + sig.entry_valid_bars)):
            if times[k] >= exit_t:
                return None
            if side == 1 and h[k] >= px:
                j, fill = k, max(o[k], px)
                break
            if side == -1 and l[k] <= px:
                j, fill = k, min(o[k], px)
                break
        if j is None:
            return None

    fill = costs.entry(fill, side)
    risk = side * (fill - sig.stop)
    if risk <= 0:
        return None
    if sig.target is not None and side * (sig.target - fill) <= 0:
        return None

    exit_px, reason, k_exit = None, None, None
    mae, mfe = 0.0, 0.0
    stop = sig.stop
    scale_px = None if not sig.scale_out_r else fill + side * sig.scale_out_r * risk
    scaled, done_frac, done_value = False, 0.0, 0.0   # value = sum(frac * exit price)
    for k in range(j, n):
        if times[k] >= exit_t:
            exit_px, reason, k_exit = o[k], "time", k
            break
        adverse = (l[k] if side == 1 else h[k])
        favorable = (h[k] if side == 1 else l[k])
        mae = min(mae, side * (adverse - fill) / risk)
        hit_stop = (l[k] <= stop) if side == 1 else (h[k] >= stop)
        hit_tgt = sig.target is not None and ((h[k] >= sig.target) if side == 1 else (l[k] <= sig.target))
        if hit_stop:
            gap_through = (o[k] < stop) if side == 1 else (o[k] > stop)
            exit_px = o[k] if (gap_through and k > j) else stop
            reason, k_exit = ("breakeven" if scaled else "stop"), k
            break
        mfe = max(mfe, side * (favorable - fill) / risk)
        if hit_tgt:
            exit_px, reason, k_exit = sig.target, "target", k
            break
        # trade management for the next bar (no look-ahead inside the current bar)
        if sig.time_stop_min and (k - j + 1) >= sig.time_stop_min and mfe < sig.time_stop_min_r and k + 1 < n:
            exit_px, reason, k_exit = o[k + 1], "timestop", k + 1
            break
        if sig.be_at_r is not None and mfe >= sig.be_at_r:
            stop = max(stop, fill) if side == 1 else min(stop, fill)
        if sig.trail_r is not None and mfe >= sig.trail_after_r:
            trail = fill + side * (mfe - sig.trail_r) * risk
            stop = max(stop, trail) if side == 1 else min(stop, trail)
        if scale_px is not None and not scaled and side * (favorable - scale_px) >= 0:
            # resting limit for part of the position; remaining stop moves to breakeven from next bar
            scaled, done_frac, done_value = True, sig.scale_out_frac, sig.scale_out_frac * scale_px
            stop = fill
    if exit_px is None:
        exit_px, reason, k_exit = c[-1], "eod", n - 1

    exit_px = costs.exit(exit_px, side, "stop" if reason in ("breakeven",) else reason)
    if reason == "stop" and side * (exit_px - fill) > -0.999 * risk:
        reason = "trail"   # a stop that had been moved up (breakeven or trailing)
    if scaled:
        exit_px = done_value + (1 - done_frac) * exit_px   # average exit price across both pieces
        reason = f"scaled+{reason}"
    r = side * (exit_px - fill) / risk
    success = first_touch(h, l, j, fill, risk, side, times, flatten)
    idx = bars.index
    # time exits fill at a bar open, so the exit timestamp is that bar's start; others at bar end
    exit_ts = idx[k_exit] if reason.endswith("time") else idx[k_exit] + pd.Timedelta(minutes=1)
    return Trade(
        symbol=sig.symbol, strategy=sig.strategy, side=side, date=idx[0].date(),
        signal_time=idx[sig.bar_index] + pd.Timedelta(minutes=1),
        entry_time=idx[j] if sig.entry_type == "market" else idx[j] + pd.Timedelta(minutes=1),
        entry=float(fill), stop=float(sig.stop),
        target=None if sig.target is None else float(sig.target),
        exit_time=exit_ts, exit=float(exit_px), exit_reason=reason,
        r_multiple=float(r), mae_r=float(mae), mfe_r=float(max(mfe, r)), success=success,
        meta=";".join(f"{k}={v:.4g}" if isinstance(v, float) else f"{k}={v}" for k, v in sig.meta.items()),
    )


class SymbolHistory:
    """Prior-day statistics for one symbol, aligned so date D only sees data from < D."""

    def __init__(self, symbol: str, intraday: pd.DataFrame, rvol_lookback: int = 14):
        self.symbol = symbol
        self.intraday = intraday
        daily = daily_from_intraday(intraday)
        self.daily = daily
        prev = daily.shift(1)
        self.prev_close = prev["close"]
        self.prev_high = prev["high"]
        self.prev_low = prev["low"]
        self.atr = F.atr(daily).shift(1)
        self.adv = (daily["close"] * daily["volume"]).rolling(20, min_periods=5).mean().shift(1)
        self.sma20 = daily["close"].rolling(20, min_periods=15).mean().shift(1)
        prof = F.cum_volume_profile(intraday)
        self.avg_cum = prof.rolling(rvol_lookback, min_periods=5).mean().shift(1)
        self.avg_cum.index = pd.to_datetime(self.avg_cum.index)
        mos = F.minute_of_session(intraday.index)
        day_open = intraday.groupby(intraday.index.date)["open"].transform("first")
        mv = pd.DataFrame({"date": intraday.index.date, "mos": mos,
                           "m": (intraday["close"] / day_open - 1).abs().to_numpy()})
        mv = mv.pivot_table(index="date", columns="mos", values="m", aggfunc="last")
        self.avg_move = mv.rolling(rvol_lookback, min_periods=5).mean().shift(1)
        self.avg_move.index = pd.to_datetime(self.avg_move.index)
        self.by_day = {d: g for d, g in intraday.groupby(intraday.index.date)}
        from ..data.bars import resample
        self.i5 = resample(intraday, "5min")

    def context(self, d) -> DayContext | None:
        ts = pd.Timestamp(d)
        bars = self.by_day.get(d)
        if bars is None or ts not in self.daily.index:
            return None
        pc, a = self.prev_close.get(ts), self.atr.get(ts)
        if pc is None or np.isnan(pc) or a is None or np.isnan(a):
            return None
        acv = self.avg_cum.loc[ts].to_numpy() if ts in self.avg_cum.index else None
        if acv is not None and np.isnan(acv).all():
            acv = None
        return DayContext(
            symbol=self.symbol, date=d, bars=bars, prev_close=float(pc),
            prev_high=float(self.prev_high[ts]), prev_low=float(self.prev_low[ts]),
            atr=float(a), avg_dollar_volume=float(self.adv.get(ts, np.nan)), avg_cum_volume=acv,
            avg_move=self.avg_move.loc[ts].to_numpy() if ts in self.avg_move.index else None,
            prior5=self.i5[self.i5.index.date < d].tail(PRIOR5_BARS),
            sma20=float(self.sma20.get(ts, np.nan)),
        )


def slot_notional(a: dict) -> float:
    """Capital per slot: equity x buying-power multiple / slots, capped by max_position_notional_pct."""
    equity = float(a["starting_equity"] if "equity" not in a else a["equity"])
    per_slot = equity * a.get("buying_power_multiple", 1.0) / a.get("slots", a["max_concurrent_positions"])
    return min(per_slot, equity * a["max_position_notional_pct"] / 100)


def is_extended(ctx: DayContext, cfg: dict) -> bool:
    """Extended tier: liquid enough to scan, too thin to trade on an ordinary day."""
    adv = ctx.avg_dollar_volume
    return not np.isnan(adv) and adv < cfg["universe"]["min_avg_dollar_volume"]


def pinned_symbols(cfg: dict) -> set[str]:
    """Symbols an enabled setup names explicitly (e.g. index ETFs). Always in the universe:
    the universe filters exist to pick names for scanned setups, not to veto a named instrument."""
    return {s for st in cfg.get("strategies", {}).values() if st.get("enabled") for s in st.get("symbols", [])}


def universe_ok(ctx: DayContext, cfg: dict) -> bool:
    """Prior-day filters shared by backtest and paper runner (no look-ahead)."""
    if ctx.symbol in pinned_symbols(cfg):
        return True
    u, c = cfg["universe"], cfg["costs"]
    adv = ctx.avg_dollar_volume
    floor = min(u.get("extended_min_avg_dollar_volume", u["min_avg_dollar_volume"]), u["min_avg_dollar_volume"])
    return (
        ctx.prev_close >= c["min_price"]
        and ctx.atr / ctx.prev_close * 100 >= u.get("min_atr_pct", 0.0)
        and (np.isnan(adv) or adv >= floor)
    )


def in_play_filter(ctxs: list, orv: list, cfg: dict) -> tuple[list, list]:
    """Extended-tier names stay only on days they are in play (opening rvol >= extended_min_rvol)."""
    need = cfg["universe"].get("extended_min_rvol", 0.0)
    keep = [i for i, c in enumerate(ctxs)
            if not is_extended(c, cfg) or (not np.isnan(orv[i]) and orv[i] >= need)]
    return [ctxs[i] for i in keep], [orv[i] for i in keep]


def rank_contexts(ctxs: list) -> None:
    """Set rank_rvol (5-minute opening rvol) and rank_rvol20 (09:30-09:49 rvol) across the day's names.
    Shared by the backtester and the live runner so both select 'stocks in play' identically."""
    for attr, k in (("rank_rvol", 4), ("rank_rvol20", 19)):
        vals = []
        for c in ctxs:
            rv = c.rvol()
            vals.append(float(rv.iloc[k]) if len(rv) > k else (float(rv.iloc[-1]) if k == 4 and len(rv) else np.nan))
        arr = np.array(vals, dtype=float)
        for rank, i in enumerate(np.argsort(-np.nan_to_num(arr, nan=-1)), 1):
            setattr(ctxs[i], attr, rank if not np.isnan(arr[i]) else None)


class Backtester:
    def __init__(self, strategies: list[Strategy], cfg: dict):
        self.strategies = strategies
        self.cfg = cfg
        self.costs = Costs.from_cfg(cfg["costs"])
        self.costs_ext = Costs.from_cfg({**cfg["costs"], "slippage_per_share": cfg["costs"].get(
            "extended_slippage_per_share", cfg["costs"].get("slippage_per_share", 0.01))})
        self.flatten = t(cfg["session"]["flatten_by"])

    def _universe_ok(self, ctx: DayContext) -> bool:
        return universe_ok(ctx, self.cfg)

    def run(self, data: dict[str, pd.DataFrame], progress: bool = False) -> pd.DataFrame:
        hist = {s: SymbolHistory(s, df) for s, df in data.items() if not df.empty}
        dates = sorted({d for h in hist.values() for d in h.by_day})
        candidates: list[Trade] = []
        for n, d in enumerate(dates):
            ctxs = [c for h in hist.values() if (c := h.context(d)) is not None and self._universe_ok(c)]
            # opening relative volume rank (first 5 minutes)
            orv = []
            for c in ctxs:
                rv = c.rvol()
                orv.append(rv.iloc[min(4, len(rv) - 1)] if len(rv) else np.nan)
            ctxs, orv = in_play_filter(ctxs, orv, self.cfg)
            rank_contexts(ctxs)
            for c in ctxs:
                for strat in self.strategies:
                    if not strat.eligible(c):
                        continue
                    for sig in strat.signals(c):
                        tr = simulate(sig, c.bars, self.flatten, self.costs_ext if is_extended(c, self.cfg) else self.costs)
                        if tr:
                            candidates.append(tr)
            if progress and n % 20 == 0:
                print(f"  {d}: {len(candidates)} candidate trades")
        return self.allocate(candidates)

    def allocate(self, cands: list[Trade]) -> pd.DataFrame:
        a = self.cfg["account"]
        equity = float(a["starting_equity"])
        risk_dollars = equity * a["risk_per_trade_pct"] / 100
        max_notional = slot_notional(a)
        cps = self.cfg["costs"]["commission_per_share"]
        accepted: list[Trade] = []
        cands.sort(key=lambda x: (x.entry_time, x.symbol))
        open_pos: list[Trade] = []
        day, day_r, day_n = None, 0.0, 0
        closed_today: list[Trade] = []
        for tr in cands:
            if tr.date != day:
                day, day_n, open_pos, closed_today = tr.date, 0, [], []
            still = []
            for p in open_pos:
                (closed_today if p.exit_time <= tr.entry_time else still).append(p)
            open_pos = still
            day_r = sum(p.r_multiple for p in closed_today)
            if (
                len(open_pos) >= a["max_concurrent_positions"]
                or sum(p.strategy == tr.strategy for p in open_pos) >= a.get("max_positions_per_strategy", 10**9)
                or day_n >= a["max_trades_per_day"]
                or day_r <= -a["max_daily_loss_r"]
                or any(p.symbol == tr.symbol for p in open_pos)
            ):
                continue
            per_share = abs(tr.entry - tr.stop)
            shares = int(min(risk_dollars / per_share, max_notional / tr.entry))
            if shares < 1:
                continue
            tr.shares = shares
            tr.pnl = tr.side * (tr.exit - tr.entry) * shares - 2 * cps * shares
            accepted.append(tr)
            open_pos.append(tr)
            day_n += 1
        df = pd.DataFrame([asdict(x) for x in accepted])
        if not df.empty:
            # R after sizing rounding & commissions, so R and $ always agree
            df["r_multiple"] = df["pnl"] / (df["shares"] * (df["entry"] - df["stop"]).abs())
        return df
