"""Regression: 2026-10-06 the 15:55 flatten sent closes before the bracket-leg cancels settled, the broker
rejected every close ("insufficient qty available") and 10 positions stayed open overnight without stops."""
from types import SimpleNamespace

import pandas as pd

from mcf.config import load_config
from mcf.execution.alpaca_broker import AlpacaBroker


class FakeClient:
    """Alpaca-like: cancels settle only after `lag` order polls; close fails while legs hold the shares."""

    def __init__(self, lag=3):
        self.pos = {"AAA": 10.0, "BBB": -5.0}
        self.open = {"AAA": ["a1"], "BBB": ["b1"]}
        self.pending = {}
        self.lag, self.closes = lag, []

    def cancel_order_by_id(self, oid):
        self.pending.setdefault(oid, self.lag)       # re-cancelling a pending cancel does not restart it

    def get_orders(self, req):
        for oid in list(self.pending):
            self.pending[oid] -= 1
            if self.pending[oid] <= 0:
                del self.pending[oid]
                for s in self.open:
                    if oid in self.open[s]:
                        self.open[s].remove(oid)
        syms = getattr(req, "symbols", None) or list(self.open)
        return [SimpleNamespace(id=o, symbol=s, client_order_id=f"mcf-x-{s}-20261006", legs=[])
                for s in syms for o in self.open.get(s, [])]

    def get_all_positions(self):
        return [SimpleNamespace(symbol=s, qty=str(q), qty_available="0" if self.open[s] else str(q))
                for s, q in self.pos.items()]

    def close_position(self, symbol):
        if self.open[symbol]:
            raise RuntimeError('{"code":40310000,"message":"insufficient qty available for order"}')
        self.closes.append(symbol)
        self.pos.pop(symbol)


def _broker(client):
    b = AlpacaBroker.__new__(AlpacaBroker)
    b.client = client
    return b


def test_close_waits_for_cancels_to_settle():
    c = FakeClient(lag=3)
    b = _broker(c)
    assert b.close_mcf_position("AAA", "mcf-", sleep=lambda s: None)
    assert c.closes == ["AAA"] and "AAA" not in c.pos


def test_close_retries_when_broker_still_holds_shares():
    c = FakeClient(lag=50)                       # cancels slower than the wait: the retry loop must recover
    b = _broker(c)
    ok = b.close_mcf_position("BBB", "mcf-", wait_s=1.0, tries=60, sleep=lambda s: None)
    assert ok and "BBB" not in c.pos


def test_runner_flatten_closes_everything_and_reports(tmp_path, monkeypatch):
    from mcf.execution import runner as R

    monkeypatch.setattr(R._time, "sleep", lambda s: None)
    c = FakeClient(lag=3)
    b = _broker(c)
    b.orders_today_with_prefix = lambda p, a: [SimpleNamespace(symbol="AAA"), SimpleNamespace(symbol="BBB")]
    b.equity = lambda: 1e5
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    r = R.PaperRunner(cfg, [], {}, broker=b)
    r.flatten_mcf()
    assert c.pos == {} and r.health["flatten_failed"] == []
