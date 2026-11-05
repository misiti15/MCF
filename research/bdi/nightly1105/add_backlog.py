"""nightly1105: append tonight's backlog hypotheses (idempotent by id; status idea, untested tonight: CPU budget kept for
BURST1 / REGX and the queue's GATE2 + FLOW1-2Y) and add 11-05 evidence to nightly-1016-trend-day-long-reversal-veto.
Usage: python research/bdi/nightly1105/add_backlog.py   Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[3] / "research/backlog.jsonl"
SRC = "nightly learning loop 2026-11-05 (research/bdi/nightly1105/NOTES.md)"
NEW = [
 {"id": "nightly-1105-uni1-pool-by-daytype", "category": "setup",
  "title": "UNI1 (Testing 2 top-500 pool): is the smaller pool worse for the long dip-buy setups on index-down days?",
  "hypothesis": "Testing 2 since UNI1 (11-04, 11-05): 410 trades, setup-matched avg R -0.291 vs -0.034 for the same setups 10-20..11-03 (diff -0.256R; 14 of 23 setups worse); over the same two days Testing 1 +0.061, Graveyard +0.003, Primary -0.274. 11-05 (SPY -4.2%): Testing 2 -85.4R on 271 trades, 70% longs (CWT13-z05-long 100 trades -23.9R, CWT14 pdl longs -35.6R), RW3S shorts -30.8R. Two days cannot separate the pool from the day type: the top-500 pool is mostly liquid, high-beta names that track QQQ, so a dip-buy long there may be more of an index bet.",
  "test_needed": "2-year lab lists of the Testing 2 setups: tag each trade in / out of the UNI1 top-500 pool (ADV x ATR%, ADV >= $95M, ranked on priors as the runner does) and split by SPY day type (up / down / quiet at 10:00); pass = in-pool avg R not worse than out-of-pool in TRAIN and VALID on down days; report per setup. Live: keep the UNI1-T2 daily T2 vs T1 line.",
  "tags": ["nightly1105", "setup", "universe", "uni1", "testing2", "daytype"]},
 {"id": "nightly-1105-restart-catchup-entries", "category": "risk",
  "title": "Replacement / standby run: cap the age of catch-up signals (bars inside the no-session gap) and size them like late entries",
  "hypothesis": "11-05: no runner 14:35-14:50 ET (355-min limit + scheduler outage). The 14:49 run's first poll entered signals from the gap's bars (bar index 309-319 = 14:39-14:49) at 14:50 prices: Primary 1, T1 5, T2 3, GY 15 (+11 at 14:55), Gen 32 (+20 buying-power rejects; 2 from bars < 300), Explore 1 4, Live Lab 1. Today they made money (Gen +30.65R, GY +14.4R after costs), but a catch-up entry is a late entry at a different price than the signal bar, and Gen's account halt (14:10) was not carried over (see HK-HALT-RESTART).",
  "test_needed": "Replay (mcf/replay) of past sessions with an injected 10-15 min gap: catch-up entries vs the same signals entered on time and vs skipped; per setup and by signal age (0-5 / 5-10 / 10+ min); pass = an age cap that improves R in replays without dropping on-time entries. Housekeeping side (halt latch) ships separately.",
  "tags": ["nightly1105", "risk", "ops", "restart", "catchup"]},
]
EVID = ("11-05 (SPY -4.2%, QQQ LOD 10:53, IWM LOD 13:03): counter-index entries (long with SPY <= -0.25% from open) "
        "639 trades -0.428R vs others -0.011R, but setup-adjusted excess -0.001R, so the loss is which setups fired, not "
        "when; Testing long dip-buys: T2 CWT13-z05-long 100 -23.9R, CWT14 pdl longs 79 -35.6R; GY CWT14 orl longs 84 "
        "-70.5R and the -2R latch blocked +350R of long what-if losses there. Evidence for this idea, still untested "
        "(nightly1105).")
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
# fixed-$-risk idea: BURST1 filed it the same night as burst1-equal-dollar-risk; the nightly figure is added there
for r in rows:
    if r["id"] == "burst1-equal-dollar-risk" and "nightly1105" not in (r.get("notes") or ""):
        r["notes"] = (r.get("notes") or "") + " | nightly1105: same finding from the nightly (since 10-28 the same R at a fixed ~$33 risk would read -$304 vs -$1,375 actual, 1 descriptive config); folded in here instead of a duplicate entry."
have = {r["id"] for r in rows}
add = 0
for r in rows:
    if r["id"] == "nightly-1016-trend-day-long-reversal-veto" and "nightly1105" not in (r.get("notes") or ""):
        r["notes"] = (r.get("notes") or "") + " | " + EVID
for e in NEW:
    if e["id"] in have: continue
    rows.append({"id": e["id"], "title": e["title"], "added": "2026-11-05", "source": SRC, "category": e["category"],
                 "hypothesis": e["hypothesis"], "module": None, "variant": None, "status": "idea", "configs_tried": 0,
                 "tags": e["tags"], "test_needed": e["test_needed"],
                 "notes": "Not run 2026-11-05: CPU kept for the BURST1 / REGX swarms and the queue (GATE2, FLOW1-2Y). Educational only - not financial advice."})
    add += 1
B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print("added", add)
