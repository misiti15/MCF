"""Append tonight's hypotheses to research/backlog.jsonl (status idea / failed per the backtest). Idempotent by id.
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

ROOT = Path("/home/user/MCF")
B = ROOT / "research" / "backlog.jsonl"
SRC = "nightly-2026-10-14 (research/bdi/nightly1014/NOTES.md)"
D = "2026-10-14"
E = " Educational only - not financial advice."
res = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else {}

new = [
    {"id": "nightly-1014-cwt14-skip-first-bar", "title": "CWT14 fail-break setups (Testing 2): no entry on the 09:50 first decision bar; the first qualifying bar from 09:55 fires instead",
     "category": "setup", "parent": "cwt-b-b3-failed-breakout-reversal", "tags": ["testing2", "cwt14", "open", "first-bar", "nightly"],
     "hypothesis": "The 09:50 bar catches PDL/ORL reclaims while the opening move is still unresolved; on 2026-10-14 the 09:50 poll's 64 entries (60 longs) won 8% and lost -$420.84 (-0.95R) as the index peaked at 09:49.",
     "status": res.get("h1_status", "idea"), "configs_tried": res.get("h1_configs", 0), "notes": res.get("h1_notes", "One session; 2026-10-14 T2 09:50 poll 64 trades, 8% wins, -$420.84.") + E},
    {"id": "nightly-1014-liq-orl-index-confirm", "title": "LIQ-orl-sweep-open15-s25-long (Testing 1): fire only while SPY is up from its open (a) or above its session VWAP (b) at the decision bar",
     "category": "filter", "parent": "bdi-reddit1012-liquidity-sweep", "tags": ["testing1", "liq", "index-confirm", "long-beta", "nightly"],
     "hypothesis": "LIQ-orl is long beta (history: up sessions +0.59R, down -0.49R); requiring the index to be up at entry keeps its up-tape trades and drops the basket sweeps of a falling tape (2026-10-14: 30 of 47 entries in the 10:45 poll with SPY -0.3%, -$202; day -$250.67).",
     "status": res.get("h2_status", "idea"), "configs_tried": res.get("h2_configs", 0), "notes": res.get("h2_notes", "One session.") + " Related: nightly-1012-cwt14-long-index-confirm (failed) and the bdi-rg-* regime gates (failed) - a per-setup gate, not a book gate." + E},
    {"id": "nightly-1014-fd-short-late-giveback", "title": "Testing 1 short lots still open at 15:00: exit or tighten the stop to break-even / +0.5R at 15:00-15:30 instead of riding to the 15:55 flatten",
     "category": "exit", "parent": None, "tags": ["testing1", "shorts", "late-day", "giveback", "flatten", "nightly"],
     "hypothesis": "Short lots that ride into the close give back gains in the late bounce; on 2026-10-14 the 66 T1 short lots flattened at 15:55 were marked +$76.89 at 15:05 and closed -$109.57 (-$186.46), the account peak +$318 at 15:05 closed +$71.",
     "status": "idea", "configs_tried": 0,
     "notes": "Hindsight: 15:05 was the index low, only known afterwards. Related failed ideas: sw-w4-book-exits (book-wide time stops), t6-exit-overlay, nl-1007-late-holds, cutoff-1515 - a rework must beat those, scored per setup on the two-year frames with costs. One session." + E},
    {"id": "nightly-1014-t2-cap50-review", "title": "Testing 2: per-setup open-lot cap 50 vs 25 vs 35 - re-score with the -60R daily halt simulated",
     "category": "risk", "parent": "2026-10-14-testing2-setup-cap-50", "tags": ["testing2", "cap", "risk", "nightly"],
     "hypothesis": "Lots beyond 25 per setup are the most correlated (same setup, same poll, same tape); on 2026-10-14 the 81 trades taken above 25 open lots lost -$158.28 (-0.334R, 47% wins) and brought the -60R halt forward.",
     "status": "idea", "configs_tried": 0,
     "notes": "One session; cap 50 went live 2026-10-14 (ledger 2026-10-14-testing2-setup-cap-50). At cap 25 the halt would have come later and other trades would have been taken (not simulated). Score on the CWT history with the portfolio limits applied." + E},
]
es = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {e["id"] for e in es}
for n in new:
    n = {"added": D, "source": SRC, "module": None, "variant": None, **n}
    if n["id"] in have:
        es = [n if e["id"] == n["id"] else e for e in es]
    else:
        es.append(n)
B.write_text("".join(json.dumps(e) + "\n" for e in es))
print(len(es), "entries")
