"""nightly1110: append tonight's backlog hypotheses (idempotent by id; status idea) and add 11-10 evidence to
swing1103-L6-counter-index-entries. Usage: python research/bdi/nightly1110/add_backlog.py   Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[2] / "backlog.jsonl"
SRC = "nightly learning loop 2026-11-10 (research/bdi/nightly1110/NOTES.md, latchopen_out.txt, flip_out.txt)"
NEW = [
 {"id": "nightly-1110-latch-closes-open-lots", "category": "exit", "configs": 0,
  "title": "Per-setup -2R latch: also close (or tighten to breakeven / 0.5R) the setup's lots already open when it latches",
  "hypothesis": "11-10 Primary: RW3-FD, RW5-FD, MF2-FD, MF4-FD and L3-rsi5hi-FD latched at -2.1..-3.1R (13:04-15:43) but carried 43 open lots that went on to -22.46R (day -35.9R for the five); closing them at the latch minute: -9.34R (+13.1R, all 5 better). Same check on T1 / T2 / GY setups that crossed -2R: 19 of 26 setup-days better, 4 worse (all mean-reversion longs: CWT14-failbrk-pdl x3, NM-AR-AM; -5.5R), +48.5R total before costs. The latch stops new lots but the open book keeps the same bet.",
  "test_needed": "2-year lab, every setup with a -2R latch: close / tighten open lots at the latch minute vs keep (costs in, locked block out); split by side and family (fade shorts vs dip-buy longs); per-setup better / worse counts (owner remedies rule); then 20-session forward shadow. One session only so far.",
  "tags": ["nightly1110", "exit", "latch", "risk", "remedy"]},
 {"id": "nightly-1110-midday-flip-open-book-exit", "category": "exit", "configs": 0,
  "title": "Midday flip (SPY back across its open for 15 min after 12:00): close or tighten open lots on the morning-side",
  "hypothesis": "11-10: SPY +0.56% 10:08 -> -0.38% 12:45 -> +0.27% close; the compass-learn standby flip signal confirmed at 14:30. Shorts open at the flip: Primary 50 lots -23.97R actual vs -16.99R closed at the flip (+7.0R), T1 63 -29.69 vs -12.24 (+17.5R), T2 55 -34.94 vs -10.40 (+24.5R), GY 85 -23.37 vs -10.56 (+12.8R); new shorts after the flip lost too (P 5 -0.85R, T1 11 -6.42R). Complements L11 / ECG2 (entry gates) with an exit for lots already open.",
  "test_needed": "2-year lab with the compass_5m flip detector (94% recall / 70% precision per research/compass_learn/NOTES.md): exit vs tighten vs keep open lots on the pre-flip side, by family; count false flips' cost; costs in, locked block out; per-setup better / worse.",
  "tags": ["nightly1110", "exit", "compass", "regime", "remedy"]},
]
EVID = ("11-10 (V-day: SPY +0.56% 10:08, -0.38% 12:45, +0.27% close): counter-index entries won - 100 trades avg +0.328R vs 1,194 "
        "others -0.103R (Primary 12 +0.672R vs 87 -0.452R); setup-adjusted excess +0.257R; same sign as 11-06, opposite of 11-09 - nightly1110.")
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}
for r in rows:
    if r["id"] == "swing1103-L6-counter-index-entries" and "nightly1110" not in (r.get("notes") or ""):
        r["notes"] = (r.get("notes") or "") + " | " + EVID
for e in NEW:
    if e["id"] in have: continue
    rows.append({"id": e["id"], "title": e["title"], "added": "2026-11-10", "source": SRC, "category": e["category"],
                 "hypothesis": e["hypothesis"], "module": None, "variant": None, "status": "idea", "configs_tried": e["configs"],
                 "tags": e["tags"], "test_needed": e["test_needed"], "notes": "Not run 2026-11-10. Educational only - not financial advice."})
B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print(len(rows), "rows")
