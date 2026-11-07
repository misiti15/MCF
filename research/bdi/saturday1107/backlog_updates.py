"""saturday1107: backlog entries / updates from tonight's round (idempotent by id).
Usage: python research/bdi/saturday1107/backlog_updates.py     Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI Saturday deep run 2026-11-07 (research/bdi/saturday1107/NOTES.md)"
D = "2026-11-07"; ED = " Educational only - not financial advice."
NEW = [
 {"id": "sat1107-burst-flush-latch-rework", "category": "risk", "status": "parked", "configs_tried": 7, "parent": "burst2",
  "module": "research/bdi/saturday1107/sim_a.py", "title": "BURST rework: flush-gate neighbours (QQQ 30-min -0.3/-0.5%, 4th+ short), QDAY flush gate (only while SPY >= -0.25% from open), realised -2R + open -3R latch, and the pair",
  "hypothesis": "Rule-18 rework of burst2-flush-gate-short and burst1-openloss-latch3 (the week's near-misses), with the gate aimed at index flushes inside a range / up tape (11-06) rather than real down tapes (11-05).",
  "tags": ["sat1107", "bdi", "burst", "giveback", "qday", "risk"],
  "notes": "7 configs (BURST lineage 36, bar 2.68), 0 pass. Best VALID Delta t: A6 latch-or -3 6.08 / A7 6.05 but VALID excess t -0.43 / -0.74 (trades less of a losing book); A7 live +224.9R (t 2.34; 48 setups better +288R / 14 worse -63R, Primary +23.8R), VALID primary-setup give-back mean 18.1 -> 16.0R/day, p90 43.2 -> 35.3R; GEN family harmed. Flush neighbours: A1 0.3% VALID t 2.15 excess -0.58; QDAY A4 VALID t 0.89, excess -1.13, live +89.6R (11-06 +11.6, 11-05 0 by design). Forward shadow only." + ED},
 {"id": "sat1107-range-extreme", "category": "setup", "status": "parked", "configs_tried": 4, "parent": None,
  "module": "research/bdi/saturday1107/c_e.py", "title": "QDAY range-tape extremes: buy lab long entries within 0.15/0.25 ATR of the session low, or sell shorts within 0.15/0.25 ATR of the high, while |SPY from-open| <= 0.25%",
  "hypothesis": "QDAY focus: on quiet / range days the session extremes revert, so extreme entries in a flat tape should work on up and down days alike.",
  "tags": ["sat1107", "bdi", "qday", "move-hunt", "long", "both-sides", "setup"],
  "notes": "2 years (95 lab setups, first entry per symbol-day, costs in, locked block absent), 4 configs, 0 pass (Testing bar 1.50): E1a long -0.097R t -9.3 (up-regime +0.051 / down -0.215), E2a short -0.091R (up -0.291 / down +0.099); excess vs same-tape baseline -0.001..-0.015R. A flat tape at entry does not make the extremes revert: the rest of the day's direction still decides." + ED},
 {"id": "sat1107-gapup-midday-lod-long", "category": "setup", "status": "idea", "configs_tried": 0, "parent": None, "module": None,
  "title": "Long: gap-up > 2% name making a new low of day 11:00-13:30 (buy the midday flush of a gap-up) - discovery 11-07 replicated long",
  "hypothesis": "Discovery 2026-11-07: 'gap up > 2% + 11:00-13:30 + new low of day' long replicated (train n 1,054 +0.015R, test n 559 43.6% success, +0.064R); a long-side Move Hunt candidate that does not need an up tape.",
  "tags": ["sat1107", "discovery", "long", "move-hunt", "qday"],
  "test_needed": "2-year lab frames: gap >= 2%, new LOD 11:00-13:30, wide geometry (0.5 ATR stop / 15:55 or 1R), regime + SPY day-type split, same-time random-long control, Testing bar.", "notes": "Idea only (0 configs)." + ED},
 {"id": "sat1107-index-first-open-two-sided", "category": "setup", "status": "idea", "configs_tried": 0, "parent": "sat1031-open-capitulation-reversal-long", "module": None,
  "title": "Index-first open, two-sided (carried from sat1031): pick the side from SPY / QQQ / breadth at 09:35-09:45, then the biggest volume-confirmed mover on that side, wide geometry",
  "hypothesis": "sat1031 + sat1107: stock-level state at the open / at range extremes says a move is likely, not which way; the day's direction decides, so the side must come from the index.",
  "tags": ["sat1107", "move-hunt", "open", "long", "both-sides"], "notes": "Still unbuilt (needs the open frame + context table)." + ED},
]
UPD = {
 "burst2-mf-after-flush-rework": dict(status="parked", configs_tried=6, module="research/bdi/saturday1107/b_mf.py",
   add="2026-11-07: 6 configs (QQQ 30-min > -0.3/-0.4/-0.5% for MF2-FD and MF4-FD), 0 pass (BAR90 1.70). Parents are negative on 2 years (MF2-FD -0.088R t -2.08, MF4-FD -0.085R t -4.84); filtered versions -0.080..-0.096R, regime-up -0.20..-0.24R, WF 6-24%. Live paper the filter would have added +10..+22R (MF2) / +11..+13R (MF4) - the live record, not the two years. No salvage at setup level."),
 "fb1-1105-sell-bounce-not-flush": dict(configs_tried=8,
   add="2026-11-07 rework (SAT1107 C, lineage 8, bar 2.04): flush-chase guard only while SPY >= -0.25% from open (0.10/0.15/0.25 ATR, + QQQ at its low) - 0 of 4 pass; guarded shorts excess +0.005..+0.014R (removing them hurts); valid Delta -488..+32R (t -1.12..+0.13); helps on SPY-up days, hurts on down/quiet days; 13-16 families harmed vs 5-11 helped."),
 "gate1-checkpoint-gate": dict(add="2026-11-07: not reworked (pre-declared; lineage 112, bar 3.07 vs best VALID t 2.26; forward shadow keeps logging)."),
}
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"]: r for r in rows}; n = u = 0
for e in NEW:
    if e["id"] not in have:
        e.update({"added": D, "source": SRC, "variant": None}); rows.append(e); n += 1
for k, v in UPD.items():
    r = have.get(k)
    if r is None or D in (r.get("notes") or "") + (r.get("result") or ""): continue
    add = v.pop("add"); r.update(v); key = "notes" if "notes" in r else "result"
    r[key] = (r.get(key) or "").replace(" Educational only - not financial advice.", "").rstrip() + " | " + add + ED; u += 1
B.write_text("".join(json.dumps(r) + "\n" for r in rows)); print(n, "added,", u, "updated;", len(rows), "entries")
