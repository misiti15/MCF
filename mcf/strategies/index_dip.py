"""Index open-dip bounce (owner request 2026-10-15, research/bdi/idxdip1015).

Long the bounce after the index falls from the open: the SIGNAL is read on the index ETF (`signal_symbol`, SPY for the
S&P variants, QQQ for the Nasdaq one) and the trade is placed on each symbol in `symbols` (the index ETF itself and/or
leveraged trackers such as SSO / SPUU / SPXL / UPRO / QLD / TQQQ).

Signal (index bars):
  * dip: the index's running low since the 09:30 open is at least `dip_pct` % below the open on a bar that has closed by
    `dip_by` (e.g. "down >= 0.75% by 09:45");
  * trigger, the first index bar closing inside [`entry_from`, `entry_until`] (default 09:50-10:05) after the dip, with
      - "recovery": close >= running low + `recovery_frac` x (open - running low)  (bounce off the low, default 10%)
      - "hi3":      close > the highest high of the 3 prior bars
      - "vwap":     close > the session VWAP (reclaim)
    and the index still at least `dip_pct` % below its open at the trigger low (the dip is real, not a tick).
Trade (the TRADED symbol's own bars, so levels and risk scale with its leverage automatically):
  * market entry at the next bar's open (bar_index = the traded symbol's last bar at or before the index trigger bar);
  * stop = traded running low - `stop_buffer_frac` x (traded open - traded running low);
  * target: "retrace" -> traded low + `target_frac` x (open - low) (0.5 / 0.75 / 1.0 = back to the open);
            "vwap" -> the traded symbol's VWAP at the trigger (no target if VWAP is not above the price);
            null -> no target (trailing stop / backstop only);
  * trailing stop / breakeven / time stop: the shared exit keys (`trail_r`, `trail_after_r`, `be_at_r`, ...) in R of
    the traded symbol, applied by the backtester and the live runner alike;
  * backstop: the session flatten (15:55). `exit_by` (e.g. "10:30") is a backtest comparison only - the live runner
    does not act on Signal.exit_by; use `time_stop_min` with a large `time_stop_min_r` for a live fixed-duration exit.
Sizing is the account's risk-based sizing on the traded symbol's own stop distance (RiskManager.size), so a 3x ETF gets
about a third of the shares-value of the index ETF for the same dollar risk.

Single-instrument choice (owner 2026-10-15): instead of `symbols`, a setup may give `trade_candidates` (e.g.
[SPXL, UPRO]) with `pick: max_dollar_volume`. At the trigger the setup trades ONLY the candidate with the larger dollar
volume (sum of close x volume) from 09:30 through the trigger bar, i.e. on today's tape so far (known at decision time;
ties -> the first listed). The other candidates return no signal that day. The chosen symbol, the rule and every
candidate's dollar volume go into Signal.meta (journal / backtest trade meta -> scorecard). `symbols` alone (one
setup per instrument) still works as before.

The index bars come from DayContext.peers (the poll's / session's bars of every symbol); when the traded symbol is the
signal symbol, its own bars are used. Educational only - not financial advice.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .. import features as F
from .base import DayContext, Signal, Strategy, t


def _hhmm(x):
    """A clock time from config. YAML 1.1 reads an unquoted 10:05 as the base-60 integer 605 (minutes): accept that
    form too rather than silently mis-reading it."""
    if isinstance(x, int) and not isinstance(x, bool):
        return t(f"{x // 60:02d}:{x % 60:02d}")
    return t(x)


def find_trigger(idx: pd.DataFrame, dip_pct: float, dip_by, entry_from, entry_until, trigger: str = "recovery",
                 recovery_frac: float = 0.10) -> dict | None:
    """First trigger bar on the index bars `idx` (one session, RTH, 1-minute, bar-start index), or None.
    Causal: the scan stops at the first bar that qualifies and only uses bars up to it."""
    if idx is None or len(idx) < 4:
        return None
    o = float(idx["open"].iloc[0])
    if not o > 0:
        return None
    lows, highs, closes = (idx[k].to_numpy(dtype=float) for k in ("low", "high", "close"))
    run_low = np.minimum.accumulate(lows)
    ends = idx.index + pd.Timedelta(minutes=1)            # bar close times
    end_t = np.array(ends.time)
    dip_by, entry_from, entry_until = _hhmm(dip_by), _hhmm(entry_from), _hhmm(entry_until)
    thr = o * (1 - dip_pct / 100)
    dipped = (run_low <= thr) & (end_t <= dip_by)
    if not dipped.any():
        return None
    first_dip = int(np.argmax(dipped))
    vw = F.vwap(idx).to_numpy() if trigger == "vwap" else None
    for i in range(first_dip, len(idx)):
        if end_t[i] > entry_until:
            break
        if end_t[i] < entry_from:
            continue
        lo = run_low[i]
        if lo > thr:                                      # cannot happen after first_dip; kept for clarity
            continue
        c = closes[i]
        if trigger == "recovery":
            ok = c >= lo + recovery_frac * (o - lo)
        elif trigger == "hi3":
            ok = i >= 3 and c > highs[i - 3:i].max()
        elif trigger == "vwap":
            ok = bool(np.isfinite(vw[i]) and c > vw[i])
        else:
            raise ValueError(f"unknown trigger {trigger!r}")
        if ok:
            return {"i": i, "ts": idx.index[i], "open": o, "low": float(lo), "close": float(c),
                    "drop_pct": (lo / o - 1) * 100, "low_ts": idx.index[int(np.argmin(lows[: i + 1]))]}
    return None


class IndexDipBounce(Strategy):
    """See the module docstring. Config (`class: index_dip_bounce`): symbols and/or trade_candidates + pick, signal_symbol, dip_pct, dip_by, entry_from,
    entry_until, trigger, recovery_frac, stop_buffer_frac, target ('retrace' | 'vwap' | null), target_frac, exit_by."""

    name = "index_dip_bounce"
    PICK_RULES = ("max_dollar_volume",)

    def __init__(self, **params):
        super().__init__(**params)
        rule = params.get("pick", "max_dollar_volume")
        if params.get("trade_candidates") and rule not in self.PICK_RULES:
            raise ValueError(f"unknown pick rule {rule!r} (supported: {', '.join(self.PICK_RULES)})")

    def tradeable(self) -> list[str]:
        """Every symbol this setup may trade: `trade_candidates` (one chosen per day) plus `symbols` (each traded)."""
        return list(dict.fromkeys([*self.params.get("trade_candidates", []), *self.params.get("symbols", [])]))

    def eligible(self, ctx: DayContext) -> bool:
        return ctx.symbol in set(self.tradeable())

    def _today(self, ctx: DayContext, sym: str) -> pd.DataFrame | None:
        if sym == ctx.symbol:
            return ctx.bars
        b = (getattr(ctx, "peers", None) or {}).get(sym)
        if b is None or len(b) == 0 or not len(ctx.bars):
            return None
        return b[b.index.normalize() == ctx.bars.index[0].normalize()]

    def choose(self, ctx: DayContext, ts) -> tuple[str | None, dict]:
        """The candidate to trade at decision bar `ts` (bar-start time; bars at or before it are complete): the largest
        dollar volume 09:30..ts on today's tape. Causal - later bars (full-day peers in the backtest) are ignored."""
        dv = {}
        for c in self.params.get("trade_candidates", []):
            b = self._today(ctx, c)
            seg = None if b is None else b[b.index <= ts]
            dv[c] = float((seg["close"] * seg["volume"]).sum()) if seg is not None and len(seg) else 0.0
        if not dv or max(dv.values()) <= 0:
            return None, dv
        best = max(dv.values())
        return next(c for c, v in dv.items() if v == best), dv

    def _index_bars(self, ctx: DayContext) -> pd.DataFrame | None:
        return self._today(ctx, self.params.get("signal_symbol", ctx.symbol))

    def generate(self, ctx: DayContext):
        p = self.params
        bars = ctx.bars
        if bars is None or len(bars) < 2:
            return []
        idx = self._index_bars(ctx)
        if idx is None or len(idx) < 4:
            return []
        trig = find_trigger(idx, float(p.get("dip_pct", 0.75)), p.get("dip_by", "09:45"), p.get("entry_from", "09:50"),
                            p.get("entry_until", "10:05"), p.get("trigger", "recovery"),
                            float(p.get("recovery_frac", 0.10)))
        if trig is None:
            return []
        meta = {"signal_symbol": p.get("signal_symbol", ctx.symbol), "idx_drop_pct": round(trig["drop_pct"], 3),
                "idx_low_time": f"{trig['low_ts']:%H:%M}", "trigger": p.get("trigger", "recovery")}
        if ctx.symbol not in set(p.get("symbols", [])):           # a trade_candidates setup: only the day's pick trades
            chosen, dv = self.choose(ctx, trig["ts"])
            if chosen != ctx.symbol:
                return []
            meta.update(picked=chosen, pick=p.get("pick", "max_dollar_volume"),
                        candidates=",".join(dv), **{f"dv_{c}": round(v) for c, v in dv.items()})
        # the traded symbol's last bar at or before the index trigger bar (thin trackers can skip minutes)
        k = int(bars.index.searchsorted(trig["ts"], side="right")) - 1
        sig = self.build_signal(ctx.symbol, bars, k, meta)
        return [] if sig is None else [sig]

    def build_signal(self, symbol: str, bars: pd.DataFrame, k: int, meta: dict | None = None) -> Signal | None:
        """The long Signal on the traded bars decided at bar k (stop under its running low, target per config).
        Shared with the research random-entry controls (research/bdi/idxdip1015) so both use the same exit geometry."""
        p = self.params
        if k < 0 or k >= len(bars):
            return None
        seg = bars.iloc[: k + 1]
        o = float(seg["open"].iloc[0])
        lo = float(seg["low"].min())
        px = float(seg["close"].iloc[-1])
        drop = o - lo
        if not (drop > 0 and px > lo):
            return None
        stop = lo - float(p.get("stop_buffer_frac", 0.10)) * drop
        target = None
        kind = p.get("target", "retrace")
        if kind == "retrace":
            target = lo + float(p.get("target_frac", 0.5)) * drop
            if target <= px:
                return None      # the retrace level is already behind the price: no reward left in this geometry
        elif kind == "vwap":
            vw = float(F.vwap(seg).iloc[-1])
            target = vw if np.isfinite(vw) and vw > px else None   # below the price: hold for the trail / backstop
        elif kind not in (None, "none"):
            raise ValueError(f"unknown target {kind!r}")
        meta = {**(meta or {}), "drop": round(drop, 4), "bar_time": f"{bars.index[k]:%H%M}"}
        return Signal(symbol, self.name, 1, k, stop, target, "market", exit_by=_hhmm(p.get("exit_by")), meta=meta)
