"""Train-only exit grid round 2 (combinations) for orb20_a. Educational only — not financial advice."""
import json, sys
from research.exits.harness import load, run
sigs = load(); S = "orb20_a"
V = []
V += [{"target_r": t, "time_stop_min": m, "time_stop_min_r": 0.5} for t in (1.75, 2.0, None) for m in (60, 90, 120)]
V += [{"stop_mult": s, "target_r": t} for s in (1.15, 1.25, 1.35) for t in (1.2, 1.5, 1.75, 2.0)]
V += [{"stop_mult": 1.25, "target_r": t, "time_stop_min": 90, "time_stop_min_r": 0.5} for t in (1.5, 1.75)]
V += [{"stop_mult": 1.25, "time_stop_min": m, "time_stop_min_r": 0.5} for m in (60, 90, 120)]
V += [{"target_r": t, "time_stop_min": 90, "time_stop_min_r": r} for t in (1.75, 2.0) for r in (0.4, 0.6)]
out = []
for v in V:
    r = run(sigs, S, v, "train"); out.append({"variant": v, "train": r})
    print(json.dumps(v), r["n"], r["exp_r"], r["exp_r_se"], r["pf"], r["exp_r_ex_best_day"], r["avg_minutes"], flush=True)
json.dump(out, open(sys.argv[1], "w"), default=str)
