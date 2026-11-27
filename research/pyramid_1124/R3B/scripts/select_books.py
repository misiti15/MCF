"""R3B step 2: choose books on FIT only (configs B1..B9), freeze to frozen.json. Educational only - not financial advice."""
import json
import numpy as np, pandas as pd
from common import *

T = pd.read_parquet(P + "booked.parquet"); T["var"] = T["var"].str.replace("+spyopen", "+SPYOPEN")
F = T[T.half == "fit"]; ses = sessions()["fit"]; n = len(ses)
cands = SHORTS + [f"{l}+{g}" for l in LONGS for g in ("TT1", "SPYOPEN")]
tps = {v: len(F[F["var"] == v]) / n for v in cands}
w2 = {v: 1.0 / max(1.0, tps[v]) for v in cands}
avg = {v: F[F["var"] == v].r.mean() if (F["var"] == v).sum() else np.nan for v in cands}
ntr = {v: int((F["var"] == v).sum()) for v in cands}
D2 = {v: daily(F, v, ses, "r", w2[v]).to_numpy() for v in cands}
D1 = {v: daily(F, v, ses, "r", 1.0).to_numpy() for v in cands}

def score(book, D, lam=None, kind="lam"):
    d = sum(D[v] for v in book)
    if kind == "t":
        s = d.std(ddof=1); return d.mean() / s * np.sqrt(len(d)) if s > 0 else -9
    w5 = np.sort(d)[:5].mean()
    return d.mean() - lam * abs(w5)

CFG = {
    "B1": dict(D=D2, lam=0.05), "B2": dict(D=D2, lam=0.0), "B3": dict(D=D2, lam=0.15), "B4": dict(D=D2, kind="t"),
    "B5": dict(D=D2, lam=0.05, longs_n=(3,)), "B6": dict(D=D2, lam=0.05, gates=("TT1",)),
    "B7": dict(D=D2, lam=0.05, gates=("SPYOPEN",)), "B8": dict(D=D1, lam=0.05), "B9": dict(blind=True)}
out = {"weights_w2": w2, "fit_tps": tps, "fit_avg_r": avg, "fit_trades": ntr, "books": {}}
for k, c in CFG.items():
    best, bs, cnt = None, -1e9, 0
    for book in feasible(c.get("longs_n", (2, 3)), c.get("gates", ("TT1", "SPYOPEN"))):
        cnt += 1
        if c.get("blind"):
            if min(ntr[v] for v in book) < 20 or any(np.isnan(avg[v]) for v in book): continue
            s = sum(avg[v] for v in book)
        else:
            s = score(book, c["D"], c.get("lam"), c.get("kind", "lam"))
        if s > bs: bs, best = s, book
    out["books"][k] = {"book": list(best), "fit_objective": round(float(bs), 4), "books_enumerated": cnt}
    print(k, round(bs, 4), cnt, best)
json.dump(out, open(P + "frozen.json", "w"), indent=1, default=float)
