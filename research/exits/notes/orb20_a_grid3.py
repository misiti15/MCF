"""Train-only neighbourhood check for orb20_a. Educational only — not financial advice."""
import json, sys
from research.exits.harness import load, run
sigs = load(); S = "orb20_a"
V = [{"target_r": t, "time_stop_min": m, "time_stop_min_r": r} for t in (1.75, 2.0, 2.25) for m in (75, 105) for r in (0.4, 0.5)]
V += [{"target_r": t, "time_stop_min": 90, "time_stop_min_r": 0.3} for t in (1.75, 2.0)]
V += [{"target_r": 2.25, "time_stop_min": 90, "time_stop_min_r": r} for r in (0.4, 0.5)]
V += [{"stop_mult": 1.3, "target_r": t} for t in (1.5, 1.75)]
out = []
for v in V:
    r = run(sigs, S, v, "train"); out.append({"variant": v, "train": r})
    print(json.dumps(v), r["n"], r["exp_r"], r["exp_r_se"], r["pf"], r["exp_r_ex_best_day"], r["avg_minutes"], flush=True)
json.dump(out, open(sys.argv[1], "w"), default=str)
