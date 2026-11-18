"""W5 post-plan check (1 config): C3-WB5 refire-off on L3-gap-slope-rsi5hi-FD as a paired effect on the full record.
Run after demo.py (needs demo_scored.pkl in the scratch dir S). Educational only - not financial advice."""
import math, os, numpy as np, pandas as pd
S = os.environ.get("W5S", "<scratch>")
x = pd.read_pickle(f"{S}/demo_scored.pkl"); g = x[x.s == "L3-rsi5hi"].copy()
g["et"] = pd.to_datetime(g.entry_time, utc=True, format="mixed"); g = g.sort_values("et")
g["first"] = ~g.duplicated(["date", "symbol"]); g["d"] = np.where(g["first"], 0.0, -g.R)
d = g.groupby("date").d.agg(["sum", "size"]); n = d["size"].sum(); th = d["sum"].sum() / n; k = len(d)
se = math.sqrt(k / (k - 1) * ((d["sum"] - d["size"] * th) ** 2).sum()) / n
print("trades", len(g), "refires", int((~g["first"]).sum()), "paired delta/trade", round(th, 4), "SE", round(se, 4), "t", round(th / se, 2))
ds = sorted(g.date.unique()); h = ds[(len(ds) + 1) // 2]
for nm, s in [("fit", g[g.date < h]), ("check", g[g.date >= h])]:
    print(nm, len(s), "delta/trade", round(s.d.mean(), 4), "refires", int((~s["first"]).sum()))
# output 2026-11-18: trades 158 refires 25 paired delta/trade 0.0029 SE 0.0262 t 0.11; fit 77 -0.0285 (10); check 81 +0.0328 (15)
