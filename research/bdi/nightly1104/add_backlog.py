"""nightly1104: append tonight's backlog hypotheses (idempotent by id; status idea, untested: the 2-year lab lists
research/history2y/data are not in this container). Usage: python research/bdi/nightly1104/add_backlog.py
Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "nightly learning loop 2026-11-04 (research/bdi/nightly1104/NOTES.md)"
NEW = [
 {"id": "nightly-1104-no-reentry-after-stop-same-symbol", "category": "risk",
  "title": "No same-setup re-entry on a symbol that already stopped out today (or only after it reclaims the entry level)",
  "hypothesis": "11-04 Primary: Gap-Down Rebound Overbought Short (L3-gap-slope-rsi5hi-FD) shorted NRIX three times 13:00-14:10, three stops (-3.3R, -$249); a re-entry on a symbol that has already stopped the setup out is a bet against a stock that has just proved the setup wrong.",
  "test_needed": "2 years lab lists with exit times (1-min): per setup, 2nd+ entries on a symbol after a stop that day vs the setup's other entries; pass = skipped avg R < 0 in TRAIN and VALID, valid n >= 30, day-clustered t >= bar(N); report up / down / quiet days.",
  "tags": ["nightly1104", "risk", "reentry", "primary"]},
 {"id": "nightly-1104-spy-gate-spike-exhaustion", "category": "setup",
  "title": "Index-gated setups (SPY > +0.5% / QQQ > +0.6% from open) skip entries while the index is >= +1.0% from open and within 15 min of its session high",
  "hypothesis": "11-04 SPY ran to +1.65% by 10:00, then faded to +0.2% by 11:30; Gen's SPY-gated setups fired into the spike (GEN-261021-02 SPYgt0p5 long 71 trades -0.451R, GEN-261029-08 SPYgt0p5 short 49 trades -0.978R) and the account halted at 10:50 (-$2,455). A gate that says 'index is strong' is most often true right at a spike top.",
  "test_needed": "2 years: all lab / generated setups with an SPY- or QQQ-up gate; tag entries with index >= +1.0% and <= 15 min since the index HOD; pass = tagged avg R below untagged by >= 0.10R in TRAIN and VALID, t >= bar(N), n >= 30 valid.",
  "tags": ["nightly1104", "setup", "filter", "index", "gen", "spike"]},
 {"id": "nightly-1104-pdl-longs-smallcap-rotation", "category": "setup",
  "title": "Failed prior-day-low break longs (CWT14 pdl family) skip entries when IWM is below its open and >= 0.75% weaker than SPY",
  "hypothesis": "11-04 SPY +0.55% / IWM -0.05% at 10:00, IWM -1.01% at 11:27: the pdl-break longs lost in both homes - CWT14-failbrk-pdl-p10-long -12.8R and pdl-p10-lowvol -8.7R (Testing 2), pdl-p05 / pdl-p05-lowvol -16.4R (Graveyard), 'never worked' share high; a failed breakdown needs buyers that small caps did not have on a rotation-down day.",
  "test_needed": "2 years, CWT14 pdl lab lists + 1-min IWM / SPY context (IWM is not in the current context file: add it); pass = skipped avg R < 0 in TRAIN and VALID, valid n >= 30, t >= bar(N); also check it is not just 'IWM down' (direction bet).",
  "tags": ["nightly1104", "setup", "filter", "cwt14", "smallcap", "rotation"]},
 {"id": "nightly-1104-midday-index-turn-short-cluster", "category": "risk",
  "title": "Gap-down short family (MF2 / MF4 / RW3 / RW5): pause new entries for 30 min after 3 family stops inside 10 minutes",
  "hypothesis": "11-04 Primary peaked +$463 at 12:17 and closed -$209: 5 MF2-FD stops 12:21-12:27 (APLD, PL, SOXQ, GLXY, KLAC) as SPY rallied +0.22% -> +0.77% (11:30-13:00); 12:00-13:59 entries -0.67 / -1.09R. A burst of family stops marks an index turn against the book; BRAKE-1 (3rd stop of the day, half size) would have saved +5.58R today but cost -6.37R on 11-03 - a time-clustered trigger may separate the two.",
  "test_needed": "Needs exit times on the 2-year lists (BRAKE-1 note); live forward tally until then: count 3-in-10-min clusters per session and the family R entered in the 30 min after vs the rest.",
  "tags": ["nightly1104", "risk", "brake", "cluster", "primary"]},
]
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}
add = 0
for e in NEW:
    if e["id"] in have: continue
    rows.append({"id": e["id"], "title": e["title"], "added": "2026-11-04", "source": SRC, "category": e["category"],
                 "hypothesis": e["hypothesis"], "module": None, "variant": None, "status": "idea", "configs_tried": 0,
                 "tags": e["tags"], "test_needed": e["test_needed"],
                 "notes": "Not run 2026-11-04: the 2-year lab lists (research/history2y/data) are not in this container. Educational only - not financial advice."})
    add += 1
B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print("added", add)
