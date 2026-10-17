"""Gate the scan (PLAN.md gates 1-5 screen; walk-forward / regime re-checked exactly with mcf.research.gates in verify.py).
Educational only - not financial advice.   python gate.py <scratch>  -> results.csv (screen survivors + near-misses), counts.json"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
scr = Path(sys.argv[1])
PRIOR = {"B1": 356381, "B2": 272, "B4": 354, "B5": 31290, "A7": 83300}
D = pd.concat([pd.read_parquet(p) for p in sorted(scr.glob("scan_*.parquet"))], ignore_index=True)
D["lin"] = D["fam"].replace({"B4a": "B4", "B4b": "B4"})
N = D.groupby("lin").size().to_dict()
bars = {k: round(max(1.5, math.sqrt(2 * math.log(PRIOR[k] + N[k]))), 3) for k in PRIOR}
D["bar"] = D["lin"].map(bars)
D["pos"] = (D.exp_tr > 0) & (D.exp_va > 0)
D["g_n"] = D.n_all >= 200
D["g_reg"] = (D.n_up >= 30) & (D.n_dn >= 30) & (D.exp_up > 0) & (D.exp_dn > 0)
D["g_rand"] = (D.xs_tr > 0) & (D.xs_va > 0)
D["g_wf"] = D.wf >= 0.6
D["g_t"] = D.t_all >= D.bar
D["screen"] = D.pos & D.g_n & D.g_reg & D.g_rand & D.g_wf & D.g_t
D["near"] = D.pos & D.g_n & D.g_reg & D.g_rand & ~D.screen
counts = {"configs_per_family": D.groupby("fam").size().to_dict(), "N_study": int(len(D)), "N_lineage_this": N,
          "prior": PRIOR, "bars": bars,
          "pass_pos_n": int((D.pos & D.g_n).sum()), "pass_pos_n_reg": int((D.pos & D.g_n & D.g_reg).sum()),
          "pass_pos_n_reg_rand": int((D.pos & D.g_n & D.g_reg & D.g_rand).sum()),
          "pass_plus_wf": int((D.pos & D.g_n & D.g_reg & D.g_rand & D.g_wf).sum()),
          "screen_all": int(D.screen.sum()),
          "per_family_near": D[D.near].groupby("fam").size().to_dict(),
          "max_t_near": D[D.near].groupby("fam")["t_all"].max().round(2).to_dict()}
print(json.dumps(counts, indent=1))
keep = D[D.near | D.screen].sort_values("t_all", ascending=False)
keep.to_csv(HERE / "results.csv", index=False, float_format="%.4f")
json.dump(counts, open(HERE / "counts.json", "w"), indent=1, default=int)
pd.set_option("display.width", 250)
cols = ["fam", "stage", "vid", "side", "exit", "win", "pick", "f1", "f2", "n_all", "exp_tr", "exp_va", "t_all", "xs_all", "exp_up", "exp_dn", "wf", "bar"]
for f, g in keep.groupby("fam"):
    print(g[cols].head(12).to_string(index=False))
