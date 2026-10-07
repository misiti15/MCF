"""Regression for the 15:55 flatten.

2026-10-06: closes were sent before the bracket-leg cancels settled -> "insufficient qty available".
2026-10-07: the bracket legs (take-profit limit, stop) carry broker-generated client ids; once the entry parent has
filled it is no longer "open", so an open-orders query by the mcf- prefix found nothing to cancel and the legs kept
holding the shares until they expired at 16:00. The fake below behaves like Alpaca in both respects."""
from types import SimpleNamespace

from mcf.config import load_config
from mcf.execution.alpaca_broker import AlpacaBroker


class FakeClient:
    def __init__(self, lag=3, is_open=True):
        self.pos = {"AAA": 10.0, "BBB": -5.0}
        # per symbol: one filled bracket parent (mcf- id) with two open legs (uuid ids)
        self.legs = {s: {f"{s}-tp": "new", f"{s}-sl": "held"} for s in self.pos}
        self.pending, self.lag, self.closes, self.is_open, self.submitted = {}, lag, [], is_open, []

    def _tick(self):
        for oid in list(self.pending):
            self.pending[oid] -= 1
            if self.pending[oid] <= 0:
                del self.pending[oid]
                for s in self.legs:
                    if oid in self.legs[s]:
                        self.legs[s][oid] = "canceled"

    def cancel_order_by_id(self, oid):
        self.pending.setdefault(oid, self.lag)

    def get_orders(self, req):
        self._tick()
        status = str(getattr(req.status, "value", req.status))
        syms = getattr(req, "symbols", None) or list(self.legs)
        out = []
        for s in syms:
            parent = SimpleNamespace(id=f"{s}-entry", symbol=s, client_order_id=f"mcf-x-{s}-20261007", status="filled",
                                     legs=[SimpleNamespace(id=k, status=v, stop_price=1.0 if k.endswith("sl") else None,
                                                           client_order_id=f"uuid-{k}") for k, v in self.legs[s].items()])
            if status == "open":      # Alpaca: a filled parent is not an open order; its legs come back on their own
                out += [SimpleNamespace(id=leg.id, symbol=s, client_order_id=leg.client_order_id, status=leg.status, legs=None)
                        for leg in parent.legs if leg.status in ("new", "held")]
            else:
                out.append(parent)
        return out

    def _held(self, s):
        return any(v in ("new", "held") for v in self.legs[s].values())

    def get_all_positions(self):
        return [SimpleNamespace(symbol=s, qty=str(q), qty_available="0" if self._held(s) else str(q), current_price="10")
                for s, q in self.pos.items()]

    def get_clock(self):
        return SimpleNamespace(is_open=self.is_open)

    def close_position(self, symbol):
        self._tick()
        if self._held(symbol):
            raise RuntimeError('{"code":40310000,"message":"insufficient qty available for order"}')
        self.closes.append(symbol)
        self.pos.pop(symbol)

    def submit_order(self, req):
        self.submitted.append(req)
        return SimpleNamespace(id="ah", status="accepted")


def _broker(client):
    b = AlpacaBroker.__new__(AlpacaBroker)
    b.client = client
    return b


def test_close_cancels_the_bracket_legs_and_waits():
    c = FakeClient(lag=3)
    assert _broker(c).close_mcf_position("AAA", "mcf-", sleep=lambda s: None)
    assert c.closes == ["AAA"] and all(v == "canceled" for v in c.legs["AAA"].values())


def test_close_retries_when_cancels_settle_slowly():
    c = FakeClient(lag=60)
    ok = _broker(c).close_mcf_position("BBB", "mcf-", wait_s=1.0, tries=60, sleep=lambda s: None)
    assert ok and "BBB" not in c.pos


def test_after_hours_close_uses_extended_hours_limit_not_a_queued_market_order():
    c = FakeClient(lag=1, is_open=False)
    assert _broker(c).close_mcf_position("AAA", "mcf-", sleep=lambda s: None)
    assert c.closes == [] and len(c.submitted) == 1 and c.submitted[0].extended_hours


def test_runner_flatten_closes_everything_and_reports(tmp_path, monkeypatch):
    from mcf.execution import runner as R

    monkeypatch.setattr(R._time, "sleep", lambda s: None)
    c = FakeClient(lag=3)
    b = _broker(c)
    b.equity = lambda: 1e5
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    r = R.PaperRunner(cfg, [], {}, broker=b)
    r.flatten_mcf()
    assert c.pos == {} and r.health["flatten_failed"] == []
