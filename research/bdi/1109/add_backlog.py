"""bdi1109: append tonight's backlog entries (idempotent by id). Usage: python research/bdi/1109/add_backlog.py
Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI daily 2026-11-09 (research/bdi/1109/NOTES.md)"
NEW = [
 {"id": "ecg1-1109-early-compass-momentum-short-gate", "title": "ECG1: block new momentum shorts (MF / flowsell / L3) from 10:00 while the W60 15-min compass is UP-confirmed",
  "category": "filter", "status": "parked", "configs_tried": 1, "module": "research/bdi/1109/ecg1.py", "parent": "nightly-1109-mf-short-upconfirmed-gate",
  "hypothesis": "11-09 swing autopsy: Primary MF4-FD 17 shorts 10:20-10:51 entered after W60 confirmed UP at 10:00 (-17.1R); the 11:00 GATE1 checkpoint was too late.",
  "tags": ["bdi1109", "bdi", "compass", "filter", "short", "swing", "qday"],
  "notes": "2 years (bt_lab1104, 158,472 family shorts, 14 setups, costs in, locked block excluded), 1 config (lineage N 34, bar 2.66, BAR90 2.39): TRAIN -463.9R (t -0.18), VALID +605.7R (t 0.67, best day 66%), LATE +319.4R; 2 setups worse (L3-fromopen -110R) -> fails. Pays on up-close days (VALID +2,472R) and loses on quiet (-1,360R) / down-close (-507R) days. 11-09 in-sample +40.3R. Forward shadow swing1109-L11. Educational only - not financial advice."},
 {"id": "ecg2-1109-strong-up-gate", "title": "ECG2 (rework of ECG1, not run): the same momentum-short gate only when the UP compass is also strong (SPY >= +0.75% from its open at the mark)",
  "category": "filter", "status": "idea", "configs_tried": 0, "module": None, "parent": "ecg1-1109-early-compass-momentum-short-gate",
  "hypothesis": "ECG1 gains only on days that close up and loses on W60-UP mornings that end quiet / down; a strength condition may pick the days that keep going (GATE1 'strong move' holds its side 89-97%).",
  "tags": ["bdi1109", "compass", "filter", "short", "qday", "rework"],
  "notes": "Pre-register before scoring; counts in the MF short-gate lineage (N 35). Educational only - not financial advice."},
 {"id": "mh-1109-inplay-compass-side", "title": "MH1109-P1: at 10:00 with W60 confirmed, trade in-play names (vol_exp >= 0.12) already moving the compass's way, both directions, t1s1",
  "category": "setup", "status": "parked", "configs_tried": 1, "module": "research/bdi/1109/mh_p1.py",
  "hypothesis": "Move Hunt 11-09 (and 11-05 / 11-06): vol_exp is the one recurring precursor of big moves but has no direction (MH1); take the direction from the market compass.",
  "tags": ["bdi1109", "move-hunt", "both-sides", "setup", "qday", "compass"],
  "notes": "2 years (lab frames 10:00 bar, t1s1 re-costed to production, locked block excluded), 1 config (MH lineage N 4, bar 1.67 / BAR90 1.50): 217 confirmed days, class A n 78,822, win 47.2% vs base 45.2% (precision +2.0 pts) but avg R -0.138 vs base -0.111, excess -0.005 (day-t -0.59); TRAIN -0.119 / VALID -0.154; long -0.134, short -0.141; months positive 18% -> fails both bars and the light lane. QDAY: shorts on down-close days -0.005, longs on up-close days -0.022, everything on quiet days -0.22..-0.30. 11-09 in-sample +0.610 vs base +0.453 (excess +0.157). In play + compass side does not pick direction beyond the base rate. Educational only - not financial advice."},
]
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}; n = 0
for e in NEW:
    if e["id"] not in have:
        e.update({"added": "2026-11-09", "source": SRC, "variant": None}); e.setdefault("parent", None); rows.append(e); n += 1
B.write_text("".join(json.dumps(r) + "\n" for r in rows)); print(n, "added;", len(rows), "entries")
