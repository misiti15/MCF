"""Append tonight's hypotheses to research/backlog.jsonl (status idea / failed per the backtest). Idempotent by id.
Usage: python add_backlog.py [results.json]   (results.json: {"h1_status", "h1_configs", "h1_notes", "h2_...": ...})
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

ROOT = Path("/home/user/MCF")
B = ROOT / "research" / "backlog.jsonl"
SRC = "nightly-2026-10-16 (research/bdi/nightly1016/NOTES.md)"
D = "2026-10-16"
E = " Educational only - not financial advice."
res = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else {}

new = [
    {"id": "nightly-1016-trend-day-long-reversal-veto",
     "title": "Reversal longs (T2 CWT14 failbrk orl/pdl longs, T1 heat_fade_long(-FD), ST1-ordn-long): no new long while SPY is below its open AND below VWAP AND made a new session low in the last 30 min",
     "category": "filter", "parent": None, "tags": ["testing1", "testing2", "longs", "index", "trend-day", "failed-breakdown", "nightly"],
     "hypothesis": "On a one-way down day (SPY never back to its open after 09:30) failed-breakdown and fade longs keep firing into fresh lows and fail together. 2026-10-16: SPY gap +0.19%, open-path low -0.36% at 10:11, never reclaimed the open, close -1.29% from the open (QQQ -2.16%, IWM -1.84%, lows 15:07). T2 longs 274 trades, 47% wins, -0.365R, -$1,114.75 (CWT14 orl/pdl longs -$846, CWT12-coil-k4 -$238.50), daily-loss halt at 11:20 (384 later signals skipped); T1 longs 154, 29% wins, -0.491R, -$813.51 (heat_fade_long + -FD -$427.40, ST1-ordn-long-FD -$210.08) while T1 shorts made +$794.11.",
     "status": "idea", "configs_tried": 0,
     "notes": "One session. Related and failed: ix-gate (SPY/QQQ vs VWAP entry conditions on the 48 live lists), bdi-tg-heat-fade-long (trend guards G1-G5). This variant differs by requiring all three conditions (below open, below VWAP, fresh low in 30 min) as a trend-day marker; score on history2y with costs, up/down regime split, and report how many 2024-26 sessions trigger it." + E},
    {"id": "nightly-1016-primary-one-lot-per-symbol",
     "title": "Primary: at most one open lot per symbol across all setups (skip a new lot while any MCF lot on that symbol is open)",
     "category": "risk", "parent": "nightly-1013-stack-clone-skip", "tags": ["primary", "stacking", "lot-cap", "nightly"],
     "hypothesis": "With MF3-FD promoted next to MF3, MF4 and MF5 (same flow-sell family), several setups fire on the same names, so Primary stacks correlated lots. 2026-10-16 Primary: unstacked first lots 16 trades, 69% wins, +0.270R, +$64.73; lots on stacked symbols: lot 1 7 trades -0.534R, lot 2 7 trades -0.506R, lot 3 6 trades -0.164R (together -$57.56). MF3 and MF3-FD both took ENB and RPRX; the lot cap then skipped 6 MF4/MF5 signals on symbols MF3-FD already held.",
     "status": "idea", "configs_tried": 0,
     "notes": "One session, 20 stacked trades. Related ideas: nightly-1013-stack-clone-skip, nightly-1013-no-short-stacking. Needs the joint Primary portfolio replay on history2y (costs in) with the stacked lots removed, with per-setup counts of signals lost." + E},
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
