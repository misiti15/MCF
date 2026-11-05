"""Broker order paging when Alpaca's `limit` counts nested bracket legs (Testing 1, 2026-10-14: 9 filled lots never
booked, AMD 1 of 2 lots of one flatten close; 10-12 ghost orders never recovered). Educational only."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

import pandas as pd

from mcf.execution.alpaca_broker import AlpacaBroker, page_orders
from mcf.execution.reconcile import reconcile_day

T0 = datetime(2026, 10, 14, 13, 50, tzinfo=timezone.utc)
CLOSED = {"filled", "canceled", "expired", "rejected", "replaced"}


class FakeAlpaca:
    """get_orders like Alpaca's: `limit` counts every row INCLUDING nested legs (a page is filled parent by parent
    until it holds >= limit rows), filters on submitted_at (after < t < until), newest first unless direction=asc."""

    def __init__(self, parents):
        self.parents, self.calls = parents, 0

    def get_orders(self, req):
        self.calls += 1
        st = str(getattr(req.status, "value", req.status)).lower()
        rows = [p for p in self.parents if (req.after is None or p.submitted_at > req.after)
                and (req.until is None or p.submitted_at < req.until)
                and (not req.symbols or p.symbol in req.symbols)
                and (st == "all" or (st == "closed") == (str(p.status) in CLOSED))]
        asc = str(getattr(req.direction, "value", req.direction)).lower() == "asc"
        rows.sort(key=lambda p: p.submitted_at, reverse=not asc)
        out, n = [], 0
        for p in rows:
            if n >= (req.limit or 500):
                break
            out.append(p)
            n += 1 + len(p.legs or [])
        return out


def _broker(parents):
    b = AlpacaBroker.__new__(AlpacaBroker)
    b.client = FakeAlpaca(parents)
    return b


def _bracket(i, sym, side, qty, px, t, legs_state=("canceled", "canceled"), coid=None):
    stop = NS(id=f"s{i}", symbol=sym, status=legs_state[0], order_type="stop", order_class="bracket",
              filled_avg_price=None, filled_qty="0", filled_at=None, canceled_at=t + timedelta(hours=1),
              client_order_id=f"leg-s{i}", replaces=None, submitted_at=t, side="buy" if side == "sell" else "sell")
    tgt = NS(id=f"t{i}", symbol=sym, status=legs_state[1], order_type="limit", order_class="bracket",
             filled_avg_price=None, filled_qty="0", filled_at=None, canceled_at=t + timedelta(hours=1),
             client_order_id=f"leg-t{i}", replaces=None, submitted_at=t, side=stop.side)
    return NS(id=f"p{i}", symbol=sym, side=side, status="filled", order_type="market", order_class="bracket",
              filled_avg_price=px, filled_qty=str(qty), filled_at=t + timedelta(seconds=1), submitted_at=t,
              client_order_id=coid or f"mct-S{i}-{sym}-20261014", legs=[stop, tgt], replaces=None, canceled_at=None)


def _many(n):
    return [_bracket(i, f"S{i % 50}", "sell", 1, 10.0, T0 + timedelta(seconds=20 * i)) for i in range(n)]


def test_closed_orders_today_gets_every_entry_when_limit_counts_legs():
    parents = _many(400)                                  # 1,200 rows: the old code stopped after ~167 entries
    got = _broker(parents).closed_orders_today(T0 - timedelta(hours=1))
    assert sorted(o.id for o in got) == sorted(p.id for p in parents)
    assert [o.submitted_at for o in got] == sorted(o.submitted_at for o in got)        # oldest first


def test_orders_today_with_prefix_pages_too():
    parents = _many(400)
    got = _broker(parents).orders_today_with_prefix("mct-", T0 - timedelta(hours=1))
    assert len(got) == 400


def test_page_orders_drops_top_level_copies_of_nested_legs():
    p = _bracket(1, "AAA", "sell", 1, 10.0, T0)
    leg_row = p.legs[0]                                   # the same leg, also returned as its own row
    got = page_orders(lambda until: [p, leg_row] if until is None else [], None)
    assert [o.id for o in got] == ["p1"]


def test_reconcile_books_both_amd_lots_of_one_flatten_on_a_busy_day():
    """2026-10-14 AMD: MF2 and RW1 each sold 1 share in the 13:35 poll; one 2-share flatten closed both at 15:55.
    Behind ~400 other brackets the old single-page query returned only one of the two parents."""
    t_amd = T0 + timedelta(hours=3, minutes=45)
    mf2 = _bracket(901, "AMD", "sell", 1, 572.0, t_amd, coid="mct-MF2-AMD-20261014-1335")
    rw1 = _bracket(902, "AMD", "sell", 1, 572.0, t_amd + timedelta(milliseconds=150), coid="mct-RW1-AMD-20261014-1335")
    for p in (mf2, rw1):
        for leg in p.legs:
            leg.canceled_at = T0 + timedelta(hours=6, minutes=5)
    flat = NS(id="f1", symbol="AMD", side="buy", status="filled", order_type="market", order_class="simple",
              filled_avg_price=571.13, filled_qty="2", filled_at=T0 + timedelta(hours=6, minutes=5, seconds=20),
              submitted_at=T0 + timedelta(hours=6, minutes=5, seconds=19), client_order_id="random-uuid", legs=None,
              replaces=None, canceled_at=None)
    others = [_bracket(i, f"S{i % 50}", "sell", 1, 10.0, T0 + timedelta(seconds=20 * i)) for i in range(400)]
    parents = others[:330] + [mf2, rw1] + others[330:] + [flat]
    rows = [{"broker_order_id": p.id, "symbol": "AMD", "strategy": s, "side": -1, "stop": 576.0, "target": 560.0,
             "entry_ref": 572.0, "meta": "", "created_at": p.submitted_at.isoformat()}
            for p, s in ((mf2, "MF2"), (rw1, "RW1"))]

    class J:
        closed = []

        def open_orders(self, run_id):
            return pd.DataFrame(rows)

        def update_order_status(self, oid, st):
            self.closed.append((oid, st))

    j = J()
    tr = reconcile_day(_broker(parents), j, 1, "2026-10-14").set_index("strategy")
    assert set(tr.index) == {"MF2", "RW1"}
    assert (tr.exit_reason == "flatten").all() and (tr.shares == 1).all()
    assert abs(tr.pnl.sum() - 2 * (572.0 - 571.13)) < 1e-9
    assert sorted(j.closed) == [("p901", "closed"), ("p902", "closed")]


def test_reconcile_never_uses_a_leg_row_as_a_flatten_close():
    """A filled stop leg returned as its own row (its parent on another page or outside the window) is not a
    flatten close for a sibling lot on the symbol."""
    t = T0 + timedelta(hours=1)
    lot = _bracket(1, "AAA", "sell", 5, 20.0, t)
    for leg in lot.legs:
        leg.canceled_at = t + timedelta(minutes=1)
    stray = NS(id="sX", symbol="AAA", side="buy", status="filled", order_type="stop", order_class="bracket",
               filled_avg_price=21.0, filled_qty="5", filled_at=t + timedelta(minutes=30), submitted_at=t,
               client_order_id="leg-x", legs=None, replaces=None, canceled_at=None)
    rows = [{"broker_order_id": "p1", "symbol": "AAA", "strategy": "S", "side": -1, "stop": 21.0, "target": 19.0,
             "entry_ref": 20.0, "meta": "", "created_at": t.isoformat()}]
    j = NS(open_orders=lambda run_id: pd.DataFrame(rows), update_order_status=lambda *a: None)
    tr = reconcile_day(NS(closed_orders_today=lambda after: [lot, stray]), j, 1, "2026-10-14")
    assert tr.empty


def test_page_orders_keeps_paging_when_a_full_page_holds_fewer_distinct_rows():
    """Gen 2026-11-05: a full page whose legs also come back as their own rows holds fewer than `limit` distinct rows;
    the old short-page rule stopped there and the closing reconcile never saw the morning's 69 lots."""
    parents = _many(400)

    def fetch(until):                                     # 500 rows a page, every leg ALSO returned top-level
        rows = sorted((p for p in parents if until is None or p.submitted_at < until),
                      key=lambda p: p.submitted_at, reverse=True)
        out, n = [], 0
        for p in rows:
            if n >= 500:
                break
            out += [p, *p.legs]
            n += 1 + 2 * len(p.legs)
        return out

    got = page_orders(fetch, T0 - timedelta(hours=1))
    assert sorted(o.id for o in got) == sorted(p.id for p in parents)


def _gen_lot(i, t, close_t):
    """A hold-to-close short (stop leg only, cancelled at the flatten) and the flatten's market buy."""
    lot = _bracket(i, f"H{i}", "sell", 10, 20.0, t)
    lot.legs = lot.legs[:1]
    lot.legs[0].canceled_at = close_t - timedelta(seconds=5)
    flat = NS(id=f"f{i}", symbol=f"H{i}", side="buy", status="filled", order_type="market", order_class="simple",
              filled_avg_price=19.0, filled_qty="10", filled_at=close_t, submitted_at=close_t - timedelta(seconds=1),
              client_order_id=f"close-{i}", legs=None, replaces=None, canceled_at=None)
    row = {"broker_order_id": lot.id, "symbol": lot.symbol, "strategy": "HOLD", "side": -1, "stop": 21.0,
           "target": None, "entry_ref": 20.0, "meta": "", "created_at": t.isoformat()}
    return lot, flat, row


def test_reconcile_looks_up_entries_missing_from_the_days_list_by_symbol():
    close_t = T0 + timedelta(hours=6, minutes=5)
    lot, flat, row = _gen_lot(1, T0 + timedelta(minutes=10), close_t)
    late, late_flat, late_row = _gen_lot(2, T0 + timedelta(hours=4), close_t)
    asked = []

    class B:
        def closed_orders_today(self, after):             # truncated: only the last hours (late lot + both closes)
            return [late, late_flat, flat]

        def closed_orders_for_symbols(self, after, symbols):
            asked.append(list(symbols))
            return [o for o in (lot, flat, lot.legs[0]) if o.symbol in symbols]

    closed = []
    j = NS(open_orders=lambda run_id: pd.DataFrame([row, late_row]),
           update_order_status=lambda oid, st: closed.append(oid))
    tr = reconcile_day(B(), j, 1, "2026-10-14")
    assert asked == [["H1"]]
    assert sorted(tr.broker_order_id) == ["p1", "p2"] and (tr.exit_reason == "flatten").all()
    assert abs(tr.pnl.sum() - 20.0) < 1e-9 and sorted(closed) == ["p1", "p2"]


def test_reconcile_without_symbol_lookup_still_works():
    lot, flat, row = _gen_lot(1, T0, T0 + timedelta(hours=6))
    j = NS(open_orders=lambda run_id: pd.DataFrame([row]), update_order_status=lambda *a: None)
    assert reconcile_day(NS(closed_orders_today=lambda after: [flat]), j, 1, "2026-10-14").empty


def test_eod_book_pairs_fills_the_trade_jobs_left_open(tmp_path):
    from mcf.cli import eod_book
    from mcf.journal import Journal

    j = Journal(str(tmp_path / "journal.db"))
    rid = j.get_or_create_run("paper", "MCF Update (live paper)")
    lot, flat, row = _gen_lot(1, T0, T0 + timedelta(hours=6))
    j.record_order(rid, "H1", "HOLD", -1, 10, 20.0, 21.0, None, lot.id, "submitted", "{}")
    b = NS(closed_orders_today=lambda after: [lot, flat])
    assert eod_book(j, rid, "2026-10-14", {}, broker=b) == 1
    t = j.trades(run_id=rid)
    assert len(t) == 1 and abs(float(t.iloc[0]["pnl"]) - 10.0) < 1e-9
    assert j.open_orders(rid).empty
    assert eod_book(j, rid, "2026-10-14", {}, broker=b) == 0           # nothing left open: no broker call, no rows
