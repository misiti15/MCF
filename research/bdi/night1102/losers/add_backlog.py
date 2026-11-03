"""night1102 losers: append the backlog entry (idempotent by id). Usage: python research/bdi/night1102/losers/add_backlog.py
Educational only - not financial advice."""
import json
from pathlib import Path
B = Path(__file__).resolve().parents[4] / "research/backlog.jsonl"
E = {"id": "losers1102-wide-stop-15-same-dollar", "parent": "gb-1019-wide-stop-t05",
     "title": "Stop 1.5x wider at the same $ risk (2/3 of the shares), target price unchanged - all intraday lab setups",
     "added": "2026-11-03", "source": "bdi night1102 losers (research/bdi/night1102/losers/NOTES.md)", "category": "exit",
     "module": None, "variant": None, "status": "failed", "configs_tried": 26,
     "hypothesis": "Most live losers are full stops that never worked (median MFE 0.19R) on stops of ~80 bps; live entry friction alone is ~0.04R per trade (fill vs the next 1-minute open). A wider stop at the same $ risk cuts the share count, so friction and per-share costs shrink in R, and fewer trades are stopped by noise.",
     "tags": ["bdi", "night1102", "losers", "exit", "stop", "same-dollar-risk"],
     "test_needed": "Rework (rule 18): the gain sits in up sessions (shorts). Try 1.25x / 1.5x / 2.0x with the target kept at the same R (not the same price) and per side, on the two-year frames (train / valid, regime gate, walk-forward), lineage N 26 + new; then Testing-only forward if it passes BAR90.",
     "notes": "Paired on the live 1-minute paths (all 5 accounts 10-20..11-02, 7,357 trades, sim vs live R corr 0.96): +0.050R per trade, day-clustered t 4.22, better on 9 of 10 days (best day 21% of the gain); T1 +0.042, T2 +0.036, Graveyard +0.067, Gen +0.066, but Primary -0.018 (t -0.32; 10-22 alone -20.4R, the big target day). Two-year (the 10 lab setups Primary ran, 18,240 trades on 5-minute frames, locked block not loaded): +0.019R, t 2.81, 15/21 months, but up +0.057 / flat +0.002 / down -0.012 -> fails the up-AND-down gate. Status failed (rework queued in test_needed). Educational only - not financial advice."}
rows = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
if E["id"] not in {r["id"] for r in rows}:
    rows.append(E)
    B.write_text("".join(json.dumps(r) + "\n" for r in rows))
print(len(rows), "entries")
