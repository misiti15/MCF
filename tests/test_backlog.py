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
