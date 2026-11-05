"""GATE1: day-clustered detail for the most promising (setup/family, state) combos picked from TRAIN+VALID (so LIVE is
their only independent look). Entries >= 10:00, state of the latest 30-min checkpoint (k=1).
Usage: python combos.py <scratch>. Educational only - not financial advice."""
import math, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
T = pd.read_parquet(Path(sys.argv[1]) / "trades.parquet")
T = T[T.w.isin(["TRAIN", "VALID", "LIVE"]) & (T.m >= 600) & T.cp.notna()]
SN = {"UP": 1, "DOWN": -1, "MIXED": 0}
C = [("setup", "L3-gap-slope-fromopen-FD", "UP"), ("fs", "L+S", "UP"), ("setup", "NM-AR-AM-gapdown-capitulation-long", "DOWN"),
     ("setup", "ST7-rsi50dn-long-pm-t1s1-FD", "DOWN"), ("setup", "NS3-failed-vwap-reclaim-short-FD", "MIXED"),
     ("setup", "RW4-ns3-adv150-short-FD", "MIXED"), ("setup", "L3-gap-slope-rsi5hi-FD", "UP")]
rows = []
for key, u, s in C:
    x = T[T[key] == u]
    for w in ["TRAIN", "VALID", "LIVE"]:
        y = x[x.w == w]
        for lab, z in [("in", y[y.st == SN[s]]), ("out", y[y.st != SN[s]])]:
            if not len(z):
                continue
            d = z.groupby("date").r.sum(); sd = d.std(ddof=1)
            best = d.idxmax(); zb = z[z.date != best]
            rows.append(dict(combo=f"{u} | {s}", w=w, part=lab, n=len(z), days=len(d), avgR=round(z.r.mean(), 3),
                             t=round(d.mean() / (sd / math.sqrt(len(d))), 2) if len(d) > 1 and sd > 0 else np.nan,
                             avg_wo_best=round(zb.r.mean(), 3) if len(zb) else np.nan,
                             best_share=round(d.max() / d.sum(), 2) if d.sum() > 0 else np.nan))
R = pd.DataFrame(rows); R.to_csv(HERE / "combos.csv", index=False)
pd.set_option("display.width", 250); print(R.to_string(index=False))
