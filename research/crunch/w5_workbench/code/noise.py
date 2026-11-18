"""W5 A4: noise model of live R (per-trade SD, day ICC, design effect, common day factor, fit->check shift)."""
import numpy as np, pandas as pd
S = "<scratch>"
t = pd.read_pickle(f"{S}/trades.pkl")
out = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)
g = t.groupby("strategy")
st = g.agg(n=("R", "size"), days=("date", "nunique"), avg=("R", "mean"), sd=("R", "std"))
st = st[st.n >= 30]
p("setups with >=30 trades:", len(st), " median per-trade SD:", round(st.sd.median(), 3), " IQR", st.sd.quantile([.25, .75]).round(3).tolist())
p("trades per traded day: median", round((st.n / st.days).median(), 2), " IQR", (st.n / st.days).quantile([.25, .75]).round(2).tolist())
# ICC via one-way ANOVA within setup (days as groups)
rows = []
for s, x in t.groupby("strategy"):
    if len(x) < 30: continue
    d = x.groupby("date").R
    k = d.ngroups; n = len(x)
    if k < 5: continue
    msb = (d.size() * (d.mean() - x.R.mean()) ** 2).sum() / (k - 1)
    msw = ((x.R - d.transform("mean")) ** 2).sum() / (n - k)
    m0 = (n - (d.size() ** 2).sum() / n) / (k - 1)
    icc = max(0.0, (msb - msw) / (msb + (m0 - 1) * msw)) if msb + (m0 - 1) * msw > 0 else 0
    mbar = n / k
    # empirical design effect: var of mean from daily-cluster SE vs iid SE
    ds = d.sum(); se_cl = np.sqrt(k / (k - 1) * ((ds - d.size() * x.R.mean()) ** 2).sum()) / n
    se_iid = x.R.std() / np.sqrt(n)
    rows.append(dict(strategy=s, n=n, days=k, m=mbar, icc=icc, deff_formula=1 + (mbar - 1) * icc, deff_emp=(se_cl / se_iid) ** 2))
I = pd.DataFrame(rows)
p("ICC within setup (by day): median", round(I.icc.median(), 3), " IQR", I.icc.quantile([.25, .75]).round(3).tolist())
p("design effect (empirical, cluster SE^2 / iid SE^2): median", round(I.deff_emp.median(), 2), " IQR", I.deff_emp.quantile([.25, .75]).round(2).tolist(),
  " by trades/day bucket:", I.groupby(pd.cut(I.m, [0, 2, 5, 10, 100])).deff_emp.median().round(2).to_dict())
I.to_csv(f"{S}/A4_icc.csv", index=False)
# common day factor: setup daily avg R vs same-day avg R of all OTHER setups on the same side
t["sd"] = t.side
day_side = t.groupby(["date", "side"]).R.agg(["sum", "size"])
rows = []
for s, x in t.groupby("strategy"):
    if x.date.nunique() < 15: continue
    side = x.side.mode()[0]
    d = x.groupby("date").R.agg(["sum", "size"])
    o = day_side.xs(side, level="side").reindex(d.index)
    other = (o["sum"] - d["sum"]) / (o["size"] - d["size"]).replace(0, np.nan)
    a = d["sum"] / d["size"]
    ok = other.notna()
    if ok.sum() < 10: continue
    r = np.corrcoef(a[ok], other[ok])[0, 1]
    rows.append(dict(strategy=s, days=int(ok.sum()), r=r))
C = pd.DataFrame(rows)
p("common day factor: corr(setup daily avg R, other same-side setups' daily avg R): median", round(C.r.median(), 3),
  " IQR", C.r.quantile([.25, .75]).round(3).tolist(), " setups", len(C), " median R^2", round((C.r ** 2).median(), 3))
# fit/check shift: each setup's own first half vs second half of traded days
rows = []
for s, x in t.groupby("strategy"):
    ds = sorted(x.date.unique())
    if len(ds) < 10 or len(x) < 40: continue
    h = ds[len(ds) // 2]
    f, c = x[x.date < h], x[x.date >= h]
    rows.append(dict(strategy=s, f=f.R.mean(), c=c.R.mean(), n=len(x), split=h))
F = pd.DataFrame(rows)
from scipy import stats
p("setup avg R fit-half vs check-half (own sessions):", len(F), "setups; spearman", round(stats.spearmanr(F.f, F.c).correlation, 3),
  " mean fit", round(F.f.mean(), 3), " mean check", round(F.c.mean(), 3), " sign agree", round((np.sign(F.f) == np.sign(F.c)).mean(), 2))
# system-wide drift: all-trade avg R by week
t["wk"] = pd.to_datetime(t.date).dt.to_period("W").astype(str)
w = t.groupby("wk").R.agg(["mean", "size"])
p("all-account avg R by week:"); p(w.round(3).to_string())
# per-trade SD by exit structure
p("per-trade SD by exit reason share: target-exit setups vs hold setups")
tg = t.groupby("strategy").exit_reason.apply(lambda s: (s == "target").mean())
st["tg"] = tg
p(st.groupby(pd.cut(st.tg, [-0.01, 0.05, 0.4, 1])).sd.median().round(3).to_dict())
open(f"{S}/A4_out.txt", "w").write("\n".join(out))
