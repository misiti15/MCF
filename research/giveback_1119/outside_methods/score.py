"""Score the outside exit classes (PLAN.md): per class, per family-side fit selection with gates, check half once.
Usage: python score.py WALK.parquet OUTDIR. Educational only - not financial advice."""
import sys, json, math, numpy as np, pandas as pd
WALK, OUT = sys.argv[1:3]
X = pd.read_parquet(WALK)
X["date"] = pd.to_datetime(X.date).dt.date
LK0, LK1, SPLIT = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date(), pd.Timestamp("2025-09-30").date()
assert not ((X.date >= LK0) & (X.date <= LK1)).any()
NAMES = [c for c in X.columns if c[:2] in ("O1", "O2", "O3", "O4")]
assert len(NAMES) == 22
X["family"] = np.where(X.setup.str.startswith("GEN"), "GEN", X.setup.str.split("-").str[0])
X["fs"] = X.family + np.where(X.side > 0, " long", " short")
X["fit"] = X.date <= SPLIT; X["dc"] = pd.factorize(X.date)[0]
NFS = X.fs.nunique(); N_CLASS = 22 * NFS + 22; N_LIN = 916 + 2664 + 16 + N_CLASS
BAR = max(1.5, math.sqrt(2 * math.log(N_LIN)))


def cstat(d, dc):
    n = len(d)
    if n < 2: return dict(mu=np.nan, t=np.nan, wo=np.nan, sh=np.nan)
    u, inv = np.unique(dc, return_inverse=True); s = np.bincount(inv, d); k = np.bincount(inv); mu = d.mean()
    se = np.sqrt(((s - k * mu) ** 2).sum()) / n; b = s.argmax(); tot = s.sum()
    return dict(mu=mu, t=mu / se if se > 0 else np.nan, wo=(tot - s[b]) / max(1, n - k[b]), sh=s[b] / tot if tot else np.nan)


F, C = X[X.fit], X[~X.fit]
print(f"trades {len(X)} fit {len(F)} ({F.date.nunique()} s) check {len(C)} ({C.date.nunique()} s); family-sides {NFS}; "
      f"N_class {N_CLASS} N_lineage {N_LIN} bar {BAR:.2f}; base fit avg {F.base.mean():.4f} check avg {C.base.mean():.4f}; "
      f"engine corr vs 5-min list r {X.base.corr(X.r5):.3f}")
# book-wide fit/check table of every config (descriptive; selection uses fit only)
allc = []
for nm in NAMES:
    sf, sc = cstat(F[nm].to_numpy(float), F.dc.to_numpy()), cstat(C[nm].to_numpy(float), C.dc.to_numpy())
    allc.append(dict(config=nm, fit_tot=F[nm].sum(), fit_avg=sf["mu"], fit_t=sf["t"], changed_fit=int((F[nm] != 0).sum()),
                     fam_fit_better=int((F.groupby("fs")[nm].sum() > 0).sum()), fam_fit_worse=int((F.groupby("fs")[nm].sum() < 0).sum())))
ALL = pd.DataFrame(allc); ALL.to_csv(f"{OUT}/book_fit_all_configs.csv", index=False, float_format="%.5f")
print(ALL.to_string())
res = dict(N_class=N_CLASS, N_lineage=N_LIN, bar=BAR, fit_trades=len(F), check_trades=len(C), fit_sessions=int(F.date.nunique()),
           check_sessions=int(C.date.nunique()), base_check_tot=float(C.base.sum()), base_check_avg=float(C.base.mean()))
famrows, setrows, selrows = [], [], []
for cls in ("O1", "O2", "O3", "O4"):
    cn = [n for n in NAMES if n.startswith(cls)]
    sel = {}
    for fs, g in F.groupby("fs"):
        best = None
        for nm in cn:
            d = g[nm].to_numpy(float); st = cstat(d, g.dc.to_numpy())
            row = dict(cls=cls, fs=fs, config=nm, n=len(g), changed=int((d != 0).sum()), tot=d.sum(), **{f"fit_{k}": v for k, v in st.items()})
            if best is None or row["tot"] > best["tot"]: best = row
        best["adopt"] = bool(best["fit_mu"] > 0 and best["fit_t"] >= 2.0 and best["fit_wo"] > 0 and best["changed"] >= 100)
        sel[fs] = best; selrows.append(best)
    d = np.zeros(len(C))
    for fs, b in sel.items():
        if b["adopt"]:
            m = (C.fs == fs).to_numpy(); d[m] = C.loc[m, b["config"]].to_numpy(float)
    Cc = C.assign(delta=d, new=C.base.to_numpy() + d)
    sd = cstat(d, Cc.dc.to_numpy()); s0 = cstat(Cc.base.to_numpy(float), Cc.dc.to_numpy()); s1 = cstat(Cc.new.to_numpy(float), Cc.dc.to_numpy())
    adopted = [k for k, b in sel.items() if b["adopt"]]
    fam = Cc[Cc.fs.isin(adopted)].groupby("fs").agg(n=("base", "size"), changed=("delta", lambda v: int((v != 0).sum())), base_avg=("base", "mean"),
                                                    dtot=("delta", "sum"), davg=("delta", "mean")).reset_index()
    fam["rule"] = fam.fs.map(lambda k: sel[k]["config"]); fam["fit_t"] = fam.fs.map(lambda k: sel[k]["fit_t"]); fam["cls"] = cls
    famrows.append(fam)
    se = Cc[Cc.fs.isin(adopted)].groupby(["fs", "setup"]).agg(n=("base", "size"), base_avg=("base", "mean"), dtot=("delta", "sum"), davg=("delta", "mean")).reset_index()
    se["cls"] = cls; setrows.append(se)
    # far-target pocket (t1s05) inside the adopted rule
    ft = Cc[Cc.geom == "t1s05"]
    # secondary: book-wide config chosen on fit
    sb = max(cn, key=lambda nm: F[nm].sum()); dsec = C[sb].to_numpy(float); ssec = cstat(dsec, C.dc.to_numpy())
    fsec = C.groupby("fs")[sb].sum(); ssetup = C.groupby("setup")[sb].sum()
    # diagnostic: each family's fit-best config of this class applied regardless of gates
    dg = np.zeros(len(C))
    for fs, b in sel.items():
        m = (C.fs == fs).to_numpy(); dg[m] = C.loc[m, b["config"]].to_numpy(float)
    fdg = pd.Series(dg, index=C.index).groupby(C.fs).sum()
    r = dict(adopted=len(adopted), adopted_fs=adopted, check_changed=int((d != 0).sum()), base_tot=float(Cc.base.sum()), new_tot=float(Cc.new.sum()),
             d_tot=float(d.sum()), base_avg=s0["mu"], new_avg=s1["mu"], d_avg=sd["mu"], d_t=sd["t"], base_wo=s0["wo"], new_wo=s1["wo"],
             d_bestshare=sd["sh"], fam_better=int((fam.dtot > 0).sum()), fam_worse=int((fam.dtot < 0).sum()),
             fam_better_R=float(fam.dtot[fam.dtot > 0].sum()), fam_worse_R=float(fam.dtot[fam.dtot < 0].sum()),
             setup_better=int((se.dtot > 0).sum()), setup_worse=int((se.dtot < 0).sum()),
             setup_better_R=float(se.dtot[se.dtot > 0].sum()), setup_worse_R=float(se.dtot[se.dtot < 0].sum()),
             t1s05_n=len(ft), t1s05_dtot=float(ft.delta.sum()),
             fit_adopted_dtot=float(sum(b["tot"] for b in sel.values() if b["adopt"])),
             secondary=dict(config=sb, fit_tot=float(F[sb].sum()), check_tot=float(dsec.sum()), check_avg=ssec["mu"], check_t=ssec["t"],
                            check_wo_delta=ssec["wo"], fam_better=int((fsec > 0).sum()), fam_worse=int((fsec < 0).sum()),
                            setup_better=int((ssetup > 0).sum()), setup_worse=int((ssetup < 0).sum()),
                            t1s05_check_tot=float(C.loc[C.geom == "t1s05", sb].sum())),
             diag_allfam=dict(dtot=float(dg.sum()), fam_better=int((fdg > 0).sum()), fam_worse=int((fdg < 0).sum()),
                              better_R=float(fdg[fdg > 0].sum()), worse_R=float(fdg[fdg < 0].sum())))
    r["pass"] = bool(r["d_tot"] > 0 and r["d_avg"] > 0 and r["new_wo"] >= r["base_wo"] and (r["d_bestshare"] < 0.5) and
                     r["fam_better"] > r["fam_worse"] and r["setup_better"] > r["setup_worse"] and (r["d_t"] or 0) >= BAR)
    res[cls] = r
    print(f"\n=== {cls}: adopted {adopted}\n{fam.to_string()}\n{json.dumps(r, indent=1, default=float)}")
pd.DataFrame(selrows).to_csv(f"{OUT}/fit_selection.csv", index=False, float_format="%.5f")
pd.concat(famrows).to_csv(f"{OUT}/family_check.csv", index=False, float_format="%.5f")
pd.concat(setrows).to_csv(f"{OUT}/setup_check.csv", index=False, float_format="%.5f")
# far-target pocket view (descriptive, check half): every config on t1s05 trades and on the four map pocket setups
P4 = ["CWT09-gapdn-vwaploss-g5-short", "MF1-945-flowsell-vwapup-FD", "MF2-open-rsimidhi-flowsell-FD", "CWT12-coil-k6-long"]
pk = []
for nm in NAMES:
    for lab, m in (("t1s05 all", C.geom == "t1s05"), ("4 map pocket setups", C.setup.isin(P4)), ("t1s1 all", C.geom == "t1s1")):
        g = C[m]; st = cstat(g[nm].to_numpy(float), g.dc.to_numpy()) if len(g) > 1 else dict(mu=np.nan, t=np.nan)
        gf = F[(F.geom == "t1s05") if lab == "t1s05 all" else (F.setup.isin(P4) if lab.startswith("4") else F.geom == "t1s1")]
        pk.append(dict(group=lab, config=nm, n=len(g), base_avg=g.base.mean(), fit_dtot=gf[nm].sum(), check_dtot=g[nm].sum(), check_davg=st["mu"], check_t=st["t"]))
pd.DataFrame(pk).to_csv(f"{OUT}/pocket_check.csv", index=False, float_format="%.5f")
json.dump(res, open(f"{OUT}/summary.json", "w"), indent=1, default=float)
print("Educational only - not financial advice.")
