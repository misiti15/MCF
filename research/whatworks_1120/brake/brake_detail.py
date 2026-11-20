"""OUT-BRAKE detail: selectivity vs random / same-setup baselines, Primary by rule period, 11-17 Gen case, burst anatomy.
usage: python brake_detail.py trades.parquet brake_eval.csv  (reads brake_eval_blocks.npz). Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
t = pd.read_parquet(sys.argv[1]); ev = pd.read_csv(sys.argv[2])
t["et"] = pd.to_datetime(t["entry_time"], utc=True, format="mixed"); t = t.sort_values("et").reset_index(drop=True)
t["unit"] = t["account"] + "|" + t["strategy"]
B = np.load(sys.argv[2].replace(".csv", "_blocks.npz"))
R = t.r.values
umean = t.groupby("unit").r.transform("mean").values
# same-setup baseline excluding the setup's own blocked trades is brake-specific; we use the unit's mean over ALL its trades
# and also the unit's mean over its NON-blocked trades (stricter: is the blocked slice worse than the rest of that setup?)
SC = {"primary": t.account == "primary", "gen": t.account == "gen", "graveyard": t.account == "graveyard",
      "testing_all": t.account.isin(["testing", "testing2", "testingd", "testinge", "testingf"]), "all": t.account.notna()}
rows = []
for name in B.files:
    b = B[name]
    for sc, m in SC.items():
        m = m.values; bb = b & m
        if not bb.any():
            rows.append(dict(brake=name, scope=sc, blocked=0)); continue
        kept_mean = pd.Series(R[m & ~b]).groupby(t.loc[m & ~b, "unit"].values).mean()
        km = t.loc[bb, "unit"].map(kept_mean).fillna(0).values
        rows.append(dict(brake=name, scope=sc, blocked=int(bb.sum()), avg_blocked=round(R[bb].mean(), 3),
                         avg_kept=round(R[m & ~b].mean(), 3), net=round(-R[bb].sum(), 1),
                         edge_vs_random=round(-R[bb].sum() + bb.sum() * R[m].mean(), 1),
                         edge_vs_same_setup_rest=round(-(R[bb] - km).sum(), 1)))
sel = pd.DataFrame(rows)
sel.to_csv(sys.argv[2].replace(".csv", "_selectivity.csv"), index=False)
for sc in ["primary", "all", "gen", "graveyard", "testing_all"]:
    print("== selectivity", sc); print(sel[sel.scope == sc].drop(columns="scope").to_string(index=False))
# Primary by rule period
per = pd.cut(pd.to_datetime(t.date), pd.to_datetime(["2026-10-01", "2026-10-29", "2026-11-12", "2026-11-20"]), right=False,
             labels=["10-06..10-28 no setup latch (halt -20R raw)", "10-29..11-11 -2R latch raw", "11-12..11-19 -2R latch + halt cost-in (LR3)"])
p = t.account.values == "primary"
out = []
for name in ["setup_stop_2R", "setup_stop_3R", "setup_stop_4R", "setup_stop_5R", "acct_halt_15R", "acct_halt_20R",
             "xacct_family_4R_2acct", "burst_20in30m_cool", "runaway_stop_5R_after15", "setup_cap_20"]:
    b = B[name] & p
    g = pd.DataFrame({"per": per[p], "r": R[p], "b": b[p]}).groupby("per", observed=False)
    o = g.apply(lambda x: pd.Series({"trades": len(x), "base": round(x.r.sum(), 1), "blocked": int(x.b.sum()),
                                     "net": round(-x.r[x.b].sum(), 1)}), include_groups=False)
    o["brake"] = name; out.append(o.reset_index())
print("== Primary by rule period"); print(pd.concat(out).to_string(index=False))
# 11-17 Gen case
g = (t.account == "gen") & (t.date == "2026-11-17") & t.strategy.str.startswith("GEN-261022-09-Ret15m")
print("== 11-17 Gen case: trades", int(g.sum()), "R", round(R[g].sum(), 1), "first entry", t.loc[g, "et"].min(), "last", t.loc[g, "et"].max())
gg = t[g].copy(); gg["cum"] = gg.r.cumsum()
print(gg.set_index(gg.et.dt.tz_convert("America/New_York").dt.strftime("%H:%M")).resample if False else "")
gg["m"] = gg.et.dt.tz_convert("America/New_York").dt.floor("15min").dt.strftime("%H:%M")
print(gg.groupby("m").agg(n=("r", "size"), r=("r", "sum")).assign(cum=lambda x: x.r.cumsum()).round(1).T.to_string())
cases = []
for name in B.files:
    b = B[name][g.values]
    cases.append(dict(brake=name, blocked=int(b.sum()), kept=int((~b).sum()), R_after=round(R[g.values][~b].sum(), 1),
                      saved=round(-R[g.values][b].sum(), 1)))
print(pd.DataFrame(cases).sort_values("saved", ascending=False).to_string(index=False))
# how often does a whole setup go through >= 30 entries/day; worst setup-days
sd = t.groupby(["account", "strategy", "date"]).r.agg(["size", "sum"])
print("== worst 15 setup-days (all accts)"); print(sd.sort_values("sum").head(15).round(1).to_string())
print("== Primary worst 10 setup-days"); print(sd.loc["primary"].sort_values("sum").head(10).round(1).to_string())
print("== setup-day R by entry count bucket (all)"); print(sd.groupby(pd.cut(sd["size"], [0, 5, 10, 20, 30, 50, 1000])).agg(n=("sum", "size"), avgR_day=("sum", "mean"), avgR_trade=("sum", lambda s: s.sum())).assign(per_trade=lambda x: x.avgR_trade / sd.groupby(pd.cut(sd["size"], [0, 5, 10, 20, 30, 50, 1000]))["size"].sum()).round(3).to_string())
