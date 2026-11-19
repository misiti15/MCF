"""Broker stop / take-profit prices round to the cent in the conservative direction (housekeeping 2026-11-20:
ETHA 2026-11-19, round(39.5366, 2) = 39.54 moved a long stop up)."""

import sys
import types

import pytest

from mcf.execution.alpaca_broker import AlpacaBroker, stop_px, target_px


def test_long_stop_rounds_down_short_stop_up():
    assert stop_px(39.5366, True) == 39.53            # the ETHA case: was 39.54
    assert stop_px(39.5312, True) == 39.53
    assert stop_px(39.5312, False) == 39.54
    assert stop_px(39.5366, False) == 39.54


def test_targets_round_toward_entry():
    assert target_px(41.2399, True) == 41.23          # long target: down (fills whenever the model's touch fills)
    assert target_px(37.1201, False) == 37.13         # short target: up


@pytest.mark.parametrize("px", [39.54, 10.0, 0.07, 123.45, 39.54 - 1e-12, 39.54 + 1e-12, 0.1 + 0.2])
def test_on_the_cent_is_unchanged(px):
    want = round(px, 2)
    for f in (stop_px, target_px):
        assert f(px, True) == want and f(px, False) == want


def test_never_tighter_than_model():
    import random

    rnd = random.Random(7)
    for _ in range(2000):
        x = round(rnd.uniform(0.5, 500.0), 4)
        assert stop_px(x, True) <= x + 1e-9 and x - stop_px(x, True) < 0.01
        assert stop_px(x, False) >= x - 1e-9 and stop_px(x, False) - x < 0.01
        assert target_px(x, True) <= x + 1e-9 and target_px(x, False) >= x - 1e-9


class _Req:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _fake_alpaca(monkeypatch):
    enums = types.SimpleNamespace(
        OrderClass=types.SimpleNamespace(BRACKET="bracket", OTO="oto", OCO="oco"),
        OrderSide=types.SimpleNamespace(BUY="buy", SELL="sell"),
        TimeInForce=types.SimpleNamespace(DAY="day"))
    reqs = types.SimpleNamespace(MarketOrderRequest=_Req, StopLossRequest=_Req, TakeProfitRequest=_Req,
                                 LimitOrderRequest=_Req, StopOrderRequest=_Req)
    for name, mod in {"alpaca": types.ModuleType("alpaca"), "alpaca.trading": types.ModuleType("alpaca.trading"),
                      "alpaca.trading.enums": enums, "alpaca.trading.requests": reqs}.items():
        monkeypatch.setitem(sys.modules, name, mod)


class _Client:
    def __init__(self):
        self.sent = []

    def submit_order(self, req):
        self.sent.append(req)
        return req


@pytest.mark.parametrize("side,stop,target,want_stop,want_tgt",
                         [(1, 39.5366, 41.2399, 39.53, 41.23), (-1, 39.5312, 37.1201, 39.54, 37.13)])
def test_submit_bracket_uses_directional_rounding(monkeypatch, side, stop, target, want_stop, want_tgt):
    _fake_alpaca(monkeypatch)
    b = AlpacaBroker.__new__(AlpacaBroker)
    b.client = _Client()
    sig = types.SimpleNamespace(symbol="ETHA", side=side, stop=stop, target=target)
    req = b.submit_bracket(sig, 10, "mcf-x")
    assert req.stop_loss.stop_price == want_stop and req.take_profit.limit_price == want_tgt


@pytest.mark.parametrize("long,want_stop,want_tgt", [(True, 39.53, 41.23), (False, 39.54, 37.13)])
def test_protection_uses_directional_rounding(monkeypatch, long, want_stop, want_tgt):
    _fake_alpaca(monkeypatch)
    b = AlpacaBroker.__new__(AlpacaBroker)
    b.client = _Client()
    stop, target = (39.5366, 41.2399) if long else (39.5312, 37.1201)
    oco = b._submit_protection("ETHA", 5, long, stop, target, "c-p")
    assert oco.stop_loss.stop_price == want_stop and oco.take_profit.limit_price == want_tgt
    plain = b._submit_protection("ETHA", 5, long, stop, None, "c-p1")
    assert plain.stop_price == want_stop
