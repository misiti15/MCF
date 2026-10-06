"""Score <=10 train-chosen finalists once on valid; write candidates JSON. Educational only — not financial advice."""
import json
from research.exits.harness import load, run
SETUP = "exhaustion_short"
F = [{"target_r": 1.25}, {"target_r": 1.5}, {"target_r": 1.75}, {"target_r": 2.0}, {"target_r": None},
     {"target_r": 2.0, "be_at_r": 1.0}, {"target_r": 2.0, "trail_r": 1.0, "trail_after_r": 1.0},
     {"target_r": None, "trail_r": 1.0, "trail_after_r": 1.0}]
if __name__ == "__main__":
    s = load(); out = [{"variant": {}, "baseline": True, "train": run(s, SETUP, {}, "train"), "valid": run(s, SETUP, {}, "valid")}]
    for v in F:
        out.append({"variant": v, "train": run(s, SETUP, v, "train"), "valid": run(s, SETUP, v, "valid")})
    for o in out:
        print(json.dumps(o["variant"]), "| train", o["train"]["exp_r"], o["train"]["exp_r_ex_best_day"], "| valid", o["valid"]["n"],
              o["valid"]["win_rate"], o["valid"]["exp_r"], o["valid"]["exp_r_se"], o["valid"]["exp_r_ex_best_day"], o["valid"]["green_days"], o["valid"]["exit_reasons"])
    json.dump(out, open("research/exits/notes/exhaustion_short_valid_out.json", "w"), indent=1, default=str)
