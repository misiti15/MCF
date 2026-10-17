"""Gates 1-5 of PLAN.md on every screened configuration that beats the same-minute random baseline.
-> gate_all.csv (all screened rows with gate columns). Educational only - not financial advice."""
import json
import math

import numpy as np
import pandas as pd

from common import (HERE, FR, KS, PS, WM, core_rows, evfilter, frows_for, pick, trades)
from mcf.research import gates  # noqa: E402
import lib  # noqa: E402

N_PRIOR = 121309
REG = lib.regimes()
LOCKED = lib.LOCKED_MONTHS


def idx_of(r):
    f = r["filters"] if isinstance(r["filters"], str) else ""
    rows = frows_for(r["L"], float(r["p"]), int(r["k"]), r["vol"], f)
    return pick(rows[WM[r["win"]][rows]], bool(r["refire"]))


def gate_row(r):
    idx = idx_of(r)
    t = trades(idx, r["side"], r["exit"])
    rs = gates.regime_split(t, REG)
    wf = gates.walk_forward(t, exclude_months=LOCKED)
    day = t.groupby("date")["r"].agg(["sum", "size"])
    best = day["sum"].idxmax()
    exb = t.loc[t.date != best, "r"].mean()
    busiest = day["size"].max() / len(t)
    top5 = day["sum"].nlargest(5).sum() / max(t["r"].sum(), 1e-9) if t["r"].sum() > 0 else np.nan
    return {"up_n": rs["up"].get("n", 0), "up_exp": rs["up"].get("exp_r"), "flat_exp": rs["flat"].get("exp_r"),
            "down_n": rs["down"].get("n", 0), "down_exp": rs["down"].get("exp_r"), "regime_pass": rs["pass"],
            "wf_share": wf["share_positive"], "wf_folds": wf["n_folds"], "ex_best_day": exb, "busiest": busiest,
            "days": len(day), "top5_share": top5}


def neighbours(r):
    """one-step neighbours in p, k and window (Stage A/B axes); filters kept."""
    out = []
    pi = PS.index(float(r["p"]))
    for j in (pi - 1, pi + 1):
        if 0 <= j < len(PS):
            out.append(dict(r, p=PS[j]))
    ki = KS.index(int(r["k"]))
    for j in (ki - 1, ki + 1):
        if 0 <= j < len(KS):
            out.append(dict(r, k=KS[j]))
    order = ["0950-1030", "0950-1130", "1030-1300", "1130-1500", "1300-1500"]
    if r["win"] in order:
        wi = order.index(r["win"])
        for j in (wi - 1, wi + 1):
            if 0 <= j < len(order):
                out.append(dict(r, win=order[j]))
    return out


if __name__ == "__main__":
    from common import score
    d = pd.read_csv(HERE / "scan_all.csv.gz", low_memory=False)
    n_study = len(d)
    scr = (d.n_tr >= 150) & (d.n_va >= 50) & (d.n_all >= 200) & (d.exp_tr > 0) & (d.exp_va > 0)
    s = d[scr & (d.xs_tr > 0) & (d.xs_va > 0) & (d.xt_all >= 2)].copy()
    rows = []
    n_neigh = 0
    for _, r in s.iterrows():
        g = gate_row(r)
        nb = neighbours(r.to_dict())
        pos = 0
        for q in nb:
            i2 = idx_of(q)
            sc = score(i2, q["side"], q["exit"]) if len(i2) else {"exp_tr": np.nan, "exp_va": np.nan}
            n_neigh += 1
            pos += bool(sc.get("exp_tr", -1) > 0 and sc.get("exp_va", -1) > 0)
        g["plateau"] = pos / len(nb) if nb else np.nan
        rows.append({**r.to_dict(), **g})
    G = pd.DataFrame(rows)
    N = N_PRIOR + n_study + n_neigh
    bar = max(1.5, math.sqrt(2 * math.log(N)))
    G["bar"] = bar
    G["cand"] = (G.regime_pass & (G.wf_share >= 0.6) & (G.ex_best_day > 0) & (G.busiest <= 0.10) & (G.plateau >= 2 / 3))
    G["research_grade"] = G.cand & (G.t_all >= bar)
    G.to_csv(HERE / "gate_all.csv", index=False, float_format="%.5g")
    json.dump({"n_study": n_study, "n_neighbour_checks": n_neigh, "n_prior": N_PRIOR, "N_lineage": N, "bar": bar,
               "screened": int(scr.sum()), "beat_random": len(s), "candidates": int(G.cand.sum()),
               "research_grade": int(G.research_grade.sum())}, open(HERE / "gate_summary.json", "w"), indent=1)
    print(json.load(open(HERE / "gate_summary.json")))
