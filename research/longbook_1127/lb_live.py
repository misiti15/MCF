"""LONGBOOK-1127 live context: the 4 candidate longs (+ NM-ETF) from the live journals (all accounts, run 1, LR8 cost R,
identical signals once), vs Primary's live short book by day. Input: the all-account journal pickle built by
research/primadd2_1127/load.py (scratch). Usage: python lb_live.py ALL.pkl OUT.json. Paper results, not a record.
Educational only - not financial advice."""
import json, sys
import numpy as np, pandas as pd
d = pd.read_pickle(sys.argv[1]); d = d[d.run_id == 1].drop_duplicates(["strategy", "symbol", "date", "entry_time"])
C = {"L1 CWT14-WB5": "CWT14-failbrk-orl-p10-long-WB5", "L2 ULT-05": "ULT-05-withgap-cont-long",
     "L3 GEN-261027-10": "GEN-261027-10-", "L4 GEN-261023-07": "GEN-261023-07-", "NM-ETF (in Primary)": "NM-ETF-late-dip-di-long"}
pr = d[(d.account == "primary") & (d.side < 0)].groupby("date").r.sum()
out = {"window": [d.date.min(), d.date.max()], "primary_short_days": int(len(pr))}
for k, s in C.items():
    x = d[d.strategy.str.startswith(s) & (d.side > 0) & (d.account != "graveyard")]
    if s.startswith("NM-ETF"):
        x = x[x.strategy == s]
    dr = x.groupby("date").r.sum(); n = len(x)
    if not n:
        continue
    bd = dr.idxmax(); tot = dr.sum()
    e = x.r - x.r.mean(); ec = e.groupby(x.date).sum()
    j = pd.concat([dr, pr], axis=1, keys=["l", "p"]).dropna()
    red = j[j.p < 0]
    out[k] = dict(accounts=sorted(x.account.unique()), n=n, days=int(len(dr)), first=x.date.min(), avg=float(x.r.mean()),
                  wo_best=float((tot - dr[bd]) / (n - (x.date == bd).sum())) if n > (x.date == bd).sum() else None,
                  best_day=bd, best_share=float(dr[bd] / tot) if tot > 0 else None,
                  t=float(x.r.mean() * n / np.sqrt((ec ** 2).sum())), corr_primary_short=float(j.l.corr(j.p)) if len(j) > 2 else None,
                  overlap_days=int(len(j)), on_primary_red_days=float(red.l.sum()), primary_red_days=int(len(red)),
                  r_1125=float(dr.get("2026-11-25", 0.0)), r_1127=float(dr.get("2026-11-27", 0.0)))
json.dump(out, open(sys.argv[2], "w"), indent=1, default=str); print(json.dumps(out, indent=1, default=str))
