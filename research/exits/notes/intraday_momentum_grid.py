"""Single-rule + small-combination exit grid for intraday_momentum on TRAIN only. Educational only — not financial advice."""
import json
from research.exits.harness import load, run
S = "intraday_momentum"; sigs = load()
V = [{}]
V += [{"exit_by": x} for x in ("15:40", "15:43", "15:45", "15:47", "15:48", "15:50", "15:52", "15:53")]
V += [{"target_r": x} for x in (0.2, 0.3, 0.4, 0.5, 0.6, 0.75, 1.0)]
V += [{"stop_mult": x} for x in (0.5, 0.75, 1.5)]
V += [{"be_at_r": x} for x in (0.2, 0.3, 0.5)]
V += [{"trail_r": tr, "trail_after_r": ta} for tr in (0.15, 0.25, 0.4) for ta in (0.2, 0.4)]
V += [{"time_stop_min": m, "time_stop_min_r": x} for m in (5, 10, 15) for x in (0.0, 0.1, 0.2, 0.3)]
V += [{"exit_by": e, "target_r": tg} for e in ("15:45", "15:50") for tg in (0.4, 0.5)]
V += [{"exit_by": e, "time_stop_min": 10, "time_stop_min_r": x} for e in ("15:45", "15:50") for x in (0.1, 0.2)]
out = []
for v in V:
    r = run(sigs, S, v, "train"); out.append({"variant": v, "train": r})
    print(json.dumps(v), r["n"], r["exp_r"], r["exp_r_se"], r["exp_r_ex_best_day"], r["avg_minutes"], r["exit_reasons"])
print("configs", len(V) - 1)
json.dump(out, open("research/exits/notes/intraday_momentum_grid_out.json", "w"), indent=1, default=str)
