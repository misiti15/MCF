import sys, pandas as pd, numpy as np
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
d = lib.daily(); d = d[d.symbol == "SPY"].copy(); d["date"] = d.date.astype(str)
oc = (d.set_index("date").close / d.set_index("date").open - 1) * 100
typ = lambda x: "up" if x > 0.25 else ("down" if x < -0.25 else "flat")
T = pd.concat([pd.read_parquet("trades_main.parquet"), pd.read_parquet("trades_combo.parquet").query("cfg != 'PARENT'")])
T["test"] = np.where(T.split.isna(), "replay", "2y"); T["hold"] = T.xm - T.em
T["dt"] = T.date.map(oc).map(lambda x: typ(x) if pd.notna(x) else "na")
rows = []
for (c, te), g in T.groupby(["cfg", "test"], sort=False):
    r = dict(cfg=c[:44], test=te, avg_win=g.r[g.r > 0].mean(), avg_loss=g.r[g.r <= 0].mean(), hold_med=g.hold.median(),
             stop_share=(g.kind == "stop").mean(), tgt_share=(g.kind == "target").mean())
    if te == "2y":
        for k in ("up", "flat", "down"):
            r[k] = g.r[g.dt == k].mean()
    rows.append(r)
x = pd.DataFrame(rows); x.to_csv("extras.csv", index=False, float_format="%.4f"); print(x.round(3).to_string())
