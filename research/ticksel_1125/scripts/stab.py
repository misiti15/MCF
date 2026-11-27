"""TICKSEL descriptive stability: every FIT trait cell (no selection) re-measured on CHECK, T2 and live with FIT cut points.
Not configs; answers 'do trait effects keep their sign out of sample?'. Educational only - not financial advice."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ticksel")
from lib2 import *
from prep import FAM
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/"
T = S + "ticksel/"
cfg = json.load(open(T + "configs.json"))
X = pd.read_csv(T + "fit_tables.csv")
B1 = pd.read_parquet(T + "bk_t1.parquet"); B2 = pd.read_parquet(T + "bk_t2.parquet")
L = pd.read_parquet(S + "pyramid/X/live_dedup.parquet"); L = L[L.strategy.isin(FAM)].rename(columns={"strategy": "setup"})
L["date"] = L.date.astype(str)
L = L.merge(pd.read_parquet(T + "tr_live.parquet"), on=["symbol", "date"], how="left").merge(pd.read_parquet(T + "static.parquet"), on="symbol", how="left")
L["fam"] = L.setup.map(FAM); L["r_adj"] = L.r
H = {"check": B1[(B1.half == "check") & ~B1.rnd], "t2": B2[~B2.rnd], "live": L,
     "check_rnd": B1[(B1.half == "check") & B1.rnd], "fit_rnd": B1[(B1.half == "fit") & B1.rnd]}
rows = []
for r in X.itertuples():
    cu = cfg["cuts"].get(f"{r.fam}|{r.trait}", [])
    rec = r._asdict()
    for h, D in H.items():
        G = D[D.fam == r.fam]
        if not len(G): continue
        ind = bucket(G, r.trait, cu) == r.bucket
        if ind.sum() < 10 or (~ind).sum() < 10:
            rec[f"{h}_n"] = int(ind.sum()); continue
        d, t = diff_t(G.r, ind, G.date)
        rec[f"{h}_n"], rec[f"{h}_avg"], rec[f"{h}_diff"], rec[f"{h}_t"] = int(ind.sum()), float(G.r[ind].mean()), d, t
        if h in ("check", "t2"):
            rec[f"{h}_diff_adj"] = diff_t(G.r_adj, ind, G.date)[0]
    rows.append(rec)
Z = pd.DataFrame(rows).drop(columns=["Index"])
Z.to_csv(T + "stability.csv", index=False)
def agree(a, b, m):
    m = m & Z[a].notna() & Z[b].notna()
    return int(m.sum()), float((np.sign(Z[a][m]) == np.sign(Z[b][m])).mean()), float(Z[a][m].corr(Z[b][m]))
out = {}
for lab, m in (("all cells", Z.bucket != "na"), ("FIT |t|>=2", (Z.t.abs() >= 2) & (Z.bucket != "na")),
               ("FIT |t|>=2.5", (Z.t.abs() >= 2.5) & (Z.bucket != "na")), ("FIT n>=150, |diff|>=0.10", (Z.n >= 150) & (Z["diff"].abs() >= 0.10))):
    out[lab] = {h: agree("diff", f"{h}_diff", m) for h in ("check", "t2", "live")}
    out[lab]["check_vs_t2"] = agree("check_diff", "t2_diff", m)
    out[lab]["fit_vs_fitrnd"] = agree("diff", "fit_rnd_diff", m)
print(json.dumps(out, indent=1))
cols = ["fam", "trait", "bucket", "n", "share", "avg", "diff", "t", "check_n", "check_avg", "check_diff", "check_t", "t2_n", "t2_diff", "t2_t", "live_n", "live_avg", "live_diff", "fit_rnd_diff", "check_rnd_diff"]
pd.set_option("display.width", 300)
print(Z.assign(at=Z.t.abs()).sort_values("at", ascending=False)[cols].head(20).round(3).to_string())
json.dump(out, open(T + "stability.json", "w"), indent=1)
