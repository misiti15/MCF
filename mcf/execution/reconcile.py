"""Turn Alpaca order fills into journal trades (entry, exit, R, P/L) plus fill-realism measures.

Paper fills are optimistic (no queue, no size limit, limit orders fill on a touch). Each trade records:
  slip_bps  entry fill vs the price when the signal fired (latency + spread; MarcoFlow lost ~16 bps here)
  pnl_adj   broker P/L minus the stop-exit slippage a real book adds (costs.stop_slippage_per_share);
            target (limit) exits are kept but flagged `touch_fill` in meta when not verifiable.

Lots (live.max_lots_per_symbol > 1): several brackets can hold the same symbol, netted at the broker. An exit is
paired to a lot only from orders that belong to it (its own stop/target legs, their replacements after a stop move,
its own `<parent client id>-x` exit), plus - for whatever quantity those did not close - a genuine flatten close: a
filled closing order on the symbol that belongs to NO bracket (no leg, no replacement, no -x, no entry). Flatten closes
are shared out in fill-time order, each lot taking at most its remaining quantity, so a flatten that closed N shares
never closes more than N shares of lots. A lot whose legs are still working is open, whatever else filled on the
symbol (2026-10-13 autopsy: 9 lots were booked closed at a sibling lot's stop fill while their shares were held).
A lot closed by more than one fill (a partly filled target, the remainder by stop or flatten) gets one row at the
quantity-weighted exit price, so its P/L is exact; meta records the parts (`exit_parts=target:10@12.0,flatten:8@10.5`).
"""

from __future__ import annotations

import pandas as pd

OPEN = {"new", "accepted", "held", "pending_new", "partially_filled", "pending_replace", "accepted_for_bidding",
        "pending_cancel", "calculated", "stopped", "pending_review"}


def reconcile_day(broker, journal, run_id: int, day, cfg: dict | None = None) -> pd.DataFrame:
    stop_extra = (cfg or {}).get("costs", {}).get("stop_slippage_per_share", 0.02)
    after = pd.Timestamp(f"{day} 00:00", tz="America/New_York")
    orders = journal.open_orders(run_id)
    if orders.empty:
        return pd.DataFrame()
    # Orders left open in the journal from earlier sessions (e.g. missed by a truncated broker query) are picked up
    # too: look back to the oldest one, at most 7 days. Each trade is dated by its entry fill, not by `day`.
    oldest = pd.to_datetime(orders["created_at"], utc=True, errors="coerce").min()
    if pd.notna(oldest):
        floor = after - pd.Timedelta(days=7)
        after = max(floor, min(after, oldest.tz_convert("America/New_York").normalize()))
    after = after.to_pydatetime()
    by_id = {str(o.id): o for o in broker.closed_orders_today(after)}
    lots = _lot_exits(by_id, set(orders.broker_order_id.astype(str)))
    rows, residual = [], {}
    for _, rec in orders.iterrows():
        parent = by_id.get(rec.broker_order_id)
        if parent is None:
            continue
        if parent.filled_avg_price is None:
            if _state(parent) in DEAD and not _f(getattr(parent, "filled_qty", 0)):
                journal.update_order_status(rec.broker_order_id, "expired")   # never filled: not a lot, not a trade
            continue
        lot = lots.get(rec.broker_order_id)
        if lot is not None and not lot["closed"] and lot["parts"]:
            residual[rec.broker_order_id] = {"left": lot["left"], "qty": lot["qty"]}   # partly closed, rest held
        if lot is None or not lot["closed"]:
            continue  # still open: a leg is working, or part of its quantity has no paired close yet
        entry, qty, parts = lot["entry"], lot["qty"], lot["parts"]
        exit_px = sum(q * px for q, px, _, _ in parts) / qty
        exit_t = max(t for _, _, t, _ in parts)
        by_reason: dict[str, float] = {}
        for q, _, _, why in parts:
            by_reason[why] = by_reason.get(why, 0.0) + q
        reason = max(by_reason, key=by_reason.get)          # the exit that closed most of the lot
        stop_qty = by_reason.get("stop", 0.0)
        side = int(rec.side)
        risk = abs(entry - rec.stop) * qty
        pnl = sum(side * (px - entry) * q for q, px, _, _ in parts)
        pnl_adj = pnl - stop_extra * stop_qty
        meta = rec.meta + (";touch_fill" if "target" in by_reason else "")
        if len(parts) > 1:
            meta += ";exit_parts=" + ",".join(f"{w}:{q:g}@{px:g}" for q, px, _, w in parts)
        rows.append(dict(
            symbol=rec.symbol, strategy=rec.strategy, side=side, date=_et_date(parent.filled_at, day),
            signal_time=rec.created_at, entry_time=parent.filled_at, entry=entry, stop=rec.stop,
            target=rec.target, exit_time=exit_t, exit=exit_px, exit_reason=reason,
            r_multiple=pnl / risk if risk else 0.0, mae_r=None, mfe_r=None, shares=qty, pnl=pnl,
            meta=meta, broker_order_id=rec.broker_order_id,
            slip_bps=side * (entry - rec.entry_ref) / rec.entry_ref * 1e4 if rec.entry_ref else None,
            pnl_adj=pnl_adj,
        ))
        journal.update_order_status(rec.broker_order_id, "closed")
    out = pd.DataFrame(rows)
    out.attrs["residual"] = residual   # parent id -> {left, qty}: lots still open after a partial exit (status only)
    return out


def _lot_exits(by_id: dict, journal_ids: set[str]) -> dict[str, dict]:
    """parent id -> {entry, qty, parts [(qty, px, time, reason)], closed} for every filled entry (lot) in by_id."""
    parents = {i: o for i, o in by_id.items() if getattr(o, "legs", None) or i in journal_ids}
    owner: dict[str, str] = {}                 # order id -> parent id (its legs, their replacements, its -x exit)
    owned: dict[str, dict[str, object]] = {i: {} for i in parents}
    coid_parent = {str(getattr(p, "client_order_id", "") or ""): i for i, p in parents.items()}
    coid_parent.pop("", None)
    for i, p in parents.items():
        for leg in getattr(p, "legs", None) or []:
            lid = _oid(leg)
            owner[lid] = i
            owned[i][lid] = leg
    everything = list(by_id.values()) + [leg for p in parents.values() for leg in getattr(p, "legs", None) or []]
    changed = True
    while changed:                             # replacement chains (a moved stop is a new order replacing the leg)
        changed = False
        for o in everything:
            oid = _oid(o)
            if oid in owner or oid in parents:
                continue
            coid = str(getattr(o, "client_order_id", "") or "")
            rep = getattr(o, "replaces", None)
            pid = None
            if coid.endswith("-x") and coid[:-2] in coid_parent:
                pid = coid_parent[coid[:-2]]
            elif rep is not None and str(rep) in owner:
                pid = owner[str(rep)]
            if pid is not None:
                owner[oid] = pid
                owned[pid][oid] = o
                changed = True

    lots: dict[str, dict] = {}
    for i, p in parents.items():
        if p.filled_avg_price is None or not _f(getattr(p, "filled_qty", 0)):
            continue
        qty = int(_f(p.filled_qty))
        parts, working, ended = [], False, None
        for o in owned[i].values():
            if _state(o) in OPEN:
                working = True
            if o.filled_avg_price is None:
                ca = getattr(o, "canceled_at", None)
                ended = ca if ca is not None and (ended is None or ca > ended) else ended
                continue
            coid = str(getattr(o, "client_order_id", "") or "")
            fq = _f(getattr(o, "filled_qty", None)) or (qty - sum(q for q, *_ in parts))   # fakes w/o filled_qty
            why = "timestop" if coid.endswith("-x") else (
                "target" if _v(getattr(o, "order_type", "")) == "limit" else "stop")
            parts.append((fq, float(o.filled_avg_price), o.filled_at, why))
        parts.sort(key=lambda x: _ts(x[2]))
        lots[i] = dict(entry=float(p.filled_avg_price), qty=qty, parts=parts, working=working, ended=ended,
                       symbol=p.symbol, side=_side(p), entry_t=p.filled_at,
                       left=qty - sum(q for q, *_ in parts))

    # genuine flatten closes: filled, belong to no bracket (not a leg, a replacement, a -x exit, or an entry)
    # (a bracket/OTO leg returned as its own row, e.g. on a page without its parent, is never a flatten close)
    flat = sorted((o for i, o in by_id.items() if i not in owner and i not in parents and not getattr(o, "legs", None)
                   and _v(getattr(o, "order_class", None) or "simple") in ("simple", "")
                   and o.filled_avg_price is not None and _f(getattr(o, "filled_qty", None)) > 0 and o.filled_at),
                  key=lambda o: _ts(o.filled_at))
    room = {_oid(o): _f(o.filled_qty) for o in flat}
    for i, lot in sorted(lots.items(), key=lambda kv: _ts(kv[1]["entry_t"])):
        if lot["working"] or lot["left"] <= 1e-9:
            continue
        need, take = lot["left"], []
        for o in flat:
            if need <= 1e-9:
                break
            oid = _oid(o)
            if (o.symbol != lot["symbol"] or room[oid] <= 1e-9 or _side(o) is None or _side(o) == lot["side"]
                    or _ts(o.filled_at) <= _ts(lot["entry_t"])
                    or (lot["ended"] is not None and _ts(o.filled_at) < _ts(lot["ended"]))):
                continue
            q = min(need, room[oid])
            take.append((oid, q, o))
            need -= q
        if need > 1e-9:
            continue                                    # no flatten close covers its remaining shares: still open
        for oid, q, o in take:
            room[oid] -= q
            lot["parts"].append((q, float(o.filled_avg_price), o.filled_at, "flatten"))
        lot["left"] = 0.0
    for lot in lots.values():
        # A lot whose own fills (legs, replacements, -x, flatten share) cover its whole quantity is flat, even if an
        # OCO sibling leg still reports an open state (e.g. pending_cancel / held a moment after the target filled):
        # it holds no shares, so it is released now rather than at a later poll or the flatten (2026-10-15 H-4).
        lot["closed"] = lot["left"] <= 1e-9 and bool(lot["parts"])
    return lots


DEAD = {"canceled", "cancelled", "expired", "rejected", "done_for_day", "replaced"}


def _f(x) -> float:
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def _oid(o) -> str:
    i = getattr(o, "id", None)
    return str(i) if i is not None else f"obj-{id(o)}"


def _ts(t):
    return pd.Timestamp(t) if t is not None else pd.Timestamp.min.tz_localize("UTC")


def _v(x) -> str:
    return str(getattr(x, "value", x)).lower()


def _state(o) -> str:
    return _v(getattr(o, "status", ""))


def _side(o):
    s = getattr(o, "side", None)
    return None if s is None else _v(s)


def _et_date(ts, day) -> str:
    try:
        return str(pd.Timestamp(ts).tz_convert("America/New_York").date())
    except (TypeError, ValueError):
        return str(day)
