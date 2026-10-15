"""Append / update BDI 2026-10-15 entries in research/backlog.jsonl (idempotent by id). Educational only - not financial advice."""
import json
from pathlib import Path

ROOT = Path("/home/user/MCF")
B = ROOT / "research" / "backlog.jsonl"
SRC = "BDI 2026-10-15 (research/bdi/bdi1015/NOTES.md)"
E = " Educational only - not financial advice."
new = [
    {"id": "bdi1015-idxdip-prior-close", "title": "Index dip-bounce with the drop measured from the PRIOR CLOSE (gap included): SPY/QQQ down >= 0.5/0.75/1.0% vs prior close by 09:45/09:55, 20% recovery 09:50-10:05, trail/hold, 3x pick (SPXL/UPRO) or TQQQ",
     "category": "setup", "parent": "2026-10-16-testing-idxdip", "tags": ["testing1", "index", "idxdip", "prior-close", "owner", "bdi"],
     "hypothesis": "Owner chart read 2026-10-15: SPY opened -0.44% and bounced at 09:57 (-0.67% vs the prior close, only -0.24% vs the open); the open-based IDX setups miss gap-down dips.",
     "status": "failed", "configs_tried": 48,
     "notes": "pcdip.py, PLAN.md Part B. DEV (locked block never loaded; older holdouts not scored for PC). Not as good as the open-based setups on SPY (pre-declared rule: mean R and t >= the mapped open-based row, incremental days > 0, beats control, plateau): 3x TRAIL PC SPY 0.5/09:45 +0.065R (n 50, t 0.41) vs IDX5 +0.512 (14, t 1.00); 0.75/09:45 +0.165 (34, t 0.81) vs IDX2 +0.777 (5, t 0.78); 0.75/09:55 = same 34 trades vs IDX3 +0.468 (7). The extra gap-down days add +0.01..+0.11R. QQQ PC rows -0.04..+0.11R. Best row PC SPY 1.0/09:45 3x HOLD +0.522 (21, t 1.55), TRAIL +0.421 (t 1.45) - no open-based counterpart, so not eligible (queued as bdi1015-idxdip-pc-spy100). Most triggers fire on the first eligible bar (09:49 bar): the trigger is not selective; on 2026-10-15 PC SPY 0.5 fired at 09:49 and was stopped at 09:55 (-1.04R), before the owner's 09:57 low. Lineage 1,214, bar 3.77, max t 1.55." + E},
    {"id": "bdi1015-idxdip-gapdn-earlylow", "title": "Index gap-down + early low bounce: index opens >= 0.3/0.5% below the prior close and prints a low >= 0.10% below the open by 09:45/09:55; 20% recovery of (prior close - low) 09:50-10:05; trail/hold; 3x pick or TQQQ",
     "category": "setup", "parent": "2026-10-16-testing-idxdip", "tags": ["testing1", "index", "idxdip", "gap", "owner", "bdi"],
     "hypothesis": "Gap-down sessions whose gap extends into an early low bounce from the morning low (owner chart read 2026-10-15).",
     "status": "idea", "configs_tried": 32,
     "notes": "pcdip.py, PLAN.md Part B. One row passes the pre-declared comparison rule: QQQ g 0.5 / 09:55, TQQQ TRAIL +0.160R (n 43, t 0.89, ex-best +0.079) vs IDX1 TRAIL +0.003 (8) / HOLD +0.148 (8); 42 of 43 trades on days IDX1 did not trade (+0.086R); control all days -0.149R, same days random time +0.137R (the trigger adds little; the gap-day condition carries it). Plateau g 0.3 +0.024. Older holdouts scored once: n 10, +0.007R. Weak: H1 +0.621 (11) vs H2 +0.001 (32); regimes down -0.65 / flat -0.13 / up +0.96 (fails the rule-19 regime gate); 2026Q1 -0.11, 2026Q3 -0.22. 2026-10-15 (out of sample): fired 10:01, +1.81R. Research bar 3.77 not met. SPY GL rows: g 0.5 +0.218 (26, t 0.87) < IDX5/IDX3 TRAIL; g 0.3 negative. Proposed for a Testing 1 forward test only as IDX6-qqq-gapdn050-earlylow-0955-TQQQ-trail (owner decision; needs the dip_ref code change)." + E},
    {"id": "bdi1015-idxdip-pc-spy100", "title": "Index dip-bounce, SPY >= 1.0% below the PRIOR CLOSE by 09:45, 3x pick, trail or hold",
     "category": "setup", "parent": "bdi1015-idxdip-prior-close", "tags": ["testing1", "index", "idxdip", "prior-close", "bdi"],
     "hypothesis": "The deepest prior-close threshold was the strongest PC row (+0.42..+0.52R, n 21-22, t 1.25-1.55) but had no open-based counterpart under the pre-declared rule.",
     "status": "idea", "configs_tried": 0,
     "notes": "Already scored inside bdi1015-idxdip-prior-close (counted there). Regimes down -0.72 (5) / up +1.08 (13); H1 +0.72 (10) / H2 +0.15 (11). Re-test on forward sessions only before any proposal; do not re-tune on the DEV history." + E},
    {"id": "bdi1015-idxdip-late-low-trigger", "title": "Index dip-bounce rework: require the trigger to follow a new running low printed inside 09:50-10:05 (or entry_from 09:55)",
     "category": "setup", "parent": "2026-10-16-testing-idxdip", "tags": ["testing1", "index", "idxdip", "rework", "bdi"],
     "hypothesis": "Most dip-bounce triggers fire on the first eligible bar (09:49) and get stopped by a later, lower low (2026-10-15: SPY PC 0.5 trigger 09:49, stopped 09:55; real low 09:57).",
     "status": "idea", "configs_tried": 0,
     "notes": "From bdi1015 trigger-time counts (26 of 43 GL-QQQ and 32 of 50 PC-SPY triggers at the 09:49 bar). Pre-declare a small grid; count in the idxdip lineage (1,214)." + E},
    {"id": "bdi1015-short-index-up-veto", "title": "Lab short setups (NS2, NS2-FD, RW6-FD, RW2-FD, CWT09-g5-lowerhalf): a decision bar does not qualify while SPY fromOpen >= 0.25% / 0.50%",
     "category": "filter", "parent": "nightly-1015-gapdn-reclaim-short-veto", "tags": ["primary", "testing1", "testing2", "shorts", "index", "bdi"],
     "hypothesis": "2026-10-15's hindsight pointer (index up from the open against a short) as a causal veto.",
     "status": "failed", "configs_tried": 10,
     "notes": "crules.py, PLAN.md Part C2; nightly1015 first-signal hits, production + tod costs. 0 of 10 pass. The veto lowers exp in 7 of 10 and in up sessions in 10 of 10 (-0.05..-0.26R): it delays the first signal to a later, worse bar. NS2 (Primary) first signals taken with SPY fromOpen >= 0.25 are its better half (+0.065R, n 1,587). Overall exp rises only for CWT09-g5 (k 0.25 +0.082 to -0.107R; k 0.5 +0.016) and NS2-FD k 0.25 (+0.003), all still negative, and all worse in up sessions." + E},
]
upd = {"bdi1014-rw2-extension-floor": {"status": "failed", "configs_tried": 9,
       "notes_add": " | bdi1015 (crules.py, PLAN.md Part C1): F {2.0,2.5,3.0} x R {85,90,95} = 9 configs, 0 pass. 6 of 9 are no-ops (RW2's own rules already imply fromOpen >= 2 or rsi5 >= 90: identical to baseline -0.059R, n 22,187); the three rsi5 >= 95 versions lower exp (-0.004..-0.006R) and the down-session exp. 2026-10-15 live contradicts the 10-14 split (the 51 extended entries -0.373R vs 9 others -0.158R). Closed."}}
es = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {e["id"] for e in es}
for n in new:
    n = {"added": "2026-10-15", "source": SRC, "module": None, "variant": None, **n}
    if n["id"] in have:
        es = [n if e["id"] == n["id"] else e for e in es]
    else:
        es.append(n)
for e in es:
    if e["id"] in upd:
        u = upd[e["id"]]
        e["status"], e["configs_tried"] = u["status"], u["configs_tried"]
        if u["notes_add"] not in e.get("notes", ""):
            e["notes"] = e.get("notes", "") + u["notes_add"]
B.write_text("".join(json.dumps(e) + "\n" for e in es))
print(len(es), "entries")
