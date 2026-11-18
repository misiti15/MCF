"""U7 diagnostics (after the verdicts, not used for them): parent entries vs random entries on check days;
every candidate's check effect (does the fit pick beat a random pick from the same menu?); per-setup full record."""
import math, numpy as np, pandas as pd, sys
sys.argv = ["x"]; exec(open(__file__.replace("diag.py", "score.py")).read().split("out, cand_rows = [], []")[0])
R = pd.read_csv(f"{S}/u7_results.csv"); C = pd.read_csv(f"{S}/u7_candidates.csv")
rows, crow = [], []
for s in top:
    g = x[x.strategy == s].sort_values("et"); days = sorted(g.date.unique()); nf = math.ceil(len(days) / 2)
    fit = g[g.date.isin(days[:nf])]; chk = g[g.date.isin(days[nf:])]
    hasT = g.tR.notna().mean() > 0.5 and (g.exit_reason == "target").any()
    span = (int(g.emin.min()), int(g.emin.max())); real, rnd = [], []
    for r in chk.itertuples():
        tg = r.tR if hasT else None
        real.append(sim(r, math.ceil(r.emin), tg, None))
        for _ in range(5): rnd.append(sim(r, int(rng.integers(span[0], span[1] + 1)), tg, None))
    f, c, a = stats(fit, "R"), stats(chk, "R"), stats(g, "R")
    rows.append(dict(setup=s, n=a["n"], days=a["days"], tot=a["tot"], avg=a["avg"], wob=a["wob"], bsh=a["bsh"],
                     fit_n=f["n"], fit_avg=f["avg"], chk_n=c["n"], chk_avg=c["avg"], chk_wob=c["wob"],
                     sim_real_chk=np.nanmean(real), sim_rand_chk=np.nanmean(rnd), first=days[0], split_after=days[nf - 1]))
    # every candidate on check (diagnostic only)
    for cr in C[C.setup == s].itertuples():
        lab = cr.tune
        if cr.kind == "gate":
            if lab == "refire off": keep = chk.nth == 1
            else:
                fe, op, q = lab.split()[:3]; q = float(q)
                keep = (chk[fe] >= q) if op == ">=" else (chk[fe] <= q)
            v = np.where(keep.fillna(True), chk.R, 0.0).sum()
        else:
            k = float(lab.split()[1].rstrip("xR")) if lab.startswith("target") else None
            ts = int(lab.split()[2]) if lab.startswith("time") else None
            rel = "parent" in lab
            v = sum(exit_variant(r, (k * r.tR if rel else k) if k else None, ts) for r in chk.itertuples())
        crow.append(dict(setup=s, tune=lab, eligible=cr.eligible, fit_gain=cr.fit_tot - cr.parent_fit_tot, chk_gain=v - chk.R.sum()))
D = pd.DataFrame(rows); D.to_csv(f"{S}/u7_parents.csv", index=False)
CC = pd.DataFrame(crow); CC.to_csv(f"{S}/u7_candidates_check_diag.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 40)
print(D.round(3).to_string())
e = CC[CC.eligible]
print("candidates", len(CC), "eligible", len(e), "improve check", (e.chk_gain > 0).sum(), "worse", (e.chk_gain < 0).sum(), "zero", (e.chk_gain == 0).sum())
print("corr fit_gain vs chk_gain (spearman)", round(e[["fit_gain", "chk_gain"]].corr("spearman").iloc[0, 1], 3))
pk = R.dropna(subset=["chk_diff_tot"])
print("fit-picked improve/worse:", (pk.chk_diff_tot > 0).sum(), (pk.chk_diff_tot < 0).sum(), (pk.chk_diff_tot == 0).sum(), "sum", round(pk.chk_diff_tot.sum(), 2))
med = e.groupby("setup").chk_gain.median(); print("median-candidate check gain sum", round(med.sum(), 2))
print(R[["setup", "tune", "var_fit_tot", "parent_fit_tot", "chk_diff_tot"]].round(2).to_string())
