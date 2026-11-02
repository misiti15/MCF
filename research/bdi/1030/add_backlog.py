"""bdi1030: append tonight's backlog entries (idempotent by id) and add notes to two Move Hunt items.
Usage: python research/bdi/1030/add_backlog.py     Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI daily 2026-10-30 (research/bdi/1030/NOTES.md)"
NEW = [
 {"id": "mh-1030-open-pdh-pop-fade", "title": "MH3 opening pop into the prior-day high, faded (short) / opening flush into the prior-day low, bought (long), 09:35-09:45, with and without an SPY-direction gate",
  "category": "setup", "status": "failed", "configs_tried": 12, "module": "research/bdi/1030/mh3_open_pdh.py",
  "hypothesis": "Move Hunt 10-30: 33 of the 50 biggest tradable moves started at 09:35-09:45 and live caught 0 of them; 10+ of the 25 biggest short moves were names up from the open with RSI5 >= 70 sitting within ~0.3 ATR of the prior-day high (WSM, MTN, GAP, QLYS, M, ULTA, KSS, NOC, BUG, DOV). One-day precision (k 0.30 short) 51% reached >= 0.5 ATR down in 90 min vs a 34% base rate.",
  "tags": ["bdi1030", "bdi", "setup", "move-hunt", "open", "pdh", "pdl"],
  "notes": "Tested 2026-10-30 on the timeofday open frame (2 years, locked block absent, adv20 >= 95M, blackout removed, production costs with the 09:35 entry multiplier): 12 configs (side x k 0.15/0.30 x exit t1s1 / stop-0.25ATR-hold-to-10:30, plus SPY-gated k 0.30). All negative: shorts -0.134..-0.181R (t -5.3..-7.7), longs -0.114..-0.150R (t -4.3..-6.7); train and valid both negative; excess vs a random 09:35 entry -0.04..+0.01R; shorts win only on down days (+0.09R) and lose on up days (-0.35R), longs the mirror. The SPY-direction gate makes both sides worse (shorts -0.173R). The 10-30 precision was the down day, not the level. Bar: N 12, full 2.23, BAR90 2.01; best t -4.34; no locked look. Educational only - not financial advice."},
]
NOTES = {
 "mh-1029-open-drive-window": " bdi1030: day 2 of the Move Hunt - 33 of the 50 biggest tradable moves had their best decision point at 09:35-09:45 (10-29: 30 of 50); live caught 0 of the 33 (10-29: 5 of 30). An opening frame already exists (research/bdi/timeofday/data/open, 09:35-10:30, 2 years); its first use tonight (mh-1030-open-pdh-pop-fade, 12 configs) failed: the opening moves follow the day's direction, and the 09:35 entry cost (3.8x) eats any excess.",
 "mh-1029-earnings-sympathy": " bdi1030: the cyber-security peer group fell again at the 09:35-09:40 bars on 10-30 (RBRK -1.20, NTSK -1.17, QLYS -1.15, BUG -1.04 ATR within ~35 min), a second-day follow-through of the 10-29 TENB sympathy move; retailers (GAP, M, KSS, ULTA, WSM) fell as a group at 09:35. Group moves at the open keep showing up; a rework needs industry peers and the 09:35 frame.",
}
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}
for r in rows:
    if r["id"] in NOTES and "bdi1030" not in r.get("notes", ""):
        r["notes"] = (r.get("notes") or "") + NOTES[r["id"]]
for e in NEW:
    if e["id"] not in have:
        e.update({"added": "2026-10-30", "source": SRC, "variant": None, "parent": None})
        rows.append(e)
B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print(len(rows), "entries")
