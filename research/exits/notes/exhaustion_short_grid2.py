"""Train-only exit grid 2 for exhaustion_short (later time stops, combos). Educational only — not financial advice."""
import json, sys
from research.exits.harness import load, run
SETUP = "exhaustion_short"
G = []
G += [{"time_stop_min": n, "time_stop_min_r": x} for n in (90, 120) for x in (0.25, 0.5)]
G += [{"target_r": None, "time_stop_min": n, "time_stop_min_r": x} for n in (90, 120) for x in (0.25, 0.5)]
G += [{"target_r": t, "be_at_r": 1.0} for t in (1.5, 2.0)]
G += [{"target_r": t, "trail_r": 1.0, "trail_after_r": 1.0} for t in (1.5, 2.0, 3.0)]
G += [{"target_r": None, "trail_r": tr, "trail_after_r": 0.75} for tr in (0.5, 0.75, 1.0)]
G += [{"target_r": 1.75}]
G += [{"stop_mult": 1.25, "target_r": 1.5}, {"stop_mult": 0.75, "target_r": 2.0}]
if __name__ == "__main__":
    s = load(); out = []
    for v in G:
        r = run(s, SETUP, v, "train"); out.append({"variant": v, "train": r})
        print(json.dumps(v), r["n"], r["win_rate"], r["exp_r"], r["exp_r_se"], r["exp_r_ex_best_day"], r["green_days"], r["avg_minutes"], flush=True)
    json.dump(out, open(sys.argv[1], "w"), default=str)
