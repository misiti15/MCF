"""Pure core of the proposed long-hold runner (DESIGN.md): rebalance-day logic, target-weight diffing with a band,
deterministic client order ids (idempotency) and the risk / kill-switch checks. No broker, no I/O, no clock reads:
everything is passed in, so every rule is unit-tested (tests/test_longhold_core.py). Not wired into mcf/execution.
Educational only - not financial advice.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

PREFIX = "mcl-"


@dataclass(frozen=True)
class Order:
    symbol: str
    side: str            # "buy" | "sell"
    notional: float      # dollars (fractional shares: Alpaca notional orders, DAY/OPG)
    client_order_id: str


def rebalance_due(trading_days: list[date], today: date, freq: str = "M") -> bool:
    """True when `today` is the last trading day of its month (M) or week (W) in the exchange calendar.
    The signal is computed after that close and executed at the next open (MOO)."""
    if today not in trading_days:
        return False
    i = trading_days.index(today)
    if i == len(trading_days) - 1:
        raise ValueError("calendar must extend past today")
    nxt = trading_days[i + 1]
    if freq == "M":
        return (nxt.year, nxt.month) != (today.year, today.month)
    if freq == "W":
        return nxt.isocalendar()[:2] != today.isocalendar()[:2]
    raise ValueError(freq)


def client_order_id(strategy: str, signal_day: date, symbol: str, side: str) -> str:
    """Deterministic id: re-running the same rebalance cannot place a second order (the broker rejects a duplicate
    client_order_id). <= 48 chars as Alpaca requires."""
    base = f"{PREFIX}{strategy}-{signal_day:%Y%m%d}-{symbol}-{side[0]}"
    if len(base) <= 48:
        return base
    return base[:39] + "-" + hashlib.sha1(base.encode()).hexdigest()[:8]


def diff_orders(targets: dict[str, float], holdings: dict[str, float], equity: float, strategy: str,
                signal_day: date, band: float = 0.2, min_notional: float = 25.0) -> list[Order]:
    """Orders that move `holdings` ($ market value per symbol, this book only) toward `targets` (weights of equity).

    A held name is traded only when its drift exceeds `band` x its target weight (relative band; a name leaving or
    entering the target set always trades). Sells come first so buys are funded. Orders under `min_notional` are
    skipped. Weights must be >= 0 (long-only) and sum to <= 1."""
    if any(w < 0 for w in targets.values()) or sum(targets.values()) > 1 + 1e-9:
        raise ValueError("long-only targets summing to <= 1 expected")
    out: list[Order] = []
    for sym in sorted(set(targets) | set(holdings)):
        tw = targets.get(sym, 0.0)
        cur = holdings.get(sym, 0.0)
        want = tw * equity
        delta = want - cur
        if tw > 0 and cur > 0 and abs(delta) <= band * want:
            continue                                  # inside the band: leave it
        if abs(delta) < min_notional and tw > 0:
            continue
        if tw == 0 and cur <= 0:
            continue
        side = "buy" if delta > 0 else "sell"
        out.append(Order(sym, side, round(abs(delta), 2), client_order_id(strategy, signal_day, sym, side)))
    return sorted(out, key=lambda o: (o.side != "sell", o.symbol))


@dataclass
class RiskCaps:
    max_weight: float = 0.12          # per name (top-20 equal weight is 5 %)
    max_gross: float = 1.0            # long-only, no margin
    max_names: int = 60
    kill_drawdown: float = 0.25       # book drawdown from its high-water mark -> halt new buys, alert
    max_daily_orders: int = 150


def check_targets(targets: dict[str, float], caps: RiskCaps) -> list[str]:
    errs = []
    if len(targets) > caps.max_names:
        errs.append(f"{len(targets)} names > {caps.max_names}")
    big = [s for s, w in targets.items() if w > caps.max_weight]
    if big:
        errs.append(f"weight cap exceeded: {big}")
    if sum(targets.values()) > caps.max_gross + 1e-9:
        errs.append("gross above cap")
    return errs


def kill_switch(equity_curve: list[float], caps: RiskCaps, halt_file_present: bool = False) -> str | None:
    """Reason to halt (no new orders), or None. A manual halt file (state branch) always wins."""
    if halt_file_present:
        return "manual halt"
    if equity_curve:
        hwm = max(equity_curve)
        if hwm > 0 and equity_curve[-1] / hwm - 1 <= -caps.kill_drawdown:
            return f"drawdown {equity_curve[-1] / hwm - 1:.1%} beyond {-caps.kill_drawdown:.0%}"
    return None
