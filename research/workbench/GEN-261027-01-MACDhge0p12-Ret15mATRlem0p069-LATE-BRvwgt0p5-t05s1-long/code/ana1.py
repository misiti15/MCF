"""Mechanic GEN-261027-01: is the breadth-change gate a few-days effect? Day-level look (2y). Educational only - not financial advice."""
import pandas as pd, numpy as np
from sim import *
import lib
D = load(); C2, P2 = D["y2"]
reg = lib.regimes().reset_index(); reg["date"] = pd.to_datetime(reg["date"]).dt.strftime("%Y-%m-%d"); REG = reg.set_index("date").regime
p = trades(C2, P2, {}); w = trades(C2, P2, {"hi": 1430}); wb = trades(C2, P2, {"hi": 1430, "extra": (("br_chg", "<=", 0.2),)})
for t in (p, w, wb):
    t["br_chg"] = C2.loc[t.idx, "br_chg"].to_numpy(); t["spy950"] = C2.loc[t.idx, "spy950"].to_numpy(); t["breadth"] = C2.loc[t.idx, "breadth"].to_numpy()
d = p.groupby("date").agg(n=("r", "size"), R=("r", "sum"), brc=("br_chg", "median"), spy=("spy950", "median"))
d["reg"] = d.index.map(REG)
print(d.sort_values("R").head(12).round(2)); print(d.sort_values("R").tail(6).round(2))
for name, t in (("parent", p), ("W", w), ("W+B", wb)):
    dd = t.groupby("date").r.sum().sort_values()
    for k in (0, 3, 5, 10):
        drop = set(dd.index[:k]) | set(dd.index[-k:]) if k else set()
        x = t[~t.date.isin(drop)]
        print(name, f"drop {k} worst+{k} best days: avg {x.r.mean():.3f} n {len(x)}")
# br_chg buckets on parent within the 14:00-14:30 window, by split and without the 10 worst days
w["sp"] = np.where(w.date <= "2025-12-31", "T", "V")
worst10 = set(w.groupby("date").r.sum().sort_values().index[:10])
w["b"] = pd.cut(w.br_chg, [-1, 0, 0.1, 0.15, 0.2, 0.25, 0.3, 1])
print(w.groupby("b", observed=True).agg(n=("r", "size"), avg=("r", "mean"), days=("date", "nunique"),
      T=("r", lambda r: r[w.loc[r.index, "sp"] == "T"].mean()), V=("r", lambda r: r[w.loc[r.index, "sp"] == "V"].mean()),
      ex10=("r", lambda r: r[~w.loc[r.index, "date"].isin(worst10)].mean())).round(3))
w["mo"] = w.date.str[:7]; wb["mo"] = wb.date.str[:7]
print(pd.concat([w.groupby("mo").r.agg(["count", "mean"]), wb.groupby("mo").r.agg(["count", "mean"])], axis=1).round(3).to_string())
