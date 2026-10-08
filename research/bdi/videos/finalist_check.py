"""Extra checks on the finalists (not gates): every exit for the same mask, valid ex-top-3-days, trade overlap.
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import scan  # noqa: E402

fin = json.load(open(HERE / "finalists.json"))
sc = scan.S(scan.frame())
rows, sets = [], []
for k, r in enumerate(fin, 1):
    v = json.loads(r["var"])
    s = 1 if r["side"] == "long" else -1
    combo = tuple(x for x in r["layers"].split("+") if x != "-")
    base = np.asarray(scan.trig(sc.D, r["fam"], s, v, dict(scan.BASE[r["fam"]]), "t1s1"), bool) & sc.W[r["window"]]
    for nm in combo:
        base &= np.asarray(scan.layer(sc.D, nm, s), bool)
    for ex in ("t1s1", "t05s1", "t1s05", "jd", "e9c1", "c9", "trail9", "tx"):
        rr = sc.outcome(s, ex, v, r["fam"], dict(scan.BASE[r["fam"]]))
        i = np.flatnonzero(base & np.isfinite(rr))
        keep = np.r_[True, sc.sid[i][1:] != sc.sid[i][:-1]]
        i = i[keep]
        st = sc.stats(i, rr[i])
        row = {"finalist": k, "exit": ex, "tr_n": st["tr"]["n"], "tr_exp": st["tr"]["exp"], "tr_t": st["tr"]["t"],
               "va_n": st["va"]["n"], "va_exp": st["va"]["exp"], "va_t": st["va"]["t"]}
        if ex == r["exit"]:
            va = i[sc.valid[i]]
            d = pd.Series(rr[va]).groupby(sc.dayid[va]).sum().sort_values()
            top3 = set(d.index[-3:])
            m3 = ~np.isin(sc.dayid[va], list(top3))
            row["va_ex_top3_days"] = float(rr[va][m3].mean()) if m3.any() else np.nan
            row["va_days"] = int(d.size)
            sets.append(set(sc.sid[i].tolist()))
        rows.append(row)
X = pd.DataFrame(rows)
X.to_csv(HERE / "finalist_exits.csv", index=False, float_format="%.4f")
print(X.round(3).to_string())
ov = np.array([[len(a & b) / max(1, min(len(a), len(b))) for b in sets] for a in sets])
print("symbol-day overlap (share of the smaller set):")
print(pd.DataFrame(ov, index=range(1, len(sets) + 1), columns=range(1, len(sets) + 1)).round(2).to_string())
