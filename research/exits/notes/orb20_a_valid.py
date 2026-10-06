"""Score <=10 train-chosen finalists for orb20_a on train and valid (test stays locked). Educational only — not financial advice."""
import json
from research.exits.harness import load, run
sigs = load(); S = "orb20_a"
F = [{"target_r": 2.0, "time_stop_min": 90, "time_stop_min_r": 0.4},
     {"target_r": 2.0, "time_stop_min": 75, "time_stop_min_r": 0.4},
     {"target_r": 1.75, "time_stop_min": 90, "time_stop_min_r": 0.5},
     {"target_r": 2.25, "time_stop_min": 90, "time_stop_min_r": 0.4},
     {"target_r": None, "time_stop_min": 90, "time_stop_min_r": 0.5},
     {"stop_mult": 1.3, "target_r": 1.75},
     {"stop_mult": 1.25, "target_r": 1.75},
     {"stop_mult": 1.3, "target_r": 1.5},
     {"target_r": 2.0},
     {"time_stop_min": 90, "time_stop_min_r": 0.5}]
base = {sp: run(sigs, S, {}, sp) for sp in ("train", "valid")}
out = {"setup": S, "baseline": {"variant": {}, **base}, "finalists": []}
for v in F:
    tr, va = run(sigs, S, v, "train"), run(sigs, S, v, "valid")
    ok = all(x["exp_r"] - base[sp]["exp_r"] >= 0.03 and abs(x["n"] - base[sp]["n"]) <= 0.2 * base[sp]["n"] and x["exp_r_ex_best_day"] > 0
             for sp, x in (("train", tr), ("valid", va)))
    out["finalists"].append({"variant": v, "train": tr, "valid": va, "passes_train_valid_bar": ok})
    print(json.dumps(v), "| T", tr["n"], tr["exp_r"], tr["exp_r_ex_best_day"], "| V", va["n"], va["exp_r"], va["exp_r_se"], va["pf"], va["exp_r_ex_best_day"], va["avg_minutes"], va["exit_reasons"], "PASS" if ok else "fail", flush=True)
json.dump(out, open("research/exits/notes/orb20_a_valid_out.json", "w"), indent=1, default=str)
