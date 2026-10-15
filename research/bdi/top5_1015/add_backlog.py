"""Append the top5_1015 results to research/backlog.jsonl (idempotent by id). Educational only - not financial advice.
One entry per setup's grid (failed: 0 of 89 meet the Testing bar, every variant has exp <= 0), plus one entry per
variant that beat its parent at the pre-declared bar (status rework: it beats the parent but is still negative)."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path("/home/user/MCF")
B = ROOT / "research" / "backlog.jsonl"
R = pd.read_csv(ROOT / "research" / "bdi" / "top5_1015" / "results.csv")
SRC = "BDI top-5 execution tune 2026-10-15 (research/bdi/top5_1015/NOTES.md)"
E = " Educational only - not financial advice."
META = {
    "CWT14-failbrk-orl-p05-long": ("cwt-b-b3-failed-breakout-reversal", "testing2", "cwt14"),
    "CWT14-failbrk-orl-p05-lowvol-long": ("cwt-b-b3-failed-breakout-reversal", "testing2", "cwt14"),
    "CWT14-failbrk-pdl-p05-long": ("cwt-b-b3-failed-breakout-reversal", "testing2", "cwt14"),
    "heat_fade_short-FD": ("live-heat_fade_short", "testing1", "heat"),
    "CWT12-coil-k4-long": ("cwt-b-b4-coil-flag-breakout", "testing2", "cwt12"),
}
COMMON = ("open two-year history, locked block never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + 07..09-15; production + "
          "tod costs; 5-minute path simulator with parity to gates.lab_trades (mean |diff| <= 5e-5 R); random control = 5 same-minute "
          "symbols through the same entry/exit mechanics.")


def fmt(r):
    return (f"n {int(r.n_tv)}, win {r.win_tv:.3f}, avg win {r.avg_win:+.3f} / avg loss {r.avg_loss:+.3f} (break-even win {r.be_win:.3f}), "
            f"exp {r.exp_tv:+.4f}R (t {r.t_tv}), TRAIN {r.exp_train:+.4f} / VALID {r.exp_valid:+.4f}, up {r.up:+.3f} / down {r.down:+.3f}, "
            f"excess vs random {r.excess_vs_random:+.4f}R")


new = []
for s, (parent, acct, fam) in META.items():
    d = R[R.setup == s]
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    paired = v[v.t_improve.notna()]
    best = paired.sort_values("t_improve", ascending=False).iloc[0]
    both = v[(v.d_train > 0) & (v.d_valid > 0)]
    knobs = ", ".join(f"{r.var} {r.knob}" for r in v.itertuples())
    note = (f"top5_1015 (scan_1015.py / report_1015.py, pre-declared in PLAN.md). {len(v)} one-knob execution variants ({knobs}); {COMMON} "
            f"Parent TRAIN+VALID {fmt(p)}. 0 of {len(v)} variants has exp > 0; {int(v.beats_parent.sum())} beat the parent at the setup bar "
            f"{p.bar_setup}; {len(both)} improve on both TRAIN and VALID; best {best.var} ({best.knob}) {best.exp_tv:+.4f}R, d {best.d_tv:+.4f}R, "
            f"t_improve {best.t_improve} (setup bar {best.bar_setup}, lineage bar {best.bar_lineage}). Testing bar (t >= 3.00 and exp > 0) 0; "
            f"research bar 0. No holdout scored.")
    new.append({"id": f"top5-1015-{s}-exec", "title": f"{s}: execution variants (time stop, breakeven, scale-out, tighter stop, limit/delayed entry, flow filter, loser-pattern opposites)",
                "category": "setup", "parent": parent, "tags": [acct, fam, "top5-tune", "bdi"],
                "hypothesis": "An execution change (exit management or entry timing) converts the live setup's win rate into more R per trade.",
                "status": "failed", "configs_tried": int(p.lineage_N), "notes": note + E})
    for r in v[v.beats_parent].itertuples():
        new.append({"id": f"top5-1015-{s}-{r.var}-{r.knob}", "title": f"{s} with {r.knob} ({r.var}, PLAN.md section 3)",
                    "category": "setup", "parent": parent, "tags": [acct, fam, "top5-tune", "bdi", "beats-parent"],
                    "hypothesis": "This execution change raises the parent's R per trade on TRAIN and on VALID.",
                    "status": "rework", "configs_tried": int(r.lineage_N),
                    "notes": (f"top5_1015 beats parent: d {r.d_tv:+.4f}R (TRAIN {r.d_train:+.4f}, VALID {r.d_valid:+.4f}), day-block bootstrap t "
                              f"{r.t_improve} vs setup bar {r.bar_setup} (lineage bar {r.bar_lineage}: {'met' if r.t_improve >= r.bar_lineage else 'not met'}). "
                              f"Variant {fmt(r)}. Still negative after costs, so it fails the Testing bar; status rework = pair it with another "
                              f"near-miss in a pre-declared pair round (rule 18) or judge it on forward sessions. {COMMON}" + E)})
es = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {e["id"] for e in es}
for n in new:
    n = {"added": "2026-10-15", "source": SRC, "module": None, "variant": None, **n}
    es = [n if e["id"] == n["id"] else e for e in es] if n["id"] in have else es + [n]
B.write_text("".join(json.dumps(e) + "\n" for e in es))
print(len(es), "entries;", len(new), "written")
