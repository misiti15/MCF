"""Train-only exit grid for orb20_a. Educational only — not financial advice."""
import json, itertools, sys
from research.exits.harness import load, run
sigs = load(); S = "orb20_a"
V = [{}]
V += [{"target_r": x} for x in (None, 1.0, 1.25, 1.75, 2.0, 2.5, 3.0)]
V += [{"stop_mult": x} for x in (0.75, 1.25, 1.5)]
V += [{"time_stop_min": m, "time_stop_min_r": r} for m in (15, 30, 45, 60, 90, 120, 180) for r in (0.25, 0.5, 0.75)]
V += [{"be_at_r": x} for x in (0.5, 0.75, 1.0)]
V += [{"trail_r": tr, "trail_after_r": ta} for tr in (0.5, 0.75, 1.0) for ta in (0.5, 1.0)]
V += [{"exit_by": x} for x in ("11:30", "12:30", "13:30", "14:30", "15:00")]
V += [{"target_r": None, "trail_r": tr, "trail_after_r": ta} for tr in (0.75, 1.0, 1.5) for ta in (1.0, 1.5)]
out = []
for v in V:
    r = run(sigs, S, v, "train"); out.append({"variant": v, "train": r})
    print(json.dumps(v), r["n"], r["exp_r"], r["exp_r_se"], r["pf"], r["exp_r_ex_best_day"], r["avg_minutes"], flush=True)
json.dump(out, open(sys.argv[1], "w"), default=str)
