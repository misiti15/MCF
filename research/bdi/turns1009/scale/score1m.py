"""Score stage C (amendment A1): 80 lines from data/trades1m.parquet with mcf.research.gates.
Writes results_stageC.csv. Educational only - not financial advice."""
import numpy as np
import pandas as pd

from common import DATA, HERE, TRAIN_END, lib
from mcf.research import gates

T_BAR = 4.68
tr = pd.read_parquet(DATA / "trades1m.parquet")
reg = lib.regimes()
from score import setup, stats

S = setup()
D = len(S["dates"])
rows = []
for (side, sig), g in tr.groupby(["side", "sig"]):
    for take in ("all", "first"):
        x = g[g[take]]
        for ex in ("fixed", "trail"):
            for hed in (False, True):
                r = x[("h_" if hed else "r_") + ex].to_numpy(float)
                ok = np.isfinite(r)
                dd = x["d"].to_numpy()[ok]
                n_d = np.bincount(dd, minlength=D)[None].astype(float)
                s_d = np.bincount(dd, weights=r[ok], minlength=D)[None]
                st = {k: float(v[0]) for k, v in stats(n_d, s_d, S).items()}
                rows.append({"side": side, "sig": sig, "take": take, "exit": ex, "hedged": hed, **st,
                             "per_session": st["n"] / D,
                             "win_fixed": float(x["win_fixed"].mean()) if ex == "fixed" else np.nan})
o = pd.DataFrame(rows)
o["pass"] = ((o.n >= 150) & (o.exp > 0) & (o.t >= T_BAR) & (o.up_exp > 0) & (o.down_exp > 0) & (o.wf_share >= 0.6)
             & (o.ex_best > 0) & (o.busiest <= 0.10) & (o.train_exp > 0) & (o.valid_exp > 0))
o.round(4).to_csv(HERE / "results_stageC.csv", index=False)
pd.set_option("display.width", 250)
print(o.round(3).to_string())
print("pass:", int(o["pass"].sum()), "of", len(o))
