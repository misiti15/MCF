"""Giveback map, 2-year lab tables (a)(c). Usage: python analyze_lab.py lab_paths.parquet SCRATCH OUT.md
Educational only - not financial advice."""
import sys, re, numpy as np, pandas as pd, pyarrow.dataset as pds
from common import CK, state, dstat, tod_bucket, hold_bucket, md
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib  # noqa
X = pd.read_parquet(sys.argv[1]); S = sys.argv[2]; OUT = sys.argv[3]
LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date(); SPLIT = pd.Timestamp("2025-09-30").date()
X["date"] = pd.to_datetime(X.date).dt.date
assert not ((X.date >= LK0) & (X.date <= LK1)).any()
X["family"] = np.where(X.setup.str.startswith("GEN"), "GEN", X.setup.str.split("-").str[0])
X["sidec"] = np.where(X.side > 0, "long", "short"); X["fs"] = X.family + " " + X.sidec
X["half"] = np.where(X.date <= SPLIT, "fit", "check")
X["m_in"] = X.tod // 100 * 60 + X.tod % 100
X["tod_b"] = tod_bucket(X.m_in).astype(str); X["holdb"] = hold_bucket(X.hold).astype(str)
u = pd.read_csv("/home/user/MCF/data/universe.csv")[["symbol", "name"]]; NAME = dict(zip(u.symbol, u.name))
def itype(sym):
    nl = str(NAME.get(sym, "")).lower()
    etf = bool(re.search(r"\betf\b|trust|fund|shares|ishares|proshares|direxion|spdr|invesco|vaneck|graniteshares|tradr|defiance|leverage shares|t-rex|volatility", nl))
    lev = bool(re.search(r"\b[23]x\b|ultra|leveraged|daily .*(bull|bear)|1\.5x|2x|3x", nl))
    if bool(re.search(r"bear|short|inverse|-1x|-2x|-3x", nl)) and etf: return "inverse ETF"
    if lev and etf: return "leveraged ETF"
    return "ETF" if etf else ("stock" if nl else "unknown")
X["itype"] = X.symbol.map({s: itype(s) for s in X.symbol.unique()})
# SPY minute closes (locked block filtered) for day type and the SPY move during each trade
TZ = "America/New_York"; ix = "__index_level_0__"
sp = pds.dataset("/home/user/MCF/data/cache_hist/1Min/SPY.parquet").to_table(
    filter=(pds.field(ix) < pd.Timestamp("2024-11-01", tz=TZ)) | (pds.field(ix) >= pd.Timestamp("2025-03-01", tz=TZ))).to_pandas()
sp = sp.set_index(ix) if ix in sp.columns else sp
sp = sp[~sp.index.duplicated(keep="last")]; sp = sp[(sp.index.hour * 60 + sp.index.minute >= 570) & (sp.index.hour * 60 + sp.index.minute < 960)]
assert not ((sp.index >= pd.Timestamp("2024-11-01", tz=TZ)) & (sp.index < pd.Timestamp("2025-03-01", tz=TZ))).any()
grid = {}
for dte, g in sp.groupby(sp.index.date):
    a = np.full(390, np.nan); a[(g.index.hour * 60 + g.index.minute - 570).to_numpy()] = g.close.to_numpy()
    grid[dte] = (pd.Series(a).ffill().bfill().to_numpy(), float(g.open.iloc[0]))
oc = {k: (v[0][-1] / v[1] - 1) * 100 for k, v in grid.items()}
X["spy_oc"] = X.date.map(oc)
def spy_tr(r):
    g = grid.get(r[0]); 
    if g is None: return np.nan
    i0 = min(max(r[1] - 570, 0), 389); i1 = min(max(r[2] - 570, 0), 389); return r[3] * (g[0][i1] / g[0][i0] - 1) * 100
X["spy_tr"] = [spy_tr(r) for r in zip(X.date, X.m_in, X.xmin, X.side)]
X["day"] = np.where(X.spy_oc > .25, "SPY up day", np.where(X.spy_oc < -.25, "SPY down day", "SPY flat day"))
X["mkt"] = np.where(X.spy_tr > .2, "SPY with trade", np.where(X.spy_tr < -.2, "SPY against trade", "SPY flat in trade"))
X["stop"] = X.kind == 1; X["give"] = X.mfe - X.fin
L = []
def p(s=""): L.append(s)
def cut(df, col, minn=2000):
    rows = []
    for k, g in df.groupby(col):
        if len(g) < minn: continue
        r = dict(cut=k, n=len(g), avgR=g.fin.mean(), MFE=g.mfe.mean(), MAE=g.mae.mean(), med_tMFE=g.tmfe.median(), give=g.give.mean())
        for x in (.5, .8, 1.0):
            gg = g[g.mfe >= x]; r[f"reach{x}"] = len(gg) / len(g); r[f"stop|{x}"] = gg.stop.mean() if len(gg) else np.nan
        nt = g[g.mfe >= .8 * g.tgtR]; r["stop|80%tgt"] = nt.stop.mean() if len(nt) else np.nan
        uu = g[(g.mfe >= .8) & (g.fin <= 0)]; r["lost08_per100"] = 100 * (uu.mfe - uu.fin).sum() / len(g)
        rows.append(r)
    return pd.DataFrame(rows)
p(f"2-year lab, first signal per (setup, symbol, day): {len(X)} trades, {X.setup.nunique()} setups, {X.family.nunique()} families, {X.date.nunique()} sessions "
  f"(locked block absent, asserted). Avg final R {X.fin.mean():+.4f} (stop units, costs in).")
p("Geometry mix: " + ", ".join(f"{k} {v}" for k, v in X.geom.value_counts().items()))
p()
for col, title in (("sidec", "side"), ("geom", "geometry"), ("itype", "instrument type"), ("tod_b", "entry time"), ("holdb", "hold time"),
                   ("day", "day type (SPY open->close)"), ("mkt", "SPY during the trade, signed by trade side"), ("half", "fit / check half")):
    p(f"### (a) lab by {title}"); p(md(cut(X, col))); p()
F = cut(X, "fs", 3000).sort_values("lost08_per100", ascending=False); F.to_csv(f"{S}/lab_family.csv", index=False)
p("### (a) lab by family x side (n >= 3000), sorted by R lost per 100 trades after reaching +0.8"); p(md(F)); p()
# (c) stalled cells
rows = []
for t in CK:
    y = X[X[f"rem{t}"].notna()][["fs", "sidec", "date", "half", "setup", f"mk{t}", f"mf{t}", f"rem{t}", "fin"]].copy()
    y["st"] = state(y[f"mk{t}"].to_numpy(), y[f"mf{t}"].to_numpy()); y["r"] = y[f"rem{t}"].astype(float)
    for (fs, st), g in y.groupby(["fs", "st"]):
        if len(g) < 300: continue
        a = dstat(g); f_ = g[g.half == "fit"].r.mean(); c_ = g[g.half == "check"].r.mean()
        sb = g.groupby("setup").r.mean()
        rows.append(dict(t=t, group=fs, state=st, n=a["n"], days=a["days"], rem=a["mean"], t_stat=a["t"], fit=f_, check=c_, wo_best=a["wo_best"],
                         setups=len(sb), setups_neg=int((sb < 0).sum()), final=g.fin.mean()))
    for (sd, st), g in y.groupby(["sidec", "st"]):
        a = dstat(g); rows.append(dict(t=t, group=sd, state=st, n=a["n"], days=a["days"], rem=a["mean"], t_stat=a["t"],
                                       fit=g[g.half == "fit"].r.mean(), check=g[g.half == "check"].r.mean(), wo_best=a["wo_best"], final=g.fin.mean()))
C = pd.DataFrame(rows); C.to_csv(f"{S}/lab_stalled.csv", index=False)
fam = C[~C.group.isin(["long", "short"])]
K = len(fam); T = max(2.0, float(np.sqrt(2 * np.log(K))))
C["pocket"] = (~C.group.isin(["long", "short"])) & (C.fit < 0) & (C.check < 0) & (C.t_stat <= -T)
C["hold_pays"] = (~C.group.isin(["long", "short"])) & (C.fit > 0) & (C.check > 0) & (C.t_stat >= T)
p(f"### (c) lab stalled-trade map: K = {K} family x side x state x t cells (n >= 300); bar T = max(2, sqrt(2 ln K)) = {T:.2f}")
p("Remaining value = final net R minus a market exit at the minute-t close (bt_all exit cost + $0.01 extra). Negative = exiting at t would have been better.")
p(); p("By side (all families):"); p(md(C[C.group.isin(["long", "short"])].drop(columns=["setups", "setups_neg", "pocket", "hold_pays"]).sort_values(["group", "state", "t"])))
pk = C[C.pocket].sort_values("t_stat")
p(); p(f"'Not going to work out' pockets (remaining < 0 in both halves and t <= -{T:.2f}): {len(pk)} of {K} cells; by state: " + ", ".join(f"{k} {v}" for k, v in pk.state.value_counts().items()))
p(md(pk.drop(columns=["pocket", "hold_pays"]).head(40)))
hp = C[C.hold_pays]
p(); p(f"Cells where holding paid (remaining > 0 both halves, t >= {T:.2f}): {len(hp)}; by state: " + ", ".join(f"{k} {v}" for k, v in hp.state.value_counts().items()))
p(md(hp.drop(columns=["pocket", "hold_pays"]).sort_values("t_stat", ascending=False).head(20)))
# per state x t share of cells negative
sh = fam.assign(neg=fam.rem < 0).groupby(["state", "t"]).agg(cells=("rem", "size"), neg=("neg", "sum"), avg_rem=("rem", "mean")).reset_index()
p(); p("Share of family cells with negative remaining value, by state x t:"); p(md(sh))
C.to_csv(f"{S}/lab_stalled.csv", index=False)
open(OUT, "w").write("\n".join(L) + "\n"); print("\n".join(L[:6]))
