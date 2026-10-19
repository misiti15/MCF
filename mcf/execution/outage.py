"""Data-outage protection helpers (owner 2026-10-16, steps 3-6 of the outage plan; docs/OPERATIONS.md "Outage plan").

Shared by the runner's escalation (live.outage) and the independent watchdog (mcf.execution.watchdog):
  * open_lots(): every open MCF lot from the broker's own orders (filled entry parent whose stop leg is still working)
  * protect_open_lots(): move the stop of every lot that is in profit (by the broker's last known position price) to
    breakeven, through that lot's own stop leg only
  * flatten_prefix(): cancel this system's open orders (prefix only) and close the positions it traded today

Only orders whose client order id starts with the account's MCF prefix (mcf- / mct- / mt2- / mcg-) are ever touched; the
long-hold book (mcl-) and anything else on an account are never read for action. No emails or alerts.
Educational only - not financial advice."""

from __future__ import annotations

import time as _time

import pandas as pd

NY = "America/New_York"
MCF_PREFIXES = ("mcf-", "mct-", "mt2-", "mcg-")   # mcg- = Setup Generator account (2026-10-19)
DEFAULTS = {"enabled": True, "enter_pause_min": 5, "protect_min": 15, "flatten_min": 30, "watchdog_dead_min": 15}


def outage_cfg(live: dict) -> dict:
    """live.outage merged over the defaults (enabled, enter_pause_min, protect_min, flatten_min, watchdog_dead_min)."""
    o = {**DEFAULTS, **((live or {}).get("outage") or {})}
    o["enabled"] = bool(o.get("enabled"))
    for k in ("enter_pause_min", "protect_min", "flatten_min", "watchdog_dead_min"):
        o[k] = float(o[k])
    return o


def _state(o) -> str:
    return str(getattr(getattr(o, "status", None), "value", getattr(o, "status", ""))).lower()


def _side(o) -> int:
    return 1 if str(getattr(o.side, "value", o.side)).lower() == "buy" else -1


def check_prefix(prefix: str) -> str:
    if prefix not in MCF_PREFIXES:
        raise ValueError(f"refusing to act on order prefix {prefix!r}: only {MCF_PREFIXES}")
    return prefix


def open_lots(broker, prefix: str, after=None) -> list[dict]:
    """Open MCF lots: today's filled entry parents (prefix-setup-symbol-day[-HHMM]) whose stop leg is still working."""
    from .alpaca_broker import AlpacaBroker
    from .runner import parse_coid

    after = after or pd.Timestamp.now(tz=NY).normalize().to_pydatetime()
    out = []
    for o in broker.orders_today_with_prefix(prefix, after):
        if parse_coid(o.client_order_id, prefix) is None:
            continue                                  # exits (-x), flatten closes
        filled = float(getattr(o, "filled_qty", 0) or 0)
        if filled <= 0 or not getattr(o, "filled_avg_price", None):
            continue
        stop = next((leg for leg in (getattr(o, "legs", None) or []) if getattr(leg, "stop_price", None) is not None
                     and _state(leg) in AlpacaBroker.OPEN_STATES), None)
        if stop is None:
            continue                                  # closed by its own legs, or no stop to move
        out.append({"symbol": o.symbol, "coid": o.client_order_id, "side": _side(o), "qty": filled,
                    "entry": float(o.filled_avg_price), "stop": float(stop.stop_price)})
    return out


def protect_open_lots(broker, prefix: str, after=None) -> dict:
    """Breakeven for every open lot in profit by the broker's last known price (position current_price). A lot not in
    profit, or whose stop is already at/through breakeven, is left alone. Returns {moved, skipped, errors}."""
    check_prefix(prefix)
    held = broker.positions()
    moved, skipped, errors = [], [], []
    for lot in open_lots(broker, prefix, after):
        pos = held.get(lot["symbol"])
        px = float(getattr(pos, "current_price", None) or "nan") if pos is not None else float("nan")
        side, entry, stop = lot["side"], lot["entry"], lot["stop"]
        rec = {"symbol": lot["symbol"], "coid": lot["coid"], "entry": entry, "stop": stop, "price": px}
        if not side * (px - entry) > 0:
            skipped.append({**rec, "why": "not in profit"})
            continue
        new = round(entry, 2)
        if side * (new - stop) <= 0.005:
            skipped.append({**rec, "why": "stop already at or past breakeven"})
            continue
        try:
            broker.move_lot_stop(lot["symbol"], lot["coid"], new, prefix)
            moved.append({**rec, "new_stop": new})
        except Exception as e:                        # a rejected replace must not stop the other lots
            errors.append({**rec, "error": str(e)[:200]})
    return {"moved": moved, "skipped": skipped, "errors": errors}


def mcf_symbols_today(broker, prefix: str, after=None) -> set[str]:
    after = after or pd.Timestamp.now(tz=NY).normalize().to_pydatetime()
    return {o.symbol for o in broker.orders_today_with_prefix(prefix, after)}


def open_order_count(broker, prefix: str, after=None) -> int:
    """This system's working orders today (parents and bracket legs)."""
    from .alpaca_broker import AlpacaBroker

    after = after or pd.Timestamp.now(tz=NY).normalize().to_pydatetime()
    n = 0
    for o in broker.orders_today_with_prefix(prefix, after):
        n += _state(o) in AlpacaBroker.OPEN_STATES
        n += sum(_state(leg) in AlpacaBroker.OPEN_STATES for leg in (getattr(o, "legs", None) or []))
    return n


def flatten_prefix(broker, prefix: str, symbols: set[str] | None = None, sleep=None, passes: int = 3) -> list[str]:
    """The runner's flatten path (PaperRunner.flatten_mcf) for a process without runner state (the watchdog): cancel this
    system's open orders (parents and legs, prefix only), then close every position on a symbol it traded today.
    Returns the symbols still open afterwards."""
    check_prefix(prefix)
    sleep = sleep or _time.sleep
    mine = set(symbols or ()) | mcf_symbols_today(broker, prefix)
    broker.cancel_orders_with_prefix(prefix)
    left = []
    for attempt in range(passes):
        left = sorted(mine & set(broker.positions()))
        if not left:
            break
        for sym in left:
            try:
                if not broker.close_mcf_position(sym, prefix, sleep=sleep):
                    print(f"close {sym} not confirmed (pass {attempt + 1})")
            except Exception as e:
                print(f"close {sym} failed: {e}")
        sleep(3)
    return sorted(mine & set(broker.positions()))
