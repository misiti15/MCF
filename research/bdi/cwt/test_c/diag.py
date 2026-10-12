"""Tightening diagnostics for the package C candidates (not counted as configurations; they can only remove a
candidate): 2x costs, top-300 names by 20-day dollar volume (less survivorship), 2016 cohort only (names with a bar on
2016-01-04), per-instrument for C7. Writes diag.csv and data/trades_candidates.parquet. Educational only - not
financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

import common as cm
import families as fa

CANDS = {"C1_L_rsi2_5_none_L5_sma5": lambda: fa.c1_long("rsi2_5", "none", 0.05, "sma5"),
         "C1_L_rsi3_15_none_L3_sma5": lambda: fa.c1_long("rsi3_15", "none", 0.03, "sma5"),
         "C7_streak3_upclose": lambda: fa.c7_streak(3, "upclose")}
rank = np.argsort(np.argsort(-np.nan_to_num(np.where(cm.ELIG, cm.adv20, np.nan), nan=-1), axis=1), axis=1)
TOP300 = rank < 300
COHORT = np.isfinite(cm.Cn[0])
rows = []
allt = []


def summ(name, var, t):
    d = t.date
    out = {"id": name, "variant": var}
    for s, (a, b) in cm.SPLITS.items():
        g = t[(d >= a) & (d <= b)]
        out[f"{s}_n"] = len(g); out[f"{s}_exp"] = round(g.net.mean() * 1e4, 1) if len(g) else np.nan
    tv = t[d <= "2024-10-31"]
    hold = max(1, int(np.median(t.hold)))
    out["trainvalid1_t"] = round(cm.clust_t(tv.net, tv.i // max(1, 2 * hold) if hold > 1 else tv.i), 2)
    out["avg_cost_bps"] = round(float((cm.cost(t.ep) + cm.cost(t.xp)).mean()) * 1e4, 1)
    out["avg_hold"] = round(float(t.hold.mean()), 2)
    out["exit_reasons"] = t.why.value_counts(normalize=True).round(2).to_dict() if "why" in t else None
    rows.append(out)


for cid, fn in CANDS.items():
    t = fn()
    allt.append(t.assign(cid=cid))
    summ(cid, "as scored", t)
    t2 = t.copy(); t2["net"] = t2.net - cm.cost(t2.ep) - cm.cost(t2.xp)
    summ(cid, "2x costs", t2)
    if cid.startswith("C1"):
        summ(cid, "top-300 ADV names", t[TOP300[t.i, t.j]])
        summ(cid, "2016 cohort only", t[COHORT[t.j]])
        gapf = t.ep.to_numpy() >= cm.Ox[t.ei, t.j] - 1e-9
        summ(cid, "fills at the open (gapped below the limit)", t[gapf])
        summ(cid, "fills at the limit (intraday touch)", t[~gapf])
    else:
        for s in ("SPY", "QQQ", "IWM"):
            summ(cid, f"{s} only", t[t.j == cm.col[s]])
pd.DataFrame(rows).to_csv(cm.HERE / "diag.csv", index=False)
pd.concat(allt, ignore_index=True).to_parquet(cm.DATA / "trades_candidates.parquet")
pd.set_option("display.width", 250)
print(pd.DataFrame(rows).drop(columns=["exit_reasons"]).to_string(index=False))
print(pd.DataFrame(rows)[["id", "variant", "exit_reasons"]].head(1).to_string())
