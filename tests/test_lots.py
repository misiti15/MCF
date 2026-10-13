"""Per-lot stacking (owner 2026-10-13, live.max_lots_per_symbol). Each setup on a symbol is its own lot: its own bracket,
trade management, exit and journal row. The broker fake below behaves like Alpaca where it matters: a filled bracket
parent is no longer 'open' but its legs are (uuid ids), open exit legs reserve their bracket's quantity
(qty_available), positions are netted per symbol, client order ids must be unique. Educational only."""
import itertools
import json
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace as NS

import numpy as np
import pandas as pd
import pytest

from mcf.config import load_config
from mcf.execution import runner as R
from mcf.execution.alpaca_broker import AlpacaBroker
from mcf.execution.reconcile import reconcile_day
from mcf.strategies.base import Signal

NY = "America/New_York"
DAY = date(2026, 10, 13)
OPEN = {"new", "held", "accepted", "pending_new", "partially_filled"}
_ids = itertools.count(1)


def _v(x):
    return str(getattr(x, "value", x)).lower()


class FakeAlpaca:
    def __init__(self):
        self.orders, self.pos, self.price, self.coids = [], {}, {}, set()
        self.now = datetime(2026, 10, 13, 14, 0, tzinfo=timezone.utc)
        self.is_open, self.replaced, self.cancelled = True, [], []

    # -- helpers
    def _t(self):
        self.now += timedelta(seconds=1)
        return self.now

    def by_coid(self, coid):
        return next(o for o in self.orders if o.client_order_id == coid)

    def _reserved(self, sym):
        n = 0.0
        for o in self.orders:
            if o.symbol == sym and o.status == "filled" and o.legs and any(l.status in OPEN for l in o.legs):
                n += float(o.filled_qty) - sum(float(l.filled_qty) for l in o.legs)
        return n

    def fill(self, coid, px):
        o = self.by_coid(coid)
        o.status, o.filled_qty, o.filled_avg_price, o.filled_at = "filled", o.qty, str(px), self._t()
        self.pos[o.symbol] = self.pos.get(o.symbol, 0.0) + (1 if o.side == "buy" else -1) * float(o.qty)
        for leg in o.legs or []:
            leg.status = "new" if leg.order_type == "limit" else "held"   # Alpaca: TP working, SL held (OCO)

    def hit(self, coid, kind, px):
        """The lot's stop or target leg fills; its sibling is cancelled (OCO)."""
        o = self.by_coid(coid)
        for leg in o.legs:
            if (leg.order_type == "limit") == (kind == "target"):
                leg.status, leg.filled_qty, leg.filled_avg_price, leg.filled_at = "filled", o.filled_qty, str(px), self._t()
            elif leg.status in OPEN:
                leg.status = "canceled"
        self._net(o.symbol, -(1 if o.side == "buy" else -1) * float(o.filled_qty))

    def _net(self, sym, d):
        self.pos[sym] = self.pos.get(sym, 0.0) + d
        if abs(self.pos[sym]) < 1e-9:
            self.pos.pop(sym)

    # -- TradingClient surface
    def get_account(self):
        return NS(equity="100000", cash="100000")

    def get_asset(self, sym):
        return NS(shortable=True, easy_to_borrow=True)

    def get_clock(self):
        return NS(is_open=self.is_open, timestamp=self.now, next_open=self.now)

    def submit_order(self, req):
        coid = req.client_order_id or f"uuid-{next(_ids)}"
        if coid in self.coids:
            raise RuntimeError('{"code":40010001,"message":"client_order_id must be unique"}')
        side, qty = _v(req.side), float(req.qty)
        opp = "sell" if side == "buy" else "buy"
        legs = []
        if getattr(req, "stop_loss", None) is not None:
            legs.append(NS(id=f"leg-{next(_ids)}", client_order_id=f"uuid-{next(_ids)}", symbol=req.symbol, side=opp,
                           order_type="stop", stop_price=req.stop_loss.stop_price, limit_price=None, status="held",
                           filled_qty="0", filled_avg_price=None, filled_at=None, legs=None))
        if getattr(req, "take_profit", None) is not None:
            legs.append(NS(id=f"leg-{next(_ids)}", client_order_id=f"uuid-{next(_ids)}", symbol=req.symbol, side=opp,
                           order_type="limit", stop_price=None, limit_price=req.take_profit.limit_price, status="held",
                           filled_qty="0", filled_avg_price=None, filled_at=None, legs=None))
        o = NS(id=f"ord-{next(_ids)}", client_order_id=coid, symbol=req.symbol, side=side, qty=str(qty),
               filled_qty="0", filled_avg_price=None, filled_at=None, submitted_at=self._t(), status="new",
               order_type="market", legs=legs or None)
        if not legs:   # a plain closing order: needs unreserved shares, fills at the last price
            held = abs(self.pos.get(req.symbol, 0.0)) - self._reserved(req.symbol)
            if qty > held + 1e-9:
                raise RuntimeError('{"code":40310000,"message":"insufficient qty available for order"}')
        self.coids.add(coid)
        self.orders.append(o)
        if not legs:
            o.status, o.filled_qty, o.filled_avg_price, o.filled_at = "filled", str(qty), str(self.price[req.symbol]), self._t()
            self._net(req.symbol, (1 if side == "buy" else -1) * qty)
        return o

    def _all(self):
        for o in self.orders:
            yield o
            yield from o.legs or []

    def cancel_order_by_id(self, oid):
        o = next(x for x in self._all() if x.id == oid)
        if o.status not in OPEN:
            raise RuntimeError("order is not cancelable")
        self.cancelled.append(oid)
        o.status = "canceled"
        for leg in o.legs or []:
            if leg.status in OPEN:
                leg.status = "canceled"

    def replace_order_by_id(self, oid, req):
        leg = next(x for x in self._all() if x.id == oid)
        leg.stop_price = req.stop_price
        self.replaced.append((oid, req.stop_price))

    def get_orders(self, req):
        st = _v(req.status)
        syms = getattr(req, "symbols", None)
        out = []   # `after` is not applied: every order here is from the test's session
        for o in self.orders:
            if syms and o.symbol not in syms:
                continue
            if st == "open":
                if o.status in OPEN:
                    out.append(o)
                out += [NS(**{**leg.__dict__, "legs": None}) for leg in o.legs or [] if o.status == "filled" and leg.status in OPEN]
            elif st == "closed":
                if o.status not in OPEN:
                    out.append(o)
            else:
                out.append(o)
        return out[:getattr(req, "limit", None) or 500]

    def get_all_positions(self):
        return [NS(symbol=s, qty=str(q), qty_available=str(np.sign(q) * (abs(q) - self._reserved(s))),
                   side="long" if q > 0 else "short", avg_entry_price="10", current_price=str(self.price.get(s, 10)),
                   unrealized_pl="0") for s, q in self.pos.items()]

    def close_position(self, sym):
        q = self.pos[sym]
        req = NS(symbol=sym, qty=abs(q), side="sell" if q > 0 else "buy", client_order_id=None)
        return self.submit_order(req)

    def cancel_orders(self):
        for o in list(self._all()):
            if o.status in OPEN:
                o.status = "canceled"


def _runner(tmp_path, monkeypatch, client=None, lots=3, strategies=(), journal="j.db"):
    monkeypatch.setattr(R._time, "sleep", lambda s: None)
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / journal)
    cfg["live"]["max_lots_per_symbol"] = lots
    client = client or FakeAlpaca()
    b = AlpacaBroker.__new__(AlpacaBroker)
    b.client = client
    r = R.PaperRunner(cfg, list(strategies), {}, broker=b)
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px: (True, "ok", {}))
    return r, client


NOW = pd.Timestamp("2026-10-13 10:00:30", tz=NY)
CTX = NS(bars=pd.DataFrame({"volume": [1e6] * 5}), avg_dollar_volume=5e8)


def _enter(r, name, side=1, stop=9.0, target=12.0, now=NOW, **kw):
    r._enter(Signal("XYZ", name, side, 10, stop=stop, target=target, **kw), 10.0, ("XYZ", name), CTX, now)


def _skips(r):
    s = r.journal.signals(r.run_id)
    return {x.strategy: (x.reason, json.loads(x.info or "{}").get("held_by")) for x in s.itertuples() if x.status == "skipped"}


def test_all_accounts_stack_three_lots(monkeypatch):
    """Owner 2026-10-13: up to 3 lots per symbol in every account (Primary, Testing 1, Testing 2)."""
    for acct in ("primary", "testing", "testing2"):
        monkeypatch.setenv("MCF_ACCOUNT", acct)
        assert load_config()["live"]["max_lots_per_symbol"] == 3


def test_three_lots_same_poll_then_lot_cap_and_opposite_side(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    for name in ("A", "B", "C", "D"):              # same poll: nothing filled yet -> pending entries count as lots
        _enter(r, name)
    _enter(r, "S", side=-1, stop=11.0, target=9.0)
    coids = [o.client_order_id for o in c.orders]
    assert coids == [f"mcf-{n}-XYZ-20261013" for n in "ABC"] and len(set(coids)) == 3
    assert all(len(o.legs) == 2 for o in c.orders)                # each lot is its own bracket for its own qty
    assert _skips(r) == {"D": ("lot cap", ["A", "B", "C"]), "S": ("opposite side held", ["A", "B", "C"])}
    assert r.risk.open_lots() == 3 and r.risk.state.open_by_strategy == {"A": 1, "B": 1, "C": 1}
    assert r.risk.state.trades_today == 3


def test_opposite_side_blocked_and_slots_count_lots(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    r.risk.a = {**r.risk.a, "max_concurrent_positions": 2}
    _enter(r, "A", side=-1, stop=11.0, target=9.0)
    _enter(r, "L")                                                  # long into a short lot
    _enter(r, "B", side=-1, stop=11.0, target=9.0)
    _enter(r, "C", side=-1, stop=11.0, target=9.0)                  # 2 lots = 2 slots used
    assert [o.client_order_id for o in c.orders] == ["mcf-A-XYZ-20261013", "mcf-B-XYZ-20261013"]
    sk = _skips(r)
    assert sk["L"] == ("opposite side held", ["A"]) and sk["C"][0] == "max concurrent positions"


def _three_filled(r, c, **mgmt):
    for name, stop in (("A", 9.0), ("B", 9.5), ("C", 8.0)):
        _enter(r, name, stop=stop, target=12.0, **mgmt.get(name, {}))
    for i, name in enumerate("ABC"):
        c.fill(f"mcf-{name}-XYZ-20261013", 10.0 + 0.02 * i)
    return {n: int(float(c.by_coid(f"mcf-{n}-XYZ-20261013").qty)) for n in "ABC"}


def test_independent_exits_one_journal_row_per_lot(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    q = _three_filled(r, c)
    assert c.pos["XYZ"] == sum(q.values())                          # netted at the broker
    c.hit("mcf-A-XYZ-20261013", "stop", 9.0)
    c.hit("mcf-B-XYZ-20261013", "target", 12.0)
    assert c.pos["XYZ"] == q["C"]
    r.reconcile(DAY)
    t = r.journal.trades(run_id=r.run_id).set_index("strategy")
    assert set(t.index) == {"A", "B"} and list(r.lots["XYZ"]) == ["C"]   # A and B released, C still open
    c.price["XYZ"] = 10.5
    r.flatten_mcf()
    assert "XYZ" not in c.pos and r.health["flatten_failed"] == []
    r.reconcile(DAY)
    t = r.journal.trades(run_id=r.run_id).set_index("strategy")
    assert len(t) == 3
    assert t.loc["A", "exit_reason"] == "stop" and t.loc["A", "pnl"] == pytest.approx((9.0 - 10.0) * q["A"])
    assert t.loc["B", "exit_reason"] == "target" and t.loc["B", "pnl"] == pytest.approx((12.0 - 10.02) * q["B"])
    assert t.loc["C", "exit_reason"] == "flatten" and t.loc["C", "pnl"] == pytest.approx((10.5 - 10.04) * q["C"])
    assert t.loc["C", "shares"] == q["C"] and t.loc["A", "r_multiple"] == pytest.approx(-1.0)
    assert r.journal.open_orders(r.run_id).empty


def test_flatten_with_three_open_lots_closes_all_and_pairs_each(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    q = _three_filled(r, c)
    c.price["XYZ"] = 9.8
    r.flatten_mcf()
    assert c.pos == {} and r.health["flatten_failed"] == []
    assert all(l.status == "canceled" for o in c.orders if o.legs for l in o.legs)
    r.reconcile(DAY)
    t = r.journal.trades(run_id=r.run_id).set_index("strategy")
    for i, n in enumerate("ABC"):
        assert t.loc[n, "exit"] == 9.8 and t.loc[n, "pnl"] == pytest.approx((9.8 - (10.0 + 0.02 * i)) * q[n])


def _bars(t0, n, high):
    idx = pd.date_range(t0.floor("1min"), periods=n, freq="1min")
    return pd.DataFrame({"open": 10.0, "high": high, "low": 9.95, "close": 10.0, "volume": 1e5}, index=idx)


def test_time_stop_and_breakeven_touch_only_their_own_lot(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    # A: wide stop, 30-min time stop; B: tight stop, breakeven at 1R; C: unmanaged
    q = _three_filled(r, c, A={"time_stop_min": 30, "time_stop_min_r": 0.3}, B={"be_at_r": 1.0})
    assert set(r.managed) == {("XYZ", "A"), ("XYZ", "B")}
    c.price["XYZ"] = 10.1
    r.manage(NOW + pd.Timedelta(minutes=35), {"XYZ": _bars(NOW, 36, 10.6)})
    a, b_, cc = (c.by_coid(f"mcf-{n}-XYZ-20261013") for n in "ABC")
    # A: risk 1.0, best 0.6R >= 0.3 -> no time stop yet; B: risk 0.5, best 1.2R -> stop to breakeven (10.0)
    assert all(l.status in OPEN for l in a.legs) and all(l.status in OPEN for l in cc.legs)
    b_stop = next(l for l in b_.legs if l.order_type == "stop")
    assert b_stop.stop_price == 10.0 and [x[0] for x in c.replaced] == [b_stop.id]
    # a second session where A never works: time stop closes exactly A's qty and cancels only A's legs
    r.managed[("XYZ", "A")]["best"] = 0.0
    r.bars = {"XYZ": _bars(NOW, 37, 10.2)}
    r.manage(NOW + pd.Timedelta(minutes=36), r.bars)
    assert all(l.status == "canceled" for l in a.legs)
    assert all(l.status in OPEN for l in b_.legs + cc.legs)
    ex = c.by_coid("mcf-A-XYZ-20261013-x")
    assert ex.side == "sell" and float(ex.qty) == q["A"] and c.pos["XYZ"] == q["B"] + q["C"]
    assert ("XYZ", "A") not in r.managed and set(r.lots["XYZ"]) == {"B", "C"}
    r.reconcile(DAY)
    t = r.journal.trades(run_id=r.run_id)
    assert len(t) == 1 and t.iloc[0].strategy == "A" and t.iloc[0].exit_reason == "timestop"
    assert t.iloc[0].pnl == pytest.approx((10.1 - 10.0) * q["A"]) and pd.notna(t.iloc[0].mfe_r) and t.iloc[0].mfe_r == pytest.approx(0.2)
    # B stopped at breakeven, C flattened: each gets its own exit, never A's lot exit
    c.hit("mcf-B-XYZ-20261013", "stop", 10.0)
    c.price["XYZ"] = 10.3
    r.flatten_mcf()
    r.reconcile(DAY)
    t = r.journal.trades(run_id=r.run_id).set_index("strategy")
    assert t.loc["B", "exit_reason"] == "stop" and t.loc["B", "pnl"] == pytest.approx((10.0 - 10.02) * q["B"])
    assert t.loc["C", "exit_reason"] == "flatten" and t.loc["C", "exit"] == 10.3
    assert t.loc["A", "exit"] == 10.1


def test_time_stop_skips_a_lot_its_own_stop_already_closed(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    q = _three_filled(r, c, A={"time_stop_min": 30, "time_stop_min_r": 0.3})
    c.hit("mcf-A-XYZ-20261013", "stop", 9.0)                     # closed at the broker; reconcile not run yet
    r.manage(NOW + pd.Timedelta(minutes=35), {"XYZ": _bars(NOW, 36, 10.05)})
    assert not any(o.client_order_id.endswith("-x") for o in c.orders)   # B's and C's shares untouched
    assert c.pos["XYZ"] == q["B"] + q["C"]


def test_restart_restores_two_open_lots(tmp_path, monkeypatch):
    class St:
        def __init__(self, name, **params):
            self.name, self.params = name, params

    r, c = _runner(tmp_path, monkeypatch)
    q = _three_filled(r, c, A={"be_at_r": 1.0}, B={"time_stop_min": 30, "time_stop_min_r": 0.3})
    c.hit("mcf-C-XYZ-20261013", "target", 12.0)
    r.reconcile(DAY)                                              # C closed and journaled before the restart
    r2, _ = _runner(tmp_path, monkeypatch, client=c,
                    strategies=[St("A", be_at_r=1.0), St("B", time_stop_min=30, time_stop_min_r=0.3), St("C")])
    r2.restore(DAY)
    assert set(r2.lots["XYZ"]) == {"A", "B"} and r2.risk.open_lots() == 2
    assert r2.risk.state.open_by_strategy == {"A": 1, "B": 1}
    assert set(r2.managed) == {("XYZ", "A"), ("XYZ", "B")}
    assert r2.managed[("XYZ", "B")]["entry"] == 10.02 and r2.managed[("XYZ", "A")]["coid"] == "mcf-A-XYZ-20261013"
    _enter(r2, "D")                                               # third lot fits, fourth hits the cap
    _enter(r2, "E")
    assert c.orders[-1].client_order_id == "mcf-D-XYZ-20261013" and _skips(r2)["E"][0] == "lot cap"


def test_retry_after_release_under_lots_waits_for_room(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch, lots=2)
    r.retry_after_release = True
    _enter(r, "A")
    _enter(r, "B")
    _enter(r, "D")                                                 # lot cap (market entry) -> may retry
    for n in "AB":
        c.fill(f"mcf-{n}-XYZ-20261013", 10.0)
    r._sync_open()
    assert not r._retry_ready(("XYZ", "D"))
    c.hit("mcf-A-XYZ-20261013", "stop", 9.0)
    r.reconcile(DAY)
    assert r._retry_ready(("XYZ", "D"))                            # one long lot left, room for a long lot


def test_reconcile_pairs_lot_exit_not_another_lots_entry():
    t = lambda m: datetime(2026, 10, 13, 14, m, tzinfo=timezone.utc)
    leg = lambda: NS(filled_avg_price=None, filled_at=None, order_type="stop", status="canceled")
    a = NS(id="pa", client_order_id="mcf-A-XYZ-20261013", symbol="XYZ", side="buy", filled_avg_price="10",
           filled_qty="5", filled_at=t(1), status="filled", legs=[leg()])
    b = NS(id="pb", client_order_id="mcf-B-XYZ-20261013", symbol="XYZ", side="buy", filled_avg_price="11",
           filled_qty="3", filled_at=t(2), status="filled", legs=[leg()])
    bx = NS(id="xb", client_order_id="mcf-B-XYZ-20261013-x", symbol="XYZ", side="sell", filled_avg_price="12",
            filled_qty="3", filled_at=t(3), status="filled", legs=None)
    never = NS(id="pc", client_order_id="mcf-C-XYZ-20261013", symbol="XYZ", side="buy", filled_avg_price=None,
               filled_qty="0", filled_at=None, status="canceled", legs=None)
    rows = pd.DataFrame([{"broker_order_id": i, "symbol": "XYZ", "strategy": s, "side": 1, "stop": 9.0, "target": None,
                          "entry_ref": 10.0, "meta": "", "created_at": "2026-10-13T14:00:00+00:00"}
                         for i, s in (("pa", "A"), ("pb", "B"), ("pc", "C"))])
    status = {}
    j = NS(open_orders=lambda run: rows, update_order_status=lambda oid, st: status.__setitem__(oid, st))
    tr = reconcile_day(NS(closed_orders_today=lambda after: [a, b, bx, never]), j, 1, "2026-10-13").set_index("strategy")
    assert list(tr.index) == ["B"] and tr.loc["B", "pnl"] == 3.0 and tr.loc["B", "exit_reason"] == "timestop"
    assert status == {"pb": "closed", "pc": "expired"}            # A still open: B's entry and B's exit are not its exit


def test_playing_time_credits_every_lot_holder():
    from mcf.report import playing_time as pt

    assert pt.classify("skipped", "lot cap") == pt.classify("skipped", "opposite side held") == "held_by_other"
    sig = pd.DataFrame([
        {"id": 1, "day": "2026-10-13", "symbol": "XYZ", "strategy": "A", "status": "submitted", "reason": "ok", "info": "{}"},
        {"id": 2, "day": "2026-10-13", "symbol": "XYZ", "strategy": "B", "status": "submitted", "reason": "ok", "info": "{}"},
        {"id": 3, "day": "2026-10-13", "symbol": "XYZ", "strategy": "S", "status": "skipped", "reason": "opposite side held",
         "info": json.dumps({"held_by": ["A", "B"]})},
    ])
    s = pt.attribute(sig)
    assert s.loc[2, "held_by"] == "A,B"
    rows = {r["setup"]: r for r in pt._rows(s, pd.DataFrame(columns=["strategy"]), {"A": 1, "B": 1, "S": 1}, {}, {})}
    assert rows["S"]["lost_to"] == {"A": 1, "B": 1} and rows["A"]["took_from_others"] == 1
