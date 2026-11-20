"""GB-GENTRAIL scoring (PLAN.md, WB2 paired). Usage: python score.py lab.parquet live.parquet OUTDIR.
Educational only - not financial advice."""
import json
import sys

import numpy as np
import pandas as pd

LAB, LIVE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CFG = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
NAMES = {"C1": "HOLD (time exit only)", "C2": "TR1R (1R trail after +1R)", "C3": "TR50 (50% giveback after +1R)",
         "C4": "T1 (fixed 1R target)", "C5": "P1 (half at 1R + TR1R runner)", "C6": "CH2 (chandelier 2xATR5)",
         "C7": "CH3 (chandelier 3xATR5)"}
FIT_END = "2025-09-30"


def dstat(x, day):
    x = np.asarray(x, float)
    n = len(x)
    if n == 0:
        return dict(n=0, mean=np.nan, sum=0.0, t=np.nan)
    mu = x.mean()
    S = pd.Series(x).groupby(np.asarray(day)).sum()
    N = pd.Series(1, index=range(n)).groupby(np.asarray(day)).sum()
    se = np.sqrt(((S.to_numpy() - N.to_numpy() * mu) ** 2).sum()) / n
    return dict(n=n, mean=round(mu, 4), sum=round(x.sum(), 1), t=round(mu / se, 2) if se > 0 else np.nan)


def wo_best(r, day):
    s = pd.Series(np.asarray(r, float)).groupby(np.asarray(day)).agg(["sum", "size"])
    b = s["sum"].idxmax()
    tot = s["sum"].sum()
    rest = s.drop(b)
    return round(rest["sum"].sum() / max(rest["size"].sum(), 1), 4), (round(s.loc[b, "sum"] / tot, 3) if tot > 0 else None)


def prep(X):
    X = X.copy()
    X["own"] = np.where(X.geom == "hold", X["C1"], X["C2"])
    X = X[X[CFG].notna().all(axis=1)]
    X["family"] = X["side"].astype(str) + "-" + X["window"].astype(str) + "-" + X["geom"]
    return X


def per_unit(X, cfg, key):
    d = (X[cfg] - X["own"]).groupby(X[key]).sum()
    d = d[d.abs() > 1e-9]
    return dict(better=int((d > 0).sum()), better_R=round(d[d > 0].sum(), 1),
                worse=int((d < 0).sum()), worse_R=round(d[d < 0].sum(), 1))


L = pd.read_parquet(LAB)
L = L.rename(columns={})
assert not L["date"].between("2024-11-01", "2025-02-28").any()
L = prep(L)
L["half"] = np.where(L["date"] <= FIT_END, "fit", "check")
V = pd.read_parquet(LIVE)
V = V[V.C1.notna()].copy()
V["setup"] = V["strategy"].str.replace(r"-WB\d+$", "", regex=True)
V["side"] = np.where(V["side"] > 0, "long", "short")
V["window"] = V["setup"].str.extract(r"-(OPEN|AM|LAM|MID|LUNCH|PM|LATE)-")[0].fillna("POD")
V = prep(V)

rows = []
for grp in ("hold", "holdtr"):
    for half in ("fit", "check"):
        G = L[(L.geom == grp) & (L.half == half)]
        base = dstat(G["own"], G["date"])
        for cfg in CFG:
            d = G[cfg] - G["own"]
            st = dstat(d, G["date"])
            wb, _ = wo_best(G[cfg], G["date"])
            dd = d.groupby(G["date"]).sum()
            share = round(dd.max() / dd.sum(), 3) if dd.sum() > 0 else None
            rows.append(dict(src="lab", group=grp, half=half, cfg=cfg, name=NAMES[cfg], n=st["n"],
                             days=G["date"].nunique(), base_mean=base["mean"], cfg_mean=round(G[cfg].mean(), 4),
                             delta_mean=st["mean"], delta_sum=st["sum"], t=st["t"], cfg_wo_best=wb,
                             best_day_share_of_gain=share, **{f"setup_{k}": v for k, v in per_unit(G, cfg, "setup").items()},
                             **{f"fam_{k}": v for k, v in per_unit(G, cfg, "family").items()}))
    G = V[V.geom == grp]
    base = dstat(G["own"], G["date"])
    for cfg in CFG:
        d = G[cfg] - G["own"]
        st = dstat(d, G["date"])
        wb, _ = wo_best(G[cfg], G["date"])
        dd = d.groupby(G["date"]).sum()
        share = round(dd.max() / dd.sum(), 3) if dd.sum() > 0 else None
        rows.append(dict(src="live", group=grp, half="live", cfg=cfg, name=NAMES[cfg], n=st["n"], days=G["date"].nunique(),
                         base_mean=base["mean"], cfg_mean=round(G[cfg].mean(), 4), delta_mean=st["mean"],
                         delta_sum=st["sum"], t=st["t"], cfg_wo_best=wb, best_day_share_of_gain=share,
                         **{f"setup_{k}": v for k, v in per_unit(G, cfg, "setup").items()},
                         **{f"fam_{k}": v for k, v in per_unit(G, cfg, "family").items()}))
R = pd.DataFrame(rows)
R.to_csv(f"{OUT}/grid.csv", index=False)

# selection on fit, scored once on check
summ = {}
for grp in ("hold", "holdtr"):
    own = "C1" if grp == "hold" else "C2"
    f = R[(R.src == "lab") & (R.group == grp) & (R.half == "fit") & (R.cfg != own)].sort_values("delta_mean", ascending=False)
    pick = f.iloc[0]["cfg"]
    ck = R[(R.src == "lab") & (R.group == grp) & (R.half == "check") & (R.cfg == pick)].iloc[0]
    lv = R[(R.src == "live") & (R.group == grp) & (R.cfg == pick)].iloc[0]
    fit = f.iloc[0]
    passed = bool(ck.delta_mean > 0 and ck.t >= 2.0 and fit.delta_mean > 0 and ck.setup_better > ck.setup_worse
                  and (ck.best_day_share_of_gain or 1) < 0.5 and lv.delta_mean >= 0)
    summ[grp] = dict(pick=pick, name=NAMES[pick], fit_delta=float(fit.delta_mean), fit_t=float(fit.t),
                     check_delta=float(ck.delta_mean), check_sum=float(ck.delta_sum), check_t=float(ck.t),
                     check_setups=f"{ck.setup_better} better ({ck.setup_better_R}R) / {ck.setup_worse} worse ({ck.setup_worse_R}R)",
                     check_best_day_share=ck.best_day_share_of_gain, live_delta=float(lv.delta_mean),
                     live_sum=float(lv.delta_sum), PASS=passed, lineage_bar_t414=bool(ck.t >= 4.14))
    # per-setup table for the pick (check + live)
    G = L[(L.geom == grp) & (L.half == "check")]
    ps = G.assign(d=G[pick] - G["own"]).groupby("setup").agg(n=("d", "size"), base=("own", "mean"), cfg=(pick, "mean"),
                                                             delta_sum=("d", "sum")).round(4)
    GV = V[V.geom == grp]
    pv = GV.assign(d=GV[pick] - GV["own"]).groupby("setup").agg(live_n=("d", "size"), live_delta_sum=("d", "sum")).round(2)
    ps.join(pv, how="outer").to_csv(f"{OUT}/setup_{grp}_{pick}.csv")
# every alternative per setup on check (better/worse counts are in grid.csv)
summ["lab_trades"] = {h: int((L.half == h).sum()) for h in ("fit", "check")}
summ["lab_days"] = {h: int(L[L.half == h]["date"].nunique()) for h in ("fit", "check")}
summ["lab_setups"] = int(L.setup.nunique())
summ["live_trades"] = int(len(V))
summ["live_setups"] = int(V.setup.nunique())
summ["configs"] = "7 rules x 2 groups = 14 cells (12 alternatives); 1 adopted per group scored once on check"
json.dump(summ, open(f"{OUT}/summary.json", "w"), indent=1, default=str)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
print(R[["src", "group", "half", "cfg", "n", "base_mean", "cfg_mean", "delta_mean", "delta_sum", "t", "cfg_wo_best",
         "best_day_share_of_gain", "setup_better", "setup_better_R", "setup_worse", "setup_worse_R", "fam_better",
         "fam_worse"]].to_string(index=False))
print(json.dumps(summ, indent=1, default=str))
