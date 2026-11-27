"""TICKSEL: score the pre-registered configs ONCE on CHECK and T2, live direction check. Educational only."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ticksel")
from lib2 import *
import tk
from prep import HOME, FAM
T = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ticksel/"
cfg = json.load(open(T + "configs.json"))
etb = pd.read_parquet(T + "etb_rate.parquet").rate
RAW = {"check": pd.read_parquet(T + "raw_t1.parquet"), "t2": pd.read_parquet(T + "raw_t2.parquet")}
RAW["check"] = RAW["check"][RAW["check"].half == "check"]
BK1 = pd.read_parquet(T + "bk_t1.parquet"); BK2 = pd.read_parquet(T + "bk_t2.parquet")
BK = {"fit": BK1[(BK1.half == "fit") & ~BK1.rnd], "check": BK1[(BK1.half == "check") & ~BK1.rnd], "t2": BK2[~BK2.rnd]}
for k in ("check", "t2"): assert not RAW[k].date.between("2024-11-01", "2025-02-28").any()

def rebook(raw):
    return pd.concat([tk.book(g, tk.BOOK[HOME[s]], etb) for s, g in raw.groupby("setup")], ignore_index=True)

def fam_setups(fam): return [s for s, f in FAM.items() if f == fam]

def setup_rows(base, new):
    out = []
    for s in sorted(set(base.setup)):
        a, b = base[base.setup == s], new[new.setup == s]
        w, sh = wobd(b.r, b.date)
        out.append(dict(setup=s[:28], base_n=len(a), new_n=len(b), kept=len(b) / max(len(a), 1), base_avg=a.r.mean(),
                        new_avg=b.r.mean(), base_tot=a.r.sum(), new_tot=b.r.sum(), d_tot=b.r.sum() - a.r.sum(),
                        d_tot_adj=b.r_adj.sum() - a.r_adj.sum(), new_wobd=w, new_best_share=sh))
    return out

res = {"X": [], "W": [], "B": []}
for c in cfg["X"]:
    cuts = cfg["cuts"][f"{c['fam']}|{c['trait']}"]
    for h in ("check", "t2"):
        raw = RAW[h][RAW[h].setup.isin(fam_setups(c["fam"]))]
        base = BK[h][BK[h].fam == c["fam"]]
        ex_raw = bucket(raw, c["trait"], cuts) == c["bucket"]
        new = rebook(raw[~ex_raw])
        ind = bucket(base, c["trait"], cuts) == c["bucket"]
        d, t = diff_t(base.r, ind, base.date)
        da, ta = diff_t(base.r_adj, ind, base.date)
        rec = dict(id=c["id"], half=h, fam=c["fam"], rule=f"{c['trait']}={c['bucket']}", ex_n=int(ind.sum()),
                   ex_share=float(ind.mean()), ex_avg=float(base.r[ind].mean()), ex_avg_adj=float(base.r_adj[ind].mean()),
                   kept_avg=float(base.r[~ind].mean()), diff=d, t=t, diff_adj=da, t_adj=ta,
                   base=summ(base.r, base.date), new=summ(new.r, new.date), new_adj_tot=float(new.r_adj.sum()),
                   base_adj_tot=float(base.r_adj.sum()), setups=setup_rows(base, new))
        if h == "check":
            fr = ex_raw.mean()
            rng = np.random.default_rng(7); tots = []
            for _ in range(60):
                keep = np.ones(len(raw), bool)
                for s, idx in raw.groupby("setup").indices.items():
                    k = int(round(ex_raw[idx].sum()))
                    if k: keep[rng.choice(idx, k, replace=False)] = False
                tots.append(rebook(raw[keep]).r.sum())
            rec["rand_pct"] = float((np.array(tots) < new.r.sum()).mean())
            rec["rand_mean_tot"] = float(np.mean(tots))
        res["X"].append(rec); print(c["id"], h, rec["rule"], rec["ex_n"], round(rec["ex_avg"], 3), round(rec["kept_avg"], 3),
                                     round(t, 2), "tot", round(rec["base"]["tot"], 1), "->", round(rec["new"]["tot"], 1), flush=True)
for c in cfg["W"]:
    cuts = cfg["cuts"][f"{c['fam']}|{c['trait']}"]
    for h in ("check", "t2"):
        base = BK[h][BK[h].fam == c["fam"]]
        bk = bucket(base, c["trait"], cuts)
        w = np.where(bk == c["up"], 1.5, np.where(bk == c["down"], 0.5, 1.0))
        for col in ("r", "r_adj"):
            sized = (w * base[col]).sum() / w.sum()
            z = (w - 1) * (base[col] - base[col].mean())
            rec = dict(id=c["id"], half=h, col=col, fam=c["fam"], rule=f"{c['trait']}: 1.5x {c['up']}, 0.5x {c['down']}",
                       unsized=float(base[col].mean()), sized=float(sized), lift=float(sized - base[col].mean()),
                       t=ct(z, base.date), up_avg=float(base[col][bk == c["up"]].mean()), down_avg=float(base[col][bk == c["down"]].mean()),
                       per_setup={s[:24]: float((w[m] * base[col][m]).sum() / w[m].sum() - base[col][m].mean())
                                  for s in sorted(set(base.setup)) for m in [(base.setup == s).to_numpy()]})
            res["W"].append(rec); print(rec["id"], h, col, rec["rule"], round(rec["unsized"], 4), round(rec["sized"], 4), round(rec["t"], 2), flush=True)
# ---- B: individual tickers
F = BK["fit"]
for s in sorted(set(F.setup)):
    f = F[F.setup == s]; mu = f.r.mean()
    g = f.groupby("symbol").r.agg(["size", "mean"])
    g["shr"] = (g["size"] * g["mean"] + 20 * mu) / (g["size"] + 20)
    q = g[g["size"] >= 3]
    if len(q) < 30: res["B"].append(dict(setup=s, note=f"only {len(q)} FIT symbols with >=3 trades")); continue
    lo_c, hi_c = q.shr.quantile(0.1), q.shr.quantile(0.9)
    bot, top = set(q.index[q.shr <= lo_c]), set(q.index[q.shr >= hi_c])
    rec = dict(setup=s, fit_syms=len(g), ranked=len(q), fit_trades_per_sym=float(g["size"].mean()))
    for h in ("check", "t2"):
        b = BK[h][BK[h].setup == s]
        if not len(b): continue
        it, ib = b.symbol.isin(top), b.symbol.isin(bot)
        dd, tt = diff_t(b.r[it | ib], it[it | ib], b.date[it | ib]) if (it.sum() >= 3 and ib.sum() >= 3) else (np.nan, np.nan)
        ch = b.groupby("symbol").r.agg(["size", "mean"])
        j = q.join(ch, rsuffix="_h", how="inner"); j = j[j["size_h"] >= 3]
        rho = j.shr.corr(j["mean_h"], method="spearman") if len(j) >= 10 else np.nan
        raw = RAW[h][RAW[h].setup == s]
        nb1 = rebook(raw[~raw.symbol.isin(bot)])
        w = np.where(it, 1.5, 1.0)
        rec[h] = dict(n=len(b), top_n=int(it.sum()), top_avg=float(b.r[it].mean()), bot_n=int(ib.sum()), bot_avg=float(b.r[ib].mean()),
                      rest_avg=float(b.r[~(it | ib)].mean()), top_minus_bot=dd, t=tt, spearman=rho, spearman_n=len(j),
                      B1_base_tot=float(b.r.sum()), B1_new_tot=float(nb1.r.sum()), B1_kept=len(nb1) / len(b),
                      B1_new_avg=float(nb1.r.mean()), B2_sized=float((w * b.r).sum() / w.sum()), B2_unsized=float(b.r.mean()))
    res["B"].append(rec); print("B", s[:26], json.dumps({k: rec.get(k) for k in ("check", "t2")}, default=lambda x: round(float(x), 3))[:600], flush=True)
json.dump(res, open(T + "scores.json", "w"), indent=1, default=float)
