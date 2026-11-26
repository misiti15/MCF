"""TAPE-1126 S1 on the two long contenders, standalone at trade level (deviation from PREREG, disclosed in REPORT: REGSTEER-1's
bench10 lots carry no 1-min paths, so the per-setup minute book cannot be run; all raw signals, LR8 research costs for longs).
Betas as squeeze_1125 (research/squeeze_1125/build.py betas). Usage (cwd repo): python cont.py RS_CAND SIGW OUT.
Educational only - not financial advice."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

CAND, SW, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.argv = [sys.argv[0], str(OUT)]
sys.path.insert(0, "research/squeeze_1125")
import build as SB  # noqa: E402

CONT = ["GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long",
        "GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long"]


def tstat(d):
    d = np.asarray(d, float)
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 2 and d.std() > 0 else np.nan


if __name__ == "__main__":
    x = pd.read_parquet(CAND); x = x[x.setup.isin(CONT)].copy(); x["date"] = x.date.astype(str)
    SB.no_locked(x.date.unique())
    bb = SB.betas(x); x = x.merge(bb, on=["symbol", "date"], how="left")
    x["beta"] = np.where(x.nobs.ge(20) & x.beta.notna(), np.clip(0.67 * x.beta + 0.33, -3, 3), 1.0)
    SG = np.load(SW / "sig.npz"); pos = {d: i for i, d in enumerate(SG["days"].astype(str))}
    x = x[x.date.isin(pos)].reset_index(drop=True)
    fo = SG["fo5"][x.date.map(pos).to_numpy(), np.clip(x.em.to_numpy() - 570, 0, 390)]
    elig = (x.em >= 690) & (x.side > 0) & (x.beta > 0)
    flag = elig & (fo <= -0.003)
    res = {}
    for s in CONT:
        R = res[s[:13]] = {}
        for sp in ("FIT", "CHECK", "T2"):
            g = x[(x.setup == s) & (x.per == sp)]
            if not len(g):
                continue
            e, f = elig[g.index], flag[g.index]
            p = f[e].mean() if e.any() else 0.0
            days = sorted(g.date.unique())
            base = g.groupby("date").r.sum().reindex(days)
            cfg = g[~f].groupby("date").r.sum().reindex(days).fillna(0)
            const = (g.r * np.where(e, 1 - p, 1)).groupby(g.date).sum().reindex(days)
            rng = np.random.default_rng(1126)
            rnd = pd.concat([g[~(e & (rng.random(len(g)) < p))].groupby("date").r.sum().reindex(days).fillna(0)
                             for _ in range(20)], axis=1).mean(1)
            R[sp] = dict(n=len(g), days=len(days), share_blocked=float(p), blocked=int(f.sum()),
                         blocked_avg=float(g.r[f].mean()) if f.any() else np.nan, base_avg_day=float(base.mean()),
                         d_avg=float((cfg - base).mean()), rand_d=float((rnd - base).mean()), const_d=float((const - base).mean()),
                         t_vs_rand=float(tstat(cfg - rnd)), t_vs_base=float(tstat(cfg - base)))
    json.dump(res, open(OUT / "cont.json", "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
