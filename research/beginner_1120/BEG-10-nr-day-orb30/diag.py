"""FIT-only diagnosis of the BEG-10 base (booked trades). Educational only - not financial advice."""
import sys
import pandas as pd
W = sys.argv[1]
t = pd.read_parquet(f"{W}/bk_base_fit.parquet")
t = t[t.half == "fit"].copy()
print("fit trades", len(t), "avg R", round(t.r.mean(), 4), "gross", round(t.r_gross.mean(), 4), "total", round(t.r.sum(), 1))
t["cost_r"] = t.r_gross - t.r
t["hold"] = t.xm - t.em


def tab(col, bins=None):
    g = pd.cut(t[col], bins) if bins is not None else t[col]
    x = t.groupby(g, observed=True).agg(n=("r", "size"), avg=("r", "mean"), gross=("r_gross", "mean"), tot=("r", "sum"),
                                         win=("r", lambda s: (s > 0).mean()), cost=("cost_r", "mean"))
    print("\n", col); print(x.round(3).to_string())


tab("kind"); tab("side")
tab("tod", [959, 1005, 1015, 1030, 1100, 1130, 1230])
tab("risk_atr", [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5])
tab("or_atr", [0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8])
tab("prange_atr", [0, 0.3, 0.4, 0.5, 0.6])
tab("slip_r", [-0.01, 0.001, 0.1, 0.3, 1, 10])
tab("hold", [-1, 5, 15, 30, 60, 120, 400])
tab("cost_r", [0, 0.05, 0.1, 0.15])
tab("entry", [0, 20, 50, 100, 300, 5000])
w = t.nsmallest(int(len(t) * 0.1), "r")
print("\nworst 10%:", len(w), "total", round(w.r.sum(), 1), "kinds", w.kind.value_counts().to_dict(), "median hold", w.hold.median(),
      "median risk_atr", round(w.risk_atr.median(), 3), "median or_atr", round(w.or_atr.median(), 3),
      "median cost R", round(w.cost_r.median(), 3), "median slip R", round(w.slip_r.median(), 3),
      "median tod", w.tod.median())
print("all: median risk_atr", round(t.risk_atr.median(), 3), "median hold", t.hold.median(), "median tod", t.tod.median())
print(w[["symbol", "date", "side", "tod", "entry", "stop", "risk", "risk_atr", "or_atr", "slip_r", "px", "kind", "xt", "r",
         "r_gross"]].head(25).round(3).to_string())
d = t.groupby("date").r.sum().sort_values()
print("\nworst fit days", d.head(8).round(1).to_dict())
