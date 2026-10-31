"""saturday1031: append this run's backlog entries and update the ideas it re-tested (idempotent by id).
Usage: python research/bdi/saturday1031/backlog_updates.py   Educational only - not financial advice."""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[3] / "research" / "backlog.jsonl"
SRC = "BDI Saturday deep run 2026-10-31 (research/bdi/saturday1031/PLAN.md, NOTES.md)"
ED = " Educational only - not financial advice."
NEW = [
    dict(id="sat1031-f4-orl-sweep-qqq-rework", parent="reddit-1030-orbfvg-f4", category="setup", status="failed",
         configs_tried=8, tags=["rework", "rule-18", "rdt1030", "fvg", "long"],
         title="Rule-18 rework of F4-RW4-L (opening-range-low sweep + 15-min FVG, QQQ up, long): QQQ gate 0.10 / 0.30, BE +1R, fixed 2R, retrace entry, tight stop, displacement 0.30 ATR, FVG 0.10 ATR",
         hypothesis="F4-RW4-L (+0.013 / +0.114R, t 1.11) was the best rdt1030 long; its neighbourhood and one-knob pairs might sit on a plateau.",
         notes="0 of 8 pass (BAR90 t >= 3.52 at N 2,145). Best S31-D30-L (push >= 0.30 ATR): -0.011 / +0.190R, t 1.35, WF 70%, 5.0/session, down days -0.29R. Every row: TRAIN ~0 (-0.067..+0.018), down days -0.29..-0.39R, the random same-bar control +0.02..+0.05R (edge vs control +0.01..+0.04R), best day 51-87% of total R. It is a QQQ-up-day long, not a stock signal. Two rework rounds done (6 + 8): drop the F4 lineage." + ED),
    dict(id="sat1031-open-capitulation-reversal-long", parent="mh-1030-open-pdh-pop-fade", category="setup", status="failed",
         configs_tried=4, tags=["move-hunt", "open", "long", "new-idea"],
         title="09:40-09:50 opening capitulation reversal long: gap <= -1%, prior bar RSI5 <= 20, reversal bar (close up, buyPressure > 0), volumeRatio >= 1.5 / 3, at or below PDL + 0.25 ATR",
         hypothesis="Move library 10-29 / 10-30: the 69 early long movers had median gap -1.7%, RSI5 16, below VWAP, at the PDL, volumeRatio 2.2.",
         notes="0 of 4 pass (BAR90 2.20, N 20 Move Hunt lineage). Best v1.5 h1030w (0.5 ATR stop, exit 10:30): -0.065R, t -1.60, = the random 09:40 baseline (-0.065R); up days +0.11, down days -0.26R. The profile picks names that move, not the direction." + ED),
    dict(id="sat1031-open-gap-and-go-long", parent="mh-1030-open-pdh-pop-fade", category="setup", status="failed",
         configs_tried=4, tags=["move-hunt", "open", "long", "new-idea"],
         title="09:40-09:50 gap-and-go long: gap >= +1%, from-open >= +0.25 ATR, above VWAP, volumeRatio >= 1.5 / 3, SPY up from the open",
         hypothesis="Opening moves follow the day's direction (mh-1030); a stock already driving with the index at 09:40 may continue.",
         notes="0 of 4 pass. Best v3 h1030w: -0.063R, t -1.62 (baseline -0.065R), WF 41%, down days -0.18R; t1s1 versions -0.12..-0.15R. Finding: the wide 0.5 ATR stop + 10:30 exit halves the opening cost drag of a random 09:40 long (-0.135 -> -0.065R), but no single-stock feature tested picks direction at 09:40." + ED),
    dict(id="sat1031-burst-risk-share", parent="nightly-1029-burst20-one-bet", category="risk", status="failed",
         configs_tried=6, tags=["giveback", "burst", "sizing"],
         title="Burst risk sharing: a setup entering >= 10 / 20 symbols on one 5-min bar risks 3 / 5 / 10 R in total (each lot C/n of normal risk); no trade removed",
         hypothesis="Same-bar bursts are one index bet (10-29 GEN-261020-07: 47 longs, -42R); sizing them as one bet should cut give-back without removing trades or touching exits.",
         notes="0 of 6 pass on two years: burst lots are BETTER than the rest (K10: -0.002 vs -0.028R; train -0.033 vs -0.064, valid +0.025 vs -0.008), so R per unit risk falls (valid -0.0014 -> -0.004..-0.007R) and only 70-83% of the top-decile winners' R is kept; day std 51 -> 33-38R, worst 5 days halved, best 5 days cut 44-60%. Live paper 10-06..10-30 disagrees (K10/C3: give-back mean P 198 -> 186, T2 436 -> 328, GY 864 -> 696, Gen 763 -> 558 $/day; P/L better in every account) - live-only, not proposed. Gen setups are not in the two-year lab lists; a Gen-only test is the open follow-up." + ED),
]
UPD = {
    "nightly-1027-flatten-1545": ("failed", 5, "saturday1031 two-year test (flat2y.py, 60,907 lab trades of 21 setups, 1-min walk, sim vs lab r corr 0.999): flatten at 15:40 / 15:45 / 15:50 vs 15:55 = -0.0002 / -0.0011 / -0.0007R per trade (t -0.11 / -0.72 / -0.56); 15:45 longs -0.0050R (t -1.08), shorts -0.0001R; TRAIN and VALID both <= 0 at 15:45, positive only in up sessions. The live replay (+66.9R since 10-06, t 2.02, two days = 58%) does not hold on two years; consistent with sat1024's late lock. Coverage caveat: base windows, not the -FD lots."),
    "nightly-1029-burst20-one-bet": ("failed", 6, "Tested as sat1031-burst-risk-share: fails on two years (burst lots better than the rest); live-only evidence favours it, Gen-only test open."),
    "reddit-1030-orbfvg-f4": ("failed", 8, "saturday1031 rework round 2 (sat1031-f4-orl-sweep-qqq-rework): 0 of 8; lineage dropped."),
    "reddit-1030-orbfvg-f2": ("failed", 0, "saturday1031: F2-RW3-L not reworked - its +0.039R is 89% one day (2025-04-07; +0.005R without it), so it is not a near-miss under the one-big-day rule."),
}
es = [json.loads(l) for l in P.read_text().splitlines() if l.strip()]
ids = {e["id"] for e in es}
for e in es:
    if e["id"] in UPD:
        st, n, note = UPD[e["id"]]
        if "saturday1031" not in (e.get("notes") or ""):
            e["status"] = st
            e["configs_tried"] = (e.get("configs_tried") or 0) + n
            e["notes"] = (e.get("notes") or "").rstrip() + " | 2026-10-31: " + note + ED
for n in NEW:
    if n["id"] not in ids:
        es.append({"added": "2026-10-31", "source": SRC, "module": None, "variant": None, **n})
P.write_text("".join(json.dumps(e) + "\n" for e in es))
print(len(es), "entries")
