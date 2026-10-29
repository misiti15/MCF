"""swarm15_1029: proposed backlog lines (NOT appended to research/backlog.jsonl; the lead decides) ->
backlog_proposed.jsonl. One grid line per setup (status from its best verdict) + one line per near-miss / pass.
Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
R = pd.read_csv(HERE / "results.csv")
out = []
for s, g in R.groupby("setup", sort=False):
    p = g[g["var"] == "P"].iloc[0]
    v = g[g["var"] != "P"]
    best = v.sort_values("exp_tv", ascending=False).iloc[0]
    nm = v[v.verdict.isin(["near-miss", "pass", "fail-hold"])]
    out.append({"id": f"swarm15-1029-{s}-grid", "title": f"{s}: swarm15 variant grid (stop x2/2.5/3 same $, target/scale-out, "
                "45/180-min time stops, windows, QQQ-VWAP / breadth / SPY-gap / prior-day-vol filters, re-entry, day caps, cost floors)",
                "added": "2026-10-29", "source": "BDI swarm15 2026-10-29 (research/bdi/swarm15_1029/NOTES.md)",
                "category": "setup", "parent": None, "tags": ["swarm15", "top5-tune", "bdi", "bdi-1029"],
                "hypothesis": "A one-knob variant of a high-trade-count live setup turns it positive after costs.",
                "status": "failed" if not len(nm) else "rework", "configs_tried": int(len(v)),
                "notes": (f"Grid {len(v)} rows, lineage N {int(p.lineage_N)}, bar t {p.bar:.2f}. Parent TRAIN+VALID n {int(p.n_tv)} "
                          f"exp {p.exp_tv:+.4f}R (TRAIN {p.exp_train:+.4f} / VALID {p.exp_valid:+.4f}), w/o best day {p.ex_best_day:+.4f}. "
                          f"Best row {best['var']} {best.knob}: {best.exp_tv:+.4f}R (TRAIN {best.exp_train:+.4f} / VALID {best.exp_valid:+.4f}, "
                          f"t {best.t_tv}). Pass {int((v.verdict == 'pass').sum())}, near-miss {int((v.verdict == 'near-miss').sum())}. "
                          "Open two-year history, locked block never loaded, costs in. Educational only - not financial advice."),
                "module": None, "variant": None})
    for _, r in nm.iterrows():
        out.append({"id": f"swarm15-1029-{s}-{r['var']}-{r.knob}", "title": f"{s}: {r.knob}", "added": "2026-10-29",
                    "source": "BDI swarm15 2026-10-29 (research/bdi/swarm15_1029/NOTES.md)", "category": "setup",
                    "parent": f"swarm15-1029-{s}-grid", "tags": ["swarm15", "bdi", "bdi-1029", r.verdict],
                    "hypothesis": f"{r.knob} improves {s}.", "status": "rework", "configs_tried": int(r.lineage_N),
                    "notes": (f"TRAIN {r.exp_train:+.4f} (n {int(r.n_train)}) / VALID {r.exp_valid:+.4f} (n {int(r.n_valid)}); "
                              f"TRAIN+VALID t {r.t_tv} vs bar {r.bar:.2f}; d vs parent TRAIN {r.d_train:+.4f} (t {r.t_imp_train:.2f}) / "
                              f"VALID {r.d_valid:+.4f} (t {r.t_imp_valid:.2f}); up {r.up:+.4f} / down {r.down:+.4f}; w/o best day "
                              f"{r.ex_best_day:+.4f}; vs random {r.excess_vs_random:+.4f}; HOLD (one look) n {r.get('hold_n')} "
                              f"exp {r.get('hold_exp')} t {r.get('hold_t')}. Verdict {r.verdict}. Educational only - not financial advice."),
                    "module": None, "variant": None})
(HERE / "backlog_proposed.jsonl").write_text("".join(json.dumps(o) + "\n" for o in out))
print(len(out), "lines")
