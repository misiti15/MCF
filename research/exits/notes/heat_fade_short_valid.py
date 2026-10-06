"""Score <=10 train-chosen finalists on valid; write candidates JSON. Educational only — not financial advice."""
import json
from research.exits.harness import load, run
S = "heat_fade_short"; sigs = load()
F = [{"stop_mult": 0.55}, {"stop_mult": 0.6}, {"stop_mult": 0.65},
     {"stop_mult": 0.6, "time_stop_min": 20, "time_stop_min_r": 0.5},
     {"time_stop_min": 20, "time_stop_min_r": 0.5, "target_r": None},
     {"time_stop_min": 15, "time_stop_min_r": 0.5, "target_r": None},
     {"time_stop_min": 20, "time_stop_min_r": 0.5, "target_r": 1.5},
     {"time_stop_min": 30, "time_stop_min_r": 0.6, "target_r": 1.5},
     {"time_stop_min": 20, "time_stop_min_r": 0.5}]
base = {sp: run(sigs, S, {}, sp) for sp in ("train", "valid")}
print("BASE", base)
out = [{"variant": {}, "baseline": True, **base}]
for v in F:
    rec = {"variant": v, "train": run(sigs, S, v, "train"), "valid": run(sigs, S, v, "valid")}
    ok = all(rec[sp]["exp_r"] - base[sp]["exp_r"] >= 0.03 and abs(rec[sp]["n"] - base[sp]["n"]) <= 0.2 * base[sp]["n"]
             and rec[sp]["exp_r_ex_best_day"] > 0 for sp in ("train", "valid"))
    rec["passes_train_valid_gate"] = ok
    out.append(rec)
    print(json.dumps(v), "| T", rec["train"]["exp_r"], "| V", rec["valid"], ok, flush=True)
json.dump(out, open(f"research/exits/candidates/{S}.json", "w"), indent=1)
