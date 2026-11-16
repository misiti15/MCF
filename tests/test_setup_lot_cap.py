"""Per-setup max lots per symbol (owner 2026-11-16, "2-lot option yes"): `strategies.<id>.max_lots_per_symbol`, opt-in,
default off (None = the account rules only, no change). Live: RiskManager skip "max lots per symbol for this setup";
backtest: Backtester.allocate lets that setup stack its own same-side lots up to min(cap, live.max_lots_per_symbol).
Educational only - not financial advice."""
import copy
import json

import pandas as pd
import pytest

from mcf.backtest.engine import Backtester, Trade
from mcf.config import load_config
from mcf.execution.risk import SETUP_LOT_CAP, RiskManager, setup_lot_caps
from mcf.report.playing_time import classify
from mcf.strategies.base import Signal

from test_lots import CTX, ID, NY, _enter, _runner, _skips


def _cfg(caps=None, lots=3):
    cfg = load_config()
    cfg["live"]["max_lots_per_symbol"] = lots
    cfg["live"]["same_setup_reentry"] = True
    cfg["strategies"] = {k: dict(v) for k, v in (cfg.get("strategies") or {}).items() if isinstance(v, dict)}
    for k, v in (caps or {}).items():
        cfg["strategies"].setdefault(k, {"enabled": False})["max_lots_per_symbol"] = v
    return cfg


def _sig(strategy, sym="XYZ", side=1):
    return Signal(sym, strategy, side, 10, stop=9.0 if side == 1 else 11.0)


def _hold(rm, sym, *lots):
    rm.state.open_symbols.add(sym)
    rm.state.lots[sym] = list(lots)


def test_no_setup_in_config_sets_the_key():
    for acct in ("primary", "testing", "testing2"):
        import os
        os.environ["MCF_ACCOUNT"] = acct
        try:
            assert setup_lot_caps(load_config()) == {}
        finally:
            os.environ.pop("MCF_ACCOUNT", None)


def test_default_none_unchanged_decisions():
    base = RiskManager(_cfg(), 100000)
    cfg = _cfg()
    cfg["strategies"]["A"] = {"enabled": False, "max_lots_per_symbol": None}
    nul = RiskManager(cfg, 100000)
    for rm in (base, nul):
        assert rm.setup_lot_caps == {}
        _hold(rm, "XYZ", ("A", 1), ("A", 1))
    for s in (_sig("A"), _sig("B"), _sig("A", "ABC"), _sig("A", side=-1)):
        assert base.check(s, 10.0) == nul.check(s, 10.0)
    assert base.check(_sig("A"), 10.0) == (True, "ok")              # third lot of A: allowed by the account cap of 3


def test_cap_two_skips_third_own_lot_only():
    rm = RiskManager(_cfg({"A": 2}), 100000)
    _hold(rm, "XYZ", ("A", 1))
    assert rm.check(_sig("A"), 10.0) == (True, "ok")                  # second lot of A
    rm.state.lots["XYZ"].append(("A", 1))
    assert rm.check(_sig("A"), 10.0) == (False, SETUP_LOT_CAP)        # third lot of A
    assert rm.check(_sig("B"), 10.0) == (True, "ok")                  # other setups unaffected
    assert rm.check(_sig("A", "ABC"), 10.0) == (True, "ok")           # other symbols unaffected
    _hold(rm, "ABC", ("A", 1), ("B", 1))
    assert rm.check(_sig("A", "ABC"), 10.0) == (True, "ok")           # only A's own lots count
    assert classify("skipped", SETUP_LOT_CAP) == "setup_cap"


def test_runner_logs_the_skip(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    r.risk.setup_lot_caps = {"A": 2}
    for hhmm in ("1005", "1120", "1200"):
        _enter(r, "A", now=pd.Timestamp(f"2026-10-13 {hhmm[:2]}:{hhmm[2:]}:30", tz=NY))
    _enter(r, "B", now=pd.Timestamp("2026-10-13 12:10:30", tz=NY))
    assert [o.client_order_id for o in c.orders] == [ID("A", "1005"), ID("A", "1120"), ID("B", "1210")]
    assert _skips(r) == {"A": (SETUP_LOT_CAP, ["A"])}


def test_runner_default_same_as_before(tmp_path, monkeypatch):
    """Regression on the test_lots fixture: no per-setup key -> A,B,C stack, D hits the account lot cap."""
    r, c = _runner(tmp_path, monkeypatch)
    assert r.risk.setup_lot_caps == {}
    for name in ("A", "B", "C", "D"):
        _enter(r, name)
    assert [o.client_order_id for o in c.orders] == [ID(n) for n in "ABC"]
    assert _skips(r) == {"D": ("lot cap", ["A", "B", "C"])}


def _tr(strategy, sym, t0, t1, side=1, entry=10.0):
    d = pd.Timestamp(t0, tz=NY)
    return Trade(sym, strategy, side, d.date(), d, d, entry, entry - side, entry + 2 * side,
                 pd.Timestamp(t1, tz=NY), entry + side, "target", 1.0, -0.2, 1.0)


def _cands():
    return [_tr("A", "XYZ", "2026-10-13 10:00", "2026-10-13 12:00"),
            _tr("A", "XYZ", "2026-10-13 10:30", "2026-10-13 12:00"),
            _tr("A", "XYZ", "2026-10-13 11:00", "2026-10-13 12:00"),      # third concurrent A lot
            _tr("B", "XYZ", "2026-10-13 11:10", "2026-10-13 12:00"),      # other setup, symbol held by A
            _tr("A", "ABC", "2026-10-13 11:20", "2026-10-13 12:00"),
            _tr("A", "ABC", "2026-10-13 11:25", "2026-10-13 12:00"),
            _tr("A", "XYZ", "2026-10-13 12:30", "2026-10-13 13:00")]      # after the earlier lots closed


def _alloc(cfg):
    return Backtester([], cfg).allocate(copy.deepcopy(_cands()))


def _keys(df):
    return [(x.strategy, x.symbol, x.entry_time.strftime("%H%M")) for x in df.itertuples()]


def test_backtest_default_unchanged_and_cap_two():
    base = _keys(_alloc(_cfg()))
    assert base == [("A", "XYZ", "1000"), ("A", "ABC", "1120"), ("A", "XYZ", "1230")]   # one position per symbol
    cfg = _cfg()
    cfg["strategies"]["A"] = {"enabled": False, "max_lots_per_symbol": None}
    assert _keys(_alloc(cfg)) == base
    two = _keys(_alloc(_cfg({"A": 2})))
    assert two == [("A", "XYZ", "1000"), ("A", "XYZ", "1030"), ("A", "ABC", "1120"), ("A", "ABC", "1125"),
                   ("A", "XYZ", "1230")]
    assert _keys(_alloc(_cfg({"A": 2}, lots=1))) == base       # the account lot cap still binds


def test_backtest_live_parity():
    """Same sequence through RiskManager (live) and allocate (backtest) -> same accepted lots."""
    cfg = _cfg({"A": 2})
    bt = _keys(_alloc(cfg))
    rm = RiskManager(cfg, 100000)
    live, open_ = [], []
    for tr in _cands():
        open_ = [o for o in open_ if o.exit_time > tr.entry_time]
        rm.state.open_symbols = {o.symbol for o in open_}
        rm.state.lots = {s: [(o.strategy, o.side) for o in open_ if o.symbol == s] for s in rm.state.open_symbols}
        # live lets B stack beside A (account cap 3); the backtest keeps other setups out of a held symbol as before
        if tr.strategy != "A":
            continue
        if rm.check(Signal(tr.symbol, tr.strategy, tr.side, 10, stop=tr.stop), tr.entry)[0]:
            open_.append(tr)
            live.append((tr.strategy, tr.symbol, tr.entry_time.strftime("%H%M")))
    assert live == bt


@pytest.mark.parametrize("val", [2])
def test_workbench_set_accepts_key(tmp_path, val, monkeypatch):
    from mcf.report import blueprint as B
    from mcf.research import workbench as W
    bp = {"block": {"enabled": True, "window": [1000, 1500]}, "module": None, "geom": "atr", "account": "testing", "name": "P1"}
    monkeypatch.setattr(B, "extract", lambda parent, with_record=False: bp)
    assert B.params(bp)["max_lots_per_symbol"] is None
    rec = W.spawn("P1", f"max_lots_per_symbol={val}", out_dir=tmp_path, today="2026-11-16")
    assert (rec["param"], rec["old"], rec["new"]) == ("max_lots_per_symbol", None, val)
    stub = (tmp_path / "P1" / f"{rec['id']}.yaml").read_text()
    assert f"max_lots_per_symbol: {val}" in stub and json.loads((tmp_path / "P1" / "variants.jsonl").read_text())["new"] == val
