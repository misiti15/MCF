"""Setup Generator seeds from the weekly Setup lab scan (owner 2026-10-19): faithful layer mapping, variants that meet
the generator rules (>= 3 conditions incl. a window and a context filter), unmappable rules skipped with a reason, and
a run that tolerates a missing discovery report. Educational only - not financial advice."""
import json

import numpy as np

from mcf.research.generator import seeds as SD
from mcf.research.generator.spec import CONTEXT, WINDOWS, valid_seed


def _disc(cands):
    return {"generated": "2026-10-17", "candidates": cands}


def test_layer_mapping():
    w, conds, why = SD.translate(["RSI14 > 65", "gap within 2%", "09:50-11:00"])
    assert why is None and w == "AM"
    assert conds == [("rsi", ">", 65.0), ("gap", ">=", -2.0), ("gap", "<=", 2.0)]
    assert SD.translate(["above 20 SMA"])[1] == [("sma20_dist_pct", ">", 0.0)]
    assert SD.translate(["above VWAP"])[1] == [("vwap_atr", ">", 0.0)]
    assert SD.translate(["new high of day"])[1] == [("new_hod", "==", 1.0)]
    assert SD.translate(["up > 2% from open"])[1] == [("fromOpen", ">", 2.0)]
    assert SD.translate(["gap down > 2%"])[1] == [("gap", "<", -2.0)]
    assert SD.nearest_window("11:00-13:30") == "MID"
    assert SD.nearest_window("13:30-15:00") == "PM"


def test_variants_meet_generator_rules():
    d = _disc([{"side": "short", "layers": ["RSI14 > 65", "gap within 2%", "09:50-11:00"], "replicated": True},
               {"side": "long", "layers": ["new high of day", "above 20 SMA"], "replicated": True},
               {"side": "long", "layers": ["above VWAP"], "replicated": False}])
    specs, info, meta = SD.generate(d, set(), set(), log=lambda *a: None)
    assert info["replicated"] == 2 and info["mapped"] == 2 and not info["skipped"]
    per = {}
    for s in specs:
        ok, why = valid_seed(s)
        assert ok, why
        assert s.n_conditions() >= 3 and s.window in WINDOWS
        assert sum(c[0] in CONTEXT for c in s.conds) == 1
        per.setdefault(tuple(meta[s.key()]["layers"]), []).append(s)
        assert meta[s.key()]["source"] == "discovery 2026-10-17"
    assert all(1 <= len(v) <= SD.MAX_VARIANTS for v in per.values())
    am = per[("RSI14 > 65", "gap within 2%", "09:50-11:00")]
    assert {s.window for s in am} == {"AM"} and {s.geom for s in am} == {"t1s1", "t05s1", "holdtr"}
    assert all(s.side == "short" for s in am)
    nowin = per[("new high of day", "above 20 SMA")]
    assert {s.window for s in nowin} == set(SD.NO_WINDOW)
    # registry dedupe and prior-family avoidance, as for random specs
    specs2, info2, _ = SD.generate(d, {s.key() for s in specs}, set(), log=lambda *a: None)
    assert not specs2 and info2["rejected"]["seen"] == len(specs)
    specs3, info3, _ = SD.generate(d, set(), {s.family() for s in am}, log=lambda *a: None)
    assert not ({s.key() for s in specs3} & {s.key() for s in am}) and info3["rejected"]["tried_family"] == len(am)


def test_unmappable_layers_are_skipped_with_a_reason():
    d = _disc([{"side": "long", "layers": ["rvol >= 2", "new high of day", "09:50-11:00"], "replicated": True},
               {"side": "long", "layers": ["moon phase full"], "replicated": True}])
    specs, info, meta = SD.generate(d, set(), set(), log=lambda *a: None)
    assert not specs and info["mapped"] == 0 and len(info["skipped"]) == 2
    assert "rvol" in info["skipped"][0]["reason"]
    assert "no mapping" in info["skipped"][1]["reason"]


def test_missing_discovery_is_no_seeds(tmp_path):
    assert SD.load_discovery(tmp_path / "nope.json", log=lambda *a: None) is None
    specs, info, meta = SD.generate(None, set(), set(), log=lambda *a: None)
    assert specs == [] and meta == {} and info["seeds"] == 0


class _FakePanel:
    """A tiny panel with the attributes run() reads; every spec scores nothing (no rows match)."""

    def __init__(self):
        n = 4
        self.n, self.n_days = n, 2
        self.a = {"tod": np.array([1000, 1005, 1000, 1005], np.int16), "adv20": np.full(n, 1e9, np.float32)}
        self.sd = np.array([0, 0, 1, 1], np.int32)
        self.day = np.array([0, 0, 1, 1], np.int32)
        self.days = np.array(["2025-06-02", "2026-03-02"], dtype=object)
        self.split = np.array([0, 0, 1, 1], np.int8)


def test_run_tolerates_missing_discovery(tmp_path, monkeypatch):
    from mcf.research.generator import apply as A
    from mcf.research.generator import screen as S

    seen = {}

    def fake_screen(P, specs, workers=4, log=print):
        seen["n"] = len(specs)
        return [{"key": s.key(), "score": None, "tier1": False} for s in specs]

    monkeypatch.setattr(S, "quantile_table", lambda P, seed=0: {})
    monkeypatch.setattr(S, "tried_families", lambda: set())
    monkeypatch.setattr(S, "screen", fake_screen)
    monkeypatch.setattr(S, "existing_keys", lambda P, months, log=print: ({}, []))
    monkeypatch.setattr(S, "evaluate", lambda P, s, keep_keys=False: {"_keys": np.empty(0, np.int64)})
    monkeypatch.setattr(A, "load_account", lambda: json.loads(json.dumps(A.BASE)))
    monkeypatch.setattr(A, "registry_keys", lambda: set())
    rep = A.run("2026-10-19", n=2, n_specs=0, panel=_FakePanel(), log=lambda *a: None,
                discovery=tmp_path / "missing.json")
    assert rep["seeds"]["seeds"] == 0 and rep["picks"] == [] and rep["n_tried"] == 0
    # with a report, the seeds join the same screen and count in n_tried
    f = tmp_path / "latest.json"
    f.write_text(json.dumps(_disc([{"side": "short", "layers": ["RSI14 > 65", "gap within 2%", "09:50-11:00"],
                                    "replicated": True}])))
    rep = A.run("2026-10-19", n=2, n_specs=0, panel=_FakePanel(), log=lambda *a: None, discovery=f)
    assert rep["seeds"]["seeds"] == 6 == rep["seeds"]["screened"] == rep["n_tried"] == seen["n"]
    rep = A.run("2026-10-19", n=2, n_specs=0, panel=_FakePanel(), log=lambda *a: None, discovery=f, seeds=False)
    assert rep["seeds"] is None and rep["n_tried"] == 0
