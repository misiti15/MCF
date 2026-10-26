"""2026-10-23 10:47 ET: AlpacaBroker.can_short -> client.get_asset raised a pydantic ValidationError for an asset on
exchange "TXSE" and ended Primary's live job (blocked-signal audit 2026-10-26). can_short now reads the raw
/assets/<symbol> JSON instead, and only a failure of that too means "not shortable". Educational only - not financial
advice."""
import pytest

from mcf.execution.alpaca_broker import AlpacaBroker


class _Client:
    def __init__(self, asset_exc=None, raw=None, raw_exc=None):
        self.asset_exc, self.raw, self.raw_exc, self.calls = asset_exc, raw, raw_exc, []

    def get_asset(self, symbol):
        self.calls.append(("get_asset", symbol))
        if self.asset_exc:
            raise self.asset_exc

        class A:
            shortable, easy_to_borrow = True, True
        return A()

    def get(self, path):
        self.calls.append(("get", path))
        if self.raw_exc:
            raise self.raw_exc
        return self.raw


def _broker(client):
    b = object.__new__(AlpacaBroker)   # no credentials / network
    b.client = client
    return b


def test_normal_asset():
    c = _Client()
    b = _broker(c)
    assert b.can_short("AAPL") is True and b.can_short("AAPL") is True
    assert c.calls == [("get_asset", "AAPL")]   # cached for the session


def test_unknown_exchange_falls_back_to_raw_assets():
    c = _Client(asset_exc=ValueError("1 validation error for Asset exchange input_value='TXSE'"),
                raw={"symbol": "TXCO", "exchange": "TXSE", "shortable": True, "easy_to_borrow": False})
    b = _broker(c)
    assert b.can_short("TXCO") is False          # raw flags used, no exception
    c.raw["easy_to_borrow"] = True
    assert b.can_short("TXCO") is False          # cached
    b2 = _broker(_Client(asset_exc=ValueError("x"), raw={"shortable": True, "easy_to_borrow": True}))
    assert b2.can_short("TXCO") is True


def test_both_fail_means_not_shortable():
    b = _broker(_Client(asset_exc=ValueError("x"), raw_exc=RuntimeError("y")))
    assert b.can_short("TXCO") is False


def test_connection_errors_still_raise():
    requests = pytest.importorskip("requests")
    b = _broker(_Client(asset_exc=requests.exceptions.ConnectionError("down")))
    with pytest.raises(requests.exceptions.ConnectionError):
        b.can_short("AAPL")
