"""W5 Part A: diagnosis of why Workbench tunes fail out of sample. Educational only - not financial advice."""
import numpy as np, pandas as pd, math
from scipy import stats
S = "<scratch>"
out = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)

# ---------------- A1 U7 fit vs check
c = pd.read_csv(f"{S}/u7c.csv"); c = c[c.eligible].copy()
c["fit_gain"] = c.fit_tot - c.parent_fit_tot
c = c[c.chk_gain.notna()]
p("A1 U7 eligible candidates with check:", len(c))
for k, g in [("all", c)] + list(c.groupby("kind")):
    rho = stats.spearmanr(g.fit_gain, g.chk_gain).correlation
    sl = np.polyfit(g.fit_gain, g.chk_gain, 1)[0]
    p(f"  {k}: n={len(g)} spearman={rho:.3f} OLS slope check~fit={sl:.3f} mean fit gain={g.fit_gain.mean():.2f} mean check gain={g.chk_gain.mean():.2f} share check>0={(g.chk_gain>0).mean():.2f}")
# chosen: best fit per setup among fit_gain>0
ch = c[c.fit_gain > 0].sort_values("fit_gain").groupby("setup").tail(1)
p(f"  chosen (best fit per setup, fit gain>0): n={len(ch)} fit gain sum={ch.fit_gain.sum():.1f} check gain sum={ch.chk_gain.sum():.1f}")
# top decile by fit gain
q = c.fit_gain.quantile(0.9); tq = c[c.fit_gain >= q]
p(f"  top-decile fit gains: n={len(tq)} mean fit={tq.fit_gain.mean():.2f} mean check={tq.chk_gain.mean():.2f}")
# fit/check trade ratio: gates drop trades -> check gain tracks parent's check avg (removing trades from losers)
par = pd.read_csv(f"{S}/u7p.csv").set_index("setup")
c["par_chk_avg"] = c.setup.map(par.chk_avg); c["par_fit_avg"] = c.setup.map(par.fit_avg)
p("  parent fit avg vs check avg (20 setups) spearman:", round(stats.spearmanr(par.fit_avg, par.chk_avg).correlation, 3),
  " mean fit avg", round(par.fit_avg.mean(), 3), " mean check avg", round(par.chk_avg.mean(), 3))
g = c[c.kind == "gate"]
rho = stats.spearmanr(g.chk_gain, -g.par_chk_avg).correlation
p(f"  gates: spearman(check gain, -parent check avg) = {rho:.3f}  (gate gain is mostly 'removing trades from a loser')")

# ---------------- A2 pooling by tune class
c["cls"] = c.tune.str.replace(r"[-+]?\d+(\.\d+)?", "#", regex=True)
cl = c.groupby("cls").agg(k=("setup", "nunique"), fit=("fit_gain", "sum"), chk=("chk_gain", "sum"),
                          fit_pos=("fit_gain", lambda s: (s > 0).mean()), chk_pos=("chk_gain", lambda s: (s > 0).mean()))
cl = cl[cl.k >= 4].sort_values("fit", ascending=False)
p("\nA2 classes (k>=4 setups):"); p(cl.round(2).to_string())
p("  spearman class fit vs check (summed):", round(stats.spearmanr(cl.fit, cl.chk).correlation, 3), " n classes", len(cl))
best = cl.index[0]
p(f"  class-level choice: best pooled-fit class = '{best}' -> check sum {cl.chk.iloc[0]:.1f} over {cl.k.iloc[0]} setups "
  f"(vs per-setup choice {ch.chk_gain.sum():.1f} over {len(ch)}); class median check sum {cl.chk.median():.1f}")
# sign agreement of class means
p("  classes where pooled fit sign == pooled check sign:", int((np.sign(cl.fit) == np.sign(cl.chk)).sum()), "of", len(cl))
# matched-sides symmetric pairs: drop bottom third vs drop top third of the same feature (one must be 'removing trades')
cl.to_csv(f"{S}/A2_classes.csv")

# ---------------- A3 L3 bespoke
l = pd.read_csv(f"{S}/l3c.csv")
l["key"] = l.test + ":" + l.seg
pv = l[l.cfg != "PARENT"].pivot_table(index="cfg", columns="key", values="dR_vs_parent")
p("\nA3 L3 21 variants, spearman of dR vs parent between segments:")
cols = [k for k in ["replay:ALL", "2y:TRAIN", "2y:VALID", "2y:FWD"] if k in pv.columns]
p(pv[cols].corr(method="spearman").round(2).to_string())
p(pv[cols].round(1).to_string())

# ---------------- A5 expected max null t
p("\nA5 expected max of K null t (approx E[max N(0,1)]) vs sqrt(2 ln K):")
rng = np.random.default_rng(1)
for K in [3, 5, 15, 20, 68, 265, 1100]:
    m = rng.standard_normal((4000, K)).max(1)
    p(f"  K={K}: E[max]={m.mean():.2f}  95th pct={np.quantile(m,0.95):.2f}  sqrt(2lnK)={math.sqrt(2*math.log(K)):.2f}")
open(f"{S}/A_out.txt", "w").write("\n".join(out))
