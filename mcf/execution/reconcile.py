"""Turn Alpaca order fills into journal trades (entry, exit, R, P/L) plus fill-realism measures.

Paper fills are optimistic (no queue, no size limit, limit orders fill on a touch). Each trade records:
  slip_bps  entry fill vs the price when the signal fired (latency + spread; MarcoFlow lost ~16 bps here)
  pnl_adj   broker P/L minus the stop-exit slippage a real book adds (costs.stop_slippage_per_share);
            target (limit) exits are kept but flagged `touch_fill` in meta when not verifiable.
"""

from __future__ import annotations

import pandas as pd


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
    rows = []
    for _, rec in orders.iterrows():
        parent = by_id.get(rec.broker_order_id)
        if parent is None:
            continue
        if parent.filled_avg_price is None:
            if _state(parent) in DEAD and not float(getattr(parent, "filled_qty", 0) or 0):
                journal.update_order_status(rec.broker_order_id, "expired")   # never filled: not a lot, not a trade
            continue
        entry = float(parent.filled_avg_price)
        qty = int(float(parent.filled_qty))
        exit_px, exit_t, reason = None, None, "flatten"
        for leg in parent.legs or []:
            if leg.filled_avg_price is not None:
                exit_px, exit_t = float(leg.filled_avg_price), leg.filled_at
                reason = "target" if getattr(leg.order_type, "value", leg.order_type) == "limit" else "stop"
        pcoid = str(getattr(parent, "client_order_id", "") or "")
        if exit_px is None and pcoid:
            # a lot-specific exit (time stop with stacked lots): its client id is <parent client id>-x
            own = next((o for o in by_id.values() if getattr(o, "client_order_id", None) == pcoid + "-x"
                        and o.filled_avg_price is not None), None)
            if own is not None:
                exit_px, exit_t, reason = float(own.filled_avg_price), own.filled_at, "timestop"
        if exit_px is None:
            # closed by the flatten -> the market close order for this symbol. With stacked lots, never another lot's
            # entry (same side) or another lot's own exit (-x): each remaining lot gets the flatten fill, its own qty.
            for o in by_id.values():
                ocoid = str(getattr(o, "client_order_id", "") or "")
                oside = _side(o)
                if (o.symbol == rec.symbol and o.filled_at and o.filled_at > parent.filled_at
                        and str(o.id) != rec.broker_order_id and o.filled_avg_price is not None
                        and not (oside is not None and oside == _side(parent))
                        and not (ocoid.endswith("-x") and ocoid != pcoid + "-x")):
                    exit_px, exit_t = float(o.filled_avg_price), o.filled_at
        if exit_px is None:
            continue  # still open
        side = int(rec.side)
        risk = abs(entry - rec.stop) * qty
        pnl = side * (exit_px - entry) * qty
        pnl_adj = pnl - (stop_extra * qty if reason == "stop" else 0.0)
        meta = rec.meta + (";touch_fill" if reason == "target" else "")
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
    return pd.DataFrame(rows)


DEAD = {"canceled", "cancelled", "expired", "rejected", "done_for_day", "replaced"}


def _state(o) -> str:
    return str(getattr(getattr(o, "status", ""), "value", getattr(o, "status", ""))).lower()


def _side(o):
    s = getattr(o, "side", None)
    return None if s is None else str(getattr(s, "value", s)).lower()


def _et_date(ts, day) -> str:
    try:
        return str(pd.Timestamp(ts).tz_convert("America/New_York").date())
    except (TypeError, ValueError):
        return str(day)
