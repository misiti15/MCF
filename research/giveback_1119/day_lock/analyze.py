"""Score the day-lock grid (PLAN.md + addendum A). Usage: python analyze.py OUTDIR TABLES.md. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
O, MD = sys.argv[1], sys.argv[2]
D = pd.read_csv(f"{O}/days.csv"); L = pd.read_csv(f"{O}/lots.csv")
D["half"] = np.where(D.date <= "2026-10-31", "fit", "check"); L["half"] = np.where(L.date <= "2026-10-31", "fit", "check")
D["delta"] = D.new - D.base; D["excess"] = np.where(D.fired, D.delta - D.placebo.fillna(0), 0.0)
N_CLASS = 16; BAR16 = max(1.5, np.sqrt(2 * np.log(16))); BAR200 = max(1.5, np.sqrt(2 * np.log(200)))
def tstat(v):
    v = np.asarray(v, float); return v.mean() / (v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 2 and v.std(ddof=1) > 0 else np.nan
def wobest(x, col, ncol):
    g = x.groupby("date")[[col, ncol]].sum(); b = g[col].idxmax(); return (g[col].sum() - g.loc[b, col]) / max(1, g[ncol].sum() - g.loc[b, ncol])
rows = []
for (X, Y, A), c in D.groupby(["X", "Y", "A"]):
    for scope in ("All", "Primary"):
        for half in ("fit", "check", "all"):
            x = c if scope == "All" else c[c.account == "Primary"]
            x = x if half == "all" else x[x.half == half]
            l = L[(L.X == X) & (L.Y == Y) & (L.A == A)]; l = l if scope == "All" else l[l.account == "Primary"]
            l = l if half == "all" else l[l.half == half]
            f = x[x.fired]; per = x.groupby("date")[["delta", "excess"]].sum()
            fam = l.groupby("family").d.sum(); st = l.groupby("strategy").d.sum()
            pos = per.delta[per.delta > 0]
            rows.append(dict(X=X, Y=Y, A=A, scope=scope, half=half, acct_days=len(x), fired=len(f), helped=int((f.delta > 0).sum()),
                             hurt=int((f.delta < 0).sum()), delta=x.delta.sum(), per_acct_day=x.delta.mean(), placebo=f.placebo.sum(),
                             excess=x.excess.sum(), t_delta=tstat(per.delta), t_excess=tstat(per.excess),
                             best_share=per.delta.max() / x.delta.sum() if x.delta.sum() > 0 else np.nan,
                             avgR_base=x.base.sum() / x.n.sum(), avgR_new=x.new.sum() / x.n_new.sum(),
                             wob_base=wobest(x, "base", "n"), wob_new=wobest(x, "new", "n_new"),
                             runners=int(f.runner.sum()), runner_delta=f[f.runner].delta.sum(),
                             fam_better=int((fam > 0).sum()), fam_worse=int((fam < 0).sum()), fam_gain=fam[fam > 0].sum(), fam_loss=fam[fam < 0].sum(),
                             set_better=int((st > 0).sum()), set_worse=int((st < 0).sum())))
R = pd.DataFrame(rows)
def passes(r, fit):
    ok = [r.delta > 0, r.avgR_new > r.avgR_base, r.wob_new >= r.wob_base, (r.best_share < 0.5) if r.delta > 0 else False,
          r.fam_better > r.fam_worse, r.t_delta >= BAR16, r.excess > 0, r.t_excess >= BAR16, fit.delta > 0]
    return "PASS" if all(ok) else "fail (" + ",".join(n for n, k in zip(["total", "avgR", "wobest", "1day", "families", "t", "excess", "t_excess", "fit sign"], ok) if not k) + ")"
out = []
for (X, Y, A), c in R[R.scope == "All"].groupby(["X", "Y", "A"]):
    ck = c[c.half == "check"].iloc[0]; ft = c[c.half == "fit"].iloc[0]; out.append(dict(X=X, Y=Y, A=A, verdict=passes(ck, ft)))
V = pd.DataFrame(out); R.to_csv(f"{O}/scores.csv", index=False); V.to_csv(f"{O}/verdicts.csv", index=False)
def md(df, fmt="{:.2f}"):
    df = df.copy()
    for k in df.columns:
        if df[k].dtype.kind == "f": df[k] = df[k].map(lambda v: "" if pd.isna(v) else fmt.format(v))
    return "\n".join(["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)] + ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)])
o = [f"N_class = {N_CLASS}; bar max(1.5, sqrt(2 ln 16)) = {BAR16:.2f}; conservative N = 200 bar = {BAR200:.2f}.", ""]
cols = ["X", "Y", "A", "fired", "helped", "hurt", "delta", "placebo", "excess", "t_delta", "t_excess", "best_share", "avgR_base", "avgR_new",
        "wob_base", "wob_new", "runners", "runner_delta", "fam_better", "fam_worse", "fam_gain", "fam_loss", "set_better", "set_worse"]
for scope in ("All", "Primary"):
    for half in ("check", "fit", "all"):
        o += [f"### {scope}, {half} half", "", md(R[(R.scope == scope) & (R.half == half)][cols], "{:.3f}"), ""]
o += ["### Verdicts (check half, all accounts)", "", md(V), ""]
# per account, check half, delta and excess
pa = D[D.half == "check"].groupby(["X", "Y", "A", "account"]).agg(fired=("fired", "sum"), delta=("delta", "sum"), excess=("excess", "sum")).reset_index()
o += ["### Per account, check half (delta / excess R)", "", md(pa.pivot_table(index=["X", "Y", "A"], columns="account", values="delta").reset_index(), "{:+.1f}"), "",
      md(pa.pivot_table(index=["X", "Y", "A"], columns="account", values="excess").reset_index(), "{:+.1f}"), ""]
# per family, check half, for each config: family delta
pf = L[L.half == "check"].groupby(["X", "Y", "A", "family"]).d.sum().reset_index()
o += ["### Per family, check half, delta R by config (families with |delta| >= 3R in any config)", ""]
pv = pf.pivot_table(index="family", columns=["A", "X", "Y"], values="d").fillna(0)
pv = pv[(pv.abs() >= 3).any(axis=1)]; pv.columns = [f"{a[:2]} {x:.0f}/{y:.0%}" for a, x, y in pv.columns]
o += [md(pv.reset_index(), "{:+.1f}"), ""]
open(MD, "w").write("\n".join(o)); print(md(V)); print(md(R[(R.scope == "All") & (R.half == "check")][cols[:16]], "{:.2f}"))
print(md(R[(R.scope == "Primary") & (R.half == "check")][cols[:16]], "{:.2f}"))
