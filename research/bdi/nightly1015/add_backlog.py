"""Append tonight's hypotheses to research/backlog.jsonl (status idea / failed per the backtest). Idempotent by id.
Usage: python add_backlog.py [results.json]   (results.json: {"h1_status", "h1_configs", "h1_notes", "h2_...": ...})
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

ROOT = Path("/home/user/MCF")
B = ROOT / "research" / "backlog.jsonl"
SRC = "nightly-2026-10-15 (research/bdi/nightly1015/NOTES.md)"
D = "2026-10-15"
E = " Educational only - not financial advice."
res = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else {}

new = [
    {"id": "nightly-1015-short-breadth-cluster-skip",
     "title": "Lab short setups (NS2, NS2-FD, RW6-FD, RW2-FD, CWT09-g5-lowerhalf): skip a decision bar where >= 5 symbols take their first signal of the same setup",
     "category": "filter", "parent": None, "tags": ["primary", "testing1", "testing2", "shorts", "cluster", "breadth", "nightly"],
     "hypothesis": "When one short setup fires on many symbols in the same poll the trigger is a market-wide rally, not a stock-specific exhaustion, and the lots fail together. 2026-10-15: Primary NS2 took 42 shorts (31 in same-setup clusters of >= 5 per poll), -$788.87; same-setup clusters of >= 10 lost -0.81R (P), -0.73R (T1), -0.30R (T2) vs singles -0.24 / -0.64 / -0.20R; T2 CWT09-g5 took 21 shorts in the 10:30 poll, 1 win, -$537.62.",
     "status": res.get("h1_status", "idea"), "configs_tried": res.get("h1_configs", 0),
     "notes": res.get("h1_notes", "One session.") + " Related: loop-1008-exhaustion-cluster-t1 (per-setup entry-rate cap, failed), window-open-cluster (idea), bdi-rg-g*-breadth (book regime gates, failed)." + E},
    {"id": "nightly-1015-gapdn-reclaim-short-veto",
     "title": "Lab short setups: no new short while SPY gapped down <= -0.30% and has reclaimed its open (SPY fromOpen > 0) at the decision bar",
     "category": "filter", "parent": None, "tags": ["primary", "testing1", "testing2", "shorts", "index", "gap-down", "reversal", "nightly"],
     "hypothesis": "A gap-down that is bought back above the open marks a reversal day; shorts entered after the reclaim fight the tape. 2026-10-15: SPY gap -0.44%, low 09:57 (-0.24% from open), above the open from 10:01, +0.72% at the close (QQQ gap -1.41%, then +1.32%); shorts lost -$883.52 (P, 47), -$1,767.66 (T1, 207), -$1,276.76 (T2, 175) while longs made +$21.69 / +$94.64 / +$179.05.",
     "status": res.get("h2_status", "idea"), "configs_tried": res.get("h2_configs", 0),
     "notes": res.get("h2_notes", "One session.") + " Related: bdi-tg-* trend guards on NS2/NS3/NS4/RW6 (failed), nightly-1014-liq-orl-index-confirm (failed). The index dip-bounce setups start in Testing 1 on 2026-10-16 (long side of the same event)." + E},
    {"id": "nightly-1015-l3-fromopen-refire-cap",
     "title": "L3-gap-slope-fromopen-FD (Testing 1, refire cd1): cap refires per symbol-day (e.g. 1) or require price back below the prior signal's entry",
     "category": "risk", "parent": "2026-10-14-refire-option-b", "tags": ["testing1", "refire", "l3", "nightly"],
     "hypothesis": "On a rising tape the from-open slope condition stays true bar after bar, so the cooldown-1 refire re-signals every 10 minutes into strength. 2026-10-15: 732 L3-fromopen refire signals (458 skipped by the halt, 330 not shortable), 5 submitted, all stopped (-$65.93), plus 4 same-setup re-entries -$55.35; the setup lost 12 of 12 (-$174.57).",
     "status": "idea", "configs_tried": 0,
     "notes": "One session, one setup; refire went live 2026-10-14 (partial). Score on research/bdi/refire1014 extras for L3-fromopen with a per-day refire cap; report the extras alone." + E},
]
es = [json.loads(line) for line in B.read_text().splitlines() if line.strip()]
have = {e["id"] for e in es}
for n in new:
    n = {"added": D, "source": SRC, "module": None, "variant": None, **n}
    if n["id"] in have:
        es = [n if e["id"] == n["id"] else e for e in es]
    else:
        es.append(n)
B.write_text("".join(json.dumps(e) + "\n" for e in es))
print(len(es), "entries")
