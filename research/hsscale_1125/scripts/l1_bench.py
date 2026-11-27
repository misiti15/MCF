"""Layer-1 candidates on the bench paths (base books). Educational only - not financial advice."""
import pandas as pd, numpy as np
for tag in ("P4_LAT", "P4_GDX", "P9_LAT", "P9_GDX"):
    B = pd.read_csv(f"work/base_{tag}.csv")
    R = pd.read_csv(f"work/rules_{tag}.csv.gz", usecols=["rule", "date", "X"])
    X = R[R.rule == "K4"].set_index("date").X
    B = B.set_index("date").join(X.rename("X4")).dropna(subset=["X4"])
    n = len(B); yr = n / 252
    N = 4 if tag.startswith("P4") else 9
    v1 = B.drop2 <= -np.maximum(8, 0.5 * B.X4)
    v2 = B.drop10 <= -np.maximum(12, 0.75 * B.X4)
    p99 = B.peak_open.rolling(250, min_periods=120).quantile(0.99).shift(1)
    e1 = (B.peak_open > 1.5 * p99) | (B.peak_open > 77)
    e2 = B.peak_sym > 6
    b1 = B.max_ent5 >= 10
    print(f"== {tag} scored days {n}; drop1/2/10 pctl (1%,5%,50%):",
          [round(B[c].quantile(q), 1) for c in ("drop1", "drop2", "drop10") for q in (0.01, 0.05, 0.5)])
    for nm, f in (("V1", v1), ("V2", v2), ("E1", e1), ("E2", e2), ("B1", b1)):
        g = B[f]
        print(f"{nm}: fires {int(f.sum())} ({f.sum()/yr:.1f}/yr); fired days final mean {g.final.mean():.1f}, final<=-X4 {int((g.final<=-g.X4).sum())}, final>0 {int((g.final>0).sum())}")
    print(B.sort_values("drop1").head(6)[["final", "trough", "drop1", "drop2", "drop10", "peak_open", "X4"]].round(1).to_string())
    if "2026-07-29" in B.index:
        print("07-29:", B.loc["2026-07-29", ["final", "trough", "drop1", "drop2", "drop10", "peak_open", "X4"]].round(1).to_dict(), "V1", bool(v1.get("2026-07-29")), "V2", bool(v2.get("2026-07-29")))
