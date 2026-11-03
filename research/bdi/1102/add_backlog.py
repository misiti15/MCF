"""bdi1102: append tonight's backlog entries (idempotent by id) and add notes to the Move Hunt items it builds on.
Usage: python research/bdi/1102/add_backlog.py     Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "BDI daily 2026-11-02 (research/bdi/1102/NOTES.md)"
NEW = [
 {"id": "mh-1102-open-group-move", "title": "MH4 opening group move: trade a name in the direction of its residual-correlation peer group's move from the open (09:40-09:50), laggard (catch-up) or leader (continuation)",
  "category": "setup", "status": "failed", "configs_tried": 16, "module": "research/bdi/1102/mh4_group.py",
  "hypothesis": "Three Move Hunt days show the big tradable moves arriving in groups at the open (10-29 cyber / defence, 10-30 cyber / retail, 11-02 packaged food short, alternative asset managers long). Peers = top-10 residual-return (ex-SPY beta) correlation names from the trailing 120 non-locked sessions, refreshed monthly; group move P = median peer move from the open in ATR units minus the cross-sectional median.",
  "tags": ["bdi1102", "bdi", "setup", "move-hunt", "open", "group", "sympathy"],
  "notes": "Tested 2026-11-02 on the timeofday open frame (2 years, locked block absent and dropped from the peer table, adv20 >= 95M, blackout removed, production costs with the tod entry multiplier): 16 configs (side x lag/lead x g 0.40/0.60 x exit t1s1 / stop-0.25ATR-to-10:30). Absolute: all fail (exp -0.118..+0.056R, best t 0.64; walk-forward 16-56% positive months; longs win only on up days, shorts only on down days). But the group carries real cross-sectional information: the excess over a DAY-MATCHED baseline (all eligible names, same date + bar + side + exit) is positive in 14 of 16 configs, +0.05..+0.17R, t up to 2.71 (lag-short g40 t1s1; lag-long g40 t1s1 2.43). Split: lag-long g40 excess is positive in both halves (train +0.135R / valid +0.062R, valid t 1.75); the short-side excess sits in valid only (lag-short g40 train -0.010R / valid +0.109R). Laggards catch up to their group; the day's direction and the opening cost eat it. N 16, full bar 2.35, BAR90 2.12; no locked look. Rework queued: mh-1102-group-laggard-hedged. Educational only - not financial advice."},
 {"id": "mh-1102-group-laggard-hedged", "parent": "mh-1102-open-group-move", "title": "Rework of MH4: group-laggard catch-up as a market-neutral book (each lot hedged with a beta-sized SPY leg, or long and short laggards netted per bar), entry 09:40-09:50",
  "category": "setup", "status": "idea", "configs_tried": 0, "module": None,
  "hypothesis": "MH4 found a positive day-matched excess for laggards of a moving peer group on both sides (+0.075..+0.157R, t 2.4-2.7) that the absolute P/L hides because the 09:40-09:50 entries carry the day's direction. Taking out the market leg should keep the excess.",
  "test": "Pre-declare: MH4 lag g 0.40 / 0.60, both sides, exit h1030 only (a hedge needs a common exit time), hedge = beta (trailing 120 sessions) x SPY return over the same holding, SPY cost included; 4 configs (+4 for a 10:00 entry). Gates: train and valid both > 0 after costs incl. the hedge, day-clustered t >= the lineage bar (N cumulative 16 + new), walk-forward >= 54%, both regimes > 0. Needs the hedged-return column only (SPY is in the open frame).",
  "tags": ["bdi1102", "bdi", "setup", "move-hunt", "open", "group", "hedged", "rework"],
  "notes": "Idea only, 0 configurations. Live setups are single-leg today; a hedged book would be a new execution feature (owner call) - test first. Educational only - not financial advice."},
 {"id": "bdi-1102-underlying-exposure-cap", "title": "Count leveraged / inverse ETF lots by their underlying: a short SOXS, a long SOXL and a long AMDL are the same long-semis bet; cap open lots per underlying direction per account",
  "category": "risk", "status": "idea", "configs_tried": 0, "module": None,
  "hypothesis": "11-02: Primary's 6 SOXS shorts (-6.1R, -$641) plus T1 NS5-FD SOXL long (-$42), T2 NM-HL SOXL / AMDL longs (-$69) and T2 R2A AMDL long (-$70) were one direction on semis; the per-symbol lot cap and the -2R per-setup stop see them as unrelated. The family-wide inverse-ETF skip failed (nightly-1102-skip-inverse-etf-shorts) because inverse shorts are not worse as signals - this is about stacking, not signal quality.",
  "test": "Map every leveraged / inverse ETF in the universe to its underlying + sign (issuer lists; single-stock 2x included). On the two-year lab book (P / T1 / T2 setup lists, research/bdi/saturday1024 book_sim harness), cap open lots per (underlying, direction) at 2 / 3 and compare worst-10-day R, total R and R per trade vs dropping the same number of lots at random (as sat1024-one-lot-per-symbol-2y). Pass only if worst days improve without losing avg R.",
  "tags": ["bdi1102", "bdi", "risk", "etf", "stacking", "primary"],
  "notes": "Idea only, 0 configurations. Related but different: sat1024-one-lot-per-symbol-2y (failed, per symbol), nightly-1102-l3-inverse-etf-skip (signal filter, L3 only). Educational only - not financial advice."},
]
NOTES = {
 "mh-1029-earnings-sympathy": " bdi1102: the industry-peer rework at the open was tested as mh-1102-open-group-move (16 configs): fails in absolute terms, but laggards of a moving residual-correlation group show a positive day-matched excess (t up to 2.7); hedged rework queued (mh-1102-group-laggard-hedged). 11-02 groups: packaged food short (CPB, GIS, HRL, CAG; KMB in blackout) 09:45-09:55, alternative asset managers long (BN, KKR; BAM / APO / ARES reporting) 09:35-09:40.",
 "mh-1029-open-drive-window": " bdi1102: day 3 - 36 of the 50 biggest tradable moves had their best decision point at 09:35-09:45 (10-29 30, 10-30 33); live caught 7 of the 36 (Gen opening shorts, GY CWT12-coil and T2 CWT12-flag longs).",
}
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {r["id"] for r in rows}
for r in rows:
    if r["id"] in NOTES and "bdi1102" not in (r.get("notes") or ""):
        r["notes"] = (r.get("notes") or "") + NOTES[r["id"]]
for e in NEW:
    if e["id"] not in have:
        e.update({"added": "2026-11-02", "source": SRC, "variant": None})
        e.setdefault("parent", None)
        rows.append(e)
B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print(len(rows), "entries")
