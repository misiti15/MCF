"""FIT-only diagnosis of the BEG-09 base (booked trades). Educational only - not financial advice."""
import sys
import pandas as pd
W = sys.argv[1]
t = pd.read_parquet(f"{W}/bk_base_t1.parquet")
t = t[t.half == "fit"].copy()
print("fit trades", len(t), "avg R", round(t.r.mean(), 4), "gross", round(t.r_gross.mean(), 4), "total", round(t.r.sum(), 1))
t["cost_r"] = t.r_gross - t.r
t["hold"] = t.xm - t.em
def tab(col, bins=None):
    g = pd.cut(t[col], bins) if bins is not None else t[col]
    x = t.groupby(g, observed=True).agg(n=("r", "size"), avg=("r", "mean"), tot=("r", "sum"), win=("r", lambda s: (s > 0).mean()),
                                         cost=("cost_r", "mean"))
    print("\n", col); print(x.round(3).to_string())
tab("kind"); tab("side")
tab("tod", [1159, 1230, 1300, 1330, 1400, 1430, 1500])
tab("arm_tod", [1158, 1215, 1245, 1330, 1430])
tab("risk_atr", [0, 0.1, 0.15, 0.2, 0.3, 0.5, 2])
tab("hod_dist_atr", [-1, 0.01, 0.1, 0.2, 0.4, 0.8, 5])
tab("move1129", [-50, -6, -4, -3, 0, 3, 4, 6, 50])
tab("rank", [0, 10, 20, 30])
tab("hold", [-1, 5, 15, 30, 60, 120, 300])
t["entry_gap_r"] = t.side * (t.entry - (t.tgt - t.side * 2 * 0)) / t.risk  # placeholder
w = t.nsmallest(40, "r")
print("\nworst 40: total", round(w.r.sum(), 1), "kinds", w.kind.value_counts().to_dict(), "median hold", w.hold.median(),
      "median risk_atr", round(w.risk_atr.median(), 3), "median cost R", round(w.cost_r.median(), 3))
print(w[["symbol", "date", "side", "tod", "arm_tod", "entry", "stop", "risk", "risk_atr", "hod_dist_atr", "px", "kind", "xt", "r", "r_gross"]].head(20).round(3).to_string())
# MFE-free proxy: time exits vs targets
print("\nexit-time trades (kind 0): n", (t.kind == 0).sum(), "avg R", round(t[t.kind == 0].r.mean(), 3))
