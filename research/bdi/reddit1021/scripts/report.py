"""reddit1021 report: merge results, apply the pre-declared bars (PLAN.md), write results.csv, gate_check.csv,
finalists.csv, counts.json and the breakdown tables. Educational only - not financial advice."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import HERE, SCR, split_of
from mcf.research import gates

parts = []
for g in ("idx", "stk"):
    for s in ("s1", "s2", "ph"):
        p = HERE / f"results_{g}_{s}.csv"
        if p.exists():
            d = pd.read_csv(p)
            d["stage"] = s
            parts.append(d)
R = pd.concat(parts, ignore_index=True)
MV = pd.read_csv(HERE / "module_versions.csv") if (HERE / "module_versions.csv").exists() else pd.DataFrame()
N = len(R) + len(MV)
bar = gates.t_required(N)
bar_lineage = gates.t_required(N + 7718)


def fails(r):
    f = []
    ntr = 30 if r.group == "idx" else 150
    for sp in ("train", "valid"):
        if not (r[f"{sp}_exp"] > 0):
            f.append(f"{sp} exp<=0")
        if not (r[f"{sp}_exp"] > r[f"{sp}_ctrl"]):
            f.append(f"{sp}<=random")
    if not (r.valid_t >= 1.5):
        f.append("valid t<1.5")
    if not (r.train_n >= ntr):
        f.append(f"n_train<{ntr}")
    if not (r.all_ex_best > 0):
        f.append("ex-best<=0")
    return f


def cand_fails(r):
    f = []
    if not (r.all_t >= bar):
        f.append(f"t<{bar}")
    if not (r.up_exp > 0 and r.down_exp > 0 and r.up_n >= 30 and r.down_n >= 30):
        f.append("regime")
    if not (r.wf_share >= 0.6):
        f.append("wf<0.6")
    return f


R["testing_fails"] = R.apply(lambda r: "; ".join(fails(r)), axis=1)
R["n_testing_fails"] = R.apply(lambda r: len(fails(r)), axis=1)
R["candidate_fails"] = R.apply(lambda r: "; ".join(cand_fails(r)), axis=1)
R["status"] = np.where(R.n_testing_fails == 0, np.where(R.candidate_fails == "", "candidate", "testing-bar"),
                       np.where(R.n_testing_fails == 1, "near-miss", "fail"))
R.to_csv(HERE / "results.csv", index=False)
F = R[R.status != "fail"].sort_values(["group", "n_testing_fails", "valid_t"], ascending=[True, True, False])
F.to_csv(HERE / "finalists.csv", index=False)
cnt = {"configs_total": N, "module_versions_scored": len(MV), "by_group_stage": R.groupby(["group", "stage"]).size().to_dict(),
       "study_bar": bar, "bar_with_reddit1012liq_lineage": bar_lineage,
       "status": R.status.value_counts().to_dict(),
       "positive_both_splits": int(((R.train_exp > 0) & (R.valid_exp > 0)).sum()),
       "expected_false_pos_p05": round(0.05 * N, 1)}
cnt["by_group_stage"] = {f"{a}-{b}": int(v) for (a, b), v in cnt["by_group_stage"].items()}
json.dump(cnt, open(HERE / "counts.json", "w"), indent=1)
print(json.dumps(cnt, indent=1))
cols = ["group", "cfg", "train_n", "train_exp", "train_t", "train_win", "valid_n", "valid_exp", "valid_t", "valid_win",
        "all_t", "all_excess", "all_per_day", "up_exp", "down_exp", "wf_share", "all_ex_best", "status", "testing_fails"]
print(F[cols].to_string())

# breakdowns of the primary configurations by level family, side, split (trade level)
rows = []
for g in ("idx", "stk"):
    p = SCR / f"trades_{g}_s1.parquet"
    if not p.exists():
        continue
    T = pd.read_parquet(p)
    for typ in ("C", "R"):
        t = T[T.cfg == f"{typ}-f0.5-t2.0-eod"].copy()
        t["split"] = split_of(t.date)
        fam = {0: "OR", 1: "PM", 2: "AH", 3: "PD", 4: "SW"}
        for keyname, key in (("family", t.fam.map(fam)), ("side", np.where(t.side > 0, "long", "short")),
                             ("split", t.split), ("ticker", t.symbol if g == "idx" else pd.Series("stocks", index=t.index))):
            for v, u in t.groupby(key):
                for sp in ("train", "valid"):
                    w = u[u.split == sp]
                    if not len(w):
                        continue
                    s = gates.summary(w[["date", "r"]])
                    rows.append(dict(group=g, type=typ, by=keyname, value=v, split=sp, n=s["n"], win=s["win_rate"],
                                     exp=s["exp_r"], t=s["t"], gross=round(float(w.gross.mean()), 4),
                                     ctrl=round(float(w.ctrl.mean()), 4)))
pd.DataFrame(rows).to_csv(HERE / "breakdown_primary.csv", index=False)
