"""Append the top5_1014 grids to research/backlog.jsonl (idempotent by id). Educational only - not financial advice.
No variant beat its parent at the pre-declared bar, so each setup's grid is recorded once, as failed, with its numbers."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path("/home/user/MCF")
B = ROOT / "research" / "backlog.jsonl"
R = pd.read_csv(ROOT / "research" / "bdi" / "top5_1014" / "results.csv")
SRC = "BDI top-5 tune 2026-10-14 (research/bdi/top5_1014/NOTES.md)"
E = " Educational only - not financial advice."
META = {
    "CWT14-failbrk-orl-p05-long": ("cwt-b-b3-failed-breakout-reversal", "testing2", "cwt14"),
    "CWT14-failbrk-orl-p05-lowvol-long": ("cwt-b-b3-failed-breakout-reversal", "testing2", "cwt14"),
    "CWT14-failbrk-pdl-p05-long": ("cwt-b-b3-failed-breakout-reversal", "testing2", "cwt14"),
    "heat_fade_short-FD": ("live-heat_fade_short", "testing1", "heat"),
    "RW7-gapdn-bounce-early-short-FD": ("bdi-rw-gapdn-bounce-early", "testing1", "rw7"),
}
new = []
for s, (parent, acct, fam) in META.items():
    d = R[R.setup == s]
    p = d[d.is_parent].iloc[0]
    v = d[~d.is_parent]
    best = v.sort_values("t_improve", ascending=False).iloc[0]
    both = v[(v.d_train > 0) & (v.d_valid > 0)]
    knobs = ", ".join(f"{r.var} {r.knob}" for r in v.itertuples())
    note = (f"top5_1014 (scan_top5.py / report_top5.py, pre-declared in PLAN.md). {len(v)} one-knob variants ({knobs}); "
            f"open two-year history, locked block never loaded; TRAIN <= 2025-12, VALID 2026-01..03 + 07..09-15; production + tod costs. "
            f"Parent TRAIN+VALID n {int(p.n_tv)}, exp {p.exp_tv:+.4f}R, t {p.t_tv}, up {p.up:+.3f} / down {p.down:+.3f}, "
            f"excess vs same-minute random {p.excess_vs_random:+.4f}R. 0 of {len(v)} variants has exp > 0; 0 beat the parent at the bar "
            f"(t_improve >= {p.bar_improve if pd.notna(p.bar_improve) else best.bar_improve}). {len(both)} improve on both TRAIN and VALID; "
            f"best {best.var} ({best.knob}) {best.exp_tv:+.4f}R, d {best.d_tv:+.4f}R, t_improve {best.t_improve} (bar {best.bar_improve}). "
            f"Testing bar 0, research bar (lineage t >= {best.t_research_bar}) 0. No holdout scored.")
    new.append({"id": f"top5-1014-{s}-tune", "title": f"{s}: small one-knob variations (thresholds +-10-20%, window, exit geometry, VWAP/RSI cut, one extra filter)",
                "category": "setup", "parent": parent, "tags": [acct, fam, "top5-tune", "bdi"],
                "hypothesis": "A small one-knob change to one of the 5 most-traded live setups (2026-10-08..14) raises its win rate or average R without changing what it is.",
                "status": "failed", "configs_tried": int(best.lineage_N), "notes": note + E})
es = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {e["id"] for e in es}
for n in new:
    n = {"added": "2026-10-14", "source": SRC, "module": None, "variant": None, **n}
    es = [n if e["id"] == n["id"] else e for e in es] if n["id"] in have else es + [n]
B.write_text("".join(json.dumps(e) + "\n" for e in es))
print(len(es), "entries")
