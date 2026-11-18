"""U4 scoring (PLAN.md). Educational only - not financial advice."""
import glob, pickle, sys, numpy as np, pandas as pd
sys.path.insert(0, "."); import jload
S = jload.S
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{S}/out"
import os; os.makedirs(OUT, exist_ok=True)
res = [pickle.load(open(f, "rb")) for f in sorted(glob.glob(f"{S}/res/*.pkl"))]
DY = pd.DataFrame([r["day"] for r in res]).set_index("date")
DY["oc"] = (DY.spy_c / DY.spy_o - 1) * 100; DY["gap"] = (DY.spy_o / DY.spy_pc - 1) * 100
DY["dtype"] = np.where(DY.oc > 0.25, "up", np.where(DY.oc < -0.25, "down", "quiet"))
DY["gapup"] = DY.gap >= 0.30
T = pd.concat([r["trades"] for r in res if len(r["trades"])], ignore_index=True)
assert not T.date.between("2024-11-01", "2025-02-28").any()
T["tier"] = np.where(T.date >= "2026-10-06", "live", "2y")
T["half"] = np.where(T.tier == "live", np.where(T.date < "2026-10-28", "fit", "check"),
                     np.where(T.date <= "2025-08-31", "H1", "H2"))
T = T.join(DY[["dtype", "gapup", "oc"]], on="date")
LIVE_DAYS = sorted(DY.index[DY.index >= "2026-10-06"]); Y2_DAYS = sorted(DY.index[DY.index < "2026-10-06"])
J = jload.load()
PRI = J[J.acct == "Primary"].groupby("date").R.sum().reindex(LIVE_DAYS).fillna(0)


def tcl(x):
    if len(x) < 3:
        return np.nan
    m = x.R.mean(); e = (x.R - m).groupby(x.date).sum()
    se = np.sqrt((e ** 2).sum()) / len(x)
    return m / se if se > 0 else np.nan


def base(x, days):
    d = x.groupby("date").R.sum()
    if not len(x):
        return dict(n=0)
    b = d.idxmax(); tot = d.sum(); nb = (x.date == b).sum()
    return dict(n=len(x), days=len(d), avg=x.R.mean(), total=tot, t=tcl(x), avg_wo_best=(tot - d.max()) / max(1, len(x) - nb),
                best_share=(d.max() / tot) if tot > 0 else np.nan, best_day=b, win=(x.R > 0).mean(),
                rnd_time=x.rnd_time.mean(), rnd_bar=x.rnd_bar.mean())


rows, dtr = [], []
for (sp, ex), x in T.groupby(["spec", "exit"]):
    L = x[x.tier == "live"]; Y = x[x.tier == "2y"]
    r = dict(spec=sp, exit=ex, **{f"live_{k}": v for k, v in base(L, LIVE_DAYS).items()})
    for h in ("fit", "check"):
        r[f"live_{h}_avg"] = L[L.half == h].R.mean(); r[f"live_{h}_n"] = (L.half == h).sum()
    yb = base(Y, Y2_DAYS)
    r.update({f"y2_{k}": yb.get(k) for k in ("n", "days", "avg", "t", "avg_wo_best", "best_share", "rnd_time", "rnd_bar")})
    for h in ("H1", "H2"):
        r[f"y2_{h}_avg"] = Y[Y.half == h].R.mean(); r[f"y2_{h}_n"] = (Y.half == h).sum()
    for tier, X in (("live", L), ("y2", Y)):
        for dt in ("up", "quiet", "down"):
            z = X[X.dtype == dt]
            r[f"{tier}_{dt}_avg"] = z.R.mean(); r[f"{tier}_{dt}_n"] = len(z)
            dtr.append(dict(spec=sp, exit=ex, tier=tier, dtype=dt, n=len(z), avg=z.R.mean(), total=z.R.sum(),
                            days=z.date.nunique(), per_day=z.R.sum() / max(1, ((DY.dtype == dt) & DY.index.isin(LIVE_DAYS if tier == "live" else Y2_DAYS)).sum())))
        z = X[X.gapup]; r[f"{tier}_gapup_avg"] = z.R.mean(); r[f"{tier}_gapup_n"] = len(z)
    dl = L.groupby("date").R.sum().reindex(LIVE_DAYS).fillna(0)
    r["corr_primary"] = np.corrcoef(dl, PRI)[0, 1]
    r["R_on_primary_red_days"] = dl[PRI < 0].sum(); r["R_on_primary_green_days"] = dl[PRI > 0].sum()
    r["primary_red_days_spec_green"] = int(((PRI < 0) & (dl > 0)).sum()); r["primary_red_days"] = int((PRI < 0).sum())
    rows.append(r)
R = pd.DataFrame(rows)
BAR, BAR90 = 2.146, 0.9 * 2.146
R["pass_bar90"] = ((R.live_fit_avg > 0) & (R.live_check_avg > 0) & (R.live_t >= BAR90) & (R.live_avg_wo_best > 0) &
                   (R.live_best_share < 0.5) & (R.live_avg > R.live_rnd_time) & (R.live_avg > R.live_rnd_bar) &
                   (R.y2_H1_avg > 0) & (R.y2_H2_avg > 0) & (R.live_up_avg >= 0) & (R.live_quiet_avg >= 0))
R["pass_full"] = R.pass_bar90 & (R.live_t >= BAR)
R.to_csv(f"{OUT}/u4_specs.csv", index=False, float_format="%.4f")
pd.DataFrame(dtr).to_csv(f"{OUT}/u4_daytype.csv", index=False, float_format="%.4f")
DY.to_csv(f"{OUT}/u4_days.csv", float_format="%.4f")
T.to_csv(f"{OUT}/u4_trades.csv.gz", index=False, float_format="%.4f")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 80)
print(len(LIVE_DAYS), "live days", len(Y2_DAYS), "2y days; day types live:", DY.loc[LIVE_DAYS].dtype.value_counts().to_dict(),
      "2y:", DY.loc[Y2_DAYS].dtype.value_counts().to_dict())
c1 = ["spec", "exit", "live_n", "live_days", "live_avg", "live_total", "live_t", "live_avg_wo_best", "live_best_share",
      "live_fit_avg", "live_check_avg", "live_rnd_time", "live_rnd_bar", "pass_bar90", "pass_full"]
print(R[c1].round(3).to_string())
c2 = ["spec", "exit", "y2_n", "y2_avg", "y2_t", "y2_avg_wo_best", "y2_H1_avg", "y2_H2_avg", "y2_rnd_time", "y2_rnd_bar"]
print(R[c2].round(3).to_string())
c3 = ["spec", "exit", "live_up_avg", "live_up_n", "live_quiet_avg", "live_quiet_n", "live_down_avg", "live_down_n", "live_gapup_avg",
      "y2_up_avg", "y2_quiet_avg", "y2_down_avg", "y2_gapup_avg", "corr_primary", "R_on_primary_red_days", "R_on_primary_green_days",
      "primary_red_days_spec_green", "primary_red_days"]
print(R[c3].round(3).to_string())

# Part A: existing live long setups
A = pd.read_csv(f"{S}/longs_live.csv", index_col=0)
sel = list(A[(A.n >= 30)].sort_values("avg_wo_best", ascending=False).index[:6]) + ["NM-ETF-late-dip-di-long",
      "GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long"]
Lg = J[J.side == 1].join(DY[["dtype", "gapup"]], on="date")
ar = []
for s in sel + ["ALL LONGS"]:
    x = Lg if s == "ALL LONGS" else Lg[Lg.strategy == s]
    r = dict(strategy=s, n=len(x), avg=x.R.mean(), total=x.R.sum())
    for dt in ("up", "quiet", "down"):
        z = x[x.dtype == dt]; r[f"{dt}_n"] = len(z); r[f"{dt}_avg"] = z.R.mean(); r[f"{dt}_total"] = z.R.sum()
    z = x[x.gapup]; r["gapup_n"] = len(z); r["gapup_avg"] = z.R.mean()
    dl = x.groupby("date").R.sum().reindex(LIVE_DAYS).fillna(0)
    r["corr_primary"] = np.corrcoef(dl, PRI)[0, 1]
    r["R_on_primary_red_days"] = dl[PRI < 0].sum()
    ar.append(r)
AR = pd.DataFrame(ar); AR.to_csv(f"{OUT}/u4_live_longs_daytype.csv", index=False, float_format="%.4f")
print(AR.round(3).to_string())
pp = J[J.acct == "Primary"].join(DY[["dtype"]], on="date")
print("Primary by day type:", pp.groupby("dtype").R.agg(["size", "sum", "mean"]).round(3).to_dict(),
      "days:", DY.loc[LIVE_DAYS].groupby("dtype").size().to_dict())
print("Primary daily by dtype:", PRI.groupby(DY.loc[LIVE_DAYS].dtype).agg(["sum", "mean", "size"]).round(2).to_dict())
