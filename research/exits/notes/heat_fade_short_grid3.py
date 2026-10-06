"""Train-only neighbourhood checks #3 for heat_fade_short. Educational only — not financial advice."""
import json
from research.exits.harness import load, run
S = "heat_fade_short"; sigs = load(); grid = []
for tm in [15, 20, 25, 30]:
    for tr in [0.4, 0.6, 0.75]:
        grid.append({"time_stop_min": tm, "time_stop_min_r": tr, "target_r": 1.5})
for tm in [15, 20, 25]:
    for tr in [0.4, 0.6, 0.75]:
        grid.append({"time_stop_min": tm, "time_stop_min_r": tr, "target_r": None})
grid.append({"time_stop_min": 15, "time_stop_min_r": 0.5, "target_r": None})
grid.append({"time_stop_min": 15, "time_stop_min_r": 0.5, "target_r": 1.5})
for sm in [0.5, 0.55, 0.65]:
    grid.append({"stop_mult": sm})
for sm in [0.6, 0.7]:
    grid.append({"stop_mult": sm, "time_stop_min": 20, "time_stop_min_r": 0.5})
out = []
for v in grid:
    r = run(sigs, S, v, "train"); out.append({"variant": v, **r})
    print(json.dumps(v), r["n"], r["exp_r"], r["exp_r_se"], r["exp_r_ex_best_day"], r["avg_minutes"], flush=True)
print("configs", len(grid))
