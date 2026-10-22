"""st7_1022 robustness of the post-diagnosis row H1 (QQQ below its VWAP at entry): threshold neighbours, cohorts,
quarters, live replay, and a mechanism check on the other long lab setups (regime1022 as-run trades). Counted rows:
R1-R6 (6). Writes robust.csv. Educational only - not financial advice."""
import numpy as np
import pandas as pd
from core import load, first_per_symday, p0_cond, exit_r, stats
from sc import HERE, RG22, summ

cand, part, pc, pp = load()
base = p0_cond(cand)
r = exit_r(cand, pc, "t1s1")
pr = exit_r(part, pp, "t1s1")
ctrl = cand["cid"].map(pd.Series(pr).groupby(part["cid"].to_numpy()).mean()).to_numpy(float)
q = cand["qqq_vwap"].to_numpy(float)
s = cand["spy_vwap"].to_numpy(float)
tod = cand["tod"].to_numpy()
rows = []
with np.errstate(invalid="ignore"):
    defs = {"P0": base, "H1 qqq<=0": base & (q <= 0),
            "R1 qqq<=+0.10": base & (q <= 0.10), "R2 qqq<=-0.10": base & (q <= -0.10), "R3 qqq<=-0.25": base & (q <= -0.25),
            "R4 qqq<=0 & spy<=0": base & (q <= 0) & (s <= 0),
            "R5 H1 10:45 bar only": base & (q <= 0) & (tod == 1045), "R6 H1 other bars": base & (q <= 0) & (tod != 1045)}
for k, m in defs.items():
    idx = first_per_symday(cand, m)
    st = stats(cand.loc[idx], r[idx], ctrl[idx])
    st["row"] = k
    df = cand.loc[idx].assign(r=r[idx])
    qtr = df.groupby(pd.PeriodIndex(pd.to_datetime(df["date"]), freq="Q").astype(str))["r"].mean().round(3)
    st["quarters_pos"] = f"{int((qtr > 0).sum())}/{len(qtr)}"
    st["quarters"] = " ".join(f"{a}:{b:+.2f}" for a, b in qtr.items())
    rows.append(st)
d = pd.DataFrame(rows)
cols = ["row", "n_train", "avg_train", "n_valid", "avg_valid", "t_all", "excess_train", "excess_valid", "top_day_share_all",
        "Bull_all_avg", "Bear_all_avg", "Choppy_all_avg", "Quiet_all_avg", "Choppy-up_all_avg", "Up_all_tot", "Up_all_n",
        "Bear_all_tot", "worst_day_all", "worst5pct_days", "quarters_pos", "quarters"]
d[cols].to_csv(HERE / "robust.csv", index=False)
pd.set_option("display.width", 320)
print(d[cols].to_string())

# mechanism check: every long lab setup in regime1022 as-run, QQQ above / below its VWAP at entry (descriptive)
a = pd.read_parquet(RG22 / "asrun.parquet")
a = a[a.asrun & (a.side == "long")]
ix = pd.concat([pd.read_parquet(p) for p in sorted((RG22 / "idx").glob("*.parquet"))])
ix = ix[ix.symbol == "QQQ"][["date", "tod", "vwapDistPct"]].rename(columns={"vwapDistPct": "qv"})
ix["date"] = pd.to_datetime(ix["date"]).dt.date
a = a.merge(ix, on=["date", "tod"], how="left")
out = []
for st, g in a.groupby("setup"):
    row = {"setup": st, "n": len(g)}
    for nm, m in (("qqq_below", g.qv <= 0), ("qqq_above", g.qv > 0)):
        for sp in ("train", "valid"):
            x = g[m & (g.split == sp)]
            row[f"{nm}_{sp}"] = round(x.r.mean(), 3) if len(x) else None
            row[f"{nm}_{sp}_n"] = len(x)
    out.append(row)
o = pd.DataFrame(out)
o["below_better_both"] = (o.qqq_below_train > o.qqq_above_train) & (o.qqq_below_valid > o.qqq_above_valid)
o.to_csv(HERE / "mechanism_longs.csv", index=False)
print(o.to_string())
print("long setups where QQQ-below beats QQQ-above in both periods:", int(o.below_better_both.sum()), "of", len(o))
