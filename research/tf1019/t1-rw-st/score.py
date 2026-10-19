"""Score the t1-rw-st grid (PLAN.md gates). Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from mcf.research import gates, timeframes as tf

S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent
LIN = {"MF": 203800 + 20, "NS": 114400 + 10, "EXH": 967100 + 10, "ST": 227400 + 40, "L3": 315800 + 15}
def lineage(nm):
    if nm.startswith(("RW1", "RW3", "RW5", "RW7")): return "MF"
    if nm.startswith(("RW4", "RW6")): return "NS"
    if nm.startswith(("RW2", "exhaustion")): return "EXH"
    return nm[:2] if nm.startswith("ST") else "L3"
reg = tf.regimes()
rows = []
for f in sorted(S.glob("*.parquet")):
    nm, m = f.stem.split("__"); m = int(m)
    tr = pd.read_parquet(f)
    hist = tr[tr["split"] != "forward"]
    N = LIN[lineage(nm)]
    s = tf.summarize(hist, N, reg)
    o = s.get("overall", {}); bs = s.get("by_split", {}); fw = gates.summary(tr[tr["split"] == "forward"]) if (tr["split"] == "forward").any() else {}
    rnd = s.get("random_same_minute", {}); rg = s.get("regime", {})
    tr_e, va_e = bs.get("train", {}).get("exp_r"), bs.get("valid", {}).get("exp_r")
    fails = list(s.get("fails", []))
    if not (tr_e and tr_e > 0 and va_e and va_e > 0): fails.append("train and valid exp must both be > 0")
    if not (rnd.get("excess_exp_r") is not None and rnd["excess_exp_r"] > 0): fails.append("excess vs random <= 0")
    rows.append({"setup": nm, "min": m, "lineage": lineage(nm), "N": N, "t_req": s["t_required"],
                 "n": o.get("n", 0), "exp": o.get("exp_r"), "t": o.get("t"),
                 "n_tr": bs.get("train", {}).get("n", 0), "exp_tr": tr_e, "t_tr": bs.get("train", {}).get("t"),
                 "n_va": bs.get("valid", {}).get("n", 0), "exp_va": va_e, "t_va": bs.get("valid", {}).get("t"),
                 "n_fw": fw.get("n", 0), "exp_fw": fw.get("exp_r"),
                 "ctrl": rnd.get("ctrl_exp_r"), "excess": rnd.get("excess_exp_r"), "excess_t": rnd.get("excess_t"),
                 "up": rg.get("up", {}).get("exp_r"), "down": rg.get("down", {}).get("exp_r"),
                 "regime_pass": s.get("regime_pass"), "wf": s.get("walk_forward", {}).get("share_positive"),
                 "pass": len(fails) == 0, "fails": "; ".join(fails)})
df = pd.DataFrame(rows).sort_values(["setup", "min"])
df.to_csv(HERE / "results.csv", index=False)
print(df.drop(columns=["fails", "N", "lineage"]).to_string(index=False))
print("configs scored:", len(df), "passing:", int(df["pass"].sum()))
