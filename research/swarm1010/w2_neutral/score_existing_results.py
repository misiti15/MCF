"""Task 1 scoring (NOTES 1.4) of data/existing_trades.parquet written by score_existing.py (split in two after a container
restart killed the first run during scoring). Writes existing_results.csv. Educational only - not financial advice."""
import math

import numpy as np
import pandas as pd

from common import DATA, HERE, bars, lib
from hedge import bar_check, score

dates = bars()["dates"]
reg = lib.regimes()
T = pd.read_parquet(DATA / "existing_trades.parquet",
                    columns=["d", "r", "list", "set", "side", "geom", "beta_spy", "beta_sec", "r_spy", "r_sec"])
T["date"] = np.array(dates, dtype=object)[T["d"].to_numpy()]

# ---------------------------------------------------------------- scoring
LIN = [("heat", 19200), ("exhaustion", 855600), ("MF", 8012), ("NS", 7374), ("RW2", 934522), ("RW1", 82068),
       ("RW3", 82068), ("RW5", 82068), ("RW7", 82068), ("RW", 81430), ("ST", 120500), ("L3", 11178), ("RDT", 2551)]


def lineage_n(nm):
    for k, n in LIN:
        if nm.startswith(k):
            return n
    return max(n for _, n in LIN)


rows = []
for nm, g in T.groupby("list", observed=True):
    both = g[np.isfinite(g["r_spy"]) & np.isfinite(g["r_sec"])]
    treq = round(max(2.0, math.sqrt(2 * math.log(lineage_n(nm) + 206))), 3)
    print(nm, len(both), flush=True)
    for hedge, col in (("none", "r"), ("SPY", "r_spy"), ("SEC", "r_sec")):
        o = score(pd.DataFrame({"date": both["date"].to_numpy(), "r": both[col].to_numpy(float)}), reg)
        okb, fails = bar_check(o, treq)
        rows.append({"part": "existing", "list": nm, "set": g["set"].iloc[0], "side": g["side"].iloc[0],
                     "geom": g["geom"].iloc[0], "hedge": hedge, "n_all": len(g), "t_req": treq,
                     "beta_mean": round(float(both["beta_spy" if hedge != "SEC" else "beta_sec"].mean()), 3), **o,
                     "pass": okb if hedge != "none" else None, "fails": ";".join(fails)})
res = pd.DataFrame(rows)
res.to_csv(HERE / "existing_results.csv", index=False)
print(res[res.hedge != "none"]["pass"].sum(), "pass of", (res.hedge != "none").sum())
