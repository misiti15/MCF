"""Apply the pre-declared screen and gates (PLAN.md) to scan_all.csv. Writes results.csv (screen passers with every
gate), finalists.csv (gate passers after de-duplication). Educational only - not financial advice."""
import json
import math

import numpy as np
import pandas as pd

from common import (F, PARENT, SCR, WM, col, core, dcode, pick, symday)
from common import S as FR
from mcf.research.gates import regime_split, summary, walk_forward
from research.history2y import lib

HERE = __import__("pathlib").Path(__file__).resolve().parent
PRIOR = 86084
R = pd.read_csv(SCR / "scan_all.csv")
N_STUDY = len(R)
BAR = round(math.sqrt(2 * math.log(PRIOR + N_STUDY)), 3)
REG = lib.regimes()
print("configs", N_STUDY, "lineage", PRIOR + N_STUDY, "bar", BAR)

# plateau for stage A
A = R[R.stage == "A"].copy()
A["pos"] = (A.exp_tr > 0) & (A.exp_va > 0)
key = A.set_index(["parent", "x", "side", "geom", "window", "h", "b"])["pos"].to_dict()
from common import HGRID, BGRID  # noqa: E402


def plateau(r):
    hs, bs = HGRID[r.parent], BGRID
    i, j = hs.index(int(r.h)), bs.index(float(r.b))
    nb = [(hs[i + d], r.b) for d in (-1, 1) if 0 <= i + d < len(hs)] + [(r.h, bs[j + d]) for d in (-1, 1) if 0 <= j + d < len(bs)]
    xv = r.x if pd.notna(r.x) else None
    v = [key.get((r.parent, xv if xv is not None else np.nan, r.side, r.geom, r.window, int(h), float(b))) for h, b in nb]
    v = [bool(x) for x in v if x is not None]
    return round(sum(v) / len(v), 3) if v else np.nan


scr = R[(R.n_tr >= 150) & (R.n_va >= 50) & (R.n_all >= 200) & (R.exp_tr > 0) & (R.exp_va > 0)].copy()
print("screen passers", len(scr))


def mask_of(r):
    if r.stage == "A":
        x = None if pd.isna(r.x) else (float(r.x) if r.parent != "MF2" else int(r.x))
        m = core(r.parent, int(r.h), float(r.b), x)
    else:
        m = core(r.parent, *PARENT[r.parent]) & F[r.f1]
        if r.stage == "C":
            m = m & F[r.f2]
    return m & WM[r.window]


out, trades_of = [], {}
for k, r in scr.iterrows():
    idx = pick(mask_of(r), r.side, r.geom, bool(r.refire))
    t = pd.DataFrame({"date": FR["date"].to_numpy()[idx], "symbol": FR["symbol"].to_numpy()[idx],
                      "tod": FR["tod"].to_numpy()[idx], "r": col[f"p_{r.side}_{r.geom}"][idx]})
    rs = regime_split(t, REG)
    wf = walk_forward(t, exclude_months=lib.LOCKED_MONTHS)
    sm = summary(t)
    d = r.to_dict()
    d.update({"reg_up": rs["up"].get("exp_r"), "reg_flat": rs["flat"].get("exp_r"), "reg_down": rs["down"].get("exp_r"),
              "reg_pass": rs["pass"], "wf_share": wf["share_positive"], "wf_folds": wf["n_folds"],
              "ex_best_day": sm.get("ex_best_day"), "days": sm.get("days"), "win_rate": sm.get("win_rate"),
              "plateau": plateau(r) if r.stage == "A" else np.nan, "per_day": round(len(t) / max(1, len(set(FR["date"]))), 3)})
    d["gates_pass"] = bool(d["reg_pass"] and (d["wf_share"] or 0) >= 0.6 and d["xs_tr"] > 0 and d["xs_va"] > 0
                           and (d["xt_all"] or 0) >= 2 and (d["ex_best_day"] or -1) > 0
                           and (r.stage != "A" or (d["plateau"] >= 2 / 3)))
    d["bar_pass"] = bool(d["t_all"] >= BAR)
    out.append(d)
    trades_of[k] = set(symday[idx])
res = pd.DataFrame(out)
res.insert(0, "cid", res.index)
res.to_csv(HERE / "results.csv", index=False)
gp = res[res.gates_pass].copy()
gp["rank"] = gp[["t_tr", "t_va"]].min(axis=1)
gp = gp.sort_values("rank", ascending=False)
keep = []
for _, r in gp.iterrows():
    s = trades_of[scr.index[r.cid]]
    if all(len(s & trades_of[scr.index[q.cid]]) / len(s) < 0.6 for q in keep):
        keep.append(r)
fin = pd.DataFrame(keep)
fin.to_csv(HERE / "finalists.csv", index=False)
print("gate passers", len(gp), "after dedupe", len(fin), "bar passers", int(res.bar_pass.sum()), "gates+bar", int((res.gates_pass & res.bar_pass).sum()))
json.dump({"n_study": N_STUDY, "prior": PRIOR, "bar": BAR, "screen": len(scr), "gates": len(gp), "dedup": len(fin)},
          open(HERE / "gate_summary.json", "w"), indent=1)
