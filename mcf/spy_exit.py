"""SPY-since-entry exit (owner "SPYEXIT build yes", 2026-11-16; spec research/workbench/UPDAY/L3-gap-slope-fromopen-FD/
RESULTS.md "Runner spec"). Opt-in per setup, default OFF:

    spy_exit_pct: 0.30           # close a SHORT once SPY is up >= 0.30 % since the lot's entry (a LONG: SPY down >= 0.30 %)
    spy_exit_only_losing: false  # true: only while the lot is under water

spy0 = SPY's last completed 1-minute close at the entry minute. The live runner (mcf/execution/runner.py manage()), the
shadow book (mcf/execution/shadow.py) and the backtest engine (mcf/backtest/engine.py simulate(), bar t-1 SPY close vs
spy0, exit at bar t open, as the UPDAY bench code/sim3.py walk does) all decide through spy_exit_hit() so research and
live use one rule. Missing / stale SPY -> no exit (fail safe). Exit reason "spy_exit" (a market exit for costs).
Educational only - not financial advice."""

from __future__ import annotations

import math

SPY = "SPY"
REASON = "spy_exit"
TAG = ";spy_exit"          # appended to the journal order's meta when the runner closes a lot this way
KEYS = ("spy_exit_pct", "spy_exit_only_losing")
EPS = 1e-9


def _num(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def spy_move_pct(spy0, spy_now) -> float | None:
    """SPY % change since the entry reference; None when either price is missing or not positive."""
    a, b = _num(spy0), _num(spy_now)
    if a is None or b is None or a <= 0 or b <= 0:
        return None
    return (b / a - 1) * 100


def spy_exit_hit(side: int, spy0, spy_now, pct, only_losing: bool = False, under_water: bool | None = None) -> bool:
    """True when the lot should close: SHORT (side -1) and SPY up >= pct % since entry, LONG (side +1) and SPY down
    >= pct %. With only_losing, also only while the lot is under water (under_water None = unknown -> no exit)."""
    p = _num(pct)
    if p is None or p <= 0:
        return False
    move = spy_move_pct(spy0, spy_now)
    if move is None:
        return False
    if int(side) == -1:
        hit = move >= p - EPS
    elif int(side) == 1:
        hit = move <= -p + EPS
    else:
        return False
    if hit and only_losing:
        return bool(under_water)
    return hit


def enabled(strategies) -> bool:
    """Any setup with spy_exit_pct set (the runner then polls SPY every minute)."""
    return any(_num((getattr(s, "params", None) or {}).get("spy_exit_pct")) for s in strategies)
