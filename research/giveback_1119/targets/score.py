"""Targets class scoring (PLAN.md): per family-side fit selection, check scored once; book-wide configs; live descriptive.
Usage: python score.py LAB.parquet LIVE.parquet OUTDIR. Educational only - not financial advice."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "map"))
from common import dstat
LAB, LIVE, OUT = sys.argv[1:4]
CF = ["C1", "C2", "C3", "C4", "C5", "C6"]
NAME = dict(C1="PART06", C2="PART08", C3="CAP10", C4="CAP15", C5="NOTGT-EOD", C6="NOTGT-120")
X = pd.read_parquet(LAB)
X["date"] = pd.to_datetime(X.date).dt.date
assert not ((X.date >= pd.Timestamp("2024-11-01").date()) & (X.date <= pd.Timestamp("2025-02-28").date())).any()
X["family"] = np.where(X.setup.str.startswith("GEN"), "GEN", X.setup.str.split("-").str[0])
X["fs"] = X.family + np.where(X.side > 0, " long", " short")
SPLIT = pd.Timestamp("2025-09-30").date(); X["half"] = np.where(X.date <= SPLIT, "fit", "check")
for c in CF: X["d" + c] = (X[c] - X.P).astype(float)
X["P"] = X.P.astype(float)
F, K = X[X.half == "fit"], X[X.half == "check"]
print("lab trades", len(X), "fit", len(F), F.date.nunique(), "check", len(K), K.date.nunique(), "family-sides", X.fs.nunique(), "setups", X.setup.nunique())
def gstat(g, col):
    s = dstat(g.assign(r=g[col]))
    day = g.groupby("date")[col].sum(); tot = day.sum()
    return dict(n=len(g), changed=int((g[col] != 0).sum()), tot=tot, t=s.get("t", np.nan), wo_best=tot - day.max() if len(day) else np.nan,
                best_share=day.max() / tot if tot > 0 else np.nan)
# ---- fit selection
sel = []
for fs, g in F.groupby("fs"):
    for c in CF:
        st = gstat(g, "d" + c); st.update(fs=fs, cfg=c)
        st["ok"] = bool(st["tot"] > 0 and st["t"] >= 2.0 and st["wo_best"] > 0 and st["changed"] >= 100); sel.append(st)
S = pd.DataFrame(sel); S.to_csv(f"{OUT}/data/fit_grid.csv", index=False, float_format="%.4f")
NF = X.fs.nunique(); NCFG = len(CF) * NF + len(CF)
adopt = {}
for fs, g in S.groupby("fs"):
    gg = g[g.ok]
    if len(gg): adopt[fs] = gg.sort_values("tot").iloc[-1].cfg
print("adopted", adopt)
# ---- check, adopted book
K = K.copy(); K["new"] = K.P
for fs, c in adopt.items(): K.loc[K.fs == fs, "new"] = K.loc[K.fs == fs, c]
K["dd"] = K.new - K.P
b0, b1 = dstat(K.assign(r=K.P)), dstat(K.assign(r=K.new)); bd = gstat(K, "dd")
fam = []
for fs, g in K.groupby("fs"):
    st = gstat(g, "dd"); fam.append(dict(fs=fs, cfg=NAME.get(adopt.get(fs), "-"), n=len(g), changed=st["changed"], dR=st["tot"], t=st["t"]))
FAM = pd.DataFrame(fam)
setd = K[K.fs.isin(adopt)].groupby("setup").dd.sum()
summ = dict(N_family_sides=NF, configs_class=NCFG, adopted={k: NAME[v] for k, v in adopt.items()},
            check=dict(base_tot=K.P.sum(), new_tot=K.new.sum(), base_avg=b0["mean"], new_avg=b1["mean"], base_wo=b0["wo_best"], new_wo=b1["wo_best"],
                       d_tot=bd["tot"], d_t=bd["t"], best_share=bd["best_share"], changed=bd["changed"],
                       fam_better=int((FAM.dR > 1e-9).sum()), fam_worse=int((FAM.dR < -1e-9).sum()),
                       set_better=int((setd > 1e-9).sum()), set_worse=int((setd < -1e-9).sum())))
FAM.to_csv(f"{OUT}/data/check_adopted_family.csv", index=False, float_format="%.4f")
setd.rename("dR").to_csv(f"{OUT}/data/check_adopted_setup.csv", float_format="%.4f")
# fit-best of every family on check (diagnostic)
diag = []
for fs, g in S.groupby("fs"):
    best = g.sort_values("tot").iloc[-1]; gk = K[K.fs == fs]
    st = gstat(gk, "d" + best.cfg)
    diag.append(dict(fs=fs, fit_best=NAME[best.cfg], fit_tot=best.tot, fit_t=best.t, adopted=fs in adopt, check_dR=st["tot"], check_t=st["t"], check_n=len(gk)))
DG = pd.DataFrame(diag); DG.to_csv(f"{OUT}/data/fitbest_on_check.csv", index=False, float_format="%.4f")
# ---- book-wide configs, both halves
bw = []; bwf = []
for c in CF:
    for h, g in (("fit", F), ("check", K)):
        st = gstat(g, "d" + c); s1 = dstat(g.assign(r=g[c].astype(float)))
        per = g.groupby("fs")["d" + c].sum(); pers = g.groupby("setup")["d" + c].sum()
        bw.append(dict(cfg=NAME[c], half=h, n=st["n"], changed=st["changed"], dR=st["tot"], d_avg=st["tot"] / st["n"], t=st["t"],
                       best_share=st["best_share"], wo_best_after=s1["wo_best"], fam_b=int((per > 1e-9).sum()), fam_w=int((per < -1e-9).sum()),
                       fam_bR=per[per > 0].sum(), fam_wR=per[per < 0].sum(), set_b=int((pers > 1e-9).sum()), set_w=int((pers < -1e-9).sum())))
        if h == "check":
            for fs, v in per.items(): bwf.append(dict(cfg=NAME[c], fs=fs, dR=v, n=int((g.fs == fs).sum())))
BW = pd.DataFrame(bw); BW.to_csv(f"{OUT}/data/bookwide.csv", index=False, float_format="%.4f")
pd.DataFrame(bwf).pivot(index="fs", columns="cfg", values="dR").to_csv(f"{OUT}/data/bookwide_check_family.csv", float_format="%.2f")
# far-target subset (t1s05 / tgt > 1): caps C3/C4 and partials
far = K[K.tgtR > 1.0]
summ["check_far_target"] = {NAME[c]: dict(n=len(far), dR=far["d" + c].sum(), t=dstat(far.assign(r=far["d" + c]))["t"]) for c in CF}
summ["check_base_stats"] = dict(base=b0, new=b1)
# ---- live descriptive
L = pd.read_parquet(LIVE); L = L[L.P.notna()].copy()
L["half"] = np.where(L.date <= "2026-10-31", "fit", "check"); L["fs"] = L.family + np.where(L.side > 0, " long", " short")
L["gen"] = L.family == "GEN"
lv = []
for c in CF:
    L["d" + c] = L[c] - L.P
    for h, g in L.groupby("half"):
        for gen, gg in g.groupby("gen"):
            if gen and c not in ("C1", "C2"): continue
            st = gstat(gg, "d" + c); per = gg.groupby("fs")["d" + c].sum()
            lv.append(dict(cfg=NAME[c], half=h, gen_hold=gen, n=len(gg), changed=st["changed"], dR=st["tot"], t=st["t"],
                           fam_b=int((per > 1e-9).sum()), fam_w=int((per < -1e-9).sum())))
LV = pd.DataFrame(lv); LV.to_csv(f"{OUT}/data/live.csv", index=False, float_format="%.4f")
calib = dict(n=len(L), within010=float(((L.P - L.R).abs() <= 0.10).mean()), mean_diff=float((L.P - L.R).mean()))
summ["live_calib"] = calib
# live far-target setups
lf = L[(L.tgtR > 1.2) & ~L.gen]
summ["live_far"] = {NAME[c]: dict(n=len(lf), dR=float(lf["d" + c].sum()), t=dstat(lf.assign(r=lf["d" + c]))["t"]) for c in CF}
json.dump(summ, open(f"{OUT}/data/summary.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250)
print(json.dumps(summ, indent=1, default=float)); print(BW.to_string()); print(DG.to_string()); print(FAM[FAM.cfg != "-"].to_string()); print(LV.to_string())
