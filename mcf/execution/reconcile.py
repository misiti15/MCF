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
    after = pd.Timestamp(f"{day} 00:00", tz="America/New_York").to_pydatetime()
    orders = journal.open_orders(run_id)
    if orders.empty:
        return pd.DataFrame()
    by_id = {str(o.id): o for o in broker.closed_orders_today(after)}
    rows = []
    for _, rec in orders.iterrows():
        parent = by_id.get(rec.broker_order_id)
        if parent is None or parent.filled_avg_price is None:
            continue
        entry = float(parent.filled_avg_price)
        qty = int(float(parent.filled_qty))
        exit_px, exit_t, reason = None, None, "flatten"
        for leg in parent.legs or []:
            if leg.filled_avg_price is not None:
                exit_px, exit_t = float(leg.filled_avg_price), leg.filled_at
                reason = "target" if getattr(leg.order_type, "value", leg.order_type) == "limit" else "stop"
        if exit_px is None:
            # closed by the flatten -> the market close order for this symbol
            for o in by_id.values():
                if (o.symbol == rec.symbol and o.filled_at and o.filled_at > parent.filled_at
                        and str(o.id) != rec.broker_order_id and o.filled_avg_price is not None):
                    exit_px, exit_t = float(o.filled_avg_price), o.filled_at
        if exit_px is None:
            continue  # still open
        side = int(rec.side)
        risk = abs(entry - rec.stop) * qty
        pnl = side * (exit_px - entry) * qty
        pnl_adj = pnl - (stop_extra * qty if reason == "stop" else 0.0)
        meta = rec.meta + (";touch_fill" if reason == "target" else "")
        rows.append(dict(
            symbol=rec.symbol, strategy=rec.strategy, side=side, date=str(day),
            signal_time=rec.created_at, entry_time=parent.filled_at, entry=entry, stop=rec.stop,
            target=rec.target, exit_time=exit_t, exit=exit_px, exit_reason=reason,
            r_multiple=pnl / risk if risk else 0.0, mae_r=None, mfe_r=None, shares=qty, pnl=pnl,
            meta=meta, broker_order_id=rec.broker_order_id,
            slip_bps=side * (entry - rec.entry_ref) / rec.entry_ref * 1e4 if rec.entry_ref else None,
            pnl_adj=pnl_adj,
        ))
        journal.update_order_status(rec.broker_order_id, "closed")
    return pd.DataFrame(rows)
