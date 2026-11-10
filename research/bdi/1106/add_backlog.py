"""bdi1106: append tonight's backlog entries (idempotent by id). Usage: python research/bdi/1106/add_backlog.py
Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI daily 2026-11-06 (research/bdi/1106/NOTES.md)"
NEW = [
 {"id": "sqz1-1106-chase-burst-scalp", "title": "SQZ1: chase bursts (>= 3rd same-side entry of a setup in 15 min after QQQ already moved >= 0.4% that way in 30 min) take a +0.5R target",
  "category": "exit", "status": "parked", "configs_tried": 1, "module": "research/bdi/1106/sqz1.py", "parent": "burst2",
  "hypothesis": "11-05 / 11-06 swing autopsy: the burst entries go in the money first (11-06 MF2 wave MFE median 0.57R, 2 min) and then stop together in the snap-back; blocking them fails on two years (BURST1/2), so scalp them instead.",
  "tags": ["bdi1106", "bdi", "burst", "exit", "both-sides", "swing"],
  "notes": "2 years (95 lab setups, 1.10M trades, 5-min MFE, stop-first on the exit bar, costs in, locked block absent), 1 config (BURST lineage 30, bar 2.61): class A 7.6% of trades; TRAIN -268R (t -1.15), VALID -277R (t -1.38), VALID excess -84R (t -0.45); 4 families harmed (GEN -239R, exhaustion -62R, MF -38R); VALID setups 20 better / 29 worse. Fails. The +0.5R target is worse for these trades on two years than their own exits; 11-05 / 11-06 were the exception (in-sample +56.8 / +13.1R). Forward shadow swing1106-L10. Educational only - not financial advice."},
 {"id": "mh-1106-defensive-rotation-0950", "title": "Move Hunt precursor: on up opens (SPY >= +0.40% at 09:50) buy low-beta laggards (60d beta <= 0.5, fromOpen <= +0.10%)",
  "category": "setup", "status": "parked", "configs_tried": 1, "module": "research/bdi/1106/mh_p1.py",
  "hypothesis": "Move Hunt 11-06: 13 of the 25 biggest tradable long moves were defensives (TSN, HSY, KO, SBUX, MDLZ, HDV, WMT, PM, XLP...) that had not joined the up open, 1.0-1.6 ATR by 10:30-11:10; GEN-261021-02 caught some (+35.9R) and skipped 6 on max positions.",
  "tags": ["bdi1106", "move-hunt", "open", "long", "setup", "qday", "rotation"],
  "notes": "2 years (lab frames, t1s1 re-costed to production): only 20 qualifying days; n 2,799 avg -0.023R (TRAIN -0.040 / VALID +0.004), 40% months positive -> fails; relative edge vs same-day 09:50 longs +0.170R (day-t 1.51; VALID +0.357R) and +0.158R on down-close (reversal) days vs -0.114R on up-close days. 11-06 in-sample: 118 entries +0.241R vs base -0.063R. Salvage: hedge leg on up opens / forward shadow mh1106-p1. Educational only - not financial advice."},
 {"id": "bdi-1106-gen261021-02-capacity", "title": "GEN-261021-02 (Gen) skipped 6 of the day's top-25 long movers on 'max positions for this setup' at 09:50 - review its position cap vs the 09:50 burst (housekeeping / playing time, not a setup change)",
  "category": "risk", "status": "parked", "configs_tried": 0, "module": None,
  "hypothesis": "Move Hunt 11-06: SBUX, VONV, WMT, XLP, KO, TSN skipped (max positions) while the setup's 85 taken trades made +35.9R; its record is 1 quiet day of 85 trades (one-big-day check needed).",
  "tags": ["bdi1106", "move-hunt", "capacity", "gen"],
  "notes": "Descriptive; GEN-261021-02 live record must be checked with avg R w/o best day before any change. Educational only - not financial advice."},
]
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}; n = 0
for e in NEW:
    if e["id"] not in have:
        e.update({"added": "2026-11-06", "source": SRC, "variant": None}); e.setdefault("parent", None); rows.append(e); n += 1
B.write_text("".join(json.dumps(r) + "\n" for r in rows)); print(n, "added;", len(rows), "entries")
