"""Mechanic GEN-261023-09: side-by-side final table (parent + WB1..WB4), both tests, isolated and with the live P14 cap
(50 open lots), train/valid, day types, removed-vs-kept, robustness. Educational only - not financial advice."""
import pandas as pd, numpy as np
from sim import *
import lib
D = load(); C2, P2 = D["y2"]; RC, RP = D["rep"]
DAYS2 = sorted(set(C2.date)); DAYSR = sorted(set(RC.date))
reg = lib.regimes().reset_index(); reg["date"] = pd.to_datetime(reg["date"]).dt.strftime("%Y-%m-%d"); REG = reg.set_index("date").regime
R = (("ret3_atr", ">=", 0.20),); A = (("adx7", ">=", 44.0),)
V = {"parent": {}, "WB1": {"lo": 1430}, "WB2": {"extra": R}, "WB3": {"lo": 1430, "extra": R}, "WB4": {"lo": 1430, "extra": R + A}}
rows = []; T = {}
for name, v in V.items():
    for test, (C, P, days) in {"replay": (RC, RP, DAYSR), "2y": (C2, P2, DAYS2)}.items():
        for cap in (None, 50):
            t = trades(C, P, {**v, "conc": cap}); T[(name, test, cap)] = t
            s = stats(t); p = paired(t, T[("parent", test, cap)], days)
            x = dict(copy=name, test=test, cap=cap or "-", **s, pair_day=p[0], pair_t=p[1])
            if test == "2y":
                x["T"] = round(t[t.date <= "2025-12-31"].r.mean(), 3); x["V"] = round(t[t.date > "2025-12-31"].r.mean(), 3)
                rg = t.date.map(REG); x.update({k: round(t.r[rg == k].mean(), 3) for k in ("up", "flat", "down")})
                mo = t.date.str[:7]; bm = t.groupby(mo).r.sum().idxmax(); x["wo_best_month"] = round(t[mo != bm].r.mean(), 3)
                x["cap20"] = stats(trades(C, P, {**v, "daycap": 20})).get("avg")
            rows.append(x)
F = pd.DataFrame(rows); pd.set_option("display.width", 250); print(F.to_string()); F.to_csv(OUT + "final.csv", index=False)
p = T[("parent", "2y", None)]; k = T[("WB4", "2y", None)]
kk = set(zip(k.symbol, k.date)); rem = p[[x not in kk for x in zip(p.symbol, p.date)]]
print("WB4 removed", len(rem), round(rem.r.mean(), 3), "kept", len(k), round(k.r.mean(), 3))
print("replay by day:", {n: T[(n, "replay", None)].groupby("date").r.agg(["count", "sum"]).round(2).to_dict() for n in V})
