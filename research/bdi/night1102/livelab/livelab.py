"""night1102/livelab: live-first lane numbers from the 5 live journals. Usage: python livelab.py <scratch_dir>
(scratch holds <branch>.db copies from `git show origin/<branch>:journal.db`). Educational only - not financial advice."""
import json, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr

S = Path(sys.argv[1]); OUT = Path(__file__).parent
A = {"primary": "mcf-data", "testing1": "mcf-data-testing", "testing2": "mcf-data-testing2",
     "graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen"}
res = {}
T, W, SG = [], [], []
for a, b in A.items():
    c = sqlite3.connect(S / f"{b}.db")
    for rid, lst in ((1, T), (2, W)):
        t = pd.read_sql(f"select * from trades where run_id={rid}", c); t["account"] = a; lst.append(t)
    s = pd.read_sql("select day,ts,symbol,strategy,side,status,reason from signals where run_id=1", c); s["account"] = a
    SG.append(s)
T, W, SG = (pd.concat(x, ignore_index=True) for x in (T, W, SG))
for d in (T, W):
    d["risk"] = (d.entry - d.stop).abs() * d.shares
for d in (T,):
    d.drop(d[(d.risk <= 0) | d.pnl_adj.isna()].index, inplace=True)
    d["R"] = d.pnl_adj / d.risk
# what-if trades: r_multiple (what-if engine nets the production cost model per blocked_audit)
W["R"] = W.r_multiple

# ---- A capacity
cap = []
for (a, day), g in T.groupby(["account", "date"]):
    ev = []
    for _, r in g.iterrows():
        if pd.isna(r.entry_time) or pd.isna(r.exit_time):
            continue
        ev += [(r.entry_time, 1), (r.exit_time, -1)]
    ev.sort(key=lambda x: (x[0], x[1])); cur = pk = 0
    for _, e in ev:
        cur += e; pk = max(pk, cur)
    sg = SG[(SG.account == a) & (SG.day == day)]
    cap.append(dict(account=a, day=day, trades=len(g), setups=g.strategy.nunique(), peak_open=pk,
                    bp_reject=int(sg.reason.fillna("").str.contains("buying power").sum()),
                    skipped=int((sg.status == "skipped").sum()), R=g.R.sum()))
cap = pd.DataFrame(cap); cap.to_csv(OUT / "capacity.csv", index=False)
res["capacity"] = cap.groupby("account").agg(sessions=("day", "nunique"), trades_med=("trades", "median"),
    trades_max=("trades", "max"), setups_med=("setups", "median"), peak_open_med=("peak_open", "median"),
    peak_open_max=("peak_open", "max"), bp_reject=("bp_reject", "sum")).round(1).reset_index().to_dict("records")
last5 = sorted(T.date.unique())[-5:]
res["capacity_last5"] = cap[cap.day.isin(last5)].groupby("account").agg(trades_med=("trades", "median"),
    peak_open_max=("peak_open", "max"), setups_med=("setups", "median")).reset_index().to_dict("records")

# ---- B early vs later
T = T.sort_values(["account", "strategy", "date", "entry_time"])
rows = []
for (a, s), g in T.groupby(["account", "strategy"]):
    days = sorted(g.date.unique())
    if len(days) < 8 or len(g) < 40:
        continue
    d = g.groupby("date").R.agg(["sum", "count"])
    best = d["sum"].max(); tot = d["sum"].sum()
    r = dict(account=a, strategy=s, sessions=len(days), n=len(g), avgR=g.R.mean(),
             avgR_wo_best=(tot - best) / (len(g) - d.loc[d["sum"].idxmax(), "count"]),
             best_share=best / tot if tot > 0 else np.nan)
    for k in (5, 10):
        e = g[g.date.isin(days[:k])]; l = g[~g.date.isin(days[:k])]
        r[f"early{k}s"] = e.R.mean(); r[f"later{k}s"] = l.R.mean(); r[f"n_later{k}s"] = len(l)
    r["early30t"] = g.R.iloc[:30].mean(); r["later30t"] = g.R.iloc[30:].mean()
    rows.append(r)
B = pd.DataFrame(rows); B.to_csv(OUT / "early_vs_later.csv", index=False)
bres = {"setups": len(B), "later_positive": int((B.later30t > 0).sum())}
for e, l in (("early5s", "later5s"), ("early10s", "later10s"), ("early30t", "later30t")):
    m = B[[e, l]].dropna(); m = m[B.loc[m.index, "n_later" + e[5:]] >= 15] if e.endswith("s") else m
    rho, p = spearmanr(m[e], m[l])
    bres[e] = dict(n=len(m), spearman=round(rho, 3), p=round(p, 4), sign_agree=round(float((np.sign(m[e]) == np.sign(m[l])).mean()), 3),
                   early_pos_later_pos=f"{int(((m[e]>0)&(m[l]>0)).sum())}/{int((m[e]>0).sum())}",
                   early_neg_later_pos=f"{int(((m[e]<=0)&(m[l]>0)).sum())}/{int((m[e]<=0).sum())}")
# kill grid
kill = []
for K in (15, 30, 45):
    for x in (-0.40, -0.30, -0.20, -0.10, 0.00):
        killed = fk = 0; saved = 0.0; kept_later = []
        for (a, s), g in T.groupby(["account", "strategy"]):
            if len(g) < K + 15:
                continue
            e = g.R.iloc[:K].mean(); l = g.R.iloc[K:]
            if e <= x:
                killed += 1; fk += int(l.mean() > 0); saved -= l.sum()
            else:
                kept_later.append(l.mean())
        kill.append(dict(K=K, x=x, killed=killed, false_kill=fk, R_saved_later=round(saved, 1),
                         kept=len(kept_later), kept_later_pos=int(sum(v > 0 for v in kept_later))))
kill = pd.DataFrame(kill); kill.to_csv(OUT / "kill_grid.csv", index=False)
bres["kill_configs"] = len(kill); res["early"] = bres; res["kill"] = kill.to_dict("records")

# ---- C gen screen vs live
import yaml
g = yaml.safe_load(open("/home/user/MCF/config/account_gen.yaml"))["strategies"]
sc = []
for name, blk in g.items():
    s = ((blk or {}).get("gen") or {}).get("screen") or {}
    lv = T[(T.account == "gen") & (T.strategy == name)]
    if len(lv) >= 10 and s:
        sc.append(dict(strategy=name, train=s.get("train", {}).get("exp_r"), valid=(s.get("valid") or {}).get("exp_r"),
                       live=lv.R.mean(), n=len(lv)))
sc = pd.DataFrame(sc); sc.to_csv(OUT / "gen_screen_vs_live.csv", index=False)
cres = {"setups": len(sc)}
for col in ("train", "valid"):
    m = sc[[col, "live"]].dropna()
    if len(m) > 4:
        rho, p = spearmanr(m[col], m.live); cres[col] = dict(n=len(m), spearman=round(rho, 3), p=round(p, 3))
res["gen_screen"] = cres
res["account_avgR"] = T.groupby("account").agg(n=("R", "size"), avgR=("R", "mean"), setups=("strategy", "nunique")).round(3).reset_index().to_dict("records")
res["setups_live_positive"] = {a: f"{int((g.groupby('strategy').R.mean() > 0).sum())}/{g.strategy.nunique()}" for a, g in T.groupby("account")}

# ---- D noise
dd = T.groupby(["account", "strategy", "date"]).R.agg(["sum", "count"]).reset_index()
v = []
for (a, s), g in dd.groupby(["account", "strategy"]):
    if len(g) < 8 or g["count"].sum() < 40:
        continue
    tpd = g["count"].mean(); sd_day = (g["sum"] / g["count"]).std(ddof=1)   # sd of daily mean R
    sd_tr = T[(T.account == a) & (T.strategy == s)].R.std(ddof=1)
    v.append(dict(tpd=tpd, sd_daymean=sd_day, sd_trade=sd_tr, deff=(sd_day ** 2) / (sd_tr ** 2 / tpd)))
v = pd.DataFrame(v)
dres = {"setups": len(v), "trades_per_day_med": round(v.tpd.median(), 2), "sd_trade_med": round(v.sd_trade.median(), 3),
        "sd_daymean_med": round(v.sd_daymean.median(), 3), "design_effect_med": round(v.deff.median(), 2)}
for mu in (0.10, 0.20, 0.30):
    for tt in (1.0, 1.5):
        dres[f"sessions_mu{mu}_t{tt}"] = int(np.ceil((tt * v.sd_daymean.median() / mu) ** 2))
# by trades/day bucket
for lo, hi in ((0, 2), (2, 5), (5, 1e9)):
    q = v[(v.tpd >= lo) & (v.tpd < hi)]
    if len(q):
        dres[f"sd_daymean_tpd{lo}-{hi}"] = dict(n=len(q), sd=round(q.sd_daymean.median(), 3),
                                               sessions_mu020_t15=int(np.ceil((1.5 * q.sd_daymean.median() / 0.2) ** 2)))
res["noise"] = dres

# ---- E shadow coverage
SG["key"] = SG.account + "|" + SG.day + "|" + SG.symbol + "|" + SG.strategy
W["key"] = W.account + "|" + W.date + "|" + W.symbol + "|" + W.strategy
nb = SG[SG.status.isin(["skipped", "rejected"])]
cov = nb.assign(has=nb.key.isin(set(W.key)))
cov["why"] = cov.reason.fillna("").str.replace(r"\d+", "#", regex=True).str[:40]
res["shadow"] = {"blocked_signals": len(nb), "with_whatif": int(cov.has.sum()),
                 "by_reason_missing": cov[~cov.has].why.value_counts().head(12).to_dict(),
                 "by_account": cov.groupby("account").has.agg(["size", "sum"]).reset_index().to_dict("records")}
# place in line per account (held by different setup)
res["whatif_avgR_by_account"] = W.groupby("account").R.agg(["size", "mean"]).round(3).reset_index().to_dict("records")
json.dump(res, open(OUT / "results.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
