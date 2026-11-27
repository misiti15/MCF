"""hsscale step 3: score Layer-2 rules per lineup / latch variant (PLAN.md metrics). Usage: python score2.py WORK TAG...
Educational only - not financial advice."""
import math, sys
from pathlib import Path
import numpy as np
import pandas as pd
W = Path(sys.argv[1])


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if d >= "2025-10-01":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


allrows, setrows = [], []
for tag in sys.argv[2:]:
    O = pd.read_csv(W / f"rules_{tag}.csv.gz")
    B = pd.read_csv(W / f"base_{tag}.csv")
    S = [c for c in O.columns if c not in ("rule", "date", "X", "fire_m", "lots_after")]
    O["R"] = O[S].sum(1)
    base = O[O.rule == "none"].set_index("date")
    lots = B.set_index("date").lots.reindex(base.index)
    avg = base.R.sum() / lots.sum()
    base["per"] = base.index.map(period)
    for rule, g in O[O.rule != "none"].groupby("rule"):
        g = g.set_index("date").reindex(base.index)
        d = g.R - base.R
        fired = g.fire_m.notna()
        for per in ("FIT", "T2", "CHECK", "ALL"):
            m = (base.per == per) if per != "ALL" else pd.Series(True, index=base.index)
            n = int(m.sum())
            dd, f, b, x, X = d[m], fired[m], base.R[m], g.R[m], g.X[m]
            bad = f & (b <= -X + 1e-9)
            rec = f & ~bad
            la = g.lots_after[m].sum()
            t = dd.mean() / (dd.std(ddof=1) / math.sqrt(n)) if dd.std() > 0 else float("nan")
            allrows.append(dict(tag=tag, rule=rule, period=per, sessions=n, fires=int(f.sum()), fires_yr=round(f.sum() / n * 252, 1),
                                base_R=round(b.sum(), 1), R=round(x.sum(), 1), dR=round(dd.sum(), 1), dR_yr=round(dd.sum() / n * 252, 1),
                                saved_bad=round(dd[bad].sum(), 1), n_bad=int(bad.sum()), lost_rec=round(dd[rec].sum(), 1), n_rec=int(rec.sum()),
                                rec_to_neg=int((rec & (b > 0)).sum()),
                                worst_base=round(b.min(), 1), worst=round(x.min(), 1), le6_base=int((b <= -6).sum()), le6=int((x <= -6).sum()),
                                t=round(t, 2), lots_removed=int(la), avgR_lot=round(avg, 3),
                                dR_neutral=round(dd.sum() + avg * la, 1), dR_neutral_yr=round((dd.sum() + avg * la) / n * 252, 1),
                                dR_p10=round(dd.sum() + (avg - 0.10) * la, 1),
                                X_min=round(X.min(), 1), X_med=round(X.median(), 1), X_max=round(X.max(), 1)))
        for s in S:
            ds = g[s] - base[s]
            setrows.append(dict(tag=tag, rule=rule, setup=s[:40], base_R=round(base[s].sum(), 1), dR=round(ds.sum(), 1),
                                days_better=int((ds > 1e-9).sum()), days_worse=int((ds < -1e-9).sum()),
                                better_sum=round(ds[ds > 0].sum(), 1), worse_sum=round(ds[ds < 0].sum(), 1)))
A = pd.DataFrame(allrows); P = pd.DataFrame(setrows)
A.to_csv(W.parent / "l2_results.csv", index=False); P.to_csv(W.parent / "l2_per_setup.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(A[A.period == "ALL"].drop(columns=["period"]).to_string(index=False))
for per in ("FIT", "T2", "CHECK"):
    print("==", per)
    print(A[A.period == per][["tag", "rule", "fires", "fires_yr", "dR", "worst_base", "worst", "lost_rec", "saved_bad", "dR_neutral", "t"]].to_string(index=False))
print(P.to_string(index=False))
