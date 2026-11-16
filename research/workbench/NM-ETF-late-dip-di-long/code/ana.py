"""Mechanic NM-ETF: all-trades component analysis of the parent (2y + replay). Educational only - not financial advice."""
import pandas as pd, numpy as np
from sim import *
D = load()
t = trades(*D["y2"], {}); t["sp"] = np.where(t.date <= "2025-12-31", "T", "V")
t["inv"] = t.symbol.isin(INVERSE); t["lev3"] = t.symbol.isin(LEV3)
t.to_parquet(OUT + "parent2y.parquet")
def tab(col, bins=None, q=None):
    x = t[col] if bins is None and q is None else (pd.cut(t[col], bins) if bins is not None else pd.qcut(t[col], q, duplicates="drop"))
    g = t.groupby([x], observed=True).agg(n=("r", "size"), avg=("r", "mean"), win=("r", lambda r: (r > 0).mean()),
        stop=("why", lambda w: (w == "stop").mean()), T=("r", lambda r: r[t.loc[r.index, "sp"] == "T"].mean()),
        V=("r", lambda r: r[t.loc[r.index, "sp"] == "V"].mean()))
    print(f"\n== {col}"); print(g.round(3).to_string())
tab("tod", [1355, 1415, 1430, 1445, 1500])
tab("inv"); tab("lev3")
for c in ["atrp", "ret3", "di", "adx7", "spy950", "vwap_atr", "day_pos", "fo", "fpc", "rvol", "ret12", "s950", "rsi7", "z12"]:
    tab(c, q=4)
t["mo"] = t.date.str[:7]; print(t.groupby("mo").r.agg(["count", "mean", "sum"]).round(2).to_string())
d = t.groupby("date").r.agg(["count", "sum"]).sort_values("sum"); print(d.head(6)); print(d.tail(6))
print(t.groupby("why").agg(n=("r", "size"), avg=("r", "mean"), mfe=("mfe", "median"), mae=("mae", "median")).round(3))
tm = t[t.why == "time"]; print("time exits: mfe>=0.3:", (tm.mfe >= 0.3).mean().round(2), "mfe>=0.4", (tm.mfe >= 0.4).mean().round(2), "avg r", tm.r.mean().round(3))
st = t[t.why == "stop"]; print("stops: mfe>=0.3 first", (st.mfe >= 0.3).mean().round(2), "n", len(st))
print("trades per day dist", t.groupby("date").size().describe().round(2).to_dict())
t["k"] = t.groupby("date").ent.rank(method="first"); tab("k", [0, 1, 2, 3, 5, 100])
