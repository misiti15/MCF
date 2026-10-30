"""TRAIN-only description (hypothesis forming, before PLAN.md): parent trades split by stacking context.
Usage: python decomp_train.py <scratch>   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sim
S = Path(sys.argv[1])
sig = sim.load(S / "p3" / "p3bt")
tr = sim.simulate(sig)
print("parent all n", len(tr), "avgR", round(tr.r.mean(), 4), "(p3 parent: n 29285, -0.070)")
tr = tr[tr.date <= sim.TRAIN_END]
print("TRAIN n", len(tr), "avgR", round(tr.r.mean(), 4))
def tab(g, name):
    a = tr.groupby(g).r.agg(["size", "mean", "sum"]); a["se"] = tr.groupby(g).r.std() / np.sqrt(a["size"])
    print(f"\n-- {name}"); print(a.round(4).to_string())
tab("lot_seq", "lot_seq")
tab(tr.poll_n.clip(upper=3), "lots in same poll on symbol")
tab(np.where(tr.lot_seq == 1, "first", np.where(tr.open_unr > 0.25, "later, open>+0.25R", np.where(tr.open_unr > 0, "later, open 0..0.25", "later, open<=0"))), "later lot vs open lot unrealized")
tab(np.where(tr.tgt_ago.isna(), "no prior target", np.where(tr.tgt_ago <= 60, "target <=60m ago", np.where(tr.tgt_ago <= 120, "60-120m", ">120m"))), "after a same-symbol target exit")
tab(tr.sym_stops.clip(upper=2), "same-symbol stops before")
tab(tr.fam_stops.clip(upper=6) // 2 * 2, "family stops before (bucket)")
tab("fam", "family")
# day-level: share of day R from stacked lots on red days
day = tr.groupby("date").r.sum(); red = day[day < day.quantile(0.1)].index
x = tr[tr.date.isin(red)]
print("\nworst-10% days:", len(red), "R", round(x.r.sum(), 1), "of which lot_seq>1", round(x[x.lot_seq > 1].r.sum(), 1), "n", int((x.lot_seq > 1).sum()), "/", len(x))
x = tr[~tr.date.isin(red)]
print("other days: R", round(x.r.sum(), 1), "lot_seq>1", round(x[x.lot_seq > 1].r.sum(), 1))
