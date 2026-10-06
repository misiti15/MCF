import json

import pytest

from mcf.research import backlog as b


def test_gates_and_holdout_once(tmp_path, monkeypatch):
    monkeypatch.setattr(b, "BACKLOG", tmp_path / "backlog.jsonl")
    monkeypatch.setattr(b, "RESULTS", tmp_path / "results.jsonl")
    monkeypatch.setattr(b, "REPORT", tmp_path / "BACKLOG.md")
    b.save([{"id": "x", "title": "X", "status": "testing", "module": None, "variant": None},
            {"id": "y", "title": "Y", "status": "finalist", "module": None, "variant": None}])
    assert b._passes({"n": 40, "exp_r": 0.05, "t_day_clustered": 2.0}, 30, 1.5)
    assert not b._passes({"n": 40, "exp_r": 0.05, "t_day_clustered": 1.0}, 30, 1.5)
    assert not b._passes({"n": 10, "exp_r": 0.5, "t_day_clustered": 3.0}, 30, 1.5)
    with pytest.raises(SystemExit):
        b.holdout("x")                      # not a finalist
    (tmp_path / "results.jsonl").write_text(json.dumps({"id": "y", "split": "test", "metrics": {}}) + "\n")
    with pytest.raises(SystemExit):
        b.holdout("y")                      # already scored once
    b.report()
    assert "| finalist | y |" in (tmp_path / "BACKLOG.md").read_text()


def test_rework_holdout_looks_raise_the_bar(tmp_path, monkeypatch):
    monkeypatch.setattr(b, "BACKLOG", tmp_path / "backlog.jsonl")
    monkeypatch.setattr(b, "RESULTS", tmp_path / "results.jsonl")
    monkeypatch.setattr(b, "REPORT", tmp_path / "BACKLOG.md")
    es = [{"id": "a", "title": "A", "status": "holdout_failed", "holdout_burned": True},
          {"id": "a2", "title": "A rsi10", "status": "finalist", "parent": "a", "module": "m", "variant": "v"}]
    b.save(es)
    assert b.holdout_looks(es[1], es) == 1          # the ancestor's look counts
    monkeypatch.setattr(b, "_score", lambda e, s, v=None: {"n": 50, "exp_r": 0.1, "t_day_clustered": 1.2})
    b.holdout("a2")                                  # look 2 needs t >= 1.5: 1.2 fails
    assert next(e for e in b.entries() if e["id"] == "a2")["status"] == "holdout_failed"
    b.save(b.entries() + [{"id": "a3", "title": "A rsi10+vwap", "status": "finalist", "parent": "a2", "module": "m", "variant": "v"}])
    monkeypatch.setattr(b, "_score", lambda e, s, v=None: {"n": 50, "exp_r": 0.1, "t_day_clustered": 2.1})
    b.holdout("a3")                                  # look 3 needs t >= 2.0: passes -> probation
    assert next(e for e in b.entries() if e["id"] == "a3")["status"] == "probation"
