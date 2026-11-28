"""GAPSWITCH live readout (descriptive, in-sample): Primary lots of the roster setups by SPY gap, LR8 costs,
from regsteer_1126 live_states.parquet (10-06..11-25). Usage: python live.py RSW_DIR. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
L = pd.read_parquet(Path(sys.argv[1]) / "live_states.parquet"); L["date"] = L.date.astype(str)
S = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
p = L[(L.account == "primary") & L.strategy.isin(S)].copy()
print("gap units sample", p.gap.describe().round(4).to_dict())
g = p.gap if p.gap.abs().max() < 0.2 else p.gap / 100
p["b"] = np.where(g >= 0.005, "ge+0.50", np.where(g >= 0.0025, "+0.25..0.50", "lt+0.25"))
p["b"] = np.where(g.isna(), "nan", p.b)
days = p.groupby("date").agg(gap=("gap", "first"), b=("b", "first"))
print("sessions", len(days), days.b.value_counts().to_dict())
t = p.groupby(["strategy", "b"]).agg(lots=("r", "size"), R=("r", "sum"), Rlot=("r", "mean"), days=("date", "nunique")).round(3)
print(t.to_string())
sh = p[p.side < 0]
for th in (0.0025, 0.005):
    for ro, ss in (("A", S[1:3]), ("B", S[:3])):
        q = sh[sh.strategy.isin(ss)]; gg = q.gap if q.gap.abs().max() < 0.2 else q.gap / 100
        f = q[gg >= th]; ds = f.groupby("date").r.sum()
        print(f"roster {ro} th {th}: shorts skipped lots {len(f)}, R {f.r.sum():+.1f} on {ds.size} days; best skip-day share "
              f"{(-ds).max() / (-ds.sum()) if -ds.sum() > 0 else float('nan'):.2f}; R without those days {q.r.sum() - f.r.sum():+.1f} of {q.r.sum():+.1f}")
