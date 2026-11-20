"""Time-in-trade exits per family (PLAN.md). Usage: python score.py LAB.parquet LIVE.parquet OUTDIR
Educational only - not financial advice."""
import sys, json, itertools, numpy as np, pandas as pd
LAB, LIVE, OUT = sys.argv[1:4]
TS = (15, 30, 45, 60, 90, 120)
GRID = [("A", T, m, r) for T in TS for m in (.25, .5) for r in (-.25, 0, .25)] + \
       [("B", T, m, r) for T in TS for m in (.5, .8, 1.0) for r in (0, .25)]
assert len(GRID) == 72
cols = ["setup", "side", "date", "fin"] + [f"{k}{t}" for t in TS for k in ("mk", "mf", "rem")]
X = pd.read_parquet(LAB, columns=cols)
X["date"] = pd.to_datetime(X.date).dt.date
LK0, LK1, SPLIT = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date(), pd.Timestamp("2025-09-30").date()
assert not ((X.date >= LK0) & (X.date <= LK1)).any()
X["family"] = np.where(X.setup.str.startswith("GEN"), "GEN", X.setup.str.split("-").str[0])
X["fs"] = X.family + np.where(X.side > 0, " long", " short")
X["fit"] = X.date <= SPLIT
X["dc"] = pd.factorize(X.date)[0]

def fire(df, cfg, pre=""):
    c, T, m, r = cfg
    mk, mf = df[f"{pre}mk{T}"].to_numpy(), df[f"{pre}mf{T}"].to_numpy()
    f = (mf < m) & (mk < r) if c == "A" else (mf >= m) & (mk <= r)
    return f & ~np.isnan(mk)

def delta(df, cfg, rem="rem"):
    f = fire(df, cfg); d = np.where(f, -df[f"{rem}{cfg[1]}"].to_numpy(), 0.0)
    return np.nan_to_num(d), f

def cstat(d, dc):
    """mean, day-clustered t, w/o best day mean, best-day share of total."""
    n = len(d)
    if n < 2: return np.nan, np.nan, np.nan, np.nan
    u, inv = np.unique(dc, return_inverse=True)
    s = np.bincount(inv, d); k = np.bincount(inv); mu = d.mean()
    se = np.sqrt(((s - k * mu) ** 2).sum()) / n
    b = s.argmax(); tot = s.sum()
    return mu, (mu / se if se > 0 else np.nan), (tot - s[b]) / max(1, n - k[b]), (s[b] / tot if tot else np.nan)

# ---- fit-half selection per family-side
F = X[X.fit]; C = X[~X.fit]
sel, alltab = {}, []
for fs, g in F.groupby("fs"):
    best = None
    for cfg in GRID:
        d, f = delta(g, cfg)
        mu, t, wo, sh = cstat(d, g.dc.to_numpy())
        row = dict(fs=fs, cls=cfg[0], T=cfg[1], m=cfg[2], r=cfg[3], n=len(g), fires=int(f.sum()), tot=d.sum(), mu=mu, t=t, wo=wo)
        alltab.append(row)
        if best is None or row["tot"] > best["tot"]: best = row
    ok = best["mu"] > 0 and best["t"] >= 2.0 and best["wo"] > 0 and best["fires"] >= 100
    best["adopt"] = bool(ok); sel[fs] = best
pd.DataFrame(alltab).to_csv(f"{OUT}/fit_grid.csv.gz", index=False, float_format="%.5f")
S = pd.DataFrame(sel.values())
print(S[["fs", "cls", "T", "m", "r", "n", "fires", "tot", "mu", "t", "wo", "adopt"]].to_string())

# secondary: one book-wide config per class, chosen on fit
sec = {}
for c in "AB":
    rows = []
    for cfg in [g for g in GRID if g[0] == c]:
        d, f = delta(F, cfg); mu, t, wo, sh = cstat(d, F.dc.to_numpy()); rows.append((d.sum(), cfg, mu, t, wo))
    rows.sort(key=lambda z: -z[0]); sec[c] = rows[0]
    print("secondary fit best", c, rows[0][1], f"tot {rows[0][0]:.1f} mu {rows[0][2]:.4f} t {rows[0][3]:.2f}")

# ---- check half, scored once
def apply(df, rem="rem"):
    d = np.zeros(len(df)); f = np.zeros(len(df), bool)
    for fs, b in sel.items():
        if not b["adopt"]: continue
        m = (df.fs == fs).to_numpy(); cfg = (b["cls"], b["T"], b["m"], b["r"])
        dd, ff = delta(df[m], cfg, rem); d[m] = dd; f[m] = ff
    return d, f
res = {}
dC, fC = apply(C); C = C.assign(delta=dC, fired=fC, new=C.fin.to_numpy() + dC)
mu, t, wo, sh = cstat(dC, C.dc.to_numpy())
b0 = cstat(C.fin.to_numpy(), C.dc.to_numpy()); b1 = cstat(C.new.to_numpy(), C.dc.to_numpy())
res["check"] = dict(n=len(C), sessions=int(C.date.nunique()), fired=int(fC.sum()), base_tot=float(C.fin.sum()), new_tot=float(C.new.sum()),
                    base_avg=b0[0], new_avg=b1[0], base_wo=b0[2], new_wo=b1[2], d_tot=float(dC.sum()), d_avg=mu, d_t=t, d_wo=wo, d_bestshare=sh)
dF, fF = apply(F); mF = cstat(dF, F.dc.to_numpy())
res["fit"] = dict(n=len(F), fired=int(fF.sum()), d_tot=float(dF.sum()), d_avg=mF[0], d_t=mF[1])
for c, (tot, cfg, *_ ) in sec.items():
    d, f = delta(C, cfg); m_ = cstat(d, C.dc.to_numpy())
    res[f"secondary_{c}"] = dict(cfg=list(cfg), fit_tot=tot, check_fired=int(f.sum()), check_tot=float(d.sum()), check_avg=m_[0], check_t=m_[1], check_wo=m_[2], check_bestshare=m_[3])
# per family-side and per setup on check (adopted only)
fam = []
for fs, b in sel.items():
    g = C[C.fs == fs]; mm = cstat(g.delta.to_numpy(), g.dc.to_numpy())
    fam.append(dict(fs=fs, adopt=b["adopt"], rule=f'{b["cls"]} T{b["T"]} m{b["m"]} r{b["r"]}', fit_t=b["t"], fit_tot=b["tot"], check_n=len(g),
                    check_fired=int(g.fired.sum()), check_dtot=g.delta.sum(), check_davg=mm[0], check_t=mm[1], base_avg=g.fin.mean()))
FAM = pd.DataFrame(fam); FAM.to_csv(f"{OUT}/family_check.csv", index=False, float_format="%.5f")
SET = C[C.fs.isin([k for k, b in sel.items() if b["adopt"]])].groupby(["fs", "setup"]).agg(n=("fin", "size"), fired=("fired", "sum"),
      base_avg=("fin", "mean"), dtot=("delta", "sum"), davg=("delta", "mean")).reset_index()
SET.to_csv(f"{OUT}/setup_check.csv", index=False, float_format="%.5f")
# check-half: what the fit-chosen config would have done for NON-adopted families (diagnostic only, not part of the rule)
diag = []
for fs, b in sel.items():
    g = C[C.fs == fs]; d, f = delta(g, (b["cls"], b["T"], b["m"], b["r"])); diag.append(dict(fs=fs, adopt=b["adopt"], dtot=d.sum(), davg=d.mean()))
pd.DataFrame(diag).to_csv(f"{OUT}/family_check_all_bestfit.csv", index=False, float_format="%.5f")

# ---- live, descriptive
P = pd.read_parquet(LIVE)
P = P.sort_values("account").drop_duplicates(["strategy", "symbol", "m_in", "date"])
P = P[P.mfe_b.notna()].copy()
P["fs"] = P.family + np.where(P.side > 0, " long", " short"); P["fin"] = P.R
P["dc"] = pd.factorize(P.date)[0]
dL, fL = apply(P); P = P.assign(delta=dL, fired=fL)
mL = cstat(dL, P.dc.to_numpy())
res["live"] = dict(n=len(P), sessions=int(P.date.nunique()), fired=int(fL.sum()), base_tot=float(P.R.sum()), d_tot=float(dL.sum()), d_avg=mL[0], d_t=mL[1], d_wo=mL[2], d_bestshare=mL[3])
LF = P[P.fs.isin([k for k, b in sel.items() if b["adopt"]])].groupby("fs").agg(n=("R", "size"), fired=("fired", "sum"), base_avg=("R", "mean"),
      dtot=("delta", "sum"), davg=("delta", "mean")).reset_index()
LF.to_csv(f"{OUT}/live_family.csv", index=False, float_format="%.5f")
for c, (tot, cfg, *_ ) in sec.items():
    d, f = delta(P, cfg); m_ = cstat(d, P.dc.to_numpy())
    res[f"live_secondary_{c}"] = dict(cfg=list(cfg), fired=int(f.sum()), dtot=float(d.sum()), davg=m_[0], t=m_[1])
json.dump(res, open(f"{OUT}/summary.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
print(FAM.to_string()); print(SET.to_string()); print(LF.to_string())
