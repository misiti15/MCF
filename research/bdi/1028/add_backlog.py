"""bdi1028: append tonight's backlog entries (idempotent by id) and add a note to bdi1027-graveyard-cap-replay.
Usage: python add_backlog.py     Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI daily 2026-10-28 (research/bdi/1028/NOTES.md)"
NEW = [
 {"id": "bdi1028-t2-pdl-trio-twin-group", "title": "Testing 2: put the three failed-PDL-break longs (CWT14-failbrk-pdl-p10-long, pdl-p05-lowvol-long, pdl-p10-lowvol-long) in one twin group, so one symbol is bought once per day",
  "category": "risk", "hypothesis": "10-28, the first day all three ran in Testing 2: 82 trades on 63 symbols, 14 symbols bought by 2+ versions and 5 by all three; every pdl-p10-lowvol trade (7, -0.58R) was on a symbol a sibling also took. No twin group spans them, so the account carries the same entry up to three times. Expected effect: same avg R per trade, less concentration; the question is which version keeps the symbol.",
  "status": "idea", "configs_tried": 0, "tags": ["bdi1028", "bdi", "risk", "testing2", "twin-group", "CWT14"],
  "notes": "Test needed: (1) live T2 lots since 10-28: avg R of first vs duplicate entries per symbol; (2) 2-year history with the three CWT14 kernels (top5_1019 scan): overlap rate and avg R when only the first version to fire keeps the symbol vs all three, costs in, up / down sessions, w/o best day. Rule 20: each setup's twin-held count must be shown with its record. Not a setup change."},
 {"id": "bdi1028-gen-new-setup-first-poll-cap", "title": "Setup Generator: cap a newly generated setup at 5 entries per poll during its first 5 sessions",
  "category": "risk", "hypothesis": "10-28: GEN-261028-09 (new that day) took 19 of its 24 entries in one poll (24 trades -6.8R, -$107); the 10-27 new GEN setups also entered in bursts. A day-1 burst puts a new, unproven rule's whole first sample on one minute, so its first record is one draw. Bursts were not worse per trade for shorts, the coil or pdl longs on two years (nightly-1015, bdi1026, bdi1027), so this is about sample quality and $ risk, not edge.",
  "status": "idea", "configs_tried": 0, "tags": ["bdi1028", "bdi", "risk", "generator", "burst"],
  "notes": "Test needed: every GEN setup's first 5 live sessions since 10-19: entries per poll, avg R of burst (>5) vs single entries, and how often the day-1 record flips sign by session 5. Only a sizing/sample-quality change; owner is considering pausing the generator, so this waits on that decision."},
 {"id": "bdi1028-primary-stp-sizing-audit", "title": "Primary: audit the first 5 sessions of ST-P (-2R latched per-setup stop) together with the ~$4,000 / position sizing",
  "category": "risk", "hypothesis": "From 10-28 Primary sizes ~$4,000 per position (77 slots, 30 per setup) and from 10-29 ST-P latches a setup at -2R. The pre-rule replay (nightly1028 stp.py) gives +21.1R over 17 sessions for 2R; with larger positions a 30-lot burst can cross -2R inside one poll, so the latch may trip later in $ than the replay assumes.",
  "status": "idea", "configs_tried": 0, "tags": ["bdi1028", "bdi", "risk", "primary", "ST-P", "sizing"],
  "notes": "Test needed: for each live Primary session from 10-29, compare the journal's latch events and blocked signals with stp.py's replay of the same trades; report $ at the trip vs -2R, entries in the trip poll, and the replayed value of blocked signals. Monitoring only; no rule change."},
]
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}
for r in rows:
    if r["id"] == "bdi1027-graveyard-cap-replay" and "bdi1028" not in r.get("notes", ""):
        r["notes"] += (" bdi1028: the two replays disagree on 10-28 - a plain bracket replay of the 255 'setup daily loss limit'"
                       " skips (setup's median cost, no extra spread; 1028/skipped.py) gives +35.2R, the broker what-if run"
                       " (nightly1028 caps.py, run 2) -5.35R gross / -24.6R net. Reconcile fills and costs first; use run 2.")
for e in NEW:
    if e["id"] not in have:
        e.update({"added": "2026-10-28", "source": SRC, "module": None, "variant": None, "parent": None})
        rows.append(e)
extra = Path(__file__).with_name("backlog_lls.json")
if extra.exists():
    e = json.loads(extra.read_text())
    if e["id"] not in have:
        rows.append(e)
B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print(len(rows), "entries")
