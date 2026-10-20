"""Allocator (owner 2026-10-20, 'Goals for copies'): balances the two testing accounts, keeps setup / -FD pairs and
crowding pairs apart, proposes split-ticker copies, and --apply edits only the testing configs."""
import shutil
from pathlib import Path

import pytest

import mcf.config as C
from mcf.report import assignments as A
from mcf.research import allocate as AL


def rec(name, sessions=5, signals=50, verdict="ok", lost_to=None, skipped=None, exp=None):
    return {"setup": name, "sessions": sessions, "signals": signals, "verdict": verdict, "lost_to": lost_to or {},
            "skipped": skipped or {}, "expected_per_day": exp}


def test_problem_balances_separates_and_splits():
    cur = {"A": "testing", "A-FD": "testing", "B": "testing", "C": "testing", "D": "testing2", "E": "testing"}
    cards = {"testing": {"setups": [rec("A", signals=100), rec("A-FD", signals=100),
                                    rec("B", signals=50, lost_to={"C": 40}), rec("C", signals=50, lost_to={"B": 40}),
                                    rec("E", signals=20, verdict="crowded-out", skipped={"held_by_other": 30})]},
             "testing2": {"setups": [rec("D", signals=10)]}}
    stats = AL.setup_stats(sorted(cur), cur, cards)
    assert stats["A"]["load"] == 20 and stats["E"]["crowd_lost_per_day"] == 6
    p = AL.Problem(stats, cur, set())
    asg = p.solve(n_split=1, min_lost=1.0)
    assert asg["E"] == "both"                                   # crowded-out -> split copy
    assert asg["A"] != asg["A-FD"]                              # setup and its -FD apart
    assert asg["B"] != asg["C"]                                 # high mutual lost_to apart
    parts = p.parts(asg)
    assert parts["fd"] == 0 and parts["imbalance"] < p.parts(dict(cur))["imbalance"]
    assert p.solve(n_split=1) == asg                            # deterministic
    assert AL.Problem(stats, cur, {"E"}).solve(n_split=1)["E"] != "both"   # fixed-symbol setups never split


def test_no_moves_when_already_good():
    cur = {"A": "testing", "B": "testing2"}
    cards = {"testing": {"setups": [rec("A")]}, "testing2": {"setups": [rec("B")]}}
    p = AL.Problem(AL.setup_stats(sorted(cur), cur, cards), cur, set())
    assert p.solve() == cur


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    d = tmp_path / "config"
    shutil.copytree(C.CONFIG_DIR, d)
    monkeypatch.setattr(C, "CONFIG_DIR", d)
    return d


def test_apply_edits_only_testing_configs(tmp_config):
    before = A._strategies()
    t1 = [s for s in A.current(before)["testing"] if not s.startswith("IDX")]
    t2 = A.current(before)["testing2"]
    mover, splitter = t1[0], t1[1]
    cards = {"testing": {"setups": [rec(mover, signals=500), rec(splitter, verdict="starved",
                                                                 skipped={"held_by_other": 100})]},
             "testing2": {"setups": []}}
    d = AL.propose(n_split=1, cards=cards)
    # force a known proposal: one move T1 -> T2, one new split copy, everything else stays
    for r in d["rows"]:
        r["proposed"] = r["current"]
        if r["setup"] == mover:
            r["proposed"] = "testing2"
        if r["setup"] == splitter:
            r["proposed"] = "both"
    AL.apply(d, today="2026-10-20")
    assert AL.verify(d) == []
    after = A._strategies()
    for a in ("primary", "gen"):
        assert after[a] == before[a]
    strip = lambda b: {k: v for k, v in b.items() if k not in ("enabled", "ticker_split")}   # noqa: E731
    assert strip(after["testing2"][mover]) == strip(before["testing"][mover])      # full block copied
    assert strip(after["testing2"][splitter]) == strip(before["testing"][splitter])
    assert after["testing"][splitter]["ticker_split"] == {"part": 0, "of": 2}
    assert after["testing2"][splitter]["ticker_split"] == {"part": 1, "of": 2}
    import yaml
    o1 = yaml.safe_load((tmp_config / "account_testing.yaml").read_text())["live"]["setup_order"]
    o2 = yaml.safe_load((tmp_config / "account_testing2.yaml").read_text())["live"]["setup_order"]
    assert mover not in o1 and mover in o2 and splitter in o1 and splitter in o2
    assert set(A.current(after)["testing2"]) == set(t2) | {mover, splitter}
    from test_assignments import split_violations
    assert split_violations(after) == []
    md = AL.markdown(d)
    assert "Educational only" in md and mover in md
    sp = A.build(None)["setups"][splitter]["split"]                 # dashboard: one row, "split tickers" label
    assert sp == {"testing": {"part": 0, "of": 2}, "testing2": {"part": 1, "of": 2}}


def test_dashboard_merges_split_copies():
    html = (Path(__file__).resolve().parents[1] / "docs/live/index.html").read_text()
    assert '" (split tickers)"' in html and ">split copies</span>" in html
    assert '"split copies": "The setup runs in both testing accounts, each on its own half of the tickers, so no signal ' \
           'is traded twice; stats are combined."' in html
    assert "groups[r.setup]" in html                                  # rows still merge by setup name
