"""Combine BEG-02 results -> results.json (small). Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "research/ultimate_1119/top10"))
import bench10 as B
W = Path(sys.argv[1])
spy1 = B.spy_t1(); spy1 = spy1[spy1.index <= "2026-11-04"]
h = B.half(pd.Series(spy1.index)); NC = int((h != "none").sum()); NF = int((h == "fit").sum()); NK = int((h == "check").sum())
spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet"); spy2.index = spy2.index.astype(str)
spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
K = ["trades", "trades_per_session", "win", "avg_r", "avg_r_gross", "avg_r_wo_best_day", "best_day", "best_day_share",
     "total_r", "total_r_per_session", "worst_day", "t_day_clustered", "avg_r_spy_up", "avg_r_spy_flat", "avg_r_spy_down", "median_hold_min"]
def st(t, n, spy):
    s = B.stats(t, n, spy)
    if len(t):   # share also when total R <= 0 (bench10 leaves it None): best day R / |total R|
        day = t.groupby("date").r.sum(); s["best_day_r"] = round(float(day.max()), 2)
    return {k: s.get(k) for k in K + ["best_day_r"]}
out = {}
for v in ["base", "win1000"]:
    t1 = pd.read_parquet(W / f"bk_{v}_t1.parquet"); t2 = pd.read_parquet(W / f"bk_{v}_t2.parquet")
    out[v] = {"T1_fit": st(t1[t1.half == "fit"], NF, spy1), "T1_check": st(t1[t1.half == "check"], NK, spy1),
              "T1_combined": st(t1, NC, spy1), "T2": st(t2, len(spy2), spy2)}
    for side in (1, -1):
        out[v][f"T1_combined_{'long' if side>0 else 'short'}"] = st(t1[t1.side == side], NC, spy1)
    rnd = {}
    for test in ("t1", "t2"):
        fs = sorted(W.glob(f"bk_{v}_rnd*_{test}.parquet"))
        if not fs: continue
        rr = [pd.read_parquet(f) for f in fs]
        if test == "t1":
            rnd["T1_combined_avg_r"] = [round(float(x.r.mean()), 4) for x in rr]
            rnd["T1_check_avg_r"] = [round(float(x[x.half == "check"].r.mean()), 4) for x in rr]
            rnd["T1_fit_avg_r"] = [round(float(x[x.half == "fit"].r.mean()), 4) for x in rr]
        else:
            rnd["T2_avg_r"] = [round(float(x.r.mean()), 4) for x in rr]
    out[v]["random"] = rnd
for k in ("stop030", "stopx15", "win1000"):
    d = json.loads((W / f"res_{k}_fit.json").read_text())["T1_fit"]
    out.setdefault("tweaks_fit", {})[k] = {x: d.get(x) for x in ["trades", "raw_trades", "avg_r", "avg_r_gross", "avg_r_wo_best_day", "total_r_per_session", "t_day_clustered", "win"]}
def verdict(r):
    c, k, t2 = r["T1_combined"], r["T1_check"], r["T2"]
    legs = {"T1c_avg": (c["avg_r"], -0.0383), "T1k_avg": (k["avg_r"], -0.0464), "T1c_wo": (c["avg_r_wo_best_day"], -0.0674),
            "T1k_wo": (k["avg_r_wo_best_day"], -0.0781), "T1c_rps": (c["total_r_per_session"], -0.4862),
            "T1k_rps": (k["total_r_per_session"], -0.5218), "T2_avg": (t2["avg_r"], -0.1048)}
    fails = {n: round(a - b, 4) for n, (a, b) in legs.items() if a < b}
    enough = k["trades"] >= 20 and t2["trades"] >= 20
    if not fails and enough: tier = "MEETS"
    elif all(v >= -0.02 for v in fails.values() if True): tier = "NEAR"
    else: tier = "FAIL"
    rb = (c["avg_r"] <= -0.05 and c["t_day_clustered"] <= -2.0) or (r["T1_fit"]["avg_r"] < -0.03 and k["avg_r"] < -0.03 and (t2["avg_r"] < -0.03 if t2["trades"] >= 20 else True))
    return {"tier": tier, "failing_legs_gap": fails, "really_bad": bool(rb)}
for v in ["base", "win1000"]:
    out[v]["verdict"] = verdict(out[v])
(HERE / "results.json").write_text(json.dumps(out, indent=1, default=float))
for v in ["base", "win1000"]:
    print("==", v, out[v]["verdict"]); 
    for tst in ["T1_fit", "T1_check", "T1_combined", "T2", "T1_combined_long", "T1_combined_short"]:
        print(tst, out[v][tst])
    print("random", out[v]["random"])
print(out["tweaks_fit"])
