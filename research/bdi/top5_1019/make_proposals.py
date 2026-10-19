"""Write top5_1019 backlog PROPOSALS (research/backlog.jsonl format) to research/bdi/top5_1019/backlog_proposals.jsonl.
It does NOT touch research/backlog.jsonl; the lead appends these lines. Educational only - not financial advice.
One entry per setup grid (status failed: 0 of 93 meet the Testing bar, every variant but 3 LIQ rows has exp <= 0),
plus one entry per variant that beat its parent at the pre-declared bar (status rework: beats parent, still negative)."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
SRC = "BDI top-5 execution tune 2026-10-19 (fourth run) (research/bdi/top5_1019/NOTES.md)"
E = " Educational only - not financial advice."
META = {
    "CWT14-failbrk-pdl-p10-long": ("cwt-b-b3-failed-breakout-reversal", "testing2", "cwt14"),
    "CWT14-failbrk-pdl-p05-lowvol-long": ("cwt-b-b3-failed-breakout-reversal", "testing2", "cwt14"),
    "CWT14-failbrk-pdh-p10-short": ("cwt-b-b3-failed-breakout-reversal", "testing2", "cwt14"),
    "LIQ-orl-sweep-open15-s25-long": ("bdi-reddit1012-liquidity-sweep", "testing1", "liq"),
    "RW2-exhaustion-noon-adv150-short-FD": ("bdi-rw-exhaustion-noon-adv150", "testing1", "rw2"),
}
LIVE = {"E05": ("module only, no mcf/ change: a new research module with GEOM 'S' whose stop_price(f, i) = close -/+ 1.25 x "
                "0.25 x atr_d and target_price(f, i, stop) = the parent's target price (close +/- up x 0.25 x atr_d); "
                "LabStrategy sizes by the stop distance, so $ risk stays the same. Plus a new config entry."),
        "E07": ("NOT executable live today: partial exits (scale-out) do not work at Alpaca because the bracket leg qty "
                "cannot be changed; needs a runner change (cancel/replace the bracket legs) before it can run.")}
COMMON = ("open two-year history, locked block 2024-11..2025-02 never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + "
          "07..09-15; production + tod costs; 5-minute path simulator with parity to gates.lab_trades on 2025-06 "
          "(mean |diff| <= 5e-5 R, 100% within 0.01R); stop-distance variants scored at the same $ risk; random control = "
          "5 same-minute symbols through the same mechanics.")


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f}, avg win {r.avg_win:+.3f} / avg loss {r.avg_loss:+.3f} (break-even win {r.be_win:.3f}), "
            f"exp {r.exp_tv:+.4f}R (t {r.t_tv}), TRAIN {r.exp_train:+.4f} / VALID {r.exp_valid:+.4f} (t {r.t_valid}), "
            f"up {r.up:+.3f} / down {r.down:+.3f}, excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, (parent, acct, fam) in META.items():
    d = R[R.setup == s]
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    both = v[(v.d_train > 0) & (v.d_valid > 0)]
    knobs = ", ".join(f"{r.var} {r.knob}" for r in v.itertuples())
    note = (f"top5_1019 (scan_1019.py / report_1019.py, pre-declared in PLAN.md). {len(v)} one-knob execution variants ({knobs}); "
            f"{COMMON} Parent TRAIN+VALID {fmt(p)}. {int((v.exp_tv > 0).sum())} of {len(v)} variants has exp > 0; "
            f"{int(v.beats_parent.sum())} beat the parent at the setup bar {p.bar_setup}; {len(both)} improve on both TRAIN and VALID; "
            f"best {best.var} ({best.knob}) {best.exp_tv:+.4f}R, d {best.d_tv:+.4f}R, t_improve {best.t_improve} (setup bar "
            f"{best.bar_setup}, lineage bar {best.bar_lineage}). Testing bar (VALID t >= 3.01, exp > 0, both regimes) 0; no holdout scored.")
    new.append({"id": f"top5-1019-{s}-exec",
                "title": f"{s}: execution variants (time stop, tighter/wider stop, breakeven, scale-out, wait one bar, window, SPY-direction filter, flow filter, re-entry cooldown, thresholds)",
                "category": "setup", "parent": parent, "tags": [acct, fam, "top5-tune", "bdi"],
                "hypothesis": "An execution change (exit management, entry timing or one filter) converts the live setup's win rate into more R per trade.",
                "status": "failed", "configs_tried": int(p.lineage_N), "notes": note + E})
    for r in v[v.beats_parent].itertuples():
        new.append({"id": f"top5-1019-{s}-{r.var}-{r.knob.replace('_ALPACA_CAVEAT', '')}",
                    "title": f"{s} with {r.knob.replace('_ALPACA_CAVEAT', '')} ({r.var}, top5_1019 PLAN.md section 3)",
                    "category": "setup", "parent": parent, "tags": [acct, fam, "top5-tune", "bdi", "beats-parent"],
                    "hypothesis": "This execution change raises the parent's R per trade on TRAIN and on VALID.",
                    "status": "rework", "configs_tried": int(r.lineage_N), "live_support": LIVE.get(r.var, ""),
                    "notes": (f"top5_1019 beats parent: d {r.d_tv:+.4f}R (TRAIN {r.d_train:+.4f}, VALID {r.d_valid:+.4f}), day-block bootstrap t "
                              f"{r.t_improve} vs setup bar {r.bar_setup} (lineage bar {r.bar_lineage}: {'met' if r.t_improve >= r.bar_lineage else 'not met'}). "
                              f"Variant {fmt(r)}. Still negative after costs, so it fails the Testing bar; status rework = pair round (rule 18) "
                              f"or forward sessions. {COMMON}" + E)})
with open(OUT / "backlog_proposals.jsonl", "w") as fh:
    for n in new:
        fh.write(json.dumps({"added": "2026-10-19", "source": SRC, "module": None, "variant": None, **n}) + "\n")
print(len(new), "proposals written")
