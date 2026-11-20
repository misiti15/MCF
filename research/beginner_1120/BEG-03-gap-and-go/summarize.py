"""Combine BEG-03 results -> results.json (small). Educational only - not financial advice.
  python summarize.py WORK"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

W = Path(sys.argv[1])
spy1 = B.spy_t1()
spy1 = spy1[spy1.index <= "2026-11-04"]
h = B.half(pd.Series(spy1.index))
NC, NF, NK = int((h != "none").sum()), int((h == "fit").sum()), int((h == "check").sum())
spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
spy2.index = spy2.index.astype(str)
spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
K = ["trades", "trades_per_session", "win", "avg_r", "avg_r_gross", "avg_r_wo_best_day", "best_day", "best_day_share",
     "total_r", "total_r_per_session", "worst_day", "t_day_clustered", "avg_r_spy_up", "avg_r_spy_flat",
     "avg_r_spy_down", "median_hold_min", "symbols"]


def st(t, n, spy):
    s = B.stats(t, n, spy)
    if len(t):
        s["best_day_r"] = round(float(t.groupby("date").r.sum().max()), 2)
    return {k: s.get(k) for k in K + ["best_day_r"]}


def verdict(r):
    c, k, t2 = r["T1_combined"], r["T1_check"], r["T2"]
    legs = {"T1c_avg": (c["avg_r"], -0.0383), "T1k_avg": (k["avg_r"], -0.0464),
            "T1c_wo": (c["avg_r_wo_best_day"], -0.0674), "T1k_wo": (k["avg_r_wo_best_day"], -0.0781),
            "T1c_rps": (c["total_r_per_session"], -0.4862), "T1k_rps": (k["total_r_per_session"], -0.5218),
            "T2_avg": (t2["avg_r"], -0.1048)}
    fails = {n: round(a - b, 4) for n, (a, b) in legs.items() if a < b}
    enough = k["trades"] >= 20 and t2["trades"] >= 20
    tier = "MEETS" if (not fails and enough) else ("NEAR" if all(v >= -0.02 for v in fails.values()) else "FAIL")
    rb = (c["avg_r"] <= -0.05 and c["t_day_clustered"] <= -2.0) or (
        r["T1_fit"]["avg_r"] < -0.03 and k["avg_r"] < -0.03 and (t2["avg_r"] < -0.03 if t2["trades"] >= 20 else True))
    return {"tier": tier, "failing_legs_gap": fails, "really_bad": bool(rb)}


out = {}
for v in ["base", "win1015"]:
    bk = pd.read_parquet(W / f"bk_{v}_all.parquet")
    t1, t2 = bk[bk.test == "t1"], bk[bk.test == "t2"]
    out[v] = {"T1_fit": st(t1[t1.half == "fit"], NF, spy1), "T1_check": st(t1[t1.half == "check"], NK, spy1),
              "T1_combined": st(t1, NC, spy1), "T2": st(t2, len(spy2), spy2)}
    out[v]["T1_combined_by_entry"] = {
        str(b): round(float(x.r.mean()), 4) for b, x in t1.groupby(pd.cut(t1.tod, [949, 1014, 1059]), observed=True)}
    out[v]["exit_mix_T1c"] = t1.kind.map({0: "time", 1: "stop_trail", 2: "target"}).value_counts().to_dict()
    rnd = {}
    for ctl in ("", "after", "univ"):
        fs = sorted(W.glob(f"bk_{v}_rnd[0-9]{ctl}_all.parquet"))
        if not fs:
            continue
        rr = [pd.read_parquet(f) for f in fs]
        nm = ctl or "pre"
        rnd[nm] = {
            "T1_fit": [round(float(x[(x.test == "t1") & (x.half == "fit")].r.mean()), 4) for x in rr],
            "T1_check": [round(float(x[(x.test == "t1") & (x.half == "check")].r.mean()), 4) for x in rr],
            "T1_combined": [round(float(x[x.test == "t1"].r.mean()), 4) for x in rr],
            "T2": [round(float(x[x.test == "t2"].r.mean()), 4) for x in rr]}
    out[v]["random"] = rnd
    out[v]["verdict"] = verdict(out[v])
for k in ("base", "win1015", "gap5", "stopmax2"):
    d = json.loads((W / f"res_{k}_fit.json").read_text())["T1_fit"]
    out.setdefault("tweaks_fit", {})[k] = {x: d.get(x) for x in ["trades", "raw_trades", "win", "avg_r", "avg_r_gross",
                                                                 "avg_r_wo_best_day", "total_r_per_session",
                                                                 "t_day_clustered", "worst_day"]}
out["configs"] = {"base": 1, "tweaks": 3, "random_controls_fitted": 0, "total": 4}
(HERE / "results.json").write_text(json.dumps(out, indent=1, default=float))
for v in ["base", "win1015"]:
    print("==", v, out[v]["verdict"])
    for tst in ["T1_fit", "T1_check", "T1_combined", "T2"]:
        print(tst, out[v][tst])
    print(out[v]["T1_combined_by_entry"], out[v]["exit_mix_T1c"])
    print(json.dumps(out[v]["random"]))
