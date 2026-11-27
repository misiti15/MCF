"""TICKSEL live direction check (10-06..11-24, LR8, deduped). Descriptive only (STOP2: no live per-setup filters from
short samples). Educational only - not financial advice."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ticksel")
from lib2 import *
from prep import FAM
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/"
T = S + "ticksel/"
L = pd.read_parquet(S + "pyramid/X/live_dedup.parquet")
L = L[L.strategy.isin(FAM)].rename(columns={"strategy": "setup"}).copy()
L["date"] = L.date.astype(str)
tr = pd.read_parquet(T + "tr_live.parquet"); st = pd.read_parquet(T + "static.parquet")
L = L.merge(tr, on=["symbol", "date"], how="left").merge(st, on="symbol", how="left")
L["fam"] = L.setup.map(FAM)
print("live trades", len(L), "missing traits", int(L.adv20.isna().sum()))
cfg = json.load(open(T + "configs.json"))
out = {"X": [], "W": [], "desc": [], "B": [], "conc": []}
for c in cfg["X"]:
    G = L[L.fam == c["fam"]]
    ind = bucket(G, c["trait"], cfg["cuts"][f"{c['fam']}|{c['trait']}"]) == c["bucket"]
    d, t = diff_t(G.r, ind, G.date)
    per = {s[:24]: (int(m.sum()), float(G.r[m].mean()) if m.sum() else None, float(G.r[(G.setup == s) & ~ind].mean()))
           for s in sorted(set(G.setup)) for m in [((G.setup == s) & ind).to_numpy()]}
    out["X"].append(dict(id=c["id"], rule=f"{c['fam']} {c['trait']}={c['bucket']}", n=int(ind.sum()), share=float(ind.mean()),
                         in_avg=float(G.r[ind].mean()) if ind.sum() else None, out_avg=float(G.r[~ind].mean()), diff=d, t=t,
                         in_tot=float(G.r[ind].sum()), per_setup=per))
for c in cfg["W"]:
    G = L[L.fam == c["fam"]]
    bk = bucket(G, c["trait"], cfg["cuts"][f"{c['fam']}|{c['trait']}"])
    w = np.where(bk == c["up"], 1.5, np.where(bk == c["down"], 0.5, 1.0))
    out["W"].append(dict(id=c["id"], up_n=int((bk == c["up"]).sum()), up_avg=float(G.r[bk == c["up"]].mean()),
                         down_n=int((bk == c["down"]).sum()), down_avg=float(G.r[bk == c["down"]].mean()),
                         unsized=float(G.r.mean()), sized=float((w * G.r).sum() / w.sum())))
for fam, G in L.groupby("fam"):
    for trn in ("price", "etf", "levinv", "sector", "adv20", "atrp", "beta", "gap", "ret1", "rvol1"):
        cu = cfg["cuts"].get(f"{fam}|{trn}", [])
        bk = bucket(G, trn, cu)
        for bv in sorted(pd.unique(bk)):
            m = bk == bv
            out["desc"].append(dict(fam=fam, trait=trn, bucket=bv, n=int(m.sum()), avg=float(G.r[m].mean()), tot=float(G.r[m].sum())))
    g = G.groupby(["setup", "symbol"]).size()
    out["conc"].append(dict(fam=fam, trades=len(G), names=G.symbol.nunique(), per_name_setup=float(g.mean()),
                            names_ge3=int((g >= 3).sum()), share_trades_in_ge3=float(g[g >= 3].sum() / len(G))))
# B on live: lab FIT+CHECK shrunk ranks per setup -> live top/bottom decile
B1 = pd.read_parquet(T + "bk_t1.parquet"); B1 = B1[~B1.rnd & B1.half.isin(["fit", "check"])]
for s, f in B1.groupby("setup"):
    mu = f.r.mean(); g = f.groupby("symbol").r.agg(["size", "mean"])
    g["shr"] = (g["size"] * g["mean"] + 20 * mu) / (g["size"] + 20); q = g[g["size"] >= 3]
    if len(q) < 30: continue
    top, bot = set(q.index[q.shr >= q.shr.quantile(.9)]), set(q.index[q.shr <= q.shr.quantile(.1)])
    G = L[L.setup == s]
    it, ib = G.symbol.isin(top), G.symbol.isin(bot)
    out["B"].append(dict(setup=s[:28], live_n=len(G), top_n=int(it.sum()), top_avg=float(G.r[it].mean()) if it.sum() else None,
                         bot_n=int(ib.sum()), bot_avg=float(G.r[ib].mean()) if ib.sum() else None,
                         rest_avg=float(G.r[~(it | ib)].mean()), unranked_share=float((~G.symbol.isin(q.index)).mean())))
json.dump(out, open(T + "live.json", "w"), indent=1, default=float)
print(json.dumps({k: out[k] for k in ("X", "W", "B", "conc")}, indent=1, default=lambda x: round(float(x), 3)))
