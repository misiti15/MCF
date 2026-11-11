"""bdi1110: append tonight's backlog entries (idempotent by id). Usage: python research/bdi/1110/add_backlog.py
Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI daily 2026-11-10 (research/bdi/1110/NOTES.md)"
NEW = [
 {"id": "mfx1-1110-midday-flip-open-book-exit", "title": "MFX1: when SPY crosses back over its open for 15 min after 12:00, close the open trades on the morning side",
  "category": "exit", "status": "parked", "configs_tried": 1, "module": "research/bdi/1110/mfx1.py", "parent": "nightly-1110-midday-flip-open-book-exit",
  "hypothesis": "11-10 swing autopsy: Primary +9.1R (10:55) -> -34.5R (15:51); 12:45->15:51 -26.9R with market -30.2R and 45 shorts open after SPY flipped back above its open (14:31 flip).",
  "tags": ["bdi1110", "bdi", "exit", "compass", "swing", "qday", "remedy"],
  "notes": "Pre-registered (MFX1_PLAN.md, commit c25f74282), 1 config, lineage N 34 (bar 2.66 / BAR90 2.39). 2 years (bt_lab1104 + 5-min marks, every lab setup, costs in, locked block excluded): 107 flip days of 457 (44 false). TRAIN +1,555.9R (t 2.92), VALID -79.8R (t -0.17; true flips +713.7R, false flips -793.6R), LATE +202.4R (t 2.60); VALID families 4 better / 5 worse (NS -67.3R, GEN -42.2R, exhaustion -22.9R, L -15.8R, RW -8.2R vs MF +31.1R, CWT +28.2R, ST +12.8R, NM +4.4R); setups 22 better / 24 worse -> FAIL. 11-10 in-sample +56.3R across 5 accounts (P +4.69R). Forward shadow swing1110-L12. Educational only - not financial advice."},
 {"id": "mfx2-1110-flip-magnitude", "title": "MFX2 (rework of MFX1, not run): close the morning-side book only once SPY is >= 0.15% across its open after 12:00 (a real flip, not a wiggle)",
  "category": "exit", "status": "idea", "configs_tried": 0, "module": None, "parent": "mfx1-1110-midday-flip-open-book-exit",
  "hypothesis": "MFX1's VALID loss is all false flips (-793.6R) against +713.7R on true flips; compass-learn's R2 truth (SPY moves >= 0.25% against the morning side) suggests a magnitude condition separates them. Costs: fewer, later exits.",
  "tags": ["bdi1110", "exit", "compass", "qday", "rework"],
  "notes": "Pre-register the threshold before scoring (one value, 0.15%); counts in the flip lineage (N 35). Educational only - not financial advice."},
]
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}; n = 0
for e in NEW:
    if e["id"] not in have:
        e.update({"added": "2026-11-10", "source": SRC, "variant": None}); e.setdefault("parent", None); rows.append(e); n += 1
B.write_text("".join(json.dumps(r) + "\n" for r in rows)); print(n, "added;", len(rows), "entries")
