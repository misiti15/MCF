"""PYRAMID-S lab scoring: bench10 conventions, testing-arena book (cap 100, cf 0.15, <=3/symbol), ETB >= 0.9,
latch variants, random-entry controls. Educational only - not financial advice."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
W = Path(sys.argv[1]); sys.argv = sys.argv[:1]
import b10s as B
etb = pd.read_parquet(B.HERE / "etb_rate.parquet").rate
spy1 = B.spy_t1()
last = pd.read_parquet(W / "trades_t1.parquet", columns=["date"]).date.max()
d1 = pd.Series(spy1.index); d1 = d1[d1 <= last]; h1 = B.half(d1)
ns = {"fit": int((h1 == "fit").sum()), "check": int((h1 == "check").sum())}
spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet"); spy2.index = spy2.index.astype(str)
spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]; ns["T2"] = len(spy2)
T1 = B.add_r(pd.read_parquet(W / "trades_t1.parquet")); T1["half"] = B.half(T1.date)
T2 = B.add_r(pd.read_parquet(W / "trades_t2.parquet"))
B.no_locked(T1.date.unique()); B.no_locked(T2.date.unique())
K = ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share", "total_r", "worst_day",
     "t_day_clustered", "avg_r_spy_up", "avg_r_spy_flat", "avg_r_spy_down", "median_hold_min")
out, rows, days = {}, [], {}
for s in [x for x, _, _ in B.SETUPS]:
    for tag in ("", "|RND"):
        for L in ((None, -2.0, -4.0) if tag == "" else (None,)):
            rules = dict(cap=100, latch=L, cf=0.15, symcap=3)
            b1 = B.book(T1[T1.setup == s + tag], rules, etb); b2 = B.book(T2[T2.setup == s + tag], rules, etb)
            r = {"fit": B.stats(b1[b1.half == "fit"], ns["fit"], spy1), "check": B.stats(b1[b1.half == "check"], ns["check"], spy1),
                 "T2": B.stats(b2, ns["T2"], spy2)}
            out[f"{s}{tag}|{L}"] = r
            for h, z in r.items():
                rows.append({"setup": s[:14] + tag, "latch": L, "test": h, **{k: z.get(k) for k in K}})
            if tag == "" and L is None:
                days[s] = pd.concat([b1[b1.half != "none"], b2]).groupby("date").r.sum()
json.dump(out, open(W / "lab_s.json", "w"), indent=1, default=float)
pd.set_option("display.width", 300)
print(ns); print(pd.DataFrame(rows).to_string(index=False))
D = pd.DataFrame(days).fillna(0)
print("lab daily-R corr between candidates (union of traded days, 0 = no trade):"); print(D.corr().round(3).to_string())
