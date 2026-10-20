"""Universe excludes publicly traded partnerships (10% §1446(f) withholding on every sale, shorts included)."""

from types import SimpleNamespace

import pandas as pd
import pytest

from mcf.config import load_config
from mcf.data import universe as U


def _asset(sym, attributes=None, **kw):
    a = dict(symbol=sym, name=sym, exchange="NYSE", tradable=True, shortable=True, easy_to_borrow=True,
             marginable=True, attributes=attributes)
    a.update(kw)
    return SimpleNamespace(**a)


class FakeTC:
    def __init__(self, assets):
        self.assets = assets

    def get(self, path, params=None):           # raw /assets response (dicts), as TradingClient.get returns it
        assert path == "/assets"
        return [vars(a) for a in self.assets]


def test_is_ptp_attributes_and_denylist():
    assert U.is_ptp(["ptp_no_exception"], "ZZZ")
    assert U.is_ptp(["fractional_eh_enabled", "ptp_with_exception"], "ZZZ")
    assert not U.is_ptp(["fractional_eh_enabled", "has_options"], "ET", ["ET"])  # attributes win over the list
    assert not U.is_ptp([], "ET", ["ET"])
    assert U.is_ptp(None, "et", ["ET"])  # attributes unavailable -> denylist
    assert not U.is_ptp(None, "AAPL", ["ET"])


def test_config_defaults():
    u = load_config()["universe"]
    assert u["exclude_ptp"] is True
    assert {"ET", "EPD", "MPLX", "PAA"} <= set(u["ptp_denylist"])
    assert not {"USO", "UNG"} & set(u["ptp_denylist"])  # commodity pools: no withholding seen (T1 UNG 10-12)


def test_candidate_assets_drop_ptp():
    pytest.importorskip("alpaca")
    tc = FakeTC([
        _asset("AAPL", ["has_options"]),
        _asset("ET", ["ptp_no_exception"]),
        _asset("XYZP", ["ptp_with_exception"]),  # not on the denylist, flagged by attributes
        _asset("EPD", None),                     # no attributes -> denylist
        _asset("MSFT", None),
    ])
    assets = U.candidate_assets(tc)
    u = {"exclude_ptp": True, "ptp_denylist": ["ET", "EPD"]}
    assert sorted(U.drop_ptp(assets, u).symbol) == ["AAPL", "MSFT"]
    assert len(U.drop_ptp(assets, {**u, "exclude_ptp": False})) == 5


def test_drop_ptp_without_attributes_column():
    df = pd.DataFrame({"symbol": ["ET", "SPY", "PAA"]})
    assert U.drop_ptp(df, {"ptp_denylist": ["ET", "PAA"]}).symbol.tolist() == ["SPY"]


def test_build_universe_excludes_ptp_even_if_pinned(monkeypatch, tmp_path):
    pytest.importorskip("alpaca")
    cfg = load_config()
    tc = FakeTC([_asset("AAPL", ["has_options"]), _asset("ET", ["ptp_no_exception"]), _asset("EPD", None)])
    monkeypatch.setattr(U, "_clients", lambda: (tc, None))

    def stats(dc, symbols, **kw):
        assert "ET" not in symbols and "EPD" not in symbols
        return pd.DataFrame([{"symbol": s, "price": 50.0, "adv": 1e9, "avg_volume": 2e7, "atr": 2.0, "days": 20,
                              "atr_pct": 4.0} for s in symbols])

    monkeypatch.setattr(U, "daily_stats", stats)
    import mcf.backtest.engine as eng
    monkeypatch.setattr(eng, "pinned_symbols", lambda cfg: {"ET", "EPD"})
    out = U.build_universe(cfg, out_path=str(tmp_path / "u.csv"))
    assert out.symbol.tolist() == ["AAPL"]
    assert "attributes" not in out.columns


def test_candidate_assets_survive_unknown_exchange_code():
    """2026-10-20: Alpaca listed exchange "TXSE"; alpaca-py's strict enum made get_all_assets() raise for all assets."""
    tc = FakeTC([_asset("AAPL", []), _asset("TXCO", [], exchange="TXSE")])
    assets = U.candidate_assets(tc)
    assert assets.symbol.tolist() == ["AAPL"]
