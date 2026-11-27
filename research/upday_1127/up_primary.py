"""UPDAY_1127: Primary 4 bench daily R proxy (FIT+CHECK) from bench10 walked lots (lbw/walk_t1.parquet, built tonight by
LONGBOOK). LIVE-L on shorts / LR8 on NM-ETF (as E4), cap 30 lots/day by entry minute, no latch (disclosed).
Usage: python up_primary.py WALK_T1 ETB_PARQUET OUT_CSV. Locked block asserted absent. Educational only."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "research/primshorts_1126")
import calib_live as CL
from mcf.research.gates import tod_cost_mult
LOCK = ("2024-11-01", "2025-02-28")
P4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
      "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
x = pd.read_parquet(sys.argv[1]); x = x[x.setup.isin(P4) & (x.shadow < 0) & x.px.notna()].copy()
x["date"] = x.date.astype(str)
d = x.date; assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
etb = pd.read_parquet(sys.argv[2]).rate
x = x[x.entry >= 5.0]; x = x[(x.side > 0) | x.symbol.map(etb).fillna(0).ge(0.9)]
cells = json.load(open("research/primshorts_1126/cells_live.json"))
em = x.em.to_numpy(int); tod = (em // 60) * 100 + em % 60
tier = np.where((np.abs(x.gap) >= 20) | (x.entry < 5), 3.0, 1.0)
ecost = (0.01 + x.entry * 1e-4) * tod_cost_mult(tod)
xcost = np.where(x.kind == 2, 0.0, 0.01 + x.px * 1e-4) + np.where(x.kind == 1, 0.02, 0.0)
borrow = np.where(x.side < 0, 1.2e-4 * x.entry, 0.0)
gross = x.side * (x.px - x.entry)
lr8 = (gross - tier * (ecost + xcost) - borrow) / x.risk
kd = np.where(x.kind == 2, "target", np.where(x.kind == 1, "stop", "market"))
ll = gross / x.risk - CL.predict_R(cells, x.entry.to_numpy(), x.risk.to_numpy(), kd)
x["r"] = np.where(x.setup == P4[3], lr8, ll)
x = x.sort_values(["date", "em", "symbol"]).groupby("date").head(30)
out = x.groupby("date").agg(prim_R=("r", "sum"), prim_lots=("r", "size"),
                            prim_short_R=("r", lambda s: s[x.loc[s.index, "side"] < 0].sum()))
out.to_csv(sys.argv[3]); print(out.describe())
