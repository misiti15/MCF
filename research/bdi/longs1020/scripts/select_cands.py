"""Apply the pre-declared candidate rule (PLAN.md) to results_A/B; write finalists.csv and counts.json."""
import json
import numpy as np, pandas as pd
from common import HERE
from mcf.research import gates

A = pd.read_csv(HERE / "results_A.csv")
B = pd.read_csv(HERE / "results_B.csv")
A_cfg = A[A.part != "A-control"].copy()
par = {("SPY", e): A_cfg[A_cfg.cfg == f"P-IDX5-SPY-{e}"].iloc[0] for e in ("t1s1", "t05s1", "holdtr", "time60")}
par.update({("QQQ", e): A_cfg[A_cfg.cfg == f"P-IDX1-QQQ-{e}"].iloc[0] for e in ("t1s1", "t05s1", "holdtr", "time60")})
fails = []
for _, r in A_cfg.iterrows():
    f = []
    for sp in ("train", "valid"):
        if not (r[f"{sp}_exp"] > 0): f.append(f"{sp} exp<=0")
        if not (r[f"{sp}_exp"] > r[f"{sp}_ctrl_all"]): f.append(f"{sp} <= C_all")
        if r.part != "A-parent":
            if not (r[f"{sp}_exp"] > r.get(f"{sp}_ctrl_same", np.nan)): f.append(f"{sp} <= C_same")
            p = par[(r.signal, r.exit)]
            if not (r[f"{sp}_exp"] > p[f"{sp}_exp"]): f.append(f"{sp} <= parent")
    if not (r.valid_t >= 1.5): f.append("valid t<1.5")
    if not (r.train_n >= 30): f.append("n_train<30")
    if not (r.all_ex_best > 0): f.append("ex-best-day<=0")
    fails.append(dict(cfg=r.cfg, part=r.part, n_fail=len(f), fails="; ".join(f)))
for _, r in B.iterrows():
    f = []
    for sp in ("train", "valid"):
        if not (r[f"{sp}_exp"] > 0): f.append(f"{sp} exp<=0")
        if not (r[f"{sp}_excess"] > 0): f.append(f"{sp} <= random")
        if r.part == "B5" and not (r[f"{sp}_exp"] > r[f"{sp}_parent_exp"]): f.append(f"{sp} <= parent")
    if not (r.valid_t >= 1.5): f.append("valid t<1.5")
    if not (r.train_n >= 150): f.append("n_train<150")
    if not (r.all_ex_best > 0): f.append("ex-best-day<=0")
    fails.append(dict(cfg=r.cfg, part=r.part, n_fail=len(f), fails="; ".join(f)))
F = pd.DataFrame(fails).sort_values(["n_fail", "cfg"])
F.to_csv(HERE / "gate_check.csv", index=False)
n = dict(A=int((A.part == "A").sum()), A_parent=int((A.part == "A-parent").sum()), A2=int((A.part == "A2").sum()),
         B=int((B.part == "B").sum()), B5=int((B.part == "B5").sum()), B5_parent=int((B.part == "B5-parent").sum()),
         controls_reported=int((A.part == "A-control").sum()))
n["total"] = sum(v for k, v in n.items() if k != "controls_reported")
n["bar_study"] = gates.t_required(n["total"])
n["bar_lineage_ns_st_live_longs"] = gates.t_required(165764 + 7737 + n["total"])
n["bar_lineage_index_dip"] = gates.t_required(266882 + n["total"])
n["candidates"] = F[F.n_fail == 0].cfg.tolist()
json.dump(n, open(HERE / "counts.json", "w"), indent=1)
print(n); print(F.head(25).to_string())
