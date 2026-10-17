"""Apply the pre-declared screen and gates (PLAN.md) to scan_all. Writes results.csv (screen passers with every gate),
finalists.csv (gate passers after de-duplication), gate_summary.json. Educational only - not financial advice."""
import json
import math

import numpy as np
import pandas as pd

from common import (F, GRIDS, HERE, LINEAGE, PARENT, SCR, WM, col, pick, symday, trades)
from mcf.research.gates import regime_split, summary, walk_forward
from research.history2y import lib

PRIOR = {"MF": 133904, "NS": 84000, "EXH": 934500}
R = pd.read_csv(SCR / "scan_all.csv.gz", low_memory=False, dtype={"a0": str, "a1": str, "a2": str, "a3": str})
R["lineage"] = R.parent.map(LINEAGE)
N_STUDY = len(R)
NL = R.lineage.value_counts().to_dict()
BAR = {k: round(max(1.5, math.sqrt(2 * math.log(PRIOR[k] + NL.get(k, 0)))), 3) for k in PRIOR}
REG = lib.regimes()
print("configs", N_STUDY, NL, "bars", BAR)


def parse(v):
    if v in ("None", "nan") or (isinstance(v, float) and np.isnan(v)):
        return None
    if v in ("True", "False"):
        return v == "True"
    try:
        x = float(v)
        return int(x) if x.is_integer() and abs(x) < 1e6 and "." not in v else x
    except ValueError:
        return v


def combo_of(r):
    n = len(GRIDS[r.parent][1])
    return tuple(parse(getattr(r, f"a{i}")) for i in range(n))


# plateau for stage A: one-step neighbours on the first two axes
A = R[R.stage == "A"].copy()
A["pos"] = (A.exp_tr > 0) & (A.exp_va > 0)
key = {(r.parent, r.desc, r.side, r.geom, r.window): r.pos for r in A.itertuples()}


def plateau(r):
    axes = GRIDS[r.parent][1]
    c = list(combo_of(r))
    nb = []
    for ax in (0, 1):
        i = axes[ax].index(c[ax])
        for d in (-1, 1):
            if 0 <= i + d < len(axes[ax]):
                cc = list(c)
                cc[ax] = axes[ax][i + d]
                nb.append("|".join(map(str, cc)))
    v = [key.get((r.parent, d, r.side, r.geom, r.window)) for d in nb]
    v = [bool(x) for x in v if x is not None]
    return round(sum(v) / len(v), 3) if v else np.nan


scr = R[(R.n_tr >= 150) & (R.n_va >= 50) & (R.n_all >= 200) & (R.exp_tr > 0) & (R.exp_va > 0)].copy()
print("screen passers", len(scr))


def mask_of(r):
    if r.stage == "A":
        return GRIDS[r.parent][0](*combo_of(r)) & WM[r.window]
    m = PARENT[r.parent]() & WM[r.window]
    if r.stage in ("B", "C", "D"):
        m = m & F[r.f1]
    if r.stage == "C":
        m = m & F[r.f2]
    return m


out, trades_of = [], {}
for k, r in scr.iterrows():
    rf = int(r.refire) if r.refire else None
    idx = pick(np.flatnonzero(mask_of(r)), r.side, r.geom, rf)
    t = trades(idx, r.side, r.geom)
    rs = regime_split(t, REG)
    wf = walk_forward(t, exclude_months=lib.LOCKED_MONTHS)
    sm = summary(t)
    d = r.to_dict()
    d.update({"reg_up": rs["up"].get("exp_r"), "reg_flat": rs["flat"].get("exp_r"), "reg_down": rs["down"].get("exp_r"),
              "n_up": rs["up"].get("n"), "n_down": rs["down"].get("n"),
              "reg_pass": rs["pass"], "wf_share": wf["share_positive"], "wf_folds": wf["n_folds"],
              "ex_best_day": sm.get("ex_best_day"), "days": sm.get("days"), "win_rate": sm.get("win_rate"),
              "plateau": plateau(r) if r.stage == "A" else np.nan,
              "per_day": round(len(t) / 425, 3), "bar": BAR[r.lineage]})
    d["gates_pass"] = bool(d["reg_pass"] and (d["wf_share"] or 0) >= 0.6 and d["xs_tr"] > 0 and d["xs_va"] > 0
                           and (d["xt_all"] or 0) >= 2 and (d["ex_best_day"] or -1) > 0
                           and (r.stage != "A" or (d["plateau"] >= 2 / 3)))
    d["bar_pass"] = bool(d["t_all"] >= d["bar"])
    out.append(d)
    trades_of[k] = set(symday[idx])
res = pd.DataFrame(out)
res.insert(0, "cid", scr.index.to_numpy())
res.to_csv(HERE / "results.csv", index=False)
gp = res[res.gates_pass].copy()
gp["rank"] = gp[["t_tr", "t_va"]].min(axis=1)
gp = gp.sort_values("rank", ascending=False)
keep = []
for _, r in gp.iterrows():
    s = trades_of[r.cid]
    if all(len(s & trades_of[q.cid]) / len(s) < 0.6 for q in keep):
        keep.append(r)
fin = pd.DataFrame(keep)
fin.to_csv(HERE / "finalists.csv", index=False)
print("gate passers", len(gp), "after dedupe", len(fin), "bar passers", int(res.bar_pass.sum()),
      "gates+bar", int((res.gates_pass & res.bar_pass).sum()))
json.dump({"n_study": N_STUDY, "n_by_lineage": NL, "prior": PRIOR, "bar": BAR, "screen": len(scr),
           "reg_pass": int(res.reg_pass.sum()), "wf_pass": int((res.wf_share >= 0.6).sum()),
           "gates": len(gp), "dedup": len(fin), "gates_and_bar": int((res.gates_pass & res.bar_pass).sum())},
          open(HERE / "gate_summary.json", "w"), indent=1)
