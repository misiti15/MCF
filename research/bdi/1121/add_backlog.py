"""BD&I Saturday 1121: append tonight's backlog entries (idempotent by id), then re-render research/BACKLOG.md through
mcf.research.backlog (report()). Usage: python research/bdi/1121/add_backlog.py
Educational only - not financial advice."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.research import backlog as BL  # noqa: E402
SRC = "BD&I Saturday 2026-11-21 (research/bdi/1121/REPORT.md)"
EDU = " Educational only - not financial advice."
NEW = json.loads((Path(__file__).resolve().parent / "backlog_new.json").read_text())
es = BL.entries()
have = {e["id"] for e in es}
n = 0
for e in NEW:
    if e["id"] in have:
        continue
    e.setdefault("added", "2026-11-21"); e.setdefault("source", SRC); e.setdefault("variant", None)
    e.setdefault("parent", None); e.setdefault("module", None)
    e["notes"] = e.get("notes", "").rstrip() + EDU
    es.append(e); n += 1
BL.save(es)
BL.report()
print(n, "added;", len(es), "entries")
