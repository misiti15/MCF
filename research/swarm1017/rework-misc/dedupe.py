"""De-duplicate the quality near-misses (PLAN: rank by min(t_train, t_valid), drop >= 60% trade overlap) and add
neighbour checks (same rule on the other geometries). Educational only - not financial advice."""
import json
import numpy as np
import pandas as pd
from common import SCR, Fam, load, CODE_NEEDED
from gate import parts_for

CUTS = json.load(open(SCR / "cuts.json"))["atr"]
out = []
for fam, src in (("HS", ("hs", 125)), ("HL", ("hl", 125))):
    g = pd.read_parquet(SCR / f"{fam}_gated.parquet")
    q = g[g.quality].copy()
    q["mt"] = q[["t_tr", "t_va"]].min(axis=1)
    q = q.sort_values("mt", ascending=False)
    FM = Fam(load(*src), CUTS)
    sc = pd.read_parquet(SCR / f"{fam}_scan.parquet")
    kept = []
    for _, row in q.iterrows():
        ix = set(np.concatenate([p[0] for p in parts_for(fam, FM, row.to_dict())]).tolist())
        if any(len(ix & k[1]) >= 0.6 * min(len(ix), len(k[1])) for k in kept):
            continue
        kept.append((row, ix))
    for row, ix in kept:
        nb = sc[(sc.stage == row.stage) & (sc.cfg == row.cfg) & (sc.window == row.window) & (sc.side == row.side)
                & (sc.refire == row.refire) & (sc.geom != row.geom)]
        fl = [x for x in (row.get("f1"), row.get("f2")) if isinstance(x, str)]
        out.append({**row.to_dict(), "n_unique": len(ix),
                    "geom_neighbours": ";".join(f"{r.geom}:{r.exp_tr:+.3f}/{r.exp_va:+.3f}" for r in nb.itertuples()),
                    "live_supported": not any(f in CODE_NEEDED for f in fl)})
d = pd.DataFrame(out)
d.to_csv(SCR / "nearmiss.csv", index=False)
pd.set_option("display.width", 250)
print(d[["fam", "stage", "cfg", "window", "side", "geom", "refire", "n_all", "exp_tr", "exp_va", "t_all", "t_bar", "up_exp",
         "down_exp", "wf_share", "xt_all", "ex_best_day", "per_day", "live_supported", "geom_neighbours"]].round(3).to_string())
