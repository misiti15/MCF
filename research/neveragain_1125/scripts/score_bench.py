"""NEVERAGAIN bench scoring vs NOW (PLAN.md). Usage: python score_bench.py WORK CFG[,CFG..]. Educational only."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

W = Path(sys.argv[1]); CFGS = sys.argv[2].split(",")
S = ["L3", "RW3", "RW5", "NM-ETF"]


def per(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    return "CHECK" if d >= "2025-10-01" else "T2"


def load(book, cfg):
    x = pd.read_parquet(W / f"day_{book}_{cfg}.parquet")
    x = x[x.scored].set_index("date")
    x["R"] = x[[f"R{i}" for i in range(4)]].sum(axis=1); x["lots"] = x[[f"N{i}" for i in range(4)]].sum(axis=1)
    x["per"] = x.index.map(per)
    return x


def tstat(v):
    v = np.asarray(v, float); s = v.std(ddof=1)
    return v.mean() / s * np.sqrt(len(v)) if s > 0 else np.nan


rows = []; ps = []
for book in ("RAW", "NEUTRAL", "P10"):
    try:
        base = load(book, "NOW")
    except FileNotFoundError:
        continue
    for cfg in CFGS:
        try:
            x = load(book, cfg)
        except FileNotFoundError:
            continue
        for P in ("FIT", "T2", "CHECK", "ALL"):
            b = base if P == "ALL" else base[base.per == P]
            c = x.loc[b.index]
            dr = c.R - b.R; yrs = len(b) / 252
            rows.append(dict(book=book, cfg=cfg, per=P, n=len(b), R=round(c.R.sum(), 1), dR=round(dr.sum(), 1),
                             dR_yr=round(dr.sum() / yrs, 1), t=round(tstat(dr), 2),
                             worst=round(c.R.min(), 1), worst_now=round(b.R.min(), 1),
                             w5=round(c.R.nsmallest(5).mean(), 1), w5_now=round(b.R.nsmallest(5).mean(), 1),
                             le10=int((c.R <= -10).sum()), le10_now=int((b.R <= -10).sum()),
                             red=int((c.R < 0).sum()), red_now=int((b.R < 0).sum()),
                             r2g=int(((b.R < 0) & (c.R > 0)).sum()), g2r=int(((b.R > 0) & (c.R < 0)).sum()),
                             lots=int(c.lots.sum()), lots_now=int(b.lots.sum()),
                             stop_yr=round((c.stop_m >= 0).sum() / yrs, 1), g1_yr=round(c.g1.sum() / yrs, 1),
                             g2_yr=round((c.g2 > 0).sum() / yrs, 1), g3_yr=round((c.g3 > 0).sum() / yrs, 1)))
            if P == "ALL":
                for i, s in enumerate(S):
                    d = c[f"R{i}"] - b[f"R{i}"]
                    ps.append(dict(book=book, cfg=cfg, setup=s, dR=round(d.sum(), 1), better_days=int((d > 0.01).sum()),
                                   worse_days=int((d < -0.01).sum())))
out = pd.DataFrame(rows); pso = pd.DataFrame(ps)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
print(out.to_string(index=False)); print(pso.to_string(index=False))
out.to_csv(W.parent / "bench_results.csv", index=False); pso.to_csv(W.parent / "bench_per_setup.csv", index=False)
