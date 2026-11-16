"""Mechanic GEN-261027-01: live trades vs the copies' parts; 2y robustness (no April 2025, day cap 20, train/valid). Educational only - not financial advice."""
import pandas as pd, numpy as np
from sim import *
L = pd.read_parquet(OUT + "live_feat.parquet")
L["W"] = L.f_tod <= 1430; L["A"] = L.f_adv20 >= 100e6
ctx = pd.concat([pd.read_parquet(OUT + "replay_ctx_new.parquet"), pd.read_parquet("/home/user/MCF/research/history2y/data/context/month=2026-10.parquet")])
ctx["date"] = ctx.date.astype(str); ctx = ctx.drop_duplicates(["date", "tod"])
b0 = ctx[ctx.tod == 950].set_index("date").breadth
L["brc"] = [ctx[(ctx.date == d) & (ctx.tod == t)].breadth.iloc[0] - b0[d] if t == t else np.nan for d, t in zip(L.date, L.f_tod)]
L["B"] = L.brc <= 0.2
pd.set_option("display.width", 250)
print(L.sort_values("R")[["symbol", "date", "f_tod", "R", "exit_reason", "f_adv20", "brc", "W", "A", "B"]].round(3).to_string())
for k in ("W", "B", "A"):
    print(k, "kept", L[L[k]].R.agg(["count", "mean", "sum"]).round(3).to_dict(), "dropped", L[~L[k]].R.agg(["count", "mean", "sum"]).round(3).to_dict())
for ks in (("W", "B"), ("W", "A", "B")):
    m = np.logical_and.reduce([L[k] for k in ks])
    print(ks, "kept", L[m].R.agg(["count", "mean", "sum"]).round(3).to_dict(), "dropped", L[~m].R.agg(["count", "mean", "sum"]).round(3).to_dict())
D = load(); C2, P2 = D["y2"]; RC, RP = D["rep"]
V = {"parent": {}, "WB4 W+B": {"hi": 1430, "extra": (("br_chg", "<=", 0.2),)}, "WB5 W+A+B": {"hi": 1430, "adv": 100e6, "extra": (("br_chg", "<=", 0.2),)}}
for n, v in V.items():
    t = trades(C2, P2, v); na = t[~t.date.str.startswith("2025-04")]
    c20 = trades(C2, P2, {**v, "daycap": 20}); c20r = trades(RC, RP, {**v, "daycap": 20})
    print(n, "no-Apr25", round(na.r.mean(), 3), len(na), "| daycap20 2y", stats(c20), "| daycap20 replay", stats(c20r))
