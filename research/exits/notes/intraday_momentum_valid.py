"""Score the 10 fixed intraday_momentum finalists (chosen on train) on valid, once. Writes candidates JSON. Educational only — not financial advice."""
import json
from research.exits.harness import load, run
S = "intraday_momentum"; sigs = load()
F = [{"exit_by": "15:45"}, {"exit_by": "15:47"}, {"exit_by": "15:50"},
     {"target_r": 0.2}, {"target_r": 0.25},
     {"exit_by": "15:48", "target_r": 0.25}, {"exit_by": "15:50", "target_r": 0.25}, {"exit_by": "15:50", "target_r": 0.4},
     {"time_stop_min": 15, "time_stop_min_r": 0.3}, {"exit_by": "15:50", "time_stop_min": 10, "time_stop_min_r": 0.1}]
base = {sp: run(sigs, S, {}, sp) for sp in ("train", "valid")}
out = [{"variant": {}, "role": "baseline (current live exits: stop 0.25 x ATR, no target, scale-out 50% at 1R, flat 15:55)", **base}]
print("baseline", base)
for v in F:
    r = {sp: run(sigs, S, v, sp) for sp in ("train", "valid")}
    ok = all(r[sp]["exp_r"] >= base[sp]["exp_r"] + 0.03 and abs(r[sp]["n"] - base[sp]["n"]) <= 0.2 * base[sp]["n"]
             and r[sp]["exp_r_ex_best_day"] > 0 for sp in ("train", "valid"))
    out.append({"variant": v, "role": "finalist", "passes_train_valid_bar": ok, **r})
    print(json.dumps(v), ok, "| train", r["train"]["exp_r"], r["train"]["exp_r_ex_best_day"], "| valid", r["valid"]["n"],
          r["valid"]["exp_r"], r["valid"]["exp_r_se"], r["valid"]["exp_r_ex_best_day"], r["valid"]["green_days"], r["valid"]["avg_minutes"], r["valid"]["exit_reasons"])
json.dump(out, open("research/exits/candidates/intraday_momentum.json", "w"), indent=1, default=str)
