"""Train-only focused grid #2 for heat_fade_short. Educational only — not financial advice."""
import json
from research.exits.harness import load, run
S = "heat_fade_short"; sigs = load(); grid = []
for tm in [10, 15, 20, 25, 30]:
    for tr in [0.4, 0.5, 0.6, 0.75]:
        grid.append({"time_stop_min": tm, "time_stop_min_r": tr})
for tm, tr in [(20, 0.5), (25, 0.5), (30, 0.5)]:
    for tg in [None, 1.25, 1.5]:
        grid.append({"time_stop_min": tm, "time_stop_min_r": tr, "target_r": tg})
    grid.append({"time_stop_min": tm, "time_stop_min_r": tr, "stop_mult": 0.75})
    grid.append({"time_stop_min": tm, "time_stop_min_r": tr, "exit_by": "15:00"})
for sm in [0.6, 0.7, 0.8, 0.9]:
    grid.append({"stop_mult": sm})
out = []
for v in grid:
    r = run(sigs, S, v, "train"); out.append({"variant": v, **r})
    print(json.dumps(v), r["n"], r["exp_r"], r["exp_r_se"], r["exp_r_ex_best_day"], r["avg_minutes"], flush=True)
print("configs", len(grid))
