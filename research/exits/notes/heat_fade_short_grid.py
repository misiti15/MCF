"""Train-only exit grid for heat_fade_short. Educational only — not financial advice."""
import itertools, json, sys
from research.exits.harness import load, run
S = "heat_fade_short"; sigs = load()
grid = []
for tm in [15, 20, 30, 45, 60, 90, 120]:
    for tr in [0.0, 0.25, 0.5]:
        grid.append({"time_stop_min": tm, "time_stop_min_r": tr})
for eb in ["10:45", "11:00", "11:15", "11:30", "12:00", "12:30", "13:00", "14:00", "15:00"]:
    grid.append({"exit_by": eb})
for tg in [None, 0.75, 1.25, 1.5, 2.0]:
    grid.append({"target_r": tg})
for sm in [0.75, 1.25, 1.5]:
    grid.append({"stop_mult": sm})
for be in [0.5, 0.75]:
    grid.append({"be_at_r": be})
for tr_, ta in [(0.5, 0.5), (0.5, 0.75), (0.75, 0.75), (0.5, 1.0)]:
    grid.append({"target_r": None, "trail_r": tr_, "trail_after_r": ta})
for eb, tg in itertools.product(["11:00", "11:30", "12:00", "13:00"], [None, 1.5]):
    grid.append({"exit_by": eb, "target_r": tg})
for tm, eb in itertools.product([30, 45, 60, 90], ["11:30", "12:00", "13:00"]):
    grid.append({"time_stop_min": tm, "time_stop_min_r": 0.25, "exit_by": eb})
out = []
for v in grid:
    r = run(sigs, S, v, "train"); out.append({"variant": v, **r})
    print(json.dumps(v), r["n"], r["exp_r"], r["exp_r_se"], r["exp_r_ex_best_day"], r["avg_minutes"], flush=True)
json.dump(out, open("/tmp/claude-0/-home-user-MCF/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/hfs_grid.json", "w"))
print("configs", len(grid))
