"""SQUEEZE_1125 scoring (PREREG.md metrics + pass bar). Usage: python score.py W. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

W = Path(sys.argv[1])
SH = ["L3-fromopen", "RW3", "RW5", "NM-ETF"]
REM = ["B8", "B12", "B16", "SV", "SO"]
PERS = ["FIT", "CHECK", "T2", "ALL"]


def load(book, cfg):
    x = pd.read_parquet(W / f"day_{book}_{cfg}.parquet")
    x["R"] = x[[f"R{s}" for s in range(4)]].sum(1)
    return x


def sub(x, p):
    return x if p == "ALL" else x[x.per == p]


def metrics(c, r, p):
    c, r = sub(c, p), sub(r, p)
    n = len(c); yrs = n / 252
    d = c.R.to_numpy() - r.R.to_numpy()
    rec = (r.trough <= -10) & (r.R >= r.trough / 2)
    w5c = np.sort(c.R.to_numpy())[:5].mean(); w5r = np.sort(r.R.to_numpy())[:5].mean()
    best = d.max() if len(d) else 0
    out = dict(per=p, n=n, R=c.R.sum(), refR=r.R.sum(), dR=d.sum(), dRyr=d.sum() / yrs, avg=c.R.mean(),
               w5=w5c, refw5=w5r, w5imp=(w5c - w5r) / abs(w5r), le10=int((c.R <= -10).sum()),
               refle10=int((r.R <= -10).sum()), giveup=d[rec.to_numpy()].sum(), nrec=int(rec.sum()),
               best_share=best / d.sum() if d.sum() > 0 else np.nan,
               dR_wo_best_per_day=(d.sum() - best) / max(n - 1, 1),
               fires_r1=(c.r1blk > 0).sum() / yrs, trig_r2=((c.s_k >= 0) | (c.l_k >= 0)).sum() / yrs,
               act_r2=c.r2act.sum() / yrs, lots=int(c[[f"N{s}" for s in range(4)]].sum().sum()),
               reflots=int(r[[f"N{s}" for s in range(4)]].sum().sum()))
    for s in range(4):
        out[f"d_{SH[s]}"] = c[f"R{s}"].sum() - r[f"R{s}"].sum()
    return out


rows = []
for book in ("RAW", "NEUTRAL"):
    base, lo = load(book, "BASE"), load(book, "LO")
    for p in PERS:
        rows.append(dict(book=book, cfg="LO", ref="BASE", **metrics(lo, base, p)))
    for cfg in REM:
        for name, ref, rn in ((cfg, base, "BASE"), ("LO+" + cfg, lo, "LO"), ("LO+" + cfg, base, "BASE")):
            c = load(book, name)
            for p in PERS:
                rows.append(dict(book=book, cfg=name, ref=rn, **metrics(c, ref, p)))
R = pd.DataFrame(rows)
R.to_csv(W / "results.csv", index=False)


def verdict(df, cfg, ref):
    g = df[(df.book == "RAW") & (df.cfg == cfg) & (df.ref == ref)].set_index("per")
    c1 = g.loc["CHECK", "w5imp"] >= 0.20 and g.loc["T2", "w5imp"] >= 0.20
    c2 = g.loc["CHECK", "dRyr"] >= -2.5
    worse = sum(g.loc["ALL", f"d_{s}"] < -1e-9 for s in SH)
    c3 = worse < 2
    return c1, c2, c3, worse


pd.set_option("display.width", 250)
cols = ["per", "n", "R", "refR", "dR", "dRyr", "avg", "w5", "refw5", "w5imp", "le10", "refle10", "giveup", "nrec",
        "best_share", "fires_r1", "trig_r2", "act_r2", "lots", "reflots"] + [f"d_{s}" for s in SH]
for book in ("RAW", "NEUTRAL"):
    print("=" * 30, book)
    for (cfg, ref), g in R[R.book == book].groupby(["cfg", "ref"], sort=False):
        print(f"--- {cfg} vs {ref}")
        print(g[cols].round(2).to_string(index=False))
print("=" * 30, "VERDICT (RAW; bar judged vs LO; also vs BASE)")
for cfg in REM:
    a = verdict(R, "LO+" + cfg, "LO"); b = verdict(R, cfg, "BASE"); c = verdict(R, "LO+" + cfg, "BASE")
    print(cfg, "on LO:", a, "PASS" if all(a[:3]) else "FAIL", "| alone vs BASE:", b, "PASS" if all(b[:3]) else "FAIL",
          "| LO+ vs BASE:", c)
