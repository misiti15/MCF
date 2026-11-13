"""bdi1112: append tonight's backlog entry (idempotent by id). Usage: python research/bdi/1112/add_backlog.py
Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI daily 2026-11-12 (research/bdi/1112/NOTES.md)"
NEW = [
 {"id": "bdi-1112-l3-fromopen-cap-overflow", "title": "L3-gap-slope-fromopen-FD: on days its 30-lot sleeve is full, let extra first-signal lots (new symbols only) use free slots, half size",
  "category": "risk", "status": "idea", "configs_tried": 0, "module": "research/bdi/1112/l3cap.py", "parent": "nightly-1015-l3-fromopen-refire-cap",
  "hypothesis": "11-12 Primary: L3 52 shorts +30.97R but 648 'max positions for this setup' skips over 135 symbols (125 of them 11:00-11:59 as SPY topped). First skip per symbol, gross what-if (stop/target/15:50): 135 lots +108.9R (avg +0.81R, 99% win); 103 never-traded symbols +82.4R. Upper bound, one strong-fade day; buying power not modelled.",
  "tags": ["bdi1112", "bdi", "risk", "caps", "l3", "playing-time"],
  "test_needed": "2-year lab: L3-fromopen with sleeve 30 vs 45 / 60 / overflow-at-half-size, costs in, buying power modelled, report per-day R distribution and the one-big-day share (cap days are big-fade days: check the downside on cap days that reversed). Pre-register before scoring.",
  "notes": "No test tonight (lean BDI). Cap days are probably the best L3 days, so the extra R will concentrate on few sessions -- check avg R w/o best day. Educational only - not financial advice."},
]
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}; n = 0
for e in NEW:
    if e["id"] not in have:
        e.update({"added": "2026-11-12", "source": SRC, "variant": None}); rows.append(e); n += 1
B.write_text("".join(json.dumps(r) + "\n" for r in rows)); print(n, "added;", len(rows), "entries")
