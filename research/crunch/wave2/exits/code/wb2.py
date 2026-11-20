"""WB2 scoring for Y1-Y3 (replay-paired) and the SPY-exit read-out (live-paired). Educational only - not financial advice."""
import math, sys, numpy as np, pandas as pd
S = "<scratch>"
x = pd.read_pickle(f"{S}/scored.pkl"); rng = np.random.default_rng(20261119)
x["wk"] = pd.to_datetime(x.date).dt.to_period("W").astype(str)
def wob(df, col):
    d = df.groupby("date")[col].sum(); bd = d.idxmax(); nb = (df.date == bd).sum(); tot = d.sum()
    return ((tot - d.max()) / (len(df) - nb)), (d.max() / tot if tot > 0 else np.nan)
def cl(df, col):
    d = df.groupby("date")[col].agg(["sum", "size"]); n = d["size"].sum(); th = d["sum"].sum() / n; k = len(d)
    se = math.sqrt(k / (k - 1) * ((d["sum"] - d["size"] * th) ** 2).sum()) / n
    return th, se, n, k
print("parent eligibility (live R through 11-17):")
for s, g in x.groupby("s"):
    w, sh = wob(g, "R"); print(f"  {s}: n {len(g)} days {g.date.nunique()} avg {g.R.mean():+.3f} w/o best {w:+.3f} share {sh:.0%}")
def score(df, base, var, label, bar, elig):
    df = df.copy(); df["d"] = df[var] - df[base]
    rows = []; th, se = [], []
    for s in elig:
        g = df[df.s == s]; a, b, n, k = cl(g, "d"); th.append(a); se.append(b)
        pw, ps = wob(g, base); vw, vs = wob(g, var); dd = g.groupby("date").d.sum()
        rows.append(dict(cls=label, setup=s, n=n, days=k, par=g[base].mean(), par_wob=pw, par_sh=ps, var=g[var].mean(),
                         var_wob=vw, var_sh=vs, d=a, se=b, t=a / b, dtot=g.d.sum(), up=(g.d > 1e-9).sum(), dn=(g.d < -1e-9).sum(),
                         gain_bestday_sh=(dd.max() / dd.sum() if dd.sum() > 0 else np.nan), changed=(g.d.abs() > 1e-9).mean()))
    th, se = np.array(th), np.array(se); w = 1 / se ** 2; mfe = (w * th).sum() / w.sum(); Q = (w * (th - mfe) ** 2).sum()
    tau2 = max(0.0, (Q - (len(th) - 1)) / (w.sum() - (w ** 2).sum() / w.sum())) if len(th) > 1 else 0.0
    wr = 1 / (se ** 2 + tau2); mu = (wr * th).sum() / wr.sum(); semu = math.sqrt(1 / wr.sum())
    shr = mu + tau2 / (tau2 + se ** 2) * (th - mu)
    for r_, v in zip(rows, shr): r_["shrunk"] = v
    f = df[df.s.isin(elig)]; pm, pse, _, _ = cl(f, "d"); seu = max(semu, pse); t = mu / seu
    D = f.groupby("date").d.sum().to_numpy(); obs = D.mean(); null = (rng.choice([-1, 1], size=(10000, len(D))) * D).mean(1)
    p = ((null >= obs).sum() + 1) / 10001 if obs > 0 else ((null <= obs).sum() + 1) / 10001
    lw = np.array([f[f.wk != w_].d.mean() for w_ in sorted(f.wk.unique())]); lwp = np.mean(np.sign(lw) == np.sign(mu))
    pw, _ = wob(f, base); vw, vs = wob(f, var); dd = f.groupby("date").d.sum(); gsh = dd.max() / dd.sum() if dd.sum() > 0 else np.nan
    npos = int((shr > 0).sum())
    ok = dict(t=t >= bar, perm=(p < 0.01 and obs > 0), lowo=(lwp >= 0.75 and mu > 0), shrunk=(npos >= 2 and shr.min() >= -0.02) if len(elig) == 3 else (npos >= len(elig) and shr.min() >= -0.02),
              wob=vw >= pw, gainshare=(gsh < 0.5) if gsh == gsh else False)
    harm = t <= -bar or (p < 0.01 and obs < 0)
    verdict = "PASS" if all(ok.values()) else ("HARM" if harm else "FAIL (" + ",".join(k for k, v in ok.items() if not v) + ")")
    pool = dict(cls=label, n=len(f), days=f.date.nunique(), mu=mu, se_re=semu, tau=math.sqrt(tau2), d_cl=pm, se_cl=pse, t=t, perm=p,
                lowo_same_sign=lwp, nshr_pos=npos, worst_shr=shr.min(), par_wob=pw, var_wob=vw, var_sh=vs, gain_bestday_sh=gsh,
                dtot=f.d.sum(), verdict=verdict)
    return pool, rows
pd.set_option("display.width", 250)
ELIG = ["RW3", "RW5"]   # pre-registered rule on the LR8 basis: L3-rsi5hi w/o best day -0.003 -> not eligible
b = x[x.bars == True]
pools, rows = [], []
for c, lab in [("Y1", "Y1 target 1.25x"), ("Y2", "Y2 trail after +1R"), ("Y3", "Y3 target from fill")]:
    p_, r_ = score(b, "P", c, lab, max(1.5, math.sqrt(2 * math.log(9))), ELIG); pools.append(p_); rows += r_
    # calibrated-only robustness
    cal = b[((b.P - b.R).abs() <= 0.10) & (b.P_x == b.exit_reason)]
    p2, _ = score(cal, "P", c, lab + " [calibrated only]", max(1.5, math.sqrt(2 * math.log(9))), ELIG); pools.append(p2)
    p4, _ = score(b, "P", c, lab + " [3 setups incl. L3-rsi5hi]", max(1.5, math.sqrt(2 * math.log(9))), ["RW3", "RW5", "L3-rsi5hi"]); pools.append(p4)
    f = b[b.s.isin(ELIG)]; ds = sorted(f.date.unique()); h = ds[len(ds) // 2]
    print(lab, "halves (RW3+RW5): early %+.4f (%d tr), late %+.4f (%d tr)" % ((f[f.date < h][c] - f[f.date < h].P).mean(), (f.date < h).sum(), (f[f.date >= h][c] - f[f.date >= h].P).mean(), (f.date >= h).sum()))
    print(lab, "weekly mean delta:", (f[c] - f.P).groupby(f.wk).mean().round(3).to_dict())
    # descriptive: RW1 / RW7 (outside the eligibility rule; seen while running the replay)
    for s in ["RW1", "RW7"]:
        g = b[b.s == s].copy(); g["d"] = g[c] - g.P; a, se_, n, k = cl(g, "d")
        rows.append(dict(cls=lab + " [descriptive]", setup=s, n=n, days=k, par=g.P.mean(), var=g[c].mean(), d=a, se=se_, t=a / se_,
                         dtot=g.d.sum(), up=(g.d > 1e-9).sum(), dn=(g.d < -1e-9).sum()))
PO = pd.DataFrame(pools); RO = pd.DataFrame(rows)
print(PO.round(4).to_string()); print(RO.round(4).to_string())
# exit mix
for c in ["P", "Y1", "Y2", "Y3"]:
    print(c, b[b.s.isin(ELIG)][c + "_x"].value_counts().to_dict())
# SPY exit read-out
sp = x[x.s.isin(["RW3", "RW5"]) & x.spy_bars]
p3, r3 = score(sp, "R", "SPYX", "SPY-since-entry exit (RW3 0.30 / RW5 0.40)", 1.5, ["RW3", "RW5"])
print(pd.DataFrame([p3]).round(4).to_string()); print(pd.DataFrame(r3).round(4).to_string())
PO.to_csv(f"{S}/pooled.csv", index=False); RO.to_csv(f"{S}/per_setup.csv", index=False)
pd.DataFrame([p3]).to_csv(f"{S}/spy_pooled.csv", index=False); pd.DataFrame(r3).to_csv(f"{S}/spy_per_setup.csv", index=False)
