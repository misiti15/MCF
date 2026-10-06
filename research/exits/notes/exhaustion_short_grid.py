"""Train-only exit grid for exhaustion_short. Educational only — not financial advice."""
import json, sys
from research.exits.harness import load, run
SETUP = "exhaustion_short"
G = [{}]
G += [{"target_r": x} for x in (None, 0.75, 1.25, 1.5, 2.0, 2.5, 3.0)]
G += [{"stop_mult": m} for m in (0.75, 1.25, 1.5)]
G += [{"stop_mult": m, "target_r": None} for m in (0.75, 1.25, 1.5)]
G += [{"be_at_r": b} for b in (0.5, 0.75)]
G += [{"be_at_r": b, "target_r": None} for b in (0.75, 1.0, 1.5)]
G += [{"target_r": None, "trail_r": tr, "trail_after_r": ta} for tr in (0.75, 1.0, 1.5) for ta in (1.0, 1.5)]
G += [{"time_stop_min": n, "time_stop_min_r": x} for n in (20, 30, 45, 60) for x in (0.25, 0.5)]
G += [{"target_r": None, "time_stop_min": n, "time_stop_min_r": x} for n in (20, 30, 45, 60) for x in (0.25, 0.5)]
G += [{"exit_by": e} for e in ("14:30", "15:00", "15:30")]
G += [{"target_r": None, "exit_by": e} for e in ("15:00", "15:30")]
if __name__ == "__main__":
    s = load(); out = []
    for v in G:
        r = run(s, SETUP, v, "train"); out.append({"variant": v, "train": r})
        print(json.dumps(v), r["n"], r["win_rate"], r["exp_r"], r["exp_r_se"], r["exp_r_ex_best_day"], r["green_days"], r["avg_minutes"], flush=True)
    json.dump(out, open(sys.argv[1], "w"), default=str)
