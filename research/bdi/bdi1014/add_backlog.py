"""Append BDI 2026-10-14 entries to research/backlog.jsonl (idempotent by id). Educational only - not financial advice."""
import json
from pathlib import Path

ROOT = Path("/home/user/MCF")
B = ROOT / "research" / "backlog.jsonl"
SRC = "BDI 2026-10-14 (research/bdi/bdi1014/NOTES.md)"
E = " Educational only - not financial advice."
new = [
    {"id": "bdi1014-cwt14-sar", "title": "CWT14 stop-and-reverse: when a fail-break trade's bracket stop fills, enter the breakout side (stop-entry at the stop, or market at the stop bar's close), 5 exit geometries",
     "category": "setup", "parent": "cwt-b-b3-failed-breakout-reversal", "tags": ["testing2", "cwt14", "sar", "managed-trade", "bdi"],
     "hypothesis": "A level that is reclaimed and then lost again is a real breakout; reversing at the stop turns CWT14's never-worked losers into continuation trades (2026-10-14 T2: 180 stops, reversal 1R/1R +0.318R per stop, +57R, on a down day).",
     "status": "failed", "configs_tried": 240,
     "notes": "sar1014.py, pre-declared in PLAN.md Part B. Open two-year history (locked block never loaded), production + tod costs, x3 extended tier. 512,798 CWT14 first signals, 31.7% stopped; base re-simulation matches the scan (corr 0.998, -0.092 vs -0.090R). 0 of 120 SAR legs have exp > 0 (12 books x E1/E2 x t05s1/t1s1/t2s1/t1s05/eod-s1); best E2 t05s1 pdl-p10-lowvol -0.054R (n 6,515, t -4.30); pooled E2 t05s1 -0.074R (n 79,748), E1 t05s1 -0.165R. E2 legs equal the same-time random control (excess -0.000..+0.024R, |t| < 2.1): the post-stop move has no edge, it is the session's direction (long legs: up sessions +0.09..+0.19 for eod, down -0.39..-0.56). E1 (stop-entry) is 0.07-0.18R worse than control (stop slippage + the adverse bar). Managed trade base+SAR is worse than base in every book. Testing bar 0/120, research bar (t >= 4.84, lineage N 120,849) 0/120. 2026-10-14's +57R was the down day." + E},
    {"id": "bdi1014-cwt14-sar-ixalign", "title": "CWT14 stop-and-reverse, rework: reverse only when SPY's fromOpen at the stop bar is on the reversal's side (k = 0 / 0.25%)",
     "category": "setup", "parent": "bdi1014-cwt14-sar", "tags": ["testing2", "cwt14", "sar", "index-confirm", "rework", "bdi"],
     "hypothesis": "Part B's reversal legs follow the session's direction; SPY's move from the open at the stop bar is known then and may pick the sessions where the reversal pays.",
     "status": "failed", "configs_tried": 240,
     "notes": "sar_ix1014.py, pre-declared in PLAN.md Part B2 after Part B. E2 entry, 5 geometries x 12 books x k {0, 0.25%} = 120 legs + 120 managed reads; lineage N 121,089 (bar 4.84). 0 of 120 exp > 0; best pdh-p10-lowvol-short t2s1 k0 -0.040R (n 3,687, t -1.25); pooled k0 t05s1 -0.070R (n 48,339). The index gate does not fix the regime split (short legs still lose in up sessions, -0.23..-0.89R, long legs in down sessions). Lineage closed for SAR on CWT14; next step would be a different parent." + E},
    {"id": "bdi1014-rw2-extension-floor", "title": "RW2-exhaustion-noon-adv150-short: require a deeper extension at entry (fromOpen >= 2.5% or RSI5 >= 90)",
     "category": "filter", "parent": None, "tags": ["testing1", "rw2", "pattern", "never_worked", "bdi"],
     "hypothesis": "RW2's never_worked losses recur (patterns.csv: 4 sessions, 9 rows). On 2026-10-14 its winners entered at a median fromOpen +3.2% / RSI5 94 vs losers +1.4% / RSI5 80 (9 trades).",
     "status": "idea", "configs_tried": 0,
     "notes": "One session, 9 trades - a hypothesis only. Score on the two-year frames per rule 18 (neighbourhood 2.0/2.5/3.0% and RSI5 85/90/95), costs in, regime split." + E},
    {"id": "bdi1014-st2-wrong-side", "title": "ST2-slope20up-long-am: skip when the stock is already >= 3% below its open at the entry bar",
     "category": "filter", "parent": None, "tags": ["testing1", "st2", "pattern", "wrong_side_after_big_swing", "bdi"],
     "hypothesis": "ST2 longs recur as wrong_side_after_big_swing and late_hold (patterns.csv: 3 sessions each); a rising SMA20 slope on a stock already down 3-4% from the open is a stale trend signal.",
     "status": "idea", "configs_tried": 0,
     "notes": "2026-10-14: 17 trades, -$100.87; winners and losers both entered ~-4% from the open (median -3.8 vs -4.4%), so today's data does not separate them; queued because the pattern recurs on 3 sessions. Score on history with the neighbourhood 2/3/4%." + E},
]
es = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {e["id"] for e in es}
for n in new:
    n = {"added": "2026-10-14", "source": SRC, "module": None, "variant": None, **n}
    if n["id"] in have:
        es = [n if e["id"] == n["id"] else e for e in es]
    else:
        es.append(n)
B.write_text("".join(json.dumps(e) + "\n" for e in es))
print(len(es), "entries")
