"""LATE-CUT follow-up on the rows that met conditions 1-3 (late_entry1027.md): is late actually WORSE than the same
setup's earlier entries? Session-clustered t of (late mean - early mean), full / train / valid, and the passing
setup's R by entry half-hour. Information added after scoring (it does not change any pre-declared verdict; see notes).
Usage: G21SCR=$SCRATCH/szp/g python research/ops/late_entry1027/robust.py > research/ops/late_entry1027/robust_out.txt
Educational only - not financial advice."""
import math
import numpy as np
import pandas as pd
from late import load_trades

t = load_trades()


def difft(g, C):
    L = g[g.tod > C]; E = g[g.tod <= C]
    days = sorted(g.date.unique())
    a = L.groupby("date").r.agg(["sum", "size"]).reindex(days, fill_value=0)
    b = E.groupby("date").r.agg(["sum", "size"]).reindex(days, fill_value=0)
    mL = a["sum"].sum() / a["size"].sum(); mE = b["sum"].sum() / b["size"].sum()
    uL = (a["sum"] - mL * a["size"]) / a["size"].sum(); uE = (b["sum"] - mE * b["size"]) / b["size"].sum()
    se = math.sqrt(((uL - uE) ** 2).sum())
    return mL - mE, (mL - mE) / se


for s in ["NS1-rsidip-rsi5pop-long-FD", "MF5-flowsell-vwapup-rsi5hi-FD", "MF4-h40-open-flowsell-FD", "ST4-emadn-long-am-t1s05-FD",
          "RW7-gapdn-bounce-early-short-FD", "MF3-open-flowsell-rsi5hi-FD", "NS4-pm-vwap-reclaim-oversold-short-FD"]:
    g = t[t.setup == s]
    for C in (1330, 1400, 1430):
        d, tt = difft(g, C); dtr = difft(g[g.split == "train"], C); dva = difft(g[g.split == "valid"], C)
        print(f"{s} cut {C}: late-early {d:+.3f} t {tt:+.2f} | train {dtr[0]:+.3f} t {dtr[1]:+.2f} | valid {dva[0]:+.3f} t {dva[1]:+.2f}")
g = t[t.setup == "NS1-rsidip-rsi5pop-long-FD"]
g = g.assign(b=pd.cut(g.tod, [0, 1059, 1159, 1259, 1330, 1400, 1430, 1500]))
print("\nNS1-rsidip-rsi5pop-long-FD by entry bucket (n / avg R / sum R):")
print(g.groupby(["b", "split"], observed=True).r.agg(["size", "mean", "sum"]).unstack("split").round(3).to_string())
print(f"total {len(g)} trades {g.r.sum():+.1f}R; skip after 13:30 -> {g[g.tod <= 1330].r.sum():+.1f}R; "
      f"win late {(g[g.tod > 1330].r > 0).mean():.3f} vs early {(g[g.tod <= 1330].r > 0).mean():.3f}")
print("Educational only - not financial advice.")
