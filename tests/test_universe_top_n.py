"""UNI1 (owner 2026-11-03): Testing 2 trades only a top-500 pool (ADV >= $95M, ranked by ADV x ATR%) from 11-04;
other accounts are unchanged and the full universe still feeds breadth. Educational only - not financial advice."""
from types import SimpleNamespace

import numpy as np
import pandas as pd

from mcf.config import load_config
from mcf.data.universe import top_n_symbols


def test_top_n_ranks_by_adv_x_atr_after_adv_floor():
    rows = [("A", 200e6, 2.0),    # 400e6
            ("B", 100e6, 5.0),    # 500e6
            ("C", 90e6, 10.0),    # below the $95M floor, never in
            ("D", 300e6, 1.0),    # 300e6
            ("E", float("nan"), 3.0)]
    u = {"top_n": 2, "top_n_min_adv": 95e6}
    assert top_n_symbols(rows, u) == {"A", "B"}
    assert top_n_symbols(rows, {"top_n": 10}) == {"A", "B", "D"}   # default floor $95M
    assert top_n_symbols(rows, {}) is None and top_n_symbols(rows, {"top_n": None}) is None


def test_only_testing2_sets_top_500(monkeypatch):
    monkeypatch.setenv("MCF_ACCOUNT", "testing2")
    u = load_config()["universe"]
    assert u["top_n"] == 500 and u["top_n_min_adv"] == 95_000_000
    for acct in ("primary", "testing"):
        monkeypatch.setenv("MCF_ACCOUNT", acct)
        assert not load_config()["universe"].get("top_n")


def _prior(adv, atr, close=100.0):
    return SimpleNamespace(adv=adv, atr=atr, prev_close=close)


def test_runner_pool_restricts_contexts_but_keeps_pinned(monkeypatch):
    from mcf.execution import runner as R

    r = R.PaperRunner.__new__(R.PaperRunner)
    r.health = {}
    r.cfg = {"universe": {"top_n": 1, "top_n_min_adv": 95e6},
             "strategies": {"x": {"enabled": True, "type": "index", "symbols": ["SPXL"]}}}
    r.priors = {"BIG": _prior(500e6, 3.0), "SMALL": _prior(100e6, 1.0), "SPXL": _prior(50e6, 2.0)}
    assert r._top_n_pool() == {"BIG", "SPXL"}
    assert r.health["universe_top_n"] == 1
    r2 = R.PaperRunner.__new__(R.PaperRunner)
    r2.health, r2.cfg, r2.priors = {}, {"universe": {}, "strategies": {}}, r.priors
    assert r2._top_n_pool() is None


def test_build_universe_marks_pool(monkeypatch, tmp_path):
    from mcf.data import universe as U

    assets = pd.DataFrame({"symbol": ["A", "B", "C"], "name": list("ABC"), "exchange": ["NYSE"] * 3,
                           "shortable": [True] * 3, "easy_to_borrow": [True] * 3, "marginable": [True] * 3,
                           "attributes": [None] * 3})
    stats = pd.DataFrame({"symbol": ["A", "B", "C"], "price": [50.0] * 3, "adv": [200e6, 120e6, 20e6],
                          "avg_volume": [1e6] * 3, "atr": [1.0, 3.0, 2.0], "days": [20] * 3})
    stats["atr_pct"] = stats.atr / stats.price * 100
    monkeypatch.setattr(U, "_clients", lambda: (None, None))
    monkeypatch.setattr(U, "candidate_assets", lambda tc: assets)
    monkeypatch.setattr(U, "daily_stats", lambda dc, syms: stats)
    cfg = {"universe": {"min_avg_dollar_volume": 5e6, "extended_min_avg_dollar_volume": 1e6, "min_atr_pct": 1.0,
                        "top_n": 1}, "costs": {"min_price": 1.0}, "strategies": {}}
    df = U.build_universe(cfg, str(tmp_path / "u.csv"))
    assert len(df) == 3                                              # full universe kept (breadth, priors)
    assert df.set_index("symbol").top_n.to_dict() == {"A": False, "B": True, "C": False}
    assert np.isfinite(df.adv).all()
