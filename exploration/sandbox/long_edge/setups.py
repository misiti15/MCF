"""Best live long setups (non-Graveyard, >= 50 lots): one-big-day check, weeks, halves, and where their R comes from.
Usage: python setups.py <scratch>. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
S = sys.argv[1]
L = pd.read_parquet(f"{S}/longs2.parquet"); A = L[L.book != "graveyard"].copy()
A["wk"] = pd.to_datetime(A.date).dt.to_period("W-FRI").astype(str).str[:10]
def dayt(s): return s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 2 and s.std(ddof=1) > 0 else np.nan
rows = {}
for st, g in A.groupby("strategy"):
    if len(g) < 50: continue
    d = g.groupby("date").r.sum(); w = g.groupby("wk").r.sum(); tot = g.r.sum()
    h1 = g[g.date < "2026-11-12"].r; h2 = g[g.date >= "2026-11-12"].r
    rows[st] = {"acct": ",".join(sorted(g.account.unique())), "lots": len(g), "days": len(d), "R": tot, "avgR": g.r.mean(),
                "gross": g.gross_r.mean(), "day_t": dayt(d), "R_wo_best": tot - d.max(), "best_day": d.idxmax()[5:],
                "best_share": d.max() / tot if tot > 0 else np.nan, "R_1125": d.get("2026-11-25", 0.0),
                "green_d": f"{(d > 0).sum()}/{len(d)}", "green_wk": f"{(w > 0).sum()}/{len(w)}",
                "avg_h1": h1.mean() if len(h1) else np.nan, "avg_h2": h2.mean() if len(h2) else np.nan}
T = pd.DataFrame(rows).T.sort_values("R", ascending=False)
pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 46)
print(f"Long setups with >= 50 live lots (non-Graveyard): {len(T)}; positive total {int((T.R > 0).sum())}; "
      f"positive w/o best day {int((T.R_wo_best > 0).sum())}; positive w/o 11-25 {int(((T.R - T.R_1125) > 0).sum())}")
print(T.head(20).to_string(float_format=lambda x: f"{x:.3f}"))
named = ["ULT-05-withgap-cont-long", "CWT14-failbrk-orl-p10-long-WB5", "NM-ETF-late-dip-di-long"]
top = list(T.head(8).index) + [n for n in named if n in T.index and n not in T.head(8).index]
print("\nNamed + top setups: per-condition avg R (lots) -- where does each make its money?")
for st in top:
    g = A[A.strategy == st]
    print(f"\n== {st}  lots {len(g)}  R {g.r.sum():.1f}")
    for dim in ["spy_day", "tb", "spy_atb", "prevb", "sprb", "inst", "holdb"]:
        x = g.groupby(dim, observed=True).r.agg(["count", "mean", "sum"])
        print(f"  {dim:8s} " + " | ".join(f"{k}: {r['mean']:+.2f} ({int(r['count'])}, {r['sum']:+.0f}R)" for k, r in x.iterrows()))
