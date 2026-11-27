"""R3B step 3: score frozen books ONCE on CHECK and T2 (and FIT for reference) vs TOP10 / PRIMARY reference books.
Both cost bases (r = research LR8, r8 = LR8-lab). Educational only - not financial advice."""
import json
import numpy as np, pandas as pd
from common import *
fz = json.load(open(P + "frozen.json")); w2 = fz["weights_w2"]
T = pd.read_parquet(P + "booked.parquet"); T["var"] = T["var"].str.replace("+spyopen", "+SPYOPEN")
SES = sessions()
F = T[T.half == "fit"]
# reference weights from FIT tps of home variants
wref = {v: 1.0 / max(1.0, (F["var"] == v + "@home").sum() / len(SES["fit"])) for v in TOP10}
res = {}
for half in ("fit", "check", "T2"):
    H = T[T.half == half]; ses = SES[half]
    for col in ("r", "r8"):
        key = f"{half}|{col}"
        ref10 = {v: daily(H, v + "@home", ses, col, wref[v] * 0.5) for v in TOP10}
        refP = {v: daily(H, v + "@home", ses, col, wref[v] * 5 / 4) for v in PRIM}
        t10 = sum(ref10.values()); pr = sum(refP.values())
        t10w1 = sum(daily(H, v + "@home", ses, col, 0.5) for v in TOP10)
        prw1 = sum(daily(H, v + "@home", ses, col, 5 / 4) for v in PRIM)
        worst10 = pr.nsmallest(10).index
        R = {"TOP10(W2,x0.5)": {"m": metrics(t10), "per_setup": {v: round(float(s.sum()), 2) for v, s in ref10.items()}},
             "PRIMARY(W2,x5/4)": {"m": metrics(pr), "per_setup": {v: round(float(s.sum()), 2) for v, s in refP.items()}},
             "TOP10(W1,x0.5)": {"m": metrics(t10w1)}, "PRIMARY(W1,x5/4)": {"m": metrics(prw1)}}
        R["TOP10(W2,x0.5)"]["corr_primary"] = round(float(np.corrcoef(t10, pr)[0, 1]), 3)
        R["TOP10(W2,x0.5)"]["on_prim_worst10"] = round(float(t10[worst10].sum()), 2)
        R["PRIMARY(W2,x5/4)"]["on_prim_worst10"] = round(float(pr[worst10].sum()), 2)
        for k, b in fz["books"].items():
            wt = (lambda v: 1.0) if k == "B8" else (lambda v: w2[v])
            parts = {v: daily(H, v, ses, col, wt(v)) for v in b["book"]}
            d = sum(parts.values())
            ref = t10w1 if k == "B8" else t10
            ntr = {v: int((H["var"] == v).sum()) for v in b["book"]}
            longs = sum(parts[v] for v in b["book"] if "+" in v)
            shorts = sum(parts[v] for v in b["book"] if "+" not in v)
            R[k] = {"book": b["book"], "m": metrics(d), "vs_top10": paired(d, ref),
                    "per_setup": {v: round(float(s.sum()), 2) for v, s in parts.items()}, "trades": ntr,
                    "per_setup_avg_r": {v: round(float(H[H["var"] == v][col].mean()), 4) if ntr[v] else None for v in b["book"]},
                    "corr_primary": round(float(np.corrcoef(d, pr)[0, 1]), 3), "on_prim_worst10": round(float(d[worst10].sum()), 2),
                    "corr_long_short_sleeves": round(float(np.corrcoef(longs, shorts)[0, 1]), 3) if longs.std() > 0 and shorts.std() > 0 else None}
        res[key] = R
json.dump(res, open(P + "scored.json", "w"), indent=1, default=float)
for key, R in res.items():
    print("==", key)
    rows = [{"book": k, **v["m"], **(v.get("vs_top10") or {})} for k, v in R.items()]
    print(pd.DataFrame(rows).drop(columns=["sessions"]).to_string(index=False))
