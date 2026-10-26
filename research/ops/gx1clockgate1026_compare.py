"""GX1 evidence (2026-10-26): old vs new lab gate replays per account per day (signals, submitted, trades, R) and the
trades only one gate took, matched on (session, setup, symbol).

    python research/ops/gx1clockgate1026_compare.py OLD_RUN NEW_RUN [accounts] [out.json]

Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

old_dir, new_dir = Path(sys.argv[1]), Path(sys.argv[2])
accts = (sys.argv[3] if len(sys.argv) > 3 else "primary,testing,testing2,graveyard,gen").split(",")


def load(d, acct):
    tr, sg = [], []
    for p in sorted((d / acct).glob("*/signals.csv.gz")):
        s = pd.read_csv(p)
        s["session"] = p.parent.name
        sg.append(s)
        t = pd.read_csv(p.parent / "trades.csv.gz")
        t["session"] = p.parent.name
        tr.append(t)
    sg = pd.concat(sg, ignore_index=True) if sg else pd.DataFrame()
    tr = pd.concat(tr, ignore_index=True) if tr else pd.DataFrame()
    return sg, tr


def dstat(r):
    r = np.asarray(r, float)
    return {"n": int(len(r)), "avg_r": round(float(r.mean()), 3) if len(r) else None,
            "total_r": round(float(r.sum()), 2) if len(r) else None,
            "se": round(float(r.std(ddof=1) / np.sqrt(len(r))), 3) if len(r) > 1 else None}


out = {}
for a in accts:
    so, to = load(old_dir, a)
    sn, tn = load(new_dir, a)
    if so.empty and sn.empty:
        continue
    rows = []
    for day in sorted(set(so.get("session", [])) | set(sn.get("session", []))):
        o, n = so[so.session == day], sn[sn.session == day]
        ot, nt = to[to.session == day] if len(to) else to, tn[tn.session == day] if len(tn) else tn
        rows.append({"day": day, "sig_old": len(o), "sig_new": len(n),
                     "sub_old": int((o.status == "submitted").sum()), "sub_new": int((n.status == "submitted").sum()),
                     "trades_old": len(ot), "trades_new": len(nt),
                     "R_old": round(float(ot.r_multiple.sum()), 2) if len(ot) else 0.0,
                     "R_new": round(float(nt.r_multiple.sum()), 2) if len(nt) else 0.0})
    key = ["session", "strategy", "symbol"]
    ko = set(map(tuple, to[key].values)) if len(to) else set()
    kn = set(map(tuple, tn[key].values)) if len(tn) else set()
    added = tn[[tuple(x) not in ko for x in tn[key].values]] if len(tn) else tn
    lost = to[[tuple(x) not in kn for x in to[key].values]] if len(to) else to
    sko = set(map(tuple, so[key].values)) if len(so) else set()
    skn = set(map(tuple, sn[key].values)) if len(sn) else set()
    # added-trades R excluding the best session (owner one-big-day check)
    a_by = added.groupby("session").r_multiple.sum() if len(added) else pd.Series(dtype=float)
    best = a_by.idxmax() if len(a_by) else None
    wo = added[added.session != best] if best else added
    out[a] = {"days": rows,
              "signals_added": len(skn - sko), "signals_lost": len(sko - skn),
              "trades_added": dstat(added.r_multiple) if len(added) else dstat([]),
              "trades_added_wo_best_day": dstat(wo.r_multiple) if len(wo) else dstat([]),
              "best_day": best, "best_day_share": round(float(a_by.max() / a_by.sum()), 2) if len(a_by) and a_by.sum() else None,
              "trades_lost": dstat(lost.r_multiple) if len(lost) else dstat([]),
              "all_old": dstat(to.r_multiple) if len(to) else dstat([]),
              "all_new": dstat(tn.r_multiple) if len(tn) else dstat([])}
    print(f"== {a}")
    print(pd.DataFrame(rows).to_string(index=False))
    print({k: v for k, v in out[a].items() if k != "days"})
Path(sys.argv[4] if len(sys.argv) > 4 else "compare.json").write_text(json.dumps(out, indent=1, default=str))
