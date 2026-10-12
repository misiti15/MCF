"""Closed-order paging and late recovery of journal orders missed by a truncated broker query (2026-10-12)."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

import pandas as pd

from mcf.execution.alpaca_broker import page_orders
from mcf.execution.reconcile import reconcile_day

T0 = datetime(2026, 10, 12, 13, 50, tzinfo=timezone.utc)


def _orders(n):
    return [NS(id=f"o{i}", submitted_at=T0 + timedelta(seconds=i // 3)) for i in range(n)]   # timestamps shared by 3


def test_page_orders_returns_every_order_across_pages():
    allo = _orders(1234)
    calls = []

    def fetch(cursor):
        calls.append(cursor)
        return [o for o in allo if o.submitted_at > cursor][:500]

    got = page_orders(fetch, T0 - timedelta(seconds=1))
    assert sorted(o.id for o in got) == sorted(o.id for o in allo) and len(calls) >= 3


def test_page_orders_single_short_page():
    allo = _orders(10)
    assert len(page_orders(lambda c: allo, T0)) == 10


class _J:
    def __init__(self, rows):
        self.rows = pd.DataFrame(rows)
        self.closed = []

    def open_orders(self, run_id):
        return self.rows

    def update_order_status(self, oid, st):
        self.closed.append(oid)


class _B:
    def __init__(self, orders):
        self.orders, self.after = orders, None

    def closed_orders_today(self, after):
        self.after = after
        return self.orders


def test_reconcile_recovers_yesterdays_open_order_dated_by_fill():
    filled = datetime(2026, 10, 12, 14, 0, tzinfo=timezone.utc)
    leg = NS(filled_avg_price=101.0, filled_at=filled + timedelta(minutes=20), order_type="limit")
    parent = NS(id="p1", symbol="AAA", filled_avg_price=100.0, filled_qty="10", filled_at=filled, legs=[leg])
    j = _J([{"broker_order_id": "p1", "symbol": "AAA", "strategy": "S", "side": 1, "stop": 99.0, "target": 101.0,
             "entry_ref": 100.0, "meta": "", "created_at": "2026-10-12T13:59:00+00:00"}])
    b = _B([parent])
    tr = reconcile_day(b, j, 1, "2026-10-13")
    assert len(tr) == 1 and tr.iloc[0]["date"] == "2026-10-12" and tr.iloc[0]["pnl"] == 10.0
    assert b.after.date().isoformat() == "2026-10-12" and j.closed == ["p1"]
