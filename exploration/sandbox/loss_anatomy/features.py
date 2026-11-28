"""Per-lot book features: entry bursts, concurrency, same-name restacks, stop clusters. Per account (each account is
its own book). Writes <scratch>/feat.parquet. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import load
S = sys.argv[1]; t = load(S); t = t[t.book != "graveyard"].copy()
t = t.sort_values(["account", "date", "entry_et"]).reset_index(drop=True)
out = []
for (acct, d), g in t.groupby(["account", "date"], sort=False):
    g = g.copy(); e = g.entry_et.values; x = g.exit_et.values; sd = g.side.values
    burst = np.zeros(len(g), int); conc = np.zeros(len(g), int); concall = np.zeros(len(g), int); scl = np.zeros(len(g), int)
    isstop = (g.exit_reason == "stop").values
    for i in range(len(g)):
        m = (sd == sd[i]) & (e <= e[i]) & (e > e[i] - np.timedelta64(15, "m"))
        burst[i] = m.sum()
        conc[i] = ((sd == sd[i]) & (e < e[i]) & (x > e[i])).sum()
        concall[i] = ((e < e[i]) & (x > e[i])).sum()
        if isstop[i]:
            scl[i] = (isstop & (np.abs(x - x[i]) <= np.timedelta64(10, "m"))).sum()
    g["burst15"] = burst; g["conc_side"] = conc; g["conc_all"] = concall; g["stop_cluster"] = scl
    g["name_lot"] = g.groupby("symbol").cumcount() + 1
    g["setup_name_lot"] = g.groupby(["strategy", "symbol"]).cumcount() + 1
    g["day_lot"] = np.arange(1, len(g) + 1)
    g["side_lot"] = g.groupby("side").cumcount() + 1
    out.append(g)
f = pd.concat(out); f.to_parquet(f"{S}/feat.parquet"); print(len(f))
