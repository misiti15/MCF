"""Research running order (owner CAP1 2026-11-03): research/queue.jsonl + mcf/research/queue.py; owner items go to
the front, `next(n)` and the nightly job budget (default 6). Educational only - not financial advice."""
import json
from pathlib import Path

import pytest

from mcf.research import queue as Q

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {"id", "title", "added_by", "added_at", "priority", "status", "est_jobs"}


def test_order_owner_front_next_and_budget(tmp_path, monkeypatch):
    p = tmp_path / "q.jsonl"
    monkeypatch.setattr(Q, "QUEUE", p)
    Q.add("AA: claude item", "claude", est_jobs=2)
    Q.add("BB: another", "claude", est_jobs=3)
    Q.add("CC: owner item", "owner", est_jobs=4)
    Q.add("DD: second owner item", "owner 2026-11-03", est_jobs=1)
    assert [e["id"] for e in Q.next(4)] == ["DD", "CC", "AA", "BB"]       # newest owner item first, then the rest in order
    assert [e["id"] for e in Q.next(2)] == ["DD", "CC"] and Q.next(0) == []
    assert [e["id"] for e in Q.tonight(6)] == ["DD", "CC"]              # 1 + 4 jobs; A (2) would exceed 6
    assert [e["id"] for e in Q.tonight(8)] == ["DD", "CC", "AA"]
    Q.set_status("DD", "done")
    assert Q.next(1)[0]["id"] == "CC"
    with pytest.raises(ValueError):
        Q.add("AA: dup", "claude")
    with pytest.raises(ValueError):
        Q.set_status("AA", "bogus")
    Q.add("EE: big", "claude", est_jobs=9, priority=1)
    assert [e["id"] for e in Q.tonight(6)] == ["CC", "AA"]            # E (9) does not fit after C (4); A (2) does
    Q.set_status("CC", "done")
    assert [e["id"] for e in Q.tonight(6)] == ["EE"]                   # too big for the budget but first: runs alone


def test_default_budget_and_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(Q, "QUEUE", tmp_path / "q.jsonl")
    assert Q.max_jobs({}) == 6 and Q.max_jobs({"research_queue": {"max_jobs_per_night": 4}}) == 4
    from mcf.config import load_config

    assert load_config()["research_queue"]["max_jobs_per_night"] == 6
    Q.main(["add", "X1: test", "--by", "owner", "--jobs", "2"])
    Q.main(["next", "-n", "1"])
    assert "X1" in capsys.readouterr().out


def test_repo_queue_has_combo1_on_top():
    es = [json.loads(l) for l in (ROOT / "research/queue.jsonl").read_text().splitlines() if l.strip()]
    assert all(FIELDS <= set(e) for e in es)
    nxt = Q.next(3, es)
    assert nxt[0]["id"] == "COMBO1" and nxt[0]["added_by"] == "owner"
    ids = {e["id"] for e in es}
    assert {"COMBO1", "GY-BP", "SWING-L1-L3"} <= ids


RESEARCH_WORKFLOWS = ("cwt-transcripts", "reddit-archive", "reddit-dumps", "public-data", "t2-diag", "earnings-data")


def test_research_workflows_capped_at_4_slots():
    import yaml

    for name in RESEARCH_WORKFLOWS:
        wf = yaml.safe_load((ROOT / ".github/workflows" / f"{name}.yml").read_text())
        assert wf["concurrency"]["group"] == "mcf-research", name           # one research run at a time
        assert wf["concurrency"]["cancel-in-progress"] is False, name
        for job, j in wf["jobs"].items():
            if "matrix" in (j.get("strategy") or {}):
                assert 1 <= int(j["strategy"]["max-parallel"]) <= 4, (name, job)
    trade = yaml.safe_load((ROOT / ".github/workflows/trade.yml").read_text())
    assert "mcf-research" not in str(trade.get("concurrency")) and "mcf-research" not in str(trade["jobs"])
