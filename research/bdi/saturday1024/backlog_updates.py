"""saturday1024: append this run's backlog entries and update the ideas it tested (idempotent by id).
Usage: python research/bdi/saturday1024/backlog_updates.py   Educational only - not financial advice."""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[3] / "research" / "backlog.jsonl"
SRC = "BDI Saturday deep run 2026-10-24 (research/bdi/saturday1024/PLAN.md, book_sim.py, book_sim.csv)"
ED = " Educational only - not financial advice."
NEW = [
    dict(id="sat1024-rw-cluster-cap", parent="loop-1008-exhaustion-cluster-t1", category="risk", status="failed",
         configs_tried=6, tags=["giveback", "rework", "rule-18", "cluster"],
         title="Same-bar cluster cap: a setup takes at most 3 / 5 new entries per decision bar (books P / T1 / T2)",
         hypothesis="Same-poll clusters of one setup (10-21 / 10-23: 15-28 lots in one poll) are one bet; capping them should cut give-back without touching exits.",
         notes="0 of 6 pass (bar 3.79, lineage N 1,340). Primary k3/k5: train +0.017/+0.014R, valid -0.001/-0.000R (fails valid); T1 k3 +0.019/+0.009R but keeps 80-83% and down sessions -0.024R; T2 k5 valid -0.002R. Give-back mean falls only with the trade count." + ED),
    dict(id="sat1024-rw-post-peak-side-brake", parent="gb-1019-post-peak-index-guard", category="risk", status="failed",
         configs_tried=6, tags=["giveback", "rework", "rule-18"],
         title="Post-peak same-side brake: once the book's realized R has peaked >= X (P 3R, T 10R) and given back 50% / 33%, the side that lost since the peak takes no new entries",
         hypothesis="Most give-back is new same-direction entries after the day turns (giveback1019: 65-98%); braking only the losing side after a real give-back should keep the other side and the good days.",
         notes="0 of 6 pass. Best Primary f33: train +0.029 / valid +0.010R, t 3.20, but keeps 81-84% and down sessions -0.003R; T1 f50 valid +0.001R; T2 +0.001..+0.004R with t <= 1.75. Fires on few days; the book's down days are not post-peak days." + ED),
    dict(id="sat1024-one-lot-per-symbol-2y", parent="gb-1019-twin-setup-exposure", category="risk", status="failed",
         configs_tried=3, tags=["giveback", "twin", "lot-cap"],
         title="One open lot per symbol across all setups (max_lots_per_symbol 1) on the two-year book",
         hypothesis="Cross-setup same-symbol stacking (BKH x3 on 10-23) doubles the same bet; the twin cap helped live (blocked twin signals -27.9R over 10-20..10-23).",
         notes="0 of 3 pass. P: +0.013 / +0.006R, T1 +0.020 / +0.011R (t 3.41), T2 +0.014 / -0.001R, but every book keeps only 77-83% of trades and all three lose in down sessions (-0.013..-0.020R). Live twin cap stays as is." + ED),
    dict(id="sat1024-late-profit-lock", parent="nightly-1014-fd-short-late-giveback", category="exit", status="failed",
         configs_tried=6, tags=["giveback", "exit", "late"],
         title="Late profit lock: from 15:00 / 14:30, an open trade >= +0.5R at a 1-min close gets its stop raised to entry +0.25R",
         hypothesis="Open winners handed back into the 15:55 flatten (T1 10-20 -$221, P 10-22 -$135, T2 10-21 -$84) could be locked without touching targets.",
         notes="0 of 6, clearly harmful: delta -0.004..-0.009R per trade in every book and split, t -3.6..-8.0 (19,375 / 26,445 locks on 2 years). Late open winners keep drifting; the flatten give-back is cheaper than the lock. Do not reopen without a new reason." + ED),
    dict(id="sat1024-pm-drift-continuation", parent=None, category="setup", status="idea", configs_tried=0,
         tags=["new-idea", "afternoon", "drift"],
         title="Afternoon drift continuation: at 14:30-15:00 enter in the direction of a stock's day move when it is >= +X ATR from the open and on the right side of VWAP, hold to 15:55",
         hypothesis="The late-lock test shows trades already +0.5R after 14:30 keep running into the close on two years (locking them cost 0.004-0.009R per trade in all books); a dedicated late entry may capture that drift. Untested; needs the 2-year frames plus the 1-min cache after 15:00.",
         notes="Idea only, 0 configurations. Source: saturday1024 addendum L." + ED),
]
UPD = {
    "st-a-1022-primary-setup-stop": ("rework", 9, "saturday1024 2-year joint backtest of Primary's 10 cached enabled setups (CWT14-pdl-p10-lowvol missing), book sim with live lot/twin caps: latched per-setup stop S1.5 / S2 / S3 all positive in train AND valid and in up AND down sessions (S2 +0.013 / +0.013R per trade, t 3.32; S3 +0.012 / +0.008R, t 3.10; S1.5 t 3.01; bar 3.79), blocked trades avg -0.13R (S2) / -0.19R (S3), 17 of 21 months better, +374R / +292R over 2 years (+309R / +230R without the best day); the 20 best book days give up 26.5R (S2) / 2.4R (S3) of 753R. Below the bar: evidence, not proof. Goes to the owner as DECISION ST-P (inbox 2026-10-24)."),
    "nightly-1020-setup-loss-limit-open-risk": ("failed", 3, "saturday1024 SO (S2 + realized + open lots x -1R <= -3R): delta +0.02..+0.07R but keeps only 24-54% of trades in every book and loses in down sessions (-0.023..-0.074R). Too restrictive; LL-OPEN closed."),
    "gb-1019-twin-setup-exposure": ("failed", 3, "Tested as sat1024-one-lot-per-symbol-2y: keeps 77-83% of trades, negative in down sessions in all books. The live twin cap (setup vs -FD / twin_group) stays."),
    "nightly-1016-primary-one-lot-per-symbol": ("failed", 1, "Primary row of sat1024-one-lot-per-symbol-2y: +0.013 / +0.006R, t 2.29, keeps 82-83%, down sessions -0.013R."),
}
es = [json.loads(l) for l in P.read_text().splitlines() if l.strip()]
ids = {e["id"] for e in es}
for e in es:
    if e["id"] in UPD:
        st, n, note = UPD[e["id"]]
        if "saturday1024" not in (e.get("notes") or ""):
            e["status"] = st
            e["configs_tried"] = (e.get("configs_tried") or 0) + n
            e["notes"] = (e.get("notes") or "").rstrip() + " | 2026-10-24: " + note + ED
for n in NEW:
    if n["id"] not in ids:
        es.append({"added": "2026-10-24", "source": SRC, "module": None, "variant": None, **n})
P.write_text("".join(json.dumps(e) + "\n" for e in es))
print(len(es), "entries")
