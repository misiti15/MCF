"""Train-only grid for heat_fade_long exits. Educational only — not financial advice."""
import itertools, json
from research.exits.harness import load, run
S = "heat_fade_long"; sigs = load()
V = [{}]
for ts, tr in itertools.product((20, 30, 45, 60, 75, 90, 120), (0.1, 0.2, 0.3, 0.4, 0.5)):
    V.append({"time_stop_min": ts, "time_stop_min_r": tr})
for eb in ("13:30", "14:00", "14:30", "15:00", "15:30"):
    V.append({"exit_by": eb})
for tg in (0.75, 1.25, 1.5, 2.0, None):
    V.append({"target_r": tg})
for sm in (0.75, 1.25, 1.5):
    V.append({"stop_mult": sm})
for be in (0.5, 0.75):
    V.append({"be_at_r": be})
for t, a in ((0.5, 0.5), (0.5, 0.75), (0.75, 0.75), (0.5, 1.0)):
    V.append({"trail_r": t, "trail_after_r": a, "target_r": None})
out = []
for v in V:
    r = run(sigs, S, v, "train"); out.append({"variant": v, **r})
    print(json.dumps(v), r["n"], r["exp_r"], r["exp_r_se"], r["exp_r_ex_best_day"], r["avg_minutes"], flush=True)
print("configs", len(V))
