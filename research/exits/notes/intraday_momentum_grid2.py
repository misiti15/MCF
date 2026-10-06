"""Neighbourhood grid (exit_by x small target) for intraday_momentum on TRAIN only. Educational only — not financial advice."""
import json
from research.exits.harness import load, run
S = "intraday_momentum"; sigs = load()
V = [{"target_r": x} for x in (0.15, 0.25)]
V += [{"exit_by": e, "target_r": tg} for e in ("15:45", "15:47", "15:48", "15:50") for tg in (0.2, 0.25, 0.3, 0.35)]
V += [{"exit_by": e, "target_r": 0.4} for e in ("15:47", "15:48")]
V += [{"exit_by": e} for e in ("15:46", "15:49", "15:51")]
out = []
for v in V:
    r = run(sigs, S, v, "train"); out.append({"variant": v, "train": r})
    print(json.dumps(v), r["n"], r["exp_r"], r["exp_r_se"], r["exp_r_ex_best_day"], r["green_days"], r["avg_minutes"], r["exit_reasons"])
print("configs", len(V))
json.dump(out, open("research/exits/notes/intraday_momentum_grid2_out.json", "w"), indent=1, default=str)
