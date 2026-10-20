"""Owner 2026-10-20: the dashboard's setup assignments must always match the configs. Any promotion / demotion /
move must regenerate docs/live/assignments.json (python -m mcf.report.assignments) in the same commit."""
import json
from pathlib import Path

from mcf.report import assignments as A


def test_assignments_file_matches_configs():
    d = json.loads((Path(A.OUT)).read_text())
    cur = A.current()
    assert d["accounts"] == cur, "docs/live/assignments.json is stale: run python -m mcf.report.assignments"
    for name, v in d["setups"].items():
        assert v["accounts"] == sorted(a for a, s in cur.items() if name in s), name
    assert d.get("last_change", {}).get("at")


def test_build_stamps_only_real_changes():
    prev = A.build(None)
    same = A.build(prev)
    assert same["last_change"] == prev["last_change"]          # nothing moved: timestamp unchanged
    moved = json.loads(json.dumps(prev))
    k = next(iter(moved["setups"]))
    moved["setups"][k]["accounts"] = ["nowhere"]
    new = A.build(moved)
    assert new["last_change"]["changes"][0]["setup"] == k and new["setups"][k]["since"]
