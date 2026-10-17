"""Append / update BDI 2026-10-16 entries in research/backlog.jsonl (idempotent by id). Educational only - not financial advice."""
import json
from pathlib import Path

ROOT = Path("/home/user/MCF")
B = ROOT / "research" / "backlog.jsonl"
SRC = "BDI 2026-10-16 (research/bdi/bdi1016/NOTES.md)"
E = " Educational only - not financial advice."
H = ("regime_gate.py, PLAN.md Part B; open two-year history (426 sessions, locked block 2024-11..2025-02 never loaded), "
     "production + tod costs, live first-signal semantics, gate applied before 'first'. Study N 84, bar 2.98; "
     "market-context-gate lineage 2,450, bar 3.95.")
new = [
    {"id": "bdi1016-dayclass-direction-gate",
     "title": "Early-session day-class direction gate: classify the day at 10:00 / 10:30 (K1 SPY+QQQ+IWM fromOpen all beyond +-k; K2 SPY fromOpen + breadth; K3 5-of-6 votes incl. prior close and SPY 09:30-09:45 OR break) as trend-down / trend-up / chop; from T on block longs on trend-down and shorts on trend-up; chop ungated",
     "category": "filter", "parent": "ix-gate", "tags": ["primary", "testing1", "testing2", "index", "breadth", "day-class", "regime", "gate", "needs-mcf-hook", "bdi"],
     "hypothesis": "10-12..10-16 losses followed the day's direction (10-16 one-way down day: T2 longs -$1,115, T1 longs -$814, shorts won). A selective multi-feature day call fixed once at T (unlike the per-bar single-feature ix-gate / bdi-rg-g1..g5 / splitgate / index-confirm vetoes) might remove the against-trend trades.",
     "status": "failed", "configs_tried": 84,
     "notes": H + " 3 of 84 meet the pre-declared Testing bar (see bdi1016-dayclass-gate-rw7, bdi1016-dayclass-gate-cwt14pdh); 0 meet the Primary bar; the pooled 6-setup book fails all 12 gates (delta -0.004..+0.002R, rnd95 never beaten by more than noise). The classifier itself is informative: K1 k0.25 at 10:00 calls 50 down days (35 are rule-19 down sessions, 5 up) and 45 up days (30 up, 5 down); at 10:30 61/61. But the parents are negative on every class: CWT14-orl-p05-long trend-down -0.107 / chop -0.090 / trend-up -0.082R; CWT14-pdl-p05-long -0.126 / -0.087 / -0.030; CWT14-pdh-p05-lowvol-short -0.059 / -0.098 / -0.101 - blocking the against-trend days moves exp by <= 0.004R. LIQ-orl: blocked trades are not worse (blocked t -0.75..+1.16); RW2-FD blocked t -2.63..+0.24, no plateau. Week replay (week_replay.py, live paper, descriptive): 10:00 called every day 10-12..10-16 chop; at 10:30 K1 k0.25 called 10-16 DOWN (would have blocked 260 live longs, -$1,310.60), K2/K3 k0.25 called 10-14 DOWN (blocks -$586); 10-15 (the reversal day, shorts -$3,929) was chop under every gate. Most T2 longs enter in the 10:00 hour, before a 10:30 decision." + E},
    {"id": "bdi1016-dayclass-gate-rw7",
     "title": "RW7-gapdn-bounce-early-short-FD with the day-class gate K3 k0.50 at 10:00 (no new short from 10:00 on a 5-of-6-vote trend-up day)",
     "category": "filter", "parent": "bdi1016-dayclass-direction-gate", "tags": ["testing1", "shorts", "day-class", "gate", "needs-mcf-hook", "concentrated", "bdi"],
     "hypothesis": "Gap-down bounce shorts lose when the whole market is clearly up by 10:00.",
     "status": "finalist", "configs_tried": 0, "variant": "K3-k0.50-T1000",
     "notes": H + " Counted in the parent's 84. Meets the pre-declared Testing bar only: parent n 26,164 -0.058R (t -2.95) -> gated 25,502 -0.051R (t -2.58); blocked 662 trades on 11 days -0.343R (day-clustered t -3.01); delta +0.007 (H1 +0.010, H2 +0.0045), WF 5/7 months, random 95th pct +0.0045; plateau K3 k0.25 delta +0.012 (blocked t -2.87). K1 k0.50 at 10:00 also passes (blocked 584, -0.372R, t -2.98). CONCENTRATED (rule 5): 2025-04-07 and 2025-04-09 (tariff-crash rebound days) carry 233 of 662 blocked trades and -147R of -227R; ex-worst-day blocked -0.24R. Gated exp stays negative (-0.051R), up sessions -0.27R: the gate does not make RW7-FD a positive setup. Primary bar not met. Proposed for Testing 1 only (owner decision; needs a day_gate hook in mcf/)." + E},
    {"id": "bdi1016-dayclass-gate-cwt14pdh",
     "title": "CWT14-failbrk-pdh-p05-lowvol-short with the day-class gate K1 k0.25 at 10:30 (no new short from 10:30 when SPY, QQQ and IWM are all >= +0.25% from the open)",
     "category": "filter", "parent": "bdi1016-dayclass-direction-gate", "tags": ["testing2", "shorts", "day-class", "gate", "needs-mcf-hook", "bdi"],
     "hypothesis": "Failed-breakout shorts at the prior-day high lose more on broad trend-up days.",
     "status": "finalist", "configs_tried": 0, "variant": "K1-k0.25-T1030",
     "notes": H + " Counted in the parent's 84. Meets the pre-declared Testing bar: blocked 3,971 trades on 61 days -0.131R (t -4.98), delta +0.0037 (H1 +0.0037, H2 +0.0035), WF 0.60 (20 months), random 95th pct +0.0029, plateau k0.50 +0.0008 (t -2.59). Economically trivial: gated -0.090R (t -10.8) vs parent -0.094R; rule-19 up sessions -0.216R. NOT proposed: the setup is -0.09R on history with or without the gate and belongs in the rule-20 review of the CWT14 Testing 2 family." + E},
    {"id": "bdi1016-dayclass-trade-with-trend",
     "title": "Allow-list form of the day class: a long setup trades only on trend-up days and a short setup only on trend-down days (from T); chop days off",
     "category": "filter", "parent": "bdi1016-dayclass-direction-gate", "tags": ["testing1", "testing2", "day-class", "regime", "bdi"],
     "hypothesis": "The per-class table shows the aligned days carry the only positive cells: K3 k0.50 at 10:00 trend-up days CWT14-pdl-p05-long +0.071R (1,856), CWT14-orl-p05-long +0.006 (2,279), LIQ-orl +0.538 (244); K1 k0.25 10:00 trend-up LIQ-orl +0.230 (959); trend-down days RW2-FD +0.012 (2,225), CWT14-pdh short -0.010..-0.059.",
     "status": "idea", "configs_tried": 0,
     "notes": "Descriptive cells from regime_by_class.csv (bdi1016), not configurations; cells are small (9-72 days) and were seen before the test is declared, so the bar must count the 84 already tried (lineage 2,450, t >= 3.95). Trade counts fall to 2-10% of the parent." + E},
    {"id": "bdi1016-dayclass-late-decision",
     "title": "Day-class gate rework: decision at 11:00 / 12:00 (the 10-16 trend only became clear after 11:00; 10-15 reversal never classifiable by 10:30)",
     "category": "filter", "parent": "bdi1016-dayclass-direction-gate", "tags": ["testing1", "testing2", "day-class", "rework", "bdi"],
     "hypothesis": "A later decision trades accuracy against coverage: fewer remaining trades, but a clearer class (ix-oe: SPY rest-of-day slope on the move to T is continuation, t 3.2-4.2).",
     "status": "idea", "configs_tried": 0,
     "notes": "Rule-18 rework of bdi1016-dayclass-direction-gate; pre-declare T {11:00, 12:00} x the K1/K3 classifiers only; count in the 2,450 lineage. Most CWT14 and RW7 first signals fire before 11:00, so expected coverage is low." + E},
    {"id": "bdi1016-cwt14pdh-reentry-after-stop",
     "title": "CWT14 pdh failed-breakout shorts: one re-entry when price trades back below the entry within 60 min after a stop",
     "category": "exit", "parent": None, "tags": ["testing2", "shorts", "re-entry", "pattern", "bdi"],
     "hypothesis": "patterns.csv: CWT14-failbrk-pdh-p05-lowvol-short stopped_then_reversed on 5 days, pdh-p10-short on 4. 2026-10-16 T2 short re-entry legs +0.209R (10).",
     "status": "idea", "configs_tried": 0,
     "notes": "Pattern on 3+ days (rule: becomes a hypothesis). Live re-entry legs have been negative on other days (10-15 T2 -0.39R, 44), so test on history2y with costs before any proposal." + E},
    {"id": "bdi1016-rw7-late-exit",
     "title": "RW7-gapdn-bounce-early-short-FD: per-setup late exit (flat at 14:30 / 15:00 instead of 15:55)",
     "category": "exit", "parent": None, "tags": ["testing1", "shorts", "exit", "pattern", "bdi"],
     "hypothesis": "patterns.csv: RW7-FD late_hold on 4 days; LIQ-orl late_hold (3 days) is queued the same way.",
     "status": "idea", "configs_tried": 0,
     "notes": "Pattern on 3+ days. RW7-FD made +$134.69 on 10-16 and its hold-to-15:55 what-if was +0.526R vs +0.337 journal, so the late exit cuts winners on trend days: the test must split by day class." + E},
]
upd = {"nightly-1016-trend-day-long-reversal-veto": " | bdi1016: the day-level version (class fixed at 10:00/10:30, block longs on trend-down) was tested on CWT14-orl-p05/pdl-p05 longs and LIQ-orl (bdi1016-dayclass-direction-gate, 84 configs): blocked longs on trend-down days -0.03..-0.11R, barely worse than the parents (-0.09R); no long-side configuration passed. The per-bar fresh-low version in this entry is still untested and must count those 84."}
es = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {e["id"] for e in es}
for n in new:
    n = {"added": "2026-10-16", "source": SRC, "module": None, "variant": None, **n}
    if n["id"] in have:
        es = [n if e["id"] == n["id"] else e for e in es]
    else:
        es.append(n)
for e in es:
    if e["id"] in upd and upd[e["id"]] not in e.get("notes", ""):
        e["notes"] = e.get("notes", "") + upd[e["id"]]
B.write_text("".join(json.dumps(e) + "\n" for e in es))
print(len(es), "entries")
