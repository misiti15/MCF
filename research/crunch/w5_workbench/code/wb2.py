"""W5 Part D: WB2 scoring (paired, pooled random-effects, EB shrinkage, sign-flip, leave-week-out, mSPRT) and the old
fit/check protocol on the same data. Educational only - not financial advice."""
import math, numpy as np, pandas as pd
S = "<scratch>"
x = pd.read_pickle(f"{S}/demo_scored.pkl")
BAR = max(1.5, math.sqrt(2 * math.log(15))); rng = np.random.default_rng(20261118)
CL = {"X1": "target 0.75x", "X2": "BE after +0.5R", "X3": "60-min stop if MFE<0.25R"}
x["wk"] = pd.to_datetime(x.date).dt.to_period("W").astype(str)
out = []
def p(*a):
    s = " ".join(str(v) for v in a); print(s); out.append(s)
def cl_stats(df, col):
    d = df.groupby("date")[col].agg(["sum", "size"]); n = d["size"].sum(); th = d["sum"].sum() / n; k = len(d)
    se = math.sqrt(k / (k - 1) * ((d["sum"] - d["size"] * th) ** 2).sum()) / n if k > 1 else np.nan
    return th, se, n, k
def wob(df, col):
    d = df.groupby("date")[col].sum(); bd = d.idxmax(); nb = (df.date == bd).sum()
    tot = d.sum(); return ((tot - d.max()) / (len(df) - nb) if len(df) > nb else np.nan), (d.max() / tot if tot > 0 else np.nan)
def msprt(xs, sig2, tau2):
    """normal-mixture SPRT e-value path for H0 mean 0 (two-sided), plug-in variance."""
    e = []; s = 0.0
    for i, v in enumerate(xs, 1):
        s += v; xb = s / i
        e.append(math.sqrt(sig2 / (sig2 + i * tau2)) * math.exp(i * i * tau2 * xb * xb / (2 * sig2 * (sig2 + i * tau2))))
    return np.array(e)
rows, prow = [], []
for k, name in CL.items():
    c = "d" + k
    th, se, ns, ks, names = [], [], [], [], []
    for s, g in x.groupby("s"):
        a, b, n, kk = cl_stats(g, c); th.append(a); se.append(b); ns.append(n); ks.append(kk); names.append(s)
        pw, psh = wob(g, "R"); vw, vsh = wob(g, k)
        rows.append(dict(cls=k, tune=name, setup=s, n=n, days=kk, parent_avg=g.R.mean(), parent_wob=pw, parent_bsh=psh,
                         var_avg=g[k].mean(), var_wob=vw, var_bsh=vsh, d_avg=a, d_se=b, d_t=a / b if b else np.nan,
                         d_total=g[c].sum(), changed=(g[c].abs() > 1e-9).mean()))
    th, se = np.array(th), np.array(se); w = 1 / se ** 2
    mu_fe = (w * th).sum() / w.sum(); Q = (w * (th - mu_fe) ** 2).sum(); df_ = len(th) - 1
    tau2 = max(0.0, (Q - df_) / (w.sum() - (w ** 2).sum() / w.sum()))
    wr = 1 / (se ** 2 + tau2); mu = (wr * th).sum() / wr.sum(); se_mu = math.sqrt(1 / wr.sum())
    B = tau2 / (tau2 + se ** 2); shr = mu + B * (th - mu)
    for nm, sv in zip(names, shr): [r.update(shrunk=sv) for r in rows if r["cls"] == k and r["setup"] == nm]
    # day-clustered pooled (robust to cross-setup same-day correlation)
    pm, pse, pn, pk = cl_stats(x, c)
    se_use = max(se_mu, pse); t = mu / se_use
    # sign-flip on pooled daily sums
    D = x.groupby("date")[c].sum().to_numpy(); obs = D.mean()
    flips = rng.choice([-1, 1], size=(10000, len(D))); null = (flips * D).mean(1)
    pval = ((null >= obs).sum() + 1) / 10001 if obs > 0 else ((null <= obs).sum() + 1) / 10001
    # leave-one-week-out
    lw = [x[x.wk != w_][c].mean() for w_ in sorted(x.wk.unique())]
    lw_pos = np.mean(np.array(lw) > 0)
    # mSPRT on pooled daily mean delta per trade (days in order)
    dd = x.groupby("date")[c].mean().sort_index()
    sig2 = dd.var(); tau2m = (0.05) ** 2      # mixture scale ~ the +0.05R effect size of interest
    e = msprt(dd.to_numpy(), sig2, tau2m); hit = np.argmax(e >= 20) if (e >= 20).any() else -1
    seq = f"e>=20 at session {hit+1} ({dd.index[hit]}), running mean then {dd.iloc[:hit+1].mean():+.3f}" if hit >= 0 else f"no crossing in {len(dd)} sessions (max e {e.max():.1f})"
    # pooled variant vs parent w/o best day
    pw, _ = wob(x, "R"); vw, vsh = wob(x, k)
    n_pos = int((shr > 0).sum()); worst = shr.min()
    passes = dict(t=t >= BAR, perm=pval < 0.01, shrunk=(n_pos >= 4 and worst >= -0.02), lowo=lw_pos >= 0.75, wob=vw >= pw)
    prow.append(dict(cls=k, tune=name, mu_RE=mu, se_RE=se_mu, tau=math.sqrt(tau2), mu_dayclustered=pm, se_dayclustered=pse,
                     t=t, perm_p=pval, lowo_pos=lw_pos, n_shrunk_pos=n_pos, worst_shrunk=worst, parent_wob=pw, var_wob=vw,
                     var_bsh=vsh, sd_d=x[c].std(), seq=seq, verdict="PASS" if all(passes.values()) else
                     "FAIL (" + ", ".join(kk for kk, v in passes.items() if not v) + ")"))
R = pd.DataFrame(rows); PR = pd.DataFrame(prow)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
p(f"WB2 demo: {len(x)} trades, {x.date.nunique()} sessions {x.date.min()}..{x.date.max()}, bars for {int(x.bars.sum())}; bar t {BAR:.2f}")
p(PR.round(4).to_string()); p(R.round(4).to_string())
# old protocol: per setup choose best class on its fit half, score on check half
old = []
for s, g in x.groupby("s"):
    ds = sorted(g.date.unique()); h = ds[len(ds) // 2]; f, ck = g[g.date < h], g[g.date >= h]
    fg = {k: f["d" + k].sum() for k in CL}; kb = max(fg, key=fg.get)
    chk = {k: ck["d" + k].sum() for k in CL}
    old.append(dict(setup=s, split=h, fit_gains=" ".join(f"{k}:{v:+.1f}" for k, v in fg.items()), chosen=kb if fg[kb] > 0 else "none",
                    chk_of_chosen=chk[kb] if fg[kb] > 0 else 0.0, chk_gains=" ".join(f"{k}:{v:+.1f}" for k, v in chk.items())))
O = pd.DataFrame(old); p("\nOld protocol (fit half -> check half):"); p(O.round(2).to_string())
R.to_csv(f"{S}/D_per_setup.csv", index=False); PR.to_csv(f"{S}/D_pooled.csv", index=False); O.to_csv(f"{S}/D_oldprotocol.csv", index=False)
# per-setup improve/worsen per class (raw and shrunk)
p("\nimprove/worsen per class (raw total delta):")
for k in CL:
    g = R[R.cls == k]; p(f"  {k}: improve {int((g.d_total>0).sum())} ({g.d_total[g.d_total>0].sum():+.1f}R) worse {int((g.d_total<0).sum())} ({g.d_total[g.d_total<0].sum():+.1f}R)")
open(f"{S}/D_out.txt", "w").write("\n".join(out))
