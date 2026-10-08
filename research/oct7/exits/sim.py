"""simulate() from mcf.backtest.engine, copied line for line, plus three research-only exit rules
(none of them is in production; the base path is verified identical to engine.simulate in study.py):
  gb=(x, y)    give-back lock on closes: once the best excursion reached x R, exit at the next bar's open when a
               bar CLOSES at or below y R open profit (market exit, normal slippage).
  lock=(x, y)  give-back lock as a resting stop: once the best excursion reached x R, the stop moves to +y R.
  late=(hh:mm, m)  late-day profit take: from hh:mm on, exit at the first bar open where open profit > m R.
Educational only - not financial advice."""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

from mcf.backtest.engine import Costs, Trade, first_touch
from mcf.strategies.base import Signal


def simulate2(sig: Signal, bars: pd.DataFrame, flatten: time, costs: Costs, gb=None, lock=None, late=None,
              _arr=None) -> Trade | None:
    o, h, l, c, times = _arr if _arr is not None else (*(bars[k].to_numpy() for k in ("open", "high", "low", "close")),
                                                        np.array(bars.index.time))
    n = len(o)
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
    scaled, done_frac, done_value = False, 0.0, 0.0
    for k in range(j, n):
        if times[k] >= exit_t:
            exit_px, reason, k_exit = o[k], "time", k
            break
        if late is not None and times[k] >= late[0] and k > j and side * (o[k] - fill) / risk > late[1]:
            exit_px, reason, k_exit = o[k], "late", k
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
        if sig.time_stop_min and (k - j + 1) >= sig.time_stop_min and mfe < sig.time_stop_min_r and k + 1 < n:
            exit_px, reason, k_exit = o[k + 1], "timestop", k + 1
            break
        if gb is not None and mfe >= gb[0] and side * (c[k] - fill) / risk <= gb[1] and k + 1 < n:
            exit_px, reason, k_exit = o[k + 1], "giveback", k + 1
            break
        if sig.be_at_r is not None and mfe >= sig.be_at_r:
            stop = max(stop, fill) if side == 1 else min(stop, fill)
        if lock is not None and mfe >= lock[0]:
            lk = fill + side * lock[1] * risk
            stop = max(stop, lk) if side == 1 else min(stop, lk)
        if sig.trail_r is not None and mfe >= sig.trail_after_r:
            trail = fill + side * (mfe - sig.trail_r) * risk
            stop = max(stop, trail) if side == 1 else min(stop, trail)
        if scale_px is not None and not scaled and side * (favorable - scale_px) >= 0:
            scaled, done_frac, done_value = True, sig.scale_out_frac, sig.scale_out_frac * scale_px
            stop = fill
    if exit_px is None:
        exit_px, reason, k_exit = c[-1], "eod", n - 1

    exit_px = costs.exit(exit_px, side, "stop" if reason in ("breakeven",) else reason)
    if reason == "stop" and side * (exit_px - fill) > -0.999 * risk:
        reason = "trail"
    if scaled:
        exit_px = done_value + (1 - done_frac) * exit_px
        reason = f"scaled+{reason}"
    r = side * (exit_px - fill) / risk
    success = first_touch(h, l, j, fill, risk, side, times, flatten)
    idx = bars.index
    exit_ts = idx[k_exit] if reason.endswith("time") or reason == "late" else idx[k_exit] + pd.Timedelta(minutes=1)
    return Trade(
        symbol=sig.symbol, strategy=sig.strategy, side=side, date=idx[0].date(),
        signal_time=idx[sig.bar_index] + pd.Timedelta(minutes=1),
        entry_time=idx[j] if sig.entry_type == "market" else idx[j] + pd.Timedelta(minutes=1),
        entry=float(fill), stop=float(sig.stop),
        target=None if sig.target is None else float(sig.target),
        exit_time=exit_ts, exit=float(exit_px), exit_reason=reason,
        r_multiple=float(r), mae_r=float(mae), mfe_r=float(max(mfe, r)), success=success,
        meta="",
    )
