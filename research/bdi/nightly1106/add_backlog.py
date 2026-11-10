"""nightly1106: append tonight's backlog hypotheses (idempotent by id; status idea, untested tonight beyond BURST2) and add
11-06 evidence to nightly-1029-burst20-one-bet. Usage: python research/bdi/nightly1106/add_backlog.py
Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "nightly learning loop 2026-11-06 (research/bdi/nightly1106/NOTES.md, research/bdi/burst2/NOTES.md)"
NEW = [
 {"id": "burst2-mf-after-flush-rework", "category": "setup",
  "title": "MF2 / MF4 rework: do not sell after the index flush (QQQ 30-min return > -0.4%, or an RSI(5) pop first) - setup-level, not a system gate",
  "hypothesis": "Both Primary MF losses are entries after the selling already happened: 11-05 MF4-FD 13 shorts 11:00-11:10 at the QQQ low (-10.7R); 11-06 MF2-FD 23 shorts 10:30-10:40 after QQQ fell +0.68% -> -0.21% (10:00-10:30), 20 stopped 10:44-10:52 (-21.6R). The system-wide flush gate (BURST2 D) fixes both days on live Primary (+36.7R, 0 setups worse) but fails two years (VALID t 1.99, excess -0.38, MF family -57R). As an entry condition of MF2 / MF4 themselves (their own 2-year record, plateau check) it may hold where the system gate does not; RW3-FD (needs a pop) sold the bounce on both days.",
  "test_needed": "2-year lab lists of MF2-FD / MF4-FD (+ MF1 / MF3 / MF5 as the family): add the condition QQQ r30 > -y (y 0.3/0.4/0.6%) or RSI(5) >= 70 within the last 15 min; TRAIN pick, VALID check, regime split (up / down), plateau, rule-18 look count from the MF lineage; live 10-06..11-06 replay as context only.",
  "tags": ["nightly1106", "burst2", "setup", "mf", "entry-timing"]},
 {"id": "nightly-1106-etp-component-stack", "category": "risk",
  "title": "One theme = one bet: cap a setup's shorts in a sector ETP plus its top holdings in the same 15 minutes",
  "hypothesis": "11-06 10:40 poll: MF2-FD shorted 14 names in one poll - 5 tech / semis ETPs (SOXX, SOXQ, QTEC, IYW, MTUM; -6.1R) and their holdings (MU, AVGO, MRVL, ENTG, SNDK, UMC, SKHY, ASX) - 0 winners, -16.1R. MF2 + MF4 10:30-10:45: 34 shorts, 28 semis / tech names -26.2R. 5 cross-setup twins (MF2 / MF4 on AVGO, MRVL, SNDK, SOXQ, UMC) all lost (-1.11R avg). Not tested tonight; the family / cluster gates (BURST1 d, BURST2 B) were over-broad - a theme-aware cap is narrower.",
  "test_needed": "Theme map (ETP -> top-20 holdings, plus GICS industry for singles) on the 2-year lists: per setup and account, block the k-th same-theme same-side entry within 15 min (k 3/5); report per setup / family improved vs worse (Remedies rule), excess vs setup mean, regime split; live 10-06..11-06.",
  "tags": ["nightly1106", "risk", "theme", "etp", "burst"]},
 {"id": "nightly-1106-halt-scope-latched-only", "category": "risk",
  "title": "Account -20R halt: stop only the latched setups (and new entries at half size) instead of the whole account",
  "hypothesis": "11-06: the -20R halt (10:55) came from two latched setups (MF2-FD -21.6R, MF4-FD -5.5R). It blocked 92 signals (47 first per setup-symbol) that would have made +8.1R before costs (job log +6.5R): RW3-FD +5.1R, RW5-FD +2.6R, NS5 +1.4R, L3-rsi5hi +1.1R, vs MF2 / MF4 -2.2R (already latched). A halt scoped to latched setups would have kept the non-latched ones.",
  "test_needed": "Live journals 10-06..11-06 (all halts: Primary 11-06, Gen 11-05) + 2-year lists with the Primary composition: account halt at -20R vs halt of latched setups only vs halt + half size; drawdown, worst day, R, $; owner decision on risk appetite.",
  "tags": ["nightly1106", "risk", "halt", "account-limit"]},
]
EVID = ("11-06: Graveyard CWT14 orl longs 91 trades -30.5R with clusters of 17-19 per setup per poll at 10:0x; Gen GEN-261021-07 "
        "46 longs -26.6R (max 33 in one poll), GEN-261029-01 29 -21.3R; but GEN-261021-02 85 longs +35.9R (51 in one poll) - "
        "bursts cut both ways again (nightly1106).")
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}
for r in rows:
    if r["id"] == "nightly-1029-burst20-one-bet" and "nightly1106" not in (r.get("notes") or ""):
        r["notes"] = (r.get("notes") or "") + " | " + EVID
for e in NEW:
    if e["id"] in have: continue
    rows.append({"id": e["id"], "title": e["title"], "added": "2026-11-06", "source": SRC, "category": e["category"],
                 "hypothesis": e["hypothesis"], "module": None, "variant": None, "status": "idea", "configs_tried": 0,
                 "tags": e["tags"], "test_needed": e["test_needed"],
                 "notes": "Not run 2026-11-06 (BURST2 took the night's CPU). Educational only - not financial advice."})
B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print(len(rows), "rows")
