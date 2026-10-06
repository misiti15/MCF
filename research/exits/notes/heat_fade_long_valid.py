"""Score fixed heat_fade_long finalists (chosen on train) on valid once; write candidates JSON. Educational only — not financial advice."""
import json
from research.exits.harness import load, run
S = "heat_fade_long"; sigs = load()
F = [{"exit_by": "15:00"}, {"exit_by": "14:45"}, {"target_r": 1.5}, {"target_r": 1.5, "exit_by": "15:00"},
     {"target_r": 1.25, "exit_by": "15:00"}, {"target_r": 1.75, "exit_by": "15:00"}, {"target_r": 2.0, "exit_by": "15:00"},
     {"target_r": 1.5, "exit_by": "14:45"}, {"trail_r": 0.6, "trail_after_r": 0.6, "target_r": None, "exit_by": "15:00"},
     {"time_stop_min": 120, "time_stop_min_r": 0.5, "exit_by": "15:00"}]
base = {sp: run(sigs, S, {}, sp) for sp in ("train", "valid")}
out = [{"variant": {}, "role": "baseline (current live exits)", **base}]
for v in F:
    rec = {"variant": v, "train": run(sigs, S, v, "train"), "valid": run(sigs, S, v, "valid")}
    ok = all(rec[sp]["exp_r"] - base[sp]["exp_r"] >= 0.03 and abs(rec[sp]["n"] / base[sp]["n"] - 1) <= 0.2
             and rec[sp]["exp_r_ex_best_day"] > 0 for sp in ("train", "valid"))
    rec["passes_train_valid_gate"] = ok
    out.append(rec)
    print(json.dumps(v), {sp: (rec[sp]["n"], rec[sp]["exp_r"], rec[sp]["exp_r_se"], rec[sp]["exp_r_ex_best_day"], rec[sp]["green_days"]) for sp in ("train", "valid")}, ok, flush=True)
print("baseline", {sp: (base[sp]["n"], base[sp]["exp_r"], base[sp]["exp_r_ex_best_day"]) for sp in base})
json.dump(out, open("research/exits/notes/heat_fade_long_valid_out.json", "w"), indent=1)
