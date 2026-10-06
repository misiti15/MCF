"""Train-only grid 2 for heat_fade_long: target x exit_by x (late time stop / trail). Educational only — not financial advice."""
import itertools, json
from research.exits.harness import load, run
S = "heat_fade_long"; sigs = load()
V = []
for tg, eb in itertools.product((1.0, 1.25, 1.5, 1.75, 2.0), (None, "14:30", "14:45", "15:00", "15:15", "15:30")):
    v = {}
    if tg != 1.0: v["target_r"] = tg
    if eb: v["exit_by"] = eb
    if v and not (tg == 1.0 and eb in ("14:30", "15:00", "15:30")) and not (eb is None and tg in (1.25, 1.5, 2.0)):
        V.append(v)
for tg, eb in itertools.product((1.0, 1.5), (None, "15:00")):
    for ts, tr in ((120, 0.5), (105, 0.5), (135, 0.5), (120, 0.6), (120, 0.4), (150, 0.5)):
        v = {"time_stop_min": ts, "time_stop_min_r": tr}
        if tg != 1.0: v["target_r"] = tg
        if eb: v["exit_by"] = eb
        V.append(v)
for eb in (None, "15:00"):
    for t, a in ((0.5, 0.5), (0.6, 0.6), (0.5, 0.4), (0.4, 0.5)):
        v = {"trail_r": t, "trail_after_r": a, "target_r": None}
        if eb: v["exit_by"] = eb
        V.append(v)
    for t, a in ((0.75, 1.0), (0.5, 1.0)):
        v = {"trail_r": t, "trail_after_r": a, "target_r": 1.5}
        if eb: v["exit_by"] = eb
        V.append(v)
for v in V:
    r = run(sigs, S, v, "train")
    print(json.dumps(v), r["n"], r["exp_r"], r["exp_r_se"], r["exp_r_ex_best_day"], r["green_days"], r["avg_minutes"], flush=True)
print("configs", len(V))
