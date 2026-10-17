"""Screen + quality gates (PLAN.md) over scan_all.csv.gz. Writes results.csv (every screened config with gate columns)
and finalists.csv (candidates after de-duplication). Educational only - not financial advice."""
import ast
import json
import math

import numpy as np
import pandas as pd

from common import F, HERE, LIVE_CODE, PARENT, WM, core, neighbours, pick, trades
from mcf.research import gates
from research.history2y import lib

N_STUDY_DECL = 77364
N_PRIOR = 88400
A = pd.read_csv(HERE / "scan_all.csv.gz")
n_study = len(A)
N_LIN = N_PRIOR + n_study
BAR = gates.t_required(N_LIN)
print("configs", n_study, "declared", N_STUDY_DECL, "lineage", N_LIN, "bar", BAR)
REG = lib.regimes()

scr = A[(A.n_tr >= 150) & (A.n_va >= 50) & (A.n_all >= 200) & (A.exp_tr > 0) & (A.exp_va > 0)].copy()
print("screen pass", len(scr))
key = lambda r: (r.parent, r.th, r.side, r.geom, r.win)
Aa = A[A.stage == "A"].set_index(["parent", "th", "side", "geom", "win"])


def mask_of(r):
    th = ast.literal_eval(r.th)
    m = core(r.parent, th)
    if isinstance(r.filters, str) and r.filters:
        for f in r.filters.split("+"):
            m = m & F[f]
    return m & WM[r.win]


out = []
for _, r in scr.iterrows():
    idx = pick(mask_of(r), r.side, r.geom, bool(r.refire))
    tr = trades(idx, r.side, r.geom)
    reg = gates.regime_split(tr, REG)
    wf = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)
    sm = gates.summary(tr)
    rec = r.to_dict()
    rec.update({"t_gate": sm.get("t"), "ex_best_day": sm.get("ex_best_day"), "days": sm.get("days"),
                "up_exp": reg["up"].get("exp_r"), "up_n": reg["up"].get("n"), "dn_exp": reg["down"].get("exp_r"),
                "dn_n": reg["down"].get("n"), "flat_exp": reg["flat"].get("exp_r"), "regime_pass": reg["pass"],
                "wf_share": wf["share_positive"], "wf_folds": wf["n_folds"]})
    if r.stage == "A":
        th = ast.literal_eval(r.th)
        nb = [Aa.loc[(r.parent, str(t), r.side, r.geom, r.win)] for t in neighbours(r.parent, th)]
        ok = [(x.exp_tr > 0) and (x.exp_va > 0) for x in nb]
        rec["plateau"] = round(sum(ok) / len(ok), 3) if ok else None
    else:
        rec["plateau"] = None
    rec["g_regime"] = bool(reg["pass"])
    rec["g_wf"] = wf["share_positive"] is not None and wf["share_positive"] >= gates.WF_MIN_SHARE
    rec["g_random"] = bool(r.xs_tr > 0 and r.xs_va > 0 and (r.xt_all or 0) >= 2)
    rec["g_exbest"] = (sm.get("ex_best_day") or -1) > 0
    rec["g_plateau"] = r.stage != "A" or (rec["plateau"] is not None and rec["plateau"] >= 2 / 3)
    rec["candidate"] = all(rec[k] for k in ("g_regime", "g_wf", "g_random", "g_exbest", "g_plateau"))
    rec["clears_bar"] = rec["candidate"] and (sm.get("t") or 0) >= BAR
    rec["live_code"] = ",".join(sorted(set(str(r.filters).split("+")) & LIVE_CODE)) if isinstance(r.filters, str) else ""
    rec["_idx"] = idx
    out.append(rec)
R = pd.DataFrame(out)
R["rank"] = R[["t_tr", "t_va"]].min(axis=1)
R = R.sort_values("rank", ascending=False)
R.drop(columns="_idx").to_csv(HERE / "results.csv", index=False, float_format="%.4g")
C = R[R.candidate]
print("candidates", len(C), "clear bar", int(R.clears_bar.sum()))
keep = []
for _, r in C.iterrows():
    ids = set(r._idx.tolist())
    dup = any(len(ids & k[1]) / max(1, min(len(ids), len(k[1]))) >= 0.6 for k in keep)
    if not dup:
        keep.append((r, ids))
    if len(keep) >= 15:
        break
FN = pd.DataFrame([k[0] for k in keep]).drop(columns="_idx") if keep else pd.DataFrame()
FN.to_csv(HERE / "finalists.csv", index=False, float_format="%.4g")
json.dump({"n_study": n_study, "n_lineage": N_LIN, "bar": BAR, "screen": len(scr), "candidates": int(len(C)),
           "finalists": len(FN), "clear_bar": int(R.clears_bar.sum()),
           "gate_counts": {k: int(R[k].sum()) for k in ("g_regime", "g_wf", "g_random", "g_exbest", "g_plateau")}},
          open(HERE / "gate_summary.json", "w"), indent=1)
print(FN[["parent", "stage", "th", "filters", "side", "geom", "win", "refire", "n_tr", "exp_tr", "t_tr", "n_va", "exp_va",
          "t_va", "t_gate", "up_exp", "dn_exp", "wf_share", "xs_all", "xt_all"]].to_string() if len(FN) else "none")
